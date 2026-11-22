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

# Milestone 7 — Monitoring and Feedback

| Field | Value |
|---|---|
| Milestone | M7 — Monitoring/feedback |
| Status | Complete (exporter/feedback/alerts/dashboard provisioning; live dashboard validated in P6) |
| Date | 2026-11-20 (refreshed 2026-11-21) |
| Branch | `feat/m7-monitoring-feedback` (merged); current work on `dev` |
| Related commit | `db8d8a6` (merge), `46fc391` (feature), `1cf3f4a` (P6 merge) |
| Test IDs | I05, I06, F04, F05, S01–S06 |
| Architecture layers | Layer 10 execution boundary; Layer 11 monitoring/feedback |
| Evidence class | Original: local HTTP/injected-query unit tests + dry-run simulation; refreshed: P6 live Prometheus/Grafana evidence |

## Objective

Complete the observe-measure-feedback portion of the control loop: expose
Prometheus metrics and health endpoints, provision a Grafana dashboard, persist
per-cycle feedback records, and evaluate alerts/failure conditions without
allowing monitoring to mutate infrastructure.

## Module map

| File | Role |
|---|---|
| `monitoring/metrics.py` | Safe in-memory counters/gauges and Prometheus text serialization |
| `monitoring/prometheus_exporter.py` | `/metrics`, `/health`, `/ready` with injectable adapter |
| `monitoring/prometheus_adapter.py` | Validated scalar queries with stale/missing detection |
| `monitoring/alerts.py` | Deterministic alert evaluation and JSONL alert log |
| `monitoring/feedback.py` | Feedback signal plus append-only feedback records |
| `orchestrator/decision_loop.py` | Integrates feedback records, execution failure metrics and alerts into `Decision` |
| `configs/project.yaml` | Exporter port, alert rules, feedback record settings, Grafana UID |
| `monitoring/prometheus/prometheus.yml` | Scrape jobs for exporter and Prometheus self-monitoring |
| `monitoring/prometheus/alerts.yml` | Local alert rules for P95, SLA, stale metrics and executor failure |
| `monitoring/grafana/provisioning/` | Prometheus datasource and dashboard provider |
| `monitoring/grafana/dashboards/control-loop.json` | Workload / infrastructure / performance / efficiency / control panels |
| `monitoring/docker-compose.yml` | Local Prometheus + Grafana stack scaffolding |
| `monitoring/README.md` | Updated operational guide |
| `tests/test_m7_monitoring.py` | M7 tests |
| `results/monitoring/feedback.jsonl` | Runtime feedback records (generated, ignored) |
| `results/monitoring/alerts.jsonl` | Runtime alert records (generated, ignored) |

## Design and data contracts

### Metrics endpoint

`py -m monitoring.prometheus_exporter` serves:

- `/metrics`: Prometheus text exposition from `MetricsCollector.snapshot()`.
- `/health`: JSON with status and metric count.
- `/ready`: JSON readiness; returns HTTP 503 when an enabled adapter reports
  stale/missing metrics (`F05`).

`MetricsCollector.inc()`, `set_gauge()` and `observe()` now respect
`monitoring.enabled`, so disabled monitoring remains inert. Execution failures
increment `execution_failures_total` only when monitoring is enabled.

### Feedback record

Each cycle appends one JSON object to `monitoring.feedback.record_path` with
`correlation_id`, `source`, `forecast_source`, `final_action`, `p95_latency_ms`,
`sla_violated`, `cold_starts`, `energy_w`, `capacity`, `reward`,
`feedback_signal` and UTC timestamp. Values are scalar-bounded and redacted
against non-basic types. The existing caution/violation-rate/P95-trend signal
is preserved.

### Alert contract

`AlertManager.evaluate()` returns bounded JSON objects with `name`, `severity`,
`value`, `threshold`, `correlation_id`, `message` and `raised_at`. Rules detect:

- P95 within the SLA safety margin.
- SLA violation rate above threshold.
- Stale/missing metrics (`F05`).
- Executor failure (`F04` support).
- Feedback degradation.

Alerts are appended to `monitoring.alerts.log_path` and also embedded in
`Decision.to_dict()["alerts"]` for provenance.

### Dashboard

The provisioned Grafana dashboard covers actual workload, P95 with SLA line,
active containers, energy, cold starts, SLA violations, action frequency and
exporter availability. Prometheus alert rules use the same exporter metric
names where possible.

## How to run and verify

```powershell
py -m py_compile monitoring/feedback.py monitoring/alerts.py monitoring/metrics.py monitoring/prometheus_adapter.py monitoring/prometheus_exporter.py monitoring/__init__.py orchestrator/decision_loop.py tests/test_m7_monitoring.py
py -m pytest tests/test_m7_monitoring.py tests/test_monitoring.py tests/test_m6_execution.py tests/test_m5_decision_engine.py tests/test_orchestrator.py -ra
py -m monitoring.prometheus_exporter --config configs/project.yaml
docker compose -f monitoring/docker-compose.yml up -d
py -m pytest -ra
```

Focused verification: `42 passed in 8.83s`. The exporter tests start a local
ephemeral HTTP server only; they do not require Prometheus, Grafana, Docker or
a cluster.

## Test coverage

| Test | Purpose | Result |
|---|---|---|
| `test_feedback_records_are_persisted` | Append/read feedback record schema | Passed |
| `test_alert_manager_detects_failure_conditions` | All five alert rules + alert log | Passed |
| `test_exporter_serves_metrics_health_and_ready` | Local `/metrics`, `/health`, `/ready` | Passed |
| `test_exporter_ready_fails_on_stale_metrics` | F05 readiness = 503 on stale metrics | Passed |
| `test_decision_loop_records_feedback_and_alerts` | I05/I06 local integration through `Decision` | Passed |
| `test_monitoring_artifacts_are_valid` | Dashboard JSON, Prometheus scrape config, alert rules | Passed |
| Existing `tests/test_monitoring.py` | Metrics/feedback backward compatibility | Passed |
| Existing M5/M6/orchestrator tests | No integration regression | Passed |

## Evidence, limitations and next steps

- **Measured here:** unit tests, compile checks, local HTTP responses and JSONL
  record creation. No performance improvement is claimed.
- **Simulated:** feedback/reward/latency values from `ServerlessEnv` remain
  research surrogates; feedback records label their source (`simulated` by
  default).
- **Original M7 scope:** `docker-compose.yml`, Prometheus configs and Grafana
  provisioning were local scaffolding; no live dashboard or production telemetry
  was claimed.
- **P6 refresh (2026-11-21):** kube-prometheus-stack and the in-cluster
  `control-loop-exporter` were deployed on Docker Desktop Kubernetes. Live
  Prometheus queries fed `DecisionLoop`, stale metrics forced `NOOP`, and the
  `control-loop-live` Grafana dashboard was provisioned and verified. See
  `../implementation/p6-v1.1-live-execution-and-monitoring.md` and
  `../runbooks/live-g-h.md`.
- **Still not measured:** production telemetry, Qwen3 planner latency and
  percentage energy/latency improvements.
- **Safety:** monitoring remains read-only. Stale metrics are surfaced as
  alerts/readiness failures and never silently replaced with fabricated live
  measurements.
