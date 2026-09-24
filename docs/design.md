# DESIGN --- Predictive Container Management for Energy-Efficient Serverless Computing

# 1. Design Philosophy

The implementation should be modular enough that each major research
idea can be demonstrated separately.

The design separates:

1.  Data processing.
2.  Forecasting.
3.  Planning.
4.  Reinforcement-learning control.
5.  Safety validation.
6.  Infrastructure execution.
7.  Monitoring.
8.  Evaluation.

------------------------------------------------------------------------

# 2. Detailed Module Structure

``` text
project/
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── ingestion.py
│   ├── preprocessing.py
│   └── feature_engineering.py
│
├── forecasting/
│   ├── tft_model.py
│   ├── train.py
│   ├── evaluate.py
│   └── inference.py
│
├── agent/
│   ├── planner.py
│   ├── prompts/
│   ├── schemas.py
│   └── validator.py
│
├── rl/
│   ├── environment.py
│   ├── reward.py
│   ├── train_ppo.py
│   ├── evaluate_ppo.py
│   └── policy.py
│
├── orchestrator/
│   ├── decision_loop.py
│   ├── state_builder.py
│   ├── action_validator.py
│   ├── sla_guard.py
│   └── executor.py
│
├── infrastructure/
│   ├── kubernetes/
│   ├── openfaas/
│   └── docker/
│
├── monitoring/
│   ├── prometheus/
│   └── grafana/
│
├── experiments/
│   ├── baseline/
│   ├── scenarios/
│   ├── ablation/
│   └── evaluation/
│
└── configs/
    └── project.yaml
```

------------------------------------------------------------------------

# 3. Data Schema

A conceptual observation record:

``` json
{
  "timestamp": "2026-01-01T10:00:00",
  "function_id": "function_a",
  "invocation_rate": 620,
  "execution_duration_ms": 45,
  "cpu_utilization": 0.72,
  "memory_utilization": 0.68,
  "active_containers": 8,
  "warm_containers": 7,
  "cold_starts": 2,
  "latency_ms": 170,
  "p95_latency_ms": 210,
  "power_w": 120
}
```

------------------------------------------------------------------------

# 4. Feature Engineering

## 4.1 Lag Features

``` text
workload(t-1)
workload(t-2)
workload(t-3)
...
```

## 4.2 Rolling Features

``` text
moving average
moving maximum
moving minimum
rolling standard deviation
```

## 4.3 Temporal Features

``` text
hour
day_of_week
weekend
peak_period
```

## 4.4 System Features

``` text
CPU
memory
active containers
latency
cold starts
```

------------------------------------------------------------------------

# 5. Dataset Splitting

Use chronological splitting:

``` text
Earlier period ─────────────→ Later period

|------ Train ------|-- Validation --|-- Test --|
```

Do not randomly shuffle a time series when that would allow future
information to influence training.

------------------------------------------------------------------------

# 6. TFT Training Design

``` mermaid
flowchart TD
    A[Processed Time Series]
    A --> B[Window Generator]
    B --> C[Train TFT]
    C --> D[Validation]
    D --> E{Acceptable?}
    E -- No --> F[Tune Configuration]
    F --> C
    E -- Yes --> G[Save Checkpoint]
```

Record:

-   History window.
-   Forecast horizon.
-   Feature list.
-   Training epochs.
-   Learning rate.
-   Batch size.
-   Random seed.
-   Model checkpoint.

------------------------------------------------------------------------

# 7. Forecast Output

Example:

``` json
{
  "forecast_horizon": 5,
  "predicted_workload": [
    710,
    760,
    820,
    900,
    960
  ],
  "trend": "increasing"
}
```

The exact schema can be adapted to the selected implementation.

------------------------------------------------------------------------

# 8. Qwen3 Planner Design

The planner prompt should define:

-   Role.
-   Input schema.
-   Allowed strategies.
-   Constraints.
-   Output schema.
-   Instruction that infrastructure commands are forbidden.

Example:

``` text
ROLE:
You are a serverless resource-management planner.

INPUT:
Forecast + current system state + constraints.

ALLOWED STRATEGIES:
NoOp, PreWarm, ScaleOut, Reuse, ScaleIn, Terminate.

RULE:
Return structured planning information only.
Do not return shell commands.
Do not return Kubernetes YAML.
Do not bypass SLA constraints.
```

------------------------------------------------------------------------

# 9. Planner Output Schema

``` json
{
  "strategy": "prewarm",
  "desired_capacity_change": 3,
  "priority": "sla",
  "urgency": "high",
  "reason": "forecasted demand increase",
  "constraints_respected": true
}
```

The output is parsed and validated before PPO receives it.

------------------------------------------------------------------------

# 10. PPO Environment

## Observation Space

``` text
[
 predicted_workload,
 current_workload,
 cpu,
 memory,
 latency,
 p95_latency,
 active_containers,
 cold_starts,
 energy,
 sla_margin
]
```

## Action Space

``` text
0 = NoOp
1 = PreWarm
2 = ScaleOut
3 = Reuse
4 = ScaleIn
5 = Terminate
```

If desired, capacity change can be represented as a bounded discrete
action rather than an unrestricted numeric value.

------------------------------------------------------------------------

# 11. SLA Margin

A useful derived feature is:

``` text
SLA margin =
SLA threshold - current P95 latency
```

Interpretation:

``` text
positive → remaining latency headroom
zero     → at threshold
negative → SLA violation
```

------------------------------------------------------------------------

# 12. Reward Design

A normalized reward can be written as:

``` text
R_t =
-(w_e E_t
 + w_l L_t
 + w_c CS_t
 + w_r RC_t
 + w_u U_t)
- w_s V_t
```

Where:

-   `E_t` = normalized energy/resource consumption.
-   `L_t` = latency cost.
-   `CS_t` = cold-start cost.
-   `RC_t` = resource/capacity cost.
-   `U_t` = underutilization cost.
-   `V_t` = SLA violation indicator or penalty.
-   `w_*` = experimentally selected weights.

Keep reward components normalized where possible so one metric does not
dominate simply because it has a larger numerical scale.

------------------------------------------------------------------------

# 13. Action Validator

The action validator checks:

``` text
1. Is action known?
2. Is capacity change within bounds?
3. Is target function valid?
4. Is action allowed in current state?
5. Would action violate a safety condition?
6. Does executor have authorization?
```

------------------------------------------------------------------------

# 14. SLA Guard

The SLA guard is independent from the learned policy.

Example:

``` python
if requested_scale_in and p95_latency >= sla_threshold:
    reject_or_delay_scale_in()
```

This is a conceptual rule; the final implementation can use a
configurable safety margin.

------------------------------------------------------------------------

# 15. Executor Design

The executor translates an approved action into platform-specific
operations.

``` text
Abstract Action
       ↓
Executor
       ↓
Kubernetes/OpenFaaS API
       ↓
Container state change
```

The executor should never accept raw arbitrary commands from Qwen3.

------------------------------------------------------------------------

# 16. Control Cycle Timing

Example control cycle:

``` text
T0       collect metrics
T0+1     preprocess
T0+2     forecast
T0+3     planning
T0+4     PPO decision
T0+5     validation
T0+6     execution
T0+7     wait/observe
T0+8     evaluate
```

The real interval depends on infrastructure and model inference time.

------------------------------------------------------------------------

# 17. State Persistence

Store each transition:

``` json
{
  "state_before": {},
  "forecast": {},
  "plan": {},
  "action": "prewarm",
  "execution_result": "success",
  "state_after": {},
  "reward": -0.23
}
```

This supports debugging and PPO training/evaluation.

------------------------------------------------------------------------

# 18. Experiment Configuration

``` yaml
project:
  name: predictive-container-management

sla:
  p95_latency_ms: 250
  safety_margin_ms: 20

containers:
  min: 2
  max: 30
  max_change_per_cycle: 5

forecast:
  history_window: 30
  horizon: 5

control:
  interval_seconds: 60

evaluation:
  repetitions: 5
```

These are example configuration values, not experimentally established
optimal settings.

------------------------------------------------------------------------

# 19. Baseline Design

A fair baseline should use:

``` text
same workload
same cluster
same resource limits
same monitoring
same duration
same metrics
```

Only the scaling/control policy changes.

The baseline can represent reactive scaling based on current
utilization.

------------------------------------------------------------------------

# 20. Ablation Design

``` mermaid
flowchart TD
    A[Full System] --> B[Remove Qwen3]
    A --> C[Remove TFT]
    A --> D[Remove PPO]
    A --> E[Remove SLA Component]
    B --> F[Compare Metrics]
    C --> F
    D --> F
    E --> F
```

This demonstrates which architectural components contribute to observed
behavior.

------------------------------------------------------------------------

# 21. Logging

Log at minimum:

``` text
timestamp
experiment_id
trace_id
forecast
forecast_error
current_workload
CPU
memory
active_containers
P95
cold_starts
Qwen3 plan
PPO action
validation result
execution result
energy
reward
SLA status
```

------------------------------------------------------------------------

# 22. Dashboard Design

Suggested Grafana panels:

### Workload

-   Actual invocation rate.
-   Predicted invocation rate.

### Infrastructure

-   Active containers.
-   CPU.
-   Memory.

### Performance

-   Mean latency.
-   P95 latency.
-   SLA threshold.

### Efficiency

-   Power/energy.
-   Energy/request.
-   Resource utilization.

### AI Control

-   Planner strategy.
-   PPO action.
-   Action frequency.
-   Reward.

------------------------------------------------------------------------

# 23. Error Handling

Every service should return a controlled error.

``` text
Forecast failure
    ↓
Use fallback forecast/control strategy

Planner failure
    ↓
Skip planner + use bounded policy

PPO failure
    ↓
Fallback reactive policy

Kubernetes failure
    ↓
Log + retry with bounded policy

Monitoring failure
    ↓
Continue only under defined safe conditions
```

------------------------------------------------------------------------

# 24. Implementation Priority

Recommended development sequence:

1.  Build data pipeline.
2.  Implement reactive baseline.
3.  Implement monitoring.
4.  Train/evaluate TFT.
5.  Implement PPO environment.
6.  Add SLA reward.
7.  Add Qwen3 planning.
8.  Add validators.
9.  Integrate Kubernetes/OpenFaaS.
10. Run controlled experiments.
11. Add dashboard/results.
12. Perform ablation and final evaluation.
