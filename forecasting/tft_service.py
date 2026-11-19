"""Load a trained TFT checkpoint and produce validated forecasts with fallback."""

from __future__ import annotations

from typing import Dict, Optional, Sequence

import numpy as np
import pandas as pd

from forecasting.inference import forecast
from forecasting.train import load_checkpoint


class TFTForecastService:
    def __init__(
        self,
        checkpoint_path: str,
        feature_columns: Optional[Sequence[str]] = None,
        fallback_policy: str = "persistence",
        max_staleness_s: Optional[float] = None,
    ):
        if fallback_policy != "persistence":
            raise ValueError(f"unsupported fallback_policy: {fallback_policy}")
        self.checkpoint_path = checkpoint_path
        self.model, self.payload = load_checkpoint(checkpoint_path)
        self.feature_columns = list(feature_columns or self.payload["feature_columns"])
        self.scaler_mean = np.asarray(self.payload["scaler_mean"], dtype=np.float64)
        self.scaler_std = np.asarray(self.payload["scaler_std"], dtype=np.float64)
        self.target_index = int(self.payload["target_index"])
        self.history = int(self.payload["history"])
        self.horizon = int(self.payload["horizon"])
        self.fallback_policy = fallback_policy
        self.max_staleness_s = max_staleness_s

    def _result(self, values, source: str, reason: Optional[str], observed_at) -> Dict:
        return {
            "forecast_horizon": self.horizon,
            "predicted_workload": [float(v) for v in values],
            "trend": self._trend(values),
            "source": source,
            "fallback": source != "tft",
            "fallback_reason": reason,
            "model_id": "compact_tft_pytorch",
            "checkpoint_path": self.checkpoint_path,
            "feature_columns": self.feature_columns,
            "observed_at": None if observed_at is None else str(observed_at),
        }

    @staticmethod
    def _trend(values) -> str:
        series = np.asarray(values, dtype=np.float64)
        if len(series) < 2:
            return "stable"
        change = series[-1] - series[0]
        scale = max(float(np.mean(np.abs(series))), 1e-6)
        if change > 0.02 * scale:
            return "increasing"
        if change < -0.02 * scale:
            return "decreasing"
        return "stable"

    def _fallback(self, window: np.ndarray, reason: str, observed_at) -> Dict:
        target = window[:, self.target_index]
        finite = target[np.isfinite(target)]
        if finite.size == 0:
            raise ValueError("no finite target observations available for fallback")
        value = max(float(finite[-1]), 0.0)
        return self._result(np.full(self.horizon, value), "fallback_persistence", reason, observed_at)

    def _staleness_reason(self, observed_at) -> Optional[str]:
        if observed_at is None or self.max_staleness_s is None:
            return None
        observed = pd.Timestamp(observed_at)
        now = pd.Timestamp.now(tz=observed.tz) if observed.tzinfo else pd.Timestamp.now()
        age_s = (now - observed).total_seconds()
        if age_s > float(self.max_staleness_s):
            return f"stale_input: age={age_s:.1f}s > {self.max_staleness_s}s"
        return None

    def forecast_history(self, history_window: np.ndarray, observed_at=None) -> Dict:
        if history_window is None:
            raise ValueError("history_window is required")
        window = np.asarray(history_window, dtype=np.float64)
        if window.ndim != 2:
            raise ValueError(f"history_window must be 2D, got shape {window.shape}")
        if window.shape[0] != self.history:
            raise ValueError(f"history_window length {window.shape[0]} != {self.history}")
        if window.shape[1] != len(self.feature_columns):
            raise ValueError(
                f"history_window features {window.shape[1]} != {len(self.feature_columns)}"
            )

        stale = self._staleness_reason(observed_at)
        if stale:
            return self._fallback(window, stale, observed_at)
        if not np.all(np.isfinite(window)):
            return self._fallback(window, "non_finite_input", observed_at)

        try:
            result = forecast(
                self.model,
                window,
                self.scaler_mean,
                self.scaler_std,
                self.target_index,
            )
        except Exception as exc:
            return self._fallback(window, f"model_error: {exc}", observed_at)
        return self._result(
            result["predicted_workload"], "tft", None, observed_at
        )
