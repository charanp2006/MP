# Implementation Plan

Phase division for building the project, matched to the **8 steps** in
`final.png` (Complete Project Architecture). Consistent with
`project.md` §18 (agreed 12-step order) and `docs/design.md`.

## The 8 steps (from `final.png`)

1. **Users / Clients** — `API Gateway / Load Balancer` (E-commerce,
   Healthcare, Finance, Media & Streaming, IoT Applications).
2. **Workload** — request info: invocation rate, timestamp, user/session info.
3. **Workload Prediction (TFT)** — predicted workload for next 5/10/15 min
   (inputs: historical workload, system metrics, time features).
4. **Agentic AI Planning (Qwen3)** — analyze future demand → generate
   strategies (energy & SLA aware) → planned strategy (Pre-warm, Scale-out,
   Reuse, Scale-in, Terminate).
5. **Reinforcement Learning Controller (PPO)** — state in (predicted
   workload, real-time metrics, container state, SLA status, energy usage);
   reward = minimize energy + latency/cold starts + resource wastage.
6. **Serverless Execution** — `OpenFaaS` (serverless platform) + `Kubernetes`
   (orchestration) + `Docker` (container runtime) + function containers.
7. **Applications / Services** — the deployed microservices consuming the
   serverless functions.
8. **Monitoring & Feedback** — `Prometheus` (metrics collection) + `Grafana`
   (visualization) → feedback to AI engine (update models, refine agent
   planning, improve PPO policy, adapt to workload).

`final.png` also shows **Key Outcomes**: Energy Efficient, SLA Protection
(P95 latency), Reduced Cold Starts, Better Resource Utilization, Scalable &
Adaptive, Sustainable Cloud.

## Phase division matched to the 8 steps

| Phase | Image steps | Sub-phases | Merge / parallelism notes |
| --- | --- | --- | --- |
| **P0 — Scaffold** | (foundation for all 8) | package layout, config loader (`configs/project.yaml`), logging, pytest wiring, venv | Prerequisite for everything; cheap insurance |
| **P1 — Data pipeline** | **1 + 2 (merged)** | 1a: request/workload schema + trace ingestion; 1b: 60 s resample + cleaning (D01–D04); 1c: feature engineering (invocation rate, timestamp, session info, lag/rolling/temporal) | **Steps 1 & 2 are one flow** — the gateway delivers the workload; for the prototype both reduce to "ingest Azure-traces workload". The API-gateway layer itself is optional deployment context (project.md §9.6), represented by the trace source, not real infra |
| **P2 — Forecast + control in simulation** | **3 + 5 (parallel)** | **3a:** forecaster scaffolding + data loader; **3b:** TFT training (chronological splits, no leakage); **3c:** evaluation (MAE/RMSE/MAPE, T01–T04). **5a:** PPO env + action space; **5b:** base reward; **5c:** SLA-aware reward + guard (R01–R04) | **Steps 3 & 5 can be built simultaneously** — TFT training is standalone; PPO env + reward uses the same data/harness. Shared simulator. PPO state includes *predicted workload*, so the contract between 3 and 5 is just an interface, not a blocker |
| **P3 — Decision engine integration** | **4 + 5 (integrated)** | **4a:** Qwen3 prompt + structured plan schema; **4b:** plan/action validators + SLA guard (Q01–Q06); **4c:** wire planner → validator → PPO → guard in the simulator | **Steps 4 & 5 must integrate as one "AI-Driven Decision Engine"** — Qwen3 only emits high-level strategy consumed by PPO; never infrastructure commands. Joint end-to-end test in simulation before touching real pods. Step 4 cannot be validated meaningfully alone |
| **P4 — Execution + services** | **6 + 7 (merged)** | **6a:** Docker images + sample functions; **6b:** OpenFaaS deploy; **6c:** K8s manifests + RBAC + quotas; **6d:** executor → K8s API, authorized + bounded | **Steps 6 & 7 are validated together** — you cannot test the execution layer without something running on it. Use ~3 representative sample services (echo/load-generator stand-ins for the image's microservices). Prometheus exporters start here (prerequisite for step 8) |
| **P5 — Monitoring, feedback, experiments** | **8** | **8a:** Prometheus scrape (CPU/mem, request rate, latency, container count, energy, cold starts, SLA violations); **8b:** Grafana dashboards + alerts; **8c:** feedback loop → model updates / planning refinement / PPO improvement; then baseline vs proposed experiments + ablations + final report | **Step 8 closes the loop** over steps 3–5 and needs P4 running to generate real metrics. 8a overlaps P4 (scrape needs infra); 8c is the last thing and enables the final evaluation |

## Pipeline vs implementation order

- **Runtime (data) flow in the image is linear:** 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8.
- **Implementation order follows dependencies with parallelism:**
  `P0 → P1 → P2 (step 3 ‖ step 5 in parallel) → P3 → P4 → P5`.
- The only step with no phase of its own in isolation is **7** — deploying
  services is meaningless until the runtime exists, so it merges into P4.

## Mapping to the agreed 12-step order

| Agreed step (project.md §18) | Phase |
| --- | --- |
| 1. Data pipeline (ingestion, preprocessing, features) | P1 |
| 2. Reactive baseline | P2 (step 5 harness) |
| 3. Monitoring (Prometheus/Grafana) | P5 (8a/8b; exporters start P4) |
| 4. TFT training/evaluation | P2 (step 3) |
| 5. PPO environment + reward | P2 (step 5) |
| 6. SLA-aware reward/penalty | P2–P3 (5c + guard) |
| 7. Qwen3 planner + schemas/validator | P3 (step 4) |
| 8. Action/SLA validators | P3 (4b) |
| 9. Kubernetes/OpenFaaS integration | P4 (steps 6+7) |
| 10. Baseline vs proposed experiments | P5 |
| 11. Dashboards + result reporting | P5 (8b) |
| 12. Ablation + final evaluation | P5 |

## Reference configuration (initial defaults)

SLA `p95_latency_ms: 250`, `containers.min: 2`, `containers.max: 30`,
`max_change_per_cycle: 5`, forecast `history_window: 30`, `horizon: 5`,
control `interval_seconds: 60`, evaluation `repetitions: 5`
(single source of truth: `configs/project.yaml`).

## Rules that apply in every phase

- Keep `configs/project.yaml` as the single source for experiment defaults.
- Use **chronological** train/validation/test splits — never random-shuffle a
  time series.
- Never let Qwen3 or PPO issue arbitrary shell/Kubernetes commands; all
  actions pass schema + bounds + SLA + authorization checks (docs/security.md).
- Follow `docs/test_plan.md` test IDs (D01–D04, T01–T04, Q01–Q06, R01–R04,
  I01–I06, S01–S06, F01–F06) when writing tests.
- Numeric improvements (15–25% energy, 20–30% cold start) are **targets**,
  never quoted as measured results.
- Do not commit models, checkpoints, datasets, seeds, `.env` or credentials
  (see `.gitignore`).