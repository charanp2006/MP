# M9 — Deferred Demonstration Integration

- **Phase:** M9
- **Doc version:** v1.0
- **Status:** Complete for simulated end-to-end demonstration integration; live deployment and final deck integration deferred
- **Date:** 2026-11-20
- **Related commit:** `0b7cb69` (base, uncommitted)
- **Test IDs:** T09-01 to T09-04
- **Architecture layers touched:** workload ingestion, control loop, execution/audit scaffolding, observability, demonstration packaging

## Objective

Provide a reproducible demonstration path for the deferred M9 components: a
clearly synthetic client, a generic and validated ingestion contract, several
small sample service definitions, and an end-to-end runner that produces
auditable artifacts without claiming live infrastructure validation.

## Module map

| Area | Files | Purpose |
|---|---|---|
| Synthetic client | `demo/synthetic_client.py` | Deterministic request-level events with service IDs, payload classes, bursts, timings, and no user identities |
| Generic ingestion | `data/generic_adapter.py`, `demo/ingestion_schema.json` (generated) | Validate untrusted records, optional token auth, aggregate to fixed-window traces |
| Sample services | `demo/services/app.py`, `demo/services/Dockerfile`, `demo/services/docker-compose.yml`, `demo/service_registry.json` | Three small service definitions for checkout/search/recommend; scaffolding only |
| Demo runner | `demo/run_end_to_end.py` | Generate -> ingest -> feature -> forecast/plan/control -> audit/feedback/alert -> report |
| Config | `configs/project.yaml` | `demo.*` defaults for scenario, steps, rate, seed, auth, and payload classes |
| Tests | `tests/test_m9_demo.py` | Client determinism/privacy, adapter validation/auth, artifact generation |

## Design and data contracts

- Event schema version: `m9-event-v1`.
- Required event fields: `timestamp`, `service_id`, `function_id`, `invocation_count`.
- Optional fields: `request_id`, `payload_class`, `execution_duration_ms`, `error_count`, `source`, `scenario`.
- Privacy rule: no user identity, request payload, or authentication data in persisted artifacts.
- Authentication: `demo.require_ingest_auth` can require a token from `demo.ingest_token_env`; the token is checked in memory and never written to artifacts.
- Aggregation: request events are floored to `demo.interval_s` windows and grouped by `function_id`; invocation/error counts are summed and resource/latency fields are simulated proxies.
- Warmup: `forecast.history_window`, feature lags, and rolling windows are honored before the control-loop replay so feature engineering does not consume the demo steps.
- Control: `execute=false`, executor is `simulator`, planner is `stub_proxy`, forecast defaults to persistence unless TFT is explicitly requested and available.
- Sample services are local container scaffolding only; no images were built, no compose stack was started, and no routes received live traffic.

## How to run and verify

```bash
py -m demo.run_end_to_end --out-dir results/demo/m9 --steps 4 --scenario mixed --seed 42
py -m pytest tests/test_m9_demo.py -ra
py -m pytest -ra
git diff --check
```

Optional local scaffolding command (not executed for this milestone):

```bash
docker compose -f demo/services/docker-compose.yml up --build
```

## Test coverage

- **T09-01:** synthetic client determinism, event-level output, allowed service IDs, and absence of identity/payload fields.
- **T09-02:** generic adapter validation and fixed-window trace aggregation.
- **T09-03:** token auth enforced from environment without persisting token data.
- **T09-04:** end-to-end runner writes manifest, schema, events, trace, routing, decisions, feedback, alerts, report, and figure.

Verification results:

- Focused M9 tests: `4 passed`.
- Full suite: `158 passed, 1 warning`.
- `git diff --check`: clean.
- CLI smoke: `2100` synthetic events over `35` generated windows, replayed for `4` control steps with seed `42`.

## Smoke artifacts

Generated under ignored `results/demo/m9/`:

- `run_manifest.json`, `report.md`, `ingestion_schema.json`
- `events.jsonl`, `trace.csv`, `routing.csv`
- `decision.jsonl`, `decision_records.jsonl`, `audit.jsonl`, `feedback.jsonl`, `alerts.jsonl`
- `figures/demo_timeline.png`

The smoke report contains a Mermaid control-flow diagram, simulated control summary, service routing table, and an eight-slide presentation storyboard.

## Measured vs simulated vs unimplemented

- **Simulated:** all requests, service traffic, resource proxies, latency, energy, capacity, decisions, audit, alert, and feedback values.
- **Stubbed:** Qwen3 planner is a stub proxy; TFT was not requested in the smoke run.
- **Unimplemented/deferred:** live Docker/OpenFaaS/Kubernetes deployment, live request routing, live Prometheus/Grafana scraping, final PPTX editing, and measured production performance.

## Limitations and next steps

- The generic adapter is a local validated SDK-style interface, not a deployed authenticated HTTP endpoint.
- Sample services share one parametrized image; they are demonstration scaffolding, not application implementations.
- The final PPTX and image assets remain archive material on the `files` branch and were not edited.
- Next: if requested, validate live container actions and scraping on a local stack; otherwise this milestone closes the deferred demonstration integration track.
