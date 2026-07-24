"""Atomic cold-start cohort-replacement processes for frozen-policy tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from ha_ctse_process.open_roster_high_churn_g9 import (
    ChurnEvent,
    ChurnLedger,
    ChurnProfile,
    make_churn_ledger,
)


REPLACEMENT_TIMES = (9, 24, 32, 40, 49, 64)


@dataclass(frozen=True)
class AtomicReplacementSpec:
    name: str
    capacity: int
    active_count_low: int
    active_count_high: int
    replacement_low: int
    replacement_high: int

    def validate(self) -> None:
        if not (
            2 <= self.replacement_low
            <= self.replacement_high
            < self.active_count_low
            <= self.active_count_high
            <= self.capacity
        ):
            raise ValueError("atomic replacement count contract is invalid")
        if (
            self.active_count_high
            + len(REPLACEMENT_TIMES) * self.replacement_high
            > self.capacity
        ):
            raise ValueError("atomic replacement capacity is insufficient")


MODERATE_SPEC = AtomicReplacementSpec(
    name="atomic_moderate",
    capacity=64,
    active_count_low=12,
    active_count_high=20,
    replacement_low=2,
    replacement_high=6,
)
WIDE_SPEC = AtomicReplacementSpec(
    name="atomic_wide",
    capacity=144,
    active_count_low=32,
    active_count_high=48,
    replacement_low=6,
    replacement_high=14,
)
ULTRA_SPEC = AtomicReplacementSpec(
    name="atomic_ultra",
    capacity=192,
    active_count_low=64,
    active_count_high=80,
    replacement_low=10,
    replacement_high=18,
)


def _rng(master_seed: int, episode_id: int) -> np.random.Generator:
    return np.random.default_rng(
        np.random.SeedSequence([int(master_seed), int(episode_id), 14])
    )


def _sample_keys(
    rng: np.random.Generator, keys: set[int], count: int
) -> tuple[int, ...]:
    ordered = np.asarray(sorted(keys), dtype=np.int64)
    chosen = rng.choice(ordered, size=int(count), replace=False)
    return tuple(sorted(int(value) for value in np.asarray(chosen).tolist()))


def make_atomic_replacement_profile(
    episode_id: int, *, master_seed: int, spec: AtomicReplacementSpec
) -> ChurnProfile:
    spec.validate()
    rng = _rng(master_seed, episode_id)
    active_count = int(
        rng.integers(spec.active_count_low, spec.active_count_high + 1)
    )
    all_keys = set(range(spec.capacity))
    initial = _sample_keys(rng, all_keys, active_count)
    active = set(initial)
    never_joined = all_keys - active
    events: list[ChurnEvent] = []
    for time in REPLACEMENT_TIMES:
        replacement_count = int(
            rng.integers(spec.replacement_low, spec.replacement_high + 1)
        )
        terminally_left = _sample_keys(rng, active, replacement_count)
        joined = _sample_keys(rng, never_joined, replacement_count)
        active.difference_update(terminally_left)
        never_joined.difference_update(joined)
        active.update(joined)
        events.append(
            ChurnEvent(
                time,
                joined=joined,
                terminally_left=terminally_left,
            )
        )

    profile = ChurnProfile(
        name=f"{spec.name}_episode_{int(episode_id)}",
        initial_join=initial,
        events=tuple(events),
        capacity=spec.capacity,
        maximum_active_count=spec.active_count_high,
        required_event_count=len(REPLACEMENT_TIMES),
    )
    profile.validate()
    if any(
        not event.joined
        or not event.terminally_left
        or len(event.joined) != len(event.terminally_left)
        for event in profile.events
    ):
        raise ValueError("atomic replacement transaction is not count preserving")
    return profile


def make_atomic_replacement_ledger(
    episode_id: int, *, master_seed: int, spec: AtomicReplacementSpec
) -> ChurnLedger:
    profile = make_atomic_replacement_profile(
        episode_id, master_seed=master_seed, spec=spec
    )
    return make_churn_ledger(
        episode_id,
        master_seed=master_seed,
        profiles=(profile,),
    )


def make_atomic_moderate_ledger(
    episode_id: int, *, master_seed: int = 3_881_000
) -> ChurnLedger:
    return make_atomic_replacement_ledger(
        episode_id, master_seed=master_seed, spec=MODERATE_SPEC
    )


def make_atomic_wide_ledger(
    episode_id: int, *, master_seed: int = 3_881_100
) -> ChurnLedger:
    return make_atomic_replacement_ledger(
        episode_id, master_seed=master_seed, spec=WIDE_SPEC
    )


def make_atomic_ultra_ledger(
    episode_id: int, *, master_seed: int = 3_881_200
) -> ChurnLedger:
    return make_atomic_replacement_ledger(
        episode_id, master_seed=master_seed, spec=ULTRA_SPEC
    )


DOMAIN_PROFILES = {
    "atomic_moderate": (
        make_atomic_replacement_profile(0, master_seed=3_881_000, spec=MODERATE_SPEC),
    ),
    "atomic_wide": (
        make_atomic_replacement_profile(0, master_seed=3_881_100, spec=WIDE_SPEC),
    ),
    "mixed_churn": (
        make_atomic_replacement_profile(0, master_seed=3_881_200, spec=ULTRA_SPEC),
    ),
}

LEDGER_FACTORIES: dict[str, Callable[..., ChurnLedger]] = {
    "atomic_moderate": make_atomic_moderate_ledger,
    "atomic_wide": make_atomic_wide_ledger,
    "mixed_churn": make_atomic_ultra_ledger,
}
