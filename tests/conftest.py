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
