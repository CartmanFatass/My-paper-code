"""Frozen registration for CRTO-COMMON-HISTORY-GATE-20260830-01."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from numbers import Integral
from types import MappingProxyType
from typing import Final, Mapping

import numpy as np


OBJECT_ID: Final = "CRTO-COMMON-HISTORY-GATE-20260830-01"
SCHEMA_VERSION: Final = "crto-common-history-gate-result-v1"
RNG_NAMESPACE: Final = 2_026_083_001
REPLICATES: Final = tuple(range(8))
REPRESENTATIONS: Final = ("RAW", "TRUE_RESIDUAL", "CALIBRATED_DERANGEMENT")
BUDGETS: Final[Mapping[str, int]] = MappingProxyType({"SHORT": 128, "LONG": 2_048})
EVALUATION_REGIMES: Final = ("K8", "K16", "K4_TO_16", "K16_TO_4")
TARGET_REGIMES: Final = ("K16", "K4_TO_16", "K16_TO_4")
PREDICTOR_EPISODES: Final = 256
GATE_TRAIN_EPISODES: Final = 512
EVALUATION_EPISODES_PER_REGIME: Final = 64
OBSERVATION_DIM: Final = 42
PACKET_DIM: Final = 52
PREDICTOR_TARGET_DIM: Final = 8
ACTION_DIM: Final = 8
BATCH_SIZE: Final = 64
LEARNING_RATE: Final = 1e-3
ADAM_BETAS: Final = (0.9, 0.999)
ADAM_EPSILON: Final = 1e-8
GRADIENT_NORM_CAP: Final = 1.0
DISCOUNT: Final = 0.99
AUDIT_HORIZON: Final = 16
DELTA: Final = 0.005
CPU_WORKERS: Final = 1
PEAK_RSS_BYTES: Final = 2 * 1024**3
WALL_SECONDS: Final = 120 * 60
MAX_PRIMITIVE_TEAM_STEPS: Final = 2_596_864

RNG_PURPOSES: Final = (
    "panel_tape", "predictor_initialization", "predictor_order",
    "gate_initialization", "gate_order", "derangement",
)

# These clean-room policies are useful implementation seams but are not yet
# prospectively frozen by IMPLEMENTATION_THRESHOLD.md.  Registered execution must
# stop before using them for an optimizer update or result.
INHERITED_ASSUMPTIONS: Final[Mapping[str, str]] = MappingProxyType({
    "predictor_policy": "PROVISIONAL_FRESH_PREDICTOR_R01",
    "predictor_policy_status": "INHERITED_ASSUMPTION",
    "behavior_continuation_policy": "PROVISIONAL_DETERMINISTIC_SCRIPT_R01",
    "behavior_continuation_status": "INHERITED_ASSUMPTION",
    "calibration_population_policy": "CALLER_SUPPLIED_CALIBRATION_R01",
    "calibration_population_status": "INHERITED_ASSUMPTION",
    "gate_initialization_policy": "PROVISIONAL_GATE_INITIALIZATION_R01",
    "gate_initialization_status": "INHERITED_ASSUMPTION",
    "evaluation_population_policy": "LEGACY_B1_64_EPISODES_PER_REGIME",
    "evaluation_population_status": "INHERITED_ASSUMPTION",
    "audit_boundary_policy": "LEGACY_B1_ONSET_PLUS_4_TO_20_SWITCH_EXCLUSION",
    "audit_boundary_status": "INHERITED_ASSUMPTION",
})


def counter_seed(purpose: str, *coordinates: int) -> int:
    """Return a stable counter-addressed seed without consulting ambient RNG."""

    if purpose not in RNG_PURPOSES:
        raise ValueError(f"unknown RNG purpose: {purpose}")
    if any(isinstance(v, bool) or not isinstance(v, Integral) or int(v) < 0 for v in coordinates):
        raise ValueError("RNG coordinates must be nonnegative integers")
    material = ":".join((str(RNG_NAMESPACE), purpose, *(str(int(v)) for v in coordinates)))
    return int.from_bytes(sha256(material.encode("ascii")).digest()[:16], "little")


def counter_rng(purpose: str, *coordinates: int) -> np.random.Generator:
    """Construct a fresh PCG64 stream identified entirely by explicit counters."""

    return np.random.Generator(np.random.PCG64(counter_seed(purpose, *coordinates)))


@dataclass(frozen=True)
class RunConfig:
    object_id: str = OBJECT_ID
    replicates: tuple[int, ...] = REPLICATES
    predictor_episodes: int = PREDICTOR_EPISODES
    gate_train_episodes: int = GATE_TRAIN_EPISODES
    evaluation_episodes_per_regime: int = EVALUATION_EPISODES_PER_REGIME
    short_updates: int = BUDGETS["SHORT"]
    long_updates: int = BUDGETS["LONG"]
    batch_size: int = BATCH_SIZE
    cpu_workers: int = CPU_WORKERS
    gpu_enabled: bool = False
    peak_rss_bytes: int = PEAK_RSS_BYTES
    wall_seconds: int = WALL_SECONDS
    max_primitive_team_steps: int = MAX_PRIMITIVE_TEAM_STEPS

    def validate(self) -> None:
        if self.object_id != OBJECT_ID or self.replicates != REPLICATES:
            raise ValueError("object registration or replicate set drifted")
        if self.short_updates != 128 or self.long_updates != 2_048:
            raise ValueError("optimizer checkpoints drifted")
        if (
            self.predictor_episodes != PREDICTOR_EPISODES
            or self.gate_train_episodes != GATE_TRAIN_EPISODES
            or self.evaluation_episodes_per_regime != EVALUATION_EPISODES_PER_REGIME
        ):
            raise ValueError("panel population counts drifted")
        if self.batch_size != 64 or self.cpu_workers != 1 or self.gpu_enabled:
            raise ValueError("registered execution envelope drifted")
        if self.peak_rss_bytes != PEAK_RSS_BYTES:
            raise ValueError("RSS envelope drifted")
        if self.wall_seconds != WALL_SECONDS:
            raise ValueError("wall envelope drifted")
        if self.max_primitive_team_steps != MAX_PRIMITIVE_TEAM_STEPS:
            raise ValueError("primitive-step envelope drifted")

    @property
    def registered(self) -> bool:
        return self == PRODUCTION_CONFIG


PRODUCTION_CONFIG = RunConfig()
PRODUCTION_CONFIG.validate()
