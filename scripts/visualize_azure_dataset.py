from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Visualize a prepared Azure Functions 2019 invocation CSV and manifest")
    p.add_argument("--csv", required=True, help="prepared CSV (output of data.azure_functions_2019 prepare)")
    p.add_argument("--manifest", default=None, help="optional manifest JSON")
    p.add_argument("--out-dir", default="results/plots/azure", help="output directory for plots")
    args = p.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.csv, parse_dates=["timestamp"])
    manifest = None
    if args.manifest and Path(args.manifest).exists():
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))

    # Coverage / missingness (function x time completeness)
    n_func = df["function_id"].nunique() if "function_id" in df else 0
    n_ts = df["timestamp"].nunique() if "timestamp" in df else 0
    expected = n_func * n_ts
    observed = len(df)
    missing_intervals = max(expected - observed, 0)

    # Aggregate workload over time (all functions)
    by_ts = df.groupby("timestamp", as_index=False)["invocation_count"].sum().sort_values("timestamp")
    by_func = df.groupby("function_id")["invocation_count"].sum().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(by_ts["timestamp"], by_ts["invocation_count"], lw=1)
    ax.set_title("Total invocations over time (prepared trace)")
    ax.set_xlabel("time (UTC, relative-day base)")
    ax.set_ylabel("invocation_count (sum per interval)")
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out_dir / "total_invocations_over_time.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(df["invocation_count"], bins=50)
    ax.set_title("Invocation count distribution (per function-interval)")
    ax.set_xlabel("invocation_count")
    ax.set_ylabel("frequency")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "invocation_distribution.png", dpi=150)
    plt.close(fig)

    # Daily pattern by hour-of-day (from timestamp)
    tmp = df.copy()
    tmp["hour"] = tmp["timestamp"].dt.hour
    hourly = tmp.groupby("hour")["invocation_count"].mean()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(hourly.index.astype(int), hourly.values)
    ax.set_title("Mean invocations by hour of day")
    ax.set_xlabel("hour (UTC)")
    ax.set_ylabel("mean invocation_count")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "hourly_pattern.png", dpi=150)
    plt.close(fig)

    # Top functions / peaks
    top = by_func.head(20)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(range(len(top)), top.values)
    ax.set_title("Top functions by total invocations")
    ax.set_xlabel("function rank")
    ax.set_ylabel("total invocation_count")
    ax.set_xticks([])
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "top_functions.png", dpi=150)
    plt.close(fig)

    # Split boundaries (if present)
    if "split" in df.columns:
        split_ts = df.groupby("split")["timestamp"].agg(["min", "max", "count"]).reset_index()
        fig, ax = plt.subplots(figsize=(10, 3))
        colors = {"train": "tab:blue", "val": "tab:orange", "test": "tab:green"}
        for _, row in split_ts.iterrows():
            ax.hlines(1, row["min"], row["max"], colors=colors.get(row["split"], "gray"), lw=10, label=row["split"])
        ax.set_title("Chronological split boundaries (by timestamp range)")
        ax.set_yticks([])
        ax.legend(loc="upper right")
        ax.grid(True, axis="x", alpha=0.3)
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig(out_dir / "split_boundaries.png", dpi=150)
        plt.close(fig)

    summary = {
        "csv": str(args.csv),
        "rows": int(len(df)),
        "functions": int(n_func),
        "unique_timestamps": int(n_ts),
        "expected_rows_function_x_time": int(expected),
        "observed_rows": int(observed),
        "missing_intervals_function_x_time": int(missing_intervals),
        "start": str(df["timestamp"].min()) if len(df) else None,
        "end": str(df["timestamp"].max()) if len(df) else None,
        "invocation_count_min": int(df["invocation_count"].min()) if len(df) else None,
        "invocation_count_max": int(df["invocation_count"].max()) if len(df) else None,
        "invocation_count_mean": float(df["invocation_count"].mean()) if len(df) else None,
        "plots": sorted([p.name for p in out_dir.glob("*.png")]),
        "manifest_cleaning": (manifest or {}).get("cleaning"),
        "manifest_split": (manifest or {}).get("split"),
    }
    (out_dir / "visualization_summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
