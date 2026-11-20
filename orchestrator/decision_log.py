"""Append-only JSONL audit log for complete decision provenance (M5)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from agent.telemetry import redact_text

SCHEMA_VERSION = 1


def sanitize_record(value):
    if isinstance(value, dict):
        return {str(key): sanitize_record(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize_record(item) for item in value]
    if isinstance(value, str):
        return redact_text(value, max_chars=1000)
    return value


class DecisionLogger:
    """Write one redacted JSON record per decision step."""

    def __init__(self, config: Optional[Dict] = None, path: Optional[str] = None) -> None:
        config = config or {}
        log_cfg = config.get("decision_log", {})
        self.enabled = bool(log_cfg.get("enabled", True))
        self.path = path or log_cfg.get("path", "results/decision/decisions.jsonl")

    def reset(self) -> None:
        if not self.enabled:
            return
        path = Path(self.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")

    def read_records(self) -> List[Dict]:
        path = Path(self.path)
        if not path.exists():
            return []
        records: List[Dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if isinstance(record, dict):
                records.append(record)
        return records

    def log(self, decision, outcome: Optional[Dict] = None) -> Optional[str]:
        if not self.enabled:
            return None
        record = decision.to_dict() if hasattr(decision, "to_dict") else dict(decision)
        if outcome is not None:
            record["outcome"] = outcome
        record["log_schema_version"] = SCHEMA_VERSION
        record["logged_at"] = datetime.now(timezone.utc).isoformat()
        clean = sanitize_record(record)

        path = Path(self.path)
        os.makedirs(path.parent or ".", exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(clean, sort_keys=True, default=str) + "\n")
        return str(path)
