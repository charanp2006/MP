# Azure Public Dataset Availability and Provenance

| Field | Value |
|---|---|
| Document status | Local-data note for owners/agents |
| Date | 2026-11-24 |
| Scope | Azure Functions 2019 raw data, processed artifacts, Git visibility |
| Related v2 milestone | M1 — Azure data provenance and pipeline |

## 1. Owner clarification

The raw Azure Functions 2019 public dataset is **present locally** in this workspace. It is intentionally gitignored and therefore **cannot be expected in a fresh GitHub clone**. Absence from GitHub is not evidence that the data was never downloaded.

Never commit raw archive files, extracted daily CSVs, tokens, checkpoints, or large generated artifacts. Keep small fixtures and provenance manifests in Git.

## 2. Local raw data inventory

Observed local paths and sizes:

| Path | Approx. size | Git state |
|---|---:|---|
| `data/raw/azure/azurefunctions-dataset-2019/azurefunctions_dataset2019_azurefunctions-dataset2019.tar.xz` | 142,968,140 bytes (~136.3 MiB) | Ignored |
| `data/raw/azure/azurefunctions-dataset-2019/extracted/invocations_per_function_md.anon.d01.csv` … `d14.csv` | ~1.9 GiB total for 14 files | Ignored |
| `data/raw/azure/azurefunctions-dataset-2019/` | ~2.0 GiB including archive | Ignored |

Direct ignore evidence:

```text
.gitignore:53:data/raw/*  ->  data/raw/azure/azurefunctions-dataset-2019/...tar.xz
.gitignore:53:data/raw/*  ->  data/raw/azure/azurefunctions-dataset-2019/extracted/...d01.csv
```

`git ls-files data/raw` contains only `data/raw/.gitkeep`; no raw Azure data is tracked.

## 3. Processed artifacts that are tracked

Derived artifacts under `data/processed/` are currently tracked in Git, including:

- `azure_manifest.json`
- `azure2019_full_total.csv` and `azure2019_full_total_manifest.json`
- `azure2019_day1_total.csv` and `azure2019_day1_total_manifest.json`
- `azure_features.csv`
- fixture-derived prepared/total CSVs and manifests
- `features.csv`

These are small derived outputs, not the raw 1.5–2.0 GiB source. They are included so tests and reports remain reproducible. Do not treat them as a substitute for the official raw source.

## 4. Source, license and integrity

Recorded in `data/azure_functions_2019.py` and `data/processed/azure_manifest.json`:

- Source repository: `https://github.com/Azure/AzurePublicDataset`
- Dataset document: `AzureFunctionsDataset2019.md`
- Release tag: `dataset-functions-2019`
- Asset: `azurefunctions_dataset2019_azurefunctions-dataset2019.tar.xz`
- License: `CC-BY-4.0`
- Citation: Shahrad et al., “Serverless in the Wild: Characterizing and Optimizing the Serverless Workload at a Large Cloud Provider,” USENIX ATC 2020.
- Expected asset size: `142968140` bytes
- Expected SHA-256: `aff8b3ca7240a41a109e4ee598e0a96e45fcb92e7b8395ac19cb3748cd260d89`
- Manifest verification: `sha256_ok: true`, `size_ok: true`

Provenance caveat: the manifests record `reused_existing: true`, `bytes_downloaded: 0`, `retrieved_at_utc: null`, and `http_status: null` because the archive was reused locally rather than downloaded during that run. This is acceptable for reuse but should be strengthened if a fresh download is performed later.

## 5. Reproducible commands

Inspect source metadata:

```bash
python -m data.azure_functions_2019 inspect
```

Verify the local archive:

```bash
python -m data.azure_functions_2019 verify
```

Regenerate the validated `total` aggregate from the already available local archive/extracted files:

```bash
python -m data.azure_functions_2019 obtain \
  --aggregate total \
  --out data/processed/azure2019_full_total.csv \
  --manifest data/processed/azure2019_full_total_manifest.json
```

Visualize prepared data:

```bash
python scripts/visualize_azure_dataset.py \
  --csv data/processed/azure2019_full_total.csv \
  --manifest data/processed/azure2019_full_total_manifest.json
```

Full CLI help:

```bash
python -m data.azure_functions_2019 --help
python -m data.azure_functions_2019 obtain --help
```

## 6. Data limitations

The Azure Functions 2019 trace provides invocation/completion-oriented workload data. It does **not** provide real CPU, memory, P95 latency, cold-start, power, or watt measurements for our system. Any such values in experiments are clearly labelled simulation, estimate, or proxy.

The validated full-scale pipeline currently uses the `total` aggregate. `by_app` and `top_k_total` paths exist but are fixture-tested and not recommended on full daily files until optimized.

## 7. Fresh-clone guidance

A fresh GitHub clone will not contain the raw archive or extracted CSVs. To reproduce Azure experiments:

1. Obtain the official release asset from the source above, respecting license and usage terms.
2. Place the archive under `data/raw/azure/azurefunctions-dataset-2019/`.
3. Run `python -m data.azure_functions_2019 verify`.
4. Run the documented `obtain` command.
5. Confirm manifest SHA-256, size, schema, split boundaries and plots before training.

Do not email, upload, or commit raw data.
