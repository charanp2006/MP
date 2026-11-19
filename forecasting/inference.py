"""TFT inference: turn a recent history window into a forecast.

Produces the forecast structure from docs/design.md section 7:

```json
{
  "forecast_horizon": 5,
  "predicted_workload": [710, 760, 820, 900, 960],
  "trend": "increasing"
}
```

The scaler stored in the checkpoint is used to reverse the normalization, so
``predicted_workload`` is in real invocation-count units.
"""

from __future__ import annotations

from typing import Dict, List, Sequence

import numpy as np
import torch

from forecasting.tft_model import TemporalFusionTransformer


def classify_trend(predicted: Sequence[float], threshold_ratio: float = 0.02) -> str:
    """Classify the forecast as increasing / decreasing / stable."""
    values = np.asarray(predicted, dtype=np.float64)
    if len(values) < 2:
        return "stable"
    change = values[-1] - values[0]
    scale = max(np.mean(np.abs(values)), 1e-6)
    if change > threshold_ratio * scale:
        return "increasing"
    if change < -threshold_ratio * scale:
        return "decreasing"
    return "stable"


def predict_scaled_windows(
    model: TemporalFusionTransformer,
    scaled_windows: np.ndarray,
    scaler_mean: np.ndarray,
    scaler_std: np.ndarray,
    target_index: int,
) -> np.ndarray:
    values = np.asarray(scaled_windows, dtype=np.float64)
    squeeze = values.ndim == 2
    if squeeze:
        values = values[None, ...]
    if values.ndim != 3:
        raise ValueError(f"windows must be 2D or 3D, got shape {values.shape}")
    if not np.all(np.isfinite(values)):
        raise ValueError("scaled windows contain non-finite values")

    std = np.asarray(scaler_std, dtype=np.float64)
    mean = np.asarray(scaler_mean, dtype=np.float64)
    tensor = torch.tensor(values, dtype=torch.float32)
    with torch.no_grad():
        pred_scaled = model(tensor).numpy()

    predicted = pred_scaled * std[target_index] + mean[target_index]
    predicted = np.maximum(predicted, 0.0)
    if not np.all(np.isfinite(predicted)):
        raise ValueError("model produced non-finite predictions")
    return predicted[0] if squeeze else predicted


def predict_windows(
    model: TemporalFusionTransformer,
    windows: np.ndarray,
    scaler_mean: np.ndarray,
    scaler_std: np.ndarray,
    target_index: int,
) -> np.ndarray:
    values = np.asarray(windows, dtype=np.float64)
    if values.ndim not in (2, 3):
        raise ValueError(f"windows must be 2D or 3D, got shape {values.shape}")
    mean = np.asarray(scaler_mean, dtype=np.float64)
    std = np.asarray(scaler_std, dtype=np.float64)
    scaled = (values - mean) / std
    if not np.all(np.isfinite(scaled)):
        raise ValueError("history window contains non-finite values after scaling")
    return predict_scaled_windows(model, scaled, mean, std, target_index)


def forecast(
    model: TemporalFusionTransformer,
    history_window: np.ndarray,
    scaler_mean: np.ndarray,
    scaler_std: np.ndarray,
    target_index: int,
) -> Dict:
    """Forecast the workload for the next ``horizon`` steps."""
    window = np.asarray(history_window, dtype=np.float64)
    if window.ndim != 2:
        raise ValueError(f"history_window must be 2D (history, features), got shape {window.shape}")

    predicted = predict_windows(model, window, scaler_mean, scaler_std, target_index)

    return {
        "forecast_horizon": int(model.horizon),
        "predicted_workload": [float(v) for v in predicted],
        "trend": classify_trend(predicted),
    }


def forecast_from_checkpoint(
    payload: Dict, history_window: np.ndarray
) -> Dict:
    """Convenience wrapper that rebuilds the model from a saved checkpoint."""
    from forecasting.tft_model import TemporalFusionTransformer

    model = TemporalFusionTransformer.from_config(
        n_features=payload["n_features"], horizon=payload["horizon"], model_cfg=payload["model_cfg"]
    )
    model.load_state_dict(payload["model_state"])
    model.eval()
    return forecast(
        model,
        history_window,
        scaler_mean=np.asarray(payload["scaler_mean"]),
        scaler_std=np.asarray(payload["scaler_std"]),
        target_index=payload["target_index"],
    )
