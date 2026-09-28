"""Read existing B03 artifacts; never construct an environment or launch a run."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np


def same(actual, expected):
    if isinstance(expected, dict):
        assert actual.keys() == expected.keys()
        for key in expected:
            same(actual[key], expected[key])
    elif isinstance(expected, list):
        assert len(actual) == len(expected)
        for left, right in zip(actual, expected):
            same(left, right)
    elif isinstance(expected, float):
        assert np.isclose(actual, expected, atol=1e-12, rtol=1e-12), (actual, expected)
    else:
        assert actual == expected, (actual, expected)


def first(mask):
    indices = np.flatnonzero(mask)
    return int(indices[0]) if len(indices) else None


def changed(left, right):
    match = (left == right) | (np.isnan(left) & np.isnan(right))
    return ~match.reshape(len(match), -1).all(axis=1)


def audit(out, repo, raw_root=None):
    sys.path.insert(0, str(repo))
    from experiments.candidates.energy_relay_benchmark.b01.evaluation import world_row
    from experiments.candidates.uav_information_value.b02.readout import battery_reading
    from experiments.candidates.uav_information_value.b03.readout import summarize

    raw_root = out / "raw" if raw_root is None else raw_root
    load = lambda name: json.loads((out / name).read_text())
    config, rows, summary, manifest = map(load, ("config.json", "perworld.json", "summary.json", "manifest.json"))
    assert summary["status"] == "complete" and summary["actual_transitions"] == 288000
    assert summary["fits"] == 0 and summary["optimizer_updates"] == 0
    assert config["horizon"] == 3000 and len(config["jobs"]) == len(rows) == 96
    assert {row["seed"] for row in rows} == set(range(28100301, 28100333))
    reconstructed = summarize(rows, config["jobs"])
    for key, value in reconstructed.items():
        same(summary[key], value)
    checked_bytes = 0
    for name, record in (manifest["artifacts"] | manifest["raw"]).items():
        path = raw_root / Path(name).relative_to("raw") if name.startswith("raw/") else out / name
        blob = path.read_bytes()
        assert len(blob) == record["bytes"]
        assert hashlib.sha256(blob).hexdigest() == record["sha256"], name
        checked_bytes += len(blob)
    records, pair_details = {}, {}
    for row in rows:
        assert row["status"] == "completed" and row["actual_length"] == 3000
        path = raw_root / Path(row["raw_path"]).relative_to("raw")
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["raw_sha256"]
        with np.load(path, allow_pickle=False) as file:
            arrays = {key: file[key] for key in file.files}
        assert all(value.dtype.kind != "O" for value in arrays.values())
        for key, value in arrays.items():
            if value.dtype.kind in "fc":
                assert not np.isinf(value).any(), (row["job_key"], key)
        for key in ("reward", "metrics", "info_controller_proposal", "info_shield_submitted",
                    "info_native_pre_xyz", "info_native_post_xyz", "info_native_delta_xyz", "info_native_battery"):
            assert len(arrays[key]) == 3000 and np.isfinite(arrays[key]).all(), key
        native = world_row(row["seed"], arrays["reward"], arrays["metrics"], arrays["ends"], arrays, time_step_s=1.0)
        # Native time_step is one second in the fixed S2 interface.
        for key, value in (native | battery_reading(arrays["info_native_battery"])).items():
            same(row[key], value)
        np.testing.assert_array_equal(arrays["info_native_delta_xyz"], arrays["info_native_post_xyz"] - arrays["info_native_pre_xyz"])
        np.testing.assert_array_equal(arrays["info_native_pre_xyz"][1:], arrays["info_native_post_xyz"][:-1])
        same(row["native_movement_m_sum"], float(np.linalg.norm(arrays["info_native_delta_xyz"], axis=2).sum()))
        present = np.isfinite(arrays["info_current_bs_xy"]).all(axis=1)
        seen = np.maximum.accumulate(present)
        np.testing.assert_array_equal(present, arrays["info_bs_present"])
        np.testing.assert_array_equal(seen, arrays["info_bs_seen"])
        same(row["first_legal_bs_step"], first(present))
        memory = np.full(2, np.nan)
        for t in range(3000):
            if present[t]:
                memory = arrays["info_current_bs_xy"][t]
            np.testing.assert_array_equal(arrays["info_observed_memory_bs_xy"][t], memory)
        indices = np.arange(0, 3000, 30)
        sources = arrays["info_plan_bs_input_source"]
        np.testing.assert_array_equal(arrays["info_plan_step"], indices)
        np.testing.assert_array_equal(arrays["info_held_plan_source"], np.repeat(sources, 30))
        np.testing.assert_array_equal(arrays["info_plan_supplied_user_count"], arrays["info_plan_legal_user_count"])
        expected_source = np.where(present[indices], "observed-current", np.where(seen[indices], "observed-memory", "absent"))
        prior = row["prior_bs_xy"]
        if row["arm"] != "H_BS" and prior is not None:
            expected_source[~seen[indices]] = "inferred"
            station = []
            for station_id in (0, 1):
                valid = np.flatnonzero(arrays["info_reset_station_valid"][:, station_id])
                station.append(arrays["info_reset_station_xyz"][valid[0], station_id, :2] if len(valid) else None)
            expected_prior = station[0] if row["arm"] == "S0_BS" else np.clip((station[0] - .3 * station[1]) / .7, 0, 8000)
            np.testing.assert_array_equal(prior, expected_prior)
        np.testing.assert_array_equal(sources, expected_source)
        np.testing.assert_array_equal(arrays["info_plan_prior_used"], sources == "inferred")
        for i, t in enumerate(indices):
            expected_xy = arrays["info_observed_memory_bs_xy"][t] if seen[t] else prior if sources[i] == "inferred" else np.full(2, np.nan)
            np.testing.assert_array_equal(arrays["info_plan_bs_input_xy"][i], expected_xy)
        assert not arrays["info_plan_known_bs_omitted"].any()
        generated = arrays["info_plan_generated_relay_count"]
        assigned = arrays["info_plan_assigned_relay_count"]
        target_capacity = np.isfinite(arrays["info_plan_targets_xy"]).all(axis=2).sum(axis=1)
        np.testing.assert_array_equal(assigned, np.minimum(generated, target_capacity))
        np.testing.assert_array_equal(generated, np.isfinite(arrays["info_plan_relays_xy"]).all(axis=2).sum(axis=1))
        same(row["prior_used_plans"], int((sources == "inferred").sum()))
        same(row["generated_relay_count_sum"], int(generated.sum()))
        same(row["assigned_relay_count_sum"], int(assigned.sum()))
        records[row["job_key"]] = {
            "inferred_input_plans": int((sources == "inferred").sum()),
            "inferred_generated_plans": int(((sources == "inferred") & (generated > 0)).sum()),
            "inferred_assigned_plans": int(((sources == "inferred") & (assigned > 0)).sum()),
            "inferred_held_steps_after_genuine_sighting": int(((arrays["info_held_plan_source"] == "inferred") & seen).sum()),
            "shield_changed_uav_steps": int((arrays["info_controller_proposal"] != arrays["info_shield_submitted"]).any(axis=2).sum()),
            "native_moving_uav_steps": int((np.linalg.norm(arrays["info_native_delta_xyz"], axis=2) > 0).sum()),
        }
    for seed in range(28100301, 28100333):
        raws = {}
        for arm in ("H_BS", "P_BS", "S0_BS"):
            with np.load(raw_root / f"{arm}_{seed}.npz", allow_pickle=False) as file:
                raws[arm] = {key: file[key] for key in file.files}
        for arm in ("P_BS", "S0_BS"):
            for field in ("info_reset_station_xyz", "info_reset_station_valid"):
                np.testing.assert_array_equal(raws[arm][field], raws["H_BS"][field])
            np.testing.assert_array_equal(raws[arm]["info_native_pre_xyz"][0], raws["H_BS"]["info_native_pre_xyz"][0])
        pair_details[str(seed)] = {}
        for left, right in (("P_BS", "S0_BS"), ("P_BS", "H_BS"), ("S0_BS", "H_BS")):
            detail = {}
            for field in ("info_plan_bs_input_xy", "info_plan_relays_xy", "info_plan_targets_xy",
                          "info_controller_proposal", "info_shield_submitted", "info_native_delta_xyz"):
                delta = changed(raws[left][field], raws[right][field])
                detail[field] = {"different_rows": int(delta.sum()), "first_row": first(delta)}
            pair_details[str(seed)][f"{left}-{right}"] = detail
    return {"status": "verified", "source_sha": config["launch_sha"], "checked_manifest_bytes": checked_bytes,
            "episodes": len(rows), "transitions": sum(row["actual_length"] for row in rows),
            "replans": sum(row["plan_count"] for row in rows), "summary_reconstructed": True,
            "native_scores_and_risk_reconstructed": True, "perworld": records,
            "paired_trace_differences": pair_details,
            "scope": "descriptive complete-trajectory differences, not a causal mediation estimate"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path)
    args = parser.parse_args()
    result = audit(args.out, args.repo, args.raw_root)
    args.report.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key not in ("perworld", "paired_trace_differences")}))
