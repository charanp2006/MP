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

# M5 — Decision-Engine Integration and Replay Provenance

| Field | Value |
|---|---|
| Phase / Milestone | M5 — decision-engine integration |
| Document version | v1.1 |
| Status | Complete (implementation + simulation replay); merged |
| Date | 2026-11-20 |
| Branch | `feat/m5-decision-engine-integration` |
| Base commit | `f2da3f1` (pre-merge); merge `7f8e1e5`; feature `38f5297` |
| Test IDs | I01–I04 (simulation), F02/F03/F06 (fallback/validation subsets) |
| Architecture layers | 4–9: state → planner → plan validator → PPO → shield → executor hook → feedback/logging |
| Evidence tier | Simulation replay only; no live cluster, telemetry, energy or latency measurements |

## 1. Objective

Integrate the validated forecast, Qwen3/stub planner, PPO action proposal and
safety shield into one bounded control step, then prove that a replay carries
complete provenance: inputs → validated state → advisory plan → proposed action
→ final action → executor hook → observed outcome.

## 2. Module map

| Module | Change / role |
|---|---|
| `orchestrator/decision_loop.py` | `Decision` now carries forecast, metrics, correlation ID, hierarchy and outcome; PPO proposal passes through `SafetyShield` as final authority; `DecisionLoop.record_outcome()` logs the completed step. |
| `orchestrator/safety_shield.py` | Constructor accepts injected `ActionValidator` and `SLAGuard` so the loop cannot fork its own validation path. |
| `orchestrator/decision_log.py` | Redacted append-only JSONL logger with `reset()` and `read_records()` for deterministic replays. |
| `orchestrator/__init__.py` | Exports `DecisionLogger`; documents shield/logger in the layer map. |
| `experiments/evaluate_decision_engine.py` | New replay/ablation harness with CSV/JSON/Markdown/HTML/PNG artifacts. |
| `configs/project.yaml` | Adds `decision_log` and `decision_engine` defaults. |
| `tests/test_m5_decision_engine.py` | New tests for logging/redaction, shield authority, no-oracle replay and artifact generation. |

## 3. Data and control contracts

### 3.1 Decision record

Each `Decision.to_dict()` / JSONL record contains:

- `correlation_id`: unique per replay step (`<arm>-<step>-<uuid suffix>`).
- `forecast`: validated forecast mapping, including `source`, `predicted_workload`,
  `trend` and, for TFT, `raw_predicted_workload` plus the trace scale factor.
- `metrics`: current workload, CPU, memory, capacity, warm containers, P95,
  cold starts and simulated energy.
- `state`: validated `StateSnapshot`.
- `plan`, `plan_valid`, `plan_code`, `plan_reason`, `planner_record`.
- `ppo_action` and `ppo_action_name`: controller proposal, never authority.
- `hierarchy`: roles, proposed/biased action, planner strategy, shield result.
- `final_action`, `action_code`, `guard_code`, `authorized`, `execution`.
- `outcome`: reward, P95, SLA flag, cold starts, energy proxy, capacity, reward
  components.

All string fields are redacted through `agent.telemetry.redact_text` before the
record is written.

### 3.2 Authority hierarchy

- Planner (Qwen3 or stub): high-level advisory strategy only.
- Plan validator: schema, bounds, direction and capacity checks.
- PPO: bounded action proposal only.
- Feedback: soft bias, never bypasses validation or the guard.
- `SafetyShield`: single final authority combining action validation,
  authorization, plan consistency and the deterministic SLA guard.
- Executor: disabled by default; dry-run remains the safe default.

### 3.3 Forecast source honesty

`run_episode()` no longer reads future timeline values. It uses:

- `tft` when `--tft-checkpoint` points to a loadable checkpoint; TFT output is
  rescaled to the same simulator workload scale as the replay trace.
- `persistence` otherwise: the current workload is repeated across the horizon.

Every replay row records `forecast_source`. No row is labeled `oracle`.

## 4. How to run and verify

### 4.1 Unit / integration tests

```powershell
py -m py_compile orchestrator/decision_loop.py orchestrator/decision_log.py orchestrator/safety_shield.py orchestrator/__init__.py experiments/evaluate_decision_engine.py tests/test_m5_decision_engine.py
py -m pytest tests/test_m5_decision_engine.py tests/test_orchestrator.py tests/test_m5.py -ra
py -m pytest -ra
```

### 4.2 Deterministic replay with official Azure trace and TFT

```powershell
py -m experiments.evaluate_decision_engine --out-dir results/decision/m5 --steps 24 --trace-csv data/processed/azure_features.csv --tft-checkpoint results/forecast/azure2019_total/checkpoint.pt
```

Artifacts written to `results/decision/m5/`:

- `run_manifest.json`: configuration hash, git commit, source, scale factor,
  checkpoint paths, ablation list and artifact paths.
- `decisions/{full,planner_off,policy_off,feedback_off,forecast_off}.jsonl`:
  one complete provenance record per step per arm.
- `replay.csv`, `replay.json`, `replay.md`, `replay.html`, `replay_timeline.png`:
  step-by-step visualization of the full arm.
- `ablations.csv`, `summary.json`: end-to-end arm summaries.

## 5. Test coverage

| Test | Coverage |
|---|---|
| `test_decision_logger_writes_redacted_provenance` | JSONL schema version, correlation ID, hierarchy, outcome and secret redaction. |
| `test_decide_uses_shield_as_final_authority` | PPO `ScaleIn` near SLA is blocked; shield proposed/final actions are recorded. |
| `test_run_episode_logs_outcomes_without_oracle_forecast` | Persistence source, no future-value leakage, two unique correlation IDs, logged rewards match returned records. |
| `test_evaluate_decision_engine_writes_replay_and_ablations` | All five ablation arms, replay row count and all artifact files. |
| Existing `tests/test_orchestrator.py` | State builder, plan validator, action validator, SLA guard and loop compatibility. |
| Existing `tests/test_m5.py` | Safety shield, lifecycle delay, checkpoint validation and PPO evaluation compatibility. |

Focused verification result: `31 passed` for the three decision/PPO/orchestrator test modules.

## 6. Simulation replay result (not a live measurement)

The Azure replay used the prepared chronological trace, scale factor
`0.0010724772158173706`, the compatible TFT checkpoint
`results/forecast/azure2019_total/checkpoint.pt`, and the local PPO checkpoint
`models/ppo_policy.pt`. The 24-step full arm produced 24 JSONL records with
unique correlation IDs, `forecast_source=tft`, zero SLA violations and a mean
simulated reward of `-0.6418`. The step-by-step replay and all artifacts are in
`results/decision/m5/`.

The five ablation arms are structural integration checks only. On this short,
low-risk 24-step trace segment all arms have the same simulated reward/capacity
outcomes; only the final action differs for `policy_off`. This is **not**
evidence that any component improves or degrades performance, and no energy,
latency or cold-start measurements were taken from a live system.

## 7. Limitations and next steps

- Qwen3 was not available during this replay; planner behavior uses the offline
  stub. The planner telemetry path was validated earlier and remains wired.
- `models/tft_checkpoint.pt` is incompatible with the fixed TFT head; use
  `results/forecast/azure2019_total/checkpoint.pt`.
- Azure resources (CPU, memory, energy, cold starts, latency) remain simulated
  proxies; the trace supplies invocation counts only.
- I05 (executor → runtime → Prometheus) and I06 (Prometheus → next cycle)
  remain unvalidated without a live cluster and metrics stack.
- No `shield_off` ablation was added because it would bypass the canonical
  safety boundary; ablations remove advisory/informational components only.
- Next milestone: M6 execution layer (Docker/OpenFaaS/Kubernetes dry-run and
  validated live lifecycle control), followed by live monitoring in M7.

## 8. Changelog

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-11-20 | Initial M5 decision-engine integration and replay report. |
| v1.1 | 2026-11-20 | Recorded merged commits `7f8e1e5` / `38f5297` and final status. |
