"""Evaluate a trained PPO policy on the simulated environment.

Reports mean reward, SLA-violation rate, mean energy, mean capacity and cold
starts over full episodes. Used both to sanity-check training and as the
"proposed" arm of the baseline-vs-proposed comparison (docs/test_plan.md S01+).
"""

from __future__ import annotations

from typing import Dict

import numpy as np
import torch

from rl.environment import ServerlessEnv
from rl.policy import ActorCritic


def evaluate_policy(
    model: ActorCritic, env: ServerlessEnv, episodes: int = 5, greedy: bool = True
) -> Dict[str, float]:
    """Run ``episodes`` full episodes and aggregate operational metrics."""
    rewards, violations, energies, capacities, cold_starts, latencies = [], [], [], [], [], []

    for _ in range(episodes):
        obs = env.reset()
        done = False
        while not done:
            action = model.greedy_action(obs) if greedy else model.act(obs)[0]
            obs, reward, done, info = env.step(action)
            rewards.append(reward)
            energies.append(info["energy"])
            capacities.append(info["capacity"])
            cold_starts.append(info["cold_starts"])
            latencies.append(info["p95_latency"])
            violations.append(1.0 if info["sla_violated"] else 0.0)

    return {
        "mean_reward": float(np.mean(rewards)),
        "sla_violation_rate": float(np.mean(violations)),
        "mean_energy_w": float(np.mean(energies)),
        "mean_capacity": float(np.mean(capacities)),
        "mean_cold_starts": float(np.mean(cold_starts)),
        "mean_p95_latency_ms": float(np.mean(latencies)),
        "steps": int(len(rewards)),
    }


def evaluate_reactive(frame, config: Dict) -> Dict[str, float]:
    """Evaluate the reactive baseline on the same environment for comparison."""
    from baseline.reactive import ReactiveAutoscaler
    from rl.environment import ServerlessEnv

    env = ServerlessEnv(frame, config)
    scaler = ReactiveAutoscaler(config)

    rewards, violations, energies, capacities, cold_starts, latencies = [], [], [], [], [], []
    obs = env.reset()
    done = False
    while not done:
        action = scaler.select_action(env, obs)
        obs, reward, done, info = env.step(action)
        rewards.append(reward)
        energies.append(info["energy"])
        capacities.append(info["capacity"])
        cold_starts.append(info["cold_starts"])
        latencies.append(info["p95_latency"])
        violations.append(1.0 if info["sla_violated"] else 0.0)

    return {
        "mean_reward": float(np.mean(rewards)),
        "sla_violation_rate": float(np.mean(violations)),
        "mean_energy_w": float(np.mean(energies)),
        "mean_capacity": float(np.mean(capacities)),
        "mean_cold_starts": float(np.mean(cold_starts)),
        "mean_p95_latency_ms": float(np.mean(latencies)),
        "steps": int(len(rewards)),
    }
