import json
from pathlib import Path

import pandas as pd
import pytest

from data.generic_adapter import (
    GenericIngestionAdapter,
    IngestionAuthError,
    IngestionValidationError,
    records_to_trace,
)
from demo.run_end_to_end import run_demo
from demo.synthetic_client import generate_events


def test_synthetic_client_is_deterministic_and_privacy_safe():
    first = generate_events(scenario="mixed", steps=3, rate_per_interval=40, seed=7)
    second = generate_events(scenario="mixed", steps=3, rate_per_interval=40, seed=7)

    assert first == second
    assert first
    assert {event["source"] for event in first} == {"synthetic_client"}
    assert {event["service_id"] for event in first} <= {"fn_checkout", "fn_search", "fn_recommend"}
    assert all("user_id" not in event and "payload" not in event for event in first)
    assert all(event["invocation_count"] == 1 for event in first)


def test_generic_adapter_validates_records_and_aggregates_trace():
    events = generate_events(scenario="mixed", steps=3, rate_per_interval=30, seed=11)
    result = GenericIngestionAdapter({}).ingest(events)
    trace = records_to_trace(result, interval_s=60)

    assert result.event_count == len(events)
    assert not trace.empty
    assert {"timestamp", "function_id", "invocation_count"} <= set(trace.columns)
    assert trace["invocation_count"].sum() == len(events)

    invalid = [dict(events[0])]
    invalid[0]["invocation_count"] = -1
    with pytest.raises(IngestionValidationError):
        GenericIngestionAdapter({}).ingest(invalid)


def test_generic_adapter_requires_token_without_persisting_it(monkeypatch):
    config = {"demo": {"require_ingest_auth": True, "ingest_token_env": "M9_TEST_TOKEN"}}
    events = generate_events(scenario="mixed", steps=2, rate_per_interval=10, seed=3)
    adapter = GenericIngestionAdapter(config)

    with pytest.raises(IngestionAuthError):
        adapter.ingest(events)

    monkeypatch.setenv("M9_TEST_TOKEN", "local-test-token")
    authenticated = [dict(event, auth_token="local-test-token") for event in events]
    result = adapter.ingest(authenticated)

    assert result.auth_ok
    assert all("auth_token" not in event for event in events)


def test_run_demo_writes_end_to_end_artifacts(tmp_path, test_config):
    manifest = run_demo(
        test_config,
        tmp_path,
        steps=3,
        scenario="mixed",
        seed=42,
        use_tft=False,
    )
    output = Path(tmp_path)

    assert manifest["event_count"] > 0
    assert manifest["live_deployment"] is False
    assert manifest["evidence_tier"].startswith("simulation")
    assert (output / "run_manifest.json").exists()
    assert (output / "ingestion_schema.json").exists()
    assert (output / "events.jsonl").exists()
    assert (output / "trace.csv").exists()
    assert (output / "routing.csv").exists()
    assert (output / "decision_records.jsonl").exists()
    assert (output / "feedback.jsonl").exists()
    assert (output / "alerts.jsonl").exists()
    assert (output / "report.md").exists()
    assert (output / "figures" / "demo_timeline.png").exists()

    events = [json.loads(line) for line in (output / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert all("auth_token" not in event and "user_id" not in event for event in events)
    trace = pd.read_csv(output / "trace.csv")
    assert not trace.empty
    report = (output / "report.md").read_text(encoding="utf-8")
    assert "Presentation storyboard" in report
    assert "archive material" in report
