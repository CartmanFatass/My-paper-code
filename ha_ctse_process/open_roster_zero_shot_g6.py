"""Zero-shot count/event-time stress adapter for frozen G5 checkpoints.

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


COUNT_SCALE_CAPACITY = 20
EVENT_TIME_CAPACITY = 12
JOINT_CAPACITY = 20


@dataclass(frozen=True)
class ZeroShotStressProfile:
    name: str
    phase_counts: tuple[int, int, int, int]
    membership_event_times: tuple[int, int, int]

    def validate(self, *, capacity: int) -> None:
        if len(self.phase_counts) != 4:
            raise ValueError("G6 stress profile requires four phase counts")
        initial, reduced, expanded, final = self.phase_counts
        if not (2 <= reduced < initial < expanded <= int(capacity)):
            raise ValueError("G6 stress profile must reduce then expand")
        if not (2 <= final < expanded):
            raise ValueError("G6 final phase must be a nonempty reduction")
        if expanded > OPEN_ROSTER_COUNT_LIMIT:
            raise ValueError("G6 profile exceeds the frozen count-feature limit")
        if len(self.membership_event_times) != 3:
            raise ValueError("G6 stress profile requires three membership events")
        temporary, expansion, terminal = self.membership_event_times
        if not (0 < temporary < expansion < terminal < HORIZON):
            raise ValueError("G6 membership event times are invalid")

    def active_count_at(self, time: int) -> int:
        temporary, expansion, terminal = self.membership_event_times
        if int(time) < temporary:
            return self.phase_counts[0]
        if int(time) < expansion:
            return self.phase_counts[1]
        if int(time) < terminal:
            return self.phase_counts[2]
        return self.phase_counts[3]


COUNT_SCALE_PROFILES = (
    ZeroShotStressProfile("count_scale_8_4_12_6", (8, 4, 12, 6), (20, 40, 60)),
    ZeroShotStressProfile("count_scale_10_6_14_8", (10, 6, 14, 8), (20, 40, 60)),
    ZeroShotStressProfile("count_scale_12_8_16_10", (12, 8, 16, 10), (20, 40, 60)),
)
EVENT_TIME_PROFILES = (
    ZeroShotStressProfile("event_time_6_2_8_4_t15_38_58", (6, 2, 8, 4), (15, 38, 58)),
    ZeroShotStressProfile("event_time_7_4_9_6_t18_46_62", (7, 4, 9, 6), (18, 46, 62)),
)
JOINT_PROFILES = (
    ZeroShotStressProfile("joint_8_4_12_6_t15_38_58", (8, 4, 12, 6), (15, 38, 58)),
    ZeroShotStressProfile("joint_10_6_14_8_t18_46_62", (10, 6, 14, 8), (18, 46, 62)),
    ZeroShotStressProfile("joint_12_8_16_10_t21_45_70", (12, 8, 16, 10), (21, 45, 70)),
)
DOMAIN_PROFILES = {
    "count_scale": COUNT_SCALE_PROFILES,
    "event_time": EVENT_TIME_PROFILES,
    "joint": JOINT_PROFILES,
}


def _rng(master_seed: int, episode_id: int, stream: int) -> np.random.Generator:
    return np.random.default_rng(
        np.random.SeedSequence([int(master_seed), int(episode_id), int(stream)])
    )


@dataclass(frozen=True)
class ZeroShotStressLedger:
    """Duck-compatible direct-policy ledger with profile-owned event times."""

    episode_id: int
    master_seed: int
    profile: ZeroShotStressProfile
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
            raise ValueError("G6 temporary-leave set mismatch")
        if self.genuine_join != tuple(range(initial, expanded)):
            raise ValueError("G6 genuine-join set mismatch")
        if (
            len(self.terminal_leave) != expanded - final
            or len(set(self.terminal_leave)) != len(self.terminal_leave)
            or not set(self.terminal_leave).issubset(set(range(expanded)))
        ):
            raise ValueError("G6 terminal-leave set mismatch")
        if len(self.wave_arrivals) != len(WAVE_CANDIDATES) or any(
            int(value) not in candidates
            for value, candidates in zip(self.wave_arrivals, WAVE_CANDIDATES)
        ):
            raise ValueError("G6 wave arrival lies outside its frozen window")
        shape = (HORIZON, int(self.capacity))
        for name in (
            "owner_priorities",
            "presentation_priorities",
            "direct_frontier_priorities",
        ):
            values = np.asarray(getattr(self, name))
            if values.shape != shape or not np.all(np.isfinite(values)):
                raise ValueError(f"G6 {name} is invalid")
        expected = sum(
            self.profile.active_count_at(arrival) - 1
            for arrival in self.wave_arrivals
        )
        if self.expected_short_requirement != expected or expected <= 0:
            raise ValueError("G6 actual-wave short requirement is invalid")


def make_stress_ledger(
    episode_id: int,
    *,
    master_seed: int,
    profiles: tuple[ZeroShotStressProfile, ...],
    capacity: int,
) -> ZeroShotStressLedger:
    if not profiles:
        raise ValueError("G6 ledger requires at least one profile")
    profile = profiles[int(episode_id) % len(profiles)]
    profile.validate(capacity=int(capacity))
    initial, reduced, expanded, final = profile.phase_counts
    terminal_rng = _rng(master_seed, episode_id, 0)
    wave_rng = _rng(master_seed, episode_id, 1)
    owner_rng = _rng(master_seed, episode_id, 2)
    presentation_rng = _rng(master_seed, episode_id, 3)
    frontier_rng = _rng(master_seed, episode_id, 4)
    ledger = ZeroShotStressLedger(
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


def make_count_scale_ledger(
    episode_id: int, *, master_seed: int = 1_061_000
) -> ZeroShotStressLedger:
    return make_stress_ledger(
        episode_id,
        master_seed=master_seed,
        profiles=COUNT_SCALE_PROFILES,
        capacity=COUNT_SCALE_CAPACITY,
    )


def make_event_time_ledger(
    episode_id: int, *, master_seed: int = 1_061_100
) -> ZeroShotStressLedger:
    return make_stress_ledger(
        episode_id,
        master_seed=master_seed,
        profiles=EVENT_TIME_PROFILES,
        capacity=EVENT_TIME_CAPACITY,
    )


def make_joint_ledger(
    episode_id: int, *, master_seed: int = 1_061_200
) -> ZeroShotStressLedger:
    return make_stress_ledger(
        episode_id,
        master_seed=master_seed,
        profiles=JOINT_PROFILES,
        capacity=JOINT_CAPACITY,
    )


LEDGER_FACTORIES: dict[str, Callable[..., ZeroShotStressLedger]] = {
    "count_scale": make_count_scale_ledger,
    "event_time": make_event_time_ledger,
    "joint": make_joint_ledger,
}


class ZeroShotStressEnv(OpenRosterDynamicEnv):
    """G5 Generic-SHORT environment with profile-owned membership times."""

    ledger: ZeroShotStressLedger

    def __init__(self, ledger: ZeroShotStressLedger):
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
                    raise RuntimeError("G6 initial join attempted lifecycle reuse")
                state.status = ACTIVE
                state.previous_action = IDLE
                state.active_steps = 0
        elif self.time == temporary_time:
            temporarily_left = self.ledger.temporary_leave
            for key in temporarily_left:
                state = self.lifecycles[key]
                if state.status != ACTIVE:
                    raise RuntimeError("G6 temporary leave selected inactive lifecycle")
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
                    raise RuntimeError("G6 rejoin selected non-absent lifecycle")
                state.status = ACTIVE
                state.membership_epoch += 1
            for key in joined:
                state = self.lifecycles[key]
                if state.status != NOT_JOINED:
                    raise RuntimeError("G6 genuine join attempted lifecycle reuse")
                state.status = ACTIVE
                state.previous_action = IDLE
                state.active_steps = 0
        elif self.time == terminal_time:
            terminally_left = self.ledger.terminal_leave
            for key in terminally_left:
                state = self.lifecycles[key]
                if state.status != ACTIVE:
                    raise RuntimeError("G6 terminal leave selected inactive lifecycle")
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


def stress_lifecycle_contract_valid(
    trajectory: DirectTrajectory,
    *,
    ledger_seed: int,
    ledger_factory: Callable[..., ZeroShotStressLedger],
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


def profile_names(ledgers: Iterable[ZeroShotStressLedger]) -> tuple[str, ...]:
    return tuple(ledger.profile.name for ledger in ledgers)
