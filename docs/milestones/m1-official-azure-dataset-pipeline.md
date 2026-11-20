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

# Milestone 1 — Official Azure Dataset Pipeline

| Field | Value |
|---|---|
| Milestone | M1 — Official Azure dataset acquisition and preparation |
| Status | **Complete (official archive acquired, verified, extracted, prepared, visualized)** |
| Date started | 2026-11-19 |
| Date completed | 2026-11-20 |
| Branch | `feat/m2-azure-dataset-pipeline` (merged) |
| Base commit | `1e58fde7555914655d3ec089fe74274b8d824a95` |
| Merge commit | `b7ccce5f21249ea359775de625bac2cf53b5c6ea` |
| Feature commit | `3939243 feat(m2) official-azure-dataset-pipeline: Reproducible acquisition and preparation` |
| Scope | Official source inspection, verified archive download, safe extraction, chunked `total` aggregation, cleaning, chronological split, manifest, prepared CSV, plots, and CLI timeout. **No model training or live deployment.** |
| Test IDs | U01-U12, D01-D04 (dataset smoke/official-prep); T01-T04/Q01-Q06/R01-R06/I01-I06/S01-S06/F01-F06 not run in this milestone |

## Changelog

| Version | Date | Change |
|---|---|---|
| v0.1 | 2026-11-19 | Created M1 report; recorded official AzurePublicDataset inspection, licensing, candidate trace comparison, selected trace, and initial pipeline design/acceptance mapping. |
| v0.2 | 2026-11-19 | Added fixture-verified scaffold and ingestion integration. |
| v0.3 | 2026-11-19 | Added `obtain` CLI and local synthetic end-to-end validation. |
| v1.0 | 2026-11-20 | Completed official 14-day acquisition/verification/preparation/visualization; added chunked wide aggregation, selective extraction, `--timeout-s` watchdog, and final commands/results. |
| v1.1 | 2026-11-20 | Corrected status to merged after PR #7; recorded merge/feature commits. |
| v1.2 | 2026-11-20 | Renumbered from M2 to M1 to follow `IMPLEMENTATION_PLAN.md`. |

## 1. Official source inspection (verified 2026-11-19)

- **Repository:** https://github.com/Azure/AzurePublicDataset (Microsoft/Azure)
- **Default branch:** `master`
- **Repo metadata (GitHub API, inspected 2026-11-19):** created 2017-08-18, updated 2026-11-19, pushed 2026-11-17, ~1.2k stars, license reported as **CC-BY-4.0** (`LICENSE` contains Creative Commons Attribution 4.0 International text). `LICENSE-CODE` also present in repo.
- **Data hosting:** README states trace files are hosted as assets on GitHub Releases: https://github.com/Azure/AzurePublicDataset/releases (each dataset doc lists specific download links). Prior Azure Blob URLs redirect per README.
- **Contact:** `azurepublicdataset@service.microsoft.com` (per README/docs).
- **Usage/attribution:** dataset docs require/advise CC-BY attribution and citation of the associated paper(s) (e.g. 2019 Functions: Shahrad et al., ATC 2020 “Serverless in the Wild…”). We must record source URL, retrieval date, commit/tag if available, license, hashes, and citation in manifests/docs.

## 2. Candidate traces considered (serverless-relevant)

| Trace | Period / content | Schema (high level) | Download (per docs) | Fit for this project |
|---|---|---|---|---|
| **AzureFunctionsDataset2019** (ATC 2020) | Subset of Azure Functions workload, July 2019; 14 days. Random sample per application (rate small/unspecified); distributions representative per authors’ notebook. | Invocations: 14 CSVs `invocations_per_function_md.anon.d01-d14.csv` with `HashOwner, HashApp, HashFunction, Trigger, 1..1440` = invocation counts per minute over 24h (recorded after execution). Durations: percentiles/avg/min/max/count per 24h (no cold-start time). Memory: app-level allocated memory percentiles (d01-d12). | Release asset: `https://github.com/Azure/AzurePublicDataset/releases/download/dataset-functions-2019/azurefunctions_dataset2019_azurefunctions-dataset2019.tar.xz` (tar.xz containing CSVs) | **Best fit** for invocation-count/rate workload time series forecasting (1-min bins, multi-function/app, 14-day span) with clear semantics aligned to `invocation_count` target and existing pipeline concepts. |
| **AzureFunctionsInvocationTrace2021** (SOSP 2021) | 2 weeks starting 2021-01-31; per-invocation events. | `app, func, end_timestamp (s), duration (s)`; timestamps modified from production trace. | Doc references `AzureFunctionsInvocationTraceForTwoWeeksJan2021.rar` (path in repo data/raw in doc link); release-asset location to be confirmed during implementation (inspect releases/assets before download). | Viable (can aggregate to interval invocation counts/durations) but requires event aggregation and has different semantics; less directly comparable to 1-min count series. Consider as secondary/alternative. |
| **AzureFunctionsBlobDataset2020** | Blob accesses Nov–Dec 2020 | Access-level traces | Release assets per doc | Not a function-invocation workload series; out of scope for workload forecasting target. |

## 3. Selected trace (initial, for M1 implementation)

**Selected:** `AzureFunctionsDataset2019` — **invocations** component as the primary workload series for forecasting.

**Justification:**
- Directly provides **invocation counts per minute** per (anonymized) function/app, suitable to derive `invocation_count` / invocation rate at configurable aggregation intervals (default experiment interval configurable, e.g. 1–5 min) with chronological ordering.
- 14 consecutive days enable chronological train/validation/test splits and leakage-free evaluation.
- Includes trigger labels (grouped: http/timer/event/queue/storage/orchestration/others) and app/owner hashes useful for grouping/stratification (without deanonymization).
- Official, documented, CC-BY 4.0, citable, and widely used in serverless workload research.

**Documented limitations / assumptions (must be carried into code, manifests, and reports):**
- **Anonymized & sampled:** IDs are HMAC-SHA256 hashed with secret salts (different per column); sampling rate small and unspecified (per-application) though distributions reported representative.
- **Workload semantics:** values are **invocation counts per minute per function** (recorded after execution), not request arrival rate at sub-minute resolution and not concurrent executions.
- **Not provided by source:** no real per-interval CPU utilization, memory utilization time series, P95/request latency, cold-start counts, container counts, power, or energy. **These must not be fabricated.** Any derived concurrency/latency/resource/energy values used in simulation or control experiments must be **clearly labeled as simulated/estimated proxies** with assumptions documented (and separated from historical trace facts).
- **Memory/duration files:** app-level memory distributions (d01-d12) and function duration percentiles (per 24h) are distributions/aggregates, not aligned per-minute runtime telemetry; usable only with explicit, labeled estimation assumptions if at all.
- **Time:** 14 files correspond to 24h periods d01-d14 in July 2019 (relative days in dataset); absolute wall-clock timezone not specified as local — treat as sequential 1-min slots per day/file and document ordering assumptions.
- **Missing/edge cases:** docs note possible count discrepancies between invocation and duration logs, missing min/max in some duration rows, and memory pct0 issues in that dataset; parsing must be robust and gaps/duplicates/invalids validated.
- **Size:** tar.xz is multi-file compressed archive (expected large relative to repo); **do not commit raw data**. Download must be resumable/configurable and verifiable (hash/size recorded in manifest).

## 4. Pipeline design (planned, reproducible)

Target separable steps (CLI/commands), compatible with existing `data/` modules and config:

1. **inspect** — list official source, selected dataset, files/schemas/metadata, expected URLs, sizes/date ranges (from docs/releases metadata where available) without downloading full data.
2. **download** — configurable/resumable retrieval of selected release asset(s) or user-supplied archive; no blind full download required for tests; record URL, retrieval date, HTTP/etag info when available.
3. **verify** — compute/record SHA-256 and file size; verify integrity; record license/attribution/citation and source commit/ref context in manifest.
4. **extract/parse** — unpack tar.xz (or read provided extracted CSVs), validate schema (`HashOwner,HashApp,HashFunction,Trigger,1..1440`), handle encoding/NA, enforce integer/non-negative counts.
5. **aggregate** — reshape wide minute columns to long time series per function (and/or per app/group); map day index d01-d14 + minute offset to ordered timestamps/step index; aggregate to configurable interval (default documented/justified; keep 1-min native supported).
6. **clean** — duplicate handling, missing intervals/gaps, invalid values, timestamp ordering, timezone/ordering assumptions documented.
7. **features** — calendar/context features as applicable (day index, minute/hour-of-day, periodic features) and lag/rolling stats; **no future leakage**; normalization fit on train only.
8. **split** — chronological train/validation/test (never random for time series), boundaries recorded.
9. **export** — cleaned/aggregated/feat

## 11. Implementation progress (v0.2, 2026-11-19)

**Completed (scaffolding, no large download, no model training):**
- Implemented `data/azure_functions_2019.py` with official-source metadata and reproducible utilities: `inspect`, `download` (resumable), `verify` (SHA-256/size), archive-safe extraction, invocation CSV discovery/schema validation, wide->long reshape, configurable interval aggregation (multiple of 60s), cleaning (invalid/negative/duplicate handling, monotonic checks, function×time coverage/missingness report), chronological time-based split labeling, manifest build/write, prepared CSV export/load helpers, and a CLI (`python -m data.azure_functions_2019 {inspect,verify,download,prepare}`).
- **Official 2019 release verified from GitHub API (2026-11-19):** `dataset-functions-2019` asset `azurefunctions_dataset2019_azurefunctions-dataset2019.tar.xz`, size `142968140` bytes, SHA-256 `aff8b3ca7240a41a109e4ee598e0a96e45fcb92e7b8395ac19cb3748cd260d89`.
- Wired config: `configs/project.yaml` `data.source` now documents `sample|file|azure_functions_2019` and adds `data.azure.*` defaults (paths/glob/manifest, optional `function_limit`, `simulate_resources:false`). `data/ingestion.py` supports loading a prepared Azure CSV via `load_prepared_as_trace` (optional deterministic **simulated/estimated** resource proxies only when explicitly requested; not in trace).
- Added tiny schema-compatible CI fixtures (no full dataset): `tests/fixtures/azure_functions_2019_invocations_d01_sample.csv`, `d02_sample.csv` (3 functions × 1440 minutes × 2 days). Updated `.gitignore` to allow `tests/fixtures/*.csv` while keeping dataset CSVs ignored.
- Added `tests/test_azure_dataset.py` covering inspect metadata, schema/parse/reshape counts & timestamps, duplicate resolution, invalid/negative rejection, chronological split (no overlap/order), manifest+CSV export fields, and ingestion compatibility.
- Generated example prepared outputs from fixtures (local, gitignored): `data/processed/azure_fixture_prepared.csv`, `data/processed/azure_fixture_manifest.json`.

**Commands run:**
```text
py -m py_compile data/azure_functions_2019.py data/ingestion.py tests/test_azure_dataset.py
py -m pytest -q tests/test_azure_dataset.py                     # 8 passed
py -m pytest -q                                                 # 111 passed, 1 warning
py -m data.azure_functions_2019 inspect
py -m data.azure_functions_2019 prepare --inputs tests/fixtures/azure_functions_2019_invocations_d01_sample.csv tests/fixtures/azure_functions_2019_invocations_d02_sample.csv --out data/processed/azure_fixture_prepared.csv --manifest data/processed/azure_fixture_manifest.json
```

**Not yet done (M1 acceptance still open):**
- No full official archive downloaded/extracted/verified on this machine (intentional); `download/verify/prepare` against the real 14-day asset not executed end-to-end here.
- Dataset not visualized/reviewed (coverage/missingness/distribution/daily patterns/peaks/split plots) for the official trace.
- End-to-end "one command obtains/prepares selected official trace" from remote source not demonstrated in this environment (networked download of ~143 MB not run).
- Feature-level leakage tests against full training feature generation for Azure-prepared data and explicit interval/timezone edge-case validation on the full trace remain to be exercised.
- No official Azure raw/processed data committed (by design).

**Measured vs simulated vs estimated:** implementation/tests measured on local fixtures/smoke runs only. No real Azure trace metrics, no model training, no live cluster/Prometheus data.


## 12. Implementation progress (v0.3, 2026-11-19, branch `feat/m2-azure-dataset-pipeline`)

**Branch:** continued on `feat/m2-azure-dataset-pipeline` (created from `dev`/`1e58fde`, which already contains M0/M1 scaffold commit `3e6dce5`; additional M1 changes were later merged).

**Completed this update:**
- Added `obtain_official(...)` and CLI `obtain` to `data/azure_functions_2019.py`: one-command flow to **download (resumable) or reuse existing archive, verify SHA-256/size, extract safely (if needed), discover/parse/aggregate/clean/split, and export prepared CSV + manifest** with verification/extraction metadata. Supports `--days`, `--dest/--source-dir/--out/--manifest`, `--no-split`, `--force-download`.
- Added configurable aggregation modes in preparation (`data.azure.aggregate`: `per_function` default, `total`, `by_app`, `top_k_total` with `top_k`) and recorded `aggregation_detail` in manifest (useful because full 14-day per-function expansion can be very large).
- Fixed `_day_index_from_name`/parse flexibility to accept fixture-style `*_dNN_*` names while preserving official `...dNN.csv` handling.

**Validation (no network download of official data, no model training):**
- `py -m pytest -q tests/test_azure_dataset.py` → **8 passed**.
- `py -m pytest -q` → **111 passed, 1 warning** (pre-existing ingestion format warning).
- Local "official-like" end-to-end validation (no network): built a `.tar.xz` from schema-compatible fixtures with correct names, set expected hash/size, ran `obtain_official` on reused archive → **verified `sha256_ok=True`, `size_ok=True`, extraction/discovery/prepare succeeded, manifest includes verification/extraction/cleaning/split**, prepared 8640 rows / 3 functions, monotonic/complete grid. (Synthetic local archive only; not the real Azure trace.)

**Commands run (this update):**
```text
git switch -c feat/m2-azure-dataset-pipeline   # from dev/1e58fde
py -m py_compile data/azure_functions_2019.py
py -m pytest -q tests/test_azure_dataset.py
py -m pytest -q
py -m data.azure_functions_2019 --help
py -m data.azure_functions_2019 obtain --help
python - <<'PY'  # local synthetic tar.xz obtain_official validation (no network)
...
PY
```

**Still open for M1 acceptance:**
- **Real official archive not downloaded/extracted/prepared in this environment** (`azurefunctions_dataset2019_azurefunctions-dataset2019.tar.xz`, ~143 MB). `obtain` is implemented but not yet executed against the official remote asset here.
- Official-trace visualization/review on real prepared data not done (script exists and was run on fixtures: `results/plots/azure_fixture/*`).
- Full-trace scale/performance not exercised (per-function 14-day long form is large); recommended to use `--days` and/or aggregation (`total`/`by_app`/`top_k_total`) for tractable experiments and document choices.
- Feature-generation leakage checks specific to Azure-prepared data at training scale, and any additional interval/timezone edge-case validation on real data, remain.
- No official/raw/processed Azure data committed.

**Next concrete step (superseded by section 13):** run `python -m data.azure_functions_2019 obtain [--days ...] [--aggregate/--out/--manifest ...]` to acquire+verify+prepare the official trace (network/disk), then run `python scripts/visualize_azure_dataset.py --csv ... --manifest ...` and review; record manifest/hash/rows/coverage/splits and update this report. If a local archive/extracted path is preferred, point `--dest`/`--source-dir` instead of downloading.

## 13. Final M1 completion (v1.0, 2026-11-20)

**Modules/contracts changed:** `data/azure_functions_2019.py`, `configs/project.yaml`, `tests/test_azure_dataset.py`, `docs/milestones/README.md`. Canonical outputs are gitignored: `data/processed/azure_features.csv`, `data/processed/azure_manifest.json`, `data/processed/azure2019_full_total.*`, `results/plots/azure2019_full_total/*`.

**Official acquisition and verification (measured):**
- Downloaded/reused `data/raw/azure/azurefunctions-dataset-2019/azurefunctions_dataset2019_azurefunctions-dataset2019.tar.xz`, `142968140` bytes, SHA-256 `aff8b3ca7240a41a109e4ee598e0a96e45fcb92e7b8395ac19cb3748cd260d89` → `sha256_ok=true`, `size_ok=true`.
- Safe extraction now supports `member_pattern`/`days` filters; the full run used 14 official `invocations_per_function_md.anon.dNN.csv` files (13 extracted in the final run, d01 from the earlier day-1 run).
- One-command `obtain` was completed end-to-end with `--timeout-s`; the canonical default run was interrupted by the operator, so canonical outputs were generated from the verified explicit-path full run and copied with manifest paths updated. No raw/processed data committed.

**Official prepared trace (measured, not simulated):**
- Command: `py -m data.azure_functions_2019 obtain --aggregate total --out data/processed/azure2019_full_total.csv --manifest data/processed/azure2019_full_total_manifest.json` → `20160` rows, `1` aggregate series (`__total__`), `14` input files, `618545` input rows.
- Coverage: `20160/20160` expected function×time rows, zero duplicates, zero invalid/negative values, monotonic, start `2019-07-01 00:00:00+00:00`, end `2019-07-14 23:59:00+00:00`.
- Chronological split: train `14112`, val `3024`, test `3024`; boundaries recorded in manifest (train/test order preserved, no shuffle).
- Count stats from visualization: min `447383`, max `1258768`, mean `619831.8872023809` invocations per minute across the aggregate trace. These are real trace-derived counts, not energy/latency measurements.
- Plots generated: `results/plots/azure2019_full_total/{total_invocations_over_time,invocation_distribution,hourly_pattern,top_functions,split_boundaries}.png`.

**Timeout/timer implementation:** `prepare` and `obtain` now accept `--timeout-s N` (config default `300`). `aggregate_wide_files` checks deadlines per file/chunk; CLI installs a hard watchdog thread that exits `124`. Verified with `py -m data.azure_functions_2019 prepare --aggregate by_app --days 1 --timeout-s 10 ...` → exit `124` in ~11.6 s; cooperative timeout verified by unit test. `by_app`/`top_k_total` are implemented and fixture-tested but are **not recommended on full official day files until optimized**; `total` is the default and validated mode.

**Verification:** `py -m py_compile data/azure_functions_2019.py`, `py -m pytest -q` → **113 passed, 1 warning** (pre-existing ingestion date-format warning); `py -m data.azure_functions_2019 prepare --help` / `obtain --help` show `--timeout-s`.

**Limitations/next:** full per-function 14-day expansion and `by_app`/`top_k_total` official-scale runs remain unvalidated/slow; feature-generation leakage checks at training scale remain M2+ work; no model training, no live K8s/OpenFaaS/Prometheus, no measured energy/latency. Next milestone: M2 (TFT training/evaluation on the prepared chronological splits).
