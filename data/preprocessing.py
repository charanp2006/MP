from __future__ import annotations

import numpy as np
import pandas as pd

from data.ingestion import validate_trace

OUTLIER_RULES: dict[str, tuple[float | None, float | None]] = {
    "invocation_count": (0.0, None),
    "execution_duration_ms": (0.0, None),
    "cpu_utilization": (0.0, 1.0),
    "memory_utilization": (0.0, 1.0),
    "latency_ms": (0.0, None),
    "p95_latency_ms": (0.0, None),
    "active_containers": (0.0, None),
    "warm_containers": (0.0, None),
    "cold_starts": (0.0, None),
    "power_w": (0.0, None),
}

AGGREGATIONS: dict[str, str] = {
    "invocation_count": "sum",
    "execution_duration_ms": "mean",
    "cpu_utilization": "mean",
    "memory_utilization": "mean",
    "active_containers": "mean",
    "warm_containers": "mean",
    "cold_starts": "sum",
    "latency_ms": "mean",
    "p95_latency_ms": "mean",
    "power_w": "mean",
}

EXPECTED_COLUMNS = (
    "invocation_count",
    "cpu_utilization",
    "memory_utilization",
    "latency_ms",
    "active_containers",
)

ZERO_FILL_COLUMNS = ("invocation_count", "cold_starts")

ID_COLUMNS = ("timestamp", "function_id")


def sort_chronological(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.sort_values(["timestamp", "function_id"], kind="stable")
    return out.reset_index(drop=True)


def deduplicate(frame: pd.DataFrame, policy: str = "last") -> tuple[pd.DataFrame, dict]:
    keys = ["timestamp", "function_id"]
    rows_with_duplicates = int(frame.duplicated(subset=keys, keep=False).sum())
    policy = str(policy).lower()

    if policy == "mean":
        numeric_cols = [
            c for c in frame.columns if c not in keys and pd.api.types.is_numeric_dtype(frame[c])
        ]
        out = frame.groupby(keys, as_index=False, sort=False)[numeric_cols].mean()
    elif policy in ("first", "last"):
        out = frame.drop_duplicates(subset=keys, keep=policy)
    else:
        raise ValueError(f"unknown dedupe_policy: {policy!r} (expected first|last|mean)")

    out = sort_chronological(out)
    report = {
        "policy": policy,
        "rows_with_duplicates": rows_with_duplicates,
        "rows_removed": int(len(frame) - len(out)),
    }
    return out, report


def _outlier_mask(series: pd.DataFrame, bounds: tuple[float | None, float | None]) -> tuple[pd.Series, pd.Series]:
    low, high = bounds
    numeric = pd.to_numeric(series, errors="coerce")
    mask = series.notna() & numeric.isna()
    if low is not None:
        mask = mask | (numeric < low)
    if high is not None:
        mask = mask | (numeric > high)
    return mask.fillna(False).astype(bool), numeric


def repair_outliers(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    out = frame.copy()
    report: dict[str, int] = {}
    for column, bounds in OUTLIER_RULES.items():
        if column not in out.columns:
            continue
        mask, numeric = _outlier_mask(out[column], bounds)
        count = int(mask.sum())
        report[column] = count
        if count:
            out[column] = numeric.where(~mask, np.nan)
    return out, report


def missing_report(frame: pd.DataFrame) -> dict:
    nan_counts = {}
    for column in frame.columns:
        if column in ID_COLUMNS or not pd.api.types.is_numeric_dtype(frame[column]):
            continue
        count = int(frame[column].isna().sum())
        if count:
            nan_counts[column] = count
    absent = [column for column in EXPECTED_COLUMNS if column not in frame.columns]
    return {"nan_counts": nan_counts, "absent_columns": absent}


def resample_frame(frame: pd.DataFrame, interval_seconds: int) -> pd.DataFrame:
    freq = f"{int(interval_seconds)}s"
    agg = {c: f for c, f in AGGREGATIONS.items() if c in frame.columns}
    if not agg:
        raise ValueError("no aggregatable metric columns found in trace")

    work = frame.copy()
    work["__bin"] = work["timestamp"].dt.floor(freq)
    grouped = work.groupby(["function_id", "__bin"], as_index=False)[list(agg)].agg(agg)

    pieces = []
    for function_id, part in grouped.groupby("function_id", sort=True):
        bins = pd.date_range(part["__bin"].min(), part["__bin"].max(), freq=freq)
        part = part.set_index("__bin").reindex(bins)
        part.index.name = "__bin"
        part = part.reset_index()
        part["function_id"] = function_id
        pieces.append(part)

    out = pd.concat(pieces, ignore_index=True)
    out = out.rename(columns={"__bin": "timestamp"})

    sum_columns = [c for c, f in agg.items() if f == "sum"]
    if sum_columns:
        out[sum_columns] = out[sum_columns].fillna(0)

    out = out.sort_values(["function_id", "timestamp"], kind="stable")
    return out.reset_index(drop=True)


def fill_missing(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for column in out.columns:
        if column in ID_COLUMNS or not pd.api.types.is_numeric_dtype(out[column]):
            continue
        if column in ZERO_FILL_COLUMNS:
            out[column] = out[column].fillna(0)
        else:
            out[column] = out[column].ffill().bfill().fillna(0)
    return out


def preprocess(frame: pd.DataFrame, config: dict | None = None) -> tuple[pd.DataFrame, dict]:
    config = config or {}
    data_config = config.get("data", {})
    control_config = config.get("control", {})
    interval = int(control_config.get("interval_seconds", 60))
    policy = data_config.get("dedupe_policy", "last")

    work = validate_trace(frame)
    rows_in = int(len(work))

    work = sort_chronological(work)
    work, duplicate_report = deduplicate(work, policy)
    work, outlier_report = repair_outliers(work)

    report: dict = {
        "rows_in": rows_in,
        "duplicates": duplicate_report,
        "outliers": outlier_report,
        "missing_raw": missing_report(work),
    }

    work = resample_frame(work, interval)
    report["missing_resampled"] = missing_report(work)

    work = fill_missing(work)
    report["missing_after_fill"] = missing_report(work)
    report["rows_out"] = int(len(work))
    report["interval_seconds"] = interval
    report["chronological"] = bool(
        work.groupby("function_id")["timestamp"].apply(lambda s: bool(s.is_monotonic_increasing)).all()
    )
    return work, report
