"""Read-only B01 artifact audit, independent of the simulator and policy loader."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import t as student_t


def audit(run: Path, raw_root: Path):
    config = json.loads((run / "config.json").read_text())
    rows = json.loads((run / "perworld.json").read_text())
    summary = json.loads((run / "summary.json").read_text())
    manifest = json.loads((run / "manifest.json").read_text())
    expected = {job["job_key"] for job in config["jobs"]}
    assert len(rows) == len(expected) == 80
    assert {row["job_key"] for row in rows} == expected
    assert summary["status"] == "complete"
    assert summary["actual_transitions"] == 240000
    assert config["launch_sha"] == manifest["launch_sha"] == summary["launch_sha"]
    files, raw_bytes, errors = 0, 0, []
    target_none_uav_steps = 0
    by_key = {(row["program"], row["seed"]): row for row in rows}

    def raw_path(name):
        relative = Path(name)
        return raw_root / relative.relative_to("raw")

    for name, record in manifest["artifacts"].items():
        path = raw_path(name) if name.startswith("raw/") else run / name
        data = path.read_bytes()
        assert len(data) == record["bytes"], name
        assert hashlib.sha256(data).hexdigest() == record["sha256"], name
        files += 1
        raw_bytes += len(data) if name.startswith("raw/") else 0

    def match(row, field, value):
        if value is None:
            assert row[field] is None, (row["job_key"], field)
        else:
            difference = abs(float(row[field]) - float(value))
            errors.append(difference)
            assert difference < 1e-9, (row["job_key"], field, difference)

    identity_pairs = []
    for row in rows:
        assert row["status"] == "completed" and row["actual_length"] == 3000
        assert row["terminal_type"] == "truncated" and row["inference_calls"] == 3000
        path = raw_path(row["raw_path"])
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["raw_sha256"]
        progress = json.loads(path.with_suffix(".progress.json").read_text())
        assert progress["steps"] == 3000 and progress["status"] == "completed"
        with np.load(path, allow_pickle=False) as data:
            arrays = {key: data[key] for key in data.files}
        for key, value in arrays.items():
            if key != "metric_fields":
                assert value.shape[0] == 3000, (row["job_key"], key)
                if key == "target_xy":
                    # The native heuristic records a pair of NaNs for no target.
                    assert row["program"] == "H_central10"
                    missing = np.isnan(value)
                    assert np.array_equal(missing[..., 0], missing[..., 1])
                    assert np.isfinite(value[~missing]).all()
                    target_none_uav_steps += int(missing[..., 0].sum())
                else:
                    assert np.isfinite(value).all(), (row["job_key"], key)
        assert arrays["ends"][-1].tolist() == [False, True]
        assert not arrays["ends"][:-1].any()
        fields = list(arrays["metric_fields"])
        for column, field in enumerate(fields):
            match(row, f"{field}_sum", arrays["metrics"][:, column].sum())
            match(row, f"{field}_per_step", arrays["metrics"][:, column].mean())
        qos = arrays["metrics"][:, fields.index("qos_satisfaction_ratio")]
        first = np.flatnonzero(qos > 0)
        match(row, "raw_native_J", arrays["reward"].sum())
        match(row, "qos_per_step", qos.mean())
        match(row, "qos_first1000", qos[:1000].mean())
        match(row, "qos_after1000", qos[1000:].mean())
        match(row, "first_service_step", int(first[0]) if len(first) else None)
        match(row, "first_service_censored_wait", int(first[0]) if len(first) else 3000)
        match(row, "min_decoded_battery", arrays["battery"].min())
        match(row, "reserve10_uav_step_fraction", (arrays["battery"] < .1).mean())
        match(row, "mean_horizontal_speed_mps",
              np.linalg.norm(arrays["physical_displacement"][..., :2], axis=-1).mean())
        if row["program"].startswith("C_"):
            mean_xy = arrays["own_xyz"][0, :, :2].mean(axis=0)
            expected_frame = ("ROT180" if (mean_xy < 4000).all() else
                              "MIRROR_X" if mean_xy[0] < 4000 else
                              "MIRROR_Y" if mean_xy[1] < 4000 else "IDENTITY")
            assert row["frame"] == expected_frame
            baseline = by_key[row["program"].replace("C_", "P_"), row["seed"]]
            assert row["sample_seed"] == baseline["sample_seed"]
            assert row["identity"] == baseline["identity"]
            if row["frame"] == "IDENTITY":
                with np.load(raw_path(baseline["raw_path"]), allow_pickle=False) as original:
                    assert set(original.files) == set(arrays)
                    assert all(np.array_equal(arrays[k], original[k]) for k in arrays)
                identity_pairs.append(row["job_key"])

    for contrast, values in summary["contrasts"].items():
        pair, mode = contrast.split("_", 1)
        candidate = "C_" + mode
        baseline = "P_" + mode if pair == "C-P" else "H_central10"
        for field, record in values.items():
            seeds = record["paired_seeds"]
            delta = np.asarray([by_key[candidate, seed][field] - by_key[baseline, seed][field]
                                for seed in seeds], dtype=float)
            assert np.array_equal(delta, np.asarray(record["differences"]))
            assert abs(float(delta.mean()) - record["mean"]) < 1e-9
            se = delta.std(ddof=1) / np.sqrt(len(delta))
            interval = delta.mean() + np.array([-1, 1]) * student_t.ppf(.975, len(delta)-1) * se
            assert np.allclose(interval, record["ci95"], atol=1e-9, rtol=0)

    return {
        "status": "passed", "launch_sha": config["launch_sha"],
        "manifest_files_verified": files, "raw_files": len(rows),
        "raw_and_progress_bytes": raw_bytes, "episodes": len(rows), "native_steps": 240000,
        "raw_numeric_and_bool_arrays_finite_except_native_no_target_sentinel": True,
        "native_no_target_uav_steps": target_none_uav_steps,
        "maximum_recomputed_metric_absolute_difference": max(errors),
        "all_summary_contrasts_recomputed": True,
        "identity_frame_pairs_array_exact": identity_pairs,
        "canonical_frames_per_mode": dict(Counter(row["frame"] for row in rows
                                                   if row["program"] == "C_deterministic")),
        "raw_root": str(raw_root),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = audit(args.run, args.raw_root or args.run / "raw")
    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(serialized)
    print(serialized)


if __name__ == "__main__":
    main()
