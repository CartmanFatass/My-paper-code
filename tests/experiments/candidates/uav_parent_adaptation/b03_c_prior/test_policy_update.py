"""Synthetic contract checks; no native host or result-bearing episodes."""

import copy
import hashlib
import math

import pytest
import torch

from experiments.candidates.uav_parent_adaptation.b03_c_prior.policy import (
    Actor, Critic, address_seed, categorical_terms, optimizers, sample_actions, templates,
)
from experiments.candidates.uav_parent_adaptation.b03_c_prior.update import (
    _targets_advantages, update,
)


@pytest.fixture(autouse=True)
def one_thread():
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(previous)


def test_exact_init_rng_restore_prior_and_checkpoint(tmp_path):
    before = torch.random.get_rng_state().clone()
    actor, critic = templates(303031)
    assert torch.equal(before, torch.random.get_rng_state())
    assert sum(p.numel() for p in actor.parameters()) == 14361
    assert sum(p.numel() for p in critic.parameters()) == 34177
    assert all(p.requires_grad for p in actor.parameters())
    assert torch.count_nonzero(actor.table) == 0
    assert torch.count_nonzero(actor.mlp[4].weight) == 0
    assert torch.count_nonzero(actor.mlp[4].bias) == 0
    # Independent generator reconstructs only the four declared draws; constructor
    # draws must not shift this stream.
    generator = torch.Generator().manual_seed(100000 * 303031 + 11)
    for layer in (actor.mlp[0], actor.mlp[2]):
        bound = 1 / math.sqrt(layer.in_features)
        for parameter in (layer.weight, layer.bias):
            expected = torch.empty(parameter.shape, dtype=torch.float32).uniform_(
                -bound, bound, generator=generator)
            assert torch.equal(parameter, expected)
            assert float(parameter.abs().max()) <= bound
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(100000 * 303031 + 17)
        expected_critic = Critic()
    for actual, expected in zip(critic.parameters(), expected_critic.parameters()):
        assert torch.equal(actual, expected)
    generator.manual_seed(801)
    context = torch.randn(27, 120, generator=generator)
    indices = torch.arange(27)
    logits = actor(context, indices)
    expected_logits = torch.eye(27) * math.log(234)
    assert torch.equal(logits, expected_logits)
    assert torch.equal(logits.argmax(-1), indices)
    expected_probs = torch.full((27, 27), .1 / 26)
    expected_probs[indices, indices] = .9
    torch.testing.assert_close(logits.softmax(-1), expected_probs, rtol=2e-6, atol=1e-8)
    # Same master is independent of intervening unrelated random draws.
    with torch.random.fork_rng(devices=[]):
        torch.rand(50)
        second, second_critic = templates(303031)
    for first, other in ((actor, second), (critic, second_critic)):
        assert all(torch.equal(p, q) for p, q in zip(first.parameters(), other.parameters()))
    checkpoint = tmp_path / 'initial.pt'
    torch.save({'actor': actor.state_dict(), 'critic': critic.state_dict()}, checkpoint)
    saved = torch.load(checkpoint, weights_only=True)
    restored, restored_critic = templates(303032)
    restored.load_state_dict(saved['actor'])
    restored_critic.load_state_dict(saved['critic'])
    assert torch.equal(restored(context, indices), logits)
    assert all(torch.equal(p, q) for p, q in zip(critic.parameters(), restored_critic.parameters()))
    assert torch.equal(before, torch.random.get_rng_state())


def test_structural_diagonal_mapping_raw_mlp_and_gradients():
    actor, _ = templates(303031)
    with torch.no_grad():
        actor.table.copy_(torch.arange(702).reshape(27, 26) / 100)
        actor.mlp[4].bias.fill_(2.0)
    logits = actor(torch.zeros(27, 120), torch.arange(27))
    expected = torch.zeros(27, 27)
    for c in range(27):
        others = [action for action in range(27) if action != c]
        expected[c, others] = actor.table.detach()[c]
        expected[c, c] = math.log(234)
    torch.testing.assert_close(logits, expected + 2.0, rtol=0, atol=0)
    # The fixed B[c,c] has no gradient path into any table entry.
    logits.diagonal().sum().backward()
    assert torch.count_nonzero(actor.table.grad) == 0
    actor.zero_grad()
    logits = actor(torch.zeros(27, 120), torch.arange(27))
    (logits - logits.diagonal()[:, None] * torch.eye(27)).sum().backward()
    assert torch.equal(actor.table.grad, torch.ones(27, 26))


def test_optimizer_exact_membership_options_and_initial_state():
    actor, critic = templates(303031)
    aopt, copt = optimizers(actor, critic)
    assert len(aopt.param_groups) == 2
    assert aopt.param_groups[0]['params'] == [actor.table]
    assert [id(p) for p in aopt.param_groups[1]['params']] == [id(p) for p in actor.mlp.parameters()]
    actor_ids = {id(p) for group in aopt.param_groups for p in group['params']}
    critic_ids = {id(p) for group in copt.param_groups for p in group['params']}
    assert actor_ids == {id(p) for p in actor.parameters()}
    assert critic_ids == {id(p) for p in critic.parameters()}
    assert actor_ids.isdisjoint(critic_ids)
    assert [group['lr'] for group in aopt.param_groups] == [.01, .0003]
    assert copt.param_groups[0]['lr'] == .0003
    assert not aopt.state and not copt.state
    for group in aopt.param_groups + copt.param_groups:
        for key, value in dict(betas=(.9, .999), eps=1e-8, weight_decay=0,
                               amsgrad=False, foreach=False, fused=False).items():
            assert group[key] == value


def test_addressed_sampling_exact_calls_density_pairing_and_global_rng(monkeypatch):
    generator = torch.Generator().manual_seed(922)
    logits = torch.randn(5, 27, generator=generator)
    before = torch.random.get_rng_state().clone()
    addresses = dict(domain='eval', master=303031, world_seed=30300000, macro_index=17)
    expected_seeds = []
    expected_actions = []
    for agent in range(5):
        address = f'b03-c-prior-v1|eval|303031|30300000|17|{agent}'
        seed = int.from_bytes(hashlib.sha256(address.encode('ascii')).digest()[:8], 'little')
        seed &= (1 << 63) - 1
        expected_seeds.append(seed)
        expected_actions.append(torch.multinomial(logits[agent].softmax(-1), 1,
                                generator=torch.Generator().manual_seed(seed))[0])
        assert address_seed('eval', 303031, 30300000, 17, agent) == seed
        assert address_seed('train', 303031, 30300000, 17, agent) != seed
    calls = []
    multinomial = torch.multinomial

    def observed(probabilities, count, *, generator):
        calls.append((probabilities.clone(), count, generator.initial_seed()))
        return multinomial(probabilities, count, generator=generator)

    monkeypatch.setattr(torch, 'multinomial', observed)
    actions, logp, entropy, seeds = sample_actions(logits, **addresses)
    assert torch.equal(actions, torch.stack(expected_actions))
    assert seeds.tolist() == expected_seeds
    assert len(calls) == 5
    for agent, (probabilities, count, seed) in enumerate(calls):
        assert probabilities.shape == (27,) and probabilities.dtype == torch.float32
        assert torch.equal(probabilities, logits[agent].softmax(-1))
        assert count == 1 and seed == expected_seeds[agent]
    expected_logp = torch.stack([logits[i].log_softmax(-1)[actions[i]] for i in range(5)])
    expected_entropy = -(logits.softmax(-1) * logits.log_softmax(-1)).sum(-1)
    assert torch.equal(logp, expected_logp)
    torch.testing.assert_close(entropy, expected_entropy, rtol=2e-7, atol=2e-7)
    paired = sample_actions(logits + 1.0, **addresses)
    assert torch.equal(paired[0], actions) and torch.equal(paired[3], seeds)
    # Distinct learned distributions still receive the same primitive seed addresses.
    changed = sample_actions(logits * 2, **addresses)
    assert torch.equal(changed[3], seeds)
    calls.clear()
    greedy = sample_actions(logits, greedy=True)
    assert torch.equal(greedy[0], logits.argmax(-1)) and greedy[3] is None
    assert calls == []
    assert torch.equal(before, torch.random.get_rng_state())


def test_category_density_never_merges_action_labels():
    logits = torch.zeros(2, 27)
    logits[:, 4] = 2
    logits[:, 7] = -1
    logp, _ = categorical_terms(logits, torch.tensor([4, 7]))
    # Even if two requested commands later execute identically, their category
    # likelihoods stay separate. No geometry or executed displacement is an input.
    assert float(logp[0] - logp[1]) == pytest.approx(3)


def synthetic_episodes(actor, critic):
    generator = torch.Generator().manual_seed(921)
    episodes = []
    for episode in range(2):
        context = torch.randn(64, 5, 120, generator=generator)
        cx = torch.randn(64, 136, generator=generator)
        c_index = (torch.arange(320).reshape(64, 5) + episode) % 27
        action = (c_index + torch.arange(64)[:, None] % 3) % 27
        with torch.no_grad():
            old_logp, _ = categorical_terms(actor(context, c_index), action)
            value = critic(cx)
        # Exercise both clipping branches in the synthetic arithmetic check.
        offset = torch.tensor([0., math.log(2), -math.log(2), 0., 0.])
        episodes.append(dict(context=context.requires_grad_(), c_index=c_index,
                             critic=cx.requires_grad_(), action=action,
                             logp=(old_logp + offset).requires_grad_(),
                             value=value.requires_grad_(),
                             reward=((torch.arange(64) % 7 - 3) / 8.0 + episode).requires_grad_()))
    return episodes


def independent_targets(episodes):
    targets = torch.tensor([[sum(float(x) for x in ep['reward'][k:]) / 256
                             for k in range(64)] for ep in episodes])
    values = torch.stack([ep['value'].detach() for ep in episodes])
    raw = targets - values
    population_std = ((raw - raw.mean()).square().mean()).sqrt()
    return targets, (raw - raw.mean()) / (population_std + 1e-8)


def test_returns_team_advantages_no_cross_episode_or_bootstrap():
    rewards = torch.zeros(2, 64)
    rewards[0, 63] = 256
    rewards[1, 0] = 512
    values = torch.linspace(-1, 1, 128).reshape(2, 64).requires_grad_()
    targets, advantage = _targets_advantages(rewards.requires_grad_(), values)
    expected = torch.zeros_like(targets)
    expected[0] = 1
    expected[1, 0] = 2
    assert torch.equal(targets, expected)
    centered = expected - values.detach()
    centered -= centered.mean()
    torch.testing.assert_close(advantage, centered / (centered.square().mean().sqrt() + 1e-8))
    assert not targets.requires_grad and not advantage.requires_grad
    assert float(advantage.mean()) == pytest.approx(0, abs=1e-7)
    assert float(advantage.std(unbiased=False)) == pytest.approx(1, abs=1e-6)
    _, constant = _targets_advantages(torch.zeros(2, 64), torch.ones(2, 64))
    assert torch.equal(constant, torch.zeros_like(constant))


def test_four_epochs_match_independent_ppo_adam_and_counts():
    actor, critic = templates(303031)
    reference_actor, reference_critic = copy.deepcopy(actor), copy.deepcopy(critic)
    episodes = synthetic_episodes(actor, critic)
    source = [{key: tensor.detach().clone() for key, tensor in ep.items()} for ep in episodes]
    aopt, copt = optimizers(actor, critic)
    options = dict(betas=(.9, .999), eps=1e-8, weight_decay=0, amsgrad=False,
                   foreach=False, fused=False)
    raopt = torch.optim.Adam([{'params': [reference_actor.table], 'lr': .01},
                             {'params': reference_actor.mlp.parameters(), 'lr': .0003}], **options)
    rcopt = torch.optim.Adam(reference_critic.parameters(), lr=.0003, **options)
    targets, advantages = independent_targets(episodes)
    context = torch.stack([ep['context'].detach() for ep in episodes])
    c_index = torch.stack([ep['c_index'] for ep in episodes])
    actions = torch.stack([ep['action'] for ep in episodes])
    old_logp = torch.stack([ep['logp'].detach() for ep in episodes])
    cx = torch.stack([ep['critic'].detach() for ep in episodes])
    reference_records = []
    for epoch in range(4):
        logits = reference_actor(context, c_index)
        lp = torch.stack([logits[e, k, a].log_softmax(-1)[actions[e, k, a]]
                          for e in range(2) for k in range(64) for a in range(5)]).reshape(2, 64, 5)
        ratio = (lp - old_logp).exp()
        surrogate = torch.minimum(ratio * advantages[..., None],
                                  ratio.clamp(.8, 1.2) * advantages[..., None])
        policy_loss = -surrogate.sum(-1).mean()
        entropy = -(logits.softmax(-1) * logits.log_softmax(-1)).sum(-1).sum(-1).mean()
        actor_loss = policy_loss - .01 * entropy
        value_mse = (reference_critic(cx) - targets).square().mean()
        critic_loss = .5 * value_mse
        reference_records.append(dict(policy_loss=float(policy_loss.detach()),
                                      actor_loss=float(actor_loss.detach()),
                                      value_loss=float(value_mse.detach()),
                                      critic_loss=float(critic_loss.detach()),
                                      entropy=float(entropy.detach()),
                                      approx_kl=float((old_logp - lp).mean().detach()),
                                      clip_fraction=float(((ratio < .8) | (ratio > 1.2)).float().mean())))
        raopt.zero_grad()
        rcopt.zero_grad()
        actor_loss.backward()
        critic_loss.backward()
        torch.nn.utils.clip_grad_norm_(reference_actor.parameters(), .5)
        torch.nn.utils.clip_grad_norm_(reference_critic.parameters(), .5)
        raopt.step()
        rcopt.step()
    counts = {'actor_optimizer_steps': 7, 'critic_optimizer_steps': 11}
    emitted = []
    records = update(actor, critic, aopt, copt, episodes, counts, emit=emitted.append)
    assert emitted == records and len(records) == 4
    for record, expected in zip(records, reference_records):
        for key, value in expected.items():
            assert record[key] == pytest.approx(value, rel=2e-6, abs=2e-7)
        assert record['actor_clipped_grad_norm'] <= .500001
        assert record['critic_clipped_grad_norm'] <= .500001
        assert record['actor_table_lr'] == .01
        assert record['actor_mlp_lr'] == record['critic_lr'] == .0003
    for actual, expected in ((actor, reference_actor), (critic, reference_critic)):
        for p, q in zip(actual.parameters(), expected.parameters()):
            torch.testing.assert_close(p, q, rtol=2e-5, atol=2e-7)
    assert records[0]['actor_hidden_grad_norm'] == 0
    assert records[0]['actor_hidden_movement_from_update_start'] == 0
    assert records[0]['actor_head_grad_norm'] > 0
    assert records[0]['actor_table_grad_norm'] > 0
    assert records[1]['actor_hidden_grad_norm'] > 0
    assert records[-1]['actor_hidden_movement_from_update_start'] > 0
    assert counts == dict(actor_optimizer_steps=11, critic_optimizer_steps=15,
                          optimizer_steps=8, ppo_rollouts=1, actor_forward_calls=4,
                          actor_forward_rows=2560, actor_replay_rows=2560,
                          critic_forward_calls=4, critic_forward_rows=512, critic_replay_rows=512)
    for opt in (aopt, copt):
        assert all(int(state['step']) == 4 for state in opt.state.values())
    for episode, original in zip(episodes, source):
        for key, tensor in episode.items():
            assert torch.equal(tensor, original[key])
            assert tensor.grad is None


def test_actor_combined_and_critic_separate_clipping_are_exercised(monkeypatch):
    actor, critic = templates(303031)
    aopt, copt = optimizers(actor, critic)
    episodes = []
    for index in range(2):
        context = torch.ones(64, 5, 120)
        c_index = torch.zeros(64, 5, dtype=torch.long)
        action = torch.full((64, 5), index, dtype=torch.long)
        with torch.no_grad():
            logp, _ = categorical_terms(actor(context, c_index), action)
        rewards = torch.zeros(64)
        rewards[-1] = 256 * (3 - 2 * index)
        episodes.append(dict(context=context, c_index=c_index, action=action,
                             logp=logp, value=torch.zeros(64), reward=rewards,
                             critic=torch.ones(64, 136)))
    clip = torch.nn.utils.clip_grad_norm_
    clipped_sets = []

    def observed(parameters, max_norm):
        parameters = list(parameters)
        clipped_sets.append(({id(p) for p in parameters}, max_norm))
        return clip(parameters, max_norm)

    monkeypatch.setattr(torch.nn.utils, 'clip_grad_norm_', observed)
    records = update(actor, critic, aopt, copt, episodes, {})
    assert clipped_sets == [({id(p) for p in actor.parameters()}, .5),
                            ({id(p) for p in critic.parameters()}, .5)] * 4
    assert records[0]['actor_grad_norm'] > .5
    assert records[0]['critic_grad_norm'] > .5
    assert records[0]['actor_clipped_grad_norm'] == pytest.approx(.5, abs=1e-6)
    assert records[0]['critic_clipped_grad_norm'] == pytest.approx(.5, abs=1e-6)


def test_partial_critic_step_failure_preserves_actual_exposure_counts(monkeypatch):
    actor, critic = templates(303031)
    aopt, copt = optimizers(actor, critic)
    episodes = synthetic_episodes(actor, critic)
    initial_actor = copy.deepcopy(actor.state_dict())
    initial_critic = copy.deepcopy(critic.state_dict())

    def failed_step():
        raise RuntimeError('synthetic critic optimizer failure')

    monkeypatch.setattr(copt, 'step', failed_step)
    counts = {'actor_optimizer_steps': 0, 'critic_optimizer_steps': 0}
    with pytest.raises(RuntimeError, match='synthetic critic'):
        update(actor, critic, aopt, copt, episodes, counts)
    assert counts == dict(actor_optimizer_steps=1, critic_optimizer_steps=0,
                          optimizer_steps=1, ppo_rollouts=1, actor_forward_calls=1,
                          actor_forward_rows=640, actor_replay_rows=640,
                          critic_forward_calls=1, critic_forward_rows=128, critic_replay_rows=128)
    assert any(not torch.equal(value, initial_actor[key]) for key, value in actor.state_dict().items())
    assert all(torch.equal(value, initial_critic[key]) for key, value in critic.state_dict().items())


@pytest.mark.parametrize('defect', ['length', 'shape', 'nan', 'c_index', 'action_float'])
def test_malformed_rollout_fails_before_optimizer_exposure(defect):
    actor, critic = templates(303031)
    aopt, copt = optimizers(actor, critic)
    episodes = synthetic_episodes(actor, critic)
    if defect == 'length':
        episodes.pop()
    elif defect == 'shape':
        episodes[1]['reward'] = torch.zeros(63)
    elif defect == 'nan':
        episodes[0]['logp'] = torch.full((64, 5), float('nan'))
    elif defect == 'c_index':
        episodes[1]['c_index'][0, 0] = 27
    else:
        episodes[0]['action'] = episodes[0]['action'].float() + .5
    counts = {}
    initial = copy.deepcopy(actor.state_dict())
    with pytest.raises((ValueError, FloatingPointError)):
        update(actor, critic, aopt, copt, episodes, counts)
    assert counts == {} and not aopt.state and not copt.state
    assert all(torch.equal(value, initial[key]) for key, value in actor.state_dict().items())


def test_reject_wrong_sampler_domain_and_nonfinite_density():
    with pytest.raises(ValueError, match='domain'):
        address_seed('Ls', 303031, 30300000, 0, 0)
    with pytest.raises(ValueError):
        address_seed('eval', 303031, 30300000, -1, 0)
    with pytest.raises(ValueError, match='FP32'):
        sample_actions(torch.zeros(5, 27, dtype=torch.float64), greedy=True)
    with pytest.raises(FloatingPointError):
        categorical_terms(torch.full((5, 27), float('inf')), torch.zeros(5, dtype=torch.long))
