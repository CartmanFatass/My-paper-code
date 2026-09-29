import json

import numpy as np
import pytest
import torch

from experiments.candidates.uav_local_history.b02 import study
from experiments.candidates.uav_local_history.b02.model import templates
from tests.experiments.candidates.uav_local_history.b01.test_study import FixtureEnv as BaseFixture


class FixtureEnv(BaseFixture):
    def state(self):
        return np.r_[self.positions.ravel(), self.users.ravel(), self.clock / self.horizon].astype(np.float32)

    def reset(self, seed):
        self.reset_seeds = getattr(self, "reset_seeds", []) + [seed]
        obs, info = super().reset(seed)
        info["state"] = self.state()
        return obs, info

    def step(self, commands):
        obs, reward, terminated, truncated, info = super().step(commands)
        info["next_state"] = self.state()
        return obs, reward, terminated, truncated, info


def test_collect_macro_alignment_and_eval_rng(tmp_path):
    torch.set_num_threads(1)
    actor, critic = templates(9)
    env = FixtureEnv(17)
    counts = dict(complete_episodes=0)
    generator = torch.Generator().manual_seed(51)
    row, rollout = study.collect_learned(env, actor, critic, 9, "train", 17, generator, tmp_path, counts, horizon=8)
    assert rollout["context"].shape == (2, 5, 107)
    assert rollout["points"].shape == (2, 5, 64, 7)
    assert rollout["reward"].tolist() == pytest.approx([.52, .52])
    np.testing.assert_array_equal(rollout["context"][0, :, -3:].numpy(), np.zeros((5, 3)))
    np.testing.assert_array_equal(rollout["context"][1, :, -3:].numpy(), study.COMMANDS[rollout["action"][0].numpy()])
    assert counts["train_team_steps"] == 8 and counts["train_agent_decisions"] == 10
    assert counts["learned_cache_ingests"] == 40
    assert row["mean_served"] == 5
    (tmp_path / "raw").mkdir()
    state = generator.get_state().clone()
    row, rollout = study.collect_learned(env, actor, critic, 9, "initial", 17, generator, tmp_path, counts, horizon=8)
    assert rollout is None and torch.equal(state, generator.get_state())
    with np.load(row["raw"]["path"]) as raw:
        assert raw["context"].shape == (2, 5, 107)
        assert raw["observations"].shape == (8, 5, 104)
        np.testing.assert_array_equal(raw["action"], raw["logits"].argmax(axis=-1))
        np.testing.assert_array_equal(raw["commands"], np.repeat(study.COMMANDS[raw["action"]], 4, axis=0))
        np.testing.assert_array_equal(raw["terminal_observation"][:, -1], 1)


def test_complete_fixture_batch_exact_counts_and_seeds(tmp_path):
    torch.set_num_threads(1)
    environments = []

    def factory(seed):
        env = FixtureEnv(seed, horizon=256)
        environments.append(env)
        return env

    output = tmp_path / "batch"
    summary = study.run_batch(output, "a" * 40, factory=factory, masters=(9,), train_episodes=2, eval_seeds=(17, 18))
    assert summary["status"] == "COMPLETE", summary["limits"]
    counts = summary["counts"]
    assert counts["team_steps"] == counts["native_step_calls"] == 2560
    assert counts["train_team_steps"] == 512 and counts["eval_team_steps"] == 2048
    assert counts["fit_started"] == counts["fit_completed"] == 1
    assert counts["complete_episodes"] == counts["explicit_resets"] == 10
    assert counts["optimizer_steps"] == 8
    assert counts["actor_optimizer_steps"] == counts["critic_optimizer_steps"] == 4
    assert counts["ppo_rollouts"] == 1
    assert environments[0].reset_seeds[1:] == [17, 17, 18, 18, 17, 18, 29110000, 29110001, 17, 18]
    assert environments[0].closed
    assert len(summary["rows"]) == 8 and summary["scientific_invocation"] is False
    fit = summary["fits"][0]
    assert fit["actor_displacement"] > 0 and fit["critic_displacement"] > 0
    assert summary == json.loads((output / "summary.json").read_text())
    with pytest.raises(FileExistsError):
        study.run_batch(output, "a" * 40, factory=factory, masters=(9,), train_episodes=2, eval_seeds=(17, 18))


def test_failure_preserves_partial_step_counts_without_retry(tmp_path):
    class FailedEnv(FixtureEnv):
        def step(self, commands):
            if self.clock == 3:
                raise RuntimeError("injected fixture failure")
            return super().step(commands)

    envs = []
    def factory(seed):
        env = FailedEnv(seed, horizon=256)
        envs.append(env)
        return env

    summary = study.run_batch(tmp_path / "failed", "a" * 40, factory=factory, masters=(9,), train_episodes=2, eval_seeds=(17,))
    assert summary["status"] == "INCOMPLETE"
    assert "injected fixture failure" in summary["limits"][0]
    assert summary["counts"]["native_step_calls"] == 4 and summary["counts"]["team_steps"] == 3
    assert summary["counts"]["eval_team_steps"] == 3 and summary["counts"]["train_team_steps"] == 0
    assert summary["counts"]["fit_started"] == 0 and not summary["rows"]
    assert envs[0].closed


def test_entry_refuses_before_scientific_effects(monkeypatch, tmp_path):
    from experiments.candidates.uav_local_history.b02 import run
    from scripts import hmasd_admission

    def denied(*args, **kwargs):
        raise PermissionError("fixture refusal")
    monkeypatch.setattr(hmasd_admission, "require_admission", denied)
    monkeypatch.setattr(study, "run_batch", lambda *a, **k: pytest.fail("unadmitted scientific batch"))
    with pytest.raises(PermissionError, match="fixture refusal"):
        run.main(["--out", str(tmp_path / "not-created"), "--launch-sha", "a" * 40, "--seed", "291021"])
    assert not (tmp_path / "not-created").exists()
