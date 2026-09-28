"""Read retained output without importing or executing the controller/runner."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import t as student_t


def _digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest() if hasattr(hashlib, "file_digest") else _hash_stream(handle)


def _hash_stream(handle):
    digest = hashlib.sha256()
    for block in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(block)
    return digest.hexdigest()


def audit_decision(record, arm, own_xyz):
    """Reconstruct search selection from saved queries, without scoring a model."""
    candidates = record["candidates"]
    assert len(candidates) == record["query_count"]
    fixed = np.asarray(record["F_mask"], dtype=bool)
    expected_count = 4 + 12 * int((~fixed).sum()) if arm == "R" else 1
    assert len(candidates) == expected_count
    assert record["kmeans_solve_count"] == {"H": 1, "G": 8, "R": 9}[arm]
    for candidate in candidates:
        layout = np.asarray(candidate["targets_xyz"])
        assert layout.shape == (8, 3) and np.isfinite(layout).all()
        np.testing.assert_array_equal(layout[fixed], own_xyz[fixed])
        travel = float(np.linalg.norm(layout - own_xyz, axis=1).sum())
        assert travel == candidate["travel_m"]
        assert 0 <= candidate["score"] <= 1

    def preferred(new, old):
        gain = candidates[new]["score"] - candidates[old]["score"]
        return (gain > 1e-10 or (abs(gain) <= 1e-10
                and candidates[new]["travel_m"] < candidates[old]["travel_m"] - 1e-6))

    accepted, best = set(), 0
    if arm == "R":
        assert [row["identity"] for row in candidates[:4]] == ["H", "G", "carried_R", "current"]
        accepted.add(0)
        for index in range(1, 4):
            if preferred(index, best):
                best = index
                accepted.add(index)
        index = 4
        for sweep, (horizontal, vertical) in enumerate(((500.0, 50.0), (125.0, 25.0))):
            for offset in range(8):
                member = (record["clock_index"] + offset) % 8
                if fixed[member]:
                    continue
                incumbent = np.asarray(candidates[best]["targets_xyz"])
                winner = best
                for axis, sign in ((0, 1), (0, -1), (1, 1), (1, -1), (2, 1), (2, -1)):
                    row = candidates[index]
                    assert (row["identity"], row["sweep"], row["member"], row["direction"]) == (
                        "pattern", sweep, member, [axis, sign])
                    expected = incumbent.copy()
                    expected[member, axis] += sign * (vertical if axis == 2 else horizontal)
                    expected[member] = np.clip(expected[member], [0, 0, 50], [8000, 8000, 200])
                    np.testing.assert_array_equal(row["targets_xyz"], expected)
                    if preferred(index, winner):
                        winner = index
                    index += 1
                if winner != best:
                    best = winner
                    accepted.add(best)
        np.testing.assert_array_equal(record["selected_targets_xyz"], candidates[best]["targets_xyz"])
    else:
        assert candidates[0]["identity"] == arm
        accepted.add(0)
        np.testing.assert_array_equal(np.asarray(record["selected_targets_xyz"], dtype=float)[~fixed],
                                      np.asarray(candidates[0]["targets_xyz"])[~fixed])
    assert [i for i, row in enumerate(candidates) if row["selected"]] == [best]
    assert {i for i, row in enumerate(candidates) if row["accepted"]} == accepted
    assert record["selected_qos"] == candidates[best]["score"]


def read(out):
    out = Path(out)
    manifest = json.loads((out / "manifest.json").read_text())
    config = json.loads((out / "config.json").read_text())
    rows = json.loads((out / "perworld.json").read_text())
    summary = json.loads((out / "summary.json").read_text())
    if summary["status"] != "complete":
        raise ValueError("complete reading requires a complete native batch")
    expected = {(arm, seed) for arm in ("H", "G", "R") for seed in config["world_seeds"]}
    if len(rows) != len(expected) or {(r["arm"], r["seed"]) for r in rows} != expected:
        raise ValueError("retained world identities differ from fixed complete design")
    verified = 0
    for name, meta in manifest["artifacts"].items():
        path = out / name
        assert path.stat().st_size == meta["bytes"] and _digest(path) == meta["sha256"], name
        verified += 1
    reconstructed, user_paths, max_reward_error, snapshots = {}, {}, 0.0, 0
    for row in rows:
        key = row["job_key"]
        meta = manifest["raw"][key]
        path = out / meta["path"]
        assert path.stat().st_size == meta["bytes"] and _digest(path) == meta["sha256"], key
        verified += 1
        with np.load(path, allow_pickle=False) as a:
            fields = list(a["metric_fields"])
            columns = {name: a["metrics"][:, index] for index, name in enumerate(fields)}
            rewards = a["reward"]
            n = len(rewards)
            assert n == row["actual_length"]
            assert n <= config["horizon"] and bool(a["ends"][-1].any())
            assert not a["ends"][:-1].any()
            for name, values in columns.items():
                assert float(values.sum()) == row[f"{name}_sum"], (key, name, "sum")
                assert float(values.mean()) == row[f"{name}_per_step"], (key, name, "mean")
            assert float(rewards.sum()) == row["raw_native_J"]
            expected_reward = (columns["qos_satisfaction_ratio"]
                               - 2 * columns["return_constraint_cost"]
                               - columns["cutoff_event_penalty"]
                               - columns["depletion_event_penalty"]
                               + columns["graph_potential_delta"])
            error = float(np.abs(rewards - expected_reward).max(initial=0))
            max_reward_error = max(max_reward_error, error)
            assert error <= 1e-12, (key, error)
            assert float(columns["battery_min_ratio"].min()) == row["episode_minimum_battery_ratio"]
            assert float(np.mean(a["battery"] <= .10)) == row["below_fixed_reserve_uav_step_fraction"]
            assert float(np.mean(a["battery"] <= .02)) == row["service_cutoff_uav_step_fraction"]
            assert float(np.mean(a["return_margin"] < 0)) == row["negative_margin_uav_step_fraction"]
            displacement = np.diff(a["physical_xyz_m"], axis=0)
            assert displacement.shape == (n, 8, 3)
            assert float(np.linalg.norm(displacement, axis=-1).sum()) == row["xyz_path_m"]
            assert float(np.linalg.norm(displacement[:, :, :2], axis=-1).sum()) == row["xy_path_m"]
            assert float(a["consumed_wh"].sum()) == row["consumed_wh"]
            records = json.loads(str(a["planner_records_json"]))
            assert [r["step"] for r in records] == list(range(0, n, 30))
            counts = [r["query_count"] for r in records]
            assert max(counts) <= (100 if row["arm"] == "R" else 1)
            assert sum(counts) == row["service_snapshot_calls"]
            for record in records:
                audit_decision(record, row["arm"], a["own_xyz"][record["step"]])
            snapshots += sum(counts)
            user_paths[(row["arm"], row["seed"])] = a["user_xy_m"].copy()
            reconstructed[(row["arm"], row["seed"])] = {
                "qos_per_step": float(columns["qos_satisfaction_ratio"].mean()),
                "raw_native_J": float(rewards.sum()),
                "return_constraint_cost_sum": float(columns["return_constraint_cost"].sum()),
                "episode_minimum_battery_ratio": float(columns["battery_min_ratio"].min()),
                "below_fixed_reserve_uav_step_fraction": float(np.mean(a["battery"] <= .10)),
                "xy_path_m": float(np.linalg.norm(displacement[:, :, :2], axis=-1).sum()),
            }
    assert snapshots == summary["service_snapshot_calls"] and snapshots <= 81600
    for seed in config["world_seeds"]:
        assert np.array_equal(user_paths[("H", seed)], user_paths[("G", seed)])
        assert np.array_equal(user_paths[("H", seed)], user_paths[("R", seed)])
    contrasts = {}
    seeds = config["world_seeds"]
    for candidate, baseline in (("R", "G"), ("R", "H"), ("G", "H")):
        name = f"{candidate}_minus_{baseline}"
        result = {}
        for field in next(iter(reconstructed.values())):
            delta = np.array([reconstructed[(candidate, seed)][field]
                              - reconstructed[(baseline, seed)][field] for seed in seeds])
            half = (float(student_t.ppf(.975, len(seeds) - 1) * delta.std(ddof=1) / np.sqrt(len(seeds)))
                    if len(seeds) > 1 else None)
            interval = [float(delta.mean() - half), float(delta.mean() + half)] if half is not None else None
            saved = summary["contrasts"][name]["metrics"][field]
            assert np.isclose(delta.mean(), saved["mean"], rtol=0, atol=1e-12)
            assert (saved["t95"] is None if interval is None else
                    np.allclose(interval, saved["t95"], rtol=0, atol=1e-10))
            result[field] = {"mean": float(delta.mean()), "t95": interval,
                             "deltas_by_world": dict(zip(map(str, seeds), map(float, delta)))}
        contrasts[name] = result
    return {"status": "verified", "launch_sha": manifest["launch_sha"],
            "artifacts_verified": verified, "worlds_verified": len(rows),
            "native_metric_sums_and_means": "all fields exact", "max_native_reward_error": max_reward_error,
            "all_user_trajectories_equal": True, "service_snapshot_calls": snapshots,
            "all_search_decisions_reconstructed": True,
            "contrasts": contrasts,
            "limits": "RNG and initial-state digests matched by runner; full RNG stream not retained"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = read(args.out)
    (args.out / "reading.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "contrasts"}, sort_keys=True))


if __name__ == "__main__":
    main()
