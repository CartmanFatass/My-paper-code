"""Paired full-program outcomes, conditional on the single trained endpoint."""

from __future__ import annotations

from experiments.candidates.energy_relay_availability.readout import paired, _number
from .constants import ARMS, HORIZON


CONTRASTS = (("L", "O"), ("L", "R"), ("L", "P"), ("O", "R"), ("O", "P"), ("R", "P"))
PAIR_HASHES = ("initial_state_sha256", "user_xy_trace_sha256", "rng_state_stream_sha256")
EXCLUDE = {"seed", "raw_bytes", "worker_peak_rss_kib"}


def summarize(rows, seeds, expected_keys):
    keys = [row["job_key"] for row in rows]
    by_key = {row["job_key"]: row for row in rows}
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    unexpected = sorted(set(keys)-set(expected_keys))
    missing = [key for key in expected_keys if key not in by_key]
    incomplete = [key for key in expected_keys if key in by_key
                  and (by_key[key].get("status") != "completed" or by_key[key].get("actual_length") != HORIZON)]
    invalid = [key for key, row in by_key.items() if key != f"{row.get('arm')}/{row.get('seed')}"]
    groups = {arm: [by_key[f"{arm}/{seed}"] for seed in seeds
                    if f"{arm}/{seed}" in by_key and by_key[f"{arm}/{seed}"].get("status") == "completed"]
              for arm in ARMS}
    complete = not (duplicates or unexpected or missing or incomplete or invalid)
    fields = sorted({field for group in groups.values() for row in group
                     for field, value in row.items() if _number(value) and field not in EXCLUDE})
    panels = {}
    for arm, group in groups.items():
        panels[arm] = {
            "completed_worlds": len(group),
            "means": {field: sum(float(row[field]) for row in group)/len(group)
                      for field in fields if group and all(_number(row.get(field)) for row in group)},
            "zero_service_worlds": [row["seed"] for row in group if row.get("zero_service")],
            "terminal_reserve_worlds": [row["seed"] for row in group if row.get("terminal_reserve_members", 0)],
            "minimum_episode_battery_ratio": min((row["episode_minimum_battery_ratio"] for row in group), default=None),
        }
    pairing, contrasts = [], {}
    if complete:
        for seed in seeds:
            equal = {name: bool(by_key[f"R/{seed}"].get(name)) and len({
                by_key[f"{arm}/{seed}"].get(name) for arm in ARMS}) == 1 for name in PAIR_HASHES}
            pairing.append({"seed": seed, "hashes_equal": equal})
        complete = all(all(row["hashes_equal"].values()) for row in pairing)
        for candidate, baseline in (CONTRASTS if complete else ()):
            comparable = [field for field in fields if all(_number(by_key[f"{arm}/{seed}"].get(field))
                          for arm in (candidate, baseline) for seed in seeds)]
            per_world = [{"seed": seed, **{field: float(by_key[f"{candidate}/{seed}"][field])
                                          - float(by_key[f"{baseline}/{seed}"][field])
                                          for field in comparable}} for seed in seeds]
            contrasts[f"{candidate}_minus_{baseline}"] = {
                "metrics": {field: paired([by_key[f"{candidate}/{seed}"][field] for seed in seeds],
                                           [by_key[f"{baseline}/{seed}"][field] for seed in seeds])
                            for field in comparable},
                "worlds": per_world,
                "qos_wins": sum(row["qos_per_step"] > 0 for row in per_world),
                "qos_losses": sum(row["qos_per_step"] < 0 for row in per_world),
                "J_wins": sum(row["raw_native_J"] > 0 for row in per_world),
                "J_losses": sum(row["raw_native_J"] < 0 for row in per_world),
                "qos_up_J_down": [row["seed"] for row in per_world
                                  if row["qos_per_step"] > 0 and row["raw_native_J"] < 0],
            }
    return {"status": "complete" if complete else "incomplete", "planned_jobs": len(expected_keys),
            "completed_jobs": sum(len(group) for group in groups.values()), "missing_jobs": missing,
            "incomplete_jobs": incomplete, "duplicate_jobs": duplicates, "unexpected_jobs": unexpected,
            "invalid_identity_jobs": invalid, "panels": panels, "contrasts": contrasts, "pairing": pairing,
            "exogenous_pairing_valid": bool(pairing) and all(all(row["hashes_equal"].values()) for row in pairing),
            "inference_unit": f"paired initialized world, n={len(seeds)}; descriptive t intervals conditional on one fit",
            "scope": "complete fixed L/O/R/P packages; no training replication or isolated geometry mechanism"}
