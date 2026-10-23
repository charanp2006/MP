import pandas as pd
import pytest

from data.ingestion import TraceValidationError, summarize_trace, validate_trace


def make_frame(**overrides):
    base = {
        "timestamp": ["2026-01-05T10:00:00", "2026-01-05T10:01:00"],
        "function_id": ["fn_a", "fn_a"],
        "invocation_count": [10, 20],
    }
    base.update(overrides)
    return pd.DataFrame(base)


def test_valid_frame_passes():
    out = validate_trace(make_frame())
    assert pd.api.types.is_datetime64_any_dtype(out["timestamp"])
    assert out["function_id"].astype(str).tolist() == ["fn_a", "fn_a"]


def test_missing_required_column_raises():
    frame = make_frame().drop(columns=["invocation_count"])
    with pytest.raises(TraceValidationError, match="invocation_count"):
        validate_trace(frame)


def test_missing_function_id_raises():
    frame = make_frame().drop(columns=["function_id"])
    with pytest.raises(TraceValidationError, match="function_id"):
        validate_trace(frame)


def test_unparseable_timestamp_raises():
    frame = make_frame(timestamp=["not-a-timestamp", "2026-01-05T10:01:00"])
    with pytest.raises(TraceValidationError, match="timestamp"):
        validate_trace(frame)


def test_non_numeric_invocation_raises():
    frame = make_frame(invocation_count=["10", "twenty"])
    with pytest.raises(TraceValidationError, match="invocation_count"):
        validate_trace(frame)


def test_summarize_trace_reports_normative_columns():
    summary = summarize_trace(validate_trace(make_frame()))
    assert summary["rows"] == 2
    assert summary["functions"] == ["fn_a"]
    assert "invocation_count" in summary["normative_present"]
    assert "cpu_utilization" in summary["normative_missing"]
