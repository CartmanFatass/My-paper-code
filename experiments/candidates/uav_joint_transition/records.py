"""Common native outcomes and controller work counts for training and evaluation."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from experiments.candidates.energy_relay_availability.runner import _sha256
from experiments.candidates.energy_relay_availability.b04.transit_hold import battery_tail_readings
from experiments.candidates.uav_radio_placement.b01.runner import _plain
from experiments.candidates.uav_service_auxiliary.b04.evaluation import TRACE_FIELDS
from .motion import toward, waypoints


def controller_records(controller, arm):
    if arm == "P":
        return controller.heuristic.decision_records
    return controller.decision_records


def enrich(row, steps, observer, controller, arm):
    arrays = observer.as_arrays()
    raw = observer.raw
    row.update(battery_tail_readings(steps["battery"], reserve_ratio=raw.return_reserve_ratio,
                                    service_cutoff_ratio=raw.service_cutoff_threshold))
    qos = steps["metrics"][:, TRACE_FIELDS.index("qos_satisfaction_ratio")]
    zeros = qos == 0
    edges = np.diff(np.concatenate(([False], zeros, [False])).astype(np.int8))
    gaps = np.flatnonzero(edges == -1) - np.flatnonzero(edges == 1)
    displacement = np.diff(arrays["physical_xyz_m"], axis=0)
    row.update(observer.digests())
    row.update(xy_path_m=float(np.linalg.norm(displacement[:, :, :2], axis=-1).sum()),
               xyz_path_m=float(np.linalg.norm(displacement, axis=-1).sum()),
               consumed_wh=float(arrays["consumed_wh"].sum()),
               return_constraint_cost_raw_max=float(steps["metrics"][:, TRACE_FIELDS.index("return_constraint_cost_raw")].max()),
               negative_margin_uav_step_fraction=float(np.mean(steps["return_margin"] < 0)),
               zero_service_steps=int(zeros.sum()), longest_zero_service_gap=int(gaps.max(initial=0)),
               terminal_reserve_members=int(np.sum(steps["battery"][-1] <= .10)),
               physical_transition_count=len(displacement))
    for index, (lo, hi) in enumerate(((0, 1000), (1000, 2000), (2000, 3000))):
        values = slice(lo, min(hi, row["actual_length"]))
        if len(qos[values]):
            row[f"fixed_third_{index}_qos"] = float(qos[values].mean())
            row[f"fixed_third_{index}_J"] = float(steps["reward"][values].sum())
    records = controller_records(controller, arm)
    clock = 10 if arm == "P" else 30
    if [record["step"] for record in records] != list(range(0, row["actual_length"], clock)):
        raise RuntimeError("controller clock differs from the selected contract")
    row["planner_windows"] = len(records)
    if arm == "P":
        row.update(service_snapshot_calls=int(controller.heuristic.service_snapshot_calls),
                   transition_snapshot_calls=int(controller.heuristic.service_snapshot_calls),
                   destination_snapshot_calls=0,
                   selected_hold_windows=sum(record["selected_hold_uav"] >= 0 for record in records),
                   prediction_team_ticks=0)
    elif arm == "R":
        row.update(service_snapshot_calls=int(controller.snapshot_calls_started),
                   destination_snapshot_calls=int(controller.snapshot_calls_started),
                   transition_snapshot_calls=0, prediction_team_ticks=0,
                   planner_cpu_seconds=sum(record["planner_cpu_seconds"] for record in records),
                   planner_wall_seconds=sum(record["planner_wall_seconds"] for record in records))
    else:
        row.update(controller.work_counts())
        choices = np.asarray([record["requested_modes"] for record in records], dtype=np.int64)
        eligible = np.asarray([record["eligible"] for record in records], dtype=bool)
        row.update(eligible_member_windows=int(eligible.sum()),
                   requested_non_direct_member_windows=int(np.sum((choices != 0) & eligible)),
                   requested_joint_non_direct_windows=int(np.sum(np.any((choices != 0) & eligible, axis=1))),
                   requested_multimember_windows=int(np.sum(np.sum((choices != 0) & eligible, axis=1) >= 2)))
        row["requested_mode_counts"] = {str(mode): int(np.sum((choices == mode) & eligible)) for mode in range(4)}
        changed_proposals = changed_submitted = still_after_change = 0
        waypoint_members = waypoint_reached = target_reached = member_windows = 0
        phase_distances, endpoint_distances = [], []
        cancelled, nominal_aliases = 0, 0
        for record in records:
            start = int(record["step"])
            stop = min(start+30, row["actual_length"])
            target = np.asarray(record["R_targets_xyz"])
            requested = np.asarray(record["requested_modes"])
            active = np.asarray(record["eligible"], dtype=bool)
            intermediate = waypoints(steps["own_xyz"][start], target)
            cancelled += int(np.sum(record["cancelled_member_ticks"]))
            nominal_aliases += int(np.sum(record["nominal_aliases"]))
            proposed = arrays["proposal_actions"][start:stop]
            submitted = arrays["submitted_actions"][start:stop]
            direct = np.zeros_like(proposed)
            direct[:, :, :3] = toward(steps["own_xyz"][start:stop], target[None]) / np.array([30, 30, 5])
            differs = np.any(np.abs(proposed-direct) > 1e-6, axis=2)
            survives = differs & ~np.any(np.abs(proposed-submitted) > 1e-6, axis=2)
            changed_proposals += int(differs.sum())
            changed_submitted += int(survives.sum())
            still_after_change += int(np.sum(survives & (np.linalg.norm(displacement[start:stop], axis=2) <= 1e-6)))
            endpoint = arrays["physical_xyz_m"][stop]
            distances = np.linalg.norm(endpoint-target, axis=1)
            endpoint_distances.extend(distances[active].tolist())
            target_reached += int(np.sum((distances <= 1.0) & active))
            member_windows += int(active.sum())
            phase = arrays["physical_xyz_m"][min(start+15, stop)]
            for member in np.flatnonzero(active & (requested >= 2)):
                distance = float(np.linalg.norm(phase[member]-intermediate[requested[member]-2, member]))
                phase_distances.append(distance)
                waypoint_members += 1
                waypoint_reached += int(distance <= 1.0)
        row.update(proposal_different_from_current_state_D_member_ticks=changed_proposals,
                   distinct_proposals_surviving_F_member_ticks=changed_submitted,
                   distinct_surviving_proposals_with_no_displacement_member_ticks=still_after_change,
                   cancelled_intermediate_member_ticks=cancelled, nominal_D_alias_mode_members=nominal_aliases,
                   detour_member_windows=waypoint_members, intermediate_arrival_within_1m=waypoint_reached,
                   target_arrival_within_1m=target_reached, target_eligible_member_windows=member_windows,
                   target_endpoint_distance_m_mean=float(np.mean(endpoint_distances)) if endpoint_distances else None,
                   intermediate_phase_distance_m_mean=float(np.mean(phase_distances)) if phase_distances else None)
        if any(record["candidate_count"] > 161 or record["feature_forecasts"] > 25 for record in records):
            raise RuntimeError("transition candidate or feature budget exceeded")
        if row["service_snapshot_calls"] != row["service_snapshot_calls_completed"]:
            raise RuntimeError("completed world has incomplete radio work")
    return arrays, records


def save_world(path: Path, row, steps, observer, controller, arm):
    arrays, records = enrich(row, steps, observer, controller, arm)
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **steps, **arrays, metric_fields=np.asarray(TRACE_FIELDS),
                        planner_records_json=np.asarray(json.dumps(_plain(records), allow_nan=False,
                                                                   separators=(",", ":"))))
    row.update(raw_sha256=_sha256(path), raw_bytes=path.stat().st_size)
    return row
