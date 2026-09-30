#!/usr/bin/env python3
"""Independently reconstruct B04 saved outcomes/decoding without native/radio calls."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import resource
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import torch

from experiments.candidates.uav_local_history.b01.study import file_identity, write_json
from experiments.candidates.uav_fleet_adaptation.b02.contract import array_digest
from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, WAYPOINTS
from experiments.candidates.uav_fleet_adaptation.b02.read import check_memo, saved_ranking_choice
from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest
from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.contract import (
    ASSET, ASSET_PATH, FROZEN, OBJECT, Protocol, SOURCE_PINS, source_identities, validate_counts,
)
from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.reading import (
    cost_totals, episode_metrics, read_comparisons,
)
from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.study import load_asset

M = 1 << 53


def require(condition, label):
    if not condition:
        raise AssertionError(label)


def equal(actual, expected, label, atol=0.):
    a, b = np.asarray(actual), np.asarray(expected)
    require(a.shape == b.shape, label + " shape")
    if atol == 0:
        require(np.array_equal(a, b), label)
    else:
        require(np.allclose(a, b, rtol=0., atol=atol), label)


def own_position(row):
    return row[:3].astype(np.float64) * [1000., 1000., 100.] + [0., 0., 50.]


def regenerate_bundle(protocol, world, tape):
    """Separate reader address reconstruction; never calls candidate sampling code."""
    n = protocol.horizon // 4
    def stream(root, agent=None):
        address = [root, world, tape] + ([] if agent is None else [agent])
        return np.random.Generator(np.random.PCG64(np.random.SeedSequence(address))).integers(
            0, M, size=n, dtype=np.uint64)
    return {"public": stream(protocol.public_root),
            "private_depart": np.column_stack([stream(protocol.departure_root, i) for i in range(5)]),
            "private_tail": np.column_stack([stream(protocol.tail_root, i) for i in range(5)])}


def expected_pairs(thresholds):
    """Integrate the count over all integer-interval breakpoints, independently."""
    b = [int(x) for x in thresholds]
    intervals, breaks = [], {0, M}
    for i, length in enumerate(b):
        start = (-(i * M // 5)) % M
        pieces = []
        if length:
            if start + length <= M:
                pieces = [(start, start + length)]
            else:
                pieces = [(start, M), (0, start + length - M)]
        intervals.append(pieces)
        for lo, hi in pieces:
            breaks.update((lo, hi))
    bounds = sorted(breaks)
    numerator = 0
    for lo, hi in zip(bounds, bounds[1:]):
        active = sum(any(left <= lo < right for left, right in pieces) for pieces in intervals)
        numerator += (hi - lo) * active * (active - 1) // 2
    return np.array([sum(b) / M,
                     sum(b[i] * b[j] for i in range(5) for j in range(i + 1, 5)) / (M * M),
                     numerator / M,
                     sum(min(b[i], b[j]) for i in range(5) for j in range(i + 1, 5)) / M])


def check_episode(raw, row, protocol, actor, bundle, calls):
    h, d = protocol.horizon, protocol.horizon // 4
    stochastic, student = row["arm"] != "C", row["arm"].startswith("S_")
    shapes = dict(observations=(h, 5, 104), commands=(h, 5, 3), positions=(h + 1, 5, 3),
                  reward=(h,), served=(h,), sinr_quality=(h,), sinr=(h, 5, 50), connections=(h, 5, 50),
                  transmitter_mask=(h, 5), features=(d, 5, 114), terminal_observation=(5, 104),
                  nav_pre=(d, 5), nav_next=(d, 5), fallback=(d, 5), action_index=(d, 5),
                  modal_index=(d, 5), memo_hit=(d, 5), n_current=(d, 5), n_peers=(d, 5),
                  initial_users=(50, 2), probabilities=(d, 5, 27))
    if student:
        shapes["logits"] = (d, 5, 27)
    else:
        shapes.update(policy_scores=(d, 5, 27), policy_served=(d, 5, 27))
    if stochastic:
        shapes.update(departure_threshold=(d, 5), tail_thresholds=(d, 5, 26),
                      effective_probabilities=(d, 5, 27), departure_integer=(d, 5),
                      requested_departure=(d, 5), public_integer=(d,),
                      private_depart_integer=(d, 5), private_tail_integer=(d, 5))
    require(set(raw) == set(shapes) | {"decision_ticks"}, "raw schema mismatch")
    for key, shape in shapes.items():
        require(raw[key].shape == shape and np.isfinite(raw[key]).all(), f"invalid finite {key}")
    for key in ("observations", "features", "commands", "terminal_observation"):
        require(raw[key].dtype == np.float32, f"{key} dtype")
    for key in ("action_index", "modal_index", "nav_pre", "nav_next"):
        require(np.issubdtype(raw[key].dtype, np.integer), f"{key} integer labels")
    require(np.all((raw["action_index"] >= 0) & (raw["action_index"] < 27)), "invalid action category")
    require(np.all((raw["nav_pre"] >= 0) & (raw["nav_pre"] < 10)), "invalid navigation category")
    equal(raw["decision_ticks"], np.arange(0, h, 4), "decision clock")
    require(raw["connections"].dtype == bool and raw["transmitter_mask"].dtype == bool
            and raw["fallback"].dtype == bool and raw["memo_hit"].dtype == bool, "boolean contract")
    require(raw["transmitter_mask"].all(), "all-on host")
    served = raw["connections"].sum(axis=(1, 2))
    equal(raw["served"], served, "native service")
    require(not np.any(raw["connections"].sum(axis=1) > 1)
            and not np.any(raw["connections"].sum(axis=2) > 10), "native connection capacity")
    require(np.all(raw["sinr"][raw["connections"]] >= 3.), "ineligible connection")
    quality = np.where(raw["connections"], np.clip((raw["sinr"] - 3.) / 30., 0., 1.), 0.).sum(axis=(1, 2)) / np.maximum(served, 1)
    equal(raw["sinr_quality"], quality, "native quality", 1e-14)
    equal(raw["reward"], .7 * served / 50. + .3 * quality, "native reward", 1e-12)
    calls["actual_motion_agent_ticks"] += h * 5
    equal(raw["positions"][1:], np.clip(raw["positions"][:-1] + raw["commands"].astype(np.float64) * 30.,
                                      [0., 0., 50.], [1000., 1000., 150.]), "native motion")
    scale = np.array([1000., 1000., 100.])
    offset = np.array([0., 0., 50.])
    # The saved sensor is FP32 on the bounded [0,1] normalized coordinates.
    # One normalized FP32 epsilon covers quantization, not physical drift.
    tolerance = np.finfo(np.float32).eps * scale
    require(np.allclose(raw["observations"][..., :3].astype(np.float64) * scale + offset,
                        raw["positions"][:-1], rtol=0., atol=tolerance), "observed own position")
    require(np.allclose(raw["terminal_observation"][..., :3].astype(np.float64) * scale + offset,
                        raw["positions"][-1], rtol=0., atol=tolerance), "terminal own position")
    equal(raw["commands"], np.repeat(COMMANDS[raw["action_index"]], 4, axis=0), "four-tick commitment")
    obs = raw["observations"][::4]
    equal(raw["features"][..., :103], obs[..., :103], "local features")
    equal(raw["features"][..., 103:113], np.eye(10, dtype=np.float32)[raw["nav_pre"]], "navigation features")
    equal(raw["features"][..., -1], raw["fallback"], "fallback feature")
    equal(raw["n_current"], np.count_nonzero(obs[..., 3:63].reshape(d, 5, 20, 3)[..., 2] > 0., axis=-1), "local users")
    equal(raw["n_peers"], np.count_nonzero(obs[..., 63:103].reshape(d, 5, 10, 4)[..., 3] > 0., axis=-1), "local peers")
    require(not np.any(raw["n_peers"] > 4), "peer contract")
    nav = np.array([np.argmin(np.sum((WAYPOINTS - own_position(r)[:2]) ** 2, axis=1)) for r in obs[0]])
    for j in range(d):
        equal(raw["nav_pre"][j], nav, "navigation continuity")
        own = np.array([own_position(r) for r in obs[j]])
        nav = np.where(raw["fallback"][j] & (np.linalg.norm(WAYPOINTS[nav] - own[:, :2], axis=1) <= 60.), (nav + 1) % 10, nav)
        equal(raw["nav_next"][j], nav, "navigation transition")
    # Project the selected action onto its source base before using the pinned memo auditor.
    base_raw = {**raw, "action_index": raw["modal_index"]}
    expected_costs = check_memo(base_raw, {**row, "arm": "S_greedy" if student else "C_memo"}, "", "student" if student else "C")
    require(row["policy_counts"] == expected_costs, "reconstructed controller cost/cache mismatch")
    if not student:
        equal(np.all(raw["policy_served"] == 0., axis=-1), raw["fallback"], "paid C fallback")
    if stochastic:
        for key in ("departure_threshold", "tail_thresholds", "departure_integer"):
            require(raw[key].dtype == np.uint64, f"{key} integer dtype")
        require(raw["requested_departure"].dtype == bool, "departure boolean dtype")
        require(raw["effective_probabilities"].dtype == np.float64, "effective probability dtype")
        for key, stored in (("public", "public_integer"), ("private_depart", "private_depart_integer"),
                            ("private_tail", "private_tail_integer")):
            require(raw[stored].dtype == np.uint64, f"{stored} integer dtype")
            equal(raw[stored], bundle[key], "fresh addressed " + key)
        require(row["bundle_sha256"] == array_digest(bundle["public"], bundle["private_depart"], bundle["private_tail"]), "tape digest")
    diagnostics = np.zeros((d, 4), dtype=np.float64)
    require(raw["probabilities"].dtype == np.float64, "base probability dtype")
    requested = raw["action_index"] != raw["modal_index"]
    physical = np.zeros((d, 5), dtype=bool)
    for j in range(d):
        for agent in range(5):
            if student:
                require(raw["logits"].dtype == np.float32, "logit dtype")
                calls["S_forward_rows"] += 1
                with torch.inference_mode():
                    logits = actor(torch.from_numpy(raw["features"][j, agent].copy()).reshape(1, 114))[0].numpy()
                equal(raw["logits"][j, agent], logits, "frozen S one-row forward")
                p = np.exp(logits.astype(np.float64) - float(np.max(logits)))
                p /= p.sum(dtype=np.float64)
            else:
                modal = int(raw["modal_index"][j, agent])
                if not raw["memo_hit"][j, agent]:
                    fallback = bool(raw["fallback"][j, agent])
                    if fallback:
                        calls["C_fallback_candidate_motion_steps"] += 27 * 4
                    choice = saved_ranking_choice(obs[j, agent], int(raw["nav_next"][j, agent]), fallback,
                                                  raw["policy_scores"][j, agent], np.arange(27))
                    require(choice == modal, "paid C score/fallback choice")
                p = np.full(27, .1 / 26 if stochastic else 0., dtype=np.float64)
                p[modal] = .9 if stochastic else 1.
            equal(raw["probabilities"][j, agent], p, "base probability law")
            modal = int(np.argmax(p))
            require(raw["modal_index"][j, agent] == modal, "modal tie/order")
            if not stochastic:
                require(raw["action_index"][j, agent] == modal, "deterministic C action")
                continue
            b = math.ceil((1. - float(p[modal])) * M)
            ids = [a for a in range(27) if a != modal]
            if b:
                tail = p[ids] / p[ids].sum(dtype=np.float64)
                cdf = np.cumsum(tail, dtype=np.float64)
                require(np.all(cdf <= 1. + 64 * np.finfo(float).eps), "tail CDF roundoff bound")
                thresholds = [math.ceil(min(1., max(0., float(v))) * M) for v in cdf]
                thresholds[-1] = M
            else:
                thresholds = [0] * 25 + [M]
            require(int(raw["departure_threshold"][j, agent]) == b, "departure threshold")
            equal(raw["tail_thresholds"][j, agent], np.array(thresholds, dtype=np.uint64), "tail integer partition")
            effective = np.zeros(27)
            effective[modal] = 1. - b / M
            previous = 0
            for a, boundary in zip(ids, thresholds):
                effective[a] = (b / M) * ((boundary - previous) / M)
                previous = boundary
            equal(raw["effective_probabilities"][j, agent], effective, "implemented finite marginal")
            public = int(bundle["public"][j])
            integer = (int(bundle["private_depart"][j, agent]) if row["arm"][-1] == "I"
                       else (public + agent * M // 5) % M if row["arm"][-1] == "A" else public)
            require(int(raw["departure_integer"][j, agent]) == integer, "coupled departure integer")
            depart = integer < b
            require(bool(raw["requested_departure"][j, agent]) == depart, "departure event")
            tail_integer = int(bundle["private_tail"][j, agent])
            selected = next(a for a, boundary in zip(ids, thresholds) if tail_integer < boundary) if depart else modal
            require(raw["action_index"][j, agent] == selected, "finite decoder action")
        if stochastic:
            diagnostics[j] = expected_pairs(raw["departure_threshold"][j])
            position = raw["positions"][j * 4].copy()
            for offset in range(4):
                position = np.clip(position + COMMANDS[raw["modal_index"][j]].astype(np.float64) * 30.,
                                   [0., 0., 50.], [1000., 1000., 150.])
                physical[j] |= np.any(position != raw["positions"][j * 4 + offset + 1], axis=-1)
                calls["modal_alias_motion_steps"] += 5
            require(np.all(~physical[j] | requested[j]), "physical departure without categorical departure")
    for key, value in episode_metrics(raw).items():
        equal(row[key], value, "saved episode metric " + key, 1e-12)
    equal(row["initial_state_sha256"], array_digest(raw["positions"][0], raw["initial_users"]), "initial state digest")
    count = requested.sum(axis=1)
    audit = dict(arm=row["arm"], world=row["world"], tape=row["tape"],
                categorical_departures=int(requested.sum()), physical_departures=int(physical.sum()),
                aliased_departures=int(np.count_nonzero(requested & ~physical)),
                categorical_count_histogram=np.bincount(count, minlength=6).tolist(),
                physical_count_histogram=np.bincount(physical.sum(axis=1), minlength=6).tolist(),
                realized_departing_pairs_mean=float(np.mean(count * (count - 1) / 2)),
                expected_joint_means=dict(zip(("departures", "pairs_I", "pairs_A", "pairs_B"), diagnostics.mean(axis=0).tolist())))
    joint = dict(expected_joint=diagnostics, requested_departure=requested,
                 physical_departure=physical) if stochastic else None
    return audit, joint


def read_batch(out, *, permit_fixture=False):
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    out = Path(out).resolve()
    progress_path = out / "reader-progress.json"
    if not permit_fixture and (progress_path.exists() or (out / "reading.json").exists()):
        raise FileExistsError("reader already attempted; reconcile paid replay rather than repeat")
    calls = dict(environment_steps=0, radio_calls=0, teacher_queries=0, optimizer_steps=0,
                 S_forward_rows=0, actual_motion_agent_ticks=0, modal_alias_motion_steps=0,
                 C_fallback_candidate_motion_steps=0, regenerated_tape_integers=0)
    progress = dict(object=OBJECT, status="READING", completed_rows=0, current_row=None,
                    reader_calls=calls)

    def publish():
        progress.update(reader_wall_seconds=time.perf_counter() - start_wall,
                        reader_cpu_seconds=time.process_time() - start_cpu)
        write_json(progress_path, progress)

    publish()
    try:
        result = _read_batch(out, permit_fixture=permit_fixture, calls=calls, progress=progress,
                             publish=publish, start_wall=start_wall, start_cpu=start_cpu)
        progress["status"] = "VERIFIED"
        publish()
        return result
    except Exception:
        progress.update(status="FAILED", error=traceback.format_exc())
        publish()
        raise


def _read_batch(out, *, permit_fixture, calls, progress, publish, start_wall, start_cpu):
    summary = json.loads((out / "summary.json").read_text())
    config = json.loads((out / "config.json").read_text())
    require(summary["object"] == OBJECT and summary["status"] == "COMPLETE", "incomplete/wrong scientific object")
    pd = summary["protocol"].copy()
    pd["worlds"], pd["tapes"] = tuple(pd["worlds"]), tuple(pd["tapes"])
    protocol = Protocol(**pd).validate()
    scientific = summary["scientific_invocation"]
    if not scientific and not permit_fixture:
        raise ValueError("only fixed scientific data may be read without fixture permission")
    require(not scientific or (protocol == FROZEN and summary["asset"]["path"] == str(ASSET_PATH)), "production protocol/asset path")
    for key in config:
        require(config[key] == summary[key], "config/summary " + key)
    require(summary["expected"] == protocol.expected(), "expected exposure tampering")
    require(summary["source_sha256"] == source_identities(ROOT), "source bindings differ")
    require([(r["arm"], r["world"], r["tape"]) for r in summary["rows"]] == list(protocol.schedule()), "ordered complete schedule")
    actor, asset = load_asset(summary["asset"]["path"], ASSET if scientific else summary["asset"])
    require(asset == summary["asset"], "asset record changed")
    require(summary["asset_after_state_sha256"] == asset["state_sha256"], "worker changed frozen asset")
    bundles = {(w, t): regenerate_bundle(protocol, w, t) for w in protocol.worlds for t in protocol.tapes}
    calls["regenerated_tape_integers"] = sum(a.size for b in bundles.values() for a in b.values())
    audits, starts, joints, joint_index = [], {}, [], []
    for row in summary["rows"]:
        progress["current_row"] = {k: row[k] for k in ("arm", "world", "tape")}
        path = (out / row["raw"]["path"]).resolve()
        require(path.is_relative_to(out / "raw"), "raw path escape")
        identity = file_identity(path)
        require(all(identity[k] == row["raw"][k] for k in ("bytes", "sha256")), "raw file identity mismatch")
        expected_sha = (asset["state_sha256"] if row["arm"].startswith("S_")
                        else SOURCE_PINS["experiments/candidates/uav_local_history/b01/controller.py"])
        require(row["policy_sha256"] == expected_sha, "wrong frozen behavior asset")
        with np.load(path, allow_pickle=False) as z:
            raw = {k: z[k] for k in z.files}
        audit, joint = check_episode(raw, row, protocol, actor, bundles.get((row["world"], row["tape"])), calls)
        if joint is not None:
            audit["joint_array_index"] = len(joints)
            joint_index.append(progress["current_row"])
            joints.append(joint)
        audits.append(audit)
        before = starts.setdefault(row["world"], row["initial_state_sha256"])
        require(before == row["initial_state_sha256"], "matched world reset differs")
        progress["completed_rows"] += 1
        publish()
    require(state_digest(actor.state_dict()) == asset["state_sha256"], "reader changed fixed S")
    require(summary["costs"] == cost_totals(summary["rows"]), "worker cost aggregation")
    validate_counts(summary)
    comparisons = read_comparisons(summary["rows"], protocol)
    require(comparisons == summary["comparisons"], "comparison/primary arithmetic")
    expected = protocol.expected()
    require(calls["S_forward_rows"] == expected["s_forward_rows_ceiling"], "reader S row scope")
    require(calls["actual_motion_agent_ticks"] == expected["reader_motion_agent_ticks"], "reader motion scope")
    require(calls["modal_alias_motion_steps"] == expected["reader_modal_motion_ceiling"], "reader modal alias scope")
    require(calls["C_fallback_candidate_motion_steps"] <= expected["c_model_ticks_ceiling"], "reader fallback geometry scope")
    audit_path = out / "audit" / "joint_sampling.npz"
    audit_path.parent.mkdir(exist_ok=True)
    np.savez_compressed(audit_path, **{key: np.stack([j[key] for j in joints]) for key in joints[0]})
    joint_record = dict(file_identity(audit_path), path=str(audit_path.relative_to(out)),
                        index=joint_index, decision_ticks=list(range(0, protocol.horizon, 4)),
                        expected_joint_columns=["departures", "pairs_I", "pairs_A", "pairs_B"],
                        scope="Each stochastic episode retains every joint-decision conditional expectation and "
                              "each agent's requested and physically distinct departure; radio counterfactuals excluded.")
    reading = dict(object=OBJECT, status="VERIFIED", launch_sha=summary["launch_sha"],
                   scientific_invocation=scientific, protocol=protocol.to_dict(),
                   inputs={"summary": file_identity(out / "summary.json"), "config": file_identity(out / "config.json")},
                   source_sha256=summary["source_sha256"], asset=asset, raw_files=len(audits),
                   native_steps_verified=summary["actual"]["native_steps"], reader_calls=calls,
                   audits=audits, joint_diagnostics=joint_record, comparisons=comparisons,
                   reader_wall_seconds=time.perf_counter() - start_wall,
                   reader_cpu_seconds=time.process_time() - start_cpu,
                   process_lifetime_peak_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
                   scope="Saved-data reconstruction plus paid frozen-S row replay; no new environment, radio, teacher "
                         "or optimizer call. Fallback flags/navigation are source-bound, not independent helper-radio replay. "
                         "RSS is this process's lifetime peak, not incremental reader memory. Reader timing excludes final self-report write.")
    write_json(out / "reading.json", reading)
    return reading


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    return read_batch(args.out)


if __name__ == "__main__":
    main()
