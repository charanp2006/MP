# Monitoring (P5) — Prometheus & Grafana

The in-memory `MetricsCollector` provides counters/gauges and a Prometheus text export (`export_prometheus_text`) for simulation runs. `FeedbackLoop` computes a bounded caution/violation-rate/P95-trend signal from recent steps and is the current source of feedback.

**Current state:** in-memory only, disabled by default.  
**Future work:** real Prometheus scraping, Grafana dashboards and alerts, and tighter feedback integration into planning/control.

See `configs/project.yaml` → `monitoring:` and `docs/implementation/p5-v1.0-monitoring-feedback-experiments.md`.
