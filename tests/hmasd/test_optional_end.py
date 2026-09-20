"""Core hook contract: mandatory clocks, partial order, and unchanged disabled path."""
import ast
import copy
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import hmasd.agent as agent_module
from hmasd.agent import HMASDAgent


class Coordinator:
    def __init__(self):
        self.calls = []

    def evaluate_held_batch(self, state, observations, held_team, held_agents):
        return {'Z_logits': torch.zeros(len(state), 6),
                'z_logits': torch.zeros(len(state), 3, 6)}

    def assign_partial_batch(self, state, observations, held_team, held_agents,
                             sample_team, sampled, deterministic=False):
        self.calls.append((sample_team.clone(), sampled.clone()))
        team = torch.zeros_like(held_team) if deterministic else torch.randint(6, held_team.shape)
        labels = torch.zeros_like(held_agents) if deterministic else torch.randint(6, held_agents.shape)
        return {
            'team_skills': torch.where(sample_team, team, held_team),
            'agent_skills': torch.where(sampled, labels, held_agents),
            'team_log_probs': torch.zeros_like(team, dtype=torch.float32),
            'agent_log_probs': torch.zeros_like(labels, dtype=torch.float32),
            'order': torch.argsort(torch.arange(3)[None] + 3 * sampled.long(), dim=1),
            'state_values': torch.zeros(len(state), 1),
            'agent_values': torch.zeros(len(state), 3),
        }


def bare_agent():
    agent = HMASDAgent.__new__(HMASDAgent)
    agent.config = SimpleNamespace(n_agents=3, use_valuenorm=False)
    agent.device = torch.device('cpu')
    agent.d2_enabled = True
    agent.d2_cost_c = agent.d2_cost_c_Z = float('inf')
    agent.d2_k_max = agent.d2_k_Z = 10
    for name in ('env_team_skills', 'env_agent_skills', 'env_log_probs', 'env_skill_ages',
                 'env_team_ages', 'env_timers', 'env_d2_last_decision'):
        setattr(agent, name, {})
    agent.d2_metrics = agent._new_d2_metrics()
    agent.skill_coordinator = Coordinator()
    agent._normalize_states = lambda x, **kwargs: x
    agent._normalize_observations = lambda x, **kwargs: x
    agent._add_transition_profile = lambda *args: None
    return agent


def step(agent, tick=1, deterministic=True):
    return agent._batched_assign_skills_d2(
        np.zeros((2, 4)), np.zeros((2, 3, 2)), np.full(2, tick),
        np.zeros(2, dtype=bool), deterministic=deterministic)


def prime(agent):
    step(agent, 0)
    agent.skill_coordinator.calls.clear()


def test_disabled_matches_committed_pre_hook_method_and_rng():
    # Reference is read from the pre-hook commit, never generated from candidate output.
    source = subprocess.check_output(
        ['git', 'show', '56b203dfc:hmasd/agent.py'], cwd=ROOT, text=True)
    tree = ast.parse(source)
    klass = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'HMASDAgent')
    method = next(node for node in klass.body if isinstance(node, ast.FunctionDef)
                  and node.name == '_batched_assign_skills_d2')
    reference = ast.Module(body=[method], type_ignores=[])
    namespace = dict(vars(agent_module))
    exec(compile(reference, '<committed-before-hook>', 'exec'), namespace)
    original = namespace['_batched_assign_skills_d2']

    def trace(enabled_method):
        agent = bare_agent()
        if not enabled_method:
            agent._batched_assign_skills_d2 = original.__get__(agent)
        else:
            agent.set_optional_end_hook(None)
        torch.manual_seed(817)
        rows = []
        for tick in range(24):
            if tick == 13:
                agent.env_agent_skills[0] = np.full(3, -1)
            output = step(agent, tick, deterministic=False)
            rows.append((copy.deepcopy(output), copy.deepcopy(agent._d2_last_step)))
        metrics = copy.deepcopy(agent.d2_metrics)
        metrics.pop('coordinator_inference_seconds')
        return rows, metrics, torch.get_rng_state()

    old, new = trace(False), trace(True)

    def equal(a, b):
        if isinstance(a, dict):
            assert a.keys() == b.keys()
            for key in a:
                equal(a[key], b[key])
        elif isinstance(a, (tuple, list)):
            assert len(a) == len(b)
            for left, right in zip(a, b):
                equal(left, right)
        elif torch.is_tensor(a):
            assert torch.equal(a, b)
        else:
            np.testing.assert_equal(a, b)
    equal(old, new)


def test_optional_singleton_keeps_team_and_other_labels_and_resets_only_its_age():
    agent = bare_agent()
    prime(agent)
    snapshots = []

    def choose(snapshot, *, deterministic):
        snapshots.append(snapshot)
        with pytest.raises(ValueError):
            snapshot['states'][0, 0] = 99
        mask = np.zeros((2, 3), dtype=bool)
        mask[:, 1] = True
        return mask

    agent.set_optional_end_hook(choose)
    step(agent)
    last = agent._d2_last_step
    assert not last['team_decision'].any()
    np.testing.assert_array_equal(last['sampled_mask'], [[False, True, False]] * 2)
    np.testing.assert_array_equal(last['order'], [[0, 2, 1]] * 2)
    np.testing.assert_array_equal(snapshots[0]['agent_ages'], np.ones((2, 3)))
    np.testing.assert_array_equal(last['agent_ages'], [[1, 0, 1]] * 2)
    # Deterministic fake decoder reselects the same label: still a real END event.
    np.testing.assert_array_equal(agent.env_agent_skills[0], [0, 0, 0])
    assert agent.env_team_ages[0] == 2
    assert last['agent_cause'][0, 1] == agent.D2_CAUSE_OPTIONAL_END
    assert agent.d2_metrics['cause_counts']['optional_end'] == 2
    step(agent, 2)
    np.testing.assert_array_equal(snapshots[0]['agent_ages'], np.ones((2, 3)))


def test_mandatory_team_and_local_caps_are_not_gate_decisions():
    agent = bare_agent()
    prime(agent)
    agent.env_team_ages[0] = 10
    agent.env_skill_ages[1] = np.array([10, 4, 2])
    seen = []

    def keep(snapshot, *, deterministic):
        seen.append(snapshot)
        return np.zeros((2, 3), dtype=bool)

    agent.set_optional_end_hook(keep)
    step(agent, 10)
    np.testing.assert_array_equal(seen[0]['eligible'], [[False] * 3, [False, True, True]])
    np.testing.assert_array_equal(agent._d2_last_step['sample_Z'], [True, False])
    np.testing.assert_array_equal(agent._d2_last_step['sampled_mask'], [[True] * 3, [True, False, False]])
    assert agent._d2_last_step['agent_cause'][1, 0] == agent.D2_CAUSE_CAP


@pytest.mark.parametrize('bad', [np.zeros((2, 3)), np.zeros((1, 3), dtype=bool),
                                np.ones((2, 3), dtype=bool)])
def test_rejects_malformed_or_ineligible_requests(bad):
    agent = bare_agent()
    agent.set_optional_end_hook(lambda snapshot, **kwargs: bad)
    with pytest.raises(ValueError, match='optional END'):
        step(agent, 0)


def test_hook_is_explicit_and_requires_fixed_clock_d2():
    agent = bare_agent()
    assert not hasattr(agent, '_optional_end_hook')
    agent.d2_enabled = False
    with pytest.raises(ValueError):
        agent.set_optional_end_hook(lambda *_: None)
    agent.d2_enabled = True
    agent.d2_cost_c = 0
    with pytest.raises(ValueError):
        agent.set_optional_end_hook(lambda *_: None)
    agent.d2_cost_c = float('inf')
    agent.set_optional_end_hook(lambda snapshot, **kwargs: np.zeros((2, 3), dtype=bool))
    agent.d2_cost_c_Z = 0
    with pytest.raises(ValueError, match='remain'):
        step(agent)
