"""M8 consolidated evaluation: matched workloads, repeat runs, ablations, report."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from agent.planner import StubPlanner
from configs import load_config
from data.feature_engineering import build_features
from experiments.evaluate_decision_engine import _summary_row
from experiments.synthetic_scenarios import generate_scenarios
from monitoring.alerts import AlertManager
from monitoring.feedback import FeedbackLoop
from monitoring.metrics import MetricsCollector
from orchestrator.decision_log import DecisionLogger
from orchestrator.decision_loop import DecisionLoop, run_episode
from orchestrator.execution_audit import ExecutionAuditLogger
from rl.environment import NOOP, SCALE_IN, SCALE_OUT, ServerlessEnv

EXPERIMENTS = {
    "E0": {"forecast": "none", "planner": "rules", "controller": "rules", "executor": "simulator"},
    "E1": {"forecast": "persistence", "planner": "rules", "controller": "rules", "executor": "simulator"},
    "E2": {"forecast": "tft", "planner": "rules", "controller": "rules", "executor": "simulator"},
    "E3": {"forecast": "tft", "planner": "qwen3_stub", "controller": "rules", "executor": "simulator"},
    "E4": {"forecast": "persistence", "planner": "rules", "controller": "ppo", "executor": "simulator"},
    "E5": {"forecast": "tft", "planner": "rules", "controller": "ppo", "executor": "simulator"},
    "E6": {"forecast": "tft", "planner": "qwen3_stub", "controller": "ppo", "executor": "simulator"},
    "E7": {"forecast": "selected", "planner": "selected", "controller": "selected", "executor": "live_deferred"},
}

RUN_FIELDS = [
    "experiment_id",
    "forecast",
    "forecast_actual",
    "planner",
    "planner_actual",
    "controller",
    "executor",
    "workload_id",
    "source",
    "seed",
    "steps",
    "status",
    "mean_reward",
    "reward_std",
    "sla_violation_rate",
    "mean_energy_w",
    "mean_capacity",
    "mean_cold_starts",
    "mean_p95_latency_ms",
    "shield_intervention_rate",
    "fallback_rate",
    "final_action",
    "correlation_id",
    "run_dir",
]

AGGREGATE_FIELDS = [
    "experiment_id",
    "forecast",
    "planner",
    "controller",
    "executor",
    "runs",
    "degraded_runs",
    "mean_reward",
    "reward_std",
    "reward_ci95",
    "sla_violation_rate",
    "mean_energy_w",
    "mean_capacity",
    "mean_cold_starts",
    "shield_intervention_rate",
    "status",
]


class _RulePolicy:
    def greedy_action(self, obs) -> int:
        values = np.asarray(obs, dtype=float)
        p95_ratio = float(values[5]) if len(values) > 5 else 0.0
        capacity_ratio = float(values[6]) if len(values) > 6 else 0.0
        sla_margin = float(values[9]) if len(values) > 9 else 0.0
        if p95_ratio >= 0.95 or sla_margin < 0.0:
            return SCALE_OUT
        if capacity_ratio > 0.65 and p95_ratio < 0.5:
            return SCALE_IN
        return NOOP


class _FixedPolicy:
    def __init__(self, action: int) -> None:
        self._action = int(action)

    def greedy_action(self, _obs) -> int:
        return self._action


def _config_hash(config: Dict) -> str:
    return hashlib.sha256(json.dumps(config, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _git_commit() -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=False
        )
        return result.stdout.strip() or None
    except OSError:
        return None


def _file_sha256(path: Optional[str]) -> Optional[str]:
    if not path or not Path(path).exists():
        return None
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _frame_sha256(frame: pd.DataFrame) -> str:
    payload = frame.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _chronological_split(frame: pd.DataFrame, train_ratio: float = 0.7):
    split = int(len(frame) * train_ratio)
    return frame.iloc[:split].copy(), frame.iloc[split:].copy()


def _load_trace_frame(config: Dict, trace_csv: Optional[str], steps: int) -> Tuple[pd.DataFrame, float]:
    trace = pd.read_csv(trace_csv, parse_dates=["timestamp"])
    sim = config["control"]["rl"]["sim"]
    load_per_container = max(
        1.0, (100.0 / float(sim["containers_per_100_rps"])) * (float(config["control"]["interval_seconds"]) / 60.0)
    )
    target_peak = float(config["containers"]["max"]) * load_per_container * 0.9
    raw_peak = max(float(trace["invocation_count"].max()), 1.0)
    scale_factor = target_peak / raw_peak
    trace["raw_invocation_count"] = trace["invocation_count"]
    trace["invocation_count"] = trace["invocation_count"] * scale_factor
    if "cpu_utilization" not in trace.columns or "memory_utilization" not in trace.columns:
        load_scale = max(float(trace["invocation_count"].max()), 1.0)
        trace["cpu_utilization"] = np.clip(trace["invocation_count"] / load_scale, 0.0, 1.0)
        trace["memory_utilization"] = np.clip(0.25 + 0.6 * trace["cpu_utilization"], 0.0, 1.0)
    trace, _ = build_features(trace, config)
    _, heldout = _chronological_split(trace)
    return heldout.iloc[:steps].copy(), float(scale_factor)


def _workloads(
    config: Dict,
    steps: int,
    seed: int,
    scenarios: List[str],
    include_trace: bool,
    trace_csv: Optional[str],
) -> Dict[str, Dict]:
    generated = generate_scenarios(steps=steps, seed=seed)
    registry: Dict[str, Dict] = {}
    for name in scenarios:
        if name not in generated:
            raise ValueError(f"unknown workload scenario {name!r}")
        frame = generated[name].copy()
        registry[f"{seed}:{name}"] = {
            "id": name,
            "seed": int(seed),
            "source": "synthetic",
            "scale_factor": 1.0,
            "sha256": _frame_sha256(frame),
            "frame": frame,
        }
    if include_trace and trace_csv and Path(trace_csv).exists():
        frame, scale_factor = _load_trace_frame(config, trace_csv, steps)
        registry[f"{seed}:chronological_trace"] = {
            "id": "chronological_trace",
            "seed": int(seed),
            "source": "azure_historical" if "azure" in str(trace_csv) else "trace",
            "scale_factor": scale_factor,
            "sha256": _frame_sha256(frame),
            "frame": frame,
        }
    return registry


def _make_loop(config: Dict, run_dir: Path, experiment_id: str, workload_id: str, seed: int) -> DecisionLoop:
    run_config = deepcopy(config)
    run_config.setdefault("decision_log", {})["enabled"] = True
    run_config["decision_log"]["path"] = str(run_dir / "decision.jsonl")
    run_config.setdefault("execution", {})["audit_enabled"] = True
    run_config["execution"]["audit_path"] = str(run_dir / "audit.jsonl")
    run_config.setdefault("monitoring", {}).setdefault("feedback", {})["record_enabled"] = True
    run_config["monitoring"]["feedback"]["record_path"] = str(run_dir / "feedback.jsonl")
    run_config.setdefault("monitoring", {}).setdefault("alerts", {})["enabled"] = True
    run_config["monitoring"]["alerts"]["log_path"] = str(run_dir / "alerts.jsonl")
    run_config["monitoring"]["enabled"] = True

    return DecisionLoop(
        run_config,
        planner=StubPlanner(run_config),
        metrics=MetricsCollector(run_config),
        feedback=FeedbackLoop(run_config),
        alerts=AlertManager(run_config),
        logger=DecisionLogger(run_config),
        execution_audit=ExecutionAuditLogger(run_config),
    )


def _load_policy(path: Optional[str], injected, config: Dict):
    if injected is not None:
        return injected, "injected", _file_sha256(path)
    if not path or not Path(path).exists():
        return None, "missing", None
    try:
        from rl.train_ppo import load_checkpoint

        model = load_checkpoint(path)
        return model, path, _file_sha256(path)
    except Exception:
        return None, "load_failed", _file_sha256(path)


def _tft_available(path: Optional[str]) -> bool:
    if not path or not Path(path).exists():
        return False
    try:
        from forecasting.tft_service import TFTForecastService

        TFTForecastService(path, max_staleness_s=None)
        return True
    except Exception:
        return False


def _summary(experiment: Dict, experiment_id: str, workload: Dict, seed: int, records: List[Dict], run_dir: Path) -> Dict:
    row = _summary_row(experiment_id, records)
    forecast_actual = records[0]["forecast_source"] if records else "none"
    statuses: List[str] = []
    if experiment["forecast"] == "tft" and forecast_actual != "tft":
        statuses.append("degraded_tft_fallback")
    if experiment["planner"] == "qwen3_stub":
        statuses.append("stub_proxy")
    status = ",".join(statuses) if statuses else "ok"
    row.update(
        {
            "experiment_id": experiment_id,
            "forecast": experiment["forecast"],
            "forecast_actual": forecast_actual,
            "planner": experiment["planner"],
            "planner_actual": "stub_proxy" if experiment["planner"] == "qwen3_stub" else "rules",
            "controller": experiment["controller"],
            "executor": experiment["executor"],
            "workload_id": workload["id"],
            "source": workload["source"],
            "seed": int(seed),
            "status": status,
            "correlation_id": records[-1]["correlation_id"] if records else "",
            "run_dir": str(run_dir),
        }
    )
    return {key: row.get(key, "") for key in RUN_FIELDS}


def _aggregate(rows: List[Dict]) -> List[Dict]:
    frame = pd.DataFrame(rows)
    output: List[Dict] = []
    for experiment_id, group in frame.groupby("experiment_id", sort=True):
        rewards = group["mean_reward"].to_numpy(dtype=float)
        mean = float(np.mean(rewards)) if len(rewards) else 0.0
        std = float(np.std(rewards, ddof=0)) if len(rewards) else 0.0
        ci = 1.96 * std / math.sqrt(len(rewards)) if len(rewards) else 0.0
        first = group.iloc[0]
        statuses = set(group["status"].astype(str))
        status = "ok" if statuses == {"ok"} else ",".join(sorted(statuses))
        output.append(
            {
                "experiment_id": str(experiment_id),
                "forecast": first["forecast"],
                "planner": first["planner"],
                "controller": first["controller"],
                "executor": first["executor"],
                "runs": int(len(group)),
                "degraded_runs": int(group["status"].astype(str).ne("ok").sum()),
                "mean_reward": mean,
                "reward_std": std,
                "reward_ci95": float(ci),
                "sla_violation_rate": float(np.mean(group["sla_violation_rate"].astype(float))),
                "mean_energy_w": float(np.mean(group["mean_energy_w"].astype(float))),
                "mean_capacity": float(np.mean(group["mean_capacity"].astype(float))),
                "mean_cold_starts": float(np.mean(group["mean_cold_starts"].astype(float))),
                "shield_intervention_rate": float(np.mean(group["shield_intervention_rate"].astype(float))),
                "status": status,
            }
        )
    output.append(
        {
            "experiment_id": "E7",
            "forecast": "selected",
            "planner": "selected",
            "controller": "selected",
            "executor": "live_deferred",
            "runs": 0,
            "degraded_runs": 0,
            "mean_reward": "",
            "reward_std": "",
            "reward_ci95": "",
            "sla_violation_rate": "",
            "mean_energy_w": "",
            "mean_capacity": "",
            "mean_cold_starts": "",
            "shield_intervention_rate": "",
            "status": "not_run_requires_live_cluster",
        }
    )
    return output


def _write_csv(path: Path, rows: List[Dict], fields: List[str]) -> None:
    pd.DataFrame(rows, columns=fields).to_csv(path, index=False)


def _figures(out_dir: Path, aggregates: List[Dict], sla_threshold_ms: float) -> List[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figures = out_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame([row for row in aggregates if row.get("runs")])
    paths: List[str] = []
    if frame.empty:
        return paths
    ids = frame["experiment_id"].astype(str).tolist()
    plots = [
        ("mean_reward", "Mean simulated reward", None),
        ("sla_violation_rate", "SLA violation rate", None),
        ("mean_energy_w", "Mean simulated energy (W)", None),
        ("mean_capacity", "Mean active containers", None),
    ]
    for column, title, _ in plots:
        values = frame[column].astype(float).to_numpy()
        errors = frame["reward_ci95"].astype(float).to_numpy() if column == "mean_reward" else None
        fig, ax = plt.subplots(figsize=(9, 4.5))
        ax.bar(ids, values, yerr=errors, capsize=3, color="#3b6ea5")
        ax.set_title(title)
        ax.set_xlabel("Experiment")
        ax.grid(axis="y", alpha=0.25)
        if column == "sla_violation_rate":
            ax.text(0.02, 0.95, f"SLA target: {sla_threshold_ms:.0f} ms", transform=ax.transAxes, va="top")
        path = figures / f"{column}_by_experiment.png"
        fig.tight_layout()
        fig.savefig(path, dpi=140)
        plt.close(fig)
        paths.append(str(path))
    return paths


def _markdown_table(rows: List[Dict], fields: List[str]) -> List[str]:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        values = []
        for field in fields:
            value = row.get(field, "")
            if isinstance(value, float):
                value = f"{value:.4f}"
            values.append(str(value).replace("|", "\\|"))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def _write_report(
    out_dir: Path,
    manifest: Dict,
    aggregates: List[Dict],
    figure_paths: List[str],
    config: Dict,
) -> Path:
    sla = float(config["sla"]["p95_latency_ms"])
    lines = [
        "# M8 — Consolidated Evaluation Report",
        "",
        "**Evidence tier:** simulated closed-loop replay; dry-run execution only. No live cluster, live energy, live latency or Grafana measurement is claimed.",
        "",
        "## 1. Dataset and licensing",
        "",
        "Azure Functions 2019 invocation traces are a historical workload data source only (CC-BY-4.0). Synthetic scenarios are deterministic and generated locally. See the manifest for trace hashes, schema and coverage.",
        "",
        "## 2. Trace schema, units and time coverage",
        "",
        "- `timestamp`, `invocation_count`, `cpu_utilization`, `memory_utilization`, derived time/cyclic features.",
        "- Invocation count is scaled to the configured container capacity envelope; CPU/memory proxies are simulated when absent.",
        "- Coverage and per-workload SHA-256 are recorded in `run_manifest.json` and `workloads.json`.",
        "",
        "## 3. Data preparation and split",
        "",
        "Chronological 70/15/15 split is used by the forecast track; control-loop workloads use the predeclared held-out segment/short scenario window. No random shuffle is used.",
        "",
        "## 4. Model configurations and seeds",
        "",
        f"- Config SHA-256: `{manifest['config_sha256']}`",
        f"- Commit: `{manifest.get('git_commit', 'unknown')}`",
        f"- Seeds: `{manifest['seeds']}`",
        f"- Steps per run: `{manifest['steps']}`",
        f"- TFT checkpoint available: `{manifest['tft']['available']}`",
        f"- PPO checkpoint available: `{manifest['policy']['available']}`",
        "- Qwen3 runtime: unavailable/stub proxy in this environment; no real Qwen3 result is reported.",
        "",
        "## 5. Forecast results",
        "",
        "See `results/forecast/azure2019_total/metrics.json` for the separate TFT/baseline evaluation. This runner records whether TFT was actually used per run; fallback runs are marked `degraded_tft_fallback`.",
        "",
        "## 6. PPO training/evaluation results",
        "",
        "See `results/ppo/m5/` for the multi-seed PPO training/evaluation artifacts. This runner loads the policy checkpoint and compares it against rule/reactive baselines on identical workload frames.",
        "",
        "## 7. Agentic planner evaluation",
        "",
        "See `results/planner/` for planner validation/latency artifacts. `qwen3_stub` rows are offline stubs, not Qwen3 measurements.",
        "",
        "## 8. End-to-end comparison and ablations",
        "",
        "E0-E6 form a predeclared ablation ladder. E7 is deferred until a live cluster and deployed metrics stack are available.",
        "",
    ]
    lines.extend(_markdown_table(aggregates, AGGREGATE_FIELDS))
    lines.extend(
        [
            "",
            "## 9. SLA protection",
            "",
            f"The SLA target is {sla:.0f} ms P95. SLA violations are reported from the simulated environment; the safety shield remains the final authority in every arm.",
            "",
            "## 10. Energy measurement caveat",
            "",
            "Energy values are `power_per_container_w * active_containers + idle_power_w` from the simulator, not metered wall-plug or cloud billing data.",
            "",
            "## 11. Limitations",
            "",
            "- Live execution, live Prometheus/Grafana values and real Qwen3 are not validated here.",
            "- Confidence intervals are normal approximations over matched-run means, not independently sampled physical trials.",
            "- Azure CPU/memory/energy/latency/cold-start values are simulated proxies; the trace supplies invocations only.",
            "",
            "## 12. Reproducibility",
            "",
        ]
    )
    command = (
        "py -m experiments.evaluate_m8 --config configs/project.yaml "
        f"--out-dir {manifest['out_dir']} --seeds {','.join(str(s) for s in manifest['seeds'])} "
        f"--steps {manifest['steps']} --scenarios {','.join(manifest['scenarios'])}"
    )
    if manifest.get("trace_csv"):
        command += f" --trace-csv {manifest['trace_csv']} --include-trace"
    lines.extend(["```powershell", command, "```", "", "Artifacts: `run_manifest.json`, `runs.csv`, `aggregates.csv`, `workloads.json`, `figures/`, `runs/`.", ""])
    lines.extend(
        [
            "## 13. Implemented architecture",
            "",
            "```mermaid",
            "flowchart LR",
            "  A[Workload registry] --> B[TFT or persistence forecast]",
            "  B --> C[Stub planner / Qwen3 stub proxy]",
            "  C --> D[Rules or PPO controller]",
            "  D --> E[Safety shield and validators]",
            "  E --> F[Bounded executor; dry-run in research runs]",
            "  F --> G[Simulated environment outcome]",
            "  G --> H[Feedback, alerts, decision/audit logs]",
            "  H --> I[M8 aggregate report and figures]",
            "```",
            "",
        ]
    )
    if figure_paths:
        lines.extend(["## 14. Figures", ""])
        for path in figure_paths:
            lines.append(f"![{Path(path).stem}]({Path(path).relative_to(out_dir).as_posix()})")
            lines.append("")
    path = out_dir / "report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def evaluate_m8(
    config: Dict,
    out_dir: str | Path,
    seeds: List[int],
    steps: int,
    scenarios: List[str],
    trace_csv: Optional[str] = None,
    tft_checkpoint: Optional[str] = None,
    policy_checkpoint: Optional[str] = None,
    include_trace: bool = False,
    policy=None,
    disable_tft: bool = False,
) -> Dict:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    runs_dir = output / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    tft_path = None if disable_tft else (
        tft_checkpoint if tft_checkpoint is not None else config.get("evaluation", {}).get("m8", {}).get("tft_checkpoint")
    )
    policy_path = policy_checkpoint or config.get("evaluation", {}).get("m8", {}).get("policy_checkpoint")
    tft_state = _tft_available(tft_path)
    loaded_policy, policy_source, policy_sha = _load_policy(policy_path, policy, config)
    workloads: Dict[str, Dict] = {}
    for seed in seeds:
        workloads.update(_workloads(config, steps, seed, scenarios, include_trace, trace_csv))

    rows: List[Dict] = []
    for experiment_id, experiment in EXPERIMENTS.items():
        if experiment["executor"] == "live_deferred":
            continue
        if experiment["controller"] == "ppo" and loaded_policy is None:
            rows.append(
                {
                    "experiment_id": experiment_id,
                    "forecast": experiment["forecast"],
                    "forecast_actual": "tft" if tft_state and experiment["forecast"] == "tft" else "persistence",
                    "planner": experiment["planner"],
                    "planner_actual": "stub_proxy" if experiment["planner"] == "qwen3_stub" else "rules",
                    "controller": experiment["controller"],
                    "executor": experiment["executor"],
                    "workload_id": "none",
                    "source": "none",
                    "seed": int(seeds[0]),
                    "steps": 0,
                    "status": "skipped_policy_unavailable",
                    "mean_reward": "",
                    "reward_std": "",
                    "sla_violation_rate": "",
                    "mean_energy_w": "",
                    "mean_capacity": "",
                    "mean_cold_starts": "",
                    "mean_p95_latency_ms": "",
                    "shield_intervention_rate": "",
                    "fallback_rate": "",
                    "final_action": "",
                    "correlation_id": "",
                    "run_dir": "",
                }
            )
            continue

        for _workload_key, workload in workloads.items():
            seed = int(workload["seed"])
            if seed not in seeds:
                continue
            workload_id = workload["id"]
            frame = workload["frame"]
            run_dir = runs_dir / experiment_id / workload_id / f"seed_{seed}"
            run_dir.mkdir(parents=True, exist_ok=True)
            selected_policy = loaded_policy if experiment["controller"] == "ppo" else _RulePolicy()
            loop = _make_loop(config, run_dir, experiment_id, workload_id, seed)
            env = ServerlessEnv(frame, config)
            records = run_episode(
                env,
                config,
                loop=loop,
                policy=selected_policy,
                steps=steps,
                execute=False,
                use_tft=bool(tft_state and experiment["forecast"] == "tft"),
                tft_checkpoint=tft_path,
                correlation_prefix=f"{experiment_id}-{workload_id}-s{seed}",
                forecast_scale=workload["scale_factor"],
            )
            row = _summary(experiment, experiment_id, workload, seed, records, run_dir)
            row["steps"] = len(records)
            rows.append(row)

    aggregates = _aggregate(rows)
    _write_csv(output / "runs.csv", rows, RUN_FIELDS)
    _write_csv(output / "aggregates.csv", aggregates, AGGREGATE_FIELDS)
    (output / "workloads.json").write_text(
        json.dumps(
            {key: {k: v for k, v in value.items() if k != "frame"} for key, value in workloads.items()},
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    manifest = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "python": sys.version.split()[0],
        "config_sha256": _config_hash(config),
        "out_dir": str(output),
        "seeds": [int(seed) for seed in seeds],
        "steps": int(steps),
        "scenarios": list(scenarios),
        "include_trace": bool(include_trace),
        "trace_csv": str(trace_csv) if trace_csv else None,
        "trace_sha256": _file_sha256(trace_csv),
        "tft": {"path": tft_path, "available": tft_state, "sha256": _file_sha256(tft_path)},
        "policy": {"path": policy_path, "source": policy_source, "available": loaded_policy is not None, "sha256": policy_sha},
        "qwen3_available": bool(config.get("evaluation", {}).get("m8", {}).get("qwen3_available", False)),
        "experiments": EXPERIMENTS,
        "evidence_tier": "simulated",
        "units": {
            "energy": "simulated watts from configured simulator constants",
            "latency": "simulated milliseconds",
            "capacity": "container count",
            "reward": "configured weighted simulated objective",
        },
        "artifacts": ["runs.csv", "aggregates.csv", "workloads.json", "report.md", "figures/"],
    }
    (output / "run_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    figures = _figures(output, aggregates, float(config["sla"]["p95_latency_ms"]))
    manifest["artifacts"].extend(str(Path(path).relative_to(output).as_posix()) for path in figures)
    (output / "run_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    report = _write_report(output, manifest, aggregates, figures, config)

    return {
        "manifest": str(output / "run_manifest.json"),
        "runs": str(output / "runs.csv"),
        "aggregates": str(output / "aggregates.csv"),
        "report": str(report),
        "figures": figures,
        "rows": rows,
        "aggregates_data": aggregates,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="M8 consolidated evaluation runner")
    parser.add_argument("--config", default=None)
    parser.add_argument("--out-dir", default=None)
    parser.add_argument("--seeds", default=None)
    parser.add_argument("--steps", type=int, default=None)
    parser.add_argument("--scenarios", default=None)
    parser.add_argument("--trace-csv", default=None)
    parser.add_argument("--tft-checkpoint", default=None)
    parser.add_argument("--policy-checkpoint", default=None)
    parser.add_argument("--include-trace", action="store_true")
    parser.add_argument("--no-tft", action="store_true", help="force persistence forecasts for a fast smoke run")
    args = parser.parse_args()

    config = load_config(args.config)
    m8 = config.get("evaluation", {}).get("m8", {})
    seeds = [int(value) for value in args.seeds.split(",")] if args.seeds else list(config.get("evaluation", {}).get("seeds", [42]))
    scenarios = args.scenarios.split(",") if args.scenarios else list(m8.get("scenarios", ["mixed"]))
    result = evaluate_m8(
        config,
        args.out_dir or m8.get("out_dir", "results/evaluation/m8"),
        seeds,
        args.steps or int(m8.get("steps", 12)),
        scenarios,
        trace_csv=args.trace_csv or m8.get("trace_csv"),
        tft_checkpoint=args.tft_checkpoint or m8.get("tft_checkpoint"),
        policy_checkpoint=args.policy_checkpoint or m8.get("policy_checkpoint"),
        include_trace=args.include_trace or bool(m8.get("include_trace", False)),
        disable_tft=args.no_tft,
    )
    print(json.dumps({key: value for key, value in result.items() if key not in {"rows", "aggregates_data"}}, indent=2))


if __name__ == "__main__":
    main()
