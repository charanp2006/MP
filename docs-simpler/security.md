# Security --- Predictive Container Management for Energy-Efficient Serverless Computing

## 1. Security Objective

AI components must never become an unrestricted path to Kubernetes.
Treat model output as **untrusted data until validated and authorized**.

## 2. Threats

-   Malformed/manipulated workload data.
-   Prompt injection through metadata.
-   Unsafe Qwen3 output.
-   Out-of-bound PPO action.
-   Unauthorized Kubernetes access.
-   Exposed credentials.
-   Compromised images.
-   Monitoring data exposure.
-   Denial of service through excessive scaling.
-   Runaway controller behavior.

## 3. Trust Boundaries

``` mermaid
flowchart LR
    A[Workload Data] --> B[Validation]
    B --> C[TFT]
    C --> D[Qwen3]
    D --> E[Schema + Policy Validation]
    E --> F[PPO]
    F --> G[Action Validation]
    G --> H[Restricted Executor]
    H --> I[Kubernetes/OpenFaaS]
```

## 4. Least Privilege

Qwen3 should not receive unrestricted Kubernetes credentials.

``` text
Qwen3
  ↓ recommendation
Orchestrator
  ↓ validated action
Restricted Executor
  ↓
Kubernetes/OpenFaaS
```

Use dedicated service accounts, RBAC and only required permissions.

## 5. Kubernetes Security

-   Dedicated service accounts.
-   RBAC.
-   Namespace isolation.
-   Resource quotas.
-   Network policies where appropriate.
-   Non-root containers where feasible.
-   Restricted capabilities.
-   Resource requests/limits.
-   No cluster-admin permission for the controller.

## 6. AI Input Security

-   Validate types and ranges.
-   Limit input size.
-   Avoid unnecessary free-form text.
-   Use structured fields.
-   Treat metadata as untrusted.
-   Never pass secrets to the model.

## 7. AI Output Security

Never implement:

``` text
Qwen3 → arbitrary shell/Kubernetes command
```

Instead use:

``` json
{
  "strategy": "prewarm",
  "desired_capacity_change": 3,
  "priority": "sla"
}
```

Then validate against a closed schema.

## 8. Action Allowlist

Only:

``` text
NoOp
PreWarm
ScaleOut
Reuse
ScaleIn
Terminate
```

Each action needs parameter bounds, timeout and authorization checks.

## 9. Resource Protection

Use explicit limits:

``` yaml
containers:
  min: 2
  max: 30
```

Also consider: - maximum change per cycle; - scaling cooldown; - rate
limits; - emergency stop; - conservative fallback.

## 10. Secrets

Do not hard-code API keys, Kubernetes tokens, passwords or cloud
credentials.

Use environment variables for development and Kubernetes
Secrets/appropriate secret management for deployment. Never log secret
values.

## 11. Network Security

Use TLS where appropriate, authentication for internal services,
restricted network paths, limited inbound/outbound access and no public
Kubernetes API exposure.

## 12. Container Security

-   Pin image versions.
-   Scan images/dependencies.
-   Prefer non-root.
-   Drop unnecessary capabilities.
-   Avoid privileged containers.
-   Apply CPU/memory limits.
-   Keep images updated.

## 13. Monitoring and Audit

Record:

``` text
timestamp
forecast
system_state
planner_output
ppo_action
validated_action
executor_result
SLA_status
```

Do not record credentials or unnecessary sensitive workload information.

## 14. Safe Failure

``` mermaid
flowchart TD
    A[Normal AI Control] --> B{AI Healthy?}
    B -- Yes --> C[Validate + Execute]
    B -- No --> D[Safe Fallback]
    D --> E[Conservative Capacity Policy]
    E --> F[Continue Monitoring]
```

The system should fail closed for unsafe commands, not fail open.

## 15. Prompt-Injection Mitigation

-   Keep system instructions separate from data.
-   Treat external text as data.
-   Use structured JSON.
-   Close the action space.
-   Validate outputs independently.
-   Do not allow the model to choose its own permissions.

## 16. Model/Artifact Integrity

Protect and version: - TFT checkpoints. - PPO policies. - Configuration
files. - Container images. - Evaluation scripts.

Use integrity/version checks so unauthorized replacement is detectable.

## 17. Privacy

Use minimum required workload information. Prefer anonymized/synthetic
traces for demonstrations and never send unnecessary customer/user
information to the AI model.

## 18. Security Tests

1.  Invalid planner output.
2.  Action injection.
3.  Capacity overflow.
4.  Unauthorized Kubernetes request.
5.  Malformed metadata.
6.  Prompt-injection strings.
7.  Credential exposure.
8.  Container privilege checks.
9.  Image vulnerability checks.
10. Network access checks.
11. Secret leakage in logs.
12. Runaway scaling.

## 19. Security Acceptance Criteria

-   Qwen3 cannot execute arbitrary Kubernetes commands.
-   PPO actions are allowlisted.
-   Action parameters are bounded.
-   Kubernetes follows least privilege.
-   Secrets are not hard-coded.
-   Invalid outputs are rejected.
-   Scaling has explicit limits.
-   Actions are auditable.
-   Safe fallback exists.

## 20. Security Principle

``` text
AI proposes
   ↓
Policy validates
   ↓
Authorization checks
   ↓
Restricted executor acts
   ↓
Monitoring records
```
