"""The real update entry must honor episode boundaries in stored transitions."""
from contextlib import nullcontext
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from hmasd.agent import HMASDAgent
from hmasd.utils import RolloutBuffer


class _MasksObserved(Exception):
    """Stop at the critic call, before any loss, backward or optimizer step."""


@pytest.mark.parametrize("cache_tensors", [False, True])
def test_discoverer_update_resets_on_episode_entry_not_terminal_transition(cache_tensors):
    buffer = RolloutBuffer(
        num_steps=4, num_envs=2, n_agents=1, obs_dim=3, action_dim=1,
        gru_hidden_size=2, n_Z=2, n_z=2, state_dim=3, sampler_seed=53,
    )
    # Episodes represented by these input rows are [7,8,8,8] and [4,4,5,5].
    # Both final transitions terminate; environment 0 also terminates on row 0.
    transition_dones = [[True, False, False, True], [False, True, False, True]]
    expected_entries = [[1.0, 0.0, 1.0, 1.0], [1.0, 1.0, 0.0, 1.0]]
    for t in range(4):
        for env in range(2):
            assert buffer.add(
                t=t, env_idx=env,
                state=np.array([env, t, 1], dtype=np.float32),
                obs=np.array([[env, t, 1]], dtype=np.float32),
                action=np.zeros((1, 1)), reward=np.zeros(1),
                done=np.array([transition_dones[env][t]]), value=np.zeros(1),
                log_prob=np.zeros(1),
                gru_hidden_state=np.full((1, 2), env + 10, dtype=np.float32),
                critic_gru_hidden_state=np.full((1, 2), env + 20, dtype=np.float32),
                team_skill=0, agent_skills=np.zeros(1, dtype=np.int64),
            )

    captured = {}

    def actor_call(observations, initial_hidden, actions, masks, skills):
        captured["actor"] = (observations[0, :, 0].clone(), initial_hidden.clone(), masks.clone())
        return torch.zeros_like(masks), torch.tensor(0.0)

    def critic_call(states, initial_hidden, masks, skills):
        captured["critic"] = (states[0, :, 0].clone(), initial_hidden.clone(), masks.clone())
        raise _MasksObserved

    agent = HMASDAgent.__new__(HMASDAgent)
    agent.r39_native_toy_fixed_primitives = False
    agent.enable_runtime_profiling = False
    agent.config = SimpleNamespace(
        gamma=.99, gae_lambda=.95, ppo_epochs=1, sequence_batch_size=2, k=4,
        cache_update_tensors=cache_tensors, use_valuenorm=False,
        use_obsnorm=False, use_statenorm=False,
    )
    agent.device = torch.device("cpu")
    agent.rollout_buffer = buffer
    agent.value_norm_discoverer = None
    agent.use_low_level_compact = False
    agent.use_central_snapshot = False
    agent._update_autocast = nullcontext
    agent.skill_discoverer = SimpleNamespace(
        _apply_compact_context=lambda values, context, adapter: values,
        _apply_central_input=lambda observations, central: observations,
        actor_context_adapter=None, critic_context_adapter=None,
        actor=SimpleNamespace(evaluate_actions=actor_call), critic=critic_call,
    )

    # Storage, GAE, cached/uncached chunking and the update entry are all real.
    # Recording doubles stop execution before optimization; no learner is fitted.
    with pytest.raises(_MasksObserved):
        agent.update_discoverer_from_rollout(np.zeros((2, 1)), np.ones(2, dtype=bool))

    assert set(captured) == {"actor", "critic"}
    for name, hidden_offset in (("actor", 10), ("critic", 20)):
        identities, initial_hidden, masks = captured[name]
        assert sorted(identities.tolist()) == [0.0, 1.0]
        for column, identity in enumerate(identities.int().tolist()):
            torch.testing.assert_close(masks[:, column], torch.tensor(expected_entries[identity]))
            torch.testing.assert_close(
                initial_hidden[column], torch.full((2,), float(identity + hidden_offset))
            )
