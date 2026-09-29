"""Read all B06 native evidence without policy, environment or optimizer calls."""

import argparse
import hashlib
import json
from pathlib import Path
import statistics
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.uav_message_content.read_b05 import (
    BOUND_SHA, EXPOSURE, METRICS, checkpoint_arrays, close, digest, expected_counts,
    interval, read_trace as read_retained_trace, read_updates,
)

MASTERS, ARMS = (19701, 19702, 19703), ("K", "D")


def contrast(first, second, metric):
    vectors = np.asarray([[x[metric] - y[metric] for x, y in zip(first[m], second[m])] for m in MASTERS])
    assert vectors.shape == (3, 32)
    means = vectors.mean(1)
    conditional = interval(means, 2)
    conditional["scope"] = "fresh continuations conditional on one selected parent and common deployment panel"
    low = np.unravel_index(vectors.argmin(), vectors.shape)
    high = np.unravel_index(vectors.argmax(), vectors.shape)
    higher = metric in ("J_net", "J_physical", "served_users_per_tick", "Q", "worst_tick_service")
    lower = metric in ("zero_service_steps", "longest_zero_service")
    adverse = vectors < 0 if higher else (vectors > 0 if lower else None)
    return dict(
        mean=float(means.mean()), per_continuation_mean=means.tolist(), conditional_training=conditional,
        deployment_by_continuation={str(m): interval(v, 31) for m, v in zip(MASTERS, vectors)},
        deployment_average_over_blocks=interval(vectors.mean(0), 31),
        per_world_differences={str(m): v.tolist() for m, v in zip(MASTERS, vectors)},
        utility_direction="higher" if higher else ("lower" if lower else "descriptive_only"),
        negative_worlds={str(m): np.flatnonzero(v < 0).tolist() for m, v in zip(MASTERS, vectors)},
        positive_worlds={str(m): np.flatnonzero(v > 0).tolist() for m, v in zip(MASTERS, vectors)},
        adverse_worlds={str(m): np.flatnonzero(v).tolist() for m, v in zip(MASTERS, adverse)}
        if adverse is not None else None,
        minimum=float(vectors.min()), maximum=float(vectors.max()),
        minimum_at=[int(MASTERS[low[0]]), int(low[1])], maximum_at=[int(MASTERS[high[0]]), int(high[1])],
    )


def parameter_groups(arrays, arm):
    actor, critic = arrays["actor"], arrays["critic"]

    def flat(values, prefix):
        return np.concatenate([v.ravel() for key, v in values.items() if key.startswith(prefix)])

    groups = dict(base_actor=flat(actor, "base."), critic_old=flat(critic, "network."),
                  critic_forecast=flat(critic, "forecast_projection."))
    if arm == "K":
        groups["calibration"] = actor["b"].ravel()
        assert groups["calibration"].size == 3
        assert set(actor) == {"b"} | {"base." + key for key in arrays["parent_actor_keys"]}
    else:
        groups.update(residual_hidden=flat(actor, "residual_hidden."),
                      residual_output=flat(actor, "residual_output."))
    return groups


def read_checkpoints(cell, parent):
    groups, final_arrays = [], None
    for label in ("initial", "final"):
        record = cell[f"{label}_checkpoint"]
        assert digest(record["path"]) == record["sha256"]
        assert Path(record["path"]).stat().st_size == record["bytes"]
        meta, arrays = checkpoint_arrays(record["path"])
        assert meta["arm"] == cell["arm"] and meta["master"] == cell["master"]
        assert meta["inherited_sha256"] == BOUND_SHA and meta["correction_bound"] == .1
        assert meta["source_sha"] == cell["launch_sha"] and meta["input_size"] == 186 and meta["critic_size"] == 526
        for key, original in parent["actor"].items():
            assert np.array_equal(arrays["actor"]["base." + key], original), key
        arrays["parent_actor_keys"] = list(parent["actor"])
        grouped = parameter_groups(arrays, cell["arm"])
        for name, values in grouped.items():
            assert hashlib.sha256(values.tobytes()).hexdigest() == cell[f"{label}_tensor_sha256"][name]
        if label == "initial":
            assert not np.any(grouped["calibration" if cell["arm"] == "K" else "residual_output"])
            assert not np.any(grouped["critic_forecast"])
            for key, original in parent["critic"].items():
                assert np.array_equal(arrays["critic"][key], original), key
        groups.append(grouped)
        final_arrays = arrays
    for name in groups[0]:
        before, after = groups[0][name], groups[1][name]
        reported = cell["exposure"][name]
        assert reported["parameters"] == before.size
        for key, value in (("initial_norm", np.linalg.norm(before)), ("final_norm", np.linalg.norm(after)),
                           ("displacement", np.linalg.norm(after - before))):
            close(reported[key], float(value), 2e-4)
    assert cell["exposure"]["base_actor"]["displacement"] == cell["exposure"]["critic_forecast"]["displacement"] == 0
    assert cell["after_eval_tensor_sha256"] == cell["final_tensor_sha256"]
    assert cell["actor_trainable_parameters"] == (3 if cell["arm"] == "K" else 16259)
    assert cell["critic_trainable_parameters"] == groups[0]["critic_old"].size + groups[0]["critic_forecast"].size
    return dict(base_matches_parent=True, initial_and_final_hashes_verified=True,
                group_sizes={k: int(v.size) for k, v in groups[0].items()},
                final_calibration_b=final_arrays["actor"]["b"].tolist() if cell["arm"] == "K" else None)


def rng_state_hash(rng):
    return hashlib.sha256(rng.get_state().numpy().tobytes()).hexdigest()


def verify_innovations(row, rng, raw=None):
    import torch

    assert row["motion_rng_start_sha256"] == rng_state_hash(rng)
    # Preserve the primitive sampler's five separate three-vector calls per tick.
    epsilon = torch.stack([torch.stack([torch.randn(3, generator=rng) for _ in range(5)])
                           for _ in range(row["steps"])])
    assert row["innovation_vectors"] == 5 * row["steps"]
    assert row["innovation_sha256"] == hashlib.sha256(epsilon.numpy().tobytes()).hexdigest()
    assert row["motion_rng_end_sha256"] == rng_state_hash(rng)
    if raw is not None:
        mean = torch.from_numpy(raw["composed_mean"])
        sigma = torch.from_numpy(raw["log_std"]).clamp(-5, 2).exp()
        assert torch.equal(torch.from_numpy(raw["pre_tanh_motion"]), mean + sigma * epsilon)


def read_trace(row, arm, calibration_b=None):
    import torch

    reading = read_retained_trace(row, "B40" if arm == "B40" else "M_G")
    with np.load(row["raw"], allow_pickle=False) as raw:
        assert not np.any(raw["packet"][:, 7:])
        assert not np.any(raw["actor_input"][..., 171:])
        assert not np.any(raw["critic_input"][..., 451:])
        verify_innovations(row, torch.Generator().manual_seed(row["motion_seed"]), raw)
        delta = raw["correction"].astype(np.float64)
        if arm == "K":
            expected = .1 * torch.tensor(calibration_b, dtype=torch.float32).tanh().numpy()
            close(delta, np.broadcast_to(expected, delta.shape), 0)
        reading["correction_mean"] = delta.mean((0, 1)).tolist()
        reading["correction_std"] = delta.std((0, 1)).tolist()
        reading["correction_min"] = delta.min((0, 1)).tolist()
        reading["correction_max_by_coordinate"] = delta.max((0, 1)).tolist()
        reading["correction_second_moment"] = np.square(delta).mean((0, 1)).tolist()
        metres = np.array([1000., 1000., 100.])
        steps = np.diff(raw["position"].astype(np.float64), axis=0) * metres
        reading["motion_path_m_per_uav"] = float(np.linalg.norm(steps, axis=-1).sum(0).mean())
        reading["innovation_sha256"] = row["innovation_sha256"]
    return reading


def read_run(root, parent_path=None):
    import torch

    root = Path(root)
    summary = json.loads((root / "summary.json").read_text())
    manifest = json.loads((root / "launch-manifest.json").read_text())
    witness = json.loads((root / "process-exit.json").read_text())
    assert summary["object"] == "UAV-MESSAGE-CONTENT-B06"
    assert summary["status"] == "COMPLETE" and not summary["limits"] and witness["exit_code"] == 0
    assert summary["source_sha"] == manifest["sha"]
    assert manifest["node"] == "local_linux" and manifest["direction"] == "uav_message_content"
    assert manifest["lead"] == "Codex DM (native child)"
    assert summary["warm_start"]["sha256"] == BOUND_SHA
    parent_path = Path(parent_path or summary["warm_start"]["path"])
    assert digest(parent_path) == BOUND_SHA
    assert parent_path.stat().st_size == summary["warm_start"]["bytes"] == 463357
    _, parent = checkpoint_arrays(parent_path)
    cells, b40, actual = summary["cells"], summary["b40"], summary["actual"]
    assert [(c["master"], c["arm"]) for c in cells] == [(m, a) for m in MASTERS for a in ARMS]
    assert b40["master"] == 19451 and b40["arm"] == "B40"
    for cell in cells + [b40]:
        assert cell["status"] == "COMPLETE" and not cell["limits"]
        for key, count in expected_counts(cell["arm"]).items():
            assert cell["counts"][key] == count, (cell["master"], cell["arm"], key)
        assert cell["counts"]["delivered_packets"] + cell["counts"]["censored_packets"] == cell["counts"]["team_steps"]
    for key, count in actual.items():
        assert count == sum(c["counts"][key] for c in cells + [b40]), key
    assert actual["team_steps"] == 843776 and actual["fit_started"] == 6
    assert actual["actor_optimizer_steps"] == actual["critic_optimizer_steps"] == 6144
    reading = dict(
        source_sha=summary["source_sha"], summary_sha256=digest(root / "summary.json"),
        reader_sha256=digest(__file__), inherited_reader_sha256=digest(Path(__file__).with_name("read_b05.py")),
        all_checks_passed=False, native_steps_added=0, optimizer_calls_added=0, model_or_policy_calls_added=0,
        actual=actual, policy_fits=6, trained_predictor_instances=0, levels={}, raw_checks={},
        checkpoint_checks={}, update_checks={}, exposure={}, corrections={}, per_cell_resources={},
        contrasts={}, versus_B40={}, warm_start=summary["warm_start"],
        batch_wall_seconds=summary["finished_wall"] - summary["started_wall"], resources=summary["resources"],
        limitations=[
            "Three continuation pairs condition on one selected parent and a common evaluation panel, not independent parents.",
            "Training df2 uncertainty differs from fixed-endpoint world df31 uncertainty; 96 rows are not 96 training runs.",
            "One sampled action stream per scene/channel tuple does not measure within-scene stochastic-policy risk.",
            "D-K compares finite representation/optimization packages, not causal state-information use.",
            "K's whole policy still uses recurrent state and legal messages; only its new three-vector is constant.",
            "The40-byte abstract contract retains the old28-byte fees/delays, not measured physical-network bandwidth.",
            "Correction variation is exposure, not useful coordination; path/altitude are not energy or physical safety.",
        ],
    )
    panels, train_bindings, initial_critics = {}, {}, {}
    reference = None
    raw_bytes = connected_bytes = 0
    base_hash = b40["initial_tensor_sha256"]["base_actor"]
    for cell in cells + [b40]:
        master, arm = cell["master"], cell["arm"]
        label = "B40" if arm == "B40" else f"{master}/{arm}"
        assert cell["initial_tensor_sha256"]["base_actor"] == cell["final_tensor_sha256"]["base_actor"] == base_hash
        assert cell["after_eval_tensor_sha256"] == cell["final_tensor_sha256"]
        episode_path = Path(cell["directory"]) / "episodes.jsonl"
        assert digest(episode_path) == cell["episode_stream_sha256"]
        episodes = [json.loads(line) for line in episode_path.read_text().splitlines()]
        train = [r for r in episodes if r["phase"] == "train"]
        final = [r for r in episodes if r["phase"] == "final_eval"]
        assert len(train) == (0 if arm == "B40" else 512) and len(final) == 32
        assert len(episodes) == len(train) + len(final) and final == cell["rows"]
        assert cell["counts"]["delivered_packets"] == sum(r["delivered_packets"] for r in episodes)
        assert cell["counts"]["censored_packets"] == sum(r["pending_at_end"] for r in episodes)
        training_rng = torch.Generator().manual_seed(100000 * master + 21)
        for e, row in enumerate(train):
            assert row["arm"] == arm and row["master"] == master and row["episode"] == e
            assert row["reset_seed"] == 100000 * master + 1000 + e
            assert row["channel_seed"] == 100000 * master + 6000 + e
            assert row["motion_seed"] == 100000 * master + 21
            assert row["steps"] == row["attempts"] == row["accepted_packets"] == 256
            assert row["collided_attempts"] == 0 and row["correction_max"] <= .1 + 1e-7
            close(row["J_physical"], .014 * row["served_users_per_tick"] + .3 * row["Q"])
            close(row["J_net"], row["J_physical"] - .001)
            verify_innovations(row, training_rng)
        calibration = None
        if arm != "B40":
            binding = [(r["initial_scene_sha256"], r["channel_sequence_sha256"], r["innovation_sha256"],
                        r["motion_rng_start_sha256"], r["motion_rng_end_sha256"]) for r in train]
            critic_hashes = {key: cell["initial_tensor_sha256"][key] for key in ("base_actor", "critic_old", "critic_forecast")}
            if master in train_bindings:
                assert binding == train_bindings[master] and critic_hashes == initial_critics[master]
            else:
                train_bindings[master], initial_critics[master] = binding, critic_hashes
            assert cell["initial_optimizer_state_entries"] == [0, 0]
            assert cell["actual_optimizer_lrs"] == ([.003, .0003] if arm == "K" else [.0003, .0003])
            reading["checkpoint_checks"][label] = read_checkpoints(cell, parent)
            calibration = reading["checkpoint_checks"][label]["final_calibration_b"]
            reading["update_checks"][label] = read_updates(cell)
            reading["exposure"][label] = cell["exposure"]
            reading["corrections"][label] = dict(
                training={key: statistics.mean(r[key] for r in train) for key in EXPOSURE},
                training_first2_max=max(r["correction_max"] for r in train[:2]),
                training_last32={key: statistics.mean(r[key] for r in train[-32:]) for key in EXPOSURE},
            )
            assert reading["corrections"][label]["training_first2_max"] == 0
        checks = []
        for e, row in enumerate(final):
            assert row["arm"] == arm and row["master"] == master and row["episode"] == e
            assert row["reset_seed"] == 1970002000 + e and row["channel_seed"] == 1970007000 + e
            assert row["motion_seed"] == 1970003000 + e
            check = read_trace(row, arm, calibration)
            close(np.exp(check["log_std"]), cell["inherited_sigma"], 2e-7)
            close(check["log_std"], parent["actor"]["log_std"], 0)
            checks.append(check)
            raw_bytes += Path(row["raw"]).stat().st_size
            connected_bytes += check["connected_bits_bytes"]
        witnesses = [(c["initial_scene_sha256"], c["channel_sha256"], c["user_positions_sha256"], c["innovation_sha256"])
                     for c in checks]
        if reference is None:
            reference = witnesses
        else:
            assert reference == witnesses
        panels[(master, arm)] = [dict(row, **check["levels"]) for row, check in zip(final, checks)]
        reading["raw_checks"][label] = checks
        reading["levels"][label] = {metric: statistics.mean(c["levels"][metric] for c in checks) for metric in METRICS}
        reading["levels"][label]["motion_path_m_per_uav"] = statistics.mean(c["motion_path_m_per_uav"] for c in checks)
        mean = np.mean([c["correction_mean"] for c in checks], axis=0)
        second = np.mean([c["correction_second_moment"] for c in checks], axis=0)
        reading["corrections"].setdefault(label, {})["evaluation"] = dict(
            {key: statistics.mean(c["residual"][key] for c in checks) for key in EXPOSURE},
            coordinate_mean=mean.tolist(), coordinate_std=np.sqrt(np.maximum(second - mean ** 2, 0)).tolist(),
        )
        reading["per_cell_resources"][label] = dict(cell["resources"], wall_seconds=cell["finished_wall"] - cell["started_wall"])
    reading["contrasts"]["D-K"] = {
        metric: contrast({m: panels[(m, "D")] for m in MASTERS}, {m: panels[(m, "K")] for m in MASTERS}, metric)
        for metric in METRICS}
    for arm in ARMS:
        reading["versus_B40"][arm] = {
            metric: contrast({m: panels[(m, arm)] for m in MASTERS}, {m: panels[(19451, "B40")] for m in MASTERS}, metric)
            for metric in METRICS}
    assert connected_bytes == 2867200
    reading.update(all_checks_passed=True, trajectories_read=224, raw_trace_bytes=raw_bytes,
                   connected_bits_uncompressed_bytes=connected_bytes,
                   initial_common_hashes_by_block={str(k): v for k, v in initial_critics.items()})
    return reading


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--parent", type=Path)
    args = parser.parse_args()
    result = read_run(args.run, args.parent)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("all_checks_passed", "trajectories_read", "actual")}, allow_nan=False))


if __name__ == "__main__":
    main()
