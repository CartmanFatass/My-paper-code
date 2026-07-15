"""Lightweight R39 native-categorical two-timescale mechanism gate."""

from __future__ import annotations

from ha_ctse_process.config import Config as ProcessConfig


class Config(ProcessConfig):
    algorithm = "r39_toy_native_categorical"
    scenario = "two_timescale_role_free_actions"
    scenario_label = scenario

    n_agents = 2
    n_uavs = 2
    max_observed_uavs = 2
    state_dim = 6
    obs_dim = 4
    action_dim = 2
    episode_length = 40
    max_steps = 40
    skill_interval = 5
    k = 5
    r39_toy_k0 = 5
    r39_toy_slow_period_blocks = 4

    n_Z = 1
    n_z = 4
    num_team_codes = 1
    legacy_n_skills_override = 4
    opt_num_prototypes = 4

    # Stage-0 mechanism model: intentionally much smaller than S7/HMASD.
    network_scale_profile = "r39_toy_32"
    hidden_size = 32
    embedding_dim = 32
    gru_hidden_size = 32
    opt_compact_dim = 16
    team_code_dim = 16
    process_encoder_embedding_dim = 8
    low_rnn_hidden_size = 32
    low_level_architecture = "feedforward"
    use_recurrent_low_level = False
    use_centralized_low_value = False
    use_low_value_norm = False
    low_sequence_length = 5
    low_sequence_batch_size = 64
    low_ppo_epochs = 3
    ppo_epochs = 3
    lr_coordinator = 3e-4
    lr_discoverer_actor = 3e-4
    lr_discoverer_critic = 3e-4

    high_controller = "r30_fixed_clock_ar_edit"
    r39_native_categorical_edit = True
    r30_force_refresh_every_check = False
    r30_keep_init = 0.6  # Ignored by the native single-categorical policy.
    r30_high_buffer_version = 1
    r30_high_gae_lambda = 0.95
    team_bridge_type = "deterministic"
    enable_team_intent = False
    low_actor_condition_on_team_code = False
    use_compact_return_head = False
    edit_penalty_alpha = 0.0
    switch_penalty_beta = 0.0
    high_keep_entropy_coef = 0.0
    duration_entropy_floor_enabled = False
    z_entropy_floor_enabled = False

    # The gate uses only the dense external task reward.  Every intrinsic,
    # posterior, topology, and benchmark-specific auxiliary path is disabled.
    opt_cd_coef = 0.0
    opt_cmi_coef = 0.0
    enable_prototype_disc_probe = False
    enable_prototype_disc_reward = False
    enable_team_disc_probe = False
    enable_team_disc_reward = False
    enable_assignment_actionability_probe = False
    enable_assignment_actionability_reward = False
    enable_team_effect_target_audit = False
    enable_team_conditioned_qd_probe = False
    r29_action_info_mode = "off"
    r31_effect_mode = "off"

    process_reward_injection = "none"
    process_reward_coef = 0.0
    process_contrast_coef = 0.0
    process_outcome_coef = 0.0
    process_prior_coef = 0.0
    process_shortcut_coef = 0.0
    context_shortcut_coef = 0.0
    process_shortcut_margin_coef = 0.0
    use_process_posterior_mi = False
    use_residual_process_posterior = False
    use_transition_skill_discriminator = False
    transition_skill_reward_coef = 0.0
    use_outcome_residual_probe = False
    outcome_residual_injection = "none"
    outcome_residual_reward_coef = 0.0
    use_topology_role_probe = False
    topology_role_injection = "none"
    topology_role_reward_coef = 0.0
    use_topology_potential_shaping = False
    topology_potential_injection = "none"
    topology_potential_coef = 0.0
    skill_effect_discovery_on = False
    skill_effect_reward_on = False
    skill_effect_reward_injection = "none"
    skill_force_probe_on = False
    enable_skill_forcing_reward = False
    skill_force_reward_injection = "none"
    enable_situation_diagnostics = False
    enable_situation_hazard_control = False
    enable_team_transition_probe = False
    enable_team_transition_reward = False
    use_g_intervention_kl_diagnostic = False
    use_g_info_diagnostic = False
    enable_g_info_objective = False
    intrinsic_segment_gate_enabled = False
    alice_bob_semantic_reward_enabled = False
    p2_recovery_credit_compute_on = False
    p2_recovery_credit_reward_on = False
    exact_cf_compute_on = False
    exact_cf_reward_on = False
    aem_joint_novelty_enabled = False

