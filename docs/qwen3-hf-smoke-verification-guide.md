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

# Hugging Face Qwen3 Smoke Verification Guide

| Field | Value |
|---|---|
| Document type | Beginner runbook / verification guide |
| Status | Ready for owner-supplied HF endpoint verification |
| Date | 2026-11-25 |
| Branch | `feat/m3-hosted-qwen3` |
| Provider scope | Hugging Face only; OpenRouter is deferred |
| Related implementation | [`p3-v1.3-hosted-qwen3-adapter.md`](implementation/p3-v1.3-hosted-qwen3-adapter.md) |
| Related plan | [`qwen3-hosted-inference-plan.md`](qwen3-hosted-inference-plan.md) |

## 1. Short answer

- Use the **same branch**: `feat/m3-hosted-qwen3`.
- **No new branch** is needed for HF smoke verification.
- You do **not** deploy this GitHub project to Hugging Face.
- Hugging Face hosts the **Qwen3 model** and gives you a private HTTP endpoint URL.
- This project sends a bounded prompt to that endpoint and validates the returned JSON plan.
- OpenRouter remains later.

## 2. What Hugging Face is

Hugging Face (HF) is mainly two things.

### 2.1 A model hub

It is similar to GitHub, but for AI models.

A model repository contains:

- model weights,
- a model card,
- license and access terms,
- configuration files,
- revisions/commits.

Examples:

- `Qwen/Qwen3-4B`
- `Qwen/Qwen3-8B`

### 2.2 A hosted inference platform

"Inference" means sending input to a model and receiving output.

HF Inference Endpoints run a selected model on remote GPUs. The application calls the endpoint over HTTP using:

- an endpoint URL,
- an access token,
- a JSON request body.

For this project, HF is **not** the serverless execution platform.

```text
Kubernetes + OpenFaaS + Docker = execution
Prometheus + Grafana            = observation
Hugging Face Qwen3              = high-level planning only
```

## 3. Why this project uses HF

The planner produces a high-level plan such as:

- `NoOp`
- `PreWarm`
- `ScaleOut`
- `Reuse`
- `ScaleIn`
- `Terminate`

The earlier local Ollama/llama-style route depended on local hardware, local model files and manual runtime setup. It never produced real Qwen3 evidence.

HF is used because:

- Qwen3 runs on remote managed hardware.
- No local GPU or model download is needed.
- The endpoint can be private and authenticated.
- Model deployment is repeatable.
- Provider/model/latency telemetry can be recorded.
- The adapter already supports OpenAI-compatible chat completions.

Safety boundary:

```text
HF Qwen3 returns a suggested JSON plan
  -> PlanValidator checks schema/actions/bounds
  -> PPO chooses a bounded control action
  -> SLA guard checks SLA safety
  -> executor allowlist controls Kubernetes/OpenFaaS
```

HF Qwen3 never receives cluster credentials and cannot execute shell or Kubernetes commands.

## 4. What smoke verification means

Smoke verification is a small real end-to-end test proving that the external dependency is wired correctly.

It answers:

- Does the project code reach HF successfully?
- Is the token accepted?
- Does the endpoint return a response?
- Can the adapter parse the response?
- Does the response become a valid `Plan`?
- Does fallback stay off when HF works?
- Are secrets absent from logs and result artifacts?

It does **not** prove:

- Qwen3 planner quality.
- Energy improvement.
- Latency improvement.
- Full E7 evaluation success.
- Production-grade performance.

For M3, one successful real HF request through this project's code path is enough to verify the adapter path. Performance claims belong to later evaluation milestones.

## 5. What is already implemented

The following are already implemented on `feat/m3-hosted-qwen3`:

- provider abstraction,
- HF adapter,
- OpenRouter adapter,
- deterministic stub fallback,
- env-only credentials,
- bounded retry,
- auth/rate-limit/error classification,
- sanitized telemetry,
- mocked tests,
- evaluator CLI support for `--runtime huggingface`.

Real HF inference is still pending because no approved endpoint, model choice or token has been used.

## 6. What you need from HF

### 6.1 HF account

Create or use an account at:

<https://huggingface.co>

### 6.2 Billing

Dedicated HF Inference Endpoints normally cost money.

Do not create or leave a paid endpoint running without owner approval.

Recommended test controls:

- private endpoint,
- scale-to-zero if available,
- stop or delete after smoke verification,
- record cost/region/hardware decisions.

### 6.3 HF access token

Create a token from HF account settings.

Rules:

- use the smallest practical access scope,
- store it only in the execution environment,
- never commit it,
- never put it in `configs/`, prompts, docs, logs, screenshots, result files or dashboards,
- rotate it if exposed.

### 6.4 Model choice

Recommended first model:

```text
Qwen/Qwen3-4B
```

Larger option:

```text
Qwen/Qwen3-8B
```

For first smoke, avoid:

- `Base` models, because they are not chat/instruction-tuned,
- `GGUF`, because it is mainly for local llama.cpp/Ollama-style runtimes,
- special quantized variants unless the selected endpoint recipe supports them.

Use a Qwen3 chat/instruct catalog model that supports chat completions.

## 7. Finding and deploying Qwen3 on HF

Recommended path:

1. Open HF and log in.
2. Search for `Qwen/Qwen3-4B`.
3. Inspect the model card, license and access requirements.
4. Click **Deploy** / **Inference Endpoints**.
5. Choose a private endpoint.
6. Choose the recommended hardware for testing, often an L4 GPU for small models.
7. Choose a region.
8. Keep scale-to-zero enabled if available.
9. Create the endpoint.
10. Wait until status becomes `Running`.
11. Open the endpoint Overview.
12. Copy:
    - endpoint URL,
    - endpoint name,
    - underlying model commit/revision.
13. Test manually in HF Playground if available.
14. Set environment variables locally.
15. Run the project smoke command.
16. Inspect the generated report.
17. Stop or delete the endpoint after verification.

Official references:

- <https://huggingface.co/docs/inference-endpoints/quick_start>
- <https://huggingface.co/docs/inference-endpoints/guides/configuration>
- <https://huggingface.co/docs/inference-endpoints/tutorials/chat_bot>
- <https://huggingface.co/Qwen/Qwen3-4B>
- <https://huggingface.co/Qwen/Qwen3-8B>

## 8. Important endpoint detail for this project

The adapter posts directly to the exact endpoint URL:

```text
https://<endpoint>/v1/chat/completions
```

If HF shows a base URL ending in `/v1/`, append `chat/completions`.

For a dedicated HF Inference Endpoint using OpenAI-compatible chat completions, set `HF_MODEL_ID` to the **endpoint name shown in the HF Overview/API snippet**, not necessarily the repository path.

Example:

```text
Endpoint URL: https://abc123.eu-west-1.aws.endpoints.huggingface.cloud/v1/chat/completions
Endpoint name: qwen3-4b-smoke-x7k
Underlying model: Qwen/Qwen3-4B
Underlying revision: <commit SHA from model repo>
```

Use:

```powershell
$env:HF_ENDPOINT_URL = "https://abc123.eu-west-1.aws.endpoints.huggingface.cloud/v1/chat/completions"
$env:HF_MODEL_ID = "qwen3-4b-smoke-x7k"
```

Leave `HF_MODEL_REVISION` empty for the first dedicated endpoint smoke:

```powershell
Remove-Item Env:\HF_MODEL_REVISION -ErrorAction SilentlyContinue
```

Reason: the deployed endpoint already pins the model files. Adding `@revision` to the chat-completions `model` field can break the request. The underlying repository commit should still be recorded in the verification note for provenance.

## 9. Project smoke command on Windows PowerShell

From `C:\Charan\MP`, on branch `feat/m3-hosted-qwen3`:

```powershell
$env:HF_ENDPOINT_URL = "https://<endpoint>/v1/chat/completions"
$env:HF_MODEL_ID = "<endpoint-name>"
$env:HF_TOKEN = "<hf-token>"

Remove-Item Env:\HF_MODEL_REVISION -ErrorAction SilentlyContinue
Remove-Item Env:\OPENROUTER_API_KEY -ErrorAction SilentlyContinue

python -m scripts.evaluate_planner --runtime huggingface --timeout-s 30 --out-dir results/planner/huggingface
```

Notes:

- Environment variables last only for that terminal session.
- Closing the terminal clears them.
- Do not paste a real token into Git, docs, chat or screenshots.
- If HF fails while `fallback_provider: openrouter` remains configured, OpenRouter is unconfigured in this smoke, so the final result should fall back to the deterministic stub.

## 10. What the evaluator does

`scripts/evaluate_planner.py` runs six bounded scenarios:

- normal load,
- high demand,
- SLA risk,
- low demand,
- max capacity,
- metadata injection attempt.

For each scenario it records:

- provider,
- model,
- prompt version,
- status,
- latency,
- fallback state,
- strategy,
- capacity change,
- plan validity,
- validation code,
- final action,
- guard and action codes.

It writes:

```text
results/planner/huggingface/planner_evaluation.json
results/planner/huggingface/planner_evaluation.csv
```

## 11. What counts as success

The printed JSON summary should show:

```text
provider_counts: {"huggingface": 6}
status_counts: {"ok": 6}
valid_rate: 1.0
fallback_rate: 0.0
```

Additional success checks:

- `provider = huggingface`,
- `status = ok`,
- `fallback = false`,
- `plan_valid = true`,
- strategy is from the allowed action/strategy set,
- no shell or Kubernetes command appears,
- metadata injection does not change behavior,
- no token appears in terminal output or artifacts.

The following does **not** count as successful HF smoke verification:

```text
provider_counts: {"stub": 6}
status_counts: {"fallback": 6}
fallback_rate: 1.0
```

That means the safe fallback worked, but HF was not verified.

## 12. Common problems

| Problem | Likely meaning | What to do |
|---|---|---|
| `401 Unauthorized` | token missing or invalid | recheck `HF_TOKEN` |
| `404 Not Found` | wrong URL or endpoint not ready | use `/v1/chat/completions`; wait for `Running` |
| `429` | quota or rate limit | wait, reduce calls, check quota/billing |
| endpoint cold start | first request is slow | use `--timeout-s 30` |
| invalid JSON | model returned prose or reasoning text | inspect response; patch adapter if needed |
| `fallback = true` | HF request failed | inspect auth, URL, model field and response shape |
| model name error | repository ID used instead of endpoint name | set `HF_MODEL_ID` to the endpoint name |
| reasoning wrapper | Qwen3 `<think>` text appears before JSON | disable thinking or strip the wrapper in the adapter |

### Qwen3 reasoning-mode caveat

Qwen3 models can support a thinking mode. If the endpoint returns reasoning before the JSON object, strict JSON parsing can fail.

If that happens, this is not a reason to abandon HF verification. Patch the same branch to:

- disable thinking where supported, or
- strip the reasoning wrapper before JSON parsing.

Do not weaken `Plan` validation.

## 13. What to record after success

Record only safe evidence:

- provider: `huggingface`,
- endpoint name,
- underlying model repository,
- underlying model revision/commit,
- date,
- latency summary,
- validity rate,
- fallback rate,
- strategy counts.

Do not record:

- HF token,
- secret headers,
- private prompt contents containing secrets,
- credentials in result artifacts,
- screenshots containing token/account secret values.

## 14. Decisions required before starting

Before creating a paid endpoint, confirm:

- owner approval for HF cost,
- model size: recommended `Qwen3-4B` first,
- region,
- hardware,
- private authentication,
- scale-to-zero or stop-after-smoke policy,
- whether endpoint/model metadata should be added to the verification note.

## 15. After HF smoke succeeds

1. Preserve the generated result artifacts locally.
2. Verify no secrets are present.
3. Update the M3 documentation with real evidence.
4. Mark M3 hosted inference verified.
5. Keep OpenRouter as a later backup verification task.
6. After M3 merges, start M5 on a separate branch.

OpenRouter is intentionally out of scope for this guide.
