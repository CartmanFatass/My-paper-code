"""R40 public fixed-N cooperative-access gate on MPE simple_spread."""

from __future__ import annotations

from ha_ctse_process.config_r38_two_timescale_sparse import Config as R38Config


class Config(R38Config):
    algorithm = "r40_simple_spread_constant_code_recurrent_mappo"
    scenario = "simple_spread"
    scenario_label = "pettingzoo_simple_spread_v3_r40"

    n_agents = 3
    n_uavs = 3
    max_observed_uavs = 3
    state_dim = 54
    obs_dim = 18
    action_dim = 5
    action_space_type = "discrete"
    episode_length = 25
    max_steps = 25

    simple_spread_version = "1.24.3"
    simple_spread_local_ratio = 0.0
    simple_spread_continuous_actions = False

    n_skills = 1
    num_team_codes = 1
    skill_interval = 25
    skill_lifetime_candidates = (25,)

    constant_skill_no_high = True
    alice_bob_semantic_reward_enabled = False
    aem_joint_novelty_enabled = False
    r31_effect_mode = "off"
    transition_skill_reward_coef = 0.0
    process_reward_injection = "none"
    outcome_residual_injection = "none"
    topology_role_injection = "none"
    topology_potential_injection = "none"
    skill_effect_reward_injection = "none"
    skill_force_reward_injection = "none"

    lr_discoverer_actor = 3e-4
    lr_discoverer_critic = 3e-4
    gamma = 0.99
    low_gae_lambda = 0.95
    low_clip_epsilon = 0.2
    low_value_clip = 0.2
    low_value_loss_coef = 0.5
    low_entropy_coef = 0.01
    low_max_grad_norm = 0.5
    low_rnn_hidden_size = 64
    low_sequence_length = 25
    low_sequence_batch_size = 64
    low_ppo_epochs = 5
    ppo_epochs = 5
    use_recurrent_low_level = True
    use_centralized_low_value = True
    use_low_value_norm = True
