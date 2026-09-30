#!/usr/bin/env python3
"""Verify new recurrence evidence and explicitly source-bound retained controls."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import torch

from experiments.candidates.uav_local_history.b01.study import file_identity, write_json
from experiments.candidates.uav_fleet_adaptation.b02.contract import array_digest
from experiments.candidates.uav_fleet_adaptation.b02.model import movement, state_digest
from experiments.candidates.uav_fleet_adaptation.b02.read import check_episode, equal, identity
from experiments.candidates.uav_fleet_adaptation.b02.reading import cost_totals
from experiments.candidates.uav_fleet_adaptation.b03.contract import (
    NEW_ARMS, FROZEN, OBJECT, PHASES, Protocol, SOURCE_PINS, source_identities, validate_counts,
)
from experiments.candidates.uav_fleet_adaptation.b03.reading import read_comparisons
from experiments.candidates.uav_fleet_adaptation.b03.retained import load_retained


def read_batch(out, *, permit_fixture=False):
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    out = Path(out).resolve()
    batch = json.loads((out / "summary.json").read_text())
    if batch["status"] != "COMPLETE" or batch["object"] != OBJECT:
        raise ValueError("incomplete/failed worker cannot yield a complete scientific reading")
    config = dict(batch["protocol"])
    config["training_worlds"] = tuple(tuple(phase) for phase in config["training_worlds"])
    config["evaluation_worlds"], config["epochs"] = tuple(config["evaluation_worlds"]), tuple(config["epochs"])
    protocol = Protocol(**config).validate()
    if (not batch["scientific_invocation"] or protocol != FROZEN) and not permit_fixture:
        raise ValueError("not the fixed scientific study")
    if batch["expected"] != protocol.expected():
        raise AssertionError("expected envelope changed")
    if source_identities(ROOT) != batch["source_sha256"]:
        raise AssertionError("reader is not running from the recorded source identities")
    retained = load_retained(batch["retained"]["root"], protocol, repo=ROOT, permit_fixture=permit_fixture,
                             binding=batch["retained"]["binding"])
    for key in ("root", "binding", "original_protocol", "rows", "source_sha256", "raw_verification"):
        if retained[key] != batch["retained"][key]:
            raise AssertionError(f"retained provenance changed: {key}")
    if (retained["old_reading"]["screens"] != batch["retained"]["previous_screens"]
            or retained["old_assets"] != batch["retained"]["original_assets"]
            or cost_totals(retained["rows"]) != batch["retained"]["costs"]):
        raise AssertionError("retained outcomes/asset metadata/historical costs changed")
    config_file = json.loads((out / "config.json").read_text())
    for key in ("object", "launch_sha", "scientific_invocation", "protocol", "expected", "source_sha256", "environment"):
        if config_file[key] != batch[key]:
            raise AssertionError(f"new config/summary mismatch: {key}")
    if config_file["retained"] != {key: batch["retained"][key] for key in
                                    ("root", "binding", "original_protocol", "already_paid", "new_native_steps")}:
        raise AssertionError("new config/retained binding mismatch")
    assets = {}
    for name in ("S0", "BC", "D1", "S"):
        record = batch["assets"][name]
        path = identity(out, record)
        asset = torch.load(path, map_location="cpu", weights_only=True)
        if (asset["endpoint"] != name or asset["launch_sha"] != batch["launch_sha"]
                or asset["protocol"] != batch["protocol"] or asset["architecture"] != [114, 128, 128, 27]
                or asset["activation"] != "relu" or asset["dtype"] != "float32"):
            raise AssertionError("checkpoint identity/architecture mismatch")
        if state_digest(asset["state_dict"]) != record["state_sha256"] or asset["state_sha256"] != record["state_sha256"]:
            raise AssertionError("checkpoint tensor identity mismatch")
        assets[name] = asset
    expected_rows = [(PHASES[p], w, "training", p) for p, worlds in enumerate(protocol.training_worlds) for w in worlds]
    for wi, world in enumerate(protocol.evaluation_worlds):
        expected_rows += [(arm, world, "evaluation", None) for arm in NEW_ARMS[wi % len(NEW_ARMS):] + NEW_ARMS[:wi % len(NEW_ARMS)]]
    found_rows = [(r["arm"], r["world"], r["kind"], r["phase"]) for r in batch["rows"]]
    if found_rows != expected_rows:
        raise AssertionError("phase/world/arm collection order or identity mismatch")
    if assets["S0"]["state_sha256"] == retained["old_assets"]["S0"]["state_sha256"]:
        raise AssertionError("new initialization is the retained initial actor")
    x_parts, y_parts, paired_resets = [], [], {}
    per_row = []
    for row in batch["rows"]:
        if row["kind"] == "training":
            expected_sha = (SOURCE_PINS["experiments/candidates/uav_local_history/b01/controller.py"] if row["phase"] == 0
                            else assets[("BC", "D1")[row["phase"] - 1]]["state_sha256"])
        elif row["arm"] in ("C_memo", "C7_memo"):
            expected_sha = batch["source_sha256"]["experiments/candidates/uav_fleet_adaptation/b02/controllers.py"]
        else:
            expected_sha = assets["S" if row["arm"].startswith("S_") else row["arm"]]["state_sha256"]
        if row["policy_sha256"] != expected_sha:
            raise AssertionError("trajectory is bound to the wrong behavior checkpoint/source")
        path = identity(out, row["raw"])
        with np.load(path, allow_pickle=False) as archive:
            raw = {key: archive[key] for key in archive.files}
        cases = check_episode(raw, row, protocol)
        if cases is not None:
            x_parts.append(cases[0]); y_parts.append(cases[1])
        else:
            key = row["world"]
            previous = paired_resets.setdefault(key, row["initial_state_sha256"])
            if previous != row["initial_state_sha256"]:
                raise AssertionError("evaluation arms did not start from the same native world")
        per_row.append(dict(arm=row["arm"], world=row["world"], kind=row["kind"], verified=True,
                            provenance="new", raw_sha256=row["raw"]["sha256"]))
    for row in retained["rows"]:
        if row["policy_sha256"] != retained["source_sha256"]["experiments/candidates/uav_fleet_adaptation/b02/controllers.py"]:
            raise AssertionError("retained control policy/source binding changed")
        path = identity(Path(retained["root"]), row["raw"])
        with np.load(path, allow_pickle=False) as archive:
            raw = {key: archive[key] for key in archive.files}
        if check_episode(raw, row, protocol) is not None:
            raise AssertionError("retained control was a training trajectory")
        if paired_resets[row["world"]] != row["initial_state_sha256"]:
            raise AssertionError("new and retained controls use different initial worlds")
        per_row.append(dict(arm=row["arm"], world=row["world"], kind=row["kind"], verified=True,
                            provenance="retained_B02", raw_sha256=row["raw"]["sha256"]))
    x, y = np.concatenate(x_parts), np.concatenate(y_parts)
    total_updates = 0
    for p, phase in enumerate(batch["phases"]):
        n = batch["expected"]["datasets"][p]
        if phase["phase"] != p or phase["examples"] != n or phase["data_sha256"] != array_digest(x[:n], y[:n]):
            raise AssertionError("accumulated actual-history training data changed")
        before, after = assets[("S0", "BC", "D1")[p]], assets[("BC", "D1", "S")[p]]
        if phase["before_sha256"] != before["state_sha256"] or phase["after_sha256"] != after["state_sha256"]:
            raise AssertionError("training lineage was reset/selected/replaced")
        if phase["movement"] != movement(before["state_dict"], after["state_dict"]):
            raise AssertionError("phase parameter movement")
        equal(phase["label_counts"], np.bincount(y[:n], minlength=27), "training label distribution")
        if len(phase["epochs"]) != protocol.epochs[p]:
            raise AssertionError("epoch exposure changed")
        all_order = hashlib.sha256()
        for e, epoch in enumerate(phase["epochs"]):
            order = np.random.default_rng(np.random.SeedSequence([protocol.shuffle_root, p, e])).permutation(n)
            payload = order.astype("<i8", copy=False).tobytes()
            all_order.update(payload)
            if (epoch["epoch"] != e or epoch["shuffle_sha256"] != hashlib.sha256(payload).hexdigest()
                    or epoch["updates"] != n // protocol.batch_size or epoch["sample_presentations"] != n):
                raise AssertionError("shuffle/update/presentation exposure changed")
        updates = n // protocol.batch_size * protocol.epochs[p]
        total_updates += updates
        if (phase["all_shuffle_sha256"] != all_order.hexdigest() or phase["optimizer_steps"] != updates
                or phase["sample_presentations"] != n * protocol.epochs[p]
                or after["optimizer_steps"] != total_updates
                or any(int(v["step"]) != total_updates for v in after["optimizer"]["state"].values())
                or any(step != total_updates for step in phase["adam_step_values"])):
            raise AssertionError("optimizer continuity/exposure mismatch")
    if len(batch["phases"]) != 3 or assets["S0"]["optimizer_steps"] != 0:
        raise AssertionError("wrong number of training phases")
    measured_movement = movement(assets["S0"]["state_dict"], assets["S"]["state_dict"])
    if measured_movement != batch["learner_movement"]:
        raise AssertionError("learner movement changed")
    learning = total_updates > 0 and measured_movement["changed_parameters"] > 0
    if learning != batch["actual_learning"]:
        raise AssertionError("actual learning claim inconsistent")
    if cost_totals(batch["rows"]) != batch["costs"]:
        raise AssertionError("aggregate compute counts changed")
    validate_counts(batch)
    reading = read_comparisons(batch["rows"], batch["retained"], protocol.evaluation_worlds, actual_learning=learning)
    if reading != batch["reading"]:
        raise AssertionError("paired reductions/screens changed")
    return dict(object=batch["object"], status="VERIFIED", launch_sha=batch["launch_sha"],
                summary=file_identity(out / "summary.json"), expected=batch["expected"], actual=batch["actual"],
                raw_files=len(per_row), new_raw_files=len(batch["rows"]), retained_raw_files=len(retained["rows"]),
                new_raw_bytes=sum(r["raw"]["bytes"] for r in batch["rows"]),
                retained_raw_bytes=sum(r["raw"]["bytes"] for r in retained["rows"]),
                native_ticks_verified=batch["actual"]["native_steps"],
                retained_native_ticks_verified=batch["expected"]["retained_native_steps"],
                decisions_verified=len(x) + len(NEW_ARMS) * len(protocol.evaluation_worlds) * protocol.horizon // 4 * 5,
                retained_decisions_verified=len(retained["rows"]) * protocol.horizon // 4 * 5,
                assets=batch["assets"], per_row=per_row, costs=batch["costs"],
                retained_costs=batch["retained"]["costs"], retained_binding=batch["retained"]["binding"], reading=reading,
                reader_calls=dict(native=0, expert_queries=0, radio_power_model=0, actor_forward=0, optimizer=0),
                scope="all new and retained raw hashes with separate exposure/provenance; complete fixed identities/clocks/holds/motion, lawful features/navigation, paid "
                      "labels/rankings, memoization and fresh draws, saved native reductions, checkpoint tensors and "
                      "recorded optimizer/data/shuffle exposure; no replay of host physics, radio model, actor, or optimizer",
                reader_wall_seconds=time.perf_counter() - start_wall, reader_cpu_seconds=time.process_time() - start_cpu,
                reader_max_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[name] = "1"
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    result = read_batch(args.out)
    write_json(args.out / "reading.json", result)
    print(json.dumps({key: result[key] for key in
                      ("status", "new_raw_files", "retained_raw_files", "native_ticks_verified",
                       "retained_native_ticks_verified", "reader_cpu_seconds")}))


if __name__ == "__main__":
    main()
