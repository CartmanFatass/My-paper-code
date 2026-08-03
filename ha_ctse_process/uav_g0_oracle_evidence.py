"""Oracle evidence records, codecs, and native method identity for UAV G0."""

from __future__ import annotations

from dataclasses import dataclass, field
import functools
import hashlib
import inspect
import math
from typing import TYPE_CHECKING, Any, Callable, Mapping

import numpy as np

from envs.pettingzoo.relay.energy_aware import UAVEnergyAwareRelayEnv
from ha_ctse_process import uav_g0_geometry as _geometry
from ha_ctse_process.uav_episode_schema import (
    ACTION_DIM,
    PHYSICAL_HORIZON,
    PHYSICAL_UAVS,
    G0RealizationError,
)
from ha_ctse_process.uav_g0_geometry import (
    TargetKind,
    TargetLabel,
    g1_common_target_actions,
    sha256_json,
)

if TYPE_CHECKING:
    from ha_ctse_process.uav_g0_geometry import G0EpisodeSource


K_SEARCH = 2


K_SEARCH_CEILING = 16


_ORACLE_SAFETY_ALLOWED_STEP_KEYS = frozenset(
    {
        "physical_step",
        "candidate_id",
        "current_uav_positions",
        "current_uav_velocities",
        "current_service_mask",
        "pre_action_context",
        "executed_service_mask",
        "common_transducer_evidence",
        "raw_candidate_action",
        "shared_channel_draw_coordinate",
        "shared_channel_draw_block",
        "connections",
        "routing_paths",
        "exact_link_capacity_values_read_by_the_real_guard",
        "real_guard_intervention_or_violation_output",
        "guarded_executed_action",
        "next_uav_positions",
        "next_uav_velocities",
    }
)


_PRE_ACTION_CONTEXT_KEYS = frozenset(
    {
        "physical_step",
        "lifecycle_owner_to_internal",
        "service_active_mask",
        "event_owner_handle",
        "event_owner_epoch",
        "selected_reserve_handle",
        "selected_reserve_original_target",
        "survivor_ownership",
        "survivor_controller_rng_owners",
        "non_controller_rng_states",
        "channel_tape_cursor",
    }
)


_LIFECYCLE_CONTEXT_ROW_KEYS = frozenset(
    {"handle", "epoch", "internal_row", "owner_target"}
)


_COMMON_TRANSDUCER_EVIDENCE_KEYS = frozenset(
    {
        "transducer_source_sha256",
        "row_order",
        "physical_positions",
        "target_positions",
        "active_mask",
        "raw_action",
        "max_speed",
        "max_vertical_speed",
        "time_step",
    }
)


def _json_safe(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return {"nonfinite_float": value.hex()}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise G0RealizationError(
        f"value of type {type(value).__name__} is not primitive evidence"
    )


@functools.cache
def _callable_source_digest(value: Callable[..., Any]) -> str:
    """Hash immutable code identity once per callable object in this process."""

    text = inspect.getsource(value).replace("\r\n", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def common_tracker_source_digest() -> str:
    return _callable_source_digest(_geometry.actions_toward_targets)


def shared_action_method_digests() -> dict[str, str]:
    return {
        "prepare_energy_actions": _callable_source_digest(
            UAVEnergyAwareRelayEnv._prepare_energy_actions
        ),
        "movement_velocity": _callable_source_digest(
            UAVEnergyAwareRelayEnv._movement_velocity_from_action
        ),
        "base_action": _callable_source_digest(
            UAVEnergyAwareRelayEnv._base_action_from_velocity
        ),
        "scenario7_backhaul_guard": _callable_source_digest(
            UAVEnergyAwareRelayEnv._apply_backhaul_action_guard
        ),
        "base_backhaul_guard": _callable_source_digest(
            UAVEnergyAwareRelayEnv.__mro__[1]._apply_backhaul_action_guard
        ),
    }


@dataclass(frozen=True)
class OracleSafetyDrawCoordinate:
    physical_step: int
    channel_update_ordinal: int
    rng_operation: str
    shape: tuple[int, ...]
    dtype: str

    def to_primitive(self) -> dict[str, Any]:
        return {
            "physical_step": int(self.physical_step),
            "channel_update_ordinal": int(self.channel_update_ordinal),
            "rng_operation": str(self.rng_operation),
            "shape": list(self.shape),
            "dtype": str(self.dtype),
        }


@dataclass(frozen=True)
class _NativeArrayEvidence:
    dtype: str
    shape: tuple[int, ...]
    data_hex: str

    @classmethod
    def from_array(cls, value: Any) -> "_NativeArrayEvidence":
        array = np.asarray(value)
        return cls(
            dtype=array.dtype.str,
            shape=tuple(int(item) for item in array.shape),
            data_hex=array.tobytes(order="C").hex(),
        )

    def array(self) -> np.ndarray:
        dtype = np.dtype(self.dtype)
        expected = int(np.prod(self.shape, dtype=np.int64)) * dtype.itemsize
        raw = bytes.fromhex(self.data_hex)
        if len(raw) != expected:
            raise G0RealizationError("native array byte count does not match shape/dtype")
        return np.frombuffer(raw, dtype=dtype).reshape(self.shape).copy()

    def to_primitive(self) -> dict[str, Any]:
        return {
            "dtype": self.dtype,
            "shape": list(self.shape),
            "data_hex": self.data_hex,
        }


@dataclass(frozen=True)
class OracleGuardCapacityRead:
    guarded_uav: int
    node1_type: str
    node1_idx: int
    node2_type: str
    node2_idx: int
    capacity_dtype: str
    capacity_hex: str

    @classmethod
    def from_value(
        cls,
        *,
        guarded_uav: int,
        node1_type: str,
        node1_idx: int,
        node2_type: str,
        node2_idx: int,
        value: Any,
    ) -> "OracleGuardCapacityRead":
        scalar = np.asarray(value)
        if scalar.shape != () or not np.isfinite(scalar).all():
            raise G0RealizationError("real guard returned a nonfinite link capacity")
        return cls(
            guarded_uav=int(guarded_uav),
            node1_type=str(node1_type),
            node1_idx=int(node1_idx),
            node2_type=str(node2_type),
            node2_idx=int(node2_idx),
            capacity_dtype=scalar.dtype.str,
            capacity_hex=scalar.tobytes().hex(),
        )

    def capacity(self) -> float:
        dtype = np.dtype(self.capacity_dtype)
        raw = bytes.fromhex(self.capacity_hex)
        if len(raw) != dtype.itemsize:
            raise G0RealizationError("guard capacity byte count drifted")
        value = np.frombuffer(raw, dtype=dtype)[0]
        if not np.isfinite(value):
            raise G0RealizationError("guard capacity is nonfinite")
        return float(value)

    def to_primitive(self) -> dict[str, Any]:
        return {
            "guarded_uav": int(self.guarded_uav),
            "node1_type": self.node1_type,
            "node1_idx": int(self.node1_idx),
            "node2_type": self.node2_type,
            "node2_idx": int(self.node2_idx),
            "capacity_dtype": self.capacity_dtype,
            "capacity_hex": self.capacity_hex,
        }


def _routing_paths_primitive(routing_paths: Mapping[Any, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_index, value in routing_paths.items():
        path, bottleneck = value
        rows.append(
            {
                "source_uav": int(source_index),
                "path": [[str(kind), int(index)] for kind, index in path],
                "bottleneck_capacity_dtype": np.asarray(bottleneck).dtype.str,
                "bottleneck_capacity_hex": np.asarray(bottleneck).tobytes().hex(),
            }
        )
    return rows


@dataclass(frozen=True)
class OracleSafetyStepRecord:
    physical_step: int
    candidate_id: str
    current_uav_positions: _NativeArrayEvidence
    current_uav_velocities: _NativeArrayEvidence
    current_service_mask: _NativeArrayEvidence
    pre_action_context: Mapping[str, Any]
    executed_service_mask: _NativeArrayEvidence
    common_transducer_evidence: Mapping[str, Any]
    raw_candidate_action: _NativeArrayEvidence
    shared_channel_draw_coordinate: tuple[OracleSafetyDrawCoordinate, ...]
    shared_channel_draw_block: tuple[str, ...]
    connections: Mapping[str, _NativeArrayEvidence]
    routing_paths: tuple[Mapping[str, Any], ...]
    exact_link_capacity_values_read_by_the_real_guard: tuple[OracleGuardCapacityRead, ...]
    real_guard_intervention_or_violation_output: Mapping[str, Any]
    guarded_executed_action: _NativeArrayEvidence
    next_uav_positions: _NativeArrayEvidence
    next_uav_velocities: _NativeArrayEvidence

    def to_primitive(self) -> dict[str, Any]:
        value = {
            "physical_step": int(self.physical_step),
            "candidate_id": self.candidate_id,
            "current_uav_positions": self.current_uav_positions.to_primitive(),
            "current_uav_velocities": self.current_uav_velocities.to_primitive(),
            "current_service_mask": self.current_service_mask.to_primitive(),
            "pre_action_context": _json_safe(self.pre_action_context),
            "executed_service_mask": self.executed_service_mask.to_primitive(),
            "common_transducer_evidence": _json_safe(
                self.common_transducer_evidence
            ),
            "raw_candidate_action": self.raw_candidate_action.to_primitive(),
            "shared_channel_draw_coordinate": [
                coordinate.to_primitive()
                for coordinate in self.shared_channel_draw_coordinate
            ],
            "shared_channel_draw_block": list(self.shared_channel_draw_block),
            "connections": {
                key: item.to_primitive() for key, item in self.connections.items()
            },
            "routing_paths": [dict(item) for item in self.routing_paths],
            "exact_link_capacity_values_read_by_the_real_guard": [
                item.to_primitive()
                for item in self.exact_link_capacity_values_read_by_the_real_guard
            ],
            "real_guard_intervention_or_violation_output": dict(
                self.real_guard_intervention_or_violation_output
            ),
            "guarded_executed_action": self.guarded_executed_action.to_primitive(),
            "next_uav_positions": self.next_uav_positions.to_primitive(),
            "next_uav_velocities": self.next_uav_velocities.to_primitive(),
        }
        if set(value) != _ORACLE_SAFETY_ALLOWED_STEP_KEYS:
            raise G0RealizationError("oracle safety step schema drifted")
        return value


@dataclass(frozen=True)
class OracleCandidateSafetyTrace:
    candidate_id: str
    target_schedule_sha256: str
    common_prestate_sha256: str
    steps: tuple[OracleSafetyStepRecord, ...]
    hard_violation_count: int
    gate_arrival_time: int
    gate_arrival_error: float
    event_window_tracking_error: float
    path_length: float
    stage_coordinates: tuple[float, float]
    trace_sha256: str

    @property
    def rank(self) -> tuple[float, ...]:
        return (
            float(self.hard_violation_count),
            float(self.gate_arrival_time),
            float(self.event_window_tracking_error),
            float(self.path_length),
            float(self.stage_coordinates[0]),
            float(self.stage_coordinates[1]),
        )

    def to_primitive(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "target_schedule_sha256": self.target_schedule_sha256,
            "common_prestate_sha256": self.common_prestate_sha256,
            "steps": [step.to_primitive() for step in self.steps],
            "hard_violation_count": int(self.hard_violation_count),
            "gate_arrival_time": int(self.gate_arrival_time),
            "gate_arrival_error": float(self.gate_arrival_error),
            "event_window_tracking_error": float(self.event_window_tracking_error),
            "path_length": float(self.path_length),
            "stage_coordinates": list(self.stage_coordinates),
            "trace_sha256": self.trace_sha256,
        }


@dataclass(frozen=True)
class OracleSafetyLedger:
    source_sha256: str
    common_prestate: Mapping[str, Any]
    common_prestate_sha256: str
    candidate_prestate_sha256: tuple[str, str]
    channel_draw_schema: tuple[OracleSafetyDrawCoordinate, ...]
    shared_channel_draw_blocks: tuple[str, ...]
    candidates: tuple[OracleCandidateSafetyTrace, OracleCandidateSafetyTrace]
    selected_candidate_id: str
    selected_rank: tuple[float, ...]
    shared_action_method_sha256: Mapping[str, str]
    content_sha256: str

    def to_primitive(self, *, include_digest: bool = True) -> dict[str, Any]:
        value = {
            "source_sha256": self.source_sha256,
            "common_prestate": dict(self.common_prestate),
            "common_prestate_sha256": self.common_prestate_sha256,
            "candidate_prestate_sha256": list(self.candidate_prestate_sha256),
            "channel_draw_schema": [item.to_primitive() for item in self.channel_draw_schema],
            "shared_channel_draw_blocks": list(self.shared_channel_draw_blocks),
            "candidates": [item.to_primitive() for item in self.candidates],
            "selected_candidate_id": self.selected_candidate_id,
            "selected_rank": list(self.selected_rank),
            "shared_action_method_sha256": dict(self.shared_action_method_sha256),
            "registration_order": [
                "freeze_common_prestate",
                "freeze_channel_draw_schema",
                "materialize_shared_channel_tape",
                "advance_each_candidate_once",
                "seal_both_candidate_traces",
                "rank_sealed_trace_keys_only",
                "behavioral_service_after_selection",
            ],
            "K_search": K_SEARCH,
            "physical_horizon": PHYSICAL_HORIZON,
            "hypothetical_candidate_transitions": sum(
                len(item.steps) for item in self.candidates
            ),
        }
        if include_digest:
            value["content_sha256"] = self.content_sha256
        return value


@dataclass(frozen=True)
class OracleSafetyCertificate:
    ledger_sha256: str
    selected_candidate_id: str
    candidate_trace_sha256: tuple[str, str]
    behavioral_replay_sha256: str | None = None
    return_ready_step: int | None = None
    prefix_identity_ok: bool | None = None
    branchpoint_identity_ok: bool | None = None
    shared_ledger_identity_ok: bool | None = None
    prebehavior_self_replay_ok: bool | None = None
    behavioral_self_replay_ok: bool | None = None
    target_switch_ok: bool | None = None
    safety_guard_ok: bool | None = None
    replay_ok: bool | None = None

    def to_primitive(self) -> dict[str, Any]:
        return {
            "ledger_sha256": self.ledger_sha256,
            "selected_candidate_id": self.selected_candidate_id,
            "candidate_trace_sha256": list(self.candidate_trace_sha256),
            "behavioral_replay_sha256": self.behavioral_replay_sha256,
            "return_ready_step": self.return_ready_step,
            "prefix_identity_ok": self.prefix_identity_ok,
            "branchpoint_identity_ok": self.branchpoint_identity_ok,
            "shared_ledger_identity_ok": self.shared_ledger_identity_ok,
            "prebehavior_self_replay_ok": self.prebehavior_self_replay_ok,
            "behavioral_self_replay_ok": self.behavioral_self_replay_ok,
            "target_switch_ok": self.target_switch_ok,
            "safety_guard_ok": self.safety_guard_ok,
            "replay_ok": self.replay_ok,
        }


_VALIDATED_ORACLE_SAFETY_CONTEXT_SEAL = object()


@dataclass(frozen=True, eq=False, init=False)
class _ValidatedOracleSafetyContext:
    """Call-local proof that one immutable ledger passed native reconstruction."""

    source: G0EpisodeSource
    ledger: OracleSafetyLedger
    certificate: OracleSafetyCertificate
    content_sha256: str
    candidate_trace_sha256: tuple[str, str]
    seal: object = field(repr=False, compare=False)


@dataclass(frozen=True)
class OracleBehavioralExecution:
    """Safety-only projection of one causal selected-candidate execution."""

    selected_candidate_id: str
    return_ready_step: int | None
    steps: tuple[OracleSafetyStepRecord, ...]
    target_schedule: _NativeArrayEvidence
    pre_action_weakest_service: _NativeArrayEvidence
    trace_sha256: str

    def to_primitive(self) -> dict[str, Any]:
        return {
            "selected_candidate_id": self.selected_candidate_id,
            "return_ready_step": self.return_ready_step,
            "steps": [step.to_primitive() for step in self.steps],
            "target_schedule": self.target_schedule.to_primitive(),
            "pre_action_weakest_service": (
                self.pre_action_weakest_service.to_primitive()
            ),
            "trace_sha256": self.trace_sha256,
        }


@dataclass(frozen=True)
class OracleCandidateEvidence:
    reserve_target: str
    latest_departure: int
    gate_arrival_time: int
    gate_arrival_error: float
    gate_arrival_roundoff_bound: float
    hard_violation_count: int
    event_window_tracking_error: float
    path_length: float
    stage_coordinates: tuple[float, float]
    physical_steps_advanced: int
    target_schedule_exact: bool
    action_support_valid: bool
    map_support_valid: bool
    candidate_complete: bool
    trace_sha256: str

    @property
    def rank(self) -> tuple[float, ...]:
        return (
            float(self.hard_violation_count),
            float(self.gate_arrival_time),
            float(self.event_window_tracking_error),
            float(self.path_length),
            float(self.stage_coordinates[0]),
            float(self.stage_coordinates[1]),
        )

    def to_primitive(self) -> dict[str, Any]:
        return {
            "reserve_target": self.reserve_target,
            "latest_departure": int(self.latest_departure),
            "gate_arrival_time": int(self.gate_arrival_time),
            "gate_arrival_error": float(self.gate_arrival_error),
            "gate_arrival_roundoff_bound": float(self.gate_arrival_roundoff_bound),
            "hard_violation_count": int(self.hard_violation_count),
            "event_window_tracking_error": float(self.event_window_tracking_error),
            "path_length": float(self.path_length),
            "stage_coordinates": list(self.stage_coordinates),
            "physical_steps_advanced": int(self.physical_steps_advanced),
            "target_schedule_exact": bool(self.target_schedule_exact),
            "action_support_valid": bool(self.action_support_valid),
            "map_support_valid": bool(self.map_support_valid),
            "candidate_complete": bool(self.candidate_complete),
            "trace_sha256": self.trace_sha256,
        }


@dataclass(frozen=True)
class OracleQualificationCertificate:
    candidates: tuple[OracleCandidateEvidence, OracleCandidateEvidence]
    selected_reserve_target: str
    selected_rank: tuple[float, ...]
    both_candidates_evaluated: bool
    exact_lexicographic_winner: bool
    future_channel_read_count: int
    future_service_read_count: int
    unaffected_primary_move_creates_vacancy: bool
    candidate_owner_is_reserve: bool
    shared_dynamics_action_safety_identity: bool
    candidate_count: int
    complexity: str
    nested_rollout: bool
    replanning: bool
    tree_search: bool
    beam_search: bool
    mcts: bool
    adaptive_candidate_creation: bool
    passed: bool
    oracle_safety_ledger_sha256: str = ""
    safety_certificate: OracleSafetyCertificate | None = None

    def to_primitive(self) -> dict[str, Any]:
        return {
            "candidates": [candidate.to_primitive() for candidate in self.candidates],
            "selected_reserve_target": self.selected_reserve_target,
            "selected_rank": list(self.selected_rank),
            "both_candidates_evaluated": self.both_candidates_evaluated,
            "exact_lexicographic_winner": self.exact_lexicographic_winner,
            "future_channel_read_count": self.future_channel_read_count,
            "future_service_read_count": self.future_service_read_count,
            "unaffected_primary_move_creates_vacancy": self.unaffected_primary_move_creates_vacancy,
            "candidate_owner_is_reserve": self.candidate_owner_is_reserve,
            "shared_dynamics_action_safety_identity": self.shared_dynamics_action_safety_identity,
            "shared_action_method_sha256": shared_action_method_digests(),
            "candidate_count": self.candidate_count,
            "K_search": K_SEARCH,
            "K_search_ceiling": K_SEARCH_CEILING,
            "complexity": self.complexity,
            "nested_rollout": self.nested_rollout,
            "replanning": self.replanning,
            "tree_search": self.tree_search,
            "beam_search": self.beam_search,
            "MCTS": self.mcts,
            "adaptive_candidate_creation": self.adaptive_candidate_creation,
            "oracle_safety_ledger_sha256": self.oracle_safety_ledger_sha256,
            "safety_certificate": (
                None
                if self.safety_certificate is None
                else self.safety_certificate.to_primitive()
            ),
            "passed": self.passed,
        }


def _native_array_from_primitive(value: Any) -> _NativeArrayEvidence:
    if not isinstance(value, Mapping) or set(value) != {"dtype", "shape", "data_hex"}:
        raise G0RealizationError("native array primitive schema drifted")
    evidence = _NativeArrayEvidence(
        dtype=str(value["dtype"]),
        shape=tuple(int(item) for item in value["shape"]),
        data_hex=str(value["data_hex"]),
    )
    evidence.array()
    return evidence


def _draw_coordinate_from_primitive(value: Any) -> OracleSafetyDrawCoordinate:
    expected = {
        "physical_step",
        "channel_update_ordinal",
        "rng_operation",
        "shape",
        "dtype",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        raise G0RealizationError("channel draw coordinate schema drifted")
    return OracleSafetyDrawCoordinate(
        physical_step=int(value["physical_step"]),
        channel_update_ordinal=int(value["channel_update_ordinal"]),
        rng_operation=str(value["rng_operation"]),
        shape=tuple(int(item) for item in value["shape"]),
        dtype=str(value["dtype"]),
    )


def _guard_read_from_primitive(value: Any) -> OracleGuardCapacityRead:
    expected = {
        "guarded_uav",
        "node1_type",
        "node1_idx",
        "node2_type",
        "node2_idx",
        "capacity_dtype",
        "capacity_hex",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        raise G0RealizationError("guard capacity-read schema drifted")
    result = OracleGuardCapacityRead(
        guarded_uav=int(value["guarded_uav"]),
        node1_type=str(value["node1_type"]),
        node1_idx=int(value["node1_idx"]),
        node2_type=str(value["node2_type"]),
        node2_idx=int(value["node2_idx"]),
        capacity_dtype=str(value["capacity_dtype"]),
        capacity_hex=str(value["capacity_hex"]),
    )
    result.capacity()
    return result


def oracle_safety_step_from_primitive(value: Any) -> OracleSafetyStepRecord:
    if not isinstance(value, Mapping) or set(value) != _ORACLE_SAFETY_ALLOWED_STEP_KEYS:
        raise G0RealizationError("oracle safety step primitive schema drifted")
    connections = value["connections"]
    if not isinstance(connections, Mapping) or set(connections) != {
        "user",
        "uav",
        "uav_bs",
    }:
        raise G0RealizationError("oracle native connections primitive drifted")
    routing = value["routing_paths"]
    if not isinstance(routing, list):
        raise G0RealizationError("oracle routing primitive is not ordered")
    return OracleSafetyStepRecord(
        physical_step=int(value["physical_step"]),
        candidate_id=str(value["candidate_id"]),
        current_uav_positions=_native_array_from_primitive(
            value["current_uav_positions"]
        ),
        current_uav_velocities=_native_array_from_primitive(
            value["current_uav_velocities"]
        ),
        current_service_mask=_native_array_from_primitive(
            value["current_service_mask"]
        ),
        pre_action_context=_validate_pre_action_context_primitive(
            value["pre_action_context"]
        ),
        executed_service_mask=_native_array_from_primitive(
            value["executed_service_mask"]
        ),
        common_transducer_evidence=_validate_common_transducer_evidence_primitive(
            value["common_transducer_evidence"],
            recompute=False,
        ),
        raw_candidate_action=_native_array_from_primitive(
            value["raw_candidate_action"]
        ),
        shared_channel_draw_coordinate=tuple(
            _draw_coordinate_from_primitive(item)
            for item in value["shared_channel_draw_coordinate"]
        ),
        shared_channel_draw_block=tuple(
            str(item) for item in value["shared_channel_draw_block"]
        ),
        connections={
            str(key): _native_array_from_primitive(item)
            for key, item in connections.items()
        },
        routing_paths=tuple(_json_safe(item) for item in routing),
        exact_link_capacity_values_read_by_the_real_guard=tuple(
            _guard_read_from_primitive(item)
            for item in value[
                "exact_link_capacity_values_read_by_the_real_guard"
            ]
        ),
        real_guard_intervention_or_violation_output=_json_safe(
            value["real_guard_intervention_or_violation_output"]
        ),
        guarded_executed_action=_native_array_from_primitive(
            value["guarded_executed_action"]
        ),
        next_uav_positions=_native_array_from_primitive(
            value["next_uav_positions"]
        ),
        next_uav_velocities=_native_array_from_primitive(
            value["next_uav_velocities"]
        ),
    )


def oracle_safety_trace_from_primitive(value: Any) -> OracleCandidateSafetyTrace:
    expected = {
        "candidate_id",
        "target_schedule_sha256",
        "common_prestate_sha256",
        "steps",
        "hard_violation_count",
        "gate_arrival_time",
        "gate_arrival_error",
        "event_window_tracking_error",
        "path_length",
        "stage_coordinates",
        "trace_sha256",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        raise G0RealizationError("oracle candidate trace schema drifted")
    return OracleCandidateSafetyTrace(
        candidate_id=str(value["candidate_id"]),
        target_schedule_sha256=str(value["target_schedule_sha256"]),
        common_prestate_sha256=str(value["common_prestate_sha256"]),
        steps=tuple(
            oracle_safety_step_from_primitive(item) for item in value["steps"]
        ),
        hard_violation_count=int(value["hard_violation_count"]),
        gate_arrival_time=int(value["gate_arrival_time"]),
        gate_arrival_error=float(value["gate_arrival_error"]),
        event_window_tracking_error=float(value["event_window_tracking_error"]),
        path_length=float(value["path_length"]),
        stage_coordinates=tuple(float(item) for item in value["stage_coordinates"]),
        trace_sha256=str(value["trace_sha256"]),
    )


def oracle_behavioral_execution_from_primitive(
    value: Any,
) -> OracleBehavioralExecution:
    expected = {
        "selected_candidate_id",
        "return_ready_step",
        "steps",
        "target_schedule",
        "pre_action_weakest_service",
        "trace_sha256",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        raise G0RealizationError("oracle behavioral execution schema drifted")
    return_ready = value["return_ready_step"]
    if return_ready is not None:
        return_ready = int(return_ready)
        if not 0 <= return_ready < PHYSICAL_HORIZON:
            raise G0RealizationError("RETURN_READY step is outside H")
    result = OracleBehavioralExecution(
        selected_candidate_id=str(value["selected_candidate_id"]),
        return_ready_step=return_ready,
        steps=tuple(
            oracle_safety_step_from_primitive(item) for item in value["steps"]
        ),
        target_schedule=_native_array_from_primitive(value["target_schedule"]),
        pre_action_weakest_service=_native_array_from_primitive(
            value["pre_action_weakest_service"]
        ),
        trace_sha256=str(value["trace_sha256"]),
    )
    targets = result.target_schedule.array()
    weakest = result.pre_action_weakest_service.array()
    if targets.shape != (PHYSICAL_HORIZON, PHYSICAL_UAVS, 3):
        raise G0RealizationError("behavioral target schedule shape drifted")
    if weakest.shape != (PHYSICAL_HORIZON,) or not np.isfinite(weakest).all():
        raise G0RealizationError("behavioral pre-action service evidence drifted")
    expected_digest = sha256_json(
        {
            "selected_candidate_id": result.selected_candidate_id,
            "return_ready_step": result.return_ready_step,
            "steps": [step.to_primitive() for step in result.steps],
            "target_schedule": result.target_schedule.to_primitive(),
            "pre_action_weakest_service": (
                result.pre_action_weakest_service.to_primitive()
            ),
        }
    )
    if result.trace_sha256 != expected_digest:
        raise G0RealizationError("behavioral execution digest drifted")
    return result


def oracle_safety_ledger_from_primitive(value: Any) -> OracleSafetyLedger:
    expected = {
        "source_sha256",
        "common_prestate",
        "common_prestate_sha256",
        "candidate_prestate_sha256",
        "channel_draw_schema",
        "shared_channel_draw_blocks",
        "candidates",
        "selected_candidate_id",
        "selected_rank",
        "shared_action_method_sha256",
        "registration_order",
        "K_search",
        "physical_horizon",
        "hypothetical_candidate_transitions",
        "content_sha256",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        raise G0RealizationError("oracle safety ledger primitive schema drifted")
    if (
        int(value["K_search"]) != K_SEARCH
        or int(value["physical_horizon"]) != PHYSICAL_HORIZON
        or int(value["hypothetical_candidate_transitions"])
        > 2 * PHYSICAL_HORIZON
    ):
        raise G0RealizationError("oracle safety ledger complexity inventory drifted")
    if list(value["registration_order"]) != [
        "freeze_common_prestate",
        "freeze_channel_draw_schema",
        "materialize_shared_channel_tape",
        "advance_each_candidate_once",
        "seal_both_candidate_traces",
        "rank_sealed_trace_keys_only",
        "behavioral_service_after_selection",
    ]:
        raise G0RealizationError("oracle safety registration order drifted")
    candidates = tuple(
        oracle_safety_trace_from_primitive(item) for item in value["candidates"]
    )
    if len(candidates) != 2:
        raise G0RealizationError("oracle safety ledger requires exactly two candidates")
    return OracleSafetyLedger(
        source_sha256=str(value["source_sha256"]),
        common_prestate=_json_safe(value["common_prestate"]),
        common_prestate_sha256=str(value["common_prestate_sha256"]),
        candidate_prestate_sha256=tuple(
            str(item) for item in value["candidate_prestate_sha256"]
        ),
        channel_draw_schema=tuple(
            _draw_coordinate_from_primitive(item)
            for item in value["channel_draw_schema"]
        ),
        shared_channel_draw_blocks=tuple(
            str(item) for item in value["shared_channel_draw_blocks"]
        ),
        candidates=(candidates[0], candidates[1]),
        selected_candidate_id=str(value["selected_candidate_id"]),
        selected_rank=tuple(float(item) for item in value["selected_rank"]),
        shared_action_method_sha256={
            str(key): str(item)
            for key, item in value["shared_action_method_sha256"].items()
        },
        content_sha256=str(value["content_sha256"]),
    )


def _validate_pre_action_context_primitive(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _PRE_ACTION_CONTEXT_KEYS:
        raise G0RealizationError("branchpoint pre-action context schema drifted")
    physical_step = int(value["physical_step"])
    if not 0 <= physical_step < PHYSICAL_HORIZON:
        raise G0RealizationError("branchpoint physical step is outside H")

    lifecycle_value = value["lifecycle_owner_to_internal"]
    if not isinstance(lifecycle_value, list) or len(lifecycle_value) != PHYSICAL_UAVS:
        raise G0RealizationError("branchpoint lifecycle inventory is incomplete")
    lifecycle: list[dict[str, Any]] = []
    for item in lifecycle_value:
        if not isinstance(item, Mapping) or set(item) != _LIFECYCLE_CONTEXT_ROW_KEYS:
            raise G0RealizationError("branchpoint lifecycle row schema drifted")
        label = TargetLabel.parse(str(item["owner_target"]))
        row = {
            "handle": str(item["handle"]),
            "epoch": int(item["epoch"]),
            "internal_row": int(item["internal_row"]),
            "owner_target": label.key,
        }
        if not row["handle"] or row["epoch"] not in (0, 1):
            raise G0RealizationError("branchpoint lifecycle identity is invalid")
        lifecycle.append(row)
    if (
        [row["internal_row"] for row in lifecycle] != list(range(PHYSICAL_UAVS))
        or len({row["handle"] for row in lifecycle}) != PHYSICAL_UAVS
        or len({row["owner_target"] for row in lifecycle}) != PHYSICAL_UAVS
    ):
        raise G0RealizationError("branchpoint lifecycle ordering is ambiguous")

    service_active_value = value["service_active_mask"]
    if (
        not isinstance(service_active_value, list)
        or len(service_active_value) != PHYSICAL_UAVS
        or any(type(item) is not bool for item in service_active_value)
    ):
        raise G0RealizationError("branchpoint service-active mask is incomplete")
    service_active_mask = [bool(item) for item in service_active_value]

    event_owner_handle = str(value["event_owner_handle"])
    event_owner_epoch = int(value["event_owner_epoch"])
    selected_reserve_handle = str(value["selected_reserve_handle"])
    selected_target = TargetLabel.parse(
        str(value["selected_reserve_original_target"])
    )
    if selected_target.kind is not TargetKind.STAGE:
        raise G0RealizationError("branchpoint selected owner is not a reserve")
    by_handle = {row["handle"]: row for row in lifecycle}
    if (
        event_owner_handle not in by_handle
        or by_handle[event_owner_handle]["epoch"] != event_owner_epoch
        or selected_reserve_handle not in by_handle
        or by_handle[selected_reserve_handle]["owner_target"] != selected_target.key
        or selected_reserve_handle == event_owner_handle
    ):
        raise G0RealizationError("branchpoint owner/epoch identity is inconsistent")

    survivor_value = value["survivor_ownership"]
    if not isinstance(survivor_value, list) or len(survivor_value) != 6:
        raise G0RealizationError("branchpoint survivor-controller state is incomplete")
    survivor: list[dict[str, Any]] = []
    for item in survivor_value:
        if not isinstance(item, Mapping) or set(item) != _LIFECYCLE_CONTEXT_ROW_KEYS:
            raise G0RealizationError("branchpoint survivor row schema drifted")
        canonical = {
            "handle": str(item["handle"]),
            "epoch": int(item["epoch"]),
            "internal_row": int(item["internal_row"]),
            "owner_target": TargetLabel.parse(str(item["owner_target"])).key,
        }
        if canonical not in lifecycle:
            raise G0RealizationError("branchpoint survivor is not lifecycle-owned")
        survivor.append(canonical)
    expected_survivors = [
        row
        for row in lifecycle
        if row["handle"] not in {event_owner_handle, selected_reserve_handle}
    ]
    if survivor != expected_survivors:
        raise G0RealizationError("branchpoint survivor-controller ordering drifted")
    if value["survivor_controller_rng_owners"] != []:
        raise G0RealizationError("branchpoint controller unexpectedly owns RNG")

    rng_value = value["non_controller_rng_states"]
    if (
        not isinstance(rng_value, Mapping)
        or not rng_value
        or list(rng_value) != sorted(str(key) for key in rng_value)
    ):
        raise G0RealizationError("branchpoint non-controller RNG inventory drifted")
    rng_states: dict[str, dict[str, str]] = {}
    for name, item in rng_value.items():
        expected_binding_keys = {"state_source", "state_sha256"}
        if not isinstance(item, Mapping) or set(item) != expected_binding_keys:
            raise G0RealizationError("branchpoint RNG binding schema drifted")
        state_source = str(item["state_source"])
        state_sha256 = str(item["state_sha256"])
        if (
            state_source != f"common_prestate.rng_states/{name}"
            or len(state_sha256) != 64
            or any(character not in "0123456789abcdef" for character in state_sha256)
        ):
            raise G0RealizationError("branchpoint RNG binding is invalid")
        rng_states[str(name)] = {
            "state_source": state_source,
            "state_sha256": state_sha256,
        }
    if "_channel_rng" not in rng_states:
        raise G0RealizationError("branchpoint omitted the registered channel RNG")

    cursor = value["channel_tape_cursor"]
    if (
        not isinstance(cursor, Mapping)
        or set(cursor) != {"draw_ordinal", "coordinate_count", "block_count"}
        or any(int(cursor[key]) != 0 for key in cursor)
    ):
        raise G0RealizationError("branchpoint channel-tape cursor is not empty")
    return {
        "physical_step": physical_step,
        "lifecycle_owner_to_internal": lifecycle,
        "service_active_mask": service_active_mask,
        "event_owner_handle": event_owner_handle,
        "event_owner_epoch": event_owner_epoch,
        "selected_reserve_handle": selected_reserve_handle,
        "selected_reserve_original_target": selected_target.key,
        "survivor_ownership": survivor,
        "survivor_controller_rng_owners": [],
        "non_controller_rng_states": rng_states,
        "channel_tape_cursor": {
            "draw_ordinal": 0,
            "coordinate_count": 0,
            "block_count": 0,
        },
    }


def _validate_common_transducer_evidence_primitive(
    value: Any,
    *,
    recompute: bool = True,
) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _COMMON_TRANSDUCER_EVIDENCE_KEYS:
        raise G0RealizationError("common transducer evidence schema drifted")
    positions = _native_array_from_primitive(value["physical_positions"])
    targets = _native_array_from_primitive(value["target_positions"])
    active = _native_array_from_primitive(value["active_mask"])
    raw = _native_array_from_primitive(value["raw_action"])
    position_array = positions.array()
    target_array = targets.array()
    active_array = active.array()
    raw_array = raw.array()
    if (
        str(value["transducer_source_sha256"]) != common_tracker_source_digest()
        or str(value["row_order"]) != "target_owned_internal"
        or position_array.shape != (PHYSICAL_UAVS, 3)
        or position_array.dtype != np.dtype(np.float64)
        or target_array.shape != (PHYSICAL_UAVS, 3)
        or target_array.dtype != np.dtype(np.float64)
        or active_array.shape != (PHYSICAL_UAVS,)
        or active_array.dtype != np.dtype(np.bool_)
        or raw_array.shape != (PHYSICAL_UAVS, ACTION_DIM)
        or raw_array.dtype != np.dtype(np.float32)
        or not np.isfinite(position_array).all()
        or not np.isfinite(target_array).all()
        or not np.isfinite(raw_array).all()
        or float(value["max_speed"]) != 30.0
        or float(value["max_vertical_speed"]) != 5.0
        or float(value["time_step"]) != 1.0
    ):
        raise G0RealizationError("common transducer primitive is not frozen G1")
    if recompute:
        expected_raw = g1_common_target_actions(
            physical_positions=position_array,
            target_positions=target_array,
            active_mask=active_array,
            max_speed=30.0,
            max_vertical_speed=5.0,
            time_step=1.0,
        )
        if not np.array_equal(raw_array, expected_raw):
            raise G0RealizationError(
                "common transducer output is not independently recomputed"
            )
    return {
        "transducer_source_sha256": common_tracker_source_digest(),
        "row_order": "target_owned_internal",
        "physical_positions": positions.to_primitive(),
        "target_positions": targets.to_primitive(),
        "active_mask": active.to_primitive(),
        "raw_action": raw.to_primitive(),
        "max_speed": 30.0,
        "max_vertical_speed": 5.0,
        "time_step": 1.0,
    }
