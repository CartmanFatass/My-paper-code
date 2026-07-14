"""Small R30 configuration for the asymmetric-cycle Alice--Bob surrogate."""

from __future__ import annotations

from ha_ctse_process.config import Config as ProcessConfig


class Config(ProcessConfig):
    scenario_label = "alice_bob_asymmetric_cycles"
    r30_force_refresh_every_check = False

    n_agents = 2
    n_uavs = 2
    max_observed_uavs = 2
    state_dim = 14
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
    alice_bob_progress_reward_coef = 0.20
    alice_bob_state_holder_slice = (4, 6)
    alice_bob_state_long_phase_index = 11

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

    # Preserve HMASD's pressure for behaviorally distinguishable individual
    # skills.  The context residual prevents agent identity and clock phase from
    # being sufficient shortcuts; this reward affects only the low policy.
    alice_bob_semantic_reward_enabled = True
    use_transition_skill_discriminator = True
    transition_skill_condition_on_team = False
    transition_skill_reward_coef = 0.02
    transition_skill_reward_warmup_steps = 0
    transition_skill_reward_clip = 0.05
    transition_skill_max_samples = 4096

    process_reward_injection = "none"
    outcome_residual_injection = "none"
    topology_role_injection = "none"
    topology_potential_injection = "none"
    skill_effect_reward_injection = "none"
    skill_force_reward_injection = "none"
