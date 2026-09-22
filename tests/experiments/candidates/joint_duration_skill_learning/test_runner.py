"""Actual S1 collection/update/evaluation and result-entry boundaries."""
from dataclasses import replace
import json
from pathlib import Path
import random

import numpy as np
import pytest
import torch

from experiments.candidates.joint_duration_skill_learning import runner


def test_runner_satisfies_native_static_guard_contract():
    from scripts.hmasd_launch import _validate_guard_contract
    _validate_guard_contract(Path(runner.__file__), runner.DIRECTION)


def test_production_exposure_and_seed_bindings():
    for arm, seed in runner.SEEDS.items():
        spec = runner.StudySpec(arm, seed)
        assert spec.lanes * spec.horizon * spec.rollouts == 360000
        assert [r * spec.lanes * spec.horizon for r in spec.eval_rollouts] == [0, 120000, 240000, 360000]
        assert spec.eval_lanes * spec.horizon * len(spec.eval_rollouts) == 64000
        assert list(range(spec.eval_seed, spec.eval_seed + spec.eval_lanes)) == list(range(740000, 740032))


def test_native_entry_requires_admission_before_outputs(monkeypatch, tmp_path):
    def refuse(*args, **kwargs):
        raise PermissionError("no native admission")
    monkeypatch.setattr(runner, "require_admission", refuse)
    target = tmp_path / "unadmitted"
    with pytest.raises(PermissionError, match="no native admission"):
        runner.main(["--arm", "fixed", "--seed", str(runner.SEEDS["fixed"]),
                     "--launch-sha", "a" * 40, "--out", str(target)])
    assert not target.exists()


def test_admitted_sha_cannot_be_relabelled(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "require_admission", lambda *a, **kw: {"sha": "b" * 40})
    target = tmp_path / "wrong-sha"
    with pytest.raises(ValueError, match="SHA differs"):
        runner.main(["--arm", "fixed", "--seed", str(runner.SEEDS["fixed"]),
                     "--launch-sha", "a" * 40, "--out", str(target)])
    assert not target.exists()


def test_preserve_rng_restores_every_available_stream():
    runner.seed_rng(127)
    python_state, numpy_state = random.getstate(), np.random.get_state()
    cpu_state = torch.get_rng_state().clone()
    cuda_states = torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None
    with runner.preserve_rng():
        runner.seed_rng(993)
        random.random()
        np.random.rand(4)
        torch.rand(4)
        if cuda_states is not None:
            torch.rand(4, device="cuda")
    assert random.getstate() == python_state
    restored = np.random.get_state()
    assert restored[0] == numpy_state[0] and restored[2:] == numpy_state[2:]
    np.testing.assert_array_equal(restored[1], numpy_state[1])
    assert torch.equal(torch.get_rng_state(), cpu_state)
    if cuda_states is not None:
        assert all(torch.equal(a, b) for a, b in zip(torch.cuda.get_rng_state_all(), cuda_states))


@pytest.mark.parametrize("arm", ["fixed", "factored", "ar"])
@pytest.mark.parametrize("device_name", ["cpu", "cuda"])
def test_short_complete_native_learning_and_evaluation(arm, device_name, tmp_path):
    if device_name == "cuda" and not torch.cuda.is_available():
        pytest.skip("CUDA unavailable on this test host")
    # Correctness only: native UAV dimensions, two complete short episodes,
    # two updates and fresh deterministic panels. No scientific comparison.
    spec = replace(runner.StudySpec(arm, 123), lanes=2, horizon=20, rollouts=2,
                   eval_lanes=2, eval_rollouts=(0, 2), epochs=1, threads=1,
                   coordinator_batch_size=16)
    out = tmp_path / f"{arm}-{device_name}"
    summary = runner.execute(spec, out, "test-source", torch.device(device_name))
    assert summary["status"] == "complete"
    assert summary["counts"]["training_transitions"] == 80
    assert summary["counts"]["stored_training_transitions"] == 80
    assert summary["counts"]["update_stages"] == 2
    assert summary["counts"]["evaluation_transitions"] == 80
    assert set(summary["optimizer_calls"]) == set(runner.NETWORKS)
    assert all(value > 0 for value in summary["optimizer_calls"].values())
    assert all(value > 0 for value in summary["final_relative_initialization_displacement"].values())
    assert len(summary["evaluations"]) == 2
    for row in summary["evaluations"]:
        np.testing.assert_allclose(np.asarray(row["native_scores_J"]),
                                   spec.n_agents * np.asarray(row["returns_U"]) / spec.horizon)
        assert all(value == 0 for value in row["optimizer_calls"].values())
        if row["after_rollout"] == 0:
            assert row["duration"]["coordinator_relative_initialization_displacement"] == 0.0
    for checkpoint in summary["checkpoints"]:
        assert (out / checkpoint["path"]).is_file()
        assert checkpoint["bytes"] > 0
    assert json.loads((out / "summary.json").read_text())["status"] == "complete"
    assert len((out / "training.jsonl").read_text().splitlines()) == 2
    with pytest.raises(FileExistsError, match="overwrite"):
        runner.execute(spec, out, "test-source", torch.device(device_name))


def test_nonfinite_measurements_cannot_be_published(tmp_path):
    target = tmp_path / "summary.json"
    with pytest.raises(ValueError, match="nonfinite"):
        runner.write_json(target, {"metric": float("nan")})
    assert not target.exists()


@pytest.mark.parametrize("failure", ["evaluation", "update", "displacement", "replay", "replay_capture"])
def test_failed_attempt_retains_consumed_exposure(failure, monkeypatch, tmp_path):
    spec = replace(runner.StudySpec("fixed", 456), lanes=1, horizon=10, rollouts=1,
                   eval_lanes=1, eval_rollouts=(0, 1), epochs=1, threads=1)
    out = tmp_path / failure
    if failure == "evaluation":
        original_make = runner.native._make_envs

        def make_with_failure(count, base_seed, *args):
            envs = original_make(count, base_seed, *args)
            if base_seed == spec.eval_seed:
                env = envs[0]
                original_step = env.step
                calls = [0]

                def interrupted_step(action):
                    if calls[0] == 2:
                        raise RuntimeError("injected evaluation failure")
                    calls[0] += 1
                    return original_step(action)

                env.step = interrupted_step
            return envs

        monkeypatch.setattr(runner.native, "_make_envs", make_with_failure)
    elif failure in ("update", "replay", "replay_capture"):
        def interrupted_update(*args, **kwargs):
            error_class = RuntimeError if failure == "update" else runner.ReplayAuditError
            raise error_class("injected update failure")
        monkeypatch.setattr(runner.DurationAgent, "update", interrupted_update)
        def payload(self):
            if failure == "replay_capture":
                raise OSError("injected capture failure")
            return {"coordinator": {"weight": torch.ones(3)}, "events": [{"env_id": 0}]}
        monkeypatch.setattr(runner.DurationAgent, "replay_failure_payload", payload)
    else:
        monkeypatch.setattr(runner.native, "_exposure_line", lambda *args: {"coordinator": float("nan")})
    with pytest.raises((RuntimeError, ValueError)):
        runner.execute(spec, out, "test-source", torch.device("cpu"))
    saved = json.loads((out / "summary.json").read_text())
    assert saved["status"] == "incomplete" and saved["stage"] == "technical_failure"
    if failure == "evaluation":
        assert saved["counts"]["evaluation_transitions"] == 2
        assert saved["evaluations"][0]["status"] == "incomplete"
        assert saved["evaluations"][0]["steps_per_lane"] == [2]
        assert saved["counts"]["training_transitions"] == 0
    else:
        assert saved["counts"]["training_transitions"] == 10
        assert saved["counts"]["stored_training_transitions"] == 10
        assert saved["counts"]["training_episodes"] == 1
        assert saved["counts"]["update_stages"] == int(failure == "displacement")
    assert (out / "error.txt").is_file()
    if failure == "replay":
        artifact = saved["replay_failure"]
        loaded = torch.load(out / artifact["path"], weights_only=False)
        torch.testing.assert_close(loaded["coordinator"]["weight"], torch.ones(3))
        assert loaded["events"] == [{"env_id": 0}]
        assert loaded["launch_sha"] == "test-source"
        assert loaded["runner_spec"]["arm"] == "fixed"
        assert runner.artifact_facts(out / artifact["path"])["sha256"] == artifact["sha256"]
    elif failure == "replay_capture":
        assert "injected capture failure" in saved["replay_failure_capture_error"]
        assert "injected update failure" in saved["error"]
