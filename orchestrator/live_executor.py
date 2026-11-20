from __future__ import annotations

import subprocess
import time
from numbers import Integral
from typing import Dict, List, Optional, Tuple

from agent.schemas import Plan, StateSnapshot
from orchestrator.executor import ExecutionResult, KubernetesExecutor
from rl.environment import ACTIONS

LivePlan = Tuple[str, int, int, List[List[str]], Dict[str, int]]


class LiveKubernetesExecutor(KubernetesExecutor):
    backend = "kubernetes_live"

    def __init__(self, config: Optional[Dict] = None) -> None:
        super().__init__(config)
        live = (config or {}).get("execution", {}).get("live", {})
        self.verify = bool(live.get("verify", True))
        self.cooldown_s = float(live.get("cooldown_s", 30))
        self.rollback = bool(live.get("rollback", True))
        self.warm_deployment = str(live.get("warm_deployment", ""))
        self.warm_namespace = str(live.get("warm_namespace", self.namespace))
        self.warm_increment = max(1, int(live.get("warm_increment", 2)))
        self.warm_max = max(self.warm_increment, int(live.get("warm_max", 6)))
        self._last_live_command = 0.0

    def _get_replicas(self, deployment: str, namespace: Optional[str] = None) -> int:
        command = [
            self.kubectl,
            "-n",
            namespace or self.namespace,
            "get",
            f"deployment/{deployment}",
            "-o",
            "jsonpath={.spec.replicas}",
        ]
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=self.timeout_s,
            check=False,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "unknown")[:200]
            raise RuntimeError(f"replica read failed for {deployment}: {detail}")
        return max(0, int((completed.stdout or "0").strip() or 0))

    def _scale_command(self, deployment: str, target: int, namespace: Optional[str] = None) -> List[str]:
        return [
            self.kubectl,
            "-n",
            namespace or self.namespace,
            "scale",
            f"deployment/{deployment}",
            f"--replicas={int(target)}",
        ]

    def _run_command(self, command: List[str]) -> str:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=self.timeout_s,
            check=False,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "unknown").strip()[:300]
            raise RuntimeError(detail)
        return (completed.stdout or "").strip()[:300]

    def _plan_live(self, action: int, state: StateSnapshot) -> LivePlan:
        name = ACTIONS[action]
        current_active = self._get_replicas(self.function) if self.verify else int(state.active_containers)
        previous = {"active": current_active}

        if name == "PreWarm" and self.warm_deployment:
            current_warm = self._get_replicas(self.warm_deployment, self.warm_namespace) if self.verify else 0
            target_warm = min(self.warm_max, max(1, current_warm + self.warm_increment))
            previous["warm"] = current_warm
            return "prewarm", target_warm, current_active, [self._scale_command(self.warm_deployment, target_warm, self.warm_namespace)], previous

        if name == "Reuse":
            available = int(getattr(state, "warm_containers", 0) or 0)
            if available <= 0:
                return "rejected", current_active, current_active, [], previous
            reusable = min(available, self.max_change)
            target_active = min(self.max_replicas, max(self.min_capacity, current_active + reusable))
            if self.warm_deployment:
                current_warm = self._get_replicas(self.warm_deployment, self.warm_namespace) if self.verify else available
                target_warm = max(0, current_warm - reusable)
                previous["warm"] = current_warm
                commands = [
                    self._scale_command(self.function, target_active),
                    self._scale_command(self.warm_deployment, target_warm, self.warm_namespace),
                ]
                return "reuse", target_active, current_active, commands, previous
            return "reuse", target_active, current_active, [self._scale_command(self.function, target_active)], previous

        operation, target, commands = super()._plan_operation(action, state)
        if operation in {"scale", "terminate"}:
            commands = [self._scale_command(self.function, int(target))]
        return operation, int(target), current_active, commands, previous

    def _result(
        self,
        ok: bool,
        code: str,
        reason: str,
        dry_run: bool,
        executed: bool,
        operation: str,
        target: int,
        commands: Optional[List[List[str]]] = None,
    ) -> ExecutionResult:
        return ExecutionResult(
            ok=ok,
            code=code,
            reason=reason[:300],
            dry_run=dry_run,
            executed=executed,
            operation=operation,
            target_capacity=int(target),
            commands=commands or [],
            backend=self.backend,
        )

    def _rollback(self, previous: Dict[str, int]) -> List[str]:
        commands: List[List[str]] = []
        if "active" in previous:
            commands.append(self._scale_command(self.function, previous["active"]))
        if "warm" in previous and self.warm_deployment:
            commands.append(self._scale_command(self.warm_deployment, previous["warm"], self.warm_namespace))
        return commands

    def execute(
        self,
        action: int,
        state: StateSnapshot,
        plan: Optional[Plan] = None,
        authorized: bool = True,
    ) -> ExecutionResult:
        current = int(getattr(state, "active_containers", 0))
        if isinstance(action, bool) or not isinstance(action, Integral):
            return self._result(False, "invalid_action", "action must be an integer", True, False, "none", current)
        action = int(action)
        if action not in range(len(ACTIONS)):
            return self._result(False, "invalid_action", f"unknown action {action}", True, False, "none", current)
        if not authorized:
            return self._result(False, "unauthorized", "executor authorization missing", True, False, "none", current)

        if not self.enabled:
            operation, target, _ = super()._plan_operation(action, state)
            return self._result(True, "disabled", "execution.enabled is false; no platform call made", True, False, operation, target, [])

        if self.dry_run:
            operation, target, commands = super()._plan_operation(action, state)
            return self._result(True, "dry_run", "execution.dry_run is true; commands not applied", True, False, operation, target, commands)

        if not self.allow_live:
            return self._result(True, "live_disabled", "execution.allow_live is false; commands not applied", False, False, "none", current)

        now = time.monotonic()
        if now - self._last_live_command < self.cooldown_s:
            return self._result(False, "cooldown", "live action suppressed by cooldown", False, False, "none", current)

        try:
            operation, target, observed, commands, previous = self._plan_live(action, state)
        except Exception as exc:
            return self._result(False, "verification_failed", str(exc), False, False, "none", current)

        if operation == "rejected":
            return self._result(False, "reuse_no_warm_capacity", "REUSE requires available warm capacity", True, False, "none", observed)

        if not commands:
            return self._result(True, "noop", "no platform change required", False, False, operation, target, [])

        self._last_live_command = now
        applied: List[List[str]] = []
        try:
            for command in commands:
                self._run_command(command)
                applied.append(command)
        except Exception as exc:
            reason = str(exc)
            if self.rollback:
                for command in self._rollback(previous):
                    try:
                        self._run_command(command)
                    except Exception:
                        pass
            return self._result(False, "execution_failed", reason, False, False, operation, target, applied)

        if self.verify:
            try:
                active_after = self._get_replicas(self.function)
                if operation in {"scale", "terminate", "reuse"} and active_after != int(target):
                    raise RuntimeError(f"active replicas {active_after} != target {target}")
                if operation in {"prewarm", "reuse"} and self.warm_deployment:
                    warm_target = previous.get("warm", 0) - (int(target) - observed) if operation == "reuse" else int(target)
                    warm_after = self._get_replicas(self.warm_deployment, self.warm_namespace)
                    if warm_after != max(0, warm_target):
                        raise RuntimeError(f"warm replicas {warm_after} != target {warm_target}")
            except Exception as exc:
                if self.rollback:
                    for command in self._rollback(previous):
                        try:
                            self._run_command(command)
                        except Exception:
                            pass
                return self._result(False, "verification_failed", str(exc), False, False, operation, target, applied)

        return self._result(True, "executed", f"bounded {operation} applied and verified", False, True, operation, target, applied)
