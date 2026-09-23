# Test Plan --- Predictive Container Management for Energy-Efficient Serverless Computing

## 1. Objective

Verify forecasting, planning, control, execution, SLA protection,
monitoring, security and reproducibility before reporting results.

## 2. Test Levels

  Level          Purpose
  -------------- ----------------------------------
  Unit           Individual functions/modules
  Integration    Communication between modules
  System         Complete closed loop
  Performance    Latency/resource/energy behavior
  Reliability    Failure and recovery
  Security       Authorization and validation
  Experimental   Baseline/proposed comparison

## 3. Unit Tests

### Data

-   Valid trace loading.
-   Malformed record handling.
-   Missing-value handling.
-   Chronological window generation.
-   Correct normalization.

### TFT

-   Correct input shape.
-   Correct forecast horizon.
-   No NaN/invalid output.
-   Checkpoint save/load.

### Qwen3

-   Valid structured input.
-   Valid output schema.
-   Invalid strategy rejection.
-   No arbitrary infrastructure commands.

### PPO

-   Correct state dimensions.
-   Valid action IDs.
-   Finite rewards.
-   SLA penalty applied during violation.

### Validator

-   Reject capacity above maximum.
-   Reject capacity below minimum.
-   Reject invalid action.
-   Reject malformed planner output.

## 4. Forecast Tests

### F-01 Forecast Shape

Expected: configured forecast horizon is returned.

### F-02 Missing Input

Expected: controlled validation/preprocessing behavior.

### F-03 Time Leakage

Expected: test/future observations never enter training.

### F-04 Forecast Metrics

Calculate MAE, RMSE and MAPE on held-out time periods.

## 5. Planner Tests

### P-01 Increasing Demand

Expected: proactive capacity strategy when capacity is insufficient.

### P-02 Falling Demand

Expected: controlled scale-in/reduction when safe.

### P-03 SLA Risk

Expected: SLA is reflected as a high-priority constraint.

### P-04 Malformed Output

Expected: output is rejected and fallback is used.

## 6. PPO Tests

### R-01 Valid State

Policy returns an approved action.

### R-02 SLA Violation

Reward contains the configured SLA penalty.

### R-03 Capacity Boundary

No action exceeds min/max capacity.

### R-04 Stable Workload

Controller can maintain capacity without unnecessary changes.

## 7. Integration Tests

``` text
Metrics → TFT → Forecast → Qwen3 → PPO
      → Validator → Kubernetes/OpenFaaS
      → Prometheus → Feedback
```

Verify each connection independently.

## 8. System Scenarios

  Scenario          Main test
  ----------------- --------------------------------------
  Low workload      Avoid unnecessary capacity
  Stable workload   Steady-state efficiency
  Sudden spike      Forecast/prewarm/cold-start behavior
  Workload drop     Scale-in behavior
  Highly variable   Robustness
  Peak workload     Capacity and SLA protection

## 9. Baseline Test

Run the same workload, duration, infrastructure limits and metrics
for: - Reactive baseline. - Proposed TFT + Qwen3 + PPO system.

Only the management policy should differ.

## 10. Ablation

  Experiment   Components
  ------------ ----------------------
  E1           Reactive baseline
  E2           TFT + proactive rule
  E3           TFT + Qwen3
  E4           PPO without TFT
  E5           TFT + Qwen3 + PPO

## 11. Metrics

### Forecast

``` text
MAE
RMSE
MAPE
```

### System

``` text
Mean latency
P95 latency
SLA compliance
Cold-start rate
Active containers
CPU utilization
Memory utilization
Total energy
Energy/request
```

### Relative change

``` text
((Baseline - Proposed) / Baseline) × 100
```

Use this direction only for metrics where lower is better.

## 12. Repetition

Run multiple trials, keep workload and environment controlled, record
random seeds where applicable, and report variation as well as averages.

## 13. Failure Tests

Test: - TFT unavailable. - Qwen3 unavailable. - PPO unavailable. -
Prometheus unavailable. - Kubernetes API unavailable. - Malformed
planner output. - Invalid forecast. - Capacity limit reached. -
Timeout/network failure.

Expected: controlled fallback, bounded actions and continued monitoring.

## 14. Acceptance Criteria

-   Core tests pass.
-   Forecast outputs are valid.
-   Planner output passes schema validation.
-   PPO uses only approved actions.
-   Kubernetes actions respect limits.
-   SLA monitoring works.
-   Baseline/proposed experiments are reproducible.
-   Every reported result is supported by recorded measurements.
