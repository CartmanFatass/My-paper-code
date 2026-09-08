"""B02 credit checks on deterministic tensors and the existing synthetic adapter."""
import math

import pytest
import torch

from experiments.candidates.ucope.uav_motion_prefix_b01 import learner, study
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import (
    arm_copy, generator, joint_terms, tanh_log_prob, templates)


def test_agent_grouping_and_signed_clipping():
    new = torch.full((1, 5), math.log(1.05), requires_grad=True)
    old = torch.zeros_like(new)
    loss = learner.clipped_policy_loss(new, old, torch.ones(1), torch.ones_like(new, dtype=torch.bool))
    assert loss.item() == pytest.approx(-5.25)
    loss.backward()
    torch.testing.assert_close(new.grad, torch.full_like(new, -1.05))
    joint = learner.clipped_policy_loss(new.sum(-1), old.sum(-1), torch.ones(1))
    assert joint.item() == pytest.approx(-1.2)
    ratios = torch.tensor([[1.4, .6, 1.1, .9, 1.], [1.4, .6, 1.1, .9, 1.], [1.]*5])
    new = ratios.log().requires_grad_()
    mask = torch.tensor([[True]*4 + [False], [True]*4 + [False], [False]*5])
    loss = learner.clipped_policy_loss(new, torch.zeros_like(new), torch.tensor([1., -1., 3.]), mask)
    # Positive row: 1.2+.6+1.1+.9; negative row: -(1.4+.8+1.1+.9).
    assert loss.item() == pytest.approx((4.2 - 3.8)/3, abs=1e-6)
    loss.backward()
    expected = torch.tensor([[0., -.6, -1.1, -.9, 0.], [1.4, 0., 1.1, .9, 0.], [0.]*5])/3
    torch.testing.assert_close(new.grad, expected)


def test_behavior_gradient_scale_matches_joint_reference():
    mask = torch.tensor([[[True]*5, [True, False, True, False, False], [False]*5],
                         [[False, True, False, True, True], [True]*5, [False]*5]])
    advantage = torch.tensor([[1., -2., 3.], [-.5, .7, -1.]])
    new = torch.linspace(-2., 2., 30).reshape(2, 3, 5).requires_grad_()
    old = new.detach().clone()
    agent_loss = learner.clipped_policy_loss(new, old, advantage, mask)
    agent_grad, = torch.autograd.grad(agent_loss, new)
    joint_ratio = torch.exp(torch.where(mask, new-old, 0).sum(-1))
    reference_grad, = torch.autograd.grad(-(joint_ratio*advantage).mean(), new)
    torch.testing.assert_close(agent_grad, reference_grad, rtol=1e-5, atol=1e-6)
    assert not agent_grad[~mask].any()


def test_compound_density_keeps_owner_and_duration_at_opening():
    actor, _ = arm_copy(templates(9001), True)
    mean = torch.zeros(2, 5, 3, requires_grad=True)
    u = torch.linspace(-.7, .8, 30).reshape(2, 5, 3)
    rec = torch.zeros(2, 5, 64)
    vm = torch.tensor([[True]*5, [True, False, True, False, False]])
    dm = torch.tensor([[True]*5, [False]*5])
    durations = torch.tensor([[0, 1, 0, 1, 1], [0]*5])
    lp, entropy = joint_terms(actor, mean, rec, u, durations, vm, dm, "agent_compound")
    expected = torch.where(vm, tanh_log_prob(u, mean, actor.log_std), 0) - dm*math.log(2)
    torch.testing.assert_close(lp, expected)
    old_joint, old_entropy = joint_terms(actor, mean, rec, u, durations, vm, dm)
    torch.testing.assert_close(lp.sum(-1), old_joint)
    torch.testing.assert_close(entropy, old_entropy, rtol=0, atol=0)
    grad, = torch.autograd.grad(lp[0, 1], mean, retain_graph=True)
    assert grad[0, 1].count_nonzero() == 3 and grad.count_nonzero() == 3
    duration_grad, = torch.autograd.grad(lp[0, 1], actor.duration.bias, retain_graph=True)
    torch.testing.assert_close(duration_grad, torch.tensor([-.5, .5]))
    later_grad, = torch.autograd.grad(lp[1].sum(), actor.duration.bias)
    assert not later_grad.any()


@pytest.mark.parametrize("treatment", [True, False])
def test_collected_vector_and_real_update(treatment, monkeypatch):
    actor, critic = arm_copy(templates(9001), treatment)
    def scripted(actor, mean, recurrent, active, opening, vrng, drng):
        return torch.full((5, 3), .3), torch.tensor([0, 1, 0, 1, 1]) if opening and treatment else torch.zeros(5, dtype=torch.long)
    monkeypatch.setattr(learner, "sample", scripted)
    counts = study.new_counts()
    episodes = [learner.collect_episode(
        SyntheticAdapter(9001), actor, critic, 8, 9001 + e, generator(22), generator(23),
        {"arm": "T" if treatment else "G", "phase": "train", "episode": e},
        lambda: None, counts, lambda row: None, lambda row: None, [],
        ratio_grouping="agent_compound") for e in range(2)]
    for ep in episodes:
        assert ep["logp"].shape == (8, 5) and not ep["logp"].requires_grad
        assert ep["value"].shape == ep["reward"].shape == (8,)
        assert not ep["logp"][~ep["velocity_mask"]].any()
        assert ep["duration_mask"][0].all() == treatment
        assert not ep["duration_mask"][1:].any()
    assert counts["velocity_decisions"] == (62 if treatment else 80)
    assert counts["duration_decisions"] == (10 if treatment else 0)
    stored = torch.stack([ep["logp"] for ep in episodes]).clone()
    original_loss = learner.clipped_policy_loss
    seen = []
    def inspect_loss(new, old, advantage, velocity_mask=None):
        assert new.shape == old.shape == (2, 8, 5)
        assert new.requires_grad and not old.requires_grad and not advantage.requires_grad
        assert advantage.shape == (2, 8) and velocity_mask.shape == old.shape
        torch.testing.assert_close(old, stored, rtol=0, atol=0)
        loss = original_loss(new, old, advantage, velocity_mask)
        gradient, = torch.autograd.grad(loss, new, retain_graph=True)
        assert gradient[velocity_mask].abs().sum() > 0 and not gradient[~velocity_mask].any()
        seen.append(True)
        return loss
    monkeypatch.setattr(learner, "clipped_policy_loss", inspect_loss)
    optimizer = learner.optimizer_for(actor, critic)
    rng = torch.random.get_rng_state().clone()
    learner.update(actor, critic, optimizer, episodes, 8, lambda: None, counts, "agent_compound")
    assert len(seen) == counts["optimizer_steps"] == 4
    assert all(int(state["step"]) == 4 for state in optimizer.state.values())
    assert torch.equal(rng, torch.random.get_rng_state())


def test_vector_nonfinite_stops_before_step(monkeypatch):
    actor, critic = arm_copy(templates(9001), False)
    monkeypatch.setattr(learner, "joint_terms", lambda *args: (torch.tensor([0., 0., float("nan"), 0., 0.]), 0))
    counts = study.new_counts()
    with pytest.raises(FloatingPointError, match="nonfinite sampled density"):
        learner.collect_episode(SyntheticAdapter(9001), actor, critic, 8, 9001, generator(22), generator(23),
                                {"arm": "G", "phase": "train", "episode": 0}, lambda: None,
                                counts, lambda row: None, lambda row: None, [], ratio_grouping="agent_compound")
    assert counts["team_steps"] == counts["step_calls"] == 0
