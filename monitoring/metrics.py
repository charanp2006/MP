"""Prometheus-style metrics collector (P5, docs/architecture.md monitoring).

Provides in-memory counters/gauges/histograms and helpers to emit/collect
runtime metrics for the control loop. Disabled by default; safe to import in
tests/simulations.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class MetricPoint:
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class MetricsCollector:
    def __init__(self, config: Optional[Dict] = None) -> None:
        cfg = (config or {}).get("monitoring", {})
        self.enabled = bool(cfg.get("enabled", False))
        self.history_size = int(cfg.get("metrics", {}).get("history_size", 1000))
        self._history: deque[MetricPoint] = deque(maxlen=self.history_size)
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}

    def inc(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        key = self._key(name, labels)
        self._counters[key] = self._counters.get(key, 0.0) + float(value)
        self._history.append(MetricPoint(name, self._counters[key], labels or {}, time.time()))

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        key = self._key(name, labels)
        self._gauges[key] = float(value)
        self._history.append(MetricPoint(name, self._gauges[key], labels or {}, time.time()))

    def observe(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        self.set_gauge(name, value, labels)

    def snapshot(self) -> Dict[str, float]:
        snap = dict(self._counters)
        snap.update(self._gauges)
        return snap

    def recent(self, n: int = 10) -> List[MetricPoint]:
        items = list(self._history)
        return items[-n:]

    @staticmethod
    def _escape_label(value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

    @staticmethod
    def _key(name: str, labels: Optional[Dict[str, str]]) -> str:
        if not labels:
            return name
        parts = []
        for k in sorted(labels):
            parts.append(f'{k}="{MetricsCollector._escape_label(str(labels[k]))}"')
        return f"{name}{{{','.join(parts)}}}"


    def record_step(self, info: Dict, final_action_name: str) -> None:
        if not self.enabled:
            return
        self.set_gauge("containers_active", float(info.get("capacity", 0)))
        self.set_gauge("p95_latency_ms", float(info.get("p95_latency", 0.0)))
        self.set_gauge("latency_ms", float(info.get("latency", 0.0)))
        self.set_gauge("energy_w", float(info.get("energy", 0.0)))
        self.set_gauge("cold_starts", float(info.get("cold_starts", 0.0)))
        self.set_gauge("workload", float(info.get("workload", 0.0)))
        if info.get("sla_violated"):
            self.inc("sla_violations_total")
        self.inc("action_selected_total", 1.0, {"action": final_action_name})


def export_prometheus_text(snapshot: Dict[str, float]) -> str:
    lines = []
    for key, value in sorted(snapshot.items()):
        lines.append(f"{key} {value}")
    return "\n".join(lines) + "\n"
