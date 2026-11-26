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
| [docs/PROJECT_STATUS_SUMMARY.md](docs/PROJECT_STATUS_SUMMARY.md) | Consolidated summary of all completed work, live G/H evidence, limitations and delivery metadata |
| [IMPLEMENTATIONV2.md](IMPLEMENTATIONV2.md) | Forward-looking V2 implementation plan with stricter evidence and evaluation requirements |
| [docs/implementationv2/m0-audit.md](docs/implementationv2/m0-audit.md) | V2 M0 audit and V1↔V2 crosscheck: completed V1 work and remaining V2 gaps |
| [docs/azure-dataset-availability.md](docs/azure-dataset-availability.md) | Local Azure dataset inventory, Git visibility, provenance and regeneration commands |
| [docs/qwen3-hosted-inference-plan.md](docs/qwen3-hosted-inference-plan.md) | Hosted Hugging Face Qwen3 primary path and OpenRouter backup plan; explains why the local llama/Ollama plan is outdated |
| [docs/qwen3-hf-smoke-verification-guide.md](docs/qwen3-hf-smoke-verification-guide.md) | Beginner guide to HF concepts, endpoint deployment and real Qwen3 smoke verification |
| [docs/git-ignored-inventory.md](docs/git-ignored-inventory.md) | Exact ignored files/folders inventory with sizes, ignore rules and handling guidance |
| [docs/ai-driven-decision-engine-dashboard.html](docs/ai-driven-decision-engine-dashboard.html) | Unified TFT + Qwen3 + PPO decision engine dashboard (roles, handoffs, safety, evidence) |
| [docs/forecasting-dashboard.html](docs/forecasting-dashboard.html) | TFT workload-forecasting dashboard (trained forecaster + baselines, offline evidence) |
| [docs/agentic-planning-dashboard.html](docs/agentic-planning-dashboard.html) | Qwen3 planner dashboard (adapter/safety evidence; hosted inference unavailable, local Transformers smoke evidence available) |
| [docs/ppo-controller-dashboard.html](docs/ppo-controller-dashboard.html) | PPO controller dashboard (smoke training, simulated evaluation evidence) |
| [docs/implementation/](docs/implementation/README.md) | Versioned per-phase implementation records (P1–P6) — [P3 hosted Qwen3](docs/implementation/p3-v1.3-hosted-qwen3-adapter.md), [P3 local Transformers](docs/implementation/p3-v1.5-local-transformers-runtime.md), [P3 hosted verification prep](docs/implementation/p3-v1.6-hosted-qwen3-verification.md), [P4 execution](docs/implementation/p4-v1.1-execution.md), [P6 live G/H](docs/implementation/p6-v1.1-live-execution-and-monitoring.md) |
| [docs/runbooks/live-g-h.md](docs/runbooks/live-g-h.md) | Exact commands to deploy and verify live Kubernetes/OpenFaaS execution and in-cluster monitoring |
| [AGENTS.md](AGENTS.md) | Guidance for AI coding agents and contributors |
| [configs/project.yaml](configs/project.yaml) | Experiment configuration defaults (single source of truth) |

A compact summary is archived in `docs-simpler/` on the `files` branch.

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
- **Status:** Phase 1 — design & documentation complete; P1–P6 implemented, including local live G/H validation.

## Status / roadmap

Documentation and design are complete. Implementation follows `docs/design.md` §24 (data pipeline → baseline → monitoring → TFT → PPO → SLA reward → Qwen3 planning → validators → Kubernetes/OpenFaaS integration → experiments → dashboards → ablation/evaluation). All v1 phases P1–P6 and C1/C2/C7 prototypes are implemented; P6 adds local live Kubernetes/OpenFaaS execution and Prometheus/Grafana feedback while preserving dry-run defaults. V2 now targets hosted Qwen3 and stricter evaluation; see [IMPLEMENTATIONV2.md](IMPLEMENTATIONV2.md), [docs/implementation/](docs/implementation/README.md) and [docs/PROJECT_STATUS_SUMMARY.md](docs/PROJECT_STATUS_SUMMARY.md).

## Notes

- The `files` branch archives media: project images, the final presentation
  (`Predictive-Container-Management-for-Energy-Efficient-Serverless-Computing.pptx`)
  and the compact `docs-simpler/` set — do not edit it.
- The `docs` branch contains the research survey (26 PDFs) and older
  presentation material. See [docs/references.md](docs/references.md) for the
  recommended papers.
- The project is a research prototype: numerical improvements are targets, not pre-existing results.