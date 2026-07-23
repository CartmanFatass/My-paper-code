"""Episode-random valid membership processes for frozen-policy evaluation."""

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


EVENT_WINDOWS = (
    (4, 5, 6, 7, 8),
    (9,),
    tuple(range(14, 24)),
    (24,),
    (29, 30, 31),
    (32,),
    (37, 38, 39),
    (40,),
    (44, 45, 46, 47, 48),
    (49,),
    tuple(range(54, 64)),
    (64,),
)


@dataclass(frozen=True)
class RandomProcessSpec:
    name: str
    capacity: int
    minimum_active_count: int
    initial_count_low: int
    initial_count_high: int
    maximum_active_count: int
    maximum_batch: int

    def validate(self) -> None:
        if not (
            2 <= self.minimum_active_count
            < self.initial_count_low
            <= self.initial_count_high
            <= self.maximum_active_count
            <= self.capacity
        ):
            raise ValueError("random-process count contract is invalid")
        if not 1 <= self.maximum_batch < self.capacity:
            raise ValueError("random-process batch contract is invalid")


MODERATE_SPEC = RandomProcessSpec(
    name="random_moderate",
    capacity=48,
    minimum_active_count=4,
    initial_count_low=12,
    initial_count_high=32,
    maximum_active_count=40,
    maximum_batch=8,
)
WIDE_SPEC = RandomProcessSpec(
    name="random_wide",
    capacity=96,
    minimum_active_count=8,
    initial_count_low=24,
    initial_count_high=56,
    maximum_active_count=64,
    maximum_batch=12,
)
ULTRA_SPEC = RandomProcessSpec(
    name="random_ultra",
    capacity=96,
    minimum_active_count=12,
    initial_count_low=40,
    initial_count_high=72,
    maximum_active_count=80,
    maximum_batch=16,
)


def _rng(master_seed: int, episode_id: int) -> np.random.Generator:
    return np.random.default_rng(
        np.random.SeedSequence([int(master_seed), int(episode_id), 13])
    )


def _sample_keys(
    rng: np.random.Generator, keys: set[int], count: int
) -> tuple[int, ...]:
    ordered = np.asarray(sorted(keys), dtype=np.int64)
    chosen = rng.choice(ordered, size=int(count), replace=False)
    return tuple(sorted(int(value) for value in np.asarray(chosen).tolist()))


def make_random_process_profile(
    episode_id: int, *, master_seed: int, spec: RandomProcessSpec
) -> ChurnProfile:
    spec.validate()
    rng = _rng(master_seed, episode_id)
    event_times = tuple(
        int(rng.choice(np.asarray(window, dtype=np.int64)))
        for window in EVENT_WINDOWS
    )
    initial_count = int(
        rng.integers(spec.initial_count_low, spec.initial_count_high + 1)
    )
    all_keys = set(range(spec.capacity))
    initial = _sample_keys(rng, all_keys, initial_count)
    active = set(initial)
    temporarily_absent: set[int] = set()
    never_joined = all_keys - active
    events: list[ChurnEvent] = []

    for block in range(3):
        leave_limit = min(
            spec.maximum_batch,
            len(active) - spec.minimum_active_count,
        )
        leave_count = int(rng.integers(1, leave_limit + 1))
        temporarily_left = _sample_keys(rng, active, leave_count)
        active.difference_update(temporarily_left)
        temporarily_absent.update(temporarily_left)
        events.append(
            ChurnEvent(
                event_times[4 * block], temporarily_left=temporarily_left
            )
        )

        rejoined = tuple(sorted(temporarily_absent))
        active.update(rejoined)
        temporarily_absent.clear()
        events.append(ChurnEvent(event_times[4 * block + 1], rejoined=rejoined))

        terminal_limit = min(
            spec.maximum_batch,
            len(active) - spec.minimum_active_count,
        )
        terminal_count = int(rng.integers(1, terminal_limit + 1))
        terminally_left = _sample_keys(rng, active, terminal_count)
        active.difference_update(terminally_left)
        events.append(
            ChurnEvent(
                event_times[4 * block + 2], terminally_left=terminally_left
            )
        )

        join_limit = min(
            spec.maximum_batch,
            len(never_joined),
            spec.maximum_active_count - len(active),
        )
        join_count = int(rng.integers(1, join_limit + 1))
        joined = _sample_keys(rng, never_joined, join_count)
        never_joined.difference_update(joined)
        active.update(joined)
        events.append(ChurnEvent(event_times[4 * block + 3], joined=joined))

    profile = ChurnProfile(
        name=f"{spec.name}_episode_{int(episode_id)}",
        initial_join=initial,
        events=tuple(events),
        capacity=spec.capacity,
        maximum_active_count=spec.maximum_active_count,
        required_event_count=len(EVENT_WINDOWS),
    )
    profile.validate()
    return profile


def make_random_process_ledger(
    episode_id: int, *, master_seed: int, spec: RandomProcessSpec
) -> ChurnLedger:
    profile = make_random_process_profile(
        episode_id, master_seed=master_seed, spec=spec
    )
    return make_churn_ledger(
        episode_id,
        master_seed=master_seed,
        profiles=(profile,),
    )


def make_random_moderate_ledger(
    episode_id: int, *, master_seed: int = 3_481_000
) -> ChurnLedger:
    return make_random_process_ledger(
        episode_id, master_seed=master_seed, spec=MODERATE_SPEC
    )


def make_random_wide_ledger(
    episode_id: int, *, master_seed: int = 3_481_100
) -> ChurnLedger:
    return make_random_process_ledger(
        episode_id, master_seed=master_seed, spec=WIDE_SPEC
    )


def make_random_ultra_ledger(
    episode_id: int, *, master_seed: int = 3_481_200
) -> ChurnLedger:
    return make_random_process_ledger(
        episode_id, master_seed=master_seed, spec=ULTRA_SPEC
    )


DOMAIN_PROFILES = {
    "random_moderate": (
        make_random_process_profile(0, master_seed=3_481_000, spec=MODERATE_SPEC),
    ),
    "random_wide": (
        make_random_process_profile(0, master_seed=3_481_100, spec=WIDE_SPEC),
    ),
    "mixed_churn": (
        make_random_process_profile(0, master_seed=3_481_200, spec=ULTRA_SPEC),
    ),
}

LEDGER_FACTORIES: dict[str, Callable[..., ChurnLedger]] = {
    "random_moderate": make_random_moderate_ledger,
    "random_wide": make_random_wide_ledger,
    "mixed_churn": make_random_ultra_ledger,
}
