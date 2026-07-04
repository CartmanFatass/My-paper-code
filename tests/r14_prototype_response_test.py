import pytest
import torch

from ha_ctse_process.config import Config
from ha_ctse_process.g_info_objective import GInfoConfig, GInfoObjective
from ha_ctse_process.prototype_response_discriminator import PrototypeResponseDiscriminator
from ha_ctse_process.standalone_agent import (
    InteractionCompactEncoder,
    Segment,
    SkillDurationPolicy,
    StandaloneProcessAgent,
)


class _DummyTeamBridge(torch.nn.Module):
    bridge_type = "stochastic"

    def __init__(self, num_team_codes: int, team_code_dim: int):
        super().__init__()
        self.num_team_codes = int(num_team_codes)
        self.embedding = torch.nn.Embedding(self.num_team_codes, int(team_code_dim))

    def code_embedding(self, codes: torch.Tensor) -> torch.Tensor:
        return self.embedding(codes)


def _make_r15_prefix_probe_agent(ar_prefix_mode: str = "same_check") -> StandaloneProcessAgent:
    cfg = Config()
    cfg.n_Z = 6
    cfg.opt_num_prototypes = 4
    cfg.prototype_skill_extra_codes = 0
    cfg.skill_lifetime_candidates = (3, 7, 13, 24)

    cfg.hidden_size = 16
    cfg.embedding_dim = 16
    cfg.opt_compact_dim = 8
    cfg.team_code_dim = 8
    cfg.num_team_codes = 4
    cfg.low_rnn_hidden_size = 16
    cfg.low_ppo_epochs = 1
    cfg.high_ppo_epochs = 1

    cfg.use_prototype_response_skills = True
    cfg.use_autoregressive_selection = True
    cfg.parallel_selection = False
    cfg.ar_prefix_mode = ar_prefix_mode
    cfg.high_condition_on_omega = True
    cfg.use_agent_prototype_relevance = True
    cfg.use_per_agent_kappa = True

    cfg.enable_prototype_disc_probe = True
    cfg.enable_prototype_disc_reward = False
    cfg.use_process_posterior_mi = False
    cfg.use_outcome_residual_probe = False
    cfg.use_transition_skill_discriminator = False
    cfg.use_topology_role_probe = False
    cfg.skill_effect_discovery_on = False

    return StandaloneProcessAgent(
        obs_dim=5,
        action_dim=2,
        n_agents=6,
        config=cfg,
        device="cpu",
        action_space_type="continuous",
        num_envs=1,
        state_dim=9,
    )


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


def test_skill_duration_policy_ar_prefix_and_logp_parts():
    policy = SkillDurationPolicy(
        obs_dim=3,
        n_skills=4,
        n_durations=2,
        hidden_dim=8,
        compact_dim=5,
        team_code_dim=6,
        ar_prefix_dim=4,
    )
    batch = 3
    obs = torch.randn(batch, 3)
    prev = torch.zeros(batch, dtype=torch.long)
    ages = torch.zeros(batch)
    compact = torch.randn(batch, 5)
    team = torch.randn(batch, 6)
    prefix_a = torch.zeros(batch, 4)
    prefix_b = torch.zeros(batch, 4)
    prefix_b[:, 2] = 1.0

    logits_a, _duration_a, _value_a = policy.logits(obs, prev, ages, compact, team, ar_prefix=prefix_a)
    logits_b, _duration_b, _value_b = policy.logits(obs, prev, ages, compact, team, ar_prefix=prefix_b)
    assert logits_a.shape == (batch, 4)
    assert not torch.allclose(logits_a, logits_b)

    sample = policy.act_with_parts(
        obs,
        prev,
        ages,
        compact,
        team,
        ar_prefix=prefix_a,
        deterministic=True,
    )
    torch.testing.assert_close(sample.logp, sample.skill_logp + sample.duration_logp)
    torch.testing.assert_close(sample.entropy, sample.skill_entropy + sample.duration_entropy)

    eval_logp, eval_entropy, eval_value = policy.evaluate(
        obs,
        prev,
        ages,
        compact,
        team,
        sample.skills,
        sample.durations,
        ar_prefix=prefix_a,
    )
    torch.testing.assert_close(eval_logp, sample.logp)
    torch.testing.assert_close(eval_entropy, sample.entropy)
    assert eval_value.shape == sample.value.shape


def test_r15_agent_init_forced_prefix_changes_assignment_logits():
    torch.manual_seed(20260704)
    agent = _make_r15_prefix_probe_agent()
    assert agent.use_prototype_response_skills
    assert agent.use_autoregressive_selection
    assert not agent.parallel_selection
    assert agent.high.ar_prefix_dim == agent.n_skills

    batch = 5
    obs = torch.randn(batch, agent.obs_dim)
    prev = torch.zeros(batch, dtype=torch.long)
    ages = torch.zeros(batch)
    compact = torch.randn(batch, int(agent.bridge.compact_dim))
    team = torch.randn(batch, int(agent.bridge.team_code_dim))
    omega = torch.softmax(torch.randn(batch, agent.opt_num_prototypes), dim=-1)
    relevance = torch.softmax(torch.randn(batch, agent.opt_num_prototypes), dim=-1)

    prefix_zero = torch.zeros(batch, agent.n_skills)
    prefix_forced = prefix_zero.clone()
    prefix_forced[:, 0] = 1.0 / float(agent.n_agents)

    logits_none, _, _ = agent.high.logits(
        obs,
        prev,
        ages,
        compact,
        team,
        omega=omega,
        agent_relevance=relevance,
        ar_prefix=None,
    )
    logits_zero, _, _ = agent.high.logits(
        obs,
        prev,
        ages,
        compact,
        team,
        omega=omega,
        agent_relevance=relevance,
        ar_prefix=prefix_zero,
    )
    logits_forced, _, _ = agent.high.logits(
        obs,
        prev,
        ages,
        compact,
        team,
        omega=omega,
        agent_relevance=relevance,
        ar_prefix=prefix_forced,
    )

    torch.testing.assert_close(logits_none, logits_zero)
    delta = (logits_forced - logits_zero).detach().abs().max()
    kl = agent._categorical_kl(logits_forced, logits_zero).detach().mean()
    assert float(delta) > 1e-8
    assert float(kl) > 1e-10


def test_roster_prefix_includes_active_skills_and_ages():
    agent = _make_r15_prefix_probe_agent(ar_prefix_mode="roster")
    assert agent.ar_prefix_mode == "roster"
    assert agent.high.ar_prefix_dim == agent.n_skills * (1 + 2 * agent.n_agents)

    active_skills = torch.tensor([0, 1, 2, 3, 1, 0])
    skill_ages = torch.tensor([0, 5, 10, 20, 3, 1])
    active_mask = torch.tensor([True, True, True, True, True, True])
    prefix = agent._build_roster_ar_prefix(
        agent_id=2,
        active_skills=active_skills,
        skill_ages=skill_ages,
        active_mask=active_mask,
        processed_new_skills=[],
    )

    assert prefix.shape == (1, agent.n_skills * (1 + 2 * agent.n_agents))
    counts = prefix[0, : agent.n_skills]
    skill_slots = prefix[0, agent.n_skills : agent.n_skills + agent.n_agents * agent.n_skills]
    age_slots = prefix[0, agent.n_skills + agent.n_agents * agent.n_skills :]
    torch.testing.assert_close(counts.sum(), torch.tensor(5.0 / 6.0))
    torch.testing.assert_close(counts[0], torch.tensor(2.0 / 6.0))
    torch.testing.assert_close(counts[1], torch.tensor(2.0 / 6.0))
    assert float(skill_slots[1 * agent.n_skills + 1]) > 0.0
    assert float(skill_slots[2 * agent.n_skills + 2]) == 0.0
    assert float(age_slots[1 * agent.n_skills + 1]) > float(age_slots[0 * agent.n_skills + 0])
    assert float(age_slots[2 * agent.n_skills + 2]) == 0.0


def test_roster_full_sync_prefix_reduces_to_same_check_ar():
    agent = _make_r15_prefix_probe_agent(ar_prefix_mode="roster")
    active_skills = torch.zeros(agent.n_agents, dtype=torch.long)
    skill_ages = torch.zeros(agent.n_agents, dtype=torch.long)
    active_mask = torch.zeros(agent.n_agents, dtype=torch.bool)

    prefix = agent._build_roster_ar_prefix(
        agent_id=2,
        active_skills=active_skills,
        skill_ages=skill_ages,
        active_mask=active_mask,
        processed_new_skills=[1, 3],
    )

    expected = torch.zeros(agent.n_skills * (1 + 2 * agent.n_agents))
    expected[1] = 1.0 / float(agent.n_agents)
    expected[3] = 1.0 / float(agent.n_agents)
    torch.testing.assert_close(prefix[0], expected)


def test_roster_snapshot_recomputes_skill_assignment_logp():
    torch.manual_seed(20260704)
    agent = _make_r15_prefix_probe_agent(ar_prefix_mode="roster")

    obs = torch.randn(1, agent.obs_dim)
    prev = torch.tensor([1])
    ages = torch.tensor([4.0])
    compact = torch.randn(1, int(agent.bridge.compact_dim))
    team = torch.randn(1, int(agent.bridge.team_code_dim))
    omega = torch.softmax(torch.randn(1, agent.opt_num_prototypes), dim=-1)
    relevance = torch.softmax(torch.randn(1, agent.opt_num_prototypes), dim=-1)
    active_skills = torch.tensor([0, 1, 2, 3, 1, 0])
    skill_ages = torch.tensor([0, 5, 10, 20, 3, 1])
    active_mask = torch.tensor([True, True, True, True, True, True])
    prefix = agent._build_roster_ar_prefix(
        agent_id=2,
        active_skills=active_skills,
        skill_ages=skill_ages,
        active_mask=active_mask,
        processed_new_skills=[3],
    )

    sample = agent.high.act_with_parts(
        obs,
        prev,
        ages,
        compact,
        team,
        omega=omega,
        agent_relevance=relevance,
        ar_prefix=prefix,
        deterministic=True,
    )
    segment = Segment(
        env_id=0,
        agent_id=2,
        skill=int(sample.skills.item()),
        duration_idx=int(sample.durations.item()),
        start_step=0,
        high_obs=obs[0].numpy(),
        high_logp=float(sample.logp.item()),
        high_value=float(sample.value.item()),
        high_entropy=float(sample.entropy.item()),
        prev_skill=int(prev.item()),
        skill_age_prev=int(ages.item()),
        skill_assignment_logp=float(sample.skill_logp.item()),
        duration_assignment_logp=float(sample.duration_logp.item()),
        ar_prefix_start=prefix[0].numpy(),
        roster_active_skills_start=active_skills.numpy(),
        roster_active_ages_start=skill_ages.numpy(),
        roster_active_mask_start=active_mask.numpy(),
    )

    rebuilt = agent._segment_ar_prefix_tensor([segment])
    logits, _duration_logits, _value = agent.high.logits(
        obs,
        prev,
        ages,
        compact,
        team,
        omega=omega,
        agent_relevance=relevance,
        ar_prefix=rebuilt,
    )
    logp = torch.log_softmax(logits, dim=-1)[0, int(segment.skill)]
    torch.testing.assert_close(logp, torch.tensor(segment.skill_assignment_logp), atol=1e-6, rtol=1e-6)


def test_selection_independence_deficit_is_matched_marginal_null():
    agent = _make_r15_prefix_probe_agent(ar_prefix_mode="roster")
    segments = []
    for idx, skill in enumerate([0, 1, 2, 3]):
        roster = torch.tensor([(skill + 1) % 4, (skill + 2) % 4, (skill + 3) % 4, skill, skill, skill])
        mask = torch.tensor([True, True, True, False, False, False])
        segments.append(
            Segment(
                env_id=0,
                agent_id=5,
                skill=skill,
                duration_idx=0,
                start_step=idx,
                high_obs=torch.zeros(agent.obs_dim).numpy(),
                high_logp=0.0,
                high_value=0.0,
                high_entropy=0.0,
                roster_active_skills_start=roster.numpy(),
                roster_active_ages_start=torch.ones(agent.n_agents).numpy(),
                roster_active_mask_start=mask.numpy(),
            )
        )

    metrics = agent._roster_selection_metrics(segments)
    assert metrics["selection_independence_available"] == 1.0
    assert metrics["selection_same_skill_rate"] == 0.0
    assert metrics["selection_independence_null_rate"] > 0.0
    assert metrics["selection_independence_deficit"] < 0.0


def test_prototype_response_uses_stored_assignment_null():
    module = PrototypeResponseDiscriminator(
        obs_dim=4,
        n_skills=3,
        condition_dim=2,
        hidden_dim=8,
        use_learned_prior=False,
    )
    condition = torch.randn(5, 2)
    obs = torch.randn(5, 4)
    labels = torch.tensor([0, 1, 2, 1, 0])
    null_logp = torch.tensor([-1.0, -0.5, -2.0, -0.25, -1.5])

    q_logits = module(obs, condition)
    q_logp = torch.log_softmax(q_logits, dim=-1).gather(1, labels.unsqueeze(1)).squeeze(1)
    expected_residual = q_logp - null_logp

    loss, metrics = module.loss_and_metrics(obs, condition, labels, null_logp=null_logp)
    assert loss.ndim == 0
    assert metrics["proto_disc_samples"] == 5.0
    assert metrics["proto_disc_prior_loss"] == 0.0
    assert metrics["proto_disc_prior_acc"] == 0.0
    assert metrics["proto_disc_null_logp_mean"] == float(null_logp.mean())
    assert abs(metrics["proto_disc_residual_mean"] - float(expected_residual.mean())) < 1e-6

    reward = module.residual_reward(obs, condition, labels, null_logp=null_logp, clip=0.1)
    assert reward.shape == (5,)
    assert torch.max(torch.abs(reward)) <= 0.100001


def test_prototype_response_requires_null_when_learned_prior_disabled():
    module = PrototypeResponseDiscriminator(
        obs_dim=4,
        n_skills=3,
        condition_dim=2,
        hidden_dim=8,
        use_learned_prior=False,
    )
    condition = torch.randn(5, 2)
    obs = torch.randn(5, 4)
    labels = torch.tensor([0, 1, 2, 1, 0])

    with pytest.raises(ValueError, match="null_logp is required"):
        module.loss_and_metrics(obs, condition, labels)
    with pytest.raises(ValueError, match="null_logp is required"):
        module.residual_reward(obs, condition, labels)
    with pytest.raises(RuntimeError, match="learned prior head is disabled"):
        module.forward_with_prior(obs, condition)


def test_prototype_response_learned_prior_is_fallback_only():
    module = PrototypeResponseDiscriminator(
        obs_dim=4,
        n_skills=3,
        condition_dim=2,
        hidden_dim=8,
        use_learned_prior=True,
        prior_coef=0.5,
    )
    condition = torch.randn(5, 2)
    obs_a = torch.randn(5, 4)
    obs_b = torch.randn(5, 4) + 10.0
    labels = torch.tensor([0, 1, 2, 1, 0])

    q_a, prior_a = module.forward_with_prior(obs_a, condition)
    q_b, prior_b = module.forward_with_prior(obs_b, condition)
    assert q_a.shape == (5, 3)
    assert prior_a.shape == (5, 3)
    assert not torch.allclose(q_a, q_b)
    torch.testing.assert_close(prior_a, prior_b)

    loss, metrics = module.loss_and_metrics(obs_a, condition, labels)
    assert loss.ndim == 0
    assert metrics["proto_disc_prior_loss"] > 0.0
    assert metrics["proto_disc_prior_acc"] >= 0.0


def test_prototype_batch_broadcasts_segment_assignment_null():
    class _BatchHarness:
        prototype_discriminator = object()
        opt_num_prototypes = 4
        transition_skill_max_samples = 8192
        obs_dim = 3

        _fit_vector = StandaloneProcessAgent._fit_vector

    segment = Segment(
        env_id=0,
        agent_id=1,
        skill=2,
        duration_idx=0,
        start_step=0,
        high_obs=torch.zeros(3).numpy(),
        high_logp=-1.7,
        high_value=0.0,
        high_entropy=0.0,
        skill_assignment_logp=-0.75,
        duration_assignment_logp=-0.25,
        ar_parallel_kl_start=0.125,
        omega_start=torch.tensor([0.2, 0.3, 0.1, 0.4]).numpy(),
        agent_relevance_start=torch.tensor([0.1, 0.2, 0.3, 0.4]).numpy(),
        kappa_start=3,
    )
    segment.append(
        obs=torch.tensor([1.0, 2.0, 3.0]).numpy(),
        action=torch.tensor([0.0]).numpy(),
        reward=0.1,
        next_obs=torch.tensor([2.0, 3.0, 4.0]).numpy(),
        rollout_idx=0,
    )
    segment.append(
        obs=torch.tensor([2.0, 3.0, 4.0]).numpy(),
        action=torch.tensor([1.0]).numpy(),
        reward=0.2,
        next_obs=torch.tensor([3.0, 4.0, 5.0]).numpy(),
        rollout_idx=1,
    )

    batch = StandaloneProcessAgent._prototype_discriminator_batch(_BatchHarness(), [segment])

    assert batch is not None
    assert batch["labels"].tolist() == [2, 2]
    assert batch["null_logp"].tolist() == [-0.75, -0.75]
    assert batch["ar_parallel_kl"].tolist() == [0.125, 0.125]
    assert batch["rollout_indices"].tolist() == [0, 1]


def test_g_info_objective_subsamples_optional_omega_and_relevance():
    batch = 11
    max_segments = 4
    n_codes = 3
    omega_dim = 4
    policy = SkillDurationPolicy(
        obs_dim=5,
        n_skills=6,
        n_durations=3,
        hidden_dim=16,
        compact_dim=7,
        team_code_dim=8,
        omega_dim=omega_dim,
        agent_relevance_dim=omega_dim,
    )
    bridge = _DummyTeamBridge(num_team_codes=n_codes, team_code_dim=8)
    objective = GInfoObjective(
        GInfoConfig(
            diagnostic_on=True,
            objective_on=False,
            max_segments=max_segments,
        )
    )

    loss, metrics = objective(
        high_policy=policy,
        bridge=bridge,
        high_obs=torch.randn(batch, 5),
        prev_skills=torch.zeros(batch, dtype=torch.long),
        ages=torch.zeros(batch),
        compact=torch.randn(batch, 7),
        omega=torch.softmax(torch.randn(batch, omega_dim), dim=-1),
        agent_relevance=torch.softmax(torch.randn(batch, omega_dim), dim=-1),
        total_steps=0,
    )

    assert loss.ndim == 0
    assert metrics["g_info_active"] == 1.0
    assert metrics["g_info_samples"] == float(max_segments)
