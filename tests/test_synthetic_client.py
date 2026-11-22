import json
from collections import Counter
from dataclasses import replace

import pytest

from demo.synthetic_client import (
    BurstWindow,
    PayloadClassSpec,
    SyntheticClientConfig,
    build_load_profile,
    generate_events,
    generate_run,
    main,
    replay_events,
)

EXPECTED_EVENT_KEYS = {
    "request_id",
    "timestamp",
    "service_id",
    "function_id",
    "payload_class",
    "invocation_count",
    "execution_duration_ms",
    "error_count",
    "source",
    "scenario",
}
FORBIDDEN_KEYS = {"user_id", "payload", "auth_token", "request_body", "body", "authorization"}


def _assert_events_private(events):
    for event in events:
        assert not FORBIDDEN_KEYS.intersection(event)
        assert isinstance(event["request_id"], str)
        assert event["source"] == "synthetic_client"


def _all_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _all_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _all_keys(item)


def test_generate_events_is_backward_compatible_deterministic_and_private():
    first = generate_events(scenario="mixed", steps=3, rate_per_interval=40, seed=7)
    second = generate_events(scenario="mixed", steps=3, rate_per_interval=40, seed=7)

    assert first == second
    assert first
    assert all(set(event) == EXPECTED_EVENT_KEYS for event in first)
    assert [event["timestamp"] for event in first] == sorted(event["timestamp"] for event in first)
    assert {event["service_id"] for event in first} <= {
        "fn_checkout",
        "fn_search",
        "fn_recommend",
    }
    assert {event["scenario"] for event in first} == {"mixed"}
    assert all(event["invocation_count"] == 1 for event in first)
    _assert_events_private(first)
    assert list(replay_events(list(reversed(first)))) == first


def test_arrival_models_are_deterministic_and_distinct():
    base = SyntheticClientConfig(scenario="mixed", steps=6, rate_per_interval=80, seed=7)
    uniform = generate_run(base)
    poisson = generate_run(replace(base, arrival_model="poisson"))

    assert generate_run(base).events == uniform.events
    assert generate_run(replace(base, arrival_model="poisson")).events == poisson.events
    assert [row["observed_invocations"] for row in uniform.profile] == [
        row["planned_invocations"] for row in uniform.profile
    ]
    assert [row["observed_invocations"] for row in poisson.profile] != [
        row["planned_invocations"] for row in poisson.profile
    ]
    assert uniform.events != poisson.events
    assert len(uniform.profile) == len(poisson.profile) == base.steps


def test_service_weights_and_payload_specs_apply():
    specs = {
        "small": PayloadClassSpec(weight=9.0, duration_ms=10.0),
        "medium": PayloadClassSpec(weight=0.5, duration_ms=100.0),
        "large": PayloadClassSpec(weight=0.5, duration_ms=200.0),
    }
    config = SyntheticClientConfig(
        scenario="mixed",
        steps=8,
        rate_per_interval=200,
        seed=7,
        services=("fn_a", "fn_b", "fn_c"),
        service_weights=(12.0, 1.0, 1.0),
        payload_specs=specs,
    )
    run = generate_run(config)

    services = Counter(event["service_id"] for event in run.events)
    payloads = Counter(event["payload_class"] for event in run.events)
    small_durations = [
        event["execution_duration_ms"] for event in run.events if event["payload_class"] == "small"
    ]

    assert services["fn_a"] > services["fn_b"] + services["fn_c"]
    assert payloads["small"] > payloads["medium"] + payloads["large"]
    assert small_durations
    assert sum(small_durations) / len(small_durations) < 25.0


def test_burst_windows_raise_counts_and_set_profile_flags():
    base = SyntheticClientConfig(scenario="mixed", steps=5, rate_per_interval=50, seed=3)
    burst = replace(base, burst_windows=(BurstWindow(2, 4, 3.0),))
    base_run = generate_run(base)
    burst_run = generate_run(burst)

    assert [row["burst"] for row in base_run.profile] == [False] * 5
    assert [row["burst"] for row in burst_run.profile] == [False, False, True, True, False]
    assert (
        burst_run.profile[2]["observed_invocations"]
        > base_run.profile[2]["observed_invocations"]
    )
    assert (
        burst_run.profile[4]["observed_invocations"]
        == base_run.profile[4]["observed_invocations"]
    )
    assert (
        burst_run.profile[2]["expected_invocations"]
        > base_run.profile[2]["expected_invocations"]
    )
    assert any(row["burst"] for row in generate_run(replace(base, scenario="burst")).profile)


def test_profile_manifest_and_replay_are_consistent():
    config = SyntheticClientConfig(
        scenario="mixed",
        steps=5,
        rate_per_interval=50,
        seed=11,
        start_time="2026-02-01T12:30:00Z",
        arrival_model="poisson",
        services=("fn_a", "fn_b"),
        service_weights=(3.0, 1.0),
        burst_windows=(BurstWindow(1, 3, 2.0),),
    )
    run = generate_run(config)

    assert run.profile == build_load_profile(config, run.events)
    assert list(replay_events(list(reversed(run.events)))) == run.events
    assert sum(row["observed_invocations"] for row in run.profile) == len(run.events)
    for row in run.profile:
        assert sum(row["service_counts"].values()) == row["observed_invocations"]
    assert run.profile[0]["window_start"] == "2026-02-01T12:30:00Z"
    assert run.manifest["config_sha256"] == generate_run(config).manifest["config_sha256"]
    assert run.manifest["events_sha256"] == generate_run(config).manifest["events_sha256"]


def test_cli_writes_deterministic_private_artifacts(tmp_path, capsys):
    args = [
        "--scenario",
        "mixed",
        "--steps",
        "4",
        "--seed",
        "7",
        "--arrival-model",
        "poisson",
        "--start-time",
        "2026-02-01T00:00:00Z",
        "--service-weight",
        "fn_checkout=4",
        "--burst-window",
        "1:2:3",
        "--error-rate",
        "0.0",
    ]
    out_dirs = [tmp_path / "first", tmp_path / "second"]
    outputs = []
    for out_dir in out_dirs:
        assert main(args + ["--out-dir", str(out_dir)]) == 0
        outputs.append(json.loads(capsys.readouterr().out))
    assert set(outputs[0]["artifacts"]) == {"events", "load_profile", "client_manifest"}

    names = ("events.jsonl", "load_profile.json", "client_manifest.json")
    for name in names:
        assert (out_dirs[0] / name).read_bytes() == (out_dirs[1] / name).read_bytes()

    first = out_dirs[0]
    events = [json.loads(line) for line in (first / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    profile = json.loads((first / "load_profile.json").read_text(encoding="utf-8"))
    manifest = json.loads((first / "client_manifest.json").read_text(encoding="utf-8"))

    assert len(profile) == 4
    assert [row["burst"] for row in profile] == [False, True, False, False]
    assert profile[0]["window_start"].startswith("2026-02-01T00:00:00")
    assert len(events) == manifest["event_count"] == sum(row["observed_invocations"] for row in profile)
    assert manifest["config"]["arrival_model"] == "poisson"
    assert manifest["config"]["start_time"] == "2026-02-01T00:00:00Z"
    assert manifest["evidence_tier"].startswith("synthetic")
    assert all(value is False for value in manifest["privacy"].values())
    _assert_events_private(events)
    assert not FORBIDDEN_KEYS.intersection(_all_keys(events + [profile, manifest]))


def test_invalid_configuration_is_rejected():
    with pytest.raises(ValueError, match="unknown arrival_model"):
        SyntheticClientConfig(arrival_model="exponential")
    with pytest.raises(ValueError, match="service_weights must match services"):
        SyntheticClientConfig(service_weights=(1.0,))
    with pytest.raises(ValueError, match="burst windows"):
        SyntheticClientConfig(burst_windows=(BurstWindow(2, 2, 3.0),))
