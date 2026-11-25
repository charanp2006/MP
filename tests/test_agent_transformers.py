import json
from collections import UserDict
from types import SimpleNamespace

import pytest

from agent import planner as planner_module
from agent.planner import PlannerError, Qwen3TransformersPlanner, build_planner


PLAN_PAYLOAD = {
    "strategy": "ScaleOut",
    "desired_capacity_change": 2,
    "priority": "sla",
    "urgency": "high",
    "reason": "forecast peak exceeds current load",
    "constraints_respected": True,
}


class _FakeTensor:
    def __init__(self, values):
        self.values = values
        if values and isinstance(values[0], list):
            self.shape = (len(values), len(values[0]))
        else:
            self.shape = (len(values),)

    def to(self, device):
        self.device = device
        return self

    def __getitem__(self, key):
        if isinstance(key, int):
            return _FakeTensor([self.values[key]])
        if isinstance(key, slice):
            if self.values and isinstance(self.values[0], list):
                return _FakeTensor([row[key] for row in self.values])
            return _FakeTensor(self.values[key])
        return _FakeTensor(self.values)


class _FakeBatchEncoding(UserDict):
    pass


class _FakeTokenizer:
    def __init__(self, response_text):
        self.response_text = response_text
        self.eos_token_id = 2
        self.calls = {}

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False, **kwargs):
        self.calls["messages"] = messages
        self.calls["enable_thinking"] = kwargs.get("enable_thinking")
        return "rendered prompt"

    def __call__(self, text, return_tensors=None):
        self.calls["prompt"] = text
        return _FakeBatchEncoding(
            {
                "input_ids": _FakeTensor([[1, 2, 3]]),
                "attention_mask": _FakeTensor([[1, 1, 1]]),
            }
        )

    def decode(self, tokens, skip_special_tokens=True):
        self.calls["decoded"] = tokens
        return self.response_text


class _FakeModel:
    def __init__(self):
        self.generate_calls = {}
        self.device = None

    def to(self, device):
        self.device = device
        return self

    def generate(self, **kwargs):
        self.generate_calls = kwargs
        return _FakeTensor([[1, 2, 3, 4, 5]])


class _FakeNoGrad:
    def __enter__(self):
        return None

    def __exit__(self, *args):
        return False


class _FakeAutoTokenizer:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.load_kwargs = None

    def from_pretrained(self, model_id, **kwargs):
        self.load_kwargs = kwargs
        self.model_id = model_id
        return self.tokenizer


class _FakeAutoModel:
    def __init__(self, model):
        self.model = model
        self.load_kwargs = None

    def from_pretrained(self, model_id, **kwargs):
        self.load_kwargs = kwargs
        self.model_id = model_id
        return self.model


def _config(test_config, response_text=None):
    config = json.loads(json.dumps(test_config))
    agent = config["agent"]
    agent["runtime"] = "transformers"
    agent["provider"] = "transformers"
    agent["transformers"] = {
        "model_id": "owner/qwen3-local-test",
        "revision": "rev-local",
        "cache_dir": "models/qwen3-cache",
        "device": "cpu",
        "dtype": "float32",
        "local_files_only": True,
        "trust_remote_code": False,
        "max_new_tokens": 32,
        "temperature": 0.0,
        "enable_thinking": False,
    }
    return config


def _install_fake_transformers(monkeypatch, response_text, version="0"):
    tokenizer = _FakeTokenizer(response_text)
    model = _FakeModel()
    auto_tokenizer = _FakeAutoTokenizer(tokenizer)
    auto_model = _FakeAutoModel(model)
    torch = SimpleNamespace(no_grad=_FakeNoGrad, float32=object())
    transformers = SimpleNamespace(
        AutoTokenizer=auto_tokenizer,
        AutoModelForCausalLM=auto_model,
        __version__=version,
    )

    def _import_module(name):
        if name == "torch":
            return torch
        if name == "transformers":
            return transformers
        raise ImportError(f"unexpected import {name}")

    monkeypatch.setattr(
        planner_module,
        "importlib",
        SimpleNamespace(import_module=_import_module),
    )
    return tokenizer, model, auto_tokenizer, auto_model


def test_transformers_planner_parses_plan_and_records_usage(monkeypatch, test_config, state_factory):
    tokenizer, model, auto_tokenizer, auto_model = _install_fake_transformers(
        monkeypatch, json.dumps(PLAN_PAYLOAD)
    )
    planner = Qwen3TransformersPlanner(_config(test_config))

    plan = planner.plan(state_factory())
    record = planner.last_record.to_dict()

    assert plan.strategy == "ScaleOut"
    assert plan.desired_capacity_change == 2
    assert record["provider"] == "transformers"
    assert record["model"] == "owner/qwen3-local-test"
    assert record["revision"] == "rev-local"
    assert record["status"] == "ok"
    assert record["usage"] == {
        "prompt_tokens": 3,
        "completion_tokens": 2,
        "total_tokens": 5,
    }
    assert tokenizer.calls["enable_thinking"] is False
    assert model.generate_calls["max_new_tokens"] == 32
    assert model.generate_calls["do_sample"] is False
    assert model.device == "cpu"
    assert auto_tokenizer.load_kwargs == {
        "revision": "rev-local",
        "cache_dir": "models/qwen3-cache",
        "local_files_only": True,
    }
    assert "torch_dtype" in auto_model.load_kwargs


def test_transformers_planner_uses_dtype_for_modern_transformers(monkeypatch, test_config, state_factory):
    _, _, _, auto_model = _install_fake_transformers(
        monkeypatch, json.dumps(PLAN_PAYLOAD), version="4.57.6"
    )
    planner = Qwen3TransformersPlanner(_config(test_config))

    planner.plan(state_factory())

    assert "dtype" in auto_model.load_kwargs
    assert "torch_dtype" not in auto_model.load_kwargs


def test_transformers_planner_accepts_thinking_wrapper_and_extracts_json(
    monkeypatch, test_config, state_factory
):
    _install_fake_transformers(
        monkeypatch,
        "<think>internal planning notes</think>\n" + json.dumps(PLAN_PAYLOAD),
    )
    planner = Qwen3TransformersPlanner(_config(test_config))

    plan = planner.plan(state_factory())

    assert plan.strategy == "ScaleOut"
    assert planner.last_record.status == "ok"


def test_transformers_planner_rejects_invalid_output(monkeypatch, test_config, state_factory):
    _install_fake_transformers(monkeypatch, "I cannot help with that")
    planner = Qwen3TransformersPlanner(_config(test_config))

    with pytest.raises(PlannerError, match="invalid_plan"):
        planner.plan(state_factory())

    assert planner.last_record.status == "error"
    assert "invalid_plan" in planner.last_record.reason


def test_transformers_missing_dependency_falls_back_to_stub(monkeypatch, test_config, state_factory):
    def _import_module(name):
        if name == "torch":
            return SimpleNamespace(float32=object())
        raise ImportError("transformers is not installed")

    monkeypatch.setattr(
        planner_module,
        "importlib",
        SimpleNamespace(import_module=_import_module),
    )
    planner = build_planner(_config(test_config), with_fallback=True)

    plan = planner.plan(state_factory())

    assert plan.strategy in {"NoOp", "PreWarm", "ScaleOut", "ScaleIn"}
    assert planner.last_fallback is True
    assert "local_model_load_failed" in planner.last_error


def test_build_planner_selects_transformers(test_config):
    config = _config(test_config)

    planner = build_planner(config, with_fallback=False)

    assert isinstance(planner, Qwen3TransformersPlanner)
