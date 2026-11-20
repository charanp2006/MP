import json
from pathlib import Path

import numpy as np
import pandas as pd

from experiments.evaluate_m8 import _RulePolicy, _config_hash, evaluate_m8
from rl.environment import NOOP, SCALE_IN, SCALE_OUT


class _FixedPolicy:
    def greedy_action(self, _obs):
        return NOOP


def test_rule_policy_bounds_actions():
    policy = _RulePolicy()

    assert policy.greedy_action(np.array([0.5, 0.5, 0.5, 0.5, 0.5, 1.0, 0.2, 0.0, 0.5, -0.1])) == SCALE_OUT
    assert policy.greedy_action(np.array([0.5, 0.5, 0.3, 0.3, 0.3, 0.3, 0.9, 0.0, 0.4, 0.7])) == SCALE_IN
    assert policy.greedy_action(np.array([0.5, 0.5, 0.4, 0.4, 0.4, 0.4, 0.4, 0.0, 0.4, 0.6])) == NOOP


def test_evaluate_m8_writes_reproducible_artifacts(tmp_path, test_config):
    result = evaluate_m8(
        test_config,
        tmp_path,
        seeds=[42],
        steps=3,
        scenarios=["mixed"],
        disable_tft=True,
        policy_checkpoint=None,
        policy=_FixedPolicy(),
    )
    output = Path(result["report"]).parent
    manifest = json.loads((output / "run_manifest.json").read_text(encoding="utf-8"))
    runs = pd.read_csv(output / "runs.csv")
    aggregates = pd.read_csv(output / "aggregates.csv")
    report = (output / "report.md").read_text(encoding="utf-8")

    assert manifest["config_sha256"] == _config_hash(test_config)
    assert manifest["evidence_tier"] == "simulated"
    assert len(runs) == 7
    assert set(aggregates["experiment_id"]) == {f"E{i}" for i in range(8)}
    assert "not_run_requires_live_cluster" in set(aggregates["status"].astype(str))
    assert "simulated closed-loop replay" in report.lower()
    assert all(Path(path).exists() for path in result["figures"])
    assert (output / "workloads.json").exists()
    assert (output / "runs" / "E0" / "mixed" / "seed_42" / "decision.jsonl").exists()


def test_evaluate_m8_marks_tft_fallback_when_checkpoint_missing(tmp_path, test_config):
    result = evaluate_m8(
        test_config,
        tmp_path,
        seeds=[42],
        steps=2,
        scenarios=["burst"],
        disable_tft=True,
        policy_checkpoint=None,
        policy=_FixedPolicy(),
    )
    runs = pd.read_csv(result["runs"])

    tft_rows = runs[runs["forecast"] == "tft"]
    assert not tft_rows.empty
    assert all(str(value).startswith("degraded_tft_fallback") for value in tft_rows["status"])
