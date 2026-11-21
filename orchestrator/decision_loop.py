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
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Union
from uuid import uuid4

import numpy as np

from agent.planner import Planner, StubPlanner, build_planner
from agent.schemas import Plan, StateSnapshot
from agent.validator import PlanValidation, PlanValidator
from forecasting.inference import classify_trend
from monitoring.alerts import AlertManager
from monitoring.feedback import FeedbackLoop
from monitoring.metrics import MetricsCollector
from orchestrator.action_validator import ActionValidator
from orchestrator.decision_log import DecisionLogger, sanitize_record
from orchestrator.execution_audit import ExecutionAuditLogger
from orchestrator.executor import Executor, build_executor
from orchestrator.safety_shield import SafetyShield
from orchestrator.sla_guard import SLAGuard
from orchestrator.state_builder import build_state
from rl.environment import ACTIONS, NOOP, SCALE_IN, SCALE_OUT, PREWARM, TERMINATE, REUSE


def _correlation_id(prefix: Optional[str], step: int) -> str:
    suffix = uuid4().hex[:12]
    return f"{prefix}-{step:04d}-{suffix}" if prefix else f"{step:04d}-{suffix}"


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
    metrics_stale: bool = False
    execution: Optional[Dict] = None
    feedback: Optional[Dict] = None
    feedback_applied: bool = False
    planner_record: Optional[Dict] = None
    forecast: Dict = field(default_factory=dict)
    metrics: Dict = field(default_factory=dict)
    correlation_id: str = ""
    hierarchy: Dict = field(default_factory=dict)
    outcome: Optional[Dict] = None
    alerts: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        data = {
            "correlation_id": self.correlation_id,
            "hierarchy": sanitize_record(self.hierarchy),
            "forecast": sanitize_record(self.forecast),
            "metrics": sanitize_record(self.metrics),
            "state": sanitize_record(self.state.model_dump()),
            "plan": sanitize_record(self.plan.model_dump()),
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
            "metrics_stale": self.metrics_stale,
            "feedback_applied": self.feedback_applied,
        }
        if self.execution is not None:
            data["execution"] = self.execution
        if self.feedback is not None:
            data["feedback"] = sanitize_record(self.feedback)
        if self.planner_record is not None:
            data["planner_record"] = sanitize_record(self.planner_record)
        if self.outcome is not None:
            data["outcome"] = sanitize_record(self.outcome)
        data["alerts"] = sanitize_record(self.alerts)
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
        safety_shield: Optional[SafetyShield] = None,
        logger: Optional[DecisionLogger] = None,
        execution_audit: Optional[ExecutionAuditLogger] = None,
        alerts: Optional[AlertManager] = None,
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
        self.safety_shield = safety_shield or SafetyShield(
            self.config, validator=self.action_validator, guard=self.sla_guard
        )
        self.logger = logger or DecisionLogger(self.config)
        self.execution_audit = execution_audit or ExecutionAuditLogger(self.config)
        self.alerts = alerts or AlertManager(self.config)

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

    def _apply_feedback_bias(self, action: int, plan: Plan, signal: Optional[Dict]) -> tuple[int, bool]:
        """Soft, safe bias from runtime feedback. Never bypasses validation/SLA guard."""
        if not signal or not isinstance(signal, dict):
            return action, False
        caution = float(signal.get("caution", 0.0) or 0.0)
        if caution <= 0.0:
            return action, False
        # Under caution prefer SLA-safe/preemptive moves; keep plan-aligned when possible.
        if action in {SCALE_IN, TERMINATE}:
            if plan.strategy in {"ScaleOut", "PreWarm"}:
                return SCALE_OUT if action == SCALE_IN else PREWARM, True
            return PREWARM, True
        if action == NOOP and plan.strategy == "ScaleOut":
            return PREWARM, True
        return action, False

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
        correlation_id: Optional[str] = None,
    ) -> Decision:
        correlation = str(correlation_id or uuid4())
        forecast_source = str(forecast.get("source", forecast.get("forecast_source", "unspecified")))
        state = build_state(
            forecast,
            metrics,
            self.config,
            metadata={"forecast_source": forecast_source, "correlation_id": correlation},
        )
        plan, plan_validation, used_fallback = self._safe_plan(state)
        planner_record_obj = getattr(self.planner, "last_record", None)
        planner_record = (
            planner_record_obj.to_dict() if hasattr(planner_record_obj, "to_dict") else None
        )
        if planner_record is not None:
            planner_record = dict(planner_record)
            planner_record["plan_code"] = plan_validation.code

        ppo_action = self._select_action(policy, obs)
        metrics_stale = bool(metrics.get("stale", False))
        if metrics_stale:
            ppo_action = NOOP
        biased_action, feedback_applied = self._apply_feedback_bias(int(ppo_action), plan, feedback_signal)
        shield = self.safety_shield.filter(
            biased_action,
            state,
            authorized=authorized,
            plan=plan,
            p95_latency_ms=metrics.get("p95_latency_ms", state.p95_latency_ms),
        )
        final_action = int(shield.action) if int(shield.action) in range(len(ACTIONS)) else NOOP
        guard_code = "sla_guard" if "sla_guard" in shield.codes else "ok"
        action_code = shield.codes[0] if shield.codes else "ok"

        planner_latency = planner_record.get("latency_ms") if planner_record else None
        if planner_latency is not None:
            try:
                self.metrics.set_gauge("planner_latency_ms", float(planner_latency))
            except (TypeError, ValueError):
                pass
        if used_fallback:
            self.metrics.inc("planner_fallback_total")
        if guard_code == "sla_guard" or action_code != "ok":
            self.metrics.inc("guard_interventions_total")
        if ppo_action in range(len(ACTIONS)):
            self.metrics.inc("ppo_action_total", 1.0, {"action": ACTIONS[int(ppo_action)]})

        execution = None
        if execute:
            result = self.executor.execute(final_action, state, plan=plan, authorized=authorized)
            execution = result.to_dict()
            if not execution.get("ok", False):
                self.metrics.inc("execution_failures_total")
            self.execution_audit.log(
                execution,
                {
                    "correlation_id": correlation,
                    "final_action_name": ACTIONS[final_action],
                    "authorized": authorized,
                    "planner_strategy": plan.strategy,
                    "forecast_source": forecast_source,
                },
            )

        signal = feedback_signal
        if step_info is not None and signal is None:
            try:
                self.feedback.record_cycle(
                    correlation,
                    step_info,
                    {
                        "forecast_source": forecast_source,
                        "final_action": ACTIONS[final_action],
                        "source": str(metrics.get("source", self.feedback.source)),
                    },
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

        alert_list = self.alerts.evaluate(
            metrics={
                "p95_latency_ms": metrics.get("p95_latency_ms", state.p95_latency_ms),
                "stale": bool(metrics.get("stale", False)),
            },
            feedback=signal,
            execution=execution,
            correlation_id=correlation,
        )
        self.alerts.log(alert_list)

        hierarchy = {
            "correlation_id": correlation,
            "forecast_source": forecast_source,
            "metrics_stale": metrics_stale,
            "planner_role": "advisory",
            "controller_role": "proposal",
            "shield_role": "final_authority",
            "planner_strategy": plan.strategy,
            "proposed_action": int(ppo_action),
            "biased_action": int(biased_action),
            "feedback_bias_applied": bool(feedback_applied),
            "shield": shield.to_dict(),
        }

        return Decision(
            state=state,
            plan=plan,
            plan_valid=plan_validation.ok,
            plan_code=plan_validation.code,
            plan_reason=plan_validation.reason,
            ppo_action=int(ppo_action),
            ppo_action_name=ACTIONS[int(ppo_action)] if int(ppo_action) in range(len(ACTIONS)) else "invalid",
            final_action=final_action,
            final_action_name=ACTIONS[final_action],
            guard_code=guard_code,
            action_code=action_code,
            used_fallback=used_fallback,
            authorized=authorized,
            metrics_stale=metrics_stale,
            execution=execution,
            feedback=signal,
            feedback_applied=feedback_applied,
            planner_record=planner_record,
            forecast=dict(forecast),
            metrics=dict(metrics),
            correlation_id=correlation,
            hierarchy=hierarchy,
            alerts=alert_list,
        )

    def record_outcome(self, decision: Decision, outcome: Dict) -> Decision:
        decision.outcome = sanitize_record(dict(outcome))
        self.logger.log(decision, decision.outcome)
        return decision


def _persistence_forecast(current_workload: float, horizon: int) -> Dict:
    predicted = [max(float(current_workload), 0.0)] * max(int(horizon), 1)
    return {
        "forecast_horizon": len(predicted),
        "predicted_workload": predicted,
        "trend": classify_trend(predicted),
        "source": "persistence",
        "fallback": False,
        "fallback_reason": None,
    }


def _tft_forecast(env, service, horizon: int, scale_factor: float = 1.0) -> Dict:
    idx = int(env.idx)
    columns = ["workload", "cpu", "memory"]
    start = max(0, idx - service.history)
    hist = env.timeline.iloc[start:idx][columns].to_numpy(dtype=float)
    if len(hist) < service.history:
        pad = np.repeat(hist[:1], service.history - len(hist), axis=0) if len(hist) else np.zeros((service.history, len(columns)))
        hist = np.vstack([pad, hist])
    window = np.zeros((service.history, len(service.feature_columns)), dtype=np.float64)
    mapping = {name: position for position, name in enumerate(service.feature_columns)}
    values = {
        "invocation_count": hist[:, 0],
        "cpu_utilization": hist[:, 1],
        "memory_utilization": hist[:, 2],
        "active_containers": float(env.capacity),
    }
    for name, value in values.items():
        if name in mapping:
            window[:, mapping[name]] = value
    observed_at = env.timeline.iloc[idx].get("timestamp") if "timestamp" in env.timeline.columns else None
    forecast = service.forecast_history(window, observed_at=observed_at)
    raw_predicted = [max(float(value), 0.0) for value in forecast["predicted_workload"]]
    predicted = [value * float(scale_factor) for value in raw_predicted]
    forecast["forecast_horizon"] = max(int(horizon), 1)
    forecast["raw_predicted_workload"] = raw_predicted
    forecast["predicted_workload"] = predicted
    forecast["trend"] = classify_trend(predicted)
    forecast["scale_factor"] = float(scale_factor)
    return forecast


def run_episode(
    env,
    config: Dict,
    policy=None,
    steps: Optional[int] = None,
    use_tft: bool = False,
    tft_checkpoint: Optional[str] = None,
    execute: bool = False,
    logger: Optional[DecisionLogger] = None,
    loop: Optional[DecisionLoop] = None,
    correlation_prefix: Optional[str] = None,
    use_feedback: bool = True,
    forecast_scale: float = 1.0,
    metrics_source: str = "simulator",
    prometheus_adapter=None,
) -> List[Dict]:
    """Replay a trace through the bounded decision loop with logged provenance."""
    loop = loop or DecisionLoop(config, logger=logger)
    obs = env.reset()
    horizon = int(config["forecast"]["horizon"])

    service = None
    checkpoint_path = tft_checkpoint or config.get("forecast", {}).get("checkpoint_path", "")
    if use_tft and checkpoint_path and os.path.exists(str(checkpoint_path)):
        try:
            from forecasting.tft_service import TFTForecastService

            service = TFTForecastService(str(checkpoint_path), max_staleness_s=None)
        except Exception:
            service = None

    adapter = prometheus_adapter
    if metrics_source == "prometheus" and adapter is None:
        from monitoring.prometheus_adapter import PrometheusMetricsAdapter

        adapter = PrometheusMetricsAdapter(config)

    records: List[Dict] = []
    done = False
    prev_info = None
    prev_feedback = None
    prev_decision = None
    while not done and (steps is None or len(records) < steps):
        idx = int(env.idx)
        row = env.timeline.iloc[idx]
        live_metrics = adapter.fetch() if adapter is not None else None
        if service is not None:
            forecast = _tft_forecast(env, service, horizon, forecast_scale)
        elif live_metrics is not None:
            forecast = _persistence_forecast(float(live_metrics.get("current_workload", row["workload"])), horizon)
            forecast["source"] = "prometheus_persistence"
        else:
            forecast = _persistence_forecast(row["workload"], horizon)
        forecast_source = str(forecast.get("source", "persistence"))
        if live_metrics is not None:
            metrics = dict(live_metrics)
            metrics.setdefault("active_containers", int(env.capacity))
            metrics.setdefault("warm_containers", int(getattr(env, "warm", 0)))
            metrics["source"] = "prometheus"
        else:
            metrics = {
                "current_workload": float(row["workload"]),
                "cpu_utilization": float(row["cpu"]),
                "memory_utilization": float(row["memory"]),
                "active_containers": int(env.capacity),
                "warm_containers": int(getattr(env, "warm", 0)),
                "p95_latency_ms": float(obs[5]) * env.sla_threshold,
                "cold_starts": 0.0,
                "energy": float(obs[8]) * env.energy_ref,
            }
        if use_feedback and prev_info is not None:
            try:
                loop.feedback.record_cycle(
                    getattr(prev_decision, "correlation_id", ""),
                    prev_info,
                    {
                        "forecast_source": getattr(prev_decision, "hierarchy", {}).get("forecast_source", ""),
                        "final_action": getattr(prev_decision, "final_action_name", ""),
                        "source": str(metrics.get("source", loop.feedback.source)),
                    },
                )
                prev_feedback = loop.feedback.signal()
            except Exception:
                prev_feedback = None
        else:
            prev_feedback = None

        decision = loop.decide(
            forecast,
            metrics,
            obs=obs,
            policy=policy,
            execute=execute,
            feedback_signal=prev_feedback,
            correlation_id=_correlation_id(correlation_prefix, len(records)),
        )
        prev_decision = decision
        obs, reward, done, info = env.step(decision.final_action)
        try:
            loop.metrics.record_step(info, decision.final_action_name)
        except Exception:
            pass
        outcome = {
            "reward": float(reward),
            "p95_latency_ms": float(info.get("p95_latency", metrics["p95_latency_ms"])),
            "sla_violated": bool(info.get("sla_violated", False)),
            "cold_starts": float(info.get("cold_starts", 0.0)),
            "energy_w": float(info.get("energy", metrics["energy"])),
            "capacity": int(info.get("capacity", env.capacity)),
            "warm_containers": int(info.get("warm_containers", env.warm)),
            "required_capacity": int(info.get("required_capacity", 0)),
            "reward_components": info.get("reward_components", {}),
        }
        try:
            predicted = float(forecast.get("predicted_workload", [0.0])[0])
            actual = float(metrics.get("current_workload", row["workload"]))
            loop.metrics.set_gauge("forecast_error", abs(predicted - actual) / max(abs(actual), 1.0))
        except (TypeError, ValueError, IndexError):
            pass
        loop.record_outcome(decision, outcome)
        records.append(
            {
                "correlation_id": decision.correlation_id,
                "decision": decision.to_dict(),
                "reward": float(reward),
                "info": info,
                "forecast_source": forecast_source,
                "outcome": decision.outcome,
            }
        )
        prev_info = info
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the bounded decision loop (P3/P4 smoke)")
    parser.add_argument("--config", default=None)
    parser.add_argument("--steps", type=int, default=5)
    parser.add_argument("--runtime", choices=["stub", "ollama"], default=None)
    parser.add_argument("--policy", choices=["none", "checkpoint"], default="checkpoint")
    parser.add_argument("--execute", action="store_true", help="call the executor (respecting config)")
    parser.add_argument("--use-tft", action="store_true", help="use trained TFT checkpoint for forecasts (no oracle)")
    parser.add_argument(
        "--metrics-source",
        choices=["simulator", "prometheus"],
        default="simulator",
        help="source for live runtime metrics",
    )
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

    records = run_episode(
        ServerlessEnv(frame, config),
        config,
        policy=policy,
        steps=args.steps,
        use_tft=args.use_tft,
        execute=args.execute,
        correlation_prefix="cli",
        metrics_source=args.metrics_source,
    )
    last = records[-1] if records else None
    print(
        json.dumps(
            {
                "steps": len(records),
                "last": last,
                "modes": {
                    "tft": args.use_tft,
                    "runtime": config.get("agent", {}).get("runtime"),
                    "execute": bool(args.execute),
                    "metrics_source": args.metrics_source,
                },
            },
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()

