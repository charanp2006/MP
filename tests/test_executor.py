"""Executor tests: Layer 10 allowlist, dry-run, bounds, authorization."""

import pytest

from agent.schemas import StateSnapshot
from orchestrator.executor import KubernetesExecutor, NoOpExecutor, build_executor
from rl.environment import ACTIONS, NOOP, SCALE_IN, SCALE_OUT, TERMINATE


def _state():
    return StateSnapshot(
        forecast_workload=600.0,
        forecast_peak=620.0,
        current_workload=600.0,
        trend="stable",
        cpu_utilization=0.5,
        memory_utilization=0.5,
        active_containers=8,
        p95_latency_ms=120.0,
        cold_start_rate=0.02,
        energy=100.0,
        sla_threshold_ms=250.0,
        sla_margin_ms=130.0,
        forecast_horizon=5,
    )


def test_executor_default_dry_run(test_config):
    executor = KubernetesExecutor(test_config)
    result = executor.execute(SCALE_OUT, _state())
    assert result.code in {"dry_run", "disabled"}
    assert result.executed is False
    if result.code == "dry_run":
        assert result.commands[0][0] == test_config["execution"]["kubectl"]


def test_executor_disabled_no_platform_call(test_config):
    test_config["execution"]["enabled"] = False
    executor = KubernetesExecutor(test_config)
    result = executor.execute(SCALE_OUT, _state())
    assert result.code == "disabled"
    assert result.executed is False


def test_executor_never_accepts_shell_strings(test_config):
    executor = KubernetesExecutor(test_config)
    result = executor.execute("ScaleOut", _state())
    assert not result.ok
    assert result.code == "invalid_action"


def test_executor_allowlist_only_bounded_scale(test_config):
    executor = KubernetesExecutor(test_config)
    out = executor.execute(SCALE_OUT, _state())
    in_ = executor.execute(SCALE_IN, _state())
    no = executor.execute(NOOP, _state())
    term = executor.execute(TERMINATE, _state())
    pre = executor.execute(1, _state())

    for result in [out, in_, term]:
        assert result.commands
        assert result.commands[0][1:4] == ["-n", test_config["execution"]["namespace"], "scale"]
    assert no.commands == []
    assert pre.commands == []
    assert out.target_capacity >= in_.target_capacity


def test_executor_respects_max_replicas(test_config):
    test_config["execution"]["max_replicas"] = 12
    executor = KubernetesExecutor(test_config)
    state = _state()
    state.active_containers = 10
    result = executor.execute(SCALE_OUT, state)
    assert result.target_capacity <= 12


def test_executor_unauthorized_rejected(test_config):
    executor = KubernetesExecutor(test_config)
    result = executor.execute(SCALE_OUT, _state(), authorized=False)
    assert not result.ok
    assert result.code == "unauthorized"


def test_executor_namespace_allowlist_enforced(test_config):
    test_config["execution"]["namespace"] = "other"
    with pytest.raises(ValueError):
        KubernetesExecutor(test_config)


def test_noop_executor_safe(test_config):
    executor = NoOpExecutor()
    result = executor.execute(SCALE_OUT, _state())
    assert result.ok and result.executed is False


def test_build_executor(test_config):
    assert isinstance(build_executor(test_config), KubernetesExecutor)
    test_config["execution"]["backend"] = "noop"
    assert isinstance(build_executor(test_config), NoOpExecutor)


def test_decision_loop_can_call_executor(processed_frame, test_config, metrics_factory):
    from orchestrator.decision_loop import DecisionLoop

    loop = DecisionLoop(test_config)
    decision = loop.decide(
        forecast={"predicted_workload": [600.0] * 5, "trend": "stable"},
        metrics=metrics_factory(),
        obs=__import__("numpy").zeros(10, dtype=__import__("numpy").float32),
        policy=lambda _: SCALE_OUT,
        execute=True,
    )
    assert decision.execution is not None
    assert decision.execution["dry_run"] is True
    assert decision.execution["executed"] is False
    assert decision.final_action in range(len(ACTIONS))
