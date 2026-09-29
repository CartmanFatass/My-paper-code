"""B04 original-control reconstruction, R pairing, and finite contrasts."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from experiments.candidates.energy_relay_availability.readout import paired
from experiments.candidates.uav_information_value.readout import distribution, number
from experiments.candidates.uav_persistent_service.b03.episode import longest_spell

from .binding import HORIZON, OLD_ARMS, SEEDS, verified_path, verify_raw_identity


ARMS = ("P", "O_H", "R")
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
    return [{"arm": "R", "seed": seed, "job_key": f"R/{seed}"} for seed in SEEDS]


def reconstruct_old_station(row: dict, raw, *, station_z: float, time_step_s: float = 1.0) -> dict:
    """Attribute old eligible/charged members by native post-position geometry only."""
    length = int(row["actual_length"])
    xy = np.asarray(row.get("station_xy"), dtype=float)
    if (xy.shape != (2, 2) or not np.isfinite(xy).all() or not np.isfinite(station_z)
            or time_step_s <= 0 or np.linalg.norm(xy[0]-xy[1]) <= 40.000002):
        raise ValueError("old native stations are absent or ambiguously close")
    stations = np.column_stack([xy, np.full(2, station_z)])
    position = raw["native_post_xyz"]
    eligible = raw["native_charging_eligible"].astype(bool)
    charging = raw["charging"].astype(bool)
    consumed = raw["native_consumed_wh"]
    charged = raw["native_charger_input_wh"]
    battery = raw["native_battery"]
    pre_nearest = raw["nearest_station"]
    occupancy = raw["native_station_occupancy"]
    queue = raw["native_station_queue"]
    if (position.shape != (length, 8, 3) or eligible.shape != (length, 8)
            or charging.shape != (length, 8) or consumed.shape != (length, 8)
            or charged.shape != (length, 8) or battery.shape != (length, 8)
            or pre_nearest.shape != (length, 8) or occupancy.shape != (length, 2)
            or queue.shape != (length, 2)
            or any(not np.isfinite(values).all() for values in
                   (position, consumed, charged, battery))):
        raise ValueError("old native station telemetry shape or finiteness differs")
    distances = np.linalg.norm(position[:, :, None, :]-stations[None, None, :, :], axis=3)
    nearest = distances.argmin(axis=2)
    minimum = np.take_along_axis(distances, nearest[:, :, None], axis=2)[:, :, 0]
    if (np.any(eligible & (minimum > 20.000001))
            or np.any(eligible & (pre_nearest != nearest))
            or np.any(charging & ~eligible)
            or np.any((charged > 0) & ~eligible)
            or np.any((charged > 0) != charging)):
        raise ValueError("old eligible/charged station geometry differs")
    counts = np.column_stack([(eligible & (nearest == station)).sum(axis=1)
                              for station in range(2)])
    if not np.array_equal(counts, occupancy+queue):
        raise ValueError("old native occupancy/queue differs from reconstructed eligibility")
    demand = np.column_stack([np.where(eligible & (nearest == station), consumed, 0).sum(axis=1)
                              * 3600.0/time_step_s for station in range(2)])
    inputs = np.column_stack([np.where(nearest == station, charged, 0).sum(axis=1)
                              for station in range(2)])
    stock = np.column_stack([np.where(nearest == station, battery*160.0, 0).sum(axis=1)
                             for station in range(2)])
    if (not np.isclose(inputs.sum(), row["gross_charger_input_wh"], atol=1e-6, rtol=1e-9)
            or not np.isclose(consumed.sum(), row["native_consumed_wh"], atol=1e-6, rtol=1e-9)
            or int(occupancy.sum()) != row["native_station_occupancy_uav_steps"]):
        raise ValueError("old reconstructed station totals differ from native row")
    overload = demand > 1000.0
    result = {"station_reconstruction_provenance":
              "old native post xyz and original legal-decoded station xy at native floor z; no native target field"}
    for station in range(2):
        prefix = f"station{station}_"
        result[prefix+"eligible_uav_steps"] = int(counts[:, station].sum())
        result[prefix+"eligible_demand_wh"] = float(demand[:, station].sum()*time_step_s/3600.0)
        result[prefix+"charger_input_wh"] = float(inputs[:, station].sum())
        result[prefix+"overload_ticks"] = int(overload[:, station].sum())
        result[prefix+"longest_overload_spell"] = longest_spell(overload[:, station])
        final = slice(9000, HORIZON)
        observed = max(0, min(length, HORIZON)-9000)
        result[prefix+"final3000_observed_steps"] = observed
        result[prefix+"final3000_mean_demand_w"] = (
            float(demand[final, station].mean()) if observed else None)
        result[prefix+"final3000_input_wh"] = float(inputs[final, station].sum())
        result[prefix+"final3000_mean_stock_wh"] = (
            float(stock[final, station].mean()) if observed else None)
        result[prefix+"terminal_stock_wh"] = float(stock[-1, station])
    result["station_overload_ticks_any"] = int(overload.any(axis=1).sum())
    result["station_overload_longest_spell_any"] = longest_spell(overload.any(axis=1))
    if set(row) & set(result):
        raise ValueError("old reconstruction would overwrite a native metric")
    return result


def enrich_old_rows(root: Path, binding: dict, *, station_z: float,
                    time_step_s: float = 1.0) -> dict[str, dict]:
    enriched = {}
    for key, row in binding["rows"].items():
        with np.load(root/row["raw_path"], allow_pickle=False) as raw:
            fields = reconstruct_old_station(row, raw, station_z=station_z,
                                             time_step_s=time_step_s)
        enriched[key] = row | fields
    return enriched


def verify_new_triplet(old_root: Path, out: Path, old_rows: dict[str, dict],
                       new_row: dict) -> dict:
    seed = int(new_row["seed"])
    if (new_row.get("arm") != "R" or new_row.get("job_key") != f"R/{seed}"
            or seed not in SEEDS):
        return {"seed": seed, "status": "failed", "reason": "new_identity"}
    try:
        new_path = verified_path(out, new_row["raw_path"], new_row["raw_sha256"],
                                 new_row["raw_bytes"])
        verified_path(out, new_row["decisions_path"], new_row["decisions_sha256"])
        with np.load(new_path, allow_pickle=False) as raw:
            new_trace = verify_raw_identity(raw, new_row)
        pairs = {}
        for arm in OLD_ARMS:
            old = old_rows[f"{arm}/{seed}"]
            if (new_row.get("effective_config") != old.get("effective_config")
                    or any(not old.get(field) or old.get(field) != new_row.get(field)
                           for field in ("initial_state_sha256", "ground_bs_sha256"))):
                pairs[arm] = {"status": "failed", "reason": "identity_or_config"}
                continue
            with np.load(old_root/old["raw_path"], allow_pickle=False) as raw:
                old_trace = verify_raw_identity(raw, old)
            prefix = min(old["actual_length"], new_row["actual_length"])+1
            users_equal = np.array_equal(old_trace[0][:prefix], new_trace[0][:prefix])
            rng_equal = np.array_equal(old_trace[1][:prefix], new_trace[1][:prefix])
            equal_length = old["actual_length"] == new_row["actual_length"]
            full_equal = all(isinstance(old.get(field), str) and len(old[field]) == 64
                             and old[field] == new_row.get(field) for field in
                             ("user_xy_trace_sha256", "rng_state_stream_sha256"))
            pairs[arm] = {"status": "verified" if users_equal and rng_equal
                          and (not equal_length or full_equal) else "failed",
                          "prefix_states": prefix, "users_equal": bool(users_equal),
                          "rng_equal": bool(rng_equal), "unequal_lengths": not equal_length,
                          "equal_length_full_stream_equal": full_equal if equal_length else None}
        return {"seed": seed, "status": "verified" if all(
            pair["status"] == "verified" for pair in pairs.values()) else "failed",
            "pairs": pairs}
    except (OSError, ValueError, KeyError, TypeError) as error:
        return {"seed": seed, "status": "failed", "reason": "artifact_integrity",
                "error": f"{type(error).__name__}: {error}"}


def summarize(new_rows: list[dict], old_rows: dict[str, dict],
              pairing: dict[int, dict] | None = None) -> dict:
    expected = {job["job_key"]: job for job in plan()}
    indexed = {row["job_key"]: row for row in new_rows}
    if len(indexed) != len(new_rows) or set(indexed)-set(expected):
        raise ValueError("duplicate or unexpected B04 R world")
    for key, row in indexed.items():
        if any(row.get(field) != expected[key][field] for field in ("arm", "seed")):
            raise ValueError("B04 R identity differs from fixed plan")
    if set(old_rows) != {f"{arm}/{seed}" for seed in SEEDS for arm in OLD_ARMS}:
        raise ValueError("old control set differs from fixed plan")
    pairing = pairing or {}
    groups = {arm: [old_rows[f"{arm}/{seed}"] for seed in SEEDS] for arm in OLD_ARMS}
    groups["R"] = [row for row in new_rows if row["status"] == "completed"]
    excluded = {"seed", "actual_length", "raw_bytes", "worker_wall_seconds",
                "worker_cpu_seconds", "worker_peak_rss_kib"}
    fields = sorted({key for panel in groups.values() for row in panel for key, value in row.items()
                     if number(value) and key not in excluded})
    panels = {arm: {"worlds": len(panel), "metrics": {
        field: distribution([row[field] for row in panel if number(row.get(field))]) |
               {"missing": sum(not number(row.get(field)) for row in panel)}
        for field in fields},
        "early_terminal_worlds": [row["seed"] for row in panel if row["actual_length"] < HORIZON],
        "terminal_zero_service_worlds": [row["seed"] for row in panel if row["terminal_zero_service"]],
        "missing_final300_worlds": [row["seed"] for row in panel
                                    if row["final300_persistent_reserve_members"] is None]}
        for arm, panel in groups.items()}
    complete = (len(new_rows) == 8 and all(row["status"] == "completed" for row in new_rows)
                and all(pairing.get(seed, {}).get("status") == "verified" for seed in SEEDS))
    result = {"status": "complete" if complete else "incomplete", "planned_new_jobs": 8,
              "native_completed_new_jobs": sum(bool(row.get("native_completed") or row.get("status") == "completed")
                                               for row in new_rows),
              "comparable_new_jobs": len(groups["R"]),
              "missing_new_jobs": [key for key in expected if key not in indexed],
              "failed_new_jobs": [key for key, row in indexed.items() if row["status"] != "completed"],
              "pairing": {str(seed): pairing[seed] for seed in SEEDS if seed in pairing},
              "panels": panels, "contrasts": {}, "fits": 0, "optimizer_updates": 0,
              "reused_control_jobs": 16, "reused_control_native_steps": 192000,
              "estimand": "unchanged R on original B02 H12000 worlds against exact reused O_H/P",
              "inference_unit": "paired original S2 world; nominal t7 intervals descriptive"}
    if not complete:
        return result
    worlds = {arm: {row["seed"]: row for row in panel} for arm, panel in groups.items()}
    for field in CONTRAST_FIELDS:
        result["contrasts"][field] = {}
        for left, right in (("R", "O_H"), ("R", "P"), ("O_H", "P")):
            missing = [seed for seed in SEEDS if any(not number(worlds[arm][seed].get(field))
                                                     for arm in (left, right))]
            if missing:
                result["contrasts"][field][f"{left}-{right}"] = {
                    "status": "not_comparable", "missing_seeds": missing}
                continue
            delta = [float(worlds[left][seed][field])-float(worlds[right][seed][field])
                     for seed in SEEDS]
            result["contrasts"][field][f"{left}-{right}"] = paired(delta, [0.]*8) | {
                "positive": sum(value > 0 for value in delta),
                "negative": sum(value < 0 for value in delta),
                "ties": sum(value == 0 for value in delta),
                "by_seed": dict(zip(map(str, SEEDS), delta))}
    return result
