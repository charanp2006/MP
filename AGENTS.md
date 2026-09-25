# AGENTS.md

Guidance for AI coding agents / copilots working in this repository.

## What this project is

A **research prototype** (Major Project - Phase 1) for *predictive, autonomous
container management in serverless computing*. The system closes a control
loop:

```
Workload traces + runtime metrics
  -> preprocessing (fixed windows)
  -> TFT workload forecast
  -> Qwen3 agentic plan (high-level only)
  -> PPO control action (bounded)
  -> validation / SLA guard / authorization
  -> Kubernetes + OpenFaaS + Docker execution
  -> Prometheus/Grafana observation
  -> logging + feedback
```

Objective: `Minimize E + αL + βCS + γC` subject to `P95 latency <= SLA target`.

## Branch layout (important)

| Branch | Contents | Use |
|---|---|---|
| `main` | This repo's ground truth: `README.md`, `project.md`, `docs/`, `AGENTS.md`, `configs/`, `.gitignore` | Build/implement from here |
| `files` | Full archive: images, final PPTX, `docs-simpler/`, temp extracts | Media / archive only - do not edit |
| `docs` | Research papers (PDFs) + older/shorter Markdown documents | Research source material |

## Canonical decisions (do NOT change without a documented reason)

- **Forecast model:** Temporal Fusion Transformer (**TFT**), not PatchTST/generic Transformer.
- **Agentic planner:** **Qwen3**, high-level planning only - never gives infrastructure commands.
- **Controller:** **PPO** with the fixed action set `NoOp, PreWarm, ScaleOut, Reuse, ScaleIn, Terminate`.
- **Execution:** **Kubernetes + OpenFaaS + Docker** (not Knative).
- **Observability:** **Prometheus + Grafana**.
- **Dataset:** **Azure Functions traces** are the DATA SOURCE only, not the execution platform.
- **SLA:** P95 latency as the primary constraint; SLA violation carries the highest reward penalty.
- **Forecast settings (defaults):** history window 30, horizon 5, control interval 60 s
  (see `configs/project.yaml`).
- **Capacity bounds (defaults):** min 2, max 30, max change/cycle 5.
- **Persistence:** log what was predicted, planned, selected, executed, and what happened next.

## Documentation map

- `project.md` - complete consolidated specification (start here).
- `docs/prd.md` - requirements, scope, SLA, reward, risks.
- `docs/architecture.md` - layered architecture, control loop, failure design.
- `docs/design.md` - module layout, schemas, timer design, implementation order.
- `docs/security.md` - threat model, trust boundaries, RBAC, action allowlist.
- `docs/test_plan.md` - test strategy, system scenarios, baselines, ablations.
- `docs/validation-report.md` - image-vs-docs audit + implementation-readiness checklist.
- `docs/references.md` - recommended research papers mapped to components.
- `docs/tech-stack.md` - technology stack, tools and per-stage mapping.
- `configs/project.yaml` - experiment configuration defaults.

## How to implement (agreed order, from docs/design.md)

1. Data pipeline (`data/`) - ingestion, preprocessing, feature engineering.
2. Reactive baseline.
3. Monitoring (Prometheus/Grafana).
4. TFT training/evaluation (`forecasting/`).
5. PPO environment + reward (`rl/`).
6. SLA-aware reward/penalty.
7. Qwen3 planner + schemas/validator (`agent/`).
8. Action/SLA validators (`orchestrator/`).
9. Kubernetes/OpenFaaS integration (`infrastructure/`).
10. Controlled baseline vs proposed experiments (`experiments/`).
11. Dashboards + result reporting.
12. Ablation + final evaluation.

## Engineering rules

- Keep `configs/project.yaml` as the single source for experiment defaults.
- Use **chronological** train/validation/test splits - never random shuffle a
  time series.
- Never let Qwen3 or PPO issue arbitrary shell/Kubernetes commands; all
  actions pass schema + bounds + SLA + authorization checks.
- Assume external data and model output are **untrusted** until validated.
- Do not commit models, checkpoints, datasets, seeds, `.env` or credentials
  (see `.gitignore`).
- Numeric improvements (15-25% energy, 20-30% cold-start) are **targets**,
  never quoted as measured results.

## Verification

- Read `project.md` and the relevant `docs/*` file before touching that area.
- Follow `docs/test_plan.md` test IDs (U01-U12, D01-D04, T01-T04, Q01-Q06,
  R01-R04, I01-I06, S01-S06, F01-F06) when writing tests.
- After a change, run the project's tests/lint; if the project has no test
  runner yet, state how you verified instead.