"""Real short S1 collector/update/transfer panels; technical checks, not fits."""
from dataclasses import replace
import json

import numpy as np
import pytest
import torch

from experiments.candidates.agent_count_generalization import runner
from experiments.candidates.agent_count_generalization.configuration import DEFAULT_SPEC, SEEDS


def test_native_reward_conversion_uses_actual_test_roster():
    parts = dict(coverage_reward=.6, quality_reward=.4, energy_penalty=.03,
                 total_reward=.51)
    info = {"reward_components": {"reward_info": parts}}
    for n in (4, 6, 8):
        assert runner.native_components(info, .51 / n, n) == parts
    with pytest.raises(ValueError, match="mismatch"):
        runner.native_components(info, .51 / 8, 6)


@pytest.mark.parametrize("arm", ["H6", "SET"])
def test_real_short_fit_updates_and_evaluates_all_counts(tmp_path, arm):
    spec = replace(DEFAULT_SPEC, horizon=20, train_lanes=2, eval_lanes=1,
                   rollouts=1, panels=(0, 1), hidden_size=32, n_heads=2,
                   n_layers=1, ppo_epochs=1, sequence_batch_size=64, torch_threads=1)
    out = tmp_path / arm
    assert runner.run_fit(out, arm, SEEDS[arm][0], "technical-fixture", {"sha": "technical-fixture"}, spec) == 0, (
        (out / "summary.json").read_text())
    result = json.loads((out / "summary.json").read_text())
    assert result["status"] == "complete" and result["fit_started"]
    assert result["counts"] == {"training_team_steps": 40, "stored_team_steps": 40,
                                "training_episodes": 2, "updates": 1,
                                "evaluation_team_steps": 120, "evaluation_episodes": 6}
    assert result["config"]["k"] == 10 and result["config"]["obs_dim"] == 104
    assert len(result["panels"]) == 6
    for panel in result["panels"]:
        assert panel["status"] == "complete"
        assert not any(panel["optimizer_calls"].values())
        assert panel["frozen_weights_and_normalizers"]
        components = panel["component_means"]
        expected = .7 * np.asarray(components["coverage_reward"]) + .3 * np.asarray(components["quality_reward"]) - np.asarray(components["energy_penalty"])
        np.testing.assert_allclose(panel["J"], expected, rtol=1e-6, atol=1e-7)
        assert panel["config"]["n_agents"] == panel["test_n"]
    assert result["initial_parameter_digest"] != result["final_parameter_digest"]
    assert result["parameter_motion"]["discoverer_actor"]["delta_l2"] > 0
    assert result["parameter_motion"]["discoverer_critic"]["delta_l2"] > 0
    assert len((out / "training.jsonl").read_text().splitlines()) == 1
    for checkpoint in result["checkpoints"]:
        state = torch.load(out / checkpoint["path"], weights_only=False)
        assert state["launch_sha"] == "technical-fixture"
        assert state["modules"]


def test_failed_evaluation_preserves_failure_and_does_not_start_training(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("injected evaluation failure")
    monkeypatch.setattr(runner, "evaluate_panel", fail)
    spec = replace(DEFAULT_SPEC, horizon=10, train_lanes=1, eval_lanes=1,
                   rollouts=1, panels=(0, 1), hidden_size=16, n_heads=2,
                   n_layers=1, ppo_epochs=1, torch_threads=1)
    out = tmp_path / "failed"
    assert runner.run_fit(out, "SET", SEEDS["SET"][0], "test", {"sha": "test"}, spec) == 1
    result = json.loads((out / "summary.json").read_text())
    assert not result["fit_started"]
    assert result["counts"]["training_team_steps"] == 0
    assert result["status"] == "failed" and "injected" in result["failure"]
    assert "injected" in (out / "error.txt").read_text()
    with pytest.raises(ValueError, match="existing scientific summary"):
        runner.run_fit(out, "SET", SEEDS["SET"][0], "test", {"sha": "test"}, spec)


def test_cli_checks_admission_before_run(tmp_path, monkeypatch):
    calls = []
    def refuse(*args, **kwargs):
        calls.append("admission")
        raise RuntimeError("not admitted")
    monkeypatch.setattr(runner, "require_admission", refuse)
    monkeypatch.setattr(runner, "run_fit", lambda *args: calls.append("scientific effects"))
    out = tmp_path / "never-created"
    with pytest.raises(RuntimeError, match="not admitted"):
        runner.main(["--arm", "H6", "--seed", str(SEEDS["H6"][0]),
                     "--launch-sha", "test", "--out", str(out)])
    assert calls == ["admission"] and not out.exists()
