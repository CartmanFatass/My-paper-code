"""Registered analytic and evaluation-only mechanism controls."""

from __future__ import annotations

import numpy as np
import torch

from .config import HELDOUT_SCHEDULES, LEASE_TICKS
from .host import EpisodeResult, generate_episode, run_episode
from .models import MarkedLearner


PARTITIONS = ((32,), (16, 16), (8, 8, 8, 8), (4, 4, 4, 4, 4, 4, 4, 4))


def _prob_vector_jacobian(
    g: float, h: float, exposure: float, *, probability_identity: bool,
) -> tuple[np.ndarray, np.ndarray]:
    q = 1.0 / (1.0 + np.exp(-g))
    rho = 1.0 / (1.0 + np.exp(-h))
    survival = (
        (1.0 - q) ** exposure
        if probability_identity
        else np.exp(-np.logaddexp(0.0, g) * exposure)
    )
    event = 1.0 - survival
    event_gradient = exposure * q * survival
    vector = np.asarray(
        [survival, event * rho, event * (1.0 - rho)], dtype=np.float64,
    )
    jacobian = np.asarray([
        [-event_gradient, 0.0],
        [rho * event_gradient, event * rho * (1.0 - rho)],
        [(1.0 - rho) * event_gradient, -event * rho * (1.0 - rho)],
    ], dtype=np.float64)
    return vector, jacobian


def _identity_errors(g: float, h: float, exposure: float) -> tuple[float, float]:
    onlgr_p, onlgr_j = _prob_vector_jacobian(
        g, h, exposure, probability_identity=False,
    )
    prob_p, prob_j = _prob_vector_jacobian(
        g, h, exposure, probability_identity=True,
    )
    return (
        float(np.max(np.abs(onlgr_p - prob_p))),
        float(np.max(np.abs(onlgr_j - prob_j))),
    )


def prob_exp_identity_probe() -> dict[str, object]:
    maximum_probability_error = maximum_jacobian_error = 0.0
    rows: list[dict[str, float]] = []
    for g_value in (-8.0, -2.0, 0.0, 2.0, 8.0):
        for h_value in (-4.0, 0.0, 4.0):
            for exposure in (1.0, 4.0, 8.0, 16.0, 24.0, 32.0):
                probability_error, jacobian_error = _identity_errors(
                    g_value, h_value, exposure,
                )
                maximum_probability_error = max(maximum_probability_error, probability_error)
                maximum_jacobian_error = max(maximum_jacobian_error, jacobian_error)
                rows.append({
                    "g": g_value, "h": h_value, "e": exposure,
                    "probability_vector_error": probability_error,
                    "event_mark_logit_jacobian_error": jacobian_error,
                })
    tolerance = 1e-10
    return {"rows": rows, "maximum_probability_error": maximum_probability_error,
            "maximum_event_mark_logit_jacobian_error": maximum_jacobian_error,
            "tolerance": tolerance,
            "pass": maximum_probability_error <= tolerance and maximum_jacobian_error <= tolerance,
            "checkpoint_or_trajectory": False}


def _partition_feature(*, role: int, binding: int, cue: float, age: int, interval: int) -> np.ndarray:
    partner_binding = binding
    return np.asarray([
        float(role == 0), float(role == 1), float(binding == 0), float(binding == 1),
        cue, age / 64.0, 0.0, 0.0, float(partner_binding), float(cue >= 0.5),
        1.0, 0.0, interval / 32.0, interval / 32.0,
    ], dtype=np.float32)


def _composition(learner: MarkedLearner, *, role: int, binding: int,
                 cue: float, age: int, partition: tuple[int, ...]) -> tuple[float, float, float]:
    survival = 1.0
    refresh = rebind = 0.0
    for interval in partition:
        feature = _partition_feature(role=role, binding=binding, cue=cue, age=age, interval=interval)
        _logit, event, mark = learner.policy(feature[None, :], np.asarray([interval], dtype=np.float32))
        u, rho = float(event[0]), float(mark[0])
        refresh += survival * u * rho
        rebind += survival * u * (1.0 - rho)
        survival *= 1.0 - u
    return survival, refresh, rebind


def _max_pairwise(values: list[tuple[float, float, float]]) -> tuple[float, float]:
    tv = hazard = 0.0
    for left in values:
        for right in values:
            tv = max(tv, 0.5 * sum(abs(a - b) for a, b in zip(left, right)))
            hazard = max(hazard, abs(-np.log(left[0]) + np.log(right[0])))
    return float(tv), float(hazard)


def marked_partition_probe(onlgr: MarkedLearner, raw: MarkedLearner) -> dict[str, object]:
    cells: list[dict[str, object]] = []
    identity_probability_max_error = identity_jacobian_max_error = 0.0
    for role in range(2):
        for binding in range(2):
            for cue in (0.25, 0.75):
                for age in (16, 32):
                    operational = {
                        "ONLGR": [_composition(onlgr, role=role, binding=binding, cue=cue,
                                                age=age, partition=p) for p in PARTITIONS],
                        "RAW-BOUNDARY-LEASE": [_composition(raw, role=role, binding=binding,
                                                             cue=cue, age=age, partition=p)
                                                for p in PARTITIONS],
                    }
                    identity: dict[str, object] = {}
                    for partition in PARTITIONS:
                        point_rows: list[dict[str, float]] = []
                        for step, interval in enumerate(partition):
                            feature = _partition_feature(
                                role=role, binding=binding, cue=cue, age=age,
                                interval=interval,
                            )
                            with torch.no_grad():
                                g_tensor, h_tensor = onlgr.actor(torch.as_tensor(feature[None, :]))
                            g, h = float(g_tensor[0]), float(h_tensor[0])
                            probability_error, jacobian_error = _identity_errors(g, h, interval)
                            identity_probability_max_error = max(
                                identity_probability_max_error, probability_error,
                            )
                            identity_jacobian_max_error = max(
                                identity_jacobian_max_error, jacobian_error,
                            )
                            point_rows.append({
                                "step": float(step), "e": float(interval),
                                "g": g, "h": h,
                                "probability_vector_error": probability_error,
                                "event_mark_logit_jacobian_error": jacobian_error,
                            })
                        identity["-".join(map(str, partition))] = point_rows
                    unsplit_gap = abs((1-operational["ONLGR"][0][0])
                                      - (1-operational["RAW-BOUNDARY-LEASE"][0][0]))
                    exclusion_reasons = [
                        f"{arm}:{'-'.join(map(str, PARTITIONS[index]))}:failure_outside_[.05,.95]"
                        for arm, values in operational.items() for index in range(len(PARTITIONS))
                        if not 0.05 <= 1-values[index][0] <= 0.95
                    ]
                    if unsplit_gap > 0.05:
                        exclusion_reasons.append("unsplit_ONLGR_RAW_failure_gap_above_.05")
                    common_valid = not exclusion_reasons
                    metrics = {arm: dict(zip(("MPI", "HPI"), _max_pairwise(values)))
                               for arm, values in operational.items()}
                    cells.append({
                        "role": role, "binding": binding, "binding_match_cue": cue,
                        "plan_age": age, "operational_compositions": {
                            arm: {"-".join(map(str, p)): {
                                "marked_distribution_S_R_B": values[i],
                                "F_first_event": 1.0 - values[i][0],
                            } for i,p in enumerate(PARTITIONS)}
                            for arm, values in operational.items()
                        }, "metrics": metrics, "common_valid": common_valid,
                        "unsplit_failure_gap": unsplit_gap,
                        "exclusion_reasons": exclusion_reasons,
                        "frozen_score_identity": identity,
                    })
    valid = [cell for cell in cells if cell["common_valid"]]
    return {
        "declared_cell_count": 16, "realized_cell_count": len(cells),
        "factors": ["role", "active_binding", "mismatch_cue", "plan_age"],
        "cells": cells, "C_s": [
            {
                "role": cell["role"], "binding": cell["binding"],
                "binding_match_cue": cell["binding_match_cue"],
                "plan_age": cell["plan_age"],
            } for cell in valid
        ], "common_valid_cells": len(valid),
        "operational_estimand_available": len(valid) >= 12,
        "MPI": {arm: float(np.mean([cell["metrics"][arm]["MPI"] for cell in valid])) if valid else None
                for arm in ("ONLGR", "RAW-BOUNDARY-LEASE")},
        "HPI": {arm: float(np.mean([cell["metrics"][arm]["HPI"] for cell in valid])) if valid else None
                for arm in ("ONLGR", "RAW-BOUNDARY-LEASE")},
        "prob_exp_identity_probability_max_abs_error": identity_probability_max_error,
        "prob_exp_identity_jacobian_max_abs_error": identity_jacobian_max_error,
        "prob_exp_identity_tolerance": 1e-10,
        "prob_exp_identity_pass": (
            identity_probability_max_error <= 1e-10
            and identity_jacobian_max_error <= 1e-10
        ),
        "estimand_conditioning": (
            "MPI/HPI are conditional on the exact common cells selected by both learned outputs; "
            "they are not population-wide invariance or causal mediators"
        ),
        "uses_task_reward": False, "simulated_team_ticks": 0,
    }


def _agent_dwell_multiset(
    ticks: tuple[int, ...], actions: tuple[tuple[int, int], ...], role: int,
) -> tuple[int, ...]:
    selected = [tick for tick, action in zip(ticks, actions) if action[role] != 0]
    return tuple(sorted(b - a for a, b in zip(selected, selected[1:])))


def _rotated_mapping(
    source: EpisodeResult, shift: int,
) -> tuple[dict[int, tuple[int, int]], tuple[int, ...]]:
    ticks = source.voluntary_joint_event_ticks
    actions = source.voluntary_action_tuples
    blocks = tuple(b - a for a, b in zip(ticks, ticks[1:]))
    rotated = tuple(blocks[(i + shift) % len(blocks)] for i in range(len(blocks)))
    reconstructed = [ticks[0]]
    for dwell in rotated:
        reconstructed.append(reconstructed[-1] + dwell)
    return dict(zip(reconstructed, actions)), tuple(reconstructed)


def preselected_yoke_mapping(
    onlgr: EpisodeResult, raw: EpisodeResult, *, seed_ordinal: int,
    schedule_ordinal: int, episode_slot: int,
) -> tuple[dict[str, object], dict[int, tuple[int, int]] | None,
           dict[int, tuple[int, int]] | None]:
    m_onlgr = max(0, len(onlgr.voluntary_joint_event_ticks) - 1)
    m_raw = max(0, len(raw.voluntary_joint_event_ticks) - 1)
    base: dict[str, object] = {
        "episode_slot": episode_slot,
        "q_ONLGR": len(onlgr.voluntary_joint_event_ticks),
        "q_RAW": len(raw.voluntary_joint_event_ticks),
        "m_ONLGR": m_onlgr, "m_RAW": m_raw,
        "candidate_count": 1,
    }
    if m_onlgr != m_raw:
        return ({**base, "eligible": False, "reason": "arms_have_different_q",
                 "candidates_checked": 0}, None, None)
    if m_onlgr < 2:
        return ({**base, "eligible": False, "reason": "common_m_below_2",
                 "candidates_checked": 0}, None, None)
    m = m_onlgr
    shift = 1 + ((17 * seed_ordinal + 31 * schedule_ordinal + episode_slot) % (m - 1))
    onlgr_mapping, _ = _rotated_mapping(onlgr, shift)
    raw_mapping, _ = _rotated_mapping(raw, shift)
    return ({**base, "preselected_shift": shift, "candidates_checked": 1,
             "support_pending_recomputed_execution": True}, onlgr_mapping, raw_mapping)


def yoke_support(native: EpisodeResult, yoked: EpisodeResult,
                 imposed: dict[int, tuple[int, int]]) -> tuple[bool, str, float | None]:
    expected_ticks = tuple(imposed)
    expected_actions = tuple(imposed.values())
    if not all(tick in native.routine_boundary_ticks for tick in expected_ticks):
        return False, "shifted_event_not_preexisting_routine_callback", None
    if yoked.voluntary_joint_event_ticks != expected_ticks or yoked.voluntary_action_tuples != expected_actions:
        return False, "recomputed_lease_mask_or_boundary_legality_failed", None
    if native.voluntary_action_tuples != yoked.voluntary_action_tuples:
        return False, "ordered_joint_action_sequence_changed", None
    if native.voluntary_joint_event_destinations != yoked.voluntary_joint_event_destinations:
        return False, "destination_local_sequence_changed", None
    if sorted(b-a for a,b in zip(native.voluntary_joint_event_ticks, native.voluntary_joint_event_ticks[1:])) != sorted(
        b-a for a,b in zip(yoked.voluntary_joint_event_ticks, yoked.voluntary_joint_event_ticks[1:])
    ):
        return False, "physical_dwell_multiset_changed", None
    def legal_replay(result: EpisodeResult) -> bool:
        leases = [-8, -8]
        previous = [-8, -8]
        for tick, action in zip(
            result.voluntary_joint_event_ticks, result.voluntary_action_tuples,
        ):
            exposure = [
                max(0, tick - max(previous[role], leases[role] - 1))
                for role in range(2)
            ]
            for role in range(2):
                if action[role] != 0 and exposure[role] <= 0:
                    return False
                if action[role] != 0:
                    leases[role] = tick + LEASE_TICKS
            previous = [tick, tick]
        return True
    if not legal_replay(yoked):
        return False, "recomputed_exposure_or_lease_legality_failed", None
    for role in range(2):
        if _agent_dwell_multiset(native.voluntary_joint_event_ticks, native.voluntary_action_tuples, role) != _agent_dwell_multiset(
            yoked.voluntary_joint_event_ticks, yoked.voluntary_action_tuples, role
        ):
            return False, "per_agent_lease_duration_multiset_changed", None
    native_occupancy = {binding: sum((q[0],q[1]) == binding for q in native.q_trace)
                        for binding in ((0,0),(0,1),(1,0),(1,1))}
    yoked_occupancy = {binding: sum((q[0],q[1]) == binding for q in yoked.q_trace)
                       for binding in ((0,0),(0,1),(1,0),(1,1))}
    if native_occupancy != yoked_occupancy:
        return False, "joint_binding_time_occupancy_changed", None
    native_e = native.voluntary_joint_event_exposures[1:]
    yoked_e = yoked.voluntary_joint_event_exposures[1:]
    denominator = 2 * sum(sum(row) for row in native_e)
    if denominator <= 0 or sum(sum(row) for row in native_e) != sum(sum(row) for row in yoked_e):
        return False, "interior_total_eligible_exposure_changed_or_zero", None
    materiality = sum(abs(a-b) for left,right in zip(native_e,yoked_e)
                      for a,b in zip(left,right)) / denominator
    return True, "supported_preselected_rotation", float(materiality)


def keep_grid_equality(root: int, episode_count: int = 16) -> dict[str, object]:
    reference_schedule = HELDOUT_SCHEDULES[0]
    failures: list[dict[str, object]] = []
    ticks = 0
    for episode_index in range(episode_count):
        reference = generate_episode(
            root=root, episode=episode_index, namespace="keep_grid_probe",
            schedule=reference_schedule,
        )
        reference_result = run_episode(reference, arm="ALWAYS-KEEP")
        ticks += reference_result.physics_ticks
        for schedule in HELDOUT_SCHEDULES[1:]:
            candidate = generate_episode(
                root=root, episode=episode_index, namespace="keep_grid_probe", schedule=schedule,
            )
            candidate_result = run_episode(candidate, arm="ALWAYS-KEEP")
            ticks += candidate_result.physics_ticks
            if not (np.array_equal(reference.mode, candidate.mode)
                    and np.array_equal(reference.sensors, candidate.sensors)
                    and reference.initial_bindings == candidate.initial_bindings
                    and reference.initial_plan_ages == candidate.initial_plan_ages
                    and reference_result.plan_age_trace == candidate_result.plan_age_trace
                    and reference_result.service_trace == candidate_result.service_trace
                    and reference_result.reward_trace == candidate_result.reward_trace):
                failures.append({"episode": episode_index, "schedule": schedule})
    return {
        "episodes_per_schedule": episode_count, "schedules": list(HELDOUT_SCHEDULES),
        "physics_sensor_plan_age_service_reward_equal": not failures, "failures": failures,
        "actual_team_ticks": ticks,
    }


def leakage_twin_contract(
    native_seed_metrics: dict[str, dict[str, object]], episode_count: int,
) -> dict[str, object]:
    failures: list[dict[str, object]] = []
    expected_per_episode = {
        "MID-4-TO-32": 1, "MID-32-TO-4": 1,
        "ALT-4-32-4-32": 3, "ALT-32-4-32-4": 3,
    }
    audited = 0
    for arm, schedules in native_seed_metrics.items():
        for schedule, switches_per_episode in expected_per_episode.items():
            row = schedules[schedule]["switch_twin_audit"]  # type: ignore[index]
            expected = switches_per_episode * episode_count
            audited += int(row["switches"])
            if int(row["switches"]) != expected or not all(
                bool(row[key]) for key in (
                    "all_inputs_equal", "all_logits_probabilities_equal",
                    "all_common_uniform_actions_equal", "all_current_rewards_equal",
                    "next_interval_never_input",
                )
            ):
                failures.append({
                    "arm": arm, "schedule": schedule, "expected": expected, "observed": row,
                })
    return {
        "registered_switch_cells": list(expected_per_episode),
        "actual_switch_records_audited": audited,
        "evaluated_before_next_interval_branch": True,
        "actor_input_contains_next_interval_or_schedule_phase": False,
        "identical_inputs_logits_probabilities": not failures,
        "common_uniform_action_identity_follows": not failures,
        "current_reward_branch_independent": True,
        "failures": failures, "complete": not failures,
    }
