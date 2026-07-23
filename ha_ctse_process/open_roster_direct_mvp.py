"""Open-roster task family for the direct recurrent MVP.

The skill/event hierarchy is deliberately absent.  This module varies active
team membership within an episode while keeping the proven Generic-SHORT task
and direct primitive-action learner.  Operational padding capacity is metadata;
it is never an input or model parameter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from ha_ctse_process.dynamic_roster_direct import DirectTrajectory
from ha_ctse_process.dynamic_roster_testbed import (
    ACTIVE,
    HORIZON,
    IDLE,
    OBSERVATION_DIM,
    PERSISTENT_TARGET,
    TEMPORARILY_ABSENT,
    TERMINAL,
    WAVE_CANDIDATES,
    DynamicRosterView,
    EpisodeOutcome,
    GenericShortDynamicRosterEnv,
    LifecycleState,
    MembershipChange,
)


TRAIN_CAPACITY = 10
HELDOUT_CAPACITY = 12
OPEN_ROSTER_COUNT_LIMIT = 16
TRAIN_LEDGER_SEED = 675_501
EVAL_LEDGER_SEED = 975_501


@dataclass(frozen=True)
class RosterProfile:
    name: str
    phase_counts: tuple[int, int, int, int]

    def validate(self, *, capacity: int) -> None:
        if len(self.phase_counts) != 4:
            raise ValueError("open-roster profile requires four phase counts")
        initial, reduced, expanded, final = self.phase_counts
        if not (2 <= reduced < initial < expanded <= capacity):
            raise ValueError("open-roster profile must reduce then expand")
        if not (2 <= final < expanded):
            raise ValueError("open-roster final count must be a nonempty reduction")
        if expanded > OPEN_ROSTER_COUNT_LIMIT:
            raise ValueError("open-roster profile exceeds the declared count limit")


TRAIN_PROFILES = (
    RosterProfile("train_3_2_4_3", (3, 2, 4, 3)),
    RosterProfile("train_4_2_6_4", (4, 2, 6, 4)),
    RosterProfile("train_5_3_7_5", (5, 3, 7, 5)),
)
HELDOUT_PROFILES = (
    RosterProfile("heldout_6_2_8_4", (6, 2, 8, 4)),
    RosterProfile("heldout_7_4_9_6", (7, 4, 9, 6)),
)


def _rng(master_seed: int, episode_id: int, stream: int) -> np.random.Generator:
    return np.random.default_rng(
        np.random.SeedSequence([int(master_seed), int(episode_id), int(stream)])
    )


@dataclass(frozen=True)
class OpenRosterLedger:
    episode_id: int
    master_seed: int
    profile: RosterProfile
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
        return 2 * sum(count - 1 for count in self.profile.phase_counts)

    def validate(self) -> None:
        self.profile.validate(capacity=int(self.capacity))
        initial, reduced, expanded, final = self.profile.phase_counts
        if self.temporary_leave != tuple(range(reduced, initial)):
            raise ValueError("open-roster temporary-leave set mismatch")
        if self.genuine_join != tuple(range(initial, expanded)):
            raise ValueError("open-roster genuine-join set mismatch")
        if (
            len(self.terminal_leave) != expanded - final
            or len(set(self.terminal_leave)) != len(self.terminal_leave)
            or not set(self.terminal_leave).issubset(set(range(expanded)))
        ):
            raise ValueError("open-roster terminal-leave set mismatch")
        if len(self.wave_arrivals) != len(WAVE_CANDIDATES) or any(
            int(value) not in candidates
            for value, candidates in zip(self.wave_arrivals, WAVE_CANDIDATES)
        ):
            raise ValueError("open-roster wave arrival lies outside its window")
        shape = (HORIZON, int(self.capacity))
        for name in (
            "owner_priorities",
            "presentation_priorities",
            "direct_frontier_priorities",
        ):
            values = np.asarray(getattr(self, name))
            if values.shape != shape or not np.all(np.isfinite(values)):
                raise ValueError(f"open-roster {name} is invalid")


def make_open_roster_ledger(
    episode_id: int,
    *,
    master_seed: int,
    profiles: tuple[RosterProfile, ...],
    capacity: int,
) -> OpenRosterLedger:
    if not profiles:
        raise ValueError("open-roster ledger requires at least one profile")
    profile = profiles[int(episode_id) % len(profiles)]
    profile.validate(capacity=int(capacity))
    initial, reduced, expanded, final = profile.phase_counts
    terminal_rng = _rng(master_seed, episode_id, 0)
    wave_rng = _rng(master_seed, episode_id, 1)
    owner_rng = _rng(master_seed, episode_id, 2)
    presentation_rng = _rng(master_seed, episode_id, 3)
    frontier_rng = _rng(master_seed, episode_id, 4)
    ledger = OpenRosterLedger(
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
        presentation_priorities=presentation_rng.random(
            (HORIZON, int(capacity))
        ),
        direct_frontier_priorities=frontier_rng.random(
            (HORIZON, int(capacity))
        ),
    )
    ledger.validate()
    return ledger


def make_open_roster_training_ledger(
    episode_id: int, *, master_seed: int = TRAIN_LEDGER_SEED
) -> OpenRosterLedger:
    return make_open_roster_ledger(
        episode_id,
        master_seed=master_seed,
        profiles=TRAIN_PROFILES,
        capacity=TRAIN_CAPACITY,
    )


def make_open_roster_heldout_ledger(
    episode_id: int, *, master_seed: int = EVAL_LEDGER_SEED
) -> OpenRosterLedger:
    return make_open_roster_ledger(
        episode_id,
        master_seed=master_seed,
        profiles=HELDOUT_PROFILES,
        capacity=HELDOUT_CAPACITY,
    )


class OpenRosterDynamicEnv(GenericShortDynamicRosterEnv):
    """Generic-SHORT with a generated four-phase active-count profile."""

    ledger: OpenRosterLedger

    def __init__(self, ledger: OpenRosterLedger):
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
        joined: tuple[int, ...] = ()
        temporarily_left: tuple[int, ...] = ()
        rejoined: tuple[int, ...] = ()
        terminally_left: tuple[int, ...] = ()
        if self.time == 0:
            joined = self.ledger.initial_join
            for key in joined:
                state = self.lifecycles[key]
                state.status = ACTIVE
                state.previous_action = IDLE
                state.active_steps = 0
        elif self.time == 20:
            temporarily_left = self.ledger.temporary_leave
            for key in temporarily_left:
                state = self.lifecycles[key]
                if state.status != ACTIVE:
                    raise RuntimeError("open-roster temporary leave selected inactive key")
                state.status = TEMPORARILY_ABSENT
                state.short_streak = 0
                state.contributed_current_wave = False
                if self.persistent_owner == key:
                    self.persistent_owner = None
        elif self.time == 40:
            rejoined = self.ledger.temporary_leave
            joined = self.ledger.genuine_join
            for key in rejoined:
                state = self.lifecycles[key]
                if state.status != TEMPORARILY_ABSENT:
                    raise RuntimeError("open-roster rejoin selected non-absent key")
                state.status = ACTIVE
                state.membership_epoch += 1
            for key in joined:
                state = self.lifecycles[key]
                state.status = ACTIVE
                state.previous_action = IDLE
                state.active_steps = 0
        elif self.time == 60:
            terminally_left = self.ledger.terminal_leave
            for key in terminally_left:
                state = self.lifecycles[key]
                if state.status != ACTIVE:
                    raise RuntimeError("open-roster terminal leave selected inactive key")
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

    @staticmethod
    def _count_feature(active_count: int) -> float:
        return float(np.log1p(active_count) / np.log1p(OPEN_ROSTER_COUNT_LIMIT))

    def _critic_global_features(self) -> np.ndarray:
        values = super()._critic_global_features()
        values[1] = self._count_feature(len(self.active_keys))
        return values

    def _observation_for(self, key: int) -> np.ndarray:
        values = super()._observation_for(key)
        values[1] = self._count_feature(len(self.active_keys))
        if values.shape != (OBSERVATION_DIM,):
            raise RuntimeError("open-roster observation shape changed")
        return values

    def outcome(self) -> EpisodeOutcome:
        if not self._terminated or self.time != HORIZON:
            raise RuntimeError("open-roster outcome requires a terminal episode")
        if self.short_required_total != self.ledger.expected_short_requirement:
            raise RuntimeError("open-roster short requirement mismatch")
        persistent = min(
            float(self.persistent_units) / float(PERSISTENT_TARGET), 1.0
        )
        short = float(self.short_completed_total) / float(self.short_required_total)
        utility = 0.5 * (persistent + short)
        return EpisodeOutcome(
            persistent_score=persistent,
            short_score=short,
            utility=utility,
            terminal_reward=float(self.reward_trace[-1]),
            short_required_total=int(self.short_required_total),
            short_completed_total=int(self.short_completed_total),
            roster_sizes=tuple(self.roster_sizes),
            reward_trace=tuple(self.reward_trace),
            observation_shapes_valid=bool(self.observation_shapes_valid),
        )


def open_roster_lifecycle_contract_valid(
    trajectory: DirectTrajectory,
    *,
    ledger_seed: int,
) -> bool:
    for env_index, episode_id in enumerate(trajectory.ledger_ids):
        ledger = make_open_roster_training_ledger(
            episode_id, master_seed=ledger_seed
        )
        for key in ledger.temporary_leave:
            frozen = trajectory.hidden_after[19, env_index, key]
            if not (
                np.array_equal(
                    trajectory.hidden_before[20, env_index, key].numpy(),
                    frozen.numpy(),
                )
                and np.array_equal(
                    trajectory.hidden_after[39, env_index, key].numpy(),
                    frozen.numpy(),
                )
                and np.array_equal(
                    trajectory.hidden_before[40, env_index, key].numpy(),
                    frozen.numpy(),
                )
            ):
                return False
        for key in ledger.genuine_join:
            if not np.array_equal(
                trajectory.hidden_before[40, env_index, key].numpy(),
                np.zeros_like(trajectory.hidden_before[40, env_index, key].numpy()),
            ):
                return False
    return True


def profile_names(ledgers: Iterable[OpenRosterLedger]) -> tuple[str, ...]:
    return tuple(ledger.profile.name for ledger in ledgers)
