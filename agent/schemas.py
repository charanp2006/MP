"""Structured state and plan contracts (docs/design.md sections 3, 7, 9).

The planner (Qwen3 or the offline stub) consumes a :class:`StateSnapshot` and
returns a :class:`Plan`. Both are strict pydantic models: unknown fields are
rejected, strategies are restricted to the canonical action set and numeric
fields are bounded. This is the first gate for untrusted LLM output
(docs/security.md boundary 2); the plan/action validators and SLA guard remain
the safety boundary.
"""

from __future__ import annotations

from typing import Dict, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

STRATEGIES = ["NoOp", "PreWarm", "ScaleOut", "Reuse", "ScaleIn", "Terminate"]
PRIORITIES = ["sla", "energy", "cost", "balanced"]
URGENCIES = ["low", "medium", "high"]

_STRATEGY_ALIASES: Dict[str, str] = {
    "noop": "NoOp",
    "prewarm": "PreWarm",
    "scaleout": "ScaleOut",
    "reuse": "Reuse",
    "scalein": "ScaleIn",
    "terminate": "Terminate",
}


def normalize_strategy(value: object) -> str:
    """Normalize common spellings to the canonical strategy name."""
    if not isinstance(value, str):
        raise ValueError(f"strategy must be a string, got {type(value).__name__}")
    key = value.strip().lower().replace("_", "").replace("-", "").replace(" ", "")
    if key not in _STRATEGY_ALIASES:
        allowed = ", ".join(STRATEGIES)
        raise ValueError(f"unknown strategy {value!r}; allowed: {allowed}")
    return _STRATEGY_ALIASES[key]


class StateSnapshot(BaseModel):
    """Combined forecast + current observation (architecture Layer 4)."""

    model_config = ConfigDict(extra="forbid")

    forecast_workload: float = Field(ge=0.0)
    forecast_peak: float = Field(ge=0.0)
    current_workload: float = Field(ge=0.0)
    trend: Literal["increasing", "decreasing", "stable"] = "stable"
    cpu_utilization: float = Field(ge=0.0, le=1.0)
    memory_utilization: float = Field(ge=0.0, le=1.0)
    active_containers: int = Field(ge=0)
    p95_latency_ms: float = Field(ge=0.0)
    cold_start_rate: float = Field(ge=0.0, le=1.0)
    energy: float = Field(ge=0.0)
    sla_threshold_ms: float = Field(gt=0.0)
    sla_margin_ms: float
    forecast_horizon: int = Field(default=5, ge=1)
    metadata: Dict[str, str] = Field(default_factory=dict)


class Plan(BaseModel):
    """High-level planning output (architecture Layer 5). No infra commands."""

    model_config = ConfigDict(extra="forbid")

    strategy: str
    desired_capacity_change: int = 0
    priority: Literal["sla", "energy", "cost", "balanced"] = "balanced"
    urgency: Literal["low", "medium", "high"] = "medium"
    reason: str = Field(default="", max_length=500)
    constraints_respected: bool = True

    @field_validator("strategy", mode="before")
    @classmethod
    def _normalize_strategy(cls, value: object) -> str:
        return normalize_strategy(value)
