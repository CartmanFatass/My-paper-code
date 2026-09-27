"""Independent-seed SET runner contract on short, non-scientific worlds."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
import torch

from experiments.candidates.energy_relay_baselines.b01 import configuration as cfg
from experiments.candidates.energy_relay_baselines.b01 import evaluation as ev
from experiments.candidates.energy_relay_baselines.b01 import run as entry
from experiments.candidates.energy_relay_baselines.b01 import training as tr
from experiments.candidates.energy_relay_benchmark.b02 import configuration as b02
from experiments.candidates.energy_relay_benchmark.b02 import training as b02_training
from experiments.candidates.energy_relay_benchmark.b01 import evaluation as benchmark_ev
from experiments.candidates.uav_service_auxiliary.b01.native import (
    initialization_fingerprint, optimizer_steps, sha256_file,
)

TEST_WORLDS = (317811, 317812)
TEST_SHA = "test-source-sha"


def tiny_spec(seed=cfg.TRAINING_SEEDS[0]):
    return replace(b02.B02Spec(seed=seed), rollouts=2, rollout_length=20,
                   episode_length=20, checkpoint_every_transitions=40)


def test_production_recipe_parity_and_real_seed_isolation(tmp_path):
    assert tr.collect_and_train is b02_training.collect_and_train
    assert tr.new_agent is b02_training.new_agent
    assert ev.WorldTask is benchmark_ev.WorldTask
    assert ev.run_tasks is benchmark_ev.run_tasks
    assert ev.aggregate is benchmark_ev.aggregate
    assert ev.trace_arrays is benchmark_ev.trace_arrays
    assert b02.checkpoint_rollouts(cfg.production_spec(cfg.TRAINING_SEEDS[0])) == \
        (34, 67, 100, 134, 167, 200)
    first, second = (cfg.production_spec(seed) for seed in cfg.TRAINING_SEEDS)
    first_config, second_config = b02.make_b02_config(first), b02.make_b02_config(second)
    expected = b02.config_dict(first_config)
    expected["seed"] = second.seed
    assert b02.config_dict(second_config) == expected
    fingerprints = []
    torch.set_num_threads(1)
    for index, seed in enumerate((first.seed, second.seed, first.seed)):
        agent, identity = tr.new_agent(b02.make_b02_config(b02.B02Spec(seed=seed)),
                                       device=torch.device("cpu"),
                                       log_dir=tmp_path / f"logs-{index}", seed=seed)
        assert identity["policy_fingerprint"] == initialization_fingerprint(agent)
        fingerprints.append(identity["policy_fingerprint"])
    assert fingerprints[0] != fingerprints[1]
    assert fingerprints[0] == fingerprints[2]


@pytest.fixture(scope="module")
def fit(tmp_path_factory):
    spec = tiny_spec()
    out = tmp_path_factory.mktemp("baseline-fit") / f"seed-{spec.seed}"
    summary = tr.run_training(out=out, spec=spec, launch_sha=TEST_SHA,
                              device_name="cpu", threads=2, argv=["test"])
    return out, spec, summary


def test_short_native_fit_and_evaluation_roundtrip(fit, tmp_path):
    out, spec, summary = fit
    assert summary["status"] == "COMPLETE"
    assert summary["counts"]["transitions"] == 80
    assert summary["counts"]["checkpoints"] == 3
    assert summary["initial_fingerprint"] != summary["final_fingerprint"]
    assert summary["fingerprint_changed"]
    assert summary["optimizer_steps"]["low_actor"] > 0
    assert summary["optimizer_steps"]["low_critic"] > 0
    assert summary["checkpoint_rollouts"] == [1, 2]
    assert [summary["checkpoints"][name]["transitions"] for name in
            ("c00", "c01", "c02")] == [0, 40, 80]
    run_config = json.loads((out / "config.json").read_text())
    assert run_config["object_id"] == cfg.OBJECT_ID
    assert run_config["direction"] == cfg.DIRECTION
    progress = [json.loads(line) for line in (out / "progress.jsonl").read_text().splitlines()]
    assert [row["event"]["event"] for row in progress].count("rollout") == 2
    assert [row["event"]["event"] for row in progress].count("checkpoint") == 3
    assert progress[-1]["event"]["status"] == "COMPLETE"

    for label in ("c00", "c02"):
        root = out / "checkpoints" / label
        record = json.loads((root / "record.json").read_text())
        assert record["object_id"] == cfg.OBJECT_ID
        assert record["direction"] == cfg.DIRECTION
        assert record["agent_pt_sha256"] == sha256_file(root / "agent.pt")
        agent, _ = tr.new_agent(b02.make_b02_config(spec), device=torch.device("cpu"),
                                log_dir=tmp_path / f"restore-{label}", seed=spec.seed)
        agent.load_model(str(root / "agent.pt"))
        assert initialization_fingerprint(agent) == record["policy_fingerprint"]
        assert optimizer_steps(agent) == record["optimizer_steps"]

    # The production wrapper selects c06; a short internal spec ends at c02.
    # A copy named c06 with an internally consistent endpoint record tests the same path.
    short = tmp_path / "short" / f"seed-{spec.seed}"
    shutil.copytree(out, short, copy_function=os.link)
    root = short / "checkpoints" / "c06"
    shutil.copytree(short / "checkpoints" / "c02", root, copy_function=os.link)
    record = json.loads((root / "record.json").read_text())
    record["checkpoint"] = "c06"
    (root / "record.json").unlink()
    (root / "record.json").write_text(json.dumps(record))
    saved = json.loads((short / "summary.json").read_text())
    saved["checkpoints"]["c06"] = saved["checkpoints"]["c02"]
    (short / "summary.json").unlink()
    (short / "summary.json").write_text(json.dumps(saved))
    results = []
    for label in ("first", "again"):
        external = tmp_path / label / "external-artifact"
        shutil.copytree(short / "checkpoints" / "c00", external / "c00",
                        copy_function=os.link)
        shutil.copytree(short / "checkpoints" / "c06", external / "c06",
                        copy_function=os.link)
        assert not (external / "config.json").exists()
        eval_out = tmp_path / label / "eval-c06" / f"seed-{spec.seed}"
        eval_out.parent.mkdir()
        if label == "first":
            initial_out = tmp_path / label / "eval-c00" / f"seed-{spec.seed}"
            initial_out.parent.mkdir()
            initial = ev.evaluate_checkpoint(
                checkpoint_dir=external / "c00", out=initial_out, spec=spec,
                launch_sha=TEST_SHA, worlds=TEST_WORLDS, expected_worlds=TEST_WORLDS,
                expected_checkpoint_sha256=saved["checkpoints"]["c00"]["agent_pt_sha256"],
                expected_source_sha=TEST_SHA,
                workers=1, threads=1, horizon=30, device_name="cpu", argv=["test"])
            assert initial["status"] == "COMPLETE"
            assert initial["counts"]["new_optimizer_updates"] == 0
            assert initial["record_optimizer_steps"]["low_actor"] == 0
            assert (initial_out / "checkpoint-eval" / "panels" /
                    "L_c00_deterministic_e0.00_x0.05.json").is_file()
        summary = ev.evaluate_checkpoint(
            checkpoint_dir=external / "c06", out=eval_out, spec=spec,
            launch_sha=TEST_SHA, worlds=TEST_WORLDS, expected_worlds=TEST_WORLDS,
            expected_checkpoint_sha256=record["agent_pt_sha256"],
            expected_source_sha=TEST_SHA,
            workers=1, threads=1, horizon=30, device_name="cpu", argv=["test"])
        assert summary["status"] == "COMPLETE"
        assert summary["counts"]["episodes_completed"] == 4
        assert summary["counts"]["new_optimizer_updates"] == 0
        assert summary["record_optimizer_steps"] == record["optimizer_steps"]
        for mode in cfg.MODES:
            name = f"L_c06_{mode}_e0.00_x0.05"
            panel_path = eval_out / "checkpoint-eval" / "panels" / f"{name}.json"
            trace_path = eval_out / "checkpoint-eval" / "traces" / f"{name}.npz"
            assert panel_path.is_file() and trace_path.is_file()
            assert summary["artifacts"][str(panel_path.relative_to(eval_out / "checkpoint-eval"))] == \
                sha256_file(panel_path)
        results.append(json.loads((eval_out / "checkpoint-eval" / "panels" /
                                   "L_c06_stochastic_e0.00_x0.05.json").read_text()))
    volatile = {"wall_seconds", "worker_peak_rss_kib"}
    clean = lambda rows: [{key: value for key, value in row.items() if key not in volatile}
                          for row in rows]
    assert clean(results[0]["worlds"]) == clean(results[1]["worlds"])


def _copy_fit(fit, tmp_path):
    out, spec, _ = fit
    copy = tmp_path / f"seed-{spec.seed}"
    shutil.copytree(out, copy, copy_function=os.link)
    root = copy / "checkpoints" / "c06"
    shutil.copytree(copy / "checkpoints" / "c02", root, copy_function=os.link)
    record = json.loads((root / "record.json").read_text())
    record["checkpoint"] = "c06"
    (root / "record.json").unlink()
    (root / "record.json").write_text(json.dumps(record))
    saved = json.loads((copy / "summary.json").read_text())
    saved["checkpoints"]["c06"] = saved["checkpoints"]["c02"]
    (copy / "summary.json").unlink()
    (copy / "summary.json").write_text(json.dumps(saved))
    return copy, spec


@pytest.mark.parametrize("mutation", [
    "object", "direction", "seed", "config", "sha", "bytes", "fingerprint",
    "schedule", "checkpoint", "source", "declared_sha", "declared_source",
])
def test_rejections_before_evaluation_output(fit, tmp_path, mutation):
    out, spec = _copy_fit(fit, tmp_path)
    eval_out = tmp_path / "evaluation"
    root = out / "checkpoints" / "c06"
    record_path = root / "record.json"
    record = json.loads(record_path.read_text())
    if mutation == "object":
        record["object_id"] = "ENERGY-RELAY-BENCHMARK-B02"
    elif mutation == "direction":
        record["direction"] = "energy_relay_benchmark"
    elif mutation == "seed":
        record["training_seed"] += 1
    elif mutation == "config":
        record["config"]["gamma"] = 0.5
    elif mutation == "sha":
        record["agent_pt_sha256"] = "0" * 64
    elif mutation == "bytes":
        agent_pt = root / "agent.pt"
        original = agent_pt.read_bytes()
        agent_pt.unlink()
        agent_pt.write_bytes(original + b"X")
    elif mutation == "fingerprint":
        record["policy_fingerprint"] = "0" * 64
    elif mutation == "schedule":
        record["rollout"] = 1
    elif mutation == "checkpoint":
        record["checkpoint"] = "c05"
    elif mutation == "source":
        record["launch_sha"] = "other-source"
    record_path.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        ev.evaluate_checkpoint(checkpoint_dir=root, out=eval_out, spec=spec,
                               launch_sha=TEST_SHA, worlds=TEST_WORLDS,
                               expected_worlds=TEST_WORLDS, horizon=30,
                               expected_checkpoint_sha256=("0" * 64 if mutation == "declared_sha"
                                   else fit[2]["checkpoints"]["c02"]["agent_pt_sha256"]),
                               expected_source_sha=("wrong-source" if mutation == "declared_source"
                                                    else TEST_SHA))
    assert not eval_out.exists()


def test_world_and_path_rejections_before_effects(fit, tmp_path):
    out, spec = _copy_fit(fit, tmp_path)
    eval_out = tmp_path / "evaluation"
    checksum = fit[2]["checkpoints"]["c02"]["agent_pt_sha256"]
    for worlds in ((955001,), tuple(reversed(cfg.DEVELOPMENT_WORLDS)),
                   (*cfg.DEVELOPMENT_WORLDS[:-1], 957001)):
        with pytest.raises(ValueError, match="world list"):
            ev.evaluate_checkpoint(checkpoint_dir=out / "checkpoints" / "c06",
                                   out=eval_out, spec=spec, launch_sha=TEST_SHA,
                                   expected_checkpoint_sha256=checksum,
                                   expected_source_sha=TEST_SHA,
                                   worlds=worlds)
    with pytest.raises(ValueError, match="owned c00 or c06"):
        ev.evaluate_checkpoint(checkpoint_dir=out / "checkpoints" / "c02",
                               out=eval_out, spec=spec, launch_sha=TEST_SHA,
                               expected_checkpoint_sha256=checksum,
                               expected_source_sha=TEST_SHA,
                               worlds=TEST_WORLDS, expected_worlds=TEST_WORLDS)
    assert not eval_out.exists()


def test_cli_requires_admission_and_owned_output(tmp_path):
    seed = cfg.TRAINING_SEEDS[0]
    target = tmp_path / "runs" / cfg.DIRECTION / "test" / f"seed-{seed}"
    assert entry.seed_output(str(target), seed) == target
    with pytest.raises(ValueError, match="--out"):
        entry.seed_output(str(tmp_path / "unowned" / f"seed-{seed}"), seed)
    completed = subprocess.run(
        [sys.executable, str(Path(entry.__file__)), "train", "--seed", str(seed),
         "--out", str(target), "--launch-sha", "0" * 40, "--device", "cpu"],
        capture_output=True, text=True, check=False)
    assert completed.returncode != 0
    assert "admission" in completed.stderr.lower()
    assert not target.exists()


def test_manifest_only_training_output_is_accepted(tmp_path, monkeypatch):
    spec = tiny_spec()
    out = tmp_path / f"seed-{spec.seed}"
    out.mkdir()
    (out / "launch-manifest.json").write_text("{}")

    def stop_after_config(*args, **kwargs):
        raise RuntimeError("stop before training for output admission test")

    monkeypatch.setattr(tr, "new_agent", stop_after_config)
    with pytest.raises(RuntimeError, match="stop before training"):
        tr.run_training(out=out, spec=spec, launch_sha=TEST_SHA,
                        device_name="cpu", threads=1, argv=["test"])
    assert (out / "launch-manifest.json").is_file()
    assert (out / "config.json").is_file()
    assert json.loads((out / "summary.json").read_text())["status"] == "INCOMPLETE"


def test_cli_routes_external_checkpoint_to_fresh_output(tmp_path, monkeypatch):
    from scripts import hmasd_admission

    seed = cfg.TRAINING_SEEDS[0]
    output = tmp_path / "runs" / cfg.DIRECTION / "eval-a" / f"seed-{seed}"
    checkpoint_dir = tmp_path / "external-artifact" / "c06"
    source_sha = "a" * 40
    checksum = "b" * 64
    monkeypatch.setattr(hmasd_admission, "require_admission",
                        lambda *args, **kwargs: {"sha": source_sha})
    seen = {}

    def fake_evaluate(**kwargs):
        seen.update(kwargs)

    monkeypatch.setattr(ev, "evaluate_checkpoint", fake_evaluate)
    assert entry.main(["evaluate", "--seed", str(seed), "--out", str(output),
                       "--launch-sha", source_sha, "--checkpoint-dir", str(checkpoint_dir),
                       "--checkpoint-sha256", checksum,
                       "--checkpoint-source-sha", "c" * 40]) == 0
    assert seen["checkpoint_dir"] == checkpoint_dir
    assert seen["out"] == output
    assert seen["expected_checkpoint_sha256"] == checksum
    assert seen["expected_source_sha"] == "c" * 40
    assert seen["threads"] == 2
    assert not output.exists()
