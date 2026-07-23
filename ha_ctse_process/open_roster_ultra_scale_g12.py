"""N=48--80 scale stress profiles for the frozen G8 roster policy."""

from __future__ import annotations

from typing import Callable

from ha_ctse_process.open_roster_high_churn_g9 import (
    ChurnEvent,
    ChurnLedger,
    ChurnProfile,
    make_churn_ledger,
)


EDGE_CAPACITY = 64
FAR_CAPACITY = 80
ULTRA_CAPACITY = 96


EDGE_SCALE_PROFILE = ChurnProfile(
    name="edge_scale_churn_n48",
    initial_join=tuple(range(32)),
    events=(
        ChurnEvent(6, temporarily_left=tuple(range(20, 32))),
        ChurnEvent(10, rejoined=tuple(range(20, 32))),
        ChurnEvent(24, terminally_left=tuple(range(12))),
        ChurnEvent(28, joined=tuple(range(32, 56))),
        ChurnEvent(40, temporarily_left=tuple(range(12, 24))),
        ChurnEvent(
            44,
            rejoined=tuple(range(12, 24)),
            joined=tuple(range(56, 60)),
        ),
        ChurnEvent(60, terminally_left=tuple(range(24, 36))),
        ChurnEvent(64, terminally_left=tuple(range(36, 48))),
    ),
    capacity=EDGE_CAPACITY,
    maximum_active_count=48,
)

FAR_SCALE_PROFILE = ChurnProfile(
    name="far_scale_churn_n64",
    initial_join=tuple(range(40)),
    events=(
        ChurnEvent(6, temporarily_left=tuple(range(24, 40))),
        ChurnEvent(10, rejoined=tuple(range(24, 40))),
        ChurnEvent(24, terminally_left=tuple(range(16))),
        ChurnEvent(28, joined=tuple(range(40, 72))),
        ChurnEvent(40, temporarily_left=tuple(range(16, 32))),
        ChurnEvent(
            44,
            rejoined=tuple(range(16, 32)),
            joined=tuple(range(72, 80)),
        ),
        ChurnEvent(60, terminally_left=tuple(range(32, 48))),
        ChurnEvent(64, terminally_left=tuple(range(48, 64))),
    ),
    capacity=FAR_CAPACITY,
    maximum_active_count=64,
)

ULTRA_SCALE_PROFILE = ChurnProfile(
    name="ultra_scale_churn_n80",
    initial_join=tuple(range(48)),
    events=(
        ChurnEvent(6, temporarily_left=tuple(range(32, 48))),
        ChurnEvent(10, rejoined=tuple(range(32, 48))),
        ChurnEvent(24, terminally_left=tuple(range(16))),
        ChurnEvent(28, joined=tuple(range(48, 80))),
        ChurnEvent(40, temporarily_left=tuple(range(16, 32))),
        ChurnEvent(
            44,
            rejoined=tuple(range(16, 32)),
            joined=tuple(range(80, 96)),
        ),
        ChurnEvent(60, terminally_left=tuple(range(32, 48))),
        ChurnEvent(64, terminally_left=tuple(range(48, 64))),
    ),
    capacity=ULTRA_CAPACITY,
    maximum_active_count=80,
)


DOMAIN_PROFILES = {
    "edge_ultra_scale": (EDGE_SCALE_PROFILE,),
    "far_ultra_scale": (FAR_SCALE_PROFILE,),
    "mixed_churn": (ULTRA_SCALE_PROFILE,),
}


def make_edge_scale_ledger(
    episode_id: int, *, master_seed: int = 3_081_000
) -> ChurnLedger:
    return make_churn_ledger(
        episode_id,
        master_seed=master_seed,
        profiles=DOMAIN_PROFILES["edge_ultra_scale"],
    )


def make_far_scale_ledger(
    episode_id: int, *, master_seed: int = 3_081_100
) -> ChurnLedger:
    return make_churn_ledger(
        episode_id,
        master_seed=master_seed,
        profiles=DOMAIN_PROFILES["far_ultra_scale"],
    )


def make_ultra_scale_ledger(
    episode_id: int, *, master_seed: int = 3_081_200
) -> ChurnLedger:
    return make_churn_ledger(
        episode_id,
        master_seed=master_seed,
        profiles=DOMAIN_PROFILES["mixed_churn"],
    )


LEDGER_FACTORIES: dict[str, Callable[..., ChurnLedger]] = {
    "edge_ultra_scale": make_edge_scale_ledger,
    "far_ultra_scale": make_far_scale_ledger,
    "mixed_churn": make_ultra_scale_ledger,
}
