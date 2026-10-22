"""TFT training loop (docs/design.md section 6).

Trains the compact TFT on a leakage-safe windowed dataset, tracks validation
loss, keeps the best checkpoint and persists model weights together with the
feature list and train-fit scaler so inference can reverse the normalization.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Dict, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from configs import load_config
from forecasting.dataset import ForecastData, StandardScaler, make_forecast_data
from forecasting.evaluate import regression_metrics
from forecasting.tft_model import TemporalFusionTransformer


def set_seed(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)


def _to_loader(X: np.ndarray, y: np.ndarray, batch_size: int, shuffle: bool) -> DataLoader:
    tensor_x = torch.tensor(X, dtype=torch.float32)
    tensor_y = torch.tensor(y, dtype=torch.float32)
    return DataLoader(TensorDataset(tensor_x, tensor_y), batch_size=batch_size, shuffle=shuffle)


def train_tft(
    frame,
    config: Optional[Dict] = None,
    feature_columns=None,
    verbose: bool = False,
) -> Tuple[TemporalFusionTransformer, ForecastData, Dict]:
    """Train the TFT and return (model, data, history)."""
    config = config or load_config()
    forecast_cfg = config["forecast"]
    train_cfg = forecast_cfg["training"]
    model_cfg = forecast_cfg["model"]

    history = int(forecast_cfg["history_window"])
    horizon = int(forecast_cfg["horizon"])
    target_column = forecast_cfg.get("target_column", "invocation_count")
    feature_columns = list(feature_columns or forecast_cfg.get("covariates", []))
    if target_column not in feature_columns:
        feature_columns = [target_column] + feature_columns

    set_seed(int(train_cfg.get("seed", 42)))

    data = make_forecast_data(
        frame,
        feature_columns=feature_columns,
        target_column=target_column,
        history=history,
        horizon=horizon,
        split=train_cfg.get("split", [0.70, 0.15, 0.15]),
    )

    model = TemporalFusionTransformer.from_config(
        n_features=data.n_features, horizon=horizon, model_cfg=model_cfg
    )
    optimizer = torch.optim.Adam(
        model.parameters(), lr=float(train_cfg.get("learning_rate", 1e-3))
    )
    loss_fn = nn.MSELoss()

    train_loader = _to_loader(
        data.X_train, data.y_train, int(train_cfg.get("batch_size", 64)), shuffle=True
    )
    val_loader = _to_loader(data.X_val, data.y_val, int(train_cfg.get("batch_size", 64)), shuffle=False)

    epochs = int(train_cfg.get("epochs", 8))
    best_val = float("inf")
    best_state = {k: v.clone() for k, v in model.state_dict().items()}
    history_log = {"train_loss": [], "val_loss": []}

    for epoch in range(epochs):
        model.train()
        total, count = 0.0, 0
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            pred = model(batch_x)
            loss = loss_fn(pred, batch_y)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total += loss.item() * len(batch_x)
            count += len(batch_x)
        train_loss = total / max(count, 1)

        model.eval()
        val_total, val_count = 0.0, 0
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                pred = model(batch_x)
                val_total += loss_fn(pred, batch_y).item() * len(batch_x)
                val_count += len(batch_x)
        val_loss = val_total / max(val_count, 1)

        history_log["train_loss"].append(train_loss)
        history_log["val_loss"].append(val_loss)
        if val_loss < best_val:
            best_val = val_loss
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
        if verbose:
            print(f"epoch {epoch + 1}/{epochs}  train={train_loss:.4f}  val={val_loss:.4f}")

    model.load_state_dict(best_state)
    model.eval()

    # Final held-out test metrics (inverse-scaled to real workload units).
    test_metrics = {}
    if len(data.X_test) > 0:
        with torch.no_grad():
            pred_scaled = model(torch.tensor(data.X_test, dtype=torch.float32)).numpy()
        pred = data.scaler.inverse_column(pred_scaled, data.target_index)
        truth = data.scaler.inverse_column(data.y_test, data.target_index)
        test_metrics = regression_metrics(truth, pred)

    history_log["best_val_loss"] = best_val
    history_log["test_metrics"] = test_metrics
    return model, data, history_log


def save_checkpoint(model: TemporalFusionTransformer, data: ForecastData, path: str, model_cfg: Dict) -> str:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    payload = {
        "model_state": model.state_dict(),
        "n_features": data.n_features,
        "horizon": data.horizon,
        "history": data.history,
        "feature_columns": data.feature_columns,
        "target_index": data.target_index,
        "scaler_mean": data.scaler.mean_.tolist(),
        "scaler_std": data.scaler.std_.tolist(),
        "model_cfg": model_cfg,
    }
    torch.save(payload, path)
    return path


def load_checkpoint(path: str) -> Tuple[TemporalFusionTransformer, Dict]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    model = TemporalFusionTransformer.from_config(
        n_features=payload["n_features"], horizon=payload["horizon"], model_cfg=payload["model_cfg"]
    )
    model.load_state_dict(payload["model_state"])
    model.eval()
    return model, payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the compact TFT forecaster")
    parser.add_argument("--config", default=None, help="Path to project.yaml")
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    from data.pipeline import run

    config = load_config(args.config)
    if args.epochs is not None:
        config["forecast"]["training"]["epochs"] = args.epochs

    frame, _ = run(config=config)
    model, data, history = train_tft(frame, config=config, verbose=args.epochs is not None or args.verbose)

    checkpoint = config["forecast"].get("checkpoint_path", "models/tft_checkpoint.pt")
    save_checkpoint(model, data, checkpoint, config["forecast"]["model"])
    print(json.dumps({"checkpoint": checkpoint, "history": history}, indent=2, default=str))


if __name__ == "__main__":
    main()
