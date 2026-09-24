# TEST PLAN --- Predictive Container Management for Energy-Efficient Serverless Computing

# 1. Test Strategy

Testing is divided into:

``` text
Unit
  ↓
Component
  ↓
Integration
  ↓
System
  ↓
Performance
  ↓
Reliability
  ↓
Security
  ↓
Experimental evaluation
```

The project should not move to final comparison until the control
pipeline produces valid and bounded actions.

------------------------------------------------------------------------

# 2. Unit Test Matrix

  ID    Module      Test                  Expected
  ----- ----------- --------------------- ---------------------
  U01   Data        Valid trace           Loads successfully
  U02   Data        Missing value         Controlled handling
  U03   Data        Wrong timestamp       Rejected/handled
  U04   TFT         Correct input shape   Accepted
  U05   TFT         Forecast output       Correct horizon
  U06   TFT         Invalid input         Controlled error
  U07   Planner     Valid JSON            Accepted
  U08   Planner     Invalid strategy      Rejected
  U09   PPO         Valid state           Valid action
  U10   PPO         Invalid state         Rejected
  U11   Validator   Capacity overflow     Rejected
  U12   SLA guard   Unsafe scale-in       Blocked/deferred

------------------------------------------------------------------------

# 3. Data Tests

## D01 --- Chronological Ordering

Input may arrive unordered.

Expected:

``` text
All records sorted by timestamp
```

## D02 --- Duplicate Records

Detect and handle duplicate timestamps according to the configured
policy.

## D03 --- Missing Metrics

Check:

``` text
CPU
memory
latency
invocation count
container count
```

Expected behavior must be documented.

## D04 --- Outliers

Identify unrealistic values such as:

``` text
negative invocation rate
negative latency
CPU > 100%
memory < 0
```

These should not silently enter the training dataset.

------------------------------------------------------------------------

# 4. TFT Tests

## T01 --- Input Window

Verify that the model receives exactly the configured historical
sequence length.

## T02 --- Horizon

Verify output length.

## T03 --- No Leakage

Verify:

``` text
Training timestamp < validation timestamp < test timestamp
```

## T04 --- Accuracy

Compute:

``` text
MAE = (1/n) Σ |y_i - ŷ_i|

RMSE = sqrt((1/n) Σ (y_i - ŷ_i)^2)

MAPE = (100/n) Σ |(y_i - ŷ_i)/y_i|
```

MAPE should be interpreted carefully when actual workload approaches
zero.

------------------------------------------------------------------------

# 5. Qwen3 Tests

## Q01 --- Valid Context

Provide a normal structured state.

Expected:

-   valid strategy;
-   valid fields;
-   no arbitrary command.

## Q02 --- High-Demand Context

Expected:

-   planner identifies increasing demand;
-   strategy is consistent with capacity/SLA constraints.

## Q03 --- Low-Demand Context

Expected:

-   planner can recommend controlled capacity reduction where safe.

## Q04 --- SLA-Risk Context

Expected:

-   planner recognizes SLA as a constraint.

## Q05 --- Prompt Injection

Include malicious text in an untrusted metadata field.

Expected:

-   it is treated as data;
-   no permission escalation;
-   no arbitrary command returned.

## Q06 --- Invalid Output

Expected:

``` text
Qwen3
 ↓
schema validator
 ↓
reject
 ↓
fallback
```

------------------------------------------------------------------------

# 6. PPO Tests

## R01 --- Action Set

Every output must belong to:

``` text
{NoOp, PreWarm, ScaleOut, Reuse, ScaleIn, Terminate}
```

## R02 --- Capacity Bounds

``` text
min_capacity ≤ capacity ≤ max_capacity
```

## R03 --- SLA Penalty

Force a simulated SLA violation.

Expected:

``` text
reward decreases
```

## R04 --- Energy Trade-off

Compare a high-capacity and low-capacity state.

Expected: reward reflects both resource cost and SLA/performance
consequences.

------------------------------------------------------------------------

# 7. Integration Tests

## I01

``` text
Metrics → preprocessing → TFT
```

## I02

``` text
TFT → state builder → Qwen3
```

## I03

``` text
Qwen3 → validator → PPO
```

## I04

``` text
PPO → safety guard → executor
```

## I05

``` text
Executor → runtime → Prometheus
```

## I06

``` text
Prometheus → next control cycle
```

------------------------------------------------------------------------

# 8. System Test Scenarios

## S01 --- Low Workload

Goal: - test idle resource reduction.

Measure: - active containers; - CPU utilization; - energy; - latency; -
SLA.

## S02 --- Stable Workload

Goal: - test unnecessary oscillation.

Measure: - number of scaling events; - utilization; - energy; - SLA.

## S03 --- Sudden Spike

``` text
low → medium → very high workload
```

Measure: - forecast lead time; - cold starts; - P95; - SLA violations; -
prewarm timing.

## S04 --- Workload Drop

Measure: - scale-in response; - idle capacity; - latency after scale-in.

## S05 --- Periodic Workload

Example:

``` text
morning ↑
afternoon ↓
evening ↑
```

Measure predictive behavior.

## S06 --- Highly Irregular Workload

Purpose: test robustness when historical patterns are weak.

------------------------------------------------------------------------

# 9. Baseline Evaluation

Run:

``` text
Experiment A:
Reactive baseline

Experiment B:
TFT + Qwen3 + PPO
```

Keep all non-policy variables equal.

------------------------------------------------------------------------

# 10. Ablation Evaluation

  Experiment     TFT   Qwen3   PPO   SLA Guard
  ------------ ----- ------- ----- -----------
  Baseline        No      No    No    Baseline
  A1             Yes      No    No         Yes
  A2             Yes     Yes    No         Yes
  A3              No     Yes   Yes         Yes
  A4             Yes     Yes   Yes          No
  Full           Yes     Yes   Yes         Yes

The purpose is attribution, not just producing a single overall result.

------------------------------------------------------------------------

# 11. Performance Metrics

## Latency

``` text
Mean latency
P95 latency
```

## SLA Compliance

``` text
SLA compliance =
(number of requests satisfying SLA /
 total evaluated requests) × 100
```

## Cold Start Rate

``` text
cold-start rate =
cold-start requests / total requests
```

## Container Utilization

``` text
average utilization =
used capacity / available capacity
```

## Energy per Request

``` text
energy/request =
total measured energy / total completed requests
```

------------------------------------------------------------------------

# 12. Energy Measurement

If direct power measurement is available:

``` text
Energy = ∫ Power(t) dt
```

For sampled measurements:

``` text
E ≈ Σ P_i × Δt
```

If direct measurement is unavailable, clearly label the value as an
estimate based on a documented power model.

Do not present estimated energy as directly measured energy.

------------------------------------------------------------------------

# 13. Statistical Repetition

For each major scenario:

-   Run multiple trials.
-   Keep environment consistent.
-   Record seeds where applicable.
-   Use identical traces for baseline/proposed runs.
-   Report mean and variation.
-   Preserve raw result files.

------------------------------------------------------------------------

# 14. Reliability Tests

## F01 --- TFT Failure

Expected: bounded fallback.

## F02 --- Qwen3 Failure

Expected: no arbitrary action; fallback.

## F03 --- PPO Failure

Expected: safe policy.

## F04 --- Kubernetes API Failure

Expected: controlled error and retry/fallback.

## F05 --- Prometheus Failure

Expected: system detects stale/missing metrics.

## F06 --- Model Output Corruption

Expected: validator blocks execution.

------------------------------------------------------------------------

# 15. Stress Tests

Increase:

``` text
request rate
number of functions
number of containers
control frequency
```

Measure:

-   decision latency;
-   executor latency;
-   monitoring overhead;
-   CPU/memory overhead;
-   stability.

------------------------------------------------------------------------

# 16. Acceptance Criteria

The project passes final system testing when:

-   All critical unit tests pass.
-   Forecast pipeline works.
-   Planner output is validated.
-   PPO actions are bounded.
-   SLA guard works.
-   Infrastructure execution works.
-   Monitoring works.
-   Failure fallback works.
-   Baseline and proposed experiments can be repeated.
-   Results are generated from raw recorded measurements.
