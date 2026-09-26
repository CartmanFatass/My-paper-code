import json
import os
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.controller_composition.b01.bindings import CHECKPOINT_ROOT, SOURCE
from experiments.candidates.controller_composition.b01.runner import validate_sources
from experiments.candidates.controller_composition.b02 import runner
from experiments.candidates.controller_composition.b02.reducer import reduce_panel


def _source_paths():
    override = os.environ.get("HMASD_CONTROLLER_COMPOSITION_CHECKPOINTS")
    if override:
        values = json.loads(override)
        assert len(values) == 3
        return dict(zip(SOURCE, map(Path, values)))
    return {i: Path(CHECKPOINT_ROOT) / row["tag"] / "F/raw/checkpoint_45.pt" for i, row in SOURCE.items()}


def test_native_bounded_fit_and_evaluation_cell(tmp_path):
    torch.set_num_threads(4)
    sources, _ = validate_sources(_source_paths())
    (tmp_path / "raw").mkdir()
    spec = replace(runner.SPEC, horizon=10, train_lanes=2, eval_lanes=2, rollouts=1)
    progress = {"completed_rollouts": []}
    fit, snapshot = runner._fit("F1", sources, np.random.default_rng(92_526_002),
                                tmp_path, "fixture-sha", progress, spec, world_base=81)
    assert fit["counts"]["team_steps"] == 20
    assert fit["optimizer_calls"]["discoverer_actor"] == 15
    assert fit["optimizer_calls"]["discoverer_critic"] == 15
    assert all(v == 0 for k, v in fit["optimizer_calls"].items()
               if k not in ("discoverer_actor", "discoverer_critic"))
    trace = np.load(tmp_path / "raw/train_F1_01.npz")
    assert trace["learner_raw"].shape == (10, 2, 3, 3)
    assert trace["partner_raw"].shape == (10, 2, 3, 3)
    assert np.array_equal(trace["executed"],
                          np.clip(np.concatenate((trace["learner_raw"], trace["partner_raw"]), axis=2), -1, 1))
    assert trace["env_returned"].all()
    assert fit["rollouts"][0]["world"]["reset_convention"].endswith("reset(seed=base+lane)")
    assert fit["rollouts"][0]["per_lane_J"] == pytest.approx(6 * trace["scalar_reward"].mean(axis=0))
    assert fit["rollouts"][0]["per_lane_J"] == pytest.approx(trace["total_reward"].mean(axis=0))
    assert fit["rollouts"][0]["per_lane_scalar_return"] == pytest.approx(trace["scalar_reward"].sum(axis=0))
    compact_audit = fit["rollouts"][0]["update_audit"]
    assert "batch_sizes" not in compact_audit and "chunk_lengths" not in compact_audit
    assert compact_audit["batch_size_histogram"] == {"6": 15}
    assert compact_audit["chunk_length_histogram"] == {"10": 15}
    raw_audit = np.load(tmp_path / compact_audit["raw_artifact"]["path"])
    assert raw_audit["batch_sizes"].tolist() == [6] * 15
    mixed, _ = runner._fit("M", sources, np.random.default_rng(92_526_002),
                           tmp_path, "fixture-sha", progress, spec, world_base=81)
    assert mixed["initial_digest"] == fit["initial_digest"]
    assert mixed["initial_optimizer_state_digest"] == fit["initial_optimizer_state_digest"]
    assert sorted(mixed["rollouts"][0]["assignment"]) == [1, 2]
    assert mixed["counts"]["team_steps"] == 20
    assert mixed["counts"]["partner_inferred_rows"] == 240  # Two full N6 source runtimes.
    row = runner._eval_cell("F1", 3, {"F1": snapshot}, sources, tmp_path,
                            spec, world_base=211)
    assert row["counts"]["team_steps"] == 20
    assert row["counts"]["inferred_action_rows"] == 240
    assert row["counts"]["executed_action_rows"] == 120
    assert row["per_world"]["J"] == pytest.approx(np.asarray(row["per_world"]["total_reward"]))
    assert row["per_world"]["S"] == pytest.approx(50 * np.asarray(row["per_world"]["coverage_reward"]))
    eval_trace = np.load(tmp_path / "raw/eval_F1_p3.npz")
    assert np.array_equal(eval_trace["executed"],
                          np.clip(np.concatenate((eval_trace["learner_raw"][:, :, :3],
                                                  eval_trace["partner_raw"][:, :, 3:]), axis=2), -1, 1))
    assert row["reset_convention"].endswith("unseeded reset()")
    old = runner._eval_cell("OLD3", 3, {}, sources, tmp_path, spec, world_base=211)
    assert old["initial_world_identity"] == row["initial_world_identity"]
    assert old["initial_world_identity_per_world"] == row["initial_world_identity_per_world"]


def test_reducer_joint_world_blocks_and_specialization():
    panel = np.zeros((4, 13), dtype=float)
    panel[:, 0:3] = 1
    panel[:, 3:6] = [2, 0, 2]
    panel[:, 6:9] = [0, 2, 2]
    panel[:, 9:12] = [2, 2, 3]
    panel[:, 12] = 1
    panel[:, 11] += [3, -3, 3, -3]
    result = reduce_panel(panel, 2 * panel + 1, draws=100, seed=17)
    j = result["J"]["finite_panel"]
    s = result["S_served_users_per_step"]["finite_panel"]
    assert j["M_minus_F2_partner3"] == 1
    assert j["T_fixed_response_specialization"] == 2
    assert j["H_partner3_relative_gain"] == 0
    assert s["M_minus_F2_partner3"] == 2
    assert result["J"]["per_world"]["M_minus_F2_partner3"] == [4, -2, 4, -2]
    assert result["J"]["pointwise_95_percentiles"]["M_minus_F2_partner3"][0] < 1
    assert result["J"]["pointwise_95_percentiles"]["M_minus_F2_partner3"][1] > 1


def test_evaluation_later_lane_failure_preserves_returned_raw(tmp_path, monkeypatch):
    sources, _ = validate_sources(_source_paths())
    (tmp_path / "raw").mkdir()
    spec = replace(runner.SPEC, horizon=2, eval_lanes=2)
    original = runner.native_components
    calls = 0
    def fail_second(info, reward, n):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("fixture later-lane component error")
        return original(info, reward, n)
    monkeypatch.setattr(runner, "native_components", fail_second)
    with pytest.raises(RuntimeError, match="fixture later-lane"):
        runner._eval_cell("OLD3", 3, {}, sources, tmp_path, spec, world_base=311)
    row = json.loads((tmp_path / "eval_OLD3_p3.json").read_text())
    assert row["status"] == "failed"
    assert row["counts"]["environment_step_attempts"] == 2
    assert row["counts"]["environment_step_returns"] == 2
    assert row["counts"]["components_validated"] == 1
    trace = np.load(tmp_path / row["raw_artifact"]["path"])
    assert trace["environment_returned"][0].tolist() == [True, True]
    assert np.isfinite(trace["scalar_reward"][0]).all()


def test_training_later_lane_failure_preserves_returned_raw(tmp_path, monkeypatch):
    sources, _ = validate_sources(_source_paths())
    (tmp_path / "raw").mkdir()
    spec = replace(runner.SPEC, horizon=10, train_lanes=2, eval_lanes=2, rollouts=1)
    original = runner.native_components
    calls = 0
    def fail_second(info, reward, n):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("fixture later-lane training component error")
        return original(info, reward, n)
    monkeypatch.setattr(runner, "native_components", fail_second)
    with pytest.raises(RuntimeError, match="fixture later-lane training"):
        runner._fit("F1", sources, np.random.default_rng(92_526_002), tmp_path,
                    "fixture-sha", {"completed_rollouts": []}, spec, world_base=411)
    row = json.loads((tmp_path / "train_F1_01.json").read_text())
    assert row["status"] == "failed"
    assert row["counts"]["environment_step_returns"] == 2
    assert row["counts"]["components_validated"] == 1
    assert (tmp_path / row["world"]["raw_artifact"]["path"]).is_file()
    trace = np.load(tmp_path / row["raw_artifact"]["path"])
    assert trace["env_returned"][0].tolist() == [True, True]
    assert np.isfinite(trace["scalar_reward"][0]).all()


@pytest.mark.parametrize("failure_mode", ["accounting", "finite"])
def test_post_update_validation_failure_retains_actual_counts_and_collection(
        tmp_path, monkeypatch, failure_mode):
    sources, _ = validate_sources(_source_paths())
    (tmp_path / "raw").mkdir()
    spec = replace(runner.SPEC, horizon=10, train_lanes=2, eval_lanes=2, rollouts=1)
    original = runner.update_learner
    def fail_after_actual_update(agent, buffer, dones):
        losses, audit = original(agent, buffer, dones)
        if failure_mode == "accounting":
            agent.config.ppo_epochs += 1  # Expected count now differs from 15 actual calls.
            return losses, audit
        return (float("nan"), *losses[1:]), audit
    monkeypatch.setattr(runner, "update_learner", fail_after_actual_update)
    with pytest.raises(ValueError, match="optimizer exposure|nonfinite"):
        runner._fit("F1", sources, np.random.default_rng(92_526_002), tmp_path,
                    "fixture-sha", {"completed_rollouts": []}, spec, world_base=511)
    row = json.loads((tmp_path / "train_F1_01.json").read_text())
    assert row["status"] == "failed_during_update"
    assert row["counts"]["team_steps"] == 20
    assert row["optimizer_calls_during_rollout"]["discoverer_actor"] == 15
    assert row["optimizer_calls_during_rollout"]["discoverer_critic"] == 15
    assert (tmp_path / row["raw_artifact"]["path"]).is_file()
    if failure_mode == "accounting":
        assert row["update_audit"]["minibatches"] == 15
        assert (tmp_path / row["update_audit"]["raw_artifact"]["path"]).is_file()


def test_launcher_created_directory_and_actual_run_study_serialization(tmp_path, monkeypatch):
    out = tmp_path / "output"
    out.mkdir()
    (out / "launch-manifest.json").write_text("kernel-owned")
    monkeypatch.setattr(runner.b01, "validate_sources", lambda paths: ({}, {"source.py": "pinned"}))
    def fake_fit(arm, payloads, rng, out, sha, progress):
        path = out / "raw" / f"init_{arm}.pt"
        torch.save({"fixture": True}, path)
        fit = {"initial_digest": "same", "initial_optimizer_state_digest": "same",
               "initial_normalizers": {}, "initial_checkpoint": runner._artifact(path, out),
               "optimizer_calls": {"discoverer_actor": 50_625, "discoverer_critic": 50_625,
                                   "coordinator": 0, "team_discriminator": 0, "individual_discriminator": 0},
               "counts": {"team_steps": 360_000, "executed_learner_rows": 1_080_000,
                          "executed_partner_rows": 1_080_000, "learner_inferred_rows": 2_160_000,
                          "partner_inferred_rows": 2_160_000}}
        return fit, {"payload": {}, "digest": "same"}
    monkeypatch.setattr(runner, "_fit", fake_fit)
    def fake_eval(learner, partner, snapshots, payloads, out):
        worlds = list(range(32))
        return {"cell": [learner, partner], "initial_world_identity": {"scene": "same"},
                "initial_world_identity_per_world": ["same"] * 32,
                "per_world": {"J": [float(partner)] * 32, "S": [float(partner)] * 32},
                "counts": {"team_steps": 16_000, "executed_action_rows": 96_000,
                           "inferred_action_rows": 192_000}}
    monkeypatch.setattr(runner, "_eval_cell", fake_eval)
    summary = runner.run_study(out, "fixture-sha", {"sha": "fixture-sha"},
                               {1: Path("one"), 2: Path("two"), 3: Path("three")},
                               seed=runner.SEED, command_start=runner.time.perf_counter())
    assert summary["status"] == "complete"
    assert summary["counts"]["training_team_steps"] == 1_080_000
    assert summary["counts"]["evaluation_team_steps"] == 208_000
    assert len(summary["cells"]) == 13
    assert (out / "launch-manifest.json").read_text() == "kernel-owned"
    assert json.loads((out / "progress.json").read_text())["status"] == "complete"
    with pytest.raises(ValueError, match="scientific output already exists"):
        runner.run_study(out, "fixture-sha", {"sha": "fixture-sha"},
                         {1: Path("one"), 2: Path("two"), 3: Path("three")},
                         seed=runner.SEED, command_start=runner.time.perf_counter())
