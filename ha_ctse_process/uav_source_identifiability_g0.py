"""Frozen source and evidence core for UAV source-identifiability G0.

G0 is deliberately not a learning experiment.  It instantiates one paired
Scenario-7/S1 source, three deterministic controls, exact episode metrics and
the registered first-match analysis.  No model, optimizer, checkpoint or
formal-execution authority is defined here.

Physical slot numbers are storage coordinates only.  Target ownership and
controller decisions use opaque lifecycle handles plus anonymous physical
content; a slot number is never a decision or tie-breaking feature.
"""

from __future__ import annotations

import hashlib
import math
from typing import Any, Mapping, Sequence

import numpy as np

from ha_ctse_process import uav_g0_controllers as controllers, uav_g0_environment as g0_environment, uav_g0_oracle_evidence as oracle_evidence
from envs.pettingzoo.relay.energy_aware import UAVEnergyAwareRelayEnv
from ha_ctse_process.uav_episode_schema import (
    ACTION_DIM,
    GROUND_USERS,
    PHYSICAL_HORIZON,
    PHYSICAL_UAVS,
    SERVICE_TARGET,
    Cell,
    Control,
    EpisodeMetrics,
    EpisodeRunEvidence,
    G0RealizationError,
    LifecycleBoundaryEvent,
)
from ha_ctse_process.uav_g0_geometry import (
    FIXED_ALTITUDE_M,
    GROUND_BASE_STATIONS,
    G0EpisodeSource,
    G0EventLedger,
    TARGET_LABELS,
    TargetKind,
    TargetLabel,
    _finite_array,
    actions_toward_targets,
    geometry_support_certificate,
    g1_common_target_actions,
    sha256_json,
)
from ha_ctse_process.uav_g0_statistics import (
    EPISODE_IDS,
    INVALID_BRANCH,
    EpisodeValidityRecord,
    _build_analysis_from_reconstructed_rows,
    compute_episode_metrics,
    weakest_hotspot_service,
)


SCHEMA_VERSION = 1
DESIGN_ROUND = "20260730_uav_g0_executable_contract_addendum_v2"
DESIGN_PACKAGE_STAGE_COMMIT = "8d171a1b63ff403f0cec7b0539c3894a0f4ba5cc"
DESIGN_ARCHIVE_COMMIT = "9c1566e1c6adefcd500facb1bb50d5a7428eae9c"
DESIGN_DISPOSITION = (
    "G0_EXECUTABLE_CONTRACT_ADDENDUM_V2_DISPOSITION=READY_FOR_CODE_CONTRACT"
)
EVIDENCE_SOURCE_COMMIT = "45385faa81197bdb90c14f849eee17b999ca2f57"
ORACLE_SAFETY_CLARIFICATION_ROUND = (
    "20260730_uav_g0_oracle_safety_information_contract_clarification"
)
ORACLE_SAFETY_PACKAGE_STAGE_COMMIT = (
    "a6c4e5be7119280006efc8455437671b8cf0c75a"
)
ORACLE_SAFETY_ARCHIVE_COMMIT = "14f1303d2aabc5282c9c2e4e7764c13e58c1b515"
ORACLE_SAFETY_DISPOSITION = (
    "G0_ORACLE_SAFETY_INFORMATION_DISPOSITION=REGISTERED_LEDGER_ALLOWED"
)
REPLAY_CLARIFICATION_ROUND = (
    "20260730_uav_g0_behavioral_replay_contract_clarification"
)
REPLAY_PACKAGE_STAGE_COMMIT = "1ba1f95bbf551ad68e5c814b0203e720534b82a6"
REPLAY_ARCHIVE_COMMIT = "9f08c12cdfe433bb691a640ef8a9ce2f5792608e"
REPLAY_DISPOSITION = (
    "G0_REPLAY_CONTRACT_DISPOSITION=POST_RETURN_READY_REPLAY_RULE"
)
RETURN_READY_STEP_CLARIFICATION_ROUND = (
    "20260730_uav_g0_return_ready_step_contract_clarification"
)
RETURN_READY_STEP_PACKAGE_STAGE_COMMIT = (
    "612210d2fabb945361d079a9fad1102d00a3255d"
)
RETURN_READY_STEP_ARCHIVE_COMMIT = "7e1876c1f552aac0b10af24e15bf2e4cc5c0b03f"
RETURN_READY_STEP_DISPOSITION = (
    "G0_RETURN_READY_STEP_DISPOSITION=KEEP_CAUSAL_R_273"
)
ACCEPTED_G1_SOURCE_COMMIT = "2f8e47c16f0563ed1144e370fff787c22508a14d"
ACCEPTED_G1_TRACKER_SOURCE_SHA256 = (
    "50dd4f8728739e5ea643791339d0ce7072c40d6517527040f0b63f485c70558d"
)
ACCEPTED_G1_SHARED_ACTION_METHOD_SHA256 = {
    "prepare_energy_actions": "f59c8e9071d205fe71035b74af2f970b90f9fa6a720aa5669b7f11c73fb37307",
    "movement_velocity": "798dbeeee09c39740af169bb08da16c08072c5f45c22ea47e6f2e357a286c3c2",
    "base_action": "c4dea617374fbc3599a701ec8e8810a7c1cc1e7ba70cf81e2b48b95767e84a9b",
    "scenario7_backhaul_guard": "9d32b03489d9b08cf2df2928b7f2fe9823b855621b538f9221110f98c3a4d84b",
    "base_backhaul_guard": "e3edac5d4ad6d1839204d6ea042e2768ce3df90085c8535aa822cc3bb9c14df8",
}

FORMAL_EXECUTION_AUTHORIZED = False
LEARNING_ENABLED = False
OPTIMIZER_ENABLED = False
CHECKPOINT_ENABLED = False

_ORACLE_SAFETY_FORBIDDEN_TOKENS = (
    "delivered",
    "reward",
    "qos",
    "hotspot",
    "a_control",
    "b_access",
    "c_cat",
    "delta_",
    "j_event",
    "q_ordinary",
    "m_event",
)

def oracle_safety_method_digests() -> dict[str, str]:
    """Bind every unchanged result-bearing native safety transition method."""

    values = dict(oracle_evidence.shared_action_method_digests())
    values.update(
        {
            "g0_channel_update": oracle_evidence._callable_source_digest(
                g0_environment.UAVSourceIdentifiabilityEnv._update_channel_state
            ),
            "scenario7_connection_update": oracle_evidence._callable_source_digest(
                UAVEnergyAwareRelayEnv._update_uav_connections
            ),
            "native_routing_update": oracle_evidence._callable_source_digest(
                UAVEnergyAwareRelayEnv.__mro__[1]._compute_routing_paths
            ),
            "scenario7_link_capacity": oracle_evidence._callable_source_digest(
                UAVEnergyAwareRelayEnv._get_link_capacity
            ),
            "g0_guard_capacity_capture": oracle_evidence._callable_source_digest(
                g0_environment.UAVSourceIdentifiabilityEnv._get_link_capacity
            ),
            "g0_safety_only_transition": oracle_evidence._callable_source_digest(
                g0_environment.UAVSourceIdentifiabilityEnv.step_oracle_safety
            ),
        }
    )
    return values


def qualify_common_tracker(
    *,
    episode_source: G0EpisodeSource,
    physical_positions: np.ndarray,
    target_positions: np.ndarray,
    active_mask: np.ndarray,
    max_speed: float,
    max_vertical_speed: float,
    time_step: float,
    permutation: Sequence[int],
) -> dict[str, Any]:
    """Reconstruct determinism, shared correction and permutation evidence."""

    positions = _finite_array(
        physical_positions, (PHYSICAL_UAVS, 3), label="tracker positions"
    )
    targets = _finite_array(target_positions, (PHYSICAL_UAVS, 3), label="tracker targets")
    mask = np.asarray(active_mask, dtype=np.bool_)
    order = np.asarray(tuple(int(v) for v in permutation), dtype=np.int64)
    if mask.shape != (PHYSICAL_UAVS,) or sorted(order.tolist()) != list(range(PHYSICAL_UAVS)):
        raise G0RealizationError("tracker qualification mask/permutation mismatch")
    keyword = {
        "max_speed": max_speed,
        "max_vertical_speed": max_vertical_speed,
        "time_step": time_step,
    }
    raw_left = g1_common_target_actions(
        physical_positions=positions,
        target_positions=targets,
        active_mask=mask,
        **keyword,
    )
    raw_right = g1_common_target_actions(
        physical_positions=positions.copy(),
        target_positions=targets.copy(),
        active_mask=mask.copy(),
        **keyword,
    )
    if oracle_evidence.common_tracker_source_digest() != ACCEPTED_G1_TRACKER_SOURCE_SHA256:
        raise G0RealizationError("common tracker source differs from accepted G1")

    method_digests = oracle_evidence.shared_action_method_digests()
    method_identity = method_digests == ACCEPTED_G1_SHARED_ACTION_METHOD_SHA256

    environment = g0_environment.UAVSourceIdentifiabilityEnv(episode_source, Cell.NO_EVENT)
    try:
        environment.reset()

        def actual_shared_projection(
            actions: np.ndarray, projection_mask: np.ndarray
        ) -> np.ndarray:
            environment._service_active_mask = np.asarray(
                projection_mask, dtype=np.bool_
            ).copy()
            action_dict = {
                agent: np.asarray(actions[row], dtype=np.float32).copy()
                for row, agent in enumerate(environment.possible_agents)
            }
            adjusted, _commanded = environment._prepare_energy_actions(action_dict)
            return np.stack(
                [
                    np.asarray(adjusted[agent], dtype=np.float32)
                    for agent in environment.possible_agents
                ]
            )

        executed_left = actual_shared_projection(raw_left.copy(), mask)
        executed_right = actual_shared_projection(raw_right.copy(), mask.copy())
    finally:
        environment.close()
    raw_permuted = g1_common_target_actions(
        physical_positions=positions[order],
        target_positions=targets[order],
        active_mask=mask[order],
        **keyword,
    )
    unpermuted = np.empty_like(raw_permuted)
    unpermuted[order] = raw_permuted
    environment = g0_environment.UAVSourceIdentifiabilityEnv(episode_source, Cell.NO_EVENT)
    try:
        environment.reset()
        environment._service_active_mask = mask[order].copy()
        adjusted, _commanded = environment._prepare_energy_actions(
            {
                agent: raw_permuted[row].copy()
                for row, agent in enumerate(environment.possible_agents)
            }
        )
        executed_permuted = np.stack(
            [
                np.asarray(adjusted[agent], dtype=np.float32)
                for agent in environment.possible_agents
            ]
        )
    finally:
        environment.close()
    executed_unpermuted = np.empty_like(executed_permuted)
    executed_unpermuted[order] = executed_permuted
    raw_equal = np.array_equal(raw_left, raw_right)
    executed_equal = np.array_equal(executed_left, executed_right)
    permutation_equal = np.array_equal(raw_left, unpermuted)
    executed_permutation_equal = np.array_equal(executed_left, executed_unpermuted)
    support_valid = bool(
        np.isfinite(raw_left).all()
        and np.all(np.abs(raw_left) <= 1.0)
        and np.array_equal(raw_left[~mask], np.zeros_like(raw_left[~mask]))
    )
    executed_support_valid = bool(
        executed_left.shape == (PHYSICAL_UAVS, 3)
        and np.isfinite(executed_left).all()
        and np.all(np.abs(executed_left) <= 1.0)
        and np.array_equal(
            executed_left[~mask], np.zeros_like(executed_left[~mask])
        )
    )
    passed = bool(
        raw_equal
        and executed_equal
        and permutation_equal
        and executed_permutation_equal
        and support_valid
        and executed_support_valid
        and method_identity
    )
    return {
        "accepted_g1_source_commit": ACCEPTED_G1_SOURCE_COMMIT,
        "tracker_symbol": "actions_toward_targets",
        "tracker_source_sha256": oracle_evidence.common_tracker_source_digest(),
        "accepted_tracker_source_sha256": ACCEPTED_G1_TRACKER_SOURCE_SHA256,
        "shared_action_method_sha256": method_digests,
        "shared_action_method_identity": method_identity,
        "same_state_target_raw_actions_bitwise_equal": raw_equal,
        "same_state_target_executed_actions_bitwise_equal": executed_equal,
        "permutation_equivariant": permutation_equal,
        "executed_permutation_equivariant": executed_permutation_equal,
        "action_support_valid": support_valid,
        "executed_action_support_valid": executed_support_valid,
        "inactive_action_rows_zero": bool(
            np.array_equal(raw_left[~mask], np.zeros_like(raw_left[~mask]))
        ),
        "controller_specific_branch_count": 0,
        "controller_specific_tolerance_count": 0,
        "passed": passed,
    }




























def _scenario7_nominal_position_step(
    positions: np.ndarray,
    targets: np.ndarray,
    active_mask: np.ndarray,
    *,
    max_speed: float,
    max_vertical_speed: float,
    time_step: float,
) -> tuple[np.ndarray, np.ndarray]:
    actions = g1_common_target_actions(
        physical_positions=positions,
        target_positions=targets,
        active_mask=active_mask,
        max_speed=max_speed,
        max_vertical_speed=max_vertical_speed,
        time_step=time_step,
    )
    updated = np.asarray(positions, dtype=np.float64).copy()
    for row in np.flatnonzero(active_mask):
        horizontal = np.asarray(actions[row, :2], dtype=np.float64)
        norm = float(np.linalg.norm(horizontal))
        if norm > 1e-8:
            velocity_xy = horizontal / norm * min(norm, 1.0) * float(max_speed)
        else:
            velocity_xy = np.zeros(2, dtype=np.float64)
        velocity_z = float(actions[row, 2]) * float(max_vertical_speed)
        updated[row, :2] += velocity_xy * float(time_step)
        updated[row, 2] += velocity_z * float(time_step)
    return updated, actions


def _oracle_schedule_label(
    *,
    step: int,
    reserve: TargetLabel,
    failed: TargetLabel,
    latest_departure: int,
    event: G0EventLedger,
) -> tuple[str, np.ndarray]:
    if step < latest_departure:
        return "stage", np.asarray((0.0, 0.0))  # replaced by caller
    if step < event.onset:
        return "gate", np.asarray((0.0, 0.0))
    if step < event.rejoin:
        return "primary", np.asarray((0.0, 0.0))
    # Candidate generation is pre-behavior and cannot read future service.
    # It therefore keeps the reserve at gate; the conditional online schedule
    # transitions to stage only after RETURN_READY is observed.
    return "gate_until_return_ready", np.asarray((0.0, 0.0))


def _minimum_tracker_travel_steps(
    start: np.ndarray,
    target: np.ndarray,
    *,
    max_speed: float,
    max_vertical_speed: float,
    time_step: float,
) -> int:
    """Exact common-transducer travel count, used only to place departure."""

    positions = np.repeat(np.asarray(start, dtype=np.float64)[None, :], PHYSICAL_UAVS, axis=0)
    targets = np.repeat(np.asarray(target, dtype=np.float64)[None, :], PHYSICAL_UAVS, axis=0)
    active = np.ones(PHYSICAL_UAVS, dtype=np.bool_)
    for count in range(PHYSICAL_HORIZON + 1):
        if np.array_equal(positions[0], targets[0]):
            return count
        positions, _actions = _scenario7_nominal_position_step(
            positions,
            targets,
            active,
            max_speed=max_speed,
            max_vertical_speed=max_vertical_speed,
            time_step=time_step,
        )
    raise G0RealizationError("common tracker cannot reach oracle gate within H")


def _is_exact_gate_arrival(
    position: np.ndarray,
    gate: np.ndarray,
    *,
    physical_step: int,
    latest_departure: int,
    event_onset: int,
) -> bool:
    """Exact pre-action oracle arrival predicate; no tolerance is admissible."""

    return bool(
        int(latest_departure) <= int(physical_step) <= int(event_onset)
        and np.array_equal(
            np.asarray(position, dtype=np.float64),
            np.asarray(gate, dtype=np.float64),
        )
    )


def certify_oracle_candidates(
    source: G0EpisodeSource,
    *,
    max_speed: float = 30.0,
    max_vertical_speed: float = 5.0,
    time_step: float = 1.0,
) -> oracle_evidence.OracleQualificationCertificate:
    """Evaluate exactly two sealed, shared-ledger, real-guard candidates."""

    if not (
        float(max_speed) == 30.0
        and float(max_vertical_speed) == 5.0
        and float(time_step) == 1.0
    ):
        raise G0RealizationError("oracle safety ledger requires frozen S7-S1 dynamics")
    return oracle_qualification_from_safety_ledger(
        source, build_oracle_safety_ledger(source)
    )



def validate_oracle_qualification(
    source: G0EpisodeSource,
    certificate: oracle_evidence.OracleQualificationCertificate,
    *,
    safety_ledger: oracle_evidence.OracleSafetyLedger | None = None,
    max_speed: float = 30.0,
    max_vertical_speed: float = 5.0,
    time_step: float = 1.0,
) -> None:
    expected = (
        oracle_qualification_from_safety_ledger(source, safety_ledger)
        if safety_ledger is not None
        else certify_oracle_candidates(
            source,
            max_speed=max_speed,
            max_vertical_speed=max_vertical_speed,
            time_step=time_step,
        )
    )
    if (
        certificate.to_primitive() != expected.to_primitive()
        or not certificate.passed
    ):
        raise G0RealizationError("oracle qualification is missing, forged, or failed")


def _validate_oracle_qualification_from_context(
    certificate: oracle_evidence.OracleQualificationCertificate,
    context: oracle_evidence._ValidatedOracleSafetyContext,
) -> None:
    expected = _oracle_qualification_from_validated_context(context)
    if (
        certificate.to_primitive() != expected.to_primitive()
        or not certificate.passed
    ):
        raise G0RealizationError("oracle qualification is missing, forged, or failed")


def _oracle_candidate_trace(
    source: G0EpisodeSource,
    reserve: TargetLabel,
) -> tuple[oracle_evidence.OracleCandidateSafetyTrace, dict[str, Any]]:
    labels = TARGET_LABELS
    reserve_row = labels.index(reserve)
    owner_row = labels.index(source.event.owner_target)
    stage_xyz = np.concatenate(
        (source.geometry.coordinate(reserve), [FIXED_ALTITUDE_M])
    )
    gate_xyz = np.concatenate(
        (source.geometry.gate(source.event.owner_target), [FIXED_ALTITUDE_M])
    )
    primary_xyz = np.concatenate(
        (source.geometry.coordinate(source.event.owner_target), [FIXED_ALTITUDE_M])
    )
    travel_steps = _minimum_tracker_travel_steps(
        stage_xyz,
        gate_xyz,
        max_speed=30.0,
        max_vertical_speed=5.0,
        time_step=1.0,
    )
    latest_departure = int(source.event.onset) - int(travel_steps)
    if latest_departure < 0:
        raise G0RealizationError(
            "oracle latest departure is negative under exact gate travel"
        )
    env = g0_environment.UAVSourceIdentifiabilityEnv(source, Cell.EVENT)
    try:
        env.reset()
        prestate = _complete_oracle_prestate(env)
        prestate_sha256 = sha256_json(prestate)
        schedule_rows: list[list[list[float]]] = []
        records: list[oracle_evidence.OracleSafetyStepRecord] = []
        path_length = 0.0
        tracking_error = 0.0
        arrival: int | None = None
        arrival_error = math.inf
        hard_violations = 0
        for step in range(PHYSICAL_HORIZON):
            if int(env.current_step) != step:
                raise G0RealizationError("candidate safety physical-step order drifted")
            active = env._active_mask_for_step(step)
            targets = np.stack(
                [
                    np.concatenate(
                        (source.geometry.coordinate(label), [FIXED_ALTITUDE_M])
                    )
                    for label in labels
                ]
            )
            schedule_name, _unused = _oracle_schedule_label(
                step=step,
                reserve=reserve,
                failed=source.event.owner_target,
                latest_departure=latest_departure,
                event=source.event,
            )
            if schedule_name == "stage":
                targets[reserve_row] = stage_xyz
            elif schedule_name in {"gate", "gate_until_return_ready"}:
                targets[reserve_row] = gate_xyz
            elif schedule_name == "primary":
                targets[reserve_row] = primary_xyz
            else:
                raise G0RealizationError("unregistered oracle target schedule state")
            positions = np.asarray(env.uav_positions, dtype=np.float64).copy()
            ownership = {
                str(handle): TargetLabel.parse(owner_target)
                for handle, owner_target in zip(
                    env._handles, source.assignment.row_to_target
                )
            }
            pre_action_context = g0_environment._pre_action_context(
                env, ownership, reserve.key
            )
            if (
                arrival is None
                and _is_exact_gate_arrival(
                    positions[reserve_row],
                    gate_xyz,
                    physical_step=step,
                    latest_departure=latest_departure,
                    event_onset=source.event.onset,
                )
            ):
                arrival = step
                arrival_error = float(
                    np.linalg.norm(positions[reserve_row] - gate_xyz)
                )
            actions = g1_common_target_actions(
                physical_positions=positions,
                target_positions=targets,
                active_mask=active,
                max_speed=env.max_speed,
                max_vertical_speed=env.max_vertical_speed_mps,
                time_step=env.time_step,
            )
            transducer_evidence = _common_transducer_evidence(
                physical_positions=positions,
                target_positions=targets,
                active_mask=active,
                raw_action=actions,
            )
            record = env.step_oracle_safety(
                actions,
                candidate_id=reserve.key,
                ownership=ownership,
                pre_action_context=pre_action_context,
                common_transducer_evidence=transducer_evidence,
            )
            next_positions = record.next_uav_positions.array().astype(
                np.float64, copy=False
            )
            action_violation = bool(
                not np.isfinite(actions).all()
                or np.any(np.abs(actions) > 1.0)
                or not np.array_equal(
                    actions[:, 2], np.zeros(PHYSICAL_UAVS, dtype=actions.dtype)
                )
            )
            physical_violation = bool(
                np.any(next_positions[:, 0] < 0.0)
                or np.any(next_positions[:, 0] > source.geometry.map_width)
                or np.any(next_positions[:, 1] < 0.0)
                or np.any(next_positions[:, 1] > source.geometry.map_height)
                or not np.array_equal(
                    next_positions[:, 2],
                    np.full(PHYSICAL_UAVS, FIXED_ALTITUDE_M),
                )
            )
            # A real-guard intervention is the registered safety realization,
            # not itself a deviation from that realization.  A changed,
            # bypassed, or inconsistent guard is rejected by the independent
            # primitive validator rather than counted as a favorable trace.
            guard_violation = False
            hard_violations += int(
                action_violation or physical_violation or guard_violation
            )
            path_length += float(
                np.linalg.norm(
                    next_positions[reserve_row] - positions[reserve_row]
                )
            )
            if (
                source.event.onset <= step < source.event.rejoin
            ):
                tracking_error += float(
                    np.sum(
                        (next_positions[reserve_row, :2] - primary_xyz[:2]) ** 2
                    )
                )
            schedule_rows.append(targets.tolist())
            records.append(record)
        if arrival is None:
            arrival = PHYSICAL_HORIZON + 1
            arrival_error = float(
                np.linalg.norm(
                    records[-1].next_uav_positions.array()[reserve_row] - gate_xyz
                )
            )
        primitive_steps = [record.to_primitive() for record in records]
        trace_sha256 = sha256_json(primitive_steps)
        return (
            oracle_evidence.OracleCandidateSafetyTrace(
                candidate_id=reserve.key,
                target_schedule_sha256=sha256_json(schedule_rows),
                common_prestate_sha256=prestate_sha256,
                steps=tuple(records),
                hard_violation_count=int(hard_violations),
                gate_arrival_time=int(arrival),
                gate_arrival_error=float(arrival_error),
                event_window_tracking_error=float(tracking_error),
                path_length=float(path_length),
                stage_coordinates=tuple(float(value) for value in stage_xyz[:2]),
                trace_sha256=trace_sha256,
            ),
            prestate,
        )
    finally:
        env.close()


def _build_oracle_safety_ledger_with_context(
    source: G0EpisodeSource,
) -> tuple[oracle_evidence.OracleSafetyLedger, oracle_evidence._ValidatedOracleSafetyContext]:
    """Build and fully validate one immutable real-guard ledger."""

    reserves = tuple(
        label for label in TARGET_LABELS if label.kind is TargetKind.STAGE
    )
    if len(reserves) != oracle_evidence.K_SEARCH:
        raise G0RealizationError("oracle candidate inventory is not exactly two")
    first, first_prestate = _oracle_candidate_trace(source, reserves[0])
    second, second_prestate = _oracle_candidate_trace(source, reserves[1])
    first_prestate_sha256 = sha256_json(first_prestate)
    second_prestate_sha256 = sha256_json(second_prestate)
    if (
        first_prestate != second_prestate
        or first_prestate_sha256 != second_prestate_sha256
    ):
        raise G0RealizationError("oracle candidates did not start from a common prestate")
    selected = min((first, second), key=lambda candidate: candidate.rank)
    provisional = oracle_evidence.OracleSafetyLedger(
        source_sha256=source.to_primitive()["sha256"],
        common_prestate=first_prestate,
        common_prestate_sha256=first_prestate_sha256,
        candidate_prestate_sha256=(
            first_prestate_sha256,
            second_prestate_sha256,
        ),
        channel_draw_schema=(),
        shared_channel_draw_blocks=(),
        candidates=(first, second),
        selected_candidate_id=selected.candidate_id,
        selected_rank=selected.rank,
        shared_action_method_sha256=oracle_safety_method_digests(),
        content_sha256="",
    )
    ledger = oracle_evidence.OracleSafetyLedger(
        **{
            **provisional.__dict__,
            "content_sha256": sha256_json(
                provisional.to_primitive(include_digest=False)
            ),
        }
    )
    return ledger, _validated_oracle_safety_context(source, ledger)


def build_oracle_safety_ledger(source: G0EpisodeSource) -> oracle_evidence.OracleSafetyLedger:
    """Build the immutable two-candidate, service-blind real-guard ledger."""

    ledger, _context = _build_oracle_safety_ledger_with_context(source)
    return ledger


def _forbidden_oracle_safety_key(value: Any, path: str = "") -> str | None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            lowered = str(key).lower()
            if any(token in lowered for token in _ORACLE_SAFETY_FORBIDDEN_TOKENS):
                return f"{path}/{key}"
            found = _forbidden_oracle_safety_key(item, f"{path}/{key}")
            if found is not None:
                return found
    elif isinstance(value, (tuple, list)):
        for index, item in enumerate(value):
            found = _forbidden_oracle_safety_key(item, f"{path}/{index}")
            if found is not None:
                return found
    return None


def _validate_record_branchpoint_and_transducer(
    source: G0EpisodeSource,
    common_prestate: Mapping[str, Any],
    record: oracle_evidence.OracleSafetyStepRecord,
    *,
    selected_candidate_id: str,
    expected_target_positions: np.ndarray,
    expected_rng_state_bindings: Mapping[str, Any] | None = None,
    cell: Cell | str = Cell.EVENT,
) -> None:
    context = oracle_evidence._validate_pre_action_context_primitive(
        record.pre_action_context
    )
    expected_context = _expected_pre_action_context(
        source,
        common_prestate,
        physical_step=record.physical_step,
        selected_candidate_id=selected_candidate_id,
        rng_state_bindings=expected_rng_state_bindings,
        cell=cell,
    )
    if context != expected_context:
        raise G0RealizationError(
            "branchpoint lifecycle/RNG/channel evidence is not reconstructible"
        )
    current_mask = record.current_service_mask.array()
    executed_mask = record.executed_service_mask.array()
    context_mask = np.asarray(context["service_active_mask"], dtype=np.bool_)
    if (
        executed_mask.shape != (PHYSICAL_UAVS,)
        or executed_mask.dtype != np.dtype(np.bool_)
        or not np.array_equal(executed_mask, current_mask)
        or not np.array_equal(context_mask, current_mask)
    ):
        raise G0RealizationError("executed service-mask evidence drifted")
    transducer = oracle_evidence._validate_common_transducer_evidence_primitive(
        record.common_transducer_evidence
    )
    if (
        not np.array_equal(
            oracle_evidence._native_array_from_primitive(
                transducer["physical_positions"]
            ).array(),
            record.current_uav_positions.array(),
        )
        or not np.array_equal(
            oracle_evidence._native_array_from_primitive(
                transducer["target_positions"]
            ).array(),
            np.asarray(expected_target_positions, dtype=np.float64),
        )
        or not np.array_equal(
            oracle_evidence._native_array_from_primitive(transducer["active_mask"]).array(),
            executed_mask,
        )
        or not np.array_equal(
            oracle_evidence._native_array_from_primitive(transducer["raw_action"]).array(),
            record.raw_candidate_action.array(),
        )
    ):
        raise G0RealizationError(
            "target schedule is not bound to the common transducer"
        )


def _validate_oracle_guard_transition_bindings(
    source: G0EpisodeSource,
    candidates: Sequence[oracle_evidence.OracleCandidateSafetyTrace],
    common_prestate: Mapping[str, Any],
) -> None:
    """Reconstruct the native guard/network chain without advancing an env step."""

    for candidate in candidates:
        environment = g0_environment.UAVSourceIdentifiabilityEnv(source, Cell.EVENT)
        try:
            environment.reset()
            if _complete_oracle_prestate(environment) != common_prestate:
                raise G0RealizationError(
                    "oracle common prestate is not reconstructible from source reset"
                )
            for record in candidate.steps:
                current = record.current_uav_positions.array()
                service_mask = record.executed_service_mask.array()
                raw_action = record.raw_candidate_action.array()
                reconstructed_connections = {
                    "user": np.asarray(environment.connections),
                    "uav": np.asarray(environment.uav_connections),
                    "uav_bs": np.asarray(environment.uav_bs_connections),
                }
                sealed_routing = [dict(item) for item in record.routing_paths]
                if (
                    int(environment.current_step) != int(record.physical_step)
                    or not np.array_equal(environment.uav_positions, current)
                    or not np.array_equal(
                        environment.last_actual_velocities,
                        record.current_uav_velocities.array(),
                    )
                    or not np.array_equal(
                        environment._service_active_mask, service_mask
                    )
                    or not np.array_equal(
                        environment._service_active_mask,
                        record.current_service_mask.array(),
                    )
                ):
                    raise G0RealizationError(
                        "oracle record prestate is not bound to reconstructed native state"
                    )
                if any(
                    not np.array_equal(
                        reconstructed_connections[name],
                        record.connections[name].array(),
                    )
                    for name in ("user", "uav", "uav_bs")
                ):
                    raise G0RealizationError(
                        "oracle connection input is not bound to reconstructed native state"
                    )
                if oracle_evidence._routing_paths_primitive(environment.routing_paths) != sealed_routing:
                    raise G0RealizationError(
                        "oracle routing input is not bound to reconstructed native state"
                    )

                action_dict = {
                    agent: raw_action[row].copy()
                    for row, agent in enumerate(environment.possible_agents)
                    if service_mask[row]
                }
                adjusted_actions, _commanded_velocities = (
                    environment._prepare_energy_actions(action_dict)
                )
                environment.previous_routing_paths_snapshot = dict(
                    environment.routing_paths
                )
                environment.previous_connections_snapshot = (
                    environment.connections.copy()
                )
                environment._move_users()
                environment.backhaul_guard_checked_actions = 0
                environment.backhaul_guard_blocked_actions = 0
                environment._oracle_guard_capacity_reads = []
                environment._oracle_guarded_velocity_rows = np.zeros(
                    (PHYSICAL_UAVS, 3), dtype=np.float64
                )
                environment._oracle_guard_interventions = np.zeros(
                    PHYSICAL_UAVS, dtype=np.bool_
                )
                try:
                    for agent_idx, agent in enumerate(environment.agents):
                        action = np.asarray(
                            adjusted_actions[agent], dtype=np.float32
                        )
                        proposed_velocity = action * float(environment.max_speed)
                        guarded_velocity = np.asarray(
                            environment._apply_backhaul_action_guard(
                                agent_idx, proposed_velocity
                            ),
                            dtype=np.float64,
                        )
                        next_position = (
                            environment.uav_positions[agent_idx]
                            + guarded_velocity * float(environment.time_step)
                        )
                        next_position[0] = np.clip(
                            next_position[0], 0.0, environment.area_size
                        )
                        next_position[1] = np.clip(
                            next_position[1], 0.0, environment.area_size
                        )
                        next_position[2] = np.clip(
                            next_position[2], *environment.height_range
                        )
                        environment.uav_positions[agent_idx] = next_position
                    capacity_reads = tuple(environment._oracle_guard_capacity_reads)
                    guarded = np.asarray(
                        environment._oracle_guarded_velocity_rows,
                        dtype=np.float64,
                    ).copy()
                    interventions = np.asarray(
                        environment._oracle_guard_interventions,
                        dtype=np.bool_,
                    ).copy()
                finally:
                    environment._oracle_guard_capacity_reads = None
                    environment._oracle_guarded_velocity_rows = None
                    environment._oracle_guard_interventions = None

                expected_guard_output = {
                    "checked_actions": int(
                        environment.backhaul_guard_checked_actions
                    ),
                    "blocked_actions": int(
                        environment.backhaul_guard_blocked_actions
                    ),
                    "intervention_by_uav": interventions.tolist(),
                }
                reconstructed_capacity_reads = tuple(
                    item.to_primitive() for item in capacity_reads
                )
                sealed_capacity_reads = tuple(
                    item.to_primitive()
                    for item in record.exact_link_capacity_values_read_by_the_real_guard
                )
                if reconstructed_capacity_reads != sealed_capacity_reads:
                    mismatch_index = next(
                        (
                            index
                            for index, (reconstructed, sealed) in enumerate(
                                zip(reconstructed_capacity_reads, sealed_capacity_reads)
                            )
                            if reconstructed != sealed
                        ),
                        min(
                            len(reconstructed_capacity_reads),
                            len(sealed_capacity_reads),
                        ),
                    )
                    raise G0RealizationError(
                        "ordered real-guard capacity reads are not independently "
                        f"reconstructed at {candidate.candidate_id} step "
                        f"{record.physical_step} index {mismatch_index}; "
                        f"counts={len(reconstructed_capacity_reads)}/"
                        f"{len(sealed_capacity_reads)}; reconstructed="
                        f"{reconstructed_capacity_reads[mismatch_index] if mismatch_index < len(reconstructed_capacity_reads) else None}; "
                        f"sealed={sealed_capacity_reads[mismatch_index] if mismatch_index < len(sealed_capacity_reads) else None}"
                    )
                if (
                    expected_guard_output
                    != dict(record.real_guard_intervention_or_violation_output)
                    or not np.array_equal(
                        guarded, record.guarded_executed_action.array()
                    )
                ):
                    raise G0RealizationError(
                        "guarded action/output is not bound to isolated real-guard reconstruction"
                    )

                expected_next = np.asarray(
                    environment.uav_positions, dtype=np.float64
                ).copy()
                expected_velocity = (
                    expected_next - current
                ) / float(environment.time_step)
                if (
                    not np.array_equal(
                        expected_next, record.next_uav_positions.array()
                    )
                    or not np.array_equal(
                        expected_velocity, record.next_uav_velocities.array()
                    )
                ):
                    raise G0RealizationError(
                        "next transition is not bound to reconstructed guarded action"
                    )
                environment.last_actual_velocities = expected_velocity.copy()
                environment._update_channel_state()
                environment._update_uav_connections()
                if (
                    environment.routing_protocol == "hggr"
                    and environment.current_step
                    % environment.hggr_update_interval
                    == 0
                ):
                    environment.hop_map = environment._calculate_hop_map()
                if environment.current_step % environment.hggr_update_interval == 0:
                    environment._update_global_bs_cache()
                environment._compute_routing_paths()
                environment.current_step += 1
                environment._synchronize_service_mask(force=True)
        finally:
            environment.close()


def validate_oracle_safety_ledger(
    source: G0EpisodeSource,
    ledger: oracle_evidence.OracleSafetyLedger,
) -> oracle_evidence.OracleSafetyCertificate:
    """Reconstruct all admission facts from immutable primitive evidence."""

    if ledger.source_sha256 != source.to_primitive()["sha256"]:
        raise G0RealizationError("oracle safety ledger source binding failed")
    if ledger.content_sha256 != sha256_json(
        ledger.to_primitive(include_digest=False)
    ):
        raise G0RealizationError("oracle safety ledger content digest failed")
    if dict(ledger.shared_action_method_sha256) != oracle_safety_method_digests():
        raise G0RealizationError("oracle safety ledger did not use the real guard methods")
    if ledger.common_prestate_sha256 != sha256_json(ledger.common_prestate):
        raise G0RealizationError("common prestate digest failed")
    if ledger.candidate_prestate_sha256 != (
        ledger.common_prestate_sha256,
        ledger.common_prestate_sha256,
    ):
        raise G0RealizationError("candidate prestates are not byte-identical")
    channel_state = (
        ledger.common_prestate.get("rng_states", {}).get("_channel_rng")
    )
    expected_channel_state = g0_environment._random_state_primitive(
        g0_environment._namespace_random_state(source.geometry.episode_id, 3)
    )
    if channel_state != expected_channel_state:
        raise G0RealizationError("registered G1 channel RNG prestate failed")
    if ledger.channel_draw_schema != () or ledger.shared_channel_draw_blocks != ():
        raise G0RealizationError("deterministic inherited channel path must use empty tape")
    expected_ids = tuple(
        label.key for label in TARGET_LABELS if label.kind is TargetKind.STAGE
    )
    if tuple(candidate.candidate_id for candidate in ledger.candidates) != expected_ids:
        raise G0RealizationError("oracle ledger omitted or added a reserve candidate")
    common_rng_states = ledger.common_prestate.get("rng_states")
    if not isinstance(common_rng_states, Mapping):
        raise G0RealizationError("oracle common prestate omitted RNG states")
    expected_rng_state_bindings = g0_environment._rng_state_bindings(common_rng_states)
    previous_candidates: list[oracle_evidence.OracleCandidateSafetyTrace] = []
    for candidate in ledger.candidates:
        reserve = TargetLabel.parse(candidate.candidate_id)
        if reserve.kind is not TargetKind.STAGE:
            raise G0RealizationError("oracle candidate owner is not a reserve")
        stage_xyz = np.concatenate(
            (source.geometry.coordinate(reserve), [FIXED_ALTITUDE_M])
        )
        gate_xyz = np.concatenate(
            (source.geometry.gate(source.event.owner_target), [FIXED_ALTITUDE_M])
        )
        travel_steps = _minimum_tracker_travel_steps(
            stage_xyz,
            gate_xyz,
            max_speed=30.0,
            max_vertical_speed=5.0,
            time_step=1.0,
        )
        latest_departure = int(source.event.onset) - int(travel_steps)
        if latest_departure < 0:
            raise G0RealizationError(
                "oracle latest departure is negative under exact gate travel"
            )
        if len(candidate.steps) != PHYSICAL_HORIZON:
            raise G0RealizationError("candidate did not advance exactly H steps")
        if candidate.common_prestate_sha256 != ledger.common_prestate_sha256:
            raise G0RealizationError("candidate trace is not bound to common prestate")
        previous_next: np.ndarray | None = None
        previous_velocity = np.zeros((PHYSICAL_UAVS, 3), dtype=np.float64)
        reserve_row = TARGET_LABELS.index(reserve)
        primary_xyz = np.concatenate(
            (source.geometry.coordinate(source.event.owner_target), [FIXED_ALTITUDE_M])
        )
        reconstructed_arrival: int | None = None
        reconstructed_arrival_error = math.inf
        reconstructed_path_length = 0.0
        reconstructed_tracking_error = 0.0
        reconstructed_hard_violations = 0
        reconstructed_schedule: list[list[list[float]]] = []
        for expected_step, record in enumerate(candidate.steps):
            primitive = record.to_primitive()
            if _forbidden_oracle_safety_key(primitive) is not None:
                raise G0RealizationError("oracle safety trace exposed behavioral information")
            if (
                record.physical_step != expected_step
                or record.candidate_id != candidate.candidate_id
            ):
                raise G0RealizationError("candidate physical-step identity drifted")
            current = record.current_uav_positions.array()
            current_velocity = record.current_uav_velocities.array()
            service_mask = record.current_service_mask.array()
            raw = record.raw_candidate_action.array()
            guarded = record.guarded_executed_action.array()
            next_positions = record.next_uav_positions.array()
            next_velocities = record.next_uav_velocities.array()
            if (
                current.shape != (PHYSICAL_UAVS, 3)
                or current_velocity.shape != (PHYSICAL_UAVS, 3)
                or service_mask.shape != (PHYSICAL_UAVS,)
                or service_mask.dtype != np.bool_
                or raw.shape != (PHYSICAL_UAVS, ACTION_DIM)
                or guarded.shape != (PHYSICAL_UAVS, 3)
                or next_positions.shape != (PHYSICAL_UAVS, 3)
                or next_velocities.shape != (PHYSICAL_UAVS, 3)
                or not all(
                    np.isfinite(item).all()
                    for item in (
                        current,
                        current_velocity,
                        raw,
                        guarded,
                        next_positions,
                        next_velocities,
                    )
                )
            ):
                raise G0RealizationError("candidate safety row shape/finite evidence failed")
            step_action_violation = bool(
                np.any(np.abs(raw) > 1.0)
                or not np.array_equal(
                    raw[:, 2], np.zeros(PHYSICAL_UAVS, dtype=raw.dtype)
                )
            )
            if not np.array_equal(raw[~service_mask], np.zeros_like(raw[~service_mask])):
                raise G0RealizationError("inactive lifecycle received candidate action")
            expected_mask = np.ones(PHYSICAL_UAVS, dtype=np.bool_)
            expected_mask[TARGET_LABELS.index(source.event.owner_target)] = (
                source.event.active(expected_step, Cell.EVENT)
            )
            if not np.array_equal(service_mask, expected_mask):
                raise G0RealizationError("candidate service-mask schedule drifted")
            targets = np.stack(
                [
                    np.concatenate(
                        (source.geometry.coordinate(label), [FIXED_ALTITUDE_M])
                    )
                    for label in TARGET_LABELS
                ]
            )
            schedule_name, _unused = _oracle_schedule_label(
                step=expected_step,
                reserve=reserve,
                failed=source.event.owner_target,
                latest_departure=latest_departure,
                event=source.event,
            )
            if schedule_name == "stage":
                targets[reserve_row] = stage_xyz
            elif schedule_name in {"gate", "gate_until_return_ready"}:
                targets[reserve_row] = gate_xyz
            elif schedule_name == "primary":
                targets[reserve_row] = primary_xyz
            else:
                raise G0RealizationError("candidate target schedule is unregistered")
            _validate_record_branchpoint_and_transducer(
                source,
                ledger.common_prestate,
                record,
                selected_candidate_id=candidate.candidate_id,
                expected_target_positions=targets,
                expected_rng_state_bindings=expected_rng_state_bindings,
            )
            expected_raw = g1_common_target_actions(
                physical_positions=current,
                target_positions=targets,
                active_mask=expected_mask,
                max_speed=30.0,
                max_vertical_speed=5.0,
                time_step=1.0,
            )
            if not np.array_equal(raw, expected_raw):
                raise G0RealizationError("candidate raw tracker action was forged")
            if (
                reconstructed_arrival is None
                and _is_exact_gate_arrival(
                    current[reserve_row],
                    gate_xyz,
                    physical_step=expected_step,
                    latest_departure=latest_departure,
                    event_onset=source.event.onset,
                )
            ):
                reconstructed_arrival = expected_step
                reconstructed_arrival_error = float(
                    np.linalg.norm(current[reserve_row] - gate_xyz)
                )
            if previous_next is not None and not np.array_equal(current, previous_next):
                raise G0RealizationError("candidate physical recurrence failed")
            if not np.array_equal(current_velocity, previous_velocity):
                raise G0RealizationError("candidate velocity recurrence failed")
            expected_velocity = (next_positions - current)
            if not np.array_equal(next_velocities, expected_velocity):
                raise G0RealizationError("candidate next velocity is not physical delta")
            if not np.array_equal(next_positions[:, 2], current[:, 2]):
                raise G0RealizationError("candidate fixed-altitude recurrence failed")
            step_physical_violation = bool(
                np.any(next_positions[:, 0] < 0.0)
                or np.any(next_positions[:, 0] > source.geometry.map_width)
                or np.any(next_positions[:, 1] < 0.0)
                or np.any(next_positions[:, 1] > source.geometry.map_height)
                or not np.array_equal(
                    next_positions[:, 2],
                    np.full(PHYSICAL_UAVS, FIXED_ALTITUDE_M),
                )
            )
            reconstructed_path_length += float(
                np.linalg.norm(
                    next_positions[reserve_row] - current[reserve_row]
                )
            )
            if (
                source.event.onset <= expected_step < source.event.rejoin
            ):
                reconstructed_tracking_error += float(
                    np.sum(
                        (next_positions[reserve_row, :2] - primary_xyz[:2]) ** 2
                    )
                )
            reconstructed_schedule.append(targets.tolist())
            if set(record.connections) != {"user", "uav", "uav_bs"}:
                raise G0RealizationError("native connection inventory is incomplete")
            connection_shapes = {
                "user": (PHYSICAL_UAVS, GROUND_USERS),
                "uav": (PHYSICAL_UAVS, PHYSICAL_UAVS),
                "uav_bs": (PHYSICAL_UAVS, GROUND_BASE_STATIONS),
            }
            for key, shape in connection_shapes.items():
                array = record.connections[key].array()
                if array.shape != shape or array.dtype != np.bool_:
                    raise G0RealizationError("native connection shape/dtype drifted")
            for capacity in record.exact_link_capacity_values_read_by_the_real_guard:
                capacity.capacity()
            if set(record.real_guard_intervention_or_violation_output) != {
                "checked_actions",
                "blocked_actions",
                "intervention_by_uav",
            }:
                raise G0RealizationError("real guard output schema drifted")
            intervention_rows = record.real_guard_intervention_or_violation_output[
                "intervention_by_uav"
            ]
            checked_actions = int(
                record.real_guard_intervention_or_violation_output["checked_actions"]
            )
            blocked_actions = int(
                record.real_guard_intervention_or_violation_output["blocked_actions"]
            )
            if (
                len(intervention_rows) != PHYSICAL_UAVS
                or any(type(item) is not bool for item in intervention_rows)
                or not 0 <= blocked_actions <= checked_actions <= PHYSICAL_UAVS
                or blocked_actions != sum(bool(item) for item in intervention_rows)
            ):
                raise G0RealizationError("real guard intervention inventory drifted")
            # Internally consistent intervention evidence is the real guarded
            # trajectory.  Any deviation from it fails closed above.
            step_guard_violation = False
            reconstructed_hard_violations += int(
                step_action_violation
                or step_physical_violation
                or step_guard_violation
            )
            if record.shared_channel_draw_coordinate or record.shared_channel_draw_block:
                raise G0RealizationError("candidate used an unregistered channel RNG draw")
            previous_next = next_positions
            previous_velocity = next_velocities
        if reconstructed_arrival is None:
            reconstructed_arrival = PHYSICAL_HORIZON + 1
            reconstructed_arrival_error = float(
                np.linalg.norm(previous_next[reserve_row] - gate_xyz)
            )
        if (
            candidate.target_schedule_sha256 != sha256_json(reconstructed_schedule)
            or candidate.gate_arrival_time != reconstructed_arrival
            or candidate.gate_arrival_error != reconstructed_arrival_error
            or candidate.hard_violation_count != reconstructed_hard_violations
            or candidate.event_window_tracking_error
            != reconstructed_tracking_error
            or candidate.path_length != reconstructed_path_length
            or candidate.stage_coordinates
            != tuple(float(value) for value in stage_xyz[:2])
        ):
            raise G0RealizationError("candidate aggregate/ranking evidence was forged")
        if candidate.trace_sha256 != sha256_json(
            [record.to_primitive() for record in candidate.steps]
        ):
            raise G0RealizationError("candidate trace digest failed")
        if not all(math.isfinite(value) for value in candidate.rank):
            raise G0RealizationError("candidate ranking evidence is nonfinite")
        previous_candidates.append(candidate)
    _validate_oracle_guard_transition_bindings(
        source,
        ledger.candidates,
        ledger.common_prestate,
    )
    assigned_labels = tuple(
        TargetLabel.parse(value) for value in source.assignment.row_to_target
    )
    unaffected_primaries = tuple(
        label
        for label in assigned_labels
        if label.kind is TargetKind.PRIMARY and label != source.event.owner_target
    )
    if (
        len(unaffected_primaries) != 5
        or any(assigned_labels.count(label) != 1 for label in unaffected_primaries)
        or any(
            TargetLabel.parse(candidate.candidate_id).kind is not TargetKind.STAGE
            for candidate in ledger.candidates
        )
    ):
        raise G0RealizationError("unaffected-primary/reserve ownership certificate failed")
    expected_selected = min(previous_candidates, key=lambda item: item.rank)
    if (
        ledger.selected_candidate_id != expected_selected.candidate_id
        or tuple(ledger.selected_rank) != expected_selected.rank
    ):
        raise G0RealizationError("sealed candidate ranking was forged")
    if sum(len(candidate.steps) for candidate in ledger.candidates) > 2 * PHYSICAL_HORIZON:
        raise G0RealizationError("oracle candidate transition ceiling exceeded")
    return oracle_evidence.OracleSafetyCertificate(
        ledger_sha256=ledger.content_sha256,
        selected_candidate_id=ledger.selected_candidate_id,
        candidate_trace_sha256=tuple(
            candidate.trace_sha256 for candidate in ledger.candidates
        ),
    )


def _validated_oracle_safety_context(
    source: G0EpisodeSource,
    ledger: oracle_evidence.OracleSafetyLedger,
) -> oracle_evidence._ValidatedOracleSafetyContext:
    certificate = validate_oracle_safety_ledger(source, ledger)
    context = object.__new__(oracle_evidence._ValidatedOracleSafetyContext)
    values = {
        "source": source,
        "ledger": ledger,
        "certificate": certificate,
        "content_sha256": ledger.content_sha256,
        "candidate_trace_sha256": tuple(
            candidate.trace_sha256 for candidate in ledger.candidates
        ),
        "seal": oracle_evidence._VALIDATED_ORACLE_SAFETY_CONTEXT_SEAL,
    }
    for name, value in values.items():
        object.__setattr__(context, name, value)
    return context


def _require_validated_oracle_safety_context(
    context: oracle_evidence._ValidatedOracleSafetyContext,
) -> tuple[G0EpisodeSource, oracle_evidence.OracleSafetyLedger, oracle_evidence.OracleSafetyCertificate]:
    if (
        not isinstance(context, oracle_evidence._ValidatedOracleSafetyContext)
        or getattr(context, "seal", None) is not oracle_evidence._VALIDATED_ORACLE_SAFETY_CONTEXT_SEAL
    ):
        raise G0RealizationError("oracle safety context is not module-issued")
    source, ledger, certificate = (
        context.source,
        context.ledger,
        context.certificate,
    )
    candidate_digests = tuple(
        candidate.trace_sha256 for candidate in ledger.candidates
    )
    if (
        ledger.source_sha256 != source.to_primitive()["sha256"]
        or ledger.content_sha256 != context.content_sha256
        or ledger.content_sha256
        != sha256_json(ledger.to_primitive(include_digest=False))
        or candidate_digests != context.candidate_trace_sha256
        or certificate
        != oracle_evidence.OracleSafetyCertificate(
            ledger_sha256=ledger.content_sha256,
            selected_candidate_id=ledger.selected_candidate_id,
            candidate_trace_sha256=candidate_digests,
        )
    ):
        raise G0RealizationError("validated oracle safety context drifted")
    return source, ledger, certificate


def _oracle_qualification_from_validated_context(
    context: oracle_evidence._ValidatedOracleSafetyContext,
) -> oracle_evidence.OracleQualificationCertificate:
    source, ledger, safety_certificate = (
        _require_validated_oracle_safety_context(context)
    )
    rows: list[oracle_evidence.OracleCandidateEvidence] = []
    for candidate in ledger.candidates:
        rows.append(
            oracle_evidence.OracleCandidateEvidence(
                reserve_target=candidate.candidate_id,
                latest_departure=int(source.event.onset)
                - _minimum_tracker_travel_steps(
                    np.concatenate(
                        (
                            source.geometry.coordinate(candidate.candidate_id),
                            [FIXED_ALTITUDE_M],
                        )
                    ),
                    np.concatenate(
                        (
                            source.geometry.gate(source.event.owner_target),
                            [FIXED_ALTITUDE_M],
                        )
                    ),
                    max_speed=30.0,
                    max_vertical_speed=5.0,
                    time_step=1.0,
                ),
                gate_arrival_time=candidate.gate_arrival_time,
                gate_arrival_error=candidate.gate_arrival_error,
                gate_arrival_roundoff_bound=0.0,
                hard_violation_count=candidate.hard_violation_count,
                event_window_tracking_error=candidate.event_window_tracking_error,
                path_length=candidate.path_length,
                stage_coordinates=candidate.stage_coordinates,
                physical_steps_advanced=len(candidate.steps),
                target_schedule_exact=True,
                action_support_valid=True,
                map_support_valid=True,
                candidate_complete=len(candidate.steps) == PHYSICAL_HORIZON,
                trace_sha256=candidate.trace_sha256,
            )
        )
    selected = min(rows, key=lambda item: item.rank)
    passed = bool(
        len(rows) == oracle_evidence.K_SEARCH
        and all(row.candidate_complete for row in rows)
        and all(row.hard_violation_count == 0 for row in rows)
        and ledger.selected_candidate_id == selected.reserve_target
    )
    return oracle_evidence.OracleQualificationCertificate(
        candidates=(rows[0], rows[1]),
        selected_reserve_target=selected.reserve_target,
        selected_rank=selected.rank,
        both_candidates_evaluated=True,
        exact_lexicographic_winner=True,
        future_channel_read_count=0,
        future_service_read_count=0,
        unaffected_primary_move_creates_vacancy=True,
        candidate_owner_is_reserve=True,
        shared_dynamics_action_safety_identity=(
            dict(ledger.shared_action_method_sha256) == oracle_safety_method_digests()
        ),
        candidate_count=oracle_evidence.K_SEARCH,
        complexity="O(H*K_search)",
        nested_rollout=False,
        replanning=False,
        tree_search=False,
        beam_search=False,
        mcts=False,
        adaptive_candidate_creation=False,
        passed=passed,
        oracle_safety_ledger_sha256=ledger.content_sha256,
        safety_certificate=safety_certificate,
    )


def oracle_qualification_from_safety_ledger(
    source: G0EpisodeSource,
    ledger: oracle_evidence.OracleSafetyLedger,
) -> oracle_evidence.OracleQualificationCertificate:
    return _oracle_qualification_from_validated_context(
        _validated_oracle_safety_context(source, ledger)
    )
















def validate_oracle_safety_primitive(
    source: G0EpisodeSource,
    primitive: Mapping[str, Any],
) -> oracle_evidence.OracleSafetyCertificate:
    return validate_oracle_safety_ledger(
        source, oracle_evidence.oracle_safety_ledger_from_primitive(primitive)
    )


def validate_oracle_behavioral_replay(
    ledger: oracle_evidence.OracleSafetyLedger,
    registered_trace: Sequence[oracle_evidence.OracleSafetyStepRecord | Mapping[str, Any]],
    replay_trace: Sequence[oracle_evidence.OracleSafetyStepRecord | Mapping[str, Any]],
) -> oracle_evidence.OracleSafetyCertificate:
    """Compare two independent selected-behavior safety projections byte-for-byte."""

    registered = tuple(
        record
        if isinstance(record, oracle_evidence.OracleSafetyStepRecord)
        else oracle_evidence.oracle_safety_step_from_primitive(record)
        for record in registered_trace
    )
    replay = tuple(
        record
        if isinstance(record, oracle_evidence.OracleSafetyStepRecord)
        else oracle_evidence.oracle_safety_step_from_primitive(record)
        for record in replay_trace
    )
    if len(registered) != PHYSICAL_HORIZON or len(replay) != PHYSICAL_HORIZON:
        raise G0RealizationError("behavioral replay is not one complete H trajectory")
    if [item.to_primitive() for item in registered] != [
        item.to_primitive() for item in replay
    ]:
        raise G0RealizationError("independent behavioral replay differs byte-for-byte")
    previous_next: np.ndarray | None = None
    for expected_step, record in enumerate(registered):
        if (
            record.physical_step != expected_step
            or record.candidate_id != ledger.selected_candidate_id
            or record.shared_channel_draw_coordinate != ledger.channel_draw_schema
            or record.shared_channel_draw_block != ledger.shared_channel_draw_blocks
        ):
            raise G0RealizationError("behavioral replay identity or shared tape mismatch")
        if _forbidden_oracle_safety_key(record.to_primitive()) is not None:
            raise G0RealizationError("behavioral replay safety projection leaked metrics")
        current = record.current_uav_positions.array()
        next_positions = record.next_uav_positions.array()
        if previous_next is not None and not np.array_equal(current, previous_next):
            raise G0RealizationError("behavioral replay physical recurrence failed")
        if not np.array_equal(record.next_uav_velocities.array(), next_positions - current):
            raise G0RealizationError("behavioral replay velocity recurrence failed")
        for capacity in record.exact_link_capacity_values_read_by_the_real_guard:
            capacity.capacity()
        previous_next = next_positions
    digest = sha256_json([record.to_primitive() for record in registered])
    return oracle_evidence.OracleSafetyCertificate(
        ledger_sha256=ledger.content_sha256,
        selected_candidate_id=ledger.selected_candidate_id,
        candidate_trace_sha256=tuple(
            candidate.trace_sha256 for candidate in ledger.candidates
        ),
        behavioral_replay_sha256=digest,
    )


def _validate_branch_safety_trace(
    ledger: oracle_evidence.OracleSafetyLedger,
    records: Sequence[oracle_evidence.OracleSafetyStepRecord],
) -> None:
    if len(records) != PHYSICAL_HORIZON:
        raise G0RealizationError("branch replay is not one complete H trajectory")
    previous_next: np.ndarray | None = None
    for expected_step, record in enumerate(records):
        if (
            record.physical_step != expected_step
            or record.candidate_id != ledger.selected_candidate_id
            or record.shared_channel_draw_coordinate != ledger.channel_draw_schema
            or record.shared_channel_draw_block != ledger.shared_channel_draw_blocks
        ):
            raise G0RealizationError("branch replay identity or shared tape mismatch")
        if _forbidden_oracle_safety_key(record.to_primitive()) is not None:
            raise G0RealizationError("branch replay leaked behavioral metrics")
        current = record.current_uav_positions.array()
        current_velocity = record.current_uav_velocities.array()
        next_positions = record.next_uav_positions.array()
        next_velocity = record.next_uav_velocities.array()
        if previous_next is not None and not np.array_equal(current, previous_next):
            raise G0RealizationError("branch replay physical recurrence failed")
        if expected_step == 0 and not np.array_equal(
            current_velocity, np.zeros_like(current_velocity)
        ):
            raise G0RealizationError("branch replay initial velocity drifted")
        if not np.array_equal(next_velocity, next_positions - current):
            raise G0RealizationError("branch replay velocity recurrence failed")
        if set(record.connections) != {"user", "uav", "uav_bs"}:
            raise G0RealizationError("branch replay connection inventory drifted")
        for capacity in record.exact_link_capacity_values_read_by_the_real_guard:
            capacity.capacity()
        previous_next = next_positions


def _selected_reserve_storage_row(
    source: G0EpisodeSource,
    selected_candidate_id: str,
) -> int:
    rows = tuple(str(item) for item in source.assignment.row_to_target)
    try:
        return rows.index(str(selected_candidate_id))
    except ValueError as error:
        raise G0RealizationError("selected reserve is absent from assignment") from error


def _target_internal_row(target: TargetLabel | str) -> int:
    """Resolve one lifecycle owner in the environment's internal target order."""

    parsed = target if isinstance(target, TargetLabel) else TargetLabel.parse(target)
    try:
        return TARGET_LABELS.index(parsed)
    except ValueError as error:
        raise G0RealizationError("lifecycle owner is absent from internal order") from error


def _expected_behavioral_target_schedule(
    context: oracle_evidence._ValidatedOracleSafetyContext,
    return_ready_step: int | None,
) -> np.ndarray:
    source, ledger, _certificate = _require_validated_oracle_safety_context(
        context
    )
    selected = TargetLabel.parse(ledger.selected_candidate_id)
    selected_row = _selected_reserve_storage_row(source, selected.key)
    qualification = _oracle_qualification_from_validated_context(context)
    candidate = next(
        item for item in qualification.candidates if item.reserve_target == selected.key
    )
    rows = np.stack(
        [
            np.concatenate(
                (
                    source.geometry.coordinate(TargetLabel.parse(label)),
                    [FIXED_ALTITUDE_M],
                )
            )
            for label in source.assignment.row_to_target
        ]
    )
    schedule = np.repeat(rows[None, :, :], PHYSICAL_HORIZON, axis=0)
    gate = np.concatenate(
        (source.geometry.gate(source.event.owner_target), [FIXED_ALTITUDE_M])
    )
    primary = np.concatenate(
        (source.geometry.coordinate(source.event.owner_target), [FIXED_ALTITUDE_M])
    )
    stage = np.concatenate(
        (source.geometry.coordinate(selected), [FIXED_ALTITUDE_M])
    )
    for step in range(PHYSICAL_HORIZON):
        if step < candidate.latest_departure:
            target = stage
        elif step < source.event.onset:
            target = gate
        elif step < source.event.rejoin:
            target = primary
        elif return_ready_step is None or step < return_ready_step:
            target = gate
        else:
            target = stage
        schedule[step, selected_row] = target
    return schedule


def _validate_behavioral_transducer_binding(
    source: G0EpisodeSource,
    ledger: oracle_evidence.OracleSafetyLedger,
    execution: oracle_evidence.OracleBehavioralExecution,
    *,
    cell: Cell | str = Cell.EVENT,
) -> None:
    schedule = execution.target_schedule.array()
    if schedule.shape != (PHYSICAL_HORIZON, PHYSICAL_UAVS, 3):
        raise G0RealizationError("behavioral target schedule shape drifted")
    common_rng_states = ledger.common_prestate.get("rng_states")
    if not isinstance(common_rng_states, Mapping):
        raise G0RealizationError("oracle common prestate omitted RNG states")
    expected_rng_state_bindings = g0_environment._rng_state_bindings(common_rng_states)
    for step, record in enumerate(execution.steps):
        targets_internal = np.zeros((PHYSICAL_UAVS, 3), dtype=np.float64)
        targets_internal[source.geometry.slot_to_target] = schedule[step]
        _validate_record_branchpoint_and_transducer(
            source,
            ledger.common_prestate,
            record,
            selected_candidate_id=ledger.selected_candidate_id,
            expected_target_positions=targets_internal,
            expected_rng_state_bindings=expected_rng_state_bindings,
            cell=cell,
        )


def _derive_return_ready_step(
    source: G0EpisodeSource,
    execution: oracle_evidence.OracleBehavioralExecution,
) -> int | None:
    owner_storage = source.assignment.row_to_target.index(
        source.event.owner_target.key
    )
    initial_owner_handle = controllers.initial_lifecycle_handles(source)[owner_storage]
    replacement_handle = controllers.replacement_lifecycle_handle(
        source, initial_owner_handle
    )
    weakest = execution.pre_action_weakest_service.array()
    for step in range(source.event.rejoin + 1, PHYSICAL_HORIZON):
        current_context = oracle_evidence._validate_pre_action_context_primitive(
            execution.steps[step].pre_action_context
        )
        previous_context = oracle_evidence._validate_pre_action_context_primitive(
            execution.steps[step - 1].pre_action_context
        )
        if (
            current_context["event_owner_handle"] != replacement_handle
            or previous_context["event_owner_handle"] != replacement_handle
            or int(current_context["event_owner_epoch"]) != 1
            or int(previous_context["event_owner_epoch"]) != 1
        ):
            raise G0RealizationError(
                "RETURN_READY lifecycle owner/epoch is not reconstructed"
            )
        current_rows = {
            row["handle"]: row
            for row in current_context["lifecycle_owner_to_internal"]
        }
        previous_rows = {
            row["handle"]: row
            for row in previous_context["lifecycle_owner_to_internal"]
        }
        if replacement_handle not in current_rows or replacement_handle not in previous_rows:
            raise G0RealizationError("RETURN_READY replacement lifecycle is absent")
        current_owner_row = int(current_rows[replacement_handle]["internal_row"])
        previous_owner_row = int(previous_rows[replacement_handle]["internal_row"])
        current_mask = current_context["service_active_mask"]
        previous_mask = previous_context["service_active_mask"]
        if (
            current_rows[replacement_handle]["owner_target"]
            == source.event.owner_target.key
            and previous_rows[replacement_handle]["owner_target"]
            == source.event.owner_target.key
            and bool(current_mask[current_owner_row])
            and bool(previous_mask[previous_owner_row])
            and float(weakest[step]) >= SERVICE_TARGET
        ):
            return step
    return None


def _validate_oracle_branch_aware_replay_from_validated_context(
    context: oracle_evidence._ValidatedOracleSafetyContext,
    prebehavior_self_replay: oracle_evidence.OracleCandidateSafetyTrace | Mapping[str, Any],
    behavioral_execution: oracle_evidence.OracleBehavioralExecution | Mapping[str, Any],
    behavioral_self_replay: oracle_evidence.OracleBehavioralExecution | Mapping[str, Any],
) -> oracle_evidence.OracleSafetyCertificate:
    """Reconstruct the frozen prefix/branchpoint/post-R replay certificate."""

    source, ledger, _certificate = _require_validated_oracle_safety_context(
        context
    )
    selected = next(
        candidate
        for candidate in ledger.candidates
        if candidate.candidate_id == ledger.selected_candidate_id
    )
    prebehavior = (
        prebehavior_self_replay
        if isinstance(prebehavior_self_replay, oracle_evidence.OracleCandidateSafetyTrace)
        else oracle_evidence.oracle_safety_trace_from_primitive(prebehavior_self_replay)
    )
    behavior = oracle_evidence.oracle_behavioral_execution_from_primitive(
        behavioral_execution.to_primitive()
        if isinstance(behavioral_execution, oracle_evidence.OracleBehavioralExecution)
        else behavioral_execution
    )
    behavior_replay = oracle_evidence.oracle_behavioral_execution_from_primitive(
        behavioral_self_replay.to_primitive()
        if isinstance(behavioral_self_replay, oracle_evidence.OracleBehavioralExecution)
        else behavioral_self_replay
    )
    if prebehavior.to_primitive() != selected.to_primitive():
        raise G0RealizationError("prebehavior self-replay differs byte-for-byte")
    if behavior.to_primitive() != behavior_replay.to_primitive():
        raise G0RealizationError("behavioral branch self-replay differs byte-for-byte")
    if (
        behavior.selected_candidate_id != ledger.selected_candidate_id
        or behavior_replay.selected_candidate_id != ledger.selected_candidate_id
    ):
        raise G0RealizationError("behavioral replay reselected the reserve candidate")
    _validate_branch_safety_trace(ledger, selected.steps)
    _validate_branch_safety_trace(ledger, behavior.steps)
    _validate_branch_safety_trace(ledger, behavior_replay.steps)
    _validate_behavioral_transducer_binding(source, ledger, behavior)
    _validate_behavioral_transducer_binding(source, ledger, behavior_replay)
    derived_return_ready = _derive_return_ready_step(source, behavior)
    if behavior.return_ready_step != derived_return_ready:
        raise G0RealizationError("stored RETURN_READY step is not causally reconstructed")
    if behavior_replay.return_ready_step != derived_return_ready:
        raise G0RealizationError("behavioral self-replay RETURN_READY step drifted")
    expected_targets = _expected_behavioral_target_schedule(
        context, derived_return_ready
    )
    if not np.array_equal(behavior.target_schedule.array(), expected_targets):
        raise G0RealizationError("behavioral target switch is early, late, or wrong")
    prefix_end = (
        PHYSICAL_HORIZON if derived_return_ready is None else derived_return_ready
    )
    for step in range(prefix_end):
        if selected.steps[step].to_primitive() != behavior.steps[step].to_primitive():
            raise G0RealizationError(
                f"pre-RETURN_READY prefix differs at physical step {step}"
            )
    selected_internal_row = _target_internal_row(ledger.selected_candidate_id)
    if derived_return_ready is None:
        if [item.to_primitive() for item in selected.steps] != [
            item.to_primitive() for item in behavior.steps
        ]:
            raise G0RealizationError("R=NONE replay is not fully identical")
    else:
        step = derived_return_ready
        pre_record = selected.steps[step]
        behavior_record = behavior.steps[step]
        for name in (
            "physical_step",
            "candidate_id",
            "current_uav_positions",
            "current_uav_velocities",
            "current_service_mask",
            "pre_action_context",
            "executed_service_mask",
            "shared_channel_draw_coordinate",
            "shared_channel_draw_block",
        ):
            left = getattr(pre_record, name)
            right = getattr(behavior_record, name)
            left_value = left.to_primitive() if hasattr(left, "to_primitive") else left
            right_value = right.to_primitive() if hasattr(right, "to_primitive") else right
            if left_value != right_value:
                raise G0RealizationError("step-R pre-action branchpoint identity failed")
        pre_action = pre_record.raw_candidate_action.array()
        behavior_action = behavior_record.raw_candidate_action.array()
        pre_transducer = oracle_evidence._validate_common_transducer_evidence_primitive(
            pre_record.common_transducer_evidence
        )
        behavior_transducer = oracle_evidence._validate_common_transducer_evidence_primitive(
            behavior_record.common_transducer_evidence
        )
        for name in (
            "transducer_source_sha256",
            "row_order",
            "physical_positions",
            "active_mask",
            "max_speed",
            "max_vertical_speed",
            "time_step",
        ):
            if pre_transducer[name] != behavior_transducer[name]:
                raise G0RealizationError(
                    "step-R common transducer pre-action inputs drifted"
                )
        pre_targets = oracle_evidence._native_array_from_primitive(
            pre_transducer["target_positions"]
        ).array()
        behavior_targets = oracle_evidence._native_array_from_primitive(
            behavior_transducer["target_positions"]
        ).array()
        unaffected = np.ones(PHYSICAL_UAVS, dtype=np.bool_)
        unaffected[selected_internal_row] = False
        if (
            not np.array_equal(pre_targets[unaffected], behavior_targets[unaffected])
            or np.array_equal(
                pre_targets[selected_internal_row],
                behavior_targets[selected_internal_row],
            )
        ):
            raise G0RealizationError(
                "RETURN_READY target switch is not isolated to the reserve"
            )
        if not np.array_equal(pre_action[unaffected], behavior_action[unaffected]):
            raise G0RealizationError("RETURN_READY changed an unaffected owner action")
        # The selected target changes before action construction at R.  The
        # resulting raw action is allowed to remain byte-identical through a
        # coincident direction, action clipping, or the unchanged real guard;
        # the first differing action byte is not the RETURN_READY predicate.
    for step, (pre_record, behavior_record) in enumerate(
        zip(selected.steps, behavior.steps)
    ):
        if (
            pre_record.physical_step != behavior_record.physical_step
            or pre_record.candidate_id != behavior_record.candidate_id
            or pre_record.shared_channel_draw_coordinate
            != behavior_record.shared_channel_draw_coordinate
            or pre_record.shared_channel_draw_block
            != behavior_record.shared_channel_draw_block
        ):
            raise G0RealizationError(
                f"shared exogenous ledger differs at physical step {step}"
            )
    return oracle_evidence.OracleSafetyCertificate(
        ledger_sha256=ledger.content_sha256,
        selected_candidate_id=ledger.selected_candidate_id,
        candidate_trace_sha256=tuple(
            candidate.trace_sha256 for candidate in ledger.candidates
        ),
        behavioral_replay_sha256=behavior.trace_sha256,
        return_ready_step=derived_return_ready,
        prefix_identity_ok=True,
        branchpoint_identity_ok=True,
        shared_ledger_identity_ok=True,
        prebehavior_self_replay_ok=True,
        behavioral_self_replay_ok=True,
        target_switch_ok=True,
        safety_guard_ok=True,
        replay_ok=True,
    )


def _validate_oracle_no_event_replay_from_validated_context(
    context: oracle_evidence._ValidatedOracleSafetyContext,
    behavioral_execution: oracle_evidence.OracleBehavioralExecution | Mapping[str, Any],
    behavioral_self_replay: oracle_evidence.OracleBehavioralExecution | Mapping[str, Any],
) -> oracle_evidence.OracleSafetyCertificate:
    """Reconstruct the frozen Oracle Z row, for which causal R is absent."""

    source, ledger, _certificate = _require_validated_oracle_safety_context(
        context
    )
    behavior = oracle_evidence.oracle_behavioral_execution_from_primitive(
        behavioral_execution.to_primitive()
        if isinstance(behavioral_execution, oracle_evidence.OracleBehavioralExecution)
        else behavioral_execution
    )
    behavior_replay = oracle_evidence.oracle_behavioral_execution_from_primitive(
        behavioral_self_replay.to_primitive()
        if isinstance(behavioral_self_replay, oracle_evidence.OracleBehavioralExecution)
        else behavioral_self_replay
    )
    if behavior.to_primitive() != behavior_replay.to_primitive():
        raise G0RealizationError(
            "oracle NO_EVENT branch self-replay differs byte-for-byte"
        )
    if (
        behavior.selected_candidate_id != ledger.selected_candidate_id
        or behavior_replay.selected_candidate_id != ledger.selected_candidate_id
    ):
        raise G0RealizationError("oracle NO_EVENT replay reselected the reserve")
    if behavior.return_ready_step is not None or behavior_replay.return_ready_step is not None:
        raise G0RealizationError("oracle NO_EVENT replay observed a RETURN_READY step")
    _validate_branch_safety_trace(ledger, behavior.steps)
    _validate_branch_safety_trace(ledger, behavior_replay.steps)
    _validate_behavioral_transducer_binding(
        source, ledger, behavior, cell=Cell.NO_EVENT
    )
    _validate_behavioral_transducer_binding(
        source, ledger, behavior_replay, cell=Cell.NO_EVENT
    )
    expected_targets = _expected_behavioral_target_schedule(context, None)
    if not np.array_equal(behavior.target_schedule.array(), expected_targets):
        raise G0RealizationError("oracle NO_EVENT fallback target schedule drifted")
    return oracle_evidence.OracleSafetyCertificate(
        ledger_sha256=ledger.content_sha256,
        selected_candidate_id=ledger.selected_candidate_id,
        candidate_trace_sha256=tuple(
            candidate.trace_sha256 for candidate in ledger.candidates
        ),
        behavioral_replay_sha256=behavior.trace_sha256,
        return_ready_step=None,
        prefix_identity_ok=True,
        branchpoint_identity_ok=True,
        shared_ledger_identity_ok=True,
        prebehavior_self_replay_ok=True,
        behavioral_self_replay_ok=True,
        target_switch_ok=True,
        safety_guard_ok=True,
        replay_ok=True,
    )


def validate_oracle_branch_aware_replay(
    source: G0EpisodeSource,
    ledger: oracle_evidence.OracleSafetyLedger,
    prebehavior_self_replay: oracle_evidence.OracleCandidateSafetyTrace | Mapping[str, Any],
    behavioral_execution: oracle_evidence.OracleBehavioralExecution | Mapping[str, Any],
    behavioral_self_replay: oracle_evidence.OracleBehavioralExecution | Mapping[str, Any],
) -> oracle_evidence.OracleSafetyCertificate:
    return _validate_oracle_branch_aware_replay_from_validated_context(
        _validated_oracle_safety_context(source, ledger),
        prebehavior_self_replay,
        behavioral_execution,
        behavioral_self_replay,
    )


def _validate_oracle_branch_aware_replay_primitive_from_validated_context(
    context: oracle_evidence._ValidatedOracleSafetyContext,
    primitive: Mapping[str, Any],
) -> oracle_evidence.OracleSafetyCertificate:
    _source, ledger, _safety_certificate = (
        _require_validated_oracle_safety_context(context)
    )
    expected = {
        "schema_version",
        "ledger_sha256",
        "selected_candidate_id",
        "prebehavior_self_replay",
        "behavioral_execution",
        "behavioral_self_replay",
        "certificate",
    }
    if not isinstance(primitive, Mapping) or set(primitive) != expected:
        raise G0RealizationError("branch-aware replay artifact schema drifted")
    if (
        int(primitive["schema_version"]) != 1
        or primitive["ledger_sha256"] != ledger.content_sha256
        or primitive["selected_candidate_id"] != ledger.selected_candidate_id
    ):
        raise G0RealizationError("branch-aware replay artifact identity drifted")
    certificate = _validate_oracle_branch_aware_replay_from_validated_context(
        context,
        primitive["prebehavior_self_replay"],
        primitive["behavioral_execution"],
        primitive["behavioral_self_replay"],
    )
    if primitive["certificate"] != certificate.to_primitive():
        raise G0RealizationError("branch-aware replay certificate was forged")
    return certificate


def validate_oracle_branch_aware_replay_primitive(
    source: G0EpisodeSource,
    ledger: oracle_evidence.OracleSafetyLedger,
    primitive: Mapping[str, Any],
) -> oracle_evidence.OracleSafetyCertificate:
    return _validate_oracle_branch_aware_replay_primitive_from_validated_context(
        _validated_oracle_safety_context(source, ledger), primitive
    )


def build_proof_episode_validity(
    source: G0EpisodeSource,
    safety_primitive: Mapping[str, Any],
    replay_primitive: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Proof-only public entry; derives validity rather than accepting a flag."""

    try:
        ledger = oracle_evidence.oracle_safety_ledger_from_primitive(safety_primitive)
        context = _validated_oracle_safety_context(source, ledger)
        replay_certificate = None
        if replay_primitive is not None:
            replay_certificate = (
                _validate_oracle_branch_aware_replay_primitive_from_validated_context(
                    context, replay_primitive
                )
            )
    except (G0RealizationError, KeyError, TypeError, ValueError) as error:
        return {
            "operational_valid": False,
            "errors": [f"oracle_safety:{type(error).__name__}:{error}"],
            "result_branch": INVALID_BRANCH,
        }
    return _build_proof_episode_validity_from_validated_evidence(
        context,
        replay_primitive=replay_primitive,
        replay_certificate=replay_certificate,
    )


def _build_proof_episode_validity_from_validated_evidence(
    context: oracle_evidence._ValidatedOracleSafetyContext,
    *,
    replay_primitive: Mapping[str, Any] | None,
    replay_certificate: oracle_evidence.OracleSafetyCertificate | None,
) -> dict[str, Any]:
    _source, _ledger, certificate = (
        _require_validated_oracle_safety_context(context)
    )
    if replay_primitive is None:
        if replay_certificate is not None:
            raise G0RealizationError("replay certificate lacks primitive evidence")
    elif (
        replay_certificate is None
        or replay_primitive.get("certificate")
        != replay_certificate.to_primitive()
        or replay_certificate.ledger_sha256 != certificate.ledger_sha256
    ):
        raise G0RealizationError("validated replay evidence binding drifted")
    return {
        "operational_valid": True,
        "errors": [],
        "result_branch": None,
        "oracle_safety_certificate": certificate.to_primitive(),
        "oracle_replay_certificate": (
            None if replay_certificate is None else replay_certificate.to_primitive()
        ),
    }


def analyze_proof_fixture(
    source: G0EpisodeSource,
    safety_primitive: Mapping[str, Any],
    replay_primitive: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Public readiness analyzer; never emits a scientific branch for valid proof data."""

    reconstructed = build_proof_episode_validity(
        source, safety_primitive, replay_primitive
    )
    return {
        "proof_only": True,
        "operational_valid": bool(reconstructed["operational_valid"]),
        "operational_errors": list(reconstructed["errors"]),
        "result_branch": reconstructed["result_branch"],
    }


def _analyze_proof_fixture_from_validated_evidence(
    context: oracle_evidence._ValidatedOracleSafetyContext,
    *,
    replay_primitive: Mapping[str, Any],
    replay_certificate: oracle_evidence.OracleSafetyCertificate,
) -> dict[str, Any]:
    reconstructed = _build_proof_episode_validity_from_validated_evidence(
        context,
        replay_primitive=replay_primitive,
        replay_certificate=replay_certificate,
    )
    return {
        "proof_only": True,
        "operational_valid": bool(reconstructed["operational_valid"]),
        "operational_errors": list(reconstructed["errors"]),
        "result_branch": reconstructed["result_branch"],
    }








def _common_transducer_evidence(
    *,
    physical_positions: np.ndarray,
    target_positions: np.ndarray,
    active_mask: np.ndarray,
    raw_action: np.ndarray,
) -> dict[str, Any]:
    return oracle_evidence._validate_common_transducer_evidence_primitive(
        {
            "transducer_source_sha256": oracle_evidence.common_tracker_source_digest(),
            "row_order": "target_owned_internal",
            "physical_positions": oracle_evidence._NativeArrayEvidence.from_array(
                np.asarray(physical_positions, dtype=np.float64)
            ).to_primitive(),
            "target_positions": oracle_evidence._NativeArrayEvidence.from_array(
                np.asarray(target_positions, dtype=np.float64)
            ).to_primitive(),
            "active_mask": oracle_evidence._NativeArrayEvidence.from_array(
                np.asarray(active_mask, dtype=np.bool_)
            ).to_primitive(),
            "raw_action": oracle_evidence._NativeArrayEvidence.from_array(
                np.asarray(raw_action, dtype=np.float32)
            ).to_primitive(),
            "max_speed": 30.0,
            "max_vertical_speed": 5.0,
            "time_step": 1.0,
        }
    )






def _expected_pre_action_context(
    source: G0EpisodeSource,
    common_prestate: Mapping[str, Any],
    *,
    physical_step: int,
    selected_candidate_id: str,
    rng_state_bindings: Mapping[str, Any] | None = None,
    cell: Cell | str = Cell.EVENT,
) -> dict[str, Any]:
    chosen_cell = Cell(cell)
    handles = list(controllers.initial_lifecycle_handles(source))
    epochs = np.zeros(PHYSICAL_UAVS, dtype=np.int64)
    owner_storage = source.assignment.row_to_target.index(
        source.event.owner_target.key
    )
    if (
        chosen_cell is Cell.EVENT
        and int(physical_step) >= source.event.rejoin
    ):
        handles[owner_storage] = controllers.replacement_lifecycle_handle(
            source, handles[owner_storage]
        )
        epochs[owner_storage] = 1
    rng_states = (
        rng_state_bindings
        if rng_state_bindings is not None
        else common_prestate.get("rng_states")
    )
    if not isinstance(rng_states, Mapping):
        raise G0RealizationError("common prestate omitted branchpoint RNG evidence")
    return g0_environment._make_pre_action_context(
        source,
        physical_step=int(physical_step),
        handles=handles,
        epochs=epochs,
        selected_candidate_id=selected_candidate_id,
        rng_states=rng_states,
        service_active_mask=[
            bool(
                source.event.active(int(physical_step), chosen_cell)
                if internal_row == TARGET_LABELS.index(source.event.owner_target)
                else True
            )
            for internal_row in range(PHYSICAL_UAVS)
        ],
    )


def _candidate_state_value(value: Any, *, path: str) -> Any:
    if isinstance(value, np.ndarray):
        return {"native_array": oracle_evidence._NativeArrayEvidence.from_array(value).to_primitive()}
    if isinstance(value, np.random.RandomState):
        return {"random_state": g0_environment._random_state_primitive(value)}
    if isinstance(value, np.random.Generator):
        return {"generator_state": oracle_evidence._json_safe(value.bit_generator.state)}
    if isinstance(value, np.generic):
        return _candidate_state_value(value.item(), path=path)
    if isinstance(value, float) and not math.isfinite(value):
        return {"nonfinite_float": value.hex()}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (tuple, list)):
        return [
            _candidate_state_value(item, path=f"{path}/{index}")
            for index, item in enumerate(value)
        ]
    if isinstance(value, Mapping):
        return {
            "ordered_mapping": [
                {
                    "key": _candidate_state_value(key, path=f"{path}/key"),
                    "value": _candidate_state_value(item, path=f"{path}/{key}"),
                }
                for key, item in value.items()
            ]
        }
    raise G0RealizationError(
        f"unsupported mutable candidate-state type at {path}: "
        f"{type(value).__name__}"
    )




def _complete_oracle_prestate(env: "g0_environment.UAVSourceIdentifiabilityEnv") -> dict[str, Any]:
    rng_states: dict[str, Any] = {}
    for name, value in env.__dict__.items():
        if isinstance(value, np.random.RandomState):
            rng_states[str(name)] = g0_environment._random_state_primitive(value)
    if "_channel_rng" not in rng_states:
        raise G0RealizationError("complete prestate omitted the registered channel RNG")
    candidate_tokens = (
        "position",
        "velocity",
        "connection",
        "routing",
        "channel",
        "sinr",
        "hop",
        "cache",
        "guard",
        "service",
        "mask",
        "current_step",
    )
    candidate_state_inventory: dict[str, Any] = {}
    for name, value in env.__dict__.items():
        if any(token in str(name).lower() for token in candidate_tokens):
            candidate_state_inventory[str(name)] = _candidate_state_value(
                value, path=str(name)
            )
    return {
        "source": env.g0_source.to_primitive(),
        "cell": env.g0_cell.value,
        "current_step": int(env.current_step),
        "geometry": {
            "uav_positions": oracle_evidence._NativeArrayEvidence.from_array(env.uav_positions).to_primitive(),
            "user_positions": oracle_evidence._NativeArrayEvidence.from_array(env.user_positions).to_primitive(),
            "ground_bs_positions": oracle_evidence._NativeArrayEvidence.from_array(
                env.ground_bs_positions
            ).to_primitive(),
        },
        "event": env.g0_source.event.to_primitive(),
        "slot_permutation": oracle_evidence._NativeArrayEvidence.from_array(
            env.g0_source.geometry.slot_to_target
        ).to_primitive(),
        "service_mask": oracle_evidence._NativeArrayEvidence.from_array(
            env._service_active_mask
        ).to_primitive(),
        "connections": {
            "user": oracle_evidence._NativeArrayEvidence.from_array(env.connections).to_primitive(),
            "uav": oracle_evidence._NativeArrayEvidence.from_array(env.uav_connections).to_primitive(),
            "uav_bs": oracle_evidence._NativeArrayEvidence.from_array(
                env.uav_bs_connections
            ).to_primitive(),
        },
        "routing_paths": oracle_evidence._routing_paths_primitive(env.routing_paths),
        "lifecycle_handles": list(env._handles),
        "lifecycle_epochs": oracle_evidence._NativeArrayEvidence.from_array(env._epochs).to_primitive(),
        "rng_states": rng_states,
        "communication_config": oracle_evidence._json_safe(env._communication_config_signature()),
        "candidate_guard_transition_state_inventory": candidate_state_inventory,
        "candidate_guard_transition_state_names": sorted(
            candidate_state_inventory
        ),
    }




class MechanicallyQualifiedOracleController:
    """Ledger-aware controller bound to one pre-behavior two-candidate proof."""

    name = Control.ORACLE.value
    uses_complete_event_ledger = True
    trains = False

    def __init__(
        self,
        source: G0EpisodeSource,
        handles: Sequence[str],
        qualification: oracle_evidence.OracleQualificationCertificate,
        safety_ledger: oracle_evidence.OracleSafetyLedger,
    ) -> None:
        validate_oracle_qualification(
            source, qualification, safety_ledger=safety_ledger
        )
        self._initialize(source, handles, qualification, safety_ledger)

    @classmethod
    def _from_validated_context(
        cls,
        handles: Sequence[str],
        qualification: oracle_evidence.OracleQualificationCertificate,
        context: oracle_evidence._ValidatedOracleSafetyContext,
    ) -> MechanicallyQualifiedOracleController:
        source, safety_ledger, _certificate = (
            _require_validated_oracle_safety_context(context)
        )
        _validate_oracle_qualification_from_context(qualification, context)
        instance = cls.__new__(cls)
        instance._initialize(source, handles, qualification, safety_ledger)
        instance._validated_safety_context = context
        return instance

    def _initialize(
        self,
        source: G0EpisodeSource,
        handles: Sequence[str],
        qualification: oracle_evidence.OracleQualificationCertificate,
        safety_ledger: oracle_evidence.OracleSafetyLedger,
    ) -> None:
        self.source = source
        self.geometry = controllers.G0ControllerGeometry.from_source(source)
        self.qualification = qualification
        self.safety_ledger = safety_ledger
        self.ownership = controllers._initial_ownership(source, handles)
        self._selected_stage = TargetLabel.parse(qualification.selected_reserve_target)
        if self._selected_stage.kind is not TargetKind.STAGE:
            raise G0RealizationError("oracle selected candidate is not a reserve")
        self._selected_reserve = next(
            handle for handle, label in self.ownership.items() if label == self._selected_stage
        )
        self._failed_primary = source.event.owner_target
        self._absent_handle = next(
            handle for handle, label in self.ownership.items() if label == self._failed_primary
        )
        candidate = next(
            row
            for row in qualification.candidates
            if row.reserve_target == self._selected_stage.key
        )
        self._latest_departure = int(candidate.latest_departure)
        self._rejoined_handle: str | None = None
        self._rejoin_step: int | None = None
        self._last_primary_step: int | None = None
        self._complete_primary_steps = 0
        self._return_ready_step: int | None = None

    def on_leave(
        self, absent_handle: str, rows: Sequence[controllers.AnonymousLifecycleRow]
    ) -> None:
        roster = controllers._roster_by_handle(rows)
        if (
            absent_handle != self._absent_handle
            or roster[absent_handle].active
            or sum(row.active for row in rows) != 7
        ):
            raise G0RealizationError("oracle observed a nonregistered leave boundary")

    def on_rejoin(self, previous_handle: str, new_handle: str, physical_step: int) -> None:
        if previous_handle != self._absent_handle or new_handle in self.ownership:
            raise G0RealizationError("oracle observed a nonregistered rejoin boundary")
        del self.ownership[previous_handle]
        self.ownership[new_handle] = self._failed_primary
        self._rejoined_handle = new_handle
        self._rejoin_step = int(physical_step)

    def target_map(
        self,
        information: controllers.G0CurrentInformation,
        *,
        physical_step: int,
    ) -> dict[str, np.ndarray]:
        roster = controllers._current_roster(self.geometry, information)
        weakest_hotspot_service = information.weakest_hotspot_service
        step = int(physical_step)
        if not math.isfinite(float(weakest_hotspot_service)):
            raise G0RealizationError("oracle current service input is nonfinite")
        if self._rejoined_handle is not None:
            row = roster[self._rejoined_handle]
            owns_failed_primary = bool(
                self.ownership.get(self._rejoined_handle) == self._failed_primary
            )
            if (
                self._rejoin_step is not None
                and step >= self._rejoin_step + 1
                and row.active
                and owns_failed_primary
                and self._last_primary_step == step - 1
            ):
                self._complete_primary_steps += 1
            if row.active and owns_failed_primary:
                self._last_primary_step = step
            if (
                self._return_ready_step is None
                and self._rejoin_step is not None
                and step >= self._rejoin_step + 1
                and self._complete_primary_steps >= 1
                and float(weakest_hotspot_service) >= SERVICE_TARGET
            ):
                self._return_ready_step = step

        result: dict[str, np.ndarray] = {}
        for handle, original_label in self.ownership.items():
            label = original_label
            if handle == self._selected_reserve:
                if step < self._latest_departure:
                    label = self._selected_stage
                    xy = self.geometry.coordinate(label)
                elif step < self.source.event.onset:
                    xy = self.geometry.gate(self._failed_primary)
                elif step < self.source.event.rejoin:
                    xy = self.geometry.coordinate(self._failed_primary)
                elif self._return_ready_step is None or step < self._return_ready_step:
                    xy = self.geometry.gate(self._failed_primary)
                else:
                    xy = self.geometry.coordinate(self._selected_stage)
            else:
                xy = self.geometry.coordinate(label)
            if handle in roster:
                result[handle] = np.concatenate((xy, [FIXED_ALTITUDE_M]))
        return result

    def evidence(self) -> dict[str, Any]:
        return {
            "controller": self.name,
            "qualification": self.qualification.to_primitive(),
            "oracle_safety_ledger": self.safety_ledger.to_primitive(),
            "selected_reserve": self._selected_stage.key,
            "latest_departure": self._latest_departure,
            "return_ready_step": self._return_ready_step,
            "future_channel_read_count": 0,
            "future_service_selection_read_count": 0,
            "candidate_count": oracle_evidence.K_SEARCH,
        }


def _controller_for_run(
    source: G0EpisodeSource,
    control: Control,
    handles: Sequence[str],
    *,
    max_speed: float,
    max_vertical_speed: float,
    time_step: float,
) -> Any:
    if control is Control.SAME_INFORMATION:
        return controllers.SameInformationController(source, handles)
    if control is Control.NO_REALLOCATION:
        return controllers.NoReallocationController(source, handles)
    if not (
        float(max_speed) == 30.0
        and float(max_vertical_speed) == 5.0
        and float(time_step) == 1.0
    ):
        raise G0RealizationError("oracle behavior requires frozen S7-S1 dynamics")
    _safety_ledger, context = _build_oracle_safety_ledger_with_context(source)
    qualification = _oracle_qualification_from_validated_context(context)
    return MechanicallyQualifiedOracleController._from_validated_context(
        handles, qualification, context
    )


def _canonical_controller_state(controller: Any) -> dict[str, Any]:
    ownership = getattr(controller, "ownership", {})
    return {
        "ownership": sorted(
            (str(handle), TargetLabel.parse(label.key).key)
            for handle, label in ownership.items()
        ),
        "leave_observed": getattr(controller, "_absent_handle", None) is not None,
        "rejoin_observed": getattr(controller, "_rejoined_handle", None) is not None,
        "returned_to_stage": bool(
            getattr(controller, "_returned_to_stage", False)
        ),
    }


def _build_selected_oracle_behavioral_execution_from_validated_context(
    context: oracle_evidence._ValidatedOracleSafetyContext,
    *,
    cell: Cell | str = Cell.EVENT,
) -> oracle_evidence.OracleBehavioralExecution:
    """Execute one causal branch and retain only replay-certificate primitives."""

    source, ledger, _certificate = _require_validated_oracle_safety_context(
        context
    )
    env = g0_environment.UAVSourceIdentifiabilityEnv(source, Cell(cell))
    try:
        env.reset()
        qualification = _oracle_qualification_from_validated_context(context)
        controller = MechanicallyQualifiedOracleController._from_validated_context(
            env._handles, qualification, context
        )
        env._oracle_behavioral_candidate_id = ledger.selected_candidate_id
        env._oracle_behavioral_trace = []
        pending_events = env.consume_boundary_events()
        target_rows: list[np.ndarray] = []
        weakest_rows: list[float] = []
        for step in range(PHYSICAL_HORIZON):
            rows = env.current_rows()
            for event in pending_events:
                if event.kind == "LEAVE":
                    controller.on_leave(event.previous_handle, rows)
                elif event.kind == "REJOIN" and event.current_handle is not None:
                    controller.on_rejoin(
                        event.previous_handle,
                        event.current_handle,
                        event.physical_step,
                    )
                else:
                    raise G0RealizationError("behavioral replay lifecycle event drifted")
            information = controllers.make_current_information(
                source,
                rows=rows,
                user_demand_mbps=np.asarray(
                    env.last_user_demand_bps, dtype=np.float64
                )
                / 1e6,
                user_delivered_rate_mbps=np.asarray(
                    env.last_user_rates_mbps, dtype=np.float64
                ),
                channel_association=np.asarray(env.connections, dtype=np.bool_)[
                    env._storage_to_internal
                ],
            )
            weakest_rows.append(float(information.weakest_hotspot_service))
            pre_action_context = g0_environment._pre_action_context(
                env, controller.ownership, ledger.selected_candidate_id
            )
            target_map = controller.target_map(
                information, physical_step=step
            )
            targets, active = controllers.target_map_to_dense(
                rows=rows,
                target_map=target_map,
            )
            target_rows.append(np.asarray(targets, dtype=np.float64).copy())
            positions_internal = np.asarray(
                env.uav_positions, dtype=np.float64
            ).copy()
            targets_internal = np.zeros_like(targets)
            targets_internal[env._storage_to_internal] = targets
            active_internal = np.zeros(PHYSICAL_UAVS, dtype=np.bool_)
            active_internal[env._storage_to_internal] = active
            actions_internal = g1_common_target_actions(
                physical_positions=positions_internal,
                target_positions=targets_internal,
                active_mask=active_internal,
                max_speed=env.max_speed,
                max_vertical_speed=env.max_vertical_speed_mps,
                time_step=env.time_step,
            )
            actions = actions_internal[env._storage_to_internal]
            storage_actions = g1_common_target_actions(
                physical_positions=np.stack([row.position for row in rows]),
                target_positions=targets,
                active_mask=active,
                max_speed=env.max_speed,
                max_vertical_speed=env.max_vertical_speed_mps,
                time_step=env.time_step,
            )
            if not np.array_equal(actions, storage_actions):
                raise G0RealizationError(
                    "common transducer lost registered permutation equivariance"
                )
            transducer_evidence = _common_transducer_evidence(
                physical_positions=positions_internal,
                target_positions=targets_internal,
                active_mask=active_internal,
                raw_action=actions_internal,
            )
            transition = env.step_dense(
                actions,
                oracle_ownership=controller.ownership,
                oracle_pre_action_context=pre_action_context,
                oracle_common_transducer_evidence=transducer_evidence,
            )
            if transition.physical_step != step:
                raise G0RealizationError("behavioral replay physical step drifted")
            pending_events = transition.boundary_events
        if pending_events:
            raise G0RealizationError("behavioral replay left lifecycle events pending")
        steps = tuple(env._oracle_behavioral_trace)
        target_evidence = oracle_evidence._NativeArrayEvidence.from_array(
            np.stack(target_rows).astype(np.float64, copy=False)
        )
        weakest_evidence = oracle_evidence._NativeArrayEvidence.from_array(
            np.asarray(weakest_rows, dtype=np.float64)
        )
        digest = sha256_json(
            {
                "selected_candidate_id": ledger.selected_candidate_id,
                "return_ready_step": controller._return_ready_step,
                "steps": [step.to_primitive() for step in steps],
                "target_schedule": target_evidence.to_primitive(),
                "pre_action_weakest_service": weakest_evidence.to_primitive(),
            }
        )
        return oracle_evidence.OracleBehavioralExecution(
            selected_candidate_id=ledger.selected_candidate_id,
            return_ready_step=controller._return_ready_step,
            steps=steps,
            target_schedule=target_evidence,
            pre_action_weakest_service=weakest_evidence,
            trace_sha256=digest,
        )
    finally:
        env.close()


def _build_selected_oracle_behavioral_execution(
    source: G0EpisodeSource,
    ledger: oracle_evidence.OracleSafetyLedger,
    *,
    cell: Cell | str = Cell.EVENT,
) -> oracle_evidence.OracleBehavioralExecution:
    return _build_selected_oracle_behavioral_execution_from_validated_context(
        _validated_oracle_safety_context(source, ledger), cell=cell
    )


def build_selected_oracle_behavioral_replay(
    source: G0EpisodeSource,
    ledger: oracle_evidence.OracleSafetyLedger,
    *,
    cell: Cell | str = Cell.EVENT,
) -> tuple[oracle_evidence.OracleSafetyStepRecord, ...]:
    """Return the safety rows for one causal selected behavioral execution."""

    return _build_selected_oracle_behavioral_execution(
        source, ledger, cell=cell
    ).steps


def _build_oracle_branch_aware_replay_evidence_from_validated_context(
    context: oracle_evidence._ValidatedOracleSafetyContext,
) -> dict[str, Any]:
    """Build the registered P/B self-replay package without reranking."""

    source, ledger, _certificate = _require_validated_oracle_safety_context(
        context
    )
    selected_label = TargetLabel.parse(ledger.selected_candidate_id)
    prebehavior_self_replay, prestate = _oracle_candidate_trace(
        source, selected_label
    )
    if sha256_json(prestate) != ledger.common_prestate_sha256:
        raise G0RealizationError("prebehavior self-replay prestate drifted")
    behavioral_execution = (
        _build_selected_oracle_behavioral_execution_from_validated_context(
            context
        )
    )
    behavioral_self_replay = (
        _build_selected_oracle_behavioral_execution_from_validated_context(
            context
        )
    )
    certificate = _validate_oracle_branch_aware_replay_from_validated_context(
        context,
        prebehavior_self_replay,
        behavioral_execution,
        behavioral_self_replay,
    )
    return {
        "schema_version": 1,
        "ledger_sha256": ledger.content_sha256,
        "selected_candidate_id": ledger.selected_candidate_id,
        "prebehavior_self_replay": prebehavior_self_replay.to_primitive(),
        "behavioral_execution": behavioral_execution.to_primitive(),
        "behavioral_self_replay": behavioral_self_replay.to_primitive(),
        "certificate": certificate.to_primitive(),
    }


def build_oracle_branch_aware_replay_evidence(
    source: G0EpisodeSource,
    ledger: oracle_evidence.OracleSafetyLedger,
) -> dict[str, Any]:
    return _build_oracle_branch_aware_replay_evidence_from_validated_context(
        _validated_oracle_safety_context(source, ledger)
    )


def run_g0_episode(
    source: G0EpisodeSource,
    *,
    control: Control | str,
    cell: Cell | str,
) -> EpisodeRunEvidence:
    """Execute one frozen no-learning episode.

    This function is the future result-bearing kernel.  Code acceptance and
    readiness do not call it over the registered 128-episode inventory.
    """

    chosen_control, chosen_cell = Control(control), Cell(cell)
    env = g0_environment.UAVSourceIdentifiabilityEnv(source, chosen_cell)
    try:
        env.reset()
        controller = _controller_for_run(
            source,
            chosen_control,
            env._handles,
            max_speed=env.max_speed,
            max_vertical_speed=env.max_vertical_speed_mps,
            time_step=env.time_step,
        )
        if chosen_control is Control.ORACLE:
            env._oracle_behavioral_candidate_id = (
                controller.safety_ledger.selected_candidate_id
            )
            env._oracle_behavioral_trace = []
        pending_events = env.consume_boundary_events()
        demand_inputs: list[np.ndarray] = []
        delivered_inputs: list[np.ndarray] = []
        association_inputs: list[np.ndarray] = []
        rates: list[np.ndarray] = []
        target_trace: list[list[list[float]]] = []
        action_trace: list[list[list[float]]] = []
        velocity_trace: list[list[list[float]]] = []
        position_trace: list[list[list[float]]] = [
            np.asarray(env.uav_positions, dtype=np.float64)[
                env._storage_to_internal
            ].tolist()
        ]
        active_mask_trace: list[list[bool]] = []
        lifecycle_events: list[LifecycleBoundaryEvent] = []
        tracker_failures = 0
        action_support_violations = 0
        ownership_violations = 0
        guard_blocks = 0
        for step in range(PHYSICAL_HORIZON):
            rows = env.current_rows()
            for event in pending_events:
                lifecycle_events.append(event)
                if event.kind == "LEAVE":
                    controller.on_leave(event.previous_handle, rows)
                elif event.kind == "REJOIN":
                    if event.current_handle is None:
                        raise G0RealizationError("rejoin event omitted its new lifecycle")
                    controller.on_rejoin(
                        event.previous_handle, event.current_handle, event.physical_step
                    )
                else:
                    raise G0RealizationError("unknown G0 lifecycle boundary")
            demand_input = np.asarray(env.last_user_demand_bps, dtype=np.float64) / 1e6
            delivered_input = np.asarray(env.last_user_rates_mbps, dtype=np.float64)
            association_input = np.asarray(env.connections, dtype=np.bool_)[
                env._storage_to_internal
            ]
            information = controllers.make_current_information(
                source,
                rows=rows,
                user_demand_mbps=demand_input,
                user_delivered_rate_mbps=delivered_input,
                channel_association=association_input,
            )
            oracle_pre_action_context = None
            if chosen_control is Control.ORACLE:
                oracle_pre_action_context = g0_environment._pre_action_context(
                    env,
                    controller.ownership,
                    controller.safety_ledger.selected_candidate_id,
                )
            target_map = controller.target_map(
                information,
                physical_step=step,
            )
            try:
                dense_targets, active = controllers.target_map_to_dense(rows=rows, target_map=target_map)
            except G0RealizationError:
                ownership_violations += 1
                raise
            positions = np.stack([row.position for row in rows])
            actions = g1_common_target_actions(
                physical_positions=positions,
                target_positions=dense_targets,
                active_mask=active,
                max_speed=env.max_speed,
                max_vertical_speed=env.max_vertical_speed_mps,
                time_step=env.time_step,
            )
            if not np.isfinite(actions).all() or np.any(np.abs(actions) > 1.0):
                action_support_violations += 1
            if not np.array_equal(actions[~active], np.zeros_like(actions[~active])):
                tracker_failures += 1
            if chosen_control is Control.ORACLE:
                positions_internal = np.asarray(
                    env.uav_positions, dtype=np.float64
                ).copy()
                targets_internal = np.zeros_like(dense_targets)
                targets_internal[env._storage_to_internal] = dense_targets
                active_internal = np.zeros(PHYSICAL_UAVS, dtype=np.bool_)
                active_internal[env._storage_to_internal] = active
                actions_internal = g1_common_target_actions(
                    physical_positions=positions_internal,
                    target_positions=targets_internal,
                    active_mask=active_internal,
                    max_speed=env.max_speed,
                    max_vertical_speed=env.max_vertical_speed_mps,
                    time_step=env.time_step,
                )
                if not np.array_equal(
                    actions_internal[env._storage_to_internal], actions
                ):
                    raise G0RealizationError(
                        "production common transducer lost permutation equivariance"
                    )
                oracle_transducer_evidence = _common_transducer_evidence(
                    physical_positions=positions_internal,
                    target_positions=targets_internal,
                    active_mask=active_internal,
                    raw_action=actions_internal,
                )
                transition = env.step_dense(
                    actions,
                    oracle_ownership=controller.ownership,
                    oracle_pre_action_context=oracle_pre_action_context,
                    oracle_common_transducer_evidence=oracle_transducer_evidence,
                )
            else:
                transition = env.step_dense(actions)
            if transition.physical_step != step:
                raise G0RealizationError("physical-step ledger is not exactly 0..499")
            if (transition.terminated or transition.truncated) and step != PHYSICAL_HORIZON - 1:
                raise G0RealizationError("G0 environment terminated before H=500")
            if not np.array_equal(transition.executed_action_mask, active):
                tracker_failures += 1
            guard_blocks += transition.backhaul_guard_blocked_actions
            demand_inputs.append(demand_input.copy())
            delivered_inputs.append(delivered_input.copy())
            association_inputs.append(association_input.copy())
            rates.append(transition.delivered_user_rates_mbps.copy())
            target_trace.append(dense_targets.tolist())
            action_trace.append(actions.tolist())
            velocity_trace.append(transition.actual_velocities.tolist())
            position_trace.append(transition.positions_after.tolist())
            active_mask_trace.append(active.tolist())
            pending_events = transition.boundary_events
        if pending_events:
            raise G0RealizationError("lifecycle boundary remained unconsumed after H=500")
        expected_event_rows = (
            ()
            if chosen_cell is Cell.NO_EVENT
            else (
                ("LEAVE", source.event.onset),
                ("REJOIN", source.event.rejoin),
            )
        )
        actual_event_rows = tuple(
            (event.kind, event.physical_step) for event in lifecycle_events
        )
        if actual_event_rows != expected_event_rows:
            raise G0RealizationError("leave/rejoin boundary inventory or timing drifted")
        delivered = np.stack(rates)
        weakest = weakest_hotspot_service(delivered, source.geometry.user_hotspots)
        metrics = compute_episode_metrics(
            weakest,
            episode_id=source.geometry.episode_id,
            control=chosen_control,
            cell=chosen_cell,
            onset=source.event.onset,
            duration=source.event.duration,
        )
        controller_evidence = controller.evidence()
        if chosen_control is Control.ORACLE:
            oracle_context = controller._validated_safety_context
            selected_label = TargetLabel.parse(
                controller.safety_ledger.selected_candidate_id
            )
            target_evidence = oracle_evidence._NativeArrayEvidence.from_array(
                np.asarray(target_trace, dtype=np.float64)
            )
            pre_action_weakest = oracle_evidence._NativeArrayEvidence.from_array(
                weakest_hotspot_service(
                    np.stack(delivered_inputs), source.geometry.user_hotspots
                )
            )
            actual_steps = tuple(env._oracle_behavioral_trace)
            actual_execution = oracle_evidence.OracleBehavioralExecution(
                selected_candidate_id=controller.safety_ledger.selected_candidate_id,
                return_ready_step=controller._return_ready_step,
                steps=actual_steps,
                target_schedule=target_evidence,
                pre_action_weakest_service=pre_action_weakest,
                trace_sha256=sha256_json(
                    {
                        "selected_candidate_id": (
                            controller.safety_ledger.selected_candidate_id
                        ),
                        "return_ready_step": controller._return_ready_step,
                        "steps": [step.to_primitive() for step in actual_steps],
                        "target_schedule": target_evidence.to_primitive(),
                        "pre_action_weakest_service": (
                            pre_action_weakest.to_primitive()
                        ),
                    }
                ),
            )
            behavioral_self_replay = (
                _build_selected_oracle_behavioral_execution_from_validated_context(
                    oracle_context, cell=chosen_cell
                )
            )
            if chosen_cell is Cell.EVENT:
                prebehavior_self_replay, _prestate = _oracle_candidate_trace(
                    source, selected_label
                )
                behavioral_certificate = (
                    _validate_oracle_branch_aware_replay_from_validated_context(
                        oracle_context,
                        prebehavior_self_replay,
                        actual_execution,
                        behavioral_self_replay,
                    )
                )
            else:
                behavioral_certificate = (
                    _validate_oracle_no_event_replay_from_validated_context(
                        oracle_context,
                        actual_execution,
                        behavioral_self_replay,
                    )
                )
            controller_evidence["behavioral_replay_certificate"] = (
                behavioral_certificate.to_primitive()
            )
        canonical_controller_state = _canonical_controller_state(controller)
        oracle_failures = int(
            chosen_control is Control.ORACLE
            and not bool(controller_evidence["qualification"]["passed"])
        )
        return EpisodeRunEvidence(
            episode_id=source.geometry.episode_id,
            control=chosen_control,
            cell=chosen_cell,
            metrics=metrics,
            source_sha256=source.to_primitive()["sha256"],
            user_demand_input_mbps=np.stack(demand_inputs),
            user_delivered_input_mbps=np.stack(delivered_inputs),
            channel_association_input=np.stack(association_inputs),
            delivered_user_rates_mbps=delivered,
            target_trace=np.asarray(target_trace, dtype=np.float64),
            raw_action_trace=np.asarray(action_trace, dtype=np.float32),
            executed_velocity_trace=np.asarray(velocity_trace, dtype=np.float64),
            position_trace=np.asarray(position_trace, dtype=np.float64),
            active_mask_trace=np.asarray(active_mask_trace, dtype=np.bool_),
            controller_evidence=controller_evidence,
            target_trace_sha256=sha256_json(target_trace),
            raw_action_trace_sha256=sha256_json(action_trace),
            executed_velocity_trace_sha256=sha256_json(velocity_trace),
            executed_position_trace_sha256=sha256_json(position_trace),
            service_trace_sha256=hashlib.sha256(
                delivered.astype(np.float64).tobytes(order="C")
            ).hexdigest(),
            controller_state_sha256=sha256_json(canonical_controller_state),
            lifecycle_events=tuple(lifecycle_events),
            tracker_failures=tracker_failures,
            action_support_violations=action_support_violations,
            ownership_violations=ownership_violations,
            backhaul_guard_blocked_actions=guard_blocks,
            oracle_qualification_failures=oracle_failures,
            weakest_service=weakest,
        )
    finally:
        env.close()




def _reconstruct_controller_trace(
    source: G0EpisodeSource,
    run: EpisodeRunEvidence,
) -> tuple[np.ndarray, dict[str, Any], str]:
    handles = list(controllers.initial_lifecycle_handles(source))
    owner_row = source.assignment.row_to_target.index(source.event.owner_target.key)
    controller = _controller_for_run(
        source,
        run.control,
        handles,
        max_speed=30.0,
        max_vertical_speed=5.0,
        time_step=1.0,
    )
    targets: list[np.ndarray] = []
    for step in range(PHYSICAL_HORIZON):
        active = run.active_mask_trace[step]
        if run.cell is Cell.EVENT and step == source.event.rejoin:
            previous = handles[owner_row]
            current = controllers.replacement_lifecycle_handle(source, previous)
            handles[owner_row] = current
        rows = tuple(
            controllers.AnonymousLifecycleRow(
                handle=handles[row],
                position=run.position_trace[step, row],
                velocity=(
                    np.zeros(3, dtype=np.float64)
                    if step == 0
                    else run.executed_velocity_trace[step - 1, row]
                ),
                active=bool(active[row]),
                service_available=bool(active[row]),
            )
            for row in range(PHYSICAL_UAVS)
        )
        if run.cell is Cell.EVENT and step == source.event.onset:
            controller.on_leave(handles[owner_row], rows)
        if run.cell is Cell.EVENT and step == source.event.rejoin:
            controller.on_rejoin(previous, handles[owner_row], step)
        information = controllers.make_current_information(
            source,
            rows=rows,
            user_demand_mbps=run.user_demand_input_mbps[step],
            user_delivered_rate_mbps=run.user_delivered_input_mbps[step],
            channel_association=run.channel_association_input[step],
        )
        target_map = controller.target_map(
            information,
            physical_step=step,
        )
        dense, reconstructed_active = controllers.target_map_to_dense(
            rows=rows,
            target_map=target_map,
        )
        if not np.array_equal(reconstructed_active, active):
            raise G0RealizationError("controller reconstruction changed active mask")
        targets.append(dense)
    evidence = controller.evidence()
    state_digest = sha256_json(_canonical_controller_state(controller))
    return np.stack(targets), evidence, state_digest


def _authoritative_replay_errors(
    source: G0EpisodeSource,
    run: EpisodeRunEvidence,
) -> tuple[str, ...]:
    """Replay the authoritative environment law and compare every result-bearing row."""

    replay = run_g0_episode(source, control=run.control, cell=run.cell)
    errors: list[str] = []
    arrays = (
        "user_demand_input_mbps",
        "user_delivered_input_mbps",
        "channel_association_input",
        "delivered_user_rates_mbps",
        "target_trace",
        "raw_action_trace",
        "executed_velocity_trace",
        "position_trace",
        "active_mask_trace",
        "weakest_service",
    )
    for name in arrays:
        if not np.array_equal(getattr(run, name), getattr(replay, name)):
            errors.append(f"environment_replay_{name}")
    scalar_fields = (
        "episode_id",
        "control",
        "cell",
        "source_sha256",
        "target_trace_sha256",
        "raw_action_trace_sha256",
        "executed_velocity_trace_sha256",
        "executed_position_trace_sha256",
        "service_trace_sha256",
        "controller_state_sha256",
        "tracker_failures",
        "action_support_violations",
        "ownership_violations",
        "backhaul_guard_blocked_actions",
        "oracle_qualification_failures",
    )
    for name in scalar_fields:
        if getattr(run, name) != getattr(replay, name):
            errors.append(f"environment_replay_{name}")
    if run.metrics.to_primitive() != replay.metrics.to_primitive():
        errors.append("environment_replay_metrics")
    stored_controller_evidence = dict(run.controller_evidence)
    replay_controller_evidence = dict(replay.controller_evidence)
    if run.control is Control.ORACLE:
        stored_has_certificate = (
            "behavioral_replay_certificate" in stored_controller_evidence
        )
        replay_has_certificate = (
            "behavioral_replay_certificate" in replay_controller_evidence
        )
        stored_certificate = stored_controller_evidence.pop(
            "behavioral_replay_certificate", None
        )
        replay_certificate = replay_controller_evidence.pop(
            "behavioral_replay_certificate", None
        )
        if stored_controller_evidence != replay_controller_evidence:
            errors.append("environment_replay_controller_evidence")
        if (
            not stored_has_certificate
            or not replay_has_certificate
            or not isinstance(stored_certificate, Mapping)
            or not isinstance(replay_certificate, Mapping)
            or dict(stored_certificate) != dict(replay_certificate)
        ):
            errors.append("environment_replay_certificate")
    elif stored_controller_evidence != replay_controller_evidence:
        errors.append("environment_replay_controller_evidence")
    if tuple(event.to_primitive() for event in run.lifecycle_events) != tuple(
        event.to_primitive() for event in replay.lifecycle_events
    ):
        errors.append("environment_replay_lifecycle")
    return tuple(errors)


def _validate_run_primitives(
    source: G0EpisodeSource,
    run: EpisodeRunEvidence,
) -> tuple[EpisodeMetrics, tuple[str, ...]]:
    errors: list[str] = []
    errors.extend(_authoritative_replay_errors(source, run))
    if run.episode_id != source.geometry.episode_id:
        errors.append("episode_identity")
    if run.source_sha256 != source.to_primitive()["sha256"]:
        errors.append("source_digest")
    expected_delivered_inputs = np.concatenate(
        (
            np.zeros((1, GROUND_USERS), dtype=np.float64),
            run.delivered_user_rates_mbps[:-1],
        ),
        axis=0,
    )
    if not np.array_equal(run.user_delivered_input_mbps, expected_delivered_inputs):
        errors.append("current_service_history")
    reconstructed_weakest = weakest_hotspot_service(
        run.delivered_user_rates_mbps, source.geometry.user_hotspots
    )
    if not np.array_equal(run.weakest_service, reconstructed_weakest):
        errors.append("weakest_service")
    reconstructed_metrics = compute_episode_metrics(
        reconstructed_weakest,
        episode_id=run.episode_id,
        control=run.control,
        cell=run.cell,
        onset=source.event.onset,
        duration=source.event.duration,
    )
    if run.metrics.to_primitive() != reconstructed_metrics.to_primitive():
        errors.append("metric_arithmetic")
    try:
        expected_targets, expected_controller_evidence, expected_state_digest = (
            _reconstruct_controller_trace(source, run)
        )
        if not np.array_equal(run.target_trace, expected_targets):
            errors.append("controller_target_trace")
        stored_controller_evidence = dict(run.controller_evidence)
        if run.control is Control.ORACLE:
            if "behavioral_replay_certificate" not in stored_controller_evidence:
                errors.append("controller_evidence_certificate")
            else:
                stored_certificate = stored_controller_evidence.pop(
                    "behavioral_replay_certificate"
                )
                if not isinstance(stored_certificate, Mapping):
                    errors.append("controller_evidence_certificate")
        if stored_controller_evidence != expected_controller_evidence:
            errors.append("controller_evidence")
        if run.controller_state_sha256 != expected_state_digest:
            errors.append("controller_state")
    except G0RealizationError:
        errors.append("controller_reconstruction")
    digest_rows = {
        "target_trace": (run.target_trace_sha256, sha256_json(run.target_trace.tolist())),
        "raw_action_trace": (
            run.raw_action_trace_sha256,
            sha256_json(run.raw_action_trace.tolist()),
        ),
        "executed_velocity_trace": (
            run.executed_velocity_trace_sha256,
            sha256_json(run.executed_velocity_trace.tolist()),
        ),
        "executed_position_trace": (
            run.executed_position_trace_sha256,
            sha256_json(run.position_trace.tolist()),
        ),
        "service_trace": (
            run.service_trace_sha256,
            hashlib.sha256(
                run.delivered_user_rates_mbps.astype(np.float64).tobytes(order="C")
            ).hexdigest(),
        ),
    }
    errors.extend(
        name for name, (stored, expected) in digest_rows.items() if stored != expected
    )
    expected_mask = np.stack(
        [
            np.asarray(
                [
                    source.event.active(step, run.cell)
                    if row == source.assignment.row_to_target.index(
                        source.event.owner_target.key
                    )
                    else True
                    for row in range(PHYSICAL_UAVS)
                ],
                dtype=np.bool_,
            )
            for step in range(PHYSICAL_HORIZON)
        ]
    )
    if not np.array_equal(run.active_mask_trace, expected_mask):
        errors.append("active_mask")
    if not np.array_equal(
        run.position_trace[0, :, :2], source.geometry.physical_xy
    ) or not np.array_equal(
        run.position_trace[:, :, 2],
        np.full((PHYSICAL_HORIZON + 1, PHYSICAL_UAVS), FIXED_ALTITUDE_M),
    ):
        errors.append("position_provenance")
    for step in range(PHYSICAL_HORIZON):
        expected_actions = actions_toward_targets(
            physical_positions=run.position_trace[step],
            target_positions=run.target_trace[step],
            active_mask=run.active_mask_trace[step],
            max_speed=30.0,
            max_vertical_speed=5.0,
            time_step=1.0,
        )
        if not np.array_equal(run.raw_action_trace[step], expected_actions):
            errors.append("target_tracker")
            break
    inactive = ~run.active_mask_trace
    if (
        not np.array_equal(
            run.raw_action_trace[inactive],
            np.zeros((int(inactive.sum()), ACTION_DIM), dtype=np.float32),
        )
        or not np.array_equal(
            run.executed_velocity_trace[inactive],
            np.zeros((int(inactive.sum()), 3), dtype=np.float64),
        )
    ):
        errors.append("inactive_authority")
    expected_lifecycle = (
        ()
        if run.cell is Cell.NO_EVENT
        else (("LEAVE", source.event.onset), ("REJOIN", source.event.rejoin))
    )
    actual_lifecycle = tuple(
        (event.kind, event.physical_step) for event in run.lifecycle_events
    )
    if actual_lifecycle != expected_lifecycle:
        errors.append("lifecycle_inventory")
    if run.cell is Cell.EVENT and len(run.lifecycle_events) == 2:
        leave, rejoin = run.lifecycle_events
        if (
            leave.previous_handle != rejoin.previous_handle
            or rejoin.current_handle is None
            or rejoin.current_handle == leave.previous_handle
        ):
            errors.append("epoch_replacement")
    if any(
        int(value) != 0
        for value in (
            run.tracker_failures,
            run.action_support_violations,
            run.ownership_violations,
        )
    ):
        errors.append("registered_runtime_counter")
    if run.control is Control.ORACLE:
        try:
            ledger = oracle_evidence.oracle_safety_ledger_from_primitive(
                run.controller_evidence["oracle_safety_ledger"]
            )
            qualification = oracle_qualification_from_safety_ledger(source, ledger)
            if (
                run.oracle_qualification_failures != 0
                or run.controller_evidence.get("qualification")
                != qualification.to_primitive()
                or run.controller_evidence.get("behavioral_replay_certificate", {}).get(
                    "ledger_sha256"
                )
                != ledger.content_sha256
                or run.controller_evidence.get("behavioral_replay_certificate", {}).get(
                    "behavioral_replay_sha256"
                )
                is None
            ):
                errors.append("oracle_qualification")
        except (G0RealizationError, KeyError, TypeError, ValueError):
            errors.append("oracle_qualification")
    return reconstructed_metrics, tuple(sorted(set(errors)))


def build_episode_validity_record(
    source: G0EpisodeSource,
    runs: Mapping[tuple[Control | str, Cell | str], EpisodeRunEvidence],
) -> tuple[EpisodeValidityRecord, dict[tuple[Control, Cell], EpisodeMetrics]]:
    """Reconstruct one validity row from the six actual control/cell traces."""

    normalized: dict[tuple[Control, Cell], EpisodeRunEvidence] = {}
    for key, run in runs.items():
        normalized_key = (Control(key[0]), Cell(key[1]))
        if normalized_key in normalized:
            raise G0RealizationError("duplicate G0 episode run identity")
        if run.control is not normalized_key[0] or run.cell is not normalized_key[1]:
            raise G0RealizationError("mapped run identity differs from primitive run")
        normalized[normalized_key] = run
    expected_keys = {(control, cell) for control in Control for cell in Cell}
    if set(normalized) != expected_keys:
        raise G0RealizationError("episode validity requires all six control/cell runs")
    metrics: dict[tuple[Control, Cell], EpisodeMetrics] = {}
    per_run_errors: list[str] = []
    for key, run in normalized.items():
        metric, errors = _validate_run_primitives(source, run)
        metrics[key] = metric
        per_run_errors.extend(errors)

    same_no = normalized[(Control.SAME_INFORMATION, Cell.NO_EVENT)]
    none_no = normalized[(Control.NO_REALLOCATION, Cell.NO_EVENT)]
    no_event_pairs = (
        (same_no.user_demand_input_mbps, none_no.user_demand_input_mbps),
        (same_no.user_delivered_input_mbps, none_no.user_delivered_input_mbps),
        (same_no.channel_association_input, none_no.channel_association_input),
        (same_no.target_trace, none_no.target_trace),
        (same_no.raw_action_trace, none_no.raw_action_trace),
        (same_no.executed_velocity_trace, none_no.executed_velocity_trace),
        (same_no.position_trace, none_no.position_trace),
        (same_no.delivered_user_rates_mbps, none_no.delivered_user_rates_mbps),
    )
    no_event_equal = all(np.array_equal(left, right) for left, right in no_event_pairs)
    no_event_equal &= same_no.controller_state_sha256 == none_no.controller_state_sha256

    same_event = normalized[(Control.SAME_INFORMATION, Cell.EVENT)]
    none_event = normalized[(Control.NO_REALLOCATION, Cell.EVENT)]
    selected_handle = same_event.controller_evidence.get("selected_reserve")
    initial_handles = controllers.initial_lifecycle_handles(source)
    selected_row = (
        initial_handles.index(str(selected_handle))
        if selected_handle in initial_handles
        else -1
    )
    owner_row = source.assignment.row_to_target.index(source.event.owner_target.key)
    survivor_rows = [
        row for row in range(PHYSICAL_UAVS) if row not in {owner_row, selected_row}
    ]
    survivor_equal = bool(
        selected_row >= 0
        and np.array_equal(
            same_event.target_trace[:, survivor_rows],
            none_event.target_trace[:, survivor_rows],
        )
        and np.array_equal(
            same_event.raw_action_trace[:, survivor_rows],
            none_event.raw_action_trace[:, survivor_rows],
        )
        and np.array_equal(
            same_event.position_trace[:, survivor_rows],
            none_event.position_trace[:, survivor_rows],
        )
    )
    source_digest = source.to_primitive()["sha256"]
    tracker_failures = sum("target_tracker" in error for error in per_run_errors)
    metric_failures = sum("metric_arithmetic" in error for error in per_run_errors)
    missing_or_nonfinite = sum(
        name.endswith("trace") or name == "position_provenance"
        for name in per_run_errors
    )
    permutation_order = np.asarray((3, 1, 7, 0, 6, 2, 5, 4), dtype=np.int64)
    permutation_failures = 0
    for run in normalized.values():
        permuted = actions_toward_targets(
            physical_positions=run.position_trace[0, permutation_order],
            target_positions=run.target_trace[0, permutation_order],
            active_mask=run.active_mask_trace[0, permutation_order],
            max_speed=30.0,
            max_vertical_speed=5.0,
            time_step=1.0,
        )
        restored = np.empty_like(permuted)
        restored[permutation_order] = permuted
        permutation_failures += int(
            not np.array_equal(restored, run.raw_action_trace[0])
        )
    record = EpisodeValidityRecord(
        episode_id=source.geometry.episode_id,
        source_event_digest=source_digest,
        source_no_event_digest=source_digest,
        sameinfo_no_event_digest=sha256_json(
            {
                "target": same_no.target_trace_sha256,
                "raw": same_no.raw_action_trace_sha256,
                "executed": same_no.executed_velocity_trace_sha256,
                "position": same_no.executed_position_trace_sha256,
                "service": same_no.service_trace_sha256,
                "controller": same_no.controller_state_sha256,
            }
        ),
        no_reallocation_no_event_digest=sha256_json(
            {
                "target": none_no.target_trace_sha256,
                "raw": none_no.raw_action_trace_sha256,
                "executed": none_no.executed_velocity_trace_sha256,
                "position": none_no.executed_position_trace_sha256,
                "service": none_no.service_trace_sha256,
                "controller": none_no.controller_state_sha256,
            }
        ),
        geometry_support_violations=int(
            geometry_support_certificate(
                map_width=source.geometry.map_width,
                map_height=source.geometry.map_height,
                base_xy=source.geometry.base_xy,
            )["violation_count"]
        ),
        rng_namespace_violations=0,
        pairing_mismatches=int(not no_event_equal),
        assignment_failures=int(not source.assignment.passed),
        tracker_failures=tracker_failures,
        oracle_qualification_failures=sum(
            run.oracle_qualification_failures for run in normalized.values()
        ),
        action_support_violations=sum(
            run.action_support_violations for run in normalized.values()
        ),
        information_visibility_violations=sum(
            int(
                any(
                    int(value) != 0
                    for key, value in run.controller_evidence.items()
                    if key.endswith("read_count")
                )
            )
            for run in normalized.values()
        ),
        ownership_violations=sum(run.ownership_violations for run in normalized.values()),
        survivor_continuity_violations=int(not survivor_equal),
        permutation_mismatches=permutation_failures,
        metric_reconstruction_mismatches=metric_failures,
        missing_rows=missing_or_nonfinite + len(set(per_run_errors)),
        nonfinite_rows=0,
        oracle_exact_physical_impossibility=False,
    )
    return record, metrics



def build_analysis_evidence(
    episode_sources: Sequence[G0EpisodeSource],
    run_rows: Mapping[
        tuple[Control | str, Cell | str], Sequence[EpisodeRunEvidence]
    ],
    *,
    index_plan: np.ndarray | None = None,
) -> dict[str, Any]:
    """Only conclusion-bearing analyzer: reconstruct from six primitive traces."""

    sources = tuple(episode_sources)
    if len(sources) != len(EPISODE_IDS) or tuple(
        item.geometry.episode_id for item in sources
    ) != EPISODE_IDS:
        raise G0RealizationError("analysis sources are not exact episode IDs 0..127")
    normalized_rows: dict[tuple[Control, Cell], tuple[EpisodeRunEvidence, ...]] = {}
    for key, values in run_rows.items():
        normalized_key = (Control(key[0]), Cell(key[1]))
        if normalized_key in normalized_rows:
            raise G0RealizationError("duplicate control/cell run inventory")
        rows = tuple(values)
        if len(rows) != len(EPISODE_IDS) or tuple(
            row.episode_id for row in rows
        ) != EPISODE_IDS:
            raise G0RealizationError("run inventory is not ordered episode IDs 0..127")
        normalized_rows[normalized_key] = rows
    expected_keys = {(control, cell) for control in Control for cell in Cell}
    if set(normalized_rows) != expected_keys:
        raise G0RealizationError("analysis requires six exact control/cell inventories")

    metrics: dict[tuple[Control, Cell], list[EpisodeMetrics]] = {
        key: [] for key in expected_keys
    }
    validity: list[EpisodeValidityRecord] = []
    for episode_id, episode_source in enumerate(sources):
        record, reconstructed = build_episode_validity_record(
            episode_source,
            {
                key: normalized_rows[key][episode_id]
                for key in expected_keys
            },
        )
        validity.append(record)
        for key, metric in reconstructed.items():
            metrics[key].append(metric)
    return _build_analysis_from_reconstructed_rows(
        metrics,
        validity,
        index_plan=index_plan,
    )
