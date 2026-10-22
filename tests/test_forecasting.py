"""TFT forecasting tests: T01-T04 (docs/test_plan.md section 4)."""

import numpy as np
import pytest
import torch

from forecasting.dataset import (
    ForecastData,
    StandardScaler,
    build_windows,
    chronological_boundaries,
    make_forecast_data,
)
from forecasting.evaluate import mae, mape, regression_metrics, rmse
from forecasting.inference import classify_trend, forecast
from forecasting.tft_model import TemporalFusionTransformer
from forecasting.train import load_checkpoint, save_checkpoint, train_tft


def _forecast_data(frame, config):
    forecast_cfg = config["forecast"]
    feature_columns = [forecast_cfg["target_column"]] + list(forecast_cfg["covariates"])
    return make_forecast_data(
        frame,
        feature_columns=feature_columns,
        target_column=forecast_cfg["target_column"],
        history=forecast_cfg["history_window"],
        horizon=forecast_cfg["horizon"],
        split=forecast_cfg["training"]["split"],
    )


# ---------------------------------------------------------------- T01
def test_t01_input_window_length(processed_frame, test_config):
    data = _forecast_data(processed_frame, test_config)
    assert data.X_train.shape[1] == test_config["forecast"]["history_window"]
    assert data.X_val.shape[1] == test_config["forecast"]["history_window"]


# ---------------------------------------------------------------- T02
def test_t02_horizon_length(processed_frame, test_config):
    data = _forecast_data(processed_frame, test_config)
    horizon = test_config["forecast"]["horizon"]
    assert data.y_train.shape[1] == horizon
    assert data.y_val.shape[1] == horizon

    model = TemporalFusionTransformer(n_features=data.n_features, horizon=horizon)
    out = model(torch.randn(4, data.history, data.n_features))
    assert out.shape == (4, horizon)


def test_t02_short_series_raises():
    with pytest.raises(ValueError):
        chronological_boundaries(3, [0.7, 0.15, 0.15])


# ---------------------------------------------------------------- T03
def test_t03_chronological_splits(processed_frame, test_config):
    data = _forecast_data(processed_frame, test_config)
    ranges = data.split_time_ranges
    assert set(ranges) == {"train", "val", "test"}
    train_max = ranges["train"][1]
    val_min, val_max = ranges["val"]
    test_min = ranges["test"][0]
    assert train_max < val_min < val_max < test_min


def test_t03_windows_never_overlap_target():
    # Feature value == row index; target == row index. History must precede
    # the predicted horizon (no leakage of future into input).
    features = np.arange(20, dtype=np.float64).reshape(-1, 1)
    target = np.arange(20, dtype=np.float64)
    x, y = build_windows(features, target, history=3, horizon=2, start=0, end=20)

    assert x.shape[1] == 3 and y.shape[1] == 2
    # Last input step is immediately before the first predicted step.
    assert np.all(y[:, 0] - x[:, -1].reshape(-1) == 1)
    assert np.all(x[:, -1].reshape(-1) < y[:, 0])
    # Every window stays inside [start, end).
    assert x.min() >= 0 and y.max() <= 19


def test_t03_no_windows_when_segment_too_short():
    features = np.zeros((4, 2))
    target = np.zeros(4)
    x, y = build_windows(features, target, history=3, horizon=2, start=0, end=4)
    assert len(x) == 0 and len(y) == 0


# ---------------------------------------------------------------- T04
def test_t04_metric_functions():
    y_true = np.array([1.0, 2.0, 3.0])
    assert mae(y_true, y_true) == 0.0
    assert rmse(y_true, y_true) == 0.0

    y_pred = np.array([2.0, 4.0, 6.0])
    assert mae(y_true, y_pred) == pytest.approx(2.0)
    assert rmse(y_true, y_pred) == pytest.approx(np.sqrt(14 / 3))
    assert mape(y_true, y_pred) == pytest.approx(100.0)
    assert set(regression_metrics(y_true, y_pred)) == {"mae", "rmse", "mape"}


def test_t04_mape_ignores_zero_denominators():
    y_true = np.array([0.0, 1.0, 0.0])
    y_pred = np.array([5.0, 1.0, 5.0])
    assert mape(y_true, y_pred) == pytest.approx(0.0)


def test_t04_model_learns_finite_metrics(processed_frame, test_config):
    model, data, history = train_tft(processed_frame, config=test_config)
    metrics = history["test_metrics"]
    assert set(metrics) == {"mae", "rmse", "mape"} or metrics == {}
    for value in metrics.values():
        assert np.isfinite(value)
    assert all(np.isfinite(history["train_loss"]))
    assert all(np.isfinite(history["val_loss"]))


# ---------------------------------------------------------------- inference
def test_forecast_schema_and_trend(processed_frame, test_config):
    forecast_cfg = test_config["forecast"]
    feature_columns = [forecast_cfg["target_column"]] + list(forecast_cfg["covariates"])
    data = make_forecast_data(
        processed_frame,
        feature_columns=feature_columns,
        target_column=forecast_cfg["target_column"],
        history=forecast_cfg["history_window"],
        horizon=forecast_cfg["horizon"],
        split=forecast_cfg["training"]["split"],
    )
    model, data, _ = train_tft(processed_frame, config=test_config)

    window = data.scaler.inverse_transform(data.X_test[0])
    result = forecast(
        model,
        history_window=window,
        scaler_mean=data.scaler.mean_,
        scaler_std=data.scaler.std_,
        target_index=data.target_index,
    )
    assert result["forecast_horizon"] == forecast_cfg["horizon"]
    assert len(result["predicted_workload"]) == forecast_cfg["horizon"]
    assert all(v >= 0 for v in result["predicted_workload"])
    assert result["trend"] in {"increasing", "decreasing", "stable"}


def test_classify_trend():
    assert classify_trend([1, 2, 3, 10]) == "increasing"
    assert classify_trend([10, 3, 2, 1]) == "decreasing"
    assert classify_trend([5, 5, 5, 5]) == "stable"


def test_checkpoint_round_trip(processed_frame, test_config, tmp_path):
    model, data, _ = train_tft(processed_frame, config=test_config)
    path = str(tmp_path / "tft.pt")
    save_checkpoint(model, data, path, test_config["forecast"]["model"])
    loaded, payload = load_checkpoint(path)
    assert payload["horizon"] == data.horizon
    window = torch.randn(1, data.history, data.n_features)
    with torch.no_grad():
        assert torch.allclose(model(window), loaded(window), atol=1e-5)


def test_scaler_round_trip():
    scaler = StandardScaler().fit(np.array([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]]))
    original = np.array([[5.0, 50.0]])
    assert np.allclose(scaler.inverse_transform(scaler.transform(original)), original)
