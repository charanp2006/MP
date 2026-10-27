"""P5 tests: monitoring, feedback, experiments."""

import numpy as np

from monitoring.feedback import FeedbackLoop
from monitoring.metrics import MetricsCollector, export_prometheus_text


def test_metrics_collector_disabled():
    collector = MetricsCollector({"monitoring": {"enabled": False}})
    collector.record_step({"capacity": 5, "p95_latency": 100, "latency": 80, "energy": 80, "cold_starts": 0, "workload": 200, "sla_violated": False}, "NoOp")
    assert collector.snapshot() == {}


def test_metrics_collector_enabled():
    collector = MetricsCollector({"monitoring": {"enabled": True}})
    collector.inc("requests_total")
    collector.set_gauge("containers_active", 8)
    collector.observe("p95_latency_ms", 120)
    collector.record_step({"capacity": 8, "p95_latency": 130, "latency": 100, "energy": 125, "cold_starts": 1, "workload": 500, "sla_violated": True}, "ScaleOut")
    snap = collector.snapshot()
    assert "requests_total" in snap
    assert "containers_active" in snap
    assert any("action_selected_total" in key for key in snap)
    text = export_prometheus_text(snap)
    assert "containers_active" in text
    assert 'action="ScaleOut"' in text


def test_feedback_loop_caution_on_degradation():
    feedback = FeedbackLoop({"monitoring": {"feedback": {"enabled": True, "window": 10, "degrade_threshold": 0.1, "min_samples": 3}}})
    for i in range(5):
        feedback.record(100.0 + i * 10, i > 2, 0)
    signal = feedback.signal()
    assert "caution" in signal
    assert "violation_rate" in signal
    assert "p95_trend" in signal


def test_feedback_loop_insufficient_samples():
    feedback = FeedbackLoop({"monitoring": {"feedback": {"enabled": True, "min_samples": 10}}})
    for _ in range(3):
        feedback.record(120, False, 0)
    assert feedback.signal()["caution"] == 0.0


def test_experiments_runner_smoke(processed_frame, test_config):
    from experiments.run_experiments import run_baseline_vs_proposed

    result = run_baseline_vs_proposed(test_config, episodes=1)
    assert "baseline" in result
    assert "proposed" in result
    assert "mean_reward" in result["baseline"]
    assert "mean_reward" in result["proposed"]
