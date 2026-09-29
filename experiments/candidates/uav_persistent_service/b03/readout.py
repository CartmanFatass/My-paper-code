"""Fixed three-arm, eight-world B03 readings with raw prefix pairing."""

from __future__ import annotations

from pathlib import Path
from itertools import combinations

import numpy as np

from experiments.candidates.energy_relay_availability.readout import paired
from experiments.candidates.energy_relay_availability.runner import _sha256
from experiments.candidates.uav_information_value.readout import distribution, number

from .episode import HORIZON


SEEDS = tuple(range(52392801, 52392809))
ARMS = ("P", "O_H", "R")
PAIR_FIELDS = ("initial_state_sha256", "ground_bs_sha256")
CONTRAST_FIELDS = (
    "horizon_normalized_qos", "raw_native_J", "late6000_mission_qos",
    "late6000_native_J", "net_stored_energy_wh", "gross_charger_input_wh",
    "native_consumed_wh", "native_positive_net_charge_wh",
    "native_station_occupancy_uav_steps", "native_station_queue_steps",
    "actual_team_travel_m", "native_reserve_uav_step_fraction",
    "cutoff_event_count_sum", "depletion_event_count_sum",
    "final300_persistent_reserve_members", "unserved_remaining_mission_steps",
    "station_overload_ticks_any", "station_overload_longest_spell_any",
) + tuple(f"station{station}_{field}" for station in range(2) for field in (
    "eligible_uav_steps", "eligible_demand_wh", "charger_input_wh", "overload_ticks",
    "longest_overload_spell", "final3000_mean_demand_w", "final3000_input_wh",
    "final3000_mean_stock_wh", "terminal_stock_wh")) + tuple(
    f"block{block}_{field}" for block in range(4) for field in (
        "mission_qos", "native_J", "stock_change_wh", "gross_charger_input_wh",
        "native_consumed_wh", "station_occupancy_uav_steps", "station_queue_steps",
        "cutoff_events", "depletion_events"))


def plan():
    return [{"arm": arm, "seed": seed, "job_key": f"{arm}/{seed}"}
            for seed in SEEDS for arm in ARMS]


def _verified_path(out: Path, name: str, digest: str) -> Path:
    path = (out/name).resolve()
    if not path.is_relative_to(out.resolve()) or not path.is_file() or _sha256(path) != digest:
        raise ValueError(f"artifact missing or changed: {name}")
    return path


def verify_pair(out: Path, rows: dict[str, dict]) -> dict:
    """Verify initial identity and every arm's common raw exogenous prefix."""
    if set(rows) != set(ARMS):
        return {"status": "failed", "reason": "missing_arm"}
    seed = int(rows["P"]["seed"])
    if (any(row["seed"] != seed or row["arm"] != arm
                                     for arm, row in rows.items())
            or any(not rows["P"].get(field) or len({row.get(field) for row in rows.values()}) != 1
                   for field in PAIR_FIELDS)):
        return {"seed": seed, "status": "failed", "reason": "initial_identity"}
    try:
        traces = {}
        for arm, row in rows.items():
            _verified_path(out, row["decisions_path"], row["decisions_sha256"])
            path = _verified_path(out, row["raw_path"], row["raw_sha256"])
            with np.load(path, allow_pickle=False) as raw:
                users = raw["user_xy_m"]
                rng = raw["rng_state_sha256_by_step"]
                length = int(row["actual_length"])
                ends = raw["ends"]
                if (not 0 < length <= HORIZON or len(raw["reward"]) != length
                        or users.shape != (length+1, 30, 2) or not np.isfinite(users).all()
                        or rng.shape != (length+1,) or rng.dtype.kind != "U"
                        or not np.all(np.char.str_len(rng) == 64)
                        or ends.shape != (length, 2) or not ends[-1].any()):
                    raise ValueError("raw trajectory length or terminal witness invalid")
                traces[arm] = (users.copy(), rng.copy(), length)
        pair_checks = {}
        for left, right in combinations(ARMS, 2):
            prefix = min(traces[left][2], traces[right][2])+1
            users_equal = np.array_equal(traces[left][0][:prefix], traces[right][0][:prefix])
            rng_equal = np.array_equal(traces[left][1][:prefix], traces[right][1][:prefix])
            equal_length = traces[left][2] == traces[right][2]
            full_equal = all(isinstance(rows[left].get(field), str)
                             and len(rows[left][field]) == 64
                             and rows[left][field] == rows[right].get(field)
                             for field in ("user_xy_trace_sha256", "rng_state_stream_sha256"))
            pair_checks[f"{left}-{right}"] = {
                "prefix_states": prefix, "users_equal": bool(users_equal),
                "rng_equal": bool(rng_equal), "unequal_lengths": not equal_length,
                "equal_length_full_stream_equal": full_equal if equal_length else None,
                "status": "verified" if users_equal and rng_equal
                          and (not equal_length or full_equal) else "failed"}
        return {"seed": seed,
                "status": "verified" if all(p["status"] == "verified" for p in pair_checks.values())
                          else "failed",
                "reason": (None if all(p["status"] == "verified" for p in pair_checks.values())
                           else "exogenous_prefix"),
                "pairs": pair_checks}
    except (OSError, ValueError, KeyError, TypeError) as error:
        return {"seed": seed, "status": "failed", "reason": "artifact_integrity",
                "error": f"{type(error).__name__}: {error}"}


def summarize(rows: list[dict], *, pairing: dict[int, dict] | None = None) -> dict:
    expected = {job["job_key"]: job for job in plan()}
    indexed = {row["job_key"]: row for row in rows}
    if len(indexed) != len(rows) or set(indexed)-set(expected):
        raise ValueError("duplicate or unexpected B03 world")
    for key, row in indexed.items():
        if any(row.get(field) != expected[key][field] for field in ("arm", "seed")):
            raise ValueError("B03 world identity differs from fixed plan")
    pairing = pairing or {}
    groups = {arm: [indexed[job["job_key"]] for job in plan()
                    if job["arm"] == arm and job["job_key"] in indexed
                    and indexed[job["job_key"]]["status"] == "completed"] for arm in ARMS}
    excluded = {"seed", "actual_length", "raw_bytes", "worker_wall_seconds",
                "worker_cpu_seconds", "worker_peak_rss_kib"}
    fields = sorted({key for panel in groups.values() for row in panel for key, value in row.items()
                     if number(value) and key not in excluded})
    panels = {arm: {"completed_worlds": len(panel), "metrics": {
        field: distribution([row[field] for row in panel if number(row.get(field))]) |
               {"missing": sum(not number(row.get(field)) for row in panel)}
        for field in fields},
        "early_terminal_worlds": [row["seed"] for row in panel if row["actual_length"] < HORIZON],
        "terminal_zero_service_worlds": [row["seed"] for row in panel if row["terminal_zero_service"]],
        "missing_final300_worlds": [row["seed"] for row in panel
                                    if row["final300_persistent_reserve_members"] is None]}
        for arm, panel in groups.items()}
    complete = (len(rows) == len(expected)
                and all(row["status"] == "completed" for row in rows)
                and all(pairing.get(seed, {}).get("status") == "verified" for seed in SEEDS))
    result = {"status": "complete" if complete else "incomplete", "planned_jobs": 24,
              "completed_jobs": sum(len(panel) for panel in groups.values()),
              "missing_jobs": [key for key in expected if key not in indexed],
              "failed_jobs": [key for key, row in indexed.items() if row["status"] != "completed"],
              "pairing": {str(seed): pairing[seed] for seed in SEEDS if seed in pairing},
              "pairing_failures": [seed for seed in SEEDS if pairing.get(seed, {}).get("status") == "failed"],
              "panels": panels, "contrasts": {}, "fits": 0, "optimizer_updates": 0,
              "estimand": "finite H12000 closed-loop R/O_H/P; native early endings retained",
              "inference_unit": "paired initial S2 world; nominal t7 intervals are descriptive"}
    if not complete:
        return result
    worlds = {arm: {row["seed"]: row for row in panel} for arm, panel in groups.items()}
    if any(sorted(worlds[arm]) != list(SEEDS) for arm in ARMS):
        raise ValueError("B03 arms do not share eight unique seeds")
    for field in CONTRAST_FIELDS:
        result["contrasts"][field] = {}
        for left, right in (("R", "O_H"), ("R", "P"), ("O_H", "P")):
            name = f"{left}-{right}"
            missing = [seed for seed in SEEDS if any(not number(worlds[arm][seed].get(field))
                                                     for arm in (left, right))]
            if missing:
                result["contrasts"][field][name] = {"status": "not_comparable",
                                                       "missing_seeds": missing}
                continue
            delta = [float(worlds[left][seed][field])-float(worlds[right][seed][field])
                     for seed in SEEDS]
            result["contrasts"][field][name] = paired(delta, [0.]*len(delta)) | {
                "positive": sum(x > 0 for x in delta), "negative": sum(x < 0 for x in delta),
                "ties": sum(x == 0 for x in delta), "by_seed": dict(zip(map(str, SEEDS), delta))}
    return result
