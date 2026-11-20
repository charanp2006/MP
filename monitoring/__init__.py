"""Monitoring / feedback / experiments (P5)."""

from typing import Any

__all__ = [
    "MetricsCollector",
    "export_prometheus_text",
    "FeedbackLoop",
    "AlertManager",
    "PrometheusMetricsAdapter",
    "run_baseline_vs_proposed",
    "ablation_remove_planner",
    "run_experiments_main",
]

_EXPORTS = {
    "MetricsCollector": ("monitoring.metrics", "MetricsCollector"),
    "export_prometheus_text": ("monitoring.metrics", "export_prometheus_text"),
    "FeedbackLoop": ("monitoring.feedback", "FeedbackLoop"),
    "AlertManager": ("monitoring.alerts", "AlertManager"),
    "PrometheusMetricsAdapter": ("monitoring.prometheus_adapter", "PrometheusMetricsAdapter"),
    "run_baseline_vs_proposed": ("experiments.run_experiments", "run_baseline_vs_proposed"),
    "ablation_remove_planner": ("experiments.run_experiments", "ablation_remove_planner"),
    "run_experiments_main": ("experiments.run_experiments", "main"),
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import importlib

    module_name, attribute = _EXPORTS[name]
    value = getattr(importlib.import_module(module_name), attribute)
    globals()[name] = value
    return value
