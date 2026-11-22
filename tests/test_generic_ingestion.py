import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from data import generic_adapter
from data.generic_adapter import (
    GenericIngestionAdapter,
    IngestEnvelope,
    IngestionAuthError,
    IngestionValidationError,
    build_json_schema,
    records_to_trace,
    write_schema,
)
from data.ingestion_schema import (
    CREDENTIAL_FIELDS,
    REQUIRED_EVENT_FIELDS,
    RESOURCE_METRIC_FIELDS,
    SCHEMA_VERSION,
    validate_event,
)
from demo.run_end_to_end import run_demo
from demo.synthetic_client import generate_events

ROOT = Path(__file__).resolve().parents[1]


def _event(**overrides):
    event = {
        "timestamp": "2026-01-05T00:00:00+00:00",
        "service_id": "checkout",
        "function_id": "fn_checkout",
        "invocation_count": 10,
        "request_id": "req-1",
        "source": "external_api",
    }
    event.update(overrides)
    return event


def _auth_config(env_name="C2_TEST_TOKEN", allowed_sources=None, payload_classes=None):
    demo = {
        "require_ingest_auth": True,
        "ingest_token_env": env_name,
        "payload_classes": payload_classes or ["small", "medium", "large"],
    }
    if allowed_sources is not None:
        demo["allowed_ingest_sources"] = allowed_sources
    return {"demo": demo}


def _metric_event(function_id, request_id, **metrics):
    return _event(function_id=function_id, request_id=request_id, **metrics)


def test_json_schema_contract_is_stable_and_generated(tmp_path):
    schema = build_json_schema()
    assert schema["version"] == SCHEMA_VERSION == "m9-event-v1"
    assert schema["required"] == list(REQUIRED_EVENT_FIELDS)
    assert all(field in schema["properties"] for field in RESOURCE_METRIC_FIELDS)
    assert schema["privacy"]["allow_auth_data_in_artifacts"] is False
    assert schema["auth"]["comparison"] == "hmac.compare_digest"
    assert "IngestEnvelope" in schema["$defs"]

    target = write_schema(tmp_path / "nested" / "ingestion_schema.json")
    written = target.read_text(encoding="utf-8")
    assert json.loads(written)["version"] == SCHEMA_VERSION
    assert "s3cret" not in written


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda e: e.pop("timestamp"), "missing fields"),
        (lambda e: e.update(timestamp="not-a-date"), "invalid ISO-8601"),
        (lambda e: e.update(service_id="   "), "empty service_id"),
        (lambda e: e.update(invocation_count=-1), "below 0"),
        (lambda e: e.update(invocation_count="abc"), "non-numeric"),
        (lambda e: e.update(execution_duration_ms=float("nan")), "non-finite"),
        (lambda e: e.update(payload_class="huge"), "unknown payload class"),
        (lambda e: e.update(source="   "), "empty source"),
        (lambda e: e.update(cpu_utilization=1.5), "above 1"),
        (lambda e: e.update(power_w="high"), "non-numeric"),
    ],
)
def test_validate_event_reports_clear_errors(mutate, message):
    event = _event()
    mutate(event)
    with pytest.raises(IngestionValidationError, match=message):
        validate_event(event)


def test_validate_event_rejects_non_mapping_and_strips_credentials():
    with pytest.raises(IngestionValidationError, match="must be a mapping"):
        validate_event(["not", "an", "event"])
    validated = validate_event(_event(auth_token="s3cret", api_key="s3cret"))
    assert not any(field in validated for field in (*CREDENTIAL_FIELDS, "api_key"))


def test_envelope_auth_uses_constant_time_comparison(monkeypatch):
    monkeypatch.setenv("C2_TEST_TOKEN", "s3cret")
    calls = []
    original = generic_adapter.hmac.compare_digest

    def recording(candidate, expected):
        calls.append((candidate, expected))
        return original(candidate, expected)

    monkeypatch.setattr(generic_adapter.hmac, "compare_digest", recording)
    adapter = GenericIngestionAdapter(_auth_config())
    envelope = IngestEnvelope(records=[_event()], auth_token="Bearer s3cret")

    assert adapter.ingest(envelope).auth_ok
    assert calls == [("s3cret", "s3cret")]

    with pytest.raises(IngestionAuthError, match="invalid ingestion token"):
        adapter.ingest(IngestEnvelope(records=[_event()], auth_token="wrong"))
    with pytest.raises(IngestionAuthError, match="missing ingestion token"):
        adapter.ingest(IngestEnvelope(records=[_event()]))
    with pytest.raises(IngestionAuthError, match="missing ingestion token in environment"):
        GenericIngestionAdapter(_auth_config("C2_MISSING_TOKEN")).ingest(envelope)


def test_legacy_record_tokens_accepted_but_never_persisted(monkeypatch, tmp_path):
    monkeypatch.setenv("C2_TEST_TOKEN", "s3cret")
    adapter = GenericIngestionAdapter(_auth_config())
    records = [
        _event(request_id="req-1", auth_token="s3cret"),
        _event(request_id="req-2", auth_token="Bearer s3cret"),
    ]

    result = adapter.ingest(records)
    trace = records_to_trace(result)
    schema_path = write_schema(tmp_path / "ingestion_schema.json")

    assert result.event_count == 2
    assert not any(
        field in event
        for event in result.events.to_dict(orient="records")
        for field in CREDENTIAL_FIELDS
    )
    assert not any(field in trace.columns for field in CREDENTIAL_FIELDS)
    assert "s3cret" not in trace.to_csv(index=False)
    assert "s3cret" not in schema_path.read_text(encoding="utf-8")

    with pytest.raises(IngestionAuthError, match="invalid ingestion token"):
        adapter.ingest([_event(auth_token="wrong-token")])
    with pytest.raises(IngestionAuthError, match="conflicting ingestion tokens"):
        adapter.ingest(IngestEnvelope(records=records, auth_token="different"))


def test_allowed_sources_and_source_metadata_are_preserved():
    adapter = GenericIngestionAdapter(
        {"demo": {"allowed_ingest_sources": ["synthetic_client", "external_api"]}}
    )
    result = adapter.ingest(
        [
            _event(source="external_api", scenario="burst"),
            _event(request_id="req-2", source="synthetic_client"),
        ]
    )
    trace = records_to_trace(result)

    assert set(result.events["source"]) == {"external_api", "synthetic_client"}
    assert set(trace["source"]) == {"external_api|synthetic_client"}
    assert "scenario" in trace.columns
    assert trace[trace["function_id"] == "fn_checkout"]["scenario"].iloc[0] == "burst"

    with pytest.raises(IngestionValidationError, match="not in allowed sources"):
        adapter.ingest([_event(source="untrusted_client")])
    with pytest.raises(IngestionValidationError, match="not in allowed sources"):
        adapter.ingest(IngestEnvelope(records=[_event()], source="untrusted_client"))

    envelope_result = GenericIngestionAdapter({}).ingest(
        IngestEnvelope(records=[_event(source="unknown")], source="external_api")
    )
    assert set(envelope_result.events["source"]) == {"external_api"}


def test_observed_metrics_preserved_and_missing_metrics_derived_with_labels():
    observed = _metric_event(
        "fn_observed",
        "obs-1",
        cpu_utilization=0.44,
        memory_utilization=0.63,
        latency_ms=91.0,
        p95_latency_ms=130.0,
        power_w=88.0,
        active_containers=6,
        warm_containers=5,
        cold_starts=2,
    )
    derived = _metric_event("fn_derived", "der-1")
    partial = _metric_event("fn_mixed", "mix-1", cpu_utilization=0.30)
    partial_missing = _metric_event("fn_mixed", "mix-2")

    trace = records_to_trace(
        GenericIngestionAdapter({}).ingest([observed, derived, partial, partial_missing])
    ).set_index("function_id")
    expected_derived_cpu = 0.12 + 0.62 * (10 / 200.0)

    assert trace.loc["fn_observed", "metrics_source"] == "observed"
    assert trace.loc["fn_derived", "metrics_source"] == "derived"
    assert trace.loc["fn_mixed", "metrics_source"] == "mixed"
    for field, value in {
        "cpu_utilization": 0.44,
        "memory_utilization": 0.63,
        "latency_ms": 91.0,
        "p95_latency_ms": 130.0,
        "power_w": 88.0,
        "active_containers": 6,
        "warm_containers": 5,
        "cold_starts": 2,
    }.items():
        assert trace.loc["fn_observed", field] == pytest.approx(value)
    assert trace.loc["fn_derived", "cpu_utilization"] == pytest.approx(expected_derived_cpu)
    assert trace.loc["fn_derived", "latency_ms"] == pytest.approx(70.0 + 75.0 * (10 / 200.0))
    assert trace.loc["fn_derived", "cold_starts"] == 0
    assert trace.loc["fn_mixed", "cpu_utilization"] == pytest.approx(0.30)
    assert trace.loc["fn_mixed", "memory_utilization"] == pytest.approx(0.20 + 0.52 * (20 / 200.0))
    assert set(trace["metrics_source"]) <= {"observed", "derived", "mixed"}


def test_observed_metrics_aggregate_by_sum_mean_and_max():
    first = _metric_event(
        "fn_group",
        "a",
        cpu_utilization=0.2,
        memory_utilization=0.5,
        latency_ms=80.0,
        p95_latency_ms=100.0,
        power_w=60.0,
        active_containers=4,
        warm_containers=3,
        cold_starts=1,
    )
    second = _metric_event(
        "fn_group",
        "b",
        cpu_utilization=0.4,
        memory_utilization=0.7,
        latency_ms=100.0,
        p95_latency_ms=140.0,
        power_w=80.0,
        active_containers=7,
        warm_containers=6,
        cold_starts=2,
    )
    trace = records_to_trace(GenericIngestionAdapter({}).ingest([first, second]))

    assert len(trace) == 1
    assert trace.loc[0, "cpu_utilization"] == pytest.approx(0.3)
    assert trace.loc[0, "memory_utilization"] == pytest.approx(0.6)
    assert trace.loc[0, "latency_ms"] == pytest.approx(90.0)
    assert trace.loc[0, "p95_latency_ms"] == pytest.approx(120.0)
    assert trace.loc[0, "power_w"] == pytest.approx(70.0)
    assert trace.loc[0, "active_containers"] == 7
    assert trace.loc[0, "warm_containers"] == 6
    assert trace.loc[0, "cold_starts"] == 3
    assert trace.loc[0, "metrics_source"] == "observed"


def test_cli_ingests_jsonl_with_tokens_only_from_env_or_stdin(tmp_path, monkeypatch):
    token = "cli-secret-token"
    config = tmp_path / "c2_config.yaml"
    config.write_text(
        "demo:\n  require_ingest_auth: true\n  ingest_token_env: C2_CLI_TOKEN\n  interval_s: 60\n",
        encoding="utf-8",
    )
    records = [
        _event(request_id="a", auth_token=token),
        _event(request_id="b", auth_token=token, cpu_utilization=0.4),
    ]
    input_path = tmp_path / "events.jsonl"
    input_path.write_text("".join(json.dumps(row) + "\n" for row in records), encoding="utf-8")
    out = tmp_path / "trace.csv"
    schema = tmp_path / "ingestion_schema.json"
    monkeypatch.setenv("C2_CLI_TOKEN", token)

    command = [
        sys.executable,
        "-m",
        "data.generic_adapter",
        "--input",
        str(input_path),
        "--out",
        str(out),
        "--schema",
        str(schema),
        "--config",
        str(config),
    ]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert '"event_count": 2' in result.stdout
    assert token not in result.stdout
    assert token not in out.read_text(encoding="utf-8")
    assert token not in schema.read_text(encoding="utf-8")
    trace = pd.read_csv(out)
    assert {"metrics_source", "source"} <= set(trace.columns)
    assert set(trace["metrics_source"]) == {"mixed"}

    envelope_path = tmp_path / "envelope.jsonl"
    envelope_path.write_text(
        json.dumps({"records": [_event(request_id="c"), _event(request_id="d")], "source": "external_api"})
        + "\n",
        encoding="utf-8",
    )
    stdin_command = [
        sys.executable,
        "-m",
        "data.generic_adapter",
        "--input",
        str(envelope_path),
        "--out",
        str(tmp_path / "envelope_trace.csv"),
        "--config",
        str(config),
        "--token-stdin",
    ]
    stdin_result = subprocess.run(
        stdin_command, cwd=ROOT, input=token + "\n", capture_output=True, text=True, check=False
    )
    assert stdin_result.returncode == 0, stdin_result.stderr
    envelope_trace = pd.read_csv(tmp_path / "envelope_trace.csv")
    assert set(envelope_trace["source"]) == {"external_api"}
    assert set(envelope_trace["metrics_source"]) == {"derived"}

    rejected = subprocess.run(
        command + ["--token", token], cwd=ROOT, capture_output=True, text=True, check=False
    )
    assert rejected.returncode != 0
    assert "unrecognized arguments" in rejected.stderr


def test_m9_legacy_call_shape_still_works(tmp_path):
    events = generate_events(scenario="mixed", steps=2, rate_per_interval=5, seed=7)
    result = GenericIngestionAdapter({}).ingest(events)
    trace = records_to_trace(result, interval_s=60)
    schema = write_schema(tmp_path / "ingestion_schema.json")

    assert result.auth_ok is True
    assert result.event_count == len(events)
    assert trace["invocation_count"].sum() == len(events)
    assert pd.api.types.is_datetime64_any_dtype(trace["timestamp"])
    assert {"timestamp", "function_id", "invocation_count", "metrics_source"} <= set(trace.columns)
    assert set(trace["metrics_source"]) == {"derived"}
    assert json.loads(schema.read_text(encoding="utf-8"))["version"] == SCHEMA_VERSION


def test_demo_artifacts_never_contain_the_auth_token(tmp_path, test_config, monkeypatch):
    token = "manifest-secret-token"
    test_config["demo"]["require_ingest_auth"] = True
    test_config["demo"]["ingest_token_env"] = "C2_DEMO_TOKEN"
    monkeypatch.setenv("C2_DEMO_TOKEN", token)

    manifest = run_demo(test_config, tmp_path, steps=2, scenario="mixed", seed=5, use_tft=False)

    assert manifest["auth_ok"] is True
    assert token not in json.dumps(manifest)
    for path in Path(tmp_path).rglob("*"):
        if path.is_file() and path.suffix in {".json", ".jsonl", ".csv", ".md"}:
            assert token not in path.read_text(encoding="utf-8"), path
