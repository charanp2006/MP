"""PPO training for the serverless control environment (docs/design.md section 12).

Pure-PyTorch PPO with generalized advantage estimation (GAE) and the clipped
surrogate objective. Trains the policy on the simulated environment built from
the data pipeline's workload timeline and saves the best checkpoint.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Dict, List, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from configs import load_config
from rl.environment import ServerlessEnv
from rl.policy import ActorCritic


def set_seed(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)


def compute_gae(
    rewards: List[float], values: List[float], last_value: float, gamma: float, lam: float
) -> Tuple[np.ndarray, np.ndarray]:
    """Generalized advantage estimation over a finished trajectory."""
    advantages = np.zeros(len(rewards), dtype=np.float32)
    gae = 0.0
    for t in reversed(range(len(rewards))):
        next_value = last_value if t == len(rewards) - 1 else values[t + 1]
        delta = rewards[t] + gamma * next_value - values[t]
        gae = delta + gamma * lam * gae
        advantages[t] = gae
    returns = advantages + np.asarray(values, dtype=np.float32)
    return advantages, returns


def collect_episode(
    env: ServerlessEnv, model: ActorCritic
) -> Dict[str, np.ndarray]:
    """Run one episode and record the trajectory."""
    obs_buffer: List[np.ndarray] = []
    act_buffer: List[int] = []
    logp_buffer: List[float] = []
    rew_buffer: List[float] = []
    val_buffer: List[float] = []
    done_buffer: List[bool] = []

    obs = env.reset()
    done = False
    while not done:
        action, logp, value = model.act(obs)
        next_obs, reward, done, _ = env.step(action)
        obs_buffer.append(obs)
        act_buffer.append(action)
        logp_buffer.append(logp)
        rew_buffer.append(reward)
        val_buffer.append(value)
        done_buffer.append(done)
        obs = next_obs

    with torch.no_grad():
        _, last_value = model.forward(torch.tensor(obs, dtype=torch.float32))
    return {
        "obs": np.asarray(obs_buffer, dtype=np.float32),
        "actions": np.asarray(act_buffer, dtype=np.int64),
        "log_probs": np.asarray(logp_buffer, dtype=np.float32),
        "rewards": np.asarray(rew_buffer, dtype=np.float32),
        "values": np.asarray(val_buffer, dtype=np.float32),
        "last_value": np.float32(last_value.item()),
    }


def ppo_update(
    model: ActorCritic,
    optimizer: torch.optim.Optimizer,
    traj: Dict[str, np.ndarray],
    advantages: np.ndarray,
    returns: np.ndarray,
    cfg: Dict,
) -> Dict[str, float]:
    """Clipped PPO update over the trajectory."""
    clip_ratio = float(cfg.get("clip_ratio", 0.2))
    epochs = int(cfg.get("epochs_per_update", 4))
    minibatch = int(cfg.get("minibatch_size", 64))
    value_coef = 0.5
    entropy_coeff = float(cfg.get("entropy_coeff", 0.01))

    # Normalize advantages (stabilizes the gradient scale).
    advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

    obs = torch.tensor(traj["obs"], dtype=torch.float32)
    actions = torch.tensor(traj["actions"], dtype=torch.int64)
    old_logp = torch.tensor(traj["log_probs"], dtype=torch.float32)
    adv = torch.tensor(advantages, dtype=torch.float32)
    ret = torch.tensor(returns, dtype=torch.float32)

    dataset = TensorDataset(obs, actions, old_logp, adv, ret)
    loader = DataLoader(dataset, batch_size=minibatch, shuffle=True)

    totals = {"policy_loss": 0.0, "value_loss": 0.0, "entropy": 0.0, "batches": 0}
    for _ in range(epochs):
        for obs_b, act_b, oldlogp_b, adv_b, ret_b in loader:
            logp, entropy, value = model.evaluate(obs_b, act_b)
            ratio = torch.exp(logp - oldlogp_b)
            surr1 = ratio * adv_b
            surr2 = torch.clamp(ratio, 1.0 - clip_ratio, 1.0 + clip_ratio) * adv_b
            policy_loss = -torch.min(surr1, surr2).mean()
            value_loss = nn.functional.mse_loss(value, ret_b)
            entropy_loss = -entropy.mean()

            loss = policy_loss + value_coef * value_loss + entropy_coeff * entropy_loss
            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 0.5)
            optimizer.step()

            totals["policy_loss"] += policy_loss.item()
            totals["value_loss"] += value_loss.item()
            totals["entropy"] += entropy.mean().item()
            totals["batches"] += 1

    n = max(totals.pop("batches"), 1)
    return {k: v / n for k, v in totals.items()}


def train_ppo(frame, config: Dict | None = None, verbose: bool = False):
    """Train PPO on the simulated environment; return (model, env, history)."""
    config = config or load_config()
    rl_cfg = config["control"]["rl"]
    train_cfg = rl_cfg["training"]
    set_seed(int(train_cfg.get("seed", 42)))

    env = ServerlessEnv(frame, config)
    model = ActorCritic(obs_dim=env.observation_size, n_actions=env.n_actions)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(train_cfg.get("learning_rate", 3e-4)))

    gamma = float(train_cfg.get("gamma", 0.99))
    lam = float(train_cfg.get("gae_lambda", 0.95))
    episodes = int(train_cfg.get("episodes", 200))

    history: List[float] = []
    best_mean = -float("inf")
    best_state = {k: v.clone() for k, v in model.state_dict().items()}

    for ep in range(episodes):
        traj = collect_episode(env, model)
        advantages, returns = compute_gae(
            traj["rewards"].tolist(), traj["values"].tolist(), float(traj["last_value"]), gamma, lam
        )
        update_stats = ppo_update(model, optimizer, traj, advantages, returns, train_cfg)

        mean_reward = float(traj["rewards"].mean())
        history.append(mean_reward)
        if mean_reward > best_mean:
            best_mean = mean_reward
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
        if verbose and (ep + 1) % max(1, episodes // 10) == 0:
            print(
                f"ep {ep + 1}/{episodes}  reward={mean_reward:.3f}  "
                f"policy={update_stats['policy_loss']:.4f}  value={update_stats['value_loss']:.4f}"
            )

    model.load_state_dict(best_state)
    model.eval()
    return model, env, {"mean_reward_history": history, "best_mean_reward": best_mean}


def save_checkpoint(model: ActorCritic, path: str, obs_dim: int, n_actions: int) -> str:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    torch.save({"model_state": model.state_dict(), "obs_dim": obs_dim, "n_actions": n_actions}, path)
    return path


def load_checkpoint(path: str) -> ActorCritic:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    model = ActorCritic(obs_dim=payload["obs_dim"], n_actions=payload["n_actions"])
    model.load_state_dict(payload["model_state"])
    model.eval()
    return model


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the PPO controller")
    parser.add_argument("--config", default=None)
    parser.add_argument("--episodes", type=int, default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    from data.pipeline import run

    config = load_config(args.config)
    if args.episodes is not None:
        config["control"]["rl"]["training"]["episodes"] = args.episodes

    frame, _ = run(config=config)
    model, env, history = train_ppo(frame, config=config, verbose=args.verbose)

    checkpoint = config["control"]["rl"].get("checkpoint_path", "models/ppo_policy.pt")
    save_checkpoint(model, checkpoint, env.observation_size, env.n_actions)
    print(json.dumps({"checkpoint": checkpoint, "best_mean_reward": history["best_mean_reward"]}, indent=2))


if __name__ == "__main__":
    main()
