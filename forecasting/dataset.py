"""Window generation and chronological splitting for TFT forecasting.

Implements the leakage-safe data contract required by docs/design.md section 5
(chronological splits) and the T01/T03 tests:

* T01 --- every input window has exactly ``history_window`` steps.
* T03 --- train timestamps < validation timestamps < test timestamps, and no
  window spans a split boundary or sees the future it is predicting.

The split is done on the time axis *before* windowing, and windows are built
only inside a split segment, so a training window can never contain a
validation or test target.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd


class StandardScaler:
    """Per-column standard scaler (fit on the train split only)."""

    def __init__(self) -> None:
        self.mean_: np.ndarray | None = None
        self.std_: np.ndarray | None = None

    def fit(self, values: np.ndarray) -> "StandardScaler":
        values = np.asarray(values, dtype=np.float64)
        self.mean_ = values.mean(axis=0)
        # Guard against zero-variance columns (std == 0) -> leave as identity.
        std = values.std(axis=0)
        std[std == 0] = 1.0
        self.std_ = std
        return self

    def transform(self, values: np.ndarray) -> np.ndarray:
        values = np.asarray(values, dtype=np.float64)
        return (values - self.mean_) / self.std_

    def inverse_transform(self, values: np.ndarray) -> np.ndarray:
        values = np.asarray(values, dtype=np.float64)
        return values * self.std_ + self.mean_

    def inverse_column(self, values: np.ndarray, index: int) -> np.ndarray:
        """Inverse-transform a single column (used to unscale the target)."""
        values = np.asarray(values, dtype=np.float64)
        return values * self.std_[index] + self.mean_[index]


def chronological_boundaries(n: int, fractions: Sequence[float]) -> Tuple[int, int]:
    """Return (train_end, val_end) index boundaries for a chronological split."""
    if len(fractions) != 3:
        raise ValueError(f"expected 3 fractions [train, val, test], got {fractions}")
    if abs(sum(fractions) - 1.0) > 1e-6:
        raise ValueError(f"fractions must sum to 1.0, got {fractions}")
    train_end = int(n * fractions[0])
    val_end = train_end + int(n * fractions[1])
    # Ensure every split is non-empty for small series.
    train_end = max(train_end, 1)
    val_end = max(val_end, train_end + 1)
    if val_end >= n:
        raise ValueError(f"series too short ({n}) for split {fractions}")
    return train_end, val_end


def build_windows(
    features: np.ndarray,
    target: np.ndarray,
    history: int,
    horizon: int,
    start: int,
    end: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """Build sliding windows fully contained in ``[start, end)``.

    A sample predicts ``target[t : t + horizon]`` from
    ``features[t - history : t]``. Input times ``[t-history, t-1]`` and target
    times ``[t, t+horizon-1]`` never overlap, and both stay inside the split,
    so the model never sees the future it predicts (T03).
    """
    features = np.asarray(features, dtype=np.float64)
    target = np.asarray(target, dtype=np.float64)

    x_list: List[np.ndarray] = []
    y_list: List[np.ndarray] = []
    for t in range(start + history, end - horizon + 1):
        x_list.append(features[t - history : t])
        y_list.append(target[t : t + horizon])

    if not x_list:
        empty_x = np.empty((0, history, features.shape[1]), dtype=np.float64)
        empty_y = np.empty((0, horizon), dtype=np.float64)
        return empty_x, empty_y
    return np.stack(x_list), np.stack(y_list)


@dataclass
class ForecastData:
    """Windowed, scaled, chronologically split dataset ready for the model."""

    X_train: np.ndarray
    y_train: np.ndarray
    X_val: np.ndarray
    y_val: np.ndarray
    X_test: np.ndarray
    y_test: np.ndarray
    scaler: StandardScaler
    target_index: int
    feature_columns: List[str]
    history: int
    horizon: int
    # Per-split (function_id, min_timestamp, max_timestamp) provenance for T03.
    split_time_ranges: Dict[str, Tuple[pd.Timestamp, pd.Timestamp]] = field(
        default_factory=dict
    )

    @property
    def n_features(self) -> int:
        return self.X_train.shape[-1]


def make_forecast_data(
    frame: pd.DataFrame,
    feature_columns: Sequence[str],
    target_column: str,
    history: int,
    horizon: int,
    split: Sequence[float] = (0.70, 0.15, 0.15),
) -> ForecastData:
    """Build a leakage-safe forecast dataset from a preprocessed frame.

    ``frame`` must be the output of the data pipeline (already resampled,
    cleaned and feature-engineered). Windows are built per function so each
    function's timeline stays intact, then concatenated across functions.
    """
    feature_columns = list(feature_columns)
    if target_column not in feature_columns:
        raise ValueError(f"target_column {target_column!r} not in feature_columns")
    target_index = feature_columns.index(target_column)

    x_parts: Dict[str, List[np.ndarray]] = {"train": [], "val": [], "test": []}
    y_parts: Dict[str, List[np.ndarray]] = {"train": [], "val": [], "test": []}
    time_ranges: Dict[str, List[Tuple[pd.Timestamp, pd.Timestamp]]] = {
        "train": [],
        "val": [],
        "test": [],
    }

    # Fit the scaler on train rows only, then transform everything.
    scaler = StandardScaler()

    for function_id, group in frame.groupby("function_id", sort=True):
        group = group.sort_values("timestamp", kind="stable").reset_index(drop=True)
        n = len(group)
        if n <= history + horizon:
            continue
        train_end, val_end = chronological_boundaries(n, split)
        boundaries = {
            "train": (0, train_end),
            "val": (train_end, val_end),
            "test": (val_end, n),
        }

        full = group[feature_columns].to_numpy(dtype=np.float64)
        if scaler.mean_ is None:
            scaler.fit(full[boundaries["train"][0] : boundaries["train"][1]])
        scaled = scaler.transform(full)
        target_series = scaled[:, target_index]

        for name, (seg_start, seg_end) in boundaries.items():
            x, y = build_windows(
                scaled, target_series, history, horizon, seg_start, seg_end
            )
            if len(x) == 0:
                continue
            x_parts[name].append(x)
            y_parts[name].append(y)
            seg_times = group["timestamp"].iloc[seg_start:seg_end]
            time_ranges[name].append(
                (function_id, seg_times.min(), seg_times.max())
            )

    def _concat(parts: List[np.ndarray], shape_tail: Tuple[int, ...]) -> np.ndarray:
        non_empty = [p for p in parts if len(p) > 0]
        if not non_empty:
            return np.empty((0, *shape_tail), dtype=np.float64)
        return np.concatenate(non_empty, axis=0)

    data = ForecastData(
        X_train=_concat(x_parts["train"], (history, len(feature_columns))),
        y_train=_concat(y_parts["train"], (horizon,)),
        X_val=_concat(x_parts["val"], (history, len(feature_columns))),
        y_val=_concat(y_parts["val"], (horizon,)),
        X_test=_concat(x_parts["test"], (history, len(feature_columns))),
        y_test=_concat(y_parts["test"], (horizon,)),
        scaler=scaler,
        target_index=target_index,
        feature_columns=feature_columns,
        history=history,
        horizon=horizon,
    )
    # Collapse per-function ranges to global min/max per split for T03 checks.
    for name, entries in time_ranges.items():
        if entries:
            mins = [e[1] for e in entries]
            maxs = [e[2] for e in entries]
            data.split_time_ranges[name] = (min(mins), max(maxs))
    return data
