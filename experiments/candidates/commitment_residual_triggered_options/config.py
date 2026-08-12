"""Frozen CRTO-B1 registration constants.

This module deliberately contains only the prospective registration.  Runtime
code must not use evaluation observations to alter any value declared here.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Mapping


REVISION: Final = "CRTO-B1-SCIENCE-20260812-04"
TREATMENT: Final = "CRTO-B1-COMMITMENT-RESIDUAL-TRIGGERED-OPTIONS"
ARTIFACT_KIND: Final = "CRTO_B1_REGISTERED_RESULT"

HORIZON: Final = 256
AGENT_COUNT: Final = 4
PREDICTOR_DATA_EPISODES: Final = 256
PREDICTOR_FIT_EPISODES: Final = 128
CALIBRATION_EPISODES: Final = 64
DEVELOPMENT_EPISODES: Final = 64
TRAINING_EPISODES_PER_ARM: Final = 1_024
EPISODES_PER_PPO_UPDATE: Final = 32
PPO_EPOCHS: Final = 4
PPO_MINIBATCH_EPISODES: Final = 8
PREDICTOR_UPDATES: Final = 400
PREDICTOR_BATCH_SIZE: Final = 256

ALGORITHM_SEEDS: Final = (2101, 2111, 2129, 2141, 2161, 2179, 2203, 2221)
TRAIN_KS: Final = (4, 8)
REGIMES: Final = ("K8", "K16", "K4_TO_16", "K16_TO_4")
EVENT_CLASSES: Final = (
    "NONE", "UNANNOUNCED-DIFFERENTIAL", "CUED-DIFFERENTIAL", "COMMON-SENSOR",
)
COST_REGIMES: Final = (0.25, 4.0)
OPTIONS: Final = (
    "TRACK-L", "TRACK-R", "RELAY-L", "RELAY-R", "TRANSIT-L", "TRANSIT-R", "RETURN",
)
LEARNED_ARMS: Final = ("CRTO", "FULL-HISTORY-AUX-TERM")
CUT_ARMS: Final = (
    "DERANGED-RESIDUAL-CRTO", "Q-ONLY-CRTO", "RATE-MATCHED-HAZARD-CRTO",
    "FORCED-RENEWAL-ONLY",
)
COMPLETE_ROLLOUT_CUT_ARMS: Final = CUT_ARMS[1:]

SCORING_EPISODES_PER_REGIME: Final = 64
HAZARD_DEVELOPMENT_EPISODES_PER_REGIME: Final = 64
DONOR_EPISODES_PER_REGIME: Final = 256
MAX_AUDIT_ACTIONS: Final = 7
AUDIT_HORIZON: Final = 16

PREDICTOR_INITIALIZATION_SEED_OFFSET: Final = 400_000
PREDICTOR_PERMUTATION_SEED_OFFSET: Final = 500_000
PROBE_PERMUTATION_SEED_OFFSET: Final = 600_000
PROBE_INITIALIZATION_SEED_OFFSET: Final = 610_000
LEARNED_INITIALIZATION_SEED_OFFSET: Final = 800_000
DERANGEMENT_SEED_BASE: Final = 7_000_003
DERANGEMENT_SEED_MULTIPLIER: Final = 1_009

PPO: Final[Mapping[str, float | int]] = MappingProxyType({
    "gamma": 0.99, "gae_lambda": 0.95, "clip": 0.20,
    "learning_rate": 3e-4, "value_coefficient": 0.5,
    "entropy_coefficient": 0.01, "gradient_norm_cap": 0.5,
    "episodes_per_update": EPISODES_PER_PPO_UPDATE, "epochs": PPO_EPOCHS,
    "minibatch_episodes": PPO_MINIBATCH_EPISODES,
})
PREDICTOR_OPTIMIZER: Final[Mapping[str, float | int | tuple[float, float]]] = MappingProxyType({
    "learning_rate": 1e-3, "betas": (0.9, 0.999), "epsilon": 1e-8,
    "weight_decay": 1e-5, "gradient_norm_cap": 1.0,
    "updates": PREDICTOR_UPDATES, "batch_size": PREDICTOR_BATCH_SIZE,
})

LEDGER_FORMULAS: Final[Mapping[str, str]] = MappingProxyType({
    "predictor_data": "8 seeds * 256 episodes * 256",
    "learned_arm_training": "8 seeds * 2 arms * 1024 episodes * 256",
    "hazard_development": "8 seeds * 4 regimes * 64 episodes * 256",
    "main_evaluation": "8 seeds * 2 arms * 4 regimes * 64 episodes * 256",
    "complete_rollout_cuts": "8 seeds * 3 cuts * 4 regimes * 64 episodes * 256",
    "donor_only": "8 seeds * 4 regimes * 256 episodes * 256",
    "deranged_replays": "8 seeds * 4 regimes * 64 episodes * 256",
    "audit_action_enumeration": "8 seeds * 4 regimes * 64 episodes * at most 7 actions * 16",
})
LEDGER_MAX_STEPS: Final[Mapping[str, int]] = MappingProxyType({
    "predictor_data": 524_288,
    "learned_arm_training": 4_194_304,
    "hazard_development": 524_288,
    "main_evaluation": 1_048_576,
    "complete_rollout_cuts": 1_572_864,
    "donor_only": 2_097_152,
    "deranged_replays": 524_288,
    "audit_action_enumeration": 229_376,
})
REGISTERED_MAX_STEPS: Final = 10_715_136


@dataclass(frozen=True)
class RunConfig:
    """The only executable CRTO-B1 resource envelope."""

    revision: str = REVISION
    horizon: int = HORIZON
    algorithm_seeds: tuple[int, ...] = ALGORITHM_SEEDS
    cpu_workers: int = 1
    gpu_enabled: bool = False
    peak_rss_bytes: int = 2 * 1024**3
    wall_seconds: int = 120 * 60
    registered_max_steps: int = REGISTERED_MAX_STEPS

    @property
    def registered(self) -> bool:
        return self == PRODUCTION_CONFIG


PRODUCTION_CONFIG = RunConfig()


def registered_ledger() -> dict[str, int]:
    """Return a detached copy so runtime accounting cannot mutate registration."""
    values = dict(LEDGER_MAX_STEPS)
    values["registered_maximum"] = REGISTERED_MAX_STEPS
    if sum(LEDGER_MAX_STEPS.values()) != REGISTERED_MAX_STEPS:
        raise RuntimeError("CRTO registered ledger constants are incoherent")
    return values
