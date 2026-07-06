import numpy as np
import pytest
import torch

from ha_ctse_process.config import Config
from ha_ctse_process.standalone_agent import Segment, StandaloneProcessAgent
from ha_ctse_process.team_intent import TEAM_INTENT_METRIC_FIELDS, TeamIntentDiscriminator, label_entropy


def _make_agent(**overrides) -> StandaloneProcessAgent:
    cfg = Config()
    cfg.n_Z = 4
    cfg.n_z = 4
    cfg.legacy_n_skills_override = 4
    cfg.skill_lifetime_candidates = (2, 4)
    cfg.hidden_size = 16
    cfg.embedding_dim = 16
    cfg.opt_compact_dim = 8
    cfg.opt_num_prototypes = 3
    cfg.team_code_dim = 8
    cfg.num_team_codes = 4
    cfg.low_rnn_hidden_size = 16
    cfg.low_ppo_epochs = 1
    cfg.high_ppo_epochs = 1
    cfg.use_prototype_response_skills = False
    cfg.use_autoregressive_selection = True
    cfg.parallel_selection = True
    cfg.ar_prefix_mode = "same_check"
    cfg.enable_team_intent = True
    cfg.team_intent_k = 2
    cfg.enable_team_disc_probe = False
    cfg.enable_team_disc_reward = False
    cfg.use_transition_skill_discriminator = False
    cfg.use_process_posterior_mi = False
    cfg.use_outcome_residual_probe = False
    cfg.use_topology_role_probe = False
    cfg.skill_effect_discovery_on = False
    cfg.enable_team_transition_probe = False
    for name, value in overrides.items():
        setattr(cfg, name, value)

    return StandaloneProcessAgent(
        obs_dim=5,
        action_dim=2,
        n_agents=3,
        config=cfg,
        device="cpu",
        action_space_type="continuous",
        num_envs=1,
        state_dim=12,
    )


def test_team_intent_forces_ar_roster_even_without_prototype_response():
    agent = _make_agent()

    assert agent.enable_team_intent
    assert agent.use_autoregressive_selection
    assert not agent.parallel_selection
    assert agent.ar_prefix_mode == "roster"


def test_team_intent_metric_schema_contains_r22_gate_fields():
    required = {
        "z_decisions_per_update",
        "z_advantage_mean",
        "z_advantage_std",
        "z_advantage_var",
        "combined_intrinsic_env_ratio",
        "combined_intrinsic_env_ratio_over05_count",
        "combined_intrinsic_env_ratio_guard_active",
        "combined_intrinsic_env_ratio_kill_triggered",
    }

    assert required.issubset(set(TEAM_INTENT_METRIC_FIELDS))


def test_team_intent_rejects_bridge_none_and_disables_low_actor_team_code():
    agent = _make_agent(low_actor_condition_on_team_code=True)

    assert not agent.low_actor_condition_on_team_code

    with pytest.raises(ValueError, match="team_bridge_type='none'"):
        _make_agent(team_bridge_type="none")


def test_team_intent_boundary_renews_all_agents_and_charges_z_logp_once():
    torch.manual_seed(0)
    agent = _make_agent()
    obs = np.zeros((agent.n_agents, agent.obs_dim), dtype=np.float32)
    state = np.zeros(agent.state_dim, dtype=np.float32)

    agent.maybe_assign_skills(obs, state=state, step=0, k=10, env_id=0, deterministic=True)

    assert agent.has_active_skill[0].all()
    assert int(agent.team_intent_remaining[0]) == agent.team_intent_k * 10 - 1
    weights = [agent.segments.active[0][i].team_logp_weight for i in range(agent.n_agents)]
    assert np.allclose(weights, np.full(agent.n_agents, 1.0 / agent.n_agents))
    assert all(agent.segments.active[0][i].team_intent_boundary for i in range(agent.n_agents))
    assert all(agent.segments.active[0][i].renewal_penalty == 0.0 for i in range(agent.n_agents))

    agent.duration_remaining[0, :] = 100
    agent.team_intent_remaining[0] = 0
    agent.team_intent_age[0] = 20
    agent.maybe_assign_skills(obs, state=state, step=1, k=10, env_id=0, deterministic=True)

    assert agent._team_intent_boundary_trunc_fracs[-1] == 1.0
    assert all(agent.segments.active[0][i].team_intent_truncated for i in range(agent.n_agents))
    assert all(agent.segments.active[0][i].team_intent_boundary for i in range(agent.n_agents))


def test_async_renewal_docks_to_held_z_without_recharging_z_logp():
    torch.manual_seed(0)
    agent = _make_agent()
    obs = np.zeros((agent.n_agents, agent.obs_dim), dtype=np.float32)
    state = np.zeros(agent.state_dim, dtype=np.float32)

    agent.maybe_assign_skills(obs, state=state, step=0, k=10, env_id=0, deterministic=True)
    held_z = int(agent.active_team_codes[0])
    agent.duration_remaining[0, :] = 10
    agent.duration_remaining[0, 1] = 0
    agent.team_intent_remaining[0] = 9
    agent.maybe_assign_skills(obs, state=state, step=1, k=10, env_id=0, deterministic=True)

    assert int(agent.active_team_codes[0]) == held_z
    renewed = agent.segments.active[0][1]
    assert renewed.team_code == held_z
    assert renewed.team_logp_weight == 0.0
    assert not renewed.team_intent_boundary


def test_team_intent_discriminator_reward_is_prior_corrected_and_detached():
    disc = TeamIntentDiscriminator(state_dim=6, num_team_codes=4, hidden_dim=8)
    states = torch.randn(5, 6)
    labels = torch.tensor([0, 1, 2, 3, 1])
    prior = torch.ones(4) / 4.0

    terms = disc.losses(states, labels, prior)
    assert terms["loss"].ndim == 0
    assert terms["residual"].shape == (5,)
    reward = disc.reward(states, labels, prior, coef=0.1, clip=2.0)
    assert reward.shape == (5,)
    entropy, max_frac = label_entropy(labels.numpy(), 4)
    assert entropy > 0.0
    assert 0.0 < max_frac <= 1.0


def test_team_intent_conditions_prototype_discriminator_on_team_codes():
    agent = _make_agent(enable_prototype_disc_probe=True)
    segment = Segment(
        env_id=0,
        agent_id=1,
        skill=2,
        duration_idx=0,
        start_step=0,
        high_obs=np.zeros(agent.obs_dim, dtype=np.float32),
        high_logp=0.0,
        high_value=0.0,
        high_entropy=0.0,
        team_code=3,
        obs=[
            np.zeros(agent.obs_dim, dtype=np.float32),
            np.ones(agent.obs_dim, dtype=np.float32),
        ],
        rewards=[0.0, 0.0],
        rollout_indices=[0, 1],
        omega_start=np.zeros(agent.opt_num_prototypes, dtype=np.float32),
        agent_relevance_start=np.zeros(agent.opt_num_prototypes, dtype=np.float32),
    )

    batch = agent._prototype_discriminator_batch([segment])

    assert batch is not None
    assert "team_codes" in batch
    assert np.all(batch["team_codes"] == 3)
    condition = agent._prototype_disc_condition(batch, agent.device)
    assert condition.shape[-1] == agent.prototype_disc_condition_dim
