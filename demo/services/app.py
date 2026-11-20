from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SERVICE_NAME = os.getenv("SERVICE_NAME", "fn_sample")
PAYLOAD_CLASSES = ("small", "medium", "large")


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path.startswith("/health"):
            self._send(200, {"status": "ok", "service": SERVICE_NAME})
            return
        self._send(200, {"service": SERVICE_NAME, "routes": ["/", "/health", "/invoke"]})

    def do_POST(self) -> None:
        if not self.path.startswith("/invoke"):
            self._send(404, {"error": "not_found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid_json"})
            return
        payload_class = str(payload.get("payload_class", "small"))
        self._send(
            200,
            {
                "service": SERVICE_NAME,
                "accepted": True,
                "payload_class": payload_class if payload_class in PAYLOAD_CLASSES else "small",
            },
        )

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    port = int(os.getenv("SERVICE_PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
