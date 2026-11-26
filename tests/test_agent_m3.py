import json
import urllib.error
import urllib.request

import pytest

from agent.planner import (
    HostedQwen3Planner,
    PlannerError,
    ProviderChainPlanner,
    build_planner,
)
from agent.schemas import STRATEGIES
from agent.telemetry import redact_text


PLAN_PAYLOAD = {
    "strategy": "prewarm",
    "desired_capacity_change": 0,
    "priority": "sla",
    "urgency": "high",
    "reason": "forecast increase",
    "constraints_respected": True,
}


class _Response:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _chat_response(payload=None):
    return {
        "choices": [{"message": {"content": json.dumps(payload or PLAN_PAYLOAD)}}],
        "usage": {"prompt_tokens": 12, "completion_tokens": 5, "total_tokens": 17},
    }


def _config(test_config, provider="huggingface"):
    config = json.loads(json.dumps(test_config))
    agent = config["agent"]
    agent["provider"] = provider
    agent["runtime"] = provider
    agent["fallback_provider"] = "openrouter"
    agent["huggingface"] = {
        "endpoint_url": "https://hf.test/v1/chat/completions",
        "model_id": "owner/qwen3-test",
        "revision": "rev-123",
        "timeout_s": 5,
        "max_retries": 1,
        "retry_delay_s": 0.0,
        "temperature": 0.0,
        "max_tokens": 128,
    }
    agent["openrouter"] = {
        "endpoint_url": "https://openrouter.test/api/v1/chat/completions",
        "model": "fallback/qwen3-test",
        "timeout_s": 5,
        "max_retries": 1,
        "retry_delay_s": 0.0,
        "temperature": 0.0,
        "max_tokens": 128,
    }
    return config


@pytest.fixture(autouse=True)
def _clear_hosted_env(monkeypatch):
    for name in (
        "HF_ENDPOINT_URL",
        "HF_TOKEN",
        "HF_MODEL_ID",
        "HF_MODEL_REVISION",
        "OPENROUTER_ENDPOINT_URL",
        "OPENROUTER_API_KEY",
        "OPENROUTER_MODEL",
        "OPENROUTER_MODEL_REVISION",
        "OPENROUTER_SITE_URL",
    ):
        monkeypatch.delenv(name, raising=False)


def test_huggingface_adapter_parses_chat_response_and_records_usage(
    monkeypatch, test_config, state_factory
):
    config = _config(test_config)
    seen = {}

    def _post(request, timeout):
        seen["url"] = request.full_url
        seen["model"] = json.loads(request.data.decode("utf-8"))["model"]
        return _Response(_chat_response())

    monkeypatch.setattr(urllib.request, "urlopen", _post)
    planner = HostedQwen3Planner(config, provider="huggingface")

    plan = planner.plan(state_factory())
    record = planner.last_record.to_dict()

    assert plan.strategy == "PreWarm"
    assert plan.strategy in STRATEGIES
    assert seen["url"] == "https://hf.test/v1/chat/completions"
    assert seen["model"] == "owner/qwen3-test@rev-123"
    assert record["provider"] == "huggingface"
    assert record["model"] == "owner/qwen3-test@rev-123"
    assert record["revision"] == "rev-123"
    assert record["usage"] == {"prompt_tokens": 12, "completion_tokens": 5, "total_tokens": 17}
    assert record["attempts"] == 1


def test_openrouter_adapter_reads_secret_and_model_from_env(
    monkeypatch, test_config, state_factory
):
    config = _config(test_config, provider="openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "secret-token-123")
    monkeypatch.setenv("OPENROUTER_MODEL", "qwen3-env-model")
    seen = {}

    def _post(request, timeout):
        seen["headers"] = {key.lower(): value for key, value in request.header_items()}
        seen["model"] = json.loads(request.data.decode("utf-8"))["model"]
        return _Response(_chat_response())

    monkeypatch.setattr(urllib.request, "urlopen", _post)
    planner = HostedQwen3Planner(config, provider="openrouter")

    plan = planner.plan(state_factory())
    record = json.dumps(planner.last_record.to_dict())

    assert plan.strategy == "PreWarm"
    assert seen["model"] == "qwen3-env-model"
    assert seen["headers"]["authorization"] == "Bearer secret-token-123"
    assert "secret-token-123" not in record
    assert "openrouter" in record


def test_rate_limit_is_retried_with_bounded_attempts(monkeypatch, test_config, state_factory):
    config = _config(test_config)
    calls = []

    def _post(request, timeout):
        calls.append(request.full_url)
        if len(calls) == 1:
            raise urllib.error.HTTPError(
                request.full_url, 429, "rate limited", {}, None
            )
        return _Response(_chat_response())

    monkeypatch.setattr(urllib.request, "urlopen", _post)
    planner = HostedQwen3Planner(config, provider="huggingface")

    plan = planner.plan(state_factory())

    assert plan.strategy == "PreWarm"
    assert len(calls) == 2
    assert planner.last_record.status == "ok"
    assert planner.last_record.attempts == 2


def test_auth_failure_is_not_retried_and_is_redacted(monkeypatch, test_config, state_factory):
    config = _config(test_config)
    calls = []

    def _post(request, timeout):
        calls.append(request.full_url)
        raise urllib.error.HTTPError(
            request.full_url, 401, "unauthorized api_key=SECRET", {}, None
        )

    monkeypatch.setattr(urllib.request, "urlopen", _post)
    planner = HostedQwen3Planner(config, provider="huggingface")

    with pytest.raises(PlannerError):
        planner.plan(state_factory())

    assert len(calls) == 1
    record = json.dumps(planner.last_record.to_dict())
    assert "SECRET" not in record
    assert "[REDACTED]" in record
    assert planner.last_record.attempts == 1


def test_malformed_provider_output_is_not_retried(monkeypatch, test_config, state_factory):
    config = _config(test_config)
    calls = []

    def _post(request, timeout):
        calls.append(request.full_url)
        return _Response({"choices": [{"message": {"content": "not json"}}]})

    monkeypatch.setattr(urllib.request, "urlopen", _post)
    planner = HostedQwen3Planner(config, provider="huggingface")

    with pytest.raises(PlannerError):
        planner.plan(state_factory())

    assert len(calls) == 1
    assert "malformed_json" in planner.last_record.reason


def test_provider_chain_falls_back_from_huggingface_to_openrouter(
    monkeypatch, test_config, state_factory
):
    config = _config(test_config)

    def _post(request, timeout):
        if "hf.test" in request.full_url:
            raise urllib.error.HTTPError(
                request.full_url, 503, "endpoint unavailable", {}, None
            )
        return _Response(_chat_response())

    monkeypatch.setattr(urllib.request, "urlopen", _post)
    planner = build_planner(config)

    plan = planner.plan(state_factory())
    record = planner.last_record.to_dict()

    assert isinstance(planner, ProviderChainPlanner)
    assert plan.strategy == "PreWarm"
    assert record["provider"] == "openrouter"
    assert record["status"] == "fallback"
    assert record["fallback"] is True
    assert "huggingface" in record["reason"]


def test_provider_chain_ends_at_deterministic_stub(monkeypatch, test_config, state_factory):
    config = _config(test_config)

    def _down(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 500, "server error", {}, None)

    monkeypatch.setattr(urllib.request, "urlopen", _down)
    planner = build_planner(config)

    plan = planner.plan(state_factory(forecast_peak=1200.0, trend="increasing"))
    record = planner.last_record.to_dict()

    assert plan.strategy in STRATEGIES
    assert record["provider"] == "stub"
    assert record["status"] == "fallback"
    assert record["fallback"] is True
    assert planner.last_fallback is True


def test_hosted_timeout_is_retryable_and_redacted(monkeypatch, test_config, state_factory):
    config = _config(test_config)
    calls = []

    def _post(request, timeout):
        calls.append(timeout)
        raise TimeoutError("token=hf_secret_123 timed out")

    monkeypatch.setattr(urllib.request, "urlopen", _post)
    planner = HostedQwen3Planner(config, provider="huggingface")

    with pytest.raises(PlannerError):
        planner.plan(state_factory())

    assert calls == [5, 5]
    assert planner.last_record.status == "error"
    assert planner.last_record.attempts == 2
    record = json.dumps(planner.last_record.to_dict())
    assert "hf_secret_123" not in record
    assert "[REDACTED]" in record


def test_request_timeout_is_retryable(monkeypatch, test_config, state_factory):
    config = _config(test_config)
    calls = []

    def _post(request, timeout):
        calls.append(request.full_url)
        if len(calls) == 1:
            raise urllib.error.HTTPError(request.full_url, 408, "request timeout", {}, None)
        return _Response(_chat_response())

    monkeypatch.setattr(urllib.request, "urlopen", _post)
    planner = HostedQwen3Planner(config, provider="huggingface")

    plan = planner.plan(state_factory())

    assert plan.strategy == "PreWarm"
    assert len(calls) == 2
    assert planner.last_record.status == "ok"
    assert planner.last_record.attempts == 2


def test_forbidden_response_is_not_retried_and_redacts_bearer_secret(
    monkeypatch, test_config, state_factory
):
    config = _config(test_config)
    calls = []

    def _post(request, timeout):
        calls.append(request.full_url)
        raise urllib.error.HTTPError(
            request.full_url, 403, "Authorization: Bearer bearer_secret_999", {}, None
        )

    monkeypatch.setattr(urllib.request, "urlopen", _post)
    planner = HostedQwen3Planner(config, provider="huggingface")

    with pytest.raises(PlannerError):
        planner.plan(state_factory())

    assert len(calls) == 1
    record = json.dumps(planner.last_record.to_dict())
    assert "bearer_secret_999" not in record
    assert "[REDACTED]" in record
    assert planner.last_record.attempts == 1


def test_schema_invalid_plan_is_not_retried(monkeypatch, test_config, state_factory):
    config = _config(test_config)
    calls = []
    payload = dict(PLAN_PAYLOAD)
    payload["strategy"] = "TerminateCluster"

    def _post(request, timeout):
        calls.append(request.full_url)
        return _Response(_chat_response(payload))

    monkeypatch.setattr(urllib.request, "urlopen", _post)
    planner = HostedQwen3Planner(config, provider="huggingface")

    with pytest.raises(PlannerError):
        planner.plan(state_factory())

    assert len(calls) == 1
    assert "invalid_plan" in planner.last_record.reason
    assert planner.last_record.attempts == 1


def test_unexpected_provider_response_shape_is_not_retried(
    monkeypatch, test_config, state_factory
):
    config = _config(test_config)
    calls = []

    def _post(request, timeout):
        calls.append(request.full_url)
        return _Response({"choices": [{"message": {}}]})

    monkeypatch.setattr(urllib.request, "urlopen", _post)
    planner = HostedQwen3Planner(config, provider="huggingface")

    with pytest.raises(PlannerError):
        planner.plan(state_factory())

    assert len(calls) == 1
    assert "unexpected provider response shape" in planner.last_record.reason
    assert planner.last_record.attempts == 1


def test_redact_text_handles_bearer_and_provider_tokens():
    redacted = redact_text(
        "Authorization: Bearer hf_abcdefgh1234 source sk-or-v1-abcdefgh1234"
    )

    assert "hf_abcdefgh1234" not in redacted
    assert "sk-or-v1-abcdefgh1234" not in redacted
    assert "[REDACTED]" in redacted
