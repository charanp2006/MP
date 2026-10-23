from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from configs import load_config
from data.feature_engineering import build_features
from data.ingestion import load_trace, summarize_trace
from data.preprocessing import preprocess


def run(config: dict | None = None, config_path: str | None = None) -> tuple[pd.DataFrame, dict]:
    config = config if config is not None else load_config(config_path)

    raw = load_trace(config)
    ingest_summary = summarize_trace(raw)

    clean, preprocess_report = preprocess(raw, config)
    features, feature_report = build_features(clean, config)

    report = {
        "ingest": ingest_summary,
        "preprocess": preprocess_report,
        "features": feature_report,
    }
    return features, report


def save_features(frame: pd.DataFrame, config: dict) -> str:
    processed_path = Path(config.get("data", {}).get("processed_path", "data/processed/features.csv"))
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(processed_path, index=False)
    return str(processed_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the workload data pipeline (ingest -> preprocess -> features)"
    )
    parser.add_argument("--config", default=None, help="path to project.yaml")
    parser.add_argument("--save", action="store_true", help="write features CSV to data.processed_path")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    features, report = run(config=config)

    if args.save:
        report["saved_to"] = save_features(features, config)

    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
