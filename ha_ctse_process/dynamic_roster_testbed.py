"""Generic-short dynamic-roster testbed and no-learning carrier evaluation.

This module implements only the environment contract frozen in
``F0_F1_DYNAMIC_ROSTER_TESTBED_CONTRACT.md``.  It contains no policy network,
skill controller, intrinsic reward, shaping term, or optimizer.  Routing keys
are exposed to controller adapters only; actor observations are anonymous.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np

from ha_ctse_process.variable_roster_event import (
    JOIN,
    REJOIN,
    SNAPSHOT_CAPABILITY_NAME,
    SNAPSHOT_CAPABILITY_VERSION,
    TEMPORARY_LEAVE,
    TERMINAL_LEAVE,
)
from ha_ctse_process.variable_roster_event_types import (
    BoundaryMember,
    BoundarySnapshot,
    MembershipDelta,
    MembershipTransaction,
)


IDLE = 0
PERSIST = 1
SHORT = 2
ACTION_COUNT = 3

HORIZON = 80
MAX_LIFECYCLES = 6
OBSERVATION_DIM = 15
PERSISTENT_TARGET = 64
SHORT_WINDOW = 4
SHORT_STREAK_TARGET = 2
WAVE_CANDIDATES = (
    (0,),
    (9, 10),
    (24, 25),
    (32, 33),
    (40,),
    (49, 50),
    (64, 65),
    (72, 73),
)
EXPECTED_SHORT_REQUIREMENT = 24

EVALUATION_LEDGER_SEED = 97_057
ACTION_SAMPLING_SEED = 87_057
TRAIN_LEDGER_SEED = 67_057

NOT_JOINED = "not_joined"
ACTIVE = "active"
TEMPORARILY_ABSENT = "temporarily_absent"
TERMINAL = "terminal"


def _rng(master_seed: int, episode_id: int, stream_id: int) -> np.random.Generator:
    return np.random.default_rng(
        np.random.SeedSequence(
            [int(master_seed), int(episode_id), int(stream_id)]
        )
    )


@dataclass(frozen=True)
class DynamicRosterLedger:
    """All environment-side randomness for one episode."""

    episode_id: int
    temporary_leave: tuple[int, int]
    terminal_leave: tuple[int, int]
    wave_arrivals: tuple[int, ...]
    owner_priorities: np.ndarray
    presentation_priorities: np.ndarray
    direct_frontier_priorities: np.ndarray

    def validate(self) -> None:
        if len(self.wave_arrivals) != len(WAVE_CANDIDATES):
            raise ValueError("the ledger must contain exactly eight wave arrivals")
        if any(
            int(arrival) not in candidates
            for arrival, candidates in zip(self.wave_arrivals, WAVE_CANDIDATES)
        ):
            raise ValueError("a wave arrival lies outside its registered window")
        if len(set(self.temporary_leave)) != 2 or not set(
            self.temporary_leave
        ).issubset({0, 1, 2, 3}):
            raise ValueError("temporary leave must select two initial lifecycles")
        if len(set(self.terminal_leave)) != 2 or not set(
            self.terminal_leave
        ).issubset(set(range(MAX_LIFECYCLES))):
            raise ValueError("terminal leave must select two active lifecycles")
        expected_shape = (HORIZON, MAX_LIFECYCLES)
        for name in (
            "owner_priorities",
            "presentation_priorities",
            "direct_frontier_priorities",
        ):
            values = np.asarray(getattr(self, name))
            if values.shape != expected_shape:
                raise ValueError(
                    f"{name} has shape {values.shape}, expected {expected_shape}"
                )
            if not np.all(np.isfinite(values)):
                raise ValueError(f"{name} contains a non-finite value")


def make_dynamic_roster_ledger(
    episode_id: int,
    *,
    master_seed: int = EVALUATION_LEDGER_SEED,
) -> DynamicRosterLedger:
    """Create the registered task ledger from independent RNG streams."""

    temporary_rng = _rng(master_seed, episode_id, 0)
    terminal_rng = _rng(master_seed, episode_id, 1)
    wave_rng = _rng(master_seed, episode_id, 2)
    owner_rng = _rng(master_seed, episode_id, 3)
    presentation_rng = _rng(master_seed, episode_id, 4)
    frontier_rng = _rng(master_seed, episode_id, 5)

    ledger = DynamicRosterLedger(
        episode_id=int(episode_id),
        temporary_leave=tuple(
            sorted(
                int(value)
                for value in temporary_rng.choice(4, size=2, replace=False)
            )
        ),
        terminal_leave=tuple(
            sorted(
                int(value)
                for value in terminal_rng.choice(
                    MAX_LIFECYCLES, size=2, replace=False
                )
            )
        ),
        wave_arrivals=tuple(
            int(wave_rng.choice(np.asarray(candidates, dtype=np.int64)))
            for candidates in WAVE_CANDIDATES
        ),
        owner_priorities=owner_rng.random((HORIZON, MAX_LIFECYCLES)),
        presentation_priorities=presentation_rng.random(
            (HORIZON, MAX_LIFECYCLES)
        ),
        direct_frontier_priorities=frontier_rng.random(
            (HORIZON, MAX_LIFECYCLES)
        ),
    )
    ledger.validate()
    return ledger


@dataclass
class LifecycleState:
    key: int
    status: str = NOT_JOINED
    previous_action: int = IDLE
    active_steps: int = 0
    short_streak: int = 0
    contributed_current_wave: bool = False
    membership_epoch: int = 0


@dataclass
class ShortWave:
    index: int
    arrival_time: int
    required_work: int
    deadline_exclusive: int
    completed_work: int = 0

    def steps_remaining(self, time: int) -> int:
        return max(0, int(self.deadline_exclusive) - int(time))


@dataclass(frozen=True)
class MembershipChange:
    joined: tuple[int, ...] = ()
    temporarily_left: tuple[int, ...] = ()
    rejoined: tuple[int, ...] = ()
    terminally_left: tuple[int, ...] = ()


@dataclass(frozen=True)
class DynamicRosterView:
    time: int
    active_keys: tuple[int, ...]
    observations: np.ndarray
    membership_change: MembershipChange
    wave_active: bool
    wave_required: int
    wave_completed: int


@dataclass(frozen=True)
class EpisodeOutcome:
    persistent_score: float
    short_score: float
    utility: float
    terminal_reward: float
    short_required_total: int
    short_completed_total: int
    roster_sizes: tuple[int, ...]
    reward_trace: tuple[float, ...]
    observation_shapes_valid: bool


class GenericShortDynamicRosterEnv:
    """One exact 80-step dynamic-roster environment episode."""

    def __init__(self, ledger: DynamicRosterLedger):
        ledger.validate()
        self.ledger = ledger
        self.lifecycles = {
            key: LifecycleState(key=key) for key in range(MAX_LIFECYCLES)
        }
        self.time = 0
        self.persistent_owner: int | None = None
        self.persistent_units = 0
        self.current_wave: ShortWave | None = None
        self.wave_records: list[ShortWave] = []
        self.short_required_total = 0
        self.short_completed_total = 0
        self.roster_sizes: list[int] = []
        self.reward_trace: list[float] = []
        self.observation_shapes_valid = True
        self._prepared_time: int | None = None
        self._current_membership_change = MembershipChange()
        self._pending_event_transaction: MembershipTransaction | None = None
        self._terminated = False

    @property
    def active_keys(self) -> tuple[int, ...]:
        active = [
            key
            for key, state in self.lifecycles.items()
            if state.status == ACTIVE
        ]
        if self.time >= HORIZON:
            return tuple(sorted(active))
        priorities = self.ledger.presentation_priorities[self.time]
        return tuple(sorted(active, key=lambda key: float(priorities[key])))

    def preferred_owner(self, keys: tuple[int, ...] | None = None) -> int:
        candidates = tuple(self.active_keys if keys is None else keys)
        if not candidates:
            raise RuntimeError("cannot select a persistent owner from an empty set")
        priorities = self.ledger.owner_priorities[self.time]
        return min(candidates, key=lambda key: float(priorities[key]))

    def _reset_wave_member_state(self) -> None:
        for state in self.lifecycles.values():
            state.short_streak = 0
            state.contributed_current_wave = False

    def _apply_membership(self) -> MembershipChange:
        joined: tuple[int, ...] = ()
        temporarily_left: tuple[int, ...] = ()
        rejoined: tuple[int, ...] = ()
        terminally_left: tuple[int, ...] = ()

        if self.time == 0:
            joined = (0, 1, 2, 3)
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
                    raise RuntimeError("temporary leave selected an inactive lifecycle")
                state.status = TEMPORARILY_ABSENT
                state.short_streak = 0
                state.contributed_current_wave = False
                if self.persistent_owner == key:
                    self.persistent_owner = None
        elif self.time == 40:
            rejoined = self.ledger.temporary_leave
            joined = (4, 5)
            for key in rejoined:
                state = self.lifecycles[key]
                if state.status != TEMPORARILY_ABSENT:
                    raise RuntimeError("rejoin selected a non-absent lifecycle")
                state.status = ACTIVE
                state.membership_epoch += 1
            for key in joined:
                state = self.lifecycles[key]
                if state.status != NOT_JOINED:
                    raise RuntimeError("genuine join attempted to reuse a lifecycle")
                state.status = ACTIVE
                state.previous_action = IDLE
                state.active_steps = 0
        elif self.time == 60:
            terminally_left = self.ledger.terminal_leave
            for key in terminally_left:
                state = self.lifecycles[key]
                if state.status != ACTIVE:
                    raise RuntimeError("terminal leave selected an inactive lifecycle")
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

    def _open_wave_if_due(self) -> None:
        matches = [
            index
            for index, arrival in enumerate(self.ledger.wave_arrivals)
            if int(arrival) == self.time
        ]
        if not matches:
            return
        if len(matches) != 1 or self.current_wave is not None:
            raise RuntimeError("the registered wave windows must not overlap")
        active_count = len(self.active_keys)
        wave = ShortWave(
            index=matches[0],
            arrival_time=self.time,
            required_work=active_count - 1,
            deadline_exclusive=self.time + SHORT_WINDOW,
        )
        self.current_wave = wave
        self.wave_records.append(wave)
        self.short_required_total += wave.required_work
        self._reset_wave_member_state()

    def _critic_global_features(self) -> np.ndarray:
        wave = self.current_wave
        required_arrived = self.short_required_total
        return np.asarray(
            [
                float(self.time) / float(HORIZON),
                np.log1p(len(self.active_keys)) / np.log(7.0),
                float(self.persistent_units) / float(PERSISTENT_TARGET),
                float(self.persistent_owner is not None),
                float(wave is not None),
                (
                    float(wave.steps_remaining(self.time)) / float(SHORT_WINDOW)
                    if wave is not None
                    else 0.0
                ),
                (
                    float(wave.required_work - wave.completed_work)
                    / float(max(wave.required_work, 1))
                    if wave is not None
                    else 0.0
                ),
                (
                    float(self.short_completed_total) / float(required_arrived)
                    if required_arrived > 0
                    else 0.0
                ),
            ],
            dtype=np.float32,
        )

    def _event_snapshot(self, *, frontier: tuple[int, ...] = ()) -> BoundarySnapshot:
        members = tuple(
            BoundaryMember.make(
                str(key),
                self.lifecycles[key].membership_epoch,
                self._observation_for(key),
                self._observation_for(key),
                obs_dim=OBSERVATION_DIM,
                critic_member_dim=OBSERVATION_DIM,
            )
            for key in self.active_keys
        )
        return BoundarySnapshot.make(
            self.time,
            members,
            self._critic_global_features(),
            critic_global_dim=8,
            frontier=tuple(str(key) for key in frontier),
        )

    def _prepare(self) -> None:
        if self._terminated:
            raise RuntimeError("the episode is already terminal")
        if self._prepared_time == self.time:
            return
        pre = self._event_snapshot()
        self._current_membership_change = self._apply_membership()
        self._open_wave_if_due()
        change = self._current_membership_change
        deltas = tuple(
            [
                MembershipDelta(JOIN, str(key), 0)
                for key in change.joined
            ]
            + [
                MembershipDelta(
                    TEMPORARY_LEAVE,
                    str(key),
                    self.lifecycles[key].membership_epoch,
                )
                for key in change.temporarily_left
            ]
            + [
                MembershipDelta(
                    REJOIN,
                    str(key),
                    self.lifecycles[key].membership_epoch - 1,
                )
                for key in change.rejoined
            ]
            + [
                MembershipDelta(
                    TERMINAL_LEAVE,
                    str(key),
                    self.lifecycles[key].membership_epoch,
                )
                for key in change.terminally_left
            ]
        )
        # Structural arrivals are immediate opportunities.  The event runtime
        # binds the remaining due frontier from its private opportunity clocks.
        structural_frontier = tuple(change.rejoined + change.joined)
        post = self._event_snapshot(frontier=structural_frontier)
        self._pending_event_transaction = MembershipTransaction(pre, deltas, post)
        self._prepared_time = self.time

    def event_transaction(self) -> MembershipTransaction:
        self._prepare()
        if self._pending_event_transaction is None:
            raise RuntimeError("event boundary was not prepared")
        return deepcopy(self._pending_event_transaction)

    def _observation_for(self, key: int) -> np.ndarray:
        state = self.lifecycles[key]
        if state.status != ACTIVE:
            raise RuntimeError("cannot observe an inactive lifecycle")
        wave = self.current_wave
        required_arrived = self.short_required_total
        completion_fraction = (
            float(self.short_completed_total) / float(required_arrived)
            if required_arrived > 0
            else 0.0
        )
        observation = np.zeros(OBSERVATION_DIM, dtype=np.float32)
        observation[0] = float(self.time) / float(HORIZON)
        observation[1] = np.log1p(len(self.active_keys)) / np.log(7.0)
        observation[2] = float(self.persistent_units) / float(PERSISTENT_TARGET)
        observation[3] = float(self.persistent_owner is not None)
        observation[4] = float(wave is not None)
        observation[5] = (
            float(wave.steps_remaining(self.time)) / float(SHORT_WINDOW)
            if wave is not None
            else 0.0
        )
        observation[6] = (
            float(wave.required_work - wave.completed_work)
            / float(max(wave.required_work, 1))
            if wave is not None
            else 0.0
        )
        observation[7] = completion_fraction
        observation[8] = float(self.persistent_owner == key)
        observation[9] = float(state.short_streak) / float(SHORT_STREAK_TARGET)
        observation[10] = float(state.contributed_current_wave)
        observation[11] = float(state.active_steps) / float(HORIZON)
        observation[12 + int(state.previous_action)] = 1.0
        return observation

    def observe(self) -> DynamicRosterView:
        self._prepare()
        keys = self.active_keys
        observations = np.stack(
            [self._observation_for(key) for key in keys], axis=0
        ).astype(np.float32)
        self.observation_shapes_valid &= observations.shape == (
            len(keys),
            OBSERVATION_DIM,
        )
        wave = self.current_wave
        return DynamicRosterView(
            time=self.time,
            active_keys=keys,
            observations=observations,
            membership_change=self._current_membership_change,
            wave_active=wave is not None,
            wave_required=0 if wave is None else int(wave.required_work),
            wave_completed=0 if wave is None else int(wave.completed_work),
        )

    def _update_persistent_duty(self, actions: Mapping[int, int]) -> None:
        owner = self.persistent_owner
        owner_continues = (
            owner is not None
            and self.lifecycles[owner].status == ACTIVE
            and int(actions[owner]) == PERSIST
        )
        if owner_continues:
            self.persistent_units = min(
                PERSISTENT_TARGET, self.persistent_units + 1
            )
            return

        candidates = tuple(
            key for key in self.active_keys if int(actions[key]) == PERSIST
        )
        self.persistent_owner = (
            self.preferred_owner(candidates) if candidates else None
        )

    def _update_short_duty(self, actions: Mapping[int, int]) -> None:
        wave = self.current_wave
        if wave is None:
            for key in self.active_keys:
                self.lifecycles[key].short_streak = 0
            return

        for key in self.active_keys:
            state = self.lifecycles[key]
            if state.contributed_current_wave:
                continue
            if int(actions[key]) == SHORT:
                state.short_streak = min(
                    SHORT_STREAK_TARGET, state.short_streak + 1
                )
            else:
                state.short_streak = 0
            if state.short_streak == SHORT_STREAK_TARGET:
                state.contributed_current_wave = True
                if wave.completed_work < wave.required_work:
                    wave.completed_work += 1
                    self.short_completed_total += 1

    def step(
        self, actions: Mapping[int, int]
    ) -> tuple[float, bool, dict[str, Any]]:
        view = self.observe()
        expected = set(view.active_keys)
        provided = {int(key) for key in actions}
        if provided != expected:
            raise ValueError(
                f"action keys {sorted(provided)} do not match active set "
                f"{sorted(expected)}"
            )
        normalized = {int(key): int(value) for key, value in actions.items()}
        if any(value not in (IDLE, PERSIST, SHORT) for value in normalized.values()):
            raise ValueError("all primitive actions must lie in {IDLE,PERSIST,SHORT}")

        self.roster_sizes.append(len(view.active_keys))
        self._update_persistent_duty(normalized)
        self._update_short_duty(normalized)

        for key in view.active_keys:
            state = self.lifecycles[key]
            state.previous_action = normalized[key]
            state.active_steps += 1

        if (
            self.current_wave is not None
            and self.time + 1 >= self.current_wave.deadline_exclusive
        ):
            self.current_wave = None
            self._reset_wave_member_state()

        terminal = self.time == HORIZON - 1
        persistent_score = min(
            float(self.persistent_units) / float(PERSISTENT_TARGET), 1.0
        )
        short_score = (
            float(self.short_completed_total) / float(self.short_required_total)
            if self.short_required_total > 0
            else 0.0
        )
        utility = 0.5 * (persistent_score + short_score)
        reward = utility if terminal else 0.0
        self.reward_trace.append(float(reward))

        info = {
            "persistent_score": persistent_score,
            "short_score": short_score,
            "utility": utility,
            "persistent_units": self.persistent_units,
            "short_completed_total": self.short_completed_total,
            "short_required_total": self.short_required_total,
        }
        self.time += 1
        self._prepared_time = None
        self._pending_event_transaction = None
        if terminal:
            self._terminated = True
        return float(reward), terminal, info

    def snapshot_state(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "ledger": deepcopy(self.ledger),
            "lifecycles": deepcopy(self.lifecycles),
            "time": int(self.time),
            "persistent_owner": self.persistent_owner,
            "persistent_units": int(self.persistent_units),
            "current_wave": deepcopy(self.current_wave),
            "wave_records": deepcopy(self.wave_records),
            "short_required_total": int(self.short_required_total),
            "short_completed_total": int(self.short_completed_total),
            "roster_sizes": list(self.roster_sizes),
            "reward_trace": list(self.reward_trace),
            "observation_shapes_valid": bool(self.observation_shapes_valid),
            "prepared_time": self._prepared_time,
            "current_membership_change": deepcopy(self._current_membership_change),
            "pending_event_transaction": deepcopy(self._pending_event_transaction),
            "terminated": bool(self._terminated),
        }

    @classmethod
    def from_snapshot_state(cls, state: Mapping[str, Any]) -> "GenericShortDynamicRosterEnv":
        required = {
            "schema_version", "ledger", "lifecycles", "time",
            "persistent_owner", "persistent_units", "current_wave",
            "wave_records", "short_required_total", "short_completed_total",
            "roster_sizes", "reward_trace", "observation_shapes_valid",
            "prepared_time", "current_membership_change",
            "pending_event_transaction", "terminated",
        }
        value = dict(state)
        if set(value) != required or int(value["schema_version"]) != 1:
            raise ValueError("dynamic-roster environment snapshot schema mismatch")
        env = cls(deepcopy(value["ledger"]))
        env.lifecycles = deepcopy(value["lifecycles"])
        env.time = int(value["time"])
        env.persistent_owner = value["persistent_owner"]
        env.persistent_units = int(value["persistent_units"])
        env.current_wave = deepcopy(value["current_wave"])
        env.wave_records = deepcopy(value["wave_records"])
        env.short_required_total = int(value["short_required_total"])
        env.short_completed_total = int(value["short_completed_total"])
        env.roster_sizes = list(value["roster_sizes"])
        env.reward_trace = list(value["reward_trace"])
        env.observation_shapes_valid = bool(value["observation_shapes_valid"])
        env._prepared_time = value["prepared_time"]
        env._current_membership_change = deepcopy(value["current_membership_change"])
        env._pending_event_transaction = deepcopy(value["pending_event_transaction"])
        env._terminated = bool(value["terminated"])
        return env

    def outcome(self) -> EpisodeOutcome:
        if not self._terminated or self.time != HORIZON:
            raise RuntimeError("outcome is available only after the terminal step")
        if self.short_required_total != EXPECTED_SHORT_REQUIREMENT:
            raise RuntimeError(
                "dynamic roster produced the wrong total short requirement: "
                f"{self.short_required_total}"
            )
        persistent_score = min(
            float(self.persistent_units) / float(PERSISTENT_TARGET), 1.0
        )
        short_score = float(self.short_completed_total) / float(
            self.short_required_total
        )
        utility = 0.5 * (persistent_score + short_score)
        return EpisodeOutcome(
            persistent_score=persistent_score,
            short_score=short_score,
            utility=utility,
            terminal_reward=float(self.reward_trace[-1]),
            short_required_total=self.short_required_total,
            short_completed_total=self.short_completed_total,
            roster_sizes=tuple(self.roster_sizes),
            reward_trace=tuple(self.reward_trace),
            observation_shapes_valid=bool(self.observation_shapes_valid),
        )


@dataclass(frozen=True)
class EventEnvironmentStep:
    reward: float
    terminated: bool
    truncated: bool
    info: dict[str, Any]
    next_transaction: MembershipTransaction | None


class _DiscreteActionSpace:
    def __init__(self, n: int) -> None:
        self.n = int(n)


class DynamicRosterEventEnv:
    """Snapshot-capable collector adapter for the exact generic-SHORT testbed."""

    obs_dim = OBSERVATION_DIM
    state_dim = 8
    action_dim = ACTION_COUNT
    n_uavs = MAX_LIFECYCLES
    action_space = _DiscreteActionSpace(ACTION_COUNT)

    def __init__(self, *, task_master_seed: int = TRAIN_LEDGER_SEED) -> None:
        self.task_master_seed = int(task_master_seed)
        self.episode_id: int | None = None
        self.environment: GenericShortDynamicRosterEnv | None = None

    def event_runtime_snapshot_capability(self) -> dict[str, Any]:
        return {"name": SNAPSHOT_CAPABILITY_NAME, "version": SNAPSHOT_CAPABILITY_VERSION}

    def reset_event_runtime(self, episode_id: int) -> MembershipTransaction:
        self.episode_id = int(episode_id)
        self.environment = GenericShortDynamicRosterEnv(
            make_dynamic_roster_ledger(
                self.episode_id,
                master_seed=self.task_master_seed,
            )
        )
        return self.environment.event_transaction()

    def step_event_runtime(self, actions: Mapping[str, int]) -> EventEnvironmentStep:
        if self.environment is None:
            raise RuntimeError("event environment must be reset before stepping")
        normalized = {int(key): int(value) for key, value in actions.items()}
        reward, terminal, info = self.environment.step(normalized)
        next_transaction = (
            None if terminal else self.environment.event_transaction()
        )
        event_info = dict(info)
        event_info.update(
            {
                "episode_id": int(self.episode_id),
                "physical_time": int(self.environment.time),
                "intrinsic_reward": 0.0,
                "intrinsic_reward_applied_count": 0,
            }
        )
        return EventEnvironmentStep(
            reward=float(reward),
            terminated=bool(terminal),
            truncated=False,
            info=event_info,
            next_transaction=next_transaction,
        )

    def snapshot_event_runtime(self) -> dict[str, Any]:
        if self.environment is None or self.episode_id is None:
            raise RuntimeError("cannot snapshot an uninitialized event environment")
        transaction = deepcopy(self.environment._pending_event_transaction)
        return {
            "snapshot_capability_name": SNAPSHOT_CAPABILITY_NAME,
            "snapshot_capability_version": SNAPSHOT_CAPABILITY_VERSION,
            "active_presentation": (
                []
                if transaction is None
                else list(transaction.post_membership_pre_policy_snapshot.keys)
            ),
            "pending_membership_transaction": transaction,
            "pending_command_response_state": "boundary_ready",
            "worker_environment_snapshot": self.environment.snapshot_state(),
            "environment_rng_state": {
                "task_master_seed": int(self.task_master_seed),
                "episode_id": int(self.episode_id),
                "ledger_is_pre_sampled": True,
            },
        }

    def restore_event_runtime(self, snapshot: Mapping[str, Any]) -> None:
        required = {
            "snapshot_capability_name", "snapshot_capability_version",
            "active_presentation", "pending_membership_transaction",
            "pending_command_response_state", "worker_environment_snapshot",
            "environment_rng_state",
        }
        value = dict(snapshot)
        if set(value) != required:
            raise ValueError("event environment snapshot field mismatch")
        if value["snapshot_capability_name"] != SNAPSHOT_CAPABILITY_NAME or int(
            value["snapshot_capability_version"]
        ) != SNAPSHOT_CAPABILITY_VERSION:
            raise ValueError("event environment snapshot capability mismatch")
        rng_state = dict(value["environment_rng_state"])
        if set(rng_state) != {"task_master_seed", "episode_id", "ledger_is_pre_sampled"}:
            raise ValueError("event environment RNG state mismatch")
        if not bool(rng_state["ledger_is_pre_sampled"]):
            raise ValueError("dynamic-roster randomness must be fully ledgered")
        self.task_master_seed = int(rng_state["task_master_seed"])
        self.episode_id = int(rng_state["episode_id"])
        self.environment = GenericShortDynamicRosterEnv.from_snapshot_state(
            value["worker_environment_snapshot"]
        )
        expected = self.environment._pending_event_transaction
        actual = value["pending_membership_transaction"]
        if (actual is None) != (expected is None):
            raise ValueError("pending membership transaction does not round-trip exactly")
        if actual is not None and expected is not None:
            for left, right in (
                (actual.pre_membership_boundary_snapshot, expected.pre_membership_boundary_snapshot),
                (actual.post_membership_pre_policy_snapshot, expected.post_membership_pre_policy_snapshot),
            ):
                if (
                    left.physical_time != right.physical_time
                    or left.keys != right.keys
                    or left.frontier != right.frontier
                    or not np.array_equal(
                        left.critic_global_features, right.critic_global_features
                    )
                    or any(
                        l.membership_epoch != r.membership_epoch
                        or not np.array_equal(l.observation, r.observation)
                        or not np.array_equal(
                            l.critic_member_features, r.critic_member_features
                        )
                        for l, r in zip(left.members, right.members)
                    )
                ):
                    raise ValueError("pending membership transaction does not round-trip exactly")
            if actual.atomic_membership_delta != expected.atomic_membership_delta:
                raise ValueError("pending membership transaction does not round-trip exactly")
        expected_presentation = [] if expected is None else list(
            expected.post_membership_pre_policy_snapshot.keys
        )
        if list(value["active_presentation"]) != expected_presentation:
            raise ValueError("active presentation does not match restored environment")

    def close(self) -> None:
        return None


def constructive_actions(
    environment: GenericShortDynamicRosterEnv,
    view: DynamicRosterView,
) -> dict[int, int]:
    """Routing-only constructive controller registered for Stage A."""

    owner = environment.persistent_owner
    if owner not in view.active_keys:
        owner = environment.preferred_owner(view.active_keys)
    actions: dict[int, int] = {}
    for key in view.active_keys:
        state = environment.lifecycles[key]
        if key == owner:
            actions[key] = PERSIST
        elif view.wave_active and not state.contributed_current_wave:
            actions[key] = SHORT
        else:
            actions[key] = IDLE
    return actions


def make_uniform_action_table(episode_id: int) -> np.ndarray:
    rng = _rng(ACTION_SAMPLING_SEED, episode_id, 0)
    return rng.integers(
        0,
        ACTION_COUNT,
        size=(HORIZON, MAX_LIFECYCLES),
        dtype=np.int64,
    )


def run_stage_a_episode(
    ledger: DynamicRosterLedger,
    *,
    controller: str,
) -> EpisodeOutcome:
    environment = GenericShortDynamicRosterEnv(ledger)
    uniform_table = (
        make_uniform_action_table(ledger.episode_id)
        if controller == "uniform_random"
        else None
    )
    if controller not in {"constructive", "uniform_random"}:
        raise ValueError(f"unknown Stage A controller: {controller}")

    while environment.time < HORIZON:
        view = environment.observe()
        if controller == "constructive":
            actions = constructive_actions(environment, view)
        else:
            assert uniform_table is not None
            actions = {
                key: int(uniform_table[view.time, key]) for key in view.active_keys
            }
        _reward, _terminal, _info = environment.step(actions)
    return environment.outcome()


def _ledger_equal(left: DynamicRosterLedger, right: DynamicRosterLedger) -> bool:
    return bool(
        left.temporary_leave == right.temporary_leave
        and left.terminal_leave == right.terminal_leave
        and left.wave_arrivals == right.wave_arrivals
        and np.array_equal(left.owner_priorities, right.owner_priorities)
        and np.array_equal(
            left.presentation_priorities, right.presentation_priorities
        )
        and np.array_equal(
            left.direct_frontier_priorities, right.direct_frontier_priorities
        )
    )


def _roster_schedule_valid(roster_sizes: tuple[int, ...]) -> bool:
    return bool(
        len(roster_sizes) == HORIZON
        and all(value == 4 for value in roster_sizes[0:20])
        and all(value == 2 for value in roster_sizes[20:40])
        and all(value == 6 for value in roster_sizes[40:60])
        and all(value == 4 for value in roster_sizes[60:80])
    )


def evaluate_stage_a(episodes: int = 256) -> dict[str, Any]:
    """Evaluate the exact no-learning carrier and return one result payload."""

    episode_count = int(episodes)
    if episode_count <= 0:
        raise ValueError("episodes must be positive")

    constructive: list[EpisodeOutcome] = []
    uniform_random: list[EpisodeOutcome] = []
    ledger_replay_equal = True
    for episode_id in range(episode_count):
        ledger = make_dynamic_roster_ledger(episode_id)
        ledger_replay_equal &= _ledger_equal(
            ledger, make_dynamic_roster_ledger(episode_id)
        )
        constructive.append(
            run_stage_a_episode(ledger, controller="constructive")
        )
        uniform_random.append(
            run_stage_a_episode(ledger, controller="uniform_random")
        )

    all_outcomes = constructive + uniform_random
    m0 = {
        "episode_count_exact": episode_count == 256,
        "ledger_replay_equal": bool(ledger_replay_equal),
        "roster_schedule_exact": all(
            _roster_schedule_valid(outcome.roster_sizes)
            for outcome in all_outcomes
        ),
        "short_requirement_exact": all(
            outcome.short_required_total == EXPECTED_SHORT_REQUIREMENT
            for outcome in all_outcomes
        ),
        "terminal_reward_only": all(
            len(outcome.reward_trace) == HORIZON
            and all(reward == 0.0 for reward in outcome.reward_trace[:-1])
            and outcome.reward_trace[-1] == outcome.utility
            for outcome in all_outcomes
        ),
        "observation_shape_exact": all(
            outcome.observation_shapes_valid for outcome in all_outcomes
        ),
        "finite_metrics": all(
            np.isfinite(
                [
                    outcome.persistent_score,
                    outcome.short_score,
                    outcome.utility,
                ]
            ).all()
            for outcome in all_outcomes
        ),
    }
    implementation_valid = all(bool(value) for value in m0.values())

    constructive_p = float(
        np.mean([outcome.persistent_score for outcome in constructive])
    )
    constructive_s = float(
        np.mean([outcome.short_score for outcome in constructive])
    )
    constructive_u = float(
        np.mean([outcome.utility for outcome in constructive])
    )
    random_u_values = np.asarray(
        [outcome.utility for outcome in uniform_random], dtype=np.float64
    )
    random_positive = float(np.mean(random_u_values > 0.0))
    random_mean = float(np.mean(random_u_values))

    carrier_pass = bool(
        constructive_p >= 0.95
        and constructive_s >= 0.95
        and constructive_u >= 0.95
        and random_positive >= 0.20
        and random_mean < 0.55
    )
    if not implementation_valid:
        status = "INVALID_IMPLEMENTATION"
        next_action = "repair only the concrete Stage A implementation defect"
    elif not carrier_pass:
        status = "RETIRE_TESTBED_CARRIER"
        next_action = "retire this exact testbed without a learning run"
    else:
        status = "PASS_STAGE_A_CARRIER"
        next_action = "request separate authorization for the direct primitive-AR instrument"

    return {
        "schema_version": 1,
        "stage": "stage_a_no_learning_carrier",
        "status": status,
        "implementation_valid": implementation_valid,
        "carrier_pass": carrier_pass,
        "episodes_per_controller": episode_count,
        "m0": m0,
        "constructive": {
            "persistent_score_mean": constructive_p,
            "short_score_mean": constructive_s,
            "utility_mean": constructive_u,
        },
        "uniform_random": {
            "positive_utility_fraction": random_positive,
            "utility_mean": random_mean,
        },
        "thresholds": {
            "constructive_persistent_min": 0.95,
            "constructive_short_min": 0.95,
            "constructive_utility_min": 0.95,
            "uniform_positive_utility_fraction_min": 0.20,
            "uniform_utility_mean_max_exclusive": 0.55,
        },
        "environment_steps_per_controller": episode_count * HORIZON,
        "optimizer_steps": 0,
        "intrinsic_reward_reads": 0,
        "next_action": next_action,
    }


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value
