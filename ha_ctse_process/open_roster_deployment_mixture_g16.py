"""Fresh-seed deployment mixture over supported dynamic-roster processes."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable

import numpy as np

from ha_ctse_process.open_roster_atomic_count_shock_g15 import (
    AtomicCountShockSpec,
    make_atomic_count_shock_profile,
)
from ha_ctse_process.open_roster_high_churn_g9 import (
    ChurnEvent,
    ChurnLedger,
    ChurnProfile,
    make_churn_ledger,
)


ATOMIC_TIMES = (9, 24, 32, 40, 49, 64)
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
PROCESS_MODES = ("serial_random", "atomic_equal", "atomic_shock")


@dataclass(frozen=True)
class DeploymentMixtureSpec:
    name: str
    capacity: int
    minimum_active_count: int
    initial_count_low: int
    initial_count_high: int
    maximum_active_count: int
    maximum_batch: int
    equal_count_low: int
    equal_count_high: int
    equal_replacement_low: int
    equal_replacement_high: int
    shock_spec: AtomicCountShockSpec

    def validate(self) -> None:
        if not (
            2 <= self.minimum_active_count
            < self.initial_count_low
            <= self.initial_count_high
            <= self.maximum_active_count
            <= self.capacity
        ):
            raise ValueError("deployment random-process count contract is invalid")
        if not 1 <= self.maximum_batch < self.capacity:
            raise ValueError("deployment random-process batch contract is invalid")
        if not (
            2 <= self.equal_replacement_low
            <= self.equal_replacement_high
            < self.equal_count_low
            <= self.equal_count_high
            <= self.maximum_active_count
        ):
            raise ValueError("deployment equal-atomic contract is invalid")
        if (
            self.equal_count_high
            + len(ATOMIC_TIMES) * self.equal_replacement_high
            > self.capacity
        ):
            raise ValueError("deployment equal-atomic capacity is insufficient")
        self.shock_spec.validate()
        if self.shock_spec.capacity != self.capacity:
            raise ValueError("deployment shock capacity mismatch")


MODERATE_SPEC = DeploymentMixtureSpec(
    name="deployment_moderate",
    capacity=128,
    minimum_active_count=4,
    initial_count_low=12,
    initial_count_high=32,
    maximum_active_count=40,
    maximum_batch=8,
    equal_count_low=12,
    equal_count_high=32,
    equal_replacement_low=2,
    equal_replacement_high=6,
    shock_spec=AtomicCountShockSpec(
        "deployment_shock_moderate", 128, 12, 16, 24, 32, 2, 4
    ),
)
WIDE_SPEC = DeploymentMixtureSpec(
    name="deployment_wide",
    capacity=192,
    minimum_active_count=8,
    initial_count_low=24,
    initial_count_high=56,
    maximum_active_count=64,
    maximum_batch=12,
    equal_count_low=28,
    equal_count_high=64,
    equal_replacement_low=6,
    equal_replacement_high=14,
    shock_spec=AtomicCountShockSpec(
        "deployment_shock_wide", 192, 28, 32, 52, 64, 4, 6
    ),
)
ULTRA_SPEC = DeploymentMixtureSpec(
    name="deployment_ultra",
    capacity=224,
    minimum_active_count=12,
    initial_count_low=40,
    initial_count_high=72,
    maximum_active_count=80,
    maximum_batch=16,
    equal_count_low=40,
    equal_count_high=80,
    equal_replacement_low=10,
    equal_replacement_high=18,
    shock_spec=AtomicCountShockSpec(
        "deployment_shock_ultra", 224, 40, 48, 72, 80, 6, 8
    ),
)


def _rng(master_seed: int, episode_id: int, stream: int) -> np.random.Generator:
    return np.random.default_rng(
        np.random.SeedSequence(
            [int(master_seed), int(episode_id), 16, int(stream)]
        )
    )


def _sample_keys(
    rng: np.random.Generator, keys: set[int], count: int
) -> tuple[int, ...]:
    ordered = np.asarray(sorted(keys), dtype=np.int64)
    chosen = rng.choice(ordered, size=int(count), replace=False)
    return tuple(sorted(int(value) for value in np.asarray(chosen).tolist()))


def deployment_process_mode(episode_id: int, *, master_seed: int) -> str:
    return PROCESS_MODES[(int(episode_id) + int(master_seed)) % len(PROCESS_MODES)]


def _make_serial_random_profile(
    episode_id: int, *, master_seed: int, spec: DeploymentMixtureSpec
) -> ChurnProfile:
    rng = _rng(master_seed, episode_id, 1)
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
    absent: set[int] = set()
    never_joined = all_keys - active
    events: list[ChurnEvent] = []
    for block in range(3):
        leave_count = int(
            rng.integers(
                1,
                min(spec.maximum_batch, len(active) - spec.minimum_active_count)
                + 1,
            )
        )
        temporarily_left = _sample_keys(rng, active, leave_count)
        active.difference_update(temporarily_left)
        absent.update(temporarily_left)
        events.append(
            ChurnEvent(event_times[4 * block], temporarily_left=temporarily_left)
        )

        rejoined = tuple(sorted(absent))
        active.update(rejoined)
        absent.clear()
        events.append(ChurnEvent(event_times[4 * block + 1], rejoined=rejoined))

        terminal_count = int(
            rng.integers(
                1,
                min(spec.maximum_batch, len(active) - spec.minimum_active_count)
                + 1,
            )
        )
        terminally_left = _sample_keys(rng, active, terminal_count)
        active.difference_update(terminally_left)
        events.append(
            ChurnEvent(
                event_times[4 * block + 2], terminally_left=terminally_left
            )
        )

        join_count = int(
            rng.integers(
                1,
                min(
                    spec.maximum_batch,
                    len(never_joined),
                    spec.maximum_active_count - len(active),
                )
                + 1,
            )
        )
        joined = _sample_keys(rng, never_joined, join_count)
        never_joined.difference_update(joined)
        active.update(joined)
        events.append(ChurnEvent(event_times[4 * block + 3], joined=joined))

    return ChurnProfile(
        name=f"{spec.name}_serial_random_episode_{int(episode_id)}",
        initial_join=initial,
        events=tuple(events),
        capacity=spec.capacity,
        maximum_active_count=spec.maximum_active_count,
        required_event_count=len(EVENT_WINDOWS),
    )


def _make_atomic_equal_profile(
    episode_id: int, *, master_seed: int, spec: DeploymentMixtureSpec
) -> ChurnProfile:
    rng = _rng(master_seed, episode_id, 2)
    active_count = int(
        rng.integers(spec.equal_count_low, spec.equal_count_high + 1)
    )
    all_keys = set(range(spec.capacity))
    initial = _sample_keys(rng, all_keys, active_count)
    active = set(initial)
    never_joined = all_keys - active
    events: list[ChurnEvent] = []
    for time in ATOMIC_TIMES:
        count = int(
            rng.integers(
                spec.equal_replacement_low, spec.equal_replacement_high + 1
            )
        )
        terminally_left = _sample_keys(rng, active, count)
        joined = _sample_keys(rng, never_joined, count)
        active.difference_update(terminally_left)
        never_joined.difference_update(joined)
        active.update(joined)
        events.append(
            ChurnEvent(time, joined=joined, terminally_left=terminally_left)
        )
    return ChurnProfile(
        name=f"{spec.name}_atomic_equal_episode_{int(episode_id)}",
        initial_join=initial,
        events=tuple(events),
        capacity=spec.capacity,
        maximum_active_count=spec.maximum_active_count,
        required_event_count=len(ATOMIC_TIMES),
    )


def make_deployment_mixture_profile(
    episode_id: int, *, master_seed: int, spec: DeploymentMixtureSpec
) -> ChurnProfile:
    spec.validate()
    mode = deployment_process_mode(episode_id, master_seed=master_seed)
    if mode == "serial_random":
        profile = _make_serial_random_profile(
            episode_id, master_seed=master_seed, spec=spec
        )
    elif mode == "atomic_equal":
        profile = _make_atomic_equal_profile(
            episode_id, master_seed=master_seed, spec=spec
        )
    else:
        profile = replace(
            make_atomic_count_shock_profile(
                episode_id, master_seed=master_seed, spec=spec.shock_spec
            ),
            name=f"{spec.name}_atomic_shock_episode_{int(episode_id)}",
        )
    profile.validate()
    return profile


def make_deployment_mixture_ledger(
    episode_id: int, *, master_seed: int, spec: DeploymentMixtureSpec
) -> ChurnLedger:
    profile = make_deployment_mixture_profile(
        episode_id, master_seed=master_seed, spec=spec
    )
    return make_churn_ledger(
        episode_id,
        master_seed=master_seed,
        profiles=(profile,),
    )


def make_deployment_moderate_ledger(
    episode_id: int, *, master_seed: int = 4_481_000
) -> ChurnLedger:
    return make_deployment_mixture_ledger(
        episode_id, master_seed=master_seed, spec=MODERATE_SPEC
    )


def make_deployment_wide_ledger(
    episode_id: int, *, master_seed: int = 4_481_100
) -> ChurnLedger:
    return make_deployment_mixture_ledger(
        episode_id, master_seed=master_seed, spec=WIDE_SPEC
    )


def make_deployment_ultra_ledger(
    episode_id: int, *, master_seed: int = 4_481_200
) -> ChurnLedger:
    return make_deployment_mixture_ledger(
        episode_id, master_seed=master_seed, spec=ULTRA_SPEC
    )


DOMAIN_PROFILES = {
    "deployment_moderate": (
        make_deployment_mixture_profile(
            0, master_seed=4_481_000, spec=MODERATE_SPEC
        ),
    ),
    "deployment_wide": (
        make_deployment_mixture_profile(0, master_seed=4_481_100, spec=WIDE_SPEC),
    ),
    "mixed_churn": (
        make_deployment_mixture_profile(0, master_seed=4_481_200, spec=ULTRA_SPEC),
    ),
}

LEDGER_FACTORIES: dict[str, Callable[..., ChurnLedger]] = {
    "deployment_moderate": make_deployment_moderate_ledger,
    "deployment_wide": make_deployment_wide_ledger,
    "mixed_churn": make_deployment_ultra_ledger,
}
