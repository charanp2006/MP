# Implementation Documentation

This folder records **what was actually built** at the end of each project
phase, with a versioned, human-readable explanation. It complements the
design/spec docs (`project.md`, `docs/*.md`) — those describe *intent*; the
docs here describe *implemented reality*, including current limitations.

## Versioning convention (required from P1 onward)

Every completed phase (or standalone implementation milestone) gets its own
document. Filenames encode the phase and the document version:

```
p{N}-v{MAJOR}.{MINOR}-{slug}.md
```

| Part | Meaning |
|---|---|
| `p{N}` | Phase number (`p1` … `p5`), matching `plan.md` |
| `MAJOR` | Structural version of that phase's document (starts at `1`) |
| `MINOR` | Revision within the phase (`0` on first write; increment for corrections/additions) |
| `slug` | Short kebab-case topic |

Rules:

- **New phase → new file** (new `p{N}` + `v1.0`).
- **Updating a completed phase's doc → bump `MINOR`** and add a Changelog row
  (e.g. `p2-v1.0-…` → `p2-v1.1-…`). Keep the older file until the change is
  committed, then it may be replaced by the new version.
- Every phase doc starts with a **metadata header** and a **Changelog** table.
- Link the new doc here in the index and in `AGENTS.md` / `README.md` docs maps.
- Do not put numeric performance claims in these docs unless they are measured
  and reproducible; label smoke/sanity runs explicitly.

## Index

| Phase | Doc | Version | Status | Scope |
|---|---|---|---|---|
| P1 | [p1-v1.0-data-pipeline.md](p1-v1.0-data-pipeline.md) | v1.0 | Complete | Ingestion, preprocessing (D01–D04), feature engineering, pipeline |
| P2 | [p2-v1.0-workload-ingestion-and-prediction.md](p2-v1.0-workload-ingestion-and-prediction.md) | v1.0 | Complete | End-to-end ingestion→prediction, compact TFT, training/evaluation, integration |
| P3 | [p3-v1.2-decision-engine.md](p3-v1.2-decision-engine.md) | v1.2 | Complete for v1 runtime | Qwen3/stub planner, validators, SLA guard, bounded loop; hosted HF/OpenRouter path planned in V2 |
| P4 | [p4-v1.1-execution.md](p4-v1.1-execution.md) | v1.1 | Complete | Bounded executor (kubectl scale), allowlists, dry-run default, decision-loop wiring; P6 live backend note |
| P5 | [p5-v1.1-monitoring-feedback-experiments.md](p5-v1.1-monitoring-feedback-experiments.md) | v1.1 | Complete | Prometheus/Grafana scaffolds, feedback loop, baseline-vs-proposed, ablations; P6 live-wiring note |
| P6 | [p6-v1.1-live-execution-and-monitoring.md](p6-v1.1-live-execution-and-monitoring.md) | v1.1 | Complete | Live Kubernetes/OpenFaaS execution, live Prometheus/Grafana feedback, local live runbook |
| C1 | [c1-v1.0-synthetic-client-load-generator.md](c1-v1.0-synthetic-client-load-generator.md) | v1.0 | Complete | Replayable synthetic client/load generator, profile and CLI |
| C2 | [c2-v1.0-generic-workload-ingestion.md](c2-v1.0-generic-workload-ingestion.md) | v1.0 | Complete | Generic workload ingestion SDK/API with schema, auth, metrics and provenance |
| C7 | [c7-v1.0-sample-serverless-services.md](c7-v1.0-sample-serverless-services.md) | v1.0 | Complete | Three service behaviors, endpoints, Prometheus metrics, hardened image/Compose, registry and HTTP tests |

## Implementation V2 crosscheck

- [V2 M0 audit and V1↔V2 crosscheck](../implementationv2/m0-audit.md) — what was already complete in V1 and what remains for V2 implementation.
- [Azure dataset availability and provenance](../azure-dataset-availability.md) — local raw data, Git visibility and reproduction commands.
- [Qwen3 hosted inference plan](../qwen3-hosted-inference-plan.md) — Hugging Face primary and OpenRouter backup plan; not yet implemented.

See also: [`plan.md`](../../plan.md) for the phase-to-architecture mapping and
[`docs/PROJECT_STATUS_SUMMARY.md`](../PROJECT_STATUS_SUMMARY.md) for the consolidated project status.

## Template for a new phase doc

```markdown
# Phase N — <Title>

| Field | Value |
|---|---|
| Phase | N |
| Doc version | v1.0 |
| Status | Complete / In progress |
| Date | YYYY-MM-DD |
| Related commit | <hash> |
| Test IDs | <e.g. T01–T04> |
| Architecture layers touched | <e.g. Layer 1, Layer 2> |

## Changelog
| Version | Date | Change |
|---|---|---|
| v1.0 | YYYY-MM-DD | Initial record for Phase N |

## 1. Objective
## 2. What was built (module map)
## 3. Design / data contracts
## 4. How to run & verify
## 5. Test coverage
## 6. Limitations & next steps
```
