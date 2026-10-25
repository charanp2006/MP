# Infrastructure (P4) — Kubernetes / OpenFaaS / Docker

Execution is **off by default** and **dry-run by default**. The orchestrator.executor translates already-validated abstract actions into allow-listed operations (kubectl scale for an OpenFaaS function deployment). No component accepts raw shell commands or Kubernetes YAML.

See configs/project.yaml -> execution: and docs/security.md for bounds, RBAC and allowlists.
