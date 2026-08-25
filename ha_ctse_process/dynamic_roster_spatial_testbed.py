"""Task-neutral spatial carrier for the Iteration-5 process-semantics test.

The actor sees the sparse task state it needs for ordinary control, while the
semantic learner receives a separate route-only scalar process view containing
only the focal member's normalized position.  Lifecycle keys never enter a
network.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from ha_ctse_process.dynamic_roster_testbed import (
    ACTIVE,
    EVALUATION_LEDGER_SEED,
    EXPECTED_SHORT_REQUIREMENT,
    HORIZON,
    MAX_LIFECYCLES,
    MembershipChange,
    OBSERVATION_DIM,
    PERSISTENT_TARGET,
    SHORT_STREAK_TARGET,
    DynamicRosterEventEnv,
    DynamicRosterLedger,
    DynamicRosterView,
    EpisodeOutcome,
    GenericShortDynamicRosterEnv,
    make_dynamic_roster_ledger,
    _rng,
)
from ha_ctse_process.variable_roster_event import (
    SNAPSHOT_CAPABILITY_NAME,
    SNAPSHOT_CAPABILITY_VERSION,
)


LEFT = 0
STAY = 1
RIGHT = 2
ACTION_COUNT = 3


@dataclass(frozen=True)
class SpatialDynamicRosterLedger(DynamicRosterLedger):
    master_seed: int
    wave_targets: tuple[int, ...]

    def validate(self) -> None:
        super().validate()
        if len(self.wave_targets) != 8 or any(
            int(target) not in (1, 2) for target in self.wave_targets
        ):
            raise ValueError("spatial ledger requires eight targets in {1,2}")


def make_spatial_dynamic_roster_ledger(
    episode_id: int,
    *,
    master_seed: int = EVALUATION_LEDGER_SEED,
) -> SpatialDynamicRosterLedger:
    base = make_dynamic_roster_ledger(episode_id, master_seed=master_seed)
    target_rng = _rng(master_seed, episode_id, 6)
    ledger = SpatialDynamicRosterLedger(
        episode_id=base.episode_id,
        temporary_leave=base.temporary_leave,
        terminal_leave=base.terminal_leave,
        wave_arrivals=base.wave_arrivals,
        owner_priorities=base.owner_priorities,
        presentation_priorities=base.presentation_priorities,
        direct_frontier_priorities=base.direct_frontier_priorities,
        master_seed=int(master_seed),
        wave_targets=tuple(
            int(value) for value in target_rng.integers(1, 3, size=8)
        ),
    )
    ledger.validate()
    return ledger


class SpatialDynamicRosterEnv(GenericShortDynamicRosterEnv):
    """Exact 1-D spatial carrier with the registered dynamic membership."""

    ledger: SpatialDynamicRosterLedger

    def __init__(self, ledger: SpatialDynamicRosterLedger):
        super().__init__(ledger)
        self.positions: dict[int, int] = {
            0: 0,
            1: 1,
            2: 1,
            3: 1,
            4: 1,
            5: 1,
        }
        self.current_wave_target: int | None = None

    def _apply_membership(self) -> MembershipChange:
        change = super()._apply_membership()
        for key in change.joined:
            self.positions[int(key)] = 0 if int(key) == 0 else 1
            self.lifecycles[int(key)].previous_action = STAY
        return change

    def _open_wave_if_due(self) -> None:
        previous_count = len(self.wave_records)
        super()._open_wave_if_due()
        if len(self.wave_records) > previous_count:
            assert self.current_wave is not None
            self.current_wave_target = int(
                self.ledger.wave_targets[self.current_wave.index]
            )

    def _critic_global_features(self) -> np.ndarray:
        values = super()._critic_global_features()
        values[7] = (
            0.0
            if self.current_wave_target is None
            else float(self.current_wave_target) / 2.0
        )
        return values

    def _observation_for(self, key: int) -> np.ndarray:
        observation = super()._observation_for(key)
        observation[7] = (
            0.0
            if self.current_wave_target is None
            else float(self.current_wave_target) / 2.0
        )
        observation[11] = float(self.positions[int(key)]) / 2.0
        return observation

    def process_state_mapping(
        self, keys: Sequence[int | str] | None = None
    ) -> dict[str, float]:
        selected = self.active_keys if keys is None else tuple(int(key) for key in keys)
        return {
            str(key): float(self.positions[int(key)]) / 2.0 for key in selected
        }

    def _move(self, key: int, action: int) -> None:
        delta = -1 if int(action) == LEFT else 1 if int(action) == RIGHT else 0
        self.positions[int(key)] = int(
            np.clip(self.positions[int(key)] + delta, 0, 2)
        )

    def _update_persistent_duty(self, _actions: Mapping[int, int]) -> None:
        owner = self.persistent_owner
        owner_is_active = (
            owner is not None
            and self.lifecycles[int(owner)].status == ACTIVE
        )
        if not owner_is_active:
            candidates = tuple(
                key for key in self.active_keys if self.positions[int(key)] == 0
            )
            self.persistent_owner = (
                self.preferred_owner(candidates) if candidates else None
            )
        if (
            self.persistent_owner is not None
            and self.positions[int(self.persistent_owner)] == 0
        ):
            self.persistent_units = min(
                PERSISTENT_TARGET, self.persistent_units + 1
            )

    def _update_short_duty(self, _actions: Mapping[int, int]) -> None:
        wave = self.current_wave
        target = self.current_wave_target
        if wave is None or target is None:
            for key in self.active_keys:
                self.lifecycles[key].short_streak = 0
            return
        for key in self.active_keys:
            state = self.lifecycles[key]
            if state.contributed_current_wave:
                continue
            if self.positions[key] == target:
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
        normalized = {int(key): int(value) for key, value in actions.items()}
        if set(normalized) != expected:
            raise ValueError("spatial action keys do not match the active set")
        if any(value not in (LEFT, STAY, RIGHT) for value in normalized.values()):
            raise ValueError("spatial actions must be LEFT, STAY or RIGHT")

        self.roster_sizes.append(len(view.active_keys))
        for key in view.active_keys:
            self._move(key, normalized[key])
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
            self.current_wave_target = None
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
            "process_state": self.process_state_mapping(view.active_keys),
        }
        self.time += 1
        self._prepared_time = None
        self._pending_event_transaction = None
        if terminal:
            self._terminated = True
        return float(reward), terminal, info

    def snapshot_state(self) -> dict[str, Any]:
        value = super().snapshot_state()
        value["schema_version"] = 2
        value["positions"] = deepcopy(self.positions)
        value["current_wave_target"] = self.current_wave_target
        return value

    @classmethod
    def from_snapshot_state(
        cls, state: Mapping[str, Any]
    ) -> "SpatialDynamicRosterEnv":
        value = dict(state)
        if int(value.get("schema_version", -1)) != 2:
            raise ValueError("spatial dynamic-roster snapshot schema mismatch")
        positions = dict(deepcopy(value.pop("positions")))
        wave_target = value.pop("current_wave_target")
        value["schema_version"] = 1
        generic = GenericShortDynamicRosterEnv.from_snapshot_state(value)
        if not isinstance(generic.ledger, SpatialDynamicRosterLedger):
            raise ValueError("spatial snapshot requires a spatial task ledger")
        normalized_positions = {
            int(key): int(position) for key, position in positions.items()
        }
        if (
            len(positions) != MAX_LIFECYCLES
            or set(normalized_positions) != set(range(MAX_LIFECYCLES))
            or any(position not in (0, 1, 2) for position in normalized_positions.values())
        ):
            raise ValueError("spatial snapshot contains an invalid position mapping")
        if (generic.current_wave is None) != (wave_target is None):
            raise ValueError("spatial snapshot wave target is inconsistent")
        if wave_target is not None and int(wave_target) not in (1, 2):
            raise ValueError("spatial snapshot wave target must lie in {1,2}")
        env = cls(deepcopy(generic.ledger))
        for name in (
            "lifecycles",
            "time",
            "persistent_owner",
            "persistent_units",
            "current_wave",
            "wave_records",
            "short_required_total",
            "short_completed_total",
            "roster_sizes",
            "reward_trace",
            "observation_shapes_valid",
            "_prepared_time",
            "_current_membership_change",
            "_pending_event_transaction",
            "_terminated",
        ):
            setattr(env, name, deepcopy(getattr(generic, name)))
        env.positions = normalized_positions
        env.current_wave_target = None if wave_target is None else int(wave_target)
        return env

    def outcome(self) -> EpisodeOutcome:
        outcome = super().outcome()
        if outcome.short_required_total != EXPECTED_SHORT_REQUIREMENT:
            raise RuntimeError("spatial carrier short requirement mismatch")
        return outcome


class SpatialDynamicRosterEventEnv(DynamicRosterEventEnv):
    obs_dim = OBSERVATION_DIM
    state_dim = 8
    action_dim = ACTION_COUNT
    n_uavs = MAX_LIFECYCLES

    environment: SpatialDynamicRosterEnv | None

    def reset_event_runtime(self, episode_id: int):
        self.episode_id = int(episode_id)
        self.environment = SpatialDynamicRosterEnv(
            make_spatial_dynamic_roster_ledger(
                self.episode_id, master_seed=self.task_master_seed
            )
        )
        return self.environment.event_transaction()

    def process_state_mapping(
        self, keys: Sequence[int | str] | None = None
    ) -> dict[str, float]:
        if self.environment is None:
            raise RuntimeError("spatial environment must be reset before process read")
        return self.environment.process_state_mapping(keys)

    def restore_event_runtime(self, snapshot: Mapping[str, Any]) -> None:
        value = dict(snapshot)
        required = {
            "snapshot_capability_name",
            "snapshot_capability_version",
            "active_presentation",
            "pending_membership_transaction",
            "pending_command_response_state",
            "worker_environment_snapshot",
            "environment_rng_state",
        }
        if set(value) != required:
            raise ValueError("spatial event snapshot field mismatch")
        if value["snapshot_capability_name"] != SNAPSHOT_CAPABILITY_NAME or int(
            value["snapshot_capability_version"]
        ) != SNAPSHOT_CAPABILITY_VERSION:
            raise ValueError("spatial event snapshot capability mismatch")
        rng_state = dict(value["environment_rng_state"])
        if set(rng_state) != {"task_master_seed", "episode_id", "ledger_is_pre_sampled"}:
            raise ValueError("spatial event RNG state mismatch")
        if not bool(rng_state["ledger_is_pre_sampled"]):
            raise ValueError("spatial task randomness must be pre-sampled")
        if value["pending_command_response_state"] != "boundary_ready":
            raise ValueError("spatial event command-response state mismatch")
        worker = dict(value.get("worker_environment_snapshot", {}))
        if int(worker.get("schema_version", -1)) != 2:
            raise ValueError("spatial event snapshot schema mismatch")
        self.task_master_seed = int(rng_state["task_master_seed"])
        self.episode_id = int(rng_state["episode_id"])
        self.environment = SpatialDynamicRosterEnv.from_snapshot_state(worker)
        expected = self.environment._pending_event_transaction
        actual = value["pending_membership_transaction"]
        if (actual is None) != (expected is None):
            raise ValueError("spatial pending transaction mismatch")
        if actual is not None and expected is not None:
            for left, right in (
                (
                    actual.pre_membership_boundary_snapshot,
                    expected.pre_membership_boundary_snapshot,
                ),
                (
                    actual.post_membership_pre_policy_snapshot,
                    expected.post_membership_pre_policy_snapshot,
                ),
            ):
                if (
                    left.physical_time != right.physical_time
                    or left.keys != right.keys
                    or left.frontier != right.frontier
                    or not np.array_equal(
                        left.critic_global_features,
                        right.critic_global_features,
                    )
                    or any(
                        left_member.membership_epoch
                        != right_member.membership_epoch
                        or not np.array_equal(
                            left_member.observation,
                            right_member.observation,
                        )
                        or not np.array_equal(
                            left_member.critic_member_features,
                            right_member.critic_member_features,
                        )
                        for left_member, right_member in zip(
                            left.members, right.members
                        )
                    )
                ):
                    raise ValueError("spatial pending transaction mismatch")
            if actual.atomic_membership_delta != expected.atomic_membership_delta:
                raise ValueError("spatial pending transaction mismatch")
        expected_presentation = [] if expected is None else list(
            expected.post_membership_pre_policy_snapshot.keys
        )
        if list(value["active_presentation"]) != expected_presentation:
            raise ValueError("spatial active presentation mismatch")


def _step_towards(position: int, target: int) -> int:
    if int(position) < int(target):
        return RIGHT
    if int(position) > int(target):
        return LEFT
    return STAY


def constructive_spatial_actions(
    environment: SpatialDynamicRosterEnv,
    view: DynamicRosterView,
) -> dict[int, int]:
    """Routing-only positive controller; lifecycle keys never enter a model."""

    owner = environment.persistent_owner
    if owner not in view.active_keys:
        owner = environment.preferred_owner(view.active_keys)
    target = environment.current_wave_target
    actions: dict[int, int] = {}
    for key in view.active_keys:
        if key == owner:
            actions[key] = _step_towards(environment.positions[key], 0)
        elif target is not None and not environment.lifecycles[key].contributed_current_wave:
            actions[key] = _step_towards(environment.positions[key], target)
        else:
            actions[key] = STAY
    return actions


def make_spatial_environment(
    ledger: SpatialDynamicRosterLedger,
) -> SpatialDynamicRosterEnv:
    return SpatialDynamicRosterEnv(ledger)
