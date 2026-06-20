import torch
import pytest
from torch.distributions import Categorical

from config_test import Config
from hmasd.networks import SkillCoordinator, SkillDiscoverer


def make_small_config():
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
    config.action_space_type = "discrete"
    config.use_valuenorm = False
    config.use_obsnorm = False
    config.use_statenorm = False
    config.update_env_dims(state_dim=5, obs_dim=4, n_agents=2)
    return config


def test_coordinator_training_batch_matches_old_eval_path():
    config = make_small_config()
    coordinator = SkillCoordinator(config)
    coordinator.eval()

    states = torch.randn(4, config.state_dim)
    observations = torch.randn(4, config.n_agents, config.obs_dim)
    team_skills = torch.tensor([0, 1, 2, 1], dtype=torch.long)
    agent_skills = torch.tensor([[0, 1], [1, 2], [2, 0], [1, 1]], dtype=torch.long)

    torch.manual_seed(123)
    _, _, z_logits, agent_logits, _, _ = coordinator(states, observations)
    expected_team_log_probs = Categorical(logits=z_logits).log_prob(team_skills)
    expected_team_entropy = Categorical(logits=z_logits).entropy()
    expected_agent_log_probs = []
    expected_agent_entropies = []
    for agent_idx, logits in enumerate(agent_logits):
        dist = Categorical(logits=logits)
        expected_agent_log_probs.append(dist.log_prob(agent_skills[:, agent_idx]))
        expected_agent_entropies.append(dist.entropy())
    expected_agent_log_probs = torch.stack(expected_agent_log_probs, dim=1)
    expected_agent_entropies = torch.stack(expected_agent_entropies, dim=1)
    expected_state_values, expected_agent_values, _ = coordinator.get_value(states, observations)
    expected_agent_values = torch.stack(expected_agent_values, dim=1).squeeze(-1)

    torch.manual_seed(123)
    actual = coordinator.evaluate_training_batch(states, observations, team_skills, agent_skills)

    torch.testing.assert_close(actual["team_log_probs"], expected_team_log_probs)
    torch.testing.assert_close(actual["team_entropy"], expected_team_entropy)
    torch.testing.assert_close(actual["agent_log_probs"], expected_agent_log_probs)
    torch.testing.assert_close(actual["agent_entropies"], expected_agent_entropies)
    torch.testing.assert_close(actual["state_values"], expected_state_values)
    torch.testing.assert_close(actual["agent_values"], expected_agent_values)


def test_coordinator_training_batch_backward_has_gradients():
    config = make_small_config()
    coordinator = SkillCoordinator(config)
    coordinator.train()

    states = torch.randn(3, config.state_dim)
    observations = torch.randn(3, config.n_agents, config.obs_dim)
    team_skills = torch.tensor([0, 1, 2], dtype=torch.long)
    agent_skills = torch.tensor([[0, 1], [1, 2], [2, 0]], dtype=torch.long)

    out = coordinator.evaluate_training_batch(states, observations, team_skills, agent_skills)
    loss = (
        -out["team_log_probs"].mean()
        - out["agent_log_probs"].mean()
        + out["state_values"].pow(2).mean()
        + out["agent_values"].pow(2).mean()
    )
    loss.backward()

    grads = [param.grad for param in coordinator.parameters() if param.grad is not None]
    assert grads
    assert any(torch.isfinite(grad).all() and grad.abs().sum() > 0 for grad in grads)


def test_coordinator_assign_and_value_batch_matches_legacy_deterministic_path():
    config = make_small_config()
    coordinator = SkillCoordinator(config)
    coordinator.eval()

    states = torch.randn(5, config.state_dim)
    observations = torch.randn(5, config.n_agents, config.obs_dim)

    with torch.no_grad():
        team_skills, agent_skills, z_logits, agent_logits, _, _ = coordinator(
            states,
            observations,
            deterministic=True,
        )
        state_values, agent_values_list, _ = coordinator.get_value(states, observations)
        expected_team_log_probs = Categorical(logits=z_logits).log_prob(team_skills)
        expected_agent_log_probs = torch.stack(
            [
                Categorical(logits=agent_logits[agent_idx]).log_prob(agent_skills[:, agent_idx])
                for agent_idx in range(config.n_agents)
            ],
            dim=1,
        )
        expected_agent_values = torch.stack(agent_values_list, dim=1).squeeze(-1)

        actual = coordinator.assign_and_value_batch(states, observations, deterministic=True)

    torch.testing.assert_close(actual["team_skills"], team_skills)
    torch.testing.assert_close(actual["agent_skills"], agent_skills)
    torch.testing.assert_close(actual["team_log_probs"], expected_team_log_probs)
    torch.testing.assert_close(actual["agent_log_probs"], expected_agent_log_probs)
    torch.testing.assert_close(actual["state_values"], state_values)
    torch.testing.assert_close(actual["agent_values"], expected_agent_values)


def test_discoverer_single_backward_updates_actor_and_critic():
    pytest.importorskip("gymnasium")

    config = make_small_config()
    discoverer = SkillDiscoverer(config, device=torch.device("cpu"))
    discoverer.train()

    actor_optimizer = torch.optim.Adam(discoverer.actor.parameters(), lr=1e-3)
    critic_optimizer = torch.optim.Adam(discoverer.critic.parameters(), lr=1e-3)

    time_steps = 2
    batch_size = 3
    observations = torch.randn(time_steps, batch_size, config.obs_dim)
    states = torch.randn(time_steps, batch_size, config.state_dim)
    actions = torch.randint(0, config.action_dim, (time_steps, batch_size, 1))
    agent_skills = torch.randint(0, config.n_z, (time_steps, batch_size))
    team_skills = torch.randint(0, config.n_Z, (time_steps, batch_size))
    masks = torch.ones(time_steps, batch_size)
    actor_hxs = torch.zeros(batch_size, config.gru_hidden_size)
    critic_hxs = torch.zeros(batch_size, config.gru_hidden_size)

    actor_before = [param.detach().clone() for param in discoverer.actor.parameters()]
    critic_before = [param.detach().clone() for param in discoverer.critic.parameters()]

    log_probs, entropy = discoverer.actor.evaluate_actions(
        observations, actor_hxs, actions, masks, agent_skills
    )
    values, _ = discoverer.critic(states, critic_hxs, masks, team_skills)
    actor_loss = -log_probs.mean() - 0.01 * entropy
    critic_loss = values.pow(2).mean()

    actor_optimizer.zero_grad()
    critic_optimizer.zero_grad()
    (actor_loss + critic_loss).backward()
    actor_optimizer.step()
    critic_optimizer.step()

    assert any(
        not torch.allclose(old, new)
        for old, new in zip(actor_before, discoverer.actor.parameters())
    )
    assert any(
        not torch.allclose(old, new)
        for old, new in zip(critic_before, discoverer.critic.parameters())
    )
