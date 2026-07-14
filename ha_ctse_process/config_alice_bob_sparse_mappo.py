"""Skill-blind sparse-reward MAPPO reset on Alice--Bob."""

from __future__ import annotations

from ha_ctse_process.config_alice_bob_asymmetric import Config as AliceBobConfig


class Config(AliceBobConfig):
    algorithm = "alice_bob_sparse_mappo_constant_skill"
    scenario_label = "alice_bob_asymmetric_cycles_sparse_mappo"
    high_controller = "r30_fixed_clock_ar_edit"
    constant_skill_no_high = True

    # R36's collector-side novelty is an architecture-neutral treatment.  Keep
    # its complete contract explicit and disabled in the R35 control config so
    # both manifests expose the same fields.
    aem_joint_novelty_enabled = False
    aem_joint_position_grid_size = 5
    aem_joint_position_table_size = 625
    aem_episode_horizon = 80
    aem_position_view_name = "alice_bob_normalized_joint_positions_v1"
    aem_bonus_formula = "inverse_horizon_sqrt_preincrement_v1"

    # Modules stay architecture-matched, but no segment/classifier path receives
    # data and the only optimized policy is the recurrent low-level PPO actor.
    alice_bob_semantic_reward_enabled = False
    r31_effect_mode = "off"
    transition_skill_reward_coef = 0.0
    process_reward_injection = "none"
