"""Frozen registration for the Pro-closed ONLGR-B2 revision 02."""

from __future__ import annotations

from dataclasses import dataclass

TREATMENT = "ONLGR-B2-STATE-BLIND-EVENT-RATE-FLEXIBILITY"
REVISION = "ONLGR-B2-SCIENCE-20260814-02"
ARTIFACT_KIND = "ONLGR_B2_STATE_BLIND_EVENT_RATE_FLEXIBILITY_RESULT"
FRONTIER_REVISION = "ONLGR_B2_ATOMIC_FRONTIER_V1"
HORIZON = 256
LEASE_TICKS = 12
ROLES = ("T", "R")
ACTIONS = ("KEEP", "REFRESH-SAME", "REBIND")
ARMS = ("RATE-FLEX", "RATE-CONST")
TRAIN_SCHEDULES = ("CONST-8", "CONST-24", "MID-8-TO-24", "MID-24-TO-8")
IID_SCHEDULE = "RAND-IID-4-16-32"
SEEDS = (137, 149, 163, 181, 199, 223, 239, 257)

GAMMA_TICK = 0.99 ** (1.0 / 8.0)
LAMBDA_TICK = 0.95 ** (1.0 / 8.0)
RHO = 0.5
PPO_CLIP = 0.20
LEARNING_RATE = 3e-4
VALUE_COEFFICIENT = 0.5
ENTROPY_COEFFICIENT = 0.0
GRADIENT_NORM_CAP = 1.0
PPO_EPOCHS = 4
UPDATES = 8
EPISODES_PER_UPDATE = 32
TRAIN_EPISODES_PER_ARM_SEED = 256
IID_EPISODES_PER_ARM_SEED = 32
SAFETY_EPISODES_PER_ARM_SEED = 16
KEEP_EPISODES_PER_ARM_SEED = 16
DIAGNOSTIC_EXPOSURES = (1, 4, 8, 16, 24, 32)
DIAGNOSTIC_GRID = tuple(
    (age, delta, exposure)
    for age in (0, 16, 32, 64)
    for delta, exposure in ((4, 4), (8, 8), (16, 16), (24, 24), (32, 32))
)

CARD_RELATIVE_PATH = (
    "docs/research/candidates/opportunity_normalized_lease_gated_rebinding/"
    "ONLGR_B2_STATE_BLIND_EVENT_RATE_FLEXIBILITY_SCIENCE_CARD.md"
)
CLOSURE_RELATIVE_PATH = (
    "docs/research/candidates/opportunity_normalized_lease_gated_rebinding/"
    "ONLGR_B2_EXTERNAL_PRO_MATHEMATICAL_CLOSURE_INTAKE.md"
)


@dataclass(frozen=True)
class RunConfig:
    horizon: int = HORIZON
    seeds: tuple[int, ...] = SEEDS
    updates: int = UPDATES
    episodes_per_update: int = EPISODES_PER_UPDATE
    iid_episodes: int = IID_EPISODES_PER_ARM_SEED
    safety_episodes: int = SAFETY_EPISODES_PER_ARM_SEED
    keep_episodes: int = KEEP_EPISODES_PER_ARM_SEED
    cpu_threads: int = 1

    @property
    def registered(self) -> bool:
        return self == PRODUCTION_CONFIG


PRODUCTION_CONFIG = RunConfig()


def registered_work() -> dict[str, int]:
    cells = len(ARMS) * len(SEEDS)
    training = cells * TRAIN_EPISODES_PER_ARM_SEED * HORIZON
    iid = cells * IID_EPISODES_PER_ARM_SEED * HORIZON
    safety = cells * SAFETY_EPISODES_PER_ARM_SEED * HORIZON
    keep = cells * KEEP_EPISODES_PER_ARM_SEED * HORIZON
    return {
        "training_team_ticks": training,
        "iid_team_ticks": iid,
        "safety_team_ticks": safety,
        "keep_replay_team_ticks": keep,
        "total_team_ticks": training + iid + safety + keep,
        "training_episodes": cells * TRAIN_EPISODES_PER_ARM_SEED,
        "iid_episodes": cells * IID_EPISODES_PER_ARM_SEED,
        "safety_episodes": cells * SAFETY_EPISODES_PER_ARM_SEED,
        "keep_replay_episodes": cells * KEEP_EPISODES_PER_ARM_SEED,
    }
