"""Read completed B03 evidence only; never constructs an environment or policy."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np


ARMS = ("P", "O_H", "R")
SEEDS = tuple(range(52392801, 52392809))
FIELDS = (
    "horizon_normalized_qos", "raw_native_J", "late6000_mission_qos",
    "late6000_native_J", "cutoff_event_count_sum", "depletion_event_count_sum",
    "native_reserve_uav_step_fraction", "final300_persistent_reserve_members",
    "terminal_zero_service", "longest_zero_qos_spell", "longest_below_half_qos_spell",
    "station_overload_ticks_any", "station_overload_longest_spell_any",
    "net_stored_energy_wh", "block3_stock_change_wh", "native_final_minimum_battery_ratio",
    "gross_charger_input_wh", "native_consumed_wh", "actual_team_travel_m",
    "guard_checked_actions", "guard_blocked_actions", "commitment_failed_arrivals",
    "commitment_censored", "transfer_count", "transfer_service_recovery_count",
)


def audit(folder: Path) -> dict:
    manifest = json.loads((folder / "manifest.json").read_text())
    for name, spec in manifest["artifacts"].items():
        path = (folder / name).resolve()
        assert path.is_relative_to(folder.resolve()), name
        data = path.read_bytes()
        assert len(data) == spec["bytes"], name
        assert hashlib.sha256(data).hexdigest() == spec["sha256"], name
    rows = json.loads((folder / "perworld.json").read_text())
    summary = json.loads((folder / "summary.json").read_text())
    assert summary["status"] == "complete" and len(rows) == 24
    index = {(row["arm"], row["seed"]): row for row in rows}
    assert set(index) == {(arm, seed) for arm in ARMS for seed in SEEDS}
    compact, all_transfers, stable_groups, arrival_misses = [], [], [], []
    exogenous = {}
    for row in rows:
        assert row["status"] == "completed" and row["actual_length"] == 12000
        decisions = json.loads((folder / row["decisions_path"]).read_text())
        missing_arrival = [option for option in decisions["commitments"]
                           if option["first_geometric_arrival"] is None
                           and option["charger_input_wh"] > 0]
        arrival_misses.extend({"arm": row["arm"], "seed": row["seed"], **option}
                              for option in missing_arrival)
        with np.load(folder / row["raw_path"], allow_pickle=False) as raw:
            names = list(raw["metric_fields"])
            qos = raw["metrics"][:, names.index("qos_satisfaction_ratio")]
            assert np.isclose(raw["reward"].sum(), row["raw_native_J"])
            assert np.isclose(qos.sum() / 12000, row["horizon_normalized_qos"])
            assert np.isclose(qos[6000:].sum() / 6000, row["late6000_mission_qos"])
            assert np.isclose(raw["reward"][6000:].sum(), row["late6000_native_J"])
            for kind in ("cutoff", "depletion"):
                assert raw["metrics"][:, names.index(kind + "_event_count")].sum() == row[kind + "_event_count_sum"]
            assert int(np.all(raw["native_battery"][11700:] <= .10, axis=0).sum()) == row["final300_persistent_reserve_members"]
            assert np.isclose((raw["native_battery"] <= .10).mean(), row["native_reserve_uav_step_fraction"])
            assert np.array_equal(raw["ends"].any(axis=1), np.arange(12000) == 11999)
            current = (raw["user_xy_m"].copy(), raw["rng_state_sha256_by_step"].copy())
            if row["seed"] in exogenous:
                assert all(np.array_equal(left, right) for left, right in zip(current, exogenous[row["seed"]]))
            else:
                exogenous[row["seed"]] = current
            for station in range(2):
                member_mask = raw["native_charging_eligible"] & (raw["native_station_target"] == station)
                assert np.array_equal(member_mask.sum(axis=1), raw["native_eligible_station_count"][:, station])
                demand = (member_mask * raw["native_consumed_wh"]).sum(axis=1) * 3600
                assert np.allclose(demand, raw["native_eligible_station_demand_w"][:, station])
                overload = demand > raw["legal_station_capacity_w"][:, station]
                assert int(overload.sum()) == row[f"station{station}_overload_ticks"]
                members = np.flatnonzero(member_mask[9000:].all(axis=0))
                if not len(members):
                    continue
                motion = np.linalg.norm(raw["native_post_xyz"][9000:, members] -
                                        raw["native_pre_xyz"][9000:, members], axis=2)
                stable_groups.append({
                    "arm": row["arm"], "seed": row["seed"], "station": station,
                    "members": members.tolist(), "maximum_member_motion_m": float(motion.max()),
                    "mean_station_eligible_demand_w": float(demand[9000:].mean()),
                    "station_input_wh": float(raw["native_station_input_wh"][9000:, station].sum()),
                    "real_f_member_steps": int(raw["mode"][9000:, members].sum()),
                    "member_stock_change_wh": float((raw["native_battery"][-1, members] -
                                                       raw["native_battery"][8999, members]).sum() * 160),
                    "terminal_minimum_battery": float(raw["native_battery"][-1, members].min()),
                })
            for transfer in decisions["transfers"]:
                start, stop, member = transfer["start"], transfer["stop"], transfer["member"]
                assert stop > start
                assert transfer["charging_steps"] == int(raw["charging"][start:stop, member].sum())
                assert np.isclose(transfer["charger_input_wh"], raw["native_charger_input_wh"][start:stop, member].sum())
                before = (raw["initial_native_battery"][member] if start == 0
                          else raw["native_battery"][start - 1, member])
                all_transfers.append({
                    "seed": row["seed"], **transfer,
                    "net_member_battery_change_wh": float((raw["native_battery"][stop - 1, member] - before) * 160),
                    "native_consumed_wh": float(raw["native_consumed_wh"][start:stop, member].sum()),
                })
        compact.append({"arm": row["arm"], "seed": row["seed"],
                        "charged_without_decoded_arrival": len(missing_arrival),
                        **{key: row.get(key) for key in FIELDS}, "bins": row["bins"]})
    means = {arm: {field: float(np.mean([index[arm, seed][field] for seed in SEEDS]))
                   for field in ("horizon_normalized_qos", "raw_native_J", "late6000_mission_qos",
                                 "late6000_native_J", "native_reserve_uav_step_fraction")}
             for arm in ARMS}
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
            "no_early_endings": all(index[arm, seed]["actual_length"] == 12000
                                     for arm in ("R", reference) for seed in SEEDS),
        }
    return {
        "source_sha": summary["launch_sha"], "verified_manifest_artifacts": len(manifest["artifacts"]),
        "verified_manifest_bytes": manifest["storage_bytes"], "raw_full_exogenous_identity": True,
        "native_endpoint_reconstruction": True, "finite_useful_package_flags": flags,
        "all_finite_useful_package_flags": all(all(group.values()) for group in flags.values()),
        "means": means, "worlds": compact, "stable_final3000_groups": stable_groups,
        "charged_without_decoded_arrival": arrival_misses,
        "transfers": all_transfers,
        "transfer_release_reasons": dict(Counter(item["release_reason"] for item in all_transfers)),
        "transfer_unrecovered": [item for item in all_transfers if not item["post_release_connected_load"]],
        "transfer_real_f_steps": sum(item["real_f_steps"] for item in all_transfers),
        "transfer_f_overwritten_steps": sum(item["f_overwritten_steps"] for item in all_transfers),
        "interpretation_limit": "Exploratory finite-panel flags, not confirmation, sustainability or a deployment certificate.",
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
