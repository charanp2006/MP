"""Unified safety shield for learned or rule-based control actions.

The shield is deliberately independent of policy training: every proposed action
passes action validation, authorization, high-urgency plan consistency and the
SLA guard before it reaches the simulator or executor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from agent.schemas import Plan, StateSnapshot
from orchestrator.action_validator import ActionValidator
from orchestrator.sla_guard import SLAGuard
from orchestrator.state_builder import build_state
from rl.environment import ACTIONS, NOOP


@dataclass
class ShieldDecision:
    proposed_action: int
    action: int
    action_name: str
    allowed: bool
    codes: List[str]
    reasons: List[str]
    target_capacity: int

    def to_dict(self) -> Dict:
        return {
            "proposed_action": int(self.proposed_action),
            "proposed_action_name": ACTIONS[self.proposed_action]
            if self.proposed_action in range(len(ACTIONS))
            else "unknown",
            "action": int(self.action),
            "action_name": self.action_name,
            "allowed": bool(self.allowed),
            "codes": list(self.codes),
            "reasons": list(self.reasons),
            "target_capacity": int(self.target_capacity),
        }


class SafetyShield:
    """Apply action validation followed by the deterministic SLA guard."""

    def __init__(
        self,
        config: Optional[Dict] = None,
        validator: Optional[ActionValidator] = None,
        guard: Optional[SLAGuard] = None,
    ) -> None:
        self.config = config or {}
        self.validator = validator or ActionValidator(self.config)
        self.guard = guard or SLAGuard(self.config)

    def filter(
        self,
        action: int,
        state: StateSnapshot,
        authorized: bool = True,
        plan: Optional[Union[Plan, Dict]] = None,
        p95_latency_ms: Optional[float] = None,
    ) -> ShieldDecision:
        proposed = int(action) if isinstance(action, (int, float)) else NOOP
        validation = self.validator.validate(
            proposed, state, authorized=authorized, plan=plan
        )
        candidate = validation.action if validation.ok else NOOP
        p95 = state.p95_latency_ms if p95_latency_ms is None else float(p95_latency_ms)
        guarded = self.guard.check(candidate, p95)
        final = guarded.action if guarded.allow else NOOP
        final = int(final) if final in range(len(ACTIONS)) else NOOP

        codes = [validation.code]
        reasons = [validation.reason]
        if not guarded.allow:
            codes.append(guarded.code)
            reasons.append(guarded.reason)

        return ShieldDecision(
            proposed_action=proposed,
            action=final,
            action_name=ACTIONS[final],
            allowed=final == proposed,
            codes=codes,
            reasons=reasons,
            target_capacity=validation.target_capacity if final != NOOP else state.active_containers,
        )

    def from_env(
        self,
        env,
        action: int,
        authorized: bool = True,
        plan: Optional[Union[Plan, Dict]] = None,
    ) -> ShieldDecision:
        """Build a validated state from the simulator before filtering an action."""
        forecast, metrics = env.current_context()
        state = build_state(forecast, metrics, self.config)
        return self.filter(
            action,
            state,
            authorized=authorized,
            plan=plan,
            p95_latency_ms=metrics["p95_latency_ms"],
        )
