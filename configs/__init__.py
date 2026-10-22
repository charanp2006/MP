from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = ROOT / "configs" / "project.yaml"


def load_config(path=None):
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError(f"config must be a mapping: {config_path}")
    return config
