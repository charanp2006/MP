from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse

DEFAULT_SERVICE_NAME = "fn_checkout"
PAYLOAD_CLASSES = ("small", "medium", "large")
ROUTES = ("/", "/health", "/ready", "/invoke", "/metrics")
MAX_BODY_BYTES = 1_048_576
ERROR_LATENCY_MS = 2.0
COLD_START_PENALTY_MS = 40.0
ENERGY_IDLE_W = 0.5
DEFAULT_ENERGY_PER_MB = 0.002
DEFAULT_VERSION = "1.0.0"

FUNCTION_NAMES = {
    "fn_checkout": "fn-checkout",
    "fn_search": "fn-search",
    "fn_recommend": "fn-recommend",
}

LATENCY_PROFILE_MS = {
    "fn_checkout": {"small": 22.0, "medium": 58.0, "large": 145.0},
    "fn_search": {"small": 12.0, "medium": 34.0, "large": 86.0},
    "fn_recommend": {"small": 18.0, "medium": 47.0, "large": 118.0},
}

BUCKETS = (5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1000.0, float("inf"))
RESULT_KEYS = {
    "fn_checkout": "checkout",
    "fn_search": "search",
    "fn_recommend": "recommendations",
}
INVOCATION_CODES = ("200", "400", "404", "500")
ERROR_REASONS = (
    "invalid_json",
    "invalid_payload",
    "invalid_payload_class",
    "validation_error",
    "payload_too_large",
    "not_found",
    "server_error",
)


class PayloadError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ServiceConfig:
    name: str
    function_name: str
    version: str
    active_containers: int
    energy_per_mb: float


@dataclass
class ServiceState:
    config: ServiceConfig
    lock: threading.Lock = field(default_factory=threading.Lock)
    started: float = field(default_factory=time.monotonic)
    warm: bool = False
    cold_starts: int = 1
    invocations: dict[str, int] = field(default_factory=lambda: {code: 0 for code in INVOCATION_CODES})
    errors: dict[str, int] = field(default_factory=lambda: {reason: 0 for reason in ERROR_REASONS})
    buckets: list[int] = field(default_factory=lambda: [0] * len(BUCKETS))
    latency_sum: float = 0.0
    latency_count: int = 0
    energy_w: float = ENERGY_IDLE_W


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _label_pair(state: ServiceState) -> str:
    return (
        f'function_name="{_escape(state.config.function_name)}",'
        f'service="{_escape(state.config.name)}"'
    )


def _metrics_text(state: ServiceState) -> str:
    labels = _label_pair(state)
    with state.lock:
        lines = [
            "# HELP fn_invocations_total Invocations grouped by result code.",
            "# TYPE fn_invocations_total counter",
        ]
        for code, count in sorted(state.invocations.items()):
            lines.append(f'fn_invocations_total{{{labels},code="{code}"}} {count}')

        lines.extend(
            [
                "# HELP fn_request_duration_ms Deterministic simulated invocation latency in milliseconds.",
                "# TYPE fn_request_duration_ms histogram",
            ]
        )
        cumulative = 0
        for bound, count in zip(BUCKETS, state.buckets):
            cumulative += count
            le = "+Inf" if bound == float("inf") else str(int(bound))
            lines.append(f'fn_request_duration_ms_bucket{{{labels},le="{le}"}} {cumulative}')
        lines.append(f"fn_request_duration_ms_sum{{{labels}}} {state.latency_sum:.3f}")
        lines.append(f"fn_request_duration_ms_count{{{labels}}} {state.latency_count}")

        lines.extend(
            [
                "# HELP fn_errors_total Rejected invocations grouped by reason.",
                "# TYPE fn_errors_total counter",
            ]
        )
        for reason, count in sorted(state.errors.items()):
            lines.append(f'fn_errors_total{{{labels},reason="{reason}"}} {count}')

        lines.extend(
            [
                "# HELP fn_cold_starts_total Cold workers started by this process.",
                "# TYPE fn_cold_starts_total counter",
                f"fn_cold_starts_total{{{labels}}} {state.cold_starts}",
                "# HELP fn_energy_w Deterministic energy proxy in watts for the worker.",
                "# TYPE fn_energy_w gauge",
                f"fn_energy_w{{{labels}}} {state.energy_w:.6f}",
                "# HELP fn_active_containers Containers represented by this worker.",
                "# TYPE fn_active_containers gauge",
                f"fn_active_containers{{{labels}}} {state.config.active_containers}",
                "",
            ]
        )
        return "\n".join(lines)


def _begin_invocation(state: ServiceState) -> bool:
    with state.lock:
        is_cold = not state.warm
        state.warm = True
        return is_cold


def _record_result(
    state: ServiceState,
    code: str,
    reason: str | None,
    latency_ms: float,
    payload_bytes: int,
) -> None:
    with state.lock:
        state.invocations[code] += 1
        if reason:
            state.errors[reason] += 1
        for index, bound in enumerate(BUCKETS):
            if latency_ms <= bound:
                state.buckets[index] += 1
                break
        state.latency_sum += latency_ms
        state.latency_count += 1
        state.energy_w = round(
            ENERGY_IDLE_W + state.config.energy_per_mb * (payload_bytes / 1_048_576.0),
            6,
        )


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _bounded_int(value: object, minimum: int, maximum: int, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise PayloadError("validation_error", f"limit must be an integer between {minimum} and {maximum}")
    return value


def _digest(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _checkout_result(payload: dict) -> tuple[str, dict]:
    items = payload.get("items")
    if not isinstance(items, list) or not 1 <= len(items) <= 50:
        raise PayloadError("validation_error", "items must contain between 1 and 50 entries")

    total_units = 0
    subtotal = 0.0
    skus: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            raise PayloadError("validation_error", "each item must be an object")
        sku = item.get("sku")
        quantity = item.get("quantity")
        unit_price = item.get("unit_price")
        if not isinstance(sku, str) or not sku.strip():
            raise PayloadError("validation_error", "item sku must be a non-empty string")
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            raise PayloadError("validation_error", "item quantity must be a positive integer")
        if not _is_number(unit_price) or unit_price < 0:
            raise PayloadError("validation_error", "item unit_price must be a non-negative number")
        skus.append(sku.strip())
        total_units += quantity
        subtotal += quantity * float(unit_price)

    return (
        "checkout",
        {
            "order_id": f"ord-{_digest(*skus)[:12]}",
            "item_count": len(items),
            "total_units": total_units,
            "subtotal": round(subtotal, 2),
            "currency": "INR",
            "status": "confirmed",
        },
    )


def _search_result(payload: dict) -> tuple[str, dict]:
    query = payload.get("query")
    if not isinstance(query, str) or not 0 < len(query.strip()) <= 200:
        raise PayloadError("validation_error", "query must be a non-empty string of at most 200 characters")
    limit = _bounded_int(payload.get("limit"), 1, 20, 5)
    digest = _digest(query.strip().lower())
    matches = 1 + int(digest[:8], 16) % 50
    count = min(limit, matches)
    top_results = [
        {
            "rank": index + 1,
            "doc_id": f"doc-{digest[index * 4 : index * 4 + 4]}",
            "score": round(1.0 - index * 0.05, 2),
        }
        for index in range(count)
    ]
    return (
        "search",
        {
            "result_count": count,
            "total_matches": matches,
            "query_tokens": len(query.split()),
            "top_results": top_results,
        },
    )


def _recommend_result(payload: dict) -> tuple[str, dict]:
    category = payload.get("category")
    if not isinstance(category, str) or not 0 < len(category.strip()) <= 100:
        raise PayloadError("validation_error", "category must be a non-empty string of at most 100 characters")
    limit = _bounded_int(payload.get("limit"), 1, 10, 3)
    digest = _digest(category.strip().lower())
    items = [
        {
            "item_id": f"sku-{digest[index * 4 : index * 4 + 4]}",
            "score": round(0.95 - index * 0.07, 2),
        }
        for index in range(limit)
    ]
    return (
        "recommendations",
        {
            "basis": "category",
            "count": len(items),
            "items": items,
        },
    )


RESULT_BUILDERS = {
    "fn_checkout": _checkout_result,
    "fn_search": _search_result,
    "fn_recommend": _recommend_result,
}


def create_app(
    service_name: str | None = None,
    *,
    function_name: str | None = None,
    version: str | None = None,
    active_containers: int | None = None,
) -> type[BaseHTTPRequestHandler]:
    name = str(service_name or os.getenv("SERVICE_NAME", DEFAULT_SERVICE_NAME)).strip()
    if name not in LATENCY_PROFILE_MS:
        expected = ", ".join(sorted(LATENCY_PROFILE_MS))
        raise ValueError(f"unknown SERVICE_NAME {name!r}; expected one of {expected}")

    config = ServiceConfig(
        name=name,
        function_name=str(function_name or os.getenv("FUNCTION_NAME") or FUNCTION_NAMES[name]),
        version=str(version or os.getenv("SERVICE_VERSION", DEFAULT_VERSION)),
        active_containers=int(active_containers if active_containers is not None else os.getenv("ACTIVE_CONTAINERS", "1")),
        energy_per_mb=float(os.getenv("ENERGY_PER_MB", DEFAULT_ENERGY_PER_MB)),
    )
    state = ServiceState(config=config)

    class Handler(BaseHTTPRequestHandler):
        server_version = "c7-sample-service/1.0"

        def _send(self, status: int, body: bytes, content_type: str = "application/json") -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, payload: dict) -> None:
            self._send(status, json.dumps(payload).encode("utf-8"))

        def _route(self) -> str:
            return urlparse(self.path).path.rstrip("/") or "/"

        def _error_body(self, code: str, message: str, payload_class: str = "unknown") -> dict:
            return {
                "service": config.name,
                "accepted": False,
                "payload_class": payload_class,
                "error": {"code": code, "message": message},
                "duration_ms": ERROR_LATENCY_MS,
            }

        def _drain_body(self, length: int) -> None:
            remaining = min(length, MAX_BODY_BYTES + 1)
            while remaining > 0:
                chunk = self.rfile.read(min(8192, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)

        def _not_found(self) -> None:
            _record_result(state, "404", "not_found", ERROR_LATENCY_MS, 0)
            self._json(404, self._error_body("not_found", "route not found"))

        def do_GET(self) -> None:
            route = self._route()
            if route == "/":
                self._json(
                    200,
                    {
                        "service": config.name,
                        "function": config.function_name,
                        "version": config.version,
                        "routes": list(ROUTES),
                    },
                )
                return
            if route == "/health":
                with state.lock:
                    cold_start = not state.warm
                    uptime = time.monotonic() - state.started
                self._json(
                    200,
                    {
                        "status": "ok",
                        "service": config.name,
                        "version": config.version,
                        "uptime_s": round(max(uptime, 0.0), 3),
                        "cold_start": cold_start,
                    },
                )
                return
            if route == "/ready":
                self._json(200, {"status": "ready", "service": config.name, "version": config.version})
                return
            if route == "/metrics":
                self._send(
                    200,
                    _metrics_text(state).encode("utf-8"),
                    "text/plain; version=0.0.4; charset=utf-8",
                )
                return
            self._not_found()

        def do_POST(self) -> None:
            if self._route() != "/invoke":
                self._not_found()
                return

            raw_length = self.headers.get("Content-Length", "0")
            try:
                length = int(raw_length or 0)
                if length < 0:
                    raise ValueError
            except ValueError:
                _record_result(state, "400", "invalid_payload", ERROR_LATENCY_MS, 0)
                self._json(400, self._error_body("invalid_payload", "invalid Content-Length"))
                return

            if length > MAX_BODY_BYTES:
                self._drain_body(length)
                self.close_connection = True
                _record_result(state, "400", "payload_too_large", ERROR_LATENCY_MS, 0)
                self._json(400, self._error_body("payload_too_large", "payload exceeds 1 MiB"))
                return

            raw = self.rfile.read(length) if length else b"{}"
            payload_class = "unknown"
            code = "500"
            reason: str | None = "server_error"
            try:
                try:
                    payload = json.loads(raw.decode("utf-8") or "{}")
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise PayloadError("invalid_json", "request body is not valid JSON") from exc
                if not isinstance(payload, dict):
                    raise PayloadError("invalid_payload", "request body must be a JSON object")

                payload_class = str(payload.get("payload_class", "small"))
                if payload_class not in PAYLOAD_CLASSES:
                    raise PayloadError("invalid_payload_class", "unknown payload_class")

                is_cold = _begin_invocation(state)
                result_key, result = RESULT_BUILDERS[name](payload)
                duration_ms = LATENCY_PROFILE_MS[name][payload_class]
                if is_cold:
                    duration_ms += COLD_START_PENALTY_MS
                code = "200"
                reason = None
                body = {
                    "service": name,
                    "accepted": True,
                    "payload_class": payload_class,
                    "duration_ms": duration_ms,
                    result_key: result,
                }
            except PayloadError as exc:
                code = "400"
                reason = exc.code
                body = self._error_body(exc.code, exc.message, payload_class)
            except Exception:
                body = self._error_body("server_error", "invocation failed", payload_class)

            _record_result(state, code, reason, ERROR_LATENCY_MS if reason else duration_ms, len(raw))
            self._json(400 if code == "400" else 500 if code == "500" else 200, body)

        def log_message(self, _format: str, *_args) -> None:
            return

    Handler.service_state = state
    Handler.service_config = config
    return Handler


Handler = create_app()


def main() -> None:
    port = int(os.getenv("SERVICE_PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    server.daemon_threads = True
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
