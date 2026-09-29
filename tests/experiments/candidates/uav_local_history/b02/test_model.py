import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.learner import clipped_policy_loss
from experiments.candidates.uav_local_history.b02.model import (
    categorical_terms, optimizers, sample_action, templates,
)


def test_set_actor_permutation_padding_empty_and_leading_dims():
    actor, _ = templates(291021)
    context = torch.randn(2, 3, 5, 107)
    points = torch.randn(2, 3, 5, 64, 7)
    valid = torch.zeros(2, 3, 5, 64, dtype=torch.bool)
    valid[..., :3] = True
    with torch.no_grad():
        base = actor(context, points, valid)
        permutation = torch.randperm(64)
        permuted = actor(context, points[..., permutation, :], valid[..., permutation])
        torch.testing.assert_close(base, permuted, atol=1e-6, rtol=1e-6)
        padded = points.clone()
        padded[..., 3:, :] = float('nan')
        torch.testing.assert_close(base, actor(context, padded, valid), atol=0, rtol=0)
        empty = actor(context, points, torch.zeros_like(valid))
        expected = actor.actor(torch.cat((context, torch.zeros(*context.shape[:-1], 128)), -1))
        torch.testing.assert_close(empty, expected, atol=0, rtol=0)
        assert base.shape == (2, 3, 5, 27)
        assert actor(context[0, 0, 0], points[0, 0, 0], valid[0, 0, 0]).shape == (27,)


def test_template_seed_isolated_and_separate_optimizer_groups():
    before = torch.random.get_rng_state().clone()
    actor, critic = templates(291021)
    assert torch.equal(before, torch.random.get_rng_state())
    actor2, critic2 = templates(291021)
    for left, right in zip(actor.parameters(), actor2.parameters()):
        torch.testing.assert_close(left, right, atol=0, rtol=0)
    for left, right in zip(critic.parameters(), critic2.parameters()):
        torch.testing.assert_close(left, right, atol=0, rtol=0)
    aopt, copt = optimizers(actor, critic)
    assert set(aopt.param_groups[0]['params']).isdisjoint(copt.param_groups[0]['params'])
    for opt in (aopt, copt):
        group = opt.param_groups[0]
        assert group['lr'] == 3e-4
        assert group['betas'] == (.9, .999)
        assert group['eps'] == 1e-8
        assert group['weight_decay'] == 0
        assert group['foreach'] is False
        assert group['fused'] is False


def test_explicit_sampling_density_and_greedy_no_rng():
    logits = torch.tensor([[0., 1., 1.] + [0.]*24,
                           [3., 0., -1.] + [0.]*24])
    generator1 = torch.Generator(device='cpu').manual_seed(31)
    generator2 = torch.Generator(device='cpu').manual_seed(31)
    action, logp, entropy = sample_action(logits, generator1)
    repeated, _, _ = sample_action(logits, generator2)
    torch.testing.assert_close(action, repeated, atol=0, rtol=0)
    expected_logp = logits.log_softmax(-1).gather(-1, action[:, None]).squeeze(-1)
    expected_entropy = -(logits.log_softmax(-1).exp() * logits.log_softmax(-1)).sum(-1)
    torch.testing.assert_close(logp, expected_logp)
    torch.testing.assert_close(entropy, expected_entropy)
    torch.testing.assert_close(categorical_terms(logits, action)[0], logp)
    changed = logits.clone()
    changed[:, 0] += 0.7
    new_logp, _ = categorical_terms(changed, action)
    ratio = (new_logp - logp).exp()
    advantage = torch.tensor([[0.7]])
    expected_policy = -torch.minimum(ratio * 0.7, ratio.clamp(0.8, 1.2) * 0.7).sum()
    actual_policy = clipped_policy_loss(new_logp.reshape(1, 1, 2),
                                        logp.reshape(1, 1, 2), advantage,
                                        torch.ones(1, 1, 2, dtype=torch.bool))
    torch.testing.assert_close(actual_policy, expected_policy)
    before = torch.random.get_rng_state().clone()
    local_before = generator1.get_state().clone()
    greedy, _, _ = sample_action(logits, generator1, greedy=True)
    torch.testing.assert_close(greedy, torch.tensor([1, 0]), atol=0, rtol=0)
    assert torch.equal(before, torch.random.get_rng_state())
    assert torch.equal(local_before, generator1.get_state())
