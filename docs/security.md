# SECURITY --- Predictive Container Management for Energy-Efficient Serverless Computing

# 1. Security Objective

The project combines an LLM-based planner, a reinforcement-learning
controller and infrastructure APIs. Therefore the most important
security principle is:

> **No AI component should have unrestricted authority over
> infrastructure.**

The architecture uses multiple independent controls between AI output
and execution.

------------------------------------------------------------------------

# 2. Security Architecture

``` mermaid
flowchart TD
    A[External / Workload Data]
    A --> B[Input Validation]
    B --> C[TFT]
    C --> D[Qwen3]
    D --> E[Output Schema Validation]
    E --> F[Policy Validation]
    F --> G[PPO]
    G --> H[Action Validation]
    H --> I[SLA Guard]
    I --> J[RBAC / Authorization]
    J --> K[Restricted Executor]
    K --> L[Kubernetes/OpenFaaS]
    L --> M[Monitoring/Audit]
```

------------------------------------------------------------------------

# 3. Threat Model

## Threat T01 --- Prompt Injection

Untrusted workload metadata could contain text intended to manipulate
the planner.

### Protection

-   Treat metadata as untrusted.
-   Use structured fields.
-   Do not place untrusted text in system instructions.
-   Restrict output schema.
-   Validate output independently.

------------------------------------------------------------------------

## Threat T02 --- Unsafe LLM Output

Qwen3 could return an unsupported strategy or malformed values.

### Protection

``` text
Qwen3
 ↓
schema validation
 ↓
policy validation
 ↓
reject if invalid
```

------------------------------------------------------------------------

## Threat T03 --- Runaway Scaling

An incorrect controller could continuously increase containers.

### Protection

``` text
minimum capacity
maximum capacity
maximum change/cycle
cooldown
rate limiting
```

------------------------------------------------------------------------

## Threat T04 --- Unauthorized Kubernetes Access

A compromised AI service could attempt privileged infrastructure
operations.

### Protection

-   Dedicated service account.
-   RBAC.
-   Restricted namespace.
-   No cluster-admin.
-   Action-specific executor.

------------------------------------------------------------------------

# 4. Trust Boundaries

## Boundary 1 --- Data → AI

All external data is untrusted.

## Boundary 2 --- Qwen3 → Control

LLM output is untrusted.

## Boundary 3 --- PPO → Executor

Learned actions are untrusted until policy validation.

## Boundary 4 --- Executor → Kubernetes

Authorization is required.

------------------------------------------------------------------------

# 5. Least-Privilege Design

Recommended:

``` text
Qwen3
  │
  │ structured plan
  ▼
Planner service
  │
  │ validated plan
  ▼
PPO service
  │
  │ action ID
  ▼
Safety controller
  │
  │ authorized operation
  ▼
Restricted executor
  │
  ▼
Kubernetes/OpenFaaS
```

Qwen3 should not receive a Kubernetes token.

------------------------------------------------------------------------

# 6. RBAC

Use:

``` text
ServiceAccount
     ↓
Role
     ↓
RoleBinding
```

Permissions should be restricted to the resources actually needed.

Avoid:

``` text
cluster-admin
```

for the autonomous controller.

------------------------------------------------------------------------

# 7. Action Allowlist

Only predefined operations should be executable:

``` text
NoOp
PreWarm
ScaleOut
Reuse
ScaleIn
Terminate
```

No action should contain arbitrary shell code.

------------------------------------------------------------------------

# 8. Parameter Validation

For example:

``` text
requested_capacity = 50
maximum_capacity = 30

→ reject
```

Likewise:

``` text
requested_capacity = 0
minimum_capacity = 2

→ reject
```

------------------------------------------------------------------------

# 9. SLA Security/Safety Boundary

Security is not only about unauthorized access. The control layer must
also protect service availability.

Example:

``` mermaid
flowchart TD
    A[Scale-In Request] --> B{P95 Near SLA?}
    B -- Yes --> C[Block/Delay]
    B -- No --> D[Continue Validation]
    D --> E[Execute]
```

This prevents aggressive resource reduction from immediately harming the
service.

------------------------------------------------------------------------

# 10. Secrets

Never place these in:

-   source code;
-   prompts;
-   logs;
-   model input;
-   Git repositories.

Examples:

``` text
Kubernetes tokens
API keys
cloud credentials
database passwords
```

Use secret-management mechanisms appropriate to the deployment.

------------------------------------------------------------------------

# 11. Container Security

Recommended:

-   Non-root containers.
-   Minimal images.
-   Image scanning.
-   Pinned versions.
-   No privileged containers.
-   Dropped capabilities.
-   CPU/memory limits.
-   Read-only filesystem where practical.
-   Regular dependency updates.

------------------------------------------------------------------------

# 12. Network Security

Use:

-   TLS where applicable.
-   Authentication.
-   Network policies.
-   Restricted ingress.
-   Restricted egress.
-   Private Kubernetes API access.
-   Service-to-service authorization.

------------------------------------------------------------------------

# 13. Monitoring Security

Prometheus/Grafana should not be exposed unnecessarily.

Protect:

``` text
Prometheus endpoints
Grafana
Kubernetes API
AI service endpoints
```

Use authentication and network restrictions appropriate to the
environment.

------------------------------------------------------------------------

# 14. Audit Logging

Each action should create an audit record:

``` json
{
  "timestamp": "...",
  "experiment_id": "...",
  "forecast": "...",
  "planner_strategy": "prewarm",
  "ppo_action": "scale_out",
  "requested_change": 3,
  "validated": true,
  "executed": true,
  "sla_status": "within_target"
}
```

Never store secrets in these records.

------------------------------------------------------------------------

# 15. Model Security

Protect:

``` text
TFT checkpoint
PPO policy
configuration
prompt templates
action schema
```

An attacker who replaces a model could influence resource decisions even
if Kubernetes permissions remain restricted.

Use:

-   version control;
-   checksums/integrity checks;
-   controlled model deployment;
-   access restrictions.

------------------------------------------------------------------------

# 16. Data Privacy

The project should use only the data necessary for prediction/control.

Avoid sending:

``` text
customer names
personal information
request payloads
authentication data
```

to the planning model.

For academic experiments, synthetic/anonymized workload traces are
preferable where possible.

------------------------------------------------------------------------

# 17. Denial-of-Service Protection

Potential resource-exhaustion behavior:

``` text
Repeated ScaleOut
     ↓
Too many containers
     ↓
Cluster resource exhaustion
```

Mitigate using:

-   maximum capacity;
-   rate limits;
-   cooldown;
-   resource quotas;
-   maximum action size;
-   emergency stop.

------------------------------------------------------------------------

# 18. Safe Fallback

``` mermaid
flowchart TD
    A[Normal Control] --> B{Component Healthy?}
    B -- Yes --> C[Normal Decision]
    B -- No --> D[Fallback]
    C --> E{Action Safe?}
    E -- Yes --> F[Execute]
    E -- No --> D
    D --> G[Conservative Reactive Policy]
    G --> F
```

The fallback should be bounded and auditable.

------------------------------------------------------------------------

# 19. Security Test Cases

  ID      Attack/Failure                Expected
  ------- ----------------------------- -------------------------
  SEC01   Invalid Qwen3 strategy        Reject
  SEC02   Arbitrary shell command       Reject
  SEC03   Capacity \> max               Reject
  SEC04   Capacity \< min               Reject
  SEC05   Prompt injection              No privilege escalation
  SEC06   Missing credential            Controlled failure
  SEC07   Unauthorized Kubernetes API   Denied
  SEC08   Runaway scaling               Rate/bounds stop it
  SEC09   Secret in logs                Must not appear
  SEC10   Compromised container         Restricted permissions
  SEC11   AI service failure            Safe fallback
  SEC12   Monitoring exposure           Access controlled

------------------------------------------------------------------------

# 20. Security Acceptance Criteria

The implementation should satisfy all of the following:

-   Qwen3 cannot directly execute arbitrary Kubernetes commands.
-   PPO cannot bypass action validation.
-   Capacity is bounded.
-   SLA guard is independent of the learned policy.
-   Kubernetes access follows least privilege.
-   Secrets are not hard-coded.
-   Invalid model output is rejected.
-   All infrastructure actions are auditable.
-   AI/service failure has a safe fallback.
-   Container privileges are minimized.

------------------------------------------------------------------------

# 21. Security Principle Summary

``` text
UNTRUSTED INPUT
      ↓
VALIDATE
      ↓
AI RECOMMENDATION
      ↓
VALIDATE AGAIN
      ↓
SLA + POLICY GUARD
      ↓
AUTHORIZATION
      ↓
RESTRICTED EXECUTION
      ↓
AUDIT + MONITOR
```

This structure keeps the intelligent components useful without allowing
them to become unrestricted infrastructure administrators.
