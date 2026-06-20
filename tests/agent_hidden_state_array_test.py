import numpy as np
import torch

from config_test import Config
from hmasd.agent import HMASDAgent


def make_agent(tmp_path):
    config = Config()
    config.n_agents = 2
    config.n_uavs = 2
    config.n_Z = 3
    config.n_z = 3
    config.hidden_size = 16
    config.embedding_dim = 16
    config.n_heads = 4
    config.n_encoder_layers = 1
    config.n_decoder_layers = 1
    config.gru_hidden_size = 16
    config.action_dim = 3
    config.num_envs = 2
    config.rollout_length = 4
    config.ppo_epochs = 1
    config.num_mini_batch = 1
    config.coordinator_batch_size = 2
    config.sequence_batch_size = 2
    config.discriminator_batch_size = 4
    config.discriminator_buffer_size = 32
    config.use_valuenorm = False
    config.use_obsnorm = False
    config.use_statenorm = False
    config.disable_discriminator_rewards = True
    config.disable_discriminator_training = True
    config.disable_high_level_training = True
    config.update_env_dims(state_dim=5, obs_dim=4, n_agents=2)
    return HMASDAgent(config, log_dir=str(tmp_path), device=torch.device("cpu"))


def test_batched_step_uses_array_hidden_states_for_rollout_inputs(tmp_path):
    torch.manual_seed(5)
    np.random.seed(5)
    agent = make_agent(tmp_path)

    states = np.array(
        [[0.1, 0.2, 0.3, 0.4, 0.5], [0.5, 0.4, 0.3, 0.2, 0.1]],
        dtype=np.float32,
    )
    observations = np.array(
        [
            [[0.2, 0.1, 0.4, 0.3], [0.7, 0.6, 0.5, 0.4]],
            [[-0.1, 0.2, -0.3, 0.4], [0.9, -0.8, 0.7, -0.6]],
        ],
        dtype=np.float32,
    )
    env_steps = np.zeros(2, dtype=np.int64)
    dones = np.zeros(2, dtype=bool)

    actions, infos, step_data = agent.step(
        states,
        observations,
        env_steps,
        dones,
        deterministic=True,
        return_step_data=True,
        build_infos=False,
    )
    assert infos is None
    assert agent.actor_hidden_np.shape[:2] == (2, 2)
    np.testing.assert_allclose(agent.prev_actor_hidden_np[:2], 0.0, atol=1e-7)
    first_actor_hidden = agent.actor_hidden_np[:2].copy()
    first_critic_hidden = agent.critic_hidden_np[:2].copy()

    next_states = states + 0.01
    next_observations = observations + 0.01
    rewards = np.array([1.0, 0.5], dtype=np.float32)
    agent.store_transition_batch(
        states,
        next_states,
        observations,
        next_observations,
        actions,
        rewards,
        dones,
        infos_batch=infos,
        rollout_step_idx=0,
        step_data=step_data,
    )
    np.testing.assert_allclose(agent.rollout_buffer.gru_hidden_states[0, :2], 0.0, atol=1e-7)
    np.testing.assert_allclose(agent.rollout_buffer.critic_gru_hidden_states[0, :2], 0.0, atol=1e-7)

    env_steps += 1
    actions, infos, step_data = agent.step(
        next_states,
        next_observations,
        env_steps,
        dones,
        deterministic=True,
        return_step_data=True,
        build_infos=False,
    )
    assert infos is None
    np.testing.assert_allclose(agent.prev_actor_hidden_np[:2], first_actor_hidden, rtol=1e-5, atol=1e-6)
    np.testing.assert_allclose(agent.prev_critic_hidden_np[:2], first_critic_hidden, rtol=1e-5, atol=1e-6)

    agent.store_transition_batch(
        next_states,
        next_states + 0.01,
        next_observations,
        next_observations + 0.01,
        actions,
        np.array([0.25, 0.75], dtype=np.float32),
        dones,
        infos_batch=infos,
        rollout_step_idx=1,
        step_data=step_data,
    )
    np.testing.assert_allclose(
        agent.rollout_buffer.gru_hidden_states[1, :2],
        first_actor_hidden,
        rtol=1e-5,
        atol=1e-6,
    )
    np.testing.assert_allclose(
        agent.rollout_buffer.critic_gru_hidden_states[1, :2],
        first_critic_hidden,
        rtol=1e-5,
        atol=1e-6,
    )
