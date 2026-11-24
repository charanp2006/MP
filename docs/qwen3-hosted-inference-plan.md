# Qwen3 Hosted Inference Plan — Hugging Face Primary, OpenRouter Backup

| Field | Value |
|---|---|
| Document status | Plan / runbook; no implementation performed in this pass |
| Date | 2026-11-24 |
| Related v2 milestone | M3 — Hosted Qwen3 on Hugging Face |
| Owner decision | Replace the local/Ollama-first approach with hosted Qwen3 inference |

## 1. Decision

The Qwen3 planner must not require a model process on the user's laptop.

- **Primary provider:** Hugging Face-hosted Qwen3 inference endpoint.
- **Backup provider:** OpenRouter API using an owner-supplied API key.
- **Final fallback:** deterministic stub/NoOp planner through the existing `FallbackPlanner` behavior.

This is a documentation update only. Current code still implements `stub` and the historical local `ollama` adapter. The HF and OpenRouter adapters are future M3 work and must not be marked complete until real inference is verified.

## 1.1 Why the local llama plan was replaced

The original plan used a local model runtime: Ollama serving Qwen3, with
llama.cpp/GGUF listed as a possible local alternative. That local llama-style
path is now **outdated for this project** and is no longer the planned primary
real-inference route.

It was initially chosen because it was offline, cheap and reproducible for
early integration tests. In practice it introduced several blockers:

- inference depended on a model process and suitable hardware on the owner's laptop;
- model tags, quantization and runtime versions had to be synchronized manually;
- no successful real Qwen3 inference was ever recorded through that path;
- local runtime failures produced fallback-only evidence, not planner-quality evidence;
- managed endpoints give a pinned model/revision, predictable availability, usage telemetry and a cleaner secret-managed request path.

The V2 owner decision therefore replaces the local llama/Ollama-first approach
with Hugging Face-hosted Qwen3 as primary. OpenRouter is added as a backup so
a missing or broken HF endpoint does not block a crucial run. Historical
Ollama/llama.cpp code and records remain only for compatibility and audit;
they are not the current implementation direction.

## 2. Provider chain

```text
validated planner request
  -> Hugging Face endpoint (primary, pinned model/revision)
  -> on timeout / quota / auth / endpoint failure / invalid output:
       OpenRouter endpoint (backup, pinned model slug)
  -> on failure / invalid output:
       deterministic stub -> NoOp if needed
```

Rules:

- All providers go through the same provider interface and output the same strict `Plan` schema.
- The LLM remains advisory. It never receives cluster credentials and cannot emit shell/Kubernetes commands.
- Output is parsed as JSON, schema-validated, bounded by `PlanValidator`, and reconciled with PPO and the SLA guard.
- Timeouts, bounded retries, rate-limit handling and redacted error logs are mandatory.
- Do not log prompts containing secrets or unnecessary workload metadata.
- Record provider, model/revision, latency, status, validation result, fallback reason and sanitized output.

## 3. Hugging Face primary path

Before implementation:

1. Verify that a suitable Qwen3 model is supported by the selected HF inference product.
2. Verify license, cost, quota, latency and data-handling terms.
3. Obtain explicit owner approval before provisioning any paid endpoint.
4. Pin the exact model ID/revision and endpoint URL in versioned configuration.
5. Store the HF token in environment variables or a secret manager; never in Git, prompts, logs, or result artifacts.

Proposed configuration keys for M3 (not yet implemented):

```yaml
agent:
  provider: huggingface        # stub | huggingface | openrouter (future)
  fallback_provider: openrouter
  huggingface:
    endpoint_url: ${HF_ENDPOINT_URL}
    model_id: <verified-qwen3-model-id>
    revision: <verified-revision>
    timeout_s: 20
    max_retries: 2
  openrouter:
    model: <verified-openrouter-qwen3-slug>
    timeout_s: 20
    max_retries: 2
```

Secrets:

```bash
export HF_TOKEN="<secret>"
export HF_ENDPOINT_URL="<private-endpoint-url>"
```

PowerShell:

```powershell
$env:HF_TOKEN = "<secret>"
$env:HF_ENDPOINT_URL = "<private-endpoint-url>"
```

## 4. OpenRouter backup path

OpenRouter is the emergency backup if Hugging Face is temporarily unavailable, rate-limited, or breaks during a crucial run.

Owner setup:

1. Create an OpenRouter API key outside the repository.
2. Verify the exact Qwen3 model slug currently offered by OpenRouter.
3. Set the key in the execution environment only when the backup is needed.
4. Run the planned smoke/evaluation command against the `openrouter` provider.
5. Unset the key when finished.

Example runbook after M3 implementation:

```bash
export OPENROUTER_API_KEY="<secret>"
export OPENROUTER_MODEL="<verified-qwen3-slug>"

python -m scripts.evaluate_planner \
  --runtime openrouter \
  --timeout-s 20 \
  --out-dir results/planner/openrouter
```

PowerShell:

```powershell
$env:OPENROUTER_API_KEY = "<secret>"
$env:OPENROUTER_MODEL = "<verified-qwen3-slug>"
py -m scripts.evaluate_planner --runtime openrouter --timeout-s 20 --out-dir results/planner/openrouter
```

Security notes:

- Never place `OPENROUTER_API_KEY` in `configs/`, `results/`, prompts, notebook outputs, CI logs, or dashboards.
- Redact authorization headers and error bodies.
- Use a dedicated secret with minimal scope and rotate it if exposed.
- Provider choice must be logged by name, not by key value.

## 5. Required M3 implementation work

- Add provider abstraction for `huggingface` and `openrouter` while preserving `stub`/historical Ollama compatibility for tests.
- Use environment/secret-managed credentials only.
- Implement structured request/response with strict JSON parsing and `extra="forbid"` validation.
- Implement timeout, bounded retry, rate-limit classification, auth failure classification, and fallback to the next provider.
- Log sanitized telemetry: provider, model/revision, latency, status, validation, fallback reason, token usage if available.
- Add tests with mocked HTTP responses for success, timeout, rate limit, malformed JSON, invalid plan, auth failure and provider chain fallback.
- Add a separate real-inference verification command for owner-supplied credentials; do not run it automatically in CI.
- Evaluate a fixed scenario suite: schema validity, constraint violations, latency, consistency across repeated calls, and fallback rate.
- Avoid hidden chain-of-thought; request a concise rationale/evidence field only.

## 6. Acceptance criteria

M3 is complete only when:

- A real Qwen3 request succeeds through the project's code path using the primary HF endpoint, or an owner-approved equivalent hosted endpoint.
- OpenRouter backup is exercised with mocks in CI and optionally with an owner-supplied key for real smoke verification.
- Invalid, timeout, rate-limited and unavailable-provider cases fall back safely.
- No secrets appear in source, logs, config, result artifacts, or dashboards.
- Planner output cannot bypass validation, PPO, the safety shield, or the executor allowlist.
- A planner evaluation report records model/revision/provider, latency, validity and fallback rates.

## 7. Cost and availability

Hosted inference introduces external cost, quota, privacy and availability dependencies. Do not provision paid HF resources without approval. Do not leave an OpenRouter key configured unnecessarily. The deterministic stub fallback must always keep the research loop safe and runnable when external providers fail.
