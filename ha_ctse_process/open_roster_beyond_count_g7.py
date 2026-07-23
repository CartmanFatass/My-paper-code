"""Beyond-declared-count stress adapter for frozen G5 checkpoints.

This module changes only the open-roster membership profile.  Generic-SHORT
waves, reward, observations, primitive actions and the G5 count feature remain
unchanged.  Padding capacity is operational storage, never model input.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

import numpy as np

from ha_ctse_process.dynamic_roster_direct import DirectTrajectory
from ha_ctse_process.dynamic_roster_testbed import (
    ACTIVE,
    HORIZON,
    IDLE,
    NOT_JOINED,
    TEMPORARILY_ABSENT,
    TERMINAL,
    WAVE_CANDIDATES,
    LifecycleState,
    MembershipChange,
)
from ha_ctse_process.open_roster_direct_mvp import (
    OPEN_ROSTER_COUNT_LIMIT,
    OpenRosterDynamicEnv,
)


MODERATE_BEYOND_CAPACITY = 32
FAR_BEYOND_CAPACITY = 48
JOINT_CAPACITY = 48
MAXIMUM_ACTIVE_COUNT = 40


@dataclass(frozen=True)
class BeyondCountProfile:
    name: str
    phase_counts: tuple[int, int, int, int]
    membership_event_times: tuple[int, int, int]

    def validate(self, *, capacity: int) -> None:
        if len(self.phase_counts) != 4:
            raise ValueError("G7 stress profile requires four phase counts")
        initial, reduced, expanded, final = self.phase_counts
        if not (2 <= reduced < initial < expanded <= int(capacity)):
            raise ValueError("G7 stress profile must reduce then expand")
        if not (2 <= final < expanded):
            raise ValueError("G7 final phase must be a nonempty reduction")
        if expanded > MAXIMUM_ACTIVE_COUNT:
            raise ValueError("G7 profile exceeds the registered active-count range")
        count_features = np.log1p(np.asarray(self.phase_counts, dtype=np.float64)) / np.log1p(
            OPEN_ROSTER_COUNT_LIMIT
        )
        if not np.all(np.isfinite(count_features)):
            raise ValueError("G7 profile count feature is non-finite")
        if len(self.membership_event_times) != 3:
            raise ValueError("G7 stress profile requires three membership events")
        temporary, expansion, terminal = self.membership_event_times
        if not (0 < temporary < expansion < terminal < HORIZON):
            raise ValueError("G7 membership event times are invalid")

    def active_count_at(self, time: int) -> int:
        temporary, expansion, terminal = self.membership_event_times
        if int(time) < temporary:
            return self.phase_counts[0]
        if int(time) < expansion:
            return self.phase_counts[1]
        if int(time) < terminal:
            return self.phase_counts[2]
        return self.phase_counts[3]


MODERATE_BEYOND_PROFILES = (
    BeyondCountProfile("moderate_beyond_14_8_20_12", (14, 8, 20, 12), (20, 40, 60)),
    BeyondCountProfile("moderate_beyond_16_10_24_14", (16, 10, 24, 14), (20, 40, 60)),
)
FAR_BEYOND_PROFILES = (
    BeyondCountProfile("far_beyond_18_10_28_16", (18, 10, 28, 16), (20, 40, 60)),
    BeyondCountProfile("far_beyond_24_12_40_20", (24, 12, 40, 20), (20, 40, 60)),
)
JOINT_PROFILES = (
    BeyondCountProfile("joint_14_8_20_12_t15_38_58", (14, 8, 20, 12), (15, 38, 58)),
    BeyondCountProfile("joint_18_10_28_16_t18_46_62", (18, 10, 28, 16), (18, 46, 62)),
    BeyondCountProfile("joint_24_12_40_20_t21_45_70", (24, 12, 40, 20), (21, 45, 70)),
)
DOMAIN_PROFILES = {
    "moderate_beyond": MODERATE_BEYOND_PROFILES,
    "far_beyond": FAR_BEYOND_PROFILES,
    "joint": JOINT_PROFILES,
}


def _rng(master_seed: int, episode_id: int, stream: int) -> np.random.Generator:
    return np.random.default_rng(
        np.random.SeedSequence([int(master_seed), int(episode_id), int(stream)])
    )


@dataclass(frozen=True)
class BeyondCountLedger:
    """Duck-compatible direct-policy ledger with profile-owned event times."""

    episode_id: int
    master_seed: int
    profile: BeyondCountProfile
    capacity: int
    temporary_leave: tuple[int, ...]
    genuine_join: tuple[int, ...]
    terminal_leave: tuple[int, ...]
    wave_arrivals: tuple[int, ...]
    owner_priorities: np.ndarray
    presentation_priorities: np.ndarray
    direct_frontier_priorities: np.ndarray

    @property
    def initial_join(self) -> tuple[int, ...]:
        return tuple(range(self.profile.phase_counts[0]))

    @property
    def expected_short_requirement(self) -> int:
        return sum(
            self.profile.active_count_at(arrival) - 1
            for arrival in self.wave_arrivals
        )

    def validate(self) -> None:
        self.profile.validate(capacity=int(self.capacity))
        initial, reduced, expanded, final = self.profile.phase_counts
        if self.temporary_leave != tuple(range(reduced, initial)):
            raise ValueError("G7 temporary-leave set mismatch")
        if self.genuine_join != tuple(range(initial, expanded)):
            raise ValueError("G7 genuine-join set mismatch")
        if (
            len(self.terminal_leave) != expanded - final
            or len(set(self.terminal_leave)) != len(self.terminal_leave)
            or not set(self.terminal_leave).issubset(set(range(expanded)))
        ):
            raise ValueError("G7 terminal-leave set mismatch")
        if len(self.wave_arrivals) != len(WAVE_CANDIDATES) or any(
            int(value) not in candidates
            for value, candidates in zip(self.wave_arrivals, WAVE_CANDIDATES)
        ):
            raise ValueError("G7 wave arrival lies outside its frozen window")
        shape = (HORIZON, int(self.capacity))
        for name in (
            "owner_priorities",
            "presentation_priorities",
            "direct_frontier_priorities",
        ):
            values = np.asarray(getattr(self, name))
            if values.shape != shape or not np.all(np.isfinite(values)):
                raise ValueError(f"G7 {name} is invalid")
        expected = sum(
            self.profile.active_count_at(arrival) - 1
            for arrival in self.wave_arrivals
        )
        if self.expected_short_requirement != expected or expected <= 0:
            raise ValueError("G7 actual-wave short requirement is invalid")


def make_beyond_count_ledger(
    episode_id: int,
    *,
    master_seed: int,
    profiles: tuple[BeyondCountProfile, ...],
    capacity: int,
) -> BeyondCountLedger:
    if not profiles:
        raise ValueError("G7 ledger requires at least one profile")
    profile = profiles[int(episode_id) % len(profiles)]
    profile.validate(capacity=int(capacity))
    initial, reduced, expanded, final = profile.phase_counts
    terminal_rng = _rng(master_seed, episode_id, 0)
    wave_rng = _rng(master_seed, episode_id, 1)
    owner_rng = _rng(master_seed, episode_id, 2)
    presentation_rng = _rng(master_seed, episode_id, 3)
    frontier_rng = _rng(master_seed, episode_id, 4)
    ledger = BeyondCountLedger(
        episode_id=int(episode_id),
        master_seed=int(master_seed),
        profile=profile,
        capacity=int(capacity),
        temporary_leave=tuple(range(reduced, initial)),
        genuine_join=tuple(range(initial, expanded)),
        terminal_leave=tuple(
            sorted(
                int(value)
                for value in terminal_rng.choice(
                    expanded, size=expanded - final, replace=False
                )
            )
        ),
        wave_arrivals=tuple(
            int(wave_rng.choice(np.asarray(candidates, dtype=np.int64)))
            for candidates in WAVE_CANDIDATES
        ),
        owner_priorities=owner_rng.random((HORIZON, int(capacity))),
        presentation_priorities=presentation_rng.random((HORIZON, int(capacity))),
        direct_frontier_priorities=frontier_rng.random((HORIZON, int(capacity))),
    )
    ledger.validate()
    return ledger


def make_moderate_beyond_ledger(
    episode_id: int, *, master_seed: int = 1_071_000
) -> BeyondCountLedger:
    return make_beyond_count_ledger(
        episode_id,
        master_seed=master_seed,
        profiles=MODERATE_BEYOND_PROFILES,
        capacity=MODERATE_BEYOND_CAPACITY,
    )


def make_far_beyond_ledger(
    episode_id: int, *, master_seed: int = 1_071_100
) -> BeyondCountLedger:
    return make_beyond_count_ledger(
        episode_id,
        master_seed=master_seed,
        profiles=FAR_BEYOND_PROFILES,
        capacity=FAR_BEYOND_CAPACITY,
    )


def make_joint_ledger(
    episode_id: int, *, master_seed: int = 1_071_200
) -> BeyondCountLedger:
    return make_beyond_count_ledger(
        episode_id,
        master_seed=master_seed,
        profiles=JOINT_PROFILES,
        capacity=JOINT_CAPACITY,
    )


LEDGER_FACTORIES: dict[str, Callable[..., BeyondCountLedger]] = {
    "moderate_beyond": make_moderate_beyond_ledger,
    "far_beyond": make_far_beyond_ledger,
    "joint": make_joint_ledger,
}


class BeyondCountEnv(OpenRosterDynamicEnv):
    """G5 Generic-SHORT environment with profile-owned membership times."""

    ledger: BeyondCountLedger

    def __init__(self, ledger: BeyondCountLedger):
        ledger.validate()
        self.ledger = ledger
        self.lifecycles = {
            key: LifecycleState(key=key) for key in range(ledger.capacity)
        }
        self.time = 0
        self.persistent_owner: int | None = None
        self.persistent_units = 0
        self.current_wave = None
        self.wave_records = []
        self.short_required_total = 0
        self.short_completed_total = 0
        self.roster_sizes: list[int] = []
        self.reward_trace: list[float] = []
        self.observation_shapes_valid = True
        self._prepared_time: int | None = None
        self._current_membership_change = MembershipChange()
        self._pending_event_transaction = None
        self._terminated = False

    def _apply_membership(self) -> MembershipChange:
        temporary_time, expansion_time, terminal_time = (
            self.ledger.profile.membership_event_times
        )
        joined: tuple[int, ...] = ()
        temporarily_left: tuple[int, ...] = ()
        rejoined: tuple[int, ...] = ()
        terminally_left: tuple[int, ...] = ()
        if self.time == 0:
            joined = self.ledger.initial_join
            for key in joined:
                state = self.lifecycles[key]
                if state.status != NOT_JOINED:
                    raise RuntimeError("G7 initial join attempted lifecycle reuse")
                state.status = ACTIVE
                state.previous_action = IDLE
                state.active_steps = 0
        elif self.time == temporary_time:
            temporarily_left = self.ledger.temporary_leave
            for key in temporarily_left:
                state = self.lifecycles[key]
                if state.status != ACTIVE:
                    raise RuntimeError("G7 temporary leave selected inactive lifecycle")
                state.status = TEMPORARILY_ABSENT
                state.short_streak = 0
                state.contributed_current_wave = False
                if self.persistent_owner == key:
                    self.persistent_owner = None
        elif self.time == expansion_time:
            rejoined = self.ledger.temporary_leave
            joined = self.ledger.genuine_join
            for key in rejoined:
                state = self.lifecycles[key]
                if state.status != TEMPORARILY_ABSENT:
                    raise RuntimeError("G7 rejoin selected non-absent lifecycle")
                state.status = ACTIVE
                state.membership_epoch += 1
            for key in joined:
                state = self.lifecycles[key]
                if state.status != NOT_JOINED:
                    raise RuntimeError("G7 genuine join attempted lifecycle reuse")
                state.status = ACTIVE
                state.previous_action = IDLE
                state.active_steps = 0
        elif self.time == terminal_time:
            terminally_left = self.ledger.terminal_leave
            for key in terminally_left:
                state = self.lifecycles[key]
                if state.status != ACTIVE:
                    raise RuntimeError("G7 terminal leave selected inactive lifecycle")
                state.status = TERMINAL
                state.short_streak = 0
                state.contributed_current_wave = False
                if self.persistent_owner == key:
                    self.persistent_owner = None
        return MembershipChange(
            joined=joined,
            temporarily_left=temporarily_left,
            rejoined=rejoined,
            terminally_left=terminally_left,
        )


def beyond_count_lifecycle_contract_valid(
    trajectory: DirectTrajectory,
    *,
    ledger_seed: int,
    ledger_factory: Callable[..., BeyondCountLedger],
) -> bool:
    """Check freeze/restore, zero-join and permanent terminal removal."""

    for env_index, episode_id in enumerate(trajectory.ledger_ids):
        ledger = ledger_factory(episode_id, master_seed=ledger_seed)
        temporary_time, expansion_time, terminal_time = (
            ledger.profile.membership_event_times
        )
        for key in ledger.temporary_leave:
            frozen = trajectory.hidden_after[temporary_time - 1, env_index, key]
            if not (
                np.array_equal(
                    trajectory.hidden_before[temporary_time, env_index, key].numpy(),
                    frozen.numpy(),
                )
                and np.array_equal(
                    trajectory.hidden_after[expansion_time - 1, env_index, key].numpy(),
                    frozen.numpy(),
                )
                and np.array_equal(
                    trajectory.hidden_before[expansion_time, env_index, key].numpy(),
                    frozen.numpy(),
                )
            ):
                return False
        for key in ledger.genuine_join:
            if not np.array_equal(
                trajectory.hidden_before[expansion_time, env_index, key].numpy(),
                np.zeros_like(
                    trajectory.hidden_before[expansion_time, env_index, key].numpy()
                ),
            ):
                return False
        for key in ledger.terminal_leave:
            if bool(trajectory.active_mask[terminal_time:, env_index, key].any()):
                return False
    return True


def profile_names(ledgers: Iterable[BeyondCountLedger]) -> tuple[str, ...]:
    return tuple(ledger.profile.name for ledger in ledgers)
