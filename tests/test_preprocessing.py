import numpy as np
import pandas as pd
import pytest

from data.preprocessing import (
    deduplicate,
    fill_missing,
    missing_report,
    preprocess,
    repair_outliers,
    resample_frame,
    sort_chronological,
)

CONFIG = {"control": {"interval_seconds": 60}, "data": {"dedupe_policy": "last"}}


def make_frame(rows):
    return pd.DataFrame(rows)


def test_d01_chronological_ordering():
    frame = make_frame(
        {
            "timestamp": [
                "2026-01-05T10:02:00",
                "2026-01-05T10:00:00",
                "2026-01-05T10:01:00",
                "2026-01-05T10:00:30",
            ],
            "function_id": ["fn_a", "fn_a", "fn_a", "fn_a"],
            "invocation_count": [30, 10, 20, 15],
        }
    )
    out = sort_chronological(frame)
    assert out["timestamp"].is_monotonic_increasing
    assert out["invocation_count"].tolist() == [10, 15, 20, 30]


def test_d02_duplicate_last_policy():
    frame = make_frame(
        {
            "timestamp": ["2026-01-05T10:00:00"] * 3 + ["2026-01-05T10:01:00"],
            "function_id": ["fn_a"] * 4,
            "invocation_count": [5, 9, 7, 12],
        }
    )
    out, report = deduplicate(frame, policy="last")
    assert report["rows_with_duplicates"] == 3
    assert report["rows_removed"] == 2
    assert out["invocation_count"].tolist() == [7, 12]


def test_d02_duplicate_mean_policy():
    frame = make_frame(
        {
            "timestamp": ["2026-01-05T10:00:00", "2026-01-05T10:00:00"],
            "function_id": ["fn_a", "fn_a"],
            "invocation_count": [10, 20],
        }
    )
    out, _ = deduplicate(frame, policy="mean")
    assert out["invocation_count"].tolist() == [15.0]


def test_d02_unknown_policy_raises():
    frame = make_frame(
        {
            "timestamp": ["2026-01-05T10:00:00"],
            "function_id": ["fn_a"],
            "invocation_count": [1],
        }
    )
    with pytest.raises(ValueError, match="dedupe_policy"):
        deduplicate(frame, policy="bogus")


def test_d03_missing_metrics_reported_and_filled():
    frame = make_frame(
        {
            "timestamp": [
                "2026-01-05T10:00:00",
                "2026-01-05T10:01:00",
                "2026-01-05T10:02:00",
            ],
            "function_id": ["fn_a", "fn_a", "fn_a"],
            "invocation_count": [10, 20, 30],
            "cpu_utilization": [0.5, np.nan, 0.7],
            "latency_ms": [120.0, np.nan, 140.0],
        }
    )
    report = missing_report(frame)
    assert report["nan_counts"]["cpu_utilization"] == 1
    assert report["nan_counts"]["latency_ms"] == 1
    assert "memory_utilization" in report["absent_columns"]

    filled = fill_missing(frame)
    assert filled["cpu_utilization"].isna().sum() == 0
    assert filled["latency_ms"].isna().sum() == 0
    assert filled.loc[1, "cpu_utilization"] == 0.5
    assert filled.loc[1, "latency_ms"] == 120.0


def test_d04_outliers_detected_and_repaired():
    frame = make_frame(
        {
            "timestamp": [
                "2026-01-05T10:00:00",
                "2026-01-05T10:01:00",
                "2026-01-05T10:02:00",
                "2026-01-05T10:03:00",
            ],
            "function_id": ["fn_a"] * 4,
            "invocation_count": [100, -5, 200, 150],
            "cpu_utilization": [0.5, 1.8, 0.6, 0.4],
            "memory_utilization": [0.4, 0.5, -0.2, 0.6],
            "latency_ms": [120.0, -10.0, 130.0, 140.0],
        }
    )
    out, report = repair_outliers(frame)
    assert report["invocation_count"] == 1
    assert report["cpu_utilization"] == 1
    assert report["memory_utilization"] == 1
    assert report["latency_ms"] == 1

    assert (out["invocation_count"].dropna() >= 0).all()
    assert (out["cpu_utilization"].dropna() <= 1.0).all()
    assert (out["memory_utilization"].dropna() >= 0).all()
    assert (out["latency_ms"].dropna() >= 0).all()
    assert out.loc[1, "invocation_count"] != -5


def test_resample_sums_counts_and_fills_gaps():
    frame = make_frame(
        {
            "timestamp": pd.date_range("2026-01-05 10:00:00", periods=4, freq="30s"),
            "function_id": ["fn_a"] * 4,
            "invocation_count": [1, 2, 3, 4],
            "cpu_utilization": [0.5, 0.6, 0.7, 0.8],
        }
    )
    out = resample_frame(frame, 60)
    assert len(out) == 2
    assert out["invocation_count"].tolist() == [3, 7]
    assert out["cpu_utilization"].tolist() == [0.55, 0.75]

    gap_frame = make_frame(
        {
            "timestamp": pd.to_datetime(
                ["2026-01-05 10:00:00", "2026-01-05 10:01:00", "2026-01-05 10:05:00"]
            ),
            "function_id": ["fn_a"] * 3,
            "invocation_count": [10, 10, 10],
            "cpu_utilization": [0.5, 0.5, 0.5],
        }
    )
    gapped = resample_frame(gap_frame, 60)
    assert len(gapped) == 6
    assert gapped["invocation_count"].tolist() == [10, 10, 0, 0, 0, 10]
    filled = fill_missing(gapped)
    assert filled["cpu_utilization"].isna().sum() == 0
    assert filled["invocation_count"].isna().sum() == 0


def test_preprocess_end_to_end_report():
    frame = make_frame(
        {
            "timestamp": pd.to_datetime(
                [
                    "2026-01-05 10:01:00",
                    "2026-01-05 10:00:30",
                    "2026-01-05 10:00:00",
                    "2026-01-05 10:00:00",
                    "2026-01-05 10:04:00",
                ]
            ),
            "function_id": ["fn_a"] * 5,
            "invocation_count": [30, 15, 10, 99, 40],
            "cpu_utilization": [0.5, 0.55, 0.4, 2.5, 0.6],
            "latency_ms": [130.0, 125.0, 120.0, -1.0, 150.0],
        }
    )
    out, report = preprocess(frame, CONFIG)
    assert report["rows_in"] == 5
    assert report["duplicates"]["rows_removed"] == 1
    assert report["outliers"]["cpu_utilization"] == 1
    assert report["outliers"]["latency_ms"] == 1
    assert report["missing_after_fill"]["nan_counts"] == {}
    assert report["chronological"] is True
    assert report["interval_seconds"] == 60
    assert out["invocation_count"].isna().sum() == 0
    assert out["cpu_utilization"].max() <= 1.0
    assert (out["latency_ms"] >= 0).all()
    assert out["timestamp"].is_monotonic_increasing
