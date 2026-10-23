"""State builder, SLA guard, action validator and control-loop tests (P3)."""

import numpy as np
import pytest

from agent.schemas import STRATEGIES, Plan
from agent.validator import PlanValidator
from orchestrator.action_validator import ActionValidator
from orchestrator.decision_loop import DecisionLoop, run_episode
from orchestrator.sla_guard import SLAGuard
from orchestrator.state_builder import build_state
from rl.environment import ACTIONS, NOOP, SCALE_IN, SCALE_OUT, ServerlessEnv


class _FixedPlanner:
    def __init__(self, plan):
        self._plan = plan

    def plan(self, state):
        return self._plan


# ---------------------------------------------------------------- Layer 4
def test_state_builder_contract(test_config, metrics_factory):
    forecast = {
        "forecast_horizon": 5,
        "predicted_workload": [700.0, 750.0, 800.0, 850.0, 900.0],
        "trend": "increasing",
    }
    state = build_state(forecast, metrics_factory(current_workload=620.0, p95_latency_ms=210.0), test_config)

    assert state.forecast_workload == 700.0
    assert state.forecast_peak == 900.0
    assert state.current_workload == 620.0
    assert state.trend == "increasing"
    assert state.sla_threshold_ms == test_config["sla"]["p95_latency_ms"]
    assert state.sla_margin_ms == pytest.approx(test_config["sla"]["p95_latency_ms"] - 210.0)
    assert state.active_containers == 8
    assert 0.0 <= state.cold_start_rate <= 1.0


def test_state_builder_rejects_empty_forecast(test_config, metrics_factory):
    with pytest.raises(ValueError):
        build_state({"predicted_workload": []}, metrics_factory(), test_config)


def test_state_builder_requires_current_workload(test_config):
    with pytest.raises(ValueError):
        build_state({"predicted_workload": [1.0]}, {"cpu_utilization": 0.5}, test_config)


# ---------------------------------------------------------------- Layer 6
def test_plan_validator_rejects_above_max(test_config, state_factory):
    result = PlanValidator(test_config).validate(
        Plan(strategy="ScaleOut", desired_capacity_change=5), state_factory(active_containers=28)
    )
    assert not result.ok
    assert result.code == "capacity_max"


def test_plan_validator_rejects_below_min(test_config, state_factory):
    result = PlanValidator(test_config).validate(
        Plan(strategy="ScaleIn", desired_capacity_change=-5), state_factory(active_containers=4)
    )
    assert not result.ok
    assert result.code == "capacity_min"


def test_plan_validator_rejects_rate_limit(test_config, state_factory):
    result = PlanValidator(test_config).validate(
        Plan(strategy="ScaleOut", desired_capacity_change=6), state_factory()
    )
    assert not result.ok
    assert result.code == "rate_limit"


@pytest.mark.parametrize(
    "plan",
    [
        Plan(strategy="ScaleIn", desired_capacity_change=5),
        Plan(strategy="NoOp", desired_capacity_change=1),
        Plan(strategy="NoOp", desired_capacity_change=0, constraints_respected=False),
    ],
)
def test_plan_validator_rejects_inconsistent_plans(test_config, state_factory, plan):
    assert not PlanValidator(test_config).validate(plan, state_factory()).ok


# ---------------------------------------------------------------- Layer 8
def test_sla_guard_blocks_scale_in_near_sla(test_config):
    guard = SLAGuard(test_config)
    near_sla = test_config["sla"]["p95_latency_ms"] - 10.0
    decision = guard.check(SCALE_IN, near_sla)

    assert not decision.allow
    assert decision.code == "sla_guard"
    assert decision.action == NOOP


def test_sla_guard_allows_safe_scale_in(test_config):
    decision = SLAGuard(test_config).check(SCALE_IN, 100.0)
    assert decision.allow
    assert decision.action == SCALE_IN


def test_sla_guard_allows_noop_even_during_violation(test_config):
    assert SLAGuard(test_config).check(NOOP, 999.0).allow


# ---------------------------------------------------------------- Layer 9
def test_action_validator_rejects_unknown_action(test_config, state_factory):
    result = ActionValidator(test_config).validate(99, state_factory())
    assert not result.ok
    assert result.code == "unknown_action"
    assert result.action == NOOP


def test_action_validator_requires_authorization(test_config, state_factory):
    result = ActionValidator(test_config).validate(SCALE_OUT, state_factory(), authorized=False)
    assert not result.ok
    assert result.code == "unauthorized"


def test_action_validator_blocks_plan_conflict(test_config, state_factory):
    plan = Plan(strategy="ScaleOut", desired_capacity_change=5, urgency="high")
    result = ActionValidator(test_config).validate(SCALE_IN, state_factory(), plan=plan)
    assert not result.ok
    assert result.code == "plan_conflict"
    assert result.action == NOOP


def test_action_validator_accepts_bounded_action(test_config, state_factory):
    result = ActionValidator(test_config).validate(SCALE_OUT, state_factory())
    assert result.ok
    assert result.action_name == "ScaleOut"
    assert test_config["containers"]["min"] <= result.target_capacity <= test_config["containers"]["max"]


# ---------------------------------------------------------------- integrated loop
def test_decision_loop_integration(processed_frame, test_config, metrics_factory):
    env = ServerlessEnv(processed_frame, test_config)
    obs = env.reset()
    loop = DecisionLoop(test_config)

    decision = loop.decide(
        forecast={"predicted_workload": [600.0] * 5, "trend": "stable"},
        metrics=metrics_factory(),
        obs=obs,
        policy=lambda _: SCALE_OUT,
    )

    assert decision.plan_valid
    assert decision.plan.strategy in STRATEGIES
    assert decision.final_action in range(len(ACTIONS))
    assert isinstance(decision.to_dict(), dict)


def test_decision_loop_sla_guard_overrides_policy(test_config, metrics_factory):
    loop = DecisionLoop(
        test_config,
        planner=_FixedPlanner(Plan(strategy="NoOp", desired_capacity_change=0, urgency="low")),
    )
    decision = loop.decide(
        forecast={"predicted_workload": [600.0] * 5, "trend": "stable"},
        metrics=metrics_factory(p95_latency_ms=240.0),
        obs=np.zeros(10, dtype=np.float32),
        policy=lambda _: SCALE_IN,
    )

    assert decision.final_action == NOOP
    assert decision.guard_code == "sla_guard"


def test_decision_loop_unauthorized_falls_back_to_noop(test_config, metrics_factory):
    loop = DecisionLoop(test_config)
    decision = loop.decide(
        forecast={"predicted_workload": [600.0] * 5, "trend": "stable"},
        metrics=metrics_factory(),
        obs=np.zeros(10, dtype=np.float32),
        policy=lambda _: SCALE_OUT,
        authorized=False,
    )

    assert decision.final_action == NOOP
    assert decision.action_code == "unauthorized"


def test_run_episode_smoke(processed_frame, test_config):
    env = ServerlessEnv(processed_frame, test_config)
    records = run_episode(env, test_config, policy=None, steps=3)

    assert len(records) == 3
    for record in records:
        assert record["decision"]["final_action"] in range(len(ACTIONS))
        assert record["decision"]["plan"]["strategy"] in STRATEGIES
