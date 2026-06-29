"""Default configuration for the standalone HA-CTSE process-core algorithm.

This config intentionally lives with the standalone algorithm package so the
new algorithm is not confused with HMASD presets in ``config_1.py``.
"""

from __future__ import annotations

from config_1 import Config as EnvConfig


class Config(EnvConfig):
    """Scenario config plus standalone process-core algorithm defaults."""

    # The inherited EnvConfig still provides environment geometry, Scenario 7
    # presets, and reward settings.  Algorithm defaults below are owned by the
    # standalone process-core path.
    algorithm = "ha_ctse_process_standalone"
    policy_update_mode = "on_policy"
    allow_off_policy_policy_updates = False
    process_segment_replay_enabled = False

    # Skill and temporal process.
    # Match the Scenario-7 HMASD skill cardinality for fair comparisons.
    n_Z = 6
    n_z = 6
    # UAV service/relay formation is a long-horizon task.  These values are in
    # high-level intervals, so the primitive horizon is candidate * k.
    skill_lifetime_candidates = (3, 7, 13, 24)
    process_segment_mode = "skill_lifetime"
    allow_early_duration_termination = False

    # Compact interaction context c_tau.
    opt_compact_dim = 64
    opt_num_prototypes = 4
    opt_use_sparsemax = True
    opt_cd_coef = 0.02
    opt_cmi_coef = 0.005

    # Compact-conditioned team code g_tau.
    team_bridge_type = "stochastic"
    team_code_dim = 64
    num_team_codes = n_Z

    # PPO and entropy.
    high_entropy_coef = 0.01
    low_entropy_coef = 0.01
    clip_epsilon = 0.2
    low_clip_epsilon = 0.1
    gamma = 0.99

    # HMASD-style low-level discoverer capacity.  The actor remains skill-only
    # conditioned (`o_i, z_i`), while the critic receives centralized context for
    # cooperative credit assignment.
    network_scale_profile = "hmasd_s7_256"
    low_level_architecture = "strict_hmasd_mappo"  # strict_hmasd_mappo, gru_ctde, feedforward
    use_recurrent_low_level = True
    use_centralized_low_value = True
    use_low_value_norm = True
    low_rnn_hidden_size = 256
    low_sequence_length = 10
    low_sequence_batch_size = 32
    low_ppo_epochs = 15
    low_gae_lambda = 0.95
    low_value_clip = 10.0
    low_value_loss_coef = 1.0
    low_max_grad_norm = 0.5
    # Diagnostic-only bottleneck violation: allow the primitive actor to see g.
    # Default stays false because the intended HA-CTSE abstraction keeps g as a
    # high-level coordination latent and feeds it only to the centralized critic.
    low_actor_condition_on_team_code = False

    # Process encoder and process reward.
    process_encoder_embedding_dim = 64
    lr_process_encoder = 1e-4
    process_contrast_coef = 1.0
    process_outcome_coef = 0.25
    process_reward_mode = "mi_only"
    # Keep the task reward pure by default.  The process posterior is still
    # trained and logged, but its reward is injected only in explicit ablations.
    process_reward_injection = "none"
    process_reward_coef = 0.05
    process_reward_contrast_coef = 1.0
    process_reward_outcome_coef = 0.25
    process_reward_clip = 2.0
    normalize_process_outcomes = True
    use_process_reward_for_discoverer = True
    use_process_posterior_mi = True
    use_residual_process_posterior = True
    process_posterior_condition_on_team = True
    process_posterior_team_embed_dim = 0
    process_prior_coef = 0.25
    process_shortcut_coef = 0.5
    use_context_skill_shortcut = True
    context_shortcut_coef = 0.5
    process_shortcut_margin = 0.1
    process_shortcut_margin_coef = 0.5
    process_reward_warmup_steps = 160000
    intrinsic_phase_bins = 8

    # Dense HMASD-inspired semantic pressure.  This is not the legacy
    # discriminator: it predicts skill identity from primitive transitions
    # inside completed stochastic skill segments, giving the new process
    # algorithm many more semantic samples than one segment-level posterior
    # example per lifetime.
    use_transition_skill_discriminator = True
    transition_skill_condition_on_team = True
    transition_skill_coef = 0.5
    transition_skill_prior_coef = 0.25
    transition_context_shortcut_coef = 0.25
    transition_skill_reward_coef = 0.02
    transition_skill_reward_warmup_steps = 80000
    transition_skill_reward_clip = 0.05
    transition_skill_max_samples = 8192

    # Future cooperation outcome residual probe.  This is the next-step
    # replacement candidate for classifier-style intrinsic reward: first test
    # whether a realized segment improves prediction of future cooperation
    # outcomes over context/duration/reward shortcuts, then optionally inject
    # the residual as shaping in later ablations.
    use_outcome_residual_probe = True
    outcome_residual_horizon = 50
    outcome_residual_coef = 1.0
    outcome_residual_hidden_dim = 0
    normalize_outcome_residual_targets = True
    outcome_residual_injection = "none"  # none, low_only, high_only, high_and_low
    outcome_residual_reward_coef = 0.0
    outcome_residual_reward_clip = 0.05

    # OPT-conditioned topology role probe.  This is the HMASD-inspired
    # semantic bootstrap path for the standalone algorithm: topology
    # counterfactuals create role pseudo labels, and the full classifier must
    # beat OPT/context/duration/reward shortcuts before its residual is trusted.
    use_topology_role_probe = True
    topology_role_coef = 1.0
    topology_role_hidden_dim = 0
    topology_role_min_score = 1e-6
    topology_role_injection = "none"  # none, low_only, high_only, high_and_low
    topology_role_reward_coef = 0.0
    topology_role_reward_clip = 0.05

    # Topology-potential cooperative credit shaping.  This is the P1 credit
    # path: it uses bounded potential changes from reward_info, not learned role
    # labels.  Default off so reward-pure diagnostics remain clean.
    use_topology_potential_shaping = False
    topology_potential_injection = "none"  # none, low_only, high_only, high_and_low
    topology_potential_coef = 0.0
    topology_potential_clip = 0.05
    topology_potential_warmup_steps = 0
    # "delta" avoids an artificial penalty for maintaining a good relay state
    # through long UAV-service segments; "smdp" is available for strict PBRS.
    topology_potential_discount_mode = "delta"  # delta, one_step, smdp
    topology_potential_positive_only = False

    # Intrinsic reward composition.  Segment-level intrinsic is allowed to
    # shape the high-level SMDP policy only after the posterior demonstrably
    # beats trivial duration/length/reward shortcuts.
    intrinsic_segment_gate_enabled = True
    intrinsic_segment_gate_margin = 0.05
    intrinsic_segment_gate_min_segments = 64
    intrinsic_segment_gate_min_residual_mi = 0.0
    intrinsic_segment_gate_min_posterior_acc = 0.0
    intrinsic_reward_normalize = False
    semantic_shortcut_hard_stop_enabled = True
    semantic_shortcut_hard_stop_margin = 0.0
    semantic_shortcut_hard_stop_min_segments = 64
    semantic_shortcut_hard_stop_raise = False
    use_g_intervention_kl_diagnostic = True
    g_intervention_kl_max_segments = 256

    use_smdp_discounted_high_return = True
    use_smdp_bootstrap = True
    smdp_bootstrap_coef = 0.25
    use_high_value_norm = True
    high_max_grad_norm = 0.5

    # Anti-churn regularization.  These penalize unnecessary renewals; they do
    # not imply switching is intrinsically bad.
    edit_penalty_alpha = 0.01
    switch_penalty_beta = 0.005

    # Old HMASD discriminator/discoverer switches are deliberately off for this
    # algorithm config.  They only belong to legacy HMASD/control paths.
    use_team_code_discriminator = False
    use_individual_skill_discriminator = False
    use_segment_discriminator = False
    legacy_mi_reward_coef = 0.0

    # ----------------------------------------------------------------------
    # P2-lite: recovery-window contribution credit (see ALGORITHM_PRINCIPLES.md
    # -> "P2-lite: Recovery-Window Contribution Credit").  ALL OFF BY DEFAULT so
    # this never pollutes P1 runs.  First phase = compute_on + reward_off so the
    # Pre-check 2 diagnostics can be validated before any reward injection.
    p2_recovery_credit_compute_on = False   # compute + log soft potential / shaping
    p2_recovery_credit_reward_on = False     # inject shaping into the reward path
    p2_recovery_reward_level = "high_team"   # high_team, high_per_agent, low_only
    p2_recovery_reward_coef = 0.05
    p2_recovery_reward_clip = 0.5
    p2_low_positive_only = True              # low-level ablation uses positive-only
    p2_role_classifier_reward_on = False     # RETIRED from the active gate
    p2_g_normative_training_on = False       # DEFERRED until P2-lite moves recovery
    exact_cf_reward_on = False               # exact CF is audit-only, never reward
    exact_cf_compute_on = False              # window+candidate gated diagnostic
    p2_cf_stride = 10
    p2_near_disconnect_bh_frac = 0.4

    # Soft potential shape (fractions of area_size; gamma inherited above).
    p2_comm_range_frac = 0.25
    p2_bs_range_frac = 0.30
    p2_soft_temp_frac = 0.08
    p2_approach_scale_frac = 0.5
    p2_w_bs_approach = 0.34
    p2_w_bridge = 0.5
    p2_w_disc_approach = 0.16
    p2_lambda_rec = 1.0
    p2_bh_threshold = 0.6
    p2_w_recovery_temp = 0.15
