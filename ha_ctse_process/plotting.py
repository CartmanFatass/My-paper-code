"""Metrics export and plotting for standalone HA-CTSE UAV experiments."""

from __future__ import annotations

import csv
import re
import argparse
import warnings
from pathlib import Path
from typing import Any

import numpy as np

from ha_ctse_process.cooperation_credit import COOPERATION_CREDIT_FIELDS
from ha_ctse_process.g_info_objective import G_INFO_METRIC_FIELDS
from ha_ctse_process.assignment_actionability import ASSIGNMENT_ACTIONABILITY_METRIC_FIELDS
from ha_ctse_process.team_effect_targets import TEAM_EFFECT_TARGET_METRIC_FIELDS
from ha_ctse_process.team_conditioned_qd import TEAM_CONDITIONED_QD_METRIC_FIELDS
from ha_ctse_process.topology_potential import TOPOLOGY_POTENTIAL_FIELDS
from ha_ctse_process.situation_transition import TEAM_TRANSITION_METRIC_FIELDS
from ha_ctse_process.team_intent import TEAM_INTENT_METRIC_FIELDS

try:
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    warnings.filterwarnings(
        "ignore",
        message="Tight layout not applied.*",
        category=UserWarning,
    )
except Exception:  # pragma: no cover - plotting is optional in headless smoke.
    plt = None


# Field set follows the Scenario 7/HMASD training monitor categories, trimmed to
# scalar UAV metrics that are meaningful for standalone HA-CTSE eval plots.
UAV_METRIC_FIELDS = (
    "coverage_ratio",
    "effective_connected_users",
    "system_throughput_mbps",
    "avg_throughput_per_user_mbps",
    "capacity_limited_throughput_mbps",
    "effective_end_to_end_throughput_mbps",
    "qos_satisfaction_ratio",
    "qos_met_fraction",
    "qos_target_ratio",
    "mean_user_rate_mbps",
    "std_user_rate_mbps",
    "min_user_rate_mbps",
    "median_user_rate_mbps",
    "p10_user_rate_mbps",
    "p90_user_rate_mbps",
    "max_user_rate_mbps",
    "battery_mean_ratio",
    "battery_min_ratio",
    "low_battery_uav_count",
    "critical_battery_uav_count",
    "energy_failure_uav_count",
    "depleted_uav_count",
    "charging_uav_count",
    "effective_charging_session_count",
    "episode_charging_session_count",
    "episode_first_effective_charge_step",
    "episode_energy_charged_wh",
    "normalized_propulsion_energy",
    "instantaneous_bits_per_joule",
    "return_constraint_cost",
    "return_risk_penalty",
    "return_deficit_max",
    "return_margin_mean",
    "return_margin_min",
    "return_violation_fraction",
    "episode_return_constraint_cost_sum",
    "episode_return_risk_penalty_sum",
    "episode_return_risk_steps",
    "episode_max_return_deficit",
    "episode_final_min_return_margin",
    "cutoff_event_count",
    "depletion_event_count",
    "episode_cutoff_event_count",
    "episode_depletion_event_count",
    "episode_qos_utility_sum",
    "episode_qos_utility_mean",
    "episode_graph_pbrs_sum",
    "task_utility",
    "scenario7_reward",
    "safety_reward_before_pbrs",
    "graph_potential_delta",
    "shaping_potential_delta",
)

COMM_METRIC_FIELDS = (
    "connected_users",
    "access_connected_users",
    "total_connected_users",
    "served_users",
    "connectivity_ratio",
    "connected_uavs",
    "uavs_with_backhaul",
    "avg_hops",
    "relay_route_lost_uavs",
    "relay_route_lost_users",
    "relay_route_loss_ratio",
    "relay_route_loss_prev_served_ratio",
    "prev_backhaul_served_users",
    "current_backhaul_served_users",
    "backhaul_outage_users",
    "backhaul_outage_ratio",
    "service_drop_users",
    "service_drop_ratio",
    "backhaul_drop_users",
    "backhaul_drop_ratio",
    "full_network_disconnect",
    "full_disconnect_streak",
    "coverage_drop_ratio",
    "backhaul_outage_ema",
    "instant_outage_intensity",
    "min_serving_backhaul_bottleneck_mbps",
    "avg_serving_backhaul_bottleneck_mbps",
    "backhaul_margin_penalty_raw",
    "backhaul_outage_penalty",
    "full_disconnect_penalty",
    "coverage_drop_penalty",
    "outage_memory_penalty",
    "relay_break_penalty",
    "backhaul_margin_penalty",
    "backhaul_guard_checked_actions",
    "backhaul_guard_blocked_actions",
    "routing_overhead",
)

DERIVED_EVAL_FIELDS = (
    "backhaul_connected_flag",
    "backhaul_connected_step_fraction",
    "throughput_when_backhaul_connected_mbps",
    "coverage_eq1_step_fraction",
    "coverage_positive_step_fraction",
    "coverage_has_eq1_step_flag",
    "coverage_episode_all_eq1_flag",
    "coverage_final_eq1_flag",
    "zero_throughput_step_fraction",
    "zero_throughput_episode_flag",
    "throughput_gt5_step_fraction",
    "throughput_gt5_episode_flag",
)

SITUATION_STAGE1_FIELDS = (
    "situation_enabled",
    "situation_change_rate",
    "situation_unique_kappa",
    "situation_segment_change_frac",
    "situation_agent_kappa_enabled",
    "situation_agent_kappa_change_rate",
    "situation_agent_kappa_disagreement_rate",
    "situation_agent_kappa_median_dwell",
    "situation_agent_kappa_global_mi",
    "situation_agent_unique_kappa_mean",
    "situation_agent_unique_kappa_mean",
    "situation_hazard_control_enabled",
    "situation_hazard_forced_renewal_rate",
    "situation_hazard_mode_code",
    "situation_hazard_conservative_guard",
    "situation_hazard_guard_event_count",
    "situation_hazard_guard_allow_rate",
    "situation_hazard_guard_confirm_block_rate",
    "situation_hazard_guard_dwell_block_rate",
    "situation_hazard_guard_rate_cap_block_rate",
    "situation_hazard_guard_no_change_block_rate",
    "situation_hazard_guard_recent_force_rate",
)

R28_G1_METRIC_FIELDS = (
    "r28_g1_active",
    "r28_g1_arm_code",
    "r28_g1_segments_seen",
    "r28_g1_structural_rows",
    "r28_g1_initial_rows_rejected",
    "r28_g1_episode_truncated_rows_rejected",
    "r28_g1_update_truncated_rows_rejected",
    "r28_g1_length_rows_rejected",
    "r28_g1_pre_window_rows_rejected",
    "r28_g1_ood_fraction",
    "r28_g1_in_support_rows",
    "r28_g1_support_distance_ratio_mean",
    "r28_g1_support_distance_ratio_p95",
    "r28_g1_support_abs_z_action0_mean",
    "r28_g1_support_abs_z_action0_std",
    "r28_g1_support_abs_z_action0_slope",
    "r28_g1_support_abs_z_action1_mean",
    "r28_g1_support_abs_z_action1_std",
    "r28_g1_support_abs_z_action1_slope",
    "r28_g1_support_abs_z_action2_mean",
    "r28_g1_support_abs_z_action2_std",
    "r28_g1_support_abs_z_action2_slope",
    "r28_g1_support_abs_z_action3_mean",
    "r28_g1_support_abs_z_action3_std",
    "r28_g1_support_abs_z_action3_slope",
    "r28_g1_support_kill_switch_event",
    "r28_g1_rewardable_groups",
    "r28_g1_rewardable_rows",
    "r28_g1_unbalanced_groups",
    "r28_g1_real_score_mean",
    "r28_g1_sham_score_mean",
    "r28_g1_real_minus_sham_score_mean",
    "r28_g1_real_centered_abs_mean",
    "r28_g1_sham_centered_abs_mean",
    "r28_g1_selected_segment_reward_abs_mean",
    "r28_g1_selected_distributed_reward_abs_mean",
    "r28_g1_reward_applied_steps",
    "r28_g1_reward_env_ratio",
    "r28_g1_ratio_kill_switch_event",
)

R29_ACTION_INFO_METRIC_FIELDS = (
    "r29_action_info_active",
    "r29_action_info_mode_code",
    "r29_action_info_rows",
    "r29_action_info_segments",
    "r29_action_info_terminal_rows",
    "r29_action_info_excluded_segments",
    "r29_action_info_raw_mean",
    "r29_action_info_raw_abs_mean",
    "r29_action_info_raw_positive_frac",
    "r29_action_info_raw_q01",
    "r29_action_info_raw_q99",
    "r29_action_info_scaled_mean",
    "r29_action_info_scaled_abs_mean",
    "r29_action_info_clip_fraction",
    "r29_action_info_reward_applied_steps",
    "r29_action_info_reward_env_ratio",
    "r29_action_info_likelihood_max_abs_error",
    "r29_action_info_symmetric_kl_mean",
    "r29_action_info_symmetric_kl_mean_component",
    "r29_action_info_symmetric_kl_variance_component",
    "r29_action_info_skill_0_mean",
    "r29_action_info_skill_1_mean",
    "r29_action_info_skill_2_mean",
    "r29_action_info_skill_3_mean",
)


UPDATE_FIELDS = (
    "update",
    "total_steps",
    "env_reward_mean",
    *R28_G1_METRIC_FIELDS,
    *R29_ACTION_INFO_METRIC_FIELDS,
    "process_segments",
    "process_loss",
    "process_outcome_loss",
    "process_contrastive_loss",
    "process_prior_loss",
    "process_posterior_acc",
    "process_mi_estimate_mean",
    "process_residual_mi_mean",
    "process_residual_mi_positive_frac",
    "process_residual_log_shortcut_mean",
    "process_residual_log_context_mean",
    "process_log_q_mean",
    "process_log_p_mean",
    "process_shortcut_loss",
    "process_shortcut_context_loss",
    "process_shortcut_margin_loss",
    "process_reward_warmup_active",
    "transition_skill_samples",
    "transition_skill_available_samples",
    "transition_skill_loss",
    "transition_skill_prior_loss",
    "transition_skill_context_loss",
    "transition_skill_acc",
    "transition_skill_context_acc",
    "transition_skill_mi_mean",
    "transition_skill_mi_positive_frac",
    "transition_skill_residual_mi_mean",
    "transition_skill_residual_mi_positive_frac",
    "transition_skill_reward_mean",
    "transition_skill_reward_active",
    "transition_skill_log_q_mean",
    "transition_skill_log_p_mean",
    "transition_skill_log_context_mean",
    "transition_skill_reward_unclipped_mean",
    "transition_skill_reward_warmup_active",
    *TEAM_TRANSITION_METRIC_FIELDS,
    *TEAM_INTENT_METRIC_FIELDS,
    "proto_disc_active",
    "proto_disc_samples",
    "proto_disc_loss",
    "proto_disc_q_loss",
    "proto_disc_prior_loss",
    "proto_disc_acc",
    "proto_disc_prior_acc",
    "proto_disc_null_logp_mean",
    "proto_assignment_logp_mean",
    "proto_assignment_logp_std",
    "proto_ar_parallel_kl",
    "roster_ar_kl_zeroed",
    "roster_ar_kl_shuffled",
    "selection_independence_available",
    "selection_same_skill_rate",
    "selection_independence_null_rate",
    "selection_independence_deficit",
    "proto_disc_residual_mean",
    "proto_disc_residual_positive_frac",
    "proto_disc_acc_by_skill_std",
    "proto_disc_reward_mean",
    "proto_disc_reward_unclipped_mean",
    "proto_disc_reward_applied_steps",
    "proto_disc_reward_env_ratio",
    "proto_disc_reward_env_ratio_over05_count",
    "proto_disc_reward_env_ratio_guard_active",
    "proto_disc_reward_env_ratio_kill_triggered",
    "proto_skill_selection_entropy",
    "proto_skill_usage_entropy_by_kappa",
    "proto_skill_relevance_alignment",
    "proto_skill_selected_relevance_mean",
    "proto_omega_nonzero_frac",
    "proto_bank_drift_cos",
    "proto_rel_row_entropy_mean",
    "proto_rel_argmax_dwell_median",
    "proto_rel_stability_cos",
    "proto_rel_drop_event_rate_05",
    "proto_rel_drop_event_rate_03",
    "proto_rel_drop_event_rate_01",
    "intrinsic_segment_high_gate_active",
    "intrinsic_segment_high_gate_score",
    "intrinsic_segment_high_gate_posterior_minus_shortcut",
    "intrinsic_segment_high_gate_residual_mi",
    "intrinsic_segment_high_gate_segment_count",
    "intrinsic_segment_high_gate_reason_code",
    "process_shortcut_duration_acc",
    "process_shortcut_length_acc",
    "process_shortcut_reward_sum_acc",
    "process_shortcut_context_acc",
    "process_shortcut_max_acc",
    "posterior_acc_minus_shortcut_max",
    "posterior_acc_minus_context_shortcut",
    "process_reward_mi_component_mean",
    "process_reward_outcome_penalty_mean",
    "process_reward_unclipped_mean",
    "process_mi_positive_frac",
    "process_reward_mean",
    "process_reward_high_mean",
    "process_reward_low_mean",
    "semantic_shortcut_hard_stop_triggered",
    "semantic_shortcut_hard_stop_applied",
    "semantic_shortcut_hard_stop_score",
    "semantic_shortcut_hard_stop_reason_code",
    "outcome_available_mean",
    "outcome_abs_mean",
    "outcome_residual_full_loss",
    "outcome_residual_base_loss",
    "outcome_residual_total_loss",
    "outcome_residual_gain_mean",
    "outcome_residual_gain_positive_frac",
    "outcome_residual_available_mean",
    "outcome_residual_target_abs_mean",
    "outcome_residual_reward_mean",
    "outcome_residual_reward_active",
    "outcome_residual_reward_unclipped_mean",
    "outcome_residual_skill_gain_std",
    "outcome_residual_team_gain_std",
    "outcome_residual_duration_gain_std",
    "outcome_residual_gain_coverage_delta_h",
    "outcome_residual_gain_qos_delta_h",
    "outcome_residual_gain_full_disconnect_improvement_h",
    "outcome_residual_gain_relay_margin_delta_h",
    "outcome_residual_gain_connected_components_improvement_h",
    "outcome_residual_gain_teammate_service_gain_h",
    "outcome_residual_gain_bottleneck_link_gain_h",
    "topology_role_samples",
    "topology_role_available_frac",
    "topology_role_loss",
    "topology_role_full_loss",
    "topology_role_shortcut_loss",
    "topology_role_acc",
    "topology_role_shortcut_acc",
    "topology_role_resid_gain_mean",
    "topology_role_resid_gain_positive_frac",
    "topology_role_reward_mean",
    "topology_role_reward_active",
    "topology_role_reward_unclipped_mean",
    "topology_role_z_mi",
    "topology_role_g_mi",
    "topology_role_frac_idle",
    "topology_role_frac_relay",
    "topology_role_frac_service",
    "topology_role_frac_relay_service",
    "topology_cf_backhaul_start_mean",
    "topology_cf_backhaul_mean_mean",
    "topology_cf_backhaul_max_mean",
    "topology_cf_backhaul_delta_mean",
    "topology_cf_components_start_mean",
    "topology_cf_components_mean_mean",
    "topology_cf_components_max_mean",
    "topology_cf_components_delta_mean",
    "topology_cf_disconnect_start_mean",
    "topology_cf_disconnect_mean_mean",
    "topology_cf_disconnect_max_mean",
    "topology_cf_disconnect_delta_mean",
    "topology_service_start_mean",
    "topology_service_mean_mean",
    "topology_service_max_mean",
    "topology_service_delta_mean",
    "topology_coverage_delta_mean",
    "topology_qos_delta_mean",
    "topology_battery_start_mean",
    "topology_battery_delta_mean",
    "topology_length_log_mean",
    *TOPOLOGY_POTENTIAL_FIELDS,
    "effect_windows",
    "effect_loss_full",
    "effect_loss_base",
    "effect_loss_duration",
    "effect_loss_reward",
    "effect_loss_full_raw",
    "effect_loss_base_raw",
    "effect_loss_duration_raw",
    "effect_loss_reward_raw",
    "effect_gain_mean",
    "effect_gain_group_balanced_mean",
    "effect_gain_nonmotion",
    "effect_gain_positive_frac",
    "effect_gain_motion",
    "effect_gain_service",
    "effect_gain_energy",
    "effect_gain_topology",
    "effect_gain_minus_duration_baseline",
    "effect_gain_minus_reward_baseline",
    "effect_target_available_frac",
    "effect_skill_usage_entropy",
    "effect_skill_usage_max_frac",
    "effect_action_skill_eta2",
    "effect_target_skill_eta2",
    "effect_gain_skill_std",
    "effect_action_abs_mean",
    "effect_action_dim",
    "effect_observed_target_skill_l2_mean",
    "effect_observed_target_skill_l2_nonmotion",
    "effect_observed_action_skill_l2_mean",
    "effect_observed_action_target_corr",
    "effect_endstate_available_frac",
    "effect_window_mean_available_frac",
    "effect_intervention_active",
    "effect_intervention_samples",
    "effect_intervention_action_l2_mean",
    "effect_intervention_action_l2_max",
    "effect_intervention_action_pairwise_std",
    "effect_intervention_pred_effect_l2_mean",
    "effect_intervention_pred_effect_l2_max",
    "effect_intervention_best_skill_gap",
    "effect_intervention_low_entropy_mean",
    "effect_gain_horizon_0",
    "effect_gain_positive_frac_horizon_0",
    "effect_horizon_count_0",
    "effect_gain_horizon_1",
    "effect_gain_positive_frac_horizon_1",
    "effect_horizon_count_1",
    "effect_gain_horizon_2",
    "effect_gain_positive_frac_horizon_2",
    "effect_horizon_count_2",
    "effect_gain_horizon_3",
    "effect_gain_positive_frac_horizon_3",
    "effect_horizon_count_3",
    "effect_field_gain_delta_position_x",
    "effect_field_gain_delta_position_y",
    "effect_field_gain_delta_position_z",
    "effect_field_gain_delta_position_l2",
    "effect_field_gain_delta_battery",
    "effect_field_gain_delta_charging",
    "effect_field_gain_delta_local_service",
    "effect_field_gain_delta_local_access_count",
    "effect_field_gain_delta_uav_degree",
    "effect_field_gain_delta_bs_link",
    "effect_field_gain_delta_soft_topology",
    "effect_field_gain_delta_coverage_ratio",
    "effect_field_gain_delta_qos_satisfaction",
    "effect_field_gain_delta_system_throughput_mbps",
    "effect_field_gain_end_local_service",
    "effect_field_gain_end_local_access_count",
    "effect_field_gain_end_uav_degree",
    "effect_field_gain_end_bs_link",
    "effect_field_gain_end_soft_topology",
    "effect_field_gain_end_coverage_ratio",
    "effect_field_gain_end_qos_satisfaction",
    "effect_field_gain_end_system_throughput_mbps",
    "effect_field_gain_mean_local_service",
    "effect_field_gain_mean_uav_degree",
    "effect_field_gain_mean_bs_link",
    "effect_field_gain_mean_backhaul_connected_flag",
    "effect_field_gain_mean_full_disconnect",
    "effect_reward_low_mean",
    "effect_reward_applied_steps",
    "force_reward_low_mean",
    "force_reward_applied_steps",
    "force_disc_loss",
    "force_disc_acc",
    "force_disc_logp_mean",
    "force_disc_residual_mean",
    "force_effect_residual_mean",
    "force_shortcut_best_acc",
    "force_shortcut_best_logp_mean",
    "force_shortcut_margin",
    "force_shortcut_duration_acc",
    "force_shortcut_reward_acc",
    "force_shortcut_context_acc",
    "force_shortcut_phase_agent_acc",
    "force_gate_active",
    "force_gate_reason",
    "force_reward_unclipped_mean",
    "force_duration_entropy_bonus",
    "force_feature_dim",
    "duration_only_accuracy",
    "length_only_accuracy",
    "reward_sum_only_accuracy",
    "posterior_acc_minus_duration_only",
    "posterior_acc_minus_length_only",
    "posterior_acc_minus_reward_sum_only",
    "skill_switch_rate",
    "segment_length_mean",
    "segment_length_max",
    "duration_target_mean",
    "skill_usage_entropy",
    "skill_usage_max_frac",
    "duration_usage_entropy",
    "duration_usage_max_frac",
    "duration_policy_entropy",
    "duration_policy_entropy_norm",
    "duration_entropy_floor_active",
    "duration_entropy_floor_gap",
    "duration_entropy_floor_loss",
    "duration_entropy_floor_coef_active",
    "skill_duration_mi",
    "lifetime_heterogeneity",
    "duration_target_std",
    "duration_target_cv",
    "duration_agent_mi",
    "duration_return_std",
    "duration_return_range",
    "duration_return_active_frac",
    "duration_full_disconnect_std",
    "duration_full_disconnect_range",
    "duration_recovery_std",
    "duration_recovery_range",
    "duration_bh_frac_std",
    "duration_bh_frac_range",
    "renewal_agents_mean",
    "renewal_agents_std",
    "renewal_full_sync_rate",
    "renewal_pairwise_corr_mean",
    "team_code_usage_entropy",
    "team_code_usage_max_frac",
    "team_code_skill_mi",
    "team_code_duration_mi",
    "team_code_edit_mi",
    "g_usage_entropy",
    "g_usage_max_frac",
    "g_intervention_kl_active",
    "g_intervention_kl_samples",
    "g_intervention_kl_mean",
    "g_intervention_kl_max",
    "g_intervention_tv_mean",
    *G_INFO_METRIC_FIELDS,
    *ASSIGNMENT_ACTIONABILITY_METRIC_FIELDS,
    *TEAM_EFFECT_TARGET_METRIC_FIELDS,
    *TEAM_CONDITIONED_QD_METRIC_FIELDS,
    *SITUATION_STAGE1_FIELDS,
    *COOPERATION_CREDIT_FIELDS,
    "high_loss",
    "high_policy_loss",
    "high_value_loss",
    "high_entropy_loss",
    "high_aux_loss",
    "high_entropy",
    "high_return_mean",
    "high_env_return_mean",
    "high_bootstrap_value_mean",
    "high_bootstrap_contribution_mean",
    "high_smdp_discount_mean",
    "high_value_norm_mean",
    "high_value_norm_std",
    "high_grad_norm",
    "compact_return_loss",
    "compact_return_active",
    "team_code_entropy",
    "compact_norm_mean",
    "opt_cd_loss",
    "opt_cmi_loss",
    "opt_aggregation_entropy",
    "low_loss",
    "low_policy_loss",
    "low_value_loss",
    "low_entropy_loss",
    "low_actor_loss",
    "low_critic_loss",
    "low_entropy",
    "low_sequence_chunks",
    "low_value_norm_mean",
    "low_value_norm_std",
    "low_value_error_abs_mean",
    "low_value_error_rmse",
    "low_advantage_std",
    "low_ratio_mean",
    "low_clip_frac",
    "low_approx_kl",
    "low_actor_grad_norm",
    "low_critic_grad_norm",
    "low_actor_h_norm_mean",
    "low_critic_h_norm_mean",
    "low_skill_usage_entropy",
    "low_skill_return_std",
    "low_skill_return_range",
    "low_skill_value_error_abs_std",
    "low_skill_entropy_std",
    "low_team_usage_entropy",
    "low_team_return_std",
    "low_team_return_range",
    "low_team_value_error_abs_std",
    "return_mean",
    # P2-lite recovery-window contribution credit (mirrors empty_p2_metrics()).
    "p2_available_frac",
    "p2_window_frac",
    "p2_phi_sum_mean",
    "p2_f_team_mean",
    "p2_f_team_std",
    "p2_f_team_p95",
    "p2_w_recovery_mean",
    "p2_connected_frac_mean",
    "p2_credit_mean",
    "p2_credit_std",
    "p2_credit_p95",
    "p2_credit_by_disconnect_state",
    "p2_credit_by_recovery_event",
    "delta_phi_soft_nonzero_rate_when_full_disconnect",
    "delta_phi_soft_nonzero_rate_when_near_disconnect",
    "p2_corr_phi_recovery_event",
    "p2_delta_bh_frac_mean",
    "p2_partial_recovery_frac",
    "p2_corr_credit_delta_bh_frac",
    "p2_credit_by_partial_recovery_event",
    "p2_cf_corr",
    "p2_cf_nonzero_rate",
    "p2_segments",
)

EVAL_FIELDS = (
    "checkpoint",
    "total_steps",
    "episode",
    "action_mode_code",
    "reward",
    "length",
    *UAV_METRIC_FIELDS,
    *COMM_METRIC_FIELDS,
    *DERIVED_EVAL_FIELDS,
)


def numeric_scalar(value) -> float | None:
    if value is None:
        return None
    try:
        arr = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError):
        return None
    if arr.size == 0:
        return None
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return None
    return float(np.mean(finite))


def extract_uav_metrics(info: dict[str, Any] | None) -> dict[str, float]:
    if not isinstance(info, dict):
        return {}
    reward_info = info.get("reward_info", {})
    reward_components = info.get("reward_components", {})
    if isinstance(reward_components, dict) and isinstance(reward_components.get("reward_info"), dict):
        reward_components = {**reward_components, **reward_components["reward_info"]}
    source = {}
    for key, value in info.items():
        if key in {"reward_info", "reward_components", "infos_dict", "terminations_dict", "truncations_dict"}:
            continue
        source[key] = value
    if isinstance(reward_components, dict):
        source.update(reward_components)
    if isinstance(reward_info, dict):
        source.update(reward_info)

    aliases = {
        "coverage_ratio": ("coverage_ratio", "coverage", "final_coverage", "current_coverage"),
        "qos_satisfaction_ratio": (
            "qos_satisfaction_ratio",
            "qos_satisfaction",
            "qos_met_fraction",
            "qos_score",
            "current_qos",
        ),
        "system_throughput_mbps": (
            "system_throughput_mbps",
            "total_throughput_mbps",
            "throughput",
        ),
        "battery_min_ratio": ("battery_min_ratio", "min_battery_ratio", "min_energy_ratio"),
        "connected_users": ("connected_users", "effective_connected_users", "served_users"),
        "served_users": ("served_users", "effective_connected_users", "connected_users"),
        "connected_uavs": ("connected_uavs", "uavs_with_backhaul"),
    }
    metrics = {}
    for key in (*UAV_METRIC_FIELDS, *COMM_METRIC_FIELDS):
        scalar = numeric_scalar(source.get(key))
        if scalar is not None:
            metrics[key] = scalar
    for canonical, keys in aliases.items():
        if canonical in metrics:
            continue
        for key in keys:
            scalar = numeric_scalar(source.get(key))
            if scalar is not None:
                metrics[canonical] = scalar
                break
    throughput = metrics.get("system_throughput_mbps")
    served_backhaul = metrics.get(
        "current_backhaul_served_users",
        metrics.get("effective_connected_users", metrics.get("served_users", 0.0)),
    )
    full_disconnect = metrics.get("full_network_disconnect", 0.0)
    outage_ratio = metrics.get("backhaul_outage_ratio", 0.0)
    backhaul_connected = (
        served_backhaul is not None
        and float(served_backhaul) > 0.0
        and float(full_disconnect) < 0.5
        and float(outage_ratio) < 0.999
    )
    metrics["backhaul_connected_flag"] = 1.0 if backhaul_connected else 0.0
    if throughput is not None and backhaul_connected:
        metrics["throughput_when_backhaul_connected_mbps"] = float(throughput)
    return metrics


def append_csv(path: Path, row: dict[str, Any], fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        with path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            old_fields = tuple(reader.fieldnames or ())
            rows = list(reader)
        if old_fields != fields:
            preserved = tuple(field for field in old_fields if field not in fields)
            merged_fields = (*fields, *preserved)
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(merged_fields), extrasaction="ignore")
                writer.writeheader()
                for old_row in rows:
                    writer.writerow({field: old_row.get(field, "") for field in merged_fields})
            fields = merged_fields
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in fields})


def write_csv(path: Path, rows: list[dict[str, Any]], fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv_records(path: Path) -> list[dict[str, float]]:
    if not path.exists():
        return []
    records: list[dict[str, float]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            record = {}
            for key, value in row.items():
                if value == "":
                    continue
                try:
                    record[key] = float(value)
                except ValueError:
                    continue
            if record:
                records.append(record)
    return records


def moving_average(values: np.ndarray, window: int) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return values
    window = max(1, min(int(window), values.size))
    kernel = np.ones(window, dtype=float) / float(window)
    return np.convolve(values, kernel, mode="same")


def _series(records: list[dict[str, float]], key: str) -> tuple[np.ndarray, np.ndarray]:
    xs = []
    ys = []
    for idx, record in enumerate(records):
        if key not in record:
            continue
        xs.append(record.get("total_steps", idx + 1))
        ys.append(record[key])
    return np.asarray(xs, dtype=float), np.asarray(ys, dtype=float)


def save_update_plots(log_dir: str | Path, window: int = 5) -> None:
    if plt is None:
        return
    log_dir = Path(log_dir)
    records = read_csv_records(log_dir / "metrics" / "train_updates.csv")
    if not records:
        return

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("env_reward_mean", "Env reward mean"),
        ("return_mean", "Low return mean"),
        ("process_reward_mean", "Process reward mean"),
        ("process_reward_unclipped_mean", "Process reward raw"),
        ("process_reward_mi_component_mean", "Process MI reward"),
        ("process_reward_outcome_penalty_mean", "Process outcome penalty"),
        ("process_reward_high_mean", "Process reward to high"),
        ("process_reward_low_mean", "Process reward to low"),
        ("outcome_residual_reward_mean", "Outcome residual reward"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Standalone HA-CTSE Training Rewards", xlabel="Env steps")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "ha_ctse_training_rewards.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("process_loss", "Process loss"),
        ("process_contrastive_loss", "Process contrast"),
        ("process_prior_loss", "Process prior"),
        ("process_outcome_loss", "Process outcome"),
        ("outcome_residual_full_loss", "Outcome full"),
        ("outcome_residual_base_loss", "Outcome baseline"),
        ("high_loss", "High loss"),
        ("high_value_loss", "High value"),
        ("high_policy_loss", "High policy"),
        ("high_grad_norm", "High grad norm"),
        ("low_loss", "Low loss"),
        ("low_value_loss", "Low value"),
        ("low_actor_loss", "Low actor"),
        ("low_critic_loss", "Low critic"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Standalone HA-CTSE Losses", xlabel="Env steps")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "ha_ctse_losses.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("low_value_error_abs_mean", "Low value abs error"),
        ("low_value_error_rmse", "Low value RMSE"),
        ("low_advantage_std", "Low advantage std"),
        ("low_ratio_mean", "Low PPO ratio"),
        ("low_clip_frac", "Low clip frac"),
        ("low_approx_kl", "Low approx KL"),
        ("low_actor_grad_norm", "Low actor grad norm"),
        ("low_critic_grad_norm", "Low critic grad norm"),
        ("low_actor_h_norm_mean", "Low actor hidden norm"),
        ("low_critic_h_norm_mean", "Low critic hidden norm"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Low-Level MAPPO Diagnostics", xlabel="Env steps")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "ha_ctse_low_level_diagnostics.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("low_skill_usage_entropy", "Skill usage entropy"),
        ("low_skill_return_std", "Skill return std"),
        ("low_skill_return_range", "Skill return range"),
        ("low_skill_value_error_abs_std", "Skill value-error std"),
        ("low_skill_entropy_std", "Skill action-entropy std"),
        ("low_team_usage_entropy", "Team-code usage entropy"),
        ("low_team_return_std", "Team-code return std"),
        ("low_team_return_range", "Team-code return range"),
        ("low_team_value_error_abs_std", "Team-code value-error std"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Low-Level Skill/Team-Code Diagnostics", xlabel="Env steps")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "ha_ctse_low_level_skill_team_diagnostics.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("duration_only_accuracy", "Duration-only accuracy"),
        ("length_only_accuracy", "Length-only accuracy"),
        ("reward_sum_only_accuracy", "Reward-sum-only accuracy"),
        ("process_shortcut_context_acc", "Context shortcut accuracy"),
        ("posterior_acc_minus_duration_only", "Posterior - duration"),
        ("posterior_acc_minus_length_only", "Posterior - length"),
        ("posterior_acc_minus_reward_sum_only", "Posterior - reward-sum"),
        ("posterior_acc_minus_context_shortcut", "Posterior - context"),
        ("skill_switch_rate", "Skill switch rate"),
        ("segment_length_mean", "Segment length mean"),
        ("skill_usage_entropy", "Skill usage entropy"),
        ("duration_usage_entropy", "Duration usage entropy"),
        ("duration_policy_entropy_norm", "Duration policy entropy norm"),
        ("duration_entropy_floor_active", "Duration entropy floor active"),
        ("duration_entropy_floor_gap", "Duration entropy floor gap"),
        ("team_code_usage_entropy", "Team-code usage entropy"),
        ("skill_usage_max_frac", "Skill max fraction"),
        ("duration_usage_max_frac", "Duration max fraction"),
        ("team_code_usage_max_frac", "Team-code max fraction"),
        ("skill_duration_mi", "Skill-duration MI"),
        ("team_code_skill_mi", "Team-code/skill MI"),
        ("team_code_duration_mi", "Team-code/duration MI"),
        ("team_code_edit_mi", "Team-code/edit MI"),
        ("process_posterior_acc", "Process posterior acc"),
        ("process_mi_estimate_mean", "Process MI estimate"),
        ("process_residual_mi_mean", "Residual MI estimate"),
        ("process_shortcut_max_acc", "Max shortcut acc"),
        ("process_shortcut_context_loss", "Context shortcut loss"),
        ("process_shortcut_margin_loss", "Shortcut margin loss"),
        ("process_reward_warmup_active", "Process reward warmup"),
        ("semantic_shortcut_hard_stop_triggered", "Semantic shortcut stop"),
        ("semantic_shortcut_hard_stop_score", "Semantic stop score"),
        ("transition_skill_acc", "Transition skill acc"),
        ("transition_skill_context_acc", "Transition context acc"),
        ("transition_skill_mi_mean", "Transition skill MI"),
        ("transition_skill_residual_mi_mean", "Transition residual MI"),
        ("transition_skill_reward_mean", "Transition skill reward"),
        ("transition_skill_reward_active", "Transition reward active"),
        ("transition_skill_samples", "Transition samples"),
        ("team_transition_mi_mean", "Team transition MI"),
        ("team_transition_mi_on_self", "Team transition MI self"),
        ("team_transition_mi_on_change", "Team transition MI change"),
        ("team_transition_self_frac", "Team transition self frac"),
        ("team_transition_reward_high_mean", "Team transition reward"),
        ("team_transition_reward_env_ratio", "Team transition/env ratio"),
        ("team_transition_reward_renewal_corr", "Team transition/renew corr"),
        ("team_intent_enabled", "Team intent enabled"),
        ("z_usage_entropy", "Z usage entropy"),
        ("z_dwell", "Z dwell checks"),
        ("z_decisions_per_update", "Z decisions/update"),
        ("z_advantage_mean", "Z advantage mean"),
        ("z_advantage_std", "Z advantage std"),
        ("z_boundary_trunc_rate", "Z boundary trunc rate"),
        ("z_assignment_itv", "Z assignment intervention KL"),
        ("team_disc_acc", "Team disc acc"),
        ("team_disc_residual_mean", "Team disc residual"),
        ("team_disc_reward_mean", "Team disc reward"),
        ("team_disc_reward_env_ratio", "Team disc/env ratio"),
        ("r24_qd_acc_full", "R24 q_d full acc"),
        ("r24_qd_acc_prior", "R24 q_d prior acc"),
        ("r24_qd_acc_behavior", "R24 q_d behavior-only acc"),
        ("r24_qd_acc_pre", "R24 q_d pre-window acc"),
        ("r24_qd_residual_gain", "R24 q_d residual gain"),
        ("r24_qd_behavior_gain_over_prior", "R24 q_d behavior-prior gain"),
        ("r24_qd_pre_gain_over_prior", "R24 q_d pre-prior gain"),
        ("r24_qd_full_minus_behavior_acc", "R24 q_d full-behavior acc"),
        ("r24_qd_full_minus_pre_acc", "R24 q_d full-pre acc"),
        ("r24_qd_residual_mean", "R24 q_d residual"),
        ("r24_qd_positive_frac", "R24 q_d positive frac"),
        ("r24_qd_shuffle_acc_gap", "R24 q_d shuffled acc gap"),
        ("r24_qd_fake_acc_gap", "R24 q_d fake acc gap"),
        ("r24_qd_pre_valid_frac", "R24 q_d pre valid frac"),
        ("r24_qd_samples", "R24 q_d samples"),
        ("combined_intrinsic_env_ratio", "Combined intrinsic/env ratio"),
        ("intrinsic_segment_high_gate_active", "High intrinsic gate active"),
        ("intrinsic_segment_high_gate_score", "High intrinsic gate score"),
        ("intrinsic_segment_high_gate_posterior_minus_shortcut", "High gate posterior gap"),
        ("posterior_acc_minus_shortcut_max", "Posterior - shortcut"),
        ("process_mi_positive_frac", "Process MI positive frac"),
        ("process_residual_mi_positive_frac", "Residual MI positive frac"),
        ("high_smdp_discount_mean", "SMDP discount mean"),
        ("high_bootstrap_contribution_mean", "Bootstrap contribution"),
        ("high_value_norm_std", "High value norm std"),
        ("g_intervention_kl_mean", "g intervention KL"),
        ("g_intervention_tv_mean", "g intervention TV"),
        ("g_info_skill_mi", "g decision skill MI"),
        ("g_info_duration_mi", "g decision duration MI"),
        ("g_itv_tv_skill", "g skill TV"),
        ("g_itv_tv_duration", "g duration TV"),
        ("g_joint_assignment_distance", "g joint assignment distance"),
        ("situation_enabled", "Situation diagnostics enabled"),
        ("situation_change_rate", "Situation change rate"),
        ("situation_unique_kappa", "Unique kappa"),
        ("situation_segment_change_frac", "Segment change frac"),
        ("situation_agent_kappa_change_rate", "Agent kappa change rate"),
        ("situation_agent_kappa_disagreement_rate", "Agent/global disagreement"),
        ("situation_agent_kappa_median_dwell", "Agent kappa dwell"),
        ("situation_agent_kappa_global_mi", "Agent/global kappa MI"),
        ("situation_agent_unique_kappa_mean", "Unique agent kappa"),
        ("situation_hazard_control_enabled", "Situation hazard enabled"),
        ("situation_hazard_forced_renewal_rate", "Situation forced renewal rate"),
        ("situation_hazard_mode_code", "Situation hazard mode"),
        ("situation_hazard_conservative_guard", "Conservative guard enabled"),
        ("situation_hazard_guard_allow_rate", "Guard allow rate"),
        ("situation_hazard_guard_confirm_block_rate", "Guard confirm block"),
        ("situation_hazard_guard_dwell_block_rate", "Guard dwell block"),
        ("situation_hazard_guard_rate_cap_block_rate", "Guard rate-cap block"),
        ("situation_hazard_guard_no_change_block_rate", "Guard no-change block"),
        ("situation_hazard_guard_recent_force_rate", "Guard recent force rate"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Process Segment Diagnostics", xlabel="Env steps")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "ha_ctse_process_diagnostics.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("proto_disc_active", "Prototype disc active"),
        ("proto_disc_samples", "Prototype disc samples"),
        ("proto_disc_acc", "Prototype disc acc"),
        ("proto_disc_prior_acc", "Prototype prior acc"),
        ("proto_disc_null_logp_mean", "Prototype null logp"),
        ("proto_assignment_logp_mean", "Prototype assignment logp mean"),
        ("proto_assignment_logp_std", "Prototype assignment logp std"),
        ("proto_ar_parallel_kl", "Prototype AR vs parallel KL"),
        ("roster_ar_kl_zeroed", "Roster AR vs zeroed KL"),
        ("roster_ar_kl_shuffled", "Roster AR vs shuffled KL"),
        ("selection_independence_deficit", "Selection independence deficit"),
        ("proto_disc_residual_mean", "Prototype residual"),
        ("proto_disc_residual_positive_frac", "Prototype residual positive"),
        ("proto_disc_reward_mean", "Prototype reward"),
        ("proto_disc_reward_applied_steps", "Prototype reward steps"),
        ("proto_skill_selection_entropy", "Prototype skill entropy"),
        ("proto_skill_usage_entropy_by_kappa", "Skill entropy by kappa"),
        ("proto_skill_relevance_alignment", "Skill/relevance MI"),
        ("proto_skill_selected_relevance_mean", "Selected relevance mean"),
        ("proto_omega_nonzero_frac", "Omega nonzero frac"),
        ("proto_bank_drift_cos", "Prototype EMA cosine"),
        ("proto_rel_row_entropy_mean", "Rel row entropy"),
        ("proto_rel_argmax_dwell_median", "Rel argmax dwell"),
        ("proto_rel_stability_cos", "Rel stability cosine"),
        ("proto_rel_drop_event_rate_05", "Rel drop <0.5"),
        ("proto_rel_drop_event_rate_03", "Rel drop <0.3"),
        ("proto_rel_drop_event_rate_01", "Rel drop <0.1"),
        ("compact_return_loss", "Compact return loss"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="R14 Prototype-Response Diagnostics", xlabel="Env steps")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "ha_ctse_r14_prototype_diagnostics.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("outcome_residual_gain_mean", "Residual gain mean"),
        ("outcome_residual_gain_positive_frac", "Gain positive frac"),
        ("outcome_residual_available_mean", "Target available"),
        ("outcome_residual_skill_gain_std", "Gain by skill std"),
        ("outcome_residual_team_gain_std", "Gain by team std"),
        ("outcome_residual_duration_gain_std", "Gain by duration std"),
        ("outcome_residual_reward_mean", "Injected reward mean"),
        ("outcome_residual_reward_active", "Reward active"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Future Cooperation Outcome Residual Probe", xlabel="Env steps")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "ha_ctse_outcome_residual.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("outcome_residual_gain_coverage_delta_h", "Coverage"),
        ("outcome_residual_gain_qos_delta_h", "QoS"),
        ("outcome_residual_gain_full_disconnect_improvement_h", "Full disconnect"),
        ("outcome_residual_gain_relay_margin_delta_h", "Relay margin"),
        ("outcome_residual_gain_connected_components_improvement_h", "Components"),
        ("outcome_residual_gain_teammate_service_gain_h", "Teammate service"),
        ("outcome_residual_gain_bottleneck_link_gain_h", "Bottleneck link"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Outcome Residual Field Gains", xlabel="Env steps")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "ha_ctse_outcome_residual_fields.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("topology_role_available_frac", "Available frac"),
        ("topology_role_acc", "Full role acc"),
        ("topology_role_shortcut_acc", "Shortcut acc"),
        ("topology_role_resid_gain_mean", "Residual gain"),
        ("topology_role_resid_gain_positive_frac", "Gain positive frac"),
        ("topology_role_z_mi", "z/role MI"),
        ("topology_role_g_mi", "g/role MI"),
        ("topology_role_reward_mean", "Injected reward"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Topology Role Residual Probe", xlabel="Env steps")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "ha_ctse_topology_role_probe.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("topology_role_frac_idle", "Idle"),
        ("topology_role_frac_relay", "Relay"),
        ("topology_role_frac_service", "Service"),
        ("topology_role_frac_relay_service", "Relay service"),
        ("topology_cf_backhaul_mean_mean", "CF backhaul"),
        ("topology_cf_components_mean_mean", "CF components"),
        ("topology_cf_disconnect_mean_mean", "CF disconnect"),
        ("topology_service_mean_mean", "Service"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Topology Role Labels and Counterfactuals", xlabel="Env steps")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "ha_ctse_topology_role_fields.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("topology_potential_raw_mean", "Raw potential delta"),
        ("topology_potential_reward_mean", "Injected reward"),
        ("topology_potential_phi_start_mean", "Phi start"),
        ("topology_potential_phi_end_mean", "Phi end"),
        ("topology_potential_backhaul_up_start_mean", "Backhaul up start"),
        ("topology_potential_backhaul_up_end_mean", "Backhaul up end"),
        ("topology_potential_full_disconnect_start_mean", "Disconnect start"),
        ("topology_potential_full_disconnect_end_mean", "Disconnect end"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Topology Potential Credit Shaping", xlabel="Env steps")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "ha_ctse_topology_potential.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("effect_windows", "Micro-windows"),
        ("effect_loss_full", "Full loss"),
        ("effect_loss_base", "Context baseline loss"),
        ("effect_gain_mean", "Full - context gain"),
        ("effect_gain_group_balanced_mean", "Group-balanced gain"),
        ("effect_gain_nonmotion", "Non-motion gain"),
        ("effect_gain_positive_frac", "Positive gain frac"),
        ("effect_gain_minus_duration_baseline", "Full - duration"),
        ("effect_gain_minus_reward_baseline", "Full - reward"),
        ("effect_reward_low_mean", "Injected low reward"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Skill Effect Discovery Probe", xlabel="Env steps")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "ha_ctse_skill_effect_probe.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("effect_gain_motion", "Motion gain"),
        ("effect_gain_service", "Service gain"),
        ("effect_gain_energy", "Energy gain"),
        ("effect_gain_topology", "Topology gain"),
        ("effect_target_available_frac", "Target available"),
        ("effect_reward_applied_steps", "Reward-applied steps"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Skill Effect Fields and Reward-Off Guard", xlabel="Env steps")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "ha_ctse_skill_effect_fields.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("force_reward_low_mean", "Injected low reward"),
        ("force_reward_applied_steps", "Reward-applied steps"),
        ("force_disc_acc", "Residual disc acc"),
        ("force_shortcut_best_acc", "Best shortcut acc"),
        ("force_shortcut_margin", "Disc - shortcut acc"),
        ("force_disc_residual_mean", "Disc residual"),
        ("force_effect_residual_mean", "Effect residual"),
        ("force_gate_active", "Gate active"),
        ("force_gate_reason", "Gate reason"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Skill Forcing Reward Gate", xlabel="Env steps")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "ha_ctse_skill_forcing_reward.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("effect_gain_horizon_0", "Horizon 0 gain"),
        ("effect_gain_horizon_1", "Horizon 1 gain"),
        ("effect_gain_horizon_2", "Horizon 2 gain"),
        ("effect_gain_horizon_3", "Horizon 3 gain"),
        ("effect_action_skill_eta2", "Action~skill eta2"),
        ("effect_target_skill_eta2", "Target~skill eta2"),
        ("effect_skill_usage_entropy", "Skill usage entropy"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Skill Effect P3-2b Diagnostics", xlabel="Env steps")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "ha_ctse_skill_effect_p3_2b.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("effect_intervention_active", "Intervention active"),
        ("effect_intervention_samples", "Samples"),
        ("effect_intervention_action_l2_mean", "Action L2 mean"),
        ("effect_intervention_action_l2_max", "Action L2 max"),
        ("effect_intervention_pred_effect_l2_mean", "Pred-effect L2 mean"),
        ("effect_intervention_pred_effect_l2_max", "Pred-effect L2 max"),
        ("effect_intervention_best_skill_gap", "Best skill gap"),
        ("effect_intervention_low_entropy_mean", "Low entropy"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Skill Effect P3-2c Forced-z Intervention Audit", xlabel="Env steps")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "ha_ctse_skill_effect_p3_2c_intervention.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("effect_observed_target_skill_l2_mean", "Observed target skill L2"),
        ("effect_observed_target_skill_l2_nonmotion", "Observed non-motion skill L2"),
        ("effect_observed_action_skill_l2_mean", "Observed action skill L2"),
        ("effect_observed_action_target_corr", "Action-target corr"),
        ("effect_endstate_available_frac", "End-state target available"),
        ("effect_window_mean_available_frac", "Window-mean target available"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Skill Effect P3-2d Observed Effect Audit", xlabel="Env steps")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "ha_ctse_skill_effect_p3_2d_observed.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("credit_full_disconnect_mean", "Full disconnect mean"),
        ("credit_recovery_rate", "Disconnect recovery rate"),
        ("credit_collapse_rate", "Connectivity collapse rate"),
        ("credit_backhaul_connected_step_fraction", "Backhaul connected step fraction"),
        ("credit_throughput_when_backhaul_connected_mbps", "Throughput | backhaul up"),
        ("credit_delta_connectivity_ratio_mean", "Delta connectivity ratio"),
        ("credit_delta_backhaul_served_users_mean", "Delta backhaul served users"),
        ("credit_delta_backhaul_outage_ratio_mean", "Delta backhaul outage ratio"),
        ("credit_delta_relay_route_loss_ratio_mean", "Delta relay route loss"),
        ("credit_bottleneck_mbps_mean", "Backhaul bottleneck Mbps"),
        ("credit_reward_conn_corr", "Reward/cxn corr"),
        ("credit_reward_served_corr", "Reward/served corr"),
        ("credit_reward_outage_corr", "Reward/outage corr"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Cooperation Credit Diagnostics", xlabel="Env steps")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "ha_ctse_cooperation_credit.png", dpi=180)
    plt.close(fig)


def save_eval_plots(log_dir: str | Path, window: int = 5) -> None:
    if plt is None:
        return
    log_dir = Path(log_dir)
    records = read_csv_records(log_dir / "metrics" / "eval_episodes.csv")
    if not records:
        return

    fig, ax = plt.subplots(figsize=(12, 6))
    x, reward = _series(records, "reward")
    if reward.size:
        ax.plot(x, reward, color="steelblue", alpha=0.35, linewidth=0.9, label="Episode reward")
        ax.plot(x, moving_average(reward, window), color="black", linewidth=2.0, label="Moving average")
    ax.set(title="Eval Reward", xlabel="Env steps", ylabel="Reward")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "eval_reward.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("coverage_ratio", "Coverage"),
        ("qos_satisfaction_ratio", "QoS satisfaction"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Eval Service Quality", xlabel="Env steps", ylabel="Ratio")
    ax.set_ylim(bottom=0.0)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left")
    ax2 = ax.twinx()
    x, y = _series(records, "system_throughput_mbps")
    if y.size:
        ax2.plot(x, moving_average(y, window), color="purple", label="Throughput Mbps")
        ax2.set_ylabel("Mbps")
    x, y = _series(records, "throughput_when_backhaul_connected_mbps")
    if y.size:
        ax2.plot(
            x,
            moving_average(y, window),
            color="darkorange",
            linestyle="--",
            label="Throughput | backhaul up",
        )
        ax2.set_ylabel("Mbps")
    if ax2.lines:
        ax2.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(log_dir / "eval_service_quality.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    any_series = False
    for key, label in (
        ("coverage_eq1_step_fraction", "Coverage == 1 step fraction"),
        ("coverage_positive_step_fraction", "Coverage > 0 step fraction"),
        ("throughput_gt5_step_fraction", "Throughput > 5 Mbps step fraction"),
        ("zero_throughput_step_fraction", "Zero-throughput step fraction"),
    ):
        x, y = _series(records, key)
        if y.size:
            any_series = True
            ax.plot(x, moving_average(y, window), label=label)
    if any_series:
        ax.set(title="Eval Success Fractions", xlabel="Env steps", ylabel="Fraction")
        ax.set_ylim(bottom=0.0, top=1.02)
        ax.grid(True, alpha=0.3)
        ax.legend(loc="upper left")
        fig.tight_layout()
        fig.savefig(log_dir / "eval_success_fractions.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for key, label in (
        ("battery_min_ratio", "Min battery"),
        ("battery_mean_ratio", "Mean battery"),
        ("return_violation_fraction", "Return violation"),
    ):
        x, y = _series(records, key)
        if y.size:
            ax.plot(x, moving_average(y, window), label=label)
    ax.set(title="Eval Safety and Energy", xlabel="Env steps", ylabel="Ratio / fraction")
    ax.set_ylim(bottom=0.0)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(log_dir / "eval_safety_energy.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    any_series = False
    for key, label in (
        ("episode_charging_session_count", "Charging sessions"),
        ("effective_charging_session_count", "Effective charging sessions"),
        ("episode_energy_charged_wh", "Energy charged Wh"),
    ):
        x, y = _series(records, key)
        if y.size:
            any_series = True
            ax.plot(x, moving_average(y, window), label=label)
    if any_series:
        ax.set(title="Eval Charging Progress", xlabel="Env steps")
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()
        fig.savefig(log_dir / "eval_charging_progress.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    any_series = False
    for key, label in (
        ("avg_hops", "Average hops"),
        ("connectivity_ratio", "Connectivity ratio"),
        ("connected_uavs", "Connected UAVs"),
        ("uavs_with_backhaul", "UAVs with backhaul"),
        ("total_connected_users", "Access-connected users"),
        ("effective_connected_users", "Effectively served users"),
    ):
        x, y = _series(records, key)
        if y.size:
            any_series = True
            ax.plot(x, moving_average(y, window), label=label)
    if any_series:
        ax.set(title="Eval Communication Topology", xlabel="Env steps")
        ax.set_ylim(bottom=0.0)
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()
        fig.savefig(log_dir / "eval_communication_topology.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    any_series = False
    for key, label in (
        ("relay_route_loss_ratio", "Relay route loss ratio"),
        ("relay_route_loss_prev_served_ratio", "Loss / previous served"),
        ("backhaul_outage_ratio", "Backhaul outage ratio"),
        ("service_drop_ratio", "Service drop ratio"),
        ("backhaul_drop_ratio", "Backhaul drop ratio"),
        ("coverage_drop_ratio", "Coverage drop ratio"),
        ("full_network_disconnect", "Full disconnect flag"),
        ("backhaul_connected_step_fraction", "Backhaul connected step fraction"),
        ("backhaul_connected_flag", "Final backhaul connected flag"),
    ):
        x, y = _series(records, key)
        if y.size:
            any_series = True
            ax.plot(x, moving_average(y, window), label=label)
    if any_series:
        ax.set(title="Eval Backhaul Robustness", xlabel="Env steps", ylabel="Ratio / flag")
        ax.set_ylim(bottom=0.0)
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()
        fig.savefig(log_dir / "eval_backhaul_robustness.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    any_left = False
    for key, label in (
        ("min_serving_backhaul_bottleneck_mbps", "Min serving bottleneck Mbps"),
        ("avg_serving_backhaul_bottleneck_mbps", "Avg serving bottleneck Mbps"),
    ):
        x, y = _series(records, key)
        if y.size:
            any_left = True
            ax.plot(x, moving_average(y, window), label=label)
    ax2 = ax.twinx()
    any_right = False
    for key, label in (
        ("backhaul_margin_penalty_raw", "Margin penalty raw"),
        ("backhaul_guard_checked_actions", "Guard checked actions"),
        ("backhaul_guard_blocked_actions", "Guard blocked actions"),
        ("routing_overhead", "Routing overhead"),
    ):
        x, y = _series(records, key)
        if y.size:
            any_right = True
            ax2.plot(x, moving_average(y, window), linestyle="--", label=label)
    if any_left or any_right:
        ax.set(title="Eval Backhaul Capacity and Guard", xlabel="Env steps")
        ax.set_ylabel("Mbps")
        ax2.set_ylabel("Penalty / count")
        ax.set_ylim(bottom=0.0)
        ax.grid(True, alpha=0.3)
        if any_left:
            ax.legend(loc="upper left")
        if any_right:
            ax2.legend(loc="upper right")
        fig.tight_layout()
        fig.savefig(log_dir / "eval_backhaul_capacity_guard.png", dpi=180)
    plt.close(fig)


LOG_KEY_ALIASES = {
    "duration_only_acc": "duration_only_accuracy",
    "length_only_acc": "length_only_accuracy",
    "reward_sum_only_acc": "reward_sum_only_accuracy",
    "posterior_gap_dur": "posterior_acc_minus_duration_only",
    "posterior_gap_len": "posterior_acc_minus_length_only",
    "posterior_gap_rew": "posterior_acc_minus_reward_sum_only",
    "switch_rate": "skill_switch_rate",
    "seg_len_mean": "segment_length_mean",
    "process_mi": "process_mi_estimate_mean",
    "process_resid_mi": "process_residual_mi_mean",
    "process_shortcut_acc": "process_shortcut_max_acc",
    "process_margin_loss": "process_shortcut_margin_loss",
    "process_warmup": "process_reward_warmup_active",
    "trans_samples": "transition_skill_samples",
    "trans_acc": "transition_skill_acc",
    "trans_ctx_acc": "transition_skill_context_acc",
    "trans_mi": "transition_skill_mi_mean",
    "trans_resid_mi": "transition_skill_residual_mi_mean",
    "trans_reward": "transition_skill_reward_mean",
    "trans_active": "transition_skill_reward_active",
    "proto_acc": "proto_disc_acc",
    "proto_prior_acc": "proto_disc_prior_acc",
    "proto_null": "proto_disc_null_logp_mean",
    "proto_ar_kl": "proto_ar_parallel_kl",
    "roster_kl_shuf": "roster_ar_kl_shuffled",
    "sel_def": "selection_independence_deficit",
    "proto_resid": "proto_disc_residual_mean",
    "proto_reward": "proto_disc_reward_mean",
    "proto_steps": "proto_disc_reward_applied_steps",
    "combined_intr_ratio": "combined_intrinsic_env_ratio",
    "combined_intr_guard": "combined_intrinsic_env_ratio_guard_active",
    "combined_intr_o05": "combined_intrinsic_env_ratio_over05_count",
    "combined_intr_kill": "combined_intrinsic_env_ratio_kill_triggered",
    "proto_skill_ent": "proto_skill_selection_entropy",
    "proto_kappa_ent": "proto_skill_usage_entropy_by_kappa",
    "proto_align": "proto_skill_relevance_alignment",
    "proto_rel_dwell": "proto_rel_argmax_dwell_median",
    "proto_rel_stab": "proto_rel_stability_cos",
    "out_full_loss": "outcome_residual_full_loss",
    "out_base_loss": "outcome_residual_base_loss",
    "out_gain": "outcome_residual_gain_mean",
    "out_pos": "outcome_residual_gain_positive_frac",
    "out_active": "outcome_residual_reward_active",
    "role_avail": "topology_role_available_frac",
    "role_acc": "topology_role_acc",
    "role_ctx_acc": "topology_role_shortcut_acc",
    "role_gain": "topology_role_resid_gain_mean",
    "role_pos": "topology_role_resid_gain_positive_frac",
    "role_z_mi": "topology_role_z_mi",
    "effect_gain": "effect_gain_mean",
    "effect_gbal": "effect_gain_group_balanced_mean",
    "effect_nonmotion": "effect_gain_nonmotion",
    "effect_pos": "effect_gain_positive_frac",
    "effect_motion": "effect_gain_motion",
    "effect_service": "effect_gain_service",
    "effect_energy": "effect_gain_energy",
    "effect_topology": "effect_gain_topology",
    "effect_h0": "effect_gain_horizon_0",
    "effect_h1": "effect_gain_horizon_1",
    "effect_h2": "effect_gain_horizon_2",
    "effect_act_eta": "effect_action_skill_eta2",
    "effect_tgt_eta": "effect_target_skill_eta2",
    "effect_obs_tgt_l2": "effect_observed_target_skill_l2_mean",
    "effect_obs_nm_l2": "effect_observed_target_skill_l2_nonmotion",
    "effect_act_tgt_corr": "effect_observed_action_target_corr",
    "effect_gap_dur": "effect_gain_minus_duration_baseline",
    "effect_gap_rew": "effect_gain_minus_reward_baseline",
    "effect_low_rew": "effect_reward_low_mean",
    "effect_steps": "effect_reward_applied_steps",
    "force_rew": "force_reward_low_mean",
    "force_steps": "force_reward_applied_steps",
    "force_disc_acc": "force_disc_acc",
    "force_resid": "force_disc_residual_mean",
    "force_eff_resid": "force_effect_residual_mean",
    "force_shortcut_acc": "force_shortcut_best_acc",
    "force_margin": "force_shortcut_margin",
    "force_gate": "force_gate_active",
    "force_reason": "force_gate_reason",
    "high_intr_gate": "intrinsic_segment_high_gate_active",
    "high_intr_score": "intrinsic_segment_high_gate_score",
    "high_intr_reason": "intrinsic_segment_high_gate_reason_code",
    "posterior_gap_short": "posterior_acc_minus_shortcut_max",
    "posterior_gap_ctx": "posterior_acc_minus_context_shortcut",
    "posterior_acc": "process_posterior_acc",
    "ctx_short_acc": "process_shortcut_context_acc",
    "process_reward_raw": "process_reward_unclipped_mean",
    "process_mi_reward": "process_reward_mi_component_mean",
    "process_reward_high": "process_reward_high_mean",
    "process_reward_low": "process_reward_low_mean",
    "semantic_stop": "semantic_shortcut_hard_stop_triggered",
    "semantic_stop_apply": "semantic_shortcut_hard_stop_applied",
    "semantic_stop_score": "semantic_shortcut_hard_stop_score",
    "high_env_return": "high_env_return_mean",
    "high_bootstrap": "high_bootstrap_value_mean",
    "high_bootstrap_contrib": "high_bootstrap_contribution_mean",
    "high_vnorm_mean": "high_value_norm_mean",
    "high_vnorm_std": "high_value_norm_std",
    "skill_entropy": "skill_usage_entropy",
    "duration_entropy": "duration_usage_entropy",
    "duration_policy_entropy": "duration_policy_entropy",
    "duration_policy_entropy_norm": "duration_policy_entropy_norm",
    "dur_ent_floor": "duration_entropy_floor_active",
    "dur_ent_floor_gap": "duration_entropy_floor_gap",
    "dur_ent_floor_loss": "duration_entropy_floor_loss",
    "z_decisions": "z_decisions_per_update",
    "z_adv_mean": "z_advantage_mean",
    "z_adv_std": "z_advantage_std",
    "life_hetero": "lifetime_heterogeneity",
    "dur_agent_mi": "duration_agent_mi",
    "dur_ret_rng": "duration_return_range",
    "dur_disc_rng": "duration_full_disconnect_range",
    "dur_rec_rng": "duration_recovery_range",
    "dur_bh_rng": "duration_bh_frac_range",
    "renew_sync": "renewal_full_sync_rate",
    "renew_corr": "renewal_pairwise_corr_mean",
    "g_entropy": "team_code_usage_entropy",
    "g_skill_mi": "team_code_skill_mi",
    "g_ikl": "g_intervention_kl_mean",
    "g_itv": "g_intervention_tv_mean",
    "low_chunks": "low_sequence_chunks",
    "low_vnorm_mean": "low_value_norm_mean",
    "low_vnorm_std": "low_value_norm_std",
    "low_verr": "low_value_error_abs_mean",
    "low_vrmse": "low_value_error_rmse",
    "low_adv_std": "low_advantage_std",
    "low_ratio": "low_ratio_mean",
    "low_clip": "low_clip_frac",
    "low_kl": "low_approx_kl",
    "low_agn": "low_actor_grad_norm",
    "low_cgn": "low_critic_grad_norm",
    "low_ahn": "low_actor_h_norm_mean",
    "low_chn": "low_critic_h_norm_mean",
    "low_sent": "low_skill_usage_entropy",
    "low_sret_std": "low_skill_return_std",
    "low_sret_rng": "low_skill_return_range",
    "low_sverr_std": "low_skill_value_error_abs_std",
    "low_sent_std": "low_skill_entropy_std",
    "low_tent": "low_team_usage_entropy",
    "low_tret_std": "low_team_return_std",
    "low_tret_rng": "low_team_return_range",
    "low_tverr_std": "low_team_value_error_abs_std",
    "credit_disc": "credit_full_disconnect_mean",
    "credit_recover": "credit_recovery_rate",
    "credit_collapse": "credit_collapse_rate",
    "credit_bh_frac": "credit_backhaul_connected_step_fraction",
    "credit_bh_thr": "credit_throughput_when_backhaul_connected_mbps",
    "credit_d_conn": "credit_delta_connectivity_ratio_mean",
    "credit_d_served": "credit_delta_backhaul_served_users_mean",
    "credit_d_outage": "credit_delta_backhaul_outage_ratio_mean",
    "credit_d_relay_loss": "credit_delta_relay_route_loss_ratio_mean",
}


def parse_standalone_train_log(log_dir: str | Path) -> list[dict[str, float]]:
    log_dir = Path(log_dir)
    log_path = log_dir / "standalone_train.log"
    if not log_path.exists():
        return []
    rows: list[dict[str, float]] = []
    pattern = re.compile(r"([A-Za-z0-9_]+)=(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)")
    for line in log_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "standalone_update" not in line:
            continue
        row: dict[str, float] = {}
        for key, value in pattern.findall(line):
            key = LOG_KEY_ALIASES.get(key, key)
            try:
                row[key] = float(value)
            except ValueError:
                continue
        if "update" in row and "total_steps" in row:
            rows.append(row)
    if rows:
        csv_path = log_dir / "metrics" / "train_updates.csv"
        merged: dict[tuple[int, int], dict[str, Any]] = {}
        if csv_path.exists():
            with csv_path.open("r", newline="", encoding="utf-8") as handle:
                for existing in csv.DictReader(handle):
                    try:
                        key = (
                            int(float(existing.get("update", ""))),
                            int(float(existing.get("total_steps", ""))),
                        )
                    except ValueError:
                        continue
                    merged[key] = dict(existing)
        for row in rows:
            key = (int(row["update"]), int(row["total_steps"]))
            merged.setdefault(key, {}).update(row)
        ordered = [
            merged[key]
            for key in sorted(merged, key=lambda item: (item[0], item[1]))
        ]
        write_csv(csv_path, ordered, UPDATE_FIELDS)
        save_update_plots(log_dir)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate standalone HA-CTSE plots from metrics/log files.")
    parser.add_argument("--log_dir", required=True)
    parser.add_argument("--from_log", action="store_true")
    parser.add_argument("--window", type=int, default=5)
    args = parser.parse_args()
    if args.from_log:
        rows = parse_standalone_train_log(args.log_dir)
        print(f"parsed_updates={len(rows)} log_dir={args.log_dir}")
    save_update_plots(args.log_dir, window=args.window)
    save_eval_plots(args.log_dir, window=args.window)


if __name__ == "__main__":
    main()
