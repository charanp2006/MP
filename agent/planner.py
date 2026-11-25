"""Qwen3 planner adapters plus a deterministic offline stub (design.md section 8).

The planner is a *high-level* component: it returns a validated :class:`Plan`,
never shell or Kubernetes commands. Current V2 providers are Hugging Face-hosted
Qwen3 (primary), OpenRouter (backup) and local Transformers (opt-in demo).
Historical Ollama support and the deterministic stub remain for compatibility
and fail-safe fallback.
"""

from __future__ import annotations

import copy
import importlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from collections.abc import Mapping
from typing import Any, Dict, Optional, Protocol

from pydantic import ValidationError

from agent.prompts import PROMPT_VERSION, build_user_prompt, load_system_prompt
from agent.schemas import Plan, StateSnapshot
from agent.telemetry import PlannerCallRecord, now_ms, redact_text


class PlannerError(RuntimeError):
    """Raised when a planner cannot produce a usable plan."""


class PlannerProviderError(PlannerError):
    """Provider failure with retry classification for hosted inference."""

    def __init__(self, message: str, *, retryable: bool = False, status: str = "error") -> None:
        super().__init__(message)
        self.retryable = retryable
        self.status = status


def _classify_provider_error(exc: Exception) -> PlannerProviderError:
    if isinstance(exc, PlannerProviderError):
        return exc

    code = getattr(exc, "code", None)
    if isinstance(code, int):
        detail = redact_text(exc)
        if code in {401, 403}:
            return PlannerProviderError(
                f"auth_failed http_{code}: {detail}", retryable=False, status="auth"
            )
        if code == 429:
            return PlannerProviderError(
                f"rate_limited http_429: {detail}", retryable=True, status="rate_limit"
            )
        if code == 408 or 500 <= code < 600:
            return PlannerProviderError(
                f"provider_unavailable http_{code}: {detail}",
                retryable=True,
                status="unavailable",
            )
        return PlannerProviderError(
            f"provider_error http_{code}: {detail}", retryable=False, status="error"
        )

    if isinstance(exc, (TimeoutError, urllib.error.URLError)):
        return PlannerProviderError(
            f"provider_network_failure: {redact_text(exc)}",
            retryable=True,
            status="unavailable",
        )
    return PlannerProviderError(f"provider_failure: {redact_text(exc)}", retryable=False)


class Planner(Protocol):
    def plan(self, state: StateSnapshot) -> Plan: ...


class StubPlanner:
    """Deterministic, offline planner used by tests and as a safe fallback."""

    def __init__(self, config: Optional[Dict] = None) -> None:
        config = config or {}
        containers = config.get("containers", {})
        sla = config.get("sla", {})
        agent = config.get("agent", {})

        self.min_capacity = int(containers.get("min", 2))
        self.max_capacity = int(containers.get("max", 30))
        self.max_change = max(1, int(containers.get("max_change_per_cycle", 5)))
        self.safety_margin = float(sla.get("safety_margin_ms", 0.0))
        self.high_ratio = float(agent.get("high_demand_ratio", 1.10))
        self.low_ratio = float(agent.get("low_demand_ratio", 0.90))
        self.last_record: Optional[PlannerCallRecord] = None

    def _scale_out_change(self, state: StateSnapshot) -> int:
        room = max(0, self.max_capacity - state.active_containers)
        return min(self.max_change, room)

    def _scale_in_change(self, state: StateSnapshot) -> int:
        room = max(0, state.active_containers - self.min_capacity)
        return -min(self.max_change, room)

    def _decide(self, state: StateSnapshot) -> Plan:
        ratio = state.forecast_peak / max(state.current_workload, 1.0)
        sla_risk = state.sla_margin_ms <= self.safety_margin

        if sla_risk:
            change = self._scale_out_change(state)
            if change > 0 and (ratio >= 1.0 or state.trend == "increasing"):
                return Plan(
                    strategy="ScaleOut",
                    desired_capacity_change=change,
                    priority="sla",
                    urgency="high",
                    reason="P95 is at/near the SLA threshold and demand is not falling",
                    constraints_respected=True,
                )
            return Plan(
                strategy="PreWarm",
                desired_capacity_change=0,
                priority="sla",
                urgency="high",
                reason="P95 is at/near the SLA threshold; warm capacity without scaling",
                constraints_respected=True,
            )

        if ratio >= self.high_ratio or (state.trend == "increasing" and ratio > 1.0):
            change = self._scale_out_change(state)
            if change > 0:
                return Plan(
                    strategy="ScaleOut",
                    desired_capacity_change=change,
                    priority="sla",
                    urgency="high",
                    reason=f"forecast peak is {ratio:.2f}x current workload",
                    constraints_respected=True,
                )
            return Plan(
                strategy="PreWarm",
                desired_capacity_change=0,
                priority="balanced",
                urgency="medium",
                reason="demand is rising but capacity is already at the maximum",
                constraints_respected=True,
            )

        if ratio <= self.low_ratio and state.sla_margin_ms > self.safety_margin:
            change = self._scale_in_change(state)
            if change < 0:
                return Plan(
                    strategy="ScaleIn",
                    desired_capacity_change=change,
                    priority="energy",
                    urgency="low",
                    reason="demand is falling with comfortable SLA headroom",
                    constraints_respected=True,
                )

        if state.cpu_utilization >= 0.75 and state.active_containers < self.max_capacity:
            change = self._scale_out_change(state)
            if change > 0:
                return Plan(
                    strategy="ScaleOut",
                    desired_capacity_change=change,
                    priority="sla",
                    urgency="medium",
                    reason="CPU utilization is high",
                    constraints_respected=True,
                )

        return Plan(
            strategy="NoOp",
            desired_capacity_change=0,
            priority="balanced",
            urgency="low",
            reason="no significant forecast or SLA pressure",
            constraints_respected=True,
        )

    def plan(self, state: StateSnapshot) -> Plan:
        start = now_ms()
        plan = self._decide(state)
        self.last_record = PlannerCallRecord(
            provider="stub",
            model="stub",
            prompt_version="n/a",
            status="ok",
            latency_ms=now_ms() - start,
            fallback=False,
            strategy=plan.strategy,
        )
        return plan


class Qwen3OllamaPlanner:
    """Real Qwen3 planner backed by a local Ollama server."""

    def __init__(self, config: Optional[Dict] = None) -> None:
        config = config or {}
        agent = config.get("agent", {})
        self.base_url = str(agent.get("base_url", "http://localhost:11434")).rstrip("/")
        self.model = str(agent.get("model", "qwen3:4b"))
        self.timeout_s = float(agent.get("timeout_s", 30))
        self.temperature = float(agent.get("temperature", 0.0))
        self.num_predict = int(agent.get("num_predict", 256))
        self.prompt_version = str(agent.get("prompt_version", PROMPT_VERSION))
        self.max_prompt_chars = int(agent.get("max_prompt_chars", 8000))
        self.max_metadata_keys = int(agent.get("max_metadata_keys", 12))
        self.max_metadata_chars = int(agent.get("max_metadata_chars", 200))
        self.system_prompt = load_system_prompt()
        self.last_record: Optional[PlannerCallRecord] = None

    def _post(self, payload: Dict) -> Dict:
        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
            return json.loads(response.read().decode("utf-8"))

    def plan(self, state: StateSnapshot) -> Plan:
        start = now_ms()
        try:
            user_prompt = build_user_prompt(
                state,
                max_prompt_chars=self.max_prompt_chars,
                max_metadata_keys=self.max_metadata_keys,
                max_metadata_chars=self.max_metadata_chars,
            )
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
                "format": "json",
                "options": {"temperature": self.temperature, "num_predict": self.num_predict},
            }
            body = self._post(payload)
            content = body["message"]["content"]
            raw = content if isinstance(content, dict) else json.loads(content)
            plan = Plan.model_validate(raw)
        except Exception as exc:
            reason = redact_text(exc)
            self.last_record = PlannerCallRecord(
                provider="ollama",
                model=self.model,
                prompt_version=self.prompt_version,
                status="error",
                latency_ms=now_ms() - start,
                fallback=False,
                reason=reason,
            )
            if isinstance(exc, PlannerError):
                raise
            raise PlannerError(f"Qwen3 planner failed: {reason}") from exc

        self.last_record = PlannerCallRecord(
            provider="ollama",
            model=self.model,
            prompt_version=self.prompt_version,
            status="ok",
            latency_ms=now_ms() - start,
            fallback=False,
            strategy=plan.strategy,
        )
        return plan


class HostedQwen3Planner:
    """OpenAI-compatible hosted Qwen3 adapter for HF and OpenRouter."""

    provider_name = "huggingface"

    _PROVIDER_ENV = {
        "huggingface": {
            "endpoint": "HF_ENDPOINT_URL",
            "token": "HF_TOKEN",
            "model": "HF_MODEL_ID",
            "revision": "HF_MODEL_REVISION",
        },
        "openrouter": {
            "endpoint": "OPENROUTER_ENDPOINT_URL",
            "token": "OPENROUTER_API_KEY",
            "model": "OPENROUTER_MODEL",
            "revision": "OPENROUTER_MODEL_REVISION",
        },
    }

    def __init__(self, config: Optional[Dict] = None, provider: str = "huggingface") -> None:
        provider = provider.lower()
        if provider not in self._PROVIDER_ENV:
            raise ValueError(f"unsupported hosted provider {provider!r}")

        config = config or {}
        agent_config = config.get("agent", {})
        provider_config = dict(agent_config.get(provider, {}))
        env = self._PROVIDER_ENV[provider]

        self.provider_name = provider
        endpoint = os.environ.get(env["endpoint"]) or provider_config.get("endpoint_url", "")
        self.endpoint_url = str(endpoint).rstrip("/")
        model_key = "model_id" if provider == "huggingface" else "model"
        self.model = str(os.environ.get(env["model"]) or provider_config.get(model_key, ""))
        self.revision = str(os.environ.get(env["revision"]) or provider_config.get("revision", ""))
        self.token = os.environ.get(env["token"], "")
        self.timeout_s = float(provider_config.get("timeout_s", agent_config.get("timeout_s", 20)))
        self.max_retries = max(
            0, int(provider_config.get("max_retries", agent_config.get("max_retries", 2)))
        )
        self.retry_delay_s = max(
            0.0,
            float(provider_config.get("retry_delay_s", agent_config.get("retry_delay_s", 0.25))),
        )
        self.temperature = float(provider_config.get("temperature", agent_config.get("temperature", 0.0)))
        self.max_tokens = int(
            provider_config.get(
                "max_tokens", provider_config.get("num_predict", agent_config.get("num_predict", 256))
            )
        )
        self.prompt_version = str(agent_config.get("prompt_version", PROMPT_VERSION))
        self.max_prompt_chars = int(agent_config.get("max_prompt_chars", 8000))
        self.max_metadata_keys = int(agent_config.get("max_metadata_keys", 12))
        self.max_metadata_chars = int(agent_config.get("max_metadata_chars", 200))
        self.system_prompt = load_system_prompt()
        self.last_record: Optional[PlannerCallRecord] = None

    def _model_reference(self) -> str:
        if self.provider_name == "huggingface" and self.revision:
            return f"{self.model}@{self.revision}"
        return self.model

    def _request_body(self, state: StateSnapshot) -> Dict[str, Any]:
        user_prompt = build_user_prompt(
            state,
            max_prompt_chars=self.max_prompt_chars,
            max_metadata_keys=self.max_metadata_keys,
            max_metadata_chars=self.max_metadata_chars,
        )
        return {
            "model": self._model_reference(),
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if self.provider_name == "openrouter":
            headers["HTTP-Referer"] = os.environ.get("OPENROUTER_SITE_URL", "https://localhost")
            headers["X-Title"] = "predictive-container-management"
        return headers

    def _post(self, body: Dict[str, Any]) -> Dict[str, Any]:
        request = urllib.request.Request(
            self.endpoint_url,
            data=json.dumps(body).encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
            raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}

    def _extract_content(self, body: Dict[str, Any]) -> Any:
        content: Any = None
        choices = body.get("choices") if isinstance(body, dict) else None
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            choice = choices[0]
            message = choice.get("message")
            if isinstance(message, dict) and "content" in message:
                content = message["content"]
            elif "text" in choice:
                content = choice["text"]
        if content is None and isinstance(body, dict) and "generated_text" in body:
            content = body["generated_text"]
        if content is None and isinstance(body, dict) and isinstance(body.get("message"), dict):
            content = body["message"].get("content")
        if isinstance(body, list) and body and isinstance(body[0], dict):
            content = body[0].get("generated_text", body[0].get("message", {}).get("content"))
        if not isinstance(content, (str, dict)):
            raise PlannerProviderError(
                "unexpected provider response shape", retryable=False, status="invalid_output"
            )
        return content

    def _usage(self, body: Dict[str, Any]) -> Optional[Dict[str, int]]:
        usage = body.get("usage") if isinstance(body, dict) else None
        if not isinstance(usage, dict):
            return None
        allowed = {"prompt_tokens", "completion_tokens", "total_tokens"}
        result = {
            str(key): int(value)
            for key, value in usage.items()
            if key in allowed and isinstance(value, (int, float))
        }
        return result or None

    def plan(self, state: StateSnapshot) -> Plan:
        start = now_ms()
        attempt = 0
        last_error: Optional[PlannerProviderError] = None

        if not self.endpoint_url or not self.model:
            last_error = PlannerProviderError(
                "hosted planner endpoint/model not configured",
                retryable=False,
                status="config",
            )
        else:
            body = self._request_body(state)
            for attempt in range(1, self.max_retries + 2):
                response: Dict[str, Any] = {}
                last_error = None
                try:
                    response = self._post(body)
                    content = self._extract_content(response)
                    raw = content if isinstance(content, dict) else json.loads(content)
                    plan = Plan.model_validate(raw)
                except PlannerProviderError as exc:
                    last_error = exc
                except json.JSONDecodeError as exc:
                    last_error = PlannerProviderError(
                        f"malformed_json: {redact_text(exc)}",
                        retryable=False,
                        status="invalid_output",
                    )
                except ValidationError as exc:
                    last_error = PlannerProviderError(
                        f"invalid_plan: {redact_text(exc)}",
                        retryable=False,
                        status="invalid_output",
                    )
                except urllib.error.HTTPError as exc:
                    last_error = _classify_provider_error(exc)
                except Exception as exc:
                    last_error = _classify_provider_error(exc)

                if last_error is None:
                    self.last_record = PlannerCallRecord(
                        provider=self.provider_name,
                        model=self._model_reference(),
                        revision=self.revision or None,
                        prompt_version=self.prompt_version,
                        status="ok",
                        latency_ms=now_ms() - start,
                        fallback=False,
                        strategy=plan.strategy,
                        usage=self._usage(response),
                        attempts=attempt,
                    )
                    return plan

                if not last_error.retryable or attempt > self.max_retries:
                    break
                if self.retry_delay_s:
                    time.sleep(self.retry_delay_s)

        reason = redact_text(last_error) or "hosted planner failed"
        self.last_record = PlannerCallRecord(
            provider=self.provider_name,
            model=self._model_reference() or "unknown",
            revision=self.revision or None,
            prompt_version=self.prompt_version,
            status="error",
            latency_ms=now_ms() - start,
            fallback=False,
            reason=reason,
            attempts=max(1, attempt),
        )
        raise PlannerError(f"{self.provider_name} planner failed: {reason}") from last_error


class Qwen3TransformersPlanner:
    """Local Qwen3 planner using Hugging Face Transformers in-process."""

    provider_name = "transformers"

    def __init__(self, config: Optional[Dict] = None) -> None:
        config = config or {}
        agent_config = config.get("agent", {})
        local_config = dict(agent_config.get("transformers", {}))

        self.model_id = str(
            os.environ.get("TRANSFORMERS_MODEL_ID")
            or local_config.get("model_id")
            or agent_config.get("model")
            or "Qwen/Qwen3-1.7B"
        )
        self.revision = str(
            os.environ.get("TRANSFORMERS_REVISION") or local_config.get("revision", "")
        )
        self.cache_dir = str(
            os.environ.get("TRANSFORMERS_CACHE_DIR") or local_config.get("cache_dir", "")
        )
        self.device = str(local_config.get("device", "cpu"))
        self.dtype = str(local_config.get("dtype", "auto"))
        self.local_files_only = bool(local_config.get("local_files_only", False))
        self.trust_remote_code = bool(local_config.get("trust_remote_code", False))
        self.max_new_tokens = int(local_config.get("max_new_tokens", 256))
        self.temperature = float(local_config.get("temperature", 0.0))
        self.enable_thinking = bool(local_config.get("enable_thinking", False))
        self.prompt_version = str(agent_config.get("prompt_version", PROMPT_VERSION))
        self.max_prompt_chars = int(agent_config.get("max_prompt_chars", 8000))
        self.max_metadata_keys = int(agent_config.get("max_metadata_keys", 12))
        self.max_metadata_chars = int(agent_config.get("max_metadata_chars", 200))
        self.system_prompt = load_system_prompt()
        self.last_record: Optional[PlannerCallRecord] = None
        self._torch: Any = None
        self._transformers: Any = None
        self._tokenizer: Any = None
        self._model: Any = None

    def _load(self) -> None:
        if self._tokenizer is not None and self._model is not None:
            return
        try:
            self._torch = importlib.import_module("torch")
            self._transformers = importlib.import_module("transformers")
            load_kwargs: Dict[str, Any] = {}
            if self.revision:
                load_kwargs["revision"] = self.revision
            if self.cache_dir:
                load_kwargs["cache_dir"] = self.cache_dir
            if self.local_files_only:
                load_kwargs["local_files_only"] = True
            if self.trust_remote_code:
                load_kwargs["trust_remote_code"] = True
            self._tokenizer = self._transformers.AutoTokenizer.from_pretrained(
                self.model_id, **load_kwargs
            )
            model_kwargs = dict(load_kwargs)
            if self.dtype != "auto":
                dtype = getattr(self._torch, self.dtype, None)
                if dtype is not None:
                    version = str(getattr(self._transformers, "__version__", "0"))
                    parts = tuple(int(part) for part in re.findall(r"\d+", version)[:2])
                    supports_dtype = len(parts) == 2 and parts >= (4, 56)
                    model_kwargs["dtype" if supports_dtype else "torch_dtype"] = dtype
            self._model = self._transformers.AutoModelForCausalLM.from_pretrained(
                self.model_id, **model_kwargs
            )
            if self.device and self.device != "auto" and hasattr(self._model, "to"):
                self._model = self._model.to(self.device)
        except Exception as exc:
            reason = redact_text(exc)
            raise PlannerProviderError(
                f"local_model_load_failed: {reason}", retryable=False, status="config"
            ) from exc

    def _render_prompt(self, state: StateSnapshot) -> Any:
        user_prompt = build_user_prompt(
            state,
            max_prompt_chars=self.max_prompt_chars,
            max_metadata_keys=self.max_metadata_keys,
            max_metadata_chars=self.max_metadata_chars,
        )
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        try:
            return self._tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=self.enable_thinking,
            )
        except TypeError:
            return self._tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )

    def _prepare_inputs(self, prompt: Any) -> Dict[str, Any]:
        if isinstance(prompt, str):
            encoded = self._tokenizer(prompt, return_tensors="pt")
        elif isinstance(prompt, Mapping):
            encoded = prompt
        else:
            raise PlannerProviderError(
                "unsupported tokenizer template output", retryable=False, status="invalid_output"
            )
        if not isinstance(encoded, Mapping) or "input_ids" not in encoded:
            raise PlannerProviderError(
                "unexpected tokenizer output", retryable=False, status="invalid_output"
            )
        prepared: Dict[str, Any] = {}
        for key, value in dict(encoded).items():
            if self.device and self.device != "auto" and hasattr(value, "to"):
                value = value.to(self.device)
            prepared[key] = value
        return prepared

    def _generate(self, inputs: Dict[str, Any]) -> Any:
        generation_kwargs: Dict[str, Any] = {
            "max_new_tokens": self.max_new_tokens,
            "do_sample": self.temperature > 0,
            "pad_token_id": getattr(self._tokenizer, "eos_token_id", None),
        }
        if self.temperature > 0:
            generation_kwargs["temperature"] = self.temperature
        if hasattr(self._torch, "no_grad"):
            with self._torch.no_grad():
                return self._model.generate(**inputs, **generation_kwargs)
        return self._model.generate(**inputs, **generation_kwargs)

    @staticmethod
    def _decode_output(tokenizer: Any, outputs: Any, prompt_tokens: Optional[int]) -> str:
        sequences = outputs
        if isinstance(outputs, dict):
            sequences = outputs.get("sequences", outputs.get("generated_ids"))
        if sequences is None:
            raise PlannerProviderError(
                "unexpected generation output", retryable=False, status="invalid_output"
            )
        shape = getattr(sequences, "shape", None)
        if prompt_tokens is not None and shape is not None and len(shape) >= 2:
            tokens = sequences[0][prompt_tokens:]
        elif isinstance(sequences, (list, tuple)) and sequences:
            tokens = sequences[0]
        else:
            tokens = sequences
        if hasattr(tokenizer, "decode"):
            text = tokenizer.decode(tokens, skip_special_tokens=True)
        elif isinstance(tokens, str):
            text = tokens
        else:
            text = str(tokens)
        return str(text)

    @staticmethod
    def _clean_text(text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
        cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r"<think>.*", "", cleaned, flags=re.DOTALL)
        return cleaned.strip()

    @staticmethod
    def _extract_plan_dict(text: Any) -> Dict[str, Any]:
        if isinstance(text, dict):
            return text
        cleaned = Qwen3TransformersPlanner._clean_text(str(text))
        decoder = json.JSONDecoder()
        for index, char in enumerate(cleaned):
            if char != "{":
                continue
            try:
                raw, _ = decoder.raw_decode(cleaned[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(raw, dict):
                return raw
        raise PlannerProviderError(
            "invalid_plan: no JSON object in local model output",
            retryable=False,
            status="invalid_output",
        )

    @staticmethod
    def _token_usage(inputs: Dict[str, Any], outputs: Any) -> Optional[Dict[str, int]]:
        input_shape = getattr(inputs.get("input_ids"), "shape", None)
        if input_shape is None:
            return None
        prompt_tokens = int(input_shape[-1])
        sequences = outputs.get("sequences") if isinstance(outputs, dict) else outputs
        output_shape = getattr(sequences, "shape", None)
        if output_shape is None:
            return None
        completion_tokens = max(0, int(output_shape[-1]) - prompt_tokens)
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }

    def plan(self, state: StateSnapshot) -> Plan:
        start = now_ms()
        try:
            self._load()
            prompt = self._render_prompt(state)
            inputs = self._prepare_inputs(prompt)
            prompt_tokens = int(inputs["input_ids"].shape[-1]) if hasattr(
                inputs["input_ids"], "shape"
            ) else None
            outputs = self._generate(inputs)
            text = self._decode_output(self._tokenizer, outputs, prompt_tokens)
            raw = self._extract_plan_dict(text)
            plan = Plan.model_validate(raw)
        except PlannerProviderError as exc:
            reason = redact_text(exc)
            self.last_record = PlannerCallRecord(
                provider=self.provider_name,
                model=self.model_id,
                prompt_version=self.prompt_version,
                status="error",
                latency_ms=now_ms() - start,
                fallback=False,
                reason=reason,
                revision=self.revision or None,
            )
            raise PlannerError(f"transformers planner failed: {reason}") from exc
        except ValidationError as exc:
            reason = redact_text(exc)
            self.last_record = PlannerCallRecord(
                provider=self.provider_name,
                model=self.model_id,
                prompt_version=self.prompt_version,
                status="error",
                latency_ms=now_ms() - start,
                fallback=False,
                reason=f"invalid_plan: {reason}",
                revision=self.revision or None,
            )
            raise PlannerError(f"transformers planner failed: invalid plan: {reason}") from exc
        except Exception as exc:
            reason = redact_text(exc)
            self.last_record = PlannerCallRecord(
                provider=self.provider_name,
                model=self.model_id,
                prompt_version=self.prompt_version,
                status="error",
                latency_ms=now_ms() - start,
                fallback=False,
                reason=reason,
                revision=self.revision or None,
            )
            raise PlannerError(f"transformers planner failed: {reason}") from exc

        self.last_record = PlannerCallRecord(
            provider=self.provider_name,
            model=self.model_id,
            prompt_version=self.prompt_version,
            status="ok",
            latency_ms=now_ms() - start,
            fallback=False,
            strategy=plan.strategy,
            revision=self.revision or None,
            usage=self._token_usage(inputs, outputs),
        )
        return plan


class FallbackPlanner:
    """Use the primary planner, falling back to a deterministic stub on failure."""

    def __init__(self, primary: Planner, fallback: Optional[StubPlanner] = None) -> None:
        self.primary = primary
        self.fallback = fallback or StubPlanner()
        self.last_fallback = False
        self.last_error: Optional[str] = None
        self.last_record: Optional[PlannerCallRecord] = None

    def plan(self, state: StateSnapshot) -> Plan:
        try:
            plan = self.primary.plan(state)
            record = getattr(self.primary, "last_record", None)
            self.last_record = record or PlannerCallRecord(
                provider=type(self.primary).__name__,
                model=getattr(self.primary, "model", "unknown"),
                prompt_version="n/a",
                status="ok",
                latency_ms=0.0,
                strategy=plan.strategy,
            )
            self.last_fallback = False
            self.last_error = None
            return plan
        except Exception as exc:
            self.last_fallback = True
            self.last_error = redact_text(exc)
            record = getattr(self.primary, "last_record", None)
            self.last_record = record or PlannerCallRecord(
                provider=type(self.primary).__name__,
                model=getattr(self.primary, "model", "unknown"),
                prompt_version="n/a",
                status="error",
                latency_ms=0.0,
                reason=self.last_error,
            )
            plan = self.fallback.plan(state)
            self.last_record.status = "fallback"
            self.last_record.fallback = True
            self.last_record.reason = self.last_error
            self.last_record.strategy = plan.strategy
            return plan


class ProviderChainPlanner:
    """Try hosted providers in order, then a deterministic final fallback."""

    def __init__(self, planners: list[Planner], fallback: Optional[Planner] = None) -> None:
        if not planners:
            raise ValueError("provider chain requires at least one planner")
        self.planners = planners
        self.fallback = fallback
        self.last_fallback = False
        self.last_error: Optional[str] = None
        self.last_record: Optional[PlannerCallRecord] = None

    def _record_for(self, planner: Planner, plan: Plan) -> PlannerCallRecord:
        record = getattr(planner, "last_record", None)
        if record is None:
            return PlannerCallRecord(
                provider=type(planner).__name__,
                model=getattr(planner, "model", "unknown"),
                prompt_version="n/a",
                status="ok",
                latency_ms=0.0,
                strategy=plan.strategy,
            )
        return copy.copy(record)

    def plan(self, state: StateSnapshot) -> Plan:
        reasons: list[str] = []
        for index, planner in enumerate(self.planners):
            try:
                plan = planner.plan(state)
            except Exception as exc:
                reasons.append(f"{getattr(planner, 'provider_name', type(planner).__name__)}: {redact_text(exc)}")
                continue

            record = self._record_for(planner, plan)
            if index > 0 or reasons:
                record.status = "fallback"
                record.fallback = True
                record.reason = "; ".join(reasons)
            self.last_record = record
            self.last_fallback = bool(reasons) or index > 0
            self.last_error = "; ".join(reasons) or None
            return plan

        reason = "; ".join(reasons) or "all providers failed"
        if self.fallback is None:
            self.last_record = PlannerCallRecord(
                provider="chain",
                model="none",
                prompt_version="n/a",
                status="error",
                latency_ms=0.0,
                reason=reason,
            )
            self.last_error = reason
            self.last_fallback = True
            raise PlannerError(reason)

        plan = self.fallback.plan(state)
        record = self._record_for(self.fallback, plan)
        record.status = "fallback"
        record.fallback = True
        record.reason = reason
        self.last_record = record
        self.last_fallback = True
        self.last_error = reason
        return plan


def build_planner(config: Optional[Dict] = None, with_fallback: bool = True) -> Planner:
    """Construct the planner selected by ``agent.runtime``."""
    config = config or {}
    agent_config = config.get("agent", {})
    runtime_value = str(agent_config.get("runtime", "stub")).lower()
    provider_value = str(agent_config.get("provider", "")).lower()
    runtime = (
        provider_value
        if runtime_value == "stub" and provider_value and provider_value != "stub"
        else runtime_value
    )

    if runtime == "stub":
        return StubPlanner(config)
    if runtime in {"ollama", "qwen3"}:
        primary = Qwen3OllamaPlanner(config)
        return FallbackPlanner(primary, StubPlanner(config)) if with_fallback else primary
    if runtime == "transformers":
        primary = Qwen3TransformersPlanner(config)
        return FallbackPlanner(primary, StubPlanner(config)) if with_fallback else primary
    if runtime == "huggingface":
        primary = HostedQwen3Planner(config, provider="huggingface")
        if with_fallback and str(agent_config.get("fallback_provider", "")).lower() == "openrouter":
            fallback = HostedQwen3Planner(config, provider="openrouter")
            return ProviderChainPlanner([primary, fallback], StubPlanner(config))
        return FallbackPlanner(primary, StubPlanner(config)) if with_fallback else primary
    if runtime == "openrouter":
        primary = HostedQwen3Planner(config, provider="openrouter")
        return FallbackPlanner(primary, StubPlanner(config)) if with_fallback else primary
    raise ValueError(
        f"unknown agent.runtime {runtime!r}; expected 'stub', 'ollama', 'transformers', 'huggingface' or 'openrouter'"
    )
