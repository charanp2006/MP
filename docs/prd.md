# PRD --- Predictive Container Management for Energy-Efficient Serverless Computing

## 1. Document Purpose

This Product Requirements Document defines the requirements, scope,
architecture-facing behavior, measurable objectives, constraints,
interfaces, and deliverables for the proposed project.

The project is an academic/research prototype. Its purpose is to
demonstrate a complete predictive container-management loop rather than
claim production-grade cloud infrastructure.

------------------------------------------------------------------------

# 2. Product Vision

The proposed system anticipates future serverless workload instead of
waiting for demand to increase before scaling containers.

The intended decision chain is:

``` text
Historical workload + runtime metrics
                ↓
        Data preprocessing
                ↓
       TFT workload forecast
                ↓
        Qwen3 planning layer
                ↓
         PPO control policy
                ↓
   Action validation / SLA guard
                ↓
     Kubernetes + OpenFaaS
                ↓
         Runtime execution
                ↓
        Prometheus metrics
                ↓
             Feedback
```

The key design principle is separation of responsibilities:

-   **TFT** predicts what may happen next.
-   **Qwen3** interprets the predicted situation and forms a high-level
    management plan.
-   **PPO** converts the state and plan into a bounded operational
    action.
-   **Kubernetes/OpenFaaS** executes the action.
-   **Prometheus/Grafana** measure the result.
-   **SLA protection** prevents energy optimization from becoming
    uncontrolled latency degradation.

------------------------------------------------------------------------

# 3. Problem Definition

Traditional reactive container scaling makes decisions mainly from
current or recently observed utilization.

For serverless workloads, this creates two opposing problems:

### Problem A --- Under-provisioning

When demand rises rapidly:

``` text
Demand ↑
   ↓
Existing capacity becomes insufficient
   ↓
New container/function starts
   ↓
Cold-start delay
   ↓
Higher request latency
```

### Problem B --- Over-provisioning

To avoid cold starts, the system may keep many containers active:

``` text
Large warm pool
      ↓
Low average utilization
      ↓
Unused compute capacity
      ↓
Higher resource/energy consumption
```

The project therefore treats container management as a predictive
multi-objective control problem.

------------------------------------------------------------------------

# 4. Product Goal

Develop a working prototype that can:

1.  Observe workload and infrastructure state.
2.  Predict short-term future demand.
3.  Generate a high-level container-management strategy.
4.  Select a concrete bounded action.
5.  Protect a predefined SLA.
6.  Execute the action on a containerized serverless environment.
7.  Measure the outcome.
8.  Repeat the cycle.

------------------------------------------------------------------------

# 5. Target Users

## 5.1 Researcher

Needs reproducible experiments and quantitative evaluation.

## 5.2 Cloud/DevOps Engineer

Needs visibility into workload, containers, scaling decisions and SLA
behavior.

## 5.3 Project Evaluator

Needs an understandable end-to-end demonstration.

## 5.4 Student Developer

Needs modular components that can be developed and tested independently.

------------------------------------------------------------------------

# 6. Scope

## 6.1 In Scope

### Data

-   Historical workload traces.
-   Runtime metrics.
-   Time-series preprocessing.
-   Feature engineering.

### AI

-   TFT forecasting.
-   Qwen3 agentic planning.
-   PPO policy/control.
-   SLA-aware reward.

### Infrastructure

-   Docker.
-   Kubernetes.
-   OpenFaaS.
-   Prometheus.
-   Grafana.

### Evaluation

-   Reactive baseline.
-   Component ablation.
-   Forecast accuracy.
-   Latency.
-   P95 latency.
-   SLA compliance.
-   Cold starts.
-   Resource utilization.
-   Energy/power measurement or estimation.

## 6.2 Out of Scope

-   Full commercial production deployment.
-   Multi-cloud orchestration.
-   Automatic retraining from uncontrolled production data.
-   Autonomous arbitrary shell execution by an LLM.
-   Guaranteed numerical energy reduction before experiments.
-   Handling confidential customer data.

------------------------------------------------------------------------

# 7. Functional Requirements

## FR-01 --- Workload Ingestion

The system shall accept time-series workload data.

Minimum conceptual fields:

``` text
timestamp
function/application identifier
invocation count or rate
execution duration
```

## FR-02 --- Runtime Metric Collection

The system shall collect or derive:

``` text
CPU utilization
Memory utilization
Active containers
Warm containers
Latency
P95 latency
Cold starts
Power/energy where available
```

## FR-03 --- Preprocessing

The system shall:

1.  Sort observations chronologically.
2.  Handle missing values.
3.  Resample data into the selected control interval.
4.  Generate lag features.
5.  Generate time/context features.
6.  Normalize features where required by the model.

## FR-04 --- Forecasting

The TFT model shall produce a forecast for the configured future
horizon.

Example:

``` text
Input:
previous 30 time steps

Output:
next 5 time steps
```

The actual window/horizon shall remain configurable.

## FR-05 --- Agentic Planning

Qwen3 shall receive structured forecast and system-state information and
produce a structured strategy.

Example strategies:

``` text
NoOp
PreWarm
ScaleOut
Reuse
ScaleIn
Terminate
```

The model should not directly execute infrastructure commands.

## FR-06 --- PPO Control

PPO shall use the state and approved planning information to select an
operational action.

## FR-07 --- SLA Protection

The system shall monitor an explicitly defined SLA target, such as P95
latency.

An SLA violation shall carry a strong negative reward/penalty.

## FR-08 --- Action Validation

Every action shall pass:

``` text
Schema validation
        ↓
Capacity validation
        ↓
SLA safety check
        ↓
Authorization
        ↓
Execution
```

## FR-09 --- Monitoring

Prometheus shall collect metrics and Grafana shall display them.

## FR-10 --- Experiment Logging

Each control cycle shall store sufficient information to reconstruct:

``` text
what was predicted
what was planned
what action was selected
what was executed
what happened afterward
```

------------------------------------------------------------------------

# 8. Non-Functional Requirements

## NFR-01 Performance

The decision pipeline must fit within the selected control interval.

## NFR-02 Reliability

Failure of a model/service shall not produce unrestricted infrastructure
actions.

## NFR-03 Reproducibility

Experiments shall record:

-   Dataset/trace.
-   Configuration.
-   Model versions.
-   Random seeds where relevant.
-   Hardware/software environment.
-   Start/end timestamps.

## NFR-04 Maintainability

Each major component should be independently replaceable.

## NFR-05 Security

The system must use least privilege and closed action spaces.

## NFR-06 Observability

Every major decision should be visible through logs and metrics.

------------------------------------------------------------------------

# 9. User/Operator Workflow

``` mermaid
flowchart TD
    A[Start Experiment] --> B[Load Workload Trace]
    B --> C[Preprocess Data]
    C --> D[Collect Current State]
    D --> E[TFT Forecast]
    E --> F[Build Planning Context]
    F --> G[Qwen3 Plan]
    G --> H[Validate Plan]
    H --> I[PPO Action]
    I --> J[Validate Action]
    J --> K[Execute on Kubernetes/OpenFaaS]
    K --> L[Observe Runtime]
    L --> M[Prometheus/Grafana]
    M --> N[Store Results]
    N --> D
```

------------------------------------------------------------------------

# 10. SLA Definition

For the prototype, SLA protection should be represented by an explicit
latency target.

Example:

``` text
SLA target:
P95 latency ≤ configured threshold
```

The exact threshold should be fixed before the final experiment.

A violation occurs when:

``` text
P95 latency > SLA threshold
```

The controller must not optimize energy by intentionally allowing
repeated SLA violations.

------------------------------------------------------------------------

# 11. Reward Requirements

A conceptual reward is:

``` text
R_t =
 -(α × Energy)
 -(β × Latency)
 -(γ × ColdStarts)
 -(δ × ResourceCost)
 -(ε × Underutilization)
 -(λ × SLA_Violation)
```

The weights must be documented and held consistent across comparable
experiments.

The SLA penalty should be sufficiently meaningful that the controller
cannot obtain an attractive reward simply by aggressively reducing
containers.

------------------------------------------------------------------------

# 12. Success Criteria

The project is considered technically complete when:

-   End-to-end control loop works.
-   Forecasting model produces valid forecasts.
-   Qwen3 produces schema-valid plans.
-   PPO selects valid actions.
-   Action validator blocks invalid operations.
-   Kubernetes/OpenFaaS execution works.
-   Monitoring captures outcomes.
-   Baseline comparison is reproducible.
-   Results contain measured rather than assumed improvements.

Numerical energy/cold-start targets should be described as **targets**,
not pre-existing results.

------------------------------------------------------------------------

# 13. Deliverables

1.  Dataset preprocessing pipeline.
2.  TFT model/training pipeline.
3.  Qwen3 planner.
4.  PPO environment and policy.
5.  SLA reward mechanism.
6.  Action validator.
7.  Kubernetes/OpenFaaS deployment.
8.  Monitoring dashboard.
9.  Baseline implementation.
10. Experiment scripts.
11. Results.
12. Project report.
13. Presentation.
14. Architecture/design/test/security documents.

------------------------------------------------------------------------

# 14. Risks

  Risk                             Mitigation
  -------------------------------- -------------------------------------------
  Forecast is inaccurate           Evaluate multiple workload patterns
  LLM output is inconsistent       Structured schema + validator
  PPO behaves unexpectedly         Bounded actions + offline/testing stage
  Energy measurement unavailable   Use clearly documented estimation
  Kubernetes instability           Controlled local cluster/test environment
  SLA violations                   Strong SLA penalty + safety guard
  Excessive scaling                Min/max limits + cooldown
  Model service unavailable        Conservative fallback
