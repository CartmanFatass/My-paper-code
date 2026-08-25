"""Clean process-channel carrier for dynamic-roster access qualification.

The task, observation, reward, membership schedule and direct learner are the
accepted Generic-SHORT path.  This carrier adds only a separate lifecycle-owned
physical actuator trace.  The trace is audit-only: it is not part of actor or
critic inputs and it never changes reward or task dynamics.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from ha_ctse_process.dynamic_roster_testbed import (
    ACTION_COUNT,
    EVALUATION_LEDGER_SEED,
    HORIZON,
    IDLE,
    MAX_LIFECYCLES,
    OBSERVATION_DIM,
    PERSIST,
    SHORT,
    DynamicRosterEventEnv,
    DynamicRosterLedger,
    GenericShortDynamicRosterEnv,
    MembershipChange,
    constructive_actions,
    make_dynamic_roster_ledger,
)
from ha_ctse_process.variable_roster_event import (
    SNAPSHOT_CAPABILITY_NAME,
    SNAPSHOT_CAPABILITY_VERSION,
)


PROCESS_CHANNEL_FIELDS = ("actuator_position", "actuator_velocity")
PROCESS_DAMPING = 0.75
PROCESS_DRIVE = 0.25
PROCESS_STEP = 0.125
PROCESS_ACTION_FORCE = np.asarray((-1.0, 0.0, 1.0), dtype=np.float64)


@dataclass(frozen=True)
class CleanProcessDynamicRosterLedger(DynamicRosterLedger):
    """Independently named immutable carrier ledger."""

    master_seed: int
    carrier_schema: str = "clean_process_v1"

    def validate(self) -> None:
        super().validate()
        if self.carrier_schema != "clean_process_v1":
            raise ValueError("clean-process ledger schema mismatch")


def make_clean_process_dynamic_roster_ledger(
    episode_id: int,
    *,
    master_seed: int = EVALUATION_LEDGER_SEED,
) -> CleanProcessDynamicRosterLedger:
    base = make_dynamic_roster_ledger(episode_id, master_seed=master_seed)
    ledger = CleanProcessDynamicRosterLedger(
        episode_id=base.episode_id,
        temporary_leave=base.temporary_leave,
        terminal_leave=base.terminal_leave,
        wave_arrivals=base.wave_arrivals,
        owner_priorities=base.owner_priorities,
        presentation_priorities=base.presentation_priorities,
        direct_frontier_priorities=base.direct_frontier_priorities,
        master_seed=int(master_seed),
    )
    ledger.validate()
    return ledger


class CleanProcessDynamicRosterEnv(GenericShortDynamicRosterEnv):
    """Generic-SHORT with a separate deterministic physical process trace."""

    ledger: CleanProcessDynamicRosterLedger

    def __init__(self, ledger: CleanProcessDynamicRosterLedger):
        super().__init__(ledger)
        self.process_states = {
            key: np.zeros(2, dtype=np.float64) for key in range(MAX_LIFECYCLES)
        }

    def _apply_membership(self) -> MembershipChange:
        change = super()._apply_membership()
        for key in change.joined:
            self.process_states[int(key)] = np.zeros(2, dtype=np.float64)
        return change

    @staticmethod
    def process_channel_fields() -> tuple[str, str]:
        return PROCESS_CHANNEL_FIELDS

    def process_state_mapping(
        self, keys: Sequence[int | str] | None = None
    ) -> dict[str, np.ndarray]:
        selected = self.active_keys if keys is None else tuple(int(key) for key in keys)
        return {
            str(key): np.asarray(self.process_states[int(key)], dtype=np.float64).copy()
            for key in selected
        }

    def _advance_process(self, key: int, action: int) -> None:
        if int(action) < 0 or int(action) >= ACTION_COUNT:
            raise ValueError("clean-process action lies outside primitive support")
        position, velocity = self.process_states[int(key)]
        velocity = (
            PROCESS_DAMPING * float(velocity)
            + PROCESS_DRIVE * float(PROCESS_ACTION_FORCE[int(action)])
        )
        position = float(np.clip(position + PROCESS_STEP * velocity, -1.0, 1.0))
        self.process_states[int(key)] = np.asarray(
            (position, velocity), dtype=np.float64
        )

    def step(
        self, actions: Mapping[int, int]
    ) -> tuple[float, bool, dict[str, Any]]:
        view = self.observe()
        # Validate the complete primitive action before advancing either the
        # audit-only process channel or the task environment.  In particular,
        # a late invalid action must not leave earlier process rows advanced.
        normalized = {int(key): int(value) for key, value in actions.items()}
        if set(normalized) != set(view.active_keys):
            raise ValueError("clean-process action keys do not match active set")
        if any(
            value not in (IDLE, PERSIST, SHORT)
            for value in normalized.values()
        ):
            raise ValueError("all primitive actions must lie in {IDLE,PERSIST,SHORT}")
        for key in view.active_keys:
            self._advance_process(key, normalized[key])
        reward, terminal, info = super().step(normalized)
        info = dict(info)
        info["process_channel"] = {
            key: value.tolist()
            for key, value in self.process_state_mapping(view.active_keys).items()
        }
        return reward, terminal, info

    def snapshot_state(self) -> dict[str, Any]:
        value = super().snapshot_state()
        value["schema_version"] = 2
        value["clean_process_states"] = {
            int(key): np.asarray(state, dtype=np.float64).copy()
            for key, state in self.process_states.items()
        }
        return value

    @classmethod
    def from_snapshot_state(
        cls, state: Mapping[str, Any]
    ) -> "CleanProcessDynamicRosterEnv":
        value = dict(deepcopy(state))
        if int(value.get("schema_version", -1)) != 2:
            raise ValueError("clean-process snapshot schema mismatch")
        process_states = dict(value.pop("clean_process_states"))
        value["schema_version"] = 1
        generic = GenericShortDynamicRosterEnv.from_snapshot_state(value)
        if not isinstance(generic.ledger, CleanProcessDynamicRosterLedger):
            raise ValueError("clean-process snapshot requires its carrier ledger")
        normalized = {
            int(key): np.asarray(item, dtype=np.float64).copy()
            for key, item in process_states.items()
        }
        if set(normalized) != set(range(MAX_LIFECYCLES)) or any(
            state.shape != (2,) or not np.all(np.isfinite(state))
            for state in normalized.values()
        ):
            raise ValueError("clean-process snapshot state mapping is invalid")
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
        env.process_states = normalized
        return env


class CleanProcessDynamicRosterEventEnv(DynamicRosterEventEnv):
    """Typed event adapter retaining clean process state across snapshots."""

    obs_dim = OBSERVATION_DIM
    state_dim = 8
    action_dim = ACTION_COUNT
    n_uavs = MAX_LIFECYCLES

    environment: CleanProcessDynamicRosterEnv | None

    def reset_event_runtime(self, episode_id: int):
        self.episode_id = int(episode_id)
        self.environment = CleanProcessDynamicRosterEnv(
            make_clean_process_dynamic_roster_ledger(
                self.episode_id, master_seed=self.task_master_seed
            )
        )
        return self.environment.event_transaction()

    def process_state_mapping(
        self, keys: Sequence[int | str] | None = None
    ) -> dict[str, np.ndarray]:
        if self.environment is None:
            raise RuntimeError("clean-process runtime must be reset before read")
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
            raise ValueError("clean-process event snapshot field mismatch")
        if value["snapshot_capability_name"] != SNAPSHOT_CAPABILITY_NAME or int(
            value["snapshot_capability_version"]
        ) != SNAPSHOT_CAPABILITY_VERSION:
            raise ValueError("clean-process event snapshot capability mismatch")
        rng_state = dict(value["environment_rng_state"])
        if set(rng_state) != {
            "task_master_seed",
            "episode_id",
            "ledger_is_pre_sampled",
        } or not bool(rng_state["ledger_is_pre_sampled"]):
            raise ValueError("clean-process event RNG state mismatch")
        if value["pending_command_response_state"] != "boundary_ready":
            raise ValueError("clean-process command-response state mismatch")
        worker = dict(value["worker_environment_snapshot"])
        self.task_master_seed = int(rng_state["task_master_seed"])
        self.episode_id = int(rng_state["episode_id"])
        self.environment = CleanProcessDynamicRosterEnv.from_snapshot_state(worker)
        expected = self.environment._pending_event_transaction
        actual = value["pending_membership_transaction"]
        if (actual is None) != (expected is None):
            raise ValueError("clean-process pending transaction mismatch")
        if actual is not None and expected is not None:
            if (
                actual.atomic_membership_delta != expected.atomic_membership_delta
                or actual.pre_membership_boundary_snapshot.keys
                != expected.pre_membership_boundary_snapshot.keys
                or actual.post_membership_pre_policy_snapshot.keys
                != expected.post_membership_pre_policy_snapshot.keys
            ):
                raise ValueError("clean-process pending transaction mismatch")
        expected_presentation = [] if expected is None else list(
            expected.post_membership_pre_policy_snapshot.keys
        )
        if list(value["active_presentation"]) != expected_presentation:
            raise ValueError("clean-process active presentation mismatch")


def make_clean_process_environment(
    ledger: CleanProcessDynamicRosterLedger,
) -> CleanProcessDynamicRosterEnv:
    return CleanProcessDynamicRosterEnv(ledger)


def audit_clean_process_contract() -> dict[str, bool]:
    """One deterministic ownership, exclusion and persistence audit."""

    ledger = make_clean_process_dynamic_roster_ledger(3, master_seed=12_345)
    clean = CleanProcessDynamicRosterEnv(ledger)
    generic = GenericShortDynamicRosterEnv(deepcopy(ledger))
    absence_frozen = True
    rejoin_resumed = True
    new_join_zero = True
    observation_equal = True
    reward_equal = True
    frozen: dict[int, np.ndarray] = {}

    for time in range(HORIZON):
        clean_view = clean.observe()
        generic_view = generic.observe()
        observation_equal &= (
            clean_view.active_keys == generic_view.active_keys
            and np.array_equal(clean_view.observations, generic_view.observations)
        )
        if time == 20:
            frozen = {
                int(key): clean.process_states[int(key)].copy()
                for key in ledger.temporary_leave
            }
        if 20 <= time < 40 and frozen:
            absence_frozen &= all(
                np.array_equal(clean.process_states[key], value)
                for key, value in frozen.items()
            )
        if time == 40:
            rejoin_resumed &= all(
                np.array_equal(clean.process_states[key], value)
                for key, value in frozen.items()
            )
            new_join_zero &= all(
                np.array_equal(clean.process_states[key], np.zeros(2))
                for key in (4, 5)
            )
        actions = constructive_actions(clean, clean_view)
        clean_reward, _, _ = clean.step(actions)
        generic_reward, _, _ = generic.step(actions)
        reward_equal &= clean_reward == generic_reward

        if time == 24:
            snapshot = clean.snapshot_state()
            restored = CleanProcessDynamicRosterEnv.from_snapshot_state(snapshot)
            if restored.snapshot_state().keys() != snapshot.keys() or any(
                not np.array_equal(
                    restored.process_states[key], clean.process_states[key]
                )
                for key in range(MAX_LIFECYCLES)
            ):
                return {
                    "snapshot_round_trip": False,
                    "observation_actor_exclusion": observation_equal,
                    "reward_exclusion": reward_equal,
                    "temporary_absence_process_frozen": absence_frozen,
                    "rejoin_process_resumed": rejoin_resumed,
                    "genuine_join_process_zero": new_join_zero,
                    "task_neutral_schema": True,
                }

    forbidden = {
        "target",
        "reward",
        "success",
        "contact",
        "phase",
        "identity",
        "role",
        "progress",
        "routing",
    }
    schema_valid = all(
        not any(token in field for token in forbidden)
        for field in PROCESS_CHANNEL_FIELDS
    )
    return {
        "snapshot_round_trip": True,
        "observation_actor_exclusion": bool(observation_equal),
        "reward_exclusion": bool(reward_equal),
        "temporary_absence_process_frozen": bool(absence_frozen),
        "rejoin_process_resumed": bool(rejoin_resumed),
        "genuine_join_process_zero": bool(new_join_zero),
        "task_neutral_schema": bool(schema_valid),
    }
