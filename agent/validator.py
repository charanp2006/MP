"""Plan validation (architecture Layer 6, docs/design.md section 9).

Planner output is untrusted. This validator enforces the schema, the approved
strategy set, directional consistency and capacity/rate bounds before PPO sees
the plan. It does not execute anything.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Union

from pydantic import ValidationError

from agent.schemas import STRATEGIES, Plan, StateSnapshot

_REDUCING = {"ScaleIn", "Terminate"}
_INCREASING = {"ScaleOut", "Reuse"}


@dataclass
class PlanValidation:
    ok: bool
    code: str
    reason: str
    plan: Optional[Plan] = None


class PlanValidator:
    def __init__(self, config: Optional[Dict] = None) -> None:
        config = config or {}
        containers = config.get("containers", {})
        self.min_capacity = int(containers.get("min", 2))
        self.max_capacity = int(containers.get("max", 30))
        self.max_change = max(1, int(containers.get("max_change_per_cycle", 5)))

    def validate(
        self,
        plan: Union[Plan, Dict],
        state: Union[StateSnapshot, Dict],
        allowed: Optional[set] = None,
    ) -> PlanValidation:
        if not isinstance(state, StateSnapshot):
            try:
                state = StateSnapshot.model_validate(state)
            except ValidationError as exc:
                return PlanValidation(False, "state_schema", f"invalid state: {exc.errors()[0]['msg']}")

        if not isinstance(plan, Plan):
            try:
                plan = Plan.model_validate(plan)
            except ValidationError as exc:
                return PlanValidation(False, "schema", f"invalid plan: {exc.errors()[0]['msg']}")

        approved = set(allowed or STRATEGIES)
        if plan.strategy not in approved:
            return PlanValidation(False, "unknown_strategy", f"strategy {plan.strategy!r} is not approved", plan)

        if not plan.constraints_respected:
            return PlanValidation(False, "constraints", "planner reported constraints_respected=false", plan)

        change = int(plan.desired_capacity_change)
        if abs(change) > self.max_change:
            return PlanValidation(
                False, "rate_limit", f"change {change} exceeds max {self.max_change} per cycle", plan
            )

        if plan.strategy in _REDUCING and change > 0:
            return PlanValidation(False, "direction", f"{plan.strategy} cannot increase capacity", plan)
        if plan.strategy in _INCREASING and change < 0:
            return PlanValidation(False, "direction", f"{plan.strategy} cannot reduce capacity", plan)
        if plan.strategy == "NoOp" and change != 0:
            return PlanValidation(False, "direction", "NoOp must not change capacity", plan)

        if plan.strategy in _REDUCING:
            target = state.active_containers + change
            if target < self.min_capacity:
                return PlanValidation(
                    False,
                    "capacity_min",
                    f"target {target} is below min {self.min_capacity}",
                    plan,
                )
        elif plan.strategy in _INCREASING:
            target = state.active_containers + change
            if target > self.max_capacity:
                return PlanValidation(
                    False,
                    "capacity_max",
                    f"target {target} is above max {self.max_capacity}",
                    plan,
                )

        return PlanValidation(True, "ok", f"{plan.strategy} accepted", plan)

    def validate_or_noop(self, plan: Union[Plan, Dict], state: StateSnapshot) -> PlanValidation:
        """Return a validation result, always with a safe NoOp plan on failure."""
        result = self.validate(plan, state)
        if result.ok:
            return result
        noop = Plan(
            strategy="NoOp",
            desired_capacity_change=0,
            priority="balanced",
            urgency="low",
            reason=f"fallback: {result.code}",
            constraints_respected=True,
        )
        return PlanValidation(False, result.code, result.reason, noop)
