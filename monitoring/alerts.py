"""Local alert evaluation for monitoring and reliability failure tests."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_RULES = {
    "p95_near_sla": {"enabled": True, "severity": "warning"},
    "sla_violation_rate": {"enabled": True, "severity": "critical", "threshold": 0.1},
    "stale_metrics": {"enabled": True, "severity": "warning"},
    "executor_failure": {"enabled": True, "severity": "critical"},
    "feedback_degradation": {"enabled": True, "severity": "warning"},
}


class AlertManager:
    """Evaluate bounded, deterministic alerts from local cycle evidence."""

    def __init__(self, config: Optional[Dict] = None) -> None:
        config = config or {}
        monitoring = config.get("monitoring", {})
        alerts = monitoring.get("alerts", {})
        self.enabled = bool(alerts.get("enabled", False))
        self.log_enabled = bool(alerts.get("log_enabled", True))
        self.log_path = str(alerts.get("log_path", "results/monitoring/alerts.jsonl"))
        self.sla_threshold = float(config.get("sla", {}).get("p95_latency_ms", 250))
        self.safety_margin = float(config.get("sla", {}).get("safety_margin_ms", 20))
        self.rules = {}
        for name, defaults in DEFAULT_RULES.items():
            rule = dict(defaults)
            rule.update((alerts.get("rules", {}) or {}).get(name, {}))
            self.rules[name] = rule

    def evaluate(
        self,
        metrics: Optional[Dict] = None,
        feedback: Optional[Dict] = None,
        execution: Optional[Dict] = None,
        correlation_id: str = "",
    ) -> List[Dict]:
        if not self.enabled:
            return []
        metrics = metrics or {}
        feedback = feedback or {}
        execution = execution or {}
        alerts: List[Dict] = []
        now = datetime.now(timezone.utc).isoformat()

        p95 = metrics.get("p95_latency_ms")
        threshold = self.sla_threshold - self.safety_margin
        if p95 is not None and float(p95) >= threshold:
            alerts.append(self._alert("p95_near_sla", now, float(p95), threshold, correlation_id))

        violation_rate = feedback.get("violation_rate")
        rule_threshold = float(self.rules["sla_violation_rate"]["threshold"])
        if violation_rate is not None and float(violation_rate) >= rule_threshold:
            alerts.append(
                self._alert("sla_violation_rate", now, float(violation_rate), rule_threshold, correlation_id)
            )

        if metrics.get("stale"):
            alerts.append(self._alert("stale_metrics", now, 1.0, 0.0, correlation_id))

        if execution and (not execution.get("ok", False) or str(execution.get("code", "")) in {
            "execution_failed",
            "unauthorized",
            "invalid_action",
        }):
            alerts.append(self._alert("executor_failure", now, 1.0, 0.0, correlation_id))

        if float(feedback.get("caution", 0.0)) >= 1.0:
            alerts.append(self._alert("feedback_degradation", now, float(feedback["caution"]), 1.0, correlation_id))

        return alerts

    def log(self, alerts: List[Dict]) -> Optional[str]:
        if not self.log_enabled or not alerts:
            return None
        path = Path(self.log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            for alert in alerts:
                handle.write(json.dumps(alert, sort_keys=True) + "\n")
        return str(path)

    def read_alerts(self) -> List[Dict]:
        path = Path(self.log_path)
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

    def _alert(self, name: str, now: str, value: float, threshold: float, correlation_id: str) -> Dict:
        rule = self.rules[name]
        return {
            "name": name,
            "severity": str(rule.get("severity", "warning")),
            "value": float(value),
            "threshold": float(threshold),
            "correlation_id": str(correlation_id),
            "message": f"{name}: value={value:.6g} threshold={threshold:.6g}",
            "raised_at": now,
        }
