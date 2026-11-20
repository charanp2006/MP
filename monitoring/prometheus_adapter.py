"""Prometheus metrics adapter for the execution/monitoring boundary (M6)."""

from __future__ import annotations

import json
from typing import Callable, Dict, Optional
from urllib.parse import urlencode
from urllib.request import urlopen

DEFAULT_QUERIES = {
    "p95_latency_ms": "histogram_quantile(0.95, sum(rate(fn_latency_ms_bucket[5m])) by (le))",
    "current_workload": "sum(rate(fn_invocations_total[5m])) * 60",
    "cold_starts": "sum(increase(fn_cold_starts_total[5m]))",
    "energy_w": "sum(fn_energy_w)",
    "active_containers": "sum(kube_deployment_status_replicas)",
}


class PrometheusMetricsAdapter:
    """Read validated scalar metrics from Prometheus or an injected query function."""

    def __init__(self, config: Optional[Dict] = None, query_fn: Optional[Callable[[str], Dict]] = None) -> None:
        config = config or {}
        prometheus = config.get("monitoring", {}).get("prometheus", {})
        self.enabled = bool(prometheus.get("adapter_enabled", False))
        self.host = str(prometheus.get("host", "127.0.0.1"))
        self.port = int(prometheus.get("port", 9090))
        self.timeout_s = float(prometheus.get("timeout_s", 5))
        self.queries = dict(DEFAULT_QUERIES)
        self.queries.update(prometheus.get("queries", {}) or {})
        self.query_fn = query_fn
        self.last_errors: Dict[str, str] = {}

    def query_scalar(self, name: str) -> Optional[float]:
        if not self.enabled:
            return None
        expression = self.queries.get(name)
        if not expression:
            self.last_errors[name] = "missing_query"
            return None
        try:
            if self.query_fn is not None:
                payload = self.query_fn(expression)
            else:
                url = f"http://{self.host}:{self.port}/api/v1/query?{urlencode({'query': expression})}"
                with urlopen(url, timeout=self.timeout_s) as response:
                    payload = json.loads(response.read().decode("utf-8"))
            results = payload.get("data", {}).get("result", [])
            if not results:
                self.last_errors[name] = "empty_result"
                return None
            return float(results[0]["value"][1])
        except Exception as exc:
            self.last_errors[name] = f"{type(exc).__name__}: {exc}"[:300]
            return None

    def fetch(self) -> Dict:
        values = {name: self.query_scalar(name) for name in self.queries}
        metrics: Dict = {
            "source": "prometheus" if self.enabled else "disabled",
            "stale": False,
            "last_errors": dict(self.last_errors),
        }
        mapping = {
            "current_workload": "current_workload",
            "p95_latency_ms": "p95_latency_ms",
            "cold_starts": "cold_starts",
            "energy_w": "energy",
            "active_containers": "active_containers",
        }
        for query_name, metric_name in mapping.items():
            value = values.get(query_name)
            if value is not None:
                metrics[metric_name] = value
        required = ["current_workload", "p95_latency_ms"]
        if self.enabled and any(name not in metrics for name in required):
            metrics["stale"] = True
        return metrics
