import json

import pytest

from experiments.evaluate_ppo_m5 import evaluate_m5
from experiments.synthetic_scenarios import generate_scenarios
from orchestrator.safety_shield import SafetyShield
from rl.environment import NOOP, PREWARM, SCALE_IN, SCALE_OUT, ServerlessEnv
from rl.train_ppo import load_checkpoint, save_checkpoint, train_ppo


def test_synthetic_scenarios_are_deterministic():
    first = generate_scenarios(steps=8, seed=42)
    second = generate_scenarios(steps=8, seed=42)

    assert set(first) == {"ramp", "burst", "periodic", "sparse", "stress", "mixed"}
    assert first["ramp"]["invocation_count"].tolist() == second["ramp"]["invocation_count"].tolist()


def test_lifecycle_delay_and_cold_start_observation(test_config):
    frame = generate_scenarios(steps=5)["ramp"]
    env = ServerlessEnv(frame, test_config)

    env.reset()
    _, _, _, info = env.step(PREWARM)
    assert info["pending_warm_containers"] > 0
    assert info["warm_containers"] == 0

    obs, _, _, info = env.step(NOOP)
    assert info["warm_containers"] > 0
    assert info["pending_warm_containers"] == 0

    env.reset()
    obs, _, _, info = env.step(SCALE_OUT)
    assert info["cold_starts"] > 0
    assert obs[7] > 0.0


def test_safety_shield_blocks_risky_and_unauthorized_actions(test_config, state_factory):
    shield = SafetyShield(test_config)
    risky = state_factory(p95_latency_ms=245.0, sla_margin_ms=5.0, active_containers=8)

    guarded = shield.filter(SCALE_IN, risky)
    assert guarded.action == NOOP
    assert "sla_guard" in guarded.codes

    unauthorized = shield.filter(SCALE_OUT, state_factory(), authorized=False)
    assert unauthorized.action == NOOP
    assert "unauthorized" in unauthorized.codes


def test_safety_shield_rejects_unknown_action(test_config, state_factory):
    shield = SafetyShield(test_config)

    result = shield.filter(99, state_factory())

    assert result.action == NOOP
    assert "unknown_action" in result.codes


def test_checkpoint_rejects_shape_mismatch(tmp_path):
    from rl.policy import ActorCritic

    model = ActorCritic(obs_dim=10, n_actions=6)
    path = str(tmp_path / "policy.pt")
    save_checkpoint(model, path, 10, 6, metadata={"test": True})

    with pytest.raises(ValueError, match="obs_dim"):
        load_checkpoint(path, expected_obs_dim=12)


def test_ppo_training_accepts_safety_filter(processed_frame, test_config):
    shield = SafetyShield(test_config)
    model, _, history = train_ppo(
        processed_frame,
        config=test_config,
        action_filter=lambda env, action: shield.from_env(env, action),
    )

    assert model is not None
    assert len(history["mean_reward_history"]) >= 1
    assert "shield_interventions" in history


def test_m5_evaluation_writes_artifacts(test_config, tmp_path):
    result = evaluate_m5(test_config, tmp_path, seeds=[42], episodes=1, steps=8)

    assert result["manifest"]["mode"] == "simulation"
    assert len(result["manifest"]["arms"]) >= 4
    assert (tmp_path / "run_manifest.json").exists()
    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "comparison.csv").exists()
    assert (tmp_path / "learning_curves.csv").exists()
    assert (tmp_path / "action_frequencies.csv").exists()
    assert (tmp_path / "timelines.csv").exists()
    assert json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))["rows"]
