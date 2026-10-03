"""One full saved-evidence read, with persistent per-fit learning reconstruction."""
from __future__ import annotations

import json
from pathlib import Path
import time
import traceback

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.heuristic import HeuristicParams
from experiments.candidates.energy_relay_benchmark.b01.observation import own_positions

from .budget import check_stop, request_stop
from .contract import clean, equal, identity, telemetry, write_json
from .learner import _digest
from .study import load_checkpoint, stem


def verified_json(out, receipt):
    path = Path(out)/receipt["path"]
    actual = identity(path)
    if any(actual[k] != receipt[k] for k in ("bytes", "sha256")):
        raise AssertionError("row identity mismatch: " + str(path))
    return json.loads(path.read_text())


def verified_raw(out, receipt):
    path = Path(out)/receipt["path"]
    actual = identity(path)
    if any(actual[k] != receipt[k] for k in ("bytes", "sha256")):
        raise AssertionError("raw identity mismatch: " + str(path))
    with np.load(path, allow_pickle=False) as data:
        return {key: data[key] for key in data.files}


def ordinary_command(observation, targets):
    """Read-only arithmetic, no second act, F transition or physical branch."""
    p = HeuristicParams()
    own = own_positions(observation)
    actions = np.zeros((8, 4), dtype=np.float32)
    for member in range(8):
        delta = targets[member]-own[member, :2] if np.isfinite(targets[member]).all() else np.zeros(2)
        velocity = delta/p.time_step_s
        speed = float(np.linalg.norm(velocity))
        if speed > p.cruise_mps:
            velocity = velocity*(p.cruise_mps/speed)
        vertical = float(np.clip((p.height_m-own[member, 2])/p.time_step_s,
                                 -p.vertical_cap_mps, p.vertical_cap_mps))
        actions[member] = np.clip(np.asarray((velocity[0]/p.horizontal_speed_mps,
            velocity[1]/p.horizontal_speed_mps, vertical/p.vertical_speed_mps, 0.)), -1., 1.)
    return actions


def physical_diagnostics(raw):
    length = len(raw["native_reward"])
    alias = np.zeros((length, 8), dtype=bool)
    for tick in range(length):
        ordinary = ordinary_command(raw["observations"][tick], raw["plan_ordinary_targets"][tick//30])
        alias[tick] = np.all(ordinary == raw["proposed"][tick], axis=1)
    feedback_changed = np.any(raw["submitted"] != raw["proposed"], axis=-1)
    displacement = np.diff(raw["truth_uav_xyz"], axis=0)
    # A difference here can be a guard, charging, clipping or motion rounding;
    # retain it descriptively, without claiming a counterfactual consequence.
    requested_velocity = raw["submitted"][:, :, :3].astype(np.float64)*[30., 30., 5.]
    different_motion = np.any(np.abs(displacement-requested_velocity) > 1e-9, axis=-1)
    choice = raw.get("choice_records")
    counts = {} if choice is None else {key: int(np.count_nonzero(choice[key])) for key in (
        "h_eligible", "h_search", "h_selected_base", "selected_pair_alias", "ordinary_target_alias",
        "committed_target_changed")}
    if choice is not None:
        counts.update(requested_C=int(np.count_nonzero(choice["requested_action"] == 0)),
                      requested_H=int(np.count_nonzero(choice["requested_action"] == 1)),
                      forced_C_sparse=int(np.count_nonzero(choice["forced_reason"] == 1)),
                      forced_C_no_BS=int(np.count_nonzero(choice["forced_reason"] == 2)))
    return dict(ordinary_proposal_alias_uav_steps=int(alias.sum()),
                ordinary_proposal_different_uav_steps=int((~alias).sum()),
                all_member_ordinary_proposal_alias_steps=int(np.all(alias, axis=1).sum()),
                feedback_changed_command_uav_steps=int(feedback_changed.sum()),
                native_displacement_differs_from_submitted_velocity_uav_steps=int(different_motion.sum()),
                choices=counts,
                final_native_state={key: clean(raw[key][-1]) for key in (
                    "truth_uav_xyz", "native_battery", "native_charging", "native_failed",
                    "native_station_occupancy", "native_station_queue", "native_waiting",
                    "native_target_station", "native_dock", "native_return_margin")},
                scope="ordinary intent arithmetic on the same saved observation; no counterfactual native J")


def read_episode(out, compact, learner=None):
    from .replay import replay_episode
    out = Path(out)
    check_stop(out)
    row = verified_json(out, compact["row"])
    raw = verified_raw(out, row["raw"])
    result = replay_episode(raw, row, learner=learner, stop_check=lambda: check_stop(out))
    result["physical_diagnostics"] = physical_diagnostics(raw)
    result.update(job_key=row["job_key"], status="completed")
    target = out/"raw"/(stem(row)+".read.json")
    if target.exists():
        raise FileExistsError(target)
    write_json(target, clean(result))
    return dict(job_key=row["job_key"], status="completed",
                evidence=dict(path=str(target.relative_to(out)), **identity(target)),
                policy_counts=result["policy_counts"],
                optimizer_executions=0 if learner is None else len(raw["learn_update_number"]),
                replay_presentations=0 if learner is None else 64*len(raw["learn_update_number"]),
                physical_diagnostics=result["physical_diagnostics"])


def reader_worker(payload):
    spec, out, compact, checkpoint = payload
    wall, cpu = time.perf_counter(), time.process_time()
    try:
        learner = load_checkpoint(out, checkpoint, compact["fit"]) if checkpoint else None
        result = read_episode(out, compact, learner)
    except BaseException as error:
        request_stop(out, "reader failed", job=spec, error=repr(error))
        result = dict(**spec, status="failed", error=repr(error), traceback=traceback.format_exc())
    result.update({"reader_"+key: value for key, value in telemetry(wall, cpu).items()})
    return result


def fit_reader_worker(payload):
    spec, out, ledger = payload
    wall, cpu = time.perf_counter(), time.process_time()
    result = dict(**spec, status="running", episodes=[])
    path = Path(out)/f"fit_{spec['fit']}_read.json"
    learner = None
    try:
        if ledger["status"] != "completed" or len(ledger["episodes"]) != 128:
            raise AssertionError("cannot fill missing training evidence in reader")
        checkpoints = {c["completed_missions"]: c for c in ledger["checkpoints"]}
        if sorted(checkpoints) != list(range(0, 129, 16)):
            raise AssertionError("checkpoint cadence incomplete")
        learner = load_checkpoint(out, checkpoints[0], spec["fit"])
        for index, compact in enumerate(ledger["episodes"]):
            if compact["episode_index"] != index:
                raise AssertionError("training replay order changed")
            result["episodes"].append(read_episode(out, compact, learner))
            if (index+1) % 16 == 0:
                expected = checkpoints[index+1]
                # Verify both the file's own identity and reconstructed complete
                # compact state, including RNG and optimizer, without deploying it.
                load_checkpoint(out, expected, spec["fit"])
                if _digest(learner.state(include_replay=False)) != expected["state_digest"]:
                    raise AssertionError("chronological milestone differs from checkpoint")
            write_json(path, clean(result))
        result.update(status="completed", learner_counts=learner.counts(), learner_digests=learner.digests())
        if learner.digests() != ledger["learner_digests"] or learner.counts() != ledger["learner_counts"]:
            raise AssertionError("full fit replay final identity differs")
    except BaseException as error:
        request_stop(out, "fit reader failed", job=spec, error=repr(error))
        result.update(status="failed", error=repr(error), traceback=traceback.format_exc())
        if learner is not None:
            result.update(learner_counts=learner.counts(), learner_digests=learner.digests())
    result.update({"reader_"+key: value for key, value in telemetry(wall, cpu).items()})
    write_json(path, clean(result))
    return result


def check_exogenous(out, episodes):
    """Same initial state and complete common user-path prefix, never imputed ends."""
    grouped = {}
    for row in episodes:
        grouped.setdefault((row["phase"], row["seed"]), []).append(row)
    pairs = 0
    for _, group in grouped.items():
        if len(group) < 2:
            continue
        first = verified_raw(out, group[0]["raw"])
        for row in group[1:]:
            check_stop(out)
            other = verified_raw(out, row["raw"])
            for key in ("truth_user_xyz", "truth_uav_xyz", "truth_bs_xyz", "truth_station_xyz",
                        "native_battery", "observations"):
                equal(other[key][0], first[key][0], "exogenous initial/"+key)
            prefix = min(len(first["truth_user_xyz"]), len(other["truth_user_xyz"]))
            equal(other["truth_user_xyz"][:prefix], first["truth_user_xyz"][:prefix], "common user path")
            pairs += 1
    return dict(comparisons=pairs, scope="initial legal/native state and full common saved user-path prefix")


def check_audit_pairs(out, rows):
    indexed = {row["arm"]: row for row in rows if row["seed"] == 40039001}
    reports = []
    for canonical, forced in (("C", "forced_C"), ("H_T", "forced_H_T")):
        first, second = (verified_raw(out, indexed[arm]["raw"]) for arm in (canonical, forced))
        keys = [key for key in first if key.startswith(("native_", "truth_"))] + [
            "observations", "proposed", "submitted", "reward", "metrics", "decision_targets_xyz",
            "plan_targets", "plan_ordinary_targets", "plan_clock"]
        for key in keys:
            equal(first[key], second[key], "full forced/canonical audit/"+canonical+"/"+key)
        reports.append(dict(canonical=canonical, forced=forced, fields=keys, identical=True))
    return reports
