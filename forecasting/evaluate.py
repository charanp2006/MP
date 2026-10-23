"""Forecast accuracy metrics (docs/test_plan.md T04).

MAE, RMSE and MAPE are computed on the *unscaled* target so they are directly
interpretable. MAPE is guarded against near-zero actuals (test_plan T04 warns
about this) by ignoring denominators below a small epsilon.
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
