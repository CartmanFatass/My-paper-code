"""Reconstruct complete B05 evidence without policy or simulator calls."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.uav_message_content.read_b04 import (
    close, digest, merge_error_summaries, read_trace as read_geometry_trace,
)

MASTERS = (19601, 19602, 19603)
ARMS = ("M_G", "M_O")
BOUND_SHA = "34871c49874ec716c21438581facfaeca8a25930304a39eb26e001fb2b259da2"
BOUND_CANONICAL = "/home/wu/projects/HMASD/runs/uav_message_content/b02_preserved_scalar/19451/B/final.pt"
METRICS = (
    "J_net", "J_physical", "served_users_per_tick", "Q", "worst_tick_service",
    "zero_service_steps", "longest_zero_service", "boundary_fraction", "height_floor_fraction",
    "height_ceiling_fraction", "mean_height_m",
)
EXPOSURE = (
    "correction_rms", "correction_abs_mean", "correction_max", "correction_saturation_fraction",
    "correction_nonzero_fraction", "same_noise_action_change_rms",
)


def longest_zero_interval(values):
    zero = np.r_[False, np.asarray(values) == 0, False]
    edges = np.flatnonzero(zero[1:] != zero[:-1])
    return int(np.max(edges[1::2] - edges[::2], initial=0))


def read_trace(row, arm):
    reading = read_geometry_trace(row, "O" if arm == "M_O" else "G")
    with np.load(row["raw"], allow_pickle=False) as data:
        for name in ("base_mean", "composed_mean", "correction"):
            assert data[name].shape == (256, 5, 3) and np.isfinite(data[name]).all()
        assert data["sample_logp"].shape == (256, 5)
        assert data["log_std"].shape == (3,)
        base, mean, correction = (data[name].astype(np.float64) for name in (
            "base_mean", "composed_mean", "correction"))
        u = data["pre_tanh_motion"].astype(np.float64)
        close(mean, base + correction, 2e-7)
        close(data["central_motion"], np.tanh(mean), 1e-7)
        assert np.max(np.abs(correction)) <= .1 + 1e-7
        log_std = np.clip(data["log_std"].astype(np.float64), -5, 2)
        normal = -.5 * np.square((u - mean) / np.exp(log_std)) - log_std - .5 * math.log(2 * math.pi)
        jacobian = 2 * (math.log(2) - u - np.logaddexp(0, -2 * u))
        predicted_logp = (normal - jacobian).sum(-1)
        close(data["sample_logp"], predicted_logp, 1e-5)
        same_noise_change = np.tanh(u) - np.tanh(u - correction)
        assert np.max(np.abs(same_noise_change)) <= .1 + 1e-7
        if arm == "B40":
            close(correction, 0, 0)
            close(mean, base, 0)
        behavior = dict(
            correction_rms=float(np.sqrt(np.square(correction).mean())),
            correction_abs_mean=float(np.abs(correction).mean()), correction_max=float(np.abs(correction).max()),
            correction_saturation_fraction=float((np.abs(correction) >= .095).mean()),
            correction_nonzero_fraction=float((correction != 0).mean()),
            same_noise_action_change_rms=float(np.sqrt(np.square(same_noise_change).mean())),
        )
        for key, value in behavior.items():
            close(row[key], value, 1e-7)
        served = data["served_users"]
        reading["levels"].update(zero_service_steps=int((served == 0).sum()),
                                  longest_zero_service=longest_zero_interval(served))
        for key in ("zero_service_steps", "longest_zero_service", "worst_tick_service"):
            close(row[key], reading["levels"][key], 0)
        assert reading["cache_uses"] == row["valid_future_cache_uses"]
        reading.update(residual=behavior, log_std=data["log_std"].tolist(),
                       density_max_abs_error=float(np.max(np.abs(data["sample_logp"] - predicted_logp))))
    return reading


def interval(values, df):
    values = list(map(float, values))
    assert len(values) == df + 1 and df in (2, 31)
    mean, sd = statistics.mean(values), statistics.stdev(values)
    critical = 4.302652729911275 if df == 2 else 2.0395134463964077
    half = critical * sd / math.sqrt(len(values))
    return dict(mean=mean, sample_sd=sd, descriptive_t95=[mean - half, mean + half], df=df)


def contrast(first, second, metric):
    vectors = np.asarray([[x[metric] - y[metric] for x, y in zip(first[m], second[m])] for m in MASTERS])
    assert vectors.shape == (3, 32)
    means = vectors.mean(1)
    conditional = interval(means, 2)
    conditional["scope"] = "fresh continuations conditional on one selected parent and this common deployment panel"
    return dict(
        mean=float(means.mean()), per_continuation_mean=means.tolist(), conditional_training=conditional,
        deployment_by_continuation={str(m): interval(values, 31) for m, values in zip(MASTERS, vectors)},
        deployment_average_over_blocks=interval(vectors.mean(0), 31),
        per_world_differences={str(m): values.tolist() for m, values in zip(MASTERS, vectors)},
        adverse_worlds={str(m): np.flatnonzero(values < 0).tolist() for m, values in zip(MASTERS, vectors)},
        minimum=float(vectors.min()), maximum=float(vectors.max()),
        minimum_at=[int(MASTERS[np.unravel_index(vectors.argmin(), vectors.shape)[0]]),
                    int(np.unravel_index(vectors.argmin(), vectors.shape)[1])],
        maximum_at=[int(MASTERS[np.unravel_index(vectors.argmax(), vectors.shape)[0]]),
                    int(np.unravel_index(vectors.argmax(), vectors.shape)[1])],
    )


def expected_counts(arm):
    baseline = arm == "B40"
    return dict(
        constructors=1, explicit_resets=32 if baseline else 544, fit_started=0 if baseline else 1,
        train_episodes=0 if baseline else 512, final_eval_episodes=32,
        train_team_steps=0 if baseline else 131072, final_eval_team_steps=8192,
        team_steps=8192 if baseline else 139264, native_step_calls=8192 if baseline else 139264,
        motion_samples=40960 if baseline else 696320, broadcasts=8192 if baseline else 139264,
        attempts=8192 if baseline else 139264, rollouts=0 if baseline else 256,
        optimizer_steps=0 if baseline else 1024, actor_optimizer_steps=0 if baseline else 1024,
        critic_optimizer_steps=0 if baseline else 1024, replayed_actor_rows=0 if baseline else 2621440,
        evaluation_optimizer_steps=0, diagnostic_forward_calls=8192 if arm == "M_O" else 0,
        behavior_actor_forward_calls=8192 if baseline else 139264,
        behavior_actor_forward_rows=40960 if baseline else 696320,
        behavior_critic_forward_calls=0 if baseline else 131072,
        behavior_critic_forward_rows=0 if baseline else 131072,
        ppo_actor_forward_calls=0 if baseline else 1024, ppo_actor_forward_rows=0 if baseline else 2621440,
        ppo_critic_forward_calls=0 if baseline else 1024, ppo_critic_forward_rows=0 if baseline else 524288,
    )


def validate_exposure(cells, b40, actual):
    assert [(c["master"], c["arm"]) for c in cells] == [(m, a) for m in MASTERS for a in ARMS]
    assert b40["arm"] == "B40" and b40["master"] == 19451
    for cell in [*cells, b40]:
        assert cell["status"] == "COMPLETE" and not cell["limits"]
        for key, value in expected_counts(cell["arm"]).items():
            assert cell["counts"][key] == value, (cell["master"], cell["arm"], key, cell["counts"][key], value)
        assert cell["counts"]["delivered_packets"] + cell["counts"]["censored_packets"] == cell["counts"]["team_steps"]
    for key, value in actual.items():
        assert value == sum(c["counts"][key] for c in [*cells, b40]), key
    assert actual["fit_started"] == 6 and actual["train_team_steps"] == 786432
    assert actual["final_eval_team_steps"] == 57344 and actual["team_steps"] == 843776
    assert actual["actor_optimizer_steps"] == actual["critic_optimizer_steps"] == actual["optimizer_steps"] == 6144


def checkpoint_arrays(path):
    # Deserialization only: no learner/environment construction or forward calls.
    import torch
    value = torch.load(path, map_location="cpu", weights_only=True)
    return value, {group: {key: tensor.detach().numpy() for key, tensor in value[group].items()}
                   for group in ("actor", "critic")}


def parameter_groups(arrays):
    actor, critic = arrays["actor"], arrays["critic"]
    def flat(values, prefix):
        return np.concatenate([value.ravel() for key, value in values.items() if key.startswith(prefix)])
    return dict(base_actor=flat(actor, "base."), residual_hidden=flat(actor, "residual_hidden."),
                residual_output=flat(actor, "residual_output."), critic_old=flat(critic, "network."),
                critic_forecast=flat(critic, "forecast_projection."))


def read_checkpoints(cell, parent):
    groups = []
    for label in ("initial", "final"):
        record = cell[f"{label}_checkpoint"]
        assert digest(record["path"]) == record["sha256"] and Path(record["path"]).stat().st_size == record["bytes"]
        meta, arrays = checkpoint_arrays(record["path"])
        assert meta["arm"] == cell["arm"] and meta["master"] == cell["master"]
        assert meta["inherited_sha256"] == BOUND_SHA and meta["correction_bound"] == .1
        assert meta["source_sha"] == cell["launch_sha"] and meta["input_size"] == 186 and meta["critic_size"] == 526
        for key, original in parent["actor"].items():
            assert np.array_equal(arrays["actor"]["base." + key], original), key
        grouped = parameter_groups(arrays)
        for name, flat in grouped.items():
            assert hashlib.sha256(flat.tobytes()).hexdigest() == cell[f"{label}_tensor_sha256"][name]
        if label == "initial":
            assert not np.any(grouped["residual_output"])
            assert not np.any(grouped["critic_forecast"])
            for key, original in parent["critic"].items():
                assert np.array_equal(arrays["critic"][key], original), key
        groups.append(grouped)
    assert cell["after_eval_tensor_sha256"] == cell["final_tensor_sha256"]
    for name in groups[0]:
        before, after = groups[0][name], groups[1][name]
        reported = cell["exposure"][name]
        assert reported["parameters"] == before.size
        close(reported["initial_norm"], float(np.linalg.norm(before)), 2e-4)
        close(reported["final_norm"], float(np.linalg.norm(after)), 2e-4)
        close(reported["displacement"], float(np.linalg.norm(after - before)), 2e-4)
    assert cell["exposure"]["base_actor"]["displacement"] == 0
    if cell["arm"] == "M_G":
        assert cell["exposure"]["critic_forecast"]["displacement"] == 0
    return dict(base_matches_canonical=True, initial_and_final_hashes_verified=True,
                group_sizes={name: int(value.size) for name, value in groups[0].items()})


def read_updates(cell):
    path = Path(cell["directory"]) / "updates.jsonl"
    assert digest(path) == cell["update_stream_sha256"]
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rollouts = cell["configuration"]["train"] // 2
    assert len(rows) == cell["counts"]["optimizer_steps"] == 4 * rollouts
    assert [(r["rollout"], r["kind"], r["epoch"]) for r in rows] == [
        (rollout, "ppo", epoch) for rollout in range(rollouts) for epoch in range(4)]
    fields = ("loss", "policy_loss", "value_loss", "gaussian_entropy", "actor_grad_norm", "critic_grad_norm")
    for row in rows:
        assert all(math.isfinite(row[key]) for key in fields)
        assert row["actor_grad_norm"] >= 0 and row["critic_grad_norm"] >= 0
        close(row["loss"], row["policy_loss"] - .01 * row["gaussian_entropy"] + .5 * row["value_loss"], .0002)
    return dict(ppo_records=len(rows), sha256=digest(path),
                first16_rollouts={key: statistics.mean(row[key] for row in rows if row["rollout"] < 16) for key in fields},
                last16_rollouts={key: statistics.mean(row[key] for row in rows if row["rollout"] >= max(0, rollouts - 16)) for key in fields},
                max_actor_grad_norm=max(row["actor_grad_norm"] for row in rows),
                max_critic_grad_norm=max(row["critic_grad_norm"] for row in rows))


def read_run(root):
    root = Path(root)
    summary = json.loads((root / "summary.json").read_text())
    manifest = json.loads((root / "launch-manifest.json").read_text())
    witness = json.loads((root / "process-exit.json").read_text())
    assert summary["status"] == "COMPLETE" and not summary["limits"] and witness["exit_code"] == 0
    assert summary["source_sha"] == manifest["sha"]
    assert manifest["node"] == "wsl_4070" and manifest["direction"] == "uav_message_content"
    assert manifest["lead"] == "Codex DM (native child)"
    assert summary["warm_start"]["sha256"] == BOUND_SHA and summary["warm_start"]["bytes"] == 463357
    assert digest(BOUND_CANONICAL) == BOUND_SHA
    staged = Path(summary["warm_start"]["path"])
    if staged.exists():
        assert digest(staged) == BOUND_SHA
    _, parent = checkpoint_arrays(BOUND_CANONICAL)
    cells, b40, actual = summary["cells"], summary["b40"], summary["actual"]
    validate_exposure(cells, b40, actual)
    reading = dict(
        source_sha=summary["source_sha"], summary_sha256=digest(root / "summary.json"), reader_sha256=digest(__file__),
        inherited_reader_sha256=digest(Path(__file__).with_name("read_b04.py")), all_checks_passed=False,
        native_steps_added=0, optimizer_calls_added=0, model_or_policy_calls_added=0,
        actual=actual, policy_fits=6, trained_predictor_instances=0,
        batch_wall_seconds=summary["finished_wall"] - summary["started_wall"], resources=summary["resources"],
        levels={}, residual={}, contrasts={}, versus_B40={}, raw_checks={}, checkpoint_checks={}, update_checks={},
        exposure={}, forecast={}, per_cell_resources={}, warm_start=summary["warm_start"], canonical_warm_start=BOUND_CANONICAL,
        limitations=[
            "Three fresh continuation blocks share one selected B19451 parent; they are not independent parent trainings.",
            "Training df2 intervals condition on the common deployment panel; world df31 intervals answer a separate question.",
            "All arms use40-byte abstract packets at the original28-byte fee/delay, not a physical-network bandwidth result.",
            "Frozen mapping and bounded immediate corrections do not preserve closed-loop trajectories or guarantee service.",
            "Forecast sensitivity and executed correction are exposure measures, not mediation or useful control proofs.",
            "This is a fixed-noise c=.10 pre-tanh mean extension; no inference to all residual policies or ordinary planners.",
            "Connected-user identities remain evaluation-only; boundary and altitude are not physical-safety outcomes.",
        ],
    )
    panels, train_bindings, initial_hashes = {}, {}, {}
    reference = None
    base_hash = b40["initial_base_sha256"]
    assert base_hash == b40["final_base_sha256"]
    raw_bytes = connected_bytes = 0
    for cell in [*cells, b40]:
        master, arm = cell["master"], cell["arm"]
        label = "B40" if arm == "B40" else f"{master}/{arm}"
        episode_path = Path(cell["directory"]) / "episodes.jsonl"
        assert digest(episode_path) == cell["episode_stream_sha256"]
        episodes = [json.loads(line) for line in episode_path.read_text().splitlines()]
        train = [row for row in episodes if row["phase"] == "train"]
        final = [row for row in episodes if row["phase"] == "final_eval"]
        assert len(train) == (0 if arm == "B40" else 512) and len(final) == 32
        assert len(episodes) == len(train) + len(final) and final == cell["rows"]
        assert cell["counts"]["delivered_packets"] == sum(row["delivered_packets"] for row in episodes)
        assert cell["counts"]["censored_packets"] == sum(row["pending_at_end"] for row in episodes)
        for e, row in enumerate(train):
            assert row["arm"] == arm and row["master"] == master and row["episode"] == e
            assert row["reset_seed"] == 100000 * master + 1000 + e
            assert row["channel_seed"] == 100000 * master + 6000 + e
            assert row["motion_seed"] == 100000 * master + 21
            assert row["steps"] == row["attempts"] == row["accepted_packets"] == 256
            assert row["collided_attempts"] == 0 and row["correction_max"] <= .1 + 1e-7
            close(row["J_physical"], .014 * row["served_users_per_tick"] + .3 * row["Q"])
            close(row["J_net"], row["J_physical"] - .001)
        if arm != "B40":
            binding = [(row["reset_seed"], row["channel_seed"], row["motion_seed"], row["initial_scene_sha256"],
                        row["channel_sequence_sha256"]) for row in train]
            if master in train_bindings:
                assert binding == train_bindings[master]
                assert initial_hashes[master] == cell["initial_tensor_sha256"]
            else:
                train_bindings[master] = binding
                initial_hashes[master] = cell["initial_tensor_sha256"]
            assert cell["initial_tensor_sha256"]["base_actor"] == cell["final_tensor_sha256"]["base_actor"] == base_hash
            reading["checkpoint_checks"][label] = read_checkpoints(cell, parent)
            reading["update_checks"][label] = read_updates(cell)
            reading["exposure"][label] = cell["exposure"]
            reading["residual"][label] = dict(
                training={key: statistics.mean(row[key] for row in train) for key in EXPOSURE},
                training_first2_max=max(row["correction_max"] for row in train[:2]),
                training_last32={key: statistics.mean(row[key] for row in train[-32:]) for key in EXPOSURE},
            )
            assert reading["residual"][label]["training_first2_max"] == 0
        checks = []
        for e, row in enumerate(final):
            assert row["arm"] == arm and row["master"] == master and row["episode"] == e
            assert row["reset_seed"] == 1960002000 + e and row["channel_seed"] == 1960007000 + e
            assert row["motion_seed"] == 1960003000 + e
            check = read_trace(row, arm)
            close(np.exp(check["log_std"]), cell["inherited_sigma"], 2e-7)
            close(check["log_std"], parent["actor"]["log_std"], 0)
            checks.append(check)
            raw_bytes += Path(row["raw"]).stat().st_size
            connected_bytes += check["connected_bits_bytes"]
        witnesses = [(r["initial_scene_sha256"], r["channel_sha256"], r["user_positions_sha256"]) for r in checks]
        if reference is None:
            reference = witnesses
        else:
            assert witnesses == reference
        panels[(master, arm)] = [dict(row, **check["levels"]) for row, check in zip(final, checks)]
        reading["raw_checks"][label] = checks
        reading["levels"][label] = {metric: statistics.mean(check["levels"][metric] for check in checks) for metric in METRICS}
        reading["residual"].setdefault(label, {})["evaluation"] = {
            key: statistics.mean(check["residual"][key] for check in checks) for key in EXPOSURE}
        reading["per_cell_resources"][label] = dict(cell["resources"], wall_seconds=cell["finished_wall"] - cell["started_wall"])
        if arm == "M_O":
            reading["forecast"][label] = dict(
                ordinary_error={name: merge_error_summaries([c["forecast_error"]["ordinary"][name] for c in checks])
                                for name in checks[0]["forecast_error"]["ordinary"]},
                response_rms=float(np.sqrt(np.mean([c["response_rms"] ** 2 for c in checks]))),
                response_max=max(c["response_max"] for c in checks),
                cache_uses=sum(c["cache_uses"] for c in checks),
                cache_age_counts=np.asarray([c["cache_age_counts"] for c in checks]).sum(0).tolist(),
            )
    reading["contrasts"]["M_O-M_G"] = {
        metric: contrast({m: panels[(m, "M_O")] for m in MASTERS}, {m: panels[(m, "M_G")] for m in MASTERS}, metric)
        for metric in METRICS}
    for arm in ARMS:
        reading["versus_B40"][arm] = {
            metric: contrast({m: panels[(m, arm)] for m in MASTERS}, {m: panels[(19451, "B40")] for m in MASTERS}, metric)
            for metric in METRICS}
    assert connected_bytes == 2867200
    reading.update(all_checks_passed=True, raw_trace_bytes=raw_bytes, connected_bits_uncompressed_bytes=connected_bytes,
                   trajectories_read=224, initial_common_hashes_by_block={str(key): value for key, value in initial_hashes.items()})
    return reading


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = read_run(args.run)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(dict(all_checks_passed=result["all_checks_passed"], trajectories_read=result["trajectories_read"],
                          policy_fits=result["policy_fits"], actual=result["actual"]), allow_nan=False))


if __name__ == "__main__":
    main()
