from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from agent.schemas import Plan, StateSnapshot, STRATEGIES
from configs import load_config
from rl.environment import ACTIONS, OBS_NAMES
from scripts.generate_forecast_dashboard import STYLE, _card, _esc, _table

EXTRA_STYLE = """
<style>
.bar { background:#0a0d12; border:1px solid var(--line); border-radius:999px; height:10px; overflow:hidden; min-width:180px; }
.bar > i { display:block; height:100%; background:linear-gradient(90deg,#38bdf8,#86efac); }
.bar.warn > i { background:linear-gradient(90deg,#fbbf24,#f87171); }
.barcell { display:flex; align-items:center; gap:10px; }
.note { border-left:3px solid var(--warn); padding-left:12px; }
.code-small { font-size:.82rem; }
</style>
"""


def _fmt(value, kind: str = "num") -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float) and math.isnan(value):
        return "n/a"
    number = float(value)
    if kind == "pct":
        return f"{number * 100:.2f}%"
    if kind == "pct_value":
        return f"{number:.2f}%"
    if kind == "int":
        return f"{int(number):,}"
    if kind == "ms":
        return f"{number:,.2f}"
    return f"{number:.4f}"


def _counts(values: dict) -> str:
    return ", ".join(f"{key}={value}" for key, value in sorted(values.items()))


def _bar(label: str, value: float, maximum: float, warn: bool = False) -> list[str]:
    width = 0.0 if maximum <= 0 else max(2.0, min(100.0, value / maximum * 100.0))
    cls = "bar warn" if warn else "bar"
    return [label, f'<div class="barcell"><div class="{cls}"><i style="width:{width:.1f}%"></i></div><span>{_fmt(value)}</span></div>']


def _json_block(payload: dict) -> str:
    rendered = json.dumps(payload, indent=2, default=str)
    return f"<pre class=\"code-small\">{_esc(rendered)}</pre>"


def _page(title: str, subtitle: str, body: str, extra_style: str = EXTRA_STYLE) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(title)}</title>
{STYLE}
{extra_style}
</head>
<body>
<div class="wrap">
<h1>{_esc(title)}</h1>
<p class="sub">{subtitle}</p>
{body}
<div class="footer">Generated from tracked code and saved experiment artifacts. All runtime diagrams describe contracts, not validated live deployments.</div>
</div>
</body>
</html>
"""


def build_planner_dashboard(stub: dict, ollama: dict, config: dict) -> str:
    stub_summary = stub["summary"]
    ollama_summary = ollama["summary"]
    agent_cfg = config.get("agent", {})
    sla_cfg = config.get("sla", {})
    container_cfg = config.get("containers", {})
    state_fields = [
        [name, str(field.annotation), str(field.description or "bounded state value")]
        for name, field in StateSnapshot.model_fields.items()
    ]
    plan_fields = [
        [name, str(field.annotation), str(field.description or "validated plan value")]
        for name, field in Plan.model_fields.items()
    ]
    scenario_rows = []
    for stub_row, ollama_row in zip(stub["rows"], ollama["rows"]):
        scenario_rows.append(
            [
                stub_row["scenario"],
                stub_row["status"],
                stub_row["strategy"],
                _fmt(stub_row["capacity_change"], "int"),
                stub_row["validation_code"],
                stub_row["final_action"],
                ollama_row["status"],
                _fmt(ollama_row["latency_ms"], "ms"),
            ]
        )
    latency_max = max(ollama_summary["mean_planning_latency_ms"], 1.0)
    summary_rows = [
        ["Runtime", "Stub", "Ollama adapter"],
        ["Scenarios", _fmt(stub_summary["scenarios"], "int"), _fmt(ollama_summary["scenarios"], "int")],
        ["Plan validity rate", _fmt(stub_summary["valid_rate"], "pct"), _fmt(ollama_summary["valid_rate"], "pct")],
        ["Fallback rate", _fmt(stub_summary["fallback_rate"], "pct"), _fmt(ollama_summary["fallback_rate"], "pct")],
        ["Mean planning latency", _fmt(stub_summary["mean_planning_latency_ms"], "ms") + " ms", _fmt(ollama_summary["mean_planning_latency_ms"], "ms") + " ms"],
        ["P95 planning latency", _fmt(stub_summary["p95_planning_latency_ms"], "ms") + " ms", _fmt(ollama_summary["p95_planning_latency_ms"], "ms") + " ms"],
        ["Providers", _counts(stub_summary["provider_counts"]), _counts(ollama_summary["provider_counts"])],
        ["Statuses", _counts(stub_summary["status_counts"]), _counts(ollama_summary["status_counts"])],
        ["Strategies", _counts(stub_summary["strategy_counts"]), _counts(ollama_summary["strategy_counts"])],
        ["Final actions", _counts(stub_summary["final_action_counts"]), _counts(ollama_summary["final_action_counts"])],
    ]
    example_input = {
        "forecast_workload": 820.0,
        "forecast_peak": 1040.0,
        "current_workload": 760.0,
        "trend": "increasing",
        "cpu_utilization": 0.81,
        "memory_utilization": 0.74,
        "active_containers": 12,
        "warm_containers": 8,
        "p95_latency_ms": 238.0,
        "cold_start_rate": 0.08,
        "energy": 180.0,
        "sla_threshold_ms": sla_cfg.get("p95_latency_ms", 250),
        "sla_margin_ms": sla_cfg.get("safety_margin_ms", 20),
        "forecast_horizon": config.get("forecast", {}).get("horizon", 5),
        "metadata": {"source": "synthetic_client", "scenario": "burst"},
    }
    example_output = {
        "strategy": "ScaleOut",
        "desired_capacity_change": 3,
        "priority": "sla",
        "urgency": "high",
        "reason": "P95 is near the SLA during a forecast burst",
        "constraints_respected": True,
    }
    example_telemetry = {
        "provider": "ollama",
        "model": agent_cfg.get("model", "qwen3:4b"),
        "prompt_version": agent_cfg.get("prompt_version", "planner-v2"),
        "status": "fallback",
        "latency_ms": 4018.56,
        "fallback": True,
        "reason": "timeout: ollama unavailable",
        "strategy": "ScaleOut",
        "plan_code": "ok",
    }

    body = f"""
<div class="cards">
  {_card("Status", "adapter implemented; real Qwen3 unavailable")}
  {_card("Default runtime", agent_cfg.get('runtime', 'stub'))}
  {_card("Configured model", agent_cfg.get('model', 'qwen3:4b'))}
  {_card("Prompt version", agent_cfg.get('prompt_version', 'planner-v2'))}
  {_card("Allowed strategies", len(STRATEGIES))}
  {_card("Offline scenarios", ollama_summary['scenarios'])}
</div>

<h2>1. What it does</h2>
<p>The planner is an <strong>advisory component</strong>. It reads a bounded forecast/state snapshot and returns one high-level strategy. It never emits shell commands, Kubernetes YAML, URLs, scripts, or direct infrastructure actions. The final action is chosen later by PPO plus the safety shield.</p>
<p><strong>Control-flow:</strong> TFT/persistence forecast &rarr; <code>build_state</code> &rarr; planner proposal &rarr; <code>PlanValidator</code> &rarr; PPO/feedback bias &rarr; <code>SafetyShield</code> &rarr; executor adapter. Planner output is advisory only.</p>

<h2>2. How it is implemented</h2>
{_table(["Module", "Role"], [
    ["agent/schemas.py", "Strict StateSnapshot and Plan models; extra fields rejected"],
    ["agent/planner.py", "StubPlanner, Qwen3OllamaPlanner, FallbackPlanner, build_planner"],
    ["agent/prompts/planner.txt", "System prompt: allowlist, SLA rule, untrusted metadata, NoOp fallback"],
    ["agent/prompts/__init__.py", "Bounded/redacted prompt construction with planner-v2 version"],
    ["agent/validator.py", "Schema, allowlist, bounds, rate-limit, direction and capacity checks"],
    ["agent/telemetry.py", "Redacted provider/model/status/latency/fallback call records"],
    ["orchestrator/decision_loop.py", "Captures planner telemetry and converts validated plans into PPO context"],
])}

<h2>3. Training / testing status</h2>
<p class="note"><strong>No training was performed.</strong> Qwen3 is an external LLM accessed through a provider adapter; there is no fine-tuning, local checkpoint, or learned planner weights in this repository. Real Qwen3/Ollama inference was unavailable during the recorded experiments, so the Ollama artifacts measure timeout fallback behavior only.</p>
{_table(["Check", "Status / evidence"], [
    ["Qwen3 provider adapter", "Implemented: POST to Ollama /api/chat, strict Plan.model_validate"],
    ["Real Qwen3 inference", "Not validated; Ollama evaluation fallback_rate = 100%"],
    ["Prompt-injection tests", "Q05 string treated as untrusted metadata"],
    ["Invalid/unsafe plan tests", "Q01/Q02/Q06 plus excessive scale-in rejection"],
    ["Timeout/refusal fallback", "FallbackPlanner + DecisionLoop._safe_plan + validate_or_noop"],
    ["Telemetry", "Provider, model, prompt version, status, latency, fallback and redacted reason"],
    ["Component milestone suite", "M3 recorded 127 passed, 1 warning"],
])}

<h2>4. Input contract</h2>
<p>The planner consumes a strict <code>StateSnapshot</code>. Unknown fields are rejected. Numeric fields are bounded; metadata is treated as untrusted data.</p>
{_table(["Field", "Type", "Meaning"], state_fields)}
{_json_block(example_input)}

<h2>5. Output contract</h2>
<p>The planner returns exactly one <code>Plan</code> object. Extra fields are forbidden, the strategy must be one of <code>{_esc(', '.join(STRATEGIES))}</code>, and the reason is capped at 500 characters.</p>
{_table(["Field", "Type", "Meaning"], plan_fields)}
{_json_block(example_output)}
<p><strong>Telemetry example</strong> recorded with each call:</p>
{_json_block(example_telemetry)}

<h2>6. Validation and safety</h2>
<ul>
<li><code>PlanValidator</code> checks schema, strategy allowlist, desired change bounds, capacity bounds, direction, max change per cycle, and SLA-safe reductions.</li>
<li>Capacity bounds from config: min <code>{container_cfg.get('min', 2)}</code>, max <code>{container_cfg.get('max', 30)}</code>, max change/cycle <code>{container_cfg.get('max_change_per_cycle', 5)}</code>.</li>
<li>SLA threshold <code>{sla_cfg.get('p95_latency_ms', 250)} ms</code>, margin <code>{sla_cfg.get('safety_margin_ms', 20)} ms</code>.</li>
<li>Prompt instructs refusal/NoOp for unsafe or incomplete input; malformed output triggers deterministic fallback.</li>
<li>No planner output can bypass PPO/action validation/SLA guard/authorization.</li>
</ul>

<h2>7. Offline evaluation results</h2>
{_table(["Metric", "Stub runtime", "Ollama runtime"], summary_rows)}
<h3>Fallback and latency comparison</h3>
{_table(["Measure", "Relative bar"], [
    _bar("Stub fallback rate", stub_summary["fallback_rate"], 1.0),
    _bar("Ollama fallback rate", ollama_summary["fallback_rate"], 1.0, warn=True),
    _bar("Stub mean latency (ms)", stub_summary["mean_planning_latency_ms"], latency_max),
    _bar("Ollama mean latency (ms)", ollama_summary["mean_planning_latency_ms"], latency_max, warn=True),
])}
<h3>Per-scenario outcomes</h3>
{_table(["Scenario", "Stub status", "Strategy", "Capacity change", "Validation", "Final action", "Ollama status", "Ollama latency (ms)"], scenario_rows)}
<p class="warn">Interpretation: the stub planner passes the offline safety harness. The Ollama run used fallback plans for all six scenarios; these numbers do not measure Qwen3 planning quality.</p>

<h2>8. Live-use boundary</h2>
<ul>
<li>A live deployment can set <code>agent.runtime: ollama</code> and point <code>base_url</code> to a real provider, but that path was not validated here.</li>
<li>The planner receives no cluster credentials and has no executor path.</li>
<li>Execution defaults remain <code>enabled=false</code>, <code>dry_run=true</code>, <code>allow_live=false</code>.</li>
<li>M8 rows E3 and E6 are labelled <code>stub_proxy</code>, not real Qwen3 results.</li>
</ul>

<h2>9. Limitations</h2>
<ul>
<li>Real Qwen3 quality, latency, token usage, and model-version behavior are unmeasured.</li>
<li>The six offline states are hand-designed safety scenarios, not production workload evidence.</li>
<li>All final actions in the planner harness are NoOp because no PPO policy was supplied.</li>
<li>No live Kubernetes/OpenFaaS execution, Prometheus/Grafana telemetry, or measured energy/cold-start outcomes are claimed.</li>
</ul>

<h2>10. Reproduce</h2>
<pre>py -m pytest -q tests/test_agent.py tests/test_agent_m4.py tests/test_orchestrator.py
py -m scripts.evaluate_planner --runtime stub --out-dir results/planner/stub
py -m scripts.evaluate_planner --runtime ollama --timeout-s 2 --out-dir results/planner/ollama
py -m scripts.generate_component_dashboards</pre>
"""
    return _page("Agentic AI Planning (Qwen3) Dashboard", "Offline hardening dashboard &middot; adapter implemented, no trained planner, no validated live Qwen3 inference", body)


def build_ppo_dashboard(summary: dict, manifest: dict, config: dict, image_prefix: str) -> str:
    rl_cfg = config.get("control", {}).get("rl", {})
    weights = rl_cfg.get("reward_weights", {})
    training_cfg = rl_cfg.get("training", {})
    aggregate = summary["aggregate"]
    rows = summary["rows"]
    aggregate_rows = []
    for row in aggregate:
        arm = row["arm"]
        n = sum(1 for item in rows if item.get("arm") == arm)
        aggregate_rows.append(
            [
                arm,
                _fmt(n, "int"),
                _fmt(row["mean_reward_mean"]),
                _fmt(row["sla_violation_rate_mean"], "pct"),
                _fmt(row["mean_energy_w_mean"], "ms"),
                _fmt(row["mean_capacity_mean"], "ms"),
                _fmt(row["mean_cold_starts_mean"], "ms"),
                _fmt(row["mean_p95_latency_ms_mean"], "ms"),
                _fmt(row["shield_intervention_rate_mean"], "pct"),
            ]
        )
    obs_rows = [[str(index), name] for index, name in enumerate(OBS_NAMES)]
    action_rows = [[str(index), name] for index, name in enumerate(ACTIONS)]
    weight_rows = [[name, _fmt(value), "highest penalty" if name == "sla_violation" else ""] for name, value in weights.items()]
    plots = [
        ("learning_curve.png", "PPO learning curve"),
        ("timeline.png", "Workload / capacity timeline"),
        ("action_frequencies.png", "Action frequency distribution"),
    ]
    gallery = "".join(
        f'<figure><img src="{_esc(image_prefix)}/{_esc(filename)}" alt="{_esc(caption)}">'
        f"<figcaption>{_esc(caption)}</figcaption></figure>"
        for filename, caption in plots
    )
    example_obs = {
        name: round(0.4 + index * 0.05, 3) for index, name in enumerate(OBS_NAMES)
    }
    example_action = {
        "greedy_action": 2,
        "action_name": ACTIONS[2],
        "after_shield": {"action": ACTIONS[2], "allowed": True, "reason_code": "ok"},
        "step_result": {
            "obs": "float32[10]",
            "reward": -0.8421,
            "done": False,
            "info": {
                "action": "ScaleOut",
                "capacity": 8,
                "p95_latency_ms": 132.5,
                "sla_violated": False,
                "reward_components": {"energy": -0.12, "latency": -0.08, "sla_violation": 0.0},
            },
        },
    }

    body = f"""
<div class="cards">
  {_card("Controller", "PPO actor-critic")}
  {_card("Training evidence", f"{manifest['episodes_per_seed']} episodes/seed (smoke)")}
  {_card("Configured episodes", training_cfg.get('episodes', 200))}
  {_card("Observation dim", len(OBS_NAMES))}
  {_card("Action set", len(ACTIONS))}
  {_card("Evidence commit", manifest.get('git_commit', 'unknown'))}
</div>

<h2>1. What it does</h2>
<p>PPO selects a bounded container-management action from a fixed six-action set. It consumes a normalized state vector built from forecast, current workload, resource metrics, latency/SLA, cold starts, energy proxy, and recent history. It does not execute infrastructure commands; its proposal passes through the safety shield before any simulator or executor step.</p>
<p><strong>Control-flow:</strong> validated state &rarr; PPO <code>greedy_action</code> &rarr; feedback bias &rarr; <code>SafetyShield</code> &rarr; simulator/dry-run/live executor. PPO is a proposal role; the shield has final authority.</p>

<h2>2. How it is implemented</h2>
{_table(["Module", "Role"], [
    ["rl/environment.py", "Deterministic serverless simulator, lifecycle delay, capacity bounds, observation and step dynamics"],
    ["rl/reward.py", "SLA-aware normalized reward with energy, latency, cold-start, resource, underutilization and scaling terms"],
    ["rl/policy.py", "ActorCritic network with act, evaluate and greedy_action"],
    ["rl/train_ppo.py", "GAE, clipped PPO updates, best-state tracking, versioned checkpoint save/load"],
    ["rl/evaluate_ppo.py", "Policy and reactive evaluation helpers"],
    ["experiments/synthetic_scenarios.py", "ramp, burst, periodic, sparse, stress and mixed workloads"],
    ["orchestrator/safety_shield.py", "ActionValidator + SLAGuard; blocks unsafe actions to NoOp"],
])}

<h2>3. How it was trained</h2>
<p><strong>Trained, but smoke-level.</strong> The saved run manifest records <code>{manifest['episodes_per_seed']}</code> episodes per seed for seeds <code>{manifest['seeds']}</code>, not the configured <code>{training_cfg.get('episodes', 200)}</code> episodes. This is enough to test the training/checkpoint path, not enough to claim converged or superior control.</p>
{_table(["Training item", "Configured / evidence"], [
    ["Algorithm", "PPO with actor-critic and clipped surrogate objective"],
    ["Evidence episodes/seed", manifest['episodes_per_seed']],
    ["Seeds", ", ".join(str(value) for value in manifest['seeds'])],
    ["Batch size", training_cfg.get('batch_size', 64)],
    ["Learning rate", training_cfg.get('learning_rate', 0.0003)],
    ["Gamma", training_cfg.get('gamma', 0.99)],
    ["GAE lambda", training_cfg.get('gae_lambda', 0.95)],
    ["Clip ratio", training_cfg.get('clip_ratio', 0.2)],
    ["Epochs per update", training_cfg.get('epochs_per_update', 4)],
    ["Minibatch size", training_cfg.get('minibatch_size', 64)],
    ["Entropy coefficient", training_cfg.get('entropy_coeff', 0.01)],
    ["Config SHA-256", manifest.get('config_sha256', 'unknown')],
    ["Checkpoint", config.get('control', {}).get('rl', {}).get('checkpoint_path', 'models/ppo_policy.pt')],
])}
<p>Training keeps the best validation state by mean episode reward and saves a versioned checkpoint with model state, observation dimension, action count, seed, episode count and reward weights. Loading rejects newer checkpoint versions and shape mismatches.</p>

<h2>4. How it was tested</h2>
<p>Evaluation used <code>{manifest['scenario_steps']}</code>-step synthetic scenarios with a 70/30 chronological split and {_fmt(summary['aggregate'][0]['steps_mean'], 'int')}-step test rollouts, plus a held-out Azure trace segment. All reward, latency, energy, cold-start and capacity values are simulated proxies.</p>
{_table(["Test item", "Evidence"], [
    ["Synthetic scenarios", ", ".join(manifest['scenarios'])],
    ["Seeds", ", ".join(str(value) for value in manifest['seeds'])],
    ["Arms", ", ".join(manifest['arms'])],
    ["Trace inputs", manifest.get('trace_csv', 'n/a')],
    ["TFT path", f"attempted={manifest.get('tft', {}).get('attempted')}, available={manifest.get('tft', {}).get('available')}"],
    ["Resource columns", manifest.get('trace_resource_columns', 'n/a')],
    ["Trace scale factor", _fmt(manifest.get('trace_workload_scale_factor'))],
    ["Component suite", "M4 recorded 134 passed, 1 warning"],
])}

<h2>5. Input contract</h2>
<p>The policy input is a bounded normalized <code>float32[{len(OBS_NAMES)}]</code> observation. Names come directly from <code>rl.environment.OBS_NAMES</code>.</p>
{_table(["Index", "Observation feature"], obs_rows)}
{_json_block(example_obs)}

<h2>6. Output contract</h2>
<p>The controller returns one integer action ID. The environment maps it to a named action and returns <code>(obs, reward, done, info)</code>.</p>
{_table(["Action ID", "Meaning"], action_rows)}
{_json_block(example_action)}

<h2>7. Reward and safety</h2>
{_table(["Reward component", "Weight", "Note"], weight_rows)}
<ul>
<li><code>ActionValidator</code> checks legal action IDs, authorization, plan conflicts and capacity bounds.</li>
<li><code>SLAGuard</code> blocks ScaleIn/Terminate when P95 is near the SLA threshold.</li>
<li><code>SafetyShield.filter</code> converts any block into NoOp with a reason code.</li>
<li>Capacity is clamped to min <code>{config.get('containers', {}).get('min', 2)}</code>, max <code>{config.get('containers', {}).get('max', 30)}</code>, max change/cycle <code>{config.get('containers', {}).get('max_change_per_cycle', 5)}</code>.</li>
</ul>

<h2>8. Simulated evaluation results</h2>
{_table(["Arm", "N", "Reward", "SLA viol.", "Energy W proxy", "Capacity", "Cold starts", "P95 ms proxy", "Shield"], aggregate_rows)}
<p class="warn">Interpretation: with only three training episodes, <code>ppo_shielded</code> has the same reward/SLA/energy/capacity values as <code>fixed_noop</code>. This is a NoOp-like smoke policy, not evidence of superior control. Rule/reactive arms reduce simulated SLA violations by provisioning more capacity at higher simulated energy/cold-start cost.</p>
<div class="gallery">{gallery}</div>

<h2>9. Live-use boundary</h2>
<ul>
<li>PPO never forms shell/Kubernetes/OpenFaaS/Docker commands.</li>
<li>Only the executor adapter can form bounded commands after shield approval.</li>
<li>Execution defaults remain <code>enabled=false</code>, <code>dry_run=true</code>, <code>allow_live=false</code>.</li>
<li>Live latency, real hardware energy, real cold starts and deployed feedback were not measured.</li>
</ul>

<h2>10. Limitations</h2>
<ul>
<li>Training was deliberately short; no 200-episode production run is evidenced.</li>
<li>Latency, energy, cold-start and capacity outcomes come from simulator proxies, not live infrastructure.</li>
<li>The Azure segment was scaled for simulator capacity; trace TFT/persistence rows are single-segment observations.</li>
<li>No confidence interval over many long training runs is available for PPO itself.</li>
<li>M8 PPO arms are consolidated simulation results and do not validate live execution (E7 deferred).</li>
</ul>

<h2>11. Reproduce</h2>
<pre>py -m pytest -q tests/test_rl.py tests/test_m5.py tests/test_orchestrator.py
py -m experiments.evaluate_ppo_m5 --out-dir results/ppo/m5
py -m scripts.generate_component_dashboards</pre>
"""
    return _page("PPO Controller Dashboard", "Simulated training and evaluation dashboard &middot; smoke-trained policy, simulated metrics, no live execution", body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate planner and PPO dashboards")
    parser.add_argument("--config", default="configs/project.yaml")
    parser.add_argument("--stub", default="results/planner/stub/planner_evaluation.json")
    parser.add_argument("--ollama", default="results/planner/ollama/planner_evaluation.json")
    parser.add_argument("--ppo-summary", default="results/ppo/m5/summary.json")
    parser.add_argument("--ppo-manifest", default="results/ppo/m5/run_manifest.json")
    parser.add_argument("--planner-out", default="docs/agentic-planning-dashboard.html")
    parser.add_argument("--ppo-out", default="docs/ppo-controller-dashboard.html")
    parser.add_argument("--ppo-image-prefix", default="../results/ppo/m5/plots")
    args = parser.parse_args()

    config = load_config(args.config)
    stub = json.loads(Path(args.stub).read_text(encoding="utf-8"))
    ollama = json.loads(Path(args.ollama).read_text(encoding="utf-8"))
    ppo_summary = json.loads(Path(args.ppo_summary).read_text(encoding="utf-8"))
    ppo_manifest = json.loads(Path(args.ppo_manifest).read_text(encoding="utf-8"))

    planner_path = Path(args.planner_out)
    planner_path.parent.mkdir(parents=True, exist_ok=True)
    planner_path.write_text(build_planner_dashboard(stub, ollama, config), encoding="utf-8")

    ppo_path = Path(args.ppo_out)
    ppo_path.parent.mkdir(parents=True, exist_ok=True)
    ppo_path.write_text(build_ppo_dashboard(ppo_summary, ppo_manifest, config, args.ppo_image_prefix), encoding="utf-8")

    print(planner_path)
    print(ppo_path)


if __name__ == "__main__":
    main()
