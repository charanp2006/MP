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

# M3 — Qwen3 Agentic Planner Hardening and Offline Evaluation

> **V2 addendum:** This milestone record is historical: it covered offline
> hardening and fallback validation with the local Ollama path unavailable.
> The local llama-style path is now outdated; it was initially chosen for
> offline reproducibility but required a local model process/hardware and never
> produced real Qwen3 evidence. The owner's V2 direction is hosted Hugging Face
> Qwen3 primary with OpenRouter backup; real hosted inference is not yet
> implemented. See
> `../qwen3-hosted-inference-plan.md` and `../implementationv2/m0-audit.md`.

| Field | Value |
|---|---|
| Phase / Milestone | M3 — Qwen3 planner with bounded context and validated fallback |
| Doc version | v1.0 |
| Status | **Complete (offline hardening/evaluation; real Qwen3 inference unavailable)** |
| Date | 2026-11-20 |
| Branch | `feat/m4-qwen3-planner` (merged) |
| Base commit | `b3624ba410c1f88663d011eefe5aef0a8f520c0e` |
| Merge commit | `f2da3f1` |
| Feature commit | `4542726 feat(m4 & m5): Add synthetic workload scenarios, safety shield, and evaluation scripts` |
| Test IDs | Q01-Q06, R01-R04, S01-S06 (planner safety/validation/telemetry subset) |
| Architecture layers touched | L4 state contract, L5 agent/planner, L6 validation, orchestrator decision telemetry, config, scripts, tests |

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-11-20 | Initial completion report: bounded/redacted prompts, call telemetry, stronger failure tests, offline rule-vs-Qwen3 harness. |
| v1.1 | 2026-11-20 | Corrected status to merged after PR #9; recorded merge/feature commits. |
| v1.2 | 2026-11-20 | Renumbered from M4 to M3 to follow `IMPLEMENTATION_PLAN.md`. |

> Milestone numbering note: numbering follows `IMPLEMENTATION_PLAN.md`, which
> defines Milestone 3 as agentic-planner research. The older
> `IMPLEMENTATION_AGENT_PROMPT.md` used a different internal numbering.

## Objective

Harden the planner boundary so Qwen3 can only emit high-level, schema-valid
plans; bound and redact the context sent to the model; record safe per-call
telemetry; and quantify rule-based stub vs Qwen3-backed fallback behavior on an
offline scenario suite without claiming live model or Kubernetes validation.

## Module map

| File | Role |
|---|---|
| `agent/planner.py` | `StubPlanner`, `Qwen3OllamaPlanner`, `FallbackPlanner`, `build_planner`; all planners now expose `last_record` telemetry. |
| `agent/schemas.py` | Strict `StateSnapshot` / `Plan` contracts; `extra="forbid"` blocks unknown fields. |
| `agent/prompts/__init__.py` | `build_user_prompt` now bounds metadata keys/values, redacts secret-like labels, truncates the payload, and labels metadata as untrusted. |
| `agent/prompts/planner.txt` | System prompt strengthened with explicit refusal-to-NoOp behavior for unsafe/incomplete input. |
| `agent/telemetry.py` | `PlannerCallRecord` and `redact_text`; records provider/model/prompt version/status/latency/fallback/reason/strategy/plan code. |
| `agent/validator.py` | Existing schema/bounds direction/rate-limit/SLA-safe validator; unchanged safety boundary. |
| `orchestrator/decision_loop.py` | `Decision.planner_record` captures redacted telemetry and validation code for every cycle. |
| `configs/project.yaml` | New agent keys: `prompt_version`, `max_prompt_chars`, `max_metadata_keys`, `max_metadata_chars`. |
| `scripts/evaluate_planner.py` | Offline evaluation CLI: six scenarios, validity/fallback/strategy/latency/guard/action metrics, JSON + CSV artifacts. |
| `tests/test_agent_m4.py` | Planner tests (filename retained from original milestone numbering) for prompt bounding/redaction, timeout telemetry, refusal fallback, decision telemetry, unsafe plan rejection, and evaluation artifacts. |

## Design and data contracts

- `build_user_prompt(state, max_prompt_chars=8000, max_metadata_keys=12, max_metadata_chars=200)` serializes `StateSnapshot` as data, never as commands.
- Metadata keys matching `api key|token|password|secret|credential|authorization|bearer` are replaced with `[REDACTED]`; values are also passed through `redact_text`.
- Prompt payload truncation is explicit (`[PROMPT TRUNCATED]`) and the wrapper states that metadata is untrusted.
- `PROMPT_VERSION = "planner-v2"` is recorded with every call; changing prompt semantics requires bumping it.
- `PlannerCallRecord.to_dict()` redacts secret-like text and truncates long reasons; no raw model output or credentials are logged.
- `FallbackPlanner` preserves the primary provider/model/prompt version, sets `status="fallback"`, `fallback=True`, and records the redacted failure reason.
- `Decision.to_dict()` now includes `planner_record` with `plan_code`; existing fields and action names are unchanged.
- Bounded action space remains `NoOp, PreWarm, ScaleOut, Reuse, ScaleIn, Terminate`; planner output is still validated before PPO/action validation/SLA guard.
- Capacity bounds remain min `2`, max `30`, max change/cycle `5`; SLA threshold `250 ms`, safety margin `20 ms`.

## How to run and verify

```bash
py -m py_compile agent/*.py agent/prompts/*.py orchestrator/decision_loop.py scripts/evaluate_planner.py tests/test_agent_m4.py
py -m pytest -q tests/test_agent.py tests/test_agent_m4.py tests/test_orchestrator.py
py -m pytest -q
py -m scripts.evaluate_planner --runtime stub --out-dir results/planner/stub
py -m scripts.evaluate_planner --runtime ollama --timeout-s 2 --out-dir results/planner/ollama
```

Artifacts:

- `results/planner/stub/planner_evaluation.json`
- `results/planner/stub/planner_evaluation.csv`
- `results/planner/ollama/planner_evaluation.json`
- `results/planner/ollama/planner_evaluation.csv`

## Test coverage

- `test_prompt_is_bounded_and_redacted`: secret-like metadata is removed, untrusted label retained, and truncation marker appears.
- `test_redact_text_covers_common_secret_labels`: three common secret-label forms are redacted.
- `test_timeout_error_is_recorded_and_redacted`: timeout raises `PlannerError`, records `status="error"`, and leaks no secret in telemetry.
- `test_fallback_after_refusal_preserves_telemetry`: non-JSON refusal triggers deterministic stub fallback with `status="fallback"`.
- `test_decision_records_planner_telemetry`: decision loop emits provider/status/plan code/latency.
- `test_excessive_scale_in_is_rejected`: rate limit still rejects a 6-container scale-in.
- `test_evaluation_writes_artifacts`: evaluation harness writes valid JSON/CSV with 6 scenarios.
- Existing Q01-Q06 planner/validator tests and R01-R06 decision-loop tests still pass.

## Evaluation results (offline, not live Qwen3 inference)

Stub runtime (`py -m scripts.evaluate_planner --runtime stub`):

| Metric | Value |
|---|---|
| Scenarios | 6 |
| Plan validity rate | 1.000 |
| Fallback rate | 0.000 |
| Mean planning latency | 0.011 ms |
| P95 planning latency | 0.021 ms |
| Strategy counts | `NoOp=2, ScaleOut=2, ScaleIn=1, PreWarm=1` |
| Final action counts | `NoOp=6` |
| Guard override rate | 0.000 |
| Action reject rate | 0.000 |

Ollama runtime (`--runtime ollama --timeout-s 2`), with local Qwen3 unavailable:

| Metric | Value |
|---|---|
| Scenarios | 6 |
| Plan validity rate | 1.000 (all stub fallback plans) |
| Fallback rate | 1.000 |
| Mean planning latency | 4043.890 ms |
| P95 planning latency | 4147.962 ms |
| Status counts | `fallback=6` |
| Provider counts | `ollama=6` (primary attempted, stub result used) |
| Strategy/final-action counts | Same as stub runtime |

Full suite: `127 passed, 1 warning in 28.97s`; the warning is the pre-existing
`data/ingestion.py:36` timestamp-format warning from an ingestion failure test.

## Measured vs simulated vs estimated

- **Measured:** full pytest result; stub planning latency; JSON/CSV artifact generation; validation/telemetry records from actual code execution.
- **Simulated/offline:** all six scenario states, decisions, final actions, guard/action codes, and strategy distributions.
- **Unavailable/not measured:** real Qwen3 inference, real Ollama latency, token usage, live Kubernetes/OpenFaaS execution, live Prometheus/Grafana observation, hardware energy, and cold-start measurements.
- **Estimated/modeled:** none added in M3; M2/M1 proxy limitations still apply.

## Security and safety notes

- Qwen3 still receives a high-level prompt and returns only a strict JSON `Plan`; no shell/Kubernetes command path exists.
- Prompt injection strings in metadata are treated as data; bounded/redacted context prevents secret leakage and oversized prompts.
- All plans still pass `PlanValidator` → PPO/feedback bias → action validator → SLA guard → authorization before any dry-run execution.
- Telemetry redacts secret-like labels, truncates long reasons, and records only the plan code (not raw model output).
- `execution.enabled=false` and `execution.dry_run=true` were not changed.

## Limitations and next steps

- Real Qwen3 quality cannot be assessed until Ollama/Qwen3 is available; current Ollama numbers measure fallback behavior only.
- The offline scenario suite is small and hand-designed; it validates safety mechanics, not production planning quality.
- Final actions in the evaluation are all `NoOp` because no PPO policy was supplied; downstream metric coverage is limited to validator/guard outcomes.
- Next milestone: M4 PPO controller with SLA-aware reward/penalty, then reuse this planner harness for controlled baseline-vs-proposed experiments.

## Changelog

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-11-20 | Initial report. |
