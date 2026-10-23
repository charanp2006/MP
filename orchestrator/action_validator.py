"""Action validation (architecture Layer 9, docs/design.md section 13).

Checks that a PPO action is known, authorized and consistent with the validated
plan, then clamps the resulting capacity to the configured bounds. It never
executes platform operations (that is P4).
"""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral
from typing import Dict, Optional, Union

from agent.schemas import Plan, StateSnapshot
from rl.environment import (
    ACTIONS,
    NOOP,
    PREWARM,
    REUSE,
    SCALE_IN,
    SCALE_OUT,
    TERMINATE,
)


@dataclass
class ActionValidation:
    ok: bool
    code: str
    reason: str
    action: int
    action_name: str
    target_capacity: int


class ActionValidator:
    def __init__(self, config: Optional[Dict] = None) -> None:
        containers = (config or {}).get("containers", {})
        self.min_capacity = int(containers.get("min", 2))
        self.max_capacity = int(containers.get("max", 30))
        self.max_change = max(1, int(containers.get("max_change_per_cycle", 5)))

    def capacity_after(self, current_capacity: int, action: int) -> int:
        delta = {
            NOOP: 0,
            PREWARM: 0,
            SCALE_OUT: self.max_change,
            REUSE: self.max_change,
            SCALE_IN: -self.max_change,
            TERMINATE: -self.max_change,
        }[int(action)]
        return min(max(int(current_capacity) + delta, self.min_capacity), self.max_capacity)

    def validate(
        self,
        action: Union[int, Integral],
        state: StateSnapshot,
        authorized: bool = True,
        plan: Optional[Union[Plan, Dict]] = None,
    ) -> ActionValidation:
        if isinstance(action, bool) or not isinstance(action, Integral):
            return ActionValidation(False, "types", "action must be an integer", NOOP, ACTIONS[NOOP], state.active_containers)

        action = int(action)
        if action not in range(len(ACTIONS)):
            return ActionValidation(
                False, "unknown_action", f"action {action} is not in the canonical set", NOOP, ACTIONS[NOOP], state.active_containers
            )

        name = ACTIONS[action]
        target = self.capacity_after(state.active_containers, action)

        if not authorized:
            return ActionValidation(
                False, "unauthorized", "executor authorization missing", NOOP, ACTIONS[NOOP], target
            )

        if plan is not None:
            if not isinstance(plan, Plan):
                try:
                    plan = Plan.model_validate(plan)
                except Exception:
                    plan = None
            if plan is not None and plan.urgency == "high":
                if plan.strategy in {"ScaleOut", "PreWarm"} and name in {"ScaleIn", "Terminate"}:
                    return ActionValidation(
                        False,
                        "plan_conflict",
                        f"{name} contradicts the high-urgency {plan.strategy} plan",
                        NOOP,
                        ACTIONS[NOOP],
                        target,
                    )
                if plan.strategy in {"ScaleIn", "Terminate"} and name in {"ScaleOut", "PreWarm", "Reuse"}:
                    return ActionValidation(
                        False,
                        "plan_conflict",
                        f"{name} contradicts the high-urgency {plan.strategy} plan",
                        NOOP,
                        ACTIONS[NOOP],
                        target,
                    )

        return ActionValidation(True, "ok", f"{name} is authorized and bounded", action, name, target)
