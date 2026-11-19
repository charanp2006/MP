"""Reproducible TFT/baseline evaluation and artifact generation for M3."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

from forecasting.baselines import baseline_predictions
from forecasting.evaluate import (
    apply_residual_interval,
    calibrate_residual_interval,
    forecast_metrics,
    interval_metrics,
)
from forecasting.inference import predict_scaled_windows
from forecasting.train import save_checkpoint, train_tft
from forecasting.visualize import generate_forecast_plots


def sha256_file(path: str | Path) -> Optional[str]:
    source = Path(path)
    if not source.is_file():
        return None
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_dataset_path(config: Dict) -> Optional[str]:
    data_cfg = config.get("data", {})
    if str(data_cfg.get("source", "sample")).lower() in {
        "azure_functions_2019",
        "azure2019",
        "azure",
    }:
        return data_cfg.get("azure", {}).get("processed_path")
    if str(data_cfg.get("source", "sample")).lower() == "file":
        return data_cfg.get("source_path")
    return None


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _subset_metrics(truth: np.ndarray, prediction: np.ndarray, quantile: float) -> Dict:
    flat_truth = truth.reshape(-1)
    flat_pred = prediction.reshape(-1)
    threshold = float(np.quantile(flat_truth, quantile))
    mask = flat_truth >= threshold
    return forecast_metrics(flat_truth[mask], flat_pred[mask], quantile)


def run_forecast_evaluation(
    frame: pd.DataFrame,
    config: Dict,
    run_id: str,
    out_dir: str | Path,
    dataset_sha256: Optional[str] = None,
    model=None,
    data=None,
    history: Optional[Dict] = None,
) -> Dict:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    forecast_cfg = config["forecast"]
    eval_cfg = forecast_cfg.get("evaluation", {})
    training_cfg = forecast_cfg["training"]
    horizon = int(forecast_cfg["horizon"])
    interval_seconds = int(config.get("control", {}).get("interval_seconds", 60))
    peak_quantile = float(eval_cfg.get("peak_quantile", 0.9))
    alpha = float(eval_cfg.get("interval_alpha", 0.2))

    if model is None or data is None or history is None:
        model, data, history = train_tft(frame, config=config, verbose=True)
    truth = (
        data.y_test_raw
        if data.y_test_raw is not None
        else data.scaler.inverse_column(data.y_test, data.target_index)
    )
    truth = np.asarray(truth, dtype=np.float64)
    tft_pred = predict_scaled_windows(
        model,
        data.X_test,
        data.scaler.mean_,
        data.scaler.std_,
        data.target_index,
    )
    predictions: Dict[str, np.ndarray] = {"tft": tft_pred}
    predictions.update(
        baseline_predictions(
            data,
            frame,
            seasonal_period=int(eval_cfg.get("seasonal_period", 1440)),
            interval_seconds=interval_seconds,
            moving_average_window=int(eval_cfg.get("moving_average_window", 5)),
        )
    )

    model_results: Dict[str, Dict] = {}
    for name, prediction in predictions.items():
        model_results[name] = {
            "overall": forecast_metrics(truth, prediction, peak_quantile),
            "peak": _subset_metrics(truth, prediction, peak_quantile),
            "by_horizon": {
                str(step + 1): forecast_metrics(truth[:, step], prediction[:, step], peak_quantile)
                for step in range(horizon)
            },
        }

    interval: Dict[str, float | None] = {"alpha": alpha}
    if len(data.X_val) > 0:
        val_truth = data.scaler.inverse_column(data.y_val, data.target_index)
        val_pred = predict_scaled_windows(
            model,
            data.X_val,
            data.scaler.mean_,
            data.scaler.std_,
            data.target_index,
        )
        fitted = calibrate_residual_interval(val_truth, val_pred, alpha)
        interval.update(fitted)
        lower, upper = apply_residual_interval(tft_pred.reshape(-1), fitted)
        interval.update(interval_metrics(truth.reshape(-1), lower, upper))
    else:
        lower = np.full(truth.size, float("nan"))
        upper = np.full(truth.size, float("nan"))
        interval.update({"lower": None, "upper": None, "coverage": None})

    index = data.sample_index.get("test") or []
    if len(index) != len(truth):
        index = [
            ("unknown", pd.Timestamp("1970-01-01"), pd.Timestamp("1970-01-01"))
            for _ in range(len(truth))
        ]
    rows = []
    for sample_idx, (function_id, _, target_start) in enumerate(index):
        for step in range(horizon):
            flat_idx = sample_idx * horizon + step
            row = {
                "function_id": function_id,
                "origin": str(index[sample_idx][1]),
                "target_start": str(pd.Timestamp(target_start) + pd.Timedelta(seconds=step * interval_seconds)),
                "horizon_step": step + 1,
                "actual": float(truth[sample_idx, step]),
            }
            for name, prediction in predictions.items():
                row[name] = float(prediction[sample_idx, step])
            row["interval_lower"] = float(lower[flat_idx])
            row["interval_upper"] = float(upper[flat_idx])
            rows.append(row)
    samples = pd.DataFrame(rows)

    predictions_csv = output / "predictions.csv"
    samples.to_csv(predictions_csv, index=False)

    checkpoint_path = output / "checkpoint.pt"
    save_checkpoint(model, data, str(checkpoint_path), forecast_cfg["model"])

    dataset_path = resolve_dataset_path(config)
    if dataset_sha256 is None and dataset_path:
        dataset_sha256 = sha256_file(dataset_path)
    config_hash = hashlib.sha256(
        json.dumps(config, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()

    result = {
        "run_id": run_id,
        "commit": _git_commit(),
        "model": {
            "name": "compact_tft_pytorch",
            "library": "pytorch",
            "pytorch_forecasting": False,
            "model_config": forecast_cfg["model"],
            "checkpoint": str(checkpoint_path),
        },
        "data": {
            "source": config.get("data", {}).get("source"),
            "path": dataset_path,
            "sha256": dataset_sha256,
            "classification": "historical Azure invocation counts; no measured latency or energy",
            "feature_columns": data.feature_columns,
            "target_column": forecast_cfg.get("target_column", "invocation_count"),
            "history": data.history,
            "horizon": data.horizon,
            "split_ranges": {
                key: [str(value[0]), str(value[1])]
                for key, value in data.split_time_ranges.items()
            },
            "rows": {
                "train": int(len(data.X_train)),
                "val": int(len(data.X_val)),
                "test": int(len(data.X_test)),
            },
        },
        "training": {
            "config": training_cfg,
            "seed": int(training_cfg.get("seed", 42)),
            "train_loss": [float(v) for v in history["train_loss"]],
            "val_loss": [float(v) for v in history["val_loss"]],
            "best_val_loss": float(history["best_val_loss"]),
        },
        "models": model_results,
        "interval": interval,
        "reproducibility": {
            "config_sha256": config_hash,
            "interval_seconds": interval_seconds,
            "peak_quantile": peak_quantile,
        },
        "artifacts": {
            "predictions_csv": str(predictions_csv),
            "metrics_json": str(output / "metrics.json"),
            "run_manifest_json": str(output / "run_manifest.json"),
        },
    }

    result["artifacts"]["plots"] = generate_forecast_plots(
        output,
        samples,
        result,
        history["train_loss"],
        history["val_loss"],
    )
    for name, payload in (
        ("metrics.json", result),
        ("feature_columns.json", {"feature_columns": data.feature_columns}),
        (
            "scaler.json",
            {
                "mean": data.scaler.mean_.tolist(),
                "std": data.scaler.std_.tolist(),
                "target_index": data.target_index,
            },
        ),
    ):
        (output / name).write_text(
            json.dumps(payload, indent=2, default=str), encoding="utf-8"
        )
    return result
