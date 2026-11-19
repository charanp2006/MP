"""Naive forecast baselines evaluated on the same test windows as the TFT."""

from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

from forecasting.dataset import ForecastData


def _repeat(values: np.ndarray, horizon: int) -> np.ndarray:
    return np.repeat(np.maximum(values, 0.0)[:, None], horizon, axis=1)


def persistence(data: ForecastData) -> np.ndarray:
    last_scaled = data.X_test[:, -1, data.target_index]
    last_value = data.scaler.inverse_column(last_scaled, data.target_index)
    return _repeat(last_value, data.horizon)


def moving_average(data: ForecastData, window: int = 5) -> np.ndarray:
    steps = min(max(int(window), 1), data.history)
    recent_scaled = data.X_test[:, -steps:, data.target_index]
    recent = data.scaler.inverse_column(recent_scaled, data.target_index)
    return _repeat(recent.mean(axis=1), data.horizon)


def seasonal_persistence(
    data: ForecastData,
    frame: pd.DataFrame,
    seasonal_period: int = 1440,
    interval_seconds: int = 60,
) -> np.ndarray:
    if data.X_test_raw is None or not data.sample_index.get("test"):
        raise ValueError("seasonal persistence requires raw test windows and sample_index")

    lookup: Dict[tuple[str, pd.Timestamp], float] = {}
    for function_id, group in frame.groupby("function_id", sort=False):
        for timestamp, value in zip(group["timestamp"], group[data.feature_columns[data.target_index]]):
            lookup[(str(function_id), pd.Timestamp(timestamp))] = float(value)

    fallback = persistence(data)
    step = pd.Timedelta(seconds=int(seasonal_period) * int(interval_seconds))
    predictions = np.empty_like(fallback)
    for index, (function_id, _, target_start) in enumerate(data.sample_index["test"]):
        value = lookup.get((function_id, pd.Timestamp(target_start) - step))
        if value is None or not np.isfinite(value):
            value = fallback[index, 0]
        predictions[index, :] = max(float(value), 0.0)
    return predictions


def baseline_predictions(
    data: ForecastData,
    frame: pd.DataFrame,
    seasonal_period: int = 1440,
    interval_seconds: int = 60,
    moving_average_window: int = 5,
) -> Dict[str, np.ndarray]:
    return {
        "persistence": persistence(data),
        "seasonal_persistence": seasonal_persistence(
            data, frame, seasonal_period, interval_seconds
        ),
        "moving_average": moving_average(data, moving_average_window),
    }
