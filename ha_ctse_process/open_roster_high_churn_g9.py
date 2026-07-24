"""High-frequency membership-churn stress for frozen G8 policies."""

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
from ha_ctse_process.open_roster_direct_mvp import OpenRosterDynamicEnv


CHURN_CAPACITY = 20
MAXIMUM_ACTIVE_COUNT = 16


@dataclass(frozen=True)
class ChurnEvent:
    time: int
    temporarily_left: tuple[int, ...] = ()
    rejoined: tuple[int, ...] = ()
    joined: tuple[int, ...] = ()
    terminally_left: tuple[int, ...] = ()

    def validate(self, *, capacity: int) -> None:
        if not 0 < int(self.time) < HORIZON:
            raise ValueError("G9 churn-event time is invalid")
        groups = (
            self.temporarily_left,
            self.rejoined,
            self.joined,
            self.terminally_left,
        )
        flattened = [int(key) for group in groups for key in group]
        if len(flattened) != len(set(flattened)):
            raise ValueError("G9 churn-event operations collide")
        if any(key < 0 or key >= int(capacity) for key in flattened):
            raise ValueError("G9 churn-event key exceeds capacity")
        if not flattened:
            raise ValueError("G9 churn event must change membership")


@dataclass(frozen=True)
class ChurnProfile:
    name: str
    initial_join: tuple[int, ...]
    events: tuple[ChurnEvent, ...]
    capacity: int = CHURN_CAPACITY
    maximum_active_count: int = MAXIMUM_ACTIVE_COUNT
    required_event_count: int = 8

    def validate(self) -> None:
        if not 2 <= int(self.maximum_active_count) <= int(self.capacity):
            raise ValueError("churn capacity/count bound is invalid")
        if (
            len(self.initial_join) < 2
            or len(set(self.initial_join)) != len(self.initial_join)
            or any(key < 0 or key >= self.capacity for key in self.initial_join)
        ):
            raise ValueError("G9 initial roster is invalid")
        if self.required_event_count < 1 or len(self.events) != self.required_event_count:
            raise ValueError("churn profile event-count contract failed")
        if tuple(event.time for event in self.events) != tuple(
            sorted(event.time for event in self.events)
        ) or len({event.time for event in self.events}) != len(self.events):
            raise ValueError("G9 event times must be unique and ordered")
        status = [NOT_JOINED] * self.capacity
        for key in self.initial_join:
            status[key] = ACTIVE
        maximum = len(self.initial_join)
        for event in self.events:
            event.validate(capacity=self.capacity)
            for key in event.temporarily_left:
                if status[key] != ACTIVE:
                    raise ValueError("G9 temporary leave requires active lifecycle")
                status[key] = TEMPORARILY_ABSENT
            for key in event.rejoined:
                if status[key] != TEMPORARILY_ABSENT:
                    raise ValueError("G9 rejoin requires temporary absence")
                status[key] = ACTIVE
            for key in event.joined:
                if status[key] != NOT_JOINED:
                    raise ValueError("G9 genuine join attempted lifecycle reuse")
                status[key] = ACTIVE
            for key in event.terminally_left:
                if status[key] != ACTIVE:
                    raise ValueError("G9 terminal leave requires active lifecycle")
                status[key] = TERMINAL
            active_count = sum(value == ACTIVE for value in status)
            if active_count < 2:
                raise ValueError("G9 churn profile emptied the useful roster")
            maximum = max(maximum, active_count)
        if maximum > self.maximum_active_count:
            raise ValueError("churn profile exceeds its frozen count range")

    def active_count_at(self, time: int) -> int:
        status = [NOT_JOINED] * self.capacity
        for key in self.initial_join:
            status[key] = ACTIVE
        for event in self.events:
            if event.time > int(time):
                break
            for key in event.temporarily_left:
                status[key] = TEMPORARILY_ABSENT
            for key in event.rejoined:
                status[key] = ACTIVE
            for key in event.joined:
                status[key] = ACTIVE
            for key in event.terminally_left:
                status[key] = TERMINAL
        return sum(value == ACTIVE for value in status)


REPEATED_REJOIN_PROFILE = ChurnProfile(
    name="repeated_rejoin_8_edits",
    initial_join=tuple(range(8)),
    events=(
        ChurnEvent(9, temporarily_left=(6, 7)),
        ChurnEvent(13, rejoined=(6, 7)),
        ChurnEvent(24, temporarily_left=(6, 7)),
        ChurnEvent(28, rejoined=(6, 7)),
        ChurnEvent(40, temporarily_left=(6, 7)),
        ChurnEvent(44, rejoined=(6, 7), joined=(8, 9)),
        ChurnEvent(64, terminally_left=(0, 1)),
        ChurnEvent(68, joined=(10, 11)),
    ),
)

LOAD_PROXIMAL_PROFILE = ChurnProfile(
    name="load_proximal_8_edits",
    initial_join=tuple(range(12)),
    events=(
        ChurnEvent(9, temporarily_left=(8, 9, 10, 11)),
        ChurnEvent(13, rejoined=(8, 9, 10, 11)),
        ChurnEvent(24, terminally_left=(0, 1)),
        ChurnEvent(28, joined=(12, 13, 14, 15)),
        ChurnEvent(40, temporarily_left=(10, 11, 12, 13)),
        ChurnEvent(44, rejoined=(10, 11, 12, 13)),
        ChurnEvent(64, terminally_left=(2, 3, 4, 5)),
        ChurnEvent(68, joined=(16, 17)),
    ),
)

MIXED_CHURN_PROFILE = ChurnProfile(
    name="mixed_churn_8_edits",
    initial_join=tuple(range(10)),
    events=(
        ChurnEvent(6, temporarily_left=(8, 9)),
        ChurnEvent(10, rejoined=(8, 9)),
        ChurnEvent(24, terminally_left=(0, 1)),
        ChurnEvent(28, joined=(10, 11, 12, 13)),
        ChurnEvent(40, temporarily_left=(6, 7, 8, 9)),
        ChurnEvent(44, rejoined=(6, 7, 8, 9)),
        ChurnEvent(60, terminally_left=(2, 3, 4, 5)),
        ChurnEvent(64, joined=(14, 15, 16, 17)),
    ),
)

DOMAIN_PROFILES = {
    "repeated_rejoin": (REPEATED_REJOIN_PROFILE,),
    "load_proximal": (LOAD_PROXIMAL_PROFILE,),
    "mixed_churn": (MIXED_CHURN_PROFILE,),
}


def _rng(master_seed: int, episode_id: int, stream: int) -> np.random.Generator:
    return np.random.default_rng(
        np.random.SeedSequence([int(master_seed), int(episode_id), int(stream)])
    )


@dataclass(frozen=True)
class ChurnLedger:
    episode_id: int
    master_seed: int
    profile: ChurnProfile
    wave_arrivals: tuple[int, ...]
    owner_priorities: np.ndarray
    presentation_priorities: np.ndarray
    direct_frontier_priorities: np.ndarray

    @property
    def capacity(self) -> int:
        return self.profile.capacity

    @property
    def initial_join(self) -> tuple[int, ...]:
        return self.profile.initial_join

    @property
    def expected_short_requirement(self) -> int:
        return sum(
            self.profile.active_count_at(arrival) - 1
            for arrival in self.wave_arrivals
        )

    def validate(self) -> None:
        self.profile.validate()
        if len(self.wave_arrivals) != len(WAVE_CANDIDATES) or any(
            int(value) not in candidates
            for value, candidates in zip(self.wave_arrivals, WAVE_CANDIDATES)
        ):
            raise ValueError("G9 wave arrival lies outside its frozen window")
        shape = (HORIZON, self.capacity)
        for name in (
            "owner_priorities",
            "presentation_priorities",
            "direct_frontier_priorities",
        ):
            values = np.asarray(getattr(self, name))
            if values.shape != shape or not np.all(np.isfinite(values)):
                raise ValueError(f"G9 {name} is invalid")
        if self.expected_short_requirement <= 0:
            raise ValueError("G9 short requirement is invalid")


def make_churn_ledger(
    episode_id: int,
    *,
    master_seed: int,
    profiles: tuple[ChurnProfile, ...],
) -> ChurnLedger:
    if not profiles:
        raise ValueError("G9 ledger requires at least one profile")
    profile = profiles[int(episode_id) % len(profiles)]
    profile.validate()
    wave_rng = _rng(master_seed, episode_id, 1)
    ledger = ChurnLedger(
        episode_id=int(episode_id),
        master_seed=int(master_seed),
        profile=profile,
        wave_arrivals=tuple(
            int(wave_rng.choice(np.asarray(candidates, dtype=np.int64)))
            for candidates in WAVE_CANDIDATES
        ),
        owner_priorities=_rng(master_seed, episode_id, 2).random(
            (HORIZON, profile.capacity)
        ),
        presentation_priorities=_rng(master_seed, episode_id, 3).random(
            (HORIZON, profile.capacity)
        ),
        direct_frontier_priorities=_rng(master_seed, episode_id, 4).random(
            (HORIZON, profile.capacity)
        ),
    )
    ledger.validate()
    return ledger


def make_repeated_rejoin_ledger(
    episode_id: int, *, master_seed: int = 1_981_000
) -> ChurnLedger:
    return make_churn_ledger(
        episode_id,
        master_seed=master_seed,
        profiles=DOMAIN_PROFILES["repeated_rejoin"],
    )


def make_load_proximal_ledger(
    episode_id: int, *, master_seed: int = 1_981_100
) -> ChurnLedger:
    return make_churn_ledger(
        episode_id,
        master_seed=master_seed,
        profiles=DOMAIN_PROFILES["load_proximal"],
    )


def make_mixed_churn_ledger(
    episode_id: int, *, master_seed: int = 1_981_200
) -> ChurnLedger:
    return make_churn_ledger(
        episode_id,
        master_seed=master_seed,
        profiles=DOMAIN_PROFILES["mixed_churn"],
    )


LEDGER_FACTORIES: dict[str, Callable[..., ChurnLedger]] = {
    "repeated_rejoin": make_repeated_rejoin_ledger,
    "load_proximal": make_load_proximal_ledger,
    "mixed_churn": make_mixed_churn_ledger,
}


class HighChurnEnv(OpenRosterDynamicEnv):
    ledger: ChurnLedger

    def __init__(self, ledger: ChurnLedger):
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
        if self.time == 0:
            for key in self.ledger.initial_join:
                state = self.lifecycles[key]
                state.status = ACTIVE
                state.previous_action = IDLE
                state.active_steps = 0
            return MembershipChange(joined=self.ledger.initial_join)
        matches = [event for event in self.ledger.profile.events if event.time == self.time]
        if not matches:
            return MembershipChange()
        if len(matches) != 1:
            raise RuntimeError("G9 event schedule is not unique")
        event = matches[0]
        for key in event.temporarily_left:
            state = self.lifecycles[key]
            if state.status != ACTIVE:
                raise RuntimeError("G9 temporary leave selected inactive lifecycle")
            state.status = TEMPORARILY_ABSENT
            state.short_streak = 0
            state.contributed_current_wave = False
            if self.persistent_owner == key:
                self.persistent_owner = None
        for key in event.rejoined:
            state = self.lifecycles[key]
            if state.status != TEMPORARILY_ABSENT:
                raise RuntimeError("G9 rejoin selected non-absent lifecycle")
            state.status = ACTIVE
            state.membership_epoch += 1
        for key in event.joined:
            state = self.lifecycles[key]
            if state.status != NOT_JOINED:
                raise RuntimeError("G9 genuine join attempted lifecycle reuse")
            state.status = ACTIVE
            state.previous_action = IDLE
            state.active_steps = 0
        for key in event.terminally_left:
            state = self.lifecycles[key]
            if state.status != ACTIVE:
                raise RuntimeError("G9 terminal leave selected inactive lifecycle")
            state.status = TERMINAL
            state.short_streak = 0
            state.contributed_current_wave = False
            if self.persistent_owner == key:
                self.persistent_owner = None
        return MembershipChange(
            joined=event.joined,
            temporarily_left=event.temporarily_left,
            rejoined=event.rejoined,
            terminally_left=event.terminally_left,
        )


def expected_roster_schedule(profile: ChurnProfile) -> tuple[int, ...]:
    return tuple(profile.active_count_at(time) for time in range(HORIZON))


def high_churn_lifecycle_contract_valid(
    trajectory: DirectTrajectory,
    *,
    ledger_seed: int,
    ledger_factory: Callable[..., ChurnLedger],
) -> bool:
    for env_index, episode_id in enumerate(trajectory.ledger_ids):
        ledger = ledger_factory(episode_id, master_seed=ledger_seed)
        frozen: dict[int, tuple[np.ndarray, int]] = {}
        for event in ledger.profile.events:
            for key in event.temporarily_left:
                frozen[key] = (
                    trajectory.hidden_after[
                        event.time - 1, env_index, key
                    ].numpy(),
                    event.time,
                )
                if not np.array_equal(
                    trajectory.hidden_before[event.time, env_index, key].numpy(),
                    frozen[key][0],
                ):
                    return False
            for key in event.rejoined:
                if key not in frozen:
                    return False
                frozen_value, leave_time = frozen.pop(key)
                for time in range(leave_time, event.time):
                    if not (
                        np.array_equal(
                            trajectory.hidden_before[time, env_index, key].numpy(),
                            frozen_value,
                        )
                        and np.array_equal(
                            trajectory.hidden_after[time, env_index, key].numpy(),
                            frozen_value,
                        )
                        and not bool(trajectory.active_mask[time, env_index, key])
                    ):
                        return False
                if not np.array_equal(
                    trajectory.hidden_before[event.time, env_index, key].numpy(),
                    frozen_value,
                ):
                    return False
            for key in event.joined:
                if not np.array_equal(
                    trajectory.hidden_before[event.time, env_index, key].numpy(),
                    np.zeros_like(
                        trajectory.hidden_before[event.time, env_index, key].numpy()
                    ),
                ):
                    return False
            for key in event.terminally_left:
                if bool(trajectory.active_mask[event.time:, env_index, key].any()):
                    return False
                terminal_value = trajectory.hidden_before[
                    event.time, env_index, key
                ].numpy()
                for time in range(event.time, HORIZON):
                    if not (
                        np.array_equal(
                            trajectory.hidden_before[time, env_index, key].numpy(),
                            terminal_value,
                        )
                        and np.array_equal(
                            trajectory.hidden_after[time, env_index, key].numpy(),
                            terminal_value,
                        )
                    ):
                        return False
        if frozen:
            return False
    return True


def profile_names(ledgers: Iterable[ChurnLedger]) -> tuple[str, ...]:
    return tuple(ledger.profile.name for ledger in ledgers)
