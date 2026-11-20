# Monitoring — Prometheus / Grafana / Feedback (M7)

This directory implements the bounded observability boundary for the control
loop. Prometheus scrapes a local exporter; Grafana is provisioned with a control
loop dashboard; feedback records and alerts are written as append-only JSONL
artifacts.

## Components

| File | Role |
|---|---|
| `metrics.py` | In-memory counters/gauges and Prometheus text serialization |
| `prometheus_exporter.py` | `/metrics`, `/health`, `/ready` HTTP endpoints |
| `prometheus_adapter.py` | Reads validated scalar metrics from Prometheus or an injected query function |
| `alerts.py` | Deterministic local alert evaluation and JSONL log |
| `feedback.py` | Bounded feedback signal plus per-cycle feedback records |
| `prometheus/prometheus.yml` | Scrape configuration for the exporter |
| `prometheus/alerts.yml` | Prometheus alert rules |
| `grafana/provisioning/` | Datasource and dashboard provisioning |
| `grafana/dashboards/control-loop.json` | Workload/infrastructure/performance/efficiency/control panels |
| `docker-compose.yml` | Local Prometheus + Grafana stack scaffolding |

## Run locally

```powershell
py -m monitoring.prometheus_exporter --config configs/project.yaml
docker compose -f monitoring/docker-compose.yml up -d
```

Prometheus expects the exporter at `127.0.0.1:8000`; Grafana is provisioned at
`127.0.0.1:3000`. Live scraping/dashboards were not started as part of the M7
implementation tests. All current verification is local and injected.

## Safety

Monitoring is read-only with respect to infrastructure. Stale or missing
metrics are reported, never silently replaced with invented live measurements.
The Prometheus adapter and alert manager are injectable for tests and default
to disabled where configuration is absent. See `configs/project.yaml ->
monitoring` and `docs/milestones/m7-monitoring-feedback.md`.
