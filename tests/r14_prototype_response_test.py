import torch

from ha_ctse_process.prototype_response_discriminator import PrototypeResponseDiscriminator
from ha_ctse_process.standalone_agent import InteractionCompactEncoder, SkillDurationPolicy


def test_interaction_compact_encoder_returns_agent_relevance_and_updates_ema():
    encoder = InteractionCompactEncoder(
        state_dim=5,
        obs_dim=3,
        n_agents=4,
        hidden_dim=8,
        compact_dim=6,
        num_prototypes=3,
        use_sparsemax=True,
    )
    state = torch.randn(2, 5)
    joint_obs = torch.randn(2, 4, 3)

    compact, cd_loss, cmi_loss, weights, entropy, agent_relevance = encoder(state, joint_obs)

    assert compact.shape == (2, 6)
    assert weights.shape == (2, 3)
    assert agent_relevance.shape == (2, 4, 3)
    torch.testing.assert_close(agent_relevance.sum(dim=-1), torch.ones(2, 4))
    assert cd_loss.ndim == 0
    assert cmi_loss.ndim == 0
    assert entropy.shape == (2,)

    before = encoder.prototype_bank_ema.detach().clone()
    with torch.no_grad():
        encoder.prototypes.add_(0.1)
    encoder.update_prototype_bank_ema(tau=0.5)
    assert not torch.allclose(before, encoder.prototype_bank_ema)
    assert float(encoder.prototype_bank_drift_cos()) <= 1.0


def test_skill_duration_policy_accepts_optional_omega_and_relevance():
    policy = SkillDurationPolicy(
        obs_dim=3,
        n_skills=4,
        n_durations=2,
        hidden_dim=8,
        compact_dim=5,
        team_code_dim=6,
        omega_dim=3,
        agent_relevance_dim=3,
    )
    batch = 7
    obs = torch.randn(batch, 3)
    prev = torch.zeros(batch, dtype=torch.long)
    ages = torch.zeros(batch)
    compact = torch.randn(batch, 5)
    team = torch.randn(batch, 6)
    omega = torch.softmax(torch.randn(batch, 3), dim=-1)
    relevance = torch.softmax(torch.randn(batch, 3), dim=-1)

    skill_logits, duration_logits, values = policy.logits(
        obs,
        prev,
        ages,
        compact,
        team,
        omega=omega,
        agent_relevance=relevance,
    )
    assert skill_logits.shape == (batch, 4)
    assert duration_logits.shape == (batch, 2)
    assert values.shape == (batch,)

    # Missing optional tensors should be treated as explicit zero features.
    skill_logits_zero, duration_logits_zero, values_zero = policy.logits(obs, prev, ages, compact, team)
    assert skill_logits_zero.shape == skill_logits.shape
    assert duration_logits_zero.shape == duration_logits.shape
    assert values_zero.shape == values.shape


def test_prototype_response_prior_is_condition_only():
    module = PrototypeResponseDiscriminator(
        obs_dim=4,
        n_skills=3,
        condition_dim=2,
        hidden_dim=8,
    )
    condition = torch.randn(5, 2)
    obs_a = torch.randn(5, 4)
    obs_b = torch.randn(5, 4) + 10.0
    labels = torch.tensor([0, 1, 2, 1, 0])

    q_a, prior_a = module(obs_a, condition)
    q_b, prior_b = module(obs_b, condition)
    assert q_a.shape == (5, 3)
    assert prior_a.shape == (5, 3)
    assert not torch.allclose(q_a, q_b)
    torch.testing.assert_close(prior_a, prior_b)

    loss, metrics = module.loss_and_metrics(obs_a, condition, labels)
    assert loss.ndim == 0
    assert metrics["proto_disc_samples"] == 5.0
    reward = module.residual_reward(obs_a, condition, labels, clip=0.1)
    assert reward.shape == (5,)
    assert torch.max(torch.abs(reward)) <= 0.100001
