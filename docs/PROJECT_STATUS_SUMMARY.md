# Phase 1 Project Status Summary

| Field | Value |
|---|---|
| Document | Consolidated status of all work completed in this repository |
| Date | 2026-11-21 |
| Current git branch | `main` (work is uncommitted) |
| Related commit | none for the current changes |
| Status | Phase 1 prototype complete; real Qwen3 inference remains deferred |
| Verification | 169 Python tests passed; live G/H cluster verification passed |

## 1. Scope and canonical decisions

This repository is a research prototype for predictive, autonomous container
management in serverless computing. The implemented control loop is:

```text
Azure Functions trace data
  -> fixed-window preprocessing and features
  -> TFT workload forecast
  -> Qwen3/stub high-level plan
  -> PPO bounded action
  -> schema, SLA, authorization and safety validation
  -> Kubernetes + OpenFaaS + Docker execution
  -> Prometheus + Grafana observation
  -> decision/execution logging and feedback
```

Canonical choices retained throughout:

- Forecast model: Temporal Fusion Transformer (`TFT`).
- Agentic planner: Qwen3 contract with stub/rules runtime for local evidence.
- Controller: PPO with fixed action set
  `NoOp, PreWarm, ScaleOut, Reuse, ScaleIn, Terminate`.
- Execution: Kubernetes + OpenFaaS + Docker.
- Observability: Prometheus + Grafana.
- Dataset: Azure Functions traces are the data source only.
- SLA: P95 latency is the primary constraint.
- Defaults remain in `configs/project.yaml`; live-only overrides are isolated
  in `configs/local-live.yaml`.

## 2. Completed work

### 2.1 Data and forecasting

- Implemented ingestion, chronological preprocessing, feature engineering and
  pipeline artifacts under `data/`.
- Added compact TFT training/evaluation and reusable forecast service under
  `forecasting/`.
- Preserved chronological train/validation/test discipline; no random shuffle
  of time series data.
- Added `docs/forecasting-dashboard.html` and
  `scripts/generate_forecast_dashboard.py` with offline TFT/baseline evidence.

### 2.2 Decision engine and controllers

- Implemented planner schemas, validation, state construction, safety shield,
  SLA guard and bounded decision loop under `agent/` and `orchestrator/`.
- Implemented PPO environment, reward, smoke training and evaluation under
  `rl/`.
- Added stub/rules Qwen3-compatible planner runtime; real Ollama/Qwen3
  inference remains explicitly deferred.
- Added `docs/agentic-planning-dashboard.html`,
  `docs/ppo-controller-dashboard.html`,
  `docs/ai-driven-decision-engine-dashboard.html` and their generators
  `scripts/generate_component_dashboards.py` and
  `scripts/generate_decision_engine_dashboard.py`.

### 2.3 Execution and live infrastructure

- Existing dry-run execution adapters were preserved:
  `NoOpExecutor`, `KubernetesExecutor`, `OpenFaaSExecutor`, `DockerExecutor`.
- Added `orchestrator/live_executor.py` with `LiveKubernetesExecutor`:
  - real bounded `kubectl scale`,
  - allowlisted namespaces and deployments,
  - warm-pool scaling for `PreWarm`/`Reuse`,
  - post-action replica verification,
  - rollback and cooldown,
  - audit-compatible `ExecutionResult`.
- Registered `backend: kubernetes_live` in `orchestrator/executor.py`.
- Added live-only function and manifests:
  - `demo/services/live_app.py`,
  - `demo/services/Dockerfile.live`,
  - `infrastructure/openfaas/stack.live.yml`,
  - `infrastructure/openfaas/stack.public-router.yml`,
  - `infrastructure/kubernetes/live-namespaces.yaml`,
  - `infrastructure/kubernetes/live-service.yaml`,
  - `infrastructure/kubernetes/live-function-deployment.yaml`,
  - `infrastructure/kubernetes/live-warm-pool.yaml`.
- Added `configs/local-live.yaml`; `configs/__init__.py` now supports safe
  `extends` + deep merge without changing canonical defaults.

### 2.4 Monitoring, feedback and live dashboards

- Preserved host-level Prometheus/Grafana scaffolding under `monitoring/`.
- Added in-cluster monitoring assets:
  - `monitoring/Dockerfile.exporter`,
  - `monitoring/kubernetes/control-loop-exporter.yaml`,
  - `monitoring/kubernetes/prometheus-values.yaml`,
  - `monitoring/grafana/dashboards/control-loop-live.json`.
- Extended `monitoring/metrics.py` with optional snapshot publishing.
- Extended `monitoring/prometheus_exporter.py` with `/publish`.
- Wired `DecisionLoop` to Prometheus metrics through
  `PrometheusMetricsAdapter`; stale metrics force `NOOP`.
- Added live telemetry for PPO actions, guard interventions, SLA violations,
  planner latency/fallback, forecast error and step outcomes.
- Added `docs/runbooks/live-g-h.md` with exact install, deploy, run and verify
  commands.

### 2.5 Evaluation, demo and phase records

- M8 consolidated baseline-vs-proposed evaluation and ablations were completed
  earlier and externally merged.
- M9 demo integration was implemented earlier and included synthetic client,
  ingestion adapter, event/decision/audit artifacts and dashboards.
- Added versioned phase record
  `docs/implementation/p6-v1.0-live-execution-and-monitoring.md`.
- Updated `README.md`, `AGENTS.md` and
  `docs/implementation/README.md` docs maps/indexes.

## 3. Live Phase G/H evidence (2026-11-21)

Local target: Docker Desktop Kubernetes, context `docker-desktop`, node
`desktop-control-plane`, Kubernetes `v1.36.1`.

Deployed:

- OpenFaaS CE in namespace `openfaas`, functions in `openfaas-fn`.
- kube-prometheus-stack in namespace `monitoring`.
- Live function `fn-checkout` and warm pool `fn-checkout-warm`.
- Control-loop exporter and Grafana dashboard ConfigMap.

Verified:

- OpenFaaS gateway invocation returned
  `{"message":"ok","function":"fn-checkout","bytes":20}`.
- Live bounded execution returned
  `execution.code=executed`, `operation=prewarm`, `target_capacity=4`.
- Exact command applied:
  `kubectl -n serverless-mgmt scale deployment/fn-checkout-warm --replicas=4`.
- Post-action replica verification succeeded.
- `python scripts/verify_live_g_h.py` returned `passed: true`:
  node ready, namespaces present, gateway/exporter/Prometheus/Grafana healthy,
  Prometheus metrics non-stale, dashboard UID `control-loop-live` present, and
  live function invocation successful.
- The smoke run used the trained TFT checkpoint and stub planner runtime.

## 4. Verification performed

- `python -m pytest -q --disable-warnings` passed with 169 tests.
- `python -m json.tool monitoring/grafana/dashboards/control-loop-live.json`
  passed.
- `bash -n scripts/deploy_live_g_h.sh` passed.
- `python -m compileall -q configs orchestrator monitoring demo scripts` passed.
- `git diff --check` passed; Git reported only a CRLF normalization warning for
  `monitoring/__init__.py`.
- No commit, push or PR was created.

## 5. Known limitations

- Real Qwen3/Ollama inference remains a deferred Phase D item. Live evidence
  uses the stub/rules planner and must be labelled accordingly.
- Numeric targets such as 15-25% energy reduction and 20-30% cold-start
  reduction remain targets, not measured results.
- The live energy metric is a payload-size proxy, not a measured watt reading.
- Docker Desktop Kubernetes is a local research target, not production HA.
- OpenFaaS CE rejects locally built images through `faas-cli deploy`; the
  gateway function record is registered with a public router image and patched
  to the local image.
- Local image loading uses
  `docker save <image> | docker exec -i desktop-control-plane ctr --namespace k8s.io images import -`;
  other clusters need a registry or `kind load docker-image`.
- Live verification requires port-forwards for Grafana, Prometheus, OpenFaaS
  gateway and the control-loop exporter.

## 6. Key commands

```bash
bash scripts/deploy_live_g_h.sh

kubectl -n openfaas port-forward svc/gateway 8080:8080
kubectl -n monitoring port-forward svc/monitoring-grafana 3000:80
kubectl -n monitoring port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090
kubectl -n monitoring port-forward svc/control-loop-exporter 8000:8000

python -m orchestrator.decision_loop \
  --config configs/local-live.yaml \
  --metrics-source prometheus \
  --use-tft \
  --execute \
  --steps 1

python scripts/verify_live_g_h.py --config configs/local-live.yaml
```

## 7. Suggested delivery metadata

- Branch: `feat/phase-g-h-live-execution-monitoring`
- Commit message: `feat(live): add validated Kubernetes execution and monitoring loop`
- PR title: `Phase G/H: live Kubernetes execution and in-cluster monitoring`
- PR description: see section 8 below.

## 8. Pull request description

### Summary

Implements and validates the final live execution and monitoring objectives for
the Phase 1 prototype. Adds bounded real Kubernetes/OpenFaaS execution,
live Prometheus-backed decision-loop inputs, in-cluster Grafana dashboards,
local live configuration, deployment/verification scripts, tests and docs.
Canonical dry-run defaults and all existing scaffolding are preserved.

### Changes

- Added `LiveKubernetesExecutor` with bounded `kubectl scale`, warm-pool
  support, verification, rollback and cooldown.
- Added live function image, OpenFaaS stack files and Kubernetes manifests.
- Added `configs/local-live.yaml` and safe config `extends`/deep-merge support.
- Wired Prometheus metrics into `DecisionLoop` with stale-metric NOOP guard.
- Added live control-loop exporter, scrape configuration and Grafana dashboard.
- Added four HTML dashboards and generators for forecasting, planner, PPO and
  unified decision-engine evidence.
- Added deploy/verify scripts, runbook, phase record and status summary.
- Added tests covering live gates, bounded actions, rollback, stale metrics,
  live app metrics, exporter publishing and dashboard content.

### Verification

- 169 tests passed.
- Live Docker Desktop Kubernetes deployment verified with OpenFaaS invocation,
  verified `PreWarm` scale action and `verify_live_g_h.py` reporting
  `passed: true`.
- JSON, shell syntax, Python compile and `git diff --check` passed.

### Limitations

- Real Qwen3 inference remains deferred; live planner evidence is stub/rules.
- Energy is an explicit proxy.
- CE public-image restriction handled via public router registration plus
  local image patch.
- No performance improvement is claimed from the smoke run.
