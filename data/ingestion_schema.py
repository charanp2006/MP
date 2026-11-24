from __future__ import annotations

import json
import math
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

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
RESOURCE_METRIC_FIELDS = (
    "cpu_utilization",
    "memory_utilization",
    "latency_ms",
    "p95_latency_ms",
    "power_w",
    "active_containers",
    "warm_containers",
    "cold_starts",
)
AVERAGED_METRIC_FIELDS = (
    "cpu_utilization",
    "memory_utilization",
    "latency_ms",
    "p95_latency_ms",
    "power_w",
)
MAXIMUM_METRIC_FIELDS = ("active_containers", "warm_containers")
SUMMED_METRIC_FIELDS = ("cold_starts",)
UTILIZATION_FIELDS = ("cpu_utilization", "memory_utilization")
METRICS_SOURCE_VALUES = ("observed", "derived", "mixed")
DEFAULT_PAYLOAD_CLASSES = ("small", "medium", "large")
DEFAULT_SOURCE = "unknown"
CREDENTIAL_FIELDS = ("auth_token", "bearer_token", "token", "authorization")
MAX_TEXT_LENGTH = 256


class IngestionValidationError(ValueError):
    """Raised when an untrusted ingestion record violates the event schema."""


class IngestionAuthError(PermissionError):
    """Raised when an ingestion bearer token is missing or invalid."""


def _text(value: Any, field: str, index: int, *, default: str | None = None) -> str:
    if value is None and default is not None:
        return default
    if isinstance(value, bytes):
        raise IngestionValidationError(f"record {index} has non-text {field}")
    text = str(value).strip()
    if not text:
        if default is not None:
            return default
        raise IngestionValidationError(f"record {index} has empty {field}")
    if len(text) > MAX_TEXT_LENGTH:
        raise IngestionValidationError(
            f"record {index} has overly long {field} (max {MAX_TEXT_LENGTH} characters)"
        )
    return text


def _number(
    value: Any,
    field: str,
    index: int,
    *,
    minimum: float = 0.0,
    maximum: float | None = None,
) -> float:
    if isinstance(value, bool):
        raise IngestionValidationError(f"record {index} has non-numeric {field}")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise IngestionValidationError(f"record {index} has non-numeric {field}") from exc
    if not math.isfinite(number):
        raise IngestionValidationError(f"record {index} has non-finite {field}")
    if number < minimum:
        raise IngestionValidationError(f"record {index} has {field} below {minimum}")
    if maximum is not None and number > maximum:
        raise IngestionValidationError(f"record {index} has {field} above {maximum}")
    return number


def _timestamp(value: Any, index: int) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    text = _text(value, "timestamp", index)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise IngestionValidationError(f"record {index} has invalid ISO-8601 timestamp") from exc
    return parsed.isoformat()


def _string_set(values: Iterable[Any] | None) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, (str, bytes)):
        values = (values,)
    return tuple(str(value).strip() for value in values if str(value).strip())


def validate_source(
    value: Any,
    *,
    index: int = 0,
    allowed_sources: Iterable[str] | None = None,
) -> str:
    source = DEFAULT_SOURCE if value is None else _text(value, "source", index)
    allowed = _string_set(allowed_sources)
    if allowed and source not in allowed:
        raise IngestionValidationError(
            f"record {index} has source '{source}' which is not in allowed sources: {list(allowed)}"
        )
    return source


def validate_event(
    record: Any,
    *,
    index: int = 0,
    payload_classes: Iterable[str] = DEFAULT_PAYLOAD_CLASSES,
    allowed_sources: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Validate one untrusted record and return a sanitized event with no credentials."""
    if not isinstance(record, Mapping):
        raise IngestionValidationError(f"record {index} must be a mapping/JSON object")

    payload = {key: value for key, value in record.items() if key not in CREDENTIAL_FIELDS}
    missing = [field for field in REQUIRED_EVENT_FIELDS if field not in payload or payload[field] is None]
    if missing:
        raise IngestionValidationError(f"record {index} missing fields: {missing}")

    allowed_payloads = _string_set(payload_classes) or DEFAULT_PAYLOAD_CLASSES
    payload_class = _text(payload.get("payload_class", "small"), "payload_class", index)
    if payload_class not in allowed_payloads:
        raise IngestionValidationError(
            f"record {index} has unknown payload class: {payload_class}; allowed: {list(allowed_payloads)}"
        )

    validated: dict[str, Any] = {
        "timestamp": _timestamp(payload["timestamp"], index),
        "service_id": _text(payload["service_id"], "service_id", index),
        "function_id": _text(payload["function_id"], "function_id", index),
        "invocation_count": _number(payload["invocation_count"], "invocation_count", index),
        "execution_duration_ms": _number(
            payload.get("execution_duration_ms", 0.0), "execution_duration_ms", index
        ),
        "error_count": _number(payload.get("error_count", 0), "error_count", index),
        "payload_class": payload_class,
        "source": validate_source(
            payload.get("source", DEFAULT_SOURCE), index=index, allowed_sources=allowed_sources
        ),
        "request_id": _text(payload.get("request_id", f"event-{index}"), "request_id", index),
    }
    if payload.get("scenario") is not None:
        validated["scenario"] = _text(payload["scenario"], "scenario", index)

    for field in RESOURCE_METRIC_FIELDS:
        if payload.get(field) is not None:
            maximum = 1.0 if field in UTILIZATION_FIELDS else None
            validated[field] = _number(payload[field], field, index, maximum=maximum)
    return validated


def validate_events(
    records: Iterable[Any],
    *,
    payload_classes: Iterable[str] = DEFAULT_PAYLOAD_CLASSES,
    allowed_sources: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    materialized = list(records)
    if not materialized:
        raise IngestionValidationError("no ingestion records supplied")
    return [
        validate_event(
            record,
            index=index,
            payload_classes=payload_classes,
            allowed_sources=allowed_sources,
        )
        for index, record in enumerate(materialized)
    ]


def build_json_schema() -> dict[str, Any]:
    """Return a JSON-schema document plus the legacy summary keys used by M9."""
    properties: dict[str, Any] = {
        "timestamp": {"type": "string", "format": "date-time", "description": "ISO-8601 timestamp"},
        "service_id": {"type": "string", "minLength": 1, "maxLength": MAX_TEXT_LENGTH},
        "function_id": {"type": "string", "minLength": 1, "maxLength": MAX_TEXT_LENGTH},
        "invocation_count": {"type": "number", "minimum": 0},
        "request_id": {"type": "string", "minLength": 1, "maxLength": MAX_TEXT_LENGTH},
        "payload_class": {"type": "string", "enum": list(DEFAULT_PAYLOAD_CLASSES)},
        "execution_duration_ms": {"type": "number", "minimum": 0},
        "error_count": {"type": "number", "minimum": 0},
        "source": {"type": "string", "minLength": 1, "maxLength": MAX_TEXT_LENGTH},
        "scenario": {"type": "string", "minLength": 1, "maxLength": MAX_TEXT_LENGTH},
    }
    for field in RESOURCE_METRIC_FIELDS:
        properties[field] = {
            "type": "number",
            "minimum": 0,
            "maximum": 1 if field in UTILIZATION_FIELDS else None,
        }
        if properties[field]["maximum"] is None:
            properties[field].pop("maximum")

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Generic serverless workload ingestion event",
        "type": "object",
        "properties": properties,
        "required": list(REQUIRED_EVENT_FIELDS),
        "additionalProperties": True,
        "version": SCHEMA_VERSION,
        "optional": list(OPTIONAL_EVENT_FIELDS),
        "resource_metrics": list(RESOURCE_METRIC_FIELDS),
        "types": {
            "timestamp": "ISO-8601 string with timezone",
            "service_id": "non-empty string",
            "function_id": "non-empty string",
            "invocation_count": "non-negative finite number",
            "execution_duration_ms": "non-negative finite number",
            "error_count": "non-negative finite number",
            "payload_class": list(DEFAULT_PAYLOAD_CLASSES),
            "source": "string source metadata",
            "resource_metrics": "non-negative finite numbers; utilizations in [0, 1]",
        },
        "provenance": {
            "source": "record or envelope source metadata is preserved in the trace",
            "metrics_source": list(METRICS_SOURCE_VALUES),
        },
        "privacy": {
            "allow_user_identity": False,
            "allow_request_payload": False,
            "allow_auth_data_in_artifacts": False,
        },
        "auth": {
            "transport": "bearer token in an IngestEnvelope, or legacy per-record token",
            "comparison": "hmac.compare_digest",
            "persistence": "credentials are verified in memory and stripped before artifacts are written",
        },
        "$defs": {
            "IngestEnvelope": {
                "type": "object",
                "properties": {
                    "records": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Event objects validated against this schema",
                    },
                    "auth_token": {
                        "type": "string",
                        "description": "Transport credential; verified then discarded",
                    },
                    "source": {"type": "string", "description": "Default source metadata for records without one"},
                },
                "required": ["records"],
            }
        },
    }


def write_schema(path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(build_json_schema(), indent=2), encoding="utf-8")
    return target
