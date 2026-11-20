"""Redaction and per-call telemetry for planner invocation auditing."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Optional

_SECRET_PATTERN = re.compile(
    r"(?i)\b([a-z0-9_-]*(?:api[_-]?key|token|password|secret|credential|authorization|bearer)[a-z0-9_-]*\s*[=:]\s*)(\S+)"
)


def redact_text(value: object, max_chars: int = 300) -> Optional[str]:
    if value is None:
        return None
    text = str(value)
    text = _SECRET_PATTERN.sub(r"\1[REDACTED]", text)
    if len(text) > max_chars:
        return text[:max_chars] + "...[TRUNCATED]"
    return text


def now_ms() -> float:
    return time.perf_counter() * 1000.0


@dataclass
class PlannerCallRecord:
    provider: str
    model: str
    prompt_version: str
    status: str
    latency_ms: float
    fallback: bool = False
    reason: Optional[str] = None
    strategy: Optional[str] = None
    plan_code: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "model": redact_text(self.model, 100),
            "prompt_version": self.prompt_version,
            "status": self.status,
            "latency_ms": round(float(self.latency_ms), 3),
            "fallback": bool(self.fallback),
            "reason": redact_text(self.reason),
            "strategy": self.strategy,
            "plan_code": self.plan_code,
        }
