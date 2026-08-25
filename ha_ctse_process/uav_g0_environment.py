from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence

import numpy as np

from config_1 import Config
from envs.pettingzoo.relay.energy_aware import UAVEnergyAwareRelayEnv
from ha_ctse_process import uav_g0_controllers as controllers, uav_g0_oracle_evidence as oracle_evidence
from ha_ctse_process.uav_episode_schema import ACTION_DIM, GROUND_USERS, PHYSICAL_HORIZON, PHYSICAL_UAVS, Cell, G0RealizationError, LifecycleBoundaryEvent, _readonly_array
from ha_ctse_process.uav_g0_geometry import FIXED_ALTITUDE_M, GROUND_BASE_STATIONS, G0EpisodeSource, HOTSPOT_COUNT, TARGET_LABELS, TargetLabel, USER_ALTITUDE_M, channel_seed_word, sha256_json
@dataclass(frozen=True)
class G0Transition:
    physical_step: int
    delivered_user_rates_mbps: np.ndarray
    executed_action_mask: np.ndarray
    raw_actions: np.ndarray
    positions_before: np.ndarray
    positions_after: np.ndarray
    actual_velocities: np.ndarray
    backhaul_guard_blocked_actions: int
    boundary_events: tuple[LifecycleBoundaryEvent, ...]
    terminated: bool
    truncated: bool

    def __post_init__(self) -> None:
        arrays = (
            ("delivered_user_rates_mbps", self.delivered_user_rates_mbps, (GROUND_USERS,), np.float64),
            ("executed_action_mask", self.executed_action_mask, (PHYSICAL_UAVS,), np.bool_),
            ("raw_actions", self.raw_actions, (PHYSICAL_UAVS, ACTION_DIM), np.float32),
            ("positions_before", self.positions_before, (PHYSICAL_UAVS, 3), np.float64),
            ("positions_after", self.positions_after, (PHYSICAL_UAVS, 3), np.float64),
            ("actual_velocities", self.actual_velocities, (PHYSICAL_UAVS, 3), np.float64),
        )
        for name, value, shape, dtype in arrays:
            array = np.asarray(value, dtype=dtype)
            if array.shape != shape or (
                dtype is not np.bool_ and not np.isfinite(array).all()
            ):
                raise G0RealizationError(f"transition {name} invariant failed")
            object.__setattr__(self, name, _readonly_array(array, dtype=dtype))

def _namespace_random_state(seed: int, namespace: int) -> np.random.RandomState:
    word = np.random.SeedSequence([int(seed), int(namespace)]).generate_state(1)[0]
    return np.random.RandomState(int(word))


def _random_state_primitive(random_state: np.random.RandomState) -> dict[str, Any]:
    algorithm, keys, position, has_gauss, cached_gaussian = random_state.get_state()
    return {
        "algorithm": str(algorithm),
        "keys": oracle_evidence._NativeArrayEvidence.from_array(keys).to_primitive(),
        "position": int(position),
        "has_gauss": int(has_gauss),
        "cached_gaussian": float(cached_gaussian),
    }


def _validate_random_state_primitive(value: Any) -> dict[str, Any]:
    expected = {"algorithm", "keys", "position", "has_gauss", "cached_gaussian"}
    if not isinstance(value, Mapping) or set(value) != expected:
        raise G0RealizationError("branchpoint RNG-state schema drifted")
    keys = oracle_evidence._native_array_from_primitive(value["keys"])
    key_array = keys.array()
    if (
        str(value["algorithm"]) != "MT19937"
        or key_array.shape != (624,)
        or key_array.dtype != np.dtype(np.uint32)
        or not 0 <= int(value["position"]) <= 624
        or int(value["has_gauss"]) not in (0, 1)
        or not math.isfinite(float(value["cached_gaussian"]))
    ):
        raise G0RealizationError("branchpoint RNG-state primitive is invalid")
    return {
        "algorithm": "MT19937",
        "keys": keys.to_primitive(),
        "position": int(value["position"]),
        "has_gauss": int(value["has_gauss"]),
        "cached_gaussian": float(value["cached_gaussian"]),
    }

def _rng_state_bindings(
    rng_states: Mapping[str, Any],
) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for name, item in sorted(rng_states.items()):
        key = str(name)
        if isinstance(item, Mapping) and set(item) == {
            "state_source",
            "state_sha256",
        }:
            source = str(item["state_source"])
            digest = str(item["state_sha256"])
            if (
                source != f"common_prestate.rng_states/{key}"
                or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)
            ):
                raise G0RealizationError("branchpoint RNG binding is invalid")
            result[key] = {"state_source": source, "state_sha256": digest}
        else:
            result[key] = {
                "state_source": f"common_prestate.rng_states/{key}",
                "state_sha256": sha256_json(
                    _validate_random_state_primitive(item)
                ),
            }
    return result


def _make_pre_action_context(
    source: G0EpisodeSource,
    *,
    physical_step: int,
    handles: Sequence[str],
    epochs: Sequence[int],
    selected_candidate_id: str,
    rng_states: Mapping[str, Any],
    service_active_mask: Sequence[bool],
) -> dict[str, Any]:
    if (
        len(handles) != PHYSICAL_UAVS
        or len(epochs) != PHYSICAL_UAVS
        or len(service_active_mask) != PHYSICAL_UAVS
    ):
        raise G0RealizationError("branchpoint lifecycle source inventory drifted")
    lifecycle: list[dict[str, Any]] = []
    for storage_row, (handle, epoch, owner_target) in enumerate(
        zip(handles, epochs, source.assignment.row_to_target)
    ):
        lifecycle.append(
            {
                "handle": str(handle),
                "epoch": int(epoch),
                "internal_row": int(source.geometry.slot_to_target[storage_row]),
                "owner_target": TargetLabel.parse(owner_target).key,
            }
        )
    lifecycle.sort(key=lambda row: int(row["internal_row"]))
    by_target = {row["owner_target"]: row for row in lifecycle}
    selected = TargetLabel.parse(selected_candidate_id)
    event_row = by_target[source.event.owner_target.key]
    selected_row = by_target[selected.key]
    context = {
        "physical_step": int(physical_step),
        "lifecycle_owner_to_internal": lifecycle,
        "service_active_mask": [bool(item) for item in service_active_mask],
        "event_owner_handle": event_row["handle"],
        "event_owner_epoch": int(event_row["epoch"]),
        "selected_reserve_handle": selected_row["handle"],
        "selected_reserve_original_target": selected.key,
        "survivor_ownership": [
            dict(row)
            for row in lifecycle
            if row["handle"] not in {event_row["handle"], selected_row["handle"]}
        ],
        "survivor_controller_rng_owners": [],
        "non_controller_rng_states": _rng_state_bindings(rng_states),
        "channel_tape_cursor": {
            "draw_ordinal": 0,
            "coordinate_count": 0,
            "block_count": 0,
        },
    }
    return oracle_evidence._validate_pre_action_context_primitive(context)


def _pre_action_context(
    env: "UAVSourceIdentifiabilityEnv",
    ownership: Mapping[str, TargetLabel],
    selected_candidate_id: str,
) -> dict[str, Any]:
    env._synchronize_service_mask()
    expected_ownership = {
        str(handle): TargetLabel.parse(owner_target).key
        for handle, owner_target in zip(
            env._handles, env.g0_source.assignment.row_to_target
        )
    }
    actual_ownership = {
        str(handle): TargetLabel.parse(label.key).key
        for handle, label in ownership.items()
    }
    if actual_ownership != expected_ownership:
        raise G0RealizationError("branchpoint controller ownership is stale or forged")
    live_rngs = {
        str(name): item
        for name, item in sorted(env.__dict__.items())
        if isinstance(item, np.random.RandomState)
    }
    rng_states = getattr(env, "_g0_branchpoint_rng_bindings", None)
    snapshots = getattr(env, "_g0_branchpoint_rng_snapshots", None)
    if rng_states is None or snapshots is None:
        primitives = {
            name: _random_state_primitive(item)
            for name, item in live_rngs.items()
        }
        rng_states = _rng_state_bindings(primitives)
        snapshots = {
            name: (
                state[0],
                np.asarray(state[1], dtype=np.uint32).copy(),
                int(state[2]),
                int(state[3]),
                float(state[4]),
            )
            for name, item in live_rngs.items()
            for state in (item.get_state(),)
        }
        env._g0_branchpoint_rng_bindings = rng_states
        env._g0_branchpoint_rng_snapshots = snapshots
    if set(live_rngs) != set(snapshots):
        raise G0RealizationError("branchpoint RNG ownership changed")
    for name, item in live_rngs.items():
        current = item.get_state()
        frozen = snapshots[name]
        if not (
            str(current[0]) == str(frozen[0])
            and np.array_equal(current[1], frozen[1])
            and int(current[2]) == int(frozen[2])
            and int(current[3]) == int(frozen[3])
            and float(current[4]) == float(frozen[4])
        ):
            raise G0RealizationError("branchpoint non-controller RNG state changed")
    return _make_pre_action_context(
        env.g0_source,
        physical_step=int(env.current_step),
        handles=env._handles,
        epochs=env._epochs,
        selected_candidate_id=selected_candidate_id,
        rng_states=rng_states,
        service_active_mask=env._service_active_mask,
    )

class _EmptyChannelDrawRandomState:
    """Fail closed if the registered deterministic channel path starts drawing RNG."""

    def __init__(self, delegate: np.random.RandomState) -> None:
        self._delegate = delegate
        self.requested_operations: list[str] = []

    def __getattr__(self, name: str) -> Any:
        value = getattr(self._delegate, name)
        if not callable(value):
            return value

        def forbidden(*args: Any, **kwargs: Any) -> Any:
            self.requested_operations.append(str(name))
            raise G0RealizationError(
                "registered inherited channel path no longer has an empty RNG schema"
            )

        return forbidden

class UAVSourceIdentifiabilityEnv(UAVEnergyAwareRelayEnv):
    """Exact G0 geometry plus ledger-driven service availability over S7-S1."""

    def __init__(
        self,
        source: G0EpisodeSource,
        cell: Cell | str,
        env_kwargs: Mapping[str, Any] | None = None,
    ) -> None:
        self.g0_source = source
        self.g0_cell = Cell(cell)
        self.environment_seed = int(source.geometry.episode_id)
        # The inherited environment always runs in target-owned world order.
        # G0's sampled physical-slot permutation is a storage adapter only.
        self._storage_to_internal = np.asarray(
            source.geometry.slot_to_target, dtype=np.int64
        ).copy()
        self._internal_to_storage = np.argsort(self._storage_to_internal)
        self._service_active_mask = np.ones(PHYSICAL_UAVS, dtype=np.bool_)
        self._last_mask_step = -1
        self._handles = controllers.initial_lifecycle_handles(source)
        self._epochs = np.zeros(PHYSICAL_UAVS, dtype=np.int64)
        self._pending_boundary_events: list[LifecycleBoundaryEvent] = []
        kwargs = dict(env_kwargs or {})
        unsupported = set(kwargs).difference({"render_mode"})
        if unsupported:
            raise G0RealizationError(
                "G0 env kwargs cannot override S7-S1: " + ", ".join(sorted(unsupported))
            )
        config = Config("S7-S1")
        super().__init__(config=config, seed=self.environment_seed, **kwargs)
        self._channel_rng = _namespace_random_state(self.environment_seed, 3)
        if (
            self.n_uavs != PHYSICAL_UAVS
            or self.n_users != GROUND_USERS
            or self.n_ground_bs != GROUND_BASE_STATIONS
            or self.action_dim != ACTION_DIM
            or self.max_steps != PHYSICAL_HORIZON
            or self.energy_stage != "S1"
            or self.battery_enabled
            or self.charging_enabled
            or self.failure_enabled
            or bool(getattr(self, "terminal_loss_enabled", False))
        ):
            raise G0RealizationError("G0 did not instantiate the frozen S7-S1 inventory")
        if (
            float(self.area_size) != source.geometry.map_width
            or float(self.area_size) != source.geometry.map_height
        ):
            raise G0RealizationError("S7-S1 map support differs from frozen G0 geometry")
        if not np.array_equal(
            np.asarray(self.ground_bs_positions[0, :2], dtype=np.float64),
            source.geometry.base_xy,
        ):
            raise G0RealizationError("environment base station differs from source center")
        if float(self.height_range[0]) != FIXED_ALTITUDE_M:
            raise G0RealizationError("S7-S1 fixed altitude changed")

    def _init_ground_bs(self) -> None:
        self.ground_bs_positions = np.asarray(
            [[*self.g0_source.geometry.base_xy.tolist(), 30.0]], dtype=np.float64
        )

    def _init_uav_positions(self) -> np.ndarray:
        return np.concatenate(
            (
                self.g0_source.geometry.target_owned_initial_xy,
                np.full((PHYSICAL_UAVS, 1), FIXED_ALTITUDE_M, dtype=np.float64),
            ),
            axis=1,
        )

    def _generate_user_positions(self) -> np.ndarray:
        return np.concatenate(
            (
                self.g0_source.geometry.users_xy,
                np.full((GROUND_USERS, 1), USER_ALTITUDE_M, dtype=np.float64),
            ),
            axis=1,
        )

    def _init_user_velocities(self) -> None:
        self.user_velocities[:] = 0.0

    def _initialize_user_waypoints_rpgm(self) -> None:
        # The registered G0 users are fixed.  Populate the inherited arrays so
        # diagnostics remain defined without advancing an RNG.
        self.user_waypoints = np.asarray(self.user_positions[:, :2], dtype=np.float64).copy()
        self.user_pause_times = np.zeros(self.n_users, dtype=np.float64)
        self.user_cluster_assignments = self.g0_source.geometry.user_hotspots.copy()
        self.cluster_centers_history = self.g0_source.geometry.hotspot_centers.copy()
        self.cluster_velocities = np.zeros((HOTSPOT_COUNT, 2), dtype=np.float64)
        self.cluster_waypoints = self.cluster_centers_history.copy()
        self.cluster_pause_times = np.zeros(HOTSPOT_COUNT, dtype=np.float64)

    def _move_users(self) -> None:
        # Fixed for the complete 500-step episode.
        return None

    def _update_channel_state(self) -> None:
        previous = getattr(self, "np_random", None)
        recorder = _EmptyChannelDrawRandomState(
            np.random.RandomState(
                channel_seed_word(
                    self.g0_source.geometry.episode_id,
                    int(getattr(self, "current_step", 0)),
                )
            )
        )
        self.np_random = recorder
        try:
            super()._update_channel_state()
        finally:
            if previous is not None:
                self.np_random = previous
        if recorder.requested_operations:
            raise G0RealizationError("channel draw schema is not the registered empty schema")

    @property
    def event_owner_row(self) -> int:
        return int(self._internal_to_storage[self.event_owner_internal_row])

    @property
    def event_owner_internal_row(self) -> int:
        return TARGET_LABELS.index(self.g0_source.event.owner_target)

    def _active_mask_for_step(self, physical_step: int) -> np.ndarray:
        mask = np.ones(PHYSICAL_UAVS, dtype=np.bool_)
        mask[self.event_owner_internal_row] = self.g0_source.event.active(
            physical_step, self.g0_cell
        )
        return mask

    @property
    def service_active_mask(self) -> np.ndarray:
        self._synchronize_service_mask()
        return self._service_active_mask[self._storage_to_internal].copy()

    def _is_uav_unavailable(self, uav_idx: int) -> bool:
        service = getattr(self, "_service_active_mask", None)
        if service is not None and not bool(service[int(uav_idx)]):
            return True
        return super()._is_uav_unavailable(uav_idx)

    def _communication_unavailable_mask(self) -> np.ndarray:
        unavailable = super()._communication_unavailable_mask()
        service = getattr(self, "_service_active_mask", None)
        if service is not None:
            unavailable |= ~np.asarray(service, dtype=np.bool_)
        return unavailable

    def _is_uav_motion_disabled(self, uav_idx: int) -> bool:
        service = getattr(self, "_service_active_mask", None)
        if service is not None and not bool(service[int(uav_idx)]):
            return True
        return super()._is_uav_motion_disabled(uav_idx)

    def _update_uav_failures(self) -> None:
        self.uav_failure_timers[:] = 0
        self.uav_failed[:] = False

    def _synchronize_service_mask(self, *, force: bool = False) -> bool:
        step = int(getattr(self, "current_step", 0))
        if not force and step == self._last_mask_step:
            return False
        old = self._service_active_mask.copy()
        new = self._active_mask_for_step(step)
        changed = not np.array_equal(old, new)
        self._service_active_mask = new
        self._last_mask_step = step
        if changed:
            owner_internal = self.event_owner_internal_row
            owner_storage = self.event_owner_row
            previous = self._handles[owner_storage]
            if old[owner_internal] and not new[owner_internal]:
                event = LifecycleBoundaryEvent(
                    kind="LEAVE",
                    physical_step=step,
                    previous_handle=previous,
                    current_handle=None,
                    owner_target=self.g0_source.event.owner_target.key,
                )
            elif not old[owner_internal] and new[owner_internal]:
                current = controllers.replacement_lifecycle_handle(self.g0_source, previous)
                handles = list(self._handles)
                handles[owner_storage] = current
                self._handles = tuple(handles)
                self._epochs[owner_storage] += 1
                event = LifecycleBoundaryEvent(
                    kind="REJOIN",
                    physical_step=step,
                    previous_handle=previous,
                    current_handle=current,
                    owner_target=self.g0_source.event.owner_target.key,
                )
            else:
                raise G0RealizationError("service mask changed outside the event owner")
            self._pending_boundary_events.append(event)
            if hasattr(self, "connections"):
                self._update_channel_state()
                self._update_uav_connections()
                self._compute_routing_paths()
        return changed

    def consume_boundary_events(self) -> tuple[LifecycleBoundaryEvent, ...]:
        self._synchronize_service_mask()
        events = tuple(self._pending_boundary_events)
        self._pending_boundary_events.clear()
        return events

    def reset(self, seed: int | None = None, options: Any = None):
        if seed is not None and int(seed) != self.environment_seed:
            raise G0RealizationError("G0 reset cannot replace the episode-ID source")
        self._service_active_mask[:] = True
        self._last_mask_step = -1
        self._handles = controllers.initial_lifecycle_handles(self.g0_source)
        self._epochs[:] = 0
        self._pending_boundary_events.clear()
        self._channel_rng = _namespace_random_state(self.environment_seed, 3)
        observations, infos = super().reset(seed=self.environment_seed, options=options)
        self._last_mask_step = -1
        self._synchronize_service_mask(force=True)
        if not np.array_equal(self.user_positions[:, :2], self.g0_source.geometry.users_xy):
            raise G0RealizationError("reset changed fixed G0 user geometry")
        if not np.array_equal(
            self.uav_positions[:, :2],
            self.g0_source.geometry.target_owned_initial_xy,
        ):
            raise G0RealizationError("reset changed target-owned UAV world geometry")
        if not np.array_equal(
            np.stack([row.position[:2] for row in self.current_rows()]),
            self.g0_source.geometry.physical_xy,
        ):
            raise G0RealizationError("reset changed storage-only slot permutation")
        return observations, infos

    def current_rows(self) -> tuple[controllers.AnonymousLifecycleRow, ...]:
        self._synchronize_service_mask()
        velocities = np.asarray(
            getattr(self, "last_actual_velocities", np.zeros((PHYSICAL_UAVS, 3))),
            dtype=np.float64,
        ).copy()
        velocities[~self._service_active_mask] = 0.0
        positions = np.asarray(self.uav_positions, dtype=np.float64)[
            self._storage_to_internal
        ]
        velocities = velocities[self._storage_to_internal]
        active = self._service_active_mask[self._storage_to_internal]
        return tuple(
            controllers.AnonymousLifecycleRow(
                handle=self._handles[row],
                position=positions[row],
                velocity=velocities[row],
                active=bool(active[row]),
                service_available=bool(active[row]),
            )
            for row in range(PHYSICAL_UAVS)
        )

    def _get_link_capacity(
        self,
        node1_type: str,
        node1_idx: int,
        node2_type: str,
        node2_idx: int,
    ) -> Any:
        value = super()._get_link_capacity(
            node1_type, node1_idx, node2_type, node2_idx
        )
        guarded_uav = getattr(self, "_inside_oracle_guard_uav", None)
        reads = getattr(self, "_oracle_guard_capacity_reads", None)
        if guarded_uav is not None and reads is not None:
            reads.append(
                oracle_evidence.OracleGuardCapacityRead.from_value(
                    guarded_uav=int(guarded_uav),
                    node1_type=node1_type,
                    node1_idx=node1_idx,
                    node2_type=node2_type,
                    node2_idx=node2_idx,
                    value=value,
                )
            )
        return value

    def _apply_backhaul_action_guard(self, uav_idx: int, velocity: Any) -> Any:
        previous = getattr(self, "_inside_oracle_guard_uav", None)
        self._inside_oracle_guard_uav = int(uav_idx)
        try:
            guarded = super()._apply_backhaul_action_guard(uav_idx, velocity)
        finally:
            self._inside_oracle_guard_uav = previous
        rows = getattr(self, "_oracle_guarded_velocity_rows", None)
        interventions = getattr(self, "_oracle_guard_interventions", None)
        if rows is not None and interventions is not None:
            proposed = np.asarray(velocity, dtype=np.float64)
            guarded_array = np.asarray(guarded, dtype=np.float64)
            rows[int(uav_idx)] = guarded_array
            interventions[int(uav_idx)] = not np.array_equal(
                proposed, guarded_array
            )
        return guarded

    def _begin_oracle_safety_capture(
        self,
        *,
        candidate_id: str,
        raw_internal: np.ndarray,
        pre_action_context: Mapping[str, Any],
        executed_service_mask: np.ndarray,
        common_transducer_evidence: Mapping[str, Any],
    ) -> dict[str, Any]:
        if getattr(self, "_oracle_guard_capacity_reads", None) is not None:
            raise G0RealizationError("nested oracle safety capture is forbidden")
        self._oracle_guard_capacity_reads = []
        self._oracle_guarded_velocity_rows = np.zeros(
            (PHYSICAL_UAVS, 3), dtype=np.float64
        )
        self._oracle_guard_interventions = np.zeros(PHYSICAL_UAVS, dtype=np.bool_)
        return {
            "physical_step": int(self.current_step),
            "candidate_id": str(candidate_id),
            "positions": np.asarray(self.uav_positions).copy(),
            "velocities": np.asarray(self.last_actual_velocities).copy(),
            "service_mask": np.asarray(self._service_active_mask).copy(),
            "pre_action_context": oracle_evidence._json_safe(pre_action_context),
            "executed_service_mask": np.asarray(
                executed_service_mask, dtype=np.bool_
            ).copy(),
            "common_transducer_evidence": oracle_evidence._json_safe(
                common_transducer_evidence
            ),
            "raw_internal": np.asarray(raw_internal, dtype=np.float32).copy(),
            "connections": {
                "user": oracle_evidence._NativeArrayEvidence.from_array(self.connections),
                "uav": oracle_evidence._NativeArrayEvidence.from_array(self.uav_connections),
                "uav_bs": oracle_evidence._NativeArrayEvidence.from_array(self.uav_bs_connections),
            },
            "routing_paths": tuple(oracle_evidence._routing_paths_primitive(self.routing_paths)),
            "guard_checked_before": int(
                getattr(self, "backhaul_guard_checked_actions", 0)
            ),
            "guard_blocked_before": int(
                getattr(self, "backhaul_guard_blocked_actions", 0)
            ),
        }

    def _finish_oracle_safety_capture(
        self,
        capture: Mapping[str, Any],
    ) -> oracle_evidence.OracleSafetyStepRecord:
        reads = tuple(self._oracle_guard_capacity_reads)
        guarded = np.asarray(self._oracle_guarded_velocity_rows).copy()
        interventions = np.asarray(self._oracle_guard_interventions).copy()
        self._oracle_guard_capacity_reads = None
        self._oracle_guarded_velocity_rows = None
        self._oracle_guard_interventions = None
        current = np.asarray(capture["positions"], dtype=np.float64)
        next_positions = np.asarray(self.uav_positions, dtype=np.float64).copy()
        velocities = (next_positions - current) / float(self.time_step)
        return oracle_evidence.OracleSafetyStepRecord(
            physical_step=int(capture["physical_step"]),
            candidate_id=str(capture["candidate_id"]),
            current_uav_positions=oracle_evidence._NativeArrayEvidence.from_array(current),
            current_uav_velocities=oracle_evidence._NativeArrayEvidence.from_array(
                capture["velocities"]
            ),
            current_service_mask=oracle_evidence._NativeArrayEvidence.from_array(
                capture["service_mask"]
            ),
            pre_action_context=oracle_evidence._validate_pre_action_context_primitive(
                capture["pre_action_context"]
            ),
            executed_service_mask=oracle_evidence._NativeArrayEvidence.from_array(
                capture["executed_service_mask"]
            ),
            common_transducer_evidence=(
                oracle_evidence._validate_common_transducer_evidence_primitive(
                    capture["common_transducer_evidence"]
                )
            ),
            raw_candidate_action=oracle_evidence._NativeArrayEvidence.from_array(
                capture["raw_internal"]
            ),
            shared_channel_draw_coordinate=(),
            shared_channel_draw_block=(),
            connections=dict(capture["connections"]),
            routing_paths=tuple(capture["routing_paths"]),
            exact_link_capacity_values_read_by_the_real_guard=reads,
            real_guard_intervention_or_violation_output={
                "checked_actions": int(
                    getattr(self, "backhaul_guard_checked_actions", 0)
                ),
                "blocked_actions": int(
                    getattr(self, "backhaul_guard_blocked_actions", 0)
                ),
                "intervention_by_uav": interventions.tolist(),
            },
            guarded_executed_action=oracle_evidence._NativeArrayEvidence.from_array(guarded),
            next_uav_positions=oracle_evidence._NativeArrayEvidence.from_array(next_positions),
            next_uav_velocities=oracle_evidence._NativeArrayEvidence.from_array(velocities),
        )

    def step_oracle_safety(
        self,
        actions_internal: np.ndarray,
        *,
        candidate_id: str,
        ownership: Mapping[str, TargetLabel],
        pre_action_context: Mapping[str, Any],
        common_transducer_evidence: Mapping[str, Any],
    ) -> oracle_evidence.OracleSafetyStepRecord:
        """Advance only physical/channel/routing safety state, never service/reward."""

        self._synchronize_service_mask()
        dense = np.asarray(actions_internal, dtype=np.float32)
        if dense.shape != (PHYSICAL_UAVS, ACTION_DIM):
            raise G0RealizationError("oracle safety action must have shape [8,4]")
        if not np.isfinite(dense).all() or np.any(np.abs(dense) > 1.0):
            raise G0RealizationError("oracle safety action is outside support")
        if not np.array_equal(dense[:, 2], np.zeros(PHYSICAL_UAVS, dtype=np.float32)):
            raise G0RealizationError("oracle safety action changed fixed altitude")
        expected_context = _pre_action_context(
            self, ownership, str(candidate_id)
        )
        actual_context = oracle_evidence._validate_pre_action_context_primitive(
            pre_action_context
        )
        if actual_context != expected_context:
            raise G0RealizationError("oracle safety branchpoint context is stale")
        transducer = oracle_evidence._validate_common_transducer_evidence_primitive(
            common_transducer_evidence
        )
        if (
            not np.array_equal(
                oracle_evidence._native_array_from_primitive(
                    transducer["physical_positions"]
                ).array(),
                np.asarray(self.uav_positions, dtype=np.float64),
            )
            or not np.array_equal(
                oracle_evidence._native_array_from_primitive(transducer["active_mask"]).array(),
                self._service_active_mask,
            )
            or not np.array_equal(
                oracle_evidence._native_array_from_primitive(transducer["raw_action"]).array(),
                dense,
            )
        ):
            raise G0RealizationError("oracle safety transducer binding is stale")
        executed_service_mask = self._service_active_mask.copy()
        capture = self._begin_oracle_safety_capture(
            candidate_id=candidate_id,
            raw_internal=dense,
            pre_action_context=actual_context,
            executed_service_mask=executed_service_mask,
            common_transducer_evidence=transducer,
        )
        action_dict = {
            agent: dense[row].copy()
            for row, agent in enumerate(self.possible_agents)
            if self._service_active_mask[row]
        }
        adjusted_actions, _commanded_velocities = self._prepare_energy_actions(
            action_dict
        )
        self.previous_routing_paths_snapshot = dict(self.routing_paths)
        self.previous_connections_snapshot = self.connections.copy()
        self._move_users()
        self.backhaul_guard_checked_actions = 0
        self.backhaul_guard_blocked_actions = 0
        before = np.asarray(self.uav_positions, dtype=np.float64).copy()
        for agent_idx, agent in enumerate(self.agents):
            action = np.asarray(adjusted_actions[agent], dtype=np.float32)
            velocity = action * float(self.max_speed)
            velocity = np.asarray(
                self._apply_backhaul_action_guard(agent_idx, velocity),
                dtype=np.float64,
            )
            next_position = self.uav_positions[agent_idx] + velocity * float(
                self.time_step
            )
            next_position[0] = np.clip(next_position[0], 0.0, self.area_size)
            next_position[1] = np.clip(next_position[1], 0.0, self.area_size)
            next_position[2] = np.clip(next_position[2], *self.height_range)
            self.uav_positions[agent_idx] = next_position
        self.last_actual_velocities = (
            np.asarray(self.uav_positions, dtype=np.float64) - before
        ) / float(self.time_step)
        self._update_channel_state()
        self._update_uav_connections()
        if (
            self.routing_protocol == "hggr"
            and self.current_step % self.hggr_update_interval == 0
        ):
            self.hop_map = self._calculate_hop_map()
        if self.current_step % self.hggr_update_interval == 0:
            self._update_global_bs_cache()
        self._compute_routing_paths()
        self.current_step += 1
        record = self._finish_oracle_safety_capture(capture)
        self._synchronize_service_mask(force=True)
        return record

    def step_dense(
        self,
        actions: np.ndarray,
        *,
        oracle_ownership: Mapping[str, TargetLabel] | None = None,
        oracle_pre_action_context: Mapping[str, Any] | None = None,
        oracle_common_transducer_evidence: Mapping[str, Any] | None = None,
    ) -> G0Transition:
        self._synchronize_service_mask()
        dense = np.asarray(actions, dtype=np.float32)
        if dense.shape != (PHYSICAL_UAVS, ACTION_DIM):
            raise G0RealizationError("G0 action must have shape [8,4]")
        if not np.isfinite(dense).all() or np.any(np.abs(dense) > 1.0):
            raise G0RealizationError("G0 action is outside the Scenario-7 support")
        if not np.array_equal(
            dense[:, 2], np.zeros(PHYSICAL_UAVS, dtype=np.float32)
        ):
            raise G0RealizationError("G0 fixed-altitude route received vertical action")
        dense_internal = np.zeros_like(dense)
        dense_internal[self._storage_to_internal] = dense
        executed_internal = self._service_active_mask.copy()
        executed = executed_internal[self._storage_to_internal]
        before_internal = np.asarray(self.uav_positions, dtype=np.float64).copy()
        behavioral_candidate = getattr(
            self, "_oracle_behavioral_candidate_id", None
        )
        safety_capture = None
        if behavioral_candidate is not None:
            if (
                oracle_ownership is None
                or oracle_pre_action_context is None
                or oracle_common_transducer_evidence is None
            ):
                raise G0RealizationError(
                    "behavioral branch omitted branchpoint/transducer evidence"
                )
            expected_context = _pre_action_context(
                self, oracle_ownership, str(behavioral_candidate)
            )
            actual_context = oracle_evidence._validate_pre_action_context_primitive(
                oracle_pre_action_context
            )
            if actual_context != expected_context:
                raise G0RealizationError("behavioral branchpoint context is stale")
            transducer = oracle_evidence._validate_common_transducer_evidence_primitive(
                oracle_common_transducer_evidence
            )
            if (
                not np.array_equal(
                    oracle_evidence._native_array_from_primitive(
                        transducer["physical_positions"]
                    ).array(),
                    np.asarray(self.uav_positions, dtype=np.float64),
                )
                or not np.array_equal(
                    oracle_evidence._native_array_from_primitive(
                        transducer["active_mask"]
                    ).array(),
                    executed_internal,
                )
                or not np.array_equal(
                    oracle_evidence._native_array_from_primitive(transducer["raw_action"]).array(),
                    dense_internal,
                )
            ):
                raise G0RealizationError("behavioral transducer binding is stale")
            safety_capture = self._begin_oracle_safety_capture(
                candidate_id=str(behavioral_candidate),
                raw_internal=dense_internal,
                pre_action_context=actual_context,
                executed_service_mask=executed_internal,
                common_transducer_evidence=transducer,
            )
        elif any(
            item is not None
            for item in (
                oracle_ownership,
                oracle_pre_action_context,
                oracle_common_transducer_evidence,
            )
        ):
            raise G0RealizationError("non-oracle step received oracle evidence")
        action_dict = {
            agent: dense_internal[row].copy()
            for row, agent in enumerate(self.possible_agents)
            if executed_internal[row]
        }
        _observations, _rewards, terminations, truncations, _infos = super().step(
            action_dict
        )
        if safety_capture is not None:
            behavioral_trace = getattr(self, "_oracle_behavioral_trace", None)
            if behavioral_trace is None:
                behavioral_trace = []
                self._oracle_behavioral_trace = behavioral_trace
            behavioral_trace.append(
                self._finish_oracle_safety_capture(safety_capture)
            )
        after_internal = np.asarray(self.uav_positions, dtype=np.float64).copy()
        velocities_internal = np.asarray(
            self.last_actual_velocities, dtype=np.float64
        ).copy()
        if not np.array_equal(
            after_internal[~executed_internal], before_internal[~executed_internal]
        ):
            raise G0RealizationError("absent lifecycle physical slot moved")
        if not (
            np.array_equal(
                before_internal[:, 2], np.full(PHYSICAL_UAVS, FIXED_ALTITUDE_M)
            )
            and np.array_equal(
                after_internal[:, 2], np.full(PHYSICAL_UAVS, FIXED_ALTITUDE_M)
            )
        ):
            raise G0RealizationError("G0 fixed-altitude invariant changed")
        if not np.array_equal(
            velocities_internal[~executed_internal],
            np.zeros((int((~executed_internal).sum()), 3), dtype=np.float64),
        ):
            raise G0RealizationError("absent lifecycle velocity was not exact zero")
        before = before_internal[self._storage_to_internal]
        after = after_internal[self._storage_to_internal]
        velocities = velocities_internal[self._storage_to_internal]
        completed_step = int(self.current_step) - 1
        self._synchronize_service_mask(force=True)
        return G0Transition(
            physical_step=completed_step,
            delivered_user_rates_mbps=np.asarray(self.last_user_rates_mbps, dtype=np.float64),
            executed_action_mask=executed,
            raw_actions=dense,
            positions_before=before,
            positions_after=after,
            actual_velocities=velocities,
            backhaul_guard_blocked_actions=int(
                getattr(self, "backhaul_guard_blocked_actions", 0)
            ),
            boundary_events=self.consume_boundary_events(),
            terminated=bool(all(terminations.values())) if terminations else False,
            truncated=bool(all(truncations.values())) if truncations else False,
        )
