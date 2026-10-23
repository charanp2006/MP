import copy

import pytest

from configs import load_config


@pytest.fixture(scope="session")
def _config_template():
    config = load_config()
    config["data"]["sample_days"] = 1
    config["data"]["seed"] = 7
    config["features"]["rolling_windows"] = [5, 10]
    config["forecast"]["training"]["epochs"] = 1
    config["control"]["rl"]["training"]["episodes"] = 2
    return config


@pytest.fixture
def test_config(_config_template):
    return copy.deepcopy(_config_template)


@pytest.fixture(scope="session")
def processed_frame(_config_template):
    """A small preprocessed + feature-engineered frame (1 synthetic day)."""
    from data.pipeline import run

    frame, _ = run(config=copy.deepcopy(_config_template))
    return frame


@pytest.fixture
def state_factory():
    """Build a valid StateSnapshot with sensible defaults."""
    from agent.schemas import StateSnapshot

    def _make(**overrides):
        base = dict(
            forecast_workload=600.0,
            forecast_peak=620.0,
            current_workload=600.0,
            trend="stable",
            cpu_utilization=0.5,
            memory_utilization=0.5,
            active_containers=8,
            p95_latency_ms=120.0,
            cold_start_rate=0.02,
            energy=100.0,
            sla_threshold_ms=250.0,
            sla_margin_ms=130.0,
            forecast_horizon=5,
        )
        base.update(overrides)
        return StateSnapshot(**base)

    return _make


@pytest.fixture
def metrics_factory():
    """Build a metrics mapping for the state builder / decision loop."""

    def _make(**overrides):
        base = dict(
            current_workload=600.0,
            cpu_utilization=0.5,
            memory_utilization=0.5,
            active_containers=8,
            p95_latency_ms=120.0,
            cold_starts=1.0,
            energy=100.0,
        )
        base.update(overrides)
        return base

    return _make
