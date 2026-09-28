"""Complete, paired and adverse-inclusive H/G/R reading."""

from __future__ import annotations

import math

from experiments.candidates.energy_relay_availability.readout import paired


ARMS = ("H", "G", "R")
CONTRASTS = (("R", "G"), ("R", "H"), ("G", "H"))
PAIR_HASHES = ("initial_state_sha256", "user_xy_trace_sha256", "rng_state_stream_sha256")
EXCLUDE_METRICS = {"seed", "raw_bytes", "worker_peak_rss_kib"}


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def summarize(rows, seeds, expected_keys):
    keys = [row["job_key"] for row in rows]
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    unexpected = sorted(set(keys) - set(expected_keys))
    by_key = {row["job_key"]: row for row in rows}
    missing = [key for key in expected_keys if key not in by_key]
    incomplete = [key for key in expected_keys if key in by_key
                  and by_key[key].get("status") != "completed"]
    invalid_identity = [key for key, row in by_key.items()
                        if key != f"{row.get('arm')}/{row.get('seed')}"]
    groups = {arm: [by_key[f"{arm}/{seed}"] for seed in seeds
                    if f"{arm}/{seed}" in by_key
                    and by_key[f"{arm}/{seed}"].get("status") == "completed"]
              for arm in ARMS}
    complete = not (duplicates or unexpected or missing or incomplete or invalid_identity)
    complete &= all(len(groups[arm]) == len(seeds) for arm in ARMS)
    fields = sorted({field for group in groups.values() for row in group
                     for field, value in row.items()
                     if _number(value) and field not in EXCLUDE_METRICS})
    panels = {}
    for arm, group in groups.items():
        panels[arm] = {
            "completed_worlds": len(group),
            "means": {field: sum(float(row[field]) for row in group) / len(group)
                      for field in fields if group and all(_number(row.get(field)) for row in group)},
            "zero_service_worlds": [row["seed"] for row in group if row.get("zero_service")],
            "minimum_episode_battery_ratio": min(
                (row["episode_minimum_battery_ratio"] for row in group), default=None),
        }
    pairing, contrasts = [], {}
    if complete:
        for seed in seeds:
            equal = {name: bool(by_key[f"H/{seed}"].get(name)) and len({
                by_key[f"{arm}/{seed}"].get(name) for arm in ARMS}) == 1 for name in PAIR_HASHES}
            pairing.append({"seed": seed, "hashes_equal": equal})
        complete &= all(all(item["hashes_equal"].values()) for item in pairing)
        for candidate, baseline in (CONTRASTS if complete else ()):
            name = f"{candidate}_minus_{baseline}"
            per_world = []
            comparable = [field for field in fields if all(
                _number(by_key[f"{arm}/{seed}"].get(field))
                for arm in (candidate, baseline) for seed in seeds)]
            for seed in seeds:
                a, b = by_key[f"{candidate}/{seed}"], by_key[f"{baseline}/{seed}"]
                per_world.append({"seed": seed, **{
                    field: float(a[field]) - float(b[field]) for field in comparable}})
            contrasts[name] = {
                "metrics": {field: paired(
                    [by_key[f"{candidate}/{seed}"][field] for seed in seeds],
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
    return {
        "status": "complete" if complete else "incomplete",
        "planned_jobs": len(expected_keys),
        "completed_jobs": sum(len(group) for group in groups.values()),
        "missing_jobs": missing, "incomplete_jobs": incomplete,
        "duplicate_jobs": duplicates, "unexpected_jobs": unexpected,
        "invalid_identity_jobs": invalid_identity,
        "panels": panels, "contrasts": contrasts, "pairing": pairing,
        "exogenous_pairing_valid": bool(pairing) and all(
            all(item["hashes_equal"].values()) for item in pairing),
        "inference_unit": f"initialized world, n={len(seeds)}, descriptive paired t intervals",
        "scope": "fixed ordinary policy packages; no training or pure-objective causal claim",
    }
