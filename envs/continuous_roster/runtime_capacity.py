"""Capacity-independent continuous-service roster source for G32."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


ACTION_DIM = 2
OBSERVATION_DIM = 10
CRITIC_STATE_DIM = 6
HORIZON = 48
EVENT_TIMES = (12, 24, 36)
TRAIN_CAPACITY = 8
EVALUATION_CAPACITIES = (6, 8, 12)


@dataclass(frozen=True)
class RosterProfile:
    name: str
    member_capacity: int
    initial_count: int
    temporary_leave_count: int
    fresh_join_count: int
    terminal_leave_count: int

    def validate(self) -> None:
        counts = (
            self.member_capacity,
            self.initial_count,
            self.temporary_leave_count,
            self.fresh_join_count,
            self.terminal_leave_count,
        )
        if min(counts) <= 0:
            raise ValueError("G32 profile values must be positive")
        if self.temporary_leave_count >= self.initial_count:
            raise ValueError("G32 temporary leave would empty the roster")
        if self.initial_count + self.fresh_join_count > self.member_capacity:
            raise ValueError("G32 profile exceeds runtime member capacity")
        if self.terminal_leave_count >= self.initial_count + self.fresh_join_count:
            raise ValueError("G32 terminal leave would empty the roster")

    @property
    def segment_counts(self) -> tuple[int, int, int, int]:
        return (
            self.initial_count,
            self.initial_count - self.temporary_leave_count,
            self.initial_count + self.fresh_join_count,
            self.initial_count + self.fresh_join_count - self.terminal_leave_count,
        )


TRAIN_PROFILES = (
    RosterProfile("train_4_3_6_5", 8, 4, 1, 2, 1),
    RosterProfile("train_5_3_7_6", 8, 5, 2, 2, 1),
    RosterProfile("train_6_4_8_6", 8, 6, 2, 2, 2),
)
PADDING_CAPACITY_8 = RosterProfile("padding_4_3_6_5_cap8", 8, 4, 1, 2, 1)
PADDING_CAPACITY_12 = RosterProfile("padding_4_3_6_5_cap12", 12, 4, 1, 2, 1)
SMALL_CAPACITY_6 = RosterProfile("small_4_2_6_3", 6, 4, 2, 2, 3)
LARGE_CAPACITY_12 = RosterProfile("large_6_3_10_7", 12, 6, 3, 4, 3)


def _rng(master_seed: int, episode_id: int, stream: int) -> np.random.Generator:
    return np.random.default_rng(
        np.random.SeedSequence([int(master_seed), int(episode_id), int(stream)])
    )


@dataclass(frozen=True)
class CapacityRosterLedger:
    episode_id: int
    profile: RosterProfile
    initial_keys: tuple[int, ...]
    temporarily_absent: tuple[int, ...]
    fresh_join: tuple[int, ...]
    terminal_leave: tuple[int, ...]
    capabilities: np.ndarray
    load: np.ndarray
    target_mix: np.ndarray
    presentation_priority: np.ndarray
    expected_roster_sizes: tuple[int, ...]

    @property
    def member_capacity(self) -> int:
        return self.profile.member_capacity

    def validate(self) -> None:
        self.profile.validate()
        capacity = self.member_capacity
        if self.initial_keys != tuple(range(self.profile.initial_count)):
            raise ValueError("G32 initial lifecycle inventory mismatch")
        if self.fresh_join != tuple(
            range(
                self.profile.initial_count,
                self.profile.initial_count + self.profile.fresh_join_count,
            )
        ):
            raise ValueError("G32 fresh lifecycle inventory mismatch")
        if len(set(self.temporarily_absent)) != self.profile.temporary_leave_count:
            raise ValueError("G32 temporary lifecycle inventory mismatch")
        if not set(self.temporarily_absent).issubset(self.initial_keys):
            raise ValueError("G32 temporary leave references an unknown member")
        known = set(self.initial_keys) | set(self.fresh_join)
        if len(set(self.terminal_leave)) != self.profile.terminal_leave_count:
            raise ValueError("G32 terminal lifecycle inventory mismatch")
        if not set(self.terminal_leave).issubset(known):
            raise ValueError("G32 terminal leave references an unknown member")
        if self.capabilities.shape != (capacity, ACTION_DIM):
            raise ValueError("G32 capability shape mismatch")
        if self.load.shape != (HORIZON,) or self.target_mix.shape != (HORIZON,):
            raise ValueError("G32 demand shape mismatch")
        if self.presentation_priority.shape != (HORIZON, capacity):
            raise ValueError("G32 priority shape mismatch")
        arrays = (self.capabilities, self.load, self.target_mix, self.presentation_priority)
        if not all(np.isfinite(row).all() for row in arrays):
            raise ValueError("G32 source contains non-finite values")
        expected = tuple(
            count for count in self.profile.segment_counts for _ in range(HORIZON // 4)
        )
        if self.expected_roster_sizes != expected:
            raise ValueError("G32 roster schedule mismatch")


def make_ledger(
    episode_id: int, *, master_seed: int, profile: RosterProfile
) -> CapacityRosterLedger:
    profile.validate()
    initial = tuple(range(profile.initial_count))
    fresh = tuple(range(profile.initial_count, profile.initial_count + profile.fresh_join_count))
    temporary = tuple(sorted(int(value) for value in _rng(master_seed, episode_id, 0).choice(
        initial, size=profile.temporary_leave_count, replace=False
    )))
    terminal = tuple(sorted(int(value) for value in _rng(master_seed, episode_id, 1).choice(
        np.asarray(initial + fresh), size=profile.terminal_leave_count, replace=False
    )))
    # Every member owns its own streams. Extending runtime padding cannot shift
    # an active member's source values or any later stream.
    capabilities = np.stack([
        _rng(master_seed, episode_id, 100 + key).uniform(0.75, 1.25, ACTION_DIM)
        for key in range(profile.member_capacity)
    ]).astype(np.float32)
    priority = np.stack([
        _rng(master_seed, episode_id, 200 + key).random(HORIZON, dtype=np.float32)
        for key in range(profile.member_capacity)
    ], axis=1)
    blocks = HORIZON // 4
    load = np.repeat(_rng(master_seed, episode_id, 3).uniform(0.30, 0.70, blocks), 4).astype(np.float32)
    target_mix = np.repeat(_rng(master_seed, episode_id, 4).uniform(0.25, 0.75, blocks), 4).astype(np.float32)
    ledger = CapacityRosterLedger(
        episode_id=int(episode_id), profile=profile, initial_keys=initial,
        temporarily_absent=temporary, fresh_join=fresh, terminal_leave=terminal,
        capabilities=capabilities, load=load, target_mix=target_mix,
        presentation_priority=priority,
        expected_roster_sizes=tuple(
            count for count in profile.segment_counts for _ in range(HORIZON // 4)
        ),
    )
    ledger.validate()
    return ledger


@dataclass(frozen=True)
class MembershipChange:
    joined: tuple[int, ...] = ()
    temporarily_left: tuple[int, ...] = ()
    rejoined: tuple[int, ...] = ()
    terminally_left: tuple[int, ...] = ()


@dataclass(frozen=True)
class CapacityRosterView:
    time: int
    observations: np.ndarray
    active_mask: np.ndarray
    critic_state: np.ndarray
    membership_change: MembershipChange
    load: float
    target_mix: float


@dataclass(frozen=True)
class CapacityRosterOutcome:
    utility: float
    minimum_step_utility: float
    segment_utilities: tuple[float, ...]
    roster_sizes: tuple[int, ...]
    reward_trace: tuple[float, ...]


class RuntimeCapacityRosterEnv:
    def __init__(self, ledger: CapacityRosterLedger):
        ledger.validate()
        self.ledger = ledger
        capacity = ledger.member_capacity
        self.time = 0
        self.active = np.zeros(capacity, dtype=np.bool_)
        self.active[np.asarray(ledger.initial_keys)] = True
        self.age = np.zeros(capacity, dtype=np.int64)
        self.previous_actions = np.zeros((capacity, ACTION_DIM), dtype=np.float32)
        self.reward_trace: list[float] = []
        self.roster_sizes: list[int] = []
        self._prepared_time: int | None = None
        self._change = MembershipChange(joined=ledger.initial_keys)
        self._terminated = False

    def _prepare_membership(self) -> None:
        if self._prepared_time == self.time:
            return
        change = MembershipChange()
        if self.time == EVENT_TIMES[0]:
            keys = self.ledger.temporarily_absent
            self.active[np.asarray(keys)] = False
            change = MembershipChange(temporarily_left=keys)
        elif self.time == EVENT_TIMES[1]:
            rejoined, joined = self.ledger.temporarily_absent, self.ledger.fresh_join
            self.active[np.asarray(rejoined + joined)] = True
            self.previous_actions[np.asarray(joined)] = 0.0
            self.age[np.asarray(joined)] = 0
            change = MembershipChange(joined=joined, rejoined=rejoined)
        elif self.time == EVENT_TIMES[2]:
            keys = self.ledger.terminal_leave
            self.active[np.asarray(keys)] = False
            change = MembershipChange(terminally_left=keys)
        self._change = change
        self._prepared_time = self.time

    def observe(self) -> CapacityRosterView:
        if self._terminated:
            raise RuntimeError("G32 cannot observe a terminal environment")
        self._prepare_membership()
        count = int(self.active.sum())
        if count <= 0:
            raise RuntimeError("G32 source produced an empty roster")
        capacity = self.ledger.member_capacity
        observations = np.zeros((capacity, OBSERVATION_DIM), dtype=np.float32)
        keys = np.flatnonzero(self.active)
        load, mix = float(self.ledger.load[self.time]), float(self.ledger.target_mix[self.time])
        observations[keys, :2] = self.ledger.capabilities[keys]
        observations[keys, 2] = self.ledger.presentation_priority[self.time, keys]
        observations[keys, 3] = load
        observations[keys, 4] = mix
        observations[keys, 5] = np.float32(np.log1p(count))
        observations[keys, 6] = self.age[keys] / HORIZON
        observations[keys, 7:9] = (self.previous_actions[keys] + 1.0) / 2.0
        observations[keys, 9] = self.time / (HORIZON - 1)
        aggregate = self.ledger.capabilities[keys].sum(axis=0)
        critic_state = np.asarray((
            load, mix, aggregate[0], aggregate[1], np.log1p(count),
            self.time / (HORIZON - 1),
        ), dtype=np.float32)
        return CapacityRosterView(
            self.time, observations, self.active.copy(), critic_state,
            self._change, load, mix,
        )

    def step(self, actions: np.ndarray) -> tuple[float, bool, dict[str, float]]:
        view = self.observe()
        values = np.asarray(actions, dtype=np.float32)
        expected = (self.ledger.member_capacity, ACTION_DIM)
        if values.shape != expected or not np.isfinite(values).all():
            raise ValueError("G32 action shape/finite mismatch")
        if np.any(np.abs(values) > 1.0) or np.count_nonzero(values[~view.active_mask]):
            raise ValueError("G32 action support or inactive action mismatch")
        keys = np.flatnonzero(view.active_mask)
        effort = (values[keys, 0] + 1.0) / 2.0
        mix = (values[keys, 1] + 1.0) / 2.0
        capabilities = self.ledger.capabilities[keys]
        served = np.asarray((
            np.sum(effort * mix * capabilities[:, 0], dtype=np.float64),
            np.sum(effort * (1.0 - mix) * capabilities[:, 1], dtype=np.float64),
        ))
        aggregate = capabilities.sum(axis=0, dtype=np.float64)
        target = np.asarray((
            view.load * view.target_mix * aggregate[0],
            view.load * (1.0 - view.target_mix) * aggregate[1],
        ))
        relative_error = np.abs(served - target) / np.maximum(target, 1e-8)
        reward = float(np.clip(1.0 - relative_error.mean(), 0.0, 1.0))
        self.previous_actions[keys] = values[keys]
        self.age[keys] += 1
        self.reward_trace.append(reward)
        self.roster_sizes.append(len(keys))
        self.time += 1
        self._prepared_time = None
        self._change = MembershipChange()
        self._terminated = self.time == HORIZON
        return reward, self._terminated, {"service_utility": reward}

    def outcome(self) -> CapacityRosterOutcome:
        if not self._terminated or len(self.reward_trace) != HORIZON:
            raise RuntimeError("G32 outcome requires a complete episode")
        rewards = np.asarray(self.reward_trace, dtype=np.float64)
        return CapacityRosterOutcome(
            float(rewards.mean()), float(rewards.min()),
            tuple(float(rewards[start:start + HORIZON // 4].mean()) for start in range(0, HORIZON, HORIZON // 4)),
            tuple(self.roster_sizes), tuple(self.reward_trace),
        )


def constructive_actions(view: CapacityRosterView) -> np.ndarray:
    actions = np.zeros((len(view.active_mask), ACTION_DIM), dtype=np.float32)
    actions[view.active_mask, 0] = np.float32(2.0 * view.load - 1.0)
    actions[view.active_mask, 1] = np.float32(2.0 * view.target_mix - 1.0)
    return actions


def make_action_noise(
    episode_ids: Iterable[int], *, action_seed: int, member_capacity: int
) -> np.ndarray:
    ids = tuple(int(value) for value in episode_ids)
    if not ids:
        raise ValueError("G32 action noise requires an episode")
    # Member-owned action streams preserve CRN for common active identities.
    return np.stack([
        np.stack([
            _rng(action_seed, episode_id, 500 + key).standard_normal((HORIZON, ACTION_DIM)).astype(np.float32)
            for key in range(member_capacity)
        ], axis=1)
        for episode_id in ids
    ], axis=1)
