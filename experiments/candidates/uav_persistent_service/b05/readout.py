"""Complete finite service readings for S against the two retained R panels."""

from __future__ import annotations

import numpy as np

from experiments.candidates.energy_relay_availability.readout import paired
from experiments.candidates.uav_information_value.readout import distribution, number
from experiments.candidates.uav_persistent_service.b03.episode import QOS, longest_spell


HORIZON = 12000
PANELS = {"original": tuple(range(52292801, 52292809)),
          "reassignment": tuple(range(52392801, 52392809))}
SEEDS = PANELS["original"] + PANELS["reassignment"]


def plan():
    return [{"arm": "S", "seed": seed, "job_key": f"S/{seed}"} for seed in SEEDS]


def continuity_readings(raw) -> dict:
    qos = np.asarray(raw["metrics"][:, QOS], dtype=float)
    mode = np.asarray(raw["mode"], dtype=bool)
    committed = np.asarray(raw["commit_active"], dtype=bool)
    load = np.asarray(raw["native_load"], dtype=float)
    length = len(qos)
    if (not 0 < length <= HORIZON or mode.shape != (length, 8)
            or committed.shape != mode.shape or load.shape != mode.shape
            or not np.isfinite(qos).all() or not np.isfinite(load).all()):
        raise ValueError("invalid native continuity arrays")
    late = slice(6000, HORIZON)
    zero = qos <= 0
    suffix = int(np.argmax(~zero[::-1])) if (~zero).any() else length
    free_load = ~mode & ~committed & (load > 0)
    return {
        "late_zero_service_steps": int(zero[late].sum()),
        "late_longest_zero_service_spell": longest_spell(zero[late]),
        "late_longest_below_half_service_spell": longest_spell(qos[late] < .5),
        "terminal_zero_service_suffix": suffix,
        "final300_mission_qos": float(qos[11700:].sum()/300) if length == HORIZON else None,
        "late_free_positive_load_member_steps": int(free_load[late].sum()),
        "late_no_free_positive_load_steps": int((~free_load[late].any(axis=1)).sum()),
        "late_f_positive_load_member_steps": int((mode & (load > 0))[late].sum()),
        "late_committed_positive_load_member_steps": int((committed & (load > 0))[late].sum()),
        "late_all_f_steps": int(mode[late].all(axis=1).sum()),
        "late_all_f_zero_service_steps": int((mode[late].all(axis=1) & zero[late]).sum()),
        "late_observed_steps": max(0, length-6000),
    }


def recovery_readings(raw, events: list[dict]) -> dict:
    mode = np.asarray(raw["mode"], dtype=bool)
    active = np.asarray(raw["commit_active"], dtype=bool)
    load = np.asarray(raw["native_load"])
    readings = []
    for event_index, event in enumerate(events):
        if event.get("kind") != "release":
            continue
        member, start = int(event["member"]), int(event["step"])
        stop = next((int(other["step"]) for other in events[event_index+1:]
                     if other.get("kind") == "start" and other.get("member") == member), len(mode))
        stop = min(stop, len(mode))
        mask = (~mode[start:stop, member] & ~active[start:stop, member]
                & (load[start:stop, member] > 0))
        hits = np.flatnonzero(mask)
        readings.append({"member": member, "release_step": start,
                         "followup_steps": max(0, stop-start),
                         "first_positive_load_delay_s": int(hits[0])+1 if len(hits) else None})
    late = [row for row in readings if row["release_step"] >= 6000]
    delays = [row["first_positive_load_delay_s"] for row in late
              if row["first_positive_load_delay_s"] is not None]
    return {"release_recovery": readings,
            "late_releases": len(late), "late_releases_with_positive_load": len(delays),
            "late_releases_without_observed_positive_load": len(late)-len(delays),
            "late_release_positive_load_delay_mean_s": float(np.mean(delays)) if delays else None,
            "recovery_time_convention": "release before action t to first positive-load post-state t+1; followup stops at next start"}


def _contrast(candidate, controls, seeds, fields):
    result = {}
    for field in fields:
        missing = [seed for seed in seeds if any(not number(group[seed].get(field))
                                                for group in (candidate, controls))]
        if missing:
            result[field] = {"status": "not_comparable", "missing_seeds": missing}
            continue
        delta = [float(candidate[seed][field])-float(controls[seed][field]) for seed in seeds]
        result[field] = paired(delta, [0.]*len(seeds)) | {
            "positive": sum(x > 0 for x in delta), "negative": sum(x < 0 for x in delta),
            "ties": sum(x == 0 for x in delta), "by_seed": dict(zip(map(str, seeds), delta))}
    return result


def use_rule(candidate, controls, contrasts):
    required = ("horizon_normalized_qos", "late6000_mission_qos", "raw_native_J",
                "late6000_native_J", "late_zero_service_steps", "native_reserve_uav_step_fraction")
    missing = [field for field in required if "mean" not in contrasts.get(field, {})]
    missing += [f"final300/{seed}" for seed in SEEDS
                if any(group[seed].get("final300_persistent_reserve_members") is None
                       for group in (candidate, controls))]
    if missing:
        return {"status": "unresolved", "missing": missing}
    flags = {
        "full_qos_nonnegative": contrasts["horizon_normalized_qos"]["mean"] >= 0,
        "late_qos_at_least_01": contrasts["late6000_mission_qos"]["mean"] >= .01,
        "full_j_nonnegative": contrasts["raw_native_J"]["mean"] >= 0,
        "late_j_nonnegative": contrasts["late6000_native_J"]["mean"] >= 0,
        "mean_late_zero_steps_reduced": contrasts["late_zero_service_steps"]["mean"] < 0,
        "mean_reserve_not_higher": contrasts["native_reserve_uav_step_fraction"]["mean"] <= 0,
        "maximum_late_zero_spell_not_higher": max(candidate[s]["late_longest_zero_service_spell"] for s in SEEDS)
        <= max(controls[s]["late_longest_zero_service_spell"] for s in SEEDS),
    }
    added = {}
    for label, field in (("cutoff", "cutoff_event_count_sum"),
                         ("depletion", "depletion_event_count_sum"),
                         ("persistent_reserve", "final300_persistent_reserve_members"),
                         ("terminal_zero", "terminal_zero_service"),
                         ("early_ending", "unserved_remaining_mission_steps")):
        added[label] = [s for s in SEEDS if candidate[s][field] > 0 and controls[s][field] <= 0]
        flags[f"no_new_{label}_worlds"] = not added[label]
    return {"status": "pass" if all(flags.values()) else "fail",
            "flags": flags, "new_adverse_worlds": added,
            "scope": "declared conditional finite replacement use; exposed development worlds, not safety or sustainability"}


def summarize(rows: list[dict], controls: dict[int, dict], pairing: dict[int, dict]) -> dict:
    expected = {job["job_key"]: job for job in plan()}
    indexed = {row["job_key"]: row for row in rows}
    if len(indexed) != len(rows) or set(indexed)-set(expected) or set(controls) != set(SEEDS):
        raise ValueError("duplicate/unexpected new rows or incomplete R reference")
    for key, row in indexed.items():
        if any(row.get(field) != expected[key][field] for field in ("arm", "seed")):
            raise ValueError("new row differs from declared identity")
    complete_rows = {row["seed"]: row for row in rows if row["status"] == "completed"}
    complete = (set(complete_rows) == set(SEEDS)
                and all(pairing.get(s, {}).get("status") == "verified" for s in SEEDS))
    exclude = {"seed", "actual_length", "raw_bytes", "worker_wall_seconds",
               "worker_cpu_seconds", "worker_peak_rss_kib"}
    fields = sorted({field for row in list(controls.values())+list(complete_rows.values())
                     for field, value in row.items() if number(value) and field not in exclude})
    panels = {}
    for name, group in (("R", controls), ("S", complete_rows)):
        panels[name] = {"worlds": len(group), "metrics": {
            field: distribution([row[field] for row in group.values() if number(row.get(field))]) |
            {"missing": sum(not number(row.get(field)) for row in group.values())} for field in fields},
            "terminal_zero_worlds": [s for s, row in group.items() if row.get("terminal_zero_service")],
            "early_worlds": [s for s, row in group.items() if row["actual_length"] < HORIZON]}
    result = {"status": "complete" if complete else "incomplete", "planned_new_jobs": len(SEEDS),
              "completed_new_jobs": len(complete_rows), "fits": 0, "optimizer_updates": 0,
              "missing_new_jobs": [key for key in expected if key not in indexed],
              "failed_new_jobs": [key for key, row in indexed.items() if row["status"] != "completed"],
              "pairing": {str(s): row for s, row in pairing.items()}, "panels": panels,
              "contrasts": {}, "panel_contrasts": {}, "use_rule": {"status": "unresolved"},
              "reused_control_jobs": 16, "reused_control_native_steps": 192000,
              "estimand": "S minus exact frozen R on all retained B03/B04 H12000 worlds",
              "inference_unit": "exposed development world; paired t15 and panel t7 intervals descriptive"}
    if complete:
        result["contrasts"] = _contrast(complete_rows, controls, SEEDS, fields)
        result["panel_contrasts"] = {name: _contrast(complete_rows, controls, seeds, fields)
                                     for name, seeds in PANELS.items()}
        result["use_rule"] = use_rule(complete_rows, controls, result["contrasts"])
    return result
