"""Read complete B04 and original B02 evidence without creating an environment."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np

from experiments.candidates.uav_persistent_service.b03.audit import FIELDS

from .binding import HORIZON, ORIGINAL_ROOT, SEEDS, bind_original, verified_path


ARMS = ("P", "O_H", "R")


def first_true(mask):
    positions = np.flatnonzero(mask)
    return int(positions[0]) if len(positions) else None


def release_reason_counts(transfers):
    return dict(Counter(item["release_reason"] or item["end_kind"] for item in transfers))


def audit(folder: Path) -> dict:
    original = bind_original(ORIGINAL_ROOT)
    manifest = json.loads((folder / "manifest.json").read_text())
    for name, spec in manifest["artifacts"].items():
        verified_path(folder, name, spec["sha256"], spec["bytes"])
    new_rows = json.loads((folder / "perworld.json").read_text())
    summary = json.loads((folder / "summary.json").read_text())
    assert summary["status"] == "complete" and len(new_rows) == 8
    rows = list(original["rows"].values()) + new_rows
    index = {(row["arm"], row["seed"]): row for row in rows}
    assert set(index) == {(arm, seed) for arm in ARMS for seed in SEEDS}
    compact, transfers, stable_groups, arrival_misses = [], [], [], []
    exogenous = {}
    for row in rows:
        assert row["status"] == "completed" and 0 < row["actual_length"] <= HORIZON
        length = row["actual_length"]
        root = folder if row["arm"] == "R" else ORIGINAL_ROOT
        decisions = json.loads((root / row["decisions_path"]).read_text())
        misses = [option for option in decisions["commitments"]
                  if option["first_geometric_arrival"] is None and option["charger_input_wh"] > 0]
        arrival_misses.extend({"arm": row["arm"], "seed": row["seed"], **option} for option in misses)
        with np.load(root / row["raw_path"], allow_pickle=False) as raw:
            names = list(raw["metric_fields"])
            qos = raw["metrics"][:, names.index("qos_satisfaction_ratio")]
            assert np.isclose(raw["reward"].sum(), row["raw_native_J"])
            assert np.isclose(qos.sum() / HORIZON, row["horizon_normalized_qos"])
            assert np.isclose(qos[6000:].sum() / 6000, row["late6000_mission_qos"])
            assert np.isclose(raw["reward"][6000:].sum(), row["late6000_native_J"])
            assert np.array_equal(raw["ends"].any(axis=1), np.arange(length) == length - 1)
            event_times = {}
            for kind in ("cutoff", "depletion"):
                counts = raw["metrics"][:, names.index(kind + "_event_count")]
                assert counts.sum() == row[kind + "_event_count_sum"]
                event_times["first_" + kind + "_tick"] = first_true(counts > 0)
            assert np.isclose((raw["native_battery"] <= .10).mean(),
                              row["native_reserve_uav_step_fraction"])
            if length == HORIZON:
                assert int(np.all(raw["native_battery"][11700:] <= .10, axis=0).sum()) == row[
                    "final300_persistent_reserve_members"]
            else:
                assert row["final300_persistent_reserve_members"] is None
            current = (raw["user_xy_m"].copy(), raw["rng_state_sha256_by_step"].copy())
            if row["seed"] in exogenous:
                for left, right in zip(current, exogenous[row["seed"]]):
                    common = min(len(left), len(right))
                    assert np.array_equal(left[:common], right[:common])
            else:
                exogenous[row["seed"]] = current
            decoded_nearest = np.linalg.norm(raw["native_post_xyz"][:, :, None, :2] -
                                             np.asarray(row["station_xy"])[None, None], axis=3).argmin(axis=2)
            eligible = raw["native_charging_eligible"].astype(bool)
            nearest = decoded_nearest
            if row["arm"] == "R":
                nearest = raw["native_post_nearest_station"]
                assert not np.any(eligible & (nearest != decoded_nearest))
                assert not np.any(eligible & (nearest != raw["native_station_target"]))
            assert not np.any((raw["native_charger_input_wh"] > 0) & ~eligible)
            demand = np.column_stack([
                ((eligible & (nearest == station)) * raw["native_consumed_wh"]).sum(axis=1) * 3600
                for station in range(2)])
            overload = demand > 1000.0
            station_readings = {"station_overload_ticks_any": int(overload.any(axis=1).sum()),
                                "first_overload_tick": first_true(overload.any(axis=1))}
            for station in range(2):
                mask = eligible & (nearest == station)
                if row["arm"] == "R":
                    assert np.array_equal(mask.sum(axis=1), raw["native_eligible_station_count"][:, station])
                    assert np.allclose(demand[:, station], raw["native_eligible_station_demand_w"][:, station])
                    assert int(overload[:, station].sum()) == row[f"station{station}_overload_ticks"]
                station_readings[f"station{station}_overload_ticks"] = int(overload[:, station].sum())
                members = np.flatnonzero(mask[9000:].all(axis=0)) if length == HORIZON else np.array([], dtype=int)
                if not len(members):
                    continue
                motion = np.linalg.norm(raw["native_post_xyz"][9000:, members] -
                                        raw["native_pre_xyz"][9000:, members], axis=2)
                cohort_input = float(raw["native_charger_input_wh"][9000:, members].sum())
                cohort_consumed = float(raw["native_consumed_wh"][9000:, members].sum())
                stable_groups.append({
                    "arm": row["arm"], "seed": row["seed"], "station": station,
                    "members": members.tolist(), "maximum_member_motion_m": float(motion.max()),
                    "mean_station_eligible_demand_w": float(demand[9000:, station].mean()),
                    "cohort_charger_input_wh": cohort_input,
                    "cohort_consumed_wh": cohort_consumed,
                    "cohort_input_minus_consumed_wh": cohort_input - cohort_consumed,
                    "real_f_member_steps": int(raw["mode"][9000:, members].sum()),
                    "member_stock_change_wh": float((raw["native_battery"][-1, members] -
                                                       raw["native_battery"][8999, members]).sum() * 160),
                    "terminal_minimum_battery": float(raw["native_battery"][-1, members].min()),
                    "terminal_mean_battery": float(raw["native_battery"][-1, members].mean()),
                })
            for transfer in decisions.get("transfers", []):
                start, stop, member = transfer["start"], transfer["stop"], transfer["member"]
                assert stop > start
                assert transfer["charging_steps"] == int(raw["charging"][start:stop, member].sum())
                assert np.isclose(transfer["charger_input_wh"],
                                  raw["native_charger_input_wh"][start:stop, member].sum())
                before = (raw["initial_native_battery"][member] if start == 0
                          else raw["native_battery"][start - 1, member])
                transfers.append({
                    "seed": row["seed"], **transfer,
                    "net_member_battery_change_wh": float((raw["native_battery"][stop - 1, member] - before) * 160),
                    "native_consumed_wh": float(raw["native_consumed_wh"][start:stop, member].sum()),
                })
        compact.append({"arm": row["arm"], "seed": row["seed"], "actual_length": length,
                        "charged_without_decoded_arrival": len(misses),
                        **{key: row.get(key) for key in FIELDS}, **station_readings, **event_times,
                        "bins": row["bins"]})
    mean_fields = ("horizon_normalized_qos", "raw_native_J", "late6000_mission_qos",
                   "late6000_native_J", "native_reserve_uav_step_fraction")
    means = {arm: {field: float(np.mean([index[arm, seed][field] for seed in SEEDS]))
                   for field in mean_fields} for arm in ARMS}
    flags = {}
    for reference in ("O_H", "P"):
        flags[reference] = {
            "positive_mean_full_J": means["R"]["raw_native_J"] > means[reference]["raw_native_J"],
            "positive_mean_late_J": means["R"]["late6000_native_J"] > means[reference]["late6000_native_J"],
            "full_service_threshold": means["R"]["horizon_normalized_qos"] - means[reference]["horizon_normalized_qos"] >= (0 if reference == "O_H" else .01),
            "late_service_threshold": means["R"]["late6000_mission_qos"] - means[reference]["late6000_mission_qos"] >= (0 if reference == "O_H" else .01),
            "no_higher_mean_reserve": means["R"]["native_reserve_uav_step_fraction"] <= means[reference]["native_reserve_uav_step_fraction"],
            "no_new_adverse_world": all(
                not bool(index["R", seed][field]) or bool(index[reference, seed][field])
                for seed in SEEDS for field in ("cutoff_event_count_sum", "depletion_event_count_sum",
                                                "terminal_zero_service", "final300_persistent_reserve_members")),
            "no_early_endings": all(index[arm, seed]["actual_length"] == HORIZON
                                     for arm in ("R", reference) for seed in SEEDS),
        }
    return {
        "source_sha": summary["launch_sha"], "original_source_sha": original["source_sha"],
        "verified_new_manifest_artifacts": len(manifest["artifacts"]),
        "verified_new_manifest_bytes": manifest["storage_bytes"],
        "raw_complete_common_exogenous_identity": True, "native_endpoint_reconstruction": True,
        "all_native_lengths_full": all(row["actual_length"] == HORIZON for row in rows),
        "finite_useful_package_flags": flags,
        "all_finite_useful_package_flags": all(all(group.values()) for group in flags.values()),
        "original_added_failure_worlds_avoided": all(
            index["R", seed][field] == 0 for seed in (52292801, 52292803)
            for field in ("cutoff_event_count_sum", "depletion_event_count_sum")),
        "means": means, "worlds": compact, "stable_final3000_groups": stable_groups,
        "charged_without_decoded_arrival": arrival_misses, "transfers": transfers,
        "transfer_release_reasons": release_reason_counts(transfers),
        "transfer_unrecovered": [item for item in transfers if not item["post_release_connected_load"]],
        "transfer_real_f_steps": sum(item["real_f_steps"] for item in transfers),
        "transfer_f_overwritten_steps": sum(item["f_overwritten_steps"] for item in transfers),
        "interpretation_limit": "Exposed finite development challenge, not confirmation or sustainability.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.folder)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
