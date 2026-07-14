"""Small R30 configuration for the asymmetric-cycle Alice--Bob surrogate."""

from __future__ import annotations

from ha_ctse_process.config import Config as ProcessConfig


class Config(ProcessConfig):
    scenario_label = "alice_bob_asymmetric_cycles"
    r30_force_refresh_every_check = False

    n_agents = 2
    n_uavs = 2
    max_observed_uavs = 2
    state_dim = 19
    obs_dim = 12
    action_dim = 2
    episode_length = 80
    max_steps = 80

    # Four intended low-level meanings: left/right button and left/right target.
    n_Z = 2
    n_z = 4
    num_team_codes = 2
    legacy_n_skills_override = 4
    opt_num_prototypes = 4

    alice_bob_world_size = 8.0
    alice_bob_short_period = 10
    alice_bob_long_periods = 4
    alice_bob_num_short_periods = 8
    alice_bob_action_scale = 0.75
    alice_bob_contact_radius = 0.70
    alice_bob_state_long_phase_index = 9
    alice_bob_state_last_button_slice = (15, 17)
    alice_bob_state_last_target_slice = (17, 19)
    alice_bob_assignment_min_button_fraction = 0.30
    alice_bob_assignment_min_target_fraction = 0.10
    alice_bob_assignment_margin = 0.05

    # Keep the current algorithmic interfaces, but remove S7-sized capacity and
    # UAV-only diagnostics so this environment remains a fast iteration lane.
    network_scale_profile = "alice_bob_64"
    hidden_size = 64
    opt_compact_dim = 32
    team_code_dim = 32
    process_encoder_embedding_dim = 32
    low_rnn_hidden_size = 64
    low_sequence_length = 10
    low_sequence_batch_size = 64
    low_ppo_epochs = 5
    ppo_epochs = 5

    use_outcome_residual_probe = False
    use_topology_role_probe = False
    use_g_intervention_kl_diagnostic = False
    use_g_info_diagnostic = False
    enable_situation_diagnostics = False

    # The environment reward is sparse collection-only.  The legacy one-step
    # transition posterior remains available as a diagnostic but must not write
    # online reward in R31.
    alice_bob_semantic_reward_enabled = False
    use_transition_skill_discriminator = True
    transition_skill_condition_on_team = False
    transition_skill_reward_coef = 0.0
    transition_skill_reward_warmup_steps = 0
    transition_skill_reward_clip = 0.05
    transition_skill_max_samples = 4096

    # R31-CFEI has one fixed-window route and no coefficient sweep.  Reward use
    # remains fail-closed until the reward-off causal gate passes.
    r31_effect_mode = "off"  # off, probe_only, real_reward
    r31_effect_window = 10
    r31_effect_coef = 0.02
    r31_effect_clip = 0.05
    r31_effect_hidden_dim = 64
    r31_effect_schema_version = 1

    process_reward_injection = "none"
    outcome_residual_injection = "none"
    topology_role_injection = "none"
    topology_potential_injection = "none"
    skill_effect_reward_injection = "none"
    skill_force_reward_injection = "none"
