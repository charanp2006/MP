import numpy as np
import pandas as pd


def sample_trace(
    days=7,
    functions=("fn_checkout", "fn_search", "fn_recommend"),
    seed=42,
    start="2026-01-05",
    freq="30s",
):
    rng = np.random.default_rng(seed)
    steps_per_day = int(pd.Timedelta("1D") / pd.Timedelta(freq))
    periods = int(days * steps_per_day)
    index = pd.date_range(start=start, periods=periods, freq=freq)

    hour = index.hour + index.minute / 60.0
    weekday = (index.dayofweek < 5).astype(float)
    daily = 0.5 + 0.5 * np.sin(2 * np.pi * (hour - 14) / 24.0)
    weekly = np.where(weekday > 0, 1.0, 0.72)
    shape = daily * weekly

    bases = [420.0, 265.0, 150.0]
    frames = []
    for position, function_id in enumerate(functions):
        base = bases[position % len(bases)]
        noise = rng.normal(0.0, 0.07, periods)
        demand = np.clip(base * shape * (1.0 + noise), 0.0, None)
        scale = demand / max(base, 1.0)

        frame = pd.DataFrame(
            {
                "timestamp": index,
                "function_id": function_id,
                "invocation_count": np.rint(demand).astype(int),
                "execution_duration_ms": np.clip(
                    28.0 + 22.0 * scale + rng.normal(0.0, 3.0, periods), 4.0, None
                ),
                "cpu_utilization": np.clip(
                    0.18 + 0.55 * scale + rng.normal(0.0, 0.04, periods), 0.01, 0.98
                ),
                "memory_utilization": np.clip(
                    0.22 + 0.42 * scale + rng.normal(0.0, 0.04, periods), 0.01, 0.98
                ),
                "active_containers": np.maximum(
                    1, np.rint(2.0 + 12.0 * scale).astype(int)
                ),
                "warm_containers": np.maximum(
                    0, np.rint(1.0 + 9.0 * scale).astype(int)
                ),
                "cold_starts": np.maximum(
                    0, np.rint(rng.normal(1.4, 1.4, periods) * scale).astype(int)
                ),
                "latency_ms": np.clip(
                    120.0 + 70.0 * scale + rng.normal(0.0, 12.0, periods), 40.0, None
                ),
            }
        )
        frame["p95_latency_ms"] = frame["latency_ms"] * (1.12 + 0.10 * scale)
        frame["power_w"] = 45.0 + 120.0 * scale + rng.normal(0.0, 4.0, periods)
        frames.append(frame)

    trace = pd.concat(frames, ignore_index=True)
    return trace.sort_values(["function_id", "timestamp"]).reset_index(drop=True)
