from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from data.ingestion import validate_trace
from demo.synthetic_client import PAYLOAD_CLASSES

SCHEMA_VERSION = "m9-event-v1"
REQUIRED_EVENT_FIELDS = (
    "timestamp",
    "service_id",
    "function_id",
    "invocation_count",
)
OPTIONAL_EVENT_FIELDS = (
    "request_id",
    "payload_class",
    "execution_duration_ms",
    "error_count",
    "source",
    "scenario",
)


class IngestionValidationError(ValueError):
    pass


class IngestionAuthError(PermissionError):
    pass


@dataclass
class IngestResult:
    events: pd.DataFrame
    event_count: int
    auth_ok: bool
    schema_version: str = SCHEMA_VERSION


class GenericIngestionAdapter:
    def __init__(self, config: dict | None = None):
        cfg = (config or {}).get("demo", {})
        self.require_auth = bool(cfg.get("require_ingest_auth", False))
        self.token_env = str(cfg.get("ingest_token_env", "M9_INGEST_TOKEN"))

    def _check_auth(self, records: list[dict]) -> None:
        if not self.require_auth:
            return
        expected = os.getenv(self.token_env)
        if not expected:
            raise IngestionAuthError(f"missing ingestion token in environment: {self.token_env}")
        for index, record in enumerate(records):
            if record.get("auth_token") != expected:
                raise IngestionAuthError(f"invalid ingestion token at record {index}")

    def ingest(self, records: Iterable[dict]) -> IngestResult:
        materialized = [dict(record) for record in records]
        if not materialized:
            raise IngestionValidationError("no ingestion records supplied")
        self._check_auth(materialized)

        normalized: list[dict] = []
        for index, record in enumerate(materialized):
            missing = [field for field in REQUIRED_EVENT_FIELDS if field not in record]
            if missing:
                raise IngestionValidationError(f"record {index} missing fields: {missing}")

            timestamp = pd.to_datetime(record["timestamp"], errors="coerce", utc=True)
            if pd.isna(timestamp):
                raise IngestionValidationError(f"record {index} has invalid timestamp")

            function_id = str(record["function_id"]).strip()
            if not function_id:
                raise IngestionValidationError(f"record {index} has empty function_id")

            invocation_count = _finite_number(record["invocation_count"], "invocation_count", index)
            if invocation_count < 0:
                raise IngestionValidationError(f"record {index} has negative invocation_count")

            duration = _finite_number(record.get("execution_duration_ms", 0.0), "execution_duration_ms", index)
            errors = _finite_number(record.get("error_count", 0), "error_count", index)
            if duration < 0 or errors < 0:
                raise IngestionValidationError(f"record {index} has negative duration or error_count")

            payload_class = str(record.get("payload_class", "small"))
            if payload_class not in PAYLOAD_CLASSES:
                raise IngestionValidationError(f"record {index} has unknown payload class: {payload_class}")

            normalized.append(
                {
                    "timestamp": timestamp,
                    "service_id": str(record["service_id"]),
                    "function_id": function_id,
                    "invocation_count": invocation_count,
                    "execution_duration_ms": duration,
                    "error_count": errors,
                    "payload_class": payload_class,
                    "source": str(record.get("source", "unknown")),
                    "request_id": str(record.get("request_id", f"event-{index}")),
                }
            )

        frame = pd.DataFrame(normalized).sort_values("timestamp").reset_index(drop=True)
        return IngestResult(events=frame, event_count=len(frame), auth_ok=not self.require_auth or True)


def _finite_number(value, name: str, index: int) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise IngestionValidationError(f"record {index} has non-numeric {name}") from exc
    if not math.isfinite(number):
        raise IngestionValidationError(f"record {index} has non-finite {name}")
    return number


def records_to_trace(result: IngestResult, interval_s: int = 60) -> pd.DataFrame:
    if interval_s <= 0:
        raise ValueError("interval_s must be positive")
    frame = result.events.copy()
    frame["window_start"] = frame["timestamp"].dt.floor(f"{interval_s}s")
    grouped = frame.groupby(["window_start", "function_id"], as_index=False).agg(
        invocation_count=("invocation_count", "sum"),
        execution_duration_ms=("execution_duration_ms", "mean"),
        error_count=("error_count", "sum"),
        event_count=("request_id", "count"),
    )
    grouped = grouped.rename(columns={"window_start": "timestamp"})
    load = (grouped["invocation_count"] / 200.0).clip(0.0, 1.5)
    grouped["cpu_utilization"] = (0.12 + 0.62 * load).clip(0.01, 0.98)
    grouped["memory_utilization"] = (0.20 + 0.52 * load).clip(0.01, 0.98)
    grouped["latency_ms"] = 70.0 + 75.0 * load
    grouped["p95_latency_ms"] = grouped["latency_ms"] * 1.22
    grouped["power_w"] = 42.0 + 110.0 * load
    grouped["active_containers"] = load.mul(8).apply(lambda value: max(2, int(math.ceil(value))))
    grouped["warm_containers"] = (grouped["active_containers"] - 1).clip(lower=0)
    grouped["cold_starts"] = grouped["error_count"].astype(int)
    grouped["source"] = "generic_adapter"
    grouped = grouped.sort_values(["timestamp", "function_id"]).reset_index(drop=True)
    return validate_trace(grouped)


def write_schema(path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    schema = {
        "version": SCHEMA_VERSION,
        "required": list(REQUIRED_EVENT_FIELDS),
        "optional": list(OPTIONAL_EVENT_FIELDS),
        "types": {
            "timestamp": "ISO-8601 string with timezone",
            "service_id": "non-empty string",
            "function_id": "non-empty string",
            "invocation_count": "non-negative finite number",
            "execution_duration_ms": "non-negative finite number",
            "error_count": "non-negative finite number",
            "payload_class": list(PAYLOAD_CLASSES),
            "source": "string source metadata",
        },
        "privacy": {
            "allow_user_identity": False,
            "allow_request_payload": False,
            "allow_auth_data_in_artifacts": False,
        },
    }
    target.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    return target
