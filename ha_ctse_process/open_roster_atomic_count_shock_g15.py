"""Atomic identity replacement composed with large active-count shocks."""

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


SHOCK_TIMES = (9, 24, 32, 40, 49, 64)


@dataclass(frozen=True)
class AtomicCountShockSpec:
    name: str
    capacity: int
    low_count_low: int
    low_count_high: int
    high_count_low: int
    high_count_high: int
    turnover_low: int
    turnover_high: int

    def validate(self) -> None:
        if not (
            2 <= self.turnover_low
            <= self.turnover_high
            < self.low_count_low
            <= self.low_count_high
            < self.high_count_low
            <= self.high_count_high
            <= self.capacity
        ):
            raise ValueError("atomic count-shock contract is invalid")
        maximum_unique_keys = (
            self.low_count_high
            + 3 * (self.high_count_high - self.low_count_low)
            + len(SHOCK_TIMES) * self.turnover_high
        )
        if maximum_unique_keys > self.capacity:
            raise ValueError("atomic count-shock capacity is insufficient")


MODERATE_SPEC = AtomicCountShockSpec(
    name="shock_moderate",
    capacity=128,
    low_count_low=12,
    low_count_high=16,
    high_count_low=24,
    high_count_high=32,
    turnover_low=2,
    turnover_high=4,
)
WIDE_SPEC = AtomicCountShockSpec(
    name="shock_wide",
    capacity=192,
    low_count_low=28,
    low_count_high=32,
    high_count_low=52,
    high_count_high=64,
    turnover_low=4,
    turnover_high=6,
)
ULTRA_SPEC = AtomicCountShockSpec(
    name="shock_ultra",
    capacity=224,
    low_count_low=40,
    low_count_high=48,
    high_count_low=72,
    high_count_high=80,
    turnover_low=6,
    turnover_high=8,
)


def _rng(master_seed: int, episode_id: int) -> np.random.Generator:
    return np.random.default_rng(
        np.random.SeedSequence([int(master_seed), int(episode_id), 15])
    )


def _sample_keys(
    rng: np.random.Generator, keys: set[int], count: int
) -> tuple[int, ...]:
    ordered = np.asarray(sorted(keys), dtype=np.int64)
    chosen = rng.choice(ordered, size=int(count), replace=False)
    return tuple(sorted(int(value) for value in np.asarray(chosen).tolist()))


def make_atomic_count_shock_profile(
    episode_id: int, *, master_seed: int, spec: AtomicCountShockSpec
) -> ChurnProfile:
    spec.validate()
    rng = _rng(master_seed, episode_id)
    initial_count = int(
        rng.integers(spec.low_count_low, spec.low_count_high + 1)
    )
    all_keys = set(range(spec.capacity))
    initial = _sample_keys(rng, all_keys, initial_count)
    active = set(initial)
    never_joined = all_keys - active
    events: list[ChurnEvent] = []

    for event_index, time in enumerate(SHOCK_TIMES):
        high_target = event_index % 2 == 0
        target = int(
            rng.integers(
                spec.high_count_low if high_target else spec.low_count_low,
                (spec.high_count_high if high_target else spec.low_count_high) + 1,
            )
        )
        current = len(active)
        turnover = int(
            rng.integers(spec.turnover_low, spec.turnover_high + 1)
        )
        if target > current:
            terminal_count = turnover
            join_count = turnover + target - current
        else:
            join_count = turnover
            terminal_count = turnover + current - target

        terminally_left = _sample_keys(rng, active, terminal_count)
        joined = _sample_keys(rng, never_joined, join_count)
        active.difference_update(terminally_left)
        never_joined.difference_update(joined)
        active.update(joined)
        if len(active) != target:
            raise AssertionError("atomic count-shock target reconstruction failed")
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
        maximum_active_count=spec.high_count_high,
        required_event_count=len(SHOCK_TIMES),
    )
    profile.validate()
    if any(
        not event.joined
        or not event.terminally_left
        or len(event.joined) == len(event.terminally_left)
        for event in profile.events
    ):
        raise ValueError("atomic count shock must use unequal positive cohorts")
    return profile


def make_atomic_count_shock_ledger(
    episode_id: int, *, master_seed: int, spec: AtomicCountShockSpec
) -> ChurnLedger:
    profile = make_atomic_count_shock_profile(
        episode_id, master_seed=master_seed, spec=spec
    )
    return make_churn_ledger(
        episode_id,
        master_seed=master_seed,
        profiles=(profile,),
    )


def make_shock_moderate_ledger(
    episode_id: int, *, master_seed: int = 4_181_000
) -> ChurnLedger:
    return make_atomic_count_shock_ledger(
        episode_id, master_seed=master_seed, spec=MODERATE_SPEC
    )


def make_shock_wide_ledger(
    episode_id: int, *, master_seed: int = 4_181_100
) -> ChurnLedger:
    return make_atomic_count_shock_ledger(
        episode_id, master_seed=master_seed, spec=WIDE_SPEC
    )


def make_shock_ultra_ledger(
    episode_id: int, *, master_seed: int = 4_181_200
) -> ChurnLedger:
    return make_atomic_count_shock_ledger(
        episode_id, master_seed=master_seed, spec=ULTRA_SPEC
    )


DOMAIN_PROFILES = {
    "shock_moderate": (
        make_atomic_count_shock_profile(
            0, master_seed=4_181_000, spec=MODERATE_SPEC
        ),
    ),
    "shock_wide": (
        make_atomic_count_shock_profile(0, master_seed=4_181_100, spec=WIDE_SPEC),
    ),
    "mixed_churn": (
        make_atomic_count_shock_profile(0, master_seed=4_181_200, spec=ULTRA_SPEC),
    ),
}

LEDGER_FACTORIES: dict[str, Callable[..., ChurnLedger]] = {
    "shock_moderate": make_shock_moderate_ledger,
    "shock_wide": make_shock_wide_ledger,
    "mixed_churn": make_shock_ultra_ledger,
}
