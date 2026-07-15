"""R38 constant-code recurrent MAPPO access gate for the CTS benchmark."""

from __future__ import annotations

from ha_ctse_process.config_alice_bob_sparse_mappo import Config as SparseMAPPOConfig


class Config(SparseMAPPOConfig):
    algorithm = "r38_cts_constant_code_recurrent_mappo"
    scenario = "cooperative_two_timescale_sparse"
    scenario_label = "cooperative_two_timescale_sparse"

    n_agents = 2
    n_uavs = 2
    max_observed_uavs = 2
    state_dim = 10
    obs_dim = 10
    action_dim = 2
    episode_length = 200
    max_steps = 200

    r38_world_size = 6.0
    r38_action_scale = 0.5
    r38_zone_radius = 0.75
    r38_anchor_required_steps = 40
    r38_shuttle_stages = 4

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
    low_value_loss_coef = 1.0
    low_entropy_coef = 0.01
    low_max_grad_norm = 0.5
    low_rnn_hidden_size = 64
    low_sequence_length = 20
    low_sequence_batch_size = 64
    low_ppo_epochs = 5
    ppo_epochs = 5
    use_recurrent_low_level = True
    use_centralized_low_value = True
    use_low_value_norm = True
