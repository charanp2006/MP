# Architecture --- Predictive Container Management for Energy-Efficient Serverless Computing

## 1. High-Level Architecture

``` mermaid
flowchart TD
    D[Workload Traces + Runtime Metrics] --> P[Preprocessing]
    P --> T[TFT Forecasting]
    T --> Q[Qwen3 Agentic Planning]
    S[Current System State] --> Q
    Q --> R[PPO SLA-Aware Controller]
    R --> K[Kubernetes]
    K --> O[OpenFaaS]
    O --> C[Docker Containers / Functions]
    C --> M[Prometheus]
    M --> G[Grafana]
    C --> F[Feedback]
    F --> S
    F --> P
```

## 2. Data Layer

Inputs may include timestamp, invocation rate/count, execution duration,
CPU, memory, active/warm containers, cold starts, latency, power/energy
and time features.

The data layer cleans, resamples, normalizes and converts observations
into fixed time windows.

## 3. TFT Forecasting Layer

``` text
Historical feature window
        ↓
TFT
        ↓
Future workload forecast
```

The model predicts one or more future intervals using workload and
contextual signals.

## 4. Qwen3 Agentic Planning Layer

Qwen3 is used as a **high-level planner**, not an unrestricted
infrastructure executor.

Inputs: - forecast - current workload - CPU/memory - active containers -
latency/P95 - SLA threshold - cold starts - resource/energy state

Example structured output:

``` json
{
  "strategy": "prewarm",
  "priority": "sla",
  "desired_capacity_change": 3,
  "reason": "predicted demand increase"
}
```

## 5. PPO Control Layer

### State

``` text
[predicted_workload, workload, CPU, memory, latency,
 P95_latency, active_containers, cold_starts, energy, SLA_status]
```

### Actions

``` text
NoOp | PreWarm | ScaleOut | Reuse | ScaleIn | Terminate
```

### Reward

``` text
R = -(αE + βL + γCS + δC + εU) - λV_SLA
```

where the final term penalizes SLA violation.

## 6. Execution Layer

-   **Kubernetes:** pods, resources and lifecycle.
-   **OpenFaaS:** serverless function deployment/invocation.
-   **Docker:** container packaging.

## 7. Monitoring

Prometheus collects metrics; Grafana displays workload, forecast, active
containers, CPU, memory, latency, P95, cold starts, SLA violations and
energy-related measurements.

## 8. Feedback Loop

``` mermaid
flowchart LR
    A[Observe] --> B[Forecast]
    B --> C[Plan]
    C --> D[Control]
    D --> E[Execute]
    E --> F[Measure]
    F --> A
```

## 9. Safe Failure

``` mermaid
flowchart TD
    A[Control Cycle] --> B{AI Components Healthy?}
    B -- Yes --> C[Normal Decision Pipeline]
    B -- No --> D[Safe Fallback]
    C --> E[Validate Action]
    E --> F[Execute]
    D --> F
```

The fallback should maintain safe capacity bounds and continue
monitoring.

## 10. Deployment View

``` text
Kubernetes Cluster
├── OpenFaaS
│   ├── Function A
│   ├── Function B
│   └── Function C
├── Monitoring
│   ├── Prometheus
│   └── Grafana
└── AI Services
    ├── TFT Inference
    ├── Qwen3 Planner
    ├── PPO Controller
    └── Orchestrator
```

## 11. Core Principle

**Qwen3 plans → PPO controls → Kubernetes/OpenFaaS executes → monitoring
measures → feedback closes the loop.**
