"""Measured runtime estimates are engineering evidence, never scientific stops."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EstimateBasis(str, Enum):
    MEASURED = "MEASURED"
    EXTRAPOLATED_FROM_MEASURED = "EXTRAPOLATED_FROM_MEASURED"
    SPECULATIVE = "SPECULATIVE"


class RuntimeDisposition(str, Enum):
    PLAUSIBLE = "PLAUSIBLE"
    OPTIMIZATION_REVIEW = "OPTIMIZATION_REVIEW"
    PERFORMANCE_IMPLEMENTATION_ANOMALY = "PERFORMANCE_IMPLEMENTATION_ANOMALY"
    RESOURCE_LIMIT_CANDIDATE = "RESOURCE_LIMIT_CANDIDATE"
    UNVALIDATED_ESTIMATE = "UNVALIDATED_ESTIMATE"


@dataclass(frozen=True)
class RuntimeSample:
    runtime_profile: str
    basis: EstimateBasis
    environment_steps: int
    optimizer_updates: int
    evaluations: int
    wall_seconds: float
    backend: str
    parallel: bool
    worker_count: int
    threads_per_worker: int
    target_steps: int


@dataclass(frozen=True)
class RuntimeAssessment:
    disposition: RuntimeDisposition
    steps_per_second: float | None
    estimated_seconds: float | None
    incident_level: str
    route_to: str
    user_authority_required: bool
    checks: tuple[str, ...]


PROFILER_CHECKLIST = (
    "unexpected sleep/wait", "debug/instrumented build", "serial fallback", "Python fallback",
    "C++ extension build every run", "worker count actually active", "thread oversubscription",
    "environment reset/step bottleneck", "IPC/serialization", "per-step disk/log writes",
    "accidental nested rollout/search", "model update cadence", "evaluation loop explosion",
)


def assess_runtime(sample: RuntimeSample) -> RuntimeAssessment:
    if sample.basis == EstimateBasis.SPECULATIVE:
        return RuntimeAssessment(RuntimeDisposition.UNVALIDATED_ESTIMATE, None, None, "E0_OBSERVATION", "CURRENT_EXECUTOR", False, PROFILER_CHECKLIST)
    if sample.environment_steps <= 0 or sample.wall_seconds <= 0 or sample.target_steps <= 0:
        raise ValueError("measured runtime samples require positive steps, target and wall_seconds")
    rate = sample.environment_steps / sample.wall_seconds
    estimated = sample.target_steps / rate
    profile = sample.runtime_profile.upper()
    if profile == "TOY_SMOKE":
        review, anomaly = 120.0, 600.0
    elif profile == "TOY_EXPLORATORY":
        review, anomaly = 1200.0, 3600.0
    elif profile == "PROOF_SIZED_MULTI_SEED":
        review, anomaly = 2 * 3600.0, 4 * 3600.0
    else:
        review, anomaly = 8 * 3600.0, float("inf")
    if estimated > anomaly:
        disposition = RuntimeDisposition.PERFORMANCE_IMPLEMENTATION_ANOMALY
        level, route = "E2_ASSIGNMENT_RECOVERY", "CM"
    elif estimated > review:
        disposition = RuntimeDisposition.OPTIMIZATION_REVIEW
        level, route = "E2_ASSIGNMENT_RECOVERY", "CM"
    else:
        disposition = RuntimeDisposition.PLAUSIBLE
        level, route = "E0_OBSERVATION", "CURRENT_EXECUTOR"
    checks = (f"throughput={rate:.6f} environment_steps_per_second", f"estimated_seconds={estimated:.3f}") + PROFILER_CHECKLIST
    return RuntimeAssessment(disposition, rate, estimated, level, route, False, checks)
