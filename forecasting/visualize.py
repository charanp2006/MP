"""Forecast evaluation plots generated from saved prediction artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def generate_forecast_plots(
    out_dir: str | Path,
    samples: pd.DataFrame,
    metrics: Dict,
    train_loss: list[float],
    val_loss: list[float],
    max_points: int = 800,
) -> list[str]:
    plot_dir = Path(out_dir) / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []

    def save(name: str) -> None:
        path = plot_dir / name
        plt.tight_layout()
        plt.savefig(path, dpi=120)
        plt.close("all")
        paths.append(str(path))

    view = samples.head(int(max_points))
    x = np.arange(len(view))

    plt.figure(figsize=(14, 5))
    plt.plot(x, view["actual"], label="actual", alpha=0.8, linewidth=1)
    plt.plot(x, view["tft"], label="TFT", alpha=0.8, linewidth=1)
    plt.xlabel("test sample (flattened horizon)")
    plt.ylabel("invocation_count")
    plt.title("Actual vs predicted - full test range (first 800 points)")
    plt.legend()
    save("actual_vs_predicted.png")

    peak_pos = int(np.argmax(samples["actual"].to_numpy()))
    span = min(len(samples), 200)
    start = max(0, peak_pos - span // 2)
    end = min(len(samples), start + span)
    peak_view = samples.iloc[start:end]
    plt.figure(figsize=(14, 5))
    plt.plot(peak_view["actual"], label="actual", linewidth=1.6)
    plt.plot(peak_view["tft"], label="TFT", linewidth=1.4)
    for column in ("persistence", "seasonal_persistence", "moving_average"):
        if column in peak_view:
            plt.plot(peak_view[column], label=column, alpha=0.7, linewidth=1)
    plt.xlabel("test sample")
    plt.ylabel("invocation_count")
    plt.title("Peak burst zoom")
    plt.legend()
    save("peak_zoom.png")

    error = samples["tft"].to_numpy() - samples["actual"].to_numpy()
    plt.figure(figsize=(14, 4))
    plt.plot(x[: len(error)], error[: len(view)], alpha=0.7, linewidth=1)
    plt.axhline(0.0, color="black", linewidth=0.8)
    plt.xlabel("test sample")
    plt.ylabel("prediction - actual")
    plt.title("Forecast error over time")
    save("error_over_time.png")

    plt.figure(figsize=(9, 5))
    plt.hist(error, bins=60, color="steelblue", alpha=0.85)
    plt.axvline(0.0, color="black", linewidth=1)
    plt.xlabel("prediction - actual")
    plt.ylabel("count")
    plt.title("Residual distribution")
    save("residual_distribution.png")

    model_names = list(metrics.get("models", {}))
    comparison = pd.DataFrame(
        {
            name: {
                stat: metrics["models"][name]["overall"][stat]
                for stat in ("mae", "rmse", "wape")
            }
            for name in model_names
        }
    ).T
    comparison[["mae", "rmse"]].plot(kind="bar", figsize=(10, 5))
    plt.ylabel("invocation_count")
    plt.title("MAE / RMSE comparison (identical test rows)")
    save("metrics_comparison_absolute.png")

    comparison[["wape"]].plot(kind="bar", figsize=(8, 5), color="darkorange")
    plt.ylabel("WAPE (%)")
    plt.title("WAPE comparison (identical test rows)")
    save("metrics_comparison_wape.png")

    rates = {
        name: metrics["models"][name]["overall"]["peak_underprediction_rate"]
        for name in model_names
    }
    plt.figure(figsize=(9, 5))
    plt.bar(list(rates), [float(v) for v in rates.values()])
    plt.ylabel("rate")
    plt.title("Peak underprediction rate")
    save("peak_underprediction.png")

    horizon_means = samples.groupby("horizon_step")[["actual", "tft"]].mean()
    horizon_means.plot(kind="bar", figsize=(10, 5))
    plt.xlabel("horizon step")
    plt.ylabel("mean invocation_count")
    plt.title("Mean forecast by horizon")
    save("horizons_side_by_side.png")

    if train_loss:
        plt.figure(figsize=(9, 5))
        plt.plot(np.arange(1, len(train_loss) + 1), train_loss, label="train")
        if val_loss:
            plt.plot(np.arange(1, len(val_loss) + 1), val_loss, label="validation")
        plt.xlabel("epoch")
        plt.ylabel("MSE (scaled target)")
        plt.title("Training / validation loss")
        plt.legend()
        save("learning_curve.png")

    interval = metrics.get("interval", {})
    if interval.get("lower") is not None and interval.get("upper") is not None:
        cov_view = samples.head(int(max_points))
        plt.figure(figsize=(14, 5))
        plt.plot(cov_view["actual"].to_numpy(), label="actual", linewidth=1)
        plt.plot(cov_view["tft"].to_numpy(), label="TFT", linewidth=1)
        plt.fill_between(
            np.arange(len(cov_view)),
            cov_view["interval_lower"].to_numpy(),
            cov_view["interval_upper"].to_numpy(),
            alpha=0.25,
            label="calibrated interval",
        )
        plt.xlabel("test sample")
        plt.ylabel("invocation_count")
        plt.title(
            f"Prediction interval coverage={interval['coverage']:.3f} alpha={interval.get('alpha')}"
        )
        plt.legend()
        save("prediction_interval_coverage.png")

    return paths
