"""Qwen3 planner adapter plus a deterministic offline stub (design.md section 8).

The planner is a *high-level* component: it returns a validated :class:`Plan`,
never shell or Kubernetes commands. Qwen3 runs through Ollama's HTTP API so it
stays out of the Python process; when it is unavailable or emits invalid data,
:class:`FallbackPlanner` falls back to the deterministic :class:`StubPlanner`.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Dict, Optional, Protocol

from agent.prompts import build_user_prompt, load_system_prompt
from agent.schemas import Plan, StateSnapshot


class PlannerError(RuntimeError):
    """Raised when a planner cannot produce a usable plan."""


class Planner(Protocol):
    def plan(self, state: StateSnapshot) -> Plan: ...


class StubPlanner:
    """Deterministic, offline planner used by tests and as a safe fallback."""

    def __init__(self, config: Optional[Dict] = None) -> None:
        config = config or {}
        containers = config.get("containers", {})
        sla = config.get("sla", {})
        agent = config.get("agent", {})

        self.min_capacity = int(containers.get("min", 2))
        self.max_capacity = int(containers.get("max", 30))
        self.max_change = max(1, int(containers.get("max_change_per_cycle", 5)))
        self.safety_margin = float(sla.get("safety_margin_ms", 0.0))
        self.high_ratio = float(agent.get("high_demand_ratio", 1.10))
        self.low_ratio = float(agent.get("low_demand_ratio", 0.90))

    def _scale_out_change(self, state: StateSnapshot) -> int:
        room = max(0, self.max_capacity - state.active_containers)
        return min(self.max_change, room)

    def _scale_in_change(self, state: StateSnapshot) -> int:
        room = max(0, state.active_containers - self.min_capacity)
        return -min(self.max_change, room)

    def plan(self, state: StateSnapshot) -> Plan:
        ratio = state.forecast_peak / max(state.current_workload, 1.0)
        sla_risk = state.sla_margin_ms <= self.safety_margin

        if sla_risk:
            change = self._scale_out_change(state)
            if change > 0 and (ratio >= 1.0 or state.trend == "increasing"):
                return Plan(
                    strategy="ScaleOut",
                    desired_capacity_change=change,
                    priority="sla",
                    urgency="high",
                    reason="P95 is at/near the SLA threshold and demand is not falling",
                    constraints_respected=True,
                )
            return Plan(
                strategy="PreWarm",
                desired_capacity_change=0,
                priority="sla",
                urgency="high",
                reason="P95 is at/near the SLA threshold; warm capacity without scaling",
                constraints_respected=True,
            )

        if ratio >= self.high_ratio or (state.trend == "increasing" and ratio > 1.0):
            change = self._scale_out_change(state)
            if change > 0:
                return Plan(
                    strategy="ScaleOut",
                    desired_capacity_change=change,
                    priority="sla",
                    urgency="high",
                    reason=f"forecast peak is {ratio:.2f}x current workload",
                    constraints_respected=True,
                )
            return Plan(
                strategy="PreWarm",
                desired_capacity_change=0,
                priority="balanced",
                urgency="medium",
                reason="demand is rising but capacity is already at the maximum",
                constraints_respected=True,
            )

        if ratio <= self.low_ratio and state.sla_margin_ms > self.safety_margin:
            change = self._scale_in_change(state)
            if change < 0:
                return Plan(
                    strategy="ScaleIn",
                    desired_capacity_change=change,
                    priority="energy",
                    urgency="low",
                    reason="demand is falling with comfortable SLA headroom",
                    constraints_respected=True,
                )

        if state.cpu_utilization >= 0.75 and state.active_containers < self.max_capacity:
            change = self._scale_out_change(state)
            if change > 0:
                return Plan(
                    strategy="ScaleOut",
                    desired_capacity_change=change,
                    priority="sla",
                    urgency="medium",
                    reason="CPU utilization is high",
                    constraints_respected=True,
                )

        return Plan(
            strategy="NoOp",
            desired_capacity_change=0,
            priority="balanced",
            urgency="low",
            reason="no significant forecast or SLA pressure",
            constraints_respected=True,
        )


class Qwen3OllamaPlanner:
    """Real Qwen3 planner backed by a local Ollama server."""

    def __init__(self, config: Optional[Dict] = None) -> None:
        config = config or {}
        agent = config.get("agent", {})
        self.base_url = str(agent.get("base_url", "http://localhost:11434")).rstrip("/")
        self.model = str(agent.get("model", "qwen3:4b"))
        self.timeout_s = float(agent.get("timeout_s", 30))
        self.temperature = float(agent.get("temperature", 0.0))
        self.num_predict = int(agent.get("num_predict", 256))
        self.system_prompt = load_system_prompt()

    def _post(self, payload: Dict) -> Dict:
        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
            return json.loads(response.read().decode("utf-8"))

    def plan(self, state: StateSnapshot) -> Plan:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": build_user_prompt(state)},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": self.temperature, "num_predict": self.num_predict},
        }
        try:
            body = self._post(payload)
            content = body["message"]["content"]
            raw = content if isinstance(content, dict) else json.loads(content)
            return Plan.model_validate(raw)
        except PlannerError:
            raise
        except Exception as exc:
            raise PlannerError(f"Qwen3 planner failed: {exc}") from exc


class FallbackPlanner:
    """Use the primary planner, falling back to a deterministic stub on failure."""

    def __init__(self, primary: Planner, fallback: Optional[StubPlanner] = None) -> None:
        self.primary = primary
        self.fallback = fallback or StubPlanner()
        self.last_fallback = False
        self.last_error: Optional[str] = None

    def plan(self, state: StateSnapshot) -> Plan:
        try:
            plan = self.primary.plan(state)
            self.last_fallback = False
            self.last_error = None
            return plan
        except Exception as exc:
            self.last_fallback = True
            self.last_error = str(exc)
            return self.fallback.plan(state)


def build_planner(config: Optional[Dict] = None, with_fallback: bool = True) -> Planner:
    """Construct the planner selected by ``agent.runtime``."""
    config = config or {}
    runtime = str(config.get("agent", {}).get("runtime", "stub")).lower()
    if runtime == "stub":
        return StubPlanner(config)
    if runtime in {"ollama", "qwen3"}:
        primary = Qwen3OllamaPlanner(config)
        return FallbackPlanner(primary, StubPlanner(config)) if with_fallback else primary
    raise ValueError(f"unknown agent.runtime {runtime!r}; expected 'stub' or 'ollama'")
