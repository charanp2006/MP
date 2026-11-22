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

# Milestone 8 — Consolidated Evaluation

| Field | Value |
|---|---|
| Milestone | M8 — Consolidated evaluation |
| Status | Complete for simulated evaluation; full E7 benchmark deferred, P6 live smoke added |
| Date | 2026-11-20 (refreshed 2026-11-21) |
| Branch | `feat/m8-consolidated-evaluation` (merged); current work on `dev` |
| Related commit | `0b7cb69` (merge), `4383958` (feature), `1cf3f4a` (P6 merge) |
| Test IDs | I01–I06, S01–S06, F01–F06 protocol coverage |
| Architecture layers | 1–11: data → forecast → planner → PPO → validation → execution → monitoring → reporting |
| Evidence class | Simulated closed-loop replay + component artifacts; P6 adds a separate local live smoke, not a full E7 benchmark |

## Objective

Consolidate existing component evaluations into one predeclared E0–E7 ablation
matrix with matched workload frames, repeat seeds, reproducible artifacts,
figures and a report whose claims match the implemented system.

## Module map

| File | Role |
|---|---|
| `experiments/evaluate_m8.py` | Consolidated runner: workload registry, E0–E7 matrix, repeat runs, aggregates, figures, report |
| `configs/project.yaml` | `evaluation.m8` defaults for steps, scenarios, checkpoints, trace inclusion |
| `tests/test_m8_evaluation.py` | Runner, artifacts, fallback labelling and policy tests |
| `docs/milestones/m8-consolidated-evaluation.md` | This report |
| `docs/milestones/README.md` | Milestone index updated to M8 |
| `results/evaluation/m8/` | Generated, ignored artifacts from smoke run |

## Experiment matrix

| ID | Forecast | Planner | Controller | Executor | Status |
|---|---|---|---|---|---|
| E0 | None / reactive baseline | Rules | Rules | Simulator | Implemented |
| E1 | Persistence | Rules | Rules | Simulator | Implemented |
| E2 | TFT | Rules | Rules | Simulator | Implemented; falls back and is labelled if checkpoint unavailable |
| E3 | TFT | Qwen3 stub proxy | Rules | Simulator | Implemented; not a real Qwen3 measurement |
| E4 | Persistence | Rules | PPO | Simulator | Implemented |
| E5 | TFT | Rules | PPO | Simulator | Implemented; falls back and is labelled if checkpoint unavailable |
| E6 | TFT | Qwen3 stub proxy | PPO | Simulator | Implemented; not a real Qwen3 measurement |
| E7 | Selected AI stack | Selected stack | Selected stack | Live test | Deferred; recorded as `not_run_requires_live_cluster` |

The rules controller is a bounded observation-threshold policy; the PPO
controller uses the versioned policy checkpoint. All arms pass through the same
`DecisionLoop`, planner/plan validator, safety shield and simulated executor.

## Matched workloads and repeats

- Synthetic scenarios come from `experiments/synthetic_scenarios.py` with the
  same seed shared across all arms in a repeat.
- Optional historical trace frames are loaded once with a single scale factor
  and a fixed chronological held-out window.
- Each workload records `id`, `source`, `seed`, `scale_factor` and SHA-256 in
  `workloads.json`.
- Seeds come from CLI `--seeds` or `evaluation.seeds`; matched frames are reused
  across E0–E6 for a given seed.
- Aggregate confidence intervals are normal approximations
  (`1.96 * std / sqrt(runs)`) over matched-run means, not physical trials.

## Artifacts

| Artifact | Contents |
|---|---|
| `run_manifest.json` | Commit, config hash, Python version, seeds, steps, scenario list, trace/checkpoint hashes, units |
| `runs.csv` | One row per experiment × workload × seed with summary metrics and correlation ID |
| `aggregates.csv` | Per-experiment mean/std/CI and deferred E7 row |
| `workloads.json` | Workload hashes and provenance |
| `runs/{E}/{workload}/seed_{n}/` | Per-run decision, execution audit, feedback and alert JSONL records |
| `figures/*.png` | Reward, SLA violation, simulated energy and capacity comparisons |
| `report.md` | Predeclared final-report sections and implemented architecture diagram |

## How to run and verify

```powershell
py -m py_compile experiments/evaluate_m8.py tests/test_m8_evaluation.py
py -m pytest tests/test_m8_evaluation.py tests/test_m7_monitoring.py tests/test_m6_execution.py tests/test_m5_decision_engine.py -ra
py -m experiments.evaluate_m8 --out-dir results/evaluation/m8 --seeds 42 --steps 4 --scenarios mixed --no-tft
py -m experiments.evaluate_m8 --config configs/project.yaml --out-dir results/evaluation/m8_full --seeds 42,43,44 --steps 48 --scenarios ramp,burst,periodic,sparse,stress,mixed --trace-csv data/processed/azure_features.csv --include-trace
py -m pytest -ra
```

Focused verification: `20 passed in 5.27s`. CLI smoke verification generated
`run_manifest.json`, `runs.csv`, `aggregates.csv`, `workloads.json`,
`report.md`, four figures and per-run JSONL logs.

## Smoke-run evidence (not a research result)

The small smoke command used one seed, four steps, the `mixed` scenario and
`--no-tft`. It produced seven simulated-run rows (E0–E6) and one deferred E7
row. E2/E3/E5/E6 were correctly marked `degraded_tft_fallback`; E3/E6 were also
marked `stub_proxy`. These values must not be quoted as performance conclusions.

## Test coverage

| Test | Purpose | Result |
|---|---|---|
| `test_rule_policy_bounds_actions` | Rules controller selects bounded actions | Passed |
| `test_evaluate_m8_writes_reproducible_artifacts` | Manifest/report/figures/per-run logs | Passed |
| `test_evaluate_m8_marks_tft_fallback_when_checkpoint_missing` | Honest fallback labelling | Passed |
| Existing M5–M7 tests | No integration regression | Passed |

## Limitations and next steps

- Real Qwen3/Ollama was unavailable; E3/E6 are stub proxies only.
- E7 remains a deferred full benchmark. P6 (2026-11-21) provides a local live
  smoke with bounded execution, Prometheus feedback and Grafana verification,
  but no repeated E7 performance result.
- Energy/latency/cold starts in E0–E6 are simulator outputs; Azure traces supply
  only invocation counts. The P6 live energy metric is a payload-size proxy.
- Results are ignored by Git; `run_manifest.json` plus the documented command
  is the reproducibility contract, not committed raw result files.
- Next milestone: M9 deferred demonstration integration (synthetic client,
  generic workload ingestion, sample applications, end-to-end demo).
