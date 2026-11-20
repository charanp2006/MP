"""M5 decision-engine replay: complete provenance and end-to-end ablations.

All runtime effects are simulated. No live Kubernetes, energy or latency
measurements are claimed by this module.
"""

from __future__ import annotations

import argparse
import hashlib
import html as html_lib
import json
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from agent.planner import StubPlanner
from agent.schemas import Plan
from configs import load_config
from data.feature_engineering import build_features
from orchestrator.decision_log import DecisionLogger
from orchestrator.decision_loop import DecisionLoop, run_episode
from rl.environment import ServerlessEnv

ABLATIONS = ["full", "planner_off", "policy_off", "feedback_off", "forecast_off"]


class _FixedPlanner:
    def __init__(self, plan: Plan) -> None:
        self._plan = plan

    def plan(self, state):
        return self._plan


def _config_hash(config: Dict) -> str:
    return hashlib.sha256(json.dumps(config, sort_keys=True, default=str).encode("utf-8")).hexdigest()


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


def _load_trace_frame(config: Dict, trace_csv: Optional[str], steps: int):
    if trace_csv and Path(trace_csv).exists():
        trace = pd.read_csv(trace_csv, parse_dates=["timestamp"])
        scale_factor = 1.0
        sim = config["control"]["rl"]["sim"]
        load_per_container = max(
            1.0,
            (100.0 / float(sim["containers_per_100_rps"]))
            * (float(config["control"]["interval_seconds"]) / 60.0),
        )
        target_peak = float(config["containers"]["max"]) * load_per_container * 0.9
        raw_peak = max(float(trace["invocation_count"].max()), 1.0)
        scale_factor = target_peak / raw_peak
        trace["raw_invocation_count"] = trace["invocation_count"]
        trace["invocation_count"] = trace["invocation_count"] * scale_factor
        if "cpu_utilization" not in trace.columns or "memory_utilization" not in trace.columns:
            load_scale = max(float(trace["invocation_count"].max()), 1.0)
            trace["cpu_utilization"] = np.clip(trace["invocation_count"] / load_scale, 0.0, 1.0)
            trace["memory_utilization"] = np.clip(
                0.25 + 0.6 * trace["cpu_utilization"], 0.0, 1.0
            )
        trace, _ = build_features(trace, config)
        _, heldout = _chronological_split(trace)
        return heldout.iloc[:steps].copy(), scale_factor, "azure_historical" if "azure" in str(trace_csv) else "trace"

    from data.pipeline import run

    frame, _ = run(config=config)
    return frame, 1.0, "sample"


def _load_policy(config: Dict, checkpoint_path: Optional[str], policy: Optional[Callable]):
    if policy is not None:
        return policy, "injected", None
    path = checkpoint_path or config.get("control", {}).get("rl", {}).get("checkpoint_path", "")
    if path and Path(path).exists():
        from rl.train_ppo import load_checkpoint

        return load_checkpoint(path), str(path), str(path)
    return None, "none", None


def _summary_row(arm: str, records: List[Dict]) -> Dict:
    if not records:
        return {"arm": arm, "steps": 0}
    rewards = np.asarray([float(record["reward"]) for record in records], dtype=float)
    outcomes = [record["outcome"] for record in records]
    interventions = [
        bool(record["decision"]["hierarchy"]["shield"]["allowed"]) is False
        for record in records
    ]
    return {
        "arm": arm,
        "steps": len(records),
        "mean_reward": float(rewards.mean()),
        "reward_std": float(rewards.std(ddof=0)),
        "sla_violation_rate": float(np.mean([bool(item["sla_violated"]) for item in outcomes])),
        "mean_energy_w": float(np.mean([float(item["energy_w"]) for item in outcomes])),
        "mean_capacity": float(np.mean([int(item["capacity"]) for item in outcomes])),
        "mean_cold_starts": float(np.mean([float(item["cold_starts"]) for item in outcomes])),
        "shield_intervention_rate": float(np.mean(interventions)),
        "fallback_rate": float(np.mean([bool(record["decision"]["used_fallback"]) for record in records])),
        "final_action": records[-1]["decision"]["final_action_name"],
    }


def _replay_frame(records: List[Dict]) -> pd.DataFrame:
    rows: List[Dict] = []
    for step, record in enumerate(records, start=1):
        decision = record["decision"]
        hierarchy = decision["hierarchy"]
        shield = hierarchy["shield"]
        state = decision["state"]
        outcome = record["outcome"]
        rows.append(
            {
                "step": step,
                "correlation_id": decision["correlation_id"],
                "forecast_source": hierarchy["forecast_source"],
                "current_workload": state["current_workload"],
                "forecast_workload": state["forecast_workload"],
                "forecast_peak": state["forecast_peak"],
                "plan_strategy": decision["plan"]["strategy"],
                "plan_code": decision["plan_code"],
                "ppo_action": decision["ppo_action_name"],
                "shield_proposed": shield["proposed_action_name"],
                "shield_allowed": shield["allowed"],
                "shield_codes": ",".join(shield["codes"]),
                "final_action": decision["final_action_name"],
                "action_code": decision["action_code"],
                "guard_code": decision["guard_code"],
                "p95_latency_ms": outcome["p95_latency_ms"],
                "sla_violated": outcome["sla_violated"],
                "cold_starts": outcome["cold_starts"],
                "energy_w": outcome["energy_w"],
                "capacity": outcome["capacity"],
                "reward": outcome["reward"],
            }
        )
    return pd.DataFrame(rows)


def _markdown_cell(value) -> str:
    if isinstance(value, (dict, list)):
        value = json.dumps(value, sort_keys=True, default=str)
    return str(value).replace("|", "\\|").replace("\n", " ")[:200]


def _write_replay_markdown(out_dir: Path, frame: pd.DataFrame) -> Path:
    path = out_dir / "replay.md"
    lines = [
        "# M5 decision replay (simulated)",
        "",
        "Each row is one bounded control step with recorded inputs, actions and outcome.",
        "",
    ]
    if not frame.empty:
        lines.append("| " + " | ".join(frame.columns) + " |")
        lines.append("| " + " | ".join("---" for _ in frame.columns) + " |")
        for row in frame.to_dict(orient="records"):
            lines.append("| " + " | ".join(_markdown_cell(row[column]) for column in frame.columns) + " |")
    else:
        lines.append("_No replay steps were generated._")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_replay_html(out_dir: Path, frame: pd.DataFrame) -> Path:
    path = out_dir / "replay.html"
    headers = list(frame.columns)
    header_html = "".join(f"<th>{html_lib.escape(str(column))}</th>" for column in headers)
    rows_html = []
    for row in frame.to_dict(orient="records"):
        cells = "".join(f"<td>{html_lib.escape(_markdown_cell(row[column]))}</td>" for column in headers)
        rows_html.append(f"<tr>{cells}</tr>")
    document = "\n".join(
        [
            "<!doctype html>",
            "<html lang='en'>",
            "<head><meta charset='utf-8'><title>M5 decision replay</title>",
            "<style>body{font-family:ui-monospace,monospace;font-size:12px;margin:2rem;}"
            "table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:4px;}"
            "th{background:#f2f2f2;position:sticky;top:0}</style></head>",
            "<body>",
            "<h1>M5 decision replay (simulated)</h1>",
            "<p>Correlation ID links inputs, plan, PPO proposal, shield decision and outcome.</p>",
            "<table><thead><tr>" + header_html + "</tr></thead><tbody>" + "".join(rows_html) + "</tbody></table>",
            "</body></html>",
        ]
    )
    path.write_text(document, encoding="utf-8")
    return path


def _write_replay_plot(out_dir: Path, frame: pd.DataFrame) -> Optional[str]:
    if frame.empty:
        return None
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return None
    fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    axes[0].plot(frame["step"], frame["current_workload"], label="current workload")
    axes[0].plot(frame["step"], frame["forecast_peak"], label="forecast peak")
    axes[0].legend()
    axes[1].plot(frame["step"], frame["p95_latency_ms"], label="P95 latency (simulated)")
    axes[1].axhline(250.0, linestyle="--", color="red", label="SLA 250 ms")
    axes[1].legend()
    axes[2].plot(frame["step"], frame["capacity"], label="capacity")
    axes[2].bar(frame["step"], frame["cold_starts"], alpha=0.5, label="cold starts")
    axes[2].legend()
    axes[-1].set_xlabel("Step")
    fig.suptitle("M5 replay timeline (simulated)")
    fig.tight_layout()
    path = out_dir / "replay_timeline.png"
    fig.savefig(path)
    plt.close(fig)
    return str(path)


def evaluate_decision_engine(
    config: Dict,
    out_dir: str | Path,
    steps: int,
    trace_csv: Optional[str] = None,
    tft_checkpoint: Optional[str] = None,
    policy_checkpoint: Optional[str] = None,
    policy: Optional[Callable] = None,
    execute: bool = False,
) -> Dict:
    run_config = deepcopy(config)
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    decisions_dir = output / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)

    frame, scale_factor, source = _load_trace_frame(run_config, trace_csv, int(steps))
    selected_policy, policy_source, resolved_policy_path = _load_policy(run_config, policy_checkpoint, policy)
    use_tft = bool(tft_checkpoint and Path(tft_checkpoint).exists())
    noop_plan = Plan(strategy="NoOp", desired_capacity_change=0, priority="balanced", urgency="low")
    configured_arms = run_config.get("decision_engine", {}).get("ablations", ABLATIONS)
    ablations = [arm for arm in configured_arms if arm in ABLATIONS] or ABLATIONS

    summary_rows: List[Dict] = []
    replay_records: List[Dict] = []
    for arm in ablations:
        arm_config = deepcopy(run_config)
        arm_config.setdefault("decision_log", {})["path"] = str(decisions_dir / f"{arm}.jsonl")
        arm_config["decision_log"]["enabled"] = True
        logger = DecisionLogger(arm_config)
        logger.reset()
        arm_policy = None if arm == "policy_off" else selected_policy
        arm_loop = None
        if arm == "planner_off":
            arm_loop = DecisionLoop(arm_config, planner=_FixedPlanner(noop_plan), logger=logger)
        else:
            arm_loop = DecisionLoop(arm_config, logger=logger)
        records = run_episode(
            ServerlessEnv(frame, arm_config),
            arm_config,
            policy=arm_policy,
            steps=int(steps),
            use_tft=use_tft and arm != "forecast_off",
            tft_checkpoint=tft_checkpoint,
            execute=execute,
            logger=logger,
            loop=arm_loop,
            correlation_prefix=arm,
            use_feedback=arm != "feedback_off",
            forecast_scale=scale_factor,
        )
        summary_rows.append(_summary_row(arm, records))
        if arm == "full":
            replay_records = records

    replay_df = _replay_frame(replay_records)
    ablation_df = pd.DataFrame(summary_rows)
    replay_df.to_csv(output / "replay.csv", index=False)
    ablation_df.to_csv(output / "ablations.csv", index=False)
    (output / "replay.json").write_text(
        json.dumps(replay_records, indent=2, default=str), encoding="utf-8"
    )
    markdown_path = _write_replay_markdown(output, replay_df)
    html_path = _write_replay_html(output, replay_df)
    plot_path = _write_replay_plot(output, replay_df)
    (output / "summary.json").write_text(
        json.dumps({"mode": "simulation", "rows": summary_rows}, indent=2, default=str),
        encoding="utf-8",
    )
    manifest = {
        "mode": "simulation",
        "generated_by": "experiments.evaluate_decision_engine",
        "config_sha256": _config_hash(run_config),
        "git_commit": _git_commit(),
        "steps": int(steps),
        "trace_csv": trace_csv,
        "trace_source": source,
        "trace_workload_scale_factor": float(scale_factor),
        "tft_checkpoint": tft_checkpoint,
        "tft_used": use_tft,
        "policy_checkpoint": resolved_policy_path,
        "policy_source": policy_source,
        "execute": bool(execute),
        "ablations": ablations,
        "decision_logs": str(decisions_dir),
        "artifacts": {
            "replay_csv": str(output / "replay.csv"),
            "replay_json": str(output / "replay.json"),
            "replay_md": str(markdown_path),
            "replay_html": str(html_path),
            "replay_plot": plot_path,
        },
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
    return {
        "manifest": manifest,
        "summary": summary_rows,
        "replay_rows": len(replay_df),
        "output": str(output),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay the M5 decision engine and write provenance artifacts")
    parser.add_argument("--config", default=None)
    parser.add_argument("--out-dir", default="results/decision/m5")
    parser.add_argument("--steps", type=int, default=24)
    parser.add_argument("--trace-csv", default=None)
    parser.add_argument("--tft-checkpoint", default=None)
    parser.add_argument("--policy-checkpoint", default=None)
    parser.add_argument("--execute", action="store_true", help="exercise the executor (still disabled/dry-run by config)")
    args = parser.parse_args()

    result = evaluate_decision_engine(
        load_config(args.config),
        args.out_dir,
        steps=args.steps,
        trace_csv=args.trace_csv,
        tft_checkpoint=args.tft_checkpoint,
        policy_checkpoint=args.policy_checkpoint,
        execute=args.execute,
    )
    print(json.dumps({"manifest": result["manifest"], "summary": result["summary"]}, indent=2, default=str))


if __name__ == "__main__":
    main()
