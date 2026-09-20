"""Zero-fit evaluator checks on initialized tiny native Scenario1 foundations."""
import copy
import hashlib
import json
import random
import time

import numpy as np
import pytest
import torch

from hmasd.agent import HMASDAgent
from scripts import run_flexible_skill_duration_e0 as base
from experiments.candidates.team_conditioned_termination.evaluation import (
    EvaluationFailure, evaluate_episode,
)
from experiments.candidates.team_conditioned_termination.policy import MaskPolicy
from experiments.candidates.team_conditioned_termination.runtime import (
    Scenario1Features, foundation_modules,
)


LANES, HORIZON, AGENTS, USERS = 2, 20, 6, 12
INITIAL_SEED, WORLD_SEED = 920701, 920711


def _forbid(*args, **kwargs):
    raise AssertionError("evaluation called a learner update or buffer write")


def _state(agent):
    states = {name: copy.deepcopy(module.state_dict())
              for name, module in foundation_modules(agent).items()}
    for name in ("value_norm_coordinator", "value_norm_discoverer"):
        normalizer = getattr(agent, name)
        if normalizer is not None:
            states[name] = {key: torch.tensor(np.array(getattr(normalizer, key), copy=True))
                            for key in ("mean", "var", "count")}
    return states


def _equal_states(before, after):
    assert before.keys() == after.keys()
    for module in before:
        for key in before[module]:
            assert torch.equal(before[module][key], after[module][key]), (module, key)


@pytest.fixture
def factory(tmp_path, monkeypatch):
    worlds_created, facts = [], {"native_team_steps": 0, "model_constructions": 0,
                                 "foundation_optimizer_steps": 0, "gate_optimizer_steps": 0}
    started = time.perf_counter()
    threads = torch.get_num_threads()
    torch.set_num_threads(1)

    def make():
        worlds = base._make_envs(LANES, WORLD_SEED, AGENTS, USERS, HORIZON)
        worlds_created.extend(worlds)
        config = base._make_config('D0', INITIAL_SEED, LANES, HORIZON, HORIZON,
                                   AGENTS, USERS, 1, worlds[0].state_dim, worlds[0].obs_dim)
        config.n_Z = config.n_z = 6
        config.hidden_size = config.embedding_dim = config.gru_hidden_size = 32
        config.n_heads = 2
        config.use_obsnorm = config.use_statenorm = False
        with base._preserve_rng():
            torch.random.default_generator.manual_seed(INITIAL_SEED)
            agent = HMASDAgent(config, log_dir=str(tmp_path / str(facts['model_constructions'])),
                               device=torch.device('cpu'))
        facts['model_constructions'] += 1
        agent.train(False)
        monkeypatch.setattr(agent, 'update', _forbid)
        monkeypatch.setattr(agent, 'store_transition_batch', _forbid)
        for value in vars(agent).values():
            if isinstance(value, torch.optim.Optimizer):
                monkeypatch.setattr(value, 'step', _forbid)
        for world in worlds:
            original = world.step

            def counted(action, inner=original):
                result = inner(action)
                facts['native_team_steps'] += 1
                return result

            monkeypatch.setattr(world, 'step', counted)
        return agent, worlds

    yield make
    for world in worlds_created:
        world.close()
    torch.set_num_threads(threads)
    facts['wall_seconds'] = time.perf_counter() - started
    print('TECHNICAL_EVALUATION ' + json.dumps(facts))


def _record(agent, monkeypatch):
    trace = []
    original = agent.step

    def step(*args, **kwargs):
        result = original(*args, **kwargs)
        trace.append((result[0].copy(), result[2]['agent_skills'].copy(),
                      agent.actor_hidden_np[:LANES].copy(),
                      np.array([agent.env_team_skills[i] for i in range(LANES)])))
        return result

    monkeypatch.setattr(agent, 'step', step)
    return trace


def _run(agent, worlds, rule='as_trained', policy=None):
    return evaluate_episode(worlds, agent, rule=rule, evaluation_seed=WORLD_SEED,
                            horizon=HORIZON, policy=policy)


def test_as_trained_matches_independent_native_loop(factory, monkeypatch):
    evaluated, worlds = factory()
    reference, reference_worlds = factory()
    trace = _record(evaluated, monkeypatch)
    before = _state(evaluated)
    result = _run(evaluated, worlds)
    states, obs = [], []
    for lane, world in enumerate(reference_worlds):
        observation, info = world.reset(seed=WORLD_SEED + lane)
        reference.reset_env_state(lane)
        states.append(info['state'])
        obs.append(observation)
    states, obs = np.asarray(states), np.asarray(obs)
    returns = np.zeros(LANES)
    for tick in range(HORIZON):
        action, _, data = reference.step(states, obs, np.full(LANES, tick),
                                         np.zeros(LANES, bool), deterministic=True,
                                         return_step_data=True, build_infos=False)
        np.testing.assert_array_equal(action, trace[tick][0])
        np.testing.assert_array_equal(data['agent_skills'], trace[tick][1])
        np.testing.assert_array_equal(reference.actor_hidden_np[:LANES], trace[tick][2])
        for lane, world in enumerate(reference_worlds):
            obs[lane], reward, _, _, info = world.step(action[lane])
            states[lane] = info['next_state']
            returns[lane] += reward
    np.testing.assert_array_equal(result['return_sums_U'], returns)
    np.testing.assert_array_equal(result['native_scores_J'], AGENTS * returns / HORIZON)
    np.testing.assert_allclose(result['native_scores_J'], result['component_means']['total_reward'],
                               rtol=1e-14, atol=1e-14)
    assert result['evaluation_steps'] == 40 and result['completed_episodes'] == 2
    assert result['decision_rows'] == result['team_decision_rows'] == 4
    assert result['optional_end_bits'] == 0 and result['resampled_local_bits'] == 24
    _equal_states(before, _state(evaluated))
    assert '_batched_assign_skills' not in vars(evaluated)


@pytest.mark.parametrize('mode', ['joint', 'independent'])
def test_initial_keep_gate_matches_fixed_without_mutating_caller(factory, monkeypatch, mode):
    fixed, fixed_worlds = factory()
    gated, gated_worlds = factory()
    fixed_trace, gated_trace = _record(fixed, monkeypatch), _record(gated, monkeypatch)
    features = Scenario1Features(AGENTS, USERS, gated.config.obs_dim)
    gate = MaskPolicy(features.context_dim, AGENTS, mode, hidden_size=32, seed=920721)
    before_gate = copy.deepcopy(gate.state_dict())
    before = _state(gated)
    plain = _run(fixed, fixed_worlds)
    result = _run(gated, gated_worlds, mode, gate)
    assert plain['native_scores_J'] == result['native_scores_J']
    for left, right in zip(fixed_trace, gated_trace):
        for a, b in zip(left, right):
            np.testing.assert_array_equal(a, b)
    assert gate.training and not gate._sample_generators
    for key, value in before_gate.items():
        assert torch.equal(value, gate.state_dict()[key])
    assert not getattr(gated, '_optional_end_hook', None)
    assert '_batched_assign_skills' not in vars(gated)
    assert result['optional_end_bits'] == 0
    _equal_states(before, _state(gated))


def test_r10_exact_private_draw_schedule_holding_and_repeatability(factory, monkeypatch):
    agent, worlds = factory()
    trace = _record(agent, monkeypatch)
    before = _state(agent)
    py_rng, np_rng, torch_rng = random.getstate(), np.random.get_state(), torch.get_rng_state().clone()
    result = _run(agent, worlds, 'uniform_every_10')
    assert random.getstate() == py_rng
    after_np = np.random.get_state()
    assert after_np[0] == np_rng[0] and after_np[2:] == np_rng[2:]
    np.testing.assert_array_equal(after_np[1], np_rng[1])
    assert torch.equal(torch_rng, torch.get_rng_state())
    # Independent reproduction of the published rule's address/draw convention.
    address = int.from_bytes(hashlib.sha256(b'uniform_every_10').digest()[:8], 'big')
    rng = np.random.default_rng([WORLD_SEED, address])
    agent_hist, team_hist = np.zeros(6, int), np.zeros(6, int)
    for tick in range(HORIZON):
        drawn_team = rng.integers(0, 6, size=LANES)
        drawn_agents = rng.integers(0, 6, size=(LANES, AGENTS))
        if tick % 10 == 0:
            held_team, held_agents = drawn_team, drawn_agents
        np.testing.assert_array_equal(trace[tick][1], held_agents)
        np.testing.assert_array_equal(trace[tick][3], held_team)
        agent_hist += np.bincount(held_agents.ravel(), minlength=6)
        team_hist += np.bincount(held_team, minlength=6)
    assert result['executed_label_histograms'] == {'agents': agent_hist.tolist(), 'team': team_hist.tolist()}
    assert result['decision_rows'] == 4
    assert result['label_change_counts']['agent_comparisons'] == 19 * LANES * AGENTS
    again = _run(agent, worlds, 'uniform_every_10')
    assert again['native_scores_J'] == result['native_scores_J']
    assert again['label_change_counts'] == result['label_change_counts']
    _equal_states(before, _state(agent))


def test_nonzero_joint_mask_is_executed_and_detached(factory):
    agent, worlds = factory()
    features = Scenario1Features(AGENTS, USERS, agent.config.obs_dim)
    policy = MaskPolicy(features.context_dim, AGENTS, 'joint', hidden_size=32,
                        seed=920721, end_probability=.9)
    result = _run(agent, worlds, 'joint', policy)
    assert result['optional_end_bits'] == 18 * LANES * AGENTS
    assert result['team_decision_rows'] == 4
    assert result['decision_rows'] == LANES * HORIZON
    assert not getattr(agent, '_optional_end_hook', None)


@pytest.mark.parametrize('rule', ['uniform_every_10', 'joint'])
def test_failure_retains_returned_step_and_restores_attachments(factory, monkeypatch, rule):
    agent, worlds = factory()
    original = worlds[0].step

    def bad_reward(action):
        obs, _, term, trunc, info = original(action)
        return obs, float('nan'), term, trunc, info

    monkeypatch.setattr(worlds[0], 'step', bad_reward)
    schema = Scenario1Features(AGENTS, USERS, agent.config.obs_dim)
    policy = MaskPolicy(schema.context_dim, AGENTS, 'joint', hidden_size=32) if rule == 'joint' else None
    before = torch.get_rng_state().clone()
    with pytest.raises(EvaluationFailure, match='nonfinite evaluation reward') as failure:
        _run(agent, worlds, rule, policy)
    result = failure.value.summary
    assert result['status'] == 'incomplete' and result['native_scores_J'] is None
    assert result['evaluation_steps'] == 1 and result['steps_per_lane'] == [1, 0]
    assert sum(result['executed_label_histograms']['agents']) == AGENTS
    assert result['gate_optimizer_steps'] == result['foundation_optimizer_steps'] == 0
    assert '_batched_assign_skills' not in vars(agent)
    assert not getattr(agent, '_optional_end_hook', None)
    assert torch.equal(before, torch.get_rng_state())
    json.dumps(result, allow_nan=False)


def test_live_agent_and_rule_mismatch_refused_before_steps(factory):
    agent, worlds = factory()
    hook = lambda state, **kwargs: np.zeros_like(state['eligible'])
    agent.set_optional_end_hook(hook)
    with pytest.raises(ValueError, match='live gate'):
        _run(agent, worlds)
    assert agent._optional_end_hook is hook
    agent.set_optional_end_hook(None)
    schema = Scenario1Features(AGENTS, USERS, agent.config.obs_dim)
    policy = MaskPolicy(schema.context_dim, AGENTS, 'joint', hidden_size=32)
    with pytest.raises(ValueError, match='must match'):
        _run(agent, worlds, 'independent', policy)
    with pytest.raises(ValueError, match='fixed reference'):
        _run(agent, worlds, 'as_trained', policy)
