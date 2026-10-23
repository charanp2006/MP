import numpy as np
import pandas as pd

from data.pipeline import run, save_features

CONFIG = {
    "control": {"interval_seconds": 60},
    "data": {
        "source": "sample",
        "sample_days": 1,
        "seed": 7,
        "dedupe_policy": "last",
        "target_column": "invocation_count",
        "processed_path": "data/processed/features.csv",
    },
    "features": {
        "lags": [1, 2, 3],
        "rolling_windows": [5, 10],
        "rolling_stats": ["mean", "max", "min", "std"],
        "peak_hours": list(range(9, 18)),
    },
}


def test_pipeline_produces_clean_features():
    features, report = run(config=CONFIG)

    assert report["ingest"]["rows"] > 0
    assert report["preprocess"]["chronological"] is True
    assert report["preprocess"]["missing_after_fill"]["nan_counts"] == {}
    assert report["features"]["rows_out"] > 0

    assert features["invocation_count"].isna().sum() == 0
    assert (features["invocation_count"] >= 0).all()
    assert (features["cpu_utilization"] <= 1.0).all()
    monotonic = features.groupby("function_id")["timestamp"].apply(lambda s: s.is_monotonic_increasing)
    assert monotonic.all()

    for column in ("invocation_count_lag_1", "invocation_count_roll5_mean", "hour", "weekend"):
        assert column in features.columns
        assert features[column].isna().sum() == 0


def test_pipeline_deterministic_with_seed():
    first, _ = run(config=CONFIG)
    second, _ = run(config=CONFIG)
    pd.testing.assert_frame_equal(first, second)


def test_save_features_writes_csv(tmp_path):
    config = dict(CONFIG)
    config["data"] = dict(CONFIG["data"])
    config["data"]["processed_path"] = str(tmp_path / "features.csv")

    features, _ = run(config=config)
    saved_to = save_features(features, config)

    assert (tmp_path / "features.csv").exists()
    reloaded = pd.read_csv(saved_to)
    assert len(reloaded) == len(features)
    assert "invocation_count" in reloaded.columns
    assert not np.isnan(reloaded.select_dtypes(include=[np.number]).to_numpy()).any()
