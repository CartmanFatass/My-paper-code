"""Fixed mission denominators and integrity-bound O_H/P paired contrasts."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from experiments.candidates.energy_relay_availability.readout import paired
from experiments.candidates.energy_relay_availability.runner import _sha256
from experiments.candidates.uav_information_value.readout import distribution, number

from .episode import HORIZON


SEEDS = tuple(range(52292801, 52292809))
ARMS = ("O_H", "P")
PAIR_FIELDS = ("initial_state_sha256", "ground_bs_sha256")
CONTRAST_FIELDS = (
    "horizon_normalized_qos", "raw_native_J", "late6000_mission_qos",
    "late6000_native_J", "net_stored_energy_wh", "gross_charger_input_wh",
    "native_consumed_wh", "native_positive_net_charge_wh",
    "native_station_occupancy_uav_steps", "native_station_queue_steps",
    "actual_team_travel_m", "native_reserve_uav_step_fraction",
    "cutoff_event_count_sum", "depletion_event_count_sum",
    "final300_persistent_reserve_members",
    "unserved_remaining_mission_steps",
) + tuple(f"block{block}_{field}" for block in range(4) for field in (
    "mission_qos", "native_J", "stock_change_wh", "gross_charger_input_wh",
    "native_consumed_wh", "station_occupancy_uav_steps", "station_queue_steps",
    "cutoff_events", "depletion_events"))


def plan():
    return [{"arm": arm, "seed": seed, "job_key": f"{arm}/{seed}"}
            for seed in SEEDS for arm in ARMS]


def _verified_path(out: Path, name: str, digest: str) -> Path:
    path = (out / name).resolve()
    if not path.is_relative_to(out.resolve()) or not path.is_file() or _sha256(path) != digest:
        raise ValueError(f"artifact missing or changed: {name}")
    return path


def verify_pair(out: Path, left: dict, right: dict) -> dict:
    """Read retained raw evidence and compare the common observed prefix."""
    seed = int(left["seed"])
    if (right["seed"] != seed or left["arm"] != "O_H" or right["arm"] != "P"
            or any(left.get(field) != right.get(field) or not left.get(field)
                   for field in PAIR_FIELDS)):
        return {"seed": seed, "status": "failed", "reason": "initial_identity"}
    try:
        for row in (left, right):
            _verified_path(out, row["decisions_path"], row["decisions_sha256"])
        paths = [_verified_path(out, row["raw_path"], row["raw_sha256"])
                 for row in (left, right)]
        traces = []
        for path, row in zip(paths, (left, right)):
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
                traces.append((users, rng))
        prefix = min(int(left["actual_length"]), int(right["actual_length"]))+1
        users_equal = np.array_equal(traces[0][0][:prefix], traces[1][0][:prefix])
        rng_equal = np.array_equal(traces[0][1][:prefix], traces[1][1][:prefix])
        equal_length = left["actual_length"] == right["actual_length"]
        full_equal = all(isinstance(left.get(field), str) and len(left[field]) == 64
                         and left[field] == right.get(field)
                         for field in ("user_xy_trace_sha256", "rng_state_stream_sha256"))
        if not users_equal or not rng_equal or (equal_length and not full_equal):
            return {"seed": seed, "status": "failed", "reason": "exogenous_prefix",
                    "prefix_states": prefix, "users_equal": users_equal, "rng_equal": rng_equal,
                    "equal_length_full_stream_equal": full_equal if equal_length else None}
        return {"seed": seed, "status": "verified", "prefix_states": prefix,
                "unequal_lengths": not equal_length,
                "equal_length_full_stream_equal": full_equal if equal_length else None}
    except (OSError, ValueError, KeyError, TypeError) as error:
        return {"seed": seed, "status": "failed", "reason": "artifact_integrity",
                "error": f"{type(error).__name__}: {error}"}


def summarize(rows: list[dict], *, pairing: dict[int, dict] | None = None) -> dict:
    expected = {job["job_key"]: job for job in plan()}
    indexed = {row["job_key"]: row for row in rows}
    if len(indexed) != len(rows) or set(indexed) - set(expected):
        raise ValueError("duplicate or unexpected B02 world")
    for key, row in indexed.items():
        if any(row.get(field) != expected[key][field] for field in ("arm", "seed")):
            raise ValueError("B02 world identity differs from fixed plan")
    pairing = pairing or {}
    groups = {arm: [indexed[job["job_key"]] for job in plan()
                    if job["arm"] == arm and job["job_key"] in indexed
                    and indexed[job["job_key"]]["status"] == "completed"] for arm in ARMS}
    fields = sorted({key for panel in groups.values() for row in panel for key, value in row.items()
                     if number(value) and key not in {"seed", "actual_length", "raw_bytes",
                                                  "worker_wall_seconds", "worker_cpu_seconds",
                                                  "worker_peak_rss_kib"}})
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
    result = {
        "status": "complete" if complete else "incomplete", "planned_jobs": len(expected),
        "completed_jobs": sum(len(panel) for panel in groups.values()),
        "missing_jobs": [key for key in expected if key not in indexed],
        "failed_jobs": [key for key, row in indexed.items() if row["status"] != "completed"],
        "pairing": {str(seed): pairing[seed] for seed in SEEDS if seed in pairing},
        "pairing_failures": [seed for seed in SEEDS if pairing.get(seed, {}).get("status") == "failed"],
        "panels": panels, "contrasts": {}, "retention_rule": {"status": "unavailable"},
        "fits": 0, "optimizer_updates": 0,
        "estimand": "finite H12000 closed-loop O_H versus P; native early endings retained",
        "inference_unit": "paired initial S2 world; nominal t7 intervals are descriptive",
    }
    if not complete:
        return result
    worlds = {arm: {row["seed"]: row for row in panel} for arm, panel in groups.items()}
    if any(sorted(worlds[arm]) != list(SEEDS) for arm in ARMS):
        raise ValueError("B02 arms do not share eight unique seeds")
    for field in CONTRAST_FIELDS:
        missing = [seed for seed in SEEDS if any(not number(worlds[arm][seed].get(field))
                                                 for arm in ARMS)]
        if missing:
            result["contrasts"][field] = {"status": "not_comparable", "missing_seeds": missing}
            continue
        delta = [float(worlds["O_H"][seed][field])-float(worlds["P"][seed][field])
                 for seed in SEEDS]
        result["contrasts"][field] = paired(delta, [0.] * len(delta)) | {
            "positive": sum(x > 0 for x in delta), "negative": sum(x < 0 for x in delta),
            "ties": sum(x == 0 for x in delta),
            "by_seed": dict(zip(map(str, SEEDS), delta)),
        }
    def mean_delta(field):
        return result["contrasts"][field]["mean"]
    additional = {field: [seed for seed in SEEDS
                          if worlds["O_H"][seed][field] > worlds["P"][seed][field]]
                  for field in ("cutoff_event_count_sum", "depletion_event_count_sum",
                                "terminal_zero_service")}
    additional["early_terminal"] = [seed for seed in SEEDS
                                    if worlds["O_H"][seed]["actual_length"]
                                    < worlds["P"][seed]["actual_length"]]
    final_missing = [seed for seed in SEEDS if any(
        worlds[arm][seed]["final300_persistent_reserve_members"] is None for arm in ARMS)]
    additional["final300_persistent_reserve_members"] = [seed for seed in SEEDS
        if seed not in final_missing and worlds["O_H"][seed]["final300_persistent_reserve_members"]
        > worlds["P"][seed]["final300_persistent_reserve_members"]]
    service_pass = all(mean_delta(field) >= .01 if "qos" in field else mean_delta(field) > 0
                       for field in ("horizon_normalized_qos", "raw_native_J",
                                     "late6000_mission_qos", "late6000_native_J"))
    clean_risk = (not final_missing and not any(additional.values())
                  and mean_delta("native_reserve_uav_step_fraction") <= 0)
    result["retention_rule"] = {
        "status": "supported" if service_pass and clean_risk else "not_supported",
        "service_threshold_pass": service_pass, "clean_risk_pass": clean_risk,
        "additional_risk_worlds": additional, "missing_final300_seeds": final_missing,
        "mean_reserve_exposure_delta": mean_delta("native_reserve_uav_step_fraction"),
    }
    return result
