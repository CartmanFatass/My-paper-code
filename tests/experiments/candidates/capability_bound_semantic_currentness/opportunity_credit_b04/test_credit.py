"""Constructed-array checks, executed inside the one selected engineering call."""
from types import SimpleNamespace
import torch
from experiments.candidates.capability_bound_semantic_currentness.opportunity_credit_b04.learner import (
    opportunity_targets, decision_value_loss,
)
from experiments.candidates.capability_bound_semantic_currentness.opportunity_credit_b04.run import request_only


def test_constructed_credit():
    rewards = torch.zeros((8, 152), dtype=torch.float32, requires_grad=True)
    with torch.no_grad():
        rewards[:, 12::6] = torch.arange(192).reshape(8, 24) / 192
        rewards[:, 13::6] = 0.4
        # Delayed REFRESH's actual sampled decision/settlement example, including q23.
        rewards[0, 150], rewards[0, 151] = -0.4, 1.0
    old = torch.full_like(rewards, 0.2, requires_grad=True)
    target = opportunity_targets(rewards, old)
    expected = rewards.detach()[:, 12::6] + rewards.detach()[:, 13::6]
    torch.testing.assert_close(target.value_targets[:, 12::6], expected)
    torch.testing.assert_close(target.value_targets[0, 150], torch.tensor(0.6))
    local = expected - 0.2
    torch.testing.assert_close(target.advantages[:, 12::6], local)
    centered = local - local.mean()
    torch.testing.assert_close(target.decision_advantages[:, 12::6],
                               centered / (centered.square().mean().sqrt() + 1e-8))
    assert all(not x.requires_grad for x in
               (target.advantages, target.value_targets, target.decision_advantages))
    changed = rewards.detach().clone()
    changed[:, 151] += 7
    future = opportunity_targets(changed, old)
    torch.testing.assert_close(target.advantages[:, :150], future.advantages[:, :150])
    torch.testing.assert_close(target.value_targets[:, :150], future.value_targets[:, :150])
    assert not torch.equal(target.decision_advantages[:, 12], future.decision_advantages[:, 12])
    # Source reward/value mutations do not mutate the once-built targets.
    frozen = target.value_targets.clone()
    with torch.no_grad():
        rewards.add_(3)
        old.add_(2)
    torch.testing.assert_close(target.value_targets, frozen)
    decisions = torch.zeros((2, 152), dtype=torch.bool)
    decisions[:, 12::6] = True
    values = torch.zeros((2, 152), requires_grad=True)
    loss = decision_value_loss(values, frozen[:2], decisions)
    torch.testing.assert_close(loss, frozen[:2][decisions].square().sum() / 48)
    loss.backward()
    assert torch.count_nonzero(values.grad[~decisions]) == 0
    altered_values = values.detach().clone()
    altered_values[~decisions] = 100
    torch.testing.assert_close(loss.detach(), decision_value_loss(altered_values, frozen[:2], decisions))
    # This checks direct output loss only; shared recurrent history may receive gradients.
    public = [SimpleNamespace(request_active=False) for _ in range(152)]
    for q in range(24):
        public[12 + 6*q].request_active = q % 2 == 0
    assert request_only(public) == ["REFRESH", "SAFE_FALLBACK"] * 12
