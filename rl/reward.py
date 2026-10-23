"""PPO reward for serverless container control (docs/design.md section 12).

``R_t = -(w_e E_t + w_l L_t + w_c CS_t + w_r RC_t + w_u U_t) - w_s V_t``

Every component is normalized to an O(1) scale so a single metric cannot
dominate purely because of its units (design.md section 12). The SLA violation
term ``V_t`` carries the highest weight: SLA (P95 latency) is the primary
constraint (project.md, docs/prd.md FR-05/FR-06).

The function returns both the scalar reward and a component breakdown so tests
(R03, R04) and monitoring can inspect *why* a reward was produced.
"""

from __future__ import annotations

from typing import Dict, Tuple

DEFAULT_WEIGHTS = {
    "energy": 1.0,
    "latency": 1.0,
    "cold_start": 1.5,
    "resource": 0.5,
    "underutil": 0.3,
    "sla_violation": 5.0,
}


def compute_reward(
    raw: Dict[str, float],
    weights: Dict[str, float] | None = None,
    context: Dict[str, float] | None = None,
) -> Tuple[float, Dict[str, float]]:
    """Compute the normalized PPO reward.

    ``raw`` must contain: energy, latency, p95_latency, cold_starts, capacity,
    required_capacity. ``context`` provides the normalizers: max_capacity,
    sla_threshold, max_change, power_per_container_w.
    """
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    ctx = {
        "max_capacity": 30.0,
        "sla_threshold": 250.0,
        "max_change": 5.0,
        "power_per_container_w": 15.0,
        **(context or {}),
    }

    max_capacity = max(ctx["max_capacity"], 1.0)
    sla = max(ctx["sla_threshold"], 1.0)
    max_change = max(ctx["max_change"], 1.0)
    power = max(ctx["power_per_container_w"], 1e-6)

    energy = float(raw["energy"])
    latency = float(raw["latency"])
    p95 = float(raw["p95_latency"])
    cold_starts = float(raw["cold_starts"])
    capacity = float(raw["capacity"])
    required = float(raw["required_capacity"])

    # --- Normalized components (O(1)) ---
    e_norm = energy / (power * max_capacity)              # energy vs max fleet draw
    l_norm = latency / sla                                 # latency relative to SLA
    cs_norm = min(cold_starts / max_change, 3.0)           # cold starts per max step
    rc_norm = capacity / max_capacity                      # provisioned fraction
    u_norm = max(0.0, capacity - required) / max_capacity  # idle / over-provisioned

    # SLA violation: hinge on P95 above threshold (0 when compliant).
    v_norm = max(0.0, p95 - sla) / sla

    weighted = (
        w["energy"] * e_norm
        + w["latency"] * l_norm
        + w["cold_start"] * cs_norm
        + w["resource"] * rc_norm
        + w["underutil"] * u_norm
    )
    penalty = w["sla_violation"] * v_norm
    reward = -weighted - penalty

    components = {
        "reward": reward,
        "energy": e_norm,
        "latency": l_norm,
        "cold_start": cs_norm,
        "resource": rc_norm,
        "underutil": u_norm,
        "sla_violation": v_norm,
        "weighted_cost": weighted,
        "sla_penalty": penalty,
    }
    return float(reward), components
