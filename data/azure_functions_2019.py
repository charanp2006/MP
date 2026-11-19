"""Azure Functions 2019 (ATC 2020) dataset utilities.

Selected trace: AzureFunctionsDataset2019 invocations
(14 CSVs: invocations_per_function_md.anon.d01-d14.csv).
Source: https://github.com/Azure/AzurePublicDataset
Release: dataset-functions-2019
License: CC-BY-4.0 (see manifest/attribution).

Provides inspect/download/verify/parse/aggregate/clean/split/export and
manifest helpers. Does NOT commit or auto-download large data.
"""

from __future__ import annotations

import argparse
import fnmatch
import glob
import hashlib
import json
import os
import re
import shutil
import tarfile
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

REPO_URL = "https://github.com/Azure/AzurePublicDataset"
DATASET_DOC = "https://raw.githubusercontent.com/Azure/AzurePublicDataset/master/AzureFunctionsDataset2019.md"
RELEASE_TAG = "dataset-functions-2019"
ASSET_NAME = "azurefunctions_dataset2019_azurefunctions-dataset2019.tar.xz"
ASSET_URL = (
    "https://github.com/Azure/AzurePublicDataset/releases/download/"
    "dataset-functions-2019/azurefunctions_dataset2019_azurefunctions-dataset2019.tar.xz"
)
ASSET_SHA256 = "aff8b3ca7240a41a109e4ee598e0a96e45fcb92e7b8395ac19cb3748cd260d89"
ASSET_SIZE = 142968140
CITATION = (
    "Mohammad Shahrad, Rodrigo Fonseca, Inigo Goiri, Gohar Chaudhry, Paul Batum, "
    "Jason Cooke, Eduardo Laureano, Colby Tresness, Mark Russinovich, Ricardo Bianchini. "
    '"Serverless in the Wild: Characterizing and Optimizing the Serverless Workload at a Large Cloud Provider." '
    "USENIX ATC 2020."
)
LICENSE = "CC-BY-4.0"

INVOCATION_FILE_RE = re.compile(r"invocations_per_function_md\.anon\.d(\d{2})\.csv$")
MINUTE_COLUMNS = [str(i) for i in range(1, 1441)]
ID_COLUMNS = ["HashOwner", "HashApp", "HashFunction", "Trigger"]
REQUIRED_INVOCATION_COLUMNS = ID_COLUMNS + MINUTE_COLUMNS

DAY1_BASE_UTC = datetime(2019, 7, 1, tzinfo=timezone.utc)


@dataclass
class InspectInfo:
    dataset: str
    release_tag: str
    asset_name: str
    asset_url: str
    asset_sha256: str
    asset_size_bytes: int
    license: str
    citation: str
    source_repo: str
    schema: dict
    semantics: dict
    limitations: list[str]


def default_azure_config(config: dict | None = None) -> dict:
    cfg = (config or {}).get("data", {}).get("azure", {}) or {}
    return {
        "dataset": cfg.get("dataset", "azurefunctions-dataset-2019"),
        "release_tag": cfg.get("release_tag", RELEASE_TAG),
        "asset_name": cfg.get("asset_name", ASSET_NAME),
        "asset_url": cfg.get("asset_url", ASSET_URL),
        "asset_sha256": cfg.get("asset_sha256", ASSET_SHA256),
        "raw_dir": cfg.get("raw_dir", "data/raw/azure/azurefunctions-dataset-2019"),
        "extracted_dir": cfg.get("extracted_dir", "data/raw/azure/azurefunctions-dataset-2019/extracted"),
        "manifest_path": cfg.get("manifest_path", "data/processed/azure_manifest.json"),
        "processed_path": cfg.get("processed_path", "data/processed/azure_features.csv"),
        "invocations_glob": cfg.get("invocations_glob", "invocations_per_function_md.anon.d*.csv"),
        "days": cfg.get("days"),
        "interval_seconds": int((config or {}).get("control", {}).get("interval_seconds", 60)),
        "target_column": (config or {}).get("data", {}).get("target_column", "invocation_count"),
        "split": (config or {}).get("forecast", {}).get("training", {}).get("split", [0.7, 0.15, 0.15]),
        "aggregate": cfg.get("aggregate", "per_function"),
        "top_k": cfg.get("top_k"),
        "chunk_size": cfg.get("chunk_size", 2000),
        "timeout_s": cfg.get("timeout_s", 300),
    }


def inspect(config: dict | None = None) -> dict:
    acfg = default_azure_config(config)
    info = InspectInfo(
        dataset=acfg["dataset"],
        release_tag=acfg["release_tag"],
        asset_name=acfg["asset_name"],
        asset_url=acfg["asset_url"],
        asset_sha256=acfg["asset_sha256"],
        asset_size_bytes=ASSET_SIZE,
        license=LICENSE,
        citation=CITATION,
        source_repo=REPO_URL,
        schema={
            "invocations_csv_columns": ID_COLUMNS + ["1..1440 (minute-of-day invocation counts)"],
            "id_columns": ID_COLUMNS,
            "minute_columns": "1..1440",
            "trigger_groups": ["http", "timer", "event", "queue", "storage", "orchestration", "others"],
        },
        semantics={
            "unit": "invocation count per minute per function (recorded after execution)",
            "duration_days": 14,
            "minutes_per_day": 1440,
            "timezone": "unspecified; sequential 1-min slots per day with relative day base 2019-07-01Z (assumption)",
            "target_mapping": "sum invocation_count over configured interval_seconds per function_id and timestamp bin",
            "function_id": "HashApp|HashFunction (anonymized hashes)",
        },
        limitations=[
            "Anonymized IDs (HMAC-SHA256, different salts per column); per-application random sample, rate small/unspecified.",
            "Invocation counts are post-execution per-minute bins, not sub-minute arrivals or concurrency.",
            "No real per-interval CPU/memory/latency/cold-start/container/power/energy series; proxies must be labeled simulated/estimated.",
            "Duration/memory files are distributions/aggregates, not per-minute runtime telemetry.",
            "Possible count discrepancies/missing fields noted by authors; parsing must validate gaps/duplicates/invalid values.",
        ],
    )
    return asdict(info)


def _deadline(timeout_s: float | None) -> float | None:
    if timeout_s is None:
        return None
    timeout_s = float(timeout_s)
    if timeout_s <= 0:
        return None
    return time.monotonic() + timeout_s


def _check_deadline(deadline: float | None, stage: str) -> None:
    if deadline is not None and time.monotonic() >= deadline:
        raise TimeoutError(f"timeout after {stage}")


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def download_asset(config: dict | None = None, dest: str | Path | None = None, resume: bool = True) -> dict:
    acfg = default_azure_config(config)
    url = acfg["asset_url"]
    dest_path = Path(dest or Path(acfg["raw_dir"]) / acfg["asset_name"])
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    existing = dest_path.stat().st_size if dest_path.exists() else 0
    headers = {}
    mode = "wb"
    if resume and existing > 0:
        headers["Range"] = f"bytes={existing}-"
        mode = "ab"
    req = Request(url, headers=headers)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    status = None
    downloaded = 0
    with urlopen(req) as resp, open(dest_path, mode) as out:
        status = getattr(resp, "status", 200)
        if status == 416 and existing > 0:
            downloaded = 0
        elif status == 200 and mode == "ab":
            out.close()
            with open(dest_path, "wb") as out2, urlopen(Request(url)) as resp2:
                status = getattr(resp2, "status", 200)
                for chunk in iter(lambda: resp2.read(1024 * 1024), b""):
                    out2.write(chunk)
                    downloaded += len(chunk)
        else:
            for chunk in iter(lambda: resp.read(1024 * 1024), b""):
                out.write(chunk)
                downloaded += len(chunk)
    size = dest_path.stat().st_size
    sha = sha256_file(dest_path)
    expected = acfg.get("asset_sha256")
    return {
        "url": url,
        "dest": str(dest_path),
        "retrieved_at_utc": retrieved_at,
        "http_status": status,
        "bytes_downloaded": downloaded,
        "size_bytes": size,
        "sha256": sha,
        "expected_sha256": expected,
        "sha256_ok": (sha == expected) if expected else None,
    }


def verify_asset(path: str | Path, expected_sha256: str | None = None, expected_size: int | None = None) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"asset not found: {p}")
    sha = sha256_file(p)
    size = p.stat().st_size
    return {
        "path": str(p),
        "sha256": sha,
        "size_bytes": size,
        "sha256_ok": (sha == expected_sha256) if expected_sha256 else None,
        "size_ok": (size == expected_size) if expected_size is not None else None,
    }


def extract_archive(
    archive_path: str | Path,
    dest_dir: str | Path,
    member_pattern: str | None = None,
    days: list[int] | None = None,
) -> list[str]:
    """Extract archive safely, optionally only files matching a glob and/or day list."""
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    day_set = set(int(d) for d in days) if days is not None else None
    with tarfile.open(archive_path, mode="r:*") as tf:
        members = tf.getmembers()
        selected = []
        for m in members:
            target = (dest / m.name).resolve()
            if dest.resolve() not in target.parents and target != dest.resolve():
                raise ValueError(f"unsafe archive member path: {m.name}")
            if not m.isfile():
                continue
            name = os.path.basename(m.name)
            if member_pattern and not fnmatch.fnmatch(name, member_pattern):
                continue
            if day_set is not None:
                day = _day_index_from_name(name)
                if day is None or day not in day_set:
                    continue
            selected.append(m)
        for m in selected:
            target = dest / m.name
            target.parent.mkdir(parents=True, exist_ok=True)
            src = tf.extractfile(m)
            if src is None:
                continue
            with src, open(target, "wb") as out:
                shutil.copyfileobj(src, out)
    return [str(dest / m.name) for m in selected]


def _day_index_from_name(name: str) -> int | None:
    base = os.path.basename(name)
    m = INVOCATION_FILE_RE.search(base)
    if m:
        return int(m.group(1))
    # Fallback for fixtures/renamed copies containing dNN (e.g. *_d01_sample.csv).
    m = re.search(r"(?:^|[^0-9])d(\d{2})(?:[^0-9]|$)", base, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def find_invocation_files(
    source_dir: str | Path,
    pattern: str = "invocations_per_function_md.anon.d*.csv",
    days: list[int] | None = None,
) -> list[Path]:
    base = Path(source_dir)
    paths = [Path(p) for p in glob.glob(str(base / pattern))]
    if not paths:
        paths = [Path(p) for p in glob.glob(str(base / "**" / pattern), recursive=True)]
    out = []
    for p in sorted(paths):
        d = _day_index_from_name(p.name)
        if d is None:
            continue
        if days is not None and d not in set(days):
            continue
        out.append(p)
    return sorted(out, key=lambda p: _day_index_from_name(p.name) or 0)


def validate_invocation_schema(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in REQUIRED_INVOCATION_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"invocation CSV missing required columns (sample): {missing[:10]}")
    return df


def parse_invocation_csv(path: str | Path, day_index: int | None = None) -> pd.DataFrame:
    df = pd.read_csv(path)
    validate_invocation_schema(df)
    day = _day_index_from_name(str(path)) if day_index is None else int(day_index)
    if day is None:
        raise ValueError(f"cannot infer day index from filename: {path}")
    df = df.copy()
    df["_day_index"] = day
    return df


def reshape_invocations_long(df: pd.DataFrame, interval_seconds: int = 60) -> pd.DataFrame:
    """Wide (per-minute columns 1..1440) -> long rows per function/time bin."""
    if interval_seconds <= 0 or interval_seconds % 60 != 0:
        raise ValueError("interval_seconds must be a positive multiple of 60 for Azure minute-binned data")
    validate_invocation_schema(df)
    work = df.copy()
    for c in MINUTE_COLUMNS:
        work[c] = pd.to_numeric(work[c], errors="coerce")
    if work[MINUTE_COLUMNS].isna().any().any():
        bad = int(work[MINUTE_COLUMNS].isna().sum().sum())
        raise ValueError(f"invalid/non-numeric minute values: {bad} cells")
    if (work[MINUTE_COLUMNS] < 0).any().any():
        raise ValueError("negative invocation counts found")

    id_vars = ID_COLUMNS + ["_day_index"]
    long = work.melt(
        id_vars=id_vars,
        value_vars=MINUTE_COLUMNS,
        var_name="minute_of_day",
        value_name="invocation_count",
    )
    long["minute_of_day"] = long["minute_of_day"].astype(int)
    long["invocation_count"] = long["invocation_count"].astype(np.int64)

    base = pd.Timestamp(DAY1_BASE_UTC)
    day_offsets = pd.to_timedelta(long["_day_index"].astype(int) - 1, unit="D")
    minute_offsets = pd.to_timedelta(long["minute_of_day"].astype(int) - 1, unit="min")
    long["timestamp"] = base + day_offsets + minute_offsets
    long["function_id"] = long["HashApp"].astype(str) + "|" + long["HashFunction"].astype(str)

    out = long.rename(
        columns={
            "HashOwner": "hash_owner",
            "HashApp": "hash_app",
            "HashFunction": "hash_function",
            "Trigger": "trigger",
            "_day_index": "day_index",
        }
    )
    out = out[
        [
            "timestamp",
            "function_id",
            "invocation_count",
            "trigger",
            "hash_owner",
            "hash_app",
            "hash_function",
            "day_index",
        ]
    ]

    if interval_seconds > 60:
        freq = f"{interval_seconds}s"
        out["timestamp"] = out["timestamp"].dt.floor(freq)
        out = out.groupby(
            ["timestamp", "function_id", "trigger", "hash_owner", "hash_app", "hash_function"],
            as_index=False,
        ).agg({"invocation_count": "sum", "day_index": "min"})

    out = out.sort_values(["timestamp", "function_id"], kind="stable").reset_index(drop=True)
    return out


def clean_long(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    rows_in = len(df)
    out = df.copy()
    for c in ("timestamp", "function_id", "invocation_count"):
        if c not in out.columns:
            raise ValueError(f"missing required column: {c}")
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True, errors="raise")
    out["function_id"] = out["function_id"].astype(str)
    out["invocation_count"] = pd.to_numeric(out["invocation_count"], errors="coerce")
    invalid_numeric = int(out["invocation_count"].isna().sum())
    if invalid_numeric:
        raise ValueError(f"invalid invocation_count values: {invalid_numeric}")
    if (out["invocation_count"] < 0).any():
        raise ValueError("negative invocation_count values")

    dup_mask = out.duplicated(subset=["timestamp", "function_id"], keep=False)
    dup_rows = int(dup_mask.sum())
    if dup_rows:
        meta_cols = [c for c in out.columns if c not in ("timestamp", "function_id", "invocation_count")]
        agg = {"invocation_count": "sum"}
        for c in meta_cols:
            agg[c] = "first"
        out = out.groupby(["timestamp", "function_id"], as_index=False).agg(agg)

    out = out.sort_values(["timestamp", "function_id"], kind="stable").reset_index(drop=True)
    monotonic = (
        bool(out.groupby("function_id")["timestamp"].apply(lambda s: s.is_monotonic_increasing).all())
        if len(out)
        else True
    )

    # Coverage/missingness for the prepared grid: input comes from full 1-min schema per day,
    # but we report expected-vs-observed counts for transparency.
    expected_rows = None
    missing_intervals = None
    if len(out):
        n_func = int(out["function_id"].nunique())
        n_ts = int(out["timestamp"].nunique())
        expected_rows = n_func * n_ts
        missing_intervals = int(max(expected_rows - len(out), 0))
    nan_counts = {c: int(out[c].isna().sum()) for c in out.columns if int(out[c].isna().sum()) > 0}

    report = {
        "rows_in": rows_in,
        "rows_out": int(len(out)),
        "duplicate_key_rows": dup_rows,
        "duplicates_resolved": dup_rows > 0,
        "invalid_numeric": invalid_numeric,
        "negative_values": 0,
        "monotonic_per_function": monotonic,
        "functions": int(out["function_id"].nunique()) if len(out) else 0,
        "unique_timestamps": int(out["timestamp"].nunique()) if len(out) else 0,
        "expected_rows_function_x_time": expected_rows,
        "missing_intervals_function_x_time": missing_intervals,
        "nan_counts": nan_counts,
        "start": str(out["timestamp"].min()) if len(out) else None,
        "end": str(out["timestamp"].max()) if len(out) else None,
    }
    return out, report


def chronological_split_indices(n: int, split: list[float] | tuple[float, float, float]) -> dict:
    if n <= 0:
        return {"train": (0, 0), "val": (0, 0), "test": (0, 0)}
    s = list(split)
    if len(s) != 3:
        raise ValueError("split must have 3 fractions [train,val,test]")
    total = float(sum(s))
    if total <= 0:
        raise ValueError("split fractions must sum > 0")
    s = [x / total for x in s]
    train_end = int(n * s[0])
    val_end = int(n * (s[0] + s[1]))
    train_end = min(max(train_end, 1 if n >= 3 else n), n)
    val_end = min(max(val_end, train_end), n)
    return {"train": (0, train_end), "val": (train_end, val_end), "test": (val_end, n)}


def add_split_labels_by_time(df: pd.DataFrame, split: list[float]) -> tuple[pd.DataFrame, dict]:
    out = df.copy()
    times = pd.Index(sorted(out["timestamp"].unique()))
    n = len(times)
    idx = chronological_split_indices(n, split)

    def label(ts):
        pos_arr = times.get_indexer([ts])
        pos = int(pos_arr[0])
        if pos < 0:
            return "test"
        if pos < idx["train"][1]:
            return "train"
        if pos < idx["val"][1]:
            return "val"
        return "test"

    out["split"] = out["timestamp"].map(label)
    boundaries = {
        k: {
            "start_index": v[0],
            "end_index": v[1],
            "start_time": str(times[v[0]]) if v[1] > v[0] and n > 0 else None,
            "end_time_exclusive": str(times[v[1]])
            if v[1] < n and v[1] > v[0]
            else (str(times[-1]) if v[1] == n and v[1] > v[0] and n > 0 else None),
            "n_unique_timestamps": v[1] - v[0],
        }
        for k, v in idx.items()
    }
    counts = out["split"].value_counts().to_dict() if len(out) else {}
    return out, {
        "boundaries": boundaries,
        "row_counts": {k: int(counts.get(k, 0)) for k in ("train", "val", "test")},
    }


def build_manifest(
    config,
    source_files,
    clean_report,
    split_report,
    verify_info=None,
    download_info=None,
) -> dict:
    acfg = default_azure_config(config)
    return {
        "dataset": acfg["dataset"],
        "source": {
            "repo": REPO_URL,
            "dataset_doc": DATASET_DOC,
            "release_tag": acfg["release_tag"],
            "asset_name": acfg["asset_name"],
            "asset_url": acfg["asset_url"],
            "license": LICENSE,
            "citation": CITATION,
        },
        "retrieval": download_info
        or {"note": "not downloaded by this run (prepared from local/extracted files or fixture)"},
        "verification": verify_info,
        "files": [
            {
                "path": str(p),
                "name": p.name,
                "day_index": _day_index_from_name(p.name),
                "sha256": sha256_file(p),
                "size_bytes": p.stat().st_size,
            }
            for p in source_files
        ],
        "schema": {
            "raw_columns": ID_COLUMNS + ["1..1440"],
            "prepared_columns": [
                "timestamp",
                "function_id",
                "invocation_count",
                "trigger",
                "hash_owner",
                "hash_app",
                "hash_function",
                "day_index",
                "split(optional)",
            ],
        },
        "units": {
            "invocation_count": "count per interval (sum over minute bins within interval) per function_id",
            "interval_seconds": acfg["interval_seconds"],
            "timestamp": "UTC, sequential 1-min slots from relative day base 2019-07-01T00:00:00Z (assumption)",
        },
        "aggregation": {
            "function_id": "HashApp|HashFunction",
            "interval_seconds": acfg["interval_seconds"],
            "method": "sum of per-minute invocation counts within bin",
        },
        "cleaning": clean_report,
        "split": split_report,
        "assumptions": [
            "Relative day mapping d01..d14 -> sequential days starting 2019-07-01Z for ordering; absolute calendar alignment not asserted by trace.",
            "Per-minute counts aggregated by sum to configured interval.",
            "Duplicate (timestamp,function_id) rows resolved by summing invocation_count.",
            "CPU/memory/latency/cold-start/power/energy are not provided by this trace; downstream proxies must be labeled simulated/estimated.",
        ],
    }


def aggregate_long(df: pd.DataFrame, mode: str = "per_function", top_k: int | None = None) -> tuple[pd.DataFrame, dict]:
    """Aggregate long-form invocation rows.

    mode:
      - per_function: keep per function_id series (default)
      - total: sum invocation_count across all functions per timestamp
      - by_app: sum per hash_app per timestamp (if available)
      - top_k_total: keep only top_k functions by total invocations (plus aggregate rest as dropped)
    """
    mode = (mode or "per_function").lower()
    report = {"mode": mode, "input_rows": int(len(df)), "input_functions": int(df["function_id"].nunique()) if len(df) else 0}
    out = df.copy()
    if mode == "per_function":
        report["output_rows"] = int(len(out))
        report["output_functions"] = int(out["function_id"].nunique()) if len(out) else 0
        return out, report
    if mode == "total":
        agg = out.groupby("timestamp", as_index=False).agg({"invocation_count": "sum"})
        if "day_index" in out.columns:
            agg["day_index"] = out.groupby("timestamp")["day_index"].min().values
        agg["function_id"] = "__total__"
        agg = agg.sort_values(["timestamp"], kind="stable").reset_index(drop=True)
        report.update({"output_rows": int(len(agg)), "output_functions": 1})
        return agg, report
    if mode == "by_app" and "hash_app" in out.columns:
        group_cols = ["timestamp", "hash_app"]
        agg = out.groupby(group_cols, as_index=False).agg({"invocation_count": "sum"})
        if "day_index" in out.columns:
            agg["day_index"] = out.groupby(group_cols)["day_index"].min().values
        agg["function_id"] = agg["hash_app"].astype(str)
        agg = agg.sort_values(["timestamp", "function_id"], kind="stable").reset_index(drop=True)
        report.update({"output_rows": int(len(agg)), "output_functions": int(agg["function_id"].nunique())})
        return agg, report
    if mode in ("top_k_total", "top_k") and top_k is not None and top_k > 0:
        totals = out.groupby("function_id")["invocation_count"].sum().sort_values(ascending=False)
        keep = set(totals.head(int(top_k)).index.tolist())
        filtered = out[out["function_id"].isin(keep)].copy()
        report.update({
            "top_k": int(top_k),
            "output_rows": int(len(filtered)),
            "output_functions": int(filtered["function_id"].nunique()) if len(filtered) else 0,
            "dropped_functions": int(out["function_id"].nunique() - filtered["function_id"].nunique()),
        })
        return filtered.sort_values(["timestamp", "function_id"], kind="stable").reset_index(drop=True), report
    # fallback
    report["output_rows"] = int(len(out))
    report["output_functions"] = int(out["function_id"].nunique()) if len(out) else 0
    report["note"] = "unrecognized mode or missing requirements; returned input"
    return out, report


def _wide_chunk_values(df: pd.DataFrame) -> np.ndarray:
    missing = [c for c in MINUTE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"invocation CSV missing minute columns (sample): {missing[:10]}")
    try:
        arr = df[MINUTE_COLUMNS].to_numpy(dtype=np.int64, copy=False)
    except (TypeError, ValueError):
        vals = df[MINUTE_COLUMNS].apply(pd.to_numeric, errors="coerce")
        bad = int(vals.isna().sum().sum())
        if bad:
            raise ValueError(f"invalid/non-numeric minute values: {bad} cells") from None
        arr = vals.to_numpy(dtype=np.int64)
    if (arr < 0).any():
        raise ValueError("negative invocation counts found")
    return arr


def _minute_timestamps(day_index: int, interval_seconds: int) -> pd.DatetimeIndex:
    minutes = np.arange(1, len(MINUTE_COLUMNS) + 1)
    base = pd.Timestamp(DAY1_BASE_UTC) + pd.Timedelta(days=int(day_index) - 1)
    ts = pd.DatetimeIndex(base + pd.to_timedelta(minutes - 1, unit="m"))
    if interval_seconds > 60:
        return ts.floor(f"{interval_seconds}s")
    return ts


def _minute_vector_frame(
    values: np.ndarray,
    function_id: str,
    day_index: int,
    interval_seconds: int,
    extra: dict | None = None,
) -> pd.DataFrame:
    ts = _minute_timestamps(day_index, interval_seconds)
    out = pd.DataFrame(
        {
            "timestamp": ts,
            "function_id": str(function_id),
            "invocation_count": np.asarray(values, dtype=np.int64),
        }
    )
    extras = extra or {}
    for k, v in extras.items():
        out[k] = v
    if interval_seconds > 60 and out["timestamp"].duplicated().any():
        group_cols = ["timestamp", "function_id"] + list(extras.keys())
        out = out.groupby(group_cols, as_index=False).agg({"invocation_count": "sum"})
    out["day_index"] = int(day_index)
    cols = ["timestamp", "function_id", "invocation_count"] + list(extras.keys()) + ["day_index"]
    return out[cols].sort_values(["timestamp", "function_id"], kind="stable").reset_index(drop=True)


def aggregate_wide_files(
    file_paths,
    config=None,
    mode: str = "total",
    top_k: int | None = None,
    timeout_s: float | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Aggregate wide invocation CSVs without materializing function-by-minute long rows."""
    deadline = _deadline(timeout_s)
    _check_deadline(deadline, "aggregation start")
    acfg = default_azure_config(config)
    mode = (mode or "total").lower()
    if mode not in ("total", "by_app", "top_k_total", "top_k"):
        raise ValueError(f"unsupported wide aggregation mode: {mode}")
    paths = [Path(p) for p in file_paths]
    if not paths:
        raise ValueError("no invocation files provided")

    chunk_size = max(256, int(acfg.get("chunk_size", 2000)))
    interval_seconds = int(acfg["interval_seconds"])
    input_rows = 0
    totals_by_day: dict[int, np.ndarray] = {}
    app_vectors: dict[tuple[int, str], np.ndarray] = {}
    function_totals: dict[str, float] = {}
    function_vectors: dict[tuple[int, str], np.ndarray] = {}

    for p in paths:
        _check_deadline(deadline, f"starting file {p.name}")
        raw_header = pd.read_csv(p, nrows=0)
        validate_invocation_schema(raw_header)
        day = _day_index_from_name(p.name) or 1
        for chunk in pd.read_csv(p, usecols=ID_COLUMNS + MINUTE_COLUMNS, chunksize=chunk_size):
            _check_deadline(deadline, f"reading chunk from {p.name}")
            vals = _wide_chunk_values(chunk)
            input_rows += len(chunk)
            if mode == "total":
                totals_by_day[day] = totals_by_day.get(day, np.zeros(len(MINUTE_COLUMNS), dtype=np.int64)) + vals.sum(
                    axis=0, dtype=np.int64
                )
            elif mode == "by_app":
                app_codes, app_labels = pd.factorize(chunk["HashApp"].astype(str), sort=False)
                sums = np.zeros((len(app_labels), len(MINUTE_COLUMNS)), dtype=np.int64)
                np.add.at(sums, app_codes, vals)
                for i, app in enumerate(app_labels):
                    if i % 64 == 0:
                        _check_deadline(deadline, f"aggregating apps from {p.name}")
                    key = (day, str(app))
                    app_vectors[key] = app_vectors.get(key, np.zeros(len(MINUTE_COLUMNS), dtype=np.int64)) + sums[i]
            else:
                fids = (chunk["HashApp"].astype(str) + "|" + chunk["HashFunction"].astype(str)).to_numpy()
                fid_codes, fid_labels = pd.factorize(fids, sort=False)
                row_totals = vals.sum(axis=1, dtype=np.int64)
                sums = np.bincount(fid_codes, weights=row_totals, minlength=len(fid_labels))
                for i, fid in enumerate(fid_labels):
                    if i % 64 == 0:
                        _check_deadline(deadline, f"counting functions from {p.name}")
                    function_totals[str(fid)] = float(function_totals.get(str(fid), 0.0)) + float(sums[i])

    frames = []
    if mode == "total":
        for day, values in sorted(totals_by_day.items()):
            frames.append(_minute_vector_frame(values, "__total__", day, interval_seconds))
    elif mode == "by_app":
        for (day, app), values in sorted(app_vectors.items()):
            frames.append(_minute_vector_frame(values, app, day, interval_seconds, {"hash_app": app}))
    else:
        k = int(top_k or 10)
        keep = set(sorted(function_totals, key=function_totals.get, reverse=True)[:k])
        for p in paths:
            _check_deadline(deadline, f"second pass file {p.name}")
            raw_header = pd.read_csv(p, nrows=0)
            validate_invocation_schema(raw_header)
            day = _day_index_from_name(p.name) or 1
            for chunk in pd.read_csv(p, usecols=ID_COLUMNS + MINUTE_COLUMNS, chunksize=chunk_size):
                _check_deadline(deadline, f"second pass chunk from {p.name}")
                vals = _wide_chunk_values(chunk)
                fids = (chunk["HashApp"].astype(str) + "|" + chunk["HashFunction"].astype(str)).to_numpy()
                mask = np.isin(fids, list(keep))
                if not mask.any():
                    continue
                sub_vals = vals[mask]
                sub_fids = fids[mask]
                fid_codes, fid_labels = pd.factorize(sub_fids, sort=False)
                sums = np.zeros((len(fid_labels), len(MINUTE_COLUMNS)), dtype=np.int64)
                np.add.at(sums, fid_codes, sub_vals)
                for i, fid in enumerate(fid_labels):
                    if i % 64 == 0:
                        _check_deadline(deadline, f"second pass functions from {p.name}")
                    key = (day, str(fid))
                    function_vectors[key] = function_vectors.get(
                        key, np.zeros(len(MINUTE_COLUMNS), dtype=np.int64)
                    ) + sums[i]
        for (day, fid), values in sorted(function_vectors.items()):
            frames.append(
                _minute_vector_frame(values, fid, day, interval_seconds, {"hash_app": fid.split("|", 1)[0]})
            )

    if not frames:
        raise ValueError("no aggregated rows produced")
    out = pd.concat(frames, ignore_index=True)
    out = out.sort_values(["timestamp", "function_id"], kind="stable").reset_index(drop=True)
    report = {
        "mode": mode,
        "method": "chunked_wide",
        "input_rows": int(input_rows),
        "input_functions": int(len(function_totals)) if mode in ("top_k_total", "top_k") else None,
        "output_rows": int(len(out)),
        "output_functions": int(out["function_id"].nunique()),
        "chunk_size": chunk_size,
    }
    if mode in ("top_k_total", "top_k"):
        report["top_k"] = k
        report["dropped_functions"] = int(max(len(function_totals) - len(keep), 0))
    return out, report


def prepare_from_files(file_paths, config=None, do_split=True, verify_info=None, download_info=None, timeout_s=None):
    acfg = default_azure_config(config)
    deadline = _deadline(timeout_s if timeout_s is not None else acfg.get("timeout_s"))
    _check_deadline(deadline, "prepare start")
    paths = [Path(p) for p in file_paths]
    aggregate_mode = acfg.get("aggregate", "per_function")
    top_k = acfg.get("top_k")
    if aggregate_mode in ("total", "by_app", "top_k_total", "top_k"):
        combined, aggregate_report = aggregate_wide_files(
            paths, config, mode=aggregate_mode, top_k=top_k, timeout_s=timeout_s
        )
    else:
        frames = []
        for p in paths:
            _check_deadline(deadline, f"parsing {p.name}")
            raw = parse_invocation_csv(p)
            long = reshape_invocations_long(raw, interval_seconds=acfg["interval_seconds"])
            frames.append(long)
        if not frames:
            raise ValueError("no invocation files provided")
        combined = pd.concat(frames, ignore_index=True)
        combined, aggregate_report = aggregate_long(combined, mode=aggregate_mode, top_k=top_k)
    _check_deadline(deadline, "cleaning")
    clean_df, clean_report = clean_long(combined)
    split_report = {}
    if do_split:
        _check_deadline(deadline, "split labeling")
        clean_df, split_report = add_split_labels_by_time(clean_df, acfg["split"])
    manifest = build_manifest(
        config, paths, clean_report, split_report, verify_info=verify_info, download_info=download_info
    )
    manifest["aggregation_detail"] = aggregate_report
    manifest["aggregation"]["mode"] = aggregate_mode
    if top_k is not None:
        manifest["aggregation"]["top_k"] = top_k
    return clean_df, manifest


def obtain_official(
    config=None, dest=None, source_dir=None, days=None, do_split=True, force_download=False, timeout_s=None
):
    """Download (or reuse), verify, extract, and prepare the official Azure Functions 2019 trace.

    Returns (df, manifest, info). Does not download if a verified/reusable archive already
    exists at the destination unless force_download=True.
    """
    acfg = default_azure_config(config)
    dest_path = Path(dest or Path(acfg["raw_dir"]) / acfg["asset_name"])
    if dest_path.exists() and verify_asset(dest_path, expected_sha256=acfg.get("asset_sha256"), expected_size=ASSET_SIZE).get(
        "sha256_ok"
    ) is False:
        raise ValueError(f"archive SHA-256 mismatch before obtain: {dest_path}")
    if force_download or not dest_path.exists():
        download_info = download_asset(config, dest=dest_path, resume=not force_download)
    else:
        existing_sha = sha256_file(dest_path)
        download_info = {
            "url": acfg["asset_url"],
            "dest": str(dest_path),
            "retrieved_at_utc": None,
            "http_status": None,
            "bytes_downloaded": 0,
            "size_bytes": dest_path.stat().st_size,
            "sha256": existing_sha,
            "expected_sha256": acfg.get("asset_sha256"),
            "sha256_ok": (existing_sha == acfg.get("asset_sha256")) if acfg.get("asset_sha256") else None,
            "reused_existing": True,
        }
    verify_info = verify_asset(dest_path, expected_sha256=acfg.get("asset_sha256"), expected_size=ASSET_SIZE)
    if verify_info.get("sha256_ok") is False:
        raise ValueError(
            f"archive SHA-256 mismatch: expected {acfg.get('asset_sha256')} got {verify_info.get('sha256')}"
        )

    extract_dir = Path(source_dir or acfg["extracted_dir"])
    files = find_invocation_files(extract_dir, acfg["invocations_glob"], days=days)
    extracted = []
    found_days = {_day_index_from_name(p.name) for p in files}
    wanted_days = set(int(d) for d in days) if days is not None else set(range(1, 15))
    missing_days = sorted(wanted_days - found_days - {None})
    if missing_days:
        extracted = extract_archive(
            dest_path, extract_dir, member_pattern=acfg["invocations_glob"], days=missing_days
        )
        files = find_invocation_files(extract_dir, acfg["invocations_glob"], days=days)
    if not files:
        raise FileNotFoundError(f"no invocation CSV files found after extraction in {extract_dir}")

    df, manifest = prepare_from_files(
        files,
        config,
        do_split=do_split,
        verify_info=verify_info,
        download_info=download_info,
        timeout_s=timeout_s,
    )
    manifest["extraction"] = {
        "archive": str(dest_path),
        "extracted_dir": str(extract_dir),
        "files_found": len(files),
        "files_extracted_this_run": len(extracted),
        "days_selected": days,
    }
    return df, manifest, {"download": download_info, "verify": verify_info, "files": [str(f) for f in files]}


def write_manifest(manifest: dict, path: str | Path) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)
    return str(p)


def write_prepared(df: pd.DataFrame, path: str | Path) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False)
    return str(p)


def load_prepared_as_trace(
    config=None,
    prepared_path=None,
    function_limit=None,
    require_simulated_resources=False,
):
    """Load a prepared Azure CSV as a trace-compatible frame.

    Real CPU/memory/latency/containers/cold-start/power are not in the Azure
    invocation trace. If require_simulated_resources=True, deterministic proxy
    columns are added and MUST be labeled simulated/estimated by callers.
    """
    acfg = default_azure_config(config)
    path = Path(prepared_path or acfg["processed_path"])
    if not path.exists():
        raise FileNotFoundError(f"prepared Azure CSV not found: {path}")
    df = pd.read_csv(path, parse_dates=["timestamp"])
    keep = ["timestamp", "function_id", "invocation_count"]
    for c in ("trigger", "day_index", "split"):
        if c in df.columns:
            keep.append(c)
    df = df[keep].sort_values(["timestamp", "function_id"], kind="stable").reset_index(drop=True)
    if function_limit is not None:
        funcs = sorted(df["function_id"].unique())[: int(function_limit)]
        df = df[df["function_id"].isin(funcs)].reset_index(drop=True)
    if require_simulated_resources:
        inv = df["invocation_count"].astype(float)
        norm = inv / (inv.max() if inv.max() > 0 else 1.0)
        df["cpu_utilization"] = (0.1 + 0.8 * norm).clip(0, 1)
        df["memory_utilization"] = (0.2 + 0.6 * norm).clip(0, 1)
        df["active_containers"] = (2 + np.ceil(norm * 8)).astype(int)
        df["warm_containers"] = (df["active_containers"] - (norm > 0.7).astype(int)).clip(lower=1)
        df["cold_starts"] = (norm > 0.7).astype(int)
        df["latency_ms"] = (50 + 200 * norm).round(3)
        df["p95_latency_ms"] = (80 + 250 * norm).round(3)
        df["power_w"] = (20 + 30 * norm).round(3)
        df["_resource_columns_simulated"] = True
    return df


def _load_cfg(path):
    if path:
        from configs import load_config

        return load_config(path)
    return None


def _cmd_inspect(args):
    print(json.dumps(inspect(_load_cfg(args.config)), indent=2))


def _cmd_verify(args):
    cfg = _load_cfg(args.config)
    acfg = default_azure_config(cfg)
    info = verify_asset(
        args.path, expected_sha256=args.sha256 or acfg.get("asset_sha256"), expected_size=args.size
    )
    print(json.dumps(info, indent=2))


def _cmd_download(args):
    cfg = _load_cfg(args.config)
    info = download_asset(cfg, dest=args.dest, resume=not args.no_resume)
    print(json.dumps(info, indent=2))


def _apply_cli_overrides(cfg, args):
    cfg = cfg or {}
    if getattr(args, "timeout_s", None) is not None:
        cfg = cfg or {}
        cfg.setdefault("data", {}).setdefault("azure", {})["timeout_s"] = args.timeout_s
    if getattr(args, "aggregate", None) or getattr(args, "top_k", None) is not None:
        cfg = json.loads(json.dumps(cfg, default=str))  # cheap deepcopy-safe for config dicts
        cfg.setdefault("data", {}).setdefault("azure", {})
        if getattr(args, "aggregate", None):
            cfg["data"]["azure"]["aggregate"] = args.aggregate
        if getattr(args, "top_k", None) is not None:
            cfg["data"]["azure"]["top_k"] = args.top_k
    return cfg


def _cmd_prepare(args):
    cfg = _apply_cli_overrides(_load_cfg(args.config), args)
    acfg = default_azure_config(cfg)
    if args.inputs:
        files = [Path(p) for p in args.inputs]
    else:
        src = Path(args.source_dir or acfg["extracted_dir"])
        files = find_invocation_files(src, acfg["invocations_glob"], days=args.days)
    if not files:
        raise SystemExit(f"no invocation CSV files found (inputs={args.inputs}, source_dir={args.source_dir})")
    df, manifest = prepare_from_files(
        files, cfg, do_split=not args.no_split, timeout_s=acfg.get("timeout_s")
    )
    out = Path(args.out or acfg["processed_path"])
    write_prepared(df, out)
    man_path = Path(args.manifest or acfg["manifest_path"])
    manifest["output"] = {"prepared_csv": str(out), "rows": int(len(df)), "columns": list(df.columns)}
    write_manifest(manifest, man_path)
    print(
        json.dumps(
            {
                "prepared_csv": str(out),
                "manifest": str(man_path),
                "rows": int(len(df)),
                "functions": int(df["function_id"].nunique()),
            },
            indent=2,
        )
    )


def _cmd_obtain(args):
    cfg = _apply_cli_overrides(_load_cfg(args.config), args)
    acfg = default_azure_config(cfg)
    df, manifest, info = obtain_official(
        cfg,
        dest=args.dest,
        source_dir=args.source_dir,
        days=args.days,
        do_split=not args.no_split,
        force_download=args.force_download,
        timeout_s=acfg.get("timeout_s"),
    )
    out = Path(args.out or acfg["processed_path"])
    write_prepared(df, out)
    man_path = Path(args.manifest or acfg["manifest_path"])
    manifest["output"] = {"prepared_csv": str(out), "rows": int(len(df)), "columns": list(df.columns)}
    write_manifest(manifest, man_path)
    print(
        json.dumps(
            {
                "prepared_csv": str(out),
                "manifest": str(man_path),
                "rows": int(len(df)),
                "functions": int(df["function_id"].nunique()),
                "files_prepared": len(info.get("files") or []),
                "verified_sha256_ok": (info.get("verify") or {}).get("sha256_ok"),
                "reused_existing": (info.get("download") or {}).get("reused_existing", False),
            },
            indent=2,
            default=str,
        )
    )


def main(argv=None):
    p = argparse.ArgumentParser(description="Azure Functions 2019 dataset pipeline utilities")
    p.add_argument("--config", default=None)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("inspect")
    s.set_defaults(func=_cmd_inspect)

    s = sub.add_parser("verify")
    s.add_argument("path")
    s.add_argument("--sha256", default=None)
    s.add_argument("--size", type=int, default=None)
    s.set_defaults(func=_cmd_verify)

    s = sub.add_parser("download")
    s.add_argument("--dest", default=None)
    s.add_argument("--no-resume", action="store_true")
    s.set_defaults(func=_cmd_download)

    s = sub.add_parser("prepare")
    s.add_argument("--inputs", nargs="*")
    s.add_argument("--source-dir", default=None)
    s.add_argument("--days", nargs="*", type=int, default=None)
    s.add_argument("--out", default=None)
    s.add_argument("--manifest", default=None)
    s.add_argument("--no-split", action="store_true")
    s.add_argument("--aggregate", default=None, help="aggregation mode: per_function|total|by_app|top_k_total")
    s.add_argument("--top-k", dest="top_k", type=int, default=None, help="top_k for top_k_total aggregation")
    s.add_argument("--timeout-s", dest="timeout_s", type=float, default=None, help="abort after N seconds")
    s.set_defaults(func=_cmd_prepare)

    s = sub.add_parser(
        "obtain",
        help="download/reuse, verify, extract, and prepare official Azure Functions 2019 trace",
    )
    s.add_argument("--dest", default=None, help="archive path (defaults to config data.azure.raw_dir/asset)")
    s.add_argument("--source-dir", default=None, help="extraction/output directory for CSVs")
    s.add_argument("--days", nargs="*", type=int, default=None, help="optional day indices to prepare (e.g. 1 2)")
    s.add_argument("--out", default=None, help="prepared CSV output path")
    s.add_argument("--manifest", default=None, help="manifest JSON output path")
    s.add_argument("--no-split", action="store_true")
    s.add_argument("--force-download", action="store_true", help="re-download even if archive exists")
    s.add_argument("--aggregate", default=None, help="aggregation mode: per_function|total|by_app|top_k_total")
    s.add_argument("--top-k", dest="top_k", type=int, default=None, help="top_k for top_k_total aggregation")
    s.add_argument("--timeout-s", dest="timeout_s", type=float, default=None, help="abort after N seconds")
    s.set_defaults(func=_cmd_obtain)

    args = p.parse_args(argv)
    watchdog = None
    timeout_s = getattr(args, "timeout_s", None)
    if timeout_s is not None and float(timeout_s) > 0:
        watchdog = threading.Timer(
            float(timeout_s),
            lambda: os._exit(124),
        )
        watchdog.daemon = True
        watchdog.start()
    try:
        return args.func(args)
    except TimeoutError as exc:
        raise SystemExit(f"ERROR: {exc}") from None
    finally:
        if watchdog is not None:
            watchdog.cancel()


if __name__ == "__main__":
    main()
