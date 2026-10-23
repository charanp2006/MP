from __future__ import annotations

import pandas as pd

SYSTEM_FEATURE_COLUMNS = (
    "cpu_utilization",
    "memory_utilization",
    "active_containers",
    "latency_ms",
    "cold_starts",
)

TEMPORAL_COLUMNS = ("hour", "day_of_week", "weekend", "peak_period")

ALLOWED_ROLLING_STATS = ("mean", "max", "min", "std")


def _sorted(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.sort_values(["function_id", "timestamp"], kind="stable")
    return out.reset_index(drop=True)


def add_lag_features(frame: pd.DataFrame, target: str, lags: list[int]) -> tuple[pd.DataFrame, list[str]]:
    out = frame.copy()
    columns = []
    for lag in sorted({int(lag) for lag in lags}):
        if lag <= 0:
            continue
        column = f"{target}_lag_{lag}"
        out[column] = out.groupby("function_id", sort=False)[target].shift(lag)
        columns.append(column)
    return out, columns


def add_rolling_features(
    frame: pd.DataFrame, target: str, windows: list[int], stats: list[str]
) -> tuple[pd.DataFrame, list[str]]:
    out = frame.copy()
    columns = []
    selected_stats = [s for s in stats if s in ALLOWED_ROLLING_STATS]
    for window in sorted({int(w) for w in windows if int(w) > 0}):
        for stat in selected_stats:
            column = f"{target}_roll{window}_{stat}"
            out[column] = out.groupby("function_id", sort=False)[target].transform(
                lambda s, w=window, st=stat: getattr(s.rolling(w, min_periods=w), st)()
            )
            columns.append(column)
    return out, columns


def add_temporal_features(frame: pd.DataFrame, peak_hours: list[int]) -> pd.DataFrame:
    out = frame.copy()
    timestamp = out["timestamp"]
    out["hour"] = timestamp.dt.hour
    out["day_of_week"] = timestamp.dt.dayofweek
    out["weekend"] = (out["day_of_week"] >= 5).astype(int)
    out["peak_period"] = out["hour"].isin(list(peak_hours)).astype(int)
    return out


def build_features(frame: pd.DataFrame, config: dict | None = None) -> tuple[pd.DataFrame, dict]:
    config = config or {}
    data_config = config.get("data", {})
    features_config = config.get("features", {})

    target = data_config.get("target_column", "invocation_count")
    lags = list(features_config.get("lags", [1, 2, 3]))
    windows = list(features_config.get("rolling_windows", [5, 10, 30]))
    stats = list(features_config.get("rolling_stats", ["mean", "max", "min", "std"]))
    peak_hours = list(features_config.get("peak_hours", list(range(9, 18))))

    if target not in frame.columns:
        raise ValueError(f"target column not found in frame: {target}")

    work = _sorted(frame)
    rows_in = int(len(work))

    work, lag_columns = add_lag_features(work, target, lags)
    work, rolling_columns = add_rolling_features(work, target, windows, stats)
    work = add_temporal_features(work, peak_hours)

    system_columns = [c for c in SYSTEM_FEATURE_COLUMNS if c in work.columns]
    engineered = lag_columns + rolling_columns

    rows_dropped = 0
    if engineered:
        before = int(len(work))
        work = work.dropna(subset=engineered)
        rows_dropped = before - int(len(work))
        work = work.reset_index(drop=True)

    feature_columns = engineered + list(TEMPORAL_COLUMNS) + system_columns
    report = {
        "target": target,
        "lags": [int(l) for l in lags if int(l) > 0],
        "lag_columns": lag_columns,
        "rolling_windows": [int(w) for w in windows if int(w) > 0],
        "rolling_columns": rolling_columns,
        "temporal_columns": list(TEMPORAL_COLUMNS),
        "system_columns": system_columns,
        "feature_columns": feature_columns,
        "n_features": len(feature_columns),
        "rows_in": rows_in,
        "rows_dropped_warmup": rows_dropped,
        "rows_out": int(len(work)),
        "normalization": "deferred: scaler is fit on the train split only (P2, see data.normalize)",
    }
    return work, report
