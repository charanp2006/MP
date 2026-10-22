"""Reactive autoscaling baseline (agreed implementation step 2).

A simple utilization-threshold rule used as the comparison baseline for the
learned PPO controller (docs/test_plan.md experiment baselines). It reacts to
the *current* CPU only, with no forecasting:

* CPU above ``scale_up_threshold``  -> reuse a warm container if one is idle,
  otherwise scale out.
* CPU below ``scale_down_threshold`` -> terminate an idle warm container if
  present, otherwise scale in.
* Otherwise                          -> no-op.

The environment clamps every action to the configured capacity bounds, so the
baseline cannot violate R02 by construction.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from rl.environment import NOOP, REUSE, SCALE_IN, SCALE_OUT, TERMINATE


class ReactiveAutoscaler:
    def __init__(self, config: Dict) -> None:
        baseline = config.get("baseline", {})
        self.scale_up_threshold = float(baseline.get("scale_up_threshold", 0.7))
        self.scale_down_threshold = float(baseline.get("scale_down_threshold", 0.3))

    def select_action(self, env, obs: np.ndarray) -> int:
        cpu = float(obs[2])
        warm = getattr(env, "warm", 0)

        if cpu > self.scale_up_threshold:
            return REUSE if warm > 0 else SCALE_OUT
        if cpu < self.scale_down_threshold:
            return TERMINATE if warm > 0 else SCALE_IN
        return NOOP
