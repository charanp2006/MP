from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

import pandas as pd

from experiments.synthetic_scenarios import SCENARIO_NAMES, generate_scenarios

PAYLOAD_CLASSES = {
    "small": {"weight": 0.65, "duration_ms": 22.0},
    "medium": {"weight": 0.28, "duration_ms": 58.0},
    "large": {"weight": 0.07, "duration_ms": 145.0},
}


def _scenario_shape(scenario: str, steps: int, seed: int) -> list[float]:
    frames = generate_scenarios(steps=steps, seed=seed)
    frame = frames.get(scenario)
    if frame is None:
        raise ValueError(f"unknown scenario: {scenario}; expected one of {SCENARIO_NAMES}")
    return [float(value) for value in frame["invocation_count"].tolist()]


def generate_events(
    scenario: str = "mixed",
    steps: int = 24,
    interval_s: int = 60,
    rate_per_interval: int = 120,
    seed: int = 42,
    services: list[str] | None = None,
    payload_classes: list[str] | None = None,
    burst_multiplier: float = 2.5,
    error_rate: float = 0.01,
) -> list[dict]:
    if steps <= 0:
        raise ValueError("steps must be positive")
    if interval_s <= 0:
        raise ValueError("interval_s must be positive")
    if rate_per_interval <= 0:
        raise ValueError("rate_per_interval must be positive")
    if not 0.0 <= error_rate < 1.0:
        raise ValueError("error_rate must be in [0, 1)")

    selected_services = services or ["fn_checkout", "fn_search", "fn_recommend"]
    if not selected_services:
        raise ValueError("services must not be empty")
    selected_payloads = payload_classes or list(PAYLOAD_CLASSES)
    invalid_payloads = [name for name in selected_payloads if name not in PAYLOAD_CLASSES]
    if invalid_payloads:
        raise ValueError(f"unknown payload classes: {invalid_payloads}")

    rng = random.Random(seed)
    shape = _scenario_shape(scenario, steps, seed)
    peak = max(shape) or 1.0
    start = datetime(2026, 1, 5, tzinfo=timezone.utc)
    weights = [PAYLOAD_CLASSES[name]["weight"] for name in selected_payloads]

    events: list[dict] = []
    for step, value in enumerate(shape):
        scale = value / peak
        multiplier = burst_multiplier if scenario == "burst" and scale > 0.7 else 1.0
        count = int(round(rate_per_interval * scale * multiplier))
        window_start = start + timedelta(seconds=step * interval_s)
        window_ms = interval_s * 1000
        for index in range(count):
            service_id = rng.choice(selected_services)
            payload_class = rng.choices(selected_payloads, weights=weights, k=1)[0]
            base_duration = PAYLOAD_CLASSES[payload_class]["duration_ms"]
            duration_ms = max(1.0, rng.gauss(base_duration, base_duration * 0.18))
            error_count = 1 if rng.random() < error_rate else 0
            timestamp = window_start + timedelta(milliseconds=rng.randrange(window_ms))
            events.append(
                {
                    "request_id": f"req-{seed}-{step:04d}-{index:05d}",
                    "timestamp": timestamp.isoformat(),
                    "service_id": service_id,
                    "function_id": service_id,
                    "payload_class": payload_class,
                    "invocation_count": 1,
                    "execution_duration_ms": round(duration_ms, 3),
                    "error_count": error_count,
                    "source": "synthetic_client",
                    "scenario": scenario,
                }
            )
    return sorted(events, key=lambda event: event["timestamp"])


def replay_events(events: list[dict]):
    for event in sorted(events, key=lambda item: item["timestamp"]):
        yield event
