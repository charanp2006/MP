from __future__ import annotations

import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

FUNCTION_NAME = os.getenv("FUNCTION_NAME", "fn-checkout")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8080"))
WARM_REPLICAS = int(os.getenv("WARM_REPLICAS", "0"))
ENERGY_PER_MB = float(os.getenv("ENERGY_PER_MB", "0.002"))
BUCKETS = (5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1000.0, float("inf"))

LOCK = threading.Lock()
COUNTS = {"200": 0, "500": 0, "400": 0, "404": 0}
HISTOGRAM = [0] * len(BUCKETS)
LATENCY_SUM = 0.0
LATENCY_COUNT = 0
COLD_STARTS = 1
ENERGY_W = 0.0
START_TIME = time.time()


def _escaped(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _observe_latency(ms: float) -> None:
    global LATENCY_SUM, LATENCY_COUNT
    LATENCY_SUM += ms
    LATENCY_COUNT += 1
    for index, bound in enumerate(BUCKETS):
        if ms <= bound:
            HISTOGRAM[index] += 1


def _metrics_text() -> str:
    label = f'function_name="{_escaped(FUNCTION_NAME)}"'
    with LOCK:
        lines = [
            "# HELP fn_invocations_total Function invocations by result code.",
            "# TYPE fn_invocations_total counter",
        ]
        for code, count in sorted(COUNTS.items()):
            lines.append(f"fn_invocations_total{{{label},code=\"{code}\"}} {count}")
        lines.extend(
            [
                "# HELP fn_request_duration_ms Invocation latency in milliseconds.",
                "# TYPE fn_request_duration_ms histogram",
            ]
        )
        cumulative = 0
        for bound, count in zip(BUCKETS, HISTOGRAM):
            cumulative += count
            le = "+Inf" if bound == float("inf") else str(int(bound))
            lines.append(f"fn_request_duration_ms_bucket{{{label},le=\"{le}\"}} {cumulative}")
        lines.append(f"fn_request_duration_ms_sum{{{label}}} {LATENCY_SUM:.3f}")
        lines.append(f"fn_request_duration_ms_count{{{label}}} {LATENCY_COUNT}")
        lines.extend(
            [
                "# HELP fn_cold_starts_total Cold starts observed by this worker.",
                "# TYPE fn_cold_starts_total counter",
                f"fn_cold_starts_total{{{label}}} {COLD_STARTS}",
                "# HELP fn_energy_w Energy proxy in watts for the worker.",
                "# TYPE fn_energy_w gauge",
                f"fn_energy_w{{{label}}} {ENERGY_W:.6f}",
                "# HELP fn_warm_replicas Warm replicas configured for reuse.",
                "# TYPE fn_warm_replicas gauge",
                f"fn_warm_replicas{{{label}}} {WARM_REPLICAS}",
                "# HELP fn_process_uptime_seconds Process uptime in seconds.",
                "# TYPE fn_process_uptime_seconds gauge",
                f"fn_process_uptime_seconds{{{label}}} {time.time() - START_TIME:.3f}",
                "",
            ]
        )
        return "\n".join(lines)


class Handler(BaseHTTPRequestHandler):
    server_version = "live-fn/1.0"

    def _send(self, status: int, payload: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _json(self, status: int, payload: dict) -> None:
        self._send(status, json.dumps(payload).encode("utf-8"), "application/json")

    def _invoke(self, payload: dict) -> None:
        started = time.perf_counter()
        global ENERGY_W
        try:
            size = len(json.dumps(payload).encode("utf-8"))
            if size > 1_048_576:
                self._json(400, {"error": "payload too large"})
                code = "400"
            else:
                ENERGY_W = round(ENERGY_PER_MB * (size / 1_048_576.0) + 0.5, 6)
                self._json(200, {"message": "ok", "function": FUNCTION_NAME, "bytes": size})
                code = "200"
        except Exception:
            self._json(500, {"error": "invoke failed"})
            code = "500"
        latency_ms = (time.perf_counter() - started) * 1000.0
        with LOCK:
            COUNTS[code] += 1
            _observe_latency(latency_ms)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._json(200, {"status": "ok", "function": FUNCTION_NAME})
            return
        if parsed.path == "/metrics":
            self._send(200, _metrics_text().encode("utf-8"), "text/plain; version=0.0.4; charset=utf-8")
            return
        if parsed.path in {"/invoke", "/"} or parsed.path.startswith("/function/"):
            params = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
            self._invoke(params)
            return
        with LOCK:
            COUNTS["404"] += 1
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path not in {"/invoke", "/"} and not parsed.path.startswith("/function/"):
            with LOCK:
                COUNTS["404"] += 1
            self._json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
            if not isinstance(payload, dict):
                payload = {"value": payload}
        except Exception:
            payload = {"raw": raw.decode("utf-8", errors="replace")[:512]}
        self._invoke(payload)


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", SERVICE_PORT), Handler)
    server.daemon_threads = True
    server.serve_forever()


if __name__ == "__main__":
    main()
