import pytest

from agent.schemas import Plan, StateSnapshot
from monitoring.prometheus_adapter import PrometheusMetricsAdapter
from orchestrator.decision_loop import DecisionLoop
from orchestrator.execution_audit import ExecutionAuditLogger
from orchestrator.executor import DockerExecutor, KubernetesExecutor, OpenFaaSExecutor, build_executor
from rl.environment import SCALE_OUT


class _FixedPlanner:
    def __init__(self, plan):
        self._plan = plan

    def plan(self, state):
        return self._plan


class _FixedPolicy:
    def __init__(self, action):
        self._action = action

    def greedy_action(self, _obs):
        return self._action


def _state():
    return StateSnapshot(
        forecast_workload=600.0,
        forecast_peak=620.0,
        current_workload=600.0,
        trend="stable",
        cpu_utilization=0.5,
        memory_utilization=0.5,
        active_containers=8,
        warm_containers=0,
        p95_latency_ms=120.0,
        cold_start_rate=0.02,
        energy=100.0,
        sla_threshold_ms=250.0,
        sla_margin_ms=130.0,
        forecast_horizon=5,
    )


def test_openfaas_executor_uses_function_namespace(test_config):
    test_config["execution"]["backend"] = "openfaas"
    executor = build_executor(test_config)

    result = executor.execute(SCALE_OUT, _state())

    assert isinstance(executor, OpenFaaSExecutor)
    assert result.backend == "openfaas"
    assert result.code in {"dry_run", "disabled"}
    assert result.commands[0][:5] == [test_config["execution"]["kubectl"], "-n", "openfaas-fn", "scale", "deployment/fn-checkout"]


def test_docker_executor_dry_run_and_service_allowlist(test_config):
    test_config["execution"]["backend"] = "docker"
    executor = build_executor(test_config)

    result = executor.execute(SCALE_OUT, _state())

    assert isinstance(executor, DockerExecutor)
    assert result.backend == "docker"
    assert result.executed is False
    assert result.commands == [["docker", "service", "scale", "fn-checkout=13"]]

    test_config["execution"]["docker"]["service"] = "unapproved"
    with pytest.raises(ValueError, match="allowed_services"):
        DockerExecutor(test_config)


def test_live_execution_requires_explicit_allow_live(monkeypatch, test_config):
    def _unexpected_call(*args, **kwargs):
        pytest.fail("live command must not run without execution.allow_live")

    monkeypatch.setattr("orchestrator.executor.subprocess.run", _unexpected_call)
    test_config["execution"].update({"enabled": True, "dry_run": False, "allow_live": False})

    result = KubernetesExecutor(test_config).execute(SCALE_OUT, _state())

    assert result.code == "live_disabled"
    assert result.executed is False
    assert result.commands[0][1] == "-n"


def test_execution_audit_records_backend_and_bounded_command(tmp_path, test_config):
    test_config["execution"]["audit_path"] = str(tmp_path / "audit.jsonl")
    audit = ExecutionAuditLogger(test_config)
    audit.reset()
    result = KubernetesExecutor(test_config).execute(SCALE_OUT, _state())

    path = audit.log(result.to_dict(), {"correlation_id": "m6-audit-1", "final_action_name": "ScaleOut", "authorized": True})
    records = audit.read_records()

    assert path == str(tmp_path / "audit.jsonl")
    assert len(records) == 1
    assert records[0]["backend"] == "kubernetes"
    assert records[0]["operation"] == "scale"
    assert records[0]["target_capacity"] == 13
    assert records[0]["correlation_id"] == "m6-audit-1"


def test_decision_loop_writes_execution_audit(tmp_path, test_config):
    test_config["execution"]["audit_path"] = str(tmp_path / "loop-audit.jsonl")
    audit = ExecutionAuditLogger(test_config)
    audit.reset()
    loop = DecisionLoop(
        test_config,
        planner=_FixedPlanner(Plan(strategy="NoOp", desired_capacity_change=0)),
        execution_audit=audit,
    )

    decision = loop.decide(
        {"predicted_workload": [600.0] * 5, "trend": "stable"},
        {"current_workload": 600.0, "cpu_utilization": 0.5, "p95_latency_ms": 120.0, "active_containers": 8},
        policy=_FixedPolicy(SCALE_OUT),
        execute=True,
        correlation_id="m6-loop-1",
    )
    records = audit.read_records()

    assert decision.execution is not None
    assert decision.execution["backend"] == "kubernetes"
    assert len(records) == 1
    assert records[0]["correlation_id"] == "m6-loop-1"
    assert records[0]["executed"] is False


def test_prometheus_adapter_maps_queries_to_state_metrics(test_config):
    test_config["monitoring"]["enabled"] = True
    test_config["monitoring"]["prometheus"]["adapter_enabled"] = True
    values = {
        "fn_latency_ms_bucket": 180.0,
        "fn_invocations_total": 120.0,
        "fn_cold_starts_total": 2.0,
        "fn_energy_w": 90.0,
        "kube_deployment_status_replicas": 4.0,
    }

    def fake_query(expression):
        value = next(value for key, value in values.items() if key in expression)
        return {"data": {"result": [{"value": [0, value]}]}}

    metrics = PrometheusMetricsAdapter(test_config, query_fn=fake_query).fetch()

    assert metrics["source"] == "prometheus"
    assert metrics["stale"] is False
    assert metrics["current_workload"] == 120.0
    assert metrics["p95_latency_ms"] == 180.0
    assert metrics["cold_starts"] == 2.0
    assert metrics["energy"] == 90.0
    assert metrics["active_containers"] == 4.0


def test_prometheus_adapter_marks_stale_when_query_fails(test_config):
    test_config["monitoring"]["prometheus"]["adapter_enabled"] = True

    def failing_query(_expression):
        raise RuntimeError("prometheus unavailable")

    metrics = PrometheusMetricsAdapter(test_config, query_fn=failing_query).fetch()

    assert metrics["stale"] is True
    assert "current_workload" not in metrics
    assert "prometheus unavailable" in metrics["last_errors"]["current_workload"]
