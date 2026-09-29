"""Verify retained bytes and reconstruct B01 readings without native execution."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import torch

from experiments.candidates.uav_availability_recovery.learning import EVAL_IDS, FIT_SEEDS
from experiments.candidates.uav_availability_recovery.runner import write_json


def digest(path):
    hasher = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            hasher.update(block)
    return hasher.hexdigest()


def close(actual, expected, label, tolerance=1e-9):
    a, e = np.asarray(actual), np.asarray(expected)
    if a.shape != e.shape or not np.isfinite(a).all() or not np.isfinite(e).all():
        raise ValueError(f"{label}: shape or finite mismatch")
    error = float(np.max(np.abs(a-e))) if a.size else 0.0
    if error > tolerance:
        raise ValueError(f"{label}: maximum error {error}")
    return error


def streak(values):
    flags = np.asarray(values) < .6
    boundaries = np.flatnonzero(np.diff(np.r_[False, flags, False].astype(int)))
    return int(np.max(boundaries[1::2]-boundaries[::2])) if len(boundaries) else 0


def verify_episode(row, arrays):
    if int(arrays["world_id"]) != row["world"] or str(arrays["source_sha256"]) != row["source_sha256"]:
        raise ValueError("raw source identity")
    native = arrays["native_metrics"]
    if native.shape != (500, 9):
        raise ValueError("missing complete native metric rows")
    qos = np.minimum(arrays["user_rates_mbps"], 1).mean(axis=1)
    weakest = (arrays["user_rates_mbps"] >= 1).reshape(500, 3, 10).mean(axis=2).min(axis=1)
    errors = [close(native[:, 1], qos, "native service"),
              close(arrays["weakest_service"], weakest, "weakest hotspot"),
              close(native[:, 0], native[:, 5]+native[:, 2], "native J equation"),
              close(native[:, 5], native[:, 1]-native[:, 6], "S1 safety equation"),
              close(native[:, 7:9], np.zeros((500, 2)), "S1 cutoff/depletion")]
    potential_next = native[:, 4].copy()
    potential_next[-1] = 0
    errors.append(close(native[:, 2], .99*potential_next-native[:, 3], "native gamma .99"))
    errors.extend([close(row["J"], native[:, 0].sum(), "complete J"),
                   close(row["QoS"], qos.mean(), "complete QoS")])
    dt, speed = row["physics"]["time_step"], row["physics"]["max_speed"]
    velocity = np.diff(arrays["positions"], axis=0) / dt
    errors.append(close(velocity, arrays["executed_velocities"], "actual motion"))
    horizontal = arrays["requested_actions"][:, :, :2].astype(np.float64)
    norms = np.linalg.norm(horizontal, axis=2)
    proposed = np.zeros_like(velocity)
    scale = np.where(norms > 1e-8, np.minimum(norms, 1)/np.maximum(norms, 1e-8), 0.0)
    proposed[:, :, :2] = horizontal * scale[:, :, None] * speed
    proposed[:, :, 2] = arrays["requested_actions"][:, :, 2] * row["physics"]["max_vertical_speed_mps"]
    proposed[~arrays["active_mask"]] = 0
    changed = np.any(np.abs(proposed-velocity) > 1e-7, axis=2)
    errors.append(close(arrays["motion_modified"].astype(int), changed.astype(int), "motion modification"))
    errors.append(close(row["guard_blocked_actions"], arrays["native_guard_count"].sum(), "native guard count"))
    path = np.linalg.norm(np.diff(arrays["positions"], axis=0), axis=2)
    errors.append(close(row["reserve_path_length_m"], path[:, 6:].sum(), "reserve path"))
    onset, rejoin = row["onset"], row["onset"]+row["duration"]
    event = row["cell"] == "event"
    expected_events = [("LEAVE", onset), ("REJOIN", rejoin)] if event else []
    events = json.loads(str(arrays["events_json"]))
    if [(item["kind"], item["physical_step"]) for item in events] != expected_events:
        raise ValueError("event boundary inventory")
    expected_counts = np.full(500, 8)
    if event:
        expected_counts[onset:rejoin] = 7
    errors.append(close(arrays["active_mask"].sum(axis=1), expected_counts, "availability timing"))
    if not np.all(arrays["positions"][:, :, 2] == 50) or np.any(arrays["requested_actions"][:, :, 2]):
        raise ValueError("fixed altitude")
    if event:
        window = weakest[onset:rejoin+60]
        deficit = np.maximum(0, .9-window)/.9
        errors.append(close(row["J_event"], 1-deficit.mean(), "event metric"))
        errors.append(close(row["event_deficit_sum"], deficit.sum(), "event deficit"))
        if row["event_catastrophe"] != int(streak(window) >= 10):
            raise ValueError("event catastrophe streak")
    if row["complete_max_below_06_streak"] != streak(weakest):
        raise ValueError("complete catastrophe streak")
    learned_or_planned = row["arm"].startswith("L") or row["arm"] == "P"
    expected_clocks = sorted({onset, rejoin, *range(((onset+9)//10)*10, 500, 10)}) if event and learned_or_planned else []
    if arrays["decision_step"].tolist() != expected_clocks:
        raise ValueError("event and absolute-clock decisions")
    if np.any(arrays["joint_action"] < 0) or np.any(arrays["joint_action"] > 15):
        raise ValueError("joint action inventory")
    errors.append(close(row["joint_action_counts"], np.bincount(arrays["joint_action"], minlength=16), "joint counts"))
    for start, stop, reward in zip(arrays["macro_start"], arrays["macro_stop"], arrays["macro_reward"]):
        errors.append(close(reward, native[start:stop, 0].sum(), "actual macro return"))
    if row["arm"].startswith("L"):
        if arrays["macro_start"].tolist() != expected_clocks or arrays["macro_stop"].tolist() != expected_clocks[1:]+[500]:
            raise ValueError("forced prefix or macro endpoint")
    predictions = json.loads(str(arrays["predictions_json"]))
    calls = 0
    for prediction in predictions:
        t, action = prediction["step"], prediction["action"]
        h, w = np.asarray(prediction["horizons"]), np.asarray(prediction["weights"])
        if t+max(h) > 500 or sum(w) != min(120, 500-t):
            raise ValueError("forecast beyond complete horizon")
        errors.append(close(prediction["scores"], np.asarray(prediction["predictions"]) @ w / sum(w), "quadrature"))
        realized = qos[t+h-1]
        errors.append(close(prediction["realized_QoS_at_horizons"], realized, "realized prediction endpoints"))
        errors.append(close(prediction["selected_prediction_errors"], np.asarray(prediction["predictions"])[action]-realized,
                            "prediction error"))
        calls += prediction["snapshot_calls_this_decision"]
        if prediction["snapshot_calls"] != calls:
            raise ValueError("cumulative versus marginal snapshot calls")
    if calls != row["service_snapshot_calls"]:
        raise ValueError("episode snapshot calls")
    return max(errors), calls


def read_saved(out):
    out = Path(out)
    summary = json.loads((out / "summary.json").read_text())
    if summary["state"] != "complete":
        raise ValueError("only a complete batch can receive a complete scientific reading")
    artifacts = json.loads((out / "artifacts.json").read_text())
    total_bytes = 0
    for artifact in artifacts["files"]:
        path = out / artifact["path"]
        if path.stat().st_size != artifact["bytes"] or digest(path) != artifact["sha256"]:
            raise ValueError(f"artifact mismatch: {artifact['path']}")
        total_bytes += artifact["bytes"]
    if total_bytes != artifacts["total_bytes"]:
        raise ValueError("artifact byte count")
    train = [json.loads(line) for line in (out / "raw" / "training_episodes.jsonl").read_text().splitlines()]
    evaluation = json.loads((out / "perworld.json").read_text())
    if len(train) != 1536 or len(evaluation) != 384:
        raise ValueError("complete episode inventory")
    if len({row["world"] for row in train}) != 1536 or set(row["world"] for row in train).intersection(EVAL_IDS):
        raise ValueError("world stream collision")
    error = calls = macro_rows = 0
    for row in [*train, *evaluation]:
        path = out / row["raw"]
        if digest(path) != row["raw_sha256"]:
            raise ValueError("raw locator identity")
        with np.load(path, allow_pickle=False) as arrays:
            difference, snapshots = verify_episode(row, arrays)
            error = max(error, difference)
            calls += snapshots
            macro_rows += len(arrays["macro_start"])
    by_arm = {(row["arm"], row["world"]): row for row in evaluation}
    if len(by_arm) != 384:
        raise ValueError("duplicate evaluation rows")
    prefix_equal = 0
    for world in EVAL_IDS:
        reference_row = by_arm["S_no_event", world]
        with np.load(out / reference_row["raw"], allow_pickle=False) as reference:
            for arm in ["S", "P", *(f"L_{seed}" for seed in FIT_SEEDS)]:
                row = by_arm[arm, world]
                with np.load(out / row["raw"], allow_pickle=False) as values:
                    onset = row["onset"]
                    for field in ("positions", "targets", "requested_actions", "native_metrics", "active_mask"):
                        if not np.array_equal(reference[field][:onset], values[field][:onset]):
                            raise ValueError(f"common forced prefix differs: {world}/{arm}/{field}")
                prefix_equal += 1
    fit_checks = []
    curves = json.loads((out / "curves.json").read_text())
    if len(curves) != 96 or sum(row["optimizer_updates"] for row in curves) != 1536:
        raise ValueError("collection optimizer count")
    for seed in FIT_SEEDS:
        own = [row for row in train if row["seed"] == seed]
        if len(own) != 512 or sorted(row["episode_index"] for row in own) != list(range(512)):
            raise ValueError("training episode sequence")
        own_curves = [row for row in curves if row["seed"] == seed]
        if sorted(row["collection"] for row in own_curves) != list(range(1, 33)):
            raise ValueError("collection sequence")
        initial = torch.load(out / "raw" / f"L_{seed}_init.pt", map_location="cpu", weights_only=True)
        final = torch.load(out / "raw" / f"L_{seed}_final.pt", map_location="cpu", weights_only=True)
        before = torch.cat([value.ravel() for value in initial["weights"].values()])
        after = torch.cat([value.ravel() for value in final["weights"].values()])
        updates = {int(value["step"]) for value in final["optimizer"]["state"].values()}
        if updates != {512} or final["optimizer_updates"] != 512:
            raise ValueError("optimizer checkpoint update count")
        recorded = next(row for row in summary["fit_results"] if row["seed"] == seed)
        change = float(torch.linalg.vector_norm(after-before))
        errors = close(recorded["parameter_change_norm"], change, "learner movement", 1e-6)
        error = max(error, errors)
        if recorded["macro_rows"] != sum(row["macro_rows"] for row in own):
            raise ValueError("training macro exposure")
        fit_checks.append({"seed": seed, "actual_optimizer_updates": 512, "parameter_change_norm": change})
    if calls != summary["service_snapshot_calls"] or calls > 270336:
        raise ValueError("complete snapshot count")
    if summary["training_steps"] != 768000 or summary["evaluation_steps"] != 192000:
        raise ValueError("complete native step count")
    reading = {"state": "verified_complete", "launch_sha": summary["launch_sha"],
               "verified_files": len(artifacts["files"]), "verified_bytes": total_bytes,
               "native_steps": 960000, "training_episodes": len(train), "evaluation_episodes": len(evaluation),
               "maximum_numeric_reconstruction_error": error, "identical_pre_event_comparisons": prefix_equal,
               "service_snapshot_calls": calls, "fit_checks": fit_checks,
               "scope": "saved-byte/native-accounting verification; scientific interpretation remains separate"}
    write_json(out / "reading.json", reading)
    return reading


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    print(json.dumps(read_saved(args.out), sort_keys=True))


if __name__ == "__main__":
    main()
