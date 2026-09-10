"""B04 actual-command density, private initialization and opening-only credit."""
import torch

from experiments.candidates.ucope.uav_motion_prefix_b01 import learner, study
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import (
    arm_copy, exposure, generator, joint_terms, sample, snapshot, tanh_log_prob, templates)


def nonzero_head(actor):
    # A known command/recurrent dependency, independent of initialization luck.
    with torch.no_grad():
        actor.duration[0].weight.zero_()
        actor.duration[0].bias.zero_()
        actor.duration[0].weight[0, 0] = .4
        actor.duration[0].weight[0, 64] = 1.2
        actor.duration[2].weight.zero_()
        actor.duration[2].bias.zero_()
        actor.duration[2].weight[0, 0] = .8
        actor.duration[2].weight[1, 0] = -.6


def test_private_initialization_counts_uniform_and_exposure():
    state = torch.random.get_rng_state().clone()
    vrng, drng = generator(720100021), generator(720100022)
    before_v, before_d = vrng.get_state(), drng.get_state()
    common = templates(7201)
    actor, critic = arm_copy(common, True, duration_head_seed=720100012)
    ga, gc = arm_copy(common, False)
    assert torch.equal(state, torch.random.get_rng_state())
    assert torch.equal(before_v, vrng.get_state()) and torch.equal(before_d, drng.get_state())
    for key, value in ga.state_dict().items():
        assert torch.equal(value, actor.state_dict()[key])
    for left, right in zip(critic.parameters(), gc.parameters()):
        assert torch.equal(left, right)
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(720100012)
        expected_hidden = torch.nn.Linear(67, 32)
    assert actor.duration[0].in_features == 67 and actor.duration[0].out_features == 32
    assert isinstance(actor.duration[1], torch.nn.Tanh)
    assert actor.duration[2].in_features == 32 and actor.duration[2].out_features == 2
    assert torch.equal(actor.duration[0].weight, expected_hidden.weight)
    assert torch.equal(actor.duration[0].bias, expected_hidden.bias)
    inputs = torch.linspace(-2, 2, 335).reshape(5, 67)
    assert torch.equal(actor.duration(inputs).softmax(-1), torch.full((5, 2), .5))
    initial = snapshot(actor, critic)
    assert {k: v.numel() for k, v in initial.items()} == {
        "common_actor": 32134, "critic": 34177, "duration": 2242,
        "duration_hidden": 2176, "duration_final": 66, "total": 68553}
    assert snapshot(ga, gc)["total"].numel() == 66311
    with torch.no_grad():
        actor.duration[2].bias[0] = .5
    observed = exposure(initial, actor, critic)
    assert observed["duration_final"]["initial_norm"] == 0
    assert observed["duration_final"]["displacement"] == .5
    assert observed["duration_final"]["final_norm"] == .5
    assert observed["duration_final"]["relative_displacement"] is None
    assert observed["duration_hidden"]["relative_displacement"] == 0
    old, old_critic = arm_copy(common, True)
    old_initial = snapshot(old, old_critic)
    with torch.no_grad():
        old.duration.bias[0] = .5
    assert exposure(old_initial, old, old_critic)["duration"]["relative_displacement"] == .5 / 1e-12


def test_sample_condition_and_recomputed_density_detach_mask():
    actor, _ = arm_copy(templates(9001), True, duration_head_seed=900100012)
    nonzero_head(actor)
    seen = []
    hook = actor.duration.register_forward_pre_hook(lambda module, args: seen.append(args[0].detach().clone()))
    mean = torch.zeros(5, 3)
    recurrent = torch.zeros(5, 64)
    vrng, drng = generator(41), generator(42)
    with torch.no_grad():
        u, duration = sample(actor, mean, recurrent, [True]*5, True, vrng, drng)
        assert len(seen) == 5
        torch.testing.assert_close(torch.stack(seen)[:, 64:], u.tanh(), rtol=0, atol=0)
        assert u[:, 0].var() > 0
        probabilities = actor.duration(torch.cat((recurrent, u.tanh()), -1)).softmax(-1)
        assert probabilities[:, 0].var() > 0
        mask = torch.ones(5, dtype=torch.bool)
        behavior, _ = joint_terms(actor, mean, recurrent, u, duration, mask, mask, "agent_compound")
        expected = tanh_log_prob(u, mean, actor.log_std) + probabilities.log().gather(1, duration[:, None])[:, 0]
        torch.testing.assert_close(behavior, expected)
        state = drng.get_state().clone()
        seen.clear()
        sample(actor, mean, recurrent, [False]*5, False, vrng, drng)
        assert not seen and torch.equal(state, drng.get_state())
        # Current means/features change; stored action remains the condition.
        actor.mean.bias.add_(.3)
        actor.duration[2].bias[0].add_(.1)
    mean = torch.full((2, 5, 3), .3, requires_grad=True)
    rec = torch.full((2, 5, 64), .2, requires_grad=True)
    stored = torch.stack((u, u)).requires_grad_()
    durations = torch.stack((duration, duration))
    vm = torch.tensor([[True]*5, [True, False, True, False, False]])
    dm = torch.tensor([[True]*5, [False]*5])
    seen.clear()
    lp, entropy = joint_terms(actor, mean, rec, stored, durations, vm, dm, "agent_compound")
    assert lp.shape == (2, 5) and entropy.shape == (2,)
    assert len(seen) == 1 and seen[0].shape == (5, 67)
    torch.testing.assert_close(seen[0][:, 64:], u.tanh(), rtol=0, atol=0)
    velocity = torch.where(vm, tanh_log_prob(stored, mean, actor.log_std), 0)
    expected_logits = actor.duration(torch.cat((rec[0], u.detach().tanh()), -1))
    expected = expected_logits.log_softmax(-1).gather(-1, duration[:, None])[:, 0]
    torch.testing.assert_close(lp[0], velocity[0] + expected)
    torch.testing.assert_close(lp[1], velocity[1])
    action_grad, rec_grad, hidden_grad, final_grad = torch.autograd.grad(
        lp.sum(), (stored, rec, actor.duration[0].weight, actor.duration[2].weight), retain_graph=True)
    velocity_grad, = torch.autograd.grad(velocity.sum(), stored)
    torch.testing.assert_close(action_grad, velocity_grad, rtol=0, atol=0)
    assert rec_grad[0].abs().sum() > 0 and not rec_grad[1].any()
    assert hidden_grad.abs().sum() > 0 and final_grad.abs().sum() > 0
    seen.clear()
    held_lp, _ = joint_terms(actor, mean, rec, stored, durations, vm, torch.zeros_like(dm), "agent_compound")
    assert not seen
    torch.testing.assert_close(held_lp, velocity.detach())
    hook.remove()


def test_collector_and_update_use_only_actual_openings(monkeypatch):
    actor, critic = arm_copy(templates(9001), True, duration_head_seed=900100012)
    choices = iter([0, 1, 0, 1, 1]*2)
    monkeypatch.setattr(torch, "multinomial", lambda *args, **kwargs: torch.tensor([next(choices)]))
    inputs = []
    hook = actor.duration.register_forward_pre_hook(lambda module, args: inputs.append(args[0].detach().clone()))
    counts = study.new_counts()
    episodes = [learner.collect_episode(
        SyntheticAdapter(9001), actor, critic, 8, 9001 + e, generator(22), generator(23),
        {"arm": "T", "phase": "train", "episode": e}, lambda: None, counts,
        lambda row: None, lambda row: None, [], ratio_grouping="agent_compound") for e in range(2)]
    assert [tuple(x.shape) for x in inputs] == ([(67,)]*5 + [(5, 67)])*2
    for ep in episodes:
        mask = ep["velocity_mask"]
        assert mask[0].all() and mask[4:].all()
        assert mask[1:4, [0, 2]].all() and not mask[1:4, [1, 3, 4]].any()
        assert ep["duration_mask"][0].all() and not ep["duration_mask"][1:].any()
        assert ep["logp"].shape == (8, 5) and not ep["logp"][~mask].any()
    assert counts["duration_decisions"] == 10 and counts["velocity_decisions"] == 62
    inputs.clear()
    expected_condition = torch.cat([ep["u"][0].tanh() for ep in episodes])
    records = learner.update(actor, critic, learner.optimizer_for(actor, critic), episodes, 8,
                             lambda: None, counts, ratio_grouping="agent_compound", entropy_coef=0.)
    assert len(records) == counts["optimizer_steps"] == 4
    assert len(inputs) == 4 and all(x.shape == (10, 67) for x in inputs)
    for x in inputs:
        torch.testing.assert_close(x[:, 64:], expected_condition, rtol=0, atol=0)
    hook.remove()
