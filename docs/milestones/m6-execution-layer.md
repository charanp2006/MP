# Milestone 6 — Execution Layer

| Field | Value |
|---|---|
| Milestone | M6 — Execution layer |
| Status | Complete for bounded dry-run/adapters; live cluster validation pending |
| Date | 2026-11-20 |
| Branch | `feat/m5-decision-engine-integration` |
| Related commit | `7f8e1e5` (base; M6 changes uncommitted) |
| Test IDs | F04, F05, I01–I06, S01–S06 |
| Architecture layers | Layer 9 validator/shield boundary; Layer 10 execution; Layer 11 monitoring |
| Evidence class | Unit tests + dry-run smoke; **no live platform deployment** |

## Objective

Translate already-validated abstract PPO/DecisionLoop actions into fixed,
allow-listed platform operations across Kubernetes, OpenFaaS and Docker while
preserving safety defaults, append-only audit provenance and a testable
Prometheus metrics boundary.

## Module map

| File | Role |
|---|---|
| `orchestrator/executor.py` | `NoOpExecutor`, `KubernetesExecutor`, `OpenFaaSExecutor`, `DockerExecutor`, `build_executor()` |
| `orchestrator/execution_audit.py` | `ExecutionAuditLogger` (append-only JSONL audit with redaction) |
| `orchestrator/decision_loop.py` | Injects `ExecutionAuditLogger`; records backend/code/target/commands for every execution attempt |
| `monitoring/prometheus_adapter.py` | Injectable Prometheus query adapter with stale/missing metric detection |
| `configs/project.yaml` | `execution.allow_live`, audit path, OpenFaaS namespace, Docker allowlist, Prometheus queries |
| `infrastructure/kubernetes/rbac.yaml` | Least-privilege ServiceAccount/Role/RoleBinding for `fn-checkout` |
| `infrastructure/kubernetes/deployment.yaml` | Bounded sample Kubernetes Deployment |
| `infrastructure/openfaas/stack.yml` | Local OpenFaaS stack definition |
| `infrastructure/docker/docker-compose.yml` | Local Docker Swarm-compatible service definition |
| `infrastructure/README.md` | Backend command templates and live-execution opt-in rules |
| `tests/test_m6_execution.py` | M6 unit/safety tests |
| `tests/test_executor.py` | Existing executor safety tests retained |

## Design and data contracts

### Execution contract

`ExecutionResult` now carries `backend` (`noop`, `kubernetes`, `openfaas`,
`docker`, or `unspecified`) plus `ok`, `code`, `reason`, `dry_run`, `executed`,
`operation`, `target_capacity` and `commands`. Commands are fixed templates,
not data accepted from the planner or PPO:

- `kubectl -n <allowed namespace> scale deployment/<function> --replicas=<bounded target>`
- `docker service scale <allowed service>=<bounded target>`

The final authority remains `SafetyShield`; executor authorization is a
separate gate and does not bypass SLA/bounds checks. `Reuse` with no warm
capacity is rejected before any platform call.

### Live execution gate

A real subprocess call requires all three:

1. `execution.enabled: true`
2. `execution.dry_run: false`
3. `execution.allow_live: true`

Defaults are `false`, `true`, `false`. With `allow_live=false`, the executor
returns `code=live_disabled`, `executed=false` and records the bounded command
it would have run. No arbitrary shell string or unchecked namespace/service is
accepted.

### Audit contract

`orchestrator/execution_audit.py` appends one redacted JSON object per attempt
to `execution.audit_path` (`results/execution/audit.jsonl` by default).
Records include `correlation_id`, `final_action`, `authorized`, `backend`,
`operation`, `target_capacity`, `code`, `reason`, `dry_run`, `executed`, `ok`,
`commands`, sanitized `context`, schema version and UTC timestamp.

### Metrics contract

`PrometheusMetricsAdapter.fetch()` maps configured PromQL results to
`current_workload`, `p95_latency_ms`, `cold_starts`, `energy` and
`active_containers`. Missing/empty/failed queries produce `stale=true` and
per-query error strings; missing required workload or p95 is treated as stale
rather than silently substituted with estimated values.

## How to run and verify

```powershell
py -m py_compile orchestrator/executor.py orchestrator/execution_audit.py orchestrator/decision_loop.py orchestrator/__init__.py monitoring/prometheus_adapter.py monitoring/__init__.py experiments/evaluate_decision_engine.py tests/test_m6_execution.py
py -m pytest tests/test_m6_execution.py tests/test_executor.py tests/test_orchestrator.py tests/test_m5_decision_engine.py -ra
py -m orchestrator.decision_loop --steps 3 --execute --policy none
py -m pytest -ra
```

Expected dry-run smoke result: `modes.execute=true`, executor `code=disabled`,
`dry_run=true`, `executed=false`, `backend=kubernetes`, with matching entries in
`results/execution/audit.jsonl`.

## Test coverage

| Test | Purpose | Result |
|---|---|---|
| `test_openfaas_executor_uses_function_namespace` | OpenFaaS backend binds to `openfaas-fn` and fixed kubectl template | Passed |
| `test_docker_executor_dry_run_and_service_allowlist` | Docker command template, dry-run, service allowlist rejection | Passed |
| `test_live_execution_requires_explicit_allow_live` | No subprocess call without explicit opt-in | Passed |
| `test_execution_audit_records_backend_and_bounded_command` | Audit schema and bounded target command | Passed |
| `test_decision_loop_writes_execution_audit` | DecisionLoop audit integration/correlation ID | Passed |
| `test_prometheus_adapter_maps_queries_to_state_metrics` | Injected query mapping to state metrics | Passed |
| `test_prometheus_adapter_marks_stale_when_query_fails` | F05 stale/missing metric path | Passed |
| Existing `tests/test_executor.py` | Disabled/dry-run/allowlist/no-shell-string invariants | Passed |

Focused verification: `41 passed in 5.71s`.

## Evidence, limitations and next steps

- **Measured here:** unit tests, compile check, dry-run CLI smoke and audit
  file creation. No energy/latency/performance improvement is claimed.
- **Simulated:** reward/latency/energy values in `ServerlessEnv` remain research
  surrogate metrics from M4/M5, not live platform telemetry.
- **Scaffolding only:** `infrastructure/` manifests and stack files were not
  applied to a cluster; `monitoring/prometheus_adapter.py` was exercised with
  an injected query function, not a live Prometheus server.
- **Pending:** apply manifests to a local cluster, run `kubectl auth can-i
  scale deployment/fn-checkout --as=system:serviceaccount:serverless-mgmt:controller`,
  deploy OpenFaaS/Docker function images, enable a controlled live run, verify
  Prometheus scrape/Grafana panels, and produce F04/F05 live evidence in M7/M8.
- **Safety:** keep `allow_live=false` outside an explicitly controlled local
  experiment; never expose cluster credentials to the planner or PPO.
