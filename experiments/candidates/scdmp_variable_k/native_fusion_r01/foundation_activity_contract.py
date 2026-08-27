"""Prospective CLOSED-R01 foundation counts without activity identities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


S2_SLICE: Final[str] = "SCDMP-NATIVE-FUSION-R01-S2-FOUNDATION-PREACTIVITY-V1"
REPLICATES: Final[int] = 24
UPDATES_PER_FOUNDATION: Final[int] = 192
EPISODES_PER_UPDATE: Final[int] = 16
STRUCTURAL_STEPS_PER_UPDATE: Final[int] = 16


@dataclass(frozen=True)
class ProspectiveReplicate:
    replicate_index: int
    registered: bool = False
    activity_authorized: bool = False
    identity_materialized: bool = False


@dataclass(frozen=True)
class EpisodeSlot:
    slot_index: int
    k: int
    order: str
    stochastic_address_present: bool = False


@dataclass(frozen=True)
class UpdateAllocation:
    update_index: int
    slots: tuple[EpisodeSlot, ...]
    structural_steps: int = STRUCTURAL_STEPS_PER_UPDATE


@dataclass(frozen=True)
class ProspectiveCounts:
    replicates: int
    updates_per_foundation: int
    episodes_per_update: int
    structural_steps_per_update: int
    episodes_per_foundation: int
    steps_per_foundation: int
    total_foundation_episodes: int
    total_foundation_steps: int


def prospective_roster() -> tuple[ProspectiveReplicate, ...]:
    return tuple(ProspectiveReplicate(index) for index in range(REPLICATES))


def update_allocation(update_index: int) -> UpdateAllocation:
    if (
        isinstance(update_index, bool)
        or not isinstance(update_index, int)
        or not 1 <= update_index <= UPDATES_PER_FOUNDATION
    ):
        raise ValueError("update_index must be an integer in [1,192]")
    slots: list[EpisodeSlot] = []
    for k in (4, 10):
        for order in ("RG", "GR"):
            for _ in range(4):
                slots.append(EpisodeSlot(len(slots), k, order))
    return UpdateAllocation(update_index=update_index, slots=tuple(slots))


def prospective_counts() -> ProspectiveCounts:
    per_foundation = UPDATES_PER_FOUNDATION * EPISODES_PER_UPDATE
    steps_per_foundation = UPDATES_PER_FOUNDATION * STRUCTURAL_STEPS_PER_UPDATE
    return ProspectiveCounts(
        replicates=REPLICATES,
        updates_per_foundation=UPDATES_PER_FOUNDATION,
        episodes_per_update=EPISODES_PER_UPDATE,
        structural_steps_per_update=STRUCTURAL_STEPS_PER_UPDATE,
        episodes_per_foundation=per_foundation,
        steps_per_foundation=steps_per_foundation,
        total_foundation_episodes=REPLICATES * per_foundation,
        total_foundation_steps=REPLICATES * steps_per_foundation,
    )
