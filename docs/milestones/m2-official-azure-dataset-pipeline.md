# Milestone 2 — Official Azure Dataset Pipeline

| Field | Value |
|---|---|
| Milestone | M2 — Official Azure dataset acquisition and preparation |
| Status | **In progress (source inspection + design started; implementation not complete)** |
| Date started | 2026-11-19 |
| Branch | `feat/m1-audit-contract-harmonization` |
| Base commit | `f41feecb2433b9a304ee1ee37b118b24fc0182bc` |
| Scope (so far) | Official source inspection (README/license/docs/metadata), trace selection rationale, pipeline design notes. **No large dataset download, no model training.** |

## Changelog

| Version | Date | Change |
|---|---|---|
| v0.1 | 2026-11-19 | Created M2 report; recorded official AzurePublicDataset inspection, licensing, candidate trace comparison, selected trace, and initial pipeline design/acceptance mapping. |

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

## 3. Selected trace (initial, for M2 implementation)

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

**Not yet done (M2 acceptance still open):**
- No full official archive downloaded/extracted/verified on this machine (intentional); `download/verify/prepare` against the real 14-day asset not executed end-to-end here.
- Dataset not visualized/reviewed (coverage/missingness/distribution/daily patterns/peaks/split plots) for the official trace.
- End-to-end "one command obtains/prepares selected official trace" from remote source not demonstrated in this environment (networked download of ~143 MB not run).
- Feature-level leakage tests against full training feature generation for Azure-prepared data and explicit interval/timezone edge-case validation on the full trace remain to be exercised.
- No official Azure raw/processed data committed (by design).

**Measured vs simulated vs estimated:** implementation/tests measured on local fixtures/smoke runs only. No real Azure trace metrics, no model training, no live cluster/Prometheus data.
