"""Qwen3-style planning layer (image step 4, architecture Layer 5).

* ``schemas``   --- strict state/plan contracts.
* ``prompts``   --- planner prompt templates.
* ``planner``   --- hosted/local Qwen3 adapters, deterministic stub and fallbacks.
* ``validator`` --- plan schema/bounds validation (Layer 6).

Qwen3 only emits high-level strategies; it never issues infrastructure commands.
"""

from agent.planner import (
    FallbackPlanner,
    HostedQwen3Planner,
    Planner,
    PlannerError,
    PlannerProviderError,
    ProviderChainPlanner,
    Qwen3OllamaPlanner,
    Qwen3TransformersPlanner,
    StubPlanner,
    build_planner,
)
from agent.schemas import Plan, StateSnapshot
from agent.telemetry import PlannerCallRecord, redact_text
from agent.validator import PlanValidation, PlanValidator

__all__ = [
    "Plan",
    "StateSnapshot",
    "Planner",
    "PlannerError",
    "StubPlanner",
    "Qwen3OllamaPlanner",
    "Qwen3TransformersPlanner",
    "HostedQwen3Planner",
    "ProviderChainPlanner",
    "FallbackPlanner",
    "PlannerProviderError",
    "build_planner",
    "PlanValidator",
    "PlanValidation",
    "PlannerCallRecord",
    "redact_text",
]
