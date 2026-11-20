# Infrastructure — Kubernetes / OpenFaaS / Docker

Execution is **off by default**, **dry-run by default**, and **live control is off
by default**. `orchestrator.executor` translates already-validated abstract
actions into fixed, allow-listed operations. No component accepts raw shell
commands, Kubernetes YAML, function names or image names from the planner or PPO.

## Backends

| `execution.backend` | Executor | Operation template |
|---|---|---|
| `noop` | `NoOpExecutor` | No platform call |
| `kubernetes` | `KubernetesExecutor` | `kubectl -n <allowed namespace> scale deployment/<function> --replicas=<bounded target>` |
| `openfaas` | `OpenFaaSExecutor` | Same bounded operation against `execution.openfaas_namespace` (default `openfaas-fn`) |
| `docker` | `DockerExecutor` | `docker service scale <allowed service>=<bounded target>` |

Live execution requires all of: `execution.enabled: true`,
`execution.dry_run: false`, and `execution.allow_live: true`. Keep
`allow_live: false` unless a local cluster/service is deliberately targeted and
the RBAC/service allowlists have been reviewed.

## Local scaffolding

- `kubernetes/rbac.yaml`: least-privilege ServiceAccount/Role/RoleBinding for
  `fn-checkout`; no cluster-admin.
- `kubernetes/deployment.yaml`: bounded two-replica sample function deployment.
- `openfaas/stack.yml`: local OpenFaaS stack definition for `fn-checkout`.
- `docker/docker-compose.yml`: local Docker Swarm-compatible service definition.

These files are deployment scaffolding. They were not applied to a live cluster
during M6; no live execution, Prometheus scrape or Grafana observation is
claimed. See `configs/project.yaml -> execution` and `docs/security.md` for
bounds, allowlists and trust boundaries.
