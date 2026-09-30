#!/usr/bin/env python3
"""Read every saved B02 trajectory; zero native, expert-radio, or actor-forward calls."""
from __future__ import annotations

import argparse
import hashlib
import json
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
from experiments.candidates.uav_fleet_adaptation.b02.contract import (
    ARMS, FROZEN, PHASES, Protocol, SOURCE_PINS, array_digest, source_identities,
)
from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, WAYPOINTS
from experiments.candidates.uav_fleet_adaptation.b02.model import movement, state_digest
from experiments.candidates.uav_fleet_adaptation.b02.reading import cost_totals, episode_metrics, read_comparisons
from experiments.candidates.uav_fleet_adaptation.b02.study import validate_counts


def equal(actual, expected, label, atol=0):
    a, b = np.asarray(actual), np.asarray(expected)
    if a.shape != b.shape or not np.allclose(a, b, rtol=0, atol=atol, equal_nan=False):
        raise AssertionError(label)


def identity(root, record):
    path = (root / record["path"]).resolve()
    if not path.is_relative_to(root.resolve()):
        raise AssertionError("artifact escapes output directory")
    found = file_identity(path)
    if any(found[k] != record[k] for k in ("sha256", "bytes")):
        raise AssertionError(f"artifact identity mismatch: {record['path']}")
    return path


def own_position(row):
    return row[:3].astype(np.float64) * [1000., 1000., 100.] + [0., 0., 50.]


def saved_ranking_choice(obs, nav_next, fallback, scores, subset):
    if not fallback:
        return int(subset[np.argmax(scores)])
    # Verify recorded fallback command geometry; no radio/power/objective call.
    positions = np.broadcast_to(own_position(obs), (len(subset), 3)).copy()
    for _ in range(4):
        positions = np.clip(positions + COMMANDS[subset] * 30., [0., 0., 50.], [1000., 1000., 150.])
    target = np.r_[WAYPOINTS[nav_next], 50.]
    return int(subset[np.argmin(np.sum((positions - target) ** 2, axis=1))])


def check_memo(raw, row, prefix, mode):
    caches = [{} for _ in range(5)]
    hit_field = prefix + "memo_hit"
    score_field = "expert_scores" if prefix else "policy_scores"
    served_field = "expert_served" if prefix else "policy_served"
    counts = dict(requests=0, hits=0, misses=0, cache_entries=0, cache_key_bytes=0, cache_array_bytes=0)
    if mode in ("C", "C7"):
        counts.update(trajectories=0, model_ticks=0, candidate_links=0, setup_links=0,
                      objective_reductions=0, helper_calls=0, helper_setup_links=0, helper_extreme_links=0)
    else:
        counts.update(helper_calls=0, helper_setup_links=0, helper_extreme_links=0)
    if mode == "student":
        counts.update(neural_rows=0, sampled_draws=0)
    for di, tick in enumerate(raw["decision_ticks"]):
        for agent in range(5):
            obs = raw["observations"][tick, agent]
            nav = int(raw["nav_pre"][di, agent])
            key = obs[:103].tobytes() + bytes([nav])
            hit = key in caches[agent]
            if hit != bool(raw[hit_field][di, agent]):
                raise AssertionError("memo hit/key isolation disagrees with recorded actual history")
            value = [raw["features"][di, agent].tobytes(),
                     int(raw[prefix + "nav_next"][di, agent]), bool(raw[prefix + "fallback"][di, agent])]
            if mode in ("C", "C7"):
                value += [int(raw[prefix + "action_index"][di, agent]),
                          raw[score_field][di, agent].tobytes(), raw[served_field][di, agent].tobytes()]
            elif mode == "student":
                value.append(raw["logits"][di, agent].tobytes())
            if hit and value != caches[agent][key]:
                raise AssertionError("memo value changed for an identical per-agent episode key")
            counts["requests"] += 1
            counts["hits" if hit else "misses"] += 1
            if mode == "student" and row["arm"] == "S_sampled":
                counts["sampled_draws"] += 1
            if hit:
                continue
            caches[agent][key] = value
            n, p = int(raw["n_current"][di, agent]), int(raw["n_peers"][di, agent])
            counts["cache_entries"] += 1
            counts["cache_key_bytes"] += len(key)
            counts["cache_array_bytes"] += {"C": 900, "C7": 580, "student": 564, "features": 456}[mode]
            if mode in ("C", "C7"):
                candidates = 27 if mode == "C" else 7
                counts["trajectories"] += candidates
                counts["model_ticks"] += candidates * 4
                counts["objective_reductions"] += candidates * 4
                counts["candidate_links"] += candidates * 4 * n
                counts["setup_links"] += (1 + p) * n if mode == "C" else 0
            if mode != "C":
                counts["helper_calls"] += 1
                counts["helper_setup_links"] += (1 + p) * n
                counts["helper_extreme_links"] += 2 * n
            if mode == "student":
                counts["neural_rows"] += 1
    return counts


def check_episode(raw, row, protocol):
    h, d = protocol.horizon, protocol.horizon // 4
    shapes = dict(observations=(h, 5, 104), commands=(h, 5, 3), positions=(h + 1, 5, 3),
                  reward=(h,), served=(h,), sinr_quality=(h,), sinr=(h, 5, 50), connections=(h, 5, 50),
                  transmitter_mask=(h, 5), features=(d, 5, 114), terminal_observation=(5, 104),
                  nav_pre=(d, 5), nav_next=(d, 5), fallback=(d, 5), action_index=(d, 5),
                  memo_hit=(d, 5), n_current=(d, 5), n_peers=(d, 5), initial_users=(50, 2))
    for key, shape in shapes.items():
        if raw[key].shape != shape or not np.isfinite(raw[key]).all():
            raise AssertionError(f"invalid finite raw shape for {key}")
    if raw["observations"].dtype != np.float32 or raw["features"].dtype != np.float32:
        raise AssertionError("observation/feature dtype changed")
    equal(raw["decision_ticks"], np.arange(0, h, 4), "decision clock")
    if not raw["transmitter_mask"].all():
        raise AssertionError("not the all-on host")
    served = raw["connections"].sum(axis=(1, 2))
    equal(raw["served"], served, "native service reduction")
    if np.any(raw["connections"].sum(axis=1) > 1) or np.any(raw["connections"].sum(axis=2) > 10):
        raise AssertionError("connection capacity/assignment changed")
    if np.any(raw["sinr"][raw["connections"]] < 3.):
        raise AssertionError("ineligible native connection")
    quality = (np.where(raw["connections"], np.clip((raw["sinr"] - 3.) / 30., 0., 1.), 0.)
               .sum(axis=(1, 2)) / np.maximum(served, 1))
    equal(raw["sinr_quality"], quality, "native quality reduction", 1e-14)
    equal(raw["reward"], .7 * served / 50. + .3 * quality, "native reward reduction", 1e-12)
    equal(raw["positions"][1:], np.clip(raw["positions"][:-1] + raw["commands"].astype(np.float64) * 30.,
                                      [0., 0., 50.], [1000., 1000., 150.]), "executed native motion")
    equal(raw["commands"], np.repeat(COMMANDS[raw["action_index"]], 4, axis=0), "four-tick command/hold")
    obs = raw["observations"][::4]
    equal(raw["features"][..., :103], obs[..., :103], "actual local feature provenance")
    equal(raw["features"][..., 103:113], np.eye(10, dtype=np.float32)[raw["nav_pre"]], "pre-nav features")
    equal(raw["features"][..., -1], raw["fallback"], "fallback feature")
    equal(raw["n_current"], np.count_nonzero(obs[..., 3:63].reshape(d, 5, 20, 3)[..., 2] > 0., axis=-1),
          "visible user count")
    equal(raw["n_peers"], np.count_nonzero(obs[..., 63:103].reshape(d, 5, 10, 4)[..., 3] > 0., axis=-1),
          "visible peer count")
    if np.any(raw["n_peers"] > 4):
        raise AssertionError("nonlocal peer access")
    nav = np.array([np.argmin(np.sum((WAYPOINTS - own_position(r)[:2]) ** 2, axis=1)) for r in obs[0]])
    for di in range(d):
        equal(raw["nav_pre"][di], nav, "navigation continuity")
        own = np.array([own_position(r) for r in obs[di]])
        arrival = np.linalg.norm(WAYPOINTS[nav] - own[:, :2], axis=1) <= 60.
        nav = np.where(raw["fallback"][di] & arrival, (nav + 1) % 10, nav)
        equal(raw["nav_next"][di], nav, "navigation update")
    training = row["kind"] == "training"
    neural = row["arm"] in ("S0", "BC", "S_greedy", "S_sampled", "aggregate1", "aggregate2")
    ordinary = not neural
    if training:
        equal(raw["expert_fallback"], raw["fallback"], "source C/helper fallback disagreement")
        equal(raw["expert_nav_next"], raw["nav_next"], "source C/helper navigation disagreement")
    for prefix, small in ([("expert_", False)] if training else []) + ([("", row["arm"] == "C7_memo")] if ordinary and not training else []):
        scores = raw["expert_scores" if prefix else "policy_scores"]
        services = raw["expert_served" if prefix else "policy_served"]
        subset = np.arange(7 if small else 27)
        if scores.shape != (d, 5, len(subset)) or services.shape != scores.shape:
            raise AssertionError("paid candidate arrays incomplete")
        if not np.isfinite(scores).all() or not np.isfinite(services).all():
            raise AssertionError("nonfinite paid expert labels")
        if not small:
            equal(np.all(services == 0., axis=-1), raw[prefix + "fallback"], "full-support fallback")
        for di in range(d):
            for agent in range(5):
                choice = saved_ranking_choice(obs[di, agent], int(raw[prefix + "nav_next"][di, agent]),
                                              bool(raw[prefix + "fallback"][di, agent]), scores[di, agent], subset)
                if choice != raw[prefix + "action_index"][di, agent]:
                    raise AssertionError("paid score/fallback action mismatch")
    if training and row["phase"] == 0:
        equal(raw["action_index"], raw["expert_action_index"], "expert roll-in action/label split")
    if neural:
        logits = raw["logits"]
        if logits.shape != (d, 5, 27) or logits.dtype != np.float32 or not np.isfinite(logits).all():
            raise AssertionError("incomplete deployed logits")
        probabilities = np.exp(logits.astype(np.float64) - logits.max(axis=-1, keepdims=True))
        probabilities /= probabilities.sum(axis=-1, keepdims=True)
        equal(raw["probabilities"], probabilities, "temperature-one probabilities", 2e-16)
        entropy = -np.sum(np.where(probabilities > 0, probabilities * np.log(np.maximum(probabilities, np.finfo(float).tiny)), 0.), axis=-1)
        equal(raw["entropy"], entropy, "categorical entropy", 2e-14)
        if row["arm"] == "S_sampled":
            for di, tick in enumerate(raw["decision_ticks"]):
                for agent in range(5):
                    u = np.random.default_rng(np.random.SeedSequence(
                        [protocol.sampling_root, row["world"], int(tick), agent])).random()
                    equal(raw["innovation"][di, agent], u, "fresh addressed sample, including cache hit")
                    cdf = np.cumsum(probabilities[di, agent]); cdf[-1] = 1.
                    if raw["action_index"][di, agent] != np.searchsorted(cdf, u, side="right"):
                        raise AssertionError("categorical draw/action mismatch")
        else:
            equal(raw["innovation"], np.full((d, 5), -1.), "greedy arm sampled")
            equal(raw["action_index"], logits.argmax(axis=-1), "greedy logit action")
    checks = []
    if training:
        checks.append((check_memo(raw, row, "expert_", "C"), row["expert_counts"]))
    mode = "student" if neural else ("C7" if row["arm"] == "C7_memo" else "C")
    policy_counts = check_memo(raw, row, "expert_" if training and row["phase"] == 0 else "", mode)
    checks.append((policy_counts, row["policy_counts"]))
    if training and row["phase"] == 0:
        # Source C and the feature-only helper use the same sufficient keys but
        # separate caches. Their hit patterns coincide without shared state.
        checks.append((check_memo(raw, row, "", "features"), row["feature_counts"]))
    for measured, recorded in checks:
        if measured != recorded:
            raise AssertionError(f"recorded compute/cache counts mismatch: {measured} != {recorded}")
    metrics = episode_metrics(raw)
    for key, value in metrics.items():
        equal(row[key], value, f"saved metric {key}", 1e-12)
    equal(row["initial_state_sha256"] == array_digest(raw["positions"][0], raw["initial_users"]), True,
          "initial reset identity")
    cases = ((raw["features"].reshape(-1, 114).copy(), raw["expert_action_index"].reshape(-1).astype(np.int64))
             if training else None)
    if training and array_digest(*cases) != row["label_data_sha256"]:
        raise AssertionError("label data identity mismatch")
    return cases


def read_batch(out, *, permit_fixture=False):
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    out = Path(out).resolve()
    batch = json.loads((out / "summary.json").read_text())
    if batch["status"] != "COMPLETE":
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
        expected_rows += [(arm, world, "evaluation", None) for arm in ARMS[wi % 6:] + ARMS[:wi % 6]]
    found_rows = [(r["arm"], r["world"], r["kind"], r["phase"]) for r in batch["rows"]]
    if found_rows != expected_rows:
        raise AssertionError("phase/world/arm collection order or identity mismatch")
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
                            raw_sha256=row["raw"]["sha256"]))
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
    reading = read_comparisons(batch["rows"], protocol.evaluation_worlds, actual_learning=learning)
    if reading != batch["reading"]:
        raise AssertionError("paired reductions/screens changed")
    return dict(object=batch["object"], status="VERIFIED", launch_sha=batch["launch_sha"],
                summary=file_identity(out / "summary.json"), expected=batch["expected"], actual=batch["actual"],
                raw_files=len(per_row), raw_bytes=sum(r["raw"]["bytes"] for r in batch["rows"]),
                native_ticks_verified=batch["actual"]["native_steps"], decisions_verified=len(x) + len(ARMS) * len(protocol.evaluation_worlds) * protocol.horizon // 4 * 5,
                assets=batch["assets"], per_row=per_row, costs=batch["costs"], reading=reading,
                reader_calls=dict(native=0, expert_queries=0, radio_power_model=0, actor_forward=0, optimizer=0),
                scope="all raw hashes, complete fixed identities/clocks/holds/motion, lawful features/navigation, paid "
                      "labels/rankings, memoization and fresh draws, saved native reductions, checkpoint tensors and "
                      "recorded optimizer/data/shuffle exposure; no replay of host physics, radio model, actor, or optimizer",
                reader_wall_seconds=time.perf_counter() - start_wall, reader_cpu_seconds=time.process_time() - start_cpu,
                reader_max_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    result = read_batch(args.out)
    write_json(args.out / "reading.json", result)
    print(json.dumps({key: result[key] for key in ("status", "raw_files", "native_ticks_verified", "reader_cpu_seconds")}))


if __name__ == "__main__":
    main()
