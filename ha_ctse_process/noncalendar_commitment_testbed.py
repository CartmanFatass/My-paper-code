"""Noncalendar heterogeneous-tracking G0 benchmark.

This module is the complete task-side boundary for the registered H/C/S/D
benchmark.  It owns deterministic paired ledgers, the primitive tracking
environment, the calendar-null mask, exact hindsight solvers, causal direct
rollouts, strict checkpoints, bootstrap helpers, and terminal branch logic.
It deliberately imports the existing direct recurrent policy and PPO algebra;
there is no skill, high-level action, intrinsic reward, or extra critic here.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping, Sequence

import numpy as np
import torch

from ha_ctse_process.dynamic_roster_direct import (
    DirectPrimitiveARPolicy,
    DirectTrajectory,
    HIDDEN_DIM,
    LEARNING_RATE,
    MAX_RECURRENT_CHUNK,
    PPO_PASSES,
    model_state_copy,
    nested_state_maximum_difference,
)
from ha_ctse_process.dynamic_roster_testbed import (
    ACTION_COUNT,
    HORIZON,
    MAX_LIFECYCLES,
    OBSERVATION_DIM,
)
from ha_ctse_process.variable_roster_event import (
    JOIN,
    MembershipDelta,
    REJOIN,
    TEMPORARY_LEAVE,
    TERMINAL_LEAVE,
)


ArmMode = Literal["calendar_masked", "demand_visible"]
Profile = Literal["train", "iid", "held_out"]
SolverArm = Literal["H", "S"]

THRUST_BY_ACTION = np.asarray((-1, 0, 1), dtype=np.int64)
STATE_MIN = -2
STATE_MAX = 2
TARGET_STREAK = 2
SHARED_RENEWAL_PERIOD = 4

CALENDAR_MASK_INDICES = (3, 4, 5, 6, 9, 10, 11)
COMMON_FIELD_COUNT = 8
PARAMETER_COUNT = 14_980

MODEL_INITIALIZATION_SEED = 58_058
TRAIN_TASK_SEED = 68_058
TRAIN_ORDER_SEED = 78_058
TRAIN_ACTION_SEED = 88_058
IID_EVAL_TASK_SEED = 98_058
HELD_OUT_EVAL_TASK_SEED = 99_058
EVAL_ORDER_SEED = 79_058
EVAL_ACTION_SEED = 89_058
BOOTSTRAP_SEED = 108_058

FORMAL_NUM_ENVS = 16
FORMAL_UPDATES = 250
FORMAL_TRAIN_EPISODES = 4_000
FORMAL_TRANSITIONS_PER_ARM = 320_000
FORMAL_OPTIMIZER_STEPS_PER_ARM = 1_000
FORMAL_EVAL_EPISODES = 256
BOOTSTRAP_REPETITIONS = 10_000

TRAIN_DURATION_SUPPORT = (5, 9, 13)
HELD_OUT_DURATION_SUPPORT = (5, 7, 9)

NOT_JOINED = "not_joined"
ACTIVE = "active"
TEMPORARILY_ABSENT = "temporarily_absent"
TERMINAL = "terminal"

CHECKPOINT_SCHEMA_VERSION = 1
CHECKPOINT_KIND = "noncalendar_heterogeneous_tracking_g0"

THRESHOLDS: dict[str, float] = {
    "h_tracking_min": 0.780,
    "h_completion_min": 0.980,
    "h_utility_min": 0.880,
    "c_tracking_max": 0.550,
    "c_completion_max": 0.550,
    "c_utility_max": 0.550,
    "s_tracking_exclusive_max": 0.750,
    "s_completion_exclusive_max": 0.800,
    "s_utility_exclusive_max": 0.750,
    "h_minus_s_tracking_lcb_exclusive_min": 0.080,
    "h_minus_s_completion_lcb_exclusive_min": 0.200,
    "h_minus_s_utility_lcb_exclusive_min": 0.150,
    "d_iid_det_tracking_min": 0.780,
    "d_iid_det_completion_min": 0.900,
    "d_iid_det_utility_min": 0.830,
    "d_held_det_tracking_min": 0.720,
    "d_held_det_completion_min": 0.850,
    "d_held_det_utility_min": 0.780,
    "d_held_stoch_tracking_min": 0.650,
    "d_held_stoch_completion_min": 0.750,
    "d_held_stoch_utility_min": 0.700,
    "d_gain_utility_lcb_exclusive_min": 0.200,
    "d_minus_c_tracking_lcb_exclusive_min": 0.200,
    "d_minus_c_completion_lcb_exclusive_min": 0.250,
    "d_minus_c_utility_lcb_exclusive_min": 0.200,
}


def make_rng(seed: int, *coordinates: int) -> np.random.Generator:
    """Create the registered explicit PCG64/SeedSequence stream."""

    return np.random.Generator(
        np.random.PCG64(
            np.random.SeedSequence([int(seed), *(int(v) for v in coordinates)])
        )
    )


def _profile_contract(profile: Profile) -> tuple[tuple[int, ...], int, int, int]:
    if profile in ("train", "iid"):
        return TRAIN_DURATION_SUPPORT, 20, 40, 60
    if profile == "held_out":
        return HELD_OUT_DURATION_SUPPORT, 12, 36, 68
    raise ValueError(f"unsupported profile {profile!r}")


@dataclass(frozen=True)
class NoncalendarLedger:
    episode_id: int
    base_id: int
    sign_parity: int
    profile: Profile
    routing_permutation: tuple[int, ...]
    initial_count: int
    temporary_key: int
    terminal_key: int
    duration_streams: np.ndarray
    initial_targets: np.ndarray
    direct_frontier_priorities: np.ndarray
    generation_attempt: int

    @property
    def duration_support(self) -> tuple[int, ...]:
        return _profile_contract(self.profile)[0]

    @property
    def temporary_leave_time(self) -> int:
        return _profile_contract(self.profile)[1]

    @property
    def rejoin_time(self) -> int:
        return _profile_contract(self.profile)[2]

    @property
    def terminal_leave_time(self) -> int:
        return _profile_contract(self.profile)[3]

    @property
    def joined_key(self) -> int:
        return int(self.routing_permutation[self.initial_count])

    def validate(self) -> None:
        if self.episode_id < 0 or self.base_id != self.episode_id // 2:
            raise ValueError("ledger episode/base identity mismatch")
        if self.sign_parity != self.episode_id % 2:
            raise ValueError("ledger sign parity mismatch")
        if tuple(sorted(self.routing_permutation)) != tuple(range(MAX_LIFECYCLES)):
            raise ValueError("routing keys must be one permutation of six keys")
        allowed_initial = (3, 4) if self.profile in ("train", "iid") else (2, 5)
        if self.initial_count not in allowed_initial:
            raise ValueError("initial membership count violates profile")
        initial = set(self.routing_permutation[: self.initial_count])
        if self.temporary_key not in initial:
            raise ValueError("temporary leave must select an initial lifecycle")
        active_at_terminal = initial | {self.joined_key}
        if self.terminal_key not in active_at_terminal:
            raise ValueError("terminal leave must select an active lifecycle")
        if self.duration_streams.shape != (MAX_LIFECYCLES, 30):
            raise ValueError("duration stream shape mismatch")
        support = set(self.duration_support)
        if set(int(v) for v in np.unique(self.duration_streams)) != support:
            raise ValueError("duration stream support mismatch")
        for key in range(MAX_LIFECYCLES):
            for offset in range(0, self.duration_streams.shape[1], 3):
                if set(int(v) for v in self.duration_streams[key, offset : offset + 3]) != support:
                    raise ValueError("duration block is not a support permutation")
        if self.initial_targets.shape != (MAX_LIFECYCLES,):
            raise ValueError("initial-target shape mismatch")
        if not set(int(v) for v in self.initial_targets).issubset({-2, 2}):
            raise ValueError("initial target must be -2 or +2")
        if self.direct_frontier_priorities.shape != (HORIZON, MAX_LIFECYCLES):
            raise ValueError("presentation/order table shape mismatch")
        if not np.isfinite(self.direct_frontier_priorities).all():
            raise ValueError("presentation/order table contains non-finite values")

    def membership_deltas(self, time: int) -> tuple[MembershipDelta, ...]:
        if int(time) == 0:
            return tuple(
                MembershipDelta(JOIN, str(key), 0)
                for key in self.routing_permutation[: self.initial_count]
            )
        if int(time) == self.temporary_leave_time:
            return (MembershipDelta(TEMPORARY_LEAVE, str(self.temporary_key), 0),)
        if int(time) == self.rejoin_time:
            return (
                MembershipDelta(REJOIN, str(self.temporary_key), 0),
                MembershipDelta(JOIN, str(self.joined_key), 0),
            )
        if int(time) == self.terminal_leave_time:
            return (MembershipDelta(TERMINAL_LEAVE, str(self.terminal_key), 0),)
        return ()


def _duration_streams(rng: np.random.Generator, support: tuple[int, ...]) -> np.ndarray:
    rows = np.empty((MAX_LIFECYCLES, 30), dtype=np.int64)
    values = np.asarray(support, dtype=np.int64)
    for key in range(MAX_LIFECYCLES):
        for offset in range(0, rows.shape[1], 3):
            rows[key, offset : offset + 3] = rng.permutation(values)
    return rows


def _membership_active_keys(ledger: NoncalendarLedger, time: int) -> tuple[int, ...]:
    initial = list(ledger.routing_permutation[: ledger.initial_count])
    active = set(initial)
    if ledger.temporary_leave_time <= time < ledger.rejoin_time:
        active.remove(ledger.temporary_key)
    if time >= ledger.rejoin_time:
        active.add(ledger.joined_key)
    if time >= ledger.terminal_leave_time:
        active.remove(ledger.terminal_key)
    return tuple(sorted(active))


def ledger_active_row_count(ledger: NoncalendarLedger) -> int:
    return sum(len(_membership_active_keys(ledger, time)) for time in range(HORIZON))


def heterogeneity_support(ledger: NoncalendarLedger) -> dict[str, Any]:
    """Audit the registered held-out lifetime heterogeneity without actions."""

    remaining = np.zeros(MAX_LIFECYCLES, dtype=np.int64)
    duration_index = np.zeros(MAX_LIFECYCLES, dtype=np.int64)
    started = np.zeros(MAX_LIFECYCLES, dtype=np.bool_)
    transitions = np.zeros(MAX_LIFECYCLES, dtype=np.int64)
    differing_steps = 0
    for time in range(HORIZON):
        active = _membership_active_keys(ledger, time)
        for key in active:
            if not started[key]:
                started[key] = True
                remaining[key] = ledger.duration_streams[key, 0]
        if len(active) >= 2:
            active_remaining = remaining[np.asarray(active, dtype=np.int64)]
            if int(active_remaining.max() - active_remaining.min()) >= 2:
                differing_steps += 1
        for key in active:
            remaining[key] -= 1
            if remaining[key] == 0:
                transitions[key] += 1
                duration_index[key] += 1
                remaining[key] = ledger.duration_streams[key, duration_index[key]]
    transitioned_lifecycles = int(np.sum(transitions >= 1))
    return {
        "differing_remaining_steps": int(differing_steps),
        "transitioned_lifecycles": transitioned_lifecycles,
        "valid": bool(differing_steps >= 20 and transitioned_lifecycles >= 3),
    }


def make_noncalendar_ledger(
    episode_id: int,
    *,
    profile: Profile,
    task_seed: int,
    order_seed: int,
) -> NoncalendarLedger:
    """Materialize one sign-paired task ledger with no causal future input."""

    episode_id = int(episode_id)
    base_id = episode_id // 2
    sign_parity = episode_id % 2
    support = _profile_contract(profile)[0]
    for attempt in range(10_000):
        rng = make_rng(task_seed, base_id, attempt)
        routing = tuple(int(v) for v in rng.permutation(MAX_LIFECYCLES))
        initial_count = int(rng.choice((3, 4) if profile in ("train", "iid") else (2, 5)))
        temporary_key = int(rng.choice(np.asarray(routing[:initial_count], dtype=np.int64)))
        terminal_candidates = np.asarray((*routing[:initial_count], routing[initial_count]), dtype=np.int64)
        terminal_key = int(rng.choice(terminal_candidates))
        durations = _duration_streams(rng, support)
        base_targets = rng.choice(
            np.asarray((-2, 2), dtype=np.int64), size=MAX_LIFECYCLES, replace=True
        )
        if sign_parity:
            base_targets = -base_targets
        order_rng = make_rng(order_seed, base_id, 0)
        ledger = NoncalendarLedger(
            episode_id=episode_id,
            base_id=base_id,
            sign_parity=sign_parity,
            profile=profile,
            routing_permutation=routing,
            initial_count=initial_count,
            temporary_key=temporary_key,
            terminal_key=terminal_key,
            duration_streams=durations,
            initial_targets=np.asarray(base_targets, dtype=np.int64),
            direct_frontier_priorities=order_rng.random((HORIZON, MAX_LIFECYCLES)),
            generation_attempt=attempt,
        )
        ledger.validate()
        if profile != "held_out" or heterogeneity_support(ledger)["valid"]:
            return ledger
    raise RuntimeError("failed to materialize a valid held-out heterogeneity ledger")


def paired_ledgers_equal_except_targets(left: NoncalendarLedger, right: NoncalendarLedger) -> bool:
    if left.base_id != right.base_id or left.sign_parity == right.sign_parity:
        return False
    scalar_names = (
        "profile", "routing_permutation", "initial_count", "temporary_key",
        "terminal_key", "generation_attempt",
    )
    if any(getattr(left, name) != getattr(right, name) for name in scalar_names):
        return False
    return bool(
        np.array_equal(left.duration_streams, right.duration_streams)
        and np.array_equal(left.direct_frontier_priorities, right.direct_frontier_priorities)
        and np.array_equal(left.initial_targets, -right.initial_targets)
    )


def relabel_ledger(
    ledger: NoncalendarLedger, permutation: Sequence[int]
) -> NoncalendarLedger:
    """Synchronously rename opaque lifecycle routing keys."""

    mapping = tuple(int(v) for v in permutation)
    if tuple(sorted(mapping)) != tuple(range(MAX_LIFECYCLES)):
        raise ValueError("anonymous relabeling requires one six-key permutation")
    durations = np.empty_like(ledger.duration_streams)
    targets = np.empty_like(ledger.initial_targets)
    priorities = np.empty_like(ledger.direct_frontier_priorities)
    for old, new in enumerate(mapping):
        durations[new] = ledger.duration_streams[old]
        targets[new] = ledger.initial_targets[old]
        priorities[:, new] = ledger.direct_frontier_priorities[:, old]
    value = NoncalendarLedger(
        episode_id=ledger.episode_id,
        base_id=ledger.base_id,
        sign_parity=ledger.sign_parity,
        profile=ledger.profile,
        routing_permutation=tuple(mapping[key] for key in ledger.routing_permutation),
        initial_count=ledger.initial_count,
        temporary_key=mapping[ledger.temporary_key],
        terminal_key=mapping[ledger.terminal_key],
        duration_streams=durations,
        initial_targets=targets,
        direct_frontier_priorities=priorities,
        generation_attempt=ledger.generation_attempt,
    )
    value.validate()
    return value


@dataclass
class TrackingMemberState:
    key: int
    status: str = NOT_JOINED
    membership_epoch: int = 0
    x: int = 0
    previous_thrust: int = 0
    action_run: int = 0
    target: int = 2
    remaining: int = 0
    streak: int = 0
    active_steps: int = 0
    duration_index: int = 0
    target_changed: bool = False


@dataclass(frozen=True)
class TrackingMembershipChange:
    joined: tuple[int, ...] = ()
    temporarily_left: tuple[int, ...] = ()
    rejoined: tuple[int, ...] = ()
    terminally_left: tuple[int, ...] = ()


@dataclass(frozen=True)
class TrackingView:
    time: int
    active_keys: tuple[int, ...]
    observations: np.ndarray
    membership_change: TrackingMembershipChange


@dataclass(frozen=True)
class TrackingOutcome:
    tracking: float
    completion: float
    utility: float
    terminal_reward: float
    tracking_quarter_units: int
    active_rows: int
    completed_segments: int
    eligible_segments: int
    roster_sizes: tuple[int, ...]
    reward_trace: tuple[float, ...]

    @property
    def persistent_score(self) -> float:
        return self.tracking

    @property
    def short_score(self) -> float:
        return self.completion


class NoncalendarTrackingEnv:
    """Exact finite-state primitive tracking environment for one ledger."""

    def __init__(self, ledger: NoncalendarLedger, *, arm_mode: ArmMode):
        ledger.validate()
        if arm_mode not in ("calendar_masked", "demand_visible"):
            raise ValueError("invalid causal arm mode")
        self.ledger = ledger
        self.arm_mode = arm_mode
        self.members = {key: TrackingMemberState(key=key) for key in range(MAX_LIFECYCLES)}
        self.time = 0
        self.tracking_quarter_units = 0
        self.active_rows = 0
        self.completed_segments = 0
        self.eligible_segments = 0
        self.roster_sizes: list[int] = []
        self.reward_trace: list[float] = []
        self._prepared_time: int | None = None
        self._membership_change = TrackingMembershipChange()
        self._terminated = False

    @property
    def active_keys(self) -> tuple[int, ...]:
        active = tuple(key for key, state in self.members.items() if state.status == ACTIVE)
        if self.time >= HORIZON:
            return tuple(sorted(active))
        priorities = self.ledger.direct_frontier_priorities[self.time]
        return tuple(sorted(active, key=lambda key: float(priorities[key])))

    def _genuine_join(self, key: int) -> None:
        state = self.members[key]
        if state.status != NOT_JOINED:
            raise RuntimeError("genuine JOIN attempted to reuse a lifecycle")
        state.status = ACTIVE
        state.membership_epoch = 0
        state.x = 0
        state.previous_thrust = 0
        state.action_run = 0
        state.target = int(self.ledger.initial_targets[key])
        state.remaining = int(self.ledger.duration_streams[key, 0])
        state.streak = 0
        state.active_steps = 0
        state.duration_index = 0
        state.target_changed = True

    def _apply_membership(self) -> TrackingMembershipChange:
        joined: tuple[int, ...] = ()
        temporarily_left: tuple[int, ...] = ()
        rejoined: tuple[int, ...] = ()
        terminally_left: tuple[int, ...] = ()
        if self.time == 0:
            joined = tuple(self.ledger.routing_permutation[: self.ledger.initial_count])
            for key in joined:
                self._genuine_join(key)
        elif self.time == self.ledger.temporary_leave_time:
            key = self.ledger.temporary_key
            if self.members[key].status != ACTIVE:
                raise RuntimeError("temporary LEAVE selected a non-active lifecycle")
            self.members[key].status = TEMPORARILY_ABSENT
            temporarily_left = (key,)
        elif self.time == self.ledger.rejoin_time:
            key = self.ledger.temporary_key
            if self.members[key].status != TEMPORARILY_ABSENT:
                raise RuntimeError("REJOIN selected a non-absent lifecycle")
            self.members[key].status = ACTIVE
            self.members[key].membership_epoch += 1
            rejoined = (key,)
            joined = (self.ledger.joined_key,)
            self._genuine_join(self.ledger.joined_key)
        elif self.time == self.ledger.terminal_leave_time:
            key = self.ledger.terminal_key
            if self.members[key].status != ACTIVE:
                raise RuntimeError("terminal LEAVE selected a non-active lifecycle")
            self.members[key].status = TERMINAL
            del self.members[key]
            terminally_left = (key,)
        return TrackingMembershipChange(
            joined=joined,
            temporarily_left=temporarily_left,
            rejoined=rejoined,
            terminally_left=terminally_left,
        )

    def _prepare(self) -> None:
        if self._terminated or self.time >= HORIZON:
            raise RuntimeError("cannot prepare a terminated environment")
        if self._prepared_time == self.time:
            return
        self._membership_change = self._apply_membership()
        self._prepared_time = self.time
        self.roster_sizes.append(len(self.active_keys))

    def _raw_observations(self) -> np.ndarray:
        keys = self.active_keys
        states = [self.members[key] for key in keys]
        n = len(states)
        if n <= 0:
            raise RuntimeError("tracking environment has an empty active roster")
        xs = np.asarray([state.x for state in states], dtype=np.float64)
        targets = np.asarray([state.target for state in states], dtype=np.float64)
        changes = np.asarray([state.target_changed for state in states], dtype=np.float64)
        boundary_keys = set(self._membership_change.joined) | set(self._membership_change.rejoined)
        common = np.asarray(
            (
                self.time / 80.0,
                np.log1p(n) / np.log(7.0),
                float(np.mean(xs / 2.0)),
                float(np.mean(targets / 2.0)),
                float(np.mean((targets - xs) / 4.0)),
                float(np.mean(np.abs(targets - xs) / 4.0)),
                float(np.mean(changes)),
                float(sum(key in boundary_keys for key in keys) / n),
            ),
            dtype=np.float32,
        )
        rows = np.zeros((n, OBSERVATION_DIM), dtype=np.float32)
        for row, (key, state) in enumerate(zip(keys, states)):
            event_code = 1.0 if key in self._membership_change.joined else (
                -1.0 if key in self._membership_change.rejoined else 0.0
            )
            rows[row, :COMMON_FIELD_COUNT] = common
            rows[row, 8:] = np.asarray(
                (
                    state.x / 2.0,
                    state.target / 2.0,
                    (state.target - state.x) / 4.0,
                    float(state.target_changed),
                    event_code,
                    float(state.previous_thrust),
                    min(state.action_run, 16) / 16.0,
                ),
                dtype=np.float32,
            )
        return rows

    def observe(self) -> TrackingView:
        self._prepare()
        observations = self._raw_observations()
        if self.arm_mode == "calendar_masked":
            observations[:, CALENDAR_MASK_INDICES] = 0.0
        return TrackingView(
            time=self.time,
            active_keys=self.active_keys,
            observations=observations,
            membership_change=self._membership_change,
        )

    def step(self, actions: Mapping[int, int]) -> tuple[float, bool, dict[str, Any]]:
        self._prepare()
        active = self.active_keys
        if set(int(k) for k in actions) != set(active):
            raise ValueError("primitive action map must equal the active roster")
        for key in active:
            action = int(actions[key])
            if not 0 <= action < ACTION_COUNT:
                raise ValueError("primitive action is outside {0,1,2}")
            thrust = int(THRUST_BY_ACTION[action])
            state = self.members[key]
            new_x = int(np.clip(state.x + thrust, STATE_MIN, STATE_MAX))
            self.tracking_quarter_units += 4 - abs(new_x - state.target)
            new_streak = min(state.streak + 1, TARGET_STREAK) if new_x == state.target else 0
            state.action_run = min(state.action_run + 1, 16) if thrust == state.previous_thrust else 1
            state.previous_thrust = thrust
            state.x = new_x
            state.active_steps += 1
            state.remaining -= 1
            self.active_rows += 1
            if state.remaining == 0:
                self.eligible_segments += 1
                if new_streak == TARGET_STREAK:
                    self.completed_segments += 1
                state.duration_index += 1
                state.target = -state.target
                state.remaining = int(self.ledger.duration_streams[key, state.duration_index])
                state.streak = 0
                state.target_changed = True
            else:
                state.streak = int(new_streak)
                state.target_changed = False

        terminal = self.time == HORIZON - 1
        reward = 0.0
        if terminal:
            outcome = self._make_outcome(terminal_reward=0.0)
            reward = outcome.utility
        self.reward_trace.append(float(reward))
        self.time += 1
        self._prepared_time = None
        self._membership_change = TrackingMembershipChange()
        self._terminated = terminal
        return float(reward), terminal, {
            "tracking_quarter_units": self.tracking_quarter_units,
            "completed_segments": self.completed_segments,
            "eligible_segments": self.eligible_segments,
        }

    def _make_outcome(self, *, terminal_reward: float) -> TrackingOutcome:
        if self.active_rows <= 0 or self.eligible_segments <= 0:
            raise RuntimeError("episode lacks a valid tracking or completion denominator")
        tracking = self.tracking_quarter_units / float(4 * self.active_rows)
        completion = self.completed_segments / float(self.eligible_segments)
        utility = float(np.sqrt(tracking * completion))
        return TrackingOutcome(
            tracking=float(tracking),
            completion=float(completion),
            utility=float(utility),
            terminal_reward=float(terminal_reward),
            tracking_quarter_units=int(self.tracking_quarter_units),
            active_rows=int(self.active_rows),
            completed_segments=int(self.completed_segments),
            eligible_segments=int(self.eligible_segments),
            roster_sizes=tuple(self.roster_sizes),
            reward_trace=tuple(self.reward_trace),
        )

    def outcome(self) -> TrackingOutcome:
        if not self._terminated or self.time != HORIZON or len(self.reward_trace) != HORIZON:
            raise RuntimeError("outcome is available only after the terminal transition")
        value = self._make_outcome(terminal_reward=self.reward_trace[-1])
        if abs(value.terminal_reward - value.utility) > 1e-12:
            raise RuntimeError("terminal reward does not equal utility")
        if any(abs(v) > 0.0 for v in value.reward_trace[:-1]):
            raise RuntimeError("nonterminal reward must be exactly zero")
        return value

    def snapshot_state(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "ledger": deepcopy(self.ledger),
            "arm_mode": self.arm_mode,
            "members": deepcopy(self.members),
            "time": self.time,
            "tracking_quarter_units": self.tracking_quarter_units,
            "active_rows": self.active_rows,
            "completed_segments": self.completed_segments,
            "eligible_segments": self.eligible_segments,
            "roster_sizes": list(self.roster_sizes),
            "reward_trace": list(self.reward_trace),
            "prepared_time": self._prepared_time,
            "membership_change": deepcopy(self._membership_change),
            "terminated": self._terminated,
        }

    @classmethod
    def from_snapshot_state(cls, value: Mapping[str, Any]) -> "NoncalendarTrackingEnv":
        required = {
            "schema_version", "ledger", "arm_mode", "members", "time",
            "tracking_quarter_units", "active_rows", "completed_segments",
            "eligible_segments", "roster_sizes", "reward_trace", "prepared_time",
            "membership_change", "terminated",
        }
        payload = dict(value)
        if set(payload) != required or int(payload["schema_version"]) != 1:
            raise ValueError("tracking environment snapshot schema mismatch")
        env = cls(deepcopy(payload["ledger"]), arm_mode=payload["arm_mode"])
        env.members = deepcopy(payload["members"])
        env.time = int(payload["time"])
        env.tracking_quarter_units = int(payload["tracking_quarter_units"])
        env.active_rows = int(payload["active_rows"])
        env.completed_segments = int(payload["completed_segments"])
        env.eligible_segments = int(payload["eligible_segments"])
        env.roster_sizes = list(payload["roster_sizes"])
        env.reward_trace = list(payload["reward_trace"])
        env._prepared_time = payload["prepared_time"]
        env._membership_change = deepcopy(payload["membership_change"])
        env._terminated = bool(payload["terminated"])
        return env


def make_action_uniforms(episode_ids: Iterable[int], *, seed: int) -> np.ndarray:
    rows = []
    for episode_id in (int(v) for v in episode_ids):
        rng = make_rng(seed, episode_id // 2, 0)
        rows.append(rng.random((HORIZON, MAX_LIFECYCLES), dtype=np.float32))
    return np.stack(rows, axis=1)


def frontier_order(ledgers: Sequence[NoncalendarLedger], active_masks: np.ndarray, time: int) -> np.ndarray:
    rows: list[np.ndarray] = []
    for ledger, mask in zip(ledgers, active_masks):
        active = np.flatnonzero(mask)
        ordered = active[np.argsort(ledger.direct_frontier_priorities[time, active])]
        row = np.full(MAX_LIFECYCLES, -1, dtype=np.int64)
        row[: len(ordered)] = ordered
        rows.append(row)
    return np.stack(rows, axis=0)


def _seeds_for_profile(profile: Profile) -> tuple[int, int]:
    if profile == "train":
        return TRAIN_TASK_SEED, TRAIN_ORDER_SEED
    if profile == "iid":
        return IID_EVAL_TASK_SEED, EVAL_ORDER_SEED
    if profile == "held_out":
        return HELD_OUT_EVAL_TASK_SEED, EVAL_ORDER_SEED
    raise ValueError(f"unsupported profile {profile!r}")


def collect_causal_trajectory(
    model: DirectPrimitiveARPolicy,
    *,
    episode_ids: Iterable[int],
    profile: Profile,
    arm_mode: ArmMode,
    device: torch.device,
    deterministic: bool = False,
    action_seed: int | None = None,
) -> DirectTrajectory:
    ids = tuple(int(v) for v in episode_ids)
    if not ids:
        raise ValueError("causal collection requires at least one episode")
    task_seed, order_seed = _seeds_for_profile(profile)
    ledgers = tuple(
        make_noncalendar_ledger(
            episode_id, profile=profile, task_seed=task_seed, order_seed=order_seed
        )
        for episode_id in ids
    )
    environments = [NoncalendarTrackingEnv(ledger, arm_mode=arm_mode) for ledger in ledgers]
    uniforms = None
    if not deterministic:
        seed = TRAIN_ACTION_SEED if profile == "train" else EVAL_ACTION_SEED
        if action_seed is not None:
            seed = int(action_seed)
        uniforms = make_action_uniforms(ids, seed=seed)
    env_count = len(ids)
    hidden = torch.zeros((env_count, MAX_LIFECYCLES, model.hidden_dim), device=device)

    observations_rows: list[torch.Tensor] = []
    active_rows: list[torch.Tensor] = []
    order_rows: list[torch.Tensor] = []
    action_rows: list[torch.Tensor] = []
    logp_rows: list[torch.Tensor] = []
    value_rows: list[torch.Tensor] = []
    reward_rows: list[torch.Tensor] = []
    hidden_before_rows: list[torch.Tensor] = []
    hidden_after_rows: list[torch.Tensor] = []
    prefix_rows: list[torch.Tensor] = []

    model.eval()
    with torch.no_grad():
        for time in range(HORIZON):
            # Membership-boundary resets must not mutate the previously stored
            # hidden-after tensor, which is also the next step's live state.
            hidden = hidden.clone()
            obs_np = np.zeros((env_count, MAX_LIFECYCLES, OBSERVATION_DIM), dtype=np.float32)
            active_np = np.zeros((env_count, MAX_LIFECYCLES), dtype=np.bool_)
            views: list[TrackingView] = []
            for env_index, environment in enumerate(environments):
                view = environment.observe()
                views.append(view)
                for row_index, key in enumerate(view.active_keys):
                    obs_np[env_index, key] = view.observations[row_index]
                    active_np[env_index, key] = True
                for key in view.membership_change.terminally_left:
                    hidden[env_index, key].zero_()
                for key in view.membership_change.joined:
                    if bool(torch.count_nonzero(hidden[env_index, key])):
                        raise RuntimeError("genuine JOIN recurrent state is not zero")
            order_np = frontier_order(ledgers, active_np, time)
            observations = torch.as_tensor(obs_np, device=device)
            active_mask = torch.as_tensor(active_np, device=device)
            order = torch.as_tensor(order_np, device=device)
            hidden_before = hidden.clone()
            kwargs: dict[str, Any]
            if deterministic:
                kwargs = {"deterministic": True}
            else:
                assert uniforms is not None
                kwargs = {"sampling_uniforms": torch.as_tensor(uniforms[time], device=device)}
            output = model.forward_step(
                observations=observations,
                active_mask=active_mask,
                order=order,
                hidden=hidden,
                **kwargs,
            )
            action_values = output.actions.detach().cpu().numpy()
            rewards = np.zeros(env_count, dtype=np.float32)
            for env_index, (environment, view) in enumerate(zip(environments, views)):
                reward, _terminal, _info = environment.step(
                    {key: int(action_values[env_index, key]) for key in view.active_keys}
                )
                rewards[env_index] = reward
            observations_rows.append(observations)
            active_rows.append(active_mask)
            order_rows.append(order)
            action_rows.append(output.actions)
            logp_rows.append(output.token_log_probs)
            value_rows.append(output.value)
            reward_rows.append(torch.from_numpy(rewards))
            hidden_before_rows.append(hidden_before)
            hidden_after_rows.append(output.next_hidden)
            prefix_rows.append(output.prefix_counts)
            hidden = output.next_hidden

    return DirectTrajectory(
        observations=torch.stack(observations_rows).cpu(),
        active_mask=torch.stack(active_rows).cpu(),
        orders=torch.stack(order_rows).cpu(),
        actions=torch.stack(action_rows).cpu(),
        old_log_probs=torch.stack(logp_rows).cpu(),
        old_values=torch.stack(value_rows).cpu(),
        rewards=torch.stack(reward_rows),
        hidden_before=torch.stack(hidden_before_rows).cpu(),
        hidden_after=torch.stack(hidden_after_rows).cpu(),
        prefix_counts=torch.stack(prefix_rows).cpu(),
        outcomes=tuple(environment.outcome() for environment in environments),
        ledger_ids=ids,
    )


def trajectory_metric_arrays(trajectory: DirectTrajectory) -> dict[str, np.ndarray]:
    outcomes = tuple(trajectory.outcomes)
    return {
        "tracking": np.asarray([o.tracking for o in outcomes], dtype=np.float64),
        "completion": np.asarray([o.completion for o in outcomes], dtype=np.float64),
        "utility": np.asarray([o.utility for o in outcomes], dtype=np.float64),
    }


def anonymous_relabeling_audit(
    model: DirectPrimitiveARPolicy,
    *,
    device: torch.device,
) -> dict[str, Any]:
    """Check model/environment equivariance under one opaque-key relabeling."""

    ledger = make_noncalendar_ledger(
        0,
        profile="held_out",
        task_seed=HELD_OUT_EVAL_TASK_SEED,
        order_seed=EVAL_ORDER_SEED,
    )
    mapping = (2, 5, 1, 4, 0, 3)
    renamed = relabel_ledger(ledger, mapping)
    left = NoncalendarTrackingEnv(ledger, arm_mode="demand_visible")
    right = NoncalendarTrackingEnv(renamed, arm_mode="demand_visible")
    left_hidden = torch.zeros((1, MAX_LIFECYCLES, model.hidden_dim), device=device)
    right_hidden = torch.zeros_like(left_hidden)
    maximum_error = 0.0
    actions_equal = True
    rewards_equal = True
    model.eval()
    with torch.no_grad():
        for time in range(HORIZON):
            left_view = left.observe()
            right_view = right.observe()
            left_obs = np.zeros((1, MAX_LIFECYCLES, OBSERVATION_DIM), dtype=np.float32)
            right_obs = np.zeros_like(left_obs)
            left_active = np.zeros((1, MAX_LIFECYCLES), dtype=np.bool_)
            right_active = np.zeros_like(left_active)
            for row, key in enumerate(left_view.active_keys):
                left_obs[0, key] = left_view.observations[row]
                left_active[0, key] = True
            for row, key in enumerate(right_view.active_keys):
                right_obs[0, key] = right_view.observations[row]
                right_active[0, key] = True
            for old, new in enumerate(mapping):
                if not np.array_equal(left_obs[0, old], right_obs[0, new]):
                    maximum_error = float("inf")
                if bool(left_active[0, old]) != bool(right_active[0, new]):
                    maximum_error = float("inf")
                right_hidden[0, new] = left_hidden[0, old]
            left_order_np = frontier_order((ledger,), left_active, time)
            right_order_np = frontier_order((renamed,), right_active, time)
            expected_right_order = np.asarray(
                [[mapping[key] if key >= 0 else -1 for key in left_order_np[0]]],
                dtype=np.int64,
            )
            if not np.array_equal(right_order_np, expected_right_order):
                maximum_error = float("inf")
            left_output = model.forward_step(
                observations=torch.as_tensor(left_obs, device=device),
                active_mask=torch.as_tensor(left_active, device=device),
                order=torch.as_tensor(left_order_np, device=device),
                hidden=left_hidden,
                deterministic=True,
            )
            right_output = model.forward_step(
                observations=torch.as_tensor(right_obs, device=device),
                active_mask=torch.as_tensor(right_active, device=device),
                order=torch.as_tensor(right_order_np, device=device),
                hidden=right_hidden,
                deterministic=True,
            )
            for old, new in enumerate(mapping):
                if left_active[0, old]:
                    actions_equal = actions_equal and int(left_output.actions[0, old]) == int(right_output.actions[0, new])
                    maximum_error = max(
                        maximum_error,
                        float(torch.abs(left_output.token_log_probs[0, old] - right_output.token_log_probs[0, new])),
                        float(torch.max(torch.abs(left_output.next_hidden[0, old] - right_output.next_hidden[0, new]))),
                    )
            maximum_error = max(
                maximum_error,
                float(torch.abs(left_output.value[0] - right_output.value[0])),
            )
            left_reward, _, _ = left.step(
                {key: int(left_output.actions[0, key]) for key in left_view.active_keys}
            )
            right_reward, _, _ = right.step(
                {key: int(right_output.actions[0, key]) for key in right_view.active_keys}
            )
            rewards_equal = rewards_equal and left_reward == right_reward
            left_hidden = left_output.next_hidden
            right_hidden = right_output.next_hidden
    outcomes_equal = left.outcome() == right.outcome()
    return {
        "actions_equal": actions_equal,
        "rewards_equal": rewards_equal,
        "outcomes_equal": outcomes_equal,
        "maximum_error": maximum_error,
        "valid": bool(actions_equal and rewards_equal and outcomes_equal and maximum_error <= 1e-6),
    }


@dataclass(frozen=True)
class SolverStep:
    physical_time: int
    target: int
    segment_end: bool
    join_or_rejoin: bool


@dataclass(frozen=True)
class SolverOutcome:
    tracking: float
    completion: float
    utility: float
    tracking_quarter_units: int
    completed_segments: int
    active_rows: int
    eligible_segments: int


def lifecycle_solver_steps(ledger: NoncalendarLedger, key: int) -> tuple[SolverStep, ...]:
    rows: list[SolverStep] = []
    started = False
    target = int(ledger.initial_targets[key])
    remaining = 0
    duration_index = 0
    for time in range(HORIZON):
        active = key in _membership_active_keys(ledger, time)
        if not active:
            continue
        if not started:
            started = True
            remaining = int(ledger.duration_streams[key, 0])
        remaining -= 1
        segment_end = remaining == 0
        join_or_rejoin = bool(
            time == 0
            or (key == ledger.joined_key and time == ledger.rejoin_time)
            or (key == ledger.temporary_key and time == ledger.rejoin_time)
        )
        rows.append(SolverStep(time, target, segment_end, join_or_rejoin))
        if segment_end:
            duration_index += 1
            target = -target
            remaining = int(ledger.duration_streams[key, duration_index])
    return tuple(rows)


def _pareto_pairs(values: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    unique = set(values)
    return {
        value
        for value in unique
        if not any(
            other != value and other[0] >= value[0] and other[1] >= value[1]
            for other in unique
        )
    }


def solve_trace_outcomes(
    steps: Sequence[SolverStep], *, arm: SolverArm, prune: bool = True
) -> set[tuple[int, int]]:
    if arm not in ("H", "S"):
        raise ValueError("solver arm must be H or S")
    states: dict[tuple[int, int, int], set[tuple[int, int]]] = {(0, 0, 0): {(0, 0)}}
    for step in steps:
        next_states: dict[tuple[int, int, int], set[tuple[int, int]]] = {}
        for (x, streak, previous), labels in states.items():
            can_change = arm == "H" or step.physical_time % SHARED_RENEWAL_PERIOD == 0 or step.join_or_rejoin
            actions = (-1, 0, 1) if can_change else (previous,)
            for thrust in actions:
                new_x = int(np.clip(x + thrust, STATE_MIN, STATE_MAX))
                new_streak = min(streak + 1, TARGET_STREAK) if new_x == step.target else 0
                completed = int(step.segment_end and new_streak == TARGET_STREAK)
                state_streak = 0 if step.segment_end else new_streak
                state = (new_x, state_streak, thrust)
                bucket = next_states.setdefault(state, set())
                for tracking, completion in labels:
                    bucket.add((tracking + 4 - abs(new_x - step.target), completion + completed))
        states = {
            state: (_pareto_pairs(labels) if prune else set(labels))
            for state, labels in next_states.items()
        }
    outcomes = set().union(*states.values()) if states else {(0, 0)}
    return _pareto_pairs(outcomes) if prune else outcomes


def brute_force_trace_outcomes(steps: Sequence[SolverStep], *, arm: SolverArm) -> set[tuple[int, int]]:
    outcomes: set[tuple[int, int]] = set()

    def visit(index: int, x: int, streak: int, previous: int, tracking: int, completed: int) -> None:
        if index == len(steps):
            outcomes.add((tracking, completed))
            return
        step = steps[index]
        can_change = arm == "H" or step.physical_time % SHARED_RENEWAL_PERIOD == 0 or step.join_or_rejoin
        actions = (-1, 0, 1) if can_change else (previous,)
        for thrust in actions:
            new_x = int(np.clip(x + thrust, STATE_MIN, STATE_MAX))
            new_streak = min(streak + 1, TARGET_STREAK) if new_x == step.target else 0
            visit(
                index + 1,
                new_x,
                0 if step.segment_end else new_streak,
                thrust,
                tracking + 4 - abs(new_x - step.target),
                completed + int(step.segment_end and new_streak == TARGET_STREAK),
            )

    visit(0, 0, 0, 0, 0, 0)
    return outcomes


def solve_hindsight_episode(ledger: NoncalendarLedger, *, arm: SolverArm) -> SolverOutcome:
    aggregate: set[tuple[int, int]] = {(0, 0)}
    active_rows = 0
    eligible = 0
    for key in range(MAX_LIFECYCLES):
        steps = lifecycle_solver_steps(ledger, key)
        if not steps:
            continue
        active_rows += len(steps)
        eligible += sum(int(step.segment_end) for step in steps)
        member = solve_trace_outcomes(steps, arm=arm, prune=True)
        aggregate = _pareto_pairs(
            (left_a + right_a, left_b + right_b)
            for left_a, left_b in aggregate
            for right_a, right_b in member
        )
    if active_rows <= 0 or eligible <= 0:
        raise RuntimeError("solver episode has an invalid denominator")
    candidates = []
    for tracking_units, completed in aggregate:
        tracking = tracking_units / float(4 * active_rows)
        completion = completed / float(eligible)
        candidates.append((float(np.sqrt(tracking * completion)), tracking, completion, tracking_units, completed))
    utility, tracking, completion, tracking_units, completed = max(candidates)
    return SolverOutcome(
        tracking=float(tracking),
        completion=float(completion),
        utility=float(utility),
        tracking_quarter_units=int(tracking_units),
        completed_segments=int(completed),
        active_rows=int(active_rows),
        eligible_segments=int(eligible),
    )


def bootstrap_cluster_indices(
    cluster_count: int = 128,
    *,
    repetitions: int = BOOTSTRAP_REPETITIONS,
    seed: int = BOOTSTRAP_SEED,
) -> np.ndarray:
    rng = np.random.Generator(
        np.random.PCG64(np.random.SeedSequence([int(seed)]))
    )
    return rng.integers(0, cluster_count, size=(repetitions, cluster_count), dtype=np.int64)


def paired_cluster_ci(values: np.ndarray, *, indices: np.ndarray) -> tuple[float, float, float]:
    episode_values = np.asarray(values, dtype=np.float64)
    if episode_values.shape != (2 * indices.shape[1],):
        raise ValueError("paired bootstrap requires two sign mates per base cluster")
    clusters = episode_values.reshape(-1, 2).mean(axis=1)
    estimates = clusters[indices].mean(axis=1)
    return (
        float(np.quantile(estimates, 0.025)),
        float(clusters.mean()),
        float(np.quantile(estimates, 0.975)),
    )


def initialize_causal_arms(device: torch.device) -> tuple[
    DirectPrimitiveARPolicy,
    DirectPrimitiveARPolicy,
    torch.optim.Optimizer,
    torch.optim.Optimizer,
]:
    torch.manual_seed(MODEL_INITIALIZATION_SEED)
    calendar = DirectPrimitiveARPolicy().to(device)
    demand = DirectPrimitiveARPolicy().to(device)
    demand.load_state_dict(calendar.state_dict(), strict=True)
    if calendar.parameter_count != PARAMETER_COUNT or demand.parameter_count != PARAMETER_COUNT:
        raise RuntimeError("registered direct policy parameter count mismatch")
    calendar_optimizer = torch.optim.Adam(calendar.parameters(), lr=LEARNING_RATE)
    demand_optimizer = torch.optim.Adam(demand.parameters(), lr=LEARNING_RATE)
    return calendar, demand, calendar_optimizer, demand_optimizer


def _checkpoint_header(arm_mode: ArmMode) -> dict[str, Any]:
    return {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "kind": CHECKPOINT_KIND,
        "arm_mode": arm_mode,
        "model_shape": {
            "observation_width": OBSERVATION_DIM,
            "hidden_width": HIDDEN_DIM,
            "parameter_count": PARAMETER_COUNT,
            "bptt_chunk": MAX_RECURRENT_CHUNK,
        },
        "observation_mask_indices": list(CALENDAR_MASK_INDICES if arm_mode == "calendar_masked" else ()),
        "seeds": {
            "model": MODEL_INITIALIZATION_SEED,
            "train_task": TRAIN_TASK_SEED,
            "train_order": TRAIN_ORDER_SEED,
            "train_action": TRAIN_ACTION_SEED,
            "iid_eval_task": IID_EVAL_TASK_SEED,
            "held_out_eval_task": HELD_OUT_EVAL_TASK_SEED,
            "eval_order": EVAL_ORDER_SEED,
            "eval_action": EVAL_ACTION_SEED,
            "bootstrap": BOOTSTRAP_SEED,
        },
        "profiles": {
            "train_duration_support": list(TRAIN_DURATION_SUPPORT),
            "iid_duration_support": list(TRAIN_DURATION_SUPPORT),
            "held_out_duration_support": list(HELD_OUT_DURATION_SUPPORT),
        },
        "exposure": {
            "num_envs": FORMAL_NUM_ENVS,
            "horizon": HORIZON,
            "outer_updates": FORMAL_UPDATES,
            "ppo_passes": PPO_PASSES,
            "training_episode_ids": [0, FORMAL_TRAIN_EPISODES - 1],
        },
        "evaluation": {
            "episode_ids": [0, FORMAL_EVAL_EPISODES - 1],
            "profiles": ["iid", "held_out"],
            "modes": ["deterministic", "stochastic"],
            "checkpoints": [0, FORMAL_UPDATES],
        },
        "rng_ownership": {
            "task": "PCG64 SeedSequence([task_seed, base_id, attempt])",
            "order": "PCG64 SeedSequence([order_seed, base_id, 0])",
            "action": "PCG64 SeedSequence([action_seed, base_id, 0])",
        },
    }


def save_benchmark_checkpoint(
    path: Path,
    *,
    arm_mode: ArmMode,
    model: DirectPrimitiveARPolicy,
    optimizer: torch.optim.Optimizer,
    completed_update: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            **_checkpoint_header(arm_mode),
            "completed_update": int(completed_update),
            "next_training_episode_id": int(completed_update) * FORMAL_NUM_ENVS,
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "torch_cpu_rng_state": torch.get_rng_state(),
            "torch_cuda_rng_states": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],
        },
        path,
    )


def load_benchmark_checkpoint(
    path: Path,
    *,
    arm_mode: ArmMode,
    model: DirectPrimitiveARPolicy,
    optimizer: torch.optim.Optimizer,
) -> dict[str, Any]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    required = set(_checkpoint_header(arm_mode)) | {
        "completed_update", "next_training_episode_id", "model_state",
        "optimizer_state", "torch_cpu_rng_state", "torch_cuda_rng_states",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        raise ValueError("benchmark checkpoint key set mismatch")
    for key, expected in _checkpoint_header(arm_mode).items():
        if payload[key] != expected:
            raise ValueError(f"benchmark checkpoint header mismatch: {key}")
    completed = int(payload["completed_update"])
    if completed < 0 or completed > FORMAL_UPDATES:
        raise ValueError("benchmark checkpoint completed-update mismatch")
    if int(payload["next_training_episode_id"]) != completed * FORMAL_NUM_ENVS:
        raise ValueError("benchmark checkpoint episode counter mismatch")
    model.load_state_dict(payload["model_state"], strict=True)
    optimizer.load_state_dict(payload["optimizer_state"])
    model_device = next(model.parameters()).device
    for state in optimizer.state.values():
        for name, value in state.items():
            if isinstance(value, torch.Tensor):
                state[name] = value.to(model_device)
    torch.set_rng_state(payload["torch_cpu_rng_state"])
    if torch.cuda.is_available() and payload["torch_cuda_rng_states"]:
        torch.cuda.set_rng_state_all(payload["torch_cuda_rng_states"])
    return payload


def checkpoint_round_trip_error(
    path: Path,
    *,
    arm_mode: ArmMode,
    model: DirectPrimitiveARPolicy,
    optimizer: torch.optim.Optimizer,
) -> float:
    model_before = model_state_copy(model)
    optimizer_before = deepcopy(optimizer.state_dict())
    load_benchmark_checkpoint(path, arm_mode=arm_mode, model=model, optimizer=optimizer)
    return max(
        max(float(torch.max(torch.abs(model_before[name] - model.state_dict()[name].cpu()))) for name in model_before),
        nested_state_maximum_difference(optimizer_before, optimizer.state_dict()),
    )


def select_result_branch(
    *,
    m0_valid: bool,
    means: Mapping[str, float],
    lcbs: Mapping[str, float],
) -> str:
    """Apply the frozen mutually-exclusive priority tree, failing closed."""

    required_means = {
        "h_tracking", "h_completion", "h_utility",
        "c_held_det_tracking", "c_held_det_completion", "c_held_det_utility",
        "s_tracking", "s_completion", "s_utility",
        "d_iid_det_tracking", "d_iid_det_completion", "d_iid_det_utility",
        "d_held_det_tracking", "d_held_det_completion", "d_held_det_utility",
        "d_held_stoch_tracking", "d_held_stoch_completion", "d_held_stoch_utility",
    }
    required_lcbs = {
        "h_minus_s_tracking", "h_minus_s_completion", "h_minus_s_utility",
        "d_gain_utility", "d_minus_c_tracking", "d_minus_c_completion",
        "d_minus_c_utility",
    }
    if set(means) != required_means or set(lcbs) != required_lcbs:
        raise ValueError("terminal result contract key set mismatch")
    if not all(np.isfinite(float(value)) for value in (*means.values(), *lcbs.values())):
        raise ValueError("terminal result contract contains non-finite values")
    if not m0_valid:
        return "INVALID_BENCHMARK_IDENTIFIABILITY_G0"
    h_pass = bool(
        means["h_tracking"] >= THRESHOLDS["h_tracking_min"]
        and means["h_completion"] >= THRESHOLDS["h_completion_min"]
        and means["h_utility"] >= THRESHOLDS["h_utility_min"]
    )
    if not h_pass:
        return "REJECT_BENCHMARK_STRUCTURALLY_UNREACHABLE"
    c_pass = bool(
        means["c_held_det_tracking"] <= THRESHOLDS["c_tracking_max"]
        and means["c_held_det_completion"] <= THRESHOLDS["c_completion_max"]
        and means["c_held_det_utility"] <= THRESHOLDS["c_utility_max"]
    )
    d_pass = bool(
        means["d_iid_det_tracking"] >= THRESHOLDS["d_iid_det_tracking_min"]
        and means["d_iid_det_completion"] >= THRESHOLDS["d_iid_det_completion_min"]
        and means["d_iid_det_utility"] >= THRESHOLDS["d_iid_det_utility_min"]
        and means["d_held_det_tracking"] >= THRESHOLDS["d_held_det_tracking_min"]
        and means["d_held_det_completion"] >= THRESHOLDS["d_held_det_completion_min"]
        and means["d_held_det_utility"] >= THRESHOLDS["d_held_det_utility_min"]
        and means["d_held_stoch_tracking"] >= THRESHOLDS["d_held_stoch_tracking_min"]
        and means["d_held_stoch_completion"] >= THRESHOLDS["d_held_stoch_completion_min"]
        and means["d_held_stoch_utility"] >= THRESHOLDS["d_held_stoch_utility_min"]
        and lcbs["d_gain_utility"] > THRESHOLDS["d_gain_utility_lcb_exclusive_min"]
    )
    d_minus_c_pass = bool(
        lcbs["d_minus_c_tracking"] > THRESHOLDS["d_minus_c_tracking_lcb_exclusive_min"]
        and lcbs["d_minus_c_completion"] > THRESHOLDS["d_minus_c_completion_lcb_exclusive_min"]
        and lcbs["d_minus_c_utility"] > THRESHOLDS["d_minus_c_utility_lcb_exclusive_min"]
    )
    if not c_pass or (d_pass and not d_minus_c_pass):
        return "REJECT_BENCHMARK_CALENDAR_IDENTIFIABLE"
    s_pressure = bool(
        means["s_tracking"] < THRESHOLDS["s_tracking_exclusive_max"]
        and means["s_completion"] < THRESHOLDS["s_completion_exclusive_max"]
        and means["s_utility"] < THRESHOLDS["s_utility_exclusive_max"]
        and lcbs["h_minus_s_tracking"] > THRESHOLDS["h_minus_s_tracking_lcb_exclusive_min"]
        and lcbs["h_minus_s_completion"] > THRESHOLDS["h_minus_s_completion_lcb_exclusive_min"]
        and lcbs["h_minus_s_utility"] > THRESHOLDS["h_minus_s_utility_lcb_exclusive_min"]
    )
    if not s_pressure:
        return "REJECT_BENCHMARK_NO_HETEROGENEOUS_LIFETIME_PRESSURE"
    if not d_pass:
        return "NO_ACCESS_BENCHMARK_ORDINARY_CONTROL"
    return "PASS_BENCHMARK_IDENTIFIABILITY_AND_ORDINARY_ACCESS"


def registered_contract() -> dict[str, Any]:
    return {
        "horizon": HORIZON,
        "maximum_lifecycles": MAX_LIFECYCLES,
        "observation_width": OBSERVATION_DIM,
        "calendar_mask_indices": list(CALENDAR_MASK_INDICES),
        "field_5_formula": "mean_{i in A_t}(abs(g_i-x_i)/4)",
        "field_5_range": [0.0, 1.0],
        "duration_support": {
            "train": list(TRAIN_DURATION_SUPPORT),
            "iid": list(TRAIN_DURATION_SUPPORT),
            "held_out": list(HELD_OUT_DURATION_SUPPORT),
        },
        "shared_renewal_period": SHARED_RENEWAL_PERIOD,
        "num_envs": FORMAL_NUM_ENVS,
        "outer_updates": FORMAL_UPDATES,
        "transitions_per_arm": FORMAL_TRANSITIONS_PER_ARM,
        "optimizer_steps_per_arm": FORMAL_OPTIMIZER_STEPS_PER_ARM,
        "training_episodes_per_arm": FORMAL_TRAIN_EPISODES,
        "eval_episodes_per_cell": FORMAL_EVAL_EPISODES,
        "evaluation_cells_per_arm": 8,
        "parameter_count_per_arm": PARAMETER_COUNT,
        "ppo_passes": PPO_PASSES,
        "thresholds": dict(THRESHOLDS),
    }
