"""Decision orchestration (architecture Layers 4, 8, 9 and the control wiring).

* ``state_builder``    --- combine forecast + observation into a state snapshot.
* ``sla_guard``       --- deterministic protection against risky reductions.
* ``action_validator``--- known/authorized/plan-consistent, bounded actions.
* ``decision_loop``   --- planner -> validator -> PPO -> guard integration.

Execution against Kubernetes/OpenFaaS is P4; this package is simulation-only.
Exports are lazy so ``python -m orchestrator.decision_loop`` does not import the
module twice.
"""

from __future__ import annotations

import importlib
from typing import Any, Dict, Tuple

__all__ = [
    "build_state",
    "metrics_from_step",
    "SLAGuard",
    "GuardDecision",
    "ActionValidator",
    "ActionValidation",
    "DecisionLoop",
    "Decision",
    "run_episode",
]

_EXPORTS: Dict[str, Tuple[str, str]] = {
    "build_state": ("orchestrator.state_builder", "build_state"),
    "metrics_from_step": ("orchestrator.state_builder", "metrics_from_step"),
    "SLAGuard": ("orchestrator.sla_guard", "SLAGuard"),
    "GuardDecision": ("orchestrator.sla_guard", "GuardDecision"),
    "ActionValidator": ("orchestrator.action_validator", "ActionValidator"),
    "ActionValidation": ("orchestrator.action_validator", "ActionValidation"),
    "DecisionLoop": ("orchestrator.decision_loop", "DecisionLoop"),
    "Decision": ("orchestrator.decision_loop", "Decision"),
    "run_episode": ("orchestrator.decision_loop", "run_episode"),
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module 'orchestrator' has no attribute {name!r}")
    module_name, attribute = _EXPORTS[name]
    value = getattr(importlib.import_module(module_name), attribute)
    globals()[name] = value
    return value
