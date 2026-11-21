import json
import subprocess
import threading
import time
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest
import yaml

from agent.schemas import Plan, StateSnapshot
from configs import load_config
from demo.services import live_app
from monitoring.metrics import MetricsCollector
from monitoring.prometheus_exporter import create_handler
from orchestrator.decision_loop import DecisionLoop
from orchestrator.executor import build_executor
from orchestrator.live_executor import LiveKubernetesExecutor
from rl.environment import NOOP, SCALE_OUT, PREWARM


class _FixedPlanner:
    def __init__(self, plan):
        self._plan = plan

    def plan(self, _state):
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


def _fake_subprocess(current, calls=None):
    calls = calls if calls is not None else []

    def _run(command, **_kwargs):
        calls.append(command)
        if "get" in command:
            target_name = next(arg for arg in command if arg.startswith("deployment/")).split("/")[-1]
            return subprocess.CompletedProcess(command, 0, str(current[target_name]), "")
        if any(arg.startswith("--replicas=") for arg in command):
            target_name = next(arg for arg in command if arg.startswith("deployment/")).split("/")[-1]
            current[target_name] = int(next(arg for arg in command if arg.startswith("--replicas=")).split("=")[1])
        return subprocess.CompletedProcess(command, 0, "", "")

    return _run, calls


def test_config_extends_deep_merges_without_removing_defaults(tmp_path):
    (tmp_path / "base.yaml").write_text(
        yaml.safe_dump({"execution": {"enabled": False, "dry_run": True, "allow_live": False}, "control": {"interval_seconds": 60}}),
        encoding="utf-8",
    )
    (tmp_path / "child.yaml").write_text(
        yaml.safe_dump({"extends": "base.yaml", "execution": {"dry_run": False}}),
        encoding="utf-8",
    )

    config = load_config(tmp_path / "child.yaml")

    assert config["execution"] == {"enabled": False, "dry_run": False, "allow_live": False}
    assert config["control"]["interval_seconds"] == 60


def test_local_live_config_enables_only_explicit_live_gates():
    config = load_config(Path("configs/local-live.yaml"))

    assert config["execution"]["backend"] == "kubernetes_live"
    assert config["execution"]["enabled"] is True
    assert config["execution"]["dry_run"] is False
    assert config["execution"]["allow_live"] is True
    assert config["execution"]["live"]["warm_namespace"] == "serverless-mgmt"
    assert config["monitoring"]["feedback"]["source"] == "prometheus"


def test_build_executor_registers_live_backend(test_config):
    test_config["execution"]["backend"] = "kubernetes_live"

    executor = build_executor(test_config)

    assert isinstance(executor, LiveKubernetesExecutor)
    assert executor.backend == "kubernetes_live"


def test_live_executor_dry_run_does_not_call_platform(monkeypatch, test_config):
    def _unexpected(*_args, **_kwargs):
        pytest.fail("dry-run must not call the platform")

    monkeypatch.setattr("orchestrator.live_executor.subprocess.run", _unexpected)
    test_config["execution"].update({"enabled": True, "dry_run": True, "backend": "kubernetes_live"})

    result = build_executor(test_config).execute(SCALE_OUT, _state())

    assert result.code == "dry_run"
    assert result.executed is False
    assert result.commands[0][:4] == [test_config["execution"]["kubectl"], "-n", test_config["execution"]["namespace"], "scale"]


def test_live_executor_scales_and_verifies_active_replicas(monkeypatch, test_config):
    test_config["execution"].update({"enabled": True, "dry_run": False, "allow_live": True, "backend": "kubernetes_live", "live": {"verify": True, "warm_deployment": "", "cooldown_s": 0, "rollback": True}})
    current = {"fn-checkout": 8}
    fake_run, calls = _fake_subprocess(current)
    monkeypatch.setattr("orchestrator.live_executor.subprocess.run", fake_run)

    result = LiveKubernetesExecutor(test_config).execute(SCALE_OUT, _state())

    assert result.code == "executed"
    assert result.executed is True
    assert result.target_capacity == 13
    assert any("--replicas=13" in command for command in calls)


def test_live_executor_prewarm_scales_warm_pool(monkeypatch, test_config):
    test_config["execution"].update({"enabled": True, "dry_run": False, "allow_live": True, "backend": "kubernetes_live", "live": {"verify": True, "cooldown_s": 0, "rollback": True, "warm_deployment": "fn-checkout-warm", "warm_increment": 2, "warm_max": 6}})
    current = {"fn-checkout": 8, "fn-checkout-warm": 0}
    fake_run, calls = _fake_subprocess(current)
    monkeypatch.setattr("orchestrator.live_executor.subprocess.run", fake_run)

    result = LiveKubernetesExecutor(test_config).execute(PREWARM, _state())

    assert result.code == "executed"
    assert result.target_capacity == 2
    assert any("deployment/fn-checkout-warm" in command and "--replicas=2" in command for command in calls)


def test_live_executor_rolls_back_on_verification_failure(monkeypatch, test_config):
    test_config["execution"].update({"enabled": True, "dry_run": False, "allow_live": True, "backend": "kubernetes_live", "live": {"verify": True, "warm_deployment": "", "cooldown_s": 0, "rollback": True}})
    current = {"fn-checkout": 8}
    calls = []

    def _run(command, **_kwargs):
        calls.append(command)
        if "get" in command:
            return subprocess.CompletedProcess(command, 0, "8", "")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("orchestrator.live_executor.subprocess.run", _run)

    result = LiveKubernetesExecutor(test_config).execute(SCALE_OUT, _state())

    assert result.code == "verification_failed"
    assert result.executed is False
    assert any("--replicas=8" in command for command in calls)


def test_stale_prometheus_metrics_force_noop(test_config):
    loop = DecisionLoop(
        test_config,
        planner=_FixedPlanner(Plan(strategy="ScaleOut", desired_capacity_change=5)),
    )

    decision = loop.decide(
        {"predicted_workload": [600.0] * 5, "trend": "stable"},
        {"stale": True, "current_workload": 600.0, "p95_latency_ms": 120.0, "active_containers": 8},
        policy=_FixedPolicy(SCALE_OUT),
        execute=False,
    )

    assert decision.final_action == NOOP
    assert decision.metrics_stale is True


def test_live_function_exposes_prometheus_metrics():
    server = ThreadingHTTPServer(("127.0.0.1", 0), live_app.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        assert json.loads(urllib.request.urlopen(f"{base}/health", timeout=2).read())["status"] == "ok"
        assert json.loads(urllib.request.urlopen(f"{base}/invoke?probe=1", timeout=2).read())["message"] == "ok"
        text = urllib.request.urlopen(f"{base}/metrics", timeout=2).read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert "fn_invocations_total" in text
    assert 'code="200"' in text
    assert "fn_request_duration_ms_bucket" in text
    assert "fn_cold_starts_total" in text


def test_exporter_publish_updates_metrics_endpoint():
    handler = create_handler(MetricsCollector({"monitoring": {"enabled": True}}))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        request = urllib.request.Request(
            f"{base}/publish",
            data=json.dumps({"live_check_metric": 3.0}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(request, timeout=2).read()
        text = urllib.request.urlopen(f"{base}/metrics", timeout=2).read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert "live_check_metric 3.0" in text


def test_live_dashboard_json_has_live_promql():
    dashboard = json.loads(Path("monitoring/grafana/dashboards/control-loop-live.json").read_text(encoding="utf-8"))
    expressions = " ".join(str(target.get("expr", "")) for panel in dashboard["panels"] for target in panel.get("targets", []))

    assert dashboard["uid"] == "control-loop-live"
    assert "fn_request_duration_ms_bucket" in expressions
    assert "fn_cold_starts_total" in expressions
    assert "action_selected_total" in expressions
