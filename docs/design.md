# Design --- Predictive Container Management for Energy-Efficient Serverless Computing

## 1. Design Goals

The system should be modular, reproducible, measurable, safe by default
and simple enough to implement and explain in a final-year project.

## 2. Module Structure

``` text
project/
├── data/
│   ├── ingestion/
│   ├── preprocessing/
│   └── feature_engineering/
├── forecasting/
│   ├── model/
│   ├── training/
│   └── inference/
├── agent/
│   ├── planner/
│   └── schemas/
├── rl/
│   ├── environment/
│   ├── reward/
│   └── policy/
├── orchestrator/
│   ├── decision_loop/
│   ├── action_validator/
│   └── executor/
├── monitoring/
├── experiments/
└── results/
```

## 3. Data Design

### Raw/derived fields

``` text
timestamp
function_id
invocation_count
execution_duration
cpu_utilization
memory_utilization
active_containers
warm_containers
cold_start
latency
power_or_energy
invocation_rate
moving_average
lag_features
hour
day_of_week
peak_indicator
```

## 4. Forecasting Design

``` mermaid
flowchart LR
    A[Historical Dataset] --> B[Preprocess]
    B --> C[Time-Ordered Split]
    C --> D[TFT Training]
    D --> E[Validation]
    E --> F[Checkpoint]
    F --> G[Inference]
```

Never mix future evaluation observations into training.

## 5. Agentic Planning Design

Use structured input rather than arbitrary raw text.

``` json
{
  "forecast": {"next_interval": 800, "trend": "increasing"},
  "current_state": {
    "active_containers": 8,
    "cpu": 0.72,
    "memory": 0.68,
    "p95_latency_ms": 210,
    "cold_start_rate": 0.04
  },
  "constraints": {
    "sla_p95_ms": 250,
    "min_containers": 2,
    "max_containers": 30
  }
}
```

The planner output must be schema-validated before control.

## 6. PPO Environment

Observation:

``` text
forecast, workload, CPU, memory, latency, P95,
active_containers, cold_starts, energy, SLA_status
```

Action:

``` text
0 NoOp
1 PreWarm
2 ScaleOut
3 Reuse
4 ScaleIn
5 Terminate
```

Reward:

``` text
-energy_cost
-latency_cost
-cold_start_cost
-resource_cost
-underutilization_cost
-SLA_penalty
```

## 7. Action Validation

``` mermaid
flowchart TD
    A[PPO Action] --> B[Schema Validation]
    B --> C[Resource Bounds]
    C --> D[SLA Safety Check]
    D --> E[Authorization]
    E --> F[Execute]
    B --> G[Reject/Fallback]
    C --> G
    D --> G
    E --> G
```

## 8. Control Cycle

1.  Collect metrics.
2.  Update feature window.
3.  Generate TFT forecast.
4.  Build state.
5.  Generate Qwen3 plan.
6.  Validate plan.
7.  Query PPO.
8.  Validate action.
9.  Execute action.
10. Measure outcome.
11. Store logs/metrics.
12. Start next cycle.

## 9. Suggested Internal Interfaces

``` text
POST /forecast
POST /plan
POST /control
GET  /metrics
```

These can initially be Python functions rather than HTTP services.

## 10. Configuration

``` yaml
sla:
  p95_latency_ms: 250
containers:
  min: 2
  max: 30
forecast:
  history_window: 30
  horizon: 5
control:
  interval_seconds: 60
```

Values are experimental parameters, not assumed optimal values.

## 11. Logging

Each cycle should record:

``` text
timestamp
forecast
observed_workload
system_state
qwen3_plan
ppo_action
action_result
latency
p95_latency
cold_starts
active_containers
cpu
memory
energy
sla_status
```

## 12. Recommended Result Plots

1.  Actual vs predicted workload.
2.  Active containers over time.
3.  CPU utilization.
4.  P95 latency.
5.  Cold starts.
6.  Energy/power.
7.  Baseline vs proposed energy.
8.  Baseline vs proposed cold starts.
9.  SLA compliance.
10. PPO action distribution.

## 13. Key Design Decisions

-   **TFT:** multivariate temporal workload prediction.
-   **Qwen3:** high-level reasoning/planning.
-   **PPO:** repeated low-level control under a reward.
-   **Separation:** makes the system more deterministic and testable.
-   **Kubernetes/OpenFaaS:** practical cloud-native execution
    environment.
