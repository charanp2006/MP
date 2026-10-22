"""PPO actor-critic policy (pure PyTorch, no stable-baselines3).

A shared MLP trunk with a categorical actor head (6 discrete container actions)
and a scalar critic head. Provides ``act`` for rollout and ``evaluate`` for the
PPO clipped update (docs/tech-stack.md: custom PyTorch PPO).
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.distributions import Categorical


def _mlp(sizes, activation=nn.Tanh, output_activation=None) -> nn.Sequential:
    layers = []
    for i in range(len(sizes) - 1):
        layers.append(nn.Linear(sizes[i], sizes[i + 1]))
        if i < len(sizes) - 2:
            layers.append(activation())
        elif output_activation is not None:
            layers.append(output_activation())
    return nn.Sequential(*layers)


class ActorCritic(nn.Module):
    def __init__(self, obs_dim: int, n_actions: int, hidden: int = 64) -> None:
        super().__init__()
        self.trunk = _mlp([obs_dim, hidden, hidden])
        self.actor = nn.Linear(hidden, n_actions)
        self.critic = nn.Linear(hidden, 1)

    def forward(self, obs: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        features = self.trunk(obs)
        return self.actor(features), self.critic(features).squeeze(-1)

    def distribution(self, obs: torch.Tensor) -> Categorical:
        logits, _ = self.forward(obs)
        return Categorical(logits=logits)

    @torch.no_grad()
    def act(self, obs: np.ndarray) -> Tuple[int, float, float]:
        """Sample an action; return (action, log_prob, value)."""
        tensor = torch.tensor(obs, dtype=torch.float32)
        dist = self.distribution(tensor)
        action = dist.sample()
        _, value = self.forward(tensor)
        return int(action.item()), float(dist.log_prob(action).item()), float(value.item())

    def evaluate(self, obs: torch.Tensor, actions: torch.Tensor):
        """Return (log_probs, entropy, values) for the PPO update."""
        dist = self.distribution(obs)
        _, values = self.forward(obs)
        return dist.log_prob(actions), dist.entropy(), values

    @torch.no_grad()
    def greedy_action(self, obs: np.ndarray) -> int:
        tensor = torch.tensor(obs, dtype=torch.float32)
        logits, _ = self.forward(tensor)
        return int(torch.argmax(logits).item())
