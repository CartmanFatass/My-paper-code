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
    n_z = 5
    skill_lifetime_candidates = (1, 2, 3, 5)
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
    num_team_codes = 5

    # PPO and entropy.
    high_entropy_coef = 0.01
    low_entropy_coef = 0.01
    clip_epsilon = 0.2
    gamma = 0.99

    # Process encoder and process reward.
    process_encoder_embedding_dim = 64
    lr_process_encoder = 1e-4
    process_contrast_coef = 1.0
    process_outcome_coef = 0.25
    process_reward_coef = 0.05
    process_reward_contrast_coef = 1.0
    process_reward_outcome_coef = 0.25
    process_reward_clip = 2.0
    normalize_process_outcomes = True
    use_process_reward_for_discoverer = True
    use_process_posterior_mi = True
    process_posterior_condition_on_team = True
    process_posterior_team_embed_dim = 0
    process_prior_coef = 0.25

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
