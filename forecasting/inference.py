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


def forecast(
    model: TemporalFusionTransformer,
    history_window: np.ndarray,
    scaler_mean: np.ndarray,
    scaler_std: np.ndarray,
    target_index: int,
) -> Dict:
    """Forecast the workload for the next ``horizon`` steps.

    ``history_window`` is a raw (history, n_features) array in real units; it is
    normalized here with the train-fit scaler before being fed to the model.
    """
    window = np.asarray(history_window, dtype=np.float64)
    if window.ndim != 2:
        raise ValueError(f"history_window must be 2D (history, features), got shape {window.shape}")

    scaled = (window - np.asarray(scaler_mean)) / np.asarray(scaler_std)
    tensor = torch.tensor(scaled, dtype=torch.float32).unsqueeze(0)  # (1, history, F)
    with torch.no_grad():
        pred_scaled = model(tensor).squeeze(0).numpy()  # (horizon,)

    predicted = pred_scaled * scaler_std[target_index] + scaler_mean[target_index]
    predicted = np.maximum(predicted, 0.0)  # workload cannot be negative

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
