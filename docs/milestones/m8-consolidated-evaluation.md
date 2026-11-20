# Milestone 8 — Consolidated Evaluation

| Field | Value |
|---|---|
| Milestone | M8 — Consolidated evaluation |
| Status | Complete for simulated consolidated evaluation; live E7 deferred |
| Date | 2026-11-20 |
| Branch | `feat/m8-consolidated-evaluation` |
| Related commit | `db8d8a6` (base; M8 changes uncommitted) |
| Test IDs | I01–I06, S01–S06, F01–F06 protocol coverage |
| Architecture layers | 1–11: data → forecast → planner → PPO → validation → execution → monitoring → reporting |
| Evidence class | Simulated closed-loop replay + component artifacts; **no live platform result** |

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
- E7 remains unimplemented until live execution and live Prometheus/Grafana
  measurements are available.
- Energy/latency/cold starts are simulator outputs; Azure traces supply only
  invocation counts.
- Results are ignored by Git; `run_manifest.json` plus the documented command
  is the reproducibility contract, not committed raw result files.
- Next milestone: M9 deferred demonstration integration (synthetic client,
  generic workload ingestion, sample applications, end-to-end demo).
