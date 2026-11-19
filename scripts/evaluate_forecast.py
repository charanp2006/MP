"""Train/evaluate the TFT forecaster and baselines with saved artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from configs import load_config
from data.pipeline import run as run_pipeline
from forecasting.evaluation import run_forecast_evaluation


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate TFT against forecast baselines")
    parser.add_argument("--config", default=None, help="Path to project.yaml")
    parser.add_argument("--data-source", default=None, help="Override data.source")
    parser.add_argument("--source-path", default=None, help="Override data.source_path")
    parser.add_argument("--out-dir", default="results/forecast", help="Artifact output directory")
    parser.add_argument("--run-id", default="forecast_run", help="Run identifier")
    parser.add_argument("--epochs", type=int, default=None, help="Override forecast.training.epochs")
    parser.add_argument("--dataset-sha256", default=None, help="Recorded dataset hash")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.data_source:
        config["data"]["source"] = args.data_source
    if args.source_path:
        config["data"]["source_path"] = args.source_path
    if args.epochs is not None:
        config["forecast"]["training"]["epochs"] = args.epochs

    frame, pipeline_report = run_pipeline(config=config)
    result = run_forecast_evaluation(
        frame,
        config,
        run_id=args.run_id,
        out_dir=args.out_dir,
        dataset_sha256=args.dataset_sha256,
    )
    print(
        json.dumps(
            {
                "run_id": result["run_id"],
                "commit": result["commit"],
                "models": {
                    name: values["overall"] for name, values in result["models"].items()
                },
                "interval": result["interval"],
                "artifacts": result["artifacts"],
                "pipeline_rows": pipeline_report["features"]["rows_out"],
            },
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
