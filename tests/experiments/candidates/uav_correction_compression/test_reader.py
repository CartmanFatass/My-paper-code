"""Checks of fixed-world inference and evidence-corruption detection, without native episodes."""

import json
from pathlib import Path

import numpy as np
import pytest

from experiments.candidates.uav_correction_compression import read_b01 as reader


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n")


def test_non_significance_does_not_imply_retention():
    values = [(-1) ** i * .05 for i in range(32)]
    statistic = reader.interval(values)
    assert statistic["descriptive_t95"][0] < 0 < statistic["descriptive_t95"][1]
    assert not reader.retention({"J_net": statistic, "served_users_per_tick": reader.interval([0.] * 32)})[
        "mean_retention_pass"]


def test_retention_strict_and_both_endpoints_required():
    assert not reader.retention({"J_net": reader.interval([-.001] * 32),
                                 "served_users_per_tick": reader.interval([0.] * 32)})["mean_retention_pass"]
    assert not reader.retention({"J_net": reader.interval([0.] * 32),
                                 "served_users_per_tick": reader.interval([-.1] * 32)})["mean_retention_pass"]
    assert reader.retention({"J_net": reader.interval([-.0005] * 32),
                             "served_users_per_tick": reader.interval([-.05] * 32)})["mean_retention_pass"]
    with pytest.raises(AssertionError):
        reader.interval([0.] * 96)


def test_tail_direction_is_explicit():
    a = [{"zero_service_steps": 3, "worst_tick_service": 3} for _ in range(32)]
    b = [{"zero_service_steps": 1, "worst_tick_service": 1} for _ in range(32)]
    assert reader.contrast(a, b, "zero_service_steps")["adverse_worlds"] == list(range(32))
    assert reader.contrast(a, b, "worst_tick_service")["adverse_worlds"] == []


def counts():
    return dict(constructors=1, explicit_resets=32, train_episodes=0, final_eval_episodes=32,
                train_team_steps=0, final_eval_team_steps=8192, team_steps=8192, native_step_calls=8192,
                motion_samples=40960, broadcasts=8192, attempts=8192, fit_started=0, rollouts=0,
                optimizer_steps=0, actor_optimizer_steps=0, critic_optimizer_steps=0,
                replayed_actor_rows=0, evaluation_optimizer_steps=0, diagnostic_forward_calls=0,
                behavior_actor_forward_calls=8192, behavior_actor_forward_rows=40960,
                behavior_critic_forward_calls=0, behavior_critic_forward_rows=0,
                ppo_actor_forward_calls=0, ppo_actor_forward_rows=0,
                ppo_critic_forward_calls=0, ppo_critic_forward_rows=0,
                delivered_packets=8128, censored_packets=64)


@pytest.fixture
def evidence(tmp_path, monkeypatch):
    inputs = json.loads(Path(reader.__file__).with_name("b01_inputs.json").read_text())
    input_file = tmp_path / "inputs-source.json"
    write(input_file, inputs)
    root = tmp_path / "run"
    root.mkdir()
    cells = []
    assets = {a["master"]: a for a in inputs["assets"]}
    for arm in reader.ARMS:
        master = 19451 if arm == "B40" else int(arm[1:])
        rows = []
        for world in inputs["worlds"]:
            w = world["world"]
            raw = root / arm / "raw" / f"final_{w:02d}.npz"
            raw.parent.mkdir(parents=True, exist_ok=True)
            constant = np.asarray(assets[master]["constant_float32"] if arm.startswith("C") else [0, 0, 0],
                                  dtype=np.float32)
            np.savez(raw, log_std=np.zeros(3, dtype=np.float32),
                     correction=np.broadcast_to(constant, (256, 5, 3)), served_users=np.ones(256))
            timing = {"actor_forward": dict(calls=256, wall_ns=100, process_cpu_ns=90),
                      "episode_loop": dict(wall_ns=200, process_cpu_ns=190)}
            rows.append(dict(arm=arm, master=master, phase="final_eval", world=w, episode=w, steps=256,
                reset_seed=world["scene_seed"], channel_seed=world["channel_seed"], motion_seed=world["motion_seed"],
                raw=f"{arm}/raw/final_{w:02d}.npz", raw_sha256=reader.digest(raw), charge_per_tick=.001,
                raw_bytes=raw.stat().st_size,
                initial_scene_sha256=f"scene{w}", channel_sequence_sha256=f"channel{w}",
                innovation_sha256=f"innovation{w}", motion_rng_start_sha256=f"start{w}",
                motion_rng_end_sha256=f"end{w}", action_sequence_sha256=f"action{arm}{w}", timing=timing))
        stream = root / arm / "episodes.jsonl"
        stream.write_text("".join(json.dumps(r) + "\n" for r in rows))
        cells.append(dict(arm=arm, master=master, directory=arm, rows=rows, counts=counts(),
                          status="COMPLETE", launch_sha="source", actor_trainable_parameters=0,
                          parameter_displacement=0., raw_bytes=sum(r["raw_bytes"] for r in rows),
                          timing={"json_output": {}},
                          initial_tensor_sha256={"state": arm}, final_tensor_sha256={"state": arm},
                          frozen_equal=True, episode_stream_sha256=reader.digest(stream), log_std=[0., 0., 0.],
                          constant_float32=assets[master]["constant_float32"] if arm.startswith("C") else None))
    total = {k: sum(c["counts"][k] for c in cells) for k in counts()}
    config = dict(horizon=256, final_eval=32, arms=list(reader.ARMS), fits=0, optimizer_updates=0,
                  device="cpu", dtype="float32", inputs_sha256=reader.digest(input_file),
                  torch_threads=1, torch_interop_threads=1,
                  blas_threads=dict(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1"),
                  launch_sha="source", seed=19801, inputs=inputs)
    summary = dict(object="UAV-CORRECTION-COMPRESSION-B01", status="COMPLETE", launch_sha="source",
                   seed=19801, inputs_sha256=reader.digest(input_file), configuration={}, checkpoint_bindings={},
                   cells=cells, actual=total, limits=[], resources={}, timing={}, timing_scope={},
                   arm_order=[dict(world=w, arms=list(reader.ARMS[w % 7:] + reader.ARMS[:w % 7])) for w in range(32)])
    write(root / "summary.json", summary)
    for cell in cells:
        write(root / cell["arm"] / "summary.json", cell)
    write(root / "config.json", config)
    write(root / "inputs.json", inputs)
    write(root / "launch-manifest.json", dict(sha="source", direction="uav_correction_compression",
                                             lead="Codex DM (native child)", node="wsl_4070"))
    write(root / "process-exit.json", dict(status="exited", exit_code=0))

    def reconstructed(row, arm):
        assert reader.digest(row["raw"]) == row["raw_sha256"]
        levels = {m: 1. for m in reader.METRICS if m != "motion_path_m_per_uav"}
        levels["zero_service_steps"] = levels["longest_zero_service"] = 0
        return dict(levels=levels, motion_path_m_per_uav=1., correction_mean=[0, 0, 0],
                    correction_std=[0, 0, 0], correction_second_moment=[0, 0, 0], density_max_abs_error=0.)

    monkeypatch.setattr(reader, "read_trace", reconstructed)
    return root, input_file, summary


def test_complete_reader_counts_world_units_and_zero_effect(evidence):
    root, inputs, _ = evidence
    result = reader.read_run(root, inputs_path=inputs)
    assert result["all_checks_passed"] and result["all_three_mean_retention_pass"]
    assert result["trajectories_read"] == 224 and result["actual"]["team_steps"] == 57344
    assert result["fixed_three_asset_average"]["C-D"]["J_net"]["paired_worlds"] == 32


@pytest.mark.parametrize("corruption", ["partial", "updates", "changed_tensor", "mismatched_stream", "changed_constant"])
def test_reader_rejects_corrupt_evidence(evidence, corruption):
    root, inputs, summary = evidence
    cell = summary["cells"][1]
    if corruption == "partial":
        summary["status"] = "INCOMPLETE"
    elif corruption == "updates":
        summary["actual"]["optimizer_steps"] = 1
    elif corruption == "changed_tensor":
        cell["final_tensor_sha256"] = {"state": "changed"}
    elif corruption == "mismatched_stream":
        cell["rows"][0]["motion_seed"] += 1
    elif corruption == "changed_constant":
        cell["constant_float32"][0] += .01
    write(root / "summary.json", summary)
    with pytest.raises(AssertionError):
        reader.read_run(root, inputs_path=inputs)
