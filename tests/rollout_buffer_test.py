import numpy as np
import torch

from hmasd.utils import RolloutBuffer


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
