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

    # Round 14 Stage 1: prototype-response skill selection.  Default-off.
    # When enabled, skill codes are aligned to OPT prototypes rather than
    # arbitrary legacy z labels: n_skills = opt_num_prototypes +
    # prototype_skill_extra_codes.  The primitive actor still receives only
    # local observation and active skill.
    use_prototype_response_skills = False
    prototype_skill_extra_codes = 0
    # Round 15: the normal Stage-1 path is autoregressive prototype assignment
    # with the stored assignment log-prob as discriminator null.  Parallel
    # selection and learned-prior residuals are explicit fallback ablations.
    legacy_n_skills_override = 0
    use_autoregressive_selection = True
    parallel_selection = False
    ar_prefix_mode = "same_check"  # same_check, roster
    high_condition_on_omega = False
    use_agent_prototype_relevance = False
    prototype_bank_ema_tau = 0.005
    use_per_agent_kappa = False
    enable_prototype_disc_probe = False
    enable_prototype_disc_reward = False
    prototype_disc_reward_coef = 0.1
    prototype_disc_clip = 2.0
    prototype_disc_warmup_steps = 20000
    prototype_disc_condition = "kappa"  # kappa, omega, none
    prototype_disc_lr = 5e-4
    prototype_disc_hidden_dim = 0
    prototype_disc_use_learned_prior = False
    prototype_disc_prior_coef = 1.0
    use_compact_return_head = False
    compact_return_coef = 0.1

    # Compact-conditioned team code g_tau.
    team_bridge_type = "stochastic"
    team_code_dim = 64
    num_team_codes = n_Z
    # R21 TeamIntent restoration.  Default-off: when enabled, the bridge is
    # used as a sampled pi_Z(Z|c,omega) on a slower synchronized clock, while
    # asynchronous individual renewals dock against the held Z.
    enable_team_intent = False
    enable_team_disc_probe = False
    enable_team_disc_reward = False
    # K_team is in high-level check intervals. It must exceed the longest
    # individual lifetime candidate; otherwise Z-boundary atomic reassignment
    # structurally truncates long duration choices and fabricates collapse.
    team_intent_k = 48
    # R16.5 showed 0.1 intrinsic pressure can induce duration-collapse
    # pathology, while 0.05 was the cleaner stabilized base.
    team_disc_coef = 0.05
    team_disc_clip = 2.0
    team_disc_warmup_steps = 20000
    team_disc_lr = 5e-4
    team_disc_hidden_dim = 128
    # R23-3 hard actionability gate. Default-off (0.0 = no gate; preserves R21
    # behavior). When > 0, the team discriminator q_D(Z|s_next) REWARD is applied
    # only when the most recent measured forced-Z assignment KL (g_itv_kl_skill)
    # is >= this floor. R21 proved an ungated q_D reward is decorative: Z must be
    # actionable before the discriminator can amplify it.
    team_disc_actionability_floor = 0.0
    # R23 architecture correction (actionability). Default-off (0.0). When > 0, the
    # high policy gets a direct residual path from the team-intent vector into the
    # skill/duration assignment logits, so sampled Z can actually move the joint
    # assignment xi. R21 autopsy showed the trunk-only path had ~noise gain
    # (forced-Z skill KL ~0.002 at random-init AND final). This is the R23-0
    # static-capacity-gate knob; verify with scripts/r23_capacity_gate.py before
    # enabling any actionability objective.
    z_assignment_residual_gain = 0.0

    # R23-next q_A residual actionability (Option-B). Cross-entropy successor to the
    # self-stalling g-info MI objective (2026-07-06 gradient audit: g-info grad into
    # the Z path was <2% of PPO and MI never moved). q_A_full(Z|xi,c,omega) vs
    # q_A_prior(Z|c,omega); residual = log q_full - log q_prior. Discriminator-only
    # (detached inputs, own optimizer), high-level only. All default-off; reward is
    # gated behind the probe (residual_gain>0) + warmup. q_A may read xi; the team
    # effect discriminator q_D must NOT (PR-1 double-count contract).
    enable_assignment_actionability_probe = False
    enable_assignment_actionability_reward = False
    assignment_actionability_coef = 0.05
    assignment_actionability_clip = 1.0
    assignment_actionability_warmup_steps = 20000
    assignment_actionability_include_soft = True
    assignment_actionability_hidden_dim = 128

    # R23-next q_D effect-target / timescale audit (reward-off probe). Compares which
    # q_D observation space + horizon (if any) carries a recoverable Z signature after
    # R23-2 read q_D(Z|s_next) at chance. Targets: s_next, joint_action, joint_effect,
    # delta_omega over the given horizons. No reward is produced (audit only). q_D never
    # reads xi (double-count contract).
    enable_team_effect_target_audit = False
    team_effect_audit_targets = "s_next,joint_action,joint_effect,delta_omega"
    team_effect_audit_horizons = "10,20,50"
    team_effect_audit_hidden_dim = 128

    # PPO and entropy.
    high_entropy_coef = 0.01
    low_entropy_coef = 0.01
    # R16.5 stabilization, default-off.  When enabled, add a duration-head
    # entropy bonus only after realized duration usage entropy falls below the
    # floor.  This is a one-variable guard for duration collapse, not a new
    # task-specific reward.
    duration_entropy_floor_enabled = False
    duration_entropy_floor_threshold = 0.8
    duration_entropy_floor_coef = 0.05
    duration_entropy_floor_warmup_steps = 0
    # R21 insurance only: default-off generic entropy floor for the sampled
    # team-intent head. Enable only if the logged Z usage entropy red flag
    # fires; do not treat this as evidence of self-sustained heterogeneity.
    z_entropy_floor_enabled = False
    z_entropy_floor_threshold = 0.8
    z_entropy_floor_coef = 0.05
    z_entropy_floor_warmup_steps = 0
    reward_ratio_guard_mode = "kill"  # kill, warn
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

    # P3 Stage A: reward-off skill-effect discovery probe.  This asks whether
    # z_i adds conditional predictive power for short-horizon effects beyond
    # context/duration/reward shortcuts.  It is OFF by default and must not
    # inject reward until the Stage-A shortcut gates pass.
    skill_effect_discovery_on = False
    skill_effect_reward_on = False
    skill_effect_reward_injection = "none"  # none, low_only (Stage B only)
    skill_effect_horizons = (3, 5, 10, 20)
    skill_effect_stride = 5
    skill_effect_max_windows = 8192
    skill_effect_hidden_dim = 256
    skill_effect_group_balanced_loss = True
    skill_effect_intervention_probe_on = False
    skill_effect_intervention_max_samples = 256
    skill_effect_warmup_steps = 80000
    skill_effect_ctrl_coef = 0.02
    skill_effect_use_coef = 0.02
    skill_effect_reward_clip = 0.05
    skill_effect_min_gain = 0.0
    skill_effect_min_positive_frac = 0.55
    # P3-4 forcing reward, default-off. This is not a communication-metric
    # heuristic: by default the forcing discriminator uses only action plus
    # motion/energy effect fields for intrinsic reward.
    skill_force_probe_on = False
    enable_skill_forcing_reward = False
    skill_force_reward_injection = "low_only"  # low_only, none
    skill_force_disc_coef = 0.02
    skill_force_effect_coef = 0.0
    skill_force_duration_entropy_coef = 0.0
    skill_force_warmup_steps = 80000
    skill_force_clip = 0.05
    skill_force_shortcut_margin = 0.0
    skill_force_kill_on_shortcut = True
    skill_force_use_comm_fields = False

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
    # Round 10 / G2: live team-code usage objective.  This is generic high-level
    # decision pressure: enumerate g under the same OPT context and test whether
    # skill/duration distributions change.  It is diagnostic by default and only
    # enters the high-level loss when enable_g_info_objective is explicitly set.
    use_g_info_diagnostic = True
    enable_g_info_objective = False
    g_info_coef_skill = 0.0
    g_info_coef_duration = 0.0
    g_info_coef_edit = 0.0
    g_info_warmup_steps = 80000
    g_info_anneal_steps = 0
    g_info_max_segments = 256

    # Round 12 Stage 1: OPT situation substrate and reward-pure hazard renewal.
    # Safe by default: diagnostics and control are both off unless explicitly
    # requested. This stage must not inject SEF/DADS or communication rewards.
    situation_substrate_source = "omega"  # omega, compact_cluster
    situation_num_kappa = 4
    situation_debounce_steps = 2
    enable_situation_diagnostics = False
    enable_situation_hazard_control = False
    situation_hazard_mode = "diagnostic"  # diagnostic, oracle_change, learned_beta
    situation_hazard_check_interval = 10
    situation_hazard_min_age = 1
    situation_hazard_hidden_dim = 128
    situation_hazard_entropy_coef = 0.005
    situation_hazard_value_coef = 0.5
    situation_hazard_clip_epsilon = 0.2
    situation_hazard_reward_coef = 0.0
    situation_hazard_conservative_guard = False
    situation_hazard_min_dwell_checks = 0
    situation_hazard_confirm_changes = 1
    situation_hazard_max_force_rate = 1.0
    situation_hazard_rate_window = 128

    # R19: team situation-transition residual head.  This is the generic team
    # engine counterpart to individual role diversity: predict kappa' from
    # (kappa, active-skill counts) against a kappa-only prior.  Default-off.
    enable_team_transition_probe = False
    enable_team_transition_reward = False
    team_transition_coef = 0.05
    team_transition_clip = 2.0
    team_transition_warmup_steps = 20000
    team_transition_lr = 5e-4
    team_transition_hidden_dim = 128

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
