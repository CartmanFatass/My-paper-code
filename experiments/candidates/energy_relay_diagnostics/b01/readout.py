"""Prospective readings of native outcomes and the observed action path.

World-paired uncertainty is conditional on this one retained training instance.
Associations of overrides/walls with QoS are not causal mediation estimates.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01 import evaluation as ev


NATIVE_KEYS = (
    "raw_native_J", "qos_per_step", "return_constraint_cost_sum",
    "cutoff_event_count_sum", "depletion_event_count_sum", "min_decoded_battery",
    "episode_minimum_battery_ratio", "charger_input_wh", "wait_ticks_total",
    "mode_uav_step_fraction", "guard_blocked_actions", "boundary_share_normal",
    "proposal_saturated_xy_uav_share_normal", "mean_action_saturated_xy_uav_share_normal",
    "outward_submitted_share_at_boundary_normal", "xy_stationary_share_outward_submitted_normal",
)


def arrays_digest(arrays):
    digest = hashlib.sha256()
    for key in sorted(arrays):
        value = np.ascontiguousarray(np.asarray(arrays[key]))
        digest.update(json.dumps([key, value.dtype.str, value.shape]).encode())
        digest.update(value.tobytes())
    return digest.hexdigest()


def _mean(values, mask=None):
    values = np.asarray(values)
    if mask is not None:
        values = values[np.asarray(mask, dtype=bool)]
    return float(values.mean()) if values.size else None


def action_reading(result):
    arrays, obs = result["arrays"], result["observation"]
    proposal = np.asarray(obs["proposal_t"])
    submitted = np.asarray(obs["submitted_t"])
    position, next_position = np.asarray(obs["own_xyz_t"]), np.asarray(obs["own_xyz_t1"])
    normal = ~np.asarray(arrays["mode"], dtype=bool)
    boundary = ((position[..., :2] <= 1).any(axis=-1)
                | (position[..., :2] >= 7999).any(axis=-1))
    outward_proposal = (((position[..., :2] <= 1) & (proposal[..., :2] < 0))
                        | ((position[..., :2] >= 7999) & (proposal[..., :2] > 0))).any(axis=-1)
    outward_submitted = (((position[..., :2] <= 1) & (submitted[..., :2] < 0))
                         | ((position[..., :2] >= 7999) & (submitted[..., :2] > 0))).any(axis=-1)
    xy_motion = np.linalg.norm(next_position[..., :2] - position[..., :2], axis=-1)
    mean_raw = np.asarray(obs["actor_mean_raw"])
    mean_action = np.tanh(mean_raw) if obs["actor_distribution"] == "tanh_gaussian" else mean_raw
    reading = {
        "proposal_out_of_bounds_component_share": float((np.abs(proposal) > 1).mean()),
        "submitted_out_of_bounds_component_share": float((np.abs(submitted) > 1).mean()),
        "proposal_saturated_xy_uav_share_normal": _mean(
            (np.abs(proposal[..., :2]) >= .95).any(axis=-1), normal),
        "mean_action_saturated_xy_uav_share_normal": _mean(
            (np.abs(mean_action[..., :2]) >= .95).any(axis=-1), normal),
        "mean_abs_raw": float(np.abs(mean_raw).mean()),
        "mean_scale_raw": float(np.asarray(obs["actor_scale_raw"]).mean()),
        "shield_changed_uav_share": float(np.any(proposal != submitted, axis=-1).mean()),
        "boundary_share_normal": _mean(boundary, normal),
        "outward_proposal_share_at_boundary_normal": _mean(outward_proposal, normal & boundary),
        "outward_submitted_share_at_boundary_normal": _mean(outward_submitted, normal & boundary),
        "xy_stationary_share_outward_submitted_normal": _mean(
            xy_motion < .05, normal & outward_submitted),
        "mean_xy_displacement_m_normal": _mean(xy_motion, normal),
        "normal_uav_steps": int(normal.sum()),
        "boundary_normal_uav_steps": int((normal & boundary).sum()),
        "outward_submitted_normal_uav_steps": int((normal & outward_submitted).sum()),
        "actor_distribution": str(obs["actor_distribution"]),
        "maximum_held_age": int(np.max(obs["held_age"])),
    }
    if result["row"]["action_mode"] == "deterministic":
        reading["max_proposal_minus_tanh_mean"] = float(np.max(np.abs(proposal - mean_action)))
    if not all(math.isfinite(value) for value in reading.values() if isinstance(value, float)):
        raise ValueError("nonfinite action reading")
    return reading


def paired(candidate, baseline, keys=NATIVE_KEYS):
    base = {row["seed"]: row for row in baseline}
    if set(base) != {row["seed"] for row in candidate}:
        raise ValueError("paired comparison needs identical world ids")
    output = {"worlds": len(base), "unit": "world conditional on one retained SET fit", "metrics": {}}
    for key in keys:
        if not all(key in row and row[key] is not None for row in candidate + baseline):
            continue
        values = np.asarray([row[key] - base[row["seed"]][key] for row in candidate], dtype=float)
        output["metrics"][key] = {
            "mean": float(values.mean()), "median": float(np.median(values)),
            "se": float(values.std(ddof=1) / np.sqrt(len(values))) if len(values) > 1 else None,
            "min": float(values.min()), "max": float(values.max()),
            "positive": int((values > 0).sum()), "negative": int((values < 0).sum()),
            "per_world": [{"seed": row["seed"], "delta": float(value)}
                          for row, value in zip(candidate, values)],
        }
    return output


def _raw_comparison(candidate, baseline, raw_root):
    """A common observed pre-entry window and the first recorded path divergence."""
    first_fields = ("obs_input_digest_t", "obs_held_digest_t", "obs_actor_mean_raw",
                    "obs_actor_scale_raw", "obs_proposal_t", "obs_submitted_t",
                    "obs_own_xyz_t1", "metrics", "reward", "ends")
    base = {row["seed"]: row for row in baseline}
    rows = []
    for row in candidate:
        other = base[row["seed"]]
        with np.load(Path(raw_root) / row["raw_path"], allow_pickle=False) as a, \
                np.load(Path(raw_root) / other["raw_path"], allow_pickle=False) as b:
            horizon = min(row["actual_length"], other["actual_length"])
            window = min(horizon, *(r["first_entry_step"] if r["first_entry_step"] is not None
                                     else r["actual_length"] for r in (row, other)))
            reading = {"seed": row["seed"], "common_pre_entry_steps": int(window),
                       "qos_delta_common_pre_entry": (
                           float((a["metrics"][:window, ev.QOS] - b["metrics"][:window, ev.QOS]).mean())
                           if window else None), "first_divergence": None}
            differences = []
            for order, key in enumerate(first_fields):
                if key not in a or key not in b:
                    continue
                different = np.any((a[key][:horizon] != b[key][:horizon]).reshape(horizon, -1), axis=1)
                locations = np.flatnonzero(different)
                if locations.size:
                    differences.append((int(locations[0]), order, key))
            if differences:
                t, _, key = min(differences)
                reading["first_divergence"] = {"t": t, "first_field_in_dataflow_order": key,
                    "all_fields_different_at_t": [name for tick, _, name in differences if tick == t]}
            reading["length_difference"] = int(row["actual_length"] - other["actual_length"])
            rows.append(reading)
    observed = [row["qos_delta_common_pre_entry"] for row in rows
                if row["qos_delta_common_pre_entry"] is not None]
    return {"worlds": rows, "mean_world_qos_delta_common_pre_entry": _mean(observed),
            "observed_common_windows": len(observed),
            "scope": "descriptive common window, not a shield causal effect"}


def read_panels(panels, raw_root=None):
    """Read whatever the frozen protocol requested, retaining all comparisons and adverse worlds."""
    readings = {"panels": {}, "comparisons": {}, "collector_alignment": {}}
    for name, rows in panels.items():
        readings["panels"][name] = ev.aggregate(rows)
    for checkpoint in ("c00", "c03"):
        evaluator = panels.get(f"{checkpoint}_eval_stochastic_d0")
        collector = panels.get(f"{checkpoint}_collector_stochastic_d0")
        if evaluator and collector:
            by_seed = {row["seed"]: row for row in evaluator}
            selected = [by_seed[row["seed"]] for row in collector]
            readings["comparisons"][f"{checkpoint}_collector_minus_evaluator"] = paired(collector, selected)
            readings["collector_alignment"][checkpoint] = {
                "worlds": len(collector),
                "native_equal_worlds": [row["seed"] for row in collector
                                        if row["native_digest"] == by_seed[row["seed"]]["native_digest"]],
                "native_different_worlds": [row["seed"] for row in collector
                                            if row["native_digest"] != by_seed[row["seed"]]["native_digest"]],
                "actions_equal_worlds": [row["seed"] for row in collector
                                         if row["action_digest"] == by_seed[row["seed"]]["action_digest"]],
            }
            if raw_root is not None:
                readings["collector_alignment"][checkpoint]["trace_comparison"] = _raw_comparison(
                    collector, selected, raw_root)
    first, last = panels.get("c00_eval_stochastic_d0"), panels.get("c03_eval_stochastic_d0")
    if first and last:
        readings["comparisons"]["c03_minus_c00_sampled"] = paired(last, first)
    deterministic = panels.get("c03_eval_deterministic")
    if last and deterministic:
        readings["comparisons"]["c03_sampled_minus_deterministic"] = paired(last, deterministic)
    second = panels.get("c03_eval_stochastic_d1")
    if last and second:
        readings["comparisons"]["c03_draw1_minus_draw0"] = paired(second, last)
        if deterministic:
            readings["comparisons"]["c03_draw1_minus_deterministic"] = paired(second, deterministic)
            by_seed = {row["seed"]: row for row in last}
            averaged = [dict(seed=row["seed"], **{
                key: .5 * (row[key] + by_seed[row["seed"]][key]) for key in NATIVE_KEYS
                if row.get(key) is not None and by_seed[row["seed"]].get(key) is not None})
                for row in second]
            readings["comparisons"]["c03_equal_draw_average_minus_deterministic"] = paired(
                averaged, deterministic)
    if raw_root is not None:
        readings["common_pre_entry"] = {}
        for label, candidate, baseline in (
                ("c03_minus_c00_sampled", last, first),
                ("c03_draw0_minus_deterministic", last, deterministic),
                ("c03_draw1_minus_deterministic", second, deterministic)):
            if candidate and baseline:
                readings["common_pre_entry"][label] = _raw_comparison(candidate, baseline, raw_root)
    return readings
