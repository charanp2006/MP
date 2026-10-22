"""Compact Temporal Fusion Transformer implemented in pure PyTorch.

This is a lightweight, dependency-free TFT for the research prototype. It keeps
the architectural ingredients that define a TFT (docs/architecture.md layer 3,
docs/design.md section 6):

* **Variable selection** --- a softmax over input features produces a weighted
  mix instead of feeding all features equally.
* **Gated residual networks (GRN)** --- non-linear block with a learned gate
  and a skip connection, used for stability.
* **LSTM encoder** --- recurrent backbone over the history window.
* **Multi-head attention** --- self-attention over the temporal axis to mix
  long-range context.
* **Forecast head** --- projects the temporal context to the horizon.

It is intentionally compact (default ``d_model=32``) so it trains quickly on a
laptop for a prototype; hyperparameters live in ``configs/project.yaml``.
"""

from __future__ import annotations

from typing import Dict, Optional

import torch
import torch.nn as nn


class GatedResidualNetwork(nn.Module):
    """GRN: ELU-linear transform gated and added to a skip connection."""

    def __init__(
        self, input_size: int, d_model: int, dropout: float = 0.1, output_size: Optional[int] = None
    ) -> None:
        super().__init__()
        output_size = output_size or d_model
        self.fc1 = nn.Linear(input_size, d_model)
        self.elu = nn.ELU()
        self.fc2 = nn.Linear(d_model, output_size)
        self.dropout = nn.Dropout(dropout)
        self.gate = nn.Linear(input_size, output_size)
        self.skip = nn.Linear(input_size, output_size) if input_size != output_size else None
        self.layer_norm = nn.LayerNorm(output_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        skip = self.skip(x) if self.skip is not None else x
        hidden = self.fc2(self.dropout(self.elu(self.fc1(x))))
        gate = torch.sigmoid(self.gate(x))
        return self.layer_norm(skip + gate * hidden)


class VariableSelectionNetwork(nn.Module):
    """Per-timestep softmax weighting over the input feature channels."""

    def __init__(self, n_features: int, d_model: int, dropout: float = 0.1) -> None:
        super().__init__()
        self.n_features = n_features
        self.feature_embeds = nn.ModuleList(
            [nn.Linear(1, d_model) for _ in range(n_features)]
        )
        self.weights_mlp = nn.Sequential(
            nn.Linear(n_features, d_model), nn.ELU(), nn.Linear(d_model, n_features)
        )
        self.grn = GatedResidualNetwork(d_model, d_model, dropout)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        # x: (batch, history, n_features)
        embeds = torch.stack(
            [self.feature_embeds[i](x[..., i : i + 1]) for i in range(self.n_features)],
            dim=2,
        )  # (batch, history, n_features, d_model)
        weights = torch.softmax(self.weights_mlp(x), dim=-1)  # (batch, history, F)
        selected = (embeds * weights.unsqueeze(-1)).sum(dim=2)  # (batch, history, d_model)
        return self.grn(selected), weights


class TemporalFusionTransformer(nn.Module):
    """Compact TFT: variable selection -> LSTM -> attention -> forecast head."""

    def __init__(
        self,
        n_features: int,
        horizon: int,
        d_model: int = 32,
        attention_heads: int = 2,
        dropout: float = 0.1,
        use_variable_selection: bool = True,
    ) -> None:
        super().__init__()
        self.n_features = n_features
        self.horizon = horizon
        self.use_variable_selection = use_variable_selection

        if use_variable_selection:
            self.vsn = VariableSelectionNetwork(n_features, d_model, dropout)
        else:
            self.input_proj = nn.Linear(n_features, d_model)

        self.lstm = nn.LSTM(
            input_size=d_model, hidden_size=d_model, batch_first=True
        )
        self.attention = nn.MultiheadAttention(
            embed_dim=d_model, num_heads=attention_heads, dropout=dropout, batch_first=True
        )
        self.post_attention = GatedResidualNetwork(d_model, d_model, dropout)
        self.head = GatedResidualNetwork(d_model, d_model, dropout, output_size=horizon)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, history, n_features) -> returns (batch, horizon)
        if self.use_variable_selection:
            context, _ = self.vsn(x)
        else:
            context = self.input_proj(x)

        lstm_out, _ = self.lstm(context)  # (batch, history, d_model)
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        attn_out = self.dropout(attn_out)
        mixed = self.post_attention(lstm_out + attn_out)

        # Combine the most recent state with the temporal mean for the forecast.
        pooled = mixed[:, -1] + mixed.mean(dim=1)  # (batch, d_model)
        return self.head(pooled)  # (batch, horizon)

    @staticmethod
    def from_config(n_features: int, horizon: int, model_cfg: Dict) -> "TemporalFusionTransformer":
        return TemporalFusionTransformer(
            n_features=n_features,
            horizon=horizon,
            d_model=int(model_cfg.get("d_model", 32)),
            attention_heads=int(model_cfg.get("attention_heads", 2)),
            dropout=float(model_cfg.get("dropout", 0.1)),
            use_variable_selection=bool(model_cfg.get("variable_selection", True)),
        )
