"""Large-count and eight-edit roster profiles for the frozen G8 policy."""

from __future__ import annotations

from typing import Callable

from ha_ctse_process.open_roster_high_churn_g9 import (
    ChurnEvent,
    ChurnLedger,
    ChurnProfile,
    make_churn_ledger,
)


MODERATE_SCALE_CAPACITY = 32
FAR_SCALE_CAPACITY = 48
MAXIMUM_ACTIVE_COUNT = 40


MODERATE_SCALE_CHURN_PROFILE = ChurnProfile(
    name="moderate_scale_churn_8_edits",
    initial_join=tuple(range(16)),
    events=(
        ChurnEvent(9, temporarily_left=tuple(range(8, 12))),
        ChurnEvent(13, rejoined=tuple(range(8, 12))),
        ChurnEvent(24, terminally_left=tuple(range(4))),
        ChurnEvent(28, joined=tuple(range(16, 24))),
        ChurnEvent(40, temporarily_left=tuple(range(12, 16))),
        ChurnEvent(
            44,
            rejoined=tuple(range(12, 16)),
            joined=tuple(range(24, 28)),
        ),
        ChurnEvent(64, terminally_left=tuple(range(4, 12))),
        ChurnEvent(68, joined=tuple(range(28, 32))),
    ),
    capacity=MODERATE_SCALE_CAPACITY,
    maximum_active_count=24,
)

FAR_SCALE_CHURN_PROFILE = ChurnProfile(
    name="far_scale_churn_8_edits",
    initial_join=tuple(range(24)),
    events=(
        ChurnEvent(9, temporarily_left=tuple(range(16, 24))),
        ChurnEvent(13, rejoined=tuple(range(16, 24))),
        ChurnEvent(24, terminally_left=tuple(range(8))),
        ChurnEvent(28, joined=tuple(range(24, 40))),
        ChurnEvent(40, temporarily_left=tuple(range(8, 16))),
        ChurnEvent(
            44,
            rejoined=tuple(range(8, 16)),
            joined=tuple(range(40, 48)),
        ),
        ChurnEvent(64, terminally_left=tuple(range(16, 32))),
        ChurnEvent(68, terminally_left=tuple(range(32, 40))),
    ),
    capacity=FAR_SCALE_CAPACITY,
    maximum_active_count=MAXIMUM_ACTIVE_COUNT,
)

OSCILLATING_SCALE_CHURN_PROFILE = ChurnProfile(
    name="oscillating_scale_churn_8_edits",
    initial_join=tuple(range(20)),
    events=(
        ChurnEvent(6, temporarily_left=tuple(range(12, 20))),
        ChurnEvent(10, rejoined=tuple(range(12, 20))),
        ChurnEvent(24, terminally_left=tuple(range(8))),
        ChurnEvent(28, joined=tuple(range(20, 36))),
        ChurnEvent(40, temporarily_left=tuple(range(8, 20))),
        ChurnEvent(
            44,
            rejoined=tuple(range(8, 20)),
            joined=tuple(range(36, 48)),
        ),
        ChurnEvent(60, temporarily_left=tuple(range(12, 20))),
        ChurnEvent(64, rejoined=tuple(range(12, 20))),
    ),
    capacity=FAR_SCALE_CAPACITY,
    maximum_active_count=MAXIMUM_ACTIVE_COUNT,
)

DOMAIN_PROFILES = {
    "moderate_scale_churn": (MODERATE_SCALE_CHURN_PROFILE,),
    "far_scale_churn": (FAR_SCALE_CHURN_PROFILE,),
    "mixed_churn": (OSCILLATING_SCALE_CHURN_PROFILE,),
}


def make_moderate_scale_churn_ledger(
    episode_id: int, *, master_seed: int = 2_381_000
) -> ChurnLedger:
    return make_churn_ledger(
        episode_id,
        master_seed=master_seed,
        profiles=DOMAIN_PROFILES["moderate_scale_churn"],
    )


def make_far_scale_churn_ledger(
    episode_id: int, *, master_seed: int = 2_381_100
) -> ChurnLedger:
    return make_churn_ledger(
        episode_id,
        master_seed=master_seed,
        profiles=DOMAIN_PROFILES["far_scale_churn"],
    )


def make_oscillating_scale_churn_ledger(
    episode_id: int, *, master_seed: int = 2_381_200
) -> ChurnLedger:
    return make_churn_ledger(
        episode_id,
        master_seed=master_seed,
        profiles=DOMAIN_PROFILES["mixed_churn"],
    )


LEDGER_FACTORIES: dict[str, Callable[..., ChurnLedger]] = {
    "moderate_scale_churn": make_moderate_scale_churn_ledger,
    "far_scale_churn": make_far_scale_churn_ledger,
    "mixed_churn": make_oscillating_scale_churn_ledger,
}
