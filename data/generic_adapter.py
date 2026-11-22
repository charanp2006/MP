from __future__ import annotations

import argparse
import hmac
import json
import math
import os
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from data.ingestion import validate_trace
from data.ingestion_schema import (
    CREDENTIAL_FIELDS,
    DEFAULT_PAYLOAD_CLASSES,
    DEFAULT_SOURCE,
    OPTIONAL_EVENT_FIELDS,
    MAXIMUM_METRIC_FIELDS,
    REQUIRED_EVENT_FIELDS,
    RESOURCE_METRIC_FIELDS,
    SCHEMA_VERSION,
    SUMMED_METRIC_FIELDS,
    IngestionAuthError,
    IngestionValidationError,
    build_json_schema,
    validate_events,
    validate_source,
    write_schema,
)

__all__ = [
    "SCHEMA_VERSION",
    "REQUIRED_EVENT_FIELDS",
    "OPTIONAL_EVENT_FIELDS",
    "RESOURCE_METRIC_FIELDS",
    "IngestEnvelope",
    "IngestResult",
    "GenericIngestionAdapter",
    "IngestionAuthError",
    "IngestionValidationError",
    "records_to_trace",
    "build_json_schema",
    "write_schema",
    "main",
]

_OBSERVED_PREFIX = "__observed_"


def _token_value(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if text.lower().startswith("bearer "):
        text = text[7:].strip()
    return text or None


def _record_token(record: Mapping[str, Any]) -> tuple[str | None, str | None]:
    for field in CREDENTIAL_FIELDS:
        if field in record and record[field] is not None:
            return field, _token_value(record[field])
    return None, None


@dataclass
class IngestEnvelope:
    """API-style request: records plus an out-of-band bearer credential."""

    records: list[dict[str, Any]]
    auth_token: str | None = None
    source: str | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "IngestEnvelope":
        if not isinstance(payload, Mapping):
            raise IngestionValidationError("envelope must be a mapping/JSON object")
        if "records" not in payload:
            raise IngestionValidationError("envelope is missing 'records'")
        records = payload["records"]
        if not isinstance(records, (list, tuple)):
            raise IngestionValidationError("envelope 'records' must be a list of event objects")
        token = None
        for field in CREDENTIAL_FIELDS:
            if field in payload and payload[field] is not None:
                token = payload[field]
                break
        return cls(
            records=_copy_records(records),
            auth_token=token,
            source=payload.get("source"),
        )


@dataclass
class IngestResult:
    events: pd.DataFrame
    event_count: int
    auth_ok: bool
    schema_version: str = SCHEMA_VERSION


def _copy_records(records: Iterable[Any]) -> list[dict[str, Any]]:
    copied: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise IngestionValidationError(f"record {index} must be a mapping/JSON object")
        copied.append(dict(record))
    return copied


def _coerce_envelope(
    records: IngestEnvelope | Mapping[str, Any] | Iterable[Mapping[str, Any]],
) -> IngestEnvelope:
    if isinstance(records, IngestEnvelope):
        return records
    if isinstance(records, Mapping) and "records" in records:
        return IngestEnvelope.from_mapping(records)
    return IngestEnvelope(records=_copy_records(records))


class GenericIngestionAdapter:
    def __init__(self, config: dict | None = None):
        config = config or {}
        cfg = config.get("demo", {}) or {}
        self.require_auth = bool(cfg.get("require_ingest_auth", False))
        self.token_env = str(cfg.get("ingest_token_env", "M9_INGEST_TOKEN"))
        allowed = cfg.get("allowed_ingest_sources")
        if allowed is None:
            allowed = (config.get("data", {}) or {}).get("allowed_ingest_sources")
        self.allowed_sources = tuple(str(value) for value in (allowed or ()))
        self.payload_classes = tuple(
            str(value) for value in (cfg.get("payload_classes") or DEFAULT_PAYLOAD_CLASSES)
        )

    def _check_auth(self, envelope: IngestEnvelope, records: list[dict[str, Any]]) -> None:
        if not self.require_auth:
            return
        expected = _token_value(os.getenv(self.token_env))
        if not expected:
            raise IngestionAuthError(f"missing ingestion token in environment: {self.token_env}")

        envelope_token = _token_value(envelope.auth_token)
        legacy: list[tuple[int, str]] = []
        for index, record in enumerate(records):
            field, token = _record_token(record)
            if field is not None and token is None:
                raise IngestionAuthError(f"empty ingestion token in record {index}")
            if token is not None:
                legacy.append((index, token))

        if envelope_token is not None and any(token != envelope_token for _, token in legacy):
            raise IngestionAuthError("conflicting ingestion tokens in envelope and records")
        candidates: list[tuple[str | None, str]] = []
        if envelope_token is not None:
            candidates.append((None, envelope_token))
        candidates.extend(legacy)
        if not candidates:
            raise IngestionAuthError("missing ingestion token in envelope")
        for location, token in candidates:
            if not hmac.compare_digest(token, expected):
                where = "envelope" if location is None else f"record {location}"
                raise IngestionAuthError(f"invalid ingestion token in {where}")

    def ingest(
        self,
        records: IngestEnvelope | Mapping[str, Any] | Iterable[Mapping[str, Any]],
    ) -> IngestResult:
        envelope = _coerce_envelope(records)
        materialized = _copy_records(envelope.records)
        if not materialized:
            raise IngestionValidationError("no ingestion records supplied")
        self._check_auth(envelope, materialized)

        envelope_source = None
        if envelope.source is not None:
            envelope_source = validate_source(
                envelope.source, index=0, allowed_sources=self.allowed_sources
            )
        validated = validate_events(
            materialized,
            payload_classes=self.payload_classes,
            allowed_sources=self.allowed_sources,
        )
        if envelope_source is not None:
            for event in validated:
                if event["source"] == DEFAULT_SOURCE:
                    event["source"] = envelope_source

        frame = pd.DataFrame(validated).sort_values("timestamp").reset_index(drop=True)
        frame["timestamp"] = pd.to_datetime(
            frame["timestamp"], format="ISO8601", errors="coerce", utc=True
        )
        if frame["timestamp"].isna().any():
            raise IngestionValidationError("one or more timestamps could not be parsed")
        return IngestResult(events=frame, event_count=len(frame), auth_ok=True)


def _dominant_value(values: Iterable[Any], default: str = DEFAULT_SOURCE) -> str:
    cleaned = sorted({str(value) for value in values if pd.notna(value) and str(value).strip()})
    return cleaned[0] if cleaned else default


def _source_label(values: Iterable[Any]) -> str:
    cleaned = sorted({str(value) for value in values if pd.notna(value) and str(value).strip()})
    return "|".join(cleaned) if cleaned else DEFAULT_SOURCE


def _metric_aggregation(field: str) -> str:
    if field in SUMMED_METRIC_FIELDS:
        return "sum"
    if field in MAXIMUM_METRIC_FIELDS:
        return "max"
    return "mean"


def records_to_trace(result: IngestResult, interval_s: int = 60) -> pd.DataFrame:
    if interval_s <= 0:
        raise ValueError("interval_s must be positive")
    if result.events.empty:
        raise IngestionValidationError("cannot build a trace from zero ingestion events")

    frame = result.events.copy()
    frame["window_start"] = pd.to_datetime(
        frame["timestamp"], format="ISO8601", errors="coerce", utc=True
    ).dt.floor(f"{interval_s}s")
    if frame["window_start"].isna().any():
        raise IngestionValidationError("one or more event timestamps could not be parsed")
    frame["function_id"] = frame["function_id"].astype(str)

    for field in RESOURCE_METRIC_FIELDS:
        frame[f"{_OBSERVED_PREFIX}{field}"] = (
            frame[field].notna() if field in frame.columns else False
        )

    aggregations: dict[str, Any] = {
        "invocation_count": ("invocation_count", "sum"),
        "execution_duration_ms": ("execution_duration_ms", "mean"),
        "error_count": ("error_count", "sum"),
        "event_count": ("request_id", "count"),
        "source": ("source", _source_label),
    }
    for field in RESOURCE_METRIC_FIELDS:
        aggregations[f"observed_{field}"] = (f"{_OBSERVED_PREFIX}{field}", "any")
        if field in frame.columns:
            aggregations[f"value_{field}"] = (field, _metric_aggregation(field))
    has_scenario = "scenario" in frame.columns and frame["scenario"].notna().any()
    if has_scenario:
        aggregations["scenario"] = ("scenario", lambda values: _dominant_value(values, ""))

    grouped = frame.groupby(["window_start", "function_id"], as_index=False).agg(**aggregations)
    load = (grouped["invocation_count"] / 200.0).clip(0.0, 1.5)

    def metric_or(field: str, proxy: pd.Series) -> pd.Series:
        if f"value_{field}" not in grouped.columns:
            return proxy
        return grouped[f"value_{field}"].where(grouped[f"observed_{field}"], proxy)

    grouped["cpu_utilization"] = metric_or(
        "cpu_utilization", (0.12 + 0.62 * load).clip(0.01, 0.98)
    )
    grouped["memory_utilization"] = metric_or(
        "memory_utilization", (0.20 + 0.52 * load).clip(0.01, 0.98)
    )
    latency = metric_or("latency_ms", 70.0 + 75.0 * load)
    grouped["latency_ms"] = latency
    grouped["p95_latency_ms"] = metric_or("p95_latency_ms", latency * 1.22)
    grouped["power_w"] = metric_or("power_w", 42.0 + 110.0 * load)
    active = metric_or(
        "active_containers",
        load.mul(8).apply(lambda value: max(2, int(math.ceil(value)))),
    )
    grouped["active_containers"] = active
    grouped["warm_containers"] = metric_or("warm_containers", (active - 1).clip(lower=0))
    grouped["cold_starts"] = metric_or(
        "cold_starts", grouped["error_count"].astype(int)
    )

    observed = grouped[[f"observed_{field}" for field in RESOURCE_METRIC_FIELDS]]
    grouped["metrics_source"] = "derived"
    grouped.loc[observed.any(axis=1), "metrics_source"] = "mixed"
    grouped.loc[observed.all(axis=1), "metrics_source"] = "observed"

    columns = [
        "window_start",
        "function_id",
        "invocation_count",
        "execution_duration_ms",
        "error_count",
        "event_count",
        *RESOURCE_METRIC_FIELDS,
        "source",
        "metrics_source",
    ]
    if has_scenario:
        columns.append("scenario")
    trace = grouped[columns].rename(columns={"window_start": "timestamp"})
    trace = trace.sort_values(["timestamp", "function_id"]).reset_index(drop=True)
    return validate_trace(trace)


def _read_jsonl(path: Path) -> list[Any]:
    if not path.exists():
        raise FileNotFoundError(f"input JSONL file not found: {path}")
    payloads: list[Any] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payloads.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise IngestionValidationError(
                f"input line {line_number} is not valid JSON: {exc.msg}"
            ) from exc
    return payloads


def _payloads_to_envelope(payloads: list[Any], token: str | None) -> IngestEnvelope:
    records: list[dict[str, Any]] = []
    envelope_token = _token_value(token)
    source = None
    for index, payload in enumerate(payloads):
        if isinstance(payload, Mapping) and "records" in payload:
            envelope = IngestEnvelope.from_mapping(payload)
            records.extend(envelope.records)
            if envelope.auth_token is not None:
                candidate = _token_value(envelope.auth_token)
                if envelope_token is not None and candidate != envelope_token:
                    raise IngestionAuthError(f"conflicting ingestion tokens in input item {index + 1}")
                envelope_token = candidate
            if source is None and envelope.source is not None:
                source = envelope.source
        else:
            records.append(payload)
    return IngestEnvelope(records=records, auth_token=envelope_token, source=source)


def main(argv: list[str] | None = None) -> None:
    from configs import load_config

    parser = argparse.ArgumentParser(description="Ingest JSONL events into a fixed-window trace")
    parser.add_argument("--input", required=True, help="input JSONL file of events or envelopes")
    parser.add_argument("--out", required=True, help="output trace CSV path")
    parser.add_argument("--schema", default=None, help="optional JSON schema output path")
    parser.add_argument("--interval-s", type=int, default=None, help="fixed window size in seconds")
    parser.add_argument("--config", default="configs/project.yaml", help="experiment config path")
    parser.add_argument(
        "--token-stdin",
        action="store_true",
        help="read the bearer token from one stdin line instead of the environment",
    )
    args = parser.parse_args(argv)
    if args.interval_s is not None and args.interval_s <= 0:
        raise ValueError("interval_s must be positive")

    config = load_config(args.config)
    demo_cfg = config.get("demo", {}) or {}
    token_env = str(demo_cfg.get("ingest_token_env", "M9_INGEST_TOKEN"))
    token = sys.stdin.readline().rstrip("\r\n") if args.token_stdin else os.getenv(token_env)

    envelope = _payloads_to_envelope(_read_jsonl(Path(args.input)), token)
    result = GenericIngestionAdapter(config).ingest(envelope)
    interval_s = int(args.interval_s or demo_cfg.get("interval_s", 60))
    trace = records_to_trace(result, interval_s=interval_s)

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    trace.to_csv(output, index=False)
    if args.schema:
        write_schema(args.schema)
    print(
        json.dumps(
            {
                "event_count": result.event_count,
                "trace_rows": len(trace),
                "schema_version": SCHEMA_VERSION,
                "out": str(output),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
