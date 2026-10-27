"""Feedback loop (P5) — runtime metrics feed back to planning/control.

Computes a simple feedback signal from recent metrics to influence planning
caution (e.g. push toward SLA-safe strategies when violations are rising).
Keeps the loop bounded and safe; disabled or used as a soft hint only.
"""

from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional


class FeedbackLoop:
    def __init__(self, config: Optional[Dict] = None) -> None:
        cfg = (config or {}).get("monitoring", {}).get("feedback", {})
        self.enabled = bool(cfg.get("enabled", True))
        self.window = int(cfg.get("window", 10))
        self.degrade_threshold = float(cfg.get("degrade_threshold", 0.2))
        self.min_samples = int(cfg.get("min_samples", 5))
        self._p95: deque[float] = deque(maxlen=self.window)
        self._violations: deque[float] = deque(maxlen=self.window)
        self._cold: deque[float] = deque(maxlen=self.window)

    def record(self, p95_latency_ms: float, sla_violated: bool, cold_starts: float) -> None:
        self._p95.append(float(p95_latency_ms))
        self._violations.append(1.0 if sla_violated else 0.0)
        self._cold.append(float(cold_starts))

    def signal(self) -> Dict[str, float]:
        if not self.enabled or len(self._p95) < self.min_samples:
            return {"caution": 0.0, "violation_rate": 0.0, "p95_trend": 0.0}
        recent_p95 = list(self._p95)[-self.window :]
        recent_v = list(self._violations)[-self.window :]
        first_half = sum(recent_p95[: len(recent_p95) // 2]) / max(len(recent_p95) // 2, 1)
        second_half = sum(recent_p95[len(recent_p95) // 2 :]) / max(len(recent_p95) - len(recent_p95) // 2, 1)
        trend = (second_half - first_half) / max(first_half, 1.0)
        v_rate = sum(recent_v) / len(recent_v)
        caution = 1.0 if (trend >= self.degrade_threshold or v_rate >= 0.1) else 0.0
        return {"caution": float(caution), "violation_rate": float(v_rate), "p95_trend": float(trend)}
