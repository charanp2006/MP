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


def run_baseline_vs_proposed(config: Optional[Dict] = None, episodes: int = 1, policy=None) -> Dict:
    from configs import load_config

    config = config or load_config()
    frame, _ = run(config=config)

    baseline = evaluate_reactive(frame, config)
    if policy is None:
        from rl.train_ppo import train_ppo

        model, env, history = train_ppo(frame, config=config)
        proposed_env = env
        proposed = evaluate_policy(model, proposed_env, episodes=episodes)
    else:
        env = ServerlessEnv(frame, config)
        proposed = evaluate_policy(policy, env, episodes=episodes)
        history = {}

    return {
        "baseline": baseline,
        "proposed": proposed,
        "training": {"ppo_best_mean_reward": history.get("best_mean_reward") if history else None},
    }


def ablation_remove_planner(frame, config, policy=None) -> Dict:
    # Use PPO without planner influence (policy only) — compare to full loop in tests
    if policy is None:
        from rl.train_ppo import train_ppo

        model, env, _ = train_ppo(frame, config=config)
    else:
        model = policy
        env = ServerlessEnv(frame, config)
    return evaluate_policy(model, env, episodes=1)


def main() -> None:
    result = run_baseline_vs_proposed()
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
