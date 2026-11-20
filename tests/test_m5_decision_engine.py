import json

import numpy as np
import pytest

from agent.schemas import Plan
from experiments.evaluate_decision_engine import evaluate_decision_engine
from orchestrator.decision_log import DecisionLogger
from orchestrator.decision_loop import DecisionLoop, run_episode
from rl.environment import NOOP, SCALE_IN, SCALE_OUT, ServerlessEnv


class _FixedPlanner:
    def __init__(self, plan):
        self._plan = plan

    def plan(self, state):
        return self._plan


def test_decision_logger_writes_redacted_provenance(tmp_path, test_config, metrics_factory):
    config = dict(test_config)
    config["decision_log"] = {"enabled": True, "path": str(tmp_path / "decisions.jsonl")}
    logger = DecisionLogger(config)
    logger.reset()
    loop = DecisionLoop(
        config,
        planner=_FixedPlanner(Plan(strategy="ScaleOut", desired_capacity_change=1, urgency="low")),
        logger=logger,
    )

    decision = loop.decide(
        {
            "forecast_horizon": 2,
            "predicted_workload": [700.0, 720.0],
            "trend": "increasing",
            "source": "persistence",
            "note": "token=forecast_secret",
        },
        metrics_factory(),
        obs=np.zeros(10, dtype=np.float32),
        policy=lambda _: SCALE_OUT,
        correlation_id="test-step-0001",
    )
    loop.record_outcome(decision, {"reward": 1.0, "detail": "password=outcome_secret"})

    records = logger.read_records()
    assert len(records) == 1
    record = records[0]
    assert record["correlation_id"] == "test-step-0001"
    assert record["log_schema_version"] == 1
    assert record["hierarchy"]["shield_role"] == "final_authority"
    assert record["outcome"]["reward"] == 1.0
    assert "forecast_secret" not in json.dumps(record)
    assert "outcome_secret" not in json.dumps(record)


def test_decide_uses_shield_as_final_authority(test_config, metrics_factory):
    loop = DecisionLoop(
        test_config,
        planner=_FixedPlanner(Plan(strategy="NoOp", desired_capacity_change=0, urgency="low")),
        logger=DecisionLogger({"decision_log": {"enabled": False}}),
    )

    decision = loop.decide(
        {"predicted_workload": [600.0] * 5, "trend": "stable", "source": "persistence"},
        metrics_factory(p95_latency_ms=245.0),
        obs=np.zeros(10, dtype=np.float32),
        policy=lambda _: SCALE_IN,
    )

    assert decision.final_action == NOOP
    assert decision.guard_code == "sla_guard"
    assert decision.hierarchy["shield"]["proposed_action"] == SCALE_IN
    assert decision.hierarchy["shield"]["action"] == NOOP
    assert decision.hierarchy["forecast_source"] == "persistence"
    assert decision.metrics["p95_latency_ms"] == 245.0


def test_run_episode_logs_outcomes_without_oracle_forecast(
    processed_frame, test_config, tmp_path
):
    config = dict(test_config)
    config["decision_log"] = {"enabled": True, "path": str(tmp_path / "episode.jsonl")}
    logger = DecisionLogger(config)
    env = ServerlessEnv(processed_frame, config)

    records = run_episode(
        env,
        config,
        steps=2,
        policy=lambda _: SCALE_OUT,
        logger=logger,
        correlation_prefix="episode",
    )
    logged = logger.read_records()

    assert len(records) == 2
    assert len(logged) == 2
    assert len({record["correlation_id"] for record in records}) == 2
    for record, log in zip(records, logged):
        decision = record["decision"]
        current = decision["metrics"]["current_workload"]
        forecast = decision["forecast"]["predicted_workload"]
        assert record["forecast_source"] == "persistence"
        assert forecast == [current] * int(config["forecast"]["horizon"])
        assert log["outcome"]["reward"] == pytest.approx(record["reward"])
        assert log["correlation_id"] == record["correlation_id"]


def test_evaluate_decision_engine_writes_replay_and_ablations(test_config, tmp_path):
    result = evaluate_decision_engine(
        test_config,
        tmp_path,
        steps=3,
        policy=lambda _: SCALE_OUT,
    )

    assert result["replay_rows"] == 3
    assert result["manifest"]["mode"] == "simulation"
    assert result["manifest"]["tft_used"] is False
    assert {row["arm"] for row in result["summary"]} == {
        "full",
        "planner_off",
        "policy_off",
        "feedback_off",
        "forecast_off",
    }
    for name in (
        "run_manifest.json",
        "summary.json",
        "ablations.csv",
        "replay.csv",
        "replay.json",
        "replay.md",
        "replay.html",
        "decisions/full.jsonl",
    ):
        assert (tmp_path / name).exists()
    assert len(DecisionLogger({"decision_log": {"path": str(tmp_path / "decisions/full.jsonl")}}).read_records()) == 3
