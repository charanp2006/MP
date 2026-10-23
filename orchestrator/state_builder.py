"""State builder (architecture Layer 4, docs/architecture.md section 6).

Combines the TFT forecast with the current observation into the single
:class:`StateSnapshot` consumed by the planner and, later, the controller.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from agent.schemas import StateSnapshot
from forecasting.inference import classify_trend

_TRENDS = {"increasing", "decreasing", "stable"}


def build_state(
    forecast: Mapping[str, Any],
    metrics: Mapping[str, Any],
    config: Optional[Dict] = None,
    metadata: Optional[Mapping[str, Any]] = None,
) -> StateSnapshot:
    """Build and validate a state snapshot.

    ``forecast`` is the output of ``forecasting.inference.forecast``;
    ``metrics`` holds the current observation (workload, CPU, memory, P95,
    cold starts, energy, active containers).
    """
    config = config or {}
    sla_threshold = float(config.get("sla", {}).get("p95_latency_ms", 250.0))

    predicted = list(forecast.get("predicted_workload", []))
    if not predicted:
        raise ValueError("forecast must contain a non-empty 'predicted_workload'")
    predicted = [max(float(value), 0.0) for value in predicted]

    if "current_workload" not in metrics:
        raise ValueError("metrics must contain 'current_workload'")

    current = max(float(metrics["current_workload"]), 0.0)
    p95 = float(metrics.get("p95_latency_ms", metrics.get("p95_latency", 0.0)))

    if "cold_start_rate" in metrics:
        cold_rate = float(metrics["cold_start_rate"])
    else:
        cold_rate = float(metrics.get("cold_starts", 0.0)) / max(current, 1.0)
    cold_rate = min(max(cold_rate, 0.0), 1.0)

    trend = forecast.get("trend")
    if trend not in _TRENDS:
        trend = classify_trend(predicted)

    raw_metadata: Dict[str, Any] = {}
    raw_metadata.update(metrics.get("metadata", {}) or {})
    raw_metadata.update(metadata or {})
    clean_metadata = {str(key): str(value) for key, value in raw_metadata.items()}

    return StateSnapshot(
        forecast_workload=predicted[0],
        forecast_peak=max(predicted),
        current_workload=current,
        trend=trend,
        cpu_utilization=min(max(float(metrics.get("cpu_utilization", 0.0)), 0.0), 1.0),
        memory_utilization=min(max(float(metrics.get("memory_utilization", 0.0)), 0.0), 1.0),
        active_containers=max(int(metrics.get("active_containers", 0)), 0),
        p95_latency_ms=max(p95, 0.0),
        cold_start_rate=cold_rate,
        energy=max(float(metrics.get("energy", 0.0)), 0.0),
        sla_threshold_ms=sla_threshold,
        sla_margin_ms=sla_threshold - max(p95, 0.0),
        forecast_horizon=max(int(forecast.get("forecast_horizon", len(predicted))), 1),
        metadata=clean_metadata,
    )


def metrics_from_step(info: Mapping[str, Any], cpu_utilization: float = 0.0, memory_utilization: float = 0.0) -> Dict[str, Any]:
    """Build the metrics mapping from an environment ``step`` info dict."""
    return {
        "current_workload": float(info.get("workload", 0.0)),
        "cpu_utilization": float(cpu_utilization),
        "memory_utilization": float(memory_utilization),
        "active_containers": int(info.get("capacity", 0)),
        "p95_latency_ms": float(info.get("p95_latency", 0.0)),
        "cold_starts": float(info.get("cold_starts", 0.0)),
        "energy": float(info.get("energy", 0.0)),
    }
