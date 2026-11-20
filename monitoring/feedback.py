"""Feedback loop (P5) — runtime metrics feed back to planning/control.

Computes a simple feedback signal from recent metrics to influence planning
caution (e.g. push toward SLA-safe strategies when violations are rising).
Keeps the loop bounded and safe; disabled or used as a soft hint only.
"""

from __future__ import annotations

import json
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class FeedbackLoop:
    def __init__(self, config: Optional[Dict] = None) -> None:
        cfg = (config or {}).get("monitoring", {}).get("feedback", {})
        self.enabled = bool(cfg.get("enabled", True))
        self.window = int(cfg.get("window", 10))
        self.degrade_threshold = float(cfg.get("degrade_threshold", 0.2))
        self.min_samples = int(cfg.get("min_samples", 5))
        self.record_enabled = bool(cfg.get("record_enabled", False))
        self.record_path = str(cfg.get("record_path", "results/monitoring/feedback.jsonl"))
        self.source = str(cfg.get("source", "simulated"))
        self.last_record_path: Optional[str] = None
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

    def record_cycle(
        self,
        correlation_id: str,
        outcome: Dict,
        metadata: Optional[Dict] = None,
    ) -> Optional[str]:
        metadata = metadata or {}
        p95 = float(outcome.get("p95_latency_ms", outcome.get("p95_latency", 0.0)))
        violated = bool(outcome.get("sla_violated", False))
        cold_starts = float(outcome.get("cold_starts", 0.0))
        self.record(p95, violated, cold_starts)
        signal = self.signal()
        record = {
            "correlation_id": str(correlation_id),
            "source": str(metadata.get("source", self.source)),
            "forecast_source": str(metadata.get("forecast_source", "")),
            "final_action": str(metadata.get("final_action", "")),
            "p95_latency_ms": p95,
            "sla_violated": violated,
            "cold_starts": cold_starts,
            "energy_w": float(outcome.get("energy_w", outcome.get("energy", 0.0))),
            "capacity": int(outcome.get("capacity", 0)),
            "reward": float(outcome.get("reward", 0.0)),
            "feedback_signal": signal,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        self.last_record_path = self._append(record)
        return self.last_record_path

    def read_records(self) -> list[Dict]:
        path = Path(self.record_path)
        if not path.exists():
            return []
        records = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            value = json.loads(line)
            if isinstance(value, dict):
                records.append(value)
        return records

    def _append(self, record: Dict) -> Optional[str]:
        if not self.record_enabled:
            return None
        path = Path(self.record_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(self._safe(record), sort_keys=True) + "\n")
        return str(path)

    @classmethod
    def _safe(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {str(k): cls._safe(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [cls._safe(v) for v in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value if not isinstance(value, str) else value[:500]
        return str(value)[:500]
