"""Append-only audit log for executor operations (M6)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from orchestrator.decision_log import sanitize_record

SCHEMA_VERSION = 1


class ExecutionAuditLogger:
    """Record fixed, bounded platform operations before and after execution."""

    def __init__(self, config: Optional[Dict] = None, path: Optional[str] = None) -> None:
        config = config or {}
        execution = config.get("execution", {})
        self.enabled = bool(execution.get("audit_enabled", True))
        self.path = path or execution.get("audit_path", "results/execution/audit.jsonl")

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

    def log(self, execution: Dict, context: Optional[Dict] = None) -> Optional[str]:
        if not self.enabled:
            return None
        record = {
            "correlation_id": (context or {}).get("correlation_id", ""),
            "final_action": (context or {}).get("final_action_name", ""),
            "authorized": bool((context or {}).get("authorized", False)),
            "backend": execution.get("backend", "unspecified"),
            "operation": execution.get("operation", "none"),
            "target_capacity": int(execution.get("target_capacity", 0)),
            "code": execution.get("code", ""),
            "reason": execution.get("reason", ""),
            "dry_run": bool(execution.get("dry_run", True)),
            "executed": bool(execution.get("executed", False)),
            "ok": bool(execution.get("ok", False)),
            "commands": execution.get("commands", []),
            "context": context or {},
            "audit_schema_version": SCHEMA_VERSION,
            "logged_at": datetime.now(timezone.utc).isoformat(),
        }
        path = Path(self.path)
        os.makedirs(path.parent or ".", exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(sanitize_record(record), sort_keys=True, default=str) + "\n")
        return str(path)
