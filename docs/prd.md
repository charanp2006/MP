# PRD --- Predictive Container Management for Energy-Efficient Serverless Computing

## 1. Product Overview

This project develops a predictive, autonomous serverless
container-management system. It combines a **Temporal Fusion Transformer
(TFT)** for workload forecasting, **Qwen3** for high-level agentic
planning, **PPO** for fast SLA-aware control, and
**Kubernetes/OpenFaaS/Docker** for execution.

### Core objective

Reduce unnecessary resource/energy consumption and cold-start impact
while maintaining the defined SLA.

## 2. Problem Statement

Reactive scaling responds after workload changes become visible. Sudden
demand can therefore cause cold starts and latency, while maintaining a
large warm pool wastes resources. The proposed system predicts upcoming
workload and uses the prediction to make proactive, bounded, SLA-aware
decisions.

## 3. Goals

-   Forecast short-term serverless workload.
-   Plan proactive container actions.
-   Use PPO for operational control.
-   Protect P95 latency/SLA.
-   Reduce unnecessary container capacity and energy use.
-   Reduce cold starts.
-   Improve CPU/memory utilization.
-   Compare against a reactive autoscaling baseline.

## 4. Users

  -----------------------------------------------------------------------
  User                                Need
  ----------------------------------- -----------------------------------
  Cloud/serverless researcher         Evaluate predictive resource
                                      management

  Infrastructure engineer             Study scaling/container behavior

  Project evaluator                   Demonstrate an end-to-end AI/cloud
                                      system

  Platform administrator              Monitor workload, SLA and resources
  -----------------------------------------------------------------------

## 5. Scope

### In scope

Data ingestion, preprocessing, TFT forecasting, Qwen3 planning, PPO
control, SLA-aware reward, Kubernetes/OpenFaaS execution, monitoring,
baseline comparison, ablation and evaluation.

### Out of scope

Production deployment across multiple providers, guaranteed energy
savings before experiments, unrestricted LLM control of infrastructure,
and handling sensitive production workloads.

## 6. Functional Requirements

1.  Ingest historical workload traces.
2.  Collect CPU, memory, latency, active-container and cold-start
    metrics.
3.  Generate short-term workload forecasts.
4.  Generate structured Qwen3 management plans.
5.  Select actions with PPO.
6.  Enforce SLA constraints.
7.  Execute only approved actions.
8.  Monitor with Prometheus/Grafana.
9.  Run reproducible baseline and proposed experiments.
10. Calculate forecasting, SLA, cold-start, utilization and energy
    metrics.

## 7. Non-Functional Requirements

-   **Performance:** controller decisions must fit the selected control
    interval.
-   **Reliability:** model/service failures must have a safe fallback.
-   **Reproducibility:** record model, configuration, trace and
    experiment parameters.
-   **Explainability:** record forecast → plan → action → outcome.
-   **Security:** least privilege, secret protection and action
    validation.
-   **Maintainability:** keep forecasting, planning, control and
    execution modular.

## 8. Key Metrics

  Metric                   Purpose
  ------------------------ -------------------------------
  MAE/RMSE/MAPE            Forecast quality
  Mean/P95 latency         Performance and tail behavior
  SLA compliance           Service protection
  Cold-start rate          Cold-start impact
  Active containers        Capacity usage
  CPU/memory utilization   Resource efficiency
  Total energy             Energy cost
  Energy/request           Normalized efficiency

## 9. Success Criteria

A successful project produces a functioning closed-loop prototype and
experimental evidence comparing it with a defined reactive baseline. Any
numerical improvement targets are project targets, not guaranteed
results.

## 10. Deliverables

-   Preprocessing/data pipeline
-   Trained TFT model
-   Qwen3 planning component
-   PPO controller
-   Kubernetes/OpenFaaS deployment
-   Prometheus/Grafana dashboards
-   Baseline
-   Experiment scripts
-   Evaluation plots/tables
-   Final report and presentation
