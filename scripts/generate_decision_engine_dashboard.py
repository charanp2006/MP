from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from scripts.generate_component_dashboards import EXTRA_STYLE, _fmt, _json_block, _page
from scripts.generate_forecast_dashboard import MODEL_LABELS, STYLE, _card, _esc, _table

UNIFIED_STYLE = """
<style>
.flow { display:flex; flex-wrap:wrap; align-items:stretch; gap:8px; margin:18px 0; }
.stage { flex:1 1 170px; border:1px solid var(--line); border-radius:12px; padding:12px; background:#0e131a; min-width:165px; }
.stage b { display:block; color:var(--fg); margin-bottom:6px; }
.stage span { display:block; color:var(--muted); font-size:.86rem; line-height:1.4; }
.stage em { display:inline-block; margin-top:8px; font-style:normal; font-size:.72rem; color:#7dd3fc; border:1px solid #164e63; border-radius:999px; padding:2px 8px; }
.arrow { align-self:center; color:var(--muted); font-size:1.3rem; }
.pill { display:inline-block; border:1px solid var(--line); border-radius:999px; padding:2px 9px; margin:2px; font-size:.78rem; color:var(--muted); }
.ok { color:#86efac; }
.bad { color:#fca5a5; }
.warn { color:#fcd34d; }
.timeline li { margin-bottom:9px; }
</style>
"""


def _flow(stages: list[tuple[str, str, str]]) -> str:
    parts = []
    for index, (title, detail, tag) in enumerate(stages):
        parts.append(
            f'<div class="stage"><b>{index + 1}. {_esc(title)}</b>'
            f"<span>{detail}</span><em>{_esc(tag)}</em></div>"
        )
        if index < len(stages) - 1:
            parts.append('<div class="arrow">&rarr;</div>')
    return f'<div class="flow">{"".join(parts)}</div>'


def _status(value: str) -> str:
    text = value.replace("_", " ")
    if text == "ok":
        return '<span class="ok">ok</span>'
    if "degraded" in text or "not run" in text or "stub" in text:
        return f'<span class="bad">{_esc(text)}</span>'
    return _esc(text)


def build_dashboard(
    forecast: dict,
    planner_stub: dict,
    planner_ollama: dict,
    ppo_summary: dict,
    ppo_manifest: dict,
    m8_aggregates: list[dict],
    m8_manifest: dict,
    config: dict,
    forecast_prefix: str,
    ppo_prefix: str,
    m8_prefix: str,
) -> str:
    sla = config.get("sla", {})
    containers = config.get("containers", {})
    forecast_cfg = config.get("forecast", {})
    control_cfg = config.get("control", {})
    agent_cfg = config.get("agent", {})
    execution_cfg = config.get("execution", {})
    monitoring_cfg = config.get("monitoring", {})

    forecast_models = forecast["models"]
    forecast_data = forecast["data"]
    tft_overall = forecast_models["tft"]["overall"]
    stub_summary = planner_stub["summary"]
    ollama_summary = planner_ollama["summary"]
    ppo_rows = ppo_summary["aggregate"]

    role_rows = [
        [
            "TFT workload forecaster",
            "What workload is likely to arrive next?",
            "Trained compact Transformer over historical invocation windows",
            f"history {forecast_data['history']} &rarr; horizon {forecast_data['horizon']}",
            "<span class='ok'>trained / offline tested</span>",
        ],
        [
            "Qwen3 planner",
            "What high-level strategy should be considered?",
            "Prompted LLM adapter with deterministic stub fallback; no fine-tuning",
            "StateSnapshot &rarr; strict Plan",
            "<span class='bad'>adapter only / real inference unavailable</span>",
        ],
        [
            "PPO controller",
            "What bounded action should be taken this cycle?",
            "Actor-critic trained by clipped PPO in the simulator",
            "float32[10] &rarr; action id 0-5",
            "<span class='warn'>smoke-trained / simulated</span>",
        ],
    ]

    learning_rows = [
        [
            "TFT",
            "Yes",
            "Azure Functions 2019 invocation windows",
            "8 epochs, chronological split, seed 42",
            "No online training in the loop",
        ],
        [
            "Qwen3",
            "No",
            "External model; no weights stored here",
            "Prompt version planner-v2; safety tests only",
            "Fallback to stub on timeout/refusal/invalid JSON",
        ],
        [
            "PPO",
            "Yes (smoke)",
            "Synthetic scenarios + scaled Azure trace segment",
            f"{ppo_manifest['episodes_per_seed']} episodes/seed; 3 seeds",
            "Feedback only biases the decision; it does not retrain the policy",
        ],
    ]

    handoff_rows = [
        ["Forecast &rarr; state", "forecast dict + runtime metrics", "StateSnapshot", "DecisionLoop.decide", "build_state validates/bounds fields"],
        ["State &rarr; planner", "StateSnapshot + untrusted metadata", "Plan", "DecisionLoop._safe_plan", "PlanValidator + stub/NoOp fallback"],
        ["State &rarr; PPO", "normalized obs float32[10]", "action id", "DecisionLoop._select_action", "policy.greedy_action or callable"],
        ["Plan + PPO &rarr; shield", "action, plan, authorized, P95", "final bounded action", "SafetyShield.filter", "ActionValidator + SLAGuard"],
        ["Final action &rarr; environment/executor", "action id + state + plan", "step outcome or dry-run result", "ServerlessEnv.step / Executor", "execution.enabled=false by default"],
        ["Outcome &rarr; monitoring", "reward, SLA, energy proxy, cold starts", "feedback/alerts/audit records", "FeedbackLoop + AlertManager + DecisionLogger", "append-only telemetry"],
    ]

    cycle_steps = [
        "run_episode chooses a forecast: TFT checkpoint when available, otherwise persistence fallback.",
        "The simulator exposes runtime metrics and a normalized observation vector.",
        "build_state merges forecast + metrics into a strict StateSnapshot with forecast source metadata.",
        "_safe_plan calls the planner, falls back to stub, then to NoOp if validation still fails.",
        "The planner call record is captured with provider, model, prompt version, status and latency.",
        "_select_action asks PPO for a greedy action id; no policy means NoOp.",
        "_apply_feedback_bias may soften a risky action under caution, but never bypasses validation.",
        "SafetyShield.filter applies ActionValidator and SLAGuard; final action can become NoOp.",
        "Executor is optional and disabled by default; simulator step applies the final action.",
        "Outcome, decision, execution audit, alerts and feedback are logged for the next cycle.",
    ]

    safety_rows = [
        ["Planner output", "Strict Pydantic Plan, extra fields forbidden, allowlisted strategies, bounded capacity change", "agent/schemas.py, agent/validator.py"],
        ["Qwen3 prompt", "No shell/Kubernetes commands, metadata labelled untrusted, secret-like keys redacted", "agent/prompts/planner.txt, agent/prompts/__init__.py"],
        ["PPO output", "Integer action id mapped to six fixed actions; no direct command capability", "rl/environment.py, rl/policy.py"],
        ["SLA guard", f"Blocks ScaleIn/Terminate when P95 &ge; {sla.get('p95_latency_ms', 250) - sla.get('safety_margin_ms', 20)} ms", "orchestrator/sla_guard.py"],
        ["Capacity bounds", f"min {containers.get('min', 2)}, max {containers.get('max', 30)}, change &le; {containers.get('max_change_per_cycle', 5)} per cycle", "configs/project.yaml, validators"],
        ["Execution gate", f"enabled={execution_cfg.get('enabled', False)}, dry_run={execution_cfg.get('dry_run', True)}, allow_live={execution_cfg.get('allow_live', False)}", "orchestrator/executor.py"],
        ["Audit", "Correlation ID links forecast, plan, PPO action, final action, execution and outcome", "orchestrator/decision_log.py"],
    ]

    forecast_result_rows = [
        [
            MODEL_LABELS.get(name, name),
            "Yes" if name == "tft" else "No",
            _fmt(values["overall"].get("wape")),
            _fmt(values["overall"].get("mape")),
            _fmt(values["overall"].get("rmse")),
            _fmt(values["overall"].get("peak_underprediction_rate"), "pct"),
        ]
        for name, values in forecast_models.items()
    ]

    planner_result_rows = [
        ["Validity rate", _fmt(stub_summary["valid_rate"], "pct"), _fmt(ollama_summary["valid_rate"], "pct")],
        ["Fallback rate", _fmt(stub_summary["fallback_rate"], "pct"), _fmt(ollama_summary["fallback_rate"], "pct")],
        ["Mean latency", _fmt(stub_summary["mean_planning_latency_ms"], "ms") + " ms", _fmt(ollama_summary["mean_planning_latency_ms"], "ms") + " ms"],
        ["Strategies", ", ".join(sorted(stub_summary["strategy_counts"])), ", ".join(sorted(ollama_summary["strategy_counts"]))],
        ["Final actions", ", ".join(sorted(stub_summary["final_action_counts"])), ", ".join(sorted(ollama_summary["final_action_counts"]))],
    ]

    ppo_result_rows = [
        [
            row["arm"],
            _fmt(row["mean_reward_mean"]),
            _fmt(row["sla_violation_rate_mean"], "pct"),
            _fmt(row["mean_energy_w_mean"]),
            _fmt(row["mean_capacity_mean"]),
            _fmt(row["mean_cold_starts_mean"]),
        ]
        for row in ppo_rows
    ]

    m8_result_rows = []
    for row in m8_aggregates:
        m8_result_rows.append(
            [
                row["experiment_id"],
                row["forecast"],
                row["planner"],
                row["controller"],
                _fmt(row.get("mean_reward")) if row.get("mean_reward") else "n/a",
                _fmt(row.get("sla_violation_rate"), "pct") if row.get("sla_violation_rate") else "n/a",
                _fmt(row.get("mean_energy_w")) if row.get("mean_energy_w") else "n/a",
                _status(row.get("status", "")),
            ]
        )

    gallery = "".join(
        f'<figure><img src="{_esc(prefix)}/{_esc(name)}" alt="{_esc(caption)}">'
        f"<figcaption>{_esc(caption)}</figcaption></figure>"
        for prefix, name, caption in [
            (forecast_prefix, "actual_vs_predicted.png", "TFT: actual vs predicted"),
            (forecast_prefix, "horizons_side_by_side.png", "TFT: horizon-by-horizon forecasts"),
            (ppo_prefix, "learning_curve.png", "PPO: smoke training curve"),
            (ppo_prefix, "action_frequencies.png", "PPO: action frequencies"),
            (m8_prefix, "mean_reward_by_experiment.png", "M8: reward by ablation arm"),
            (m8_prefix, "sla_violation_rate_by_experiment.png", "M8: SLA violation by ablation arm"),
        ]
    )

    forecast_example = {
        "forecast_horizon": forecast_data["horizon"],
        "predicted_workload": [520.0, 548.0, 571.0, 559.0, 603.0],
        "trend": "increasing",
        "source": "tft",
        "fallback": False,
        "fallback_reason": None,
    }
    plan_example = {
        "strategy": "ScaleOut",
        "desired_capacity_change": 3,
        "priority": "sla",
        "urgency": "high",
        "reason": "P95 is near SLA during forecast burst",
        "constraints_respected": True,
    }
    decision_example = {
        "forecast_source": "tft",
        "planner_role": "advisory",
        "controller_role": "proposal",
        "shield_role": "final_authority",
        "planner_strategy": "ScaleOut",
        "proposed_action": 2,
        "biased_action": 2,
        "final_action": 2,
        "final_action_name": "ScaleOut",
        "guard_code": "ok",
        "action_code": "ok",
        "used_fallback": False,
        "authorized": True,
    }

    body = f"""
<div class="cards">
  {_card("Decision engine", "TFT + Qwen3 + PPO + shield")}
  {_card("Forecast", f"history {forecast_data['history']} / horizon {forecast_data['horizon']}")}
  {_card("Planner", agent_cfg.get('runtime', 'stub') + " runtime")}
  {_card("Controller", f"{len(ppo_manifest['arms'])} evaluation arms")}
  {_card("Control interval", str(control_cfg.get('interval_seconds', 60)) + " s")}
  {_card("SLA", str(sla.get('p95_latency_ms', 250)) + " ms P95")}
  {_card("Execution", "dry-run / disabled by default")}
  {_card("Evidence", "offline + simulated")}
</div>

<h2>1. Executive summary</h2>
<p><strong>There is no single all-powerful AI model in this project.</strong> The decision engine is a set of bounded specialists: TFT predicts near-term workload, Qwen3 proposes a high-level strategy, PPO selects a concrete bounded action, and deterministic validators/shield decide what is actually allowed. The executor only runs an approved, authorized action.</p>
{_table(["Component", "Question it answers", "How it works", "Contract", "Status"], role_rows)}
<p><span class="pill">TFT = perception/forecast</span><span class="pill">Qwen3 = advisory reasoning</span><span class="pill">PPO = bounded control</span><span class="pill">Shield = final authority</span></p>

<h2>2. Closed-loop architecture</h2>
{_flow([
    ("Observe", "Prometheus adapter or simulator metrics: workload, CPU, memory, P95, containers", "Layer 1-3"),
    ("Forecast", "TFT or persistence predicts the next workload window", "TFT"),
    ("Plan", "Qwen3/stub converts state into a high-level Plan", "Qwen3"),
    ("Control", "PPO proposes one of six bounded actions", "PPO"),
    ("Validate", "Plan validator, safety shield, SLA guard, authorization", "Deterministic"),
    ("Act", "Simulator or dry-run executor applies the final action", "Layer 10"),
    ("Learn/Observe", "Feedback, alerts, decision log and outcome feed the next cycle", "Layer 8-11"),
])}
<p>Code path: <code>orchestrator/decision_loop.py:193</code> (<code>DecisionLoop.decide</code>) and <code>orchestrator/decision_loop.py:372</code> (<code>run_episode</code>) wire the full cycle. Every cycle receives a correlation ID and writes a structured decision record.</p>

<h2>3. What each AI component contributes</h2>
<div class="grid2">
<div class="card">
<h3>TFT: workload forecast</h3>
<ul>
<li>Trained on chronological Azure Functions invocation windows; no shuffle.</li>
<li>Input: {forecast_data['history']} observed steps with {len(forecast_data['feature_columns'])} engineered features.</li>
<li>Output: {forecast_data['horizon']} predicted invocation counts, trend and source/fallback metadata.</li>
<li>In the loop, <code>_tft_forecast</code> builds the window and scales predictions; missing/stale/model-error inputs fall back to persistence.</li>
<li>It does not decide capacity and never touches infrastructure.</li>
</ul>
</div>
<div class="card">
<h3>Qwen3: high-level planner</h3>
<ul>
<li>Reads the bounded StateSnapshot and emits a strict JSON Plan.</li>
<li>Strategies: NoOp, PreWarm, ScaleOut, Reuse, ScaleIn, Terminate.</li>
<li>Default runtime is deterministic stub; Ollama adapter exists but real Qwen3 was unavailable.</li>
<li>Plan is advisory and is validated before PPO sees it.</li>
<li>Invalid, timeout, refusal, or unsafe output becomes stub fallback, then NoOp if still invalid.</li>
</ul>
</div>
<div class="card">
<h3>PPO: bounded controller</h3>
<ul>
<li>Actor-critic policy maps a 10-value observation to one of six action IDs.</li>
<li>Reward penalizes energy, latency, cold starts, resources, underutilization, and SLA violations most heavily.</li>
<li>Produces a proposal only; feedback may bias it, but the shield can override it.</li>
<li>Evidence checkpoint is smoke-trained for {ppo_manifest['episodes_per_seed']} episodes/seed, not a converged production policy.</li>
</ul>
</div>
<div class="card">
<h3>Deterministic guardrails</h3>
<ul>
<li><code>PlanValidator</code>: schema, allowlist, direction, bounds and rate limits.</li>
<li><code>ActionValidator</code>: legal/authorized/plan-consistent action.</li>
<li><code>SLAGuard</code>: blocks risky scale-in/terminate near the SLA.</li>
<li><code>SafetyShield</code>: combines validator + guard and has final authority.</li>
<li><code>Executor</code>: disabled by default; no AI component can call it directly.</li>
</ul>
</div>
</div>

<h2>4. How the components hand off data</h2>
{_table(["Handoff", "Input", "Output", "Consumer", "Guard / boundary"], handoff_rows)}
<h3>TFT output example</h3>
{_json_block(forecast_example)}
<h3>Qwen3/Planner output example</h3>
{_json_block(plan_example)}
<h3>Final hierarchy record example</h3>
{_json_block(decision_example)}

<h2>5. One decision cycle, step by step</h2>
<ol class="timeline">
{''.join(f'<li>{_esc(step)}</li>' for step in cycle_steps)}
</ol>
<p><strong>Hierarchy recorded by the code:</strong> planner is <code>advisory</code>, controller is <code>proposal</code>, shield is <code>final_authority</code>. This is the key design decision that keeps the AI components from directly controlling infrastructure.</p>

<h2>6. Learning and adaptation status</h2>
{_table(["Component", "Learned weights?", "Evidence source", "Training / setup", "Adaptation in runtime"], learning_rows)}
<p class="note"><strong>Feedback is not online training.</strong> <code>FeedbackLoop.signal()</code> produces a caution signal used by <code>_apply_feedback_bias</code>; it may change a proposal from ScaleIn/Terminate to PreWarm/ScaleOut, but it does not update TFT, Qwen3, or PPO weights during the loop.</p>

<h2>7. Safety and governance</h2>
{_table(["Boundary", "Rule", "Implementation"], safety_rows)}
<p>No component can emit arbitrary shell/Kubernetes commands. Planner metadata is treated as untrusted, telemetry is redacted, and execution remains gated by config plus authorization.</p>

<h2>8. Evidence: component results</h2>
<h3>8.1 TFT forecast accuracy (offline test set)</h3>
{_table(["Model", "Trained?", "WAPE", "MAPE", "RMSE", "Peak underprediction"], forecast_result_rows)}
<p>TFT is the trained forecaster; the other rows are deterministic baselines on the same chronological test rows. Azure supplies invocation counts only; latency/energy are simulated elsewhere.</p>

<h3>8.2 Qwen3 planner harness</h3>
{_table(["Metric", "Stub runtime", "Ollama runtime"], planner_result_rows)}
<p class="bad">The Ollama rows are fallback behavior: real Qwen3 inference was unavailable. Do not interpret them as Qwen3 planning quality.</p>

<h3>8.3 PPO controller evaluation (simulation)</h3>
{_table(["Arm", "Reward", "SLA violation", "Energy proxy", "Capacity", "Cold starts"], ppo_result_rows)}
<p class="warn">The PPO arm is NoOp-like after the smoke training run. Rule/reactive arms reduce simulated SLA violations by using more capacity and energy.</p>

<h3>8.4 Consolidated E0-E7 ablation smoke</h3>
{_table(["ID", "Forecast", "Planner", "Controller", "Reward", "SLA", "Energy", "Status"], m8_result_rows)}
<p>M8 smoke used one seed, four steps, mixed workload and <code>--no-tft</code>. E2/E3/E5/E6 are degraded TFT fallbacks; E3/E6 are stub proxies; E7 is deferred until a live cluster exists.</p>

<h2>9. Generated evidence plots</h2>
<div class="gallery">{gallery}</div>

<h2>10. Illustrative burst walkthrough</h2>
<p class="note">Illustrative values only — this is an explanation of the data path, not a measured experiment result.</p>
{_flow([
    ("Forecast", "P95 near SLA; predicted workload rises from 760 to 1040 over 5 steps", "TFT or persistence"),
    ("State", "forecast_peak=1040, current=760, p95=238 ms, containers=12", "StateSnapshot"),
    ("Plan", "ScaleOut +3, priority=sla, urgency=high", "Qwen3/stub proposal"),
    ("PPO", "greedy_action(obs) = 2", "ScaleOut proposal"),
    ("Shield", "ScaleOut allowed; SLA guard only blocks risky scale-down", "final action = ScaleOut"),
    ("Outcome", "Simulator applies action; reward/SLA/energy/cold starts are logged", "next cycle feedback"),
])}

<h2>11. What is implemented vs not validated</h2>
{_table(["Implemented and tested", "Not validated / deferred"], [
    ["Data pipeline, chronological splits and Azure trace preprocessing", "Live Prometheus scrape backed by deployed functions"],
    ["TFT training/evaluation and forecast service with fallback", "Live Grafana decisions from real system metrics"],
    ["Qwen3 adapter, stub, fallback, prompt bounding and telemetry", "Real Qwen3 model quality or latency"],
    ["PPO environment, reward, training path, checkpoint and shield", "Long multi-seed PPO convergence result"],
    ["Decision loop, validators, audit, feedback and alerts", "Live Kubernetes/OpenFaaS/Docker execution"],
    ["M0-M9 simulated/dry-run integration", "E7 live evaluation and measured energy/cold starts"],
])}

<h2>12. Reproduce the whole path</h2>
<pre>py -m scripts.evaluate_forecast --data-source azure_functions_2019 --out-dir results/forecast/azure2019_total --run-id azure2019_total_h30_h5 --epochs 8
py -m scripts.evaluate_planner --runtime stub --out-dir results/planner/stub
py -m experiments.evaluate_ppo_m5 --out-dir results/ppo/m5
py -m orchestrator.decision_loop --steps 8 --policy checkpoint --use-tft
py -m experiments.evaluate_m8 --out-dir results/evaluation/m8 --seeds 42 --steps 4 --scenarios mixed
py -m scripts.generate_decision_engine_dashboard</pre>
<p>Related detailed dashboards: <a href="forecasting-dashboard.html">TFT forecast dashboard</a>, <a href="agentic-planning-dashboard.html">Qwen3 planner dashboard</a>, <a href="ppo-controller-dashboard.html">PPO controller dashboard</a>.</p>
"""
    return _page(
        "AI-Driven Decision Engine Dashboard",
        "TFT + Qwen3 + PPO in one bounded control loop &middot; implementation, evidence and live-use boundary",
        body,
        extra_style=EXTRA_STYLE + UNIFIED_STYLE,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the unified AI decision engine dashboard")
    parser.add_argument("--config", default="configs/project.yaml")
    parser.add_argument("--forecast", default="results/forecast/azure2019_total/metrics.json")
    parser.add_argument("--planner-stub", default="results/planner/stub/planner_evaluation.json")
    parser.add_argument("--planner-ollama", default="results/planner/ollama/planner_evaluation.json")
    parser.add_argument("--ppo-summary", default="results/ppo/m5/summary.json")
    parser.add_argument("--ppo-manifest", default="results/ppo/m5/run_manifest.json")
    parser.add_argument("--m8-aggregates", default="results/evaluation/m8/aggregates.csv")
    parser.add_argument("--m8-manifest", default="results/evaluation/m8/run_manifest.json")
    parser.add_argument("--out", default="docs/ai-driven-decision-engine-dashboard.html")
    parser.add_argument("--forecast-image-prefix", default="../results/forecast/azure2019_total/plots")
    parser.add_argument("--ppo-image-prefix", default="../results/ppo/m5/plots")
    parser.add_argument("--m8-image-prefix", default="../results/evaluation/m8/figures")
    args = parser.parse_args()

    from configs import load_config

    config = load_config(args.config)
    forecast = json.loads(Path(args.forecast).read_text(encoding="utf-8"))
    planner_stub = json.loads(Path(args.planner_stub).read_text(encoding="utf-8"))
    planner_ollama = json.loads(Path(args.planner_ollama).read_text(encoding="utf-8"))
    ppo_summary = json.loads(Path(args.ppo_summary).read_text(encoding="utf-8"))
    ppo_manifest = json.loads(Path(args.ppo_manifest).read_text(encoding="utf-8"))
    m8_manifest = json.loads(Path(args.m8_manifest).read_text(encoding="utf-8"))
    with Path(args.m8_aggregates).open(encoding="utf-8", newline="") as handle:
        m8_aggregates = list(csv.DictReader(handle))

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        build_dashboard(
            forecast,
            planner_stub,
            planner_ollama,
            ppo_summary,
            ppo_manifest,
            m8_aggregates,
            m8_manifest,
            config,
            args.forecast_image_prefix,
            args.ppo_image_prefix,
            args.m8_image_prefix,
        ),
        encoding="utf-8",
    )
    print(output)


if __name__ == "__main__":
    main()
