"""Deterministic SLA guard (architecture Layer 8, docs/design.md section 14).

Independent of the learned policy: capacity reductions are blocked while the
observed P95 latency is inside the configured safety margin of the SLA.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from rl.environment import ACTIONS, NOOP


@dataclass
class GuardDecision:
    allow: bool
    code: str
    reason: str
    action: int


class SLAGuard:
    def __init__(self, config: Optional[Dict] = None) -> None:
        sla = (config or {}).get("sla", {})
        self.threshold_ms = float(sla.get("p95_latency_ms", 250.0))
        self.safety_margin_ms = float(sla.get("safety_margin_ms", 0.0))

    def check(self, action: int, p95_latency_ms: float) -> GuardDecision:
        action = int(action)
        if action not in range(len(ACTIONS)):
            return GuardDecision(False, "unknown_action", f"unknown action {action}", NOOP)

        name = ACTIONS[action]
        p95 = float(p95_latency_ms)
        if name in {"ScaleIn", "Terminate"} and p95 >= self.threshold_ms - self.safety_margin_ms:
            return GuardDecision(
                False,
                "sla_guard",
                f"blocked {name}: P95 {p95:.1f} ms is within {self.safety_margin_ms:.1f} ms "
                f"of the {self.threshold_ms:.1f} ms SLA",
                NOOP,
            )

        return GuardDecision(True, "ok", f"{name} is SLA-safe", action)
