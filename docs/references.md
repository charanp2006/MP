# Recommended Research Papers

This document lists the research papers most suitable for the project and
maps them to specific components. It is the result of a **title + abstract
audit of all 26 PDFs archived on the `docs` branch** (root, `New/` and
`New/Final/`), not just the six references cited in the presentation.

> The `docs` branch contains duplicates of two papers (``Sustainable
> Serverless Computing...`` and ``Taming Serverless Cold Start...`` appear in
> both the root and `New/` folders). Treat them as one paper each.

## Tiers

- **Tier 1 - Core:** directly matches the project's defining pillars
  (energy + SLA + cold start + RL/container lifecycle). Read first.
- **Tier 2 - Supportive:** strong partial overlap with one or two
  components (forecasting, scaling, RL policy, SLO management).
- **Tier 3 - Background/surveys:** context and baselines. Useful for
  related work, not for implementation design.

---

## Tier 1 - Core references

| Paper | Venue/Year | Why it fits | Maps to |
| --- | --- | --- | --- |
| Dynamic Management of Constrained Computing Resources for Serverless Services | IEEE TNSM, 2025 (DOI 10.1109/TNSM.2024.3497155) | Analysing container states (running/warm/cold) under SLA; multi-queue `AiW` balances energy vs SLA; `COME` reports 22-64% power reduction. **Closest paper to this project's energy + SLA + container-state objective.** | Energy model, container-state features, SLA-aware reuse, reward design, baselines |
| Deep Learning and Feedback Control Based Container Auto-Scaling for Cloud Native Micro-Services | IEEE TSC, 2025 (DOI 10.1109/TSC.2025.3596887) | Kubernetes-based elastic container allocation with prediction + feedback control and P95 response-time SLA. | Predictive autoscaling, Kubernetes implementation, P95 SLA control |
| Incendio: Priority-Based Scheduling for Alleviating Cold Start in Serverless Computing | IEEE TC, 2024 (DOI 10.1109/TC.2024.3386063) | Cold-start-caused latency; priority scheduling + prewarming + termination; RL-based scheduling. **Closest cold-start work.** | PreWarm/Terminate actions, planner guidance, cold-start metric |
| Tackling Cold Start in Serverless Computing with Multi-Level Container Reuse | IEEE IPDPS, 2024 (DOI 10.1109/IPDPS57955.2024.00017) | DRL scheduler for multi-level (similar-image) container reuse; up to 53% startup-latency reduction. | Reuse action, warm-pool sizing, DRL state/action design |
| Container-State-Aware Energy Consumption Minimization for Serverless Functions | IEEE TSC, 2026 | Container-state-aware energy model (idle/cold/running) with cold-start probability bound; Bayesian-optimization energy minimization. | Energy/request metric, capacity vs cold-start trade-off |
| Microservice Autoscaling With Fine-Grained DVFS in Dynamic Multi-Edge Collaboration via Deep Reinforcement Learning | IEEE TNSE, 2026 (DOI 10.1109/TNSE.2026.3691933) | DRL autoscaling jointly optimizing energy and latency with fine-grained frequency control. | PPO reward weighting (energy vs latency), edge scaling |
| Mitigating Cold Start Problem in Serverless Computing: A Reinforcement Learning Approach | IEEE IoT-J, 2023 | Two-layer RL + LSTM to learn invocation patterns and schedule pre-warming (12.7% memory reduction, 22.7% prewarms more). | PreWarm action timing, invocation prediction |
| FaaShare: Enabling Generic Low-Latency and SLO-Aware GPU Sharing in Serverless Computing | IEEE TPDS, 2026 | SLO-aware provisioning and pre-warming for low latency in serverless platforms. | SLA guard, pre-warming, SLO management |

## Tier 2 - Supportive references

| Paper | Venue/Year | Relevance |
| --- | --- | --- |
| Sustainable Serverless Computing With Cold-Start Optimization and Automatic Workflow Resource Scheduling | IEEE TSC, 2024 | Energy consumption + cold-start optimization via resource scheduling; good energy/cold-start trade-off reference. |
| A Deep Recurrent-Reinforcement Learning Method for Intelligent AutoScaling of Serverless Functions | IEEE TSC, 2024 | RRL for FaaS autoscaling under fluctuating workloads; RL policy for replica scaling. |
| Deep Reinforcement Learning for Scheduling Applications in Serverless and Serverful Hybrid Computing Environments | IEEE TSC, 2025 | DRL scheduling across serverless/serverful; action-space design and hybrid baselines. |
| MSARS: A Meta-Learning and RL Framework for SLO Resource Allocation and Adaptive Scaling for Microservices | 2025 (SIAT) | Meta-learning + RL for SLO resource allocation and adaptive scaling; transfer/adaptation ideas for the PPO policy. |
| Pre-warming: Alleviating Cold Start Occurrences on Cloud-based Serverless Platforms | 2023 | Dedicated pre-warming strategies and keep-alive decisions; informs prewarm heuristics. |
| Cold-Start-Aware Offloading and Resource Allocation by Importance-Sampling Double Dueling DQN in Serverless Edge Computing | IEEE IoT-J, 2025 | Cold-start-aware RL (Double Dueling DQN) for offloading/resource allocation - alternative RL algorithm baseline. |
| Blending Serverful and Serverless Cloud Resources for Cost-Effective Workflow Execution | IEEE TASE, 2026 | Cold-start cost modelling across provisioning modes - useful cost/capacity framing. |

## Tier 3 - Background and surveys

- **Serverless Computing: State-of-the-Art, Challenges and Opportunities** (IEEE Access survey) - field context and gap framing.
- **Taming Serverless Cold Start of Cloud Model Inference With Edge Computing** (IEEE TMC, 2024) - cold-start latency modelling, edge-based mitigation.
- **Qora: Neural-Enhanced Interference-Aware Resource Provisioning for Serverless Computing** (IEEE TASE, 2025) - interference-aware provisioning (QoS/degradation perspective).
- **Exploiting Wide-Area Resource Elasticity With Fine-Grained Orchestration for Serverless Analytics** (IEEE TON, 2025) - fine-grained orchestration for geo-distributed analytics.
- **BaaSLess: BaaS-Enabled Workflows in Federated Serverless Infrastructures** (IEEE TCC, 2024) - federated serverless workflows.
- **HealthFaaS: AI-Based Smart Healthcare System...** (IEEE IoT-J, 2023) - serverless scaling case study (application domain).
- **Modeling and Performance Evaluation of Hybrid Classical-Quantum Serverless Computing Platforms** (IEEE TQE, 2025) - orthogonal topic; skip unless quantum context is added.
- **Toward Latency-Sensitive Generative AI Provision via Dynamic Utility Maximization** (IEEE TSC, 2026) - latency-utility optimization in mobile cloud-edge; background only.
- **Deadline-Aware Task Offloading With Concurrency in Serverless Edge Computing** (IEEE IoT-J, 2026) - joint offloading + concurrency for IoT; background only.

---

## Usage guidance

- The presentation cites six Tier-1 papers (first six rows of the table above
  match the references slide). Expand to the full Tier-1 + Tier-2 set in
  `project.md` section 7 and in the final report.
- Read Tier-1 papers in full before designing the reward, the container-state
  feature set, and the baseline experiments.
- **Never quote another paper's percentage improvements as this project's
  results.** Their numbers are evidence for research direction and
  baselines, not measured outcomes of this system.