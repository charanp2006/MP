from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

import pandas as pd

from configs import load_config
from data.feature_engineering import build_features
from data.generic_adapter import GenericIngestionAdapter, records_to_trace, write_schema
from demo.synthetic_client import generate_events
from experiments.evaluate_decision_engine import _summary_row
from experiments.evaluate_m8 import _file_sha256, _load_policy, _make_loop
from orchestrator.decision_loop import run_episode
from rl.environment import ServerlessEnv


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=False
        )
        return result.stdout.strip() or None
    except OSError:
        return None


def _config_hash(config: Dict) -> str:
    return hashlib.sha256(json.dumps(config, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, default=str) + "\n" for row in rows), encoding="utf-8")


def _write_figure(trace: pd.DataFrame, records: list[dict], path: Path) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return

    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    workload = trace.pivot_table(
        index="timestamp", columns="function_id", values="invocation_count", aggfunc="sum", fill_value=0
    )
    workload.plot(ax=axes[0], title="Synthetic requests by sample service")
    axes[0].set_ylabel("invocations / window")
    p95 = [float(record.get("p95_latency_ms") or 0.0) for record in records]
    axes[1].plot(range(1, len(p95) + 1), p95, marker="o", color="#b54708")
    axes[1].set_title("P95 latency observed by the simulated control loop")
    axes[1].set_xlabel("control step")
    axes[1].set_ylabel("p95 latency (ms)")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140)
    plt.close(fig)


def _routing_summary(events: list[dict]) -> list[dict]:
    rows: dict[tuple[str, str], dict] = {}
    for event in events:
        key = (event["service_id"], event["payload_class"])
        row = rows.setdefault(
            key,
            {"service_id": key[0], "payload_class": key[1], "events": 0, "errors": 0, "route": "/invoke"},
        )
        row["events"] += 1
        row["errors"] += int(event.get("error_count", 0))
    return sorted(rows.values(), key=lambda item: (item["service_id"], item["payload_class"]))


def _report(manifest: dict, summary: dict, routing: list[dict]) -> str:
    lines = [
        "# M9 Deferred Demonstration Integration",
        "",
        f"- Generated at: `{manifest['generated_at']}`",
        f"- Evidence tier: **{manifest['evidence_tier']}**",
        f"- Scenario: `{manifest['scenario']}` with seed `{manifest['seed']}`",
        f"- Synthetic requests: `{manifest['event_count']}` across `{manifest['services']}`",
        f"- Ingestion auth: `{manifest['auth_mode']}`; no tokens are persisted",
        f"- Sample services are scaffolding only; live deployment was deferred",
        "",
        "## Flow",
        "",
        "```mermaid",
        "flowchart LR",
        "  A[Synthetic client] --> B[Generic ingestion adapter]",
        "  B --> C[Fixed-window trace]",
        "  C --> D[TFT / persistence forecast]",
        "  D --> E[Qwen3 stub planner]",
        "  E --> F[PPO / bounded policy]",
        "  F --> G[Validator + SLA guard]",
        "  G --> H[Simulated executor + audit]",
        "  H --> I[Feedback, alerts, demo report]",
        "```",
        "",
        "## Simulated control summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Mean reward | {summary.get('mean_reward', 0):.4f} |",
        f"| Reward std | {summary.get('reward_std', 0):.4f} |",
        f"| SLA violation rate | {summary.get('sla_violation_rate', 0):.4f} |",
        f"| Mean energy (W) | {summary.get('mean_energy_w', 0):.4f} |",
        f"| Mean capacity | {summary.get('mean_capacity', 0):.4f} |",
        f"| Shield intervention rate | {summary.get('shield_intervention_rate', 0):.4f} |",
        "",
        "## Service routing (simulated counts)",
        "",
        "| Service | Payload class | Requests | Errors |",
        "|---|---|---:|---:|",
    ]
    for row in routing:
        lines.append(
            f"| {row['service_id']} | {row['payload_class']} | {row['events']} | {row['errors']} |"
        )
    lines.extend(
        [
            "",
            "## Presentation storyboard",
            "",
            "1. Problem: serverless capacity and energy trade-off under a P95 SLA.",
            "2. Architecture: forecast -> planner -> PPO -> validators -> execution -> observation.",
            "3. Data: Azure invocation trace plus explicitly simulated resource proxies.",
            "4. Demo: synthetic requests arrive for checkout/search/recommend services.",
            "5. Control loop: one decision cycle with forecast, plan, action, guard, and audit.",
            "6. Evidence: M8 consolidated simulation tables and ablations; no live cluster claims.",
            "7. Limitations: live Kubernetes/OpenFaaS/Docker and Grafana validation deferred.",
            "8. Closing: reproducible artifacts and safety boundaries, with measured values only from simulation.",
            "",
            "The final PPTX and image assets remain archive material on the `files` branch and were not edited.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_demo(
    config: Dict,
    out_dir: str | Path,
    steps: int | None = None,
    scenario: str | None = None,
    seed: int | None = None,
    use_tft: bool | None = None,
) -> Dict:
    cfg = deepcopy(config)
    demo_cfg = cfg.get("demo", {})
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)

    selected_steps = int(steps or demo_cfg.get("steps", 24))
    selected_scenario = str(scenario or demo_cfg.get("scenario", "mixed"))
    selected_seed = int(seed if seed is not None else demo_cfg.get("seed", 42))
    interval_s = int(demo_cfg.get("interval_s", 60))
    selected_use_tft = bool(use_tft if use_tft is not None else demo_cfg.get("use_tft", False))
    services = [str(name) for name in demo_cfg.get("services", ["fn_checkout", "fn_search", "fn_recommend"])]
    payload_classes = [
        str(name) for name in demo_cfg.get("payload_classes", ["small", "medium", "large"])
    ]

    rolling_windows = [int(value) for value in cfg.get("features", {}).get("rolling_windows", [30])]
    lags = [int(value) for value in cfg.get("features", {}).get("lags", [1, 2, 3])]
    warmup_steps = max(
        [int(cfg.get("forecast", {}).get("history_window", 30)), 1] + rolling_windows + lags
    )
    generated_steps = selected_steps + warmup_steps + 1
    events = generate_events(
        scenario=selected_scenario,
        steps=generated_steps,
        interval_s=interval_s,
        rate_per_interval=int(demo_cfg.get("rate_per_interval", 120)),
        seed=selected_seed,
        services=services,
        payload_classes=payload_classes,
        burst_multiplier=float(demo_cfg.get("burst_multiplier", 2.5)),
        error_rate=float(demo_cfg.get("error_rate", 0.01)),
    )

    adapter = GenericIngestionAdapter(cfg)
    ingest_records = [dict(event) for event in events]
    if adapter.require_auth:
        token = os.getenv(adapter.token_env)
        if token:
            for record in ingest_records:
                record["auth_token"] = token
    result = adapter.ingest(ingest_records)

    write_schema(target / "ingestion_schema.json")
    _write_jsonl(target / "events.jsonl", events)
    trace = records_to_trace(result, interval_s)
    trace.to_csv(target / "trace.csv", index=False)
    routing = _routing_summary(events)
    pd.DataFrame(routing).to_csv(target / "routing.csv", index=False)

    featured, feature_report = build_features(trace, cfg)
    featured = featured.tail(selected_steps * len(services)).reset_index(drop=True)
    if featured.empty:
        raise RuntimeError("feature engineering removed all demo steps; increase warmup")
    env = ServerlessEnv(featured, cfg)
    policy_path = cfg.get("control", {}).get("rl", {}).get("checkpoint_path")
    policy, policy_source, policy_hash = _load_policy(policy_path, None, cfg)
    loop = _make_loop(cfg, target, "M9", selected_scenario, selected_seed)
    records = run_episode(
        env,
        cfg,
        policy=policy,
        steps=selected_steps,
        use_tft=selected_use_tft,
        tft_checkpoint=cfg.get("forecast", {}).get("checkpoint_path"),
        execute=False,
        loop=loop,
        correlation_prefix=f"m9-{selected_scenario}-{selected_seed}",
    )
    _write_jsonl(target / "decision_records.jsonl", records)
    alerts_path = target / "alerts.jsonl"
    if not alerts_path.exists():
        _write_jsonl(alerts_path, [])
    audit_path = target / "audit.jsonl"
    if not audit_path.exists():
        _write_jsonl(audit_path, [])

    summary = _summary_row("m9_demo", records)
    trace_hash = hashlib.sha256(trace.to_csv(index=False).encode("utf-8")).hexdigest()
    event_hash = hashlib.sha256(
        "".join(json.dumps(event, sort_keys=True) for event in events).encode("utf-8")
    ).hexdigest()
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "config_sha256": _config_hash(cfg),
        "evidence_tier": "simulation_synthetic_client_no_live_execution",
        "scenario": selected_scenario,
        "steps": selected_steps,
        "seed": selected_seed,
        "interval_s": interval_s,
        "warmup_steps": warmup_steps,
        "feature_rows_dropped": int(feature_report["rows_dropped_warmup"]),
        "event_count": len(events),
        "event_sha256": event_hash,
        "trace_sha256": trace_hash,
        "services": services,
        "payload_classes": payload_classes,
        "auth_mode": "required" if adapter.require_auth else "disabled",
        "auth_token_env": adapter.token_env if adapter.require_auth else None,
        "auth_ok": bool(result.auth_ok),
        "tft_requested": selected_use_tft,
        "forecast_actual": records[0].get("forecast_source", "none") if records else "none",
        "policy_source": policy_source,
        "policy_sha256": policy_hash,
        "planner_actual": "stub_proxy",
        "executor": "simulator",
        "live_deployment": False,
        "artifacts": [
            "ingestion_schema.json",
            "events.jsonl",
            "trace.csv",
            "routing.csv",
            "decision.jsonl",
            "decision_records.jsonl",
            "audit.jsonl",
            "feedback.jsonl",
            "alerts.jsonl",
            "figures/demo_timeline.png",
            "report.md",
            "run_manifest.json",
        ],
    }
    _write_figure(trace, records, target / "figures" / "demo_timeline.png")
    _write_json(target / "run_manifest.json", manifest)
    (target / "report.md").write_text(_report(manifest, summary, routing), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the M9 synthetic end-to-end demonstration")
    parser.add_argument("--config", default="configs/project.yaml")
    parser.add_argument("--out-dir", default=None)
    parser.add_argument("--steps", type=int, default=None)
    parser.add_argument("--scenario", default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--use-tft", action="store_true", default=None)
    args = parser.parse_args()

    config = load_config(args.config)
    out_dir = args.out_dir or config.get("demo", {}).get("out_dir", "results/demo/m9")
    manifest = run_demo(
        config,
        out_dir,
        steps=args.steps,
        scenario=args.scenario,
        seed=args.seed,
        use_tft=args.use_tft,
    )
    print(json.dumps({"out_dir": out_dir, "event_count": manifest["event_count"]}, indent=2))


if __name__ == "__main__":
    main()
