# Project and Image Validation Report

## 1. Purpose and Scope

This report validates the uploaded root-folder images against the written
project material on `main` and the available `docs` branch. It checks:

- whether the images describe the same system as the project files;
- whether the architecture, models, platforms, goals and safety claims are
  internally consistent;
- which statements are supported by the current documentation;
- which items must be decided or corrected before implementation or final
  presentation.

This is a design-content audit. It does not claim that the models, cluster,
energy measurements or performance targets have already been implemented or
experimentally verified.

## 2. Evidence Reviewed

### Current `main` branch

- [project.md](../project.md): consolidated project specification.
- [README.md](../README.md): project overview, technology stack and roadmap.
- [docs/prd.md](prd.md): product requirements and scope.
- [docs/architecture.md](architecture.md): layered architecture and control loop.
- [docs/design.md](design.md): modules, schemas, control cycle and experiments.
- [docs/security.md](security.md): threats, trust boundaries and authorization.
- [docs/test_plan.md](test_plan.md): unit, integration, system and evaluation tests.

### `docs` branch

The `docs` branch contains the research and presentation source material:

- six presentation files, including `Predictive-Container-Management-for-Energy-Efficient-Serverless-Computing.pptx`;
- research papers covering serverless cold starts, energy-aware scheduling,
  reinforcement learning, autoscaling and resource allocation;
- an earlier, shorter version of the five Markdown documents.

The current `main` branch does not contain the research PDFs or PPTX files.
The branch audit therefore supports the conclusion that `docs` is the source
material branch and `main` is the consolidated specification branch.

### Uploaded root images

The root contains ten PNG files:

1. `ChatGPT Image Sep 11, 2026, 12_17_00 PM.png`
2. `ChatGPT Image Sep 11, 2026, 12_19_05 PM.png`
3. `ChatGPT Image Sep 11, 2026, 12_20_25 PM.png`
4. `ChatGPT Image Sep 13, 2026, 06_14_59 PM.png`
5. `ChatGPT Image Sep 13, 2026, 06_18_51 PM.png`
6. `ChatGPT Image Sep 13, 2026, 07_51_46 PM.png`
7. `ChatGPT Image Sep 24, 2026, 07_03_16 AM.png`
8. `ChatGPT Image Sep 24, 2026, 07_04_34 AM.png`
9. `ChatGPT Image Sep 24, 2026, 07_15_38 AM.png`
10. `final.png`

The images were visually reviewed for architecture, labels, technologies,
objectives and data-flow direction.

## 3. Canonical System Supported by the Files

The project files define this canonical closed loop:

```text
Workload traces and runtime metrics
        -> preprocessing and fixed time windows
        -> TFT workload forecast
        -> structured state construction
        -> Qwen3 high-level management plan
        -> schema and policy validation
        -> PPO bounded control action
        -> SLA guard, capacity limits and authorization
        -> Kubernetes/OpenFaaS/Docker execution
        -> Prometheus/Grafana observation
        -> experiment logging and feedback
```

The responsibilities are clearly separated:

| Component | Confirmed responsibility |
| --- | --- |
| Workload data | Historical invocation and runtime observations |
| Preprocessing | Validation, resampling, feature generation and normalization |
| TFT | Short-horizon multivariate workload forecasting |
| Qwen3 | High-level structured planning only |
| PPO | Repeated operational action selection |
| Validators and SLA guard | Deterministic safety and policy enforcement |
| Kubernetes/OpenFaaS/Docker | Execution of approved abstract actions |
| Prometheus/Grafana | Measurement and visualization |
| Evaluation engine | Baseline, ablation and metric comparison |

This architecture is consistent across `project.md`, the five current `docs`
files, the earlier `docs`-branch documents and most of the uploaded images.

## 4. Image-to-File Validation

| Image group | Content seen in the images | Validation against files |
| --- | --- | --- |
| 11 September methodology images | Data collection, preprocessing, forecasting, planning, control, execution, monitoring and feedback | **Confirmed.** Matches the control cycle in `docs/design.md` and `docs/architecture.md`. |
| 11 September technology image | Docker, Kubernetes, serverless runtime, forecasting, monitoring and dashboards | **Mostly confirmed.** Docker, Kubernetes, OpenFaaS, Prometheus and Grafana are documented. |
| 13 September objective image | Prediction, proactive scaling, AI planning, PPO, SLA protection and energy reduction | **Confirmed.** Matches the objectives and success metrics in `project.md` and `docs/prd.md`. |
| 13 September data/model images | Historical data, preprocessing, TFT, Qwen3, PPO, execution and feedback | **Confirmed.** Matches the canonical data and decision flow. |
| 24 September simplified methodology image | A shorter version of the same end-to-end process | **Confirmed as an overview.** It omits safety and evaluation detail but does not contradict them. |
| 24 September expanded methodology image | Forecasting, planning, PPO, Kubernetes/OpenFaaS/Docker and monitoring | **Mostly confirmed.** The written files support these technologies, but the exact model/platform names must be standardized as described below. |
| `final.png` | Users/services, API ingestion, AI decision engine, serverless execution, monitoring and feedback | **Partially confirmed.** It is compatible with the project, but the API gateway and user-facing service boundary are not functional requirements in the written files. |

### Image claims supported by the files

- The system is predictive rather than purely reactive.
- Cold-start reduction and energy/resource efficiency are competing goals.
- P95 latency and SLA compliance are primary constraints.
- Qwen3 is a planner and must not directly execute infrastructure commands.
- PPO uses a bounded action space.
- Monitoring closes the control loop.
- Baseline and ablation experiments are required.

### Image claims not yet validated by implementation

- Any claimed percentage improvement in energy, cold starts or latency.
- Actual forecast accuracy.
- Actual Qwen3 or PPO behavior.
- Successful deployment on Kubernetes or OpenFaaS.
- Direct power measurement.
- The existence of an API gateway or production user workflow.

These must be presented as targets, design intentions or proposed tests until
raw experiment results exist.

## 5. Consistency Findings

### 5.1 Confirmed consistency

The following important concepts are consistent across the files and images:

1. **Problem:** reactive scaling can cause cold starts during spikes and waste
   energy when too many containers remain warm.
2. **Control strategy:** forecast first, plan at a high level, select a bounded
   action, validate it, execute it and measure the result.
3. **Safety:** AI output is untrusted until schema, policy, SLA and
   authorization checks pass.
4. **Evaluation:** the proposed system must be compared with a reactive
   baseline under the same workload and infrastructure conditions.
5. **Research status:** this is a Phase 1 academic prototype; performance
   targets are not established results.

### 5.2 Conflicts requiring resolution

| Topic | Variants found | Recommended canonical choice |
| --- | --- | --- |
| Forecast model | TFT, PatchTST, and generic Transformer labels | Use **Temporal Fusion Transformer (TFT)** everywhere unless the implementation changes. |
| Execution platform | Kubernetes/OpenFaaS/Docker, Knative, Azure Functions | Use **Kubernetes + OpenFaaS + Docker** for the prototype. Treat Azure Functions traces as a dataset source, not the execution platform. Remove Knative from diagrams unless it is implemented. |
| Forecast horizon | Five steps, five-to-fifteen minutes, and unspecified horizons | Use a configurable horizon. The current example is a 30-step history and five-step forecast; state the control interval beside it. |
| Planner/controller relationship | Qwen3 and PPO appear as adjacent or combined decision components | Keep the documented separation: Qwen3 produces a structured plan; PPO selects the bounded action. |
| API boundary | `final.png` shows an API/user layer | Keep it as an optional deployment boundary unless API endpoints are added to the implementation requirements. |
| Container/function terminology | Containers, functions, warm pools and replicas are used interchangeably | Define whether capacity means function replicas, containers or pods in each experiment. |

## 6. Branch Validation

### `main`

`main` contains the consolidated project documents and the root images. Its
documentation is internally aligned around TFT, Qwen3, PPO,
Kubernetes/OpenFaaS/Docker, Prometheus/Grafana and a guarded closed loop.

### `docs`

`docs` contains the source presentations and research survey. Its Markdown
documents express the same architecture in shorter form. The research papers
provide relevant background, but they do not validate this project's proposed
implementation or numerical targets. Their results must not be quoted as this
project's results.

### Cross-branch conclusion

There is no implementation code in either branch at the time of this audit.
The repository currently validates a project design and research direction,
not a working system. The branch contents are complementary rather than
contradictory: `docs` supplies research/presentation context and `main`
supplies the consolidated specification.

## 7. Requirements Traceability

| Requirement area | Written evidence | Image evidence | Status |
| --- | --- | --- | --- |
| Workload ingestion | PRD FR-01; architecture data layer | Data/source blocks | Defined |
| Runtime metrics | PRD FR-02; monitoring design | Monitoring blocks | Defined |
| Preprocessing | PRD FR-03; design feature engineering | Preprocessing blocks | Defined |
| Forecasting | PRD FR-04; TFT sections | TFT/forecast blocks | Defined, implementation pending |
| Agentic planning | PRD FR-05; Qwen3 planner schema | Planner/AI blocks | Defined, implementation pending |
| PPO control | PRD FR-06; action space and reward | PPO/control blocks | Defined, implementation pending |
| SLA protection | PRD FR-07; independent SLA guard | SLA/latency labels | Defined, test pending |
| Action safety | PRD FR-08; security allowlist/RBAC | Validator/guard blocks | Defined, implementation pending |
| Execution | PRD FR-09; Kubernetes/OpenFaaS/Docker | Platform blocks | Proposed, not deployed |
| Evaluation | PRD FR-10; test plan baselines/ablations | Evaluation/metrics blocks | Defined, results pending |

## 8. Required Corrections Before Finalizing Images

1. Replace any `PatchTST`, `Knative` or Azure Functions execution label with
   the canonical choice, or explicitly label it as an alternative.
2. Add the validator, SLA guard and authorization boundary to the main
   architecture image; these are central safety requirements, not optional
   implementation detail.
3. Label Azure Functions as a trace/data source if that is the intended use.
4. Put the forecast history, forecast horizon and control interval in one
   consistent location.
5. Use one capacity term consistently: for example, `function replicas`
   backed by containers/pods.
6. Mark percentage improvements as `indicative targets` until experiments
   produce measured values.
7. If `final.png` is intended to be authoritative, document its API boundary
   and add API requirements and tests; otherwise use it only as a conceptual
   overview.

## 9. Implementation Readiness Checklist

The design is ready to move into implementation when these decisions are
recorded in configuration and code:

- [ ] Canonical forecast model selected and named consistently.
- [ ] Control interval and forecast horizon fixed for the first experiment.
- [ ] Capacity unit defined as replicas, containers or pods.
- [ ] Dataset source and execution platform separated.
- [ ] Reactive baseline implemented before the AI controller.
- [ ] Observation, forecast, plan, action and outcome schemas versioned.
- [ ] PPO action bounds, cooldown and maximum change per cycle configured.
- [ ] Independent SLA guard implemented.
- [ ] Restricted executor and Kubernetes RBAC defined.
- [ ] Fallback policy defined for TFT, Qwen3, PPO, monitoring and platform failures.
- [ ] Energy measurement method classified as measured or estimated.
- [ ] Reproducible baseline, ablation and repeated-trial experiments prepared.

## 10. Final Verdict

The images and project files describe the same intended research system at a
high level, and the consolidated written specification is the more reliable
source of truth because it includes safety, testing, failure handling and
evaluation requirements that several images omit.

The project is **conceptually consistent but not yet presentation-final**.
Before using the images as authoritative architecture, standardize the
forecast model, execution platform, forecast horizon and capacity terminology.
After those corrections, use the current `main` documentation as the
canonical specification and retain the `docs` branch as research and
presentation source material.