from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import Counter
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Iterable, Iterator, Mapping

import pandas as pd

from configs import load_config
from experiments.synthetic_scenarios import SCENARIO_NAMES, generate_scenarios

PAYLOAD_CLASSES = {
    "small": {"weight": 0.65, "duration_ms": 22.0},
    "medium": {"weight": 0.28, "duration_ms": 58.0},
    "large": {"weight": 0.07, "duration_ms": 145.0},
}
DEFAULT_SERVICES = ("fn_checkout", "fn_search", "fn_recommend")
DEFAULT_START_TIME = "2026-01-05T00:00:00Z"
ARRIVAL_MODELS = ("uniform", "poisson")
ARTIFACT_VERSION = "c1-synthetic-client-v1"
FORBIDDEN_EVENT_KEYS = frozenset(
    {"user_id", "payload", "auth_token", "request_body", "body", "authorization"}
)


def _default_start_time() -> datetime:
    return datetime(2026, 1, 5, tzinfo=timezone.utc)


def _default_payload_specs() -> dict[str, PayloadClassSpec]:
    return {
        name: PayloadClassSpec(weight=float(values["weight"]), duration_ms=float(values["duration_ms"]))
        for name, values in PAYLOAD_CLASSES.items()
    }


def _normalize_start_time(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise TypeError("start_time must be an ISO-8601 string or datetime")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class PayloadClassSpec:
    weight: float
    duration_ms: float

    @classmethod
    def from_value(cls, value: object) -> PayloadClassSpec:
        if isinstance(value, PayloadClassSpec):
            return value
        if isinstance(value, Mapping):
            return cls(weight=float(value["weight"]), duration_ms=float(value["duration_ms"]))
        raise TypeError("payload spec must be a PayloadClassSpec or mapping")

    def to_dict(self) -> dict:
        return {"weight": self.weight, "duration_ms": self.duration_ms}


@dataclass(frozen=True)
class BurstWindow:
    start_step: int
    end_step: int
    multiplier: float

    def contains(self, step: int) -> bool:
        return self.start_step <= step < self.end_step

    @classmethod
    def from_value(cls, value: object) -> BurstWindow:
        if isinstance(value, BurstWindow):
            return value
        if isinstance(value, Mapping):
            return cls(
                start_step=int(value.get("start_step", value.get("start"))),
                end_step=int(value.get("end_step", value.get("end"))),
                multiplier=float(value.get("multiplier", 2.5)),
            )
        raise TypeError("burst window must be a BurstWindow or mapping")

    def to_dict(self) -> dict:
        return {
            "start_step": self.start_step,
            "end_step": self.end_step,
            "multiplier": self.multiplier,
        }


@dataclass(frozen=True)
class SyntheticClientConfig:
    scenario: str = "mixed"
    steps: int = 24
    interval_s: int = 60
    rate_per_interval: int = 120
    seed: int = 42
    start_time: datetime = field(default_factory=_default_start_time)
    services: tuple[str, ...] = DEFAULT_SERVICES
    service_weights: tuple[float, ...] | None = None
    payload_classes: tuple[str, ...] = tuple(PAYLOAD_CLASSES)
    payload_specs: Mapping[str, PayloadClassSpec] = field(
        default_factory=lambda: MappingProxyType(_default_payload_specs())
    )
    arrival_model: str = "uniform"
    burst_multiplier: float = 2.5
    burst_windows: tuple[BurstWindow, ...] = ()
    error_rate: float = 0.01

    def __post_init__(self) -> None:
        object.__setattr__(self, "steps", int(self.steps))
        object.__setattr__(self, "interval_s", int(self.interval_s))
        object.__setattr__(self, "rate_per_interval", int(self.rate_per_interval))
        object.__setattr__(self, "seed", int(self.seed))
        object.__setattr__(self, "start_time", _normalize_start_time(self.start_time))
        object.__setattr__(self, "services", tuple(str(name) for name in self.services))
        object.__setattr__(self, "payload_classes", tuple(str(name) for name in self.payload_classes))
        object.__setattr__(
            self,
            "payload_specs",
            MappingProxyType(
                {name: PayloadClassSpec.from_value(spec) for name, spec in self.payload_specs.items()}
            ),
        )
        object.__setattr__(
            self,
            "burst_windows",
            tuple(BurstWindow.from_value(window) for window in self.burst_windows),
        )
        if self.service_weights is not None:
            object.__setattr__(self, "service_weights", tuple(float(value) for value in self.service_weights))

        if self.steps <= 0:
            raise ValueError("steps must be positive")
        if self.interval_s <= 0:
            raise ValueError("interval_s must be positive")
        if self.rate_per_interval <= 0:
            raise ValueError("rate_per_interval must be positive")
        if not 0.0 <= self.error_rate < 1.0:
            raise ValueError("error_rate must be in [0, 1)")
        if self.scenario not in SCENARIO_NAMES:
            raise ValueError(f"unknown scenario: {self.scenario}; expected one of {SCENARIO_NAMES}")
        if self.arrival_model not in ARRIVAL_MODELS:
            raise ValueError(f"unknown arrival_model: {self.arrival_model}; expected one of {ARRIVAL_MODELS}")
        if not self.services or len(set(self.services)) != len(self.services):
            raise ValueError("services must be non-empty and unique")
        if not self.payload_classes or len(set(self.payload_classes)) != len(self.payload_classes):
            raise ValueError("payload_classes must be non-empty and unique")
        if self.service_weights is not None:
            if len(self.service_weights) != len(self.services):
                raise ValueError("service_weights must match services")
            if any(not math.isfinite(value) or value < 0 for value in self.service_weights):
                raise ValueError("service_weights must be finite and non-negative")
            if sum(self.service_weights) <= 0:
                raise ValueError("service_weights must have a positive sum")
        unknown = [name for name in self.payload_classes if name not in self.payload_specs]
        if unknown:
            raise ValueError(f"unknown payload classes: {unknown}")
        for name in self.payload_classes:
            spec = self.payload_specs[name]
            if not math.isfinite(spec.weight) or spec.weight <= 0:
                raise ValueError(f"payload class {name} has invalid weight")
            if not math.isfinite(spec.duration_ms) or spec.duration_ms <= 0:
                raise ValueError(f"payload class {name} has invalid duration_ms")
        if not math.isfinite(self.burst_multiplier) or self.burst_multiplier < 1.0:
            raise ValueError("burst_multiplier must be finite and >= 1.0")
        for window in self.burst_windows:
            if window.start_step < 0 or window.end_step <= window.start_step:
                raise ValueError("burst windows must satisfy 0 <= start_step < end_step")
            if not math.isfinite(window.multiplier) or window.multiplier < 1.0:
                raise ValueError("burst window multiplier must be finite and >= 1.0")

    @classmethod
    def from_config(cls, config: Mapping[str, object] | None) -> SyntheticClientConfig:
        demo = dict((config or {}).get("demo", {}) or {})
        services = tuple(str(name) for name in demo.get("services", DEFAULT_SERVICES))
        raw_weights = demo.get("service_weights")
        if isinstance(raw_weights, Mapping) and raw_weights:
            service_weights = tuple(float(raw_weights.get(name, 1.0)) for name in services)
        elif raw_weights:
            service_weights = tuple(float(value) for value in raw_weights)
        else:
            service_weights = None

        weights = demo.get("payload_class_weights", {}) or {}
        durations = demo.get("payload_duration_ms", {}) or {}
        payload_specs = {
            name: PayloadClassSpec(
                weight=float(weights.get(name, spec.weight)),
                duration_ms=float(durations.get(name, spec.duration_ms)),
            )
            for name, spec in _default_payload_specs().items()
        }

        return cls(
            scenario=str(demo.get("scenario", "mixed")),
            steps=int(demo.get("steps", 24)),
            interval_s=int(demo.get("interval_s", 60)),
            rate_per_interval=int(demo.get("rate_per_interval", 120)),
            seed=int(demo.get("seed", 42)),
            start_time=str(demo.get("start_time", DEFAULT_START_TIME)),
            services=services,
            service_weights=service_weights,
            payload_classes=tuple(str(name) for name in demo.get("payload_classes", list(PAYLOAD_CLASSES))),
            payload_specs=payload_specs,
            arrival_model=str(demo.get("arrival_model", "uniform")),
            burst_multiplier=float(demo.get("burst_multiplier", 2.5)),
            burst_windows=tuple(
                BurstWindow.from_value(value) for value in demo.get("burst_windows", []) or []
            ),
            error_rate=float(demo.get("error_rate", 0.01)),
        )

    from_mapping = from_config

    def to_dict(self) -> dict:
        return {
            "scenario": self.scenario,
            "steps": self.steps,
            "interval_s": self.interval_s,
            "rate_per_interval": self.rate_per_interval,
            "seed": self.seed,
            "start_time": _iso_utc(self.start_time),
            "services": list(self.services),
            "service_weights": list(self.service_weights) if self.service_weights else None,
            "payload_classes": list(self.payload_classes),
            "payload_specs": {name: spec.to_dict() for name, spec in self.payload_specs.items()},
            "arrival_model": self.arrival_model,
            "burst_multiplier": self.burst_multiplier,
            "burst_windows": [window.to_dict() for window in self.burst_windows],
            "error_rate": self.error_rate,
        }


@dataclass(frozen=True)
class SyntheticClientRun:
    config: SyntheticClientConfig
    events: list[dict]
    profile: list[dict]
    manifest: dict

    def to_artifacts(self, out_dir: str | Path) -> dict[str, Path]:
        target = Path(out_dir)
        target.mkdir(parents=True, exist_ok=True)
        artifacts = {
            "events": target / "events.jsonl",
            "load_profile": target / "load_profile.json",
            "client_manifest": target / "client_manifest.json",
        }
        artifacts["events"].write_text(_events_to_text(self.events), encoding="utf-8")
        artifacts["load_profile"].write_text(_json_text(self.profile), encoding="utf-8")
        artifacts["client_manifest"].write_text(_json_text(self.manifest), encoding="utf-8")
        return artifacts


def _scenario_shape(scenario: str, steps: int, seed: int) -> list[float]:
    frames = generate_scenarios(steps=steps, seed=seed)
    frame = frames.get(scenario)
    if frame is None:
        raise ValueError(f"unknown scenario: {scenario}; expected one of {SCENARIO_NAMES}")
    return [float(value) for value in frame["invocation_count"].tolist()]


def _burst_multiplier(config: SyntheticClientConfig, step: int, scale: float) -> float:
    multiplier = config.burst_multiplier if config.scenario == "burst" and scale > 0.7 else 1.0
    for window in config.burst_windows:
        if window.contains(step):
            multiplier = max(multiplier, window.multiplier)
    return multiplier


def _window_plans(config: SyntheticClientConfig) -> list[dict]:
    shape = _scenario_shape(config.scenario, config.steps, config.seed)
    peak = max(shape) or 1.0
    plans = []
    for step, value in enumerate(shape):
        scale = value / peak
        multiplier = _burst_multiplier(config, step, scale)
        expected = config.rate_per_interval * scale * multiplier
        plans.append(
            {
                "step": step,
                "window_start": config.start_time + timedelta(seconds=step * config.interval_s),
                "expected_invocations": expected,
                "planned_invocations": int(round(expected)),
                "burst": multiplier > 1.0,
            }
        )
    return plans


def _poisson_count(rng: random.Random, expected: float) -> int:
    if expected <= 0:
        return 0
    threshold = math.exp(-expected)
    product = 1.0
    count = 0
    while product > threshold:
        count += 1
        product *= rng.random()
    return count - 1


def _assert_privacy(events: Iterable[dict]) -> None:
    for event in events:
        forbidden = FORBIDDEN_EVENT_KEYS.intersection(event)
        if forbidden:
            raise ValueError(f"event contains forbidden fields: {sorted(forbidden)}")


def build_load_profile(
    config: SyntheticClientConfig, events: Iterable[dict], *, plans: list[dict] | None = None
) -> list[dict]:
    plans = plans if plans is not None else _window_plans(config)
    observed: Counter[int] = Counter()
    service_counts: dict[int, Counter[str]] = {}
    for event in events:
        timestamp = _normalize_start_time(event["timestamp"])
        step = int((timestamp - config.start_time).total_seconds() // config.interval_s)
        if 0 <= step < config.steps:
            observed[step] += int(event["invocation_count"])
            service_counts.setdefault(step, Counter())[event["service_id"]] += int(event["invocation_count"])

    profile = []
    for plan in plans:
        step = plan["step"]
        counts = service_counts.get(step, Counter())
        profile.append(
            {
                "window_start": _iso_utc(plan["window_start"]),
                "planned_invocations": plan["planned_invocations"],
                "expected_invocations": round(plan["expected_invocations"], 6),
                "observed_invocations": observed[step],
                "burst": plan["burst"],
                "service_counts": {name: counts[name] for name in config.services},
            }
        )
    return profile


def _events_to_text(events: Iterable[dict]) -> str:
    return "".join(
        json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n" for event in replay_events(events)
    )


def _json_text(payload: object) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_manifest(
    config: SyntheticClientConfig, events: Iterable[dict], profile: list[dict]
) -> dict:
    materialized = list(events)
    return {
        "artifact_version": ARTIFACT_VERSION,
        "evidence_tier": "synthetic_only_no_live_traffic",
        "config": config.to_dict(),
        "config_sha256": _sha256(_json_text(config.to_dict())),
        "event_count": len(materialized),
        "events_sha256": _sha256(_events_to_text(materialized)),
        "load_profile_sha256": _sha256(_json_text(profile)),
        "window_count": len(profile),
        "observed_invocations": sum(row["observed_invocations"] for row in profile),
        "privacy": {
            "allow_user_identity": False,
            "allow_request_payload": False,
            "allow_auth_token": False,
            "allow_request_body": False,
        },
    }


def generate_run(config: SyntheticClientConfig) -> SyntheticClientRun:
    plans = _window_plans(config)
    rng = random.Random(config.seed)
    service_weights = config.service_weights or tuple(1.0 for _ in config.services)
    payload_weights = [config.payload_specs[name].weight for name in config.payload_classes]
    window_ms = config.interval_s * 1000
    events: list[dict] = []

    for plan in plans:
        step = plan["step"]
        if config.arrival_model == "uniform":
            count = plan["planned_invocations"]
        else:
            count = _poisson_count(rng, plan["expected_invocations"])
        for index in range(count):
            if config.service_weights is None:
                service_id = rng.choice(config.services)
            else:
                service_id = rng.choices(config.services, weights=service_weights, k=1)[0]
            payload_class = rng.choices(config.payload_classes, weights=payload_weights, k=1)[0]
            base_duration = config.payload_specs[payload_class].duration_ms
            duration_ms = max(1.0, rng.gauss(base_duration, base_duration * 0.18))
            error_count = 1 if rng.random() < config.error_rate else 0
            timestamp = plan["window_start"] + timedelta(milliseconds=rng.randrange(window_ms))
            events.append(
                {
                    "request_id": f"req-{config.seed}-{step:04d}-{index:05d}",
                    "timestamp": timestamp.isoformat(),
                    "service_id": service_id,
                    "function_id": service_id,
                    "payload_class": payload_class,
                    "invocation_count": 1,
                    "execution_duration_ms": round(duration_ms, 3),
                    "error_count": error_count,
                    "source": "synthetic_client",
                    "scenario": config.scenario,
                }
            )

    events.sort(key=lambda event: (event["timestamp"], event["request_id"]))
    _assert_privacy(events)
    profile = build_load_profile(config, events, plans=plans)
    return SyntheticClientRun(
        config=config, events=events, profile=profile, manifest=build_manifest(config, events, profile)
    )


def generate_events(
    scenario: str = "mixed",
    steps: int = 24,
    interval_s: int = 60,
    rate_per_interval: int = 120,
    seed: int = 42,
    services: list[str] | None = None,
    payload_classes: list[str] | None = None,
    burst_multiplier: float = 2.5,
    error_rate: float = 0.01,
) -> list[dict]:
    config = SyntheticClientConfig(
        scenario=scenario,
        steps=steps,
        interval_s=interval_s,
        rate_per_interval=rate_per_interval,
        seed=seed,
        services=tuple(services or DEFAULT_SERVICES),
        payload_classes=tuple(payload_classes or list(PAYLOAD_CLASSES)),
        burst_multiplier=burst_multiplier,
        error_rate=error_rate,
    )
    return generate_run(config).events


def replay_events(events: Iterable[dict]) -> Iterator[dict]:
    for event in sorted(events, key=lambda item: (item["timestamp"], str(item.get("request_id", "")))):
        yield event


def _parse_key_values(values: list[str] | None, label: str) -> dict[str, float]:
    parsed: dict[str, float] = {}
    for value in values or []:
        name, separator, raw = value.partition("=")
        if not separator or not name.strip():
            raise ValueError(f"{label} must be NAME=VALUE: {value}")
        try:
            parsed[name.strip()] = float(raw)
        except ValueError as exc:
            raise ValueError(f"{label} has non-numeric value: {value}") from exc
    return parsed


def _parse_burst_window(value: str) -> BurstWindow:
    parts = value.split(":")
    if len(parts) != 3:
        raise ValueError(f"--burst-window must be START:END:MULTIPLIER: {value}")
    try:
        return BurstWindow(start_step=int(parts[0]), end_step=int(parts[1]), multiplier=float(parts[2]))
    except ValueError as exc:
        raise ValueError(f"--burst-window has invalid values: {value}") from exc


def _apply_cli_overrides(config: SyntheticClientConfig, args: argparse.Namespace) -> SyntheticClientConfig:
    updates: dict[str, object] = {}
    for name in ("scenario", "steps", "interval_s", "rate_per_interval", "seed", "arrival_model"):
        value = getattr(args, name)
        if value is not None:
            updates[name] = value
    for name in ("start_time", "burst_multiplier", "error_rate"):
        value = getattr(args, name)
        if value is not None:
            updates[name] = value

    if args.services:
        updates["services"] = tuple(name.strip() for name in args.services.split(",") if name.strip())
        if not args.service_weight:
            updates["service_weights"] = None
    if args.payload_classes:
        updates["payload_classes"] = tuple(
            name.strip() for name in args.payload_classes.split(",") if name.strip()
        )

    weight_overrides = _parse_key_values(args.service_weight, "service weight")
    if weight_overrides:
        selected_services = updates.get("services", config.services)
        unknown = sorted(set(weight_overrides) - set(selected_services))
        if unknown:
            raise ValueError(f"unknown services in --service-weight: {unknown}")
        weights = {name: 1.0 for name in selected_services}
        weights.update(weight_overrides)
        updates["service_weights"] = tuple(weights[name] for name in selected_services)

    payload_weights = _parse_key_values(args.payload_weight, "payload weight")
    payload_durations = _parse_key_values(args.payload_duration, "payload duration")
    if payload_weights or payload_durations:
        specs = {
            name: PayloadClassSpec(spec.weight, spec.duration_ms)
            for name, spec in config.payload_specs.items()
        }
        for name, weight in payload_weights.items():
            if name not in specs:
                raise ValueError(f"unknown payload class in --payload-weight: {name}")
            specs[name] = PayloadClassSpec(weight, specs[name].duration_ms)
        for name, duration_ms in payload_durations.items():
            if name not in specs:
                raise ValueError(f"unknown payload class in --payload-duration: {name}")
            specs[name] = PayloadClassSpec(specs[name].weight, duration_ms)
        updates["payload_specs"] = specs

    if args.burst_window:
        updates["burst_windows"] = tuple(config.burst_windows) + tuple(
            _parse_burst_window(value) for value in args.burst_window
        )
    return replace(config, **updates)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate deterministic synthetic client events")
    parser.add_argument("--config", default=None, help="project config path (default: configs/project.yaml)")
    parser.add_argument("--out-dir", default=None, help="directory for generated artifacts")
    parser.add_argument("--scenario", default=None, choices=SCENARIO_NAMES)
    parser.add_argument("--steps", type=int, default=None)
    parser.add_argument("--interval-s", type=int, default=None)
    parser.add_argument("--rate-per-interval", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--start-time", default=None, help="ISO-8601 UTC start time")
    parser.add_argument("--arrival-model", default=None, choices=ARRIVAL_MODELS)
    parser.add_argument("--services", default=None, help="comma-separated service IDs")
    parser.add_argument("--payload-classes", default=None, help="comma-separated payload classes")
    parser.add_argument("--service-weight", action="append", default=None, metavar="NAME=WEIGHT")
    parser.add_argument("--payload-weight", action="append", default=None, metavar="NAME=WEIGHT")
    parser.add_argument("--payload-duration", action="append", default=None, metavar="NAME=MS")
    parser.add_argument("--burst-multiplier", type=float, default=None)
    parser.add_argument(
        "--burst-window", action="append", default=None, metavar="START:END:MULTIPLIER"
    )
    parser.add_argument("--error-rate", type=float, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config(args.config)
    try:
        client_config = _apply_cli_overrides(SyntheticClientConfig.from_config(config), args)
    except (TypeError, ValueError) as exc:
        parser.error(str(exc))

    run = generate_run(client_config)
    demo_config = config.get("demo", {}) or {}
    out_dir = args.out_dir or demo_config.get("client_out_dir", "results/demo/c1")
    artifacts = run.to_artifacts(out_dir)
    print(
        json.dumps(
            {
                "out_dir": str(out_dir),
                "event_count": len(run.events),
                "artifacts": {key: str(path) for key, path in artifacts.items()},
                "config_sha256": run.manifest["config_sha256"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
