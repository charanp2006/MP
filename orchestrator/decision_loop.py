"""Decision loop wiring planner -> validator -> PPO -> action validator -> SLA guard -> executor -> monitoring.

Architecture Layers 4-9 in one bounded control step (docs/design.md section 16,
docs/test_plan.md I02/I03). Every step produces an auditable record of what was
forecast, planned, selected, validated and finally executed. Execution is
disabled by default (P4); monitoring/feedback is optional and safe (P5).
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Union

import numpy as np

from agent.planner import Planner, StubPlanner, build_planner
from agent.schemas import Plan, StateSnapshot
from agent.validator import PlanValidation, PlanValidator
from forecasting.inference import classify_trend
from monitoring.feedback import FeedbackLoop
from monitoring.metrics import MetricsCollector
from orchestrator.action_validator import ActionValidator
from orchestrator.executor import Executor, build_executor
from orchestrator.sla_guard import SLAGuard
from orchestrator.state_builder import build_state
from rl.environment import ACTIONS, NOOP


@dataclass
class Decision:
    state: StateSnapshot
    plan: Plan
    plan_valid: bool
    plan_code: str
    plan_reason: str
    ppo_action: int
    ppo_action_name: str
    final_action: int
    final_action_name: str
    guard_code: str
    action_code: str
    used_fallback: bool
    authorized: bool
    execution: Optional[Dict] = None
    feedback: Optional[Dict] = None

    def to_dict(self) -> Dict:
        data = {
            "state": self.state.model_dump(),
            "plan": self.plan.model_dump(),
            "plan_valid": self.plan_valid,
            "plan_code": self.plan_code,
            "plan_reason": self.plan_reason,
            "ppo_action": self.ppo_action,
            "ppo_action_name": self.ppo_action_name,
            "final_action": self.final_action,
            "final_action_name": self.final_action_name,
            "guard_code": self.guard_code,
            "action_code": self.action_code,
            "used_fallback": self.used_fallback,
            "authorized": self.authorized,
        }
        if self.execution is not None:
            data["execution"] = self.execution
        if self.feedback is not None:
            data["feedback"] = self.feedback
        return data


class DecisionLoop:
    """One bounded decision cycle over the simulator."""

    def __init__(
        self,
        config: Optional[Dict] = None,
        planner: Optional[Planner] = None,
        plan_validator: Optional[PlanValidator] = None,
        action_validator: Optional[ActionValidator] = None,
        sla_guard: Optional[SLAGuard] = None,
        executor: Optional[Executor] = None,
        metrics: Optional[MetricsCollector] = None,
        feedback: Optional[FeedbackLoop] = None,
    ) -> None:
        self.config = config or {}
        self.planner = planner or build_planner(self.config)
        self.fallback_planner = StubPlanner(self.config)
        self.plan_validator = plan_validator or PlanValidator(self.config)
        self.action_validator = action_validator or ActionValidator(self.config)
        self.sla_guard = sla_guard or SLAGuard(self.config)
        self.executor = executor or build_executor(self.config)
        self.metrics = metrics or MetricsCollector(self.config)
        self.feedback = feedback or FeedbackLoop(self.config)

    def _safe_plan(self, state: StateSnapshot) -> tuple[Plan, PlanValidation, bool]:
        used_fallback = False
        try:
            plan = self.planner.plan(state)
        except Exception:
            plan = self.fallback_planner.plan(state)
            used_fallback = True
        if getattr(self.planner, "last_fallback", False):
            used_fallback = True

        result = self.plan_validator.validate(plan, state)
        if result.ok:
            return result.plan, result, used_fallback

        plan = self.fallback_planner.plan(state)
        used_fallback = True
        result = self.plan_validator.validate(plan, state)
        if result.ok:
            return result.plan, result, used_fallback

        noop = Plan(
            strategy="NoOp",
            desired_capacity_change=0,
            priority="balanced",
            urgency="low",
            reason=f"fallback: {result.code}",
            constraints_respected=True,
        )
        return noop, PlanValidation(True, "noop_fallback", "invalid plan replaced by NoOp", noop), True

    @staticmethod
    def _select_action(policy, obs: Optional[np.ndarray]) -> int:
        if policy is None:
            return NOOP
        if hasattr(policy, "greedy_action"):
            return int(policy.greedy_action(obs))
        if callable(policy):
            if obs is None:
                raise ValueError("a callable policy requires an observation")
            return int(policy(obs))
        return int(policy)

    def decide(
        self,
        forecast: Dict,
        metrics: Dict,
        obs: Optional[np.ndarray] = None,
        policy: Optional[Union[Callable, object]] = None,
        authorized: bool = True,
        execute: bool = False,
        step_info: Optional[Dict] = None,
        feedback_signal: Optional[Dict] = None,
    ) -> Decision:
        state = build_state(forecast, metrics, self.config)
        plan, plan_validation, used_fallback = self._safe_plan(state)

        ppo_action = self._select_action(policy, obs)
        action_validation = self.action_validator.validate(
            ppo_action, state, authorized=authorized, plan=plan
        )
        candidate = action_validation.action if action_validation.ok else NOOP
        guard = self.sla_guard.check(candidate, state.p95_latency_ms)
        final_action = guard.action if not guard.allow else candidate
        final_action = int(final_action) if final_action in range(len(ACTIONS)) else NOOP

        execution = None
        if execute:
            result = self.executor.execute(final_action, state, plan=plan, authorized=authorized)
            execution = result.to_dict()

        signal = feedback_signal
        if step_info is not None and signal is None:
            try:
                self.feedback.record(
                    float(step_info.get("p95_latency", state.p95_latency_ms)),
                    bool(step_info.get("sla_violated", False)),
                    float(step_info.get("cold_starts", 0.0)),
                )
                signal = self.feedback.signal()
                self.metrics.record_step(step_info, ACTIONS[final_action])
            except Exception:
                signal = None
        elif signal is None:
            try:
                signal = self.feedback.signal()
            except Exception:
                signal = None

        return Decision(
            state=state,
            plan=plan,
            plan_valid=plan_validation.ok,
            plan_code=plan_validation.code,
            plan_reason=plan_validation.reason,
            ppo_action=int(ppo_action),
            ppo_action_name=ACTIONS[ppo_action] if int(ppo_action) in range(len(ACTIONS)) else "invalid",
            final_action=final_action,
            final_action_name=ACTIONS[final_action],
            guard_code=guard.code,
            action_code=action_validation.code,
            used_fallback=used_fallback,
            authorized=authorized,
            execution=execution,
            feedback=signal,
        )


def run_episode(env, config: Dict, policy=None, steps: Optional[int] = None) -> List[Dict]:
    """Run the decision loop over the simulator (oracle forecast; smoke only)."""
    loop = DecisionLoop(config)
    obs = env.reset()
    horizon = int(config["forecast"]["horizon"])
    timeline = env.timeline["workload"].to_numpy(dtype=float)
    env.set_forecast(timeline)

    records: List[Dict] = []
    done = False
    prev_info = None
    prev_feedback = None
    while not done and (steps is None or len(records) < steps):
        idx = env.idx
        row = env.timeline.iloc[idx]
        future = timeline[idx + 1 : idx + 1 + horizon]
        predicted = [float(value) for value in future] if len(future) else [float(row["workload"])]
        forecast = {
            "forecast_horizon": len(predicted),
            "predicted_workload": predicted,
            "trend": classify_trend(predicted),
        }
        metrics = {
            "current_workload": float(row["workload"]),
            "cpu_utilization": float(row["cpu"]),
            "memory_utilization": float(row["memory"]),
            "active_containers": int(env.capacity),
            "p95_latency_ms": float(obs[5]) * env.sla_threshold,
            "cold_starts": 0.0,
            "energy": float(obs[8]) * env.energy_ref,
        }
        if prev_info is not None:
            try:
                loop.feedback.record(
                    float(prev_info.get("p95_latency", metrics["p95_latency_ms"])),
                    bool(prev_info.get("sla_violated", False)),
                    float(prev_info.get("cold_starts", 0.0)),
                )
                prev_feedback = loop.feedback.signal()
            except Exception:
                prev_feedback = None
        decision = loop.decide(forecast, metrics, obs=obs, policy=policy, feedback_signal=prev_feedback)
        obs, reward, done, info = env.step(decision.final_action)
        try:
            loop.metrics.record_step(info, decision.final_action_name)
        except Exception:
            pass
        records.append({"decision": decision.to_dict(), "reward": float(reward), "info": info})
        prev_info = info
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the bounded decision loop (P3/P4 smoke)")
    parser.add_argument("--config", default=None)
    parser.add_argument("--steps", type=int, default=5)
    parser.add_argument("--runtime", choices=["stub", "ollama"], default=None)
    parser.add_argument("--policy", choices=["none", "checkpoint"], default="checkpoint")
    parser.add_argument("--execute", action="store_true", help="call the executor (respecting config)")
    args = parser.parse_args()

    from configs import load_config
    from data.pipeline import run
    from rl.environment import ServerlessEnv
    from rl.train_ppo import load_checkpoint

    config = load_config(args.config)
    if args.runtime:
        config.setdefault("agent", {})["runtime"] = args.runtime

    frame, _ = run(config=config)
    env = ServerlessEnv(frame, config)

    policy = None
    if args.policy == "checkpoint":
        checkpoint = config["control"]["rl"].get("checkpoint_path", "models/ppo_policy.pt")
        if os.path.exists(checkpoint):
            policy = load_checkpoint(checkpoint)

    records = run_episode(env, config, policy=policy, steps=args.steps)
    if args.execute:
        loop = DecisionLoop(config)
        env2 = ServerlessEnv(frame, config)
        obs = env2.reset()
        horizon = int(config["forecast"]["horizon"])
        timeline = env2.timeline["workload"].to_numpy(dtype=float)
        env2.set_forecast(timeline)
        records = []
        done = False
        count = 0
        prev_info = None
        prev_feedback = None
        while not done and (args.steps is None or count < args.steps):
            idx = env2.idx
            row = env2.timeline.iloc[idx]
            future = timeline[idx + 1 : idx + 1 + horizon]
            predicted = [float(value) for value in future] if len(future) else [float(row["workload"])]
            forecast = {"forecast_horizon": len(predicted), "predicted_workload": predicted, "trend": classify_trend(predicted)}
            metrics = {
                "current_workload": float(row["workload"]),
                "cpu_utilization": float(row["cpu"]),
                "memory_utilization": float(row["memory"]),
                "active_containers": int(env2.capacity),
                "p95_latency_ms": float(obs[5]) * env2.sla_threshold,
                "cold_starts": 0.0,
                "energy": float(obs[8]) * env2.energy_ref,
            }
            if prev_info is not None:
                try:
                    loop.feedback.record(
                        float(prev_info.get("p95_latency", metrics["p95_latency_ms"])),
                        bool(prev_info.get("sla_violated", False)),
                        float(prev_info.get("cold_starts", 0.0)),
                    )
                    prev_feedback = loop.feedback.signal()
                except Exception:
                    prev_feedback = None
            decision = loop.decide(forecast, metrics, obs=obs, policy=policy, execute=True, feedback_signal=prev_feedback)
            obs, reward, done, info = env2.step(decision.final_action)
            try:
                loop.metrics.record_step(info, decision.final_action_name)
            except Exception:
                pass
            records.append({"decision": decision.to_dict(), "reward": float(reward), "info": info})
            prev_info = info
            count += 1
    print(json.dumps({"steps": len(records), "last": records[-1]}, indent=2, default=str))


if __name__ == "__main__":
    main()

