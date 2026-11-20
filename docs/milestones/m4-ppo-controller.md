<style>
:root {
  --oc-bg: #0a0a0a;
  --oc-panel: #141414;
  --oc-raised: #1e1e1e;
  --oc-border: #3c3c3c;
  --oc-border-strong: #484848;
  --oc-text: #eeeeee;
  --oc-muted: #808080;
  --oc-heading: #9d7cd8;
  --oc-primary: #fab283;
  --oc-link: #56b6c2;
  --oc-code: #7fd88f;
  --oc-strong: #f5a742;
  --oc-emph: #e5c07b;
  --oc-error: #e06c75;
  --oc-font: Consolas, "Cascadia Mono", "Cascadia Code", "Courier New", monospace;
}
html { background: var(--oc-bg) !important; }
body {
  background: var(--oc-bg) !important;
  color: var(--oc-text) !important;
  font-family: var(--oc-font) !important;
  font-size: 16px !important;
  line-height: 1.55 !important;
  font-variant-ligatures: none;
  -webkit-font-smoothing: antialiased;
}
body.vscode-body {
  /* max-width: 100ch !important; */
  margin: 0 auto !important;
  padding: 34px 28px 64px !important;
}
#write {
  max-width: 100ch !important;
  margin: 0 auto !important;
  padding: 34px 28px 64px !important;
  font-family: var(--oc-font) !important;
  font-size: 16px !important;
  line-height: 1.55 !important;
  color: var(--oc-text) !important;
  background: transparent !important;
}
body.vscode-body *, #write *, .oc-doc * { font-family: var(--oc-font) !important; }
h1, h2, h3, h4, h5, h6 {
  color: var(--oc-heading) !important;
  font-weight: 700 !important;
  line-height: 1.3 !important;
  margin: 1.6em 0 .6em !important;
  padding: 0 !important;
  border: 0 !important;
  background: transparent !important;
}
h1 { font-size: 1.5em !important; text-decoration: underline !important; text-underline-offset: 5px; text-decoration-thickness: 1px; }
h2 { font-size: 1.3em !important; }
h3 { font-size: 1.15em !important; }
h4 { font-size: 1.05em !important; }
h5, h6 { font-size: 1em !important; }
p { margin: .8em 0 !important; }
strong, b { color: var(--oc-strong) !important; font-weight: 700 !important; }
em, i { color: var(--oc-emph) !important; font-style: italic !important; }
del, s { color: var(--oc-muted) !important; }
a { color: var(--oc-link) !important; text-decoration: underline !important; text-underline-offset: 2px; }
a[href^="http"]::after {
  content: " (" attr(href) ")";
  color: var(--oc-primary) !important;
  font-size: .88em;
  word-break: break-all;
}
code {
  color: var(--oc-code) !important;
  background: transparent !important;
  border: 0 !important;
  padding: 0 !important;
  font-size: 1em !important;
  font-family: var(--oc-font) !important;
  white-space: break-spaces;
}
pre {
  background: var(--oc-panel) !important;
  border: 1px solid var(--oc-border) !important;
  padding: 14px 16px !important;
  margin: 1em 0 !important;
  overflow-x: auto !important;
  line-height: 1.5 !important;
  font-size: 1em !important;
  box-shadow: none !important;
}
pre code {
  color: var(--oc-text) !important;
  background: transparent !important;
  border: 0 !important;
  padding: 0 !important;
  font-size: 1em !important;
  white-space: pre;
}
ul, ol { margin: .8em 0 !important; padding-left: 1.7em !important; }
li { margin: .28em 0 !important; }
li::marker { font-family: var(--oc-font) !important; }
ul > li::marker { color: var(--oc-primary) !important; }
ol > li::marker { color: var(--oc-link) !important; }
ul ul > li::marker { color: var(--oc-link) !important; }
ul ul ul > li::marker { color: var(--oc-emph) !important; }
input[type="checkbox"] { accent-color: var(--oc-code) !important; }
blockquote {
  margin: 1em 0 !important;
  padding: .15em 0 .15em 1em !important;
  border-left: 2px solid var(--oc-border-strong) !important;
  background: transparent !important;
  color: var(--oc-emph) !important;
  font-style: italic !important;
}
blockquote p { color: var(--oc-emph) !important; margin: .3em 0 !important; }
hr {
  border: 0 !important;
  border-top: 1px solid var(--oc-muted) !important;
  height: 0 !important;
  margin: 1.8em 0 !important;
  background: transparent !important;
}
table { border-collapse: collapse !important; margin: 1em 0 !important; width: auto !important; }
th, td { border: 1px solid var(--oc-border) !important; padding: 6px 12px !important; }
th { background: var(--oc-raised) !important; color: var(--oc-text) !important; font-weight: 700 !important; }
img { max-width: 100% !important; border: 1px solid var(--oc-border) !important; border-radius: 3px !important; }
kbd {
  background: var(--oc-raised) !important;
  border: 1px solid var(--oc-border-strong) !important;
  border-bottom-width: 2px !important;
  padding: 1px 5px !important;
  color: var(--oc-text) !important;
  font-size: .9em !important;
}
::selection { background: var(--oc-heading) !important; color: var(--oc-bg) !important; }
* { scrollbar-color: var(--oc-border) var(--oc-bg); }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: var(--oc-bg); }
::-webkit-scrollbar-thumb { background: var(--oc-border); }
.hljs-comment, .hljs-quote { color: var(--oc-muted) !important; font-style: italic; }
.hljs-keyword, .hljs-selector-tag, .hljs-literal { color: var(--oc-heading) !important; font-style: italic; }
.hljs-type { color: var(--oc-emph) !important; font-style: italic; font-weight: 700; }
.hljs-string, .hljs-regexp, .hljs-symbol, .hljs-bullet { color: var(--oc-code) !important; }
.hljs-number { color: var(--oc-strong) !important; }
.hljs-title, .hljs-section, .hljs-title.function_, .hljs-function .hljs-title { color: var(--oc-primary) !important; }
.hljs-variable, .hljs-template-variable, .hljs-params, .hljs-built_in, .hljs-builtin-name { color: var(--oc-error) !important; }
.hljs-class .hljs-title, .hljs-title.class_ { color: var(--oc-emph) !important; }
.hljs-operator, .hljs-punctuation { color: var(--oc-link) !important; }
.hljs-attr, .hljs-attribute, .hljs-property { color: var(--oc-primary) !important; }
.hljs-tag { color: var(--oc-error) !important; }
.hljs-name { color: var(--oc-heading) !important; }
.hljs-meta { color: var(--oc-muted) !important; }
.hljs-addition { color: #4fd6be !important; background: #20303b !important; }
.hljs-deletion { color: #c53b53 !important; background: #37222c !important; }
.token.comment, .token.prolog, .token.doctype, .token.cdata { color: var(--oc-muted) !important; font-style: italic; }
.token.keyword { color: var(--oc-heading) !important; font-style: italic; }
.token.tag { color: var(--oc-error) !important; }
.token.string, .token.attr-value, .token.char { color: var(--oc-code) !important; }
.token.number, .token.boolean { color: var(--oc-strong) !important; }
.token.function, .token.class-name { color: var(--oc-primary) !important; }
.token.variable, .token.parameter { color: var(--oc-error) !important; }
.token.operator, .token.punctuation { color: var(--oc-link) !important; }
.cm-keyword { color: var(--oc-heading) !important; font-style: italic; }
.cm-builtin { color: var(--oc-error) !important; }
.cm-string, .cm-string-2, .cm-atom { color: var(--oc-code) !important; }
.cm-number, .cm-literal { color: var(--oc-strong) !important; }
.cm-def, .cm-variable-2, .cm-variable-3 { color: var(--oc-primary) !important; }
.cm-variable, .cm-variable-1 { color: var(--oc-error) !important; }
.cm-comment { color: var(--oc-muted) !important; font-style: italic; }
.cm-operator, .cm-bracket { color: var(--oc-link) !important; }
.cm-property, .cm-attribute { color: var(--oc-primary) !important; }
.cm-tag { color: var(--oc-error) !important; }
.cm-type { color: var(--oc-emph) !important; }
.cm-meta { color: var(--oc-muted) !important; }
.oc-green { color: var(--oc-code) !important; }
.oc-orange { color: var(--oc-strong) !important; }
.oc-purple { color: var(--oc-heading) !important; }
</style>

# M4 — PPO Controller, Safety Shield and Simulation Evaluation

| Field | Value |
|---|---|
| Phase / Milestone | M4 — PPO controller with SLA-aware safety shield and controlled comparisons |
| Doc version | v1.0 |
| Status | **Complete (simulation/artifacts; no live latency/energy measurements)** |
| Date | 2026-11-20 |
| Branch | `feat/m4-qwen3-planner` (merged) |
| Base commit | `b3624ba410c1f88663d011eefe5aef0a8f520c0e` |
| Merge commit | `f2da3f1` |
| Feature commit | `4542726 feat(m4 & m5): Add synthetic workload scenarios, safety shield, and evaluation scripts` |
| Test IDs | R01-R04, U09-U12, I03-I04, F03, S01-S06 (simulation subset) |
| Architecture layers touched | L3 simulator/forecast handoff, L9 PPO control, L8 safety shield, scripts/experiments, config, tests |

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-11-20 | Initial completion report: lifecycle delay, cold-start observation, safety shield, multi-seed scenario evaluation, TFT+rule trace arm, plots and manifests. |
| v1.1 | 2026-11-20 | Corrected status to merged after PR #9; recorded merge/feature commits. |
| v1.2 | 2026-11-20 | Renumbered from M5 to M4 and adopted `IMPLEMENTATION_PLAN.md` numbering. |

> Milestone numbering note: numbering follows `IMPLEMENTATION_PLAN.md`, which
> defines Milestone 4 as PPO research. The older
> `IMPLEMENTATION_AGENT_PROMPT.md` used a different internal numbering. The
> commit message retains the old numbering labels.

## Objective

Reproducibly train and evaluate PPO with the canonical six-action set in a
documented, trace-driven/synthetic simulator; enforce the same validation and
SLA shield used by the decision engine; compare against fixed, reactive/rule,
persistence+rule and TFT+rule arms; and emit honest simulation artifacts with
clear measured/simulated separation.

## Module map

| File | Role |
|---|---|
| `rl/environment.py` | 10-dim observation, six actions, SLA reward, capacity bounds; now adds `lifecycle_delay_steps`, `cooldown_steps`, cold-start history, pending warm containers, forecast validation and `current_context()` for the shield. |
| `rl/reward.py` | Normalized energy/latency/cold-start/resource/underutil costs plus highest-weight SLA violation penalty (unchanged). |
| `rl/train_ppo.py` | PPO/GAE training; optional `action_filter`; versioned checkpoints with obs/action shape checks and metadata. |
| `orchestrator/safety_shield.py` | New `SafetyShield`/`ShieldDecision`: action validation + authorization + plan consistency + SLA guard in one PPO/evaluation boundary. |
| `experiments/synthetic_scenarios.py` | New deterministic ramp/burst/periodic/sparse/stress/mixed workload generators. |
| `experiments/evaluate_ppo_m5.py` | New multi-seed evaluation CLI: trains PPO per seed, evaluates four synthetic arms plus trace persistence/TFT-rule arms, writes CSV/JSON/PNG artifacts. |
| `configs/project.yaml` | Added simulator lifecycle/cooldown/cold-history keys and `evaluation.seeds`. |
| `tests/test_m5.py` | PPO tests (filename retained from original numbering) for scenario determinism, lifecycle delay, cold-start observability, shield blocks, checkpoint compatibility, filtered training and artifacts. |

## Design and data contracts

- Observation names remain `predicted_workload, current_workload, cpu, memory, latency, p95_latency, active_containers, cold_starts, energy, sla_margin`; cold-start dimension now reflects recent simulated cold starts instead of a fixed zero.
- Actions remain `NoOp, PreWarm, ScaleOut, Reuse, ScaleIn, Terminate` (indices 0-5).
- `PreWarm` queues warm containers for `lifecycle_delay_steps=1`; `ScaleOut` consumes warm containers first, otherwise incurs simulated cold starts.
- Optional `cooldown_steps=0` blocks rapid capacity reductions; default preserves existing behavior.
- `SafetyShield.filter()` returns the final action plus codes/reasons; every proposed action passes `ActionValidator` then `SLAGuard` before simulation.
- Filtered PPO training records the policy's log-probability for the proposed action while the environment receives the shielded action; interventions are counted in `history["shield_interventions"]`.
- Checkpoints now include `checkpoint_version=2`, obs/action dimensions and metadata; loading validates expected shapes (F03).
- All evaluation outputs are labeled `mode: simulation`; energy is a proxy in watts, P95 latency is simulated, cold starts are simulated container starts, and reward is normalized (higher is better).

## How to run and verify

```bash
py -m py_compile rl/*.py orchestrator/*.py experiments/*.py
py -m pytest -q tests/test_m5.py
py -m pytest -q

py -m experiments.evaluate_ppo_m5 \
  --episodes 3 --steps 48 --seeds 42,43,44 \
  --trace-csv data/processed/azure_features.csv \
  --tft-checkpoint results/forecast/azure2019_total/checkpoint.pt \
  --out-dir results/ppo/m5
```

Artifacts in `results/ppo/m5/`:

- `run_manifest.json`, `summary.json`, `comparison.csv`, `learning_curves.csv`, `action_frequencies.csv`, `timelines.csv`
- `plots/learning_curve.png`, `plots/timeline.png`, `plots/action_frequencies.png`
- `ppo_seed_42.pt`, `ppo_seed_43.pt`, `ppo_seed_44.pt` (gitignored simulation checkpoints)

## Evaluation setup (simulated)

- Seeds: `42, 43, 44`; PPO training episodes per seed: `3`; synthetic scenario test steps: `15` each after a 70/30 chronological split of each 48-step scenario.
- Synthetic scenarios: `ramp, burst, periodic, sparse, stress, mixed`.
- Arms on synthetic scenarios: `fixed_noop`, `reactive`, `persistence_rule`, `ppo_shielded`.
- Trace arms on a chronological held-out Azure segment: `trace_persistence_rule`, `trace_tft_rule`.
- Config SHA-256: `aaf3f0565875491e3160ea2c62a13a038ba9da11192453cad1155678a59b5464`.
- TFT checkpoint: `results/forecast/azure2019_total/checkpoint.pt` (M2 official checkpoint)
. Legacy `models/tft_checkpoint.pt` is incompatible with the fixed TFT head and was rejected.
- Azure trace workload was scaled by `0.0010724772158173706` to fit simulator capacity bounds; raw invocation values were retained for TFT inputs and the forecast output was rescaled for simulation. Resource columns absent from the trace were derived from scaled invocations and are explicitly simulated.
- Trace feature engineering used the canonical `data.feature_engineering.build_features`; chronological ordering was never shuffled.

## Results (aggregated over seeds/scenarios, simulated)

| Arm | N | Mean reward | SLA violation rate | Mean energy proxy (W) | Mean capacity | Mean cold starts | Mean P95 (ms) | Shield intervention rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `fixed_noop` | 18 | -1.1564 | 0.2556 | 35.0 | 2.0 | 0.0 | 196.91 | 0.0 |
| `persistence_rule` | 18 | -1.5315 | 0.0444 | 227.83 | 14.86 | 1.28 | 100.19 | 0.0 |
| `ppo_shielded` | 18 | -1.1564 | 0.2556 | 35.0 | 2.0 | 0.0 | 196.91 | 0.1148 |
| `reactive` | 18 | -1.7725 | 0.0556 | 222.50 | 14.50 | 2.17 | 97.41 | 0.0 |
| `trace_persistence_rule` | 1 | -0.6384 | 0.0 | 35.0 | 2.0 | 0.0 | 171.38 | 0.0 |
| `trace_tft_rule` | 1 | -0.6384 | 0.0 | 35.0 | 2.0 | 0.0 | 171.38 | 0.0 |

Interpretation (bounded): with only three training episodes, PPO converged to a
NoOp-like policy, matching `fixed_noop`; this is a smoke-level training result,
not evidence of superior control. Rule and reactive arms reduced simulated SLA
violations by provisioning more capacity, but paid higher normalized energy and
cold-start cost. The shield blocked 11.48% of PPO proposals across synthetic
rollouts. TFT+rule and persistence+rule matched on this single low-load trace
segment because both produced NoOp-like plans.

## Test coverage

- M4 new tests: deterministic scenarios, lifecycle delay, cold-start observation, SLA/unauthorized/unknown-action shield blocks, checkpoint shape mismatch, filtered PPO training, artifact generation.
- Existing R01-R04 action-set/capacity/reward tests, orchestrator validator/guard tests, planner tests, forecasting tests and monitoring tests still pass.
- Full suite: `134 passed, 1 warning`; the warning is the pre-existing `data/ingestion.py:36` timestamp-format warning.

## Measured vs simulated vs estimated

- **Measured:** pytest results; generated artifact existence/content; TFT checkpoint load success for the M2 checkpoint;
 deterministic scenario equality; checkpoint shape rejection.
- **Simulated:** all reward, latency, energy proxy, cold-start, capacity, action-frequency and shield-intervention values in the tables/plots.
- **Estimated:** Azure trace resource columns derived from invocation counts; trace workload scaling factor for simulator capacity calibration.
- **Not measured:** live Kubernetes/OpenFaaS latency, real hardware energy, real cold starts, Prometheus/Grafana telemetry, Qwen3/Ollama inference quality.

## Security and safety notes

- PPO never executes infrastructure commands; proposed actions pass `ActionValidator` + `SLAGuard` through `SafetyShield` before stepping the simulator.
- Planner/PPO hierarchy remains unchanged; M5 will make the combined decision provenance explicit.
- Execution defaults remain `enabled=false`, `dry_run=true`, namespace allowlisted.
- Checkpoints load with version/shape checks and are gitignored; no models or datasets were committed.
- Numeric improvements were not claimed as measured outcomes; target percentages from the PRD remain targets.

## Limitations and next steps

- PPO training was deliberately short for reproducibility; learning curves are smoke-level and need longer multi-seed runs before performance claims.
- The simulator's latency/energy/cold-start models are proxies and are not calibrated to live infrastructure.
- The Azure trace segment was scaled for simulator capacity; TFT forecasts were rescaled back for simulation, so these numbers are not production-latency predictions.
- Full E0-E6 ablation matrix, confidence intervals over many seeds and longer chronological trace segments remain for M9.
- Next milestone: M5 decision-engine integration (validated state → forecast → planner → PPO → shield → decision record → dry-run → feedback) with correlation IDs and replay provenance.

## Changelog

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-11-20 | Initial report. |
