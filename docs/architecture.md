# Architecture --- Predictive Container Management for Energy-Efficient Serverless Computing

# 1. Architecture Objective

The architecture connects predictive AI, agentic planning, reinforcement
learning and cloud-native execution into one closed-loop system.

The architecture is intentionally layered so that no single AI component
has unrestricted control of infrastructure.

------------------------------------------------------------------------

# 2. Complete Architecture

``` mermaid
flowchart TD

    subgraph DATA[Data & Observation Layer]
        A1[Workload Traces]
        A2[Runtime Metrics]
        A3[Prometheus]
        A4[Feature Store / Time Window]
    end

    subgraph AI[AI Decision Layer]
        B1[Preprocessing]
        B2[TFT Forecasting]
        B3[State Builder]
        B4[Qwen3 Agentic Planner]
        B5[Plan Validator]
        B6[PPO Controller]
    end

    subgraph SAFE[Safety & Policy Layer]
        C1[Action Validator]
        C2[SLA Guard]
        C3[Capacity Limits]
        C4[Authorization]
    end

    subgraph EXEC[Execution Layer]
        D1[Kubernetes]
        D2[OpenFaaS]
        D3[Docker Containers]
        D4[Serverless Functions]
    end

    subgraph OBS[Observation & Evaluation]
        E1[Prometheus]
        E2[Grafana]
        E3[Experiment Logger]
        E4[Evaluation Engine]
    end

    A1 --> B1
    A2 --> A4
    A3 --> A4
    A4 --> B1
    B1 --> B2
    B2 --> B3
    A4 --> B3
    B3 --> B4
    B4 --> B5
    B5 --> B6
    B6 --> C1
    C1 --> C2
    C2 --> C3
    C3 --> C4
    C4 --> D1
    D1 --> D2
    D2 --> D3
    D3 --> D4
    D3 --> E1
    D4 --> E1
    E1 --> E2
    E1 --> E3
    E3 --> E4
    E1 --> A3
```

------------------------------------------------------------------------

# 3. Layer 1 --- Data and Observation

## 3.1 Workload Trace

The trace contains historical invocation behavior.

Possible features:

``` text
timestamp
invocation_count
invocation_rate
execution_duration
function_id
```

## 3.2 Runtime Metrics

Runtime state provides the information needed for control:

``` text
CPU
Memory
Active containers
Warm containers
Latency
P95 latency
Cold starts
Power/energy
```

## 3.3 Time Window

Raw events are converted into fixed intervals.

Example:

``` text
Time 1 → aggregated metrics
Time 2 → aggregated metrics
...
Time 30 → aggregated metrics
```

The resulting sequence becomes the TFT input.

------------------------------------------------------------------------

# 4. Layer 2 --- Preprocessing

Preprocessing performs:

``` text
Raw data
  ↓
Validation
  ↓
Missing-value handling
  ↓
Resampling
  ↓
Feature engineering
  ↓
Normalization
  ↓
Model-ready sequence
```

Important rule:

> Future test information must not leak into the training window.

------------------------------------------------------------------------

# 5. Layer 3 --- TFT Forecasting

The TFT receives historical multivariate features.

Conceptually:

``` text
X(t-k ... t)
      ↓
    TFT
      ↓
ŷ(t+1 ... t+h)
```

Where:

-   `k` = history length.
-   `h` = forecast horizon.
-   `ŷ` = predicted workload.

The output may be:

``` text
Predicted invocation rate
Predicted workload trend
Optional prediction intervals
```

------------------------------------------------------------------------

# 6. Layer 4 --- State Builder

The state builder combines forecast and current observations.

Example:

``` json
{
  "forecast_workload": 800,
  "current_workload": 620,
  "cpu_utilization": 0.72,
  "memory_utilization": 0.68,
  "active_containers": 8,
  "p95_latency_ms": 210,
  "cold_start_rate": 0.04,
  "energy": 120,
  "sla_threshold_ms": 250
}
```

------------------------------------------------------------------------

# 7. Layer 5 --- Qwen3 Agentic Planner

Qwen3 is the high-level reasoning/planning layer.

## Responsibility

It answers:

> Given the predicted demand and current system condition, what
> management strategy should be considered?

It should not directly execute Kubernetes commands.

### Example

``` text
Forecast:
strong increase

Current:
8 containers

SLA:
P95 ≤ 250 ms

Planner:
PREWARM / SCALE OUT
```

------------------------------------------------------------------------

# 8. Layer 6 --- Plan Validator

The planner output must be validated.

``` mermaid
flowchart TD
    A[Qwen3 Output] --> B{Valid Schema?}
    B -- No --> X[Reject]
    B -- Yes --> C{Approved Strategy?}
    C -- No --> X
    C -- Yes --> D{Capacity Within Bounds?}
    D -- No --> X
    D -- Yes --> E[Send to PPO]
```

This makes the LLM a bounded planning component.

------------------------------------------------------------------------

# 9. Layer 7 --- PPO Controller

PPO receives:

``` text
Current State
+
Forecast
+
Validated Planning Context
```

and chooses:

``` text
NoOp
PreWarm
ScaleOut
Reuse
ScaleIn
Terminate
```

------------------------------------------------------------------------

# 10. Layer 8 --- SLA Guard

The SLA guard operates independently of the model.

Example:

``` text
If action reduces capacity
AND
P95 is already close to SLA threshold
THEN
reject/defer aggressive scale-in
```

This provides a deterministic safety mechanism around AI decisions.

------------------------------------------------------------------------

# 11. Layer 9 --- Action Validator

``` mermaid
flowchart LR
    A[PPO Action] --> B[Action Schema]
    B --> C[Min/Max Capacity]
    C --> D[Rate Limit]
    D --> E[SLA Guard]
    E --> F[Authorization]
    F --> G[Executor]
```

------------------------------------------------------------------------

# 12. Layer 10 --- Kubernetes/OpenFaaS

Kubernetes manages the container infrastructure.

OpenFaaS provides the serverless function layer.

Docker provides container images.

The executor converts abstract actions into permitted platform
operations.

Example:

``` text
PPO:
ScaleOut +2

        ↓

Validator

        ↓

Executor

        ↓

OpenFaaS/Kubernetes:
increase function capacity
```

------------------------------------------------------------------------

# 13. Monitoring Architecture

``` mermaid
flowchart TD
    A[Containers] --> B[Metrics]
    B --> C[Prometheus]
    C --> D[Grafana]
    C --> E[Experiment Logger]
    E --> F[Evaluation Engine]
```

------------------------------------------------------------------------

# 14. Closed-Loop Control

``` text
OBSERVE
   ↓
FORECAST
   ↓
PLAN
   ↓
CONTROL
   ↓
VALIDATE
   ↓
EXECUTE
   ↓
MEASURE
   ↓
FEEDBACK
   ↺
```

------------------------------------------------------------------------

# 15. Failure Architecture

``` mermaid
flowchart TD
    A[Control Cycle] --> B{TFT Available?}
    B -- No --> F[Fallback]
    B -- Yes --> C{Planner Available?}
    C -- No --> F
    C -- Yes --> D{PPO Available?}
    D -- No --> F
    D -- Yes --> E[Normal Pipeline]
    E --> G{Action Safe?}
    G -- No --> F
    G -- Yes --> H[Execute]
    F --> I[Conservative Policy]
    I --> H
```

------------------------------------------------------------------------

# 16. Deployment Architecture

``` text
                 Kubernetes Cluster
┌──────────────────────────────────────────────────┐
│                                                  │
│  ┌───────────────┐     ┌─────────────────────┐  │
│  │ OpenFaaS      │     │ AI Services         │  │
│  │ Functions     │     │ TFT                 │  │
│  │ Containers    │     │ Qwen3               │  │
│  └───────────────┘     │ PPO                 │  │
│                        │ Orchestrator        │  │
│                        └─────────────────────┘  │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │ Monitoring                                 │  │
│  │ Prometheus + Grafana                       │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

------------------------------------------------------------------------

# 17. Data Flow Table

  Stage           Input                 Output
  --------------- --------------------- --------------------------
  Ingestion       Raw trace             Time series
  Preprocessing   Time series           Feature window
  TFT             Historical features   Forecast
  State builder   Forecast + metrics    Decision state
  Qwen3           Decision state        Strategy
  Validator       Strategy              Approved plan
  PPO             State + plan          Action
  Safety guard    Action + SLA          Approved/rejected action
  Executor        Approved action       Infrastructure change
  Monitoring      Runtime               Metrics
  Evaluation      Metrics               Results

------------------------------------------------------------------------

# 18. Architectural Principle

The system deliberately avoids this unsafe architecture:

``` text
LLM → unrestricted Kubernetes
```

and instead implements:

``` text
LLM
 ↓
Structured plan
 ↓
Validation
 ↓
PPO
 ↓
Safety guard
 ↓
Authorization
 ↓
Restricted executor
 ↓
Kubernetes/OpenFaaS
```
