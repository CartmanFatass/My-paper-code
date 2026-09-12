import copy
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.vap_folr_core.entity_history_b01.environment import EntityHistoryEnv
from experiments.candidates.vap_folr_core.entity_history_b01.learner import Learner
from experiments.candidates.vap_folr_core.entity_history_b01.model import Actor
from experiments.candidates.vap_folr_core.entity_history_b01.publication import pair_result
from experiments.candidates.vap_folr_core.public_lifecycle_b01.environment import LifecycleEnv


@pytest.fixture(scope='module', autouse=True)
def one_thread():
    torch.set_num_threads(1)


def observations(t=4):
    torch.manual_seed(713)
    visible = torch.eye(5, dtype=torch.bool)[None, None].repeat(2, t, 1, 1)
    visible[:, 0, 0, 1] = True
    if t > 3:
        visible[:, 3, 0, 1] = True
    continuation = torch.ones(2, t, 5, dtype=torch.bool)
    continuation[:, 0] = False
    seen, age = torch.zeros_like(visible), torch.zeros_like(visible, dtype=torch.int16)
    for step in range(t):
        previous = seen[:, step-1] if step else torch.zeros_like(seen[:, 0])
        seen[:, step] = previous | visible[:, step]
        if step:
            age[:, step] = torch.where(previous, age[:, step-1] + 1, 0)
        age[:, step].masked_fill_(visible[:, step], 0)
    return dict(entities=torch.rand(2, t, 5, 4), previous_action=torch.zeros(2, t, 5, 5),
                entity_mask=torch.zeros(2, t, 5, dtype=torch.bool),
                visible=visible, obs_mask=~visible, seen=seen, age=age,
                birth=~continuation, continuation=continuation,
                departure=torch.zeros_like(continuation), event=torch.zeros(2, t, dtype=torch.bool))


@pytest.mark.parametrize('arm', ['GENERIC_RETAIN', 'BANK'])
def test_information_query_and_public_bypass(arm):
    batch = observations()
    actor = Actor(arm)
    original = actor(batch)[0]
    changed = copy.deepcopy(batch)
    changed['entities'][:, :, 4] = float('nan')  # never visible to observer zero
    changed['seen'][:, :, 3] = ~changed['seen'][:, :, 3]
    changed['age'][:, :, 3] = 19
    torch.testing.assert_close(actor(changed)[0][:, :, 0], original[:, :, 0])
    # Common invisible public notice must reach both policies outside peer masking.
    inputs = []
    handle = actor.fc2.register_forward_pre_hook(lambda _, args: inputs.append(args[0].detach().clone()))
    actor(batch)
    before = inputs[0]
    inputs.clear()
    changed = copy.deepcopy(batch)
    changed['departure'][:, :, 4] = True
    actor(changed)
    assert not torch.equal(before[..., 0, 128:], inputs[0][..., 0, 128:])
    handle.remove()
    # Change only query coordinates, keeping every key/value fixed: wrong slot0 fails.
    with torch.no_grad():
        actor.attn.in_trans.weight.zero_()
        actor.attn.in_trans.weight[0, 0] = 1
        actor.attn.in_trans.weight[128, 1] = 1
        actor.attn.in_trans.weight[256, 2] = 1
        actor.attn.out_trans.weight.zero_()
        actor.attn.out_trans.bias.zero_()
        actor.attn.out_trans.weight[0, 0] = 1
    tokens = torch.zeros(1, 5, 5, 128)
    tokens[..., 1] = torch.arange(5)
    tokens[..., 2] = torch.arange(5).square()
    allowed = torch.ones(1, 5, 5, dtype=torch.bool)
    base = actor.attn(tokens, allowed, torch.ones(1, 5, dtype=torch.bool))
    modified = tokens.clone()
    modified[:, 2, 2, 0] = 3
    result = actor.attn(modified, allowed, torch.ones(1, 5, dtype=torch.bool))
    assert not torch.allclose(base[:, 2], result[:, 2])
    torch.testing.assert_close(base[:, 0], result[:, 0])


def test_bank_lifetimes_unseen_carry_and_gradients():
    batch = observations(1)
    batch['continuation'][:] = True
    batch['continuation'][:, 0, 2] = False
    batch['visible'][:] = torch.eye(5, dtype=torch.bool)
    hidden = torch.randn(2, 5, 5, 16, requires_grad=True)
    actor = Actor('BANK')
    _, states = actor(batch, hidden)
    torch.testing.assert_close(states[:, 0, 0, 1], hidden[:, 0, 1])
    assert torch.count_nonzero(states[:, 0, 0, 2]) == 0
    assert torch.count_nonzero(states[:, 0, 2, 0]) == 0
    states.sum().backward()
    assert torch.count_nonzero(hidden.grad[:, :, 2]) == 0
    assert torch.count_nonzero(hidden.grad[:, 2]) == 0
    torch.testing.assert_close(hidden.grad[:, 0, 1], torch.ones_like(hidden.grad[:, 0, 1]))


@pytest.mark.parametrize('arm', ['GENERIC_RETAIN', 'BANK'])
def test_collection_unroll_and_real_learner_checkpoint(arm, tmp_path):
    batch = observations(21)
    torch.manual_seed(912)
    learner = Learner(arm)
    full_q, full_h = learner.actor(batch)
    h, sequential = None, []
    for step in range(21):
        q, states = learner.actor({k: v[:, step:step+1] for k, v in batch.items()}, h)
        h = states[:, -1]
        sequential.append(q)
    torch.testing.assert_close(torch.cat(sequential, 1), full_q, rtol=2e-5, atol=2e-6)
    torch.testing.assert_close(h, full_h[:, -1], rtol=2e-5, atol=2e-6)
    before = learner.actor.rnn.weight_ih.detach().clone()
    batch.update(actions=torch.zeros(2, 20, 5, dtype=torch.long),
                 reward=torch.ones(2, 20), terminated=torch.zeros(2, 20))
    batch['terminated'][:, -1] = 1
    loss = learner.update(batch, 200)
    assert np.isfinite(loss) and learner.updates == 1
    assert not torch.equal(before, learner.actor.rnn.weight_ih)
    torch.testing.assert_close(learner.actor.rnn.weight_ih, learner.target_actor.rnn.weight_ih)
    checkpoint = tmp_path / (arm + '.pt')
    learner.save(checkpoint)
    saved = torch.load(checkpoint, weights_only=True)
    assert saved['updates'] == 1 and saved['arm'] == arm
    assert saved['optimiser']['state']
    torch.testing.assert_close(saved['actor']['rnn.weight_ih'], learner.actor.rnn.weight_ih)


def test_common_initialization_and_future_rng_consumers():
    torch.manual_seed(914)
    generic = Learner('GENERIC_RETAIN')
    after_generic = torch.random.get_rng_state()
    torch.manual_seed(914)
    bank = Learner('BANK')
    assert torch.equal(after_generic, torch.random.get_rng_state())
    for name in ('fc1.weight', 'fc2.weight', 'fc3.weight', 'attn.in_trans.weight'):
        torch.testing.assert_close(generic.actor.state_dict()[name], bank.actor.state_dict()[name], rtol=0, atol=0)
    for name, value in generic.mixer.state_dict().items():
        torch.testing.assert_close(value, bank.mixer.state_dict()[name], rtol=0, atol=0)


def test_native_same_step_refill_rng_and_idempotent_history():
    def fixture(cls):
        env = cls(vision=1, seed=111)
        env.reset()
        env.entity_mask[:] = 1
        env.entity_mask[:2] = 0
        env.cars_pos[:] = 0
        env.cars_target[:] = 0
        env.cars_pos[:2] = [[3, 0], [3, 3]]
        env.cars_target[:2] = [[3, 0], [3, 6]]
        env.add_rate = 1
        return env
    old, new = fixture(LifecycleEnv), fixture(EntityHistoryEnv)
    new.seen[:] = True
    new.age[:] = 7
    state = np.random.get_state()
    expected = old.step([0] * 5)
    after = np.random.get_state()
    np.random.set_state(state)
    assert new.step([0] * 5) == expected
    actual = np.random.get_state()
    np.testing.assert_array_equal(after[1], actual[1])
    assert after[2:] == actual[2:]
    assert new.departure[0] and new.birth[0] and not new.continuation[0]
    np.testing.assert_array_equal(new.seen[0], new.visible[0])
    np.testing.assert_array_equal(new.seen[:, 0], new.visible[:, 0])
    first = new.observation(np.zeros(5, dtype=int))
    second = new.observation(np.zeros(5, dtype=int))
    for key in first:
        np.testing.assert_array_equal(first[key], second[key])


@pytest.mark.parametrize('delta,rule', [(1, 'WITHIN_MEI'), (-1, 'WITHIN_MEI'),
                                     (1.1, 'BANK_ABOVE_MEI'), (-1.1, 'GENERIC_ABOVE_MEI')])
def test_primary_and_dependent_publication(delta, rule, tmp_path):
    generic = dict(status='complete', arm='GENERIC_RETAIN', training_episodes=5000,
                   optimizer_steps=4969, evaluation_episodes=128, training_seed=1,
                   evaluation_seed=2, evaluation_returns=[0.] * 128)
    bank = dict(generic, arm='BANK', evaluation_returns=[delta] * 128)
    primary = pair_result(generic, bank)
    assert primary['rule'] == rule and primary['paired_difference_se'] is None
    module_path = Path(__file__).resolve().parents[5] / 'scripts/run_folr_entity_history_b01.py'
    spec = importlib.util.spec_from_file_location('folr_entity_runner_test', module_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    summary = dict(bank, pair_primary=primary)
    runner.publish(tmp_path, summary)
    assert json.loads((tmp_path / 'summary.json').read_text()) == summary
    bank['status'] = 'incomplete'
    with pytest.raises(ValueError):
        pair_result(generic, bank)
