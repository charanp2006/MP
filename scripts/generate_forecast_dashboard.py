from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

MODEL_LABELS = {
    "tft": "TFT (trained)",
    "persistence": "Persistence",
    "seasonal_persistence": "Seasonal persistence",
    "moving_average": "Moving average",
}
MODEL_NOTES = {
    "tft": "Trained compact PyTorch TFT; selected best-validation checkpoint.",
    "persistence": "Not trained; repeats the last observed invocation count.",
    "seasonal_persistence": "Not trained; reuses the value from seasonal_period=1440 steps.",
    "moving_average": "Not trained; repeats the 5-step moving average.",
}
METRIC_LABELS = {
    "mae": "MAE",
    "rmse": "RMSE",
    "mape": "MAPE %",
    "wape": "WAPE %",
    "smape": "sMAPE %",
    "bias": "Bias",
    "peak_underprediction_rate": "Peak underpred.",
}
PCT_FIELDS = {"mape", "wape", "smape"}
LOWER_BETTER = {"mae", "rmse", "mape", "wape", "smape", "peak_underprediction_rate"}

STYLE = """
<style>
:root { color-scheme: dark; --bg:#0c0f14; --panel:#151a21; --line:#2b333e; --text:#e8eef7; --muted:#94a3b8; --accent:#7dd3fc; --good:#86efac; --warn:#fcd34d; --bad:#fca5a5; }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--text); font-family:Inter,Segoe UI,Arial,sans-serif; line-height:1.5; }
.wrap { max-width:1280px; margin:0 auto; padding:32px 24px 72px; }
h1 { margin:0 0 8px; font-size:2rem; }
h2 { margin:38px 0 14px; font-size:1.25rem; color:var(--accent); }
h3 { margin:0 0 8px; font-size:1rem; }
p, li { color:var(--muted); }
.sub { color:var(--muted); margin-bottom:28px; }
.cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:14px; }
.card { background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:16px; }
.card span { display:block; color:var(--muted); font-size:.78rem; text-transform:uppercase; letter-spacing:.06em; }
.card strong { display:block; margin-top:6px; font-size:1.05rem; word-break:break-all; }
table { width:100%; border-collapse:collapse; background:var(--panel); border:1px solid var(--line); border-radius:12px; overflow:hidden; }
th, td { padding:10px 12px; border-bottom:1px solid var(--line); text-align:right; font-variant-numeric:tabular-nums; }
th:first-child, td:first-child { text-align:left; }
th { color:var(--accent); font-size:.85rem; text-transform:uppercase; letter-spacing:.04em; }
tbody tr:last-child td { border-bottom:0; }
.best { color:var(--good); font-weight:700; }
.bad { color:var(--bad); }
.warn { color:var(--warn); }
.grid2 { display:grid; grid-template-columns:repeat(auto-fit,minmax(420px,1fr)); gap:18px; }
.gallery { display:grid; grid-template-columns:repeat(auto-fit,minmax(360px,1fr)); gap:16px; }
figure { margin:0; background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:12px; }
figure img { width:100%; height:auto; border-radius:8px; background:white; }
figcaption { margin-top:8px; color:var(--muted); font-size:.9rem; }
code { background:#0a0d12; border:1px solid var(--line); border-radius:6px; padding:2px 6px; color:var(--good); }
pre { background:#0a0d12; border:1px solid var(--line); border-radius:10px; padding:14px; overflow:auto; }
ol { padding-left:22px; }
.tag { display:inline-block; padding:3px 9px; border:1px solid var(--line); border-radius:999px; color:var(--muted); font-size:.8rem; margin-right:6px; }
.footer { margin-top:42px; color:var(--muted); font-size:.85rem; border-top:1px solid var(--line); padding-top:18px; }
</style>
"""


def _esc(value) -> str:
    return html.escape(str(value))


def _num(value, field: str | None = None) -> str:
    if value is None:
        return "n/a"
    number = float(value)
    if field in PCT_FIELDS:
        return f"{number:.2f}%"
    if field == "peak_underprediction_rate":
        return f"{number * 100:.1f}%"
    if abs(number) >= 1000:
        return f"{number:,.1f}"
    return f"{number:.4f}"


def _best_by_field(models: dict, subset: str) -> dict:
    best: dict[str, tuple[str, float]] = {}
    for name, payload in models.items():
        values = payload.get(subset, {})
        for field, value in values.items():
            if field not in METRIC_LABELS or value is None:
                continue
            score = abs(float(value)) if field == "bias" else float(value)
            if field not in best or score < best[field][1]:
                best[field] = (name, score)
    return {field: name for field, (name, _) in best.items()}


def _table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{_esc(item)}</th>" for item in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _metric_table(models: dict, subset: str, best: dict, fields: list[str]) -> str:
    rows = []
    for name, payload in models.items():
        values = payload.get(subset, {})
        cells = [_esc(MODEL_LABELS.get(name, name))]
        for field in fields:
            text = _num(values.get(field), field)
            if best.get(field) == name:
                text = f'<span class="best">{text}</span>'
            cells.append(text)
        rows.append(cells)
    return _table(["Model"] + [METRIC_LABELS[field] for field in fields], rows)


def _card(label: str, value) -> str:
    return f'<div class="card"><span>{_esc(label)}</span><strong>{_esc(value)}</strong></div>'


def build_dashboard(metrics: dict, image_prefix: str) -> str:
    models = metrics["models"]
    data = metrics["data"]
    training = metrics["training"]
    interval = metrics["interval"]
    reproducibility = metrics["reproducibility"]
    overall_best = _best_by_field(models, "overall")
    peak_best = _best_by_field(models, "peak")
    fields = ["mae", "rmse", "mape", "wape", "smape", "bias", "peak_underprediction_rate"]
    split_rows = [
        [name, f"{count:,}"]
        for name, count in [
            ("Train", data["rows"]["train"]),
            ("Validation", data["rows"]["val"]),
            ("Test", data["rows"]["test"]),
        ]
    ]
    split_range_rows = [
        [name, data["split_ranges"][key][0], data["split_ranges"][key][1]]
        for name, key in [("Train", "train"), ("Validation", "val"), ("Test", "test")]
    ]
    best_epoch = min(
        range(len(training["val_loss"])), key=lambda index: training["val_loss"][index]
    )
    loss_rows = [
        [
            str(index + 1),
            _num(train_loss),
            _num(val_loss),
            "best" if index == best_epoch else "",
        ]
        for index, (train_loss, val_loss) in enumerate(
            zip(training["train_loss"], training["val_loss"])
        )
    ]
    tft_horizon_rows = []
    for step in range(1, int(data["horizon"]) + 1):
        values = models["tft"]["by_horizon"][str(step)]
        tft_horizon_rows.append(
            [str(step)] + [_num(values.get(field), field) for field in fields]
        )
    interval_rows = [
        ["alpha", _num(interval.get("alpha"))],
        ["coverage", _num(interval.get("coverage"))],
        ["under-coverage rate", _num(interval.get("under_coverage_rate"))],
        ["over-coverage rate", _num(interval.get("over_coverage_rate"))],
        ["mean interval width", _num(interval.get("mean_interval_width"))],
    ]
    roster_rows = [
        [
            MODEL_LABELS.get(name, name),
            "Yes" if name == "tft" else "No",
            MODEL_NOTES.get(name, ""),
        ]
        for name in models
    ]
    plot_names = [
        ("actual_vs_predicted.png", "Actual vs predicted"),
        ("peak_zoom.png", "Peak zoom"),
        ("error_over_time.png", "Error over time"),
        ("residual_distribution.png", "Residual distribution"),
        ("metrics_comparison_absolute.png", "Absolute metric comparison"),
        ("metrics_comparison_wape.png", "WAPE comparison"),
        ("peak_underprediction.png", "Peak underprediction"),
        ("horizons_side_by_side.png", "Horizon-by-horizon forecasts"),
        ("learning_curve.png", "Training / validation loss"),
        ("prediction_interval_coverage.png", "Interval coverage"),
    ]
    gallery = "".join(
        f'<figure><img src="{_esc(image_prefix)}/{_esc(filename)}" alt="{_esc(caption)}">'
        f"<figcaption>{_esc(caption)}</figcaption></figure>"
        for filename, caption in plot_names
    )
    runtime_input_example = json.dumps(
        {
            "history_window": f"float32[{data['history']}][{len(data['feature_columns'])}]",
            "feature_columns": data["feature_columns"],
            "observed_at": "2026-11-20T09:00:00+00:00",
            "max_staleness_s": 300,
        },
        indent=2,
    )
    runtime_output_example = json.dumps(
        {
            "forecast_horizon": data["horizon"],
            "predicted_workload": [520.0, 548.0, 571.0, 559.0, 603.0],
            "trend": "increasing",
            "source": "tft",
            "fallback": False,
            "fallback_reason": None,
            "model_id": metrics["model"]["name"],
            "checkpoint_path": metrics["model"]["checkpoint"],
            "feature_columns": data["feature_columns"],
            "observed_at": "2026-11-20T09:00:00+00:00",
        },
        indent=2,
    )
    fallback_output_example = json.dumps(
        {
            "forecast_horizon": data["horizon"],
            "predicted_workload": [520.0] * data["horizon"],
            "trend": "stable",
            "source": "fallback_persistence",
            "fallback": True,
            "fallback_reason": "stale_input: age=412.0s > 300.0s",
            "model_id": metrics["model"]["name"],
        },
        indent=2,
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Forecast Model Dashboard</title>
{STYLE}
</head>
<body>
<div class="wrap">
<h1>Forecast Model Dashboard</h1>
<p class="sub">Azure Functions 2019 total invocation trace &middot; run <code>{_esc(metrics['run_id'])}</code> &middot; evidence: historical invocation counts, no measured latency/energy</p>

<div class="cards">
  {_card("Trained model", "compact TFT (PyTorch)")}
  {_card("Tested models", "TFT + 3 deterministic baselines")}
  {_card("History / horizon", f"{data['history']} / {data['horizon']} steps")}
  {_card("Control interval", f"{reproducibility['interval_seconds']} s")}
  {_card("Test targets", f"{int(models['tft']['overall']['n']):,}")}
  {_card("Best validation loss", f"{training['best_val_loss']:.6f}")}
</div>

<h2>1. What was trained and what was tested</h2>
{_table(["Model", "Trained?", "Design"], roster_rows)}
<p><span class="tag">trained</span> Only the TFT has learned weights. The three baselines are deterministic rules evaluated on the exact same chronological test rows.</p>

<h2>2. How the model was designed</h2>
<div class="grid2">
<div class="card">
<h3>Compact TFT</h3>
<ul>
<li>PyTorch implementation with variable selection, GRN, LSTM encoder and attention.</li>
<li><code>d_model={metrics['model']['model_config']['d_model']}</code>, <code>heads={metrics['model']['model_config']['attention_heads']}</code>, <code>dropout={metrics['model']['model_config']['dropout']}</code>, variable selection <code>{metrics['model']['model_config']['variable_selection']}</code>.</li>
<li>Input window: {data['history']} steps; output: {data['horizon']} future invocation-count steps.</li>
<li>Features: <code>{', '.join(data['feature_columns'])}</code>.</li>
</ul>
</div>
<div class="card">
<h3>Baselines and inference service</h3>
<ul>
<li>Persistence: repeat last observed value.</li>
<li>Seasonal persistence: value from 1440 steps earlier, with persistence fallback.</li>
<li>Moving average: mean of last 5 steps.</li>
<li><code>TFTForecastService</code> loads the checkpoint, validates feature order, and falls back to persistence for stale, non-finite, or model-error inputs.</li>
</ul>
</div>
</div>

<h2>3. Input / output contract and live-use boundary</h2>
<p><span class="tag">contract only</span> The forecast service exists today, but live telemetry wiring, cluster execution and Grafana-backed measurements are not validated in this experiment. This section describes what a live adapter must provide and what the controller receives.</p>
<div class="grid2">
<div class="card">
<h3>Training input</h3>
<ul>
<li>Official Azure prepared trace CSV with <code>timestamp</code>, <code>function_id</code>, <code>invocation_count</code> and engineered calendar features.</li>
<li>Chronological windows: {data['history']} observed steps &rarr; {data['horizon']} future targets.</li>
<li>Only historical invocation counts are real; no measured CPU, memory, latency or energy.</li>
</ul>
</div>
<div class="card">
<h3>Live/inference input</h3>
<ul>
<li>Telemetry events: timestamp, service/function ID, invocation count, duration, error count, resource fields and source metadata.</li>
<li>Generic adapter aggregates events into fixed {reproducibility['interval_seconds']}s windows.</li>
<li><code>TFTForecastService.forecast_history()</code> requires a 2D <code>history_window</code> with exact feature order and an optional <code>observed_at</code> timestamp.</li>
<li>Input rejected/fallback when non-finite, wrong shape, wrong feature count, or stale beyond <code>max_staleness_s</code>.</li>
</ul>
</div>
</div>
{_table(["Runtime input", "Type / shape", "Purpose"], [
    ["history_window", f"float32[{data['history']}][{len(data['feature_columns'])}]", "Recent normalized feature rows in chronological order"],
    ["feature_columns", "list[str]", "Validates feature order against the checkpoint"],
    ["observed_at", "ISO-8601 timestamp", "Used for freshness/staleness checks"],
    ["max_staleness_s", "float", "Rejects old observations and triggers persistence fallback"],
])}
<pre>{_esc(runtime_input_example)}</pre>
<p><strong>Live path:</strong> telemetry events &rarr; generic ingestion adapter &rarr; fixed-window trace &rarr; feature builder &rarr; forecast service &rarr; planner/PPO &rarr; safety shield &rarr; executor adapter. The forecast returns advisory workload values only; it never issues infrastructure commands.</p>
{_table(["Output field", "Type", "Meaning used by the decision loop"], [
    ["forecast_horizon", "int", "Number of future control steps covered"],
    ["predicted_workload", "list[float]", f"{data['horizon']} forecast invocation counts"],
    ["trend", "increasing/decreasing/stable", "Compact directional summary"],
    ["source", "tft or fallback_persistence", "Whether the model or deterministic fallback produced values"],
    ["fallback / fallback_reason", "bool / str|null", "Audit trail for degraded inference"],
    ["model_id / checkpoint_path", "str", "Model provenance"],
    ["feature_columns / observed_at", "list[str] / str", "Input-order and freshness provenance"],
])}
<pre>{_esc(runtime_output_example)}</pre>
<p><strong>Fallback example</strong> (stale input):</p>
<pre>{_esc(fallback_output_example)}</pre>

<h2>4. How it was trained</h2>
<div class="cards">
{_card("Epochs", training['config']['epochs'])}
{_card("Batch size", training['config']['batch_size'])}
{_card("Learning rate", training['config']['learning_rate'])}
{_card("Optimizer / loss", "Adam / MSE")}
{_card("Gradient clipping", "1.0")}
{_card("Seed", training['seed'])}
</div>
<p>Chronological split <code>{training['config']['split']}</code>. Scaler fit on train rows only. Training batches are shuffled within the train split; windows never cross split boundaries. Best validation checkpoint restored before testing.</p>
{_table(["Split", "Windows"], split_rows)}
{_table(["Split", "Start (UTC)", "End (UTC)"], split_range_rows)}
{_table(["Epoch", "Train MSE", "Validation MSE", "Selected"], loss_rows)}

<h2>5. How it was tested</h2>
<p>All four models were evaluated on the same <strong>{int(models['tft']['overall']['n']):,} flattened test targets</strong> ({data['rows']['test']:,} windows &times; {data['horizon']} horizon steps). Metrics include MAE, RMSE, MAPE, WAPE, sMAPE, bias, and peak-underprediction rate. Peak subset is the top decile (<code>peak_quantile={reproducibility['peak_quantile']}</code>, n={int(models['tft']['peak']['n']):,}). Prediction intervals were calibrated on validation residuals at <code>alpha={interval['alpha']}</code>.</p>
<p>Unit/integration coverage: T01/T02 history and horizon shape, T03 chronological non-overlapping splits, T04 metrics/zero handling/interval calibration, F01 stale/non-finite/model-error fallback paths, and an artifact test confirming four models plus CSV/JSON/checkpoint/plots are written.</p>
{_table(["Replication item", "Value"], [
    ["Dataset SHA-256", data['sha256']],
    ["Config SHA-256", reproducibility['config_sha256']],
    ["Commit", metrics['commit']],
    ["Target column", data['target_column']],
    ["Interval seconds", reproducibility['interval_seconds']],
])}

<h2>6. Overall test results</h2>
{_metric_table(models, 'overall', overall_best, fields)}
<p class="warn">TFT is best on overall MAE/RMSE/WAPE/sMAPE, but its peak-underprediction rate is worse than persistence and seasonal persistence.</p>

<h2>7. Peak-subset results</h2>
{_metric_table(models, 'peak', peak_best, fields)}
<p class="bad">On the top-decile peak subset, persistence has the lowest WAPE ({_num(models['persistence']['peak']['wape'], 'wape')}) versus TFT ({_num(models['tft']['peak']['wape'], 'wape')}).</p>

<h2>8. TFT by forecast horizon</h2>
{_table(["Step"] + [METRIC_LABELS[field] for field in fields], tft_horizon_rows)}

<h2>9. Interval diagnostics</h2>
{_table(["Diagnostic", "Value"], interval_rows)}

<h2>10. Generated plots</h2>
<div class="gallery">{gallery}</div>

<h2>11. Limitations</h2>
<ul>
<li>Azure invocation counts are real historical data; CPU, memory, latency, cold starts and energy are not measured in this dataset.</li>
<li>TFT was trained once with seed 42; no multi-seed distribution or rolling-origin folds were run.</li>
<li>Only the <code>total</code> aggregation was trained and evaluated at official scale.</li>
<li>Peak underprediction remains a known weakness; do not rely on this checkpoint for burst control without further work.</li>
<li>No live deployment, Prometheus/Grafana, Qwen3, or PPO integration was exercised in this forecast experiment.</li>
</ul>

<h2>12. Reproduce</h2>
<pre>py -m scripts.evaluate_forecast \\
  --data-source azure_functions_2019 \\
  --out-dir results/forecast/azure2019_total \\
  --run-id azure2019_total_h30_h5 \\
  --epochs 8

py -m scripts.generate_forecast_dashboard</pre>

<div class="footer">Generated from <code>{_esc(metrics['artifacts']['metrics_json'])}</code>. Plots are read from <code>{_esc(image_prefix)}/</code>; rerun the evaluation command if those ignored artifacts are absent.</div>
</div>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the forecast model dashboard")
    parser.add_argument("--metrics", default="results/forecast/azure2019_total/metrics.json")
    parser.add_argument("--out", default="docs/forecasting-dashboard.html")
    parser.add_argument(
        "--image-prefix",
        default="../results/forecast/azure2019_total/plots",
    )
    args = parser.parse_args()

    metrics = json.loads(Path(args.metrics).read_text(encoding="utf-8"))
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_dashboard(metrics, args.image_prefix), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
