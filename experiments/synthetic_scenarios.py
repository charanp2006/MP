"""Deterministic synthetic workload scenarios for PPO evaluation (M5).

These traces are simulated. They exercise lifecycle delay, bursts and SLA stress
but are not measurements from a live system.
"""

from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

SCENARIO_NAMES = ("ramp", "burst", "periodic", "sparse", "stress", "mixed")


def _frame(steps: int, workload: np.ndarray, seed: int, name: str) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    workload = np.asarray(workload, dtype=float)
    peak = max(float(np.max(workload)), 1.0)
    noise = rng.normal(0.0, 0.02 * peak, size=steps)
    workload = np.clip(workload + noise, 1.0, None)
    cpu = np.clip(workload / peak, 0.0, 1.0)
    memory = np.clip(0.25 + 0.6 * cpu + rng.normal(0.0, 0.02, size=steps), 0.0, 1.0)
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=steps, freq="h", tz="UTC"),
            "invocation_count": workload,
            "cpu_utilization": cpu,
            "memory_utilization": memory,
            "scenario": name,
        }
    )


def generate_scenarios(steps: int = 72, seed: int = 42) -> Dict[str, pd.DataFrame]:
    """Return six deterministic synthetic fleet timelines."""
    t = np.arange(steps, dtype=float)
    base = 500.0

    ramp = base + 12.0 * t
    burst = base + 900.0 * ((t % 18) < 3)
    periodic = base + 450.0 * np.sin(2 * np.pi * t / 24.0) ** 2
    sparse = base * (0.25 + 2.5 * ((t % 11) == 0))
    stress = 1600.0 + 300.0 * np.sin(t / 4.0)
    mixed = base + 400.0 * np.sin(2 * np.pi * t / 24.0) + 700.0 * ((t % 20) < 2)

    return {
        "ramp": _frame(steps, ramp, seed + 1, "ramp"),
        "burst": _frame(steps, burst, seed + 2, "burst"),
        "periodic": _frame(steps, periodic, seed + 3, "periodic"),
        "sparse": _frame(steps, sparse, seed + 4, "sparse"),
        "stress": _frame(steps, stress, seed + 5, "stress"),
        "mixed": _frame(steps, mixed, seed + 6, "mixed"),
    }
