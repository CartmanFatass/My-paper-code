import random
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from manifold_hmasd.her_replay_buffer import HERReplayBuffer, ManifoldDistanceReward
from manifold_hmasd.agent import GoalConditionedPolicy, ManifoldHMASDAgent


def _value_function(observations, goals):
    del goals
    return torch.as_tensor(np.asarray(observations), dtype=torch.float32)[:, :, 0] - 100.0


def _action_logprob_function(observations, goals, actions):
    del goals, actions
    shape = np.asarray(observations).shape[:2]
    return torch.zeros(shape, dtype=torch.float32)


def _store_three_step_episode(buffer, trajectory_id="env-0-episode-0"):
    for timestep in range(3):
        buffer.store_transition(
            state=np.array([float(timestep)]),
            action=np.array([[0.0]]),
            reward=float(timestep + 1),
            next_state=np.array([float(timestep + 1)]),
            done=timestep == 2,
            goal=np.array([99.0]),
            trajectory_id=trajectory_id,
            timestep=timestep,
            observation=np.array([[100.0 + float(timestep)]]),
            next_observation=np.array([[101.0 + float(timestep)]]),
            old_action_logprob=np.array([-0.25]),
        )


def test_her_freezes_ordered_gae_before_random_row_sampling():
    buffer = HERReplayBuffer(capacity=32, her_strategy="future", her_k=0)
    _store_three_step_episode(buffer)
    buffer.store_episode(
        trajectory_id="env-0-episode-0",
        value_function=_value_function,
        action_logprob_function=_action_logprob_function,
        gamma=1.0,
        gae_lambda=1.0,
    )

    original = list(buffer.replay_buffer)
    assert original[0].state[0] == 0.0
    assert original[0].observation[0, 0] == 100.0
    np.testing.assert_allclose(original[0].old_action_logprob, [-0.25])
    assert [row.timestep for row in original] == [0, 1, 2]
    np.testing.assert_allclose(
        [row.advantage[0] for row in original], [6.0, 4.0, 1.0]
    )
    np.testing.assert_allclose(
        [row.return_value[0] for row in original], [6.0, 5.0, 3.0]
    )

    random.seed(123)
    sampled = buffer.sample(3)
    frozen_by_timestep = {row.timestep: row.advantage[0] for row in sampled}
    assert frozen_by_timestep == {0: 6.0, 1: 4.0, 2: 1.0}

    first_episode_advantages = [row.advantage.copy() for row in original]
    for timestep in range(2):
        buffer.store_transition(
            state=np.array([float(timestep)]),
            action=np.array([0.0]),
            reward=1000.0,
            next_state=np.array([float(timestep + 1)]),
            done=timestep == 1,
            goal=np.array([0.0]),
            trajectory_id="env-1-episode-0",
            timestep=timestep,
            observation=np.array([[float(timestep)]]),
            next_observation=np.array([[float(timestep + 1)]]),
            old_action_logprob=np.array([-0.5]),
        )
    buffer.store_episode(
        trajectory_id="env-1-episode-0",
        value_function=_value_function,
        action_logprob_function=_action_logprob_function,
        gamma=1.0,
        gae_lambda=1.0,
    )
    for row, expected in zip(original, first_episode_advantages):
        np.testing.assert_array_equal(row.advantage, expected)


def test_future_her_relabels_an_intact_contiguous_segment_before_gae():
    random.seed(55)
    buffer = HERReplayBuffer(capacity=64, her_strategy="future", her_k=2)
    _store_three_step_episode(buffer)
    buffer.store_episode(
        trajectory_id="env-0-episode-0",
        value_function=_value_function,
        action_logprob_function=_action_logprob_function,
        gamma=0.9,
        gae_lambda=0.95,
    )

    her_segments = {}
    for row in buffer.replay_buffer:
        if row.segment_id != "original":
            her_segments.setdefault(row.segment_id, []).append(row)
    assert set(her_segments) == {"her-0-0", "her-0-1", "her-1-0", "her-1-1"}
    for rows in her_segments.values():
        start = rows[0].timestep
        assert [row.timestep for row in rows] == list(range(start, start + len(rows)))
        assert len({tuple(np.asarray(row.goal).tolist()) for row in rows}) == 1
        assert all(row.advantage is not None and row.return_value is not None for row in rows)
        assert rows[-1].done
        assert rows[-1].reward == 0.0
        assert rows[-1].info['is_success'] is True
        assert rows[-1].info['goal_achieved'] is True
        assert all(np.allclose(row.old_action_logprob, -0.25) for row in rows)
        assert all(row.critic_only for row in rows)
    assert all(not row.critic_only for row in buffer.replay_buffer if row.segment_id == "original")


def test_manifold_actor_objective_ignores_all_her_and_critic_only_rows():
    current_logp = torch.tensor([0.2, -0.1, 0.7], requires_grad=True)
    entropy = torch.tensor([1.0, 2.0, 50.0])
    old_logp = torch.tensor([0.0, 0.0, -100.0])
    advantages = torch.tensor([1.0, 3.0, 1e6])
    all_her = torch.zeros(3, dtype=torch.bool)
    policy_loss, entropy_loss = ManifoldHMASDAgent._actor_objective(
        current_logp, entropy, old_logp, advantages, all_her, 0.2
    )
    assert policy_loss.item() == 0.0
    assert entropy_loss.item() == 0.0

    mixed = torch.tensor([True, True, False])
    mixed_loss, mixed_entropy = ManifoldHMASDAgent._actor_objective(
        current_logp, entropy, old_logp, advantages, mixed, 0.2
    )
    altered_loss, altered_entropy = ManifoldHMASDAgent._actor_objective(
        current_logp,
        torch.tensor([1.0, 2.0, -9999.0]),
        torch.tensor([0.0, 0.0, 9999.0]),
        torch.tensor([1.0, 3.0, -9999.0]),
        mixed,
        0.2,
    )
    torch.testing.assert_close(mixed_loss, altered_loss)
    torch.testing.assert_close(mixed_entropy, altered_entropy)


def test_her_fails_closed_for_missing_or_ambiguous_trajectory_order():
    buffer = HERReplayBuffer(capacity=8, her_k=0)
    with pytest.raises(ValueError, match="trajectory_id"):
        buffer.store_transition(
            state=np.array([0.0]),
            action=np.array([0.0]),
            reward=0.0,
            next_state=np.array([1.0]),
            done=False,
            goal=np.array([1.0]),
        )
    buffer.store_transition(
        state=np.array([0.0]),
        action=np.array([0.0]),
        reward=0.0,
        next_state=np.array([1.0]),
        done=False,
        goal=np.array([1.0]),
        trajectory_id="a",
        timestep=0,
        observation=np.array([[0.0]]),
        next_observation=np.array([[1.0]]),
        old_action_logprob=np.array([-0.1]),
    )
    assert buffer.has_pending_trajectories
    with pytest.raises(ValueError, match="contiguous"):
        buffer.store_transition(
            state=np.array([1.0]),
            action=np.array([0.0]),
            reward=0.0,
            next_state=np.array([2.0]),
            done=True,
            goal=np.array([1.0]),
            trajectory_id="a",
            timestep=2,
            observation=np.array([[1.0]]),
            next_observation=np.array([[2.0]]),
            old_action_logprob=np.array([-0.1]),
        )


def test_manifold_policy_collection_replay_old_logp_parity():
    torch.manual_seed(7712)
    policy = GoalConditionedPolicy(3, 2, 2, hidden_dim=8)
    observations = torch.randn(6, 3)
    goals = torch.randn(6, 2)
    actions, collected_logp, collected_values, _ = policy(observations, goals)
    replay_logp, _entropy, replay_values = policy.evaluate_actions(
        observations, goals, actions
    )
    torch.testing.assert_close(replay_logp, collected_logp, rtol=0, atol=1e-7)
    torch.testing.assert_close(replay_values, collected_values, rtol=0, atol=1e-7)


def test_manifold_buffer_freezes_exact_policy_observations_actions_and_logps():
    torch.manual_seed(7713)
    agent = ManifoldHMASDAgent.__new__(ManifoldHMASDAgent)
    agent.device = torch.device("cpu")
    agent.policy = GoalConditionedPolicy(3, 2, 2, hidden_dim=8)
    buffer = HERReplayBuffer(capacity=8, her_k=0)
    goal = np.array([0.5, -0.5], dtype=np.float32)
    collected_logps = []
    for timestep in range(2):
        observations = torch.randn(2, 3)
        goals = torch.as_tensor(goal).unsqueeze(0).expand(2, -1)
        actions, logps, _values, _ = agent.policy(observations, goals)
        collected_logps.append(logps.detach().numpy())
        buffer.store_transition(
            state=np.array([10.0 + timestep, 20.0 + timestep]),
            action=actions.detach().numpy(),
            reward=1.0,
            next_state=np.array([11.0 + timestep, 21.0 + timestep]),
            done=timestep == 1,
            goal=goal,
            trajectory_id="exact-policy-inputs",
            timestep=timestep,
            observation=observations.numpy(),
            next_observation=(observations + 0.25).numpy(),
            old_action_logprob=logps.detach().numpy(),
        )
    buffer.store_episode(
        trajectory_id="exact-policy-inputs",
        value_function=agent._trajectory_values,
        action_logprob_function=agent._trajectory_action_logprobs,
        gamma=0.9,
        gae_lambda=0.95,
    )
    rows = list(buffer.replay_buffer)
    for timestep, row in enumerate(rows):
        np.testing.assert_allclose(
            row.old_action_logprob, collected_logps[timestep], rtol=0, atol=1e-7
        )
        assert not np.array_equal(row.state, row.observation[0])


def test_her_named_rngs_are_independent_and_strictly_restorable():
    def completed_buffer(relabel_seed):
        buffer = HERReplayBuffer(
            capacity=64,
            her_strategy="episode",
            her_k=2,
            relabel_seed=relabel_seed,
            sample_seed=404,
        )
        _store_three_step_episode(buffer)
        buffer.store_episode(
            trajectory_id="env-0-episode-0",
            value_function=_value_function,
            action_logprob_function=_action_logprob_function,
            gamma=0.9,
            gae_lambda=0.95,
        )
        return buffer

    first = completed_buffer(1)
    second = completed_buffer(999)
    first_ids = [(row.segment_id, row.timestep) for row in first.sample(6)]
    second_ids = [(row.segment_id, row.timestep) for row in second.sample(6)]
    assert first_ids == second_ids

    state = first.get_rng_state()
    order_before_restore = [(row.segment_id, row.timestep) for row in first.sample(6)]
    first.set_rng_state(state)
    order_after_restore = [(row.segment_id, row.timestep) for row in first.sample(6)]
    assert order_before_restore == order_after_restore
    with pytest.raises(ValueError, match="exactly relabel and sample"):
        first.set_rng_state({'sample': state['sample']})


def _checkpoint_manifold_agent(populate=False):
    agent = ManifoldHMASDAgent.__new__(ManifoldHMASDAgent)
    agent.device = torch.device("cpu")
    agent.policy = GoalConditionedPolicy(3, 2, 2, hidden_dim=8)
    agent.policy_optimizer = torch.optim.Adam(agent.policy.parameters())
    agent.config = {'obs_dim': 3, 'state_dim': 2, 'action_dim': 2}
    agent.global_step = 7
    agent.training_info = {'policy_loss': [], 'value_loss': []}
    agent.replay_buffer = HERReplayBuffer(
        capacity=32, her_strategy='future', her_k=1,
        relabel_seed=303, sample_seed=404
    )
    agent.current_goals = {}
    agent.episode_starts = {}
    agent._episode_ids = {}
    agent._episode_timesteps = {}
    class RandomGoalGenerator:
        current_difficulty = 0.25
        difficulty_update_steps = 6

        def sample_goals(self, batch_size, device, current_states=None):
            del current_states
            goals = torch.randn((batch_size, 2), device=device)
            return goals, {'difficulty': self.current_difficulty, 'latent_goals': goals}

    agent.goal_generator = RandomGoalGenerator()
    agent._collection_tokens = {}
    agent._collection_frontiers = {}
    agent._collection_token_counter = 0
    if populate:
        for timestep in range(3):
            agent.replay_buffer.store_transition(
                state=np.array([float(timestep), float(timestep)]),
                action=np.array([[0.0, 0.0]]),
                reward=float(timestep + 1),
                next_state=np.array([float(timestep + 1), float(timestep + 1)]),
                done=timestep == 2,
                goal=np.array([99.0, 99.0]),
                trajectory_id="env-0-episode-0",
                timestep=timestep,
                observation=np.array([[100.0 + timestep, 0.0, 0.0]]),
                next_observation=np.array([[101.0 + timestep, 0.0, 0.0]]),
                old_action_logprob=np.array([-0.25]),
            )
        agent.replay_buffer.store_episode(
            trajectory_id="env-0-episode-0",
            value_function=_value_function,
            action_logprob_function=_action_logprob_function,
            gamma=0.9,
            gae_lambda=0.95,
        )
        agent.replay_buffer.store_transition(
            state=np.array([0.0, 0.0]),
            action=np.array([[0.0, 0.0]]),
            reward=1.0,
            next_state=np.array([1.0, 1.0]),
            done=False,
            goal=np.array([2.0, 2.0]),
            trajectory_id="manifold:1:4",
            timestep=0,
            observation=np.array([[100.0, 0.0, 0.0]]),
            next_observation=np.array([[101.0, 0.0, 0.0]]),
            old_action_logprob=np.array([-0.25]),
        )
        agent.current_goals = {1: torch.tensor([2.0, 2.0])}
        agent.episode_starts = {1: False}
        agent._episode_ids = {1: 4}
        agent._episode_timesteps = {1: 1}
    return agent


def test_manifold_checkpoint_strictly_restores_her_rngs(tmp_path):
    source = _checkpoint_manifold_agent(populate=True)
    source._compute_goal_reward = lambda _next_state, _goal: 0.75
    source.current_goals[2] = torch.tensor([3.0, 4.0])
    source.episode_starts[2] = False
    source._episode_ids[2] = 9
    source._episode_timesteps[2] = 0
    token_state = np.array([0.25, 0.5], dtype=np.float32)
    token_observations = np.array([[1.0, 2.0, 3.0]], dtype=np.float32)
    token_actions, token_info = source.step(
        token_observations, token_state, env_id=2, episode_step=1
    )
    with pytest.raises(ValueError, match="does not match exact collection input"):
        source.store_transition(
            token_state,
            np.array([0.5, 0.75]),
            token_observations + 1.0,
            np.array([[2.0, 3.0, 4.0]]),
            token_actions,
            1.0,
            False,
            token_info,
            env_id=2,
        )
    checkpoint_path = tmp_path / "manifold.pt"
    saved_rng_state = source.replay_buffer.get_rng_state()
    source.save_model(checkpoint_path)
    sample_observation = torch.tensor([[0.2, -0.1, 0.7]])
    expected_next_goal = source.goal_generator.sample_goals(1, source.device)[0][0]
    expected_next_action = source.policy(
        sample_observation, expected_next_goal.unsqueeze(0)
    )[0]
    expected = [
        (row.trajectory_id, row.timestep, row.segment_id)
        for row in source.replay_buffer.sample(4)
    ]
    source.replay_buffer.store_transition(
        state=np.array([1.0, 1.0]), action=np.array([[0.0, 0.0]]), reward=2.0,
        next_state=np.array([2.0, 2.0]), done=True, goal=np.array([2.0, 2.0]),
        trajectory_id="manifold:1:4", timestep=1,
        observation=np.array([[101.0, 0.0, 0.0]]),
        next_observation=np.array([[102.0, 0.0, 0.0]]),
        old_action_logprob=np.array([-0.25]),
    )
    source.replay_buffer.store_episode(
        trajectory_id="manifold:1:4", value_function=_value_function,
        action_logprob_function=_action_logprob_function, gamma=0.9, gae_lambda=0.95,
    )
    expected_tail = [
        (row.trajectory_id, row.timestep, row.segment_id)
        for row in source.replay_buffer.replay_buffer
    ]
    token_next_state = np.array([0.5, 0.75], dtype=np.float32)
    token_next_observations = np.array([[2.0, 3.0, 4.0]], dtype=np.float32)
    source.store_transition(
        token_state, token_next_state, token_observations, token_next_observations,
        token_actions, 1.0, False, token_info, env_id=2,
    )
    source_token_row = source.replay_buffer.episode_buffer["manifold:2:9"][0]

    restored = _checkpoint_manifold_agent(populate=False)
    restored._compute_goal_reward = lambda _next_state, _goal: 0.75
    restored.load_model(checkpoint_path)
    actual_next_goal = restored.goal_generator.sample_goals(1, restored.device)[0][0]
    actual_next_action = restored.policy(
        sample_observation, actual_next_goal.unsqueeze(0)
    )[0]
    torch.testing.assert_close(actual_next_goal, expected_next_goal)
    torch.testing.assert_close(actual_next_action, expected_next_action)
    assert restored.replay_buffer.get_rng_state()['relabel'] == saved_rng_state['relabel']
    assert [
        (row.trajectory_id, row.timestep, row.segment_id)
        for row in restored.replay_buffer.sample(4)
    ] == expected
    assert "manifold:1:4" in restored.replay_buffer.episode_buffer
    restored.replay_buffer.store_transition(
        state=np.array([1.0, 1.0]), action=np.array([[0.0, 0.0]]), reward=2.0,
        next_state=np.array([2.0, 2.0]), done=True, goal=np.array([2.0, 2.0]),
        trajectory_id="manifold:1:4", timestep=1,
        observation=np.array([[101.0, 0.0, 0.0]]),
        next_observation=np.array([[102.0, 0.0, 0.0]]),
        old_action_logprob=np.array([-0.25]),
    )
    restored.replay_buffer.store_episode(
        trajectory_id="manifold:1:4", value_function=_value_function,
        action_logprob_function=_action_logprob_function, gamma=0.9, gae_lambda=0.95,
    )
    restored_tail = [
        (row.trajectory_id, row.timestep, row.segment_id)
        for row in restored.replay_buffer.replay_buffer
    ]
    assert restored_tail == expected_tail
    restored.store_transition(
        token_state, token_next_state, token_observations, token_next_observations,
        token_actions, 1.0, False, token_info, env_id=2,
    )
    restored_token_row = restored.replay_buffer.episode_buffer["manifold:2:9"][0]
    replay_logp, _entropy, _value = restored.policy.evaluate_actions(
        torch.as_tensor(restored_token_row.observation),
        torch.as_tensor(restored_token_row.goal).unsqueeze(0),
        torch.as_tensor(restored_token_row.action),
    )
    torch.testing.assert_close(
        replay_logp,
        torch.as_tensor(restored_token_row.old_action_logprob),
        rtol=0,
        atol=1e-7,
    )
    for name in ('state', 'next_state', 'observation', 'next_observation', 'action', 'goal'):
        np.testing.assert_array_equal(
            np.asarray(getattr(restored_token_row, name)),
            np.asarray(getattr(source_token_row, name)),
        )

    token_state[...] = -10
    token_next_state[...] = -11
    token_observations[...] = -12
    token_next_observations[...] = -13
    token_actions[...] = -14
    token_info['goal'][...] = -15
    token_info['action_logprobs'][...] = -16
    np.testing.assert_array_equal(restored_token_row.state, [0.25, 0.5])
    np.testing.assert_array_equal(restored_token_row.next_state, [0.5, 0.75])
    np.testing.assert_array_equal(restored_token_row.observation, [[1.0, 2.0, 3.0]])
    np.testing.assert_array_equal(restored_token_row.next_observation, [[2.0, 3.0, 4.0]])
    np.testing.assert_array_equal(restored_token_row.goal, [3.0, 4.0])
    with pytest.raises(ValueError, match="stale, or reused"):
        restored.store_transition(
            np.array([0.25, 0.5]), np.array([0.5, 0.75]),
            np.array([[1.0, 2.0, 3.0]]), np.array([[2.0, 3.0, 4.0]]),
            np.asarray(source_token_row.action), 1.0, False, token_info, env_id=2,
        )

    invalid_path = tmp_path / "manifold-invalid.pt"
    torch.save({'policy_state_dict': source.policy.state_dict()}, invalid_path)
    with pytest.raises(ValueError, match="missing strict state"):
        restored.load_model(invalid_path)

    shape_path = tmp_path / "manifold-shape-invalid.pt"
    invalid_shape = torch.load(checkpoint_path, weights_only=False)
    invalid_shape['replay_buffer_state']['episode_buffer']["manifold:1:4"][0].observation = (
        np.zeros((1, 99), dtype=np.float32)
    )
    torch.save(invalid_shape, shape_path)
    with pytest.raises(ValueError, match="policy replay shape"):
        restored.load_model(shape_path)

    device_path = tmp_path / "manifold-device-invalid.pt"
    invalid_device = torch.load(checkpoint_path, weights_only=False)
    invalid_device['topology']['policy_device'] = {'type': 'cuda', 'index': 0}
    torch.save(invalid_device, device_path)
    with pytest.raises(ValueError, match="policy parameter device"):
        restored.load_model(device_path)

    rng_path = tmp_path / "manifold-rng-invalid.pt"
    invalid_rng = torch.load(checkpoint_path, weights_only=False)
    invalid_rng['torch_sampling_rng_state']['cuda_initialized'] = False
    invalid_rng['torch_sampling_rng_state']['cuda'] = []
    invalid_rng['torch_sampling_rng_state']['cuda_device_count'] = 1
    torch.save(invalid_rng, rng_path)
    before_failed_load = torch.get_rng_state().clone()
    with pytest.raises(ValueError, match="CUDA RNG states without initialization"):
        restored.load_model(rng_path)
    torch.testing.assert_close(torch.get_rng_state(), before_failed_load)


def test_manifold_legacy_warm_start_is_explicit_weights_only_and_fail_closed(tmp_path):
    source = _checkpoint_manifold_agent(populate=True)
    legacy = {
        'policy_state_dict': source.policy.state_dict(),
        'optimizer_state_dict': source.policy_optimizer.state_dict(),
        'config': {'historical': True},
        'global_step': 99,
        'training_info': {'policy_loss': [123.0]},
    }
    legacy_path = tmp_path / 'manifold-legacy.pt'
    torch.save(legacy, legacy_path)

    target = _checkpoint_manifold_agent(populate=True)
    target._collection_tokens['token'] = {'unused': True}
    target._collection_frontiers[8] = 'token'
    with torch.no_grad():
        for parameter in target.policy.parameters():
            parameter.zero_()
    target.load_warm_start(legacy_path)
    for name, tensor in source.policy.state_dict().items():
        torch.testing.assert_close(target.policy.state_dict()[name], tensor)
    assert len(target.replay_buffer) == 0
    assert not target.replay_buffer.has_pending_trajectories
    assert not target.current_goals
    assert not target._collection_tokens
    assert target.global_step == 0
    assert not target.policy_optimizer.state
    assert target.goal_generator.current_difficulty == 0.0
    reset_rng = target.replay_buffer.get_rng_state()
    assert reset_rng['relabel'] == random.Random(2701).getstate()
    assert reset_rng['sample'] == random.Random(2702).getstate()

    with pytest.raises(ValueError, match="missing strict state"):
        target.load_model(legacy_path)
    partial = {'policy_state_dict': legacy['policy_state_dict']}
    mixed = {**legacy, 'frontier_state': {}}
    wrong = dict(legacy)
    wrong['policy_state_dict'] = {'bad': torch.zeros(1)}
    for name, payload in {'partial': partial, 'mixed': mixed, 'wrong': wrong}.items():
        path = tmp_path / f'manifold-legacy-{name}.pt'
        torch.save(payload, path)
        with pytest.raises(ValueError, match="legacy manifold"):
            target.load_warm_start(path)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
def test_manifold_strict_checkpoint_restores_cuda_distribution_rng(tmp_path):
    cpu_source = _checkpoint_manifold_agent(populate=False)
    cpu_path = tmp_path / 'manifold-cpu-for-cuda.pt'
    cpu_source.save_model(cpu_path)

    source = _checkpoint_manifold_agent(populate=False)
    source.device = torch.device('cuda')
    source.policy = source.policy.cuda()
    path = tmp_path / 'manifold-cuda.pt'
    source.save_model(path)
    expected_goal = source.goal_generator.sample_goals(1, source.device)[0][0]
    expected_action = source.policy(
        torch.zeros((1, 3), device='cuda'), expected_goal.unsqueeze(0)
    )[0]

    restored = _checkpoint_manifold_agent(populate=False)
    restored.device = torch.device('cuda')
    restored.policy = restored.policy.cuda()
    with pytest.raises(ValueError, match="policy parameter device"):
        restored.load_model(cpu_path)
    restored.load_model(path)
    actual_goal = restored.goal_generator.sample_goals(1, restored.device)[0][0]
    actual_action = restored.policy(
        torch.zeros((1, 3), device='cuda'), actual_goal.unsqueeze(0)
    )[0]
    torch.testing.assert_close(actual_goal, expected_goal)
    torch.testing.assert_close(actual_action, expected_action)

    malformed = torch.load(path, map_location='cpu', weights_only=False)
    malformed['torch_sampling_rng_state']['cuda_device_count'] += 1
    malformed_path = tmp_path / 'manifold-cuda-mismatch.pt'
    torch.save(malformed, malformed_path)
    with pytest.raises(ValueError, match="device-count/state mismatch"):
        restored.load_model(malformed_path)

    if torch.cuda.device_count() >= 2:
        different_index = _checkpoint_manifold_agent(populate=False)
        different_index.device = torch.device('cuda:1')
        different_index.policy = different_index.policy.to('cuda:1')
        with pytest.raises(ValueError, match="policy parameter device"):
            different_index.load_model(path)


class _DtypeCheckingVAE(torch.nn.Module):
    def __init__(self, device, dtype):
        super().__init__()
        self.anchor = torch.nn.Parameter(torch.ones(1, device=device, dtype=dtype))

    def encode(self, value):
        assert value.device == self.anchor.device
        assert value.dtype == self.anchor.dtype
        return value, torch.zeros_like(value)


def test_manifold_distance_reward_uses_vae_parameter_dtype_and_device():
    vae = _DtypeCheckingVAE(torch.device("cpu"), torch.float64)
    reward = ManifoldDistanceReward(vae)(np.array([0.0]), np.array([1.0]))
    assert reward == -1.0


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
def test_manifold_distance_reward_uses_cuda_vae_device():
    vae = _DtypeCheckingVAE(torch.device("cuda"), torch.float32)
    reward = ManifoldDistanceReward(vae)(np.array([0.0]), np.array([1.0]))
    assert reward == -1.0
