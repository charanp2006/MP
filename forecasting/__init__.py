"""TFT workload forecasting (image step 3).

Module layout follows docs/design.md section 2:

* ``dataset``          --- window generator + chronological splits (leakage-safe).
* ``tft_model``        --- compact Temporal Fusion Transformer (pure PyTorch).
* ``train``            --- training loop with validation and checkpointing.
* ``evaluate``         --- MAE / RMSE / MAPE metrics (test T04).
* ``inference``        --- forecast -> {forecast_horizon, predicted_workload, trend}.
"""

from forecasting.baselines import baseline_predictions
from forecasting.dataset import ForecastData, make_forecast_data
from forecasting.evaluate import forecast_metrics, regression_metrics
from forecasting.inference import forecast
from forecasting.tft_model import TemporalFusionTransformer
from forecasting.tft_service import TFTForecastService
from forecasting.train import load_checkpoint, save_checkpoint, train_tft

__all__ = [
    "ForecastData",
    "make_forecast_data",
    "baseline_predictions",
    "forecast_metrics",
    "regression_metrics",
    "forecast",
    "TemporalFusionTransformer",
    "TFTForecastService",
    "train_tft",
    "save_checkpoint",
    "load_checkpoint",
]
