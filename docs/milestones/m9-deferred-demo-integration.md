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

# M9 — Deferred Demonstration Integration

- **Phase:** M9
- **Doc version:** v1.0
- **Status:** Complete for simulated end-to-end demonstration integration; live deployment and final deck integration deferred
- **Date:** 2026-11-20
- **Related commit:** `0b7cb69` (base, uncommitted)
- **Test IDs:** T09-01 to T09-04
- **Architecture layers touched:** workload ingestion, control loop, execution/audit scaffolding, observability, demonstration packaging

## Objective

Provide a reproducible demonstration path for the deferred M9 components: a
clearly synthetic client, a generic and validated ingestion contract, several
small sample service definitions, and an end-to-end runner that produces
auditable artifacts without claiming live infrastructure validation.

## Module map

| Area | Files | Purpose |
|---|---|---|
| Synthetic client | `demo/synthetic_client.py` | Deterministic request-level events with service IDs, payload classes, bursts, timings, and no user identities |
| Generic ingestion | `data/generic_adapter.py`, `demo/ingestion_schema.json` (generated) | Validate untrusted records, optional token auth, aggregate to fixed-window traces |
| Sample services | `demo/services/app.py`, `demo/services/Dockerfile`, `demo/services/docker-compose.yml`, `demo/service_registry.json` | Three small service definitions for checkout/search/recommend; scaffolding only |
| Demo runner | `demo/run_end_to_end.py` | Generate -> ingest -> feature -> forecast/plan/control -> audit/feedback/alert -> report |
| Config | `configs/project.yaml` | `demo.*` defaults for scenario, steps, rate, seed, auth, and payload classes |
| Tests | `tests/test_m9_demo.py` | Client determinism/privacy, adapter validation/auth, artifact generation |

## Design and data contracts

- Event schema version: `m9-event-v1`.
- Required event fields: `timestamp`, `service_id`, `function_id`, `invocation_count`.
- Optional fields: `request_id`, `payload_class`, `execution_duration_ms`, `error_count`, `source`, `scenario`.
- Privacy rule: no user identity, request payload, or authentication data in persisted artifacts.
- Authentication: `demo.require_ingest_auth` can require a token from `demo.ingest_token_env`; the token is checked in memory and never written to artifacts.
- Aggregation: request events are floored to `demo.interval_s` windows and grouped by `function_id`; invocation/error counts are summed and resource/latency fields are simulated proxies.
- Warmup: `forecast.history_window`, feature lags, and rolling windows are honored before the control-loop replay so feature engineering does not consume the demo steps.
- Control: `execute=false`, executor is `simulator`, planner is `stub_proxy`, forecast defaults to persistence unless TFT is explicitly requested and available.
- Sample services are local container scaffolding only; no images were built, no compose stack was started, and no routes received live traffic.

## How to run and verify

```bash
py -m demo.run_end_to_end --out-dir results/demo/m9 --steps 4 --scenario mixed --seed 42
py -m pytest tests/test_m9_demo.py -ra
py -m pytest -ra
git diff --check
```

Optional local scaffolding command (not executed for this milestone):

```bash
docker compose -f demo/services/docker-compose.yml up --build
```

## Test coverage

- **T09-01:** synthetic client determinism, event-level output, allowed service IDs, and absence of identity/payload fields.
- **T09-02:** generic adapter validation and fixed-window trace aggregation.
- **T09-03:** token auth enforced from environment without persisting token data.
- **T09-04:** end-to-end runner writes manifest, schema, events, trace, routing, decisions, feedback, alerts, report, and figure.

Verification results:

- Focused M9 tests: `4 passed`.
- Full suite: `158 passed, 1 warning`.
- `git diff --check`: clean.
- CLI smoke: `2100` synthetic events over `35` generated windows, replayed for `4` control steps with seed `42`.

## Smoke artifacts

Generated under ignored `results/demo/m9/`:

- `run_manifest.json`, `report.md`, `ingestion_schema.json`
- `events.jsonl`, `trace.csv`, `routing.csv`
- `decision.jsonl`, `decision_records.jsonl`, `audit.jsonl`, `feedback.jsonl`, `alerts.jsonl`
- `figures/demo_timeline.png`

The smoke report contains a Mermaid control-flow diagram, simulated control summary, service routing table, and an eight-slide presentation storyboard.

## Measured vs simulated vs unimplemented

- **Simulated:** all requests, service traffic, resource proxies, latency, energy, capacity, decisions, audit, alert, and feedback values.
- **Stubbed:** Qwen3 planner is a stub proxy; TFT was not requested in the smoke run.
- **Unimplemented/deferred:** live Docker/OpenFaaS/Kubernetes deployment, live request routing, live Prometheus/Grafana scraping, final PPTX editing, and measured production performance.

## Limitations and next steps

- The generic adapter is a local validated SDK-style interface, not a deployed authenticated HTTP endpoint.
- Sample services share one parametrized image; they are demonstration scaffolding, not application implementations.
- The final PPTX and image assets remain archive material on the `files` branch and were not edited.
- Next: if requested, validate live container actions and scraping on a local stack; otherwise this milestone closes the deferred demonstration integration track.
