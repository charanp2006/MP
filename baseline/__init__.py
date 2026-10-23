"""Comparison baselines for the learned controller.

* ``reactive`` --- utilization-threshold autoscaler (agreed step 2).
"""

from baseline.reactive import ReactiveAutoscaler

__all__ = ["ReactiveAutoscaler"]
