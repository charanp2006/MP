# Milestone 7 — Monitoring and Feedback

| Field | Value |
|---|---|
| Milestone | M7 — Monitoring/feedback |
| Status | Complete for local exporter, alerts, feedback records and dashboard provisioning; live dashboard validation pending |
| Date | 2026-11-20 |
| Branch | `feat/m7-monitoring-feedback` |
| Related commit | `1ac69d4` (base; M7 changes uncommitted) |
| Test IDs | I05, I06, F04, F05, S01–S06 |
| Architecture layers | Layer 10 execution boundary; Layer 11 monitoring/feedback |
| Evidence class | Local HTTP/injected-query unit tests + dry-run simulation; **no deployed dashboard or live telemetry** |

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
- **Scaffolding only:** `docker-compose.yml`, Prometheus configs and Grafana
  provisioning were not started against a deployed system. No live dashboard
  screenshot, scrape history or production telemetry is claimed.
- **Pending:** run the exporter alongside a deployed OpenFaaS/Kubernetes
  runtime, start Prometheus/Grafana via compose, verify the dashboard with live
  metrics, record F04/F05 live failure evidence, and feed live Prometheus
  values into the next control cycle in M8.
- **Safety:** monitoring remains read-only. Stale metrics are surfaced as
  alerts/readiness failures and never silently replaced with fabricated live
  measurements.
