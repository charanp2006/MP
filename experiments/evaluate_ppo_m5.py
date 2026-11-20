"""M5 PPO evaluation: multi-seed, scenario-based, safety-shielded comparisons.

All metrics produced here are SIMULATED from workload traces or synthetic
scenarios. No live latency, energy or Kubernetes measurements are claimed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from agent.planner import StubPlanner
from baseline.reactive import ReactiveAutoscaler
from configs import load_config
from data.feature_engineering import build_features
from experiments.synthetic_scenarios import generate_scenarios
from orchestrator.safety_shield import SafetyShield
from orchestrator.state_builder import build_state
from rl.environment import NOOP, PREWARM, REUSE, SCALE_IN, SCALE_OUT, TERMINATE, ServerlessEnv
from rl.train_ppo import save_checkpoint, train_ppo

STRATEGY_TO_ACTION = {
    "NoOp": NOOP,
    "PreWarm": PREWARM,
    "ScaleOut": SCALE_OUT,
    "Reuse": REUSE,
    "ScaleIn": SCALE_IN,
    "Terminate": TERMINATE,
}

METRIC_FIELDS = [
    "arm",
    "seed",
    "scenario",
    "source",
    "steps",
    "mean_reward",
    "reward_std",
    "sla_violation_rate",
    "mean_energy_w",
    "mean_capacity",
    "max_capacity",
    "mean_cold_starts",
    "total_cold_starts",
    "mean_p95_latency_ms",
    "max_p95_latency_ms",
    "shield_intervention_rate",
    "final_capacity",
]

ACTION_FIELDS = ["arm", "seed", "scenario", "action", "count", "share"]


def _config_hash(config: Dict) -> str:
    text = json.dumps(config, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(text).hexdigest()


def _git_commit() -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip() or None
    except OSError:
        return None


def _chronological_split(frame: pd.DataFrame, train_ratio: float = 0.7):
    split = int(len(frame) * train_ratio)
    return frame.iloc[:split].copy(), frame.iloc[split:].copy()


def _tft_forecast_array(
    frame: pd.DataFrame,
    checkpoint_path: str,
    config: Dict,
    scale_factor: float = 1.0,
) -> np.ndarray:
    from forecasting.tft_service import TFTForecastService

    service = TFTForecastService(
        checkpoint_path,
        fallback_policy="persistence",
        max_staleness_s=None,
    )
    history = int(service.history)
    features = list(service.feature_columns)
    target_index = int(service.target_index)
    target_column = features[target_index] if target_index < len(features) else "invocation_count"
    if target_column not in frame.columns:
        target_column = "invocation_count"
    values: List[float] = []
    for idx in range(len(frame)):
        if idx < history:
            values.append(float(frame.iloc[idx][target_column]))
            continue
        window = frame[features].iloc[idx - history : idx].to_numpy(dtype=float)
        if target_column == "invocation_count" and "raw_invocation_count" in frame.columns:
            window[:, features.index(target_column)] = (
                frame["raw_invocation_count"].iloc[idx - history : idx].to_numpy(dtype=float)
            )
        try:
            result = service.forecast_history(window, observed_at=frame.iloc[idx]["timestamp"])
            predicted = float(result["predicted_workload"][0])
        except Exception:
            predicted = float(window[-1, target_index])
        values.append(max(0.0, predicted) * float(scale_factor))
    return np.asarray(values, dtype=float)


def _rule_action(planner: StubPlanner, shield: SafetyShield, config: Dict, env, forecast=None):
    env_forecast, metrics = env.current_context()
    if forecast is not None:
        env_forecast = dict(env_forecast)
        env_forecast["predicted_workload"] = [float(forecast)]
    state = build_state(env_forecast, metrics, config)
    plan = planner.plan(state)
    proposed = STRATEGY_TO_ACTION[plan.strategy]
    return shield.from_env(env, proposed, plan=plan), plan


def _run_arm(
    env: ServerlessEnv,
    action_fn: Callable,
    arm: str,
    seed: int,
    scenario: str,
    source: str,
) -> tuple[Dict, List[Dict], List[Dict]]:
    obs = env.reset()
    done = False
    rows: List[Dict] = []
    actions: Counter = Counter()
    interventions = 0
    total_steps = 0

    while not done:
        decision = action_fn(env, obs)
        action = int(getattr(decision, "action", decision))
        proposed = int(getattr(decision, "proposed_action", action))
        interventions += int(proposed != action)
        obs, reward, done, info = env.step(action)
        actions[info["action"]] += 1
        total_steps += 1
        rows.append(
            {
                "step": total_steps,
                "workload": info["workload"],
                "capacity": info["capacity"],
                "warm_containers": info["warm_containers"],
                "pending_warm_containers": info["pending_warm_containers"],
                "p95_latency_ms": info["p95_latency"],
                "sla_violated": info["sla_violated"],
                "cold_starts": info["cold_starts"],
                "energy_w": info["energy"],
                "reward": reward,
                "action": info["action"],
            }
        )

    frame = pd.DataFrame(rows)
    summary = {
        "arm": arm,
        "seed": int(seed),
        "scenario": scenario,
        "source": source,
        "steps": int(total_steps),
        "mean_reward": float(frame["reward"].mean()),
        "reward_std": float(frame["reward"].std(ddof=0)),
        "sla_violation_rate": float(frame["sla_violated"].mean()),
        "mean_energy_w": float(frame["energy_w"].mean()),
        "mean_capacity": float(frame["capacity"].mean()),
        "max_capacity": float(frame["capacity"].max()),
        "mean_cold_starts": float(frame["cold_starts"].mean()),
        "total_cold_starts": float(frame["cold_starts"].sum()),
        "mean_p95_latency_ms": float(frame["p95_latency_ms"].mean()),
        "max_p95_latency_ms": float(frame["p95_latency_ms"].max()),
        "shield_intervention_rate": float(interventions / max(total_steps, 1)),
        "final_capacity": int(frame["capacity"].iloc[-1]),
    }
    action_rows = [
        {
            "arm": arm,
            "seed": int(seed),
            "scenario": scenario,
            "action": name,
            "count": int(count),
            "share": float(count / max(total_steps, 1)),
        }
        for name, count in sorted(actions.items())
    ]
    for row in rows:
        row.update({"arm": arm, "seed": int(seed), "scenario": scenario, "source": source})
    return summary, action_rows, rows


def _make_plots(out_dir: Path, learning: pd.DataFrame, timelines: pd.DataFrame, actions: pd.DataFrame) -> Dict[str, str]:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return {}

    plots = out_dir / "plots"
    plots.mkdir(parents=True, exist_ok=True)
    paths = {}

    if not learning.empty:
        fig, ax = plt.subplots(figsize=(9, 4))
        for seed, group in learning.groupby("seed"):
            ax.plot(group["episode"], group["mean_reward"], alpha=0.7, label=f"seed {seed}")
        ax.set_xlabel("Training episode")
        ax.set_ylabel("Mean episode reward (simulated)")
        ax.set_title("PPO learning curves")
        ax.legend()
        fig.tight_layout()
        paths["learning_curve"] = str(plots / "learning_curve.png")
        fig.savefig(paths["learning_curve"])
        plt.close(fig)

    if not timelines.empty:
        fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
        axes[0].plot(timelines["step"], timelines["workload"], label="workload")
        axes[0].plot(timelines["step"], timelines["capacity"] * 100, label="capacity x100")
        axes[0].legend()
        axes[1].plot(timelines["step"], timelines["p95_latency_ms"], label="P95")
        axes[1].axhline(250.0, linestyle="--", color="red", label="SLA 250 ms")
        axes[1].legend()
        axes[2].plot(timelines["step"], timelines["energy_w"], label="energy proxy")
        axes[2].bar(timelines["step"], timelines["cold_starts"], alpha=0.5, label="cold starts")
        axes[2].legend()
        axes[-1].set_xlabel("Step")
        fig.suptitle("Representative simulated timeline")
        fig.tight_layout()
        paths["timeline"] = str(plots / "timeline.png")
        fig.savefig(paths["timeline"])
        plt.close(fig)

    if not actions.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        pivot = actions.pivot_table(
            index="action", columns="arm", values="share", aggfunc="mean", fill_value=0.0
        )
        pivot.plot(kind="bar", ax=ax)
        ax.set_ylabel("Action share (simulated)")
        ax.set_title("Action frequencies by arm")
        fig.tight_layout()
        paths["action_frequencies"] = str(plots / "action_frequencies.png")
        fig.savefig(paths["action_frequencies"])
        plt.close(fig)

    return paths


def evaluate_m5(
    config: Dict,
    out_dir: str | Path,
    seeds: List[int],
    episodes: int,
    steps: int,
    trace_csv: Optional[str] = None,
    tft_checkpoint: Optional[str] = None,
) -> Dict:
    run_config = deepcopy(config)
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    scenarios = generate_scenarios(steps=steps, seed=int(seeds[0]))

    learning_rows: List[Dict] = []
    summary_rows: List[Dict] = []
    action_rows: List[Dict] = []
    timeline_rows: List[Dict] = []
    model_paths: List[str] = []

    for seed in seeds:
        run_config["control"]["rl"]["training"]["seed"] = int(seed)
        run_config["control"]["rl"]["training"]["episodes"] = int(episodes)
        shield = SafetyShield(run_config)
        planner = StubPlanner(run_config)
        train_frame, _ = _chronological_split(scenarios["mixed"])

        model, train_env, history = train_ppo(
            train_frame,
            config=run_config,
            action_filter=lambda env, action: shield.from_env(env, action),
        )
        checkpoint_path = output / f"ppo_seed_{seed}.pt"
        save_checkpoint(
            model,
            str(checkpoint_path),
            train_env.observation_size,
            int(run_config["control"]["rl"]["n_actions"]),
            metadata={"seed": int(seed), "episodes": int(episodes), "mode": "simulation"},
        )
        model_paths.append(str(checkpoint_path))
        for episode_idx, reward in enumerate(history["mean_reward_history"], start=1):
            learning_rows.append(
                {"seed": int(seed), "episode": episode_idx, "mean_reward": float(reward)}
            )

        for scenario_name, frame in scenarios.items():
            _, test_frame = _chronological_split(frame)
            arms = {
                "fixed_noop": lambda env, obs, _shield=shield: _shield.from_env(env, NOOP),
                "reactive": lambda env, obs, _shield=shield, _scaler=ReactiveAutoscaler(run_config): _shield.from_env(
                    env, _scaler.select_action(env, obs)
                ),
                "persistence_rule": lambda env, obs, _planner=planner, _shield=shield: _rule_action(
                    _planner, _shield, run_config, env
                )[0],
                "ppo_shielded": lambda env, obs, _model=model, _shield=shield: _shield.from_env(
                    env, _model.greedy_action(obs)
                ),
            }
            for arm_name, action_fn in arms.items():
                env = ServerlessEnv(test_frame, run_config)
                summary, actions, timeline = _run_arm(
                    env, action_fn, arm_name, seed, scenario_name, "synthetic"
                )
                summary_rows.append(summary)
                action_rows.extend(actions)
                if seed == seeds[0] and scenario_name == "mixed":
                    timeline_rows.extend(timeline)

    tft_status = {"attempted": False, "available": False, "reason": "not_requested"}
    trace_scale_factor = 1.0
    if trace_csv and Path(trace_csv).exists():
        trace = pd.read_csv(trace_csv, parse_dates=["timestamp"])
        sim_cfg = run_config["control"]["rl"]["sim"]
        load_per_container = max(
            1.0,
            (100.0 / float(sim_cfg["containers_per_100_rps"]))
            * (float(run_config["control"]["interval_seconds"]) / 60.0),
        )
        target_peak = float(run_config["containers"]["max"]) * load_per_container * 0.9
        raw_peak = max(float(trace["invocation_count"].max()), 1.0)
        trace_scale_factor = target_peak / raw_peak
        trace["raw_invocation_count"] = trace["invocation_count"]
        trace["invocation_count"] = trace["invocation_count"] * trace_scale_factor
        if "cpu_utilization" not in trace.columns or "memory_utilization" not in trace.columns:
            load_scale = max(float(trace["invocation_count"].max()), 1.0)
            trace["cpu_utilization"] = np.clip(trace["invocation_count"] / load_scale, 0.0, 1.0)
            trace["memory_utilization"] = np.clip(
                0.25 + 0.6 * trace["cpu_utilization"], 0.0, 1.0
            )
        trace, _ = build_features(trace, run_config)
        _, trace_test = _chronological_split(trace)
        trace_test = trace_test.iloc[:steps].copy()
        tft_status["attempted"] = bool(tft_checkpoint and Path(tft_checkpoint).exists())
        if tft_checkpoint and Path(tft_checkpoint).exists():
            try:
                forecasts = _tft_forecast_array(
                    trace_test, tft_checkpoint, run_config, scale_factor=trace_scale_factor
                )
                env = ServerlessEnv(trace_test, run_config)
                env.set_forecast(forecasts)
                shield = SafetyShield(run_config)
                planner = StubPlanner(run_config)
                for arm_name, action_fn in {
                    "trace_persistence_rule": lambda env, obs, _p=planner, _s=shield: _rule_action(
                        _p, _s, run_config, env
                    )[0],
                    "trace_tft_rule": lambda env, obs, _p=planner, _s=shield: _rule_action(
                        _p, _s, run_config, env, forecast=env._forecast[env.idx]
                    )[0],
                }.items():
                    summary, actions, timeline = _run_arm(
                        env if arm_name == "trace_tft_rule" else ServerlessEnv(trace_test, run_config),
                        action_fn,
                        arm_name,
                        int(seeds[0]),
                        "chronological_trace",
                        "azure_historical" if "azure" in trace_csv else "trace",
                    )
                    summary_rows.append(summary)
                    action_rows.extend(actions)
                tft_status["available"] = True
                tft_status["reason"] = "tft_checkpoint_loaded"
            except Exception as exc:
                tft_status["reason"] = f"unavailable: {type(exc).__name__}: {exc}"
        else:
            tft_status["reason"] = "tft_checkpoint_missing"
    elif trace_csv:
        tft_status["reason"] = "trace_csv_missing"

    summary_df = pd.DataFrame(summary_rows)
    grouped = summary_df.groupby("arm")[METRIC_FIELDS[4:]].agg(["mean", "std"])
    grouped.columns = [f"{metric}_{stat}" for metric, stat in grouped.columns]
    aggregate = grouped.reset_index().to_dict(orient="records")
    learning_df = pd.DataFrame(learning_rows)
    actions_df = pd.DataFrame(action_rows)
    timelines_df = pd.DataFrame(timeline_rows)

    learning_df.to_csv(output / "learning_curves.csv", index=False)
    summary_df.to_csv(output / "comparison.csv", index=False)
    actions_df.to_csv(output / "action_frequencies.csv", index=False)
    timelines_df.to_csv(output / "timelines.csv", index=False)
    (output / "summary.json").write_text(
        json.dumps(
            {
                "mode": "simulation",
                "aggregate": aggregate,
                "rows": summary_rows,
                "tft": tft_status,
                "checkpoints": model_paths,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    manifest = {
        "mode": "simulation",
        "generated_by": "experiments.evaluate_ppo_m5",
        "config_sha256": _config_hash(run_config),
        "git_commit": _git_commit(),
        "seeds": [int(seed) for seed in seeds],
        "episodes_per_seed": int(episodes),
        "scenario_steps": int(steps),
        "scenarios": list(scenarios),
        "trace_csv": trace_csv,
        "trace_resource_columns": "simulated_from_invocations_when_absent",
        "trace_workload_scale_factor": float(trace_scale_factor),
        "tft_checkpoint": tft_checkpoint,
        "tft": tft_status,
        "arms": sorted(summary_df["arm"].unique().tolist()),
        "units": {
            "energy_w": "simulated proxy watts",
            "p95_latency_ms": "simulated latency milliseconds",
            "cold_starts": "simulated container starts",
            "reward": "normalized control objective (higher is better)",
        },
    }
    (output / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str), encoding="utf-8"
    )
    plots = _make_plots(output, learning_df, timelines_df, actions_df)

    return {"manifest": manifest, "summary": aggregate, "plots": plots, "output": str(output)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate M5 PPO controller in simulation")
    parser.add_argument("--config", default=None)
    parser.add_argument("--out-dir", default="results/ppo/m5")
    parser.add_argument("--seeds", default=None, help="Comma-separated seeds")
    parser.add_argument("--episodes", type=int, default=None)
    parser.add_argument("--steps", type=int, default=48)
    parser.add_argument("--trace-csv", default=None, help="Optional chronological prepared trace")
    parser.add_argument("--tft-checkpoint", default=None, help="Optional TFT checkpoint for tft+rule")
    args = parser.parse_args()

    config = load_config(args.config)
    seeds = (
        [int(value) for value in args.seeds.split(",")]
        if args.seeds
        else [int(value) for value in config.get("evaluation", {}).get("seeds", [42])]
    )
    episodes = (
        int(args.episodes)
        if args.episodes is not None
        else int(config["control"]["rl"]["training"].get("episodes", 3))
    )
    result = evaluate_m5(
        config,
        args.out_dir,
        seeds,
        episodes,
        int(args.steps),
        trace_csv=args.trace_csv,
        tft_checkpoint=args.tft_checkpoint,
    )
    print(json.dumps({"manifest": result["manifest"], "summary": result["summary"]}, indent=2, default=str))


if __name__ == "__main__":
    main()
