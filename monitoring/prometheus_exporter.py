"""Minimal Prometheus text exporter HTTP server (scaffold for live monitoring).

Exposes /metrics from an in-memory MetricsCollector snapshot. Safe to run
locally; does not require a cluster. Prometheus can scrape this endpoint when
enabled/configured.
"""
from __future__ import annotations
import argparse, json
from http.server import BaseHTTPRequestHandler, HTTPServer
from monitoring.metrics import MetricsCollector, export_prometheus_text

class Handler(BaseHTTPRequestHandler):
    collector: MetricsCollector = MetricsCollector({"monitoring":{"enabled":True}})
    def do_GET(self):
        if self.path.startswith('/metrics'):
            body = export_prometheus_text(self.collector.snapshot()).encode('utf-8')
            self.send_response(200); self.send_header('Content-Type','text/plain; version=0.0.4'); self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
        elif self.path.startswith('/health'):
            body=b'ok'; self.send_response(200); self.end_headers(); self.wfile.write(body)
        else:
            self.send_response(404); self.end_headers()
    def log_message(self, format, *args):
        return

def main():
    p=argparse.ArgumentParser(); p.add_argument('--host', default='127.0.0.1'); p.add_argument('--port', type=int, default=8000)
    a=p.parse_args()
    print(json.dumps({'listening': f'http://{a.host}:{a.port}/metrics', 'note':'scaffold; wire to live collector/feedback in deployment'}))
    HTTPServer((a.host,a.port), Handler).serve_forever()

if __name__=='__main__': main()
