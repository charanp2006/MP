"""Load a trained TFT checkpoint and produce forecasts from raw history windows."""
from __future__ import annotations
from typing import Dict, Optional, Sequence
import numpy as np
from forecasting.inference import forecast
from forecasting.train import load_checkpoint

class TFTForecastService:
    def __init__(self, checkpoint_path: str, feature_columns: Optional[Sequence[str]] = None):
        self.checkpoint_path = checkpoint_path
        self.model, self.payload = load_checkpoint(checkpoint_path)
        self.feature_columns = list(feature_columns or self.payload["feature_columns"])
        self.scaler_mean = np.asarray(self.payload["scaler_mean"], dtype=np.float64)
        self.scaler_std = np.asarray(self.payload["scaler_std"], dtype=np.float64)
        self.target_index = int(self.payload["target_index"])
        self.history = int(self.payload["history"])
        self.horizon = int(self.payload["horizon"])

    def forecast_history(self, history_window: np.ndarray) -> Dict:
        hw = np.asarray(history_window, dtype=np.float64)
        if hw.shape[0] != self.history:
            raise ValueError(f"history_window length {hw.shape[0]} != {self.history}")
        if hw.shape[1] != len(self.feature_columns):
            raise ValueError(f"history_window features {hw.shape[1]} != {len(self.feature_columns)}")
        return forecast(self.model, hw, self.scaler_mean, self.scaler_std, self.target_index)
