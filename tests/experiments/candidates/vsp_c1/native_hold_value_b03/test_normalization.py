"""Tiny deterministic arithmetic/gradient checks; no native environment or fit."""
from collections import defaultdict

import numpy as np
import pytest
import torch

from experiments.candidates.ucope.uav_motion_prefix_b01 import learner
from experiments.candidates.vsp_c1.native_hold_value_b03.value_normalization import ValueMoments


def test_population_merge_floor_and_detachment():
    moments = ValueMoments()
    assert moments.state() == dict(n=0, mean=0., M2=0., scale=1., updates=0)
    moments.update(torch.tensor([1., 3.], requires_grad=True))
    moments.update(torch.tensor([5., 7.], requires_grad=True))
    assert moments.n == 4 and moments.updates == 2
    assert moments.mean == 4 and moments.M2 == 20
    assert moments.scale == pytest.approx(5 ** .5)
    assert moments.mean.dtype == moments.M2.dtype == torch.float32
    assert not moments.mean.requires_grad and not moments.M2.requires_grad
    assert not any(isinstance(v, torch.nn.Parameter) for v in vars(moments).values())
    assert not moments.normalize(torch.ones(2, requires_grad=True)).requires_grad
    raw = torch.tensor(2., requires_grad=True)
    moments.decode(raw).backward()
    assert raw.grad == pytest.approx(5 ** .5)
    constant = ValueMoments()
    constant.update(torch.full((3,), 7.))
    assert constant.scale == pytest.approx(1e-4)


@pytest.mark.parametrize("normalized", [False, True])
def test_collection_uses_old_native_values_without_updates(monkeypatch, normalized):
    class Env:
        def reset(self, seed):
            return None, dict(state=None)
        def step(self, action):
            return None, None, False, False, dict(next_state=None)
    class Actor:
        duration = object()
        def __call__(self, obs, hidden):
            return torch.zeros(1, 5, 3), torch.zeros(1, 5, 64), hidden
    monkeypatch.setattr(learner, "own_positions", lambda obs: np.zeros((5, 3)))
    monkeypatch.setattr(learner, "actor_features", lambda *a: np.zeros((5, 4), np.float32))
    monkeypatch.setattr(learner, "critic_features", lambda *a: np.zeros(4, np.float32))
    monkeypatch.setattr(learner, "team_reward", lambda info: 3.)
    monkeypatch.setattr(learner, "sample", lambda *a: (torch.zeros(5, 3), torch.ones(5, dtype=torch.long)))
    monkeypatch.setattr(learner, "joint_terms", lambda *a: (torch.zeros(5), torch.zeros(5)))
    moments = ValueMoments()
    moments.update(torch.tensor([8., 12.]))
    before = moments.state()
    for e in range(2):
        result = learner.collect_episode(Env(), Actor(), lambda x: torch.tensor(2.), 2,
            e, None, None, dict(phase="train"), lambda: None, defaultdict(int),
            lambda r: None, lambda r: None, [], ratio_grouping="agent_compound",
            value_moments=moments if normalized else None)
        torch.testing.assert_close(result["value"], torch.full((2,), 14. if normalized else 2.))
        assert moments.state() == before
        torch.testing.assert_close(result["reward"], torch.full((2,), 3.))


@pytest.mark.parametrize("normalized", [False, True])
def test_update_native_advantage_fixed_targets_four_epochs_and_gradients(monkeypatch, normalized):
    class Tiny(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.p = torch.nn.Parameter(torch.tensor(.25))
        def forward(self, x):
            return self.p.expand(x.shape[:-1])
    actor, critic = Tiny(), Tiny()
    class NoStep:
        def zero_grad(self):
            actor.zero_grad(); critic.zero_grad()
        def step(self):
            pass
    episodes = []
    for rewards, values in (([1., 2.], [14., 10.]), ([3., 4.], [6., 8.])):
        episodes.append(dict(reward=torch.tensor(rewards), value=torch.tensor(values),
            critic=torch.zeros(2, 1), logp=torch.zeros(2, 1), u=torch.zeros(2, 1),
            durations=torch.zeros(2, 1), velocity_mask=torch.ones(2, 1, dtype=torch.bool),
            duration_mask=torch.ones(2, 1, dtype=torch.bool)))
    monkeypatch.setattr(learner, "recurrent_outputs", lambda *a: (None, None))
    monkeypatch.setattr(learner, "joint_terms", lambda *a: (actor.p.expand(2, 2, 1), actor.p.expand(2, 2, 1)))
    original_loss = learner.clipped_policy_loss
    seen, gradients = [], []
    def capture(new, old, advantage, mask):
        seen.append(advantage)
        return original_loss(new, old, advantage, mask)
    monkeypatch.setattr(learner, "clipped_policy_loss", capture)
    critic.p.register_hook(lambda grad: gradients.append(grad.clone()))
    moments = ValueMoments()
    moments.update(torch.tensor([8., 12.]))
    targets = torch.tensor([[3., 2.], [7., 4.]])
    raw = targets - torch.tensor([[14., 10.], [6., 8.]])
    expected_adv = (raw - raw.mean()) / (raw.std(unbiased=False) + 1e-8)
    expected_targets = (targets - 6.) / (70 / 6) ** .5 if normalized else targets
    counts = defaultdict(int)
    records = learner.update(actor, critic, NoStep(), episodes, 2, lambda: None,
        counts, ratio_grouping="agent_compound", value_moments=moments if normalized else None)
    assert len(seen) == len(records) == counts["optimizer_steps"] == 4
    assert all(x is seen[0] and not x.requires_grad for x in seen)
    for advantage in seen:
        torch.testing.assert_close(advantage, expected_adv)
    expected_loss = (.25 - expected_targets).square().mean()
    for row, grad in zip(records, gradients):
        assert row["value_loss"] == pytest.approx(float(expected_loss))
        assert row["loss"] == pytest.approx(row["policy_loss"] + .5 * row["value_loss"] - .01 * row["entropy"])
        torch.testing.assert_close(grad, (.25 - expected_targets).mean())
        assert ("value_loss_units" in row) == normalized
    if normalized:
        assert moments.n == 6 and moments.updates == 2
        assert moments.mean == 6 and moments.M2 == 70
    else:
        assert moments.n == 2 and moments.updates == 1
