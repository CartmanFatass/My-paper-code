"""B10 binding and bounded synthetic pipeline checks; zero native environments."""
from dataclasses import replace
import importlib.util
import json

import numpy as np
import pytest
import torch

from experiments.candidates.ucope.paired_branch_credit_b10 import study
from experiments.candidates.ucope.paired_branch_credit_b10.storage import inspect_pair
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import Actor, Critic


@pytest.fixture
def synthetic_inputs(tmp_path):
    config = study.Config.engineering()
    checkpoint, summary, source = (tmp_path / name for name in ("foundation.pt", "foundation.json", "source.json"))
    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(103)
        actor, critic = Actor(), Critic()
    torch.save({"object": study.inherited.SOURCE_OBJECT, "arm": "Ghalf", "seed": config.master - 30,
        "train_episodes": config.train_episodes, "optimizer_steps": 2 * config.train_episodes,
        "actor": actor.state_dict(), "critic": critic.state_dict()}, checkpoint)
    digest = lambda path: study.inherited.sha256(path.read_bytes())
    study.write_json(summary, {"object": study.inherited.SOURCE_OBJECT, "master": config.master - 30,
        "launch_sha": study.inherited.SOURCE_SHA, "status": "COMPLETE",
        "configuration": {key: getattr(config, key) for key in ("horizon", "train_episodes", "eval_episodes")},
        "arms": {"Ghalf": {"train_complete": True, "checkpoint": {"sha256": digest(checkpoint)},
            "counts": {"train_episodes": config.train_episodes, "optimizer_steps": 2 * config.train_episodes}}}})
    study.write_json(source, {"object": study.inherited.SOURCE_OBJECT, "launch_sha": study.inherited.SOURCE_SHA})
    return study.inherited.Inputs(checkpoint, summary, source, digest(checkpoint), digest(summary), digest(source))


def test_complete_synthetic_pipeline_preserves_pairs_foundation_and_final_panels(tmp_path, synthetic_inputs):
    before = torch.get_rng_state().clone()
    out = tmp_path / "complete"
    previous_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        result = study.run(study.Config.engineering(), out, {}, fixture_inputs=synthetic_inputs)
    finally:
        torch.set_num_threads(previous_threads)
    assert result["status"] == "COMPLETE", result["failure"]
    assert torch.equal(before, torch.get_rng_state())
    assert result["counts"]["train_team_steps"] == 48
    assert result["counts"]["eval_team_steps"] == 32
    assert result["counts"]["team_steps"] == 80
    assert result["counts"]["gate_optimizer_steps"] == 20
    assert result["counts"]["critic_optimizer_steps"] == 16
    assert result["counts"]["optimizer_steps"] == 36
    assert result["counts"]["foundation_forward_calls"] == 80
    assert result["counts"]["recurrent_agent_observations"] == 400
    assert result["foundation_unchanged"] and result["foundation_optimizer_steps"] == 0
    assert result["fit_accounting"]["completed_new_gate_fits"] == 3
    assert result["arms"]["R_CF"]["initial_gate_digest"] == result["arms"]["R_FULL"]["initial_gate_digest"]
    rows = [json.loads(line) for line in (out / "pairs.jsonl").read_text().splitlines()]
    assert len(rows) == 2
    for row in rows:
        actual = inspect_pair(out / row["raw_path"])
        assert actual["tick"] == row["tick"] and actual["agent"] == row["agent"]
        assert actual["delta"] == pytest.approx(row["delta"], abs=1e-14)
        assert actual["eligible"] == row["eligible"]
    for name, identity in result["artifacts"].items():
        assert study.file_identity(out / name) == identity
    coins = {}
    for arm in study.MODES:
        record = result["arms"][arm]
        assert record["eval_complete"] and all(record["evaluation_immutability"].values())
        with np.load(out / (arm + "_evaluation.npz"), allow_pickle=False) as arrays:
            values = arrays["reward"].sum(axis=1, dtype=np.float64) / 4
            np.testing.assert_allclose(values, result["final_panel"]["world_scores"][arm], rtol=0, atol=1e-14)
            assert arrays["context"].shape == (2, 4, 5, 175)
            coins[arm] = arrays["gate_uniforms"].copy()
            if arm == "G":
                assert not arrays["keep"].any() and not coins[arm].any()
            else:
                np.testing.assert_array_equal(arrays["eligible"][:, 1:], ~arrays["keep"][:, :-1])
        if arm in study.ARMS:
            checkpoint = torch.load(out / (arm + "_final.pt"), weights_only=True)
            assert checkpoint["foundation"]["actor_parameter_digest"] == result["foundation_final_digest"]
            assert checkpoint["gate_optimizer"]["state"]
            assert (checkpoint["critic"] is None) == (arm == "R_CF")
    np.testing.assert_array_equal(coins["R_CF"], coins["R_FULL"])
    np.testing.assert_array_equal(coins["R_CF"], coins["S_FULL"])
    episodes = [json.loads(line) for line in (out / "episodes.jsonl").read_text().splitlines()]
    assert len(episodes) == 20
    assert all(row["phase"] == "train" for row in episodes[:12])
    assert all(row["phase"] == "eval" for row in episodes[12:])
    with pytest.raises(ValueError, match="already exist"):
        study.run(study.Config.engineering(), out, {}, fixture_inputs=synthetic_inputs)


def test_transition_failure_keeps_partial_cost_and_does_not_report_a_scientific_score(tmp_path, synthetic_inputs, monkeypatch):
    class Failing(study.SyntheticAdapter):
        calls = 0

        def step(self, commands):
            self.calls += 1
            if self.calls == 3:
                raise RuntimeError("synthetic transition failure")
            return super().step(commands)

    monkeypatch.setattr(study, "SyntheticAdapter", Failing)
    result = study.run(study.Config.engineering(), tmp_path / "failed", {}, fixture_inputs=synthetic_inputs)
    assert result["status"] == "INCOMPLETE"
    assert result["failure"]["message"] == "synthetic transition failure"
    assert result["counts"]["train_team_steps"] == 2
    assert result["counts"]["train_episodes"] == 0
    assert result["counts"]["optimizer_steps"] == 0
    assert result["fit_accounting"]["started_new_gate_fits"] == 1
    assert result["fit_accounting"]["completed_new_gate_fits"] == 0
    assert result["foundation_unchanged"] and not result["final_panel"]["complete"]


def test_declared_scope_and_missing_admission_refuse_before_output(tmp_path):
    for config, admission in ((study.Config(8971), {}), (study.Config(8974), {"direction": "ucope"}),
                              (replace(study.Config.engineering(), horizon=9), {})):
        out = tmp_path / str(config)
        with pytest.raises(ValueError):
            study.run(config, out, admission)
        assert not out.exists()
    for master in study.MASTERS:
        study.require_config(study.Config(master))


def test_optimizer_cannot_expose_foundation_or_borrow_another_gates_parameters():
    gate = study.ScalarGate("scalar", 7, 0.0, 1.0)
    other = study.ScalarGate("scalar", 8, 0.0, 1.0)
    good = torch.optim.Adam(gate.parameters(), lr=3e-4)
    study._validate_paired_optimizer(gate, good)
    bad = torch.optim.Adam(other.parameters(), lr=3e-4)
    with pytest.raises(ValueError, match="only its model parameters"):
        study._validate_paired_optimizer(gate, bad)
    assert not good.state and not bad.state  # Construction is zero optimization steps.


def test_reducer_keeps_full_ppo_and_practical_g_as_distinct_references():
    panels = {"R_CF": [0.21, 0.24], "R_FULL": [0.23, 0.24], "S_FULL": [0.22, 0.22], "G": [0.22, 0.23]}
    result = study.reduce_panels(panels, 2)
    assert result["complete"] and result["primary"] == "R_CF_minus_R_FULL"
    assert result["R_CF_minus_R_FULL"]["mean"] == pytest.approx(-0.01)
    assert result["R_CF_minus_G"]["mean"] == pytest.approx(0.0)
    assert result["R_CF_minus_S_FULL"]["mean"] == pytest.approx(0.005)
    partial = study.reduce_panels({**panels, "S_FULL": [0.22]}, 2)
    assert not partial["complete"] and "R_CF_minus_G" not in partial


def test_runner_admission_and_sha_refuse_before_science(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("b10_runner", study.REPO / "scripts/run_ucope_paired_branch_credit_b10.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    calls = []
    monkeypatch.setattr(torch, "set_num_threads", lambda n: calls.append(n))
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda n: calls.append(n))
    out = tmp_path / "not-created"
    args = ["--master", "8971", "--out", str(out), "--launch-sha", "expected"]

    def refuse(*args, **kwargs):
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
