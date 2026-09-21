"""Study ownership, artifact fidelity, and failures using synthetic worlds only."""
from dataclasses import replace
import importlib.util
import json

import numpy as np
import pytest
import torch

from experiments.candidates.ucope.normalized_distance_gate_b09 import study
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import Actor, Critic


@pytest.fixture(autouse=True)
def one_thread():
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(previous)


@pytest.fixture
def inputs(tmp_path):
    config = study.Config.engineering()
    checkpoint, summary, source = (tmp_path / name for name in ("foundation.pt", "foundation.json", "source.json"))
    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(103)
        actor, critic = Actor(), Critic()
    torch.save({"object": study.SOURCE_OBJECT, "arm": "Ghalf", "seed": config.master - 20,
        "train_episodes": config.train_episodes, "optimizer_steps": 2 * config.train_episodes,
        "actor": actor.state_dict(), "critic": critic.state_dict()}, checkpoint)
    digest = lambda p: study.sha256(p.read_bytes())
    study.write_json(summary, {"object": study.SOURCE_OBJECT, "master": config.master - 20,
        "launch_sha": study.SOURCE_SHA, "status": "COMPLETE",
        "configuration": {k: getattr(config, k) for k in ("horizon", "train_episodes", "eval_episodes")},
        "arms": {"Ghalf": {"train_complete": True, "checkpoint": {"sha256": digest(checkpoint)},
            "counts": {"train_episodes": config.train_episodes, "optimizer_steps": 2 * config.train_episodes}}}})
    study.write_json(source, {"object": study.SOURCE_OBJECT, "launch_sha": study.SOURCE_SHA})
    return study.Inputs(checkpoint, summary, source, digest(checkpoint), digest(summary), digest(source))


def test_complete_pair_and_reference_preserve_foundation_and_reconstruct_scores(tmp_path, inputs):
    out = tmp_path / "complete"
    before = torch.get_rng_state().clone()
    result = study.run(study.Config.engineering(), out, {}, fixture_inputs=inputs)
    assert result["status"] == "COMPLETE", result["failure"]
    assert torch.equal(before, torch.get_rng_state())
    assert result["foundation_unchanged"] and result["foundation_optimizer_steps"] == 0
    assert result["fit_accounting"]["started_new_gate_fits"] == 2
    assert result["fit_accounting"]["completed_new_gate_fits"] == 2
    assert result["counts"]["train_team_steps"] == 64
    assert result["counts"]["eval_team_steps"] == 72
    assert result["counts"]["team_steps"] == 136
    assert result["counts"]["optimizer_steps"] == 32
    assert result["counts"]["gate_optimizer_steps"] == result["counts"]["critic_optimizer_steps"] == 16
    assert result["counts"]["max_minibatch"] == 16
    assert result["final_panel"]["complete"]
    panels, coins = {}, {}
    for arm in study.MODES:
        record = result["arms"][arm]
        assert record["eval_complete"] and all(record["evaluation_immutability"].values())
        with np.load(out / f"{arm}_evaluation.npz", allow_pickle=False) as arrays:
            assert arrays["reward"].dtype == np.float64
            panels[arm] = (arrays["reward"].sum(axis=1) / 8).tolist()
            np.testing.assert_allclose(panels[arm], result["final_panel"]["world_scores"][arm], rtol=0, atol=1e-15)
            assert arrays["context"].shape == (1, 8, 5, 175)
            assert arrays["context_episode_ids"].tolist() == [0]
            coins[arm] = arrays["gate_uniforms"].copy()
            if arm == "ordinary":
                assert not arrays["keep"].any()
                np.testing.assert_allclose(arrays["commands"], np.tanh(arrays["means"]), rtol=1e-6, atol=1e-7)
            else:
                np.testing.assert_array_equal(arrays["eligible"][:, 1:], ~arrays["keep"][:, :-1])
                assert not arrays["eligible"][:, 0].any()
        if arm in study.ARMS:
            assert record["movement"]["gate"]["displacement"] > 0
            assert record["movement"]["critic"]["displacement"] > 0
            payload = torch.load(out / f"{arm}_final.pt", weights_only=True)
            assert payload["arm"] == arm and payload["counts"]["optimizer_steps"] == 16
            assert payload["foundation"]["actor_parameter_digest"] == result["foundation_final_digest"]
    np.testing.assert_array_equal(coins["normalized"], coins["scalar"])
    assert not coins["ordinary"].any()
    reduced = study.reduce_panels(panels, 3)
    for key in ("normalized_minus_scalar", "scalar_minus_ordinary", "normalized_minus_ordinary"):
        actual, expected = result["final_panel"][key], reduced[key]
        # NumPy and torch float64 sums need not use identical reduction order.
        for metric in ("differences", "mean", "conditional_world_se"):
            np.testing.assert_allclose(actual[metric], expected[metric], rtol=0, atol=1e-14)
        for metric in ("worlds", "positive", "negative", "tie"):
            assert actual[metric] == expected[metric]
    for name, identity in result["artifacts"].items():
        assert study.file_identity(out / name) == identity
    for name, suffix in (("checkpoint", ".pt"), ("summary", ".json"), ("source", ".json")):
        assert (out / ("inherited_" + name + suffix)).read_bytes() == getattr(inputs, name).read_bytes()
    episodes = [json.loads(x) for x in (out / "episodes.jsonl").read_text().splitlines()]
    assert len(episodes) == 17
    assert len((out / "updates.jsonl").read_text().splitlines()) == 4
    with pytest.raises(ValueError, match="already exist"):
        study.run(study.Config.engineering(), out, {}, fixture_inputs=inputs)


def test_bad_input_and_invalid_scope_precede_fit_or_environment(tmp_path, inputs, monkeypatch):
    calls = []
    monkeypatch.setattr(study, "SyntheticAdapter", lambda *a: calls.append(a))
    inputs.checkpoint.write_bytes(inputs.checkpoint.read_bytes() + b"changed")
    result = study.run(study.Config.engineering(), tmp_path / "rejected", {}, fixture_inputs=inputs)
    assert result["status"] == "INCOMPLETE"
    assert result["failure"]["message"] == "inherited checkpoint digest mismatch"
    assert result["fit_accounting"]["started_new_gate_fits"] == 0 and calls == []
    for config, admission in ((study.Config(8961), {}), (study.Config(8964), {"direction": "ucope"}),
                              (replace(study.Config.engineering(), horizon=9), {})):
        out = tmp_path / str(config)
        with pytest.raises(ValueError):
            study.run(config, out, admission)
        assert not out.exists()


def test_returned_partial_transitions_survive_training_failure(tmp_path, inputs, monkeypatch):
    class Failing(study.SyntheticAdapter):
        calls = 0
        def step(self, actions):
            self.calls += 1
            if self.calls == 3:
                raise RuntimeError("synthetic transition failure")
            return super().step(actions)
    monkeypatch.setattr(study, "SyntheticAdapter", Failing)
    out = tmp_path / "failed"
    result = study.run(study.Config.engineering(), out, {}, fixture_inputs=inputs)
    assert result["status"] == "INCOMPLETE"
    assert result["failure"]["message"] == "synthetic transition failure"
    assert result["counts"]["team_steps"] == 2
    assert result["counts"]["train_episodes"] == 0
    assert result["counts"].get("optimizer_steps", 0) == 0
    assert result["fit_accounting"]["started_new_gate_fits"] == 1
    assert result["fit_accounting"]["completed_new_gate_fits"] == 0
    assert result["foundation_unchanged"]
    assert not result["final_panel"]["complete"] and not (out / "normalized_final.pt").exists()
    assert json.loads((out / "summary.json").read_text())["counts"]["team_steps"] == 2


def test_runner_admission_and_source_mismatch_precede_science(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("b09_runner", study.REPO / "scripts/run_ucope_normalized_distance_gate_b09.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    calls = []
    monkeypatch.setattr(torch, "set_num_threads", lambda n: calls.append(n))
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda n: calls.append(n))
    out = tmp_path / "not-created"
    args = ["--master", "8961", "--out", str(out), "--launch-sha", "expected"]
    def refuse(*a, **k):
        raise RuntimeError("admission refused")
    monkeypatch.setattr(runner, "require_admission", refuse)
    with pytest.raises(RuntimeError, match="admission refused"):
        runner.main(args)
    monkeypatch.setattr(runner, "require_admission", lambda *a, **k: {"sha": "different"})
    with pytest.raises(SystemExit):
        runner.main(args)
    with pytest.raises(SystemExit):
        runner.main(args + ["--fixture"])
    assert not out.exists() and calls == []
