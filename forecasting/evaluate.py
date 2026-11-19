"""Forecast accuracy metrics (docs/test_plan.md T04 and M3 acceptance).

All metrics are computed on the unscaled target. MAPE masks near-zero actuals,
WAPE handles zeros through the denominator, and sMAPE masks zero denominators.
"""

from __future__ import annotations

from typing import Dict

import numpy as np


def _as_1d(a: np.ndarray) -> np.ndarray:
    return np.asarray(a, dtype=np.float64).reshape(-1)


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true, y_pred = _as_1d(y_true), _as_1d(y_pred)
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true, y_pred = _as_1d(y_true), _as_1d(y_pred)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mape(y_true: np.ndarray, y_pred: np.ndarray, eps: float = 1e-6) -> float:
    """Mean absolute percentage error, skipping near-zero denominators."""
    y_true, y_pred = _as_1d(y_true), _as_1d(y_pred)
    mask = np.abs(y_true) > eps
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    return {
        "mae": mae(y_true, y_pred),
        "rmse": rmse(y_true, y_pred),
        "mape": mape(y_true, y_pred),
    }


def wape(y_true: np.ndarray, y_pred: np.ndarray, eps: float = 1e-9) -> float:
    y_true, y_pred = _as_1d(y_true), _as_1d(y_pred)
    denominator = float(np.sum(np.abs(y_true)))
    if denominator <= eps:
        return float("nan")
    return float(100.0 * np.sum(np.abs(y_true - y_pred)) / denominator)


def smape(y_true: np.ndarray, y_pred: np.ndarray, eps: float = 1e-9) -> float:
    y_true, y_pred = _as_1d(y_true), _as_1d(y_pred)
    denominator = np.abs(y_true) + np.abs(y_pred)
    mask = denominator > eps
    if not mask.any():
        return float("nan")
    return float(
        100.0
        * np.mean(2.0 * np.abs(y_true[mask] - y_pred[mask]) / denominator[mask])
    )


def bias(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true, y_pred = _as_1d(y_true), _as_1d(y_pred)
    return float(np.mean(y_pred - y_true))


def peak_underprediction_rate(
    y_true: np.ndarray, y_pred: np.ndarray, peak_quantile: float = 0.9
) -> float:
    y_true, y_pred = _as_1d(y_true), _as_1d(y_pred)
    if len(y_true) == 0:
        return float("nan")
    threshold = float(np.quantile(y_true, float(peak_quantile)))
    mask = y_true >= threshold
    if not mask.any():
        return float("nan")
    return float(np.mean(y_pred[mask] < y_true[mask]))


def forecast_metrics(
    y_true: np.ndarray, y_pred: np.ndarray, peak_quantile: float = 0.9
) -> Dict[str, float]:
    y_true, y_pred = _as_1d(y_true), _as_1d(y_pred)
    if len(y_true) == 0:
        raise ValueError("cannot compute metrics on empty arrays")
    metrics = regression_metrics(y_true, y_pred)
    metrics.update(
        {
            "wape": wape(y_true, y_pred),
            "smape": smape(y_true, y_pred),
            "bias": bias(y_true, y_pred),
            "peak_underprediction_rate": peak_underprediction_rate(
                y_true, y_pred, peak_quantile
            ),
            "n": float(len(y_true)),
        }
    )
    return metrics


def calibrate_residual_interval(
    calibration_true: np.ndarray, calibration_pred: np.ndarray, alpha: float = 0.2
) -> Dict[str, float]:
    true, pred = _as_1d(calibration_true), _as_1d(calibration_pred)
    if len(true) == 0:
        raise ValueError("calibration arrays cannot be empty")
    if not 0.0 < float(alpha) < 1.0:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")
    residuals = true - pred
    return {
        "alpha": float(alpha),
        "lower": float(np.quantile(residuals, alpha / 2.0)),
        "upper": float(np.quantile(residuals, 1.0 - alpha / 2.0)),
    }


def apply_residual_interval(
    y_pred: np.ndarray, interval: Dict[str, float]
) -> tuple[np.ndarray, np.ndarray]:
    pred = _as_1d(y_pred)
    lower = np.maximum(pred + float(interval["lower"]), 0.0)
    upper = np.maximum(pred + float(interval["upper"]), 0.0)
    return lower, upper


def interval_metrics(
    y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray
) -> Dict[str, float]:
    true, low, high = _as_1d(y_true), _as_1d(lower), _as_1d(upper)
    if len(true) == 0:
        raise ValueError("cannot compute interval metrics on empty arrays")
    under = true < low
    over = true > high
    width = high - low
    return {
        "coverage": float(np.mean((true >= low) & (true <= high))),
        "mean_interval_width": float(np.mean(width)),
        "under_coverage_rate": float(np.mean(under)),
        "over_coverage_rate": float(np.mean(over)),
    }
