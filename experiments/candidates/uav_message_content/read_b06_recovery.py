"""Read complete B06 endpoint coverage across the interrupted and recovery operations."""

import argparse
import json
from pathlib import Path
import statistics
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.uav_message_content import read_b06 as frozen


D_EPISODES_SHA = "1175cd06203221d98aa19a427b1f66c013b29d9aad8bf021563f204725bf79e8"
D_UPDATES_SHA = "b440d6f54e2b668c07de44e7255cf834d13ca7e7898365cdc87d9e7565d2f10f"


def read_json(path):
    return json.loads(Path(path).read_text())


def stream(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def join_panel(original, recovered, master, arm):
    """Validate the frozen disjoint partition, without synthesizing an original result."""
    is_d = (master, arm) == (19703, "D")
    old_indices = list(range(9 if is_d else (0 if arm == "B40" else 32)))
    new_indices = list(range(9, 32)) if is_d else (list(range(32)) if arm == "B40" else [])
    for rows, expected in ((original, old_indices), (recovered, new_indices)):
        assert [row["episode"] for row in rows] == expected, "evaluation partition differs"
        for row in rows:
            e = row["episode"]
            assert (row["master"], row["arm"], row["phase"]) == (master, arm, "final_eval")
            assert (row["reset_seed"], row["channel_seed"], row["motion_seed"]) == (
                1970002000 + e, 1970007000 + e, 1970003000 + e)
    combined = original + recovered
    assert len(combined) == 32
    return combined


def verify_evaluation_stream(cell):
    """The recovery has no training/update stream, including its partial D panel."""
    directory = Path(cell["directory"])
    episode_path, update_path = directory / "episodes.jsonl", directory / "updates.jsonl"
    assert frozen.digest(episode_path) == cell["episode_stream_sha256"]
    rows = stream(episode_path)
    assert rows == cell["rows"] and all(r["phase"] == "final_eval" for r in rows)
    assert cell["counts"]["delivered_packets"] == sum(r["delivered_packets"] for r in rows)
    assert cell["counts"]["censored_packets"] == sum(r["pending_at_end"] for r in rows)
    assert frozen.digest(update_path) == cell["update_stream_sha256"] and update_path.read_bytes() == b""
    return dict(episodes=len(rows), updates=0, episode_sha256=cell["episode_stream_sha256"],
                update_sha256=cell["update_stream_sha256"])


def verify_config(path, summary, bound):
    assert frozen.digest(path) == summary["config_sha256"]
    config = read_json(path)
    expected = dict(seed=19701, launch_sha=summary["launch_sha"], horizon=256, dtype="float32", device="cpu",
                    node="local_linux", torch_threads=1, torch_interop_threads=1, blas_threads=1,
                    deployment="sampled_composed_policy", eval_world_base=1970002000,
                    eval_channel_base=1970007000, eval_motion_base=1970003000,
                    d_episodes=list(range(9, 32)), b40_episodes=list(range(32)),
                    parent_checkpoint=bound["checkpoint_input"],
                    d_checkpoint=bound["unfinished_d"]["final_checkpoint"], original=bound["original"],
                    cpu_limit_seconds=600, optimizer_constructed=False, automatic_retry=False)
    assert config == expected, "recovery fixed configuration differs"
    return summary["config_sha256"]


def read_run(original, recovery, parent=None):
    import torch
    from experiments.candidates.uav_message_content.b06 import recovery as recovery_code

    original, recovery = Path(original).resolve(), Path(recovery).resolve()
    original_batch = read_json(original / "summary.json")
    parent = Path(parent or original_batch["warm_start"]["path"])
    bound = recovery_code.load_original_bindings(original, parent)
    summary = read_json(recovery / "summary.json")
    coverage = recovery_code.validate_recovery(summary, bound)
    config_sha = verify_config(recovery / "config.json", summary, bound)
    assert summary["original_inventory_after"] == bound["original"]["inventory"]
    old_manifest = read_json(original / "launch-manifest.json")
    manifest = read_json(recovery / "launch-manifest.json")
    old_exit = read_json(original / "process-exit.json")
    witness = read_json(recovery / "process-exit.json")
    assert original_batch["status"] == "INCOMPLETE" and old_exit["exit_code"] == -15
    assert summary["status"] == "COMPLETE" and not summary["limits"] and witness["exit_code"] == 0
    assert summary["launch_sha"] == manifest["sha"]
    assert Path(manifest["output_root"]).resolve() == recovery
    for native in (old_manifest, manifest):
        assert native["node"] == "local_linux" and native["direction"] == "uav_message_content"
        assert native["lead"] == "Codex DM (native child)"
    assert old_manifest["sha"] == original_batch["source_sha"]
    assert frozen.digest(parent) == frozen.BOUND_SHA and parent.stat().st_size == 463357
    _, parent_arrays = frozen.checkpoint_arrays(parent)

    cells = bound["cells"]
    recovered_d, b40 = summary["recovered_d"], summary["b40"]
    assert Path(recovered_d["directory"]).resolve() == recovery / "19703/D"
    assert Path(b40["directory"]).resolve() == recovery / "B40"
    recovery_streams = {"19703/D": verify_evaluation_stream(recovered_d), "B40": verify_evaluation_stream(b40)}
    assert [(c["master"], c["arm"]) for c in cells] == [(m, a) for m in frozen.MASTERS for a in frozen.ARMS]
    original_actual = {key: sum(c["counts"][key] for c in cells) for key in cells[0]["counts"]}
    assert original_actual["team_steps"] == 829696 and original_actual["final_eval_episodes"] == 169
    actual = {key: original_actual[key] + summary["actual"][key] for key in original_actual}
    assert actual["team_steps"] == 843776 and actual["fit_started"] == 6
    assert actual["final_eval_episodes"] == 224 and actual["train_episodes"] == 3072
    assert actual["actor_optimizer_steps"] == actual["critic_optimizer_steps"] == 6144
    assert actual["constructors"] == 8  # Six original, one replacement D environment, one B40.
    reading = dict(
        status="COMPLETE_ENDPOINT_COVERAGE", all_checks_passed=False,
        original_operation_status="INTERRUPTED_BY_OWNER", original_exit_code=-15,
        original_source_sha=old_manifest["sha"], recovery_source_sha=manifest["sha"],
        original_manifest_sha256=frozen.digest(original / "launch-manifest.json"),
        recovery_manifest_sha256=frozen.digest(recovery / "launch-manifest.json"),
        original_operation_ref=old_manifest["operation_ref"], recovery_operation_ref=manifest["operation_ref"],
        original_summary_sha256=frozen.digest(original / "summary.json"),
        recovery_summary_sha256=frozen.digest(recovery / "summary.json"),
        original_binding=summary["original"], coverage=coverage,
        recovery_stream_checks=recovery_streams, recovery_config_sha256=config_sha,
        reader_sha256=frozen.digest(__file__),
        inherited_reader_sha256=frozen.digest(Path(frozen.__file__)),
        original_actual=original_actual, recovery_actual=summary["actual"], actual=actual,
        original_persisted_native_steps=829696, recovery_native_steps=14080,
        total_persisted_native_steps=843776, original_unpersisted_native_steps=[0, 256],
        policy_fits=6, trained_predictor_instances=0, recovery_policy_fits=0,
        native_steps_added_by_reader=0, optimizer_calls_added_by_reader=0, model_or_policy_calls_added=0,
        levels={}, raw_checks={}, checkpoint_checks={}, update_checks={}, exposure={}, corrections={},
        per_cell_resources={}, contrasts={}, versus_B40={}, warm_start=original_batch["warm_start"],
        resources=dict(original_batch=None, original_sixth_cell=None,
                       recovery=summary["resources"],
                       missing="Owner SIGTERM bypassed original sixth-cell and batch resource finalizers."),
        limitations=[
            "The original operation remains interrupted; only endpoint coverage is now complete across two operations.",
            "Up to256 unpersisted original world9 steps remain additional exposure; recovery creates no new learning replicate.",
            "Three continuation pairs condition on one selected parent and a common panel, not independent parents.",
            "Training df2 uncertainty differs from fixed-endpoint world df31 uncertainty;96 rows are not96 training runs.",
            "One sampled action stream per scene/channel tuple does not measure within-scene stochastic-policy risk.",
            "D-K compares finite representation/optimization packages, not causal state-information use.",
            "K's whole policy still uses recurrent state and legal messages; only its learned three-vector is constant.",
            "The40-byte abstract contract retains old28-byte fees/delays, not measured physical-network bandwidth.",
            "Correction variation is exposure, not useful coordination; path/altitude are not physical safety.",
        ],
    )
    panels, train_bindings, initial_critics = {}, {}, {}
    reference = None
    raw_bytes = connected_bytes = 0
    base_hash = b40["initial_tensor_sha256"]["base_actor"]
    for cell in cells + [b40]:
        master, arm = cell["master"], cell["arm"]
        label = "B40" if arm == "B40" else f"{master}/{arm}"
        interrupted = (master, arm) == (19703, "D")
        assert cell["status"] == ("INCOMPLETE" if interrupted else "COMPLETE") and not cell["limits"]
        episode_path = Path(cell["directory"]) / "episodes.jsonl"
        assert frozen.digest(episode_path) == (D_EPISODES_SHA if interrupted else cell["episode_stream_sha256"])
        episodes = stream(episode_path)
        train = [r for r in episodes if r["phase"] == "train"]
        own_final = [r for r in episodes if r["phase"] == "final_eval"]
        assert len(train) == (0 if arm == "B40" else 512)
        assert len(episodes) == len(train) + len(own_final) and own_final == cell["rows"]
        assert cell["counts"]["delivered_packets"] == sum(r["delivered_packets"] for r in episodes)
        assert cell["counts"]["censored_packets"] == sum(r["pending_at_end"] for r in episodes)
        if interrupted:
            assert recovered_d["initial_tensor_sha256"] == cell["final_tensor_sha256"]
            assert recovered_d["after_eval_tensor_sha256"] == recovered_d["initial_tensor_sha256"]
            final = join_panel(own_final, recovered_d["rows"], master, arm)
            counts = {key: cell["counts"][key] + recovered_d["counts"][key] for key in cell["counts"]}
            # Supplemental witnesses are explicit and in memory only. Original summaries stay untouched.
            checkpoint_view = dict(cell, after_eval_tensor_sha256=recovered_d["after_eval_tensor_sha256"],
                                   update_stream_sha256=D_UPDATES_SHA)
            reading["per_cell_resources"][label] = dict(original=None, recovery=recovered_d["resources"])
        else:
            final = join_panel([] if arm == "B40" else own_final,
                               own_final if arm == "B40" else [], master, arm)
            counts, checkpoint_view = cell["counts"], cell
            reading["per_cell_resources"][label] = dict(cell["resources"],
                wall_seconds=cell["finished_wall"] - cell["started_wall"])
        for key, expected in frozen.expected_counts(arm).items():
            assert counts[key] == expected + int(interrupted and key == "constructors"), (label, key)
        assert counts["delivered_packets"] + counts["censored_packets"] == counts["team_steps"]
        assert cell["initial_tensor_sha256"]["base_actor"] == cell["final_tensor_sha256"]["base_actor"] == base_hash
        assert checkpoint_view["after_eval_tensor_sha256"] == cell["final_tensor_sha256"]
        training_rng = torch.Generator().manual_seed(100000 * master + 21)
        for e, row in enumerate(train):
            assert (row["arm"], row["master"], row["episode"]) == (arm, master, e)
            assert row["reset_seed"] == 100000 * master + 1000 + e
            assert row["channel_seed"] == 100000 * master + 6000 + e and row["motion_seed"] == 100000 * master + 21
            assert row["steps"] == row["attempts"] == row["accepted_packets"] == 256
            assert row["collided_attempts"] == 0 and row["correction_max"] <= .1 + 1e-7
            frozen.close(row["J_physical"], .014 * row["served_users_per_tick"] + .3 * row["Q"])
            frozen.close(row["J_net"], row["J_physical"] - .001)
            frozen.verify_innovations(row, training_rng)
        calibration = None
        if arm != "B40":
            witnesses = [(r["initial_scene_sha256"], r["channel_sequence_sha256"], r["innovation_sha256"],
                          r["motion_rng_start_sha256"], r["motion_rng_end_sha256"]) for r in train]
            critic_hashes = {key: cell["initial_tensor_sha256"][key] for key in ("base_actor", "critic_old", "critic_forecast")}
            if master in train_bindings:
                assert witnesses == train_bindings[master] and critic_hashes == initial_critics[master]
            else:
                train_bindings[master], initial_critics[master] = witnesses, critic_hashes
            assert cell["initial_optimizer_state_entries"] == [0, 0]
            assert cell["actual_optimizer_lrs"] == ([.003, .0003] if arm == "K" else [.0003, .0003])
            reading["checkpoint_checks"][label] = frozen.read_checkpoints(checkpoint_view, parent_arrays)
            calibration = reading["checkpoint_checks"][label]["final_calibration_b"]
            reading["update_checks"][label] = frozen.read_updates(checkpoint_view)
            reading["exposure"][label] = cell["exposure"]
            reading["corrections"][label] = dict(
                training={key: statistics.mean(r[key] for r in train) for key in frozen.EXPOSURE},
                training_first2_max=max(r["correction_max"] for r in train[:2]),
                training_last32={key: statistics.mean(r[key] for r in train[-32:]) for key in frozen.EXPOSURE})
            assert reading["corrections"][label]["training_first2_max"] == 0
        checks = []
        for e, row in enumerate(final):
            evidence_root = recovery if arm == "B40" or (interrupted and e >= 9) else original
            assert Path(row["raw"]).resolve().is_relative_to(evidence_root)
            check = frozen.read_trace(row, arm, calibration)
            frozen.close(np.exp(check["log_std"]), cell["inherited_sigma"], 2e-7)
            frozen.close(check["log_std"], parent_arrays["actor"]["log_std"], 0)
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
        reading["levels"][label] = {metric: statistics.mean(c["levels"][metric] for c in checks) for metric in frozen.METRICS}
        reading["levels"][label]["motion_path_m_per_uav"] = statistics.mean(c["motion_path_m_per_uav"] for c in checks)
        mean = np.mean([c["correction_mean"] for c in checks], axis=0)
        second = np.mean([c["correction_second_moment"] for c in checks], axis=0)
        reading["corrections"].setdefault(label, {})["evaluation"] = dict(
            {key: statistics.mean(c["residual"][key] for c in checks) for key in frozen.EXPOSURE},
            coordinate_mean=mean.tolist(), coordinate_std=np.sqrt(np.maximum(second - mean ** 2, 0)).tolist())
    reading["contrasts"]["D-K"] = {
        metric: frozen.contrast({m: panels[(m, "D")] for m in frozen.MASTERS},
                                {m: panels[(m, "K")] for m in frozen.MASTERS}, metric)
        for metric in frozen.METRICS}
    for arm in frozen.ARMS:
        reading["versus_B40"][arm] = {
            metric: frozen.contrast({m: panels[(m, arm)] for m in frozen.MASTERS},
                                    {m: panels[(19451, "B40")] for m in frozen.MASTERS}, metric)
            for metric in frozen.METRICS}
    assert connected_bytes == 2867200
    reading.update(all_checks_passed=True, trajectories_read=224, original_trajectories=169,
                   recovery_trajectories=55, raw_trace_bytes=raw_bytes,
                   connected_bits_uncompressed_bytes=connected_bytes,
                   initial_common_hashes_by_block={str(k): v for k, v in initial_critics.items()})
    return reading


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--recovery", type=Path, required=True)
    parser.add_argument("--parent", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("refusing to overwrite a recovery reading")
    result = read_run(args.original, args.recovery, args.parent)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: result[key] for key in ("status", "all_checks_passed", "trajectories_read", "actual")}))


if __name__ == "__main__":
    main()
