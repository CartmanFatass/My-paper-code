#!/usr/bin/env python3
"""Read every fixed B01 lineage, update stream and native final trajectory."""

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

from experiments.candidates.uav_message_content.read_b05 import close, digest, interval
from experiments.candidates.uav_message_content.read_b06 import (
    read_trace as read_retained_trace, verify_innovations,
)
from experiments.candidates.uav_parent_adaptation.b01.protocol import (
    HORIZON, TRAIN, EVAL, LINEAGES, STAGES, PROGRAMS, masters, addresses, rng_table,
    expected_training_counts, expected_evaluation_counts,
)

METRICS = ("J_net", "J_physical", "served_users_per_tick", "Q", "worst_tick_service",
           "service_p05", "zero_service_steps", "longest_zero_service", "motion_path_m_per_uav",
           "boundary_fraction", "height_floor_fraction", "height_ceiling_fraction", "mean_height_m")
HIGHER = {"J_net", "J_physical", "served_users_per_tick", "Q", "worst_tick_service", "service_p05"}
LOWER = {"zero_service_steps", "longest_zero_service"}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def grouped(arrays, stage):
    def flat(group, prefix=""):
        return np.concatenate([v.ravel() for k, v in arrays[group].items() if k.startswith(prefix)])
    if stage in ("C", "B"):
        return dict(actor=flat("actor"), critic=flat("critic"))
    result = dict(base_actor=flat("actor", "base."), critic_old=flat("critic", "network."),
                  critic_forecast=flat("critic", "forecast_projection."))
    if stage == "K":
        result["calibration"] = arrays["actor"]["b"].ravel()
    else:
        result.update(residual_hidden=flat("actor", "residual_hidden."),
                      residual_output=flat("actor", "residual_output."))
    return result


def read_bound_checkpoint(binding, *, lineage, stage, endpoint, launch_sha):
    # This validator deserializes/checks static tensor schemas; it must not construct/forward a model.
    from experiments.candidates.uav_parent_adaptation.b01.model import read_checkpoint

    content = Path(binding["path"]).read_bytes()
    state = read_checkpoint(content, binding, lineage=lineage, stage=stage,
                            endpoint=endpoint, launch_sha=launch_sha)
    arrays = {group: {key: tensor.detach().numpy() for key, tensor in state[group].items()}
              for group in ("actor", "critic")}
    return arrays


def read_fit_checkpoints(cell, previous):
    lineage, stage, source = cell["lineage"], cell["stage"], cell["launch_sha"]
    values, groups = {}, {}
    for endpoint in ("initial", "final"):
        binding = cell[f"{endpoint}_checkpoint"]
        arrays = read_bound_checkpoint(binding, lineage=lineage, stage=stage,
                                       endpoint=endpoint, launch_sha=source)
        values[endpoint], groups[endpoint] = arrays, grouped(arrays, stage)
        hashes = {k: hashlib.sha256(v.tobytes()).hexdigest() for k, v in groups[endpoint].items()}
        assert hashes == cell[f"{endpoint}_tensor_sha256"]
        assert binding["parent"] == cell["parent"]
    for key, before in groups["initial"].items():
        after = groups["final"][key]
        reported = cell["exposure"][key]
        assert reported["parameters"] == before.size
        close(reported["initial_norm"], float(np.linalg.norm(before)), 2e-4)
        close(reported["displacement"], float(np.linalg.norm(after - before)), 2e-4)
        if "final_norm" in reported:
            close(reported["final_norm"], float(np.linalg.norm(after)), 2e-4)
    if stage == "C":
        assert cell["parent"] is None
    elif stage == "B":
        assert cell["parent"] == previous["C"]["binding"]
        expected = {group: {key: value.copy() for key, value in tensors.items()}
                    for group, tensors in previous["C"]["arrays"].items()}
        for key in ("encoder.raw.weight", "encoder.hidden.weight"):
            expected["actor"][key][:, [126 + 10 * sender for sender in range(5)]] = 0
        expected["critic"]["network.0.weight"][:,
            [154 + 63 * receiver + 10 * sender for receiver in range(5) for sender in range(5)]] = 0
        for group in expected:
            for key, value in expected[group].items():
                np.testing.assert_array_equal(values["initial"][group][key], value)
    else:
        assert cell["parent"] == previous["B"]["binding"]
        parent = previous["B"]["arrays"]
        for endpoint in ("initial", "final"):
            for key, value in parent["actor"].items():
                np.testing.assert_array_equal(values[endpoint]["actor"]["base." + key], value)
        for key, value in parent["critic"].items():
            np.testing.assert_array_equal(values["initial"]["critic"][key], value)
        assert not np.any(groups["initial"]["calibration" if stage == "K" else "residual_output"])
        assert not np.any(groups["initial"]["critic_forecast"])
        assert not np.any(groups["final"]["critic_forecast"])
        assert cell["exposure"]["base_actor"]["displacement"] == 0
        assert cell["initial_sigma"] == cell["final_sigma"]
        assert cell["actor_trainable_parameters"] == (3 if stage == "K" else 16259)
    return dict(binding=cell["final_checkpoint"], arrays=values["final"],
                initial_arrays=values["initial"],
                reading=dict(initial_and_final_tensor_identity=True, source_and_lineage_verified=True,
                             group_sizes={k: int(v.size) for k, v in groups["final"].items()},
                             structural_zero_only_start=stage == "B",
                             frozen_parent_verified=stage in ("K", "D"),
                             final_calibration_b=values["final"]["actor"]["b"].tolist() if stage == "K" else None))


def read_updates(cell):
    path = Path(cell["directory"]) / "updates.jsonl"
    assert digest(path) == cell["update_stream_sha256"]
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    stage = cell["stage"]
    parent = stage in ("C", "B")
    rollouts = cell["configuration"]["train"] // 2
    kind = "joint_ppo" if parent else "ppo"
    assert [(r["rollout"], r["kind"], r["epoch"]) for r in rows] == [
        (r, kind, e) for r in range(rollouts) for e in range(4)]
    assert len(rows) == cell["counts"]["optimizer_steps"]
    fields = ("loss", "policy_loss", "value_loss", "entropy", "grad_norm") if parent else (
        "loss", "policy_loss", "value_loss", "gaussian_entropy", "actor_grad_norm", "critic_grad_norm")
    for row in rows:
        assert all(math.isfinite(row[k]) for k in fields)
        entropy = row["entropy" if parent else "gaussian_entropy"]
        close(row["loss"], row["policy_loss"] + .5 * row["value_loss"] - .01 * entropy, .0002)
        assert all(row[k] >= 0 for k in fields if "grad_norm" in k)
    expected_lrs = [.0003] if parent else ([.003, .0003] if stage == "K" else [.0003, .0003])
    assert cell["actual_optimizer_lrs"] == expected_lrs
    assert cell["initial_optimizer_state_entries"] == [0] * len(expected_lrs)
    assert cell["counts"]["actual_adam_calls"] == len(rows) * (1 if parent else 2)
    return dict(epoch_records=len(rows), actual_adam_calls=cell["counts"]["actual_adam_calls"],
                first16_rollouts={k: statistics.mean(r[k] for r in rows if r["rollout"] < 16) for k in fields},
                last16_rollouts={k: statistics.mean(r[k] for r in rows if r["rollout"] >= max(0, rollouts - 16))
                                 for k in fields},
                maximum_gradients={k: max(r[k] for r in rows) for k in fields if "grad_norm" in k},
                optimizer_law=cell["optimizer_law"], actual_lrs=expected_lrs, sha256=digest(path))


def read_episodes(cell, phase):
    import torch

    path = Path(cell["directory"]) / "episodes.jsonl"
    assert digest(path) == cell["episode_stream_sha256"]
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    lineage = cell["lineage"]
    train = phase == "train"
    count = cell["configuration"]["train" if train else "evaluation"]
    stage = cell["stage"] if train else "evaluation"
    addr = addresses(lineage, stage, train=count if train else TRAIN,
                     evaluation=count if not train else EVAL)
    assert addr == cell["addresses"] and len(rows) == count
    rng = torch.Generator().manual_seed(addr["motion"]) if train else None
    for e, row in enumerate(rows):
        assert row["lineage"] == lineage and row["episode"] == e and row["phase"] == phase
        assert row["arm"] == (cell["stage"] if train else cell["program"])
        assert row["reset_seed"] == addr["scene_start"] + e
        assert row["channel_seed"] == addr["channel_start"] + e
        assert row["motion_seed"] == (addr["motion"] if train else addr["motion_start"] + e)
        assert row["steps"] == cell["configuration"]["horizon"]
        assert row["packet_bytes"] == (28 if stage in ("C", "B") else 40)
        close(row["J_physical"], .014 * row["served_users_per_tick"] + .3 * row["Q"], 1e-10)
        close(row["J_net"], row["J_physical"] - .001, 1e-10)
        close(row["charge_per_tick"], .001, 1e-14)
        assert row["delivered_packets"] + row["pending_at_end"] == row["steps"]
        if train:
            verify_innovations(row, rng)
    assert cell["counts"]["delivered_packets"] == sum(row["delivered_packets"] for row in rows)
    assert cell["counts"]["censored_packets"] == sum(row["pending_at_end"] for row in rows)
    if not train:
        assert rows == cell["rows"]
    return rows


def read_trace(row, program, calibration_b=None, expected_log_std=None):
    mapped = "B40" if program in ("I", "P") else program
    reading = read_retained_trace(row, mapped, calibration_b)
    with np.load(row["raw"], allow_pickle=False) as raw:
        assert Path(row["raw"]).stat().st_size == row["raw_bytes"]
        if expected_log_std is not None:
            np.testing.assert_array_equal(raw["log_std"], expected_log_std)
        services = raw["served_users"]
        reading["levels"]["service_p05"] = float(np.quantile(services, .05))
        reading["levels"]["motion_path_m_per_uav"] = reading["motion_path_m_per_uav"]
        reading["zero_service_times"] = np.flatnonzero(services == 0).tolist()
        correction = raw["correction"].astype(np.float64)
        sigma = np.exp(np.clip(raw["log_std"].astype(np.float64), -5, 2))
        relative = correction / sigma
        reading["correction_relative_sigma_rms"] = np.sqrt(np.square(relative).mean((0, 1))).tolist()
        reading["correction_relative_sigma_max"] = np.abs(relative).max((0, 1)).tolist()
        reading["same_history_ideal_gaussian_kl_mean"] = float(.5 * np.square(relative).sum(-1).mean())
    return reading


def contrast(panels, left, right, metric):
    vectors = np.asarray([[a[metric] - b[metric] for a, b in zip(panels[l][left], panels[l][right])]
                          for l in LINEAGES])
    assert vectors.shape == (3, 32)
    means = vectors.mean(1)
    outer = interval(means, 2)
    outer["scope"] = "independent complete C→B generation, K/D adaptation and independent deployment sampling"
    utility = "higher" if metric in HIGHER else ("lower" if metric in LOWER else "descriptive_only")
    adverse = vectors < 0 if metric in HIGHER else vectors > 0 if metric in LOWER else None
    low, high = np.unravel_index(vectors.argmin(), vectors.shape), np.unravel_index(vectors.argmax(), vectors.shape)
    return dict(mean=float(means.mean()), per_lineage_mean=means.tolist(), outer_program=outer,
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
    manifest, witness = load_json(root / "launch-manifest.json"), load_json(root / "process-exit.json")
    assert summary["object"] == "UAV-PARENT-ADAPTATION-B01" and summary["status"] == "COMPLETE"
    assert not summary["limits"] and witness["exit_code"] == 0
    assert summary["scientific_invocation"] is True
    assert summary["source_sha"] == config["source_sha"] == manifest["sha"]
    assert manifest["direction"] == "uav_parent_adaptation" and manifest["lead"] == "Codex DM (native child)"
    assert manifest["node"] == "wsl_4070"
    assert (config["horizon"], config["train"], config["evaluation"]) == (HORIZON, TRAIN, EVAL)
    assert config["rng"] == rng_table() and not config["parent_quality_selection"] and not config["checkpoint_selection"]
    assert summary["config_sha256"] == digest(root / "config.json")
    fits, evaluations = summary["fits"], summary["evaluations"]
    assert [(c["lineage"], c["stage"]) for c in fits] == [(l, s) for l in LINEAGES for s in STAGES]
    assert [(c["lineage"], c["program"]) for c in evaluations] == [(l, p) for l in LINEAGES for p in PROGRAMS]
    reading = dict(object="UAV-PARENT-ADAPTATION-B01-READING", all_checks_passed=False,
                   source_sha=summary["source_sha"], summary_sha256=digest(root / "summary.json"),
                   reader_sha256=digest(__file__), actual=summary["actual"],
                   native_steps_added=0, optimizer_calls_added=0, model_or_policy_calls_added=0,
                   checkpoints={}, updates={}, curves={}, exposure={}, levels={}, raw_checks={},
                   corrections={}, contrasts={}, resources=summary["resources"], cell_resources={},
                   limitations=[
                       "Exploratory n=3 independent complete programs; 96 worlds do not increase outer n.",
                       "Outer blocks combine generation, adaptation and deployment sampling, not pure parent variance.",
                       "Descriptive t intervals assume independent appropriate contrast distributions; no equivalence or confirmation.",
                       "D-K compares finite parameterization/optimization programs, not causal state/message information.",
                       "One sampled motion stream per scene/channel tuple does not estimate within-scene policy risk.",
                       "40-byte adaptation/evaluation preserves abstract28-byte delay/fee, not physical bandwidth efficiency.",
                       "Path/boundary/height and zero-service measures do not establish battery or physical-flight safety.",
                   ])
    checkpoint_data = {l: {} for l in LINEAGES}
    training_witnesses = {}
    for cell in fits:
        assert cell["status"] == "COMPLETE" and not cell["limits"]
        lineage, stage = cell["lineage"], cell["stage"]
        label = f"{lineage}/{stage}"
        assert cell["master"] == masters(lineage)[stage]
        assert cell["launch_sha"] == summary["source_sha"]
        assert cell == load_json(Path(cell["directory"]) / "summary.json")
        for key, value in expected_training_counts(stage).items():
            assert cell["counts"][key] == value, (label, key)
        checked = read_fit_checkpoints(cell, checkpoint_data[lineage])
        checkpoint_data[lineage][stage] = checked
        reading["checkpoints"][label] = checked["reading"]
        reading["updates"][label] = read_updates(cell)
        reading["exposure"][label] = cell["exposure"]
        reading["cell_resources"][label] = cell["resources"]
        rows = read_episodes(cell, "train")
        reading["curves"][label] = {key: [row.get(key) for row in rows] for key in
                                   ("episode", "J_net", "served_users_per_tick", "Q", "correction_rms")}
        if stage in ("K", "D"):
            witness_fields = ("initial_scene_sha256", "channel_sequence_sha256", "motion_rng_start_sha256",
                              "motion_rng_end_sha256", "innovation_sha256")
            witnesses = [tuple(row[k] for k in witness_fields) for row in rows]
            if stage == "K":
                training_witnesses[lineage] = witnesses
            else:
                assert witnesses == training_witnesses[lineage]
            assert rows[0]["correction_rms"] == rows[1]["correction_rms"] == 0
    panels = {l: {} for l in LINEAGES}
    matched_evaluation = {}
    raw_bytes = 0
    for cell in evaluations:
        assert cell["status"] == "COMPLETE" and not cell["limits"]
        lineage, program = cell["lineage"], cell["program"]
        label = f"{lineage}/{program}"
        assert cell == load_json(Path(cell["directory"]) / "summary.json")
        for key, value in expected_evaluation_counts().items():
            assert cell["counts"][key] == value, (label, key)
        stage = "C" if program == "I" else "B" if program == "P" else program
        fit = next(c for c in fits if c["lineage"] == lineage and c["stage"] == stage)
        endpoint = "initial" if program == "I" else "final"
        assert cell["checkpoint"] == fit[f"{endpoint}_checkpoint"]
        assert cell["initial_tensor_sha256"] == cell["after_eval_tensor_sha256"] == fit[f"{endpoint}_tensor_sha256"]
        arrays = checkpoint_data[lineage][stage]["initial_arrays" if program == "I" else "arrays"]
        log_std = arrays["actor"]["log_std" if program in ("I", "P") else "base.log_std"]
        calibration = arrays["actor"]["b"].tolist() if program == "K" else None
        rows = read_episodes(cell, "final_eval")
        checks = [read_trace(row, program, calibration, log_std) for row in rows]
        reading["raw_checks"][label] = checks
        panels[lineage][program] = [check["levels"] for check in checks]
        reading["levels"][label] = {key: statistics.mean(row[key] for row in panels[lineage][program]) for key in METRICS}
        reading["cell_resources"][label + "/evaluation"] = cell["resources"]
        for e, checked in enumerate(checks):
            witness = tuple(checked[key] for key in ("initial_scene_sha256", "user_positions_sha256",
                                                    "channel_sha256", "innovation_sha256"))
            if program == "I":
                matched_evaluation[(lineage, e)] = witness
            else:
                assert witness == matched_evaluation[(lineage, e)]
        mean = np.mean([check["correction_mean"] for check in checks], axis=0)
        second = np.mean([check["correction_second_moment"] for check in checks], axis=0)
        variance = np.maximum(0, second - mean ** 2)
        reading["corrections"][label] = dict(
            mean=mean.tolist(), standard_deviation=np.sqrt(variance).tolist(), second_moment=second.tolist(),
            constant_component_fraction=float(np.square(mean).sum() / second.sum()) if second.sum() > 0 else None,
            relative_sigma_rms=np.sqrt(np.mean([np.square(check["correction_relative_sigma_rms"])
                                                for check in checks], axis=0)).tolist(),
            ideal_same_history_kl_mean=statistics.mean(check["same_history_ideal_gaussian_kl_mean"] for check in checks),
            **{key: statistics.mean(check["residual"][key] for check in checks) for key in checks[0]["residual"]})
        raw_bytes += sum(row["raw_bytes"] for row in rows)
    for left, right in (("D", "K"), ("D", "P"), ("K", "P"), ("P", "I")):
        label = f"{left}-{right}"
        reading["contrasts"][label] = {metric: contrast(panels, left, right, metric) for metric in METRICS}
    cells = fits + evaluations
    for key, value in summary["actual"].items():
        assert value == sum(c["counts"].get(key, 0) for c in cells), key
    assert summary["actual"]["fit_started"] == 12
    assert summary["actual"]["team_steps"] == 1671168
    assert summary["actual"]["actual_adam_calls"] == 18432
    assert summary["actual"]["replayed_actor_rows"] == 31457280
    assert len({fit["initial_tensor_sha256"]["actor"] for fit in fits if fit["stage"] == "C"}) == 3
    assert len({row[0] for row in matched_evaluation.values()}) == 96
    reading.update(all_checks_passed=True, raw_trajectories=384, raw_bytes=raw_bytes,
                   canonical_output=str(root), panels=panels,
                   inherited_readers={name: digest(ROOT / "experiments/candidates/uav_message_content" / name)
                                      for name in ("read_b04.py", "read_b05.py", "read_b06.py")})
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
