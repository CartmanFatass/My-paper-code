"""Controlled-array and synthetic verification only: no native host or master9601 fit."""
import copy
import json

import numpy as np
import pytest
import torch

from experiments.candidates.tail_return_distributional_learning.trdl_b01 import learner, study
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import tanh_log_prob

torch.set_num_threads(1)


def test_initialization_pairing_and_private_rng():
    rng_before = torch.get_rng_state().clone()
    scalar_actor, scalar = learner.models(7, "SCALAR")
    q_actor, quantile = learner.models(7, "Q32")
    assert torch.equal(torch.get_rng_state(), rng_before)
    assert all(torch.equal(a, b) for a, b in zip(scalar_actor.parameters(), q_actor.parameters()))
    assert all(torch.equal(a, b) for a, b in zip(scalar.trunk.parameters(), quantile.trunk.parameters()))
    assert [sum(p.numel() for p in model.parameters()) for model in (scalar_actor, scalar, quantile)] == [34902, 34305, 38304]
    assert all(p.requires_grad and p.dtype == torch.float32 and p.device.type == "cpu"
               for model in (scalar_actor, scalar, quantile) for p in model.parameters())
    streams = [learner.action_generator(7, arm, episode)
               for arm, episode in (("SCALAR", None), ("Q32", None), ("SCALAR", 0), ("Q32", 0))]
    assert len({stream.initial_seed() for stream in streams}) == 4
    assert [stream.initial_seed() for stream in streams] == [700021, 700022, 703000, 706000]


def test_fourth_order_statistic_ties_and_pinball_gradient():
    returns = torch.arange(16, dtype=torch.float32) / 20
    eta = returns.sort().values[3]
    expected = torch.tensor([-.6, -.4, -.2] + [0.] * 13)
    torch.testing.assert_close(learner.tail_score(returns, eta), expected)
    tied = torch.tensor([0., 0., 0., 0.] + [.5] * 12)
    assert torch.count_nonzero(learner.tail_score(tied, tied.sort().values[3])) == 0
    # Targets above every prediction push all quantiles upward, with midpoint weights.
    q = torch.zeros(1, 1, 32, requires_grad=True)
    loss = learner.pinball(q, torch.tensor([[.5]]))
    loss.backward()
    assert float(loss) == pytest.approx(.25)
    expected_grad = -(torch.arange(32) + .5) / (32 * 32)
    torch.testing.assert_close(q.grad[0, 0], expected_grad)
    q_high = torch.ones(1, 1, 32, requires_grad=True)
    learner.pinball(q_high, torch.tensor([[.5]])).backward()
    torch.testing.assert_close(q_high.grad[0, 0], (1 - (torch.arange(32) + .5) / 32) / 32)


class RewardProbe(SyntheticAdapter):
    def __init__(self):
        super().__init__(seed=8, horizon=4)
        self.rewards = []
        self.commands = []

    def step(self, actions):
        obs, _scalar, done, truncated, info = super().step(actions)
        self.rewards.append(sum(info["rewards_dict"].values()))
        self.commands.append(actions.copy())
        return obs, 999.0, done, truncated, info

    def close(self):
        pass


def test_collector_reward_preaction_context_recurrent_replay_and_evaluation():
    actor, _ = learner.models(8, "SCALAR")
    env, rows, counts = RewardProbe(), [], study.new_counts()
    batch, row = learner.collect_episode(env, actor, 123, learner.action_generator(8, "SCALAR"),
                                         "train", 0, lambda: None, counts, rows.append, horizon=4)
    assert row["J"] == pytest.approx(sum(env.rewards) / 4)
    assert row["reward_sum"] < 10  # Ignoring the deliberately wrong adapter scalar.
    assert batch["critic"].shape == (4, 137)
    torch.testing.assert_close(batch["critic"][:, -1], torch.tensor(
        [sum(env.rewards[:t]) / 4 for t in range(4)], dtype=torch.float32))
    torch.testing.assert_close(batch["critic"][:, 115], torch.arange(4) / 4)
    assert torch.count_nonzero(batch["obs"][0, :, -4:]) == 0
    np.testing.assert_array_equal(batch["obs"][1, :, -4:-1], env.commands[0])
    assert torch.count_nonzero(batch["obs"][:, :, -1]) == 0
    assert torch.count_nonzero(batch["hidden"][0]) == 0
    assert torch.count_nonzero(batch["hidden"][2]) > 0
    replay = {key: value[None] for key, value in batch.items()}
    mean, _ = learner.recurrent_outputs(actor, replay, chunk=2)
    torch.testing.assert_close(tanh_log_prob(replay["u"], mean, actor.log_std), replay["logp"], atol=2e-6, rtol=2e-6)
    before = copy.deepcopy(actor.state_dict())
    result, _ = learner.collect_episode(env, actor, 124, learner.action_generator(8, "SCALAR", 0),
                                        "eval", 0, lambda: None, counts, rows.append, horizon=4)
    assert result is None and counts["optimizer_steps"] == 0
    assert counts["train_team_steps"] == counts["eval_team_steps"] == 4
    assert all(torch.equal(value, actor.state_dict()[name]) for name, value in before.items())


@pytest.mark.parametrize("arm", learner.ARMS)
def test_frozen_advantages_targets_and_four_real_synthetic_updates(arm, monkeypatch):
    actor, critic = learner.models(9, arm)
    rng = torch.Generator().manual_seed(456)
    rollout = dict(obs=torch.randn(16, 4, 5, 108, generator=rng),
                   hidden=torch.randn(16, 4, 5, 64, generator=rng),
                   critic=torch.randn(16, 4, 137, generator=rng),
                   u=torch.randn(16, 4, 5, 3, generator=rng), G=torch.arange(16) / 20)
    with torch.no_grad():
        mean, _ = learner.recurrent_outputs(actor, rollout, 2)
        rollout["logp"] = tanh_log_prob(rollout["u"], mean, actor.log_std)
    batch = learner.frozen_batch(critic, [{key: value[i] for key, value in rollout.items()} for i in range(16)])
    baseline, advantage = batch["baseline"].clone(), batch["advantages"].clone()
    assert not any(value.requires_grad for value in batch.values())
    assert int((batch["scores"] < 0).sum()) == 3
    assert torch.count_nonzero(batch["advantages"][4:]) > 0  # Whole-score subtraction outside tail.
    with torch.no_grad():
        predictions = critic(batch["critic"])
        if arm == "SCALAR":
            torch.testing.assert_close(baseline, predictions)
            expected_loss = (predictions - batch["scores"][:, None]).square().mean()
        else:
            torch.testing.assert_close(baseline, learner.tail_score(predictions, batch["eta"]).mean(-1))
            expected_loss = learner.pinball(predictions, batch["G"][:, None].expand(16, 4))
    seen = []
    source_loss = learner.clipped_policy_loss
    def observed_loss(new, old, advantages, mask):
        seen.append(advantages.clone())
        return source_loss(new, old, advantages, mask)
    monkeypatch.setattr(learner, "clipped_policy_loss", observed_loss)
    records, counts = [], study.new_counts()
    start_actor = torch.cat([p.detach().flatten() for p in actor.parameters()]).clone()
    start_critic = torch.cat([p.detach().flatten() for p in critic.parameters()]).clone()
    learner.update(actor, critic, learner.optimizer_for(actor, critic), batch,
                   lambda: None, counts, records.append, chunk=2)
    assert counts["optimizer_steps"] == counts["optimizer_attempts"] == 4
    assert len(seen) == 4 and all(torch.equal(value, advantage) for value in seen)
    assert torch.equal(batch["baseline"], baseline)
    assert records[0]["critic_loss"] == pytest.approx(float(expected_loss))
    assert all(record["actor_grad_norm"] > 0 and record["critic_grad_norm"] > 0 for record in records)
    assert not torch.equal(start_actor, torch.cat([p.detach().flatten() for p in actor.parameters()]))
    assert not torch.equal(start_critic, torch.cat([p.detach().flatten() for p in critic.parameters()]))


def test_agent_reducer_and_own_tail_publication(tmp_path):
    advantage = torch.tensor([[.1, -.2]])
    old = torch.zeros(1, 2, 5)
    new = torch.tensor([1.5, .7, 1.1, .9, 1.]).log().expand_as(old)
    result = learner.clipped_policy_loss(new, old, advantage, torch.ones_like(old, dtype=torch.bool))
    # Positive row: .12+.07+.11+.09+.10; negative: -.30-.16-.22-.18-.20.
    assert float(result) == pytest.approx(.285)
    # Opposite worst worlds: both own tails are .1, but the tail of differences is -.8.
    scalar = [.1] * 64 + [.9] * 192
    quantile = [.9] * 192 + [.1] * 64
    pair = learner.contrast(scalar, quantile)
    assert pair["delta_tail"] == pytest.approx(0)
    assert pair["branch"] == "INSIDE_MEI"
    assert learner.contrast([0.] * 256, [.01] * 256)["branch"] == "INSIDE_MEI"
    assert learner.contrast([.01] * 256, [0.] * 256)["branch"] == "INSIDE_MEI"
    assert learner.contrast(scalar, [v + .02 for v in quantile])["branch"] == "Q32_ABOVE_MEI"
    assert learner.contrast(scalar, [v - .02 for v in quantile])["branch"] == "SCALAR_ABOVE_MEI"
    paths = []
    for arm, returns in zip(learner.ARMS, (scalar, quantile)):
        path = tmp_path / f"{arm}.json"
        study.write_json(path, dict(arm=arm, seed=9601, status="complete", counts=dict(
            train_episodes=512, eval_episodes=256, optimizer_steps=128),
            endpoint=learner.endpoint(returns), wall_seconds_through_closeout=2))
        paths.append(path)
    output = tmp_path / "summary.json"
    study.publish_pair(*paths, output, "synthetic-publication-fixture")
    saved = json.loads(output.read_text())
    assert saved["delta_tail"] == 0 and len(saved["SCALAR"]["returns"]) == 256
    broken = json.loads(paths[1].read_text())
    broken["status"] = "incomplete"
    study.write_json(paths[1], broken)
    with pytest.raises(ValueError, match="missing complete"):
        study.publish_pair(*paths, output, "fixture")
    with pytest.raises(ValueError, match="256 finite"):
        learner.endpoint([0.] * 255 + [float("nan")])
