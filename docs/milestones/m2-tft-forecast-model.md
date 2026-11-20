# M2 — TFT Workload Forecasting and Baseline Evaluation

| Field | Value |
|---|---|
| Phase / Milestone | M2 — TFT forecast model |
| Doc version | v1.0 |
| Status | **Complete (official-data training/evaluation, baselines, plots, inference fallback)** |
| Date | 2026-11-20 |
| Branch | `feat/m3-tft-forecasting` (merged) |
| Base commit | `b7ccce5f21249ea359775de625bac2cf53b5c6ea` |
| Merge commit | `b3624ba410c1f88663d011eefe5aef0a8f520c0e` |
| Feature commit | `06245d5 feat(m3-ttf-forecasting): Enhance forecasting model with new metrics, evaluation, and visualization` |
| Test IDs | T01-T04, F01 (forecast unit/integration/failure) |
| Architecture layers touched | L2 data contract, L3 forecasting, scripts/CLI, tests, config |

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-11-20 | Initial completion report: baselines, extended metrics, plots, fallback service, official Azure run. |
| v1.1 | 2026-11-20 | Corrected status to merged after PR #8; recorded merge/feature commits. |
| v1.2 | 2026-11-20 | Renumbered from M3 to M2 to follow `IMPLEMENTATION_PLAN.md`. |

> Milestone numbering note: numbering follows `IMPLEMENTATION_PLAN.md`, which
> defines Milestone 2 as forecasting research (TFT + baselines). The older
> `IMPLEMENTATION_AGENT_PROMPT.md` used a different internal numbering.

## Objective

Train and evaluate the compact Temporal Fusion Transformer on the official
Azure Functions 2019 workload trace, compare it against transparent baselines
on identical chronological test rows, generate code-produced metrics and plots,
and provide a validated inference path with deterministic fallback.

## Module map

| File | Role |
|---|---|
| `forecasting/dataset.py` | Leak-free chronological windows; raw test windows and origin/target timestamps for baselines/plots. |
| `forecasting/tft_model.py` | Compact PyTorch TFT (variable selection, GRN, LSTM, attention); output head no longer normalizes across horizon steps. |
| `forecasting/train.py` | Seeded training, best-validation checkpoint, train-only scaler; covariates filtered to columns present in the trace. |
| `forecasting/baselines.py` | Persistence, daily seasonal persistence, moving average on the same test windows. |
| `forecasting/evaluate.py` | MAE/RMSE/MAPE plus WAPE, sMAPE, bias, peak-underprediction rate, residual interval calibration/coverage. |
| `forecasting/inference.py` | Separate raw-window and already-scaled-window inference; finite/non-negative prediction checks. |
| `forecasting/tft_service.py` | Checkpoint-backed forecast service with fallback for non-finite input, stale input, and model errors. |
| `forecasting/evaluation.py` | Reproducible evaluation run: metrics, predictions CSV, checkpoint, scaler, feature order, plots, run manifest. |
| `forecasting/visualize.py` | PNG plots generated from saved prediction artifacts. |
| `scripts/evaluate_forecast.py` | CLI to run data preparation + training + evaluation + artifact generation. |
| `tests/test_forecast_m3.py` | M3 tests for extended metrics, baselines, inference scaling, fallback, and artifacts. |

## Design and data contracts

- Input: prepared Azure trace `data/processed/azure_features.csv` (official invocation counts, gitignored).
- Feature columns after filtering: `invocation_count, hour, day_of_week, peak_period`.
- Simulated CPU/memory/container covariates in the default config are skipped when absent; no proxy values were invented for this run.
- Scaler is fit on train rows only; windows never cross split boundaries; targets start immediately after the history window.
- Baselines and TFT are evaluated on the same `14935` flattened test targets (`2987` windows × horizon `5`).
- Prediction intervals are residual empirical quantiles calibrated on validation only, then evaluated on test.
- Fallback policy: last finite target observation in the input window, repeated across the horizon, with reason code.

## How to run and verify

```bash
py -m scripts.evaluate_forecast \
  --data-source azure_functions_2019 \
  --out-dir results/forecast/azure2019_total \
  --run-id azure2019_total_h30_h5 \
  --epochs 8
```

Verification commands:

```bash
py -m py_compile forecasting/*.py scripts/evaluate_forecast.py tests/test_forecast_m3.py
py -m pytest -q tests/test_forecasting.py tests/test_forecast_m3.py
py -m pytest -q
```

## Official run (measured, not simulated)

Dataset: `data/processed/azure_features.csv`, SHA-256
`b674433d83e923f82b688830cfb3efa9fbbe4f629d6ba210947bed38a91ba8b5`.
Resolved config SHA-256:
`f9310ac68bfe24675598918ee9a5e8465266f5da6abf13f86203eca98329c3ab`.
Runtime: ~37 s on the development CPU. Best validation loss (scaled MSE):
`0.2543056443`.

Chronological split (after warm-up rows from lag/rolling features):

| Split | Windows | Range (UTC) |
|---|---:|---|
| Train | 14057 | 2019-07-01 00:29 → 2019-07-10 19:19 |
| Validation | 2985 | 2019-07-10 19:20 → 2019-07-12 21:38 |
| Test | 2987 | 2019-07-12 21:39 → 2019-07-14 23:59 |

Overall test metrics (identical rows for every model):

| Model | MAE | RMSE | MAPE % | WAPE % | sMAPE % | Bias | Peak underpred. |
|---|---:|---:|---:|---:|---:|---:|---:|
| TFT | 22105.09 | 30540.06 | 3.35 | 3.41 | 3.37 | -40.58 | 0.968 |
| Persistence | 26723.39 | 37505.47 | 4.05 | 4.12 | 4.05 | +142.53 | 0.837 |
| Seasonal persistence | 48476.24 | 62602.05 | 7.44 | 7.48 | 7.70 | -20820.20 | 0.841 |
| Moving average | 24961.07 | 34507.89 | 3.78 | 3.85 | 3.79 | +206.66 | 0.932 |

TFT beats all baselines on overall MAE/RMSE/WAPE/sMAPE and has near-zero bias,
but its peak-underprediction rate is worse than persistence and seasonal
persistence. On the top-decile peak subset, TFT WAPE is `7.83%` versus
persistence `7.55%`. This is reported as a limitation, not a win.

Interval diagnostics (`alpha=0.2`, nominal 80%):
coverage `0.847`, under-coverage `0.063`, over-coverage `0.090`, mean width
`77626.54` invocation counts. Coverage is conservative/wide on this trace.

## Artifacts

- `results/forecast/azure2019_total/predictions.csv`
- `results/forecast/azure2019_total/metrics.json`
- `results/forecast/azure2019_total/run_manifest.json`
- `results/forecast/azure2019_total/checkpoint.pt` (gitignored)
- `results/forecast/azure2019_total/feature_columns.json`
- `results/forecast/azure2019_total/scaler.json`
- `results/forecast/azure2019_total/plots/`: `actual_vs_predicted.png`,
  `peak_zoom.png`, `error_over_time.png`, `residual_distribution.png`,
  `metrics_comparison_absolute.png`, `metrics_comparison_wape.png`,
  `peak_underprediction.png`, `horizons_side_by_side.png`,
  `learning_curve.png`, `prediction_interval_coverage.png`.

## Test coverage

- T01/T02: history length and horizon shape.
- T03: chronological splits and non-overlapping windows; raw test IDs support baselines.
- T04: core metrics plus extended metrics, zero handling, interval calibration/coverage.
- F01: invalid/stale/non-finite input and model-error fallback paths.
- M2 artifact test: four models evaluated, CSV/JSON/checkpoint/plots written.
- Full suite result: `py -m pytest -q` → **120 passed, 1 warning** (pre-existing ingestion date-format warning).

## Limitations and next steps

- Historical Azure invocation counts are real, but latency, CPU, energy, cold starts, and SLA outcomes are absent; no such measurements are claimed.
- TFT was trained only once (seed 42). Multi-seed distributions and rolling-origin folds remain M9 work.
- Only `total` aggregation was trained; `by_app`/`top_k_total` remain unvalidated at official scale from M1.
- Peak underprediction is unresolved; investigate log-target training, longer training, or a peak-aware loss before relying on TFT for burst control.
- No live deployment, Prometheus/Grafana, or Qwen3/PPO integration was exercised in M2.
- Next milestone: M3 (Qwen3 planner with strict schema, timeout, and fallback).
