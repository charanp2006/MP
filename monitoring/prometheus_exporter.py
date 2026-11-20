"""Prometheus text exporter and health endpoints for the monitoring stack."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional

from monitoring.metrics import MetricsCollector, export_prometheus_text
from monitoring.prometheus_adapter import PrometheusMetricsAdapter


class Handler(BaseHTTPRequestHandler):
    collector: MetricsCollector = MetricsCollector({"monitoring": {"enabled": True}})
    adapter: Optional[PrometheusMetricsAdapter] = None

    def do_GET(self) -> None:
        if self.path.startswith("/metrics"):
            body = export_prometheus_text(self.collector.snapshot()).encode("utf-8")
            self._send(200, body, "text/plain; version=0.0.4")
        elif self.path.startswith("/health"):
            body = json.dumps(
                {"status": "ok", "metrics": len(self.collector.snapshot())}, sort_keys=True
            ).encode("utf-8")
            self._send(200, body, "application/json")
        elif self.path.startswith("/ready"):
            metrics = self.adapter.fetch() if self.adapter is not None else {"stale": False}
            stale = bool(metrics.get("stale", False))
            body = json.dumps({"ready": not stale, "stale": stale}, sort_keys=True).encode("utf-8")
            self._send(503 if stale else 200, body, "application/json")
        else:
            self._send(404, b"not found", "text/plain")

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        return


def create_handler(collector: MetricsCollector, adapter: Optional[PrometheusMetricsAdapter] = None):
    class _Handler(Handler):
        pass

    _Handler.collector = collector
    _Handler.adapter = adapter
    return _Handler


def main() -> None:
    parser = argparse.ArgumentParser(description="Prometheus exporter for the decision loop")
    parser.add_argument("--config", default=None)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args()

    config = None
    if args.config:
        from configs import load_config

        config = load_config(args.config)

    config = config or {}
    monitoring = config.get("monitoring", {})
    collector = MetricsCollector(config)
    adapter = PrometheusMetricsAdapter(config) if monitoring.get("prometheus", {}).get("adapter_enabled") else None
    port = args.port or int(monitoring.get("prometheus", {}).get("exporter_port", 8000))
    server = ThreadingHTTPServer((args.host, port), create_handler(collector, adapter))
    print(json.dumps({"metrics": f"http://{args.host}:{port}/metrics", "health": f"http://{args.host}:{port}/health", "ready": f"http://{args.host}:{port}/ready"}))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
