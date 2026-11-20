import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

import yaml

from agent.schemas import Plan
from monitoring.alerts import AlertManager
from monitoring.feedback import FeedbackLoop
from monitoring.metrics import MetricsCollector
from monitoring.prometheus_adapter import PrometheusMetricsAdapter
from monitoring.prometheus_exporter import create_handler
from orchestrator.decision_loop import DecisionLoop
from rl.environment import NOOP


class _FixedPlanner:
    def __init__(self, plan):
        self._plan = plan

    def plan(self, _state):
        return self._plan


class _FixedPolicy:
    def greedy_action(self, _obs):
        return NOOP


def test_feedback_records_are_persisted(tmp_path, test_config):
    test_config["monitoring"]["feedback"].update(
        {"record_enabled": True, "record_path": str(tmp_path / "feedback.jsonl")}
    )
    feedback = FeedbackLoop(test_config)

    path = feedback.record_cycle(
        "m7-feedback-1",
        {
            "p95_latency": 180.0,
            "sla_violated": False,
            "cold_starts": 1.0,
            "energy": 42.0,
            "capacity": 4,
            "reward": 0.5,
        },
        {"forecast_source": "tft", "final_action": "ScaleOut"},
    )
    records = feedback.read_records()

    assert path == str(tmp_path / "feedback.jsonl")
    assert len(records) == 1
    assert records[0]["correlation_id"] == "m7-feedback-1"
    assert records[0]["forecast_source"] == "tft"
    assert records[0]["p95_latency_ms"] == 180.0
    assert "feedback_signal" in records[0]


def test_alert_manager_detects_failure_conditions(tmp_path, test_config):
    test_config["monitoring"]["alerts"].update(
        {"enabled": True, "log_enabled": True, "log_path": str(tmp_path / "alerts.jsonl")}
    )
    manager = AlertManager(test_config)

    alerts = manager.evaluate(
        metrics={"p95_latency_ms": 280.0, "stale": True},
        feedback={"violation_rate": 0.5, "caution": 1.0},
        execution={"ok": False, "code": "execution_failed"},
        correlation_id="m7-alert-1",
    )
    path = manager.log(alerts)
    names = {alert["name"] for alert in alerts}

    assert {"p95_near_sla", "sla_violation_rate", "stale_metrics", "executor_failure", "feedback_degradation"} <= names
    assert path == str(tmp_path / "alerts.jsonl")
    assert len(manager.read_alerts()) == len(alerts)


def test_exporter_serves_metrics_health_and_ready():
    collector = MetricsCollector({"monitoring": {"enabled": True}})
    collector.set_gauge("p95_latency_ms", 123.0)
    server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(collector))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        with urlopen(f"{base}/metrics", timeout=5) as response:
            text = response.read().decode("utf-8")
        with urlopen(f"{base}/health", timeout=5) as response:
            health = json.loads(response.read().decode("utf-8"))
        with urlopen(f"{base}/ready", timeout=5) as response:
            ready = json.loads(response.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert "p95_latency_ms 123.0" in text
    assert health["status"] == "ok"
    assert ready["ready"] is True


def test_exporter_ready_fails_on_stale_metrics():
    def failing_query(_expression):
        raise RuntimeError("prometheus down")

    adapter = PrometheusMetricsAdapter(
        {"monitoring": {"prometheus": {"adapter_enabled": True}}}, query_fn=failing_query
    )
    collector = MetricsCollector({"monitoring": {"enabled": True}})
    server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(collector, adapter))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            urlopen(f"{base}/ready", timeout=5)
            status = 200
        except Exception as exc:
            status = int(getattr(exc, "code", 0))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert status == 503


def test_decision_loop_records_feedback_and_alerts(tmp_path, test_config):
    test_config["monitoring"].update({"enabled": True})
    test_config["monitoring"]["feedback"].update(
        {"record_enabled": True, "record_path": str(tmp_path / "feedback.jsonl")}
    )
    test_config["monitoring"]["alerts"].update(
        {"enabled": True, "log_enabled": True, "log_path": str(tmp_path / "alerts.jsonl")}
    )
    feedback = FeedbackLoop(test_config)
    alerts = AlertManager(test_config)
    loop = DecisionLoop(
        test_config,
        planner=_FixedPlanner(Plan(strategy="NoOp", desired_capacity_change=0)),
        feedback=feedback,
        alerts=alerts,
    )

    decision = loop.decide(
        {"predicted_workload": [280.0] * 5, "trend": "stable", "source": "tft"},
        {"current_workload": 280.0, "cpu_utilization": 0.9, "p95_latency_ms": 280.0, "active_containers": 2},
        policy=_FixedPolicy(),
        correlation_id="m7-loop-1",
        step_info={
            "p95_latency": 280.0,
            "sla_violated": True,
            "cold_starts": 2.0,
            "energy": 60.0,
            "capacity": 2,
            "workload": 280.0,
        },
    )

    assert any(alert["name"] == "p95_near_sla" for alert in decision.alerts)
    assert "alerts" in decision.to_dict()
    assert feedback.read_records()[0]["correlation_id"] == "m7-loop-1"
    assert alerts.read_alerts()[0]["correlation_id"] == "m7-loop-1"


def test_monitoring_artifacts_are_valid():
    root = Path(__file__).resolve().parents[1]
    dashboard = json.loads((root / "monitoring/grafana/dashboards/control-loop.json").read_text(encoding="utf-8"))
    prometheus = yaml.safe_load((root / "monitoring/prometheus/prometheus.yml").read_text(encoding="utf-8"))
    alert_rules = yaml.safe_load((root / "monitoring/prometheus/alerts.yml").read_text(encoding="utf-8"))

    assert dashboard["uid"] == "control-loop"
    assert any("p95_latency_ms" in json.dumps(panel) for panel in dashboard["panels"])
    assert any(job["job_name"] == "control-loop" for job in prometheus["scrape_configs"])
    assert any(rule["alert"] == "MetricsStale" for rule in alert_rules["groups"][0]["rules"])
