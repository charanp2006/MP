import json
from pathlib import Path

import pandas as pd
import pytest

from data import ingestion
from data.azure_functions_2019 import (
    DAY1_BASE_UTC,
    add_split_labels_by_time,
    build_manifest,
    chronological_split_indices,
    clean_long,
    inspect,
    load_prepared_as_trace,
    parse_invocation_csv,
    prepare_from_files,
    reshape_invocations_long,
    validate_invocation_schema,
    write_manifest,
    write_prepared,
)


FIXTURE_DIR = Path("tests/fixtures")
D01 = FIXTURE_DIR / "azure_functions_2019_invocations_d01_sample.csv"
D02 = FIXTURE_DIR / "azure_functions_2019_invocations_d02_sample.csv"


def test_inspect_metadata_contains_required_fields():
    info = inspect()
    assert info["dataset"] == "azurefunctions-dataset-2019"
    assert info["license"] == "CC-BY-4.0"
    assert info["asset_name"].endswith(".tar.xz")
    assert info["asset_sha256"].startswith("aff8")
    assert "invocation count per minute" in info["semantics"]["unit"]
    assert any("simulated/estimated" in lim.lower() for lim in info["limitations"])


def test_parse_and_schema_validation():
    df = parse_invocation_csv(D01)
    assert "_day_index" in df.columns and int(df["_day_index"].iloc[0]) == 1
    validate_invocation_schema(df)
    bad = df.drop(columns=["Trigger"])
    with pytest.raises(ValueError, match="missing required columns"):
        validate_invocation_schema(bad)


def test_reshape_counts_and_timestamps():
    raw = parse_invocation_csv(D01)
    long = reshape_invocations_long(raw, interval_seconds=60)
    assert set(["timestamp", "function_id", "invocation_count"]).issubset(long.columns)
    assert long["invocation_count"].ge(0).all()
    # 3 functions * 1440 minutes
    assert len(long) == 3 * 1440
    # known non-zero slots for f1 at minutes 61-65 (1-indexed in source)
    f1 = long[long["function_id"].str.endswith("|f1")].sort_values("timestamp").reset_index(drop=True)
    assert f1.loc[60, "invocation_count"] == 5
    assert f1.loc[61, "invocation_count"] == 10
    assert f1.loc[62, "invocation_count"] == 3
    assert str(f1.loc[0, "timestamp"]) == str(pd.Timestamp(DAY1_BASE_UTC))


def test_clean_detects_duplicates_and_is_monotonic():
    raw = parse_invocation_csv(D01)
    long = reshape_invocations_long(raw, interval_seconds=60)
    duped = pd.concat([long, long.head(5)], ignore_index=True)
    clean, report = clean_long(duped)
    assert report["duplicate_key_rows"] > 0
    assert report["duplicates_resolved"] is True
    assert report["monotonic_per_function"] is True
    assert not clean.duplicated(subset=["timestamp", "function_id"]).any()


def test_clean_rejects_invalid_and_negative_values():
    raw = parse_invocation_csv(D01)
    long = reshape_invocations_long(raw, interval_seconds=60)
    bad_neg = long.copy()
    bad_neg.loc[0, "invocation_count"] = -1
    with pytest.raises(ValueError, match="negative"):
        clean_long(bad_neg)
    bad_num = long.copy().astype({"invocation_count": object})
    bad_num.loc[0, "invocation_count"] = "oops"
    with pytest.raises(ValueError, match="invalid"):
        clean_long(bad_num)


def test_chronological_split_no_overlap_and_ordered():
    idx = chronological_split_indices(10, [0.7, 0.15, 0.15])
    assert idx["train"] == (0, 7)
    assert idx["val"][0] == idx["train"][1]
    assert idx["test"][0] == idx["val"][1]
    assert idx["test"][1] == 10
    raw = parse_invocation_csv(D01)
    long = reshape_invocations_long(raw, interval_seconds=60)
    labeled, report = add_split_labels_by_time(long, [0.7, 0.15, 0.15])
    # each timestamp assigned to exactly one split
    per_ts = labeled.groupby("timestamp")["split"].nunique()
    assert (per_ts == 1).all()
    b = report["boundaries"]
    assert b["train"]["end_index"] == b["val"]["start_index"]
    assert b["val"]["end_index"] == b["test"]["start_index"]


def test_prepare_writes_manifest_and_csv(tmp_path):
    out_csv = tmp_path / "prepared.csv"
    out_manifest = tmp_path / "manifest.json"
    df, manifest = prepare_from_files([D01, D02], config=None, do_split=True)
    write_prepared(df, out_csv)
    manifest["output"] = {"prepared_csv": str(out_csv), "rows": int(len(df))}
    write_manifest(manifest, out_manifest)

    assert out_csv.exists() and out_manifest.exists()
    saved = json.loads(out_manifest.read_text(encoding="utf-8"))
    assert saved["dataset"] == "azurefunctions-dataset-2019"
    assert saved["source"]["license"] == "CC-BY-4.0"
    assert "files" in saved and len(saved["files"]) == 2
    assert "sha256" in saved["files"][0]
    assert "cleaning" in saved and saved["cleaning"]["monotonic_per_function"] is True
    assert "split" in saved and "boundaries" in saved["split"]
    assert "units" in saved and "assumptions" in saved
    # prepared spans 2 days * 1440 minutes * 3 functions
    assert len(pd.read_csv(out_csv)) == 2 * 1440 * 3


def test_load_prepared_as_trace_and_ingestion_integration(tmp_path):
    df, _ = prepare_from_files([D01, D02], config=None, do_split=True)
    prepared = tmp_path / "azure_features.csv"
    write_prepared(df, prepared)

    trace = load_prepared_as_trace(prepared_path=prepared)
    assert {"timestamp", "function_id", "invocation_count"}.issubset(trace.columns)
    assert not trace[["timestamp", "function_id", "invocation_count"]].isna().any().any()

    cfg = {
        "data": {
            "source": "azure_functions_2019",
            "azure": {"processed_path": str(prepared), "simulate_resources": False},
        }
    }
    loaded = ingestion.load_trace(cfg)
    ingestion.validate_trace(loaded)
    assert loaded["invocation_count"].ge(0).all()
    assert loaded["function_id"].nunique() == 3
