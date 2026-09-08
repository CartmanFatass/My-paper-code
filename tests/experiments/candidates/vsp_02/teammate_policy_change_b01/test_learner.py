import copy

import pytest
import torch

from experiments.candidates.vsp_02.teammate_policy_change_b01.learner import (
    Agent, RecurrentPolicy, adam_summary, clipped_policy_loss, compute_gae,
    fork_agents, generator, make_optimizer, parameters, training_streams, update)

# This suite uses one complete synthetic rollout update and one interrupted update.
torch.set_num_threads(1)
torch.set_num_interop_threads(1)


def synthetic_rollout(model):
    rng = generator(123)
    obs = torch.randn(16, 48, 18, generator=rng)
    with torch.no_grad():
        logits, values, _ = model(obs)
        actions = torch.multinomial(logits.softmax(-1).reshape(-1, 4), 1,
                                    generator=rng).reshape(16, 48)
        log_probs = torch.distributions.Categorical(logits=logits).log_prob(actions)
    return dict(obs=obs, values=values, actions=actions, log_probs=log_probs,
                rewards=torch.randint(0, 2, (16, 48), generator=rng).float())


@pytest.fixture(scope='module')
def trained():
    torch.manual_seed(7)
    model = RecurrentPolicy()
    agent = Agent(model, make_optimizer(model), training_streams(7))
    before = parameters(model)
    records = []
    rollout = synthetic_rollout(model)
    update(agent, rollout, lambda: None, records.append)
    return agent, before, records, rollout


def test_architecture_and_recurrent_continuity():
    model = RecurrentPolicy()
    assert sum(p.numel() for p in model.parameters()) == 26501
    assert len(list(model.parameters())) == 10
    obs = torch.ones(2, 7, 18)
    logits, values, hidden = model(obs)
    assert logits.shape == (2, 7, 4) and values.shape == (2, 7)
    assert hidden.shape == (1, 2, 64)
    first, _, h = model(obs[:, :3])
    second, _, _ = model(obs[:, 3:], h)
    torch.testing.assert_close(torch.cat((first, second), 1), logits, atol=1e-6, rtol=1e-5)
    reset, _, _ = model(obs[:, 3:])
    assert not torch.allclose(reset, second)
    explicit, _, _ = model(obs, torch.zeros(1, 2, 64))
    torch.testing.assert_close(explicit, logits, atol=1e-6, rtol=1e-5)


def test_gae_and_clipped_arithmetic():
    advantages, targets = compute_gae(torch.tensor([[0., 1.]]), torch.tensor([[0.2, 0.4]]))
    torch.testing.assert_close(advantages, torch.tensor([[0.77, 0.6]]), atol=1e-6, rtol=1e-5)
    torch.testing.assert_close(targets, torch.tensor([[0.97, 1.]]), atol=1e-6, rtol=1e-5)
    loss = clipped_policy_loss(torch.tensor([1.5, 0.5]), torch.tensor([1., -1.]))
    assert loss.item() == pytest.approx(-0.2, abs=1e-6)
    # A reward just after a service-round boundary propagates through that boundary.
    adv, _ = compute_gae(torch.tensor([[0., 0., 0., 1.]]), torch.zeros(1, 4))
    assert adv[0, 2].item() == pytest.approx(0.95)
    assert adv[0, 0].item() == pytest.approx(0.95 ** 3)


def test_joint_update_moves_all_parameters_and_counts_actual_steps(trained):
    agent, before, records, _ = trained
    row = records[0]
    assert row['optimizer_steps'] == agent.global_steps == 16 and row['complete_update']
    assert torch.isfinite(parameters(agent.model)).all()
    assert (parameters(agent.model) - before).square().mean().sqrt() > 0
    assert row['max_pre_clip_gradient_norm'] > 0
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in agent.model.parameters())
    assert len(agent.optimizer.param_groups) == 1
    assert adam_summary(agent)['step_min'] == adam_summary(agent)['step_max'] == 16


def test_fork_full_state_independence_and_private_rng(trained):
    prefix = trained[0]
    before = parameters(prefix.model)
    global_rng = torch.random.get_rng_state().clone()
    arms = fork_agents(prefix, 7)
    assert torch.equal(global_rng, torch.random.get_rng_state())
    carry, reset = arms['CARRY'], arms['RESET']
    assert carry.global_steps == reset.global_steps == prefix.global_steps == 16
    assert len(carry.optimizer.state) == 10 and len(reset.optimizer.state) == 0
    for arm in arms.values():
        assert torch.equal(parameters(arm.model), before)
        assert arm.optimizer.param_groups[0]['lr'] == 0.0003
        assert arm.optimizer.param_groups[0]['params'][0] is next(arm.model.parameters())
        for original, descendant in zip(prefix.model.parameters(), arm.model.parameters()):
            assert original.data_ptr() != descendant.data_ptr()
    for original, descendant in zip(prefix.optimizer.state.values(), carry.optimizer.state.values()):
        for key in ('step', 'exp_avg', 'exp_avg_sq'):
            assert torch.equal(original[key], descendant[key])
            assert original[key].data_ptr() != descendant[key].data_ptr()
    for key in ('light', 'action', 'shuffle'):
        assert carry.streams[key] is not reset.streams[key]
        assert torch.equal(carry.streams[key].get_state(), reset.streams[key].get_state())
    torch.rand(20, generator=generator(7 + 101))  # Isolated evaluation light draw.
    torch.multinomial(torch.ones(8, 4), 1, generator=generator(7 + 102))
    assert torch.equal(torch.randint(0, 2, (16, 16), generator=carry.streams['light']),
                       torch.randint(0, 2, (16, 16), generator=reset.streams['light']))
    assert torch.equal(torch.randperm(16, generator=carry.streams['shuffle']),
                       torch.randperm(16, generator=reset.streams['shuffle']))
    with torch.no_grad():
        next(carry.model.parameters()).add_(1)
    next(iter(carry.optimizer.state.values()))['exp_avg'].add_(1)
    assert torch.equal(parameters(prefix.model), before)
    assert torch.equal(parameters(reset.model), before)


def test_interrupted_optimizer_reports_only_performed_steps(trained):
    agent = fork_agents(trained[0], 7)['RESET']
    calls = 0
    def cutoff():
        nonlocal calls
        calls += 1
        if calls == 5:
            raise TimeoutError('finite update cutoff')
    records = []
    with pytest.raises(TimeoutError):
        update(agent, trained[3], cutoff, records.append)
    assert records[0]['optimizer_steps'] == 2
    assert not records[0]['complete_update']
    assert agent.global_steps == 18
    assert adam_summary(agent)['step_max'] == 2
