# M4 — Qwen3 Agentic Planner Hardening and Offline Evaluation

| Field | Value |
|---|---|
| Phase / Milestone | M4 — Qwen3 planner with bounded context and validated fallback |
| Doc version | v1.0 |
| Status | **Complete (offline hardening/evaluation; real Qwen3 inference unavailable)** |
| Date | 2026-11-20 |
| Branch | `feat/m4-qwen3-planner` (uncommitted changes) |
| Base commit | `b3624ba410c1f88663d011eefe5aef0a8f520c0e` |
| Test IDs | Q01-Q06, R01-R04, S01-S06 (planner safety/validation/telemetry subset) |
| Architecture layers touched | L4 state contract, L5 agent/planner, L6 validation, orchestrator decision telemetry, config, scripts, tests |

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-11-20 | Initial M4 completion report: bounded/redacted prompts, call telemetry, stronger failure tests, offline rule-vs-Qwen3 harness. |

> Milestone numbering note: `IMPLEMENTATION_AGENT_PROMPT.md` defines M4 as the
> Qwen3 agentic planner, while `IMPLEMENTATION_PLAN.md` numbers milestones
> differently. This report follows the agent prompt and `docs/milestones/README.md`.

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
| `tests/test_agent_m4.py` | M4 tests for prompt bounding/redaction, timeout telemetry, refusal fallback, decision telemetry, unsafe plan rejection, and evaluation artifacts. |

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
- **Estimated/modeled:** none added in M4; M3/M2 proxy limitations still apply.

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
- Next milestone: M5 PPO controller with SLA-aware reward/penalty, then reuse this planner harness for controlled baseline-vs-proposed experiments.

## Changelog

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-11-20 | Initial report. |
