"""PPO / environment tests: R01-R04 (docs/test_plan.md section 6)."""

import numpy as np
import pytest
import torch

from baseline.reactive import ReactiveAutoscaler
from rl.environment import ACTIONS, ServerlessEnv
from rl.evaluate_ppo import evaluate_policy, evaluate_reactive
from rl.policy import ActorCritic
from rl.reward import compute_reward
from rl.train_ppo import compute_gae, load_checkpoint, save_checkpoint, train_ppo

CTX = {
    "max_capacity": 30.0,
    "sla_threshold": 250.0,
    "max_change": 5.0,
    "power_per_container_w": 15.0,
}

COMPLIANT = dict(energy=155.0, latency=40.0, p95_latency=52.0, cold_starts=0.0, capacity=10.0, required_capacity=10.0)
VIOLATING = dict(energy=35.0, latency=264.0, p95_latency=343.2, cold_starts=5.0, capacity=2.0, required_capacity=30.0)
OVER_PROVISIONED = dict(energy=455.0, latency=40.0, p95_latency=52.0, cold_starts=0.0, capacity=30.0, required_capacity=2.0)


# ---------------------------------------------------------------- R01
def test_r01_action_set_names():
    assert ACTIONS == ["NoOp", "PreWarm", "ScaleOut", "Reuse", "ScaleIn", "Terminate"]


def test_r01_unknown_action_rejected(processed_frame, test_config):
    env = ServerlessEnv(processed_frame, test_config)
    with pytest.raises(ValueError):
        env.step(len(ACTIONS))


def test_r01_all_actions_runnable(processed_frame, test_config):
    env = ServerlessEnv(processed_frame, test_config)
    obs = env.reset()
    for action in range(len(ACTIONS)):
        obs, _, done, info = env.step(action)
        assert info["action"] == ACTIONS[action]
        assert not done


# ---------------------------------------------------------------- R02
def test_r02_capacity_bounds_random_policy(processed_frame, test_config):
    env = ServerlessEnv(processed_frame, test_config)
    bounds = test_config["containers"]
    rng = np.random.default_rng(0)

    obs = env.reset()
    done = False
    while not done:
        action = int(rng.integers(0, len(ACTIONS)))
        obs, _, done, info = env.step(action)
        assert bounds["min"] <= info["capacity"] <= bounds["max"]


def test_r02_repeated_scale_out_clamps(processed_frame, test_config):
    env = ServerlessEnv(processed_frame, test_config)
    bounds = test_config["containers"]
    env.reset()
    last = None
    for _ in range(20):
        _, _, _, info = env.step(2)  # ScaleOut
        last = info["capacity"]
    assert last == bounds["max"]

    for _ in range(20):
        _, _, _, info = env.step(4)  # ScaleIn
        last = info["capacity"]
    assert last == bounds["min"]


# ---------------------------------------------------------------- R03
def test_r03_sla_violation_decreases_reward():
    reward_ok, comp_ok = compute_reward(COMPLIANT, context=CTX)
    reward_bad, comp_bad = compute_reward(VIOLATING, context=CTX)

    assert comp_ok["sla_violation"] == 0.0
    assert comp_bad["sla_violation"] > 0.0
    assert reward_bad < reward_ok


def test_r03_sla_penalty_has_highest_weight():
    from rl.reward import DEFAULT_WEIGHTS

    # SLA is the primary constraint: its weight is the largest of the set.
    assert DEFAULT_WEIGHTS["sla_violation"] == max(DEFAULT_WEIGHTS.values())
    _, comp = compute_reward(VIOLATING, context=CTX)
    # The SLA penalty alone outweighs the energy-saving incentive.
    assert comp["sla_penalty"] > comp["energy"]


# ---------------------------------------------------------------- R04
def test_r04_energy_vs_sla_tradeoff():
    reward_bal, comp_bal = compute_reward(COMPLIANT, context=CTX)
    reward_high, comp_high = compute_reward(OVER_PROVISIONED, context=CTX)
    reward_low, comp_low = compute_reward(VIOLATING, context=CTX)

    # Over-provisioning wastes energy; under-provisioning breaks SLA. Both
    # are worse than the balanced state, which is the point of R04.
    assert reward_bal > reward_high
    assert reward_bal > reward_low
    assert comp_high["energy"] > comp_bal["energy"]
    assert comp_high["underutil"] > comp_bal["underutil"]
    assert comp_low["sla_violation"] > comp_bal["sla_violation"]
    assert comp_low["latency"] > comp_bal["latency"]


# ---------------------------------------------------------------- env behaviour
def test_environment_observation_shape(processed_frame, test_config):
    env = ServerlessEnv(processed_frame, test_config)
    obs = env.reset()
    assert obs.shape == (10,)
    obs, reward, done, info = env.step(0)
    assert obs.shape == (10,)
    assert isinstance(reward, float)
    assert {"capacity", "sla_violated", "reward_components"}.issubset(info)


def test_environment_terminates_and_then_raises(processed_frame, test_config):
    env = ServerlessEnv(processed_frame, test_config)
    env.reset()
    done = False
    while not done:
        _, _, done, _ = env.step(0)
    with pytest.raises(RuntimeError):
        env.step(0)


# ---------------------------------------------------------------- PPO mechanics
def test_compute_gae_shapes():
    advantages, returns = compute_gae([1.0, 2.0, 3.0], [0.5, 0.5, 0.5], 0.0, gamma=0.99, lam=0.95)
    assert advantages.shape == (3,)
    assert returns.shape == (3,)


def test_policy_act_and_evaluate_shapes():
    model = ActorCritic(obs_dim=10, n_actions=6)
    obs = np.zeros(10, dtype=np.float32)
    action, logp, value = model.act(obs)
    assert 0 <= action < 6
    assert isinstance(logp, float) and isinstance(value, float)

    logp_t, entropy_t, values_t = model.evaluate(
        torch.zeros(4, 10), torch.zeros(4, dtype=torch.int64)
    )
    assert logp_t.shape == (4,)
    assert entropy_t.shape == (4,)
    assert values_t.shape == (4,)


def test_train_ppo_smoke_and_checkpoint(processed_frame, test_config, tmp_path):
    model, env, history = train_ppo(processed_frame, config=test_config)
    assert len(history["mean_reward_history"]) == test_config["control"]["rl"]["training"]["episodes"]
    assert np.isfinite(history["best_mean_reward"])

    path = str(tmp_path / "ppo.pt")
    save_checkpoint(model, path, env.observation_size, env.n_actions)
    loaded = load_checkpoint(path)
    obs = np.zeros(10, dtype=np.float32)
    assert loaded.greedy_action(obs) in range(6)


def test_evaluate_policy_metrics(processed_frame, test_config):
    model, env, _ = train_ppo(processed_frame, config=test_config)
    metrics = evaluate_policy(model, env, episodes=1)
    assert 0.0 <= metrics["sla_violation_rate"] <= 1.0
    assert metrics["steps"] > 0
    for key in ("mean_reward", "mean_energy_w", "mean_capacity", "mean_cold_starts", "mean_p95_latency_ms"):
        assert np.isfinite(metrics[key])


def test_reactive_baseline_actions(processed_frame, test_config):
    env = ServerlessEnv(processed_frame, test_config)
    scaler = ReactiveAutoscaler(test_config)
    obs = env.reset()
    done = False
    steps = 0
    while not done and steps < 200:
        action = scaler.select_action(env, obs)
        assert 0 <= action < len(ACTIONS)
        obs, _, done, _ = env.step(action)
        steps += 1
    assert steps > 0


def test_evaluate_reactive_metrics(processed_frame, test_config):
    metrics = evaluate_reactive(processed_frame, test_config)
    assert set(metrics) >= {"mean_reward", "sla_violation_rate", "mean_energy_w", "steps"}
    assert 0.0 <= metrics["sla_violation_rate"] <= 1.0
