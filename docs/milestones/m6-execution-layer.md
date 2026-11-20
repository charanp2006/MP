<style>
:root {
  --oc-bg: #0a0a0a;
  --oc-panel: #141414;
  --oc-raised: #1e1e1e;
  --oc-border: #3c3c3c;
  --oc-border-strong: #484848;
  --oc-text: #eeeeee;
  --oc-muted: #808080;
  --oc-heading: #9d7cd8;
  --oc-primary: #fab283;
  --oc-link: #56b6c2;
  --oc-code: #7fd88f;
  --oc-strong: #f5a742;
  --oc-emph: #e5c07b;
  --oc-error: #e06c75;
  --oc-font: Consolas, "Cascadia Mono", "Cascadia Code", "Courier New", monospace;
}
html { background: var(--oc-bg) !important; }
body {
  background: var(--oc-bg) !important;
  color: var(--oc-text) !important;
  font-family: var(--oc-font) !important;
  font-size: 16px !important;
  line-height: 1.55 !important;
  font-variant-ligatures: none;
  -webkit-font-smoothing: antialiased;
}
body.vscode-body {
  /* max-width: 100ch !important; */
  margin: 0 auto !important;
  padding: 34px 28px 64px !important;
}
#write {
  max-width: 100ch !important;
  margin: 0 auto !important;
  padding: 34px 28px 64px !important;
  font-family: var(--oc-font) !important;
  font-size: 16px !important;
  line-height: 1.55 !important;
  color: var(--oc-text) !important;
  background: transparent !important;
}
body.vscode-body *, #write *, .oc-doc * { font-family: var(--oc-font) !important; }
h1, h2, h3, h4, h5, h6 {
  color: var(--oc-heading) !important;
  font-weight: 700 !important;
  line-height: 1.3 !important;
  margin: 1.6em 0 .6em !important;
  padding: 0 !important;
  border: 0 !important;
  background: transparent !important;
}
h1 { font-size: 1.5em !important; text-decoration: underline !important; text-underline-offset: 5px; text-decoration-thickness: 1px; }
h2 { font-size: 1.3em !important; }
h3 { font-size: 1.15em !important; }
h4 { font-size: 1.05em !important; }
h5, h6 { font-size: 1em !important; }
p { margin: .8em 0 !important; }
strong, b { color: var(--oc-strong) !important; font-weight: 700 !important; }
em, i { color: var(--oc-emph) !important; font-style: italic !important; }
del, s { color: var(--oc-muted) !important; }
a { color: var(--oc-link) !important; text-decoration: underline !important; text-underline-offset: 2px; }
a[href^="http"]::after {
  content: " (" attr(href) ")";
  color: var(--oc-primary) !important;
  font-size: .88em;
  word-break: break-all;
}
code {
  color: var(--oc-code) !important;
  background: transparent !important;
  border: 0 !important;
  padding: 0 !important;
  font-size: 1em !important;
  font-family: var(--oc-font) !important;
  white-space: break-spaces;
}
pre {
  background: var(--oc-panel) !important;
  border: 1px solid var(--oc-border) !important;
  padding: 14px 16px !important;
  margin: 1em 0 !important;
  overflow-x: auto !important;
  line-height: 1.5 !important;
  font-size: 1em !important;
  box-shadow: none !important;
}
pre code {
  color: var(--oc-text) !important;
  background: transparent !important;
  border: 0 !important;
  padding: 0 !important;
  font-size: 1em !important;
  white-space: pre;
}
ul, ol { margin: .8em 0 !important; padding-left: 1.7em !important; }
li { margin: .28em 0 !important; }
li::marker { font-family: var(--oc-font) !important; }
ul > li::marker { color: var(--oc-primary) !important; }
ol > li::marker { color: var(--oc-link) !important; }
ul ul > li::marker { color: var(--oc-link) !important; }
ul ul ul > li::marker { color: var(--oc-emph) !important; }
input[type="checkbox"] { accent-color: var(--oc-code) !important; }
blockquote {
  margin: 1em 0 !important;
  padding: .15em 0 .15em 1em !important;
  border-left: 2px solid var(--oc-border-strong) !important;
  background: transparent !important;
  color: var(--oc-emph) !important;
  font-style: italic !important;
}
blockquote p { color: var(--oc-emph) !important; margin: .3em 0 !important; }
hr {
  border: 0 !important;
  border-top: 1px solid var(--oc-muted) !important;
  height: 0 !important;
  margin: 1.8em 0 !important;
  background: transparent !important;
}
table { border-collapse: collapse !important; margin: 1em 0 !important; width: auto !important; }
th, td { border: 1px solid var(--oc-border) !important; padding: 6px 12px !important; }
th { background: var(--oc-raised) !important; color: var(--oc-text) !important; font-weight: 700 !important; }
img { max-width: 100% !important; border: 1px solid var(--oc-border) !important; border-radius: 3px !important; }
kbd {
  background: var(--oc-raised) !important;
  border: 1px solid var(--oc-border-strong) !important;
  border-bottom-width: 2px !important;
  padding: 1px 5px !important;
  color: var(--oc-text) !important;
  font-size: .9em !important;
}
::selection { background: var(--oc-heading) !important; color: var(--oc-bg) !important; }
* { scrollbar-color: var(--oc-border) var(--oc-bg); }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: var(--oc-bg); }
::-webkit-scrollbar-thumb { background: var(--oc-border); }
.hljs-comment, .hljs-quote { color: var(--oc-muted) !important; font-style: italic; }
.hljs-keyword, .hljs-selector-tag, .hljs-literal { color: var(--oc-heading) !important; font-style: italic; }
.hljs-type { color: var(--oc-emph) !important; font-style: italic; font-weight: 700; }
.hljs-string, .hljs-regexp, .hljs-symbol, .hljs-bullet { color: var(--oc-code) !important; }
.hljs-number { color: var(--oc-strong) !important; }
.hljs-title, .hljs-section, .hljs-title.function_, .hljs-function .hljs-title { color: var(--oc-primary) !important; }
.hljs-variable, .hljs-template-variable, .hljs-params, .hljs-built_in, .hljs-builtin-name { color: var(--oc-error) !important; }
.hljs-class .hljs-title, .hljs-title.class_ { color: var(--oc-emph) !important; }
.hljs-operator, .hljs-punctuation { color: var(--oc-link) !important; }
.hljs-attr, .hljs-attribute, .hljs-property { color: var(--oc-primary) !important; }
.hljs-tag { color: var(--oc-error) !important; }
.hljs-name { color: var(--oc-heading) !important; }
.hljs-meta { color: var(--oc-muted) !important; }
.hljs-addition { color: #4fd6be !important; background: #20303b !important; }
.hljs-deletion { color: #c53b53 !important; background: #37222c !important; }
.token.comment, .token.prolog, .token.doctype, .token.cdata { color: var(--oc-muted) !important; font-style: italic; }
.token.keyword { color: var(--oc-heading) !important; font-style: italic; }
.token.tag { color: var(--oc-error) !important; }
.token.string, .token.attr-value, .token.char { color: var(--oc-code) !important; }
.token.number, .token.boolean { color: var(--oc-strong) !important; }
.token.function, .token.class-name { color: var(--oc-primary) !important; }
.token.variable, .token.parameter { color: var(--oc-error) !important; }
.token.operator, .token.punctuation { color: var(--oc-link) !important; }
.cm-keyword { color: var(--oc-heading) !important; font-style: italic; }
.cm-builtin { color: var(--oc-error) !important; }
.cm-string, .cm-string-2, .cm-atom { color: var(--oc-code) !important; }
.cm-number, .cm-literal { color: var(--oc-strong) !important; }
.cm-def, .cm-variable-2, .cm-variable-3 { color: var(--oc-primary) !important; }
.cm-variable, .cm-variable-1 { color: var(--oc-error) !important; }
.cm-comment { color: var(--oc-muted) !important; font-style: italic; }
.cm-operator, .cm-bracket { color: var(--oc-link) !important; }
.cm-property, .cm-attribute { color: var(--oc-primary) !important; }
.cm-tag { color: var(--oc-error) !important; }
.cm-type { color: var(--oc-emph) !important; }
.cm-meta { color: var(--oc-muted) !important; }
.oc-green { color: var(--oc-code) !important; }
.oc-orange { color: var(--oc-strong) !important; }
.oc-purple { color: var(--oc-heading) !important; }
</style>

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
