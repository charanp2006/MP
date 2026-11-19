"""Milestone 3 tests: baselines, extended metrics, fallback, and artifacts."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from configs import load_config
from data.pipeline import run as run_pipeline
from forecasting.baselines import (
    baseline_predictions,
    moving_average,
    persistence,
    seasonal_persistence,
)
from forecasting.dataset import make_forecast_data
from forecasting.evaluate import (
    apply_residual_interval,
    calibrate_residual_interval,
    forecast_metrics,
    interval_metrics,
)
from forecasting.evaluation import run_forecast_evaluation
from forecasting.inference import predict_scaled_windows, predict_windows
from forecasting.tft_service import TFTForecastService
from forecasting.train import save_checkpoint, train_tft


@pytest.fixture(scope="module")
def m3_bundle(tmp_path_factory):
    config = load_config()
    config["data"]["sample_days"] = 1
    config["data"]["seed"] = 7
    config["features"]["rolling_windows"] = [5]
    config["forecast"]["training"]["epochs"] = 1
    frame, _ = run_pipeline(config=config)
    model, data, history = train_tft(frame, config=config)
    checkpoint = tmp_path_factory.mktemp("m3") / "tft.pt"
    save_checkpoint(model, data, str(checkpoint), config["forecast"]["model"])
    return config, frame, model, data, history, str(checkpoint)


def test_m3_extended_metrics():
    truth = np.array([1.0, 2.0, 3.0])
    pred = np.array([2.0, 4.0, 6.0])
    metrics = forecast_metrics(truth, pred, peak_quantile=0.9)
    assert metrics["mae"] == pytest.approx(2.0)
    assert metrics["rmse"] == pytest.approx(np.sqrt(14 / 3))
    assert metrics["mape"] == pytest.approx(100.0)
    assert metrics["wape"] == pytest.approx(100.0)
    assert metrics["smape"] == pytest.approx(200 / 3)
    assert metrics["bias"] == pytest.approx(2.0)
    assert metrics["peak_underprediction_rate"] == 0.0
    assert metrics["n"] == 3.0


def test_m3_interval_calibration_and_coverage():
    calibration = calibrate_residual_interval(
        np.array([10.0, 12.0, 14.0]), np.array([12.0, 12.0, 12.0]), alpha=0.2
    )
    lower, upper = apply_residual_interval(np.array([12.0, 12.0]), calibration)
    metrics = interval_metrics(np.array([11.0, 20.0]), lower, upper)
    assert calibration["lower"] == pytest.approx(-1.6)
    assert calibration["upper"] == pytest.approx(1.6)
    assert lower[0] <= 12.0 <= upper[0]
    assert 0.0 <= metrics["coverage"] <= 1.0
    assert metrics["under_coverage_rate"] == 0.0
    assert metrics["over_coverage_rate"] == pytest.approx(0.5)


def test_m3_seasonal_baseline_uses_prior_day():
    season = 1440
    timestamps = pd.date_range("2026-01-01", periods=2 * season, freq="min", tz="UTC")
    values = 100.0 + np.sin(np.arange(len(timestamps)) / 50.0) * 20.0
    frame = pd.DataFrame(
        {
            "timestamp": timestamps,
            "function_id": "fn-a",
            "invocation_count": values,
        }
    )
    data = make_forecast_data(
        frame,
        feature_columns=["invocation_count"],
        target_column="invocation_count",
        history=3,
        horizon=2,
        split=[0.7, 0.15, 0.15],
    )
    predictions = seasonal_persistence(data, frame, seasonal_period=season, interval_seconds=60)
    expected = []
    lookup = dict(zip(timestamps, values))
    for _, _, target_start in data.sample_index["test"]:
        expected.append(lookup[pd.Timestamp(target_start) - pd.Timedelta(days=1)])
    assert predictions.shape == data.y_test_raw.shape
    assert np.allclose(predictions[:, 0], np.asarray(expected))
    assert np.all(predictions >= 0.0)


def test_m3_baselines_finite_on_forecast_data(m3_bundle):
    _, frame, _, data, _, _ = m3_bundle
    predictions = baseline_predictions(data, frame, seasonal_period=1440)
    assert set(predictions) == {"persistence", "seasonal_persistence", "moving_average"}
    for values in predictions.values():
        assert values.shape == data.y_test.shape
        assert np.all(np.isfinite(values))
        assert np.all(values >= 0.0)
    assert np.allclose(persistence(data), np.repeat(persistence(data)[:, :1], data.horizon, axis=1))
    assert moving_average(data, 1).shape == data.y_test.shape


def test_m3_raw_and_scaled_inference_agree(m3_bundle):
    _, _, model, data, _, _ = m3_bundle
    raw = data.scaler.inverse_transform(data.X_test[:3])
    raw_pred = predict_windows(
        model, raw, data.scaler.mean_, data.scaler.std_, data.target_index
    )
    scaled_pred = predict_scaled_windows(
        model, data.X_test[:3], data.scaler.mean_, data.scaler.std_, data.target_index
    )
    assert np.allclose(raw_pred, scaled_pred, atol=1e-3)


def test_m3_service_fallback_and_staleness(m3_bundle):
    _, _, _, data, _, checkpoint = m3_bundle
    service = TFTForecastService(checkpoint)
    window = data.scaler.inverse_transform(data.X_test[0])
    valid = service.forecast_history(window, observed_at=pd.Timestamp.now())
    assert valid["source"] == "tft"
    assert valid["fallback"] is False
    assert len(valid["predicted_workload"]) == data.horizon

    corrupted = window.copy()
    corrupted[0, data.target_index] = np.nan
    fallback = service.forecast_history(corrupted, observed_at=pd.Timestamp.now())
    assert fallback["source"] == "fallback_persistence"
    assert fallback["fallback"] is True
    assert "non_finite_input" in fallback["fallback_reason"]

    stale_service = TFTForecastService(checkpoint, max_staleness_s=1)
    stale = stale_service.forecast_history(
        window, observed_at=pd.Timestamp.now() - pd.Timedelta(hours=1)
    )
    assert stale["source"] == "fallback_persistence"
    assert "stale_input" in stale["fallback_reason"]


def test_m3_evaluation_artifacts(m3_bundle, tmp_path):
    config, frame, model, data, history, _ = m3_bundle
    result = run_forecast_evaluation(
        frame,
        config,
        run_id="m3-smoke",
        out_dir=tmp_path,
        model=model,
        data=data,
        history=history,
    )
    assert set(result["models"]) == {
        "tft",
        "persistence",
        "seasonal_persistence",
        "moving_average",
    }
    for entry in result["models"].values():
        assert {
            "mae",
            "rmse",
            "mape",
            "wape",
            "smape",
            "bias",
            "peak_underprediction_rate",
        } <= set(entry["overall"])
    assert (tmp_path / "predictions.csv").is_file()
    assert (tmp_path / "metrics.json").is_file()
    assert (tmp_path / "checkpoint.pt").is_file()
    assert len(result["artifacts"]["plots"]) >= 7
