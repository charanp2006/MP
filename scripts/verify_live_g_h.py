from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from configs import load_config
from monitoring.prometheus_adapter import PrometheusMetricsAdapter


def _http_json(url: str, timeout: float = 5.0, headers: Optional[Dict[str, str]] = None) -> Dict:
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _http_text(url: str, timeout: float = 5.0, headers: Optional[Dict[str, str]] = None) -> str:
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def _kubectl(args: list[str]) -> str:
    result = subprocess.run(
        ["kubectl", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip()[:300])
    return result.stdout.strip()


def _check_http(url: str, timeout: float = 5.0) -> bool:
    try:
        _http_text(url, timeout)
        return True
    except Exception:
        return False


def _retry_http_text(url: str, attempts: int = 10, delay_s: float = 2.0, headers: Optional[Dict[str, str]] = None) -> str:
    last = None
    for _ in range(attempts):
        try:
            return _http_text(url, headers=headers)
        except Exception as exc:
            last = exc
            time.sleep(delay_s)
    raise RuntimeError(f"unreachable after retries: {url}: {last}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify live Phase G/H deployment")
    parser.add_argument("--config", default="configs/local-live.yaml")
    parser.add_argument("--gateway", default="http://127.0.0.1:8080")
    parser.add_argument("--prometheus", default="http://127.0.0.1:9090")
    parser.add_argument("--grafana", default="http://127.0.0.1:3000")
    parser.add_argument("--exporter", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    config = load_config(args.config)
    report: Dict[str, object] = {
        "config": {
            "execution_backend": config["execution"]["backend"],
            "enabled": config["execution"]["enabled"],
            "dry_run": config["execution"]["dry_run"],
            "allow_live": config["execution"]["allow_live"],
            "metrics_source": config["monitoring"]["feedback"]["source"],
        },
        "checks": {},
    }

    checks = report["checks"]
    try:
        checks["node_ready"] = "Ready" in _kubectl(["get", "nodes"])
    except Exception as exc:
        checks["node_ready"] = str(exc)

    namespaces = {"serverless-mgmt", "openfaas", "openfaas-fn", "monitoring"}
    try:
        existing = set(_kubectl(["get", "ns", "-o", "jsonpath={.items[*].metadata.name}"]).split())
        checks["namespaces"] = sorted(namespaces & existing)
    except Exception as exc:
        checks["namespaces"] = str(exc)

    try:
        pods = _kubectl(["get", "pods", "-A", "--no-headers"])
        checks["live_pods"] = [line.split()[1] for line in pods.splitlines() if any(name in line for name in ("fn-checkout", "gateway-", "prometheus-", "grafana-", "control-loop-exporter"))]
    except Exception as exc:
        checks["live_pods"] = str(exc)

    checks["gateway_health"] = _check_http(f"{args.gateway}/healthz")
    checks["exporter_health"] = _check_http(f"{args.exporter}/health")
    checks["prometheus_ready"] = _check_http(f"{args.prometheus}/-/ready")
    checks["grafana_health"] = _check_http(f"{args.grafana}/api/health")

    try:
        adapter = PrometheusMetricsAdapter(config)
        adapter.port = int(args.prometheus.rsplit(":", 1)[-1])
        adapter.host = args.prometheus.split("://", 1)[-1].split(":", 1)[0]
        checks["prometheus_metrics"] = adapter.fetch()
    except Exception as exc:
        checks["prometheus_metrics"] = str(exc)

    token = base64.b64encode(b"admin:admin").decode("ascii")
    try:
        encoded_password = _kubectl(["-n", "openfaas", "get", "secret", "basic-auth", "-o", "jsonpath={.data.basic-auth-password}"])
        gateway_password = base64.b64decode(encoded_password).decode("utf-8")
        gw_token = base64.b64encode(f"admin:{gateway_password}".encode("utf-8")).decode("ascii")
        gateway_headers = {"Authorization": f"Basic {gw_token}"}
    except Exception:
        gateway_headers = {}
    try:
        dashboard = _http_json(
            f"{args.grafana}/api/dashboards/uid/control-loop-live",
            headers={"Authorization": f"Basic {token}"},
        )
        checks["dashboard_uid"] = dashboard.get("dashboard", {}).get("uid")
    except Exception as exc:
        checks["dashboard_uid"] = str(exc)

    try:
        payload = _retry_http_text(f"{args.gateway}/function/fn-checkout?probe=verify", headers=gateway_headers)
        checks["function_invoke"] = json.loads(payload).get("message")
    except Exception as exc:
        checks["function_invoke"] = str(exc)

    expected_true = [
        checks["node_ready"],
        checks["gateway_health"],
        checks["exporter_health"],
        checks["prometheus_ready"],
        checks["grafana_health"],
    ]
    passed = all(value is True for value in expected_true) and checks["dashboard_uid"] == "control-loop-live"
    report["passed"] = bool(passed)
    print(json.dumps(report, indent=2, default=str))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
