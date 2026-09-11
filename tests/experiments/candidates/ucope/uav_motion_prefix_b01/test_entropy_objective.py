"""B03 actual-update objective checks on fixed tensors, without environment calls."""
import copy

import pytest
import torch

from experiments.candidates.ucope.uav_motion_prefix_b01 import learner, study
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import arm_copy, joint_terms, templates


def test_actual_entropy_coefficient_and_default_gradients(monkeypatch):
    actor, critic = arm_copy(templates(9001), True)
    with torch.no_grad():
        # Nonuniform categorical probabilities expose its entropy derivative too.
        actor.duration.bias.copy_(torch.tensor([.5, -.5]))
    vm = torch.tensor([[[True]*5, [True, False, True, False, True]],
                       [[True]*5, [False]*5]])
    dm = torch.tensor([[[True]*5, [False]*5]]*2)
    data = {"obs": torch.zeros(2, 2, 5, 108), "hidden": torch.zeros(2, 2, 5, 64),
            "critic": torch.zeros(2, 2, 136), "u": vm[..., None]*torch.full((2, 2, 5, 3), .25),
            "durations": torch.tensor([[[0, 1, 0, 1, 0], [0]*5], [[1]*5, [0]*5]]),
            "velocity_mask": vm, "duration_mask": dm, "reward": torch.tensor([[1., 2.], [3., 4.]])}
    with torch.no_grad():
        mean, recurrent = learner.recurrent_outputs(actor, data, 2)
        data["logp"] = joint_terms(actor, mean, recurrent, data["u"], data["durations"],
                                   vm, dm, "agent_compound")[0].clone()
        data["value"] = critic(data["critic"]).clone()
    episodes = [{key: value[e].clone() for key, value in data.items()} for e in range(2)]

    # Independent objective expression at the behavior policy (all ratios one).
    mean, recurrent = learner.recurrent_outputs(actor, data, 2)
    logp, entropy = joint_terms(actor, mean, recurrent, data["u"], data["durations"], vm, dm, "agent_compound")
    targets = torch.stack([data["reward"].sum(-1), data["reward"][:, 1]], dim=1)
    raw = targets-data["value"]
    advantage = ((raw-raw.mean())/(raw.std(unbiased=False)+1e-8)).detach()
    policy = -(vm*(logp-data["logp"]).exp()*advantage[..., None]).sum(-1).mean()
    value = (critic(data["critic"])-targets).square().mean()
    parameters = list(actor.parameters())+list(critic.parameters())
    native_grad = torch.autograd.grad(policy+.5*value, parameters, retain_graph=True, allow_unused=True)
    entropy_grad = torch.autograd.grad(entropy.mean(), parameters, allow_unused=True)
    native_grad = [torch.zeros_like(p) if g is None else g for p, g in zip(parameters, native_grad)]
    entropy_grad = [torch.zeros_like(p) if g is None else g for p, g in zip(parameters, entropy_grad)]
    names = list(dict(actor.named_parameters()))+['critic.'+n for n, _ in critic.named_parameters()]
    assert native_grad[names.index('log_std')].abs().sum() > 0
    assert native_grad[names.index('duration.bias')].abs().sum() > 0
    assert entropy_grad[names.index('log_std')].abs().sum() > 0
    assert entropy_grad[names.index('duration.bias')].abs().sum() > 0

    clip = torch.nn.utils.clip_grad_norm_
    captured = []
    def capture_before_clip(params, *args, **kwargs):
        params = list(params)
        captured.append([p.grad.detach().clone() for p in params])
        return clip(params, *args, **kwargs)
    monkeypatch.setattr(torch.nn.utils, 'clip_grad_norm_', capture_before_clip)
    results = {}
    for label, options in [('zero', {'entropy_coef': 0.0}), ('explicit', {'entropy_coef': .01}), ('default', {})]:
        a, c = copy.deepcopy((actor, critic))
        counts = study.new_counts()
        captured.clear()
        rng_before = torch.random.get_rng_state().clone()
        optimizer = learner.optimizer_for(a, c)
        records = learner.update(a, c, optimizer, episodes, 2, lambda: None, counts,
                                 ratio_grouping='agent_compound', **options)
        assert len(records) == counts['optimizer_steps'] == len(captured) == 4
        assert all(int(state['step']) == 4 for state in optimizer.state.values())
        assert torch.equal(rng_before, torch.random.get_rng_state())
        coefficient = options.get('entropy_coef', .01)
        for actual, base, ent in zip(captured[0], native_grad, entropy_grad):
            torch.testing.assert_close(actual, base-coefficient*ent, rtol=1e-5, atol=1e-6)
        for row in records:
            assert row['loss'] == pytest.approx(row['policy_loss']+.5*row['value_loss']-coefficient*row['entropy'],
                                                rel=1e-5, abs=1e-6)
        results[label] = (records, [p.detach().clone() for p in list(a.parameters())+list(c.parameters())])
    assert results['zero'][0][0]['entropy'] == results['explicit'][0][0]['entropy']
    assert results['zero'][0][0]['entropy'] > 0  # Still reported, unweighted.
    assert results['default'][0] == results['explicit'][0]
    for implicit, explicit in zip(results['default'][1], results['explicit'][1]):
        torch.testing.assert_close(implicit, explicit, rtol=1e-5, atol=1e-6)
