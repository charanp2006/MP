"""Serverless container-control environment for PPO (docs/design.md section 10).

A lightweight, dependency-free (no Gym) environment with the standard
``reset`` / ``step`` contract. It steps along a real workload timeline from the
data pipeline and *simulates* the effect of bounded container actions on
capacity, cold starts, latency and energy.

State (design.md section 10)::

    [predicted_workload, current_workload, cpu, memory, latency,
     p95_latency, active_containers, cold_starts, energy, sla_margin]

Action space (design.md section 10)::

    0 NoOp, 1 PreWarm, 2 ScaleOut, 3 Reuse, 4 ScaleIn, 5 Terminate

Capacity is always clamped to ``[containers.min, containers.max]`` and moves by
at most ``containers.max_change_per_cycle`` per step (R02).
"""

from __future__ import annotations

import math
from collections import deque
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from rl.reward import compute_reward

# Canonical action set (project.md, docs/test_plan.md R01).
ACTIONS: List[str] = ["NoOp", "PreWarm", "ScaleOut", "Reuse", "ScaleIn", "Terminate"]
NOOP, PREWARM, SCALE_OUT, REUSE, SCALE_IN, TERMINATE = range(6)
ACTION_BY_NAME = {name.lower(): idx for idx, name in enumerate(ACTIONS)}

OBS_NAMES = [
    "predicted_workload",
    "current_workload",
    "cpu",
    "memory",
    "latency",
    "p95_latency",
    "active_containers",
    "cold_starts",
    "energy",
    "sla_margin",
]


class ServerlessEnv:
    """Simulated serverless fleet driven by a workload timeline."""

    def __init__(self, frame: pd.DataFrame, config: Dict) -> None:
        containers = config["containers"]
        sla_cfg = config["sla"]
        rl_cfg = config["control"]["rl"]
        sim = rl_cfg["sim"]

        self.min_capacity = int(containers["min"])
        self.max_capacity = int(containers["max"])
        self.max_change = int(containers["max_change_per_cycle"])
        self.sla_threshold = float(sla_cfg["p95_latency_ms"])
        self.reward_weights = rl_cfg["reward_weights"]

        # Simulation constants.
        self.base_latency = float(sim["base_latency_ms"])
        self.ms_per_shortfall = float(sim["ms_per_extra_container"])
        self.power_per_container = float(sim["power_per_container_w"])
        self.idle_power = float(sim["idle_power_w"])
        self.lifecycle_delay_steps = max(0, int(sim.get("lifecycle_delay_steps", 0)))
        self.cooldown_steps = max(0, int(sim.get("cooldown_steps", 0)))
        self.cold_history_size = max(1, int(sim.get("cold_history_steps", 10)))
        self.p95_factor = 1.3
        # Load a single container can absorb per control interval.
        self.load_per_container = max(
            1.0, (100.0 / float(sim["containers_per_100_rps"])) * (config["control"]["interval_seconds"] / 60.0)
        )

        self.timeline = self._aggregate(frame)
        self.workload_ref = float(max(self.timeline["workload"].max(), 1.0))
        self.energy_ref = float(self.power_per_container * self.max_capacity + self.idle_power)

        self.context = {
            "max_capacity": float(self.max_capacity),
            "sla_threshold": self.sla_threshold,
            "max_change": float(self.max_change),
            "power_per_container_w": self.power_per_container,
        }

        self.capacity = self.min_capacity
        self.warm = 0
        self.idx = 0
        self._forecast: Optional[np.ndarray] = None
        self._pending_warm: deque = deque()
        self._cold_history: deque = deque()
        self._last_scale_step: Optional[int] = None

    # ------------------------------------------------------------------ setup
    @staticmethod
    def _aggregate(frame: pd.DataFrame) -> pd.DataFrame:
        """Collapse per-function rows into one global fleet timeline."""
        grouped = frame.groupby("timestamp", sort=True)
        timeline = pd.DataFrame(
            {
                "timestamp": grouped.size().index,
                "workload": grouped["invocation_count"].sum().values,
                "cpu": grouped["cpu_utilization"].mean().values,
                "memory": grouped["memory_utilization"].mean().values,
            }
        ).reset_index(drop=True)
        return timeline

    def set_forecast(self, forecast: Optional[np.ndarray]) -> None:
        """Optionally supply TFT predictions (one per step) for the PPO state."""
        if forecast is None:
            self._forecast = None
            return
        values = np.asarray(forecast, dtype=np.float64)
        if values.ndim != 1 or len(values) != len(self.timeline):
            raise ValueError("forecast must be a 1D array with one value per timeline step")
        if not np.all(np.isfinite(values)) or np.any(values < 0):
            raise ValueError("forecast must contain finite non-negative values")
        self._forecast = values

    def _promote_pending(self) -> None:
        while self._pending_warm and self._pending_warm[0][0] <= self.idx:
            _, count = self._pending_warm.popleft()
            self.warm = min(self.max_capacity, self.warm + count)

    def current_context(self) -> Tuple[Dict, Dict]:
        """Return forecast/metrics mappings for the current (unstepped) state."""
        row = self.timeline.iloc[min(self.idx, len(self.timeline) - 1)]
        workload = float(row["workload"])
        predicted = (
            float(self._forecast[self.idx]) if self._forecast is not None else workload
        )
        required_raw = math.ceil(workload / self.load_per_container)
        capacity = float(self.capacity)
        shortfall = max(0.0, (workload / self.load_per_container) - capacity)
        latency = self.base_latency + self.ms_per_shortfall * shortfall
        p95 = latency * self.p95_factor
        energy = self.power_per_container * capacity + self.idle_power
        forecast = {
            "predicted_workload": [predicted],
            "trend": "stable",
            "forecast_horizon": 1,
        }
        metrics = {
            "current_workload": workload,
            "cpu_utilization": float(row["cpu"]),
            "memory_utilization": float(row["memory"]),
            "active_containers": int(self.capacity),
            "warm_containers": int(self.warm),
            "p95_latency_ms": p95,
            "required_capacity_raw": required_raw,
            "energy": energy,
        }
        return forecast, metrics

    # ----------------------------------------------------------------- actions
    def _apply_action(self, action: int) -> Tuple[int, int]:
        """Apply a bounded action; return (cold_starts, capacity_delta)."""
        if action not in range(len(ACTIONS)):
            raise ValueError(f"unknown action {action}; must be in 0..{len(ACTIONS) - 1}")

        prev_capacity = self.capacity
        cold_starts = 0

        reducing = action in {SCALE_IN, TERMINATE}
        if (
            reducing
            and self.cooldown_steps > 0
            and self._last_scale_step is not None
            and (self.idx - self._last_scale_step) < self.cooldown_steps
        ):
            return 0, 0

        if action == PREWARM:
            self._pending_warm.append((self.idx + self.lifecycle_delay_steps, self.max_change))
        elif action == SCALE_OUT:
            increase = self.max_change
            cold_starts = max(0, increase - self.warm)  # warm reused, rest start cold
            self.warm = max(0, self.warm - increase)
            self.capacity = int(np.clip(self.capacity + increase, self.min_capacity, self.max_capacity))
        elif action == REUSE:
            increase = min(self.max_change, self.warm)  # scale up using warm containers only
            self.warm -= increase
            self.capacity = int(np.clip(self.capacity + increase, self.min_capacity, self.max_capacity))
        elif action == SCALE_IN:
            self.capacity = int(np.clip(self.capacity - self.max_change, self.min_capacity, self.max_capacity))
        elif action == TERMINATE:
            self.warm = 0
            self.capacity = int(np.clip(self.capacity - self.max_change, self.min_capacity, self.max_capacity))
        # NOOP: nothing changes.

        if self.capacity != prev_capacity:
            self._last_scale_step = self.idx
        return cold_starts, self.capacity - prev_capacity

    # ------------------------------------------------------------------- reset
    def reset(self) -> np.ndarray:
        self.capacity = self.min_capacity
        self.warm = 0
        self.idx = 0
        self._pending_warm.clear()
        self._cold_history.clear()
        self._last_scale_step = None
        return self._observe(0)[0]

    # -------------------------------------------------------------------- step
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        if self.idx >= len(self.timeline):
            raise RuntimeError("episode finished; call reset()")

        self._promote_pending()
        row = self.timeline.iloc[self.idx]
        workload = float(row["workload"])
        required_raw = int(math.ceil(workload / self.load_per_container))
        required = int(np.clip(required_raw, self.min_capacity, self.max_capacity))

        cold_starts, _ = self._apply_action(action)
        self._cold_history.append(float(cold_starts))
        while len(self._cold_history) > self.cold_history_size:
            self._cold_history.popleft()
        capacity = self.capacity

        # Use unclipped required for shortfall/latency so overload/SLA risk is not hidden
        shortfall = max(0, required_raw - capacity)
        latency = self.base_latency + self.ms_per_shortfall * shortfall
        p95 = latency * self.p95_factor
        energy = self.power_per_container * capacity + self.idle_power
        sla_margin = self.sla_threshold - p95

        raw = {
            "energy": energy,
            "latency": latency,
            "p95_latency": p95,
            "cold_starts": float(cold_starts),
            "capacity": float(capacity),
            "warm_containers": float(self.warm),
            "required_capacity": float(required),
            "required_capacity_raw": float(required_raw),
        }
        reward, components = compute_reward(raw, self.reward_weights, self.context)

        self.idx += 1
        done = self.idx >= len(self.timeline)
        obs, obs_names = self._observe(self.idx if not done else len(self.timeline) - 1)
        info = {
            "action": ACTIONS[action],
            "capacity": capacity,
            "warm_containers": int(self.warm),
            "pending_warm_containers": int(sum(count for _, count in self._pending_warm)),
            "sla_margin_ms": sla_margin,
            "required_capacity": required,
            "required_capacity_raw": required_raw,
            "workload": workload,
            "latency": latency,
            "p95_latency": p95,
            "energy": energy,
            "cold_starts": cold_starts,
            "sla_violated": p95 >= self.sla_threshold,
            "reward_components": components,
            "obs_names": obs_names,
        }
        return obs, float(reward), done, info

    # ------------------------------------------------------------------ observe
    def _observe(self, idx: int) -> Tuple[np.ndarray, List[str]]:
        idx = min(idx, len(self.timeline) - 1)
        row = self.timeline.iloc[idx]
        workload = float(row["workload"])
        predicted = float(self._forecast[idx]) if self._forecast is not None else workload

        capacity = float(self.capacity)
        shortfall = max(0.0, (workload / self.load_per_container) - capacity)
        latency = self.base_latency + self.ms_per_shortfall * shortfall
        p95 = latency * self.p95_factor
        energy = self.power_per_container * capacity + self.idle_power
        sla_margin = self.sla_threshold - p95

        obs = np.array(
            [
                predicted / self.workload_ref,
                workload / self.workload_ref,
                float(row["cpu"]),
                float(row["memory"]),
                latency / self.sla_threshold,
                p95 / self.sla_threshold,
                capacity / self.max_capacity,
                min(
                    float(np.mean(self._cold_history)) / max(float(self.max_change), 1.0),
                    1.0,
                )
                if self._cold_history
                else 0.0,
                energy / self.energy_ref,
                sla_margin / self.sla_threshold,
            ],
            dtype=np.float32,
        )
        return obs, OBS_NAMES

    @property
    def observation_size(self) -> int:
        return len(OBS_NAMES)

    @property
    def n_actions(self) -> int:
        return len(ACTIONS)
