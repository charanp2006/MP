# Predictive Container Management for Energy-Efficient Serverless Computing

> An Agentic AI and Transformer-Based Framework for Intelligent and Energy-Efficient Container Management in Serverless Computing.

Predictive, autonomous container management for serverless computing. The system combines a **Temporal Fusion Transformer (TFT)** for workload forecasting, **Qwen3** for agentic high-level planning, **PPO** for fast SLA-aware control, and **Kubernetes / OpenFaaS / Docker** for execution, closing the loop with **Prometheus / Grafana** monitoring.

**Core objective:** reduce unnecessary resource/energy consumption and cold-start impact while maintaining the defined SLA (P95 latency).

```
Minimize  E + αL + βCS + γC
subject to  P95 latency ≤ SLA target
```

## System at a glance

```
Workload traces → Preprocessing → TFT forecast → Qwen3 plan
    → PPO action → Validation / SLA guard → Kubernetes + OpenFaaS → Prometheus → feedback
```

No single AI component has unrestricted control of infrastructure — every action is validated, bounds-checked and authorized.

## Documentation

Start with the complete specification:

| Document | Description |
| --- | --- |
| [project.md](project.md) | Complete project specification (overview, architecture, design, requirements, security, testing, evaluation, roadmap) |
| [docs/prd.md](docs/prd.md) | Product requirements, scope, SLA and reward model |
| [docs/architecture.md](docs/architecture.md) | Layered architecture, data flow, failure & deployment design |
| [docs/design.md](docs/design.md) | Module layout, schemas, training/design details, implementation order |
| [docs/security.md](docs/security.md) | Threat model, trust boundaries, RBAC, action allowlist, audit |
| [docs/test_plan.md](docs/test_plan.md) | Test strategy, system scenarios, baselines, ablation, metrics |
| [docs/validation-report.md](docs/validation-report.md) | Image-vs-docs audit + implementation-readiness checklist |
| [docs/references.md](docs/references.md) | Recommended research papers mapped to components |
| [docs/tech-stack.md](docs/tech-stack.md) | Technology stack, tools and per-stage mapping |
| [docs/implementation/](docs/implementation/README.md) | Versioned per-phase implementation records (P1–P4) — [P4 execution](docs/implementation/p4-v1.0-execution.md) |
| [AGENTS.md](AGENTS.md) | Guidance for AI coding agents and contributors |
| [configs/project.yaml](configs/project.yaml) | Experiment configuration defaults (single source of truth) |

A compact summary of the same documents lives in [docs-simpler/](docs-simpler/).

## Objectives

- Workload forecasting with TFT (30-interval history → next 5–15 minutes).
- Agentic planning with Qwen3 over forecast, state and SLA.
- Proactive prewarm/scale before demand arrives, eliminating reactive cold starts.
- SLA protection: P95 latency is the primary constraint; violations carry the highest penalty.
- Energy optimization through reduced active/idle container time.
- Rigorous evaluation against a reactive autoscaling baseline.

**Indicative targets (not guaranteed):** 15–25% energy reduction, 20–30% cold-start reduction.

## Technology stack

| Layer | Tools |
| --- | --- |
| ML / AI | Python · PyTorch · TFT · Qwen3 · PPO |
| Infrastructure | Kubernetes · OpenFaaS · Docker |
| Observability | Prometheus · Grafana |
| Data | Azure Functions traces · Pandas · NumPy |

## Project metadata

- **Type:** Major Project — Phase 1 (academic / research prototype)
- **Institution:** Vidyavardhaka College of Engineering, Department of Computer Science and Engineering
- **Guide:** Dr. Tej C Hiremath
- **Team:** Charan P (4VV23CS042) · Darshan S Gowda (4VV23CS052) · Gaurav S G (4VV23CS074)
- **Status:** Phase 1 — design & documentation complete; implementation in progress (P1–P4 complete in simulation/dry-run).

## Status / roadmap

Documentation and design are complete. Implementation follows `docs/design.md` §24 (data pipeline → baseline → monitoring → TFT → PPO → SLA reward → Qwen3 planning → validators → Kubernetes/OpenFaaS integration → experiments → dashboards → ablation/evaluation). P1 (data pipeline), P2 (compact TFT + PPO in simulation), P3 (Qwen3/stub + validators + SLA guard + bounded loop), and P4 (bounded executor + allowlists + dry-run wiring) are implemented; see [docs/implementation/](docs/implementation/README.md).

## Notes

- The `files` branch archives media: project images, the final presentation
  (`Predictive-Container-Management-for-Energy-Efficient-Serverless-Computing.pptx`)
  and the compact `docs-simpler/` set — do not edit it.
- The `docs` branch contains the research survey (26 PDFs) and older
  presentation material. See [docs/references.md](docs/references.md) for the
  recommended papers.
- The project is a research prototype: numerical improvements are targets, not pre-existing results.