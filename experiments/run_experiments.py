"""Experiments runner for baseline vs proposed (P5, docs/test_plan.md sections 8-14).

Runs the reactive baseline and the proposed loop (forecast + planner + PPO)
over the same timeline and reports aggregate metrics.
"""

from __future__ import annotations

import json
from typing import Dict, Optional

import numpy as np

from baseline.reactive import ReactiveAutoscaler
from data.pipeline import run
from rl.environment import ACTIONS, ServerlessEnv
from rl.evaluate_ppo import evaluate_policy, evaluate_reactive


def _split_timeline(frame, split=(0.70, 0.15, 0.15)):
    # Chronological split by timestamps (no shuffle)
    if "timestamp" in frame.columns:
        times = sorted(frame["timestamp"].unique())
    else:
        times = sorted(frame.index)
    n = len(times)
    i1 = int(n * split[0])
    i2 = int(n * (split[0] + split[1]))
    return times[:i1], times[i1:i2], times[i2:]


def run_baseline_vs_proposed(config: Optional[Dict] = None, episodes: int = 1, policy=None) -> Dict:
    from configs import load_config

    config = config or load_config()
    frame, _ = run(config=config)

    train_t, val_t, test_t = _split_timeline(frame)
    if "timestamp" in frame.columns:
        test_frame = frame[frame["timestamp"].isin(test_t)].copy()
        train_frame = frame[frame["timestamp"].isin(train_t)].copy()
    else:
        test_frame = frame.iloc[train_t if False else slice(int(len(frame)*0.85), None)].copy()
        train_frame = frame.iloc[: int(len(frame)*0.70)].copy()

    baseline = evaluate_reactive(test_frame, config)
    if policy is None:
        from rl.train_ppo import train_ppo

        model, env, history = train_ppo(train_frame, config=config)
        proposed_env = ServerlessEnv(test_frame, config)
        proposed = evaluate_policy(model, proposed_env, episodes=episodes)
    else:
        env = ServerlessEnv(test_frame, config)
        proposed = evaluate_policy(policy, env, episodes=episodes)
        history = {}

    return {
        "baseline": baseline,
        "proposed": proposed,
        "training": {"ppo_best_mean_reward": history.get("best_mean_reward") if history else None},
        "split": {"test_frames": len(test_frame), "train_frames": len(train_frame)},
    }


def ablation_remove_planner(frame, config=None, policy=None):
    # Use PPO without planner influence (policy only) — compare to full loop in tests
    from configs import load_config

    config = config or load_config()
    train_t, val_t, test_t = _split_timeline(frame)
    if "timestamp" in frame.columns:
        train_frame = frame[frame["timestamp"].isin(train_t)].copy()
        test_frame = frame[frame["timestamp"].isin(test_t)].copy()
    else:
        train_frame = frame.iloc[: int(len(frame) * 0.70)].copy()
        test_frame = frame.iloc[int(len(frame) * 0.85) :].copy()

    if policy is None:
        from rl.train_ppo import train_ppo

        model, env, _ = train_ppo(train_frame, config=config)
        env = ServerlessEnv(test_frame, config)
    else:
        model = policy
        env = ServerlessEnv(test_frame, config)
    return evaluate_policy(model, env, episodes=1)


def main() -> None:
    result = run_baseline_vs_proposed()
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
