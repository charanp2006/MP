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
| P3 | [p3-v1.0-decision-engine.md](p3-v1.0-decision-engine.md) | v1.0 | Complete | Qwen3/stub planner, state builder, plan/action validators, SLA guard, bounded loop |
| P4 | _(planned)_ | — | Not started | Docker/OpenFaaS/Kubernetes execution |
| P5 | _(planned)_ | — | Not started | Prometheus/Grafana, feedback loop, experiments/ablation |

See also: [`plan.md`](../../plan.md) for the phase-to-architecture mapping.

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
