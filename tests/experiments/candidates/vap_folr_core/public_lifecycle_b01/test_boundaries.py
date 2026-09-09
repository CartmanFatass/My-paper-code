import copy
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from experiments.candidates.vap_folr_core.public_lifecycle_b01.native_env import Entity_Traffic_Junction_Env
from experiments.candidates.vap_folr_core.public_lifecycle_b01.environment import LifecycleEnv, count_transition
from experiments.candidates.vap_folr_core.public_lifecycle_b01.collection import primary, epsilon_at, sample


@pytest.fixture(scope='module', autouse=True)
def one_thread():
    torch.set_num_threads(1)


def fixture_env(cls):
    env = cls(vision=1)
    env.reset()
    env.entity_mask[:] = 1
    env.entity_mask[:2] = 0
    env.cars_pos[:] = 0
    env.cars_target[:] = 0
    env.cars_pos[:2] = [[3, 0], [3, 3]]
    env.cars_target[:2] = [[3, 0], [3, 6]]
    return env


def assert_rng_same(a, b):
    assert a[0] == b[0]
    np.testing.assert_array_equal(a[1], b[1])
    assert a[2:] == b[2:]


@pytest.mark.parametrize('collision', [False, True])
def test_native_reward_side_effects_rng_and_same_step_refill(collision):
    np.random.seed(42)
    native = fixture_env(Entity_Traffic_Junction_Env)
    wrapped = fixture_env(LifecycleEnv)
    # Force real native births while maintaining its original loops/draws.
    native.add_rate = wrapped.add_rate = 1.0
    if collision:
        native.cars_pos[1] = wrapped.cars_pos[1] = [3, 0]
        native.cars_target[0] = wrapped.cars_target[0] = [3, 6]
    start = np.random.get_state()
    result_native = native.step([0] * 5)
    end_native = np.random.get_state()
    np.random.set_state(start)
    result_wrapped = wrapped.step([0] * 5)
    assert result_native == result_wrapped
    assert_rng_same(end_native, np.random.get_state())
    for key in ['wait', 'cars_pos', 'last_cars_pos', 'cars_target', 'entity_mask']:
        np.testing.assert_array_equal(getattr(native, key), getattr(wrapped, key))
    assert wrapped.departure[0]
    if not collision:
        assert wrapped.birth[0]
    assert not wrapped.continuation[0]
    assert wrapped.event
    # Removal on an inactive slot still clears the native side effects.
    wrapped.entity_mask[4] = 1
    wrapped.departure[4] = False
    wrapped.wait[4] = 10
    wrapped.cars_pos[4] = 7
    wrapped._remove_car(4)
    assert wrapped.wait[4] == 0 and not wrapped.cars_pos[4].any()
    assert not wrapped.departure[4]


def test_initial_birth_previous_action_and_terminal_counts():
    env = LifecycleEnv(vision=1)
    env.reset()
    obs = env.observation(np.ones(5, dtype=int))
    assert env.birth.sum() == 1 and not env.event
    assert not obs['previous_action'].any()
    env.birth[:] = [1, 0, 0, 0, 0]
    env.departure[:] = [0, 0, 1, 0, 0]
    env.continuation[:] = [0, 1, 0, 1, 0]
    env.event = True
    obs = env.observation(np.arange(5))
    np.testing.assert_array_equal(obs['previous_action'].sum(-1), env.continuation)
    env.t = 19
    assert count_transition(env, 'EVENT')['survivor_resets'] == 2
    assert count_transition(env, 'RETAIN')['survivor_resets'] == 0
    env.event = False
    assert count_transition(env, 'RANDOM')['eligible_survivor_opportunities'] == 2
    assert count_transition(env, 'RANDOM')['survivor_opportunities'] == 0
    env.t = 20
    assert count_transition(env, 'EVENT') == dict(births=1, departures=1, survivor_opportunities=0, eligible_survivor_opportunities=0, survivor_resets=0)


def test_random_collection_schedule_replay_and_rng_isolation():
    from experiments.candidates.vap_folr_core.public_lifecycle_b01.collection import collect
    from experiments.candidates.vap_folr_core.public_lifecycle_b01.learner import Learner
    # Fixed non-scientific observations include entrant, inactive and true survivors.
    class FixtureEnv:
        max_steps = 20

        def reset(self):
            self.t = 0
            self.birth = np.zeros(5, bool)
            self.departure = np.zeros(5, bool)
            self.continuation = np.zeros(5, bool)
            self.event = False

        def observation(self, previous):
            b = synthetic_batch()
            obs = {k: v[0, self.t].numpy().copy() for k, v in b.items()
                   if k not in ['actions', 'reward', 'terminated', 'reset_mask']}
            self.continuation = obs['continuation']
            self.event = bool(obs['event'])
            return obs

        def step(self, chosen):
            self.t += 1
            self.observation(None)
            return 0.0, self.t == 20, {}

    learner = Learner('RANDOM')
    rng = np.random.Generator(np.random.PCG64(207804))
    expected_rng = np.random.Generator(np.random.PCG64(207804))
    start = np.random.get_state()
    seen = []
    hook = learner.actor.register_forward_pre_hook(
        lambda module, inputs: seen.append(inputs[0]['reset_mask'].clone()))
    episodes = []
    for _ in range(2):
        ep, _, counts = collect(FixtureEnv(), learner.actor, 0.0, rng)
        expected = ep['continuation'] & (expected_rng.random((21, 5)) < .1)
        np.testing.assert_array_equal(ep['reset_mask'], expected)
        assert ep['reset_mask'].dtype == bool and not ep['reset_mask'][0].any()
        assert counts['survivor_resets'] == int(expected[:20].sum())
        assert counts['eligible_survivor_opportunities'] == int(ep['continuation'][:20].sum())
        assert counts['survivor_opportunities'] == int((ep['continuation'][:20] & ep['event'][:20, None]).sum())
        episodes.append(ep)
    hook.remove()
    assert_rng_same(start, np.random.get_state())
    torch.testing.assert_close(torch.cat(seen, 1)[0], torch.as_tensor(np.concatenate([x['reset_mask'] for x in episodes])))
    replay_batch = sample([episodes[i % 2] for i in range(32)])
    captured = []
    hooks = [actor.register_forward_pre_hook(lambda module, inputs: captured.append(inputs[0]['reset_mask'].clone()))
             for actor in [learner.actor, learner.target_actor]]
    private_state = copy.deepcopy(rng.bit_generator.state)
    learner.update(replay_batch, 32)
    for h in hooks:
        h.remove()
    assert len(captured) == 2
    for mask in captured:
        torch.testing.assert_close(mask, replay_batch['reset_mask'])
    assert rng.bit_generator.state == private_state


@pytest.mark.parametrize('r,e,m,rule', [
    (0, 2, 1, 'EVENT_CLEAR_ADVANTAGE'), (0, 1, 1, 'SHARED_RESET_GAIN'),
    (0, 1, 2, 'MIXED_OR_REVERSE'), (2, 0, 1, 'MIXED_OR_REVERSE'),
    (0, .999, 0, 'MIXED_OR_REVERSE'), (0, 2, 1.001, 'SHARED_RESET_GAIN')])
def test_timing_branches(r, e, m, rule):
    from experiments.candidates.vap_folr_core.public_lifecycle_b01.collection import timing_primary
    got = timing_primary([r], [e], [m])
    assert got['rule'] == rule
    for key, d in [('d_ER', e-r), ('d_MR', m-r), ('d_EM', e-m)]:
        assert got['contrasts'][key]['difference'] == d


def synthetic_batch():
    b, t, n = 2, 21, 5
    batch = dict(entities=torch.linspace(0, 1, b*t*n*4).reshape(b, t, n, 4),
                 obs_mask=torch.zeros(b, t, n, n, dtype=torch.bool),
                 entity_mask=torch.zeros(b, t, n, dtype=torch.bool),
                 birth=torch.zeros(b, t, n, dtype=torch.bool),
                 continuation=torch.ones(b, t, n, dtype=torch.bool),
                 event=torch.zeros(b, t, dtype=torch.bool),
                 previous_action=torch.zeros(b, t, n, 5),
                 actions=torch.zeros(b, 20, n, dtype=torch.long),
                 reward=torch.zeros(b, 20), terminated=torch.zeros(b, 20))
    batch['continuation'][:, 0] = False
    batch['birth'][:, 0] = True
    batch['entity_mask'][:, :, 4] = True
    batch['obs_mask'][:, :, 4] = True
    batch['continuation'][:, :, 4] = False
    batch['birth'][:, :, 4] = False
    batch['reset_mask'] = torch.zeros(b, t, n, dtype=torch.bool)
    batch['reset_mask'][:, 7, 1:4] = True
    batch['event'][:, 7] = True
    batch['birth'][:, 7, 0] = True
    batch['continuation'][:, 7, 0] = False
    batch['terminated'][:, -1] = 1
    batch['reward'][:, -1] = 1
    return batch


@pytest.mark.parametrize('arm', ['RETAIN', 'EVENT', 'RANDOM'])
def test_actor_input_reset_timing_and_replay_parity(arm):
    from experiments.candidates.vap_folr_core.public_lifecycle_b01.model import Actor
    torch.manual_seed(13)
    actor = Actor(arm)
    batch = synthetic_batch()
    seen = []
    hook = actor.fc2.register_forward_pre_hook(lambda module, inputs: seen.append(inputs[0].detach().clone()))
    q, hs = actor(batch)
    hook.remove()
    cues = seen[0].reshape(2, 21, 5, -1)[..., -2:]
    torch.testing.assert_close(cues[..., 0], batch['event'][..., None].expand(2, 21, 5).float())
    torch.testing.assert_close(cues[..., 1], batch['birth'].float())
    assert not hs[:, :, 4].any()
    hidden = None
    qs, states = [], []
    for t in range(21):
        current = {k: v[:, t:t+1] for k, v in batch.items() if k not in ['actions', 'reward', 'terminated']}
        qt, ht = actor(current, hidden)
        qs.append(qt)
        states.append(ht)
        hidden = ht[:, -1]
    torch.testing.assert_close(torch.cat(qs, 1), q)
    torch.testing.assert_close(torch.cat(states, 1), hs)
    current = {k: v[:, 7:8] for k, v in batch.items() if k not in ['actions', 'reward', 'terminated']}
    incoming = torch.ones(2, 5, 64)
    actual_inputs = []
    h = actor.rnn.register_forward_pre_hook(lambda module, inputs: actual_inputs.append(inputs[1].detach().clone()))
    actor(current, incoming)
    h.remove()
    got = actual_inputs[0].reshape(2, 5, 64)
    assert not got[:, 0].any() and not got[:, 4].any()
    assert bool(got[:, 1:4].any()) == (arm == 'RETAIN')


def test_real_learner_synthetic_gradient_targets_checkpoint(tmp_path):
    from experiments.candidates.vap_folr_core.public_lifecycle_b01.learner import Learner
    torch.set_num_threads(1)
    torch.manual_seed(91)
    learner = Learner('EVENT')
    batch = synthetic_batch()
    before = [p.detach().clone() for p in learner.actor.parameters()]
    learner.update(batch, 32)
    assert all(torch.isfinite(p).all() for p in learner.actor.parameters())
    assert all(torch.isfinite(p).all() for p in learner.mixer.parameters())
    assert any(not torch.equal(x, y) for x, y in zip(before, learner.actor.parameters()))
    learner.update(batch, 200)
    for a, b in zip(learner.actor.parameters(), learner.target_actor.parameters()):
        torch.testing.assert_close(a, b)
    q_online, _ = learner.actor(batch)
    q_target, _ = learner.target_actor(batch)
    torch.testing.assert_close(q_online, q_target)
    learner.save(tmp_path / 'final.pt')
    saved = torch.load(tmp_path / 'final.pt', weights_only=False)
    assert saved


def test_primary_rules_replay_rng_and_publication(tmp_path, monkeypatch):
    assert primary([1]*32, [0]*32)['rule'] == 'RETAIN_ABOVE_MEI'
    assert primary([0]*32, [1]*32)['rule'] == 'RESET_ABOVE_MEI'
    assert primary([0.999]*32, [0]*32)['rule'] == 'WITHIN_MEI'
    assert primary([-0.999]*32, [0]*32)['rule'] == 'WITHIN_MEI'
    assert epsilon_at(0) == 1 and epsilon_at(50000) == pytest.approx(0.05) and epsilon_at(100000) == 0.05
    replay = [dict(x=np.asarray(i)) for i in range(32)]
    start = np.random.get_state()
    assert sample(replay)['x'].tolist() == list(range(32))
    assert_rng_same(start, np.random.get_state())
    # Exercise the actual JSON publication function with fixture resource data on Windows.
    monkeypatch.setitem(sys.modules, 'resource', SimpleNamespace(RUSAGE_SELF=0, getrusage=lambda _: SimpleNamespace(ru_maxrss=123)))
    path = Path(__file__).resolve().parents[5] / 'scripts/run_folr_public_lifecycle_b01.py'
    spec = importlib.util.spec_from_file_location('b01_runner', path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    summary = dict(evaluation_returns=[1.25]*32, mean_native_return=1.25, status='complete')
    runner.publish(tmp_path, summary)
    assert json.loads((tmp_path/'summary.json').read_text())['evaluation_returns'] == [1.25]*32


@pytest.mark.parametrize('arm', ['RETAIN', 'EVENT', 'RANDOM'])
def test_runner_seed_routing_with_standins(tmp_path, monkeypatch, arm):
    # Exercise real argparse/main/publication; replace every scientific entry point.
    import random
    calls = []
    for module, name, label in [(random, 'seed', 'python'),
                                (np.random, 'seed', 'numpy'),
                                (torch, 'manual_seed', 'torch')]:
        monkeypatch.setattr(module, name, lambda seed, label=label: calls.append((label, seed)))
    monkeypatch.setattr(torch, 'set_num_interop_threads', lambda n: None)
    monkeypatch.setattr(torch, 'get_num_interop_threads', lambda: 1)
    prefix = 'experiments.candidates.vap_folr_core.public_lifecycle_b01.'

    def environment(**kwargs):
        calls.append(('environment', kwargs['seed']))
        return object()

    updates, evaluations, masks = [], [], []

    def collect(env, actor, epsilon, mask_rng):
        masks.append(mask_rng)
        return {}, 1.25, {}

    def learner(arm):
        calls.append(('learner', arm))
        return SimpleNamespace(actor=SimpleNamespace(eval=lambda: evaluations.append(len(updates))),
                               update=lambda batch, episode: updates.append(episode),
                               save=lambda path: None)

    monkeypatch.setitem(sys.modules, prefix+'environment', SimpleNamespace(LifecycleEnv=environment))
    monkeypatch.setitem(sys.modules, prefix+'learner', SimpleNamespace(Learner=learner))
    monkeypatch.setitem(sys.modules, prefix+'collection', SimpleNamespace(
        collect=collect, sample=lambda replay: None,
        epsilon_at=lambda ticks: 0.0))
    monkeypatch.setitem(sys.modules, 'resource', SimpleNamespace(
        RUSAGE_SELF=0, getrusage=lambda _: SimpleNamespace(ru_maxrss=123)))
    path = Path(__file__).resolve().parents[5] / 'scripts/run_folr_public_lifecycle_b01.py'
    spec = importlib.util.spec_from_file_location('b02_seed_runner', path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    monkeypatch.setattr(runner.signal, 'signal', lambda *args: None)
    argv = [str(path), '--arm', arm, '--launch-sha', 'fixture', '--out', str(tmp_path)]
    monkeypatch.setattr(sys, 'argv', argv)
    runner.main()
    train, final = 7804, 107804
    assert calls == [('python', train), ('numpy', train), ('torch', train),
                     ('learner', arm), ('environment', train),
                     ('python', final), ('numpy', final), ('torch', final),
                     ('environment', final)]
    summary = json.loads((tmp_path/'summary.json').read_text())
    assert (summary['training_seed'], summary['evaluation_seed']) == (train, final)
    assert f'reset to{final} for final evaluation' in summary['rng']
    assert summary['status'] == 'complete' and summary['evaluation_returns'] == [1.25]*128
    assert updates == list(range(32, 5001)) and evaluations == [4969]
    assert len(masks) == 5128
    if arm == 'RANDOM':
        assert all(x is masks[0] for x in masks[:5000])
        assert all(x is masks[5000] for x in masks[5000:])
        assert masks[0] is not masks[5000]
        for rng, seed in [(masks[0], 207804), (masks[5000], 307804)]:
            np.testing.assert_array_equal(rng.random(5), np.random.Generator(np.random.PCG64(seed)).random(5))
    else:
        assert all(x is None for x in masks)
