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
- Reproducibility metadata is recorded in `metrics.json`; the previously listed `run_manifest.json` is not present in this checkout.
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
