"""Approved-action executor (architecture Layer 10, docs/design.md section 15).

The executor translates an already-validated abstract action into a fixed,
allow-listed platform operation. It never accepts raw strings, shell commands or
Kubernetes YAML from the planner or policy: namespace and function come from
configuration, and the only operation template is a bounded ``kubectl scale``.

Execution is disabled by default (``execution.enabled: false``) and dry-run by
default (``execution.dry_run: true``), so the simulator never touches a cluster
unless explicitly configured to.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from numbers import Integral
from typing import Dict, List, Optional, Protocol, Union

from agent.schemas import Plan, StateSnapshot
from orchestrator.action_validator import ActionValidator
from rl.environment import ACTIONS, NOOP, PREWARM, REUSE, SCALE_IN, SCALE_OUT, TERMINATE


@dataclass
class ExecutionResult:
    ok: bool
    code: str
    reason: str
    dry_run: bool
    executed: bool
    operation: str
    target_capacity: int
    commands: List[List[str]] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "ok": self.ok,
            "code": self.code,
            "reason": self.reason,
            "dry_run": self.dry_run,
            "executed": self.executed,
            "operation": self.operation,
            "target_capacity": self.target_capacity,
            "commands": [list(command) for command in self.commands],
        }


class Executor(Protocol):
    def execute(
        self,
        action: int,
        state: StateSnapshot,
        plan: Optional[Plan] = None,
        authorized: bool = True,
    ) -> ExecutionResult: ...


class NoOpExecutor:
    """Explicit no-op backend for offline experiments."""

    def execute(
        self,
        action: int,
        state: StateSnapshot,
        plan: Optional[Plan] = None,
        authorized: bool = True,
    ) -> ExecutionResult:
        if not authorized:
            return ExecutionResult(False, "unauthorized", "executor authorization missing", True, False, "noop", state.active_containers)
        return ExecutionResult(True, "noop", "execution backend is noop", True, False, "noop", state.active_containers)


class KubernetesExecutor:
    """Bounded ``kubectl scale`` executor for the OpenFaaS function deployment."""

    def __init__(self, config: Optional[Dict] = None) -> None:
        config = config or {}
        execution = config.get("execution", {})
        self.enabled = bool(execution.get("enabled", False))
        self.dry_run = bool(execution.get("dry_run", True))
        self.namespace = str(execution.get("namespace", "serverless-mgmt"))
        self.function = str(execution.get("function", "fn-checkout"))
        self.kubectl = str(execution.get("kubectl", "kubectl"))
        self.timeout_s = float(execution.get("timeout_s", 30))
        self.allowed_namespaces = set(execution.get("allowed_namespaces", [self.namespace]))
        self.max_replicas = int(execution.get("max_replicas", 30))
        self.action_validator = ActionValidator(config)

        if self.namespace not in self.allowed_namespaces:
            raise ValueError(f"namespace {self.namespace!r} is not in execution.allowed_namespaces")

    def _plan_operation(self, action: int, state: StateSnapshot):
        name = ACTIONS[action]
        if name == "NoOp":
            return "noop", int(state.active_containers), []
        if name == "PreWarm":
            return "prewarm", int(state.active_containers), []

        target = self.action_validator.capacity_after(state.active_containers, action)
        target = min(target, self.max_replicas)
        operation = "terminate" if name == "Terminate" else "scale"
        command = [
            self.kubectl,
            "-n",
            self.namespace,
            "scale",
            f"deployment/{self.function}",
            f"--replicas={target}",
        ]
        return operation, int(target), [command]

    def execute(
        self,
        action: int,
        state: StateSnapshot,
        plan: Optional[Plan] = None,
        authorized: bool = True,
    ) -> ExecutionResult:
        if isinstance(action, bool) or not isinstance(action, Integral):
            return ExecutionResult(False, "invalid_action", "action must be an integer", True, False, "none", state.active_containers)
        action = int(action)
        if action not in range(len(ACTIONS)):
            return ExecutionResult(False, "invalid_action", f"unknown action {action}", True, False, "none", state.active_containers)

        if not authorized:
            return ExecutionResult(
                False, "unauthorized", "executor authorization missing", True, False, "none", state.active_containers
            )

        operation, target, commands = self._plan_operation(action, state)

        if not self.enabled:
            return ExecutionResult(
                True,
                "disabled",
                "execution.enabled is false; no platform call made",
                True,
                False,
                operation,
                target,
                commands,
            )

        if self.dry_run:
            return ExecutionResult(
                True,
                "dry_run",
                "execution.dry_run is true; commands not applied",
                True,
                False,
                operation,
                target,
                commands,
            )

        if not commands:
            return ExecutionResult(
                True, "noop", "no platform change required", False, False, operation, target, []
            )

        try:
            completed = subprocess.run(
                commands[0],
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
                check=False,
            )
        except Exception as exc:
            return ExecutionResult(
                False, "execution_failed", str(exc)[:300], False, False, operation, target, commands
            )

        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            return ExecutionResult(
                False,
                "execution_failed",
                f"exit {completed.returncode}: {detail[:300]}",
                False,
                False,
                operation,
                target,
                commands,
            )

        return ExecutionResult(True, "executed", "bounded scale applied", False, True, operation, target, commands)


def build_executor(config: Optional[Dict] = None) -> Executor:
    config = config or {}
    backend = str(config.get("execution", {}).get("backend", "kubernetes")).lower()
    if backend == "noop":
        return NoOpExecutor()
    if backend in {"kubernetes", "openfaas"}:
        return KubernetesExecutor(config)
    raise ValueError(f"unknown execution.backend {backend!r}; expected 'noop', 'kubernetes' or 'openfaas'")
