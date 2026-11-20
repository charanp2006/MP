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
