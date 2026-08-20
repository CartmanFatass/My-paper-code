import numpy as np
import pytest
import torch

from hmasd.utils import ReplayBuffer, RolloutBuffer, compute_ordered_trajectory_gae


def make_buffer():
    return RolloutBuffer(
        num_steps=3,
        num_envs=1,
        n_agents=2,
        obs_dim=3,
        action_dim=2,
        gru_hidden_size=4,
        n_Z=2,
        n_z=3,
        state_dim=5,
        action_space_type="continuous",
    )


def add_step(buffer, t, reward):
    return buffer.add(
        t=t,
        env_idx=0,
        state=np.full(5, t, dtype=np.float32),
        obs=np.full((2, 3), t + 1, dtype=np.float32),
        action=np.full((2, 2), 0.1 * (t + 1), dtype=np.float32),
        reward=np.full(2, reward, dtype=np.float32),
        done=np.zeros(2, dtype=bool),
        value=np.zeros(2, dtype=np.float32),
        log_prob=np.full(2, -0.5, dtype=np.float32),
        gru_hidden_state=np.full((2, 4), t + 2, dtype=np.float32),
        critic_gru_hidden_state=torch.full((2, 4), float(t + 3)),
        team_skill=1,
        agent_skills=np.array([0, 2], dtype=np.int64),
        reward_env=np.full(2, reward, dtype=np.float32),
        reward_team_disc=np.full(2, 0.1, dtype=np.float32),
        reward_ind_disc=np.full(2, 0.2, dtype=np.float32),
    )


def test_rollout_buffer_array_storage_and_cache():
    buffer = make_buffer()
    assert add_step(buffer, 0, 1.0)
    assert add_step(buffer, 1, 2.0)
    assert buffer.add_high_level_data(
        env_idx=0,
        time_step=1,
        state_value=0.5,
        agent_values=np.array([0.6, 0.7], dtype=np.float32),
        team_log_prob=-0.1,
        agent_log_probs=np.array([-0.2, -0.3], dtype=np.float32),
        accumulated_reward=3.0,
    )

    data = buffer._get_full_rollout_data()
    assert data["num_actual_steps"] == 2
    assert data["masks"].shape == (2, 1)
    np.testing.assert_allclose(data["states"][1, 0], np.ones(5, dtype=np.float32))
    np.testing.assert_allclose(data["obs"][0, 0], np.ones((2, 3), dtype=np.float32))
    np.testing.assert_allclose(data["rewards"][:, 0, 0], [1.0, 2.0])
    np.testing.assert_allclose(data["critic_gru_hidden_states"][1, 0], np.full((2, 4), 4.0))
    assert data["high_level_valid_mask"][1, 0]
    assert data["high_level_rewards"][1, 0] == 3.0
    assert data["high_level_elapsed_steps"][1, 0] == 1
    assert not data["high_level_terminal"][1, 0]
    assert data["high_level_close_reason"][1, 0] == 0

    _ = buffer._get_full_rollout_data()
    profile = buffer.get_profile()
    assert profile["full_rollout_pack_calls"] == 1
    assert profile["full_rollout_cache_hits"] == 1


def test_rollout_buffer_advantages_are_unchanged_for_simple_case():
    buffer = make_buffer()
    assert add_step(buffer, 0, 1.0)
    assert add_step(buffer, 1, 2.0)
    assert buffer.add_high_level_data(0, 0, state_value=0.0, agent_values=[0.0, 0.0], accumulated_reward=1.0)
    assert buffer.add_high_level_data(0, 1, state_value=0.0, agent_values=[0.0, 0.0], accumulated_reward=2.0)

    buffer.compute_advantages(
        last_values=np.zeros((1, 2), dtype=np.float32),
        dones=np.zeros(1, dtype=bool),
        gamma=1.0,
        gae_lambda=1.0,
    )
    np.testing.assert_allclose(buffer.advantages[:2, 0, 0], [3.0, 2.0])
    np.testing.assert_allclose(buffer.returns[:2, 0, 1], [3.0, 2.0])

    buffer.compute_high_level_advantages(
        {"state": np.zeros(1, dtype=np.float32), "agents": np.zeros((1, 2), dtype=np.float32)},
        gamma=1.0,
        gae_lambda=1.0,
    )
    np.testing.assert_allclose(buffer.high_level_team_advantages[:2, 0], [3.0, 2.0])
    np.testing.assert_allclose(buffer.high_level_agent_returns[:2, 0, 0], [3.0, 2.0])


def test_rollout_buffer_gae_does_not_cross_current_transition_done():
    def advantages_with_final_reward(final_reward):
        buffer = make_buffer()
        assert add_step(buffer, 0, 1.0)
        assert add_step(buffer, 1, 1.0)
        assert add_step(buffer, 2, final_reward)
        buffer.dones[1, 0] = True
        buffer.compute_advantages(
            last_values=np.full((1, 2), 50.0, dtype=np.float32),
            dones=np.zeros(1, dtype=bool),
            gamma=1.0,
            gae_lambda=1.0,
        )
        return buffer.advantages[:3, 0, 0].copy()

    baseline = advantages_with_final_reward(100.0)
    changed_new_episode = advantages_with_final_reward(1000.0)
    np.testing.assert_allclose(baseline[:2], [2.0, 1.0])
    np.testing.assert_allclose(changed_new_episode[:2], baseline[:2])
    assert changed_new_episode[2] != baseline[2]


def test_ordered_trajectory_gae_uses_true_bootstraps_and_current_done():
    advantages, returns = compute_ordered_trajectory_gae(
        torch.tensor([1.0, 2.0]),
        torch.tensor([0.5, 0.6]),
        torch.tensor([0.6, 99.0]),
        torch.tensor([0.0, 1.0]),
        ["episode-a"] * 2,
        [7, 8],
        gamma=1.0,
        lam=1.0,
    )
    torch.testing.assert_close(advantages[:2], torch.tensor([2.5, 1.4]))
    torch.testing.assert_close(returns[:2], torch.tensor([3.0, 2.0]))


def test_ordered_trajectory_gae_fails_closed_for_mixed_or_gapped_rows():
    common = dict(
        rewards=torch.ones(2),
        values=torch.zeros(2),
        next_values=torch.zeros(2),
        dones=torch.zeros(2),
        gamma=0.99,
        lam=0.95,
    )
    with pytest.raises(ValueError, match="multiple trajectory"):
        compute_ordered_trajectory_gae(
            trajectory_ids=["a", "b"], timesteps=[0, 1], **common
        )
    with pytest.raises(ValueError, match="contiguous"):
        compute_ordered_trajectory_gae(
            trajectory_ids=["a", "a"], timesteps=[0, 2], **common
        )


def test_gnn_replay_tensor_sample_retains_each_rows_next_observation():
    replay = ReplayBuffer(4)
    for timestep, obs in enumerate((1.0, 2.0)):
        replay.push({
            'obs': np.array([obs]),
            'next_obs': np.array([obs * 11.0]),
            'action': np.array([0.1 * obs]),
            'reward': obs,
            'done': timestep == 1,
            'old_log_prob': -0.2,
            'role': timestep,
            'old_value': 0.5,
            'advantage': 10.0 + timestep,
            'return': 20.0 + timestep,
            'trajectory_id': 'trajectory-a',
            'timestep': timestep,
        })

    obs, next_obs, *_, advantages, returns = replay.sample_torch(2, torch.device("cpu"))
    observed_pairs = sorted(zip(obs[:, 0].tolist(), next_obs[:, 0].tolist()))
    assert observed_pairs == [(1.0, 11.0), (2.0, 22.0)]
    assert sorted(advantages.tolist()) == [10.0, 11.0]
    assert sorted(returns.tolist()) == [20.0, 21.0]


def test_gnn_replay_rejects_legacy_row_without_next_observation():
    replay = ReplayBuffer(1)
    replay.push((np.array([1.0]), np.array([0.1]), 1.0, False, -0.2, 0, 0.5))
    with pytest.raises(ValueError, match="trajectory-finalized"):
        replay.sample_torch(1, torch.device("cpu"))


def test_rollout_sampler_rng_state_round_trip_isolated_from_global_numpy_rng():
    first = make_buffer()
    second = make_buffer()
    state = first.get_sampler_rng_state()

    first_order = first._sampler_rng.permutation(20)
    np.random.seed(8675309)
    _ = np.random.permutation(200)
    second.set_sampler_rng_state(state)
    second_order = second._sampler_rng.permutation(20)

    np.testing.assert_array_equal(first_order, second_order)


def test_rollout_buffer_process_rewards_are_added_to_low_level_rewards():
    buffer = make_buffer()
    assert add_step(buffer, 0, 1.0)
    assert add_step(buffer, 1, 2.0)

    applied = buffer.add_process_rewards(
        env_idx=0,
        agent_idx=1,
        step_indices=np.array([0, 1]),
        rewards=np.array([0.25, -0.5], dtype=np.float32),
    )
    data = buffer._get_full_rollout_data()

    assert applied == 2
    np.testing.assert_allclose(data["reward_process"][:2, 0, 1], [0.25, -0.5])
    np.testing.assert_allclose(data["rewards"][:2, 0, 1], [1.25, 1.5])
    np.testing.assert_allclose(data["reward_env"][:2, 0, 1], [1.0, 2.0])


def test_high_level_advantages_use_variable_elapsed_step_discounts():
    buffer = make_buffer()
    assert add_step(buffer, 0, 0.0)
    assert add_step(buffer, 1, 0.0)
    assert buffer.add_high_level_data(
        0,
        0,
        state_value=0.0,
        agent_values=[0.0, 0.0],
        accumulated_reward=1.0,
        elapsed_steps=2,
        close_reason_code=1,
    )
    assert buffer.add_high_level_data(
        0,
        1,
        state_value=0.0,
        agent_values=[0.0, 0.0],
        accumulated_reward=2.0,
        elapsed_steps=1,
        close_reason_code=1,
    )

    data = buffer._get_full_rollout_data()
    np.testing.assert_array_equal(data["high_level_elapsed_steps"][:2, 0], [2, 1])
    np.testing.assert_array_equal(data["high_level_close_reason"][:2, 0], [1, 1])

    buffer.compute_high_level_advantages(
        {"state": np.zeros(1, dtype=np.float32), "agents": np.zeros((1, 2), dtype=np.float32)},
        gamma=0.5,
        gae_lambda=1.0,
    )
    np.testing.assert_allclose(buffer.high_level_team_advantages[:2, 0], [1.5, 2.0], rtol=1e-6)
    np.testing.assert_allclose(buffer.high_level_agent_returns[:2, 0, 0], [1.5, 2.0], rtol=1e-6)
