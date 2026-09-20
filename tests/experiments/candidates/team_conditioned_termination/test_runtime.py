"""Small real Scenario1 correctness runs; no research score/benefit claim."""
import copy
import json
from pathlib import Path
import random
import sys
import time

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from hmasd.agent import HMASDAgent
from scripts import run_flexible_skill_duration_e0 as base
from experiments.candidates.team_conditioned_termination.policy import MaskPolicy, ValueCritic, PPOUpdater
from experiments.candidates.team_conditioned_termination.runtime import (
    Scenario1Features, FrozenGateController, collect_episode, foundation_modules,
)

LANES, HORIZON, AGENTS, USERS = 2, 20, 6, 12
FOUNDATION_SEED = 920611


def envs(seed):
    return base._make_envs(LANES, seed, AGENTS, USERS, HORIZON)


def snapshot(agent):
    result = {name: {key: value.clone() for key, value in module.state_dict().items()}
              for name, module in foundation_modules(agent).items()}
    # These are numpy RunningMeanStd objects, not torch modules. Include all
    # three saved fields so the no-update/load assertion covers ValueNorm too.
    for name in ('value_norm_coordinator', 'value_norm_discoverer', 'obs_norm', 'state_norm'):
        statistics = getattr(agent, name, None)
        if statistics is not None:
            result[name] = {key: torch.as_tensor(np.array(getattr(statistics, key), copy=True))
                            for key in ('mean', 'var', 'count')}
    return result


def assert_snapshot_equal(left, right):
    assert left.keys() == right.keys()
    for name in left:
        assert left[name].keys() == right[name].keys()
        for key in left[name]:
            assert torch.equal(left[name][key], right[name][key]), (name, key)


@pytest.fixture(scope='module')
def foundation(tmp_path_factory):
    """One seed, two 40-team-step rollouts, actual small foundation learning and save."""
    out = tmp_path_factory.mktemp('small-foundation')
    started = time.perf_counter()
    torch.set_num_threads(1)
    with base._preserve_rng():
        random.seed(FOUNDATION_SEED)
        np.random.seed(FOUNDATION_SEED)
        torch.manual_seed(FOUNDATION_SEED)
        worlds = envs(FOUNDATION_SEED)
        config = base._make_config('D0', FOUNDATION_SEED, LANES, HORIZON, HORIZON,
                                   AGENTS, USERS, 2, worlds[0].state_dim, worlds[0].obs_dim)
        config.n_Z = config.n_z = 6
        config.hidden_size = config.embedding_dim = config.gru_hidden_size = 32
        config.n_heads = 2
        config.ppo_epochs = 1
        config.coordinator_batch_size = 16
        config.sequence_batch_size = 12
        config.use_obsnorm = config.use_statenorm = False
        agent = HMASDAgent(config, log_dir=str(out / 'train'), device=torch.device('cpu'))
        theta0 = snapshot(agent)
        counters = {name: base._StepCounter(value) for name, value in vars(agent).items()
                    if isinstance(value, torch.optim.Optimizer)}
        for rollout in range(2):
            states, observations = base._reset_all(worlds)
            for lane in range(LANES):
                agent.reset_env_state(lane)
            steps, dones = np.zeros(LANES, dtype=int), np.zeros(LANES, dtype=bool)
            for tick in range(HORIZON):
                actions, _, data = agent.step(states, observations, steps, dones,
                                              deterministic=False, return_step_data=True, build_infos=False)
                next_states, next_obs, rewards, next_done = [], [], [], []
                for lane, world in enumerate(worlds):
                    obs, reward, term, trunc, info = world.step(actions[lane])
                    next_states.append(info['next_state'])
                    next_obs.append(obs)
                    rewards.append(reward)
                    next_done.append(term or trunc)
                next_states, next_obs = np.asarray(next_states), np.asarray(next_obs)
                next_done = np.asarray(next_done, dtype=bool)
                agent.store_transition_batch(
                    states=states, next_states=next_states.copy(), observations=observations,
                    next_observations=next_obs.copy(), actions=actions, rewards=np.asarray(rewards),
                    dones=next_done, infos_batch=None, rollout_step_idx=tick, step_data=data)
                states, observations, dones = next_states, next_obs, next_done
                steps += 1
            assert dones.all()
            agent.update(last_values=np.zeros((LANES, AGENTS), dtype=np.float32),
                         dones=dones, steps_in_buffer=HORIZON, last_state=states,
                         last_observations=observations)
            agent.clear_buffers()
        trained = snapshot(agent)
        assert any(not torch.equal(theta0['skill_discoverer'][key], value)
                   for key, value in trained['skill_discoverer'].items())
        path = out / 'foundation.pt'
        agent.save_model(str(path))
        facts = {'foundation_seed': FOUNDATION_SEED, 'native_team_steps': 80,
                 'optimizer_steps': {name: counter.count for name, counter in counters.items()},
                 'wall_seconds': time.perf_counter() - started}
        print('TECHNICAL_FOUNDATION ' + json.dumps(facts))
        for world in worlds:
            world.close()
    return config, path, trained, facts


def load_foundation(foundation, out):
    config, path, trained, _ = foundation
    with base._preserve_rng():
        agent = HMASDAgent(copy.deepcopy(config), log_dir=str(out), device=torch.device('cpu'))
        agent.load_model(str(path))
    assert_snapshot_equal(snapshot(agent), trained)
    return agent


def features(agent):
    return Scenario1Features(AGENTS, USERS, agent.config.obs_dim)


def forbid(*args, **kwargs):
    raise AssertionError('frozen foundation training/storage was called')


@pytest.mark.parametrize('mode,seed', [('joint', 920621), ('independent', 920622)])
def test_native_collection_ppo_freeze_and_reload(foundation, tmp_path, monkeypatch, mode, seed):
    started = time.perf_counter()
    agent = load_foundation(foundation, tmp_path / 'gate')
    schema = features(agent)
    # Both arms start from identical parameter initialization; sample streams differ.
    policy = MaskPolicy(schema.context_dim, AGENTS, mode, hidden_size=32, seed=920620)
    critic = ValueCritic(schema.context_dim, hidden_size=32, seed=920620)
    controller = FrozenGateController(agent, policy, critic, schema, seed=seed)
    updater = PPOUpdater(policy, critic, epochs=2, minibatch_size=13, seed=seed)
    initial_policy = copy.deepcopy(policy.state_dict())
    initial_critic = copy.deepcopy(critic.state_dict())
    initial_foundation = snapshot(agent)
    monkeypatch.setattr(agent, 'update', forbid)
    monkeypatch.setattr(agent, 'store_transition_batch', forbid)
    for value in vars(agent).values():
        if isinstance(value, torch.optim.Optimizer):
            monkeypatch.setattr(value, 'step', forbid)
    worlds = envs(seed)
    counts, updates = [], []
    with base._preserve_rng():
        torch.manual_seed(seed + 100)
        np.random.seed(seed + 100)
        for _ in range(2):
            batch, count = collect_episode(worlds, agent, controller, horizon=HORIZON)
            replay = policy.evaluate_actions(batch.context, batch.eligible, batch.forced_end, batch.actions)
            torch.testing.assert_close(replay.log_prob, batch.old_log_prob, rtol=1e-6, atol=2e-6)
            assert batch.context.shape[0] == 40
            assert count['optional_decision_rows'] == 36
            assert count['foundation_optimizer_steps'] == count['foundation_buffer_writes'] == 0
            updates.append(updater.update(batch))
            assert updates[-1]['visited_rows'] == 80
            assert updates[-1]['max_minibatch_size'] == 13
            assert updates[-1]['actor_optimizer_steps'] > 0
            assert updates[-1]['critic_optimizer_steps'] == 8
            counts.append(count)
            assert_snapshot_equal(initial_foundation, snapshot(agent))
    assert sum(c['optional_end_bits'] for c in counts) > 0
    assert any(not torch.equal(initial_policy[key], value) for key, value in policy.state_dict().items())
    assert any(not torch.equal(initial_critic[key], value) for key, value in critic.state_dict().items())
    for module in foundation_modules(agent).values():
        assert all(not p.requires_grad for p in module.parameters())

    path = tmp_path / 'gate.pt'
    torch.save({'policy': policy.state_dict(), 'critic': critic.state_dict(),
                'generator': controller.generator.get_state()}, path)
    restored_policy = MaskPolicy(schema.context_dim, AGENTS, mode, hidden_size=32, seed=1)
    restored_critic = ValueCritic(schema.context_dim, hidden_size=32, seed=2)
    saved = torch.load(path, weights_only=True)
    restored_policy.load_state_dict(saved['policy'])
    restored_critic.load_state_dict(saved['critic'])
    with torch.no_grad():
        original = policy.sample(batch.context, batch.eligible, batch.forced_end, deterministic=True)
        restored = restored_policy.sample(batch.context, batch.eligible, batch.forced_end, deterministic=True)
        assert torch.equal(original.actions, restored.actions)
        assert torch.equal(original.log_prob, restored.log_prob)
        assert torch.equal(critic(batch.context), restored_critic(batch.context))
    print('TECHNICAL_GATE ' + json.dumps({'mode': mode, 'seed': seed, 'native_team_steps': 80,
          'updates': updates, 'wall_seconds': time.perf_counter() - started}))
    for world in worlds:
        world.close()
    controller.detach()


def test_real_optional_end_carries_actor_hidden_state(foundation, tmp_path):
    agent = load_foundation(foundation, tmp_path / 'hidden')
    schema = features(agent)
    policy = MaskPolicy(schema.context_dim, AGENTS, 'joint', hidden_size=32, seed=920620)
    critic = ValueCritic(schema.context_dim, hidden_size=32, seed=920620)
    controller = FrozenGateController(agent, policy, critic, schema, seed=920621)
    worlds = envs(920631)
    states, observations = base._reset_all(worlds)
    steps, dones = np.zeros(LANES, dtype=int), np.zeros(LANES, dtype=bool)
    agent.step(states, observations, steps, dones, deterministic=True)
    previous = agent.actor_hidden_np[:LANES].copy()
    assert np.any(previous != 0)
    # Force a legal singleton in this technical test, without changing the real decoder.
    agent.set_optional_end_hook(lambda data, **kwargs: data['eligible'] & (np.arange(AGENTS) == 1)[None])
    agent.step(states, observations, steps + 1, dones, deterministic=True)
    np.testing.assert_array_equal(agent.prev_actor_hidden_np[:LANES], previous)
    assert agent._d2_last_step['optional_end'][:, 1].all()
    assert not agent._d2_last_step['sample_Z'].any()
    for world in worlds:
        world.close()


def test_greedy_initial_keep_matches_fixed_clock_native_execution(foundation, tmp_path, monkeypatch):
    plain = load_foundation(foundation, tmp_path / 'plain')
    gated = load_foundation(foundation, tmp_path / 'gated')
    schema = features(gated)
    policy = MaskPolicy(schema.context_dim, AGENTS, 'joint', hidden_size=32, seed=920620)
    critic = ValueCritic(schema.context_dim, hidden_size=32, seed=920620)
    controller = FrozenGateController(gated, policy, critic, schema, seed=920621)
    plain.train(False)
    plain_worlds, gated_worlds = envs(920641), envs(920641)
    trace = []
    original_step = gated.step

    def record(*args, **kwargs):
        result = original_step(*args, **kwargs)
        trace.append((result[0].copy(), result[2]['agent_skills'].copy(),
                      gated.actor_hidden_np[:LANES].copy()))
        return result

    monkeypatch.setattr(gated, 'step', record)
    with base._preserve_rng():
        torch.manual_seed(920642)
        np.random.seed(920642)
        before_rng = torch.get_rng_state()
        _, count = collect_episode(gated_worlds, gated, controller, horizon=HORIZON, deterministic=True)
        # Deterministic labels, actions and mask consume no torch sampling stream.
        assert torch.equal(before_rng, torch.get_rng_state())
        states, observations = base._reset_all(plain_worlds)
        for lane in range(LANES):
            plain.reset_env_state(lane)
        for tick in range(HORIZON):
            result = plain.step(states, observations, np.full(LANES, tick), np.zeros(LANES, bool),
                                deterministic=True, return_step_data=True, build_infos=False)
            np.testing.assert_array_equal(result[0], trace[tick][0])
            np.testing.assert_array_equal(result[2]['agent_skills'], trace[tick][1])
            np.testing.assert_array_equal(plain.actor_hidden_np[:LANES], trace[tick][2])
            next_states, next_obs = [], []
            for lane, world in enumerate(plain_worlds):
                obs, _, _, _, info = world.step(result[0][lane])
                next_states.append(info['next_state'])
                next_obs.append(obs)
            states, observations = np.asarray(next_states), np.asarray(next_obs)
    assert count['optional_end_bits'] == 0
    assert_snapshot_equal(snapshot(plain), snapshot(gated))
    for world in plain_worlds + gated_worlds:
        world.close()


def test_feature_scaling_and_reset_do_not_leak_stale_labels_or_ages():
    schema = Scenario1Features(2, 1, 3)
    data = {'states': np.array([[1000, 500, 100, 250, 200, 80, 600, 700, .5]]),
            'observations': np.zeros((1, 2, 3)), 'held_team': np.array([-1]),
            'held_agents': np.array([[-1, -1]]), 'agent_ages': np.array([[99, 88]]),
            'team_ages': np.array([77]), 'reset': np.array([True]),
            'forced_end': np.ones((1, 2), dtype=bool), 'eligible': np.zeros((1, 2), dtype=bool),
            'team_forced': np.array([True])}
    encoded = schema.encode(data)
    assert encoded.shape == (1, schema.context_dim)
    torch.testing.assert_close(encoded[0, :9], torch.tensor([1., .5, .1, .25, .2, .08, .6, .7, .5]))
    data['held_team'][:] = 5
    data['held_agents'][:] = 3
    data['agent_ages'][:] = 2
    data['team_ages'][:] = 4
    assert torch.equal(encoded, schema.encode(data))
    data['reset'][:] = False
    data['held_team'][:] = -1
    with pytest.raises(ValueError, match='invalid held'):
        schema.encode(data)
