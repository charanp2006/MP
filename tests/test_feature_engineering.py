import numpy as np
import pandas as pd
import pytest

from data.feature_engineering import add_temporal_features, build_features

CONFIG = {
    "data": {"target_column": "invocation_count"},
    "features": {
        "lags": [1, 2],
        "rolling_windows": [3],
        "rolling_stats": ["mean", "max"],
        "peak_hours": [9, 10, 11, 12, 13, 14, 15, 16, 17],
    },
}


def make_frame(invocations, start="2026-01-05 08:00:00", function_id="fn_a"):
    timestamps = pd.date_range(start, periods=len(invocations), freq="60s")
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "function_id": function_id,
            "invocation_count": invocations,
            "cpu_utilization": np.linspace(0.3, 0.7, len(invocations)),
        }
    )


def test_lag_features_are_previous_values():
    frame = make_frame([10, 20, 30, 40, 50, 60])
    out, _ = build_features(frame, CONFIG)
    assert out["invocation_count_lag_1"].iloc[0] == 20
    assert out["invocation_count_lag_2"].iloc[0] == 10
    assert out["invocation_count_lag_1"].iloc[-1] == 50


def test_rolling_mean_matches_window():
    frame = make_frame([10, 20, 30, 40, 50, 60])
    out, report = build_features(frame, CONFIG)
    assert "invocation_count_roll3_mean" in report["rolling_columns"]
    assert out["invocation_count_roll3_mean"].iloc[0] == 20.0
    assert out["invocation_count_roll3_max"].iloc[0] == 30.0


def test_no_leakage_rolling_excludes_future():
    frame = make_frame([10, 20, 30, 40, 50, 60])
    out, _ = build_features(frame, CONFIG)
    expected_first_roll = np.mean([10, 20, 30])
    assert out["invocation_count_roll3_mean"].iloc[0] == expected_first_roll
    assert out["invocation_count_roll3_mean"].iloc[0] != np.mean([10, 20, 30, 40, 50, 60])


def test_warmup_rows_dropped():
    frame = make_frame([10, 20, 30, 40, 50, 60])
    out, report = build_features(frame, CONFIG)
    assert report["rows_dropped_warmup"] > 0
    assert out["invocation_count_lag_2"].isna().sum() == 0
    assert report["rows_out"] == report["rows_in"] - report["rows_dropped_warmup"]


def test_temporal_features():
    frame = make_frame([10, 20], start="2026-01-05 09:30:00")
    out = add_temporal_features(frame, peak_hours=[9, 10])
    assert out["hour"].tolist() == [9, 9]
    assert out["day_of_week"].tolist() == [0, 0]
    assert out["weekend"].tolist() == [0, 0]
    assert out["peak_period"].tolist() == [1, 1]

    weekend_frame = make_frame([10], start="2026-01-04 22:00:00")
    weekend_out = add_temporal_features(weekend_frame, peak_hours=[9])
    assert weekend_out["weekend"].tolist() == [1]
    assert weekend_out["peak_period"].tolist() == [0]


def test_lags_are_per_function():
    frame = pd.concat(
        [
            make_frame([10, 20, 30, 40], function_id="fn_a"),
            make_frame([100, 200, 300, 400], function_id="fn_b"),
        ],
        ignore_index=True,
    )
    out, _ = build_features(frame, CONFIG)
    fn_b = out[out["function_id"] == "fn_b"].reset_index(drop=True)
    assert fn_b["invocation_count_lag_1"].iloc[0] == 200
    assert fn_b["invocation_count_lag_1"].iloc[1] == 300
    assert fn_b["invocation_count_lag_2"].iloc[0] == 100


def test_missing_target_raises():
    frame = make_frame([10, 20]).drop(columns=["invocation_count"])
    with pytest.raises(ValueError, match="invocation_count"):
        build_features(frame, CONFIG)


def test_feature_columns_exclude_ids_and_target():
    frame = make_frame([10, 20, 30, 40, 50, 60])
    out, report = build_features(frame, CONFIG)
    for column in ("timestamp", "function_id", "invocation_count"):
        assert column not in report["feature_columns"]
    assert set(report["feature_columns"]).issubset(set(out.columns))
