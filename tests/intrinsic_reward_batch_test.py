import numpy as np
import pytest
import torch

from config_test import Config
from hmasd.agent import HMASDAgent
from hmasd.utils import DiscriminatorBuffer


def make_agent(tmp_path, disable_rewards=False):
    config = Config()
    config.n_agents = 2
    config.n_uavs = 2
    config.n_Z = 3
    config.n_z = 3
    config.hidden_size = 16
    config.embedding_dim = 16
    config.n_heads = 4
    config.gru_hidden_size = 8
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
    config.disable_discriminator_rewards = disable_rewards
    config.disable_discriminator_training = False
    config.disable_high_level_training = False
    config.update_env_dims(state_dim=5, obs_dim=4, n_agents=2)
    return HMASDAgent(config, log_dir=str(tmp_path), device=torch.device("cpu"))


def test_batched_intrinsic_rewards_match_scalar_path(tmp_path):
    torch.manual_seed(7)
    agent_batch = make_agent(tmp_path / "batch")
    torch.manual_seed(7)
    agent_scalar = make_agent(tmp_path / "scalar")

    agent_scalar.team_discriminator.load_state_dict(agent_batch.team_discriminator.state_dict())
    agent_scalar.individual_discriminator.load_state_dict(agent_batch.individual_discriminator.state_dict())

    next_states = np.array(
        [[0.1, 0.2, 0.3, 0.4, 0.5], [0.5, 0.4, 0.3, 0.2, 0.1]],
        dtype=np.float32,
    )
    next_observations = np.array(
        [
            [[0.2, 0.1, 0.4, 0.3], [0.7, 0.6, 0.5, 0.4]],
            [[-0.1, 0.2, -0.3, 0.4], [0.9, -0.8, 0.7, -0.6]],
        ],
        dtype=np.float32,
    )
    rewards = np.array([1.0, -0.25], dtype=np.float32)
    team_skills = np.array([0, 2], dtype=np.int64)
    agent_skills = np.array([[1, 2], [0, 1]], dtype=np.int64)

    batch = agent_batch._compute_intrinsic_rewards_batch(
        next_states, rewards, next_observations, team_skills, agent_skills
    )

    scalar = {key: np.zeros((2, 2), dtype=np.float32) for key in ("intrinsic", "env", "team_disc", "ind_disc")}
    for env_idx in range(2):
        for agent_idx in range(2):
            values = agent_scalar._compute_intrinsic_reward(
                next_states[env_idx],
                rewards[env_idx],
                next_observations[env_idx, agent_idx],
                int(team_skills[env_idx]),
                int(agent_skills[env_idx, agent_idx]),
            )
            scalar["intrinsic"][env_idx, agent_idx] = values[0]
            scalar["env"][env_idx, agent_idx] = values[1]
            scalar["team_disc"][env_idx, agent_idx] = values[2]
            scalar["ind_disc"][env_idx, agent_idx] = values[3]

    for key in scalar:
        np.testing.assert_allclose(batch[key], scalar[key], rtol=1e-5, atol=1e-6)
    assert agent_batch.team_disc_baseline == pytest.approx(agent_scalar.team_disc_baseline)
    assert agent_batch.ind_disc_baseline == pytest.approx(agent_scalar.ind_disc_baseline)


def test_batched_intrinsic_rewards_disable_discriminator_rewards(tmp_path):
    agent = make_agent(tmp_path, disable_rewards=True)

    def fail_forward(*args, **kwargs):
        raise AssertionError("discriminator forward should not run")

    agent.team_discriminator.forward = fail_forward
    agent.individual_discriminator.forward = fail_forward

    rewards = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    result = agent._compute_intrinsic_rewards_batch(
        next_states=np.ones((2, 5), dtype=np.float32),
        rewards=rewards,
        next_observations=np.ones((2, 2, 4), dtype=np.float32),
        team_skills=np.array([0, 1], dtype=np.int64),
        agent_skills=np.array([[0, 1], [1, 2]], dtype=np.int64),
    )

    np.testing.assert_allclose(result["intrinsic"], rewards)
    np.testing.assert_allclose(result["env"], rewards)
    np.testing.assert_allclose(result["team_disc"], np.zeros_like(rewards))
    np.testing.assert_allclose(result["ind_disc"], np.zeros_like(rewards))


def test_discriminator_buffer_extend_keeps_schema():
    buffer = DiscriminatorBuffer(capacity=8)
    buffer.extend([
        {"type": "team", "state": np.zeros(5, dtype=np.float32), "skill": 1},
        {
            "type": "individual",
            "obs": np.ones(4, dtype=np.float32),
            "team_skill": 1,
            "skill": 2,
        },
    ])

    data = buffer.get_all()
    assert len(data) == 2
    assert data[0]["type"] == "team"
    assert data[0]["state"].shape == (5,)
    assert data[1]["type"] == "individual"
    assert data[1]["obs"].shape == (4,)
    assert buffer.get_stats()["total_added"] == 2


@pytest.mark.parametrize("mode", ["legacy", "fused"])
def test_discriminator_update_modes_update_parameters(tmp_path, mode):
    torch.manual_seed(11)
    agent = make_agent(tmp_path / mode)
    agent.config.discriminator_update_mode = mode
    agent.config.ppo_epochs = 1
    agent.config.discriminator_batch_size = 4

    experiences = []
    for i in range(4):
        experiences.append({
            "type": "team",
            "state": np.full(5, 0.1 * i, dtype=np.float32),
            "skill": i % agent.config.n_Z,
        })
        for agent_idx in range(agent.config.n_agents):
            experiences.append({
                "type": "individual",
                "obs": np.full(4, 0.2 * (i + agent_idx), dtype=np.float32),
                "team_skill": i % agent.config.n_Z,
                "skill": (i + agent_idx) % agent.config.n_z,
            })
    agent.discriminator_buffer.extend(experiences)

    before = [p.detach().clone() for p in agent.team_discriminator.parameters()]
    loss = agent.update_discriminators(num_steps=4, noise_std=0.0)

    assert np.isfinite(loss)
    assert len(agent.discriminator_buffer.get_all()) == len(experiences)
    assert any(
        not torch.allclose(old, new)
        for old, new in zip(before, agent.team_discriminator.parameters())
    )
