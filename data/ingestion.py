from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = ("timestamp", "function_id", "invocation_count")
OPTIONAL_COLUMNS = (
    "execution_duration_ms",
    "cpu_utilization",
    "memory_utilization",
    "active_containers",
    "warm_containers",
    "cold_starts",
    "latency_ms",
    "p95_latency_ms",
    "power_w",
)
NORMATIVE_COLUMNS = ("invocation_count", "cpu_utilization", "memory_utilization", "latency_ms")


class TraceValidationError(ValueError):
    """Raised when a workload trace does not satisfy the required schema (FR-01)."""


def validate_trace(frame: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame):
        raise TraceValidationError("trace must be a pandas DataFrame")

    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise TraceValidationError(f"trace is missing required columns: {missing}")

    out = frame.copy()
    try:
        out["timestamp"] = pd.to_datetime(out["timestamp"], errors="raise")
    except (ValueError, TypeError) as exc:
        raise TraceValidationError(f"timestamp could not be parsed: {exc}") from exc
    if out["timestamp"].isna().any():
        raise TraceValidationError("timestamp contains missing/unparseable values")

    out["function_id"] = out["function_id"].astype(str)

    if not pd.api.types.is_numeric_dtype(out["invocation_count"]):
        raise TraceValidationError("invocation_count must be numeric")

    return out


def read_trace(path: str | Path) -> pd.DataFrame:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"trace file not found: {source}")
    return validate_trace(pd.read_csv(source))


def load_trace(config: dict) -> pd.DataFrame:
    data_config = config.get("data", {})
    source_kind = str(data_config.get("source", "sample")).lower()

    if source_kind == "sample":
        from data.sample import sample_trace

        frame = sample_trace(
            days=int(data_config.get("sample_days", 7)),
            seed=int(data_config.get("seed", 42)),
        )
        return validate_trace(frame)

    if source_kind in ("azure_functions_2019", "azure2019", "azure"):
        # Prepared Azure Functions 2019 invocations trace (see data.azure_functions_2019).
        from data.azure_functions_2019 import load_prepared_as_trace

        azure_cfg = data_config.get("azure", {}) or {}
        prepared_path = azure_cfg.get("processed_path") or data_config.get(
            "prepared_path", "data/processed/azure_features.csv"
        )
        frame = load_prepared_as_trace(
            config=config,
            prepared_path=prepared_path,
            function_limit=azure_cfg.get("function_limit"),
            require_simulated_resources=bool(azure_cfg.get("simulate_resources", False)),
        )
        # Keep only columns compatible with trace schema/validation; split/trigger/day_index are optional extras.
        return validate_trace(frame)

    return read_trace(data_config.get("source_path", "data/raw/trace.csv"))


def summarize_trace(frame: pd.DataFrame) -> dict:
    return {
        "rows": int(len(frame)),
        "functions": sorted(frame["function_id"].unique().tolist()),
        "start": str(frame["timestamp"].min()),
        "end": str(frame["timestamp"].max()),
        "columns": list(frame.columns),
        "normative_present": [c for c in NORMATIVE_COLUMNS if c in frame.columns],
        "normative_missing": [c for c in NORMATIVE_COLUMNS if c not in frame.columns],
    }
