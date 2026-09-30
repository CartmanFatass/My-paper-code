#!/usr/bin/env python3
"""Pure reading of the three ordinary continuations and all fresh endpoint worlds."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import resource
import statistics
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.uav_parent_adaptation import read_b01 as old
from experiments.candidates.uav_parent_adaptation.b02.assets import load_assets
from experiments.candidates.uav_parent_adaptation.b02.protocol import (
    HORIZON, TRAIN, EVAL, LINEAGES, PROGRAMS, PARENT_SOURCE, PARENT_SUMMARY_SHA256, PARENT_ROOT,
    WITNESS_FIELDS, masters, addresses, rng_table, rotating_order,
    expected_training_counts, expected_evaluation_counts,
)

METRICS, HIGHER, LOWER = old.METRICS, old.HIGHER, old.LOWER
load_json, digest, close, interval = old.load_json, old.digest, old.close, old.interval


def check_sigma(log_std, recorded):
    """Exact collector FP32 law plus independently evaluated FP64 scale check."""
    import torch
    value = np.asarray(log_std, dtype=np.float32)
    assert value.shape == (3,) and np.isfinite(value).all()
    exact = torch.from_numpy(value.copy()).clamp(-5, 2).exp().numpy()
    np.testing.assert_array_equal(recorded, exact)
    reference = np.exp(np.clip(value.astype(np.float64), -5, 2))
    np.testing.assert_allclose(recorded, reference, rtol=2 * np.finfo(np.float32).eps, atol=0)


def groups(arrays):
    actor, critic = arrays["actor"], arrays["critic"]
    def flatten(values):
        return np.concatenate([value.ravel() for value in values])
    return dict(actor_encoder=flatten([v for k, v in actor.items() if k.startswith("encoder.")]),
                actor_recurrent=flatten([v for k, v in actor.items() if k.startswith("gru.")]),
                actor_mean=flatten([v for k, v in actor.items() if k.startswith("mean.")]),
                actor_log_std=actor["log_std"].ravel(), critic=flatten(critic.values()))


def read_u_checkpoint(binding, *, lineage, endpoint, launch_sha):
    from experiments.candidates.uav_parent_adaptation.b02.model import read_checkpoint
    state = read_checkpoint(Path(binding["path"]).read_bytes(), binding, lineage=lineage,
                            endpoint=endpoint, launch_sha=launch_sha)
    return {group: {key: tensor.detach().numpy() for key, tensor in state[group].items()}
            for group in ("actor", "critic")}


def read_fit(cell, parent_binding, expected_witnesses):
    lineage, source = cell["lineage"], cell["launch_sha"]
    assert cell["stage"] == "U" and cell["master"] == masters(lineage)["U"]
    assert cell["parent_source"] == PARENT_SOURCE and cell["parent"] == parent_binding
    parent = old.read_bound_checkpoint(parent_binding, lineage=lineage, stage="B",
                                       endpoint="final", launch_sha=PARENT_SOURCE)
    arrays, grouped = {}, {}
    for endpoint in ("initial", "final"):
        binding = cell[f"{endpoint}_checkpoint"]
        assert binding["parent"] == parent_binding
        arrays[endpoint] = read_u_checkpoint(binding, lineage=lineage, endpoint=endpoint, launch_sha=source)
        grouped[endpoint] = groups(arrays[endpoint])
        hashes = {key: hashlib.sha256(value.tobytes()).hexdigest() for key, value in grouped[endpoint].items()}
        assert hashes == cell[f"{endpoint}_tensor_sha256"]
        np.testing.assert_array_equal(arrays[endpoint]["actor"]["log_std"], cell[f"{endpoint}_log_std"])
        check_sigma(arrays[endpoint]["actor"]["log_std"], cell[f"{endpoint}_sigma"])
    for group in parent:
        for key, value in parent[group].items():
            np.testing.assert_array_equal(arrays["initial"][group][key], value)
    for key, before in grouped["initial"].items():
        after, reported = grouped["final"][key], cell["exposure"][key]
        assert reported["parameters"] == before.size
        close(reported["initial_norm"], np.linalg.norm(before), 2e-4)
        close(reported["displacement"], np.linalg.norm(after - before), 2e-4)
    assert cell["actor_trainable_parameters"] == sum(value.size for value in parent["actor"].values()) == 39942
    assert cell["critic_trainable_parameters"] == sum(value.size for value in parent["critic"].values()) == 74497
    assert cell["matched_training_episodes"] == cell["configuration"]["train"]
    rows = read_episodes(cell, "train")
    assert [tuple(row[k] for k in WITNESS_FIELDS) for row in rows] == expected_witnesses
    # U uses exactly the original parent joint update law; reuse its numerical reader.
    updates = old.read_updates(dict(cell, stage="B"))
    assert cell["optimizer_law"] == "joint_actor_critic_global_clip"
    return dict(arrays=arrays["final"], initial=arrays["initial"], rows=rows, updates=updates,
                reading=dict(initial_exact_parent=True, parent_source=PARENT_SOURCE,
                             initial_and_final_tensor_identity=True, all_parameter_groups_trainable=True,
                             parameter_counts={k: v.size for k, v in grouped["final"].items()},
                             sigma_initial=cell["initial_sigma"], sigma_final=cell["final_sigma"],
                             matched_training_episodes=len(rows)))


def read_episodes(cell, phase):
    import torch
    path = Path(cell["directory"]) / "episodes.jsonl"
    assert digest(path) == cell["episode_stream_sha256"]
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    lineage, training = cell["lineage"], phase == "train"
    count = cell["configuration"]["train" if training else "evaluation"]
    addr = addresses(lineage, "U" if training else "evaluation",
                     train=count if training else TRAIN, evaluation=count if not training else EVAL)
    assert cell["addresses"] == addr and len(rows) == count
    rng = torch.Generator().manual_seed(addr["motion"]) if training else None
    for e, row in enumerate(rows):
        assert row["lineage"] == lineage and row["episode"] == e and row["phase"] == phase
        assert row["arm"] == ("U" if training else cell["program"])
        assert row["reset_seed"] == addr["scene_start"] + e and row["channel_seed"] == addr["channel_start"] + e
        assert row["motion_seed"] == (addr["motion"] if training else addr["motion_start"] + e)
        assert row["steps"] == cell["configuration"]["horizon"] and row["packet_bytes"] == 40
        close(row["J_physical"], .014 * row["served_users_per_tick"] + .3 * row["Q"], 1e-10)
        close(row["J_net"], row["J_physical"] - .001, 1e-10)
        close(row["charge_per_tick"], .001, 1e-14)
        assert row["delivered_packets"] + row["pending_at_end"] == row["steps"]
        if training:
            old.verify_innovations(row, rng)
            check_sigma(row["log_std"], row["sigma"])
    assert cell["counts"]["delivered_packets"] == sum(row["delivered_packets"] for row in rows)
    assert cell["counts"]["censored_packets"] == sum(row["pending_at_end"] for row in rows)
    if not training:
        assert rows == cell["rows"]
    return rows


def read_trace(row, program, calibration_b=None, expected_log_std=None):
    assert program in PROGRAMS
    checked = old.read_trace(row, "P" if program == "U" else program, calibration_b, expected_log_std)
    checked["mean_field_semantics"] = ("U own learned mean; base_mean is not a parent shadow" if program == "U"
                                        else "retained plain parent or composed correction")
    with np.load(row["raw"], allow_pickle=False) as raw:
        checked["motion_distribution"] = dict(
            sigma=np.exp(np.clip(raw["log_std"], -5, 2)).tolist(),
            mean=raw["composed_mean"].astype(np.float64).mean((0, 1)).tolist(),
            mean_std=raw["composed_mean"].astype(np.float64).std((0, 1)).tolist(),
            sampled_action_mean=raw["action"].astype(np.float64).mean((0, 1)).tolist(),
            sampled_action_rms=np.sqrt(np.square(raw["action"].astype(np.float64)).mean((0, 1))).tolist())
    return checked


def contrast(panels, left, right, metric):
    vectors = np.asarray([[a[metric] - b[metric] for a, b in zip(panels[l][left], panels[l][right])]
                          for l in LINEAGES])
    assert vectors.shape == (3, 32) and np.isfinite(vectors).all()
    means = vectors.mean(1)
    estimate = float(means.mean())
    variance = float(vectors.var(axis=1, ddof=1).sum() / (9 * 32))
    se = math.sqrt(variance)
    outer = interval(means, 2)
    outer["scope"] = ("descriptive independent-block approximation under reused parent/K/D assets and "
                       "result-selected U question; not new parent-generation replication or confirmation")
    utility = "higher" if metric in HIGHER else ("lower" if metric in LOWER else "descriptive_only")
    adverse = vectors < 0 if metric in HIGHER else vectors > 0 if metric in LOWER else None
    low = np.unravel_index(vectors.argmin(), vectors.shape)
    high = np.unravel_index(vectors.argmax(), vectors.shape)
    return dict(mean=estimate, per_lineage_mean=means.tolist(), descriptive_lineage_interval=outer,
                conditional_deployment=dict(variance=variance, standard_error=se,
                    normal_approximation95=[estimate - 1.96 * se, estimate + 1.96 * se],
                    scope="fixed endpoints; 3 independent 32-world panels; excludes all retraining/parent uncertainty",
                    variance_formula="sum_r(sample_variance_r / 32) / 9"),
                fixed_endpoint_world_intervals={str(l): interval(v, 31) for l, v in zip(LINEAGES, vectors)},
                per_world_differences={str(l): v.tolist() for l, v in zip(LINEAGES, vectors)},
                utility_direction=utility,
                negative_worlds={str(l): np.flatnonzero(v < 0).tolist() for l, v in zip(LINEAGES, vectors)},
                positive_worlds={str(l): np.flatnonzero(v > 0).tolist() for l, v in zip(LINEAGES, vectors)},
                adverse_worlds={str(l): np.flatnonzero(v).tolist() for l, v in zip(LINEAGES, adverse)}
                if adverse is not None else None,
                minimum=float(vectors.min()), maximum=float(vectors.max()),
                minimum_at=[int(LINEAGES[low[0]]), int(low[1])],
                maximum_at=[int(LINEAGES[high[0]]), int(high[1])])


def read_run(root):
    root = Path(root)
    summary, config = load_json(root / "summary.json"), load_json(root / "config.json")
    manifest, exit_record = load_json(root / "launch-manifest.json"), load_json(root / "process-exit.json")
    assert summary["object"] == "UAV-PARENT-ADAPTATION-B02" and summary["status"] == "COMPLETE"
    assert not summary["limits"] and summary["scientific_invocation"] is True and exit_record["exit_code"] == 0
    assert summary["source_sha"] == config["source_sha"] == manifest["sha"]
    assert manifest["direction"] == "uav_parent_adaptation" and manifest["lead"] == "Codex DM (native child)"
    assert manifest["node"] == "wsl_4070"
    assert (config["horizon"], config["train"], config["evaluation"]) == (HORIZON, TRAIN, EVAL)
    assert config["rng"] == rng_table() and not config["checkpoint_selection"] and not config["parent_quality_selection"]
    assert config["parent_root"] == PARENT_ROOT and config["parent_summary_sha256"] == PARENT_SUMMARY_SHA256
    assert config["device"] == "cpu" and config["dtype"] == "float32" and config["packet_bytes"] == 40
    assert config["runtime"]["torch_threads"] == 1 and config["parent_source"] == PARENT_SOURCE
    assert config["new_fits"] == 3 and config["retained_adaptation_refits"] == config["parent_generation_fits"] == 0
    assert digest(root / "config.json") == summary["config_sha256"]
    assets = load_assets(PARENT_ROOT)
    assert summary["retained_inputs"] == assets["identity"]
    fits, evaluations = summary["fits"], summary["evaluations"]
    assert [(c["lineage"], c["stage"]) for c in fits] == [(l, "U") for l in LINEAGES]
    assert [(c["lineage"], c["program"]) for c in evaluations] == [(l, p) for l in LINEAGES for p in PROGRAMS]
    assert summary["evaluation_order"] == [dict(lineage=l, world=e, rank=r, program=p)
        for l in LINEAGES for e in range(EVAL) for r, p in enumerate(rotating_order(e))]
    reading = dict(object="UAV-PARENT-ADAPTATION-B02-READING", all_checks_passed=False,
        source_sha=summary["source_sha"], summary_sha256=digest(root / "summary.json"), reader_sha256=digest(__file__),
        retained_inputs=assets["identity"], actual=summary["actual"], native_steps_added=0,
        optimizer_calls_added=0, model_or_policy_calls_added=0, checkpoints={}, updates={}, curves={},
        exposure={}, levels={}, raw_checks={}, corrections={}, motion_distribution={}, contrasts={},
        resources=summary["resources"], fit_resources={}, evaluation_timing={},
        limitations=[
            "Exploratory fixed-asset comparison selected after B01; K/D and all parents are reused.",
            "Conditional deployment SE excludes all new parent generation or U/K/D retraining uncertainty.",
            "Three lineage means remain heterogeneous; any outer df2 interval is descriptive, not confirmation.",
            "96 worlds do not create 96 training seeds; historical B06 is not another independent root.",
            "U differs in parameterization, trainable variance and joint optimization, not only freezing.",
            "U can express K's constant bias; no containment of D's residual architecture is assumed.",
            "No old-I versus new-U subtraction; this batch does not measure recovery from initial C generation.",
            "Path/boundary/height and abstract40-byte channel are not physical flight, energy or bandwidth evidence.",
            "One motion stream per scene/channel tuple does not identify within-scene policy risk.",
        ])
    data = {l: {} for l in LINEAGES}
    for cell in fits:
        lineage, label = cell["lineage"], f"{cell['lineage']}/U"
        assert cell["status"] == "COMPLETE" and not cell["limits"] and cell["scientific_invocation"] is True
        assert cell["launch_sha"] == summary["source_sha"]
        assert cell == load_json(Path(cell["directory"]) / "summary.json")
        for key, value in expected_training_counts().items():
            assert cell["counts"][key] == value, (label, key)
        checked = read_fit(cell, assets["checkpoints"][lineage]["P"], assets["witnesses"][lineage])
        data[lineage]["U"] = checked["arrays"]
        reading["checkpoints"][label], reading["updates"][label] = checked["reading"], checked["updates"]
        reading["curves"][label] = {key: [row[key] for row in checked["rows"]] for key in
                                   ("episode", "J_net", "served_users_per_tick", "Q", "log_std", "sigma")}
        reading["exposure"][label], reading["fit_resources"][label] = cell["exposure"], cell["resources"]
        for program in ("P", "K", "D"):
            binding = assets["checkpoints"][lineage][program]
            data[lineage][program] = old.read_bound_checkpoint(binding, lineage=lineage,
                stage="B" if program == "P" else program, endpoint="final", launch_sha=PARENT_SOURCE)
    panels, matched = {l: {} for l in LINEAGES}, {}
    raw_bytes = 0
    for cell in evaluations:
        lineage, program = cell["lineage"], cell["program"]
        label = f"{lineage}/{program}"
        assert cell["status"] == "COMPLETE" and not cell["limits"] and cell["scientific_invocation"] is True
        assert cell["launch_sha"] == summary["source_sha"]
        assert cell == load_json(Path(cell["directory"]) / "summary.json")
        for key, value in expected_evaluation_counts().items():
            assert cell["counts"][key] == value, (label, key)
        expected_binding = (next(f["final_checkpoint"] for f in fits if f["lineage"] == lineage)
                            if program == "U" else assets["checkpoints"][lineage][program])
        assert cell["checkpoint"] == expected_binding
        arrays = data[lineage][program]
        ordinary = program in ("P", "U")
        hashes = {k: hashlib.sha256(v.tobytes()).hexdigest() for k, v in old.grouped(arrays,
                  "B" if ordinary else program).items()}
        assert cell["initial_tensor_sha256"] == cell["after_eval_tensor_sha256"] == hashes
        log_std = arrays["actor"]["log_std" if ordinary else "base.log_std"]
        np.testing.assert_array_equal(cell["actual_log_std"], log_std)
        check_sigma(log_std, cell["actual_sigma"])
        calibration = arrays["actor"]["b"].tolist() if program == "K" else None
        rows = read_episodes(cell, "final_eval")
        checks = [read_trace(row, program, calibration, log_std) for row in rows]
        reading["raw_checks"][label] = checks
        panels[lineage][program] = [check["levels"] for check in checks]
        reading["levels"][label] = {key: statistics.mean(row[key] for row in panels[lineage][program]) for key in METRICS}
        timing = cell["timing"]
        assert timing["actor_forward"]["calls"] == HORIZON * EVAL and timing["episode_loop"]["calls"] == EVAL
        assert timing["setup"]["calls"] == 1
        for cost in timing.values():
            assert cost["wall_ns"] >= 0 and cost["process_cpu_ns"] >= 0
        reading["evaluation_timing"][label] = timing
        for e, check in enumerate(checks):
            witness = tuple(check[key] for key in ("initial_scene_sha256", "user_positions_sha256",
                                                   "channel_sha256", "innovation_sha256"))
            if program == "P":
                matched[(lineage, e)] = witness
            else:
                assert matched[(lineage, e)] == witness
        mean = np.mean([c["correction_mean"] for c in checks], axis=0)
        second = np.mean([c["correction_second_moment"] for c in checks], axis=0)
        reading["corrections"][label] = dict(mean=mean.tolist(), second_moment=second.tolist(),
            standard_deviation=np.sqrt(np.maximum(0, second - mean ** 2)).tolist(),
            constant_component_fraction=float(np.square(mean).sum() / second.sum()) if second.sum() else None,
            **{key: statistics.mean(c["residual"][key] for c in checks) for key in checks[0]["residual"]})
        reading["motion_distribution"][label] = dict(sigma=cell["actual_sigma"], log_std=cell["actual_log_std"],
            **{key: np.mean([c["motion_distribution"][key] for c in checks], axis=0).tolist()
               for key in ("mean", "mean_std", "sampled_action_mean", "sampled_action_rms")})
        raw_bytes += sum(row["raw_bytes"] for row in rows)
    for left, right in (("U", "D"), ("U", "P"), ("U", "K"), ("D", "P"), ("K", "P"), ("D", "K")):
        reading["contrasts"][f"{left}-{right}"] = {metric: contrast(panels, left, right, metric) for metric in METRICS}
    cells = fits + evaluations
    for key, value in summary["actual"].items():
        assert value == sum(cell["counts"].get(key, 0) for cell in cells), key
    for key, value in dict(fit_started=3, constructors=15, train_episodes=1536, final_eval_episodes=384,
        train_team_steps=393216, final_eval_team_steps=98304, team_steps=491520, native_step_calls=491520,
        actual_adam_calls=3072, joint_optimizer_steps=3072, actor_optimizer_steps=0, critic_optimizer_steps=0,
        replayed_actor_rows=7864320, replayed_critic_rows=1572864, motion_samples=2457600).items():
        assert summary["actual"][key] == value, key
    assert len({row[0] for row in matched.values()}) == 96
    reading.update(all_checks_passed=True, panels=panels, raw_trajectories=384, raw_bytes=raw_bytes,
                   canonical_output=str(root), inherited_reader_sha256=digest(old.__file__))
    return reading


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args(argv)
    start, wall = resource.getrusage(resource.RUSAGE_SELF), time.monotonic()
    reading = read_run(args.root)
    end = resource.getrusage(resource.RUSAGE_SELF)
    reading["reader_resources"] = dict(wall_seconds=time.monotonic() - wall,
        user_seconds=end.ru_utime - start.ru_utime, system_seconds=end.ru_stime - start.ru_stime,
        process_cpu_seconds=end.ru_utime + end.ru_stime - start.ru_utime - start.ru_stime,
        lifetime_peak_rss_kib_linux=end.ru_maxrss, scope="post-import reader; external full-command timing separate")
    path = args.root / "reading.json"
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(reading, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)
    print(json.dumps(dict(all_checks_passed=True, path=str(path), raw_trajectories=reading["raw_trajectories"])))


if __name__ == "__main__":
    main()
