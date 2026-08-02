"""Metric writer helpers for the HA-CTSE process core."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from ha_ctse_process.metrics_io import append_csv
from ha_ctse_process.plotting import R37_IDENTITY_METRIC_FIELDS, UPDATE_FIELDS, save_update_plots
from ha_ctse_process.team_conditioned_qd import TEAM_CONDITIONED_QD_METRIC_FIELDS


def log_train_metrics(writer, total_steps: int, episode_rewards, process_metrics, low_metrics) -> None:
    if writer is None:
        return
    env_reward_mean = float(np.mean(episode_rewards)) if episode_rewards else 0.0
    writer.add_scalar("Train/EnvRewardMean", env_reward_mean, total_steps)
    writer.add_scalar("Process/Segments", process_metrics["process_segments"], total_steps)
    writer.add_scalar("Process/Loss", process_metrics["process_loss"], total_steps)
    writer.add_scalar("Process/OutcomeLoss", process_metrics.get("process_outcome_loss", 0.0), total_steps)
    writer.add_scalar("Process/ContrastiveLoss", process_metrics.get("process_contrastive_loss", 0.0), total_steps)
    writer.add_scalar("Process/PriorLoss", process_metrics.get("process_prior_loss", 0.0), total_steps)
    writer.add_scalar("Process/PosteriorAcc", process_metrics.get("process_posterior_acc", 0.0), total_steps)
    writer.add_scalar("Process/MIEstimateMean", process_metrics.get("process_mi_estimate_mean", 0.0), total_steps)
    writer.add_scalar("Process/ResidualMIMean", process_metrics.get("process_residual_mi_mean", 0.0), total_steps)
    writer.add_scalar(
        "Process/ResidualMIPositiveFrac",
        process_metrics.get("process_residual_mi_positive_frac", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Process/ResidualLogShortcutMean",
        process_metrics.get("process_residual_log_shortcut_mean", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Process/ResidualLogContextMean",
        process_metrics.get("process_residual_log_context_mean", 0.0),
        total_steps,
    )
    writer.add_scalar("Process/LogQMean", process_metrics.get("process_log_q_mean", 0.0), total_steps)
    writer.add_scalar("Process/LogPMean", process_metrics.get("process_log_p_mean", 0.0), total_steps)
    writer.add_scalar("Process/ShortcutLoss", process_metrics.get("process_shortcut_loss", 0.0), total_steps)
    writer.add_scalar("Process/ShortcutMarginLoss", process_metrics.get("process_shortcut_margin_loss", 0.0), total_steps)
    writer.add_scalar("Process/RewardWarmupActive", process_metrics.get("process_reward_warmup_active", 0.0), total_steps)
    writer.add_scalar("TransitionSkill/Samples", process_metrics.get("transition_skill_samples", 0.0), total_steps)
    writer.add_scalar(
        "TransitionSkill/AvailableSamples",
        process_metrics.get("transition_skill_available_samples", 0.0),
        total_steps,
    )
    writer.add_scalar("TransitionSkill/Loss", process_metrics.get("transition_skill_loss", 0.0), total_steps)
    writer.add_scalar(
        "TransitionSkill/PriorLoss",
        process_metrics.get("transition_skill_prior_loss", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "TransitionSkill/ContextLoss",
        process_metrics.get("transition_skill_context_loss", 0.0),
        total_steps,
    )
    writer.add_scalar("TransitionSkill/Acc", process_metrics.get("transition_skill_acc", 0.0), total_steps)
    writer.add_scalar(
        "TransitionSkill/ContextAcc",
        process_metrics.get("transition_skill_context_acc", 0.0),
        total_steps,
    )
    writer.add_scalar("TransitionSkill/MIMean", process_metrics.get("transition_skill_mi_mean", 0.0), total_steps)
    writer.add_scalar(
        "TransitionSkill/MIPositiveFrac",
        process_metrics.get("transition_skill_mi_positive_frac", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "TransitionSkill/ResidualMIMean",
        process_metrics.get("transition_skill_residual_mi_mean", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "TransitionSkill/ResidualMIPositiveFrac",
        process_metrics.get("transition_skill_residual_mi_positive_frac", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "TransitionSkill/RewardMean",
        process_metrics.get("transition_skill_reward_mean", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "TransitionSkill/RewardActive",
        process_metrics.get("transition_skill_reward_active", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "TransitionSkill/RewardUnclippedMean",
        process_metrics.get("transition_skill_reward_unclipped_mean", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "TransitionSkill/RewardWarmupActive",
        process_metrics.get("transition_skill_reward_warmup_active", 0.0),
        total_steps,
    )
    writer.add_scalar("TransitionSkill/LogQMean", process_metrics.get("transition_skill_log_q_mean", 0.0), total_steps)
    writer.add_scalar("TransitionSkill/LogPMean", process_metrics.get("transition_skill_log_p_mean", 0.0), total_steps)
    writer.add_scalar(
        "TransitionSkill/LogContextMean",
        process_metrics.get("transition_skill_log_context_mean", 0.0),
        total_steps,
    )
    for key in (
        "team_transition_active",
        "team_transition_samples",
        "team_transition_loss",
        "team_transition_prior_loss",
        "team_transition_mi_mean",
        "team_transition_mi_on_self",
        "team_transition_mi_on_change",
        "team_transition_self_frac",
        "team_transition_missing_frac",
        "team_transition_reward_high_mean",
        "team_transition_reward_applied_steps",
        "team_transition_reward_env_ratio",
        "team_transition_reward_renewal_corr",
    ):
        writer.add_scalar(f"TeamTransition/{key}", process_metrics.get(key, 0.0), total_steps)
    for key in (
        "team_intent_enabled",
        "z_usage_entropy",
        "z_usage_max_frac",
        "z_dwell",
        "z_age_check_mean",
        "z_boundary_count",
        "z_decisions_per_update",
        "z_boundary_trunc_rate",
        "z_boundary_trunc_rate_dur3",
        "z_boundary_trunc_rate_dur7",
        "z_boundary_trunc_rate_dur13",
        "z_boundary_trunc_rate_dur24",
        "z_advantage_mean",
        "z_advantage_std",
        "z_advantage_var",
        "z_assignment_itv",
        "z_entropy_floor_active",
        "z_entropy_floor_gap",
        "z_entropy_floor_loss",
        "z_entropy_floor_coef_active",
        "z_policy_entropy",
        "z_policy_entropy_norm",
    ):
        writer.add_scalar(f"TeamIntent/{key}", process_metrics.get(key, 0.0), total_steps)
    for key in (
        "team_disc_active",
        "team_disc_samples",
        "team_disc_loss",
        "team_disc_acc",
        "team_disc_prior_entropy",
        "team_disc_residual_mean",
        "team_disc_residual_positive_frac",
        "team_disc_reward_mean",
        "team_disc_reward_unclipped_mean",
        "team_disc_reward_applied_steps",
        "team_disc_reward_env_ratio",
        "team_disc_reward_env_ratio_over05_count",
        "team_disc_reward_env_ratio_guard_active",
        "team_disc_reward_env_ratio_kill_triggered",
        "combined_intrinsic_env_ratio",
        "combined_intrinsic_env_ratio_over05_count",
        "combined_intrinsic_env_ratio_guard_active",
        "combined_intrinsic_env_ratio_kill_triggered",
    ):
        writer.add_scalar(f"TeamDisc/{key}", process_metrics.get(key, 0.0), total_steps)
    for key in TEAM_CONDITIONED_QD_METRIC_FIELDS:
        writer.add_scalar(f"R24QD/{key}", process_metrics.get(key, 0.0), total_steps)
    for key in (
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
    ):
        writer.add_scalar(f"PrototypeDisc/{key}", process_metrics.get(key, 0.0), total_steps)
    for key in (
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
    ):
        writer.add_scalar(f"PrototypeSelection/{key}", process_metrics.get(key, 0.0), total_steps)
    writer.add_scalar(
        "Intrinsic/SegmentHighGateActive",
        process_metrics.get("intrinsic_segment_high_gate_active", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Intrinsic/SegmentHighGateScore",
        process_metrics.get("intrinsic_segment_high_gate_score", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Intrinsic/SegmentHighGatePosteriorMinusShortcut",
        process_metrics.get("intrinsic_segment_high_gate_posterior_minus_shortcut", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Intrinsic/SegmentHighGateReasonCode",
        process_metrics.get("intrinsic_segment_high_gate_reason_code", 0.0),
        total_steps,
    )
    writer.add_scalar("Process/ShortcutDurationAcc", process_metrics.get("process_shortcut_duration_acc", 0.0), total_steps)
    writer.add_scalar("Process/ShortcutLengthAcc", process_metrics.get("process_shortcut_length_acc", 0.0), total_steps)
    writer.add_scalar(
        "Process/ShortcutRewardSumAcc",
        process_metrics.get("process_shortcut_reward_sum_acc", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Process/ShortcutContextAcc",
        process_metrics.get("process_shortcut_context_acc", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Process/ShortcutContextLoss",
        process_metrics.get("process_shortcut_context_loss", 0.0),
        total_steps,
    )
    writer.add_scalar("Process/ShortcutMaxAcc", process_metrics.get("process_shortcut_max_acc", 0.0), total_steps)
    writer.add_scalar(
        "Process/PosteriorMinusShortcutMax",
        process_metrics.get("posterior_acc_minus_shortcut_max", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Process/PosteriorMinusContextShortcut",
        process_metrics.get("posterior_acc_minus_context_shortcut", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Process/RewardMIComponentMean",
        process_metrics.get("process_reward_mi_component_mean", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Process/RewardOutcomePenaltyMean",
        process_metrics.get("process_reward_outcome_penalty_mean", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Process/RewardUnclippedMean",
        process_metrics.get("process_reward_unclipped_mean", 0.0),
        total_steps,
    )
    writer.add_scalar("Process/MIPositiveFrac", process_metrics.get("process_mi_positive_frac", 0.0), total_steps)
    writer.add_scalar("Process/RewardMean", process_metrics["process_reward_mean"], total_steps)
    writer.add_scalar("Process/RewardHighMean", process_metrics.get("process_reward_high_mean", 0.0), total_steps)
    writer.add_scalar("Process/RewardLowMean", process_metrics.get("process_reward_low_mean", 0.0), total_steps)
    writer.add_scalar(
        "Process/SemanticShortcutHardStopTriggered",
        process_metrics.get("semantic_shortcut_hard_stop_triggered", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Process/SemanticShortcutHardStopApplied",
        process_metrics.get("semantic_shortcut_hard_stop_applied", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Process/SemanticShortcutHardStopScore",
        process_metrics.get("semantic_shortcut_hard_stop_score", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Process/SemanticShortcutHardStopReasonCode",
        process_metrics.get("semantic_shortcut_hard_stop_reason_code", 0.0),
        total_steps,
    )
    writer.add_scalar("Process/OutcomeAvailableMean", process_metrics["outcome_available_mean"], total_steps)
    writer.add_scalar("Process/OutcomeAbsMean", process_metrics["outcome_abs_mean"], total_steps)
    writer.add_scalar(
        "OutcomeResidual/FullLoss",
        process_metrics.get("outcome_residual_full_loss", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "OutcomeResidual/BaselineLoss",
        process_metrics.get("outcome_residual_base_loss", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "OutcomeResidual/TotalLoss",
        process_metrics.get("outcome_residual_total_loss", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "OutcomeResidual/GainMean",
        process_metrics.get("outcome_residual_gain_mean", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "OutcomeResidual/GainPositiveFrac",
        process_metrics.get("outcome_residual_gain_positive_frac", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "OutcomeResidual/AvailableMean",
        process_metrics.get("outcome_residual_available_mean", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "OutcomeResidual/TargetAbsMean",
        process_metrics.get("outcome_residual_target_abs_mean", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "OutcomeResidual/RewardMean",
        process_metrics.get("outcome_residual_reward_mean", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "OutcomeResidual/RewardActive",
        process_metrics.get("outcome_residual_reward_active", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "OutcomeResidual/SkillGainStd",
        process_metrics.get("outcome_residual_skill_gain_std", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "OutcomeResidual/TeamGainStd",
        process_metrics.get("outcome_residual_team_gain_std", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "OutcomeResidual/DurationGainStd",
        process_metrics.get("outcome_residual_duration_gain_std", 0.0),
        total_steps,
    )
    for field_name in (
        "coverage_delta_h",
        "qos_delta_h",
        "full_disconnect_improvement_h",
        "relay_margin_delta_h",
        "connected_components_improvement_h",
        "teammate_service_gain_h",
        "bottleneck_link_gain_h",
    ):
        writer.add_scalar(
            f"OutcomeResidual/Gain/{field_name}",
            process_metrics.get(f"outcome_residual_gain_{field_name}", 0.0),
            total_steps,
        )
    for key in (
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
        "topology_role_z_mi",
        "topology_role_g_mi",
        "topology_cf_backhaul_mean_mean",
        "topology_cf_components_mean_mean",
        "topology_cf_disconnect_mean_mean",
        "topology_service_mean_mean",
    ):
        writer.add_scalar(f"TopologyRole/{key}", process_metrics.get(key, 0.0), total_steps)
    for role_name in ("idle", "relay", "service", "relay_service"):
        writer.add_scalar(
            f"TopologyRole/Fraction/{role_name}",
            process_metrics.get(f"topology_role_frac_{role_name}", 0.0),
            total_steps,
        )
    for key in (
        "topology_potential_available_frac",
        "topology_potential_active",
        "topology_potential_raw_mean",
        "topology_potential_reward_mean",
        "topology_potential_high_mean",
        "topology_potential_low_mean",
        "topology_potential_phi_start_mean",
        "topology_potential_phi_end_mean",
        "topology_potential_backhaul_up_start_mean",
        "topology_potential_backhaul_up_end_mean",
        "topology_potential_full_disconnect_start_mean",
        "topology_potential_full_disconnect_end_mean",
    ):
        writer.add_scalar(f"TopologyPotential/{key}", process_metrics.get(key, 0.0), total_steps)
    for key in (
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
    ):
        writer.add_scalar(f"SkillEffect/{key}", process_metrics.get(key, 0.0), total_steps)
    writer.add_scalar("Process/DurationOnlyAccuracy", process_metrics.get("duration_only_accuracy", 0.0), total_steps)
    writer.add_scalar("Process/LengthOnlyAccuracy", process_metrics.get("length_only_accuracy", 0.0), total_steps)
    writer.add_scalar("Process/RewardSumOnlyAccuracy", process_metrics.get("reward_sum_only_accuracy", 0.0), total_steps)
    writer.add_scalar(
        "Process/PosteriorMinusDurationOnly",
        process_metrics.get("posterior_acc_minus_duration_only", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Process/PosteriorMinusLengthOnly",
        process_metrics.get("posterior_acc_minus_length_only", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Process/PosteriorMinusRewardSumOnly",
        process_metrics.get("posterior_acc_minus_reward_sum_only", 0.0),
        total_steps,
    )
    writer.add_scalar("Process/SegmentLengthMean", process_metrics.get("segment_length_mean", 0.0), total_steps)
    writer.add_scalar("Process/SegmentLengthMax", process_metrics.get("segment_length_max", 0.0), total_steps)
    writer.add_scalar("Process/DurationTargetMean", process_metrics.get("duration_target_mean", 0.0), total_steps)
    writer.add_scalar("Process/SkillSwitchRate", process_metrics.get("skill_switch_rate", 0.0), total_steps)
    writer.add_scalar("Process/InitialAssignmentRate", process_metrics.get("initial_assignment_rate", 0.0), total_steps)
    writer.add_scalar("Collapse/SkillUsageEntropy", process_metrics.get("skill_usage_entropy", 0.0), total_steps)
    writer.add_scalar("Collapse/SkillUsageMaxFrac", process_metrics.get("skill_usage_max_frac", 0.0), total_steps)
    writer.add_scalar("Collapse/DurationUsageEntropy", process_metrics.get("duration_usage_entropy", 0.0), total_steps)
    writer.add_scalar("Collapse/DurationUsageMaxFrac", process_metrics.get("duration_usage_max_frac", 0.0), total_steps)
    writer.add_scalar("Collapse/DurationPolicyEntropy", process_metrics.get("duration_policy_entropy", 0.0), total_steps)
    writer.add_scalar(
        "Collapse/DurationPolicyEntropyNorm",
        process_metrics.get("duration_policy_entropy_norm", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Collapse/DurationEntropyFloorActive",
        process_metrics.get("duration_entropy_floor_active", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Collapse/DurationEntropyFloorGap",
        process_metrics.get("duration_entropy_floor_gap", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Collapse/DurationEntropyFloorLoss",
        process_metrics.get("duration_entropy_floor_loss", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Collapse/DurationEntropyFloorCoefActive",
        process_metrics.get("duration_entropy_floor_coef_active", 0.0),
        total_steps,
    )
    writer.add_scalar("Collapse/SkillDurationMI", process_metrics.get("skill_duration_mi", 0.0), total_steps)
    writer.add_scalar("Lifetime/Heterogeneity", process_metrics.get("lifetime_heterogeneity", 0.0), total_steps)
    writer.add_scalar("Lifetime/DurationAgentMI", process_metrics.get("duration_agent_mi", 0.0), total_steps)
    writer.add_scalar("Lifetime/DurationReturnRange", process_metrics.get("duration_return_range", 0.0), total_steps)
    writer.add_scalar(
        "Lifetime/DurationFullDisconnectRange",
        process_metrics.get("duration_full_disconnect_range", 0.0),
        total_steps,
    )
    writer.add_scalar("Lifetime/DurationRecoveryRange", process_metrics.get("duration_recovery_range", 0.0), total_steps)
    writer.add_scalar("Lifetime/DurationBhFracRange", process_metrics.get("duration_bh_frac_range", 0.0), total_steps)
    writer.add_scalar("Lifetime/RenewalFullSyncRate", process_metrics.get("renewal_full_sync_rate", 0.0), total_steps)
    writer.add_scalar("Lifetime/RenewalPairwiseCorr", process_metrics.get("renewal_pairwise_corr_mean", 0.0), total_steps)
    writer.add_scalar("Collapse/TeamCodeUsageEntropy", process_metrics.get("team_code_usage_entropy", 0.0), total_steps)
    writer.add_scalar("Collapse/TeamCodeUsageMaxFrac", process_metrics.get("team_code_usage_max_frac", 0.0), total_steps)
    writer.add_scalar("Collapse/TeamCodeSkillMI", process_metrics.get("team_code_skill_mi", 0.0), total_steps)
    writer.add_scalar("Collapse/GInterventionKLActive", process_metrics.get("g_intervention_kl_active", 0.0), total_steps)
    writer.add_scalar("Collapse/GInterventionKLSamples", process_metrics.get("g_intervention_kl_samples", 0.0), total_steps)
    writer.add_scalar("Collapse/GInterventionKLMean", process_metrics.get("g_intervention_kl_mean", 0.0), total_steps)
    writer.add_scalar("Collapse/GInterventionKLMax", process_metrics.get("g_intervention_kl_max", 0.0), total_steps)
    writer.add_scalar("Collapse/GInterventionTVMean", process_metrics.get("g_intervention_tv_mean", 0.0), total_steps)
    writer.add_scalar("GInfo/Active", process_metrics.get("g_info_active", 0.0), total_steps)
    writer.add_scalar("GInfo/ObjectiveActive", process_metrics.get("g_info_objective_active", 0.0), total_steps)
    writer.add_scalar("GInfo/Samples", process_metrics.get("g_info_samples", 0.0), total_steps)
    writer.add_scalar("GInfo/Loss", process_metrics.get("g_info_loss", 0.0), total_steps)
    writer.add_scalar("GInfo/CoefScale", process_metrics.get("g_info_coef_scale", 0.0), total_steps)
    writer.add_scalar("GInfo/SkillMI", process_metrics.get("g_info_skill_mi", 0.0), total_steps)
    writer.add_scalar("GInfo/DurationMI", process_metrics.get("g_info_duration_mi", 0.0), total_steps)
    writer.add_scalar("GInfo/EditMI", process_metrics.get("g_info_edit_mi", 0.0), total_steps)
    writer.add_scalar("GInfo/TotalMI", process_metrics.get("g_info_total_mi", 0.0), total_steps)
    writer.add_scalar("GInfo/SkillKL", process_metrics.get("g_itv_kl_skill", 0.0), total_steps)
    writer.add_scalar("GInfo/SkillTV", process_metrics.get("g_itv_tv_skill", 0.0), total_steps)
    writer.add_scalar("GInfo/DurationKL", process_metrics.get("g_itv_kl_duration", 0.0), total_steps)
    writer.add_scalar("GInfo/DurationTV", process_metrics.get("g_itv_tv_duration", 0.0), total_steps)
    writer.add_scalar("GInfo/EditKL", process_metrics.get("g_itv_kl_edit", 0.0), total_steps)
    writer.add_scalar("GInfo/EditTV", process_metrics.get("g_itv_tv_edit", 0.0), total_steps)
    writer.add_scalar(
        "GInfo/JointAssignmentDistance",
        process_metrics.get("g_joint_assignment_distance", 0.0),
        total_steps,
    )
    writer.add_scalar("Situation/Enabled", process_metrics.get("situation_enabled", 0.0), total_steps)
    writer.add_scalar("Situation/ChangeRate", process_metrics.get("situation_change_rate", 0.0), total_steps)
    writer.add_scalar("Situation/UniqueKappa", process_metrics.get("situation_unique_kappa", 0.0), total_steps)
    writer.add_scalar(
        "Situation/SegmentChangeFrac",
        process_metrics.get("situation_segment_change_frac", 0.0),
        total_steps,
    )
    for key in (
        "situation_agent_kappa_enabled",
        "situation_agent_kappa_change_rate",
        "situation_agent_kappa_disagreement_rate",
        "situation_agent_kappa_median_dwell",
        "situation_agent_kappa_global_mi",
        "situation_agent_unique_kappa_mean",
    ):
        writer.add_scalar(f"Situation/{key}", process_metrics.get(key, 0.0), total_steps)
    writer.add_scalar(
        "Situation/HazardControlEnabled",
        process_metrics.get("situation_hazard_control_enabled", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Situation/HazardForcedRenewalRate",
        process_metrics.get("situation_hazard_forced_renewal_rate", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Situation/HazardModeCode",
        process_metrics.get("situation_hazard_mode_code", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Situation/HazardConservativeGuard",
        process_metrics.get("situation_hazard_conservative_guard", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Situation/HazardGuardEventCount",
        process_metrics.get("situation_hazard_guard_event_count", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Situation/HazardGuardAllowRate",
        process_metrics.get("situation_hazard_guard_allow_rate", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Situation/HazardGuardConfirmBlockRate",
        process_metrics.get("situation_hazard_guard_confirm_block_rate", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Situation/HazardGuardDwellBlockRate",
        process_metrics.get("situation_hazard_guard_dwell_block_rate", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Situation/HazardGuardRateCapBlockRate",
        process_metrics.get("situation_hazard_guard_rate_cap_block_rate", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Situation/HazardGuardNoChangeBlockRate",
        process_metrics.get("situation_hazard_guard_no_change_block_rate", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Situation/HazardGuardRecentForceRate",
        process_metrics.get("situation_hazard_guard_recent_force_rate", 0.0),
        total_steps,
    )
    writer.add_scalar("Credit/ProbeAvailableFrac", process_metrics.get("credit_probe_available_frac", 0.0), total_steps)
    writer.add_scalar("Credit/FullDisconnectMean", process_metrics.get("credit_full_disconnect_mean", 0.0), total_steps)
    writer.add_scalar("Credit/RecoveryRate", process_metrics.get("credit_recovery_rate", 0.0), total_steps)
    writer.add_scalar("Credit/CollapseRate", process_metrics.get("credit_collapse_rate", 0.0), total_steps)
    writer.add_scalar(
        "Credit/BackhaulConnectedStepFraction",
        process_metrics.get("credit_backhaul_connected_step_fraction", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Credit/ThroughputWhenBackhaulConnectedMbps",
        process_metrics.get("credit_throughput_when_backhaul_connected_mbps", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Credit/DeltaConnectivityRatio",
        process_metrics.get("credit_delta_connectivity_ratio_mean", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Credit/DeltaBackhaulServedUsers",
        process_metrics.get("credit_delta_backhaul_served_users_mean", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Credit/DeltaBackhaulOutageRatio",
        process_metrics.get("credit_delta_backhaul_outage_ratio_mean", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "Credit/DeltaRelayRouteLossRatio",
        process_metrics.get("credit_delta_relay_route_loss_ratio_mean", 0.0),
        total_steps,
    )
    writer.add_scalar("Credit/RewardConnectivityCorr", process_metrics.get("credit_reward_conn_corr", 0.0), total_steps)
    writer.add_scalar("Credit/RewardServedCorr", process_metrics.get("credit_reward_served_corr", 0.0), total_steps)
    writer.add_scalar("Credit/RewardOutageCorr", process_metrics.get("credit_reward_outage_corr", 0.0), total_steps)
    writer.add_scalar("High/Loss", process_metrics["high_loss"], total_steps)
    writer.add_scalar("High/PolicyLoss", process_metrics.get("high_policy_loss", 0.0), total_steps)
    writer.add_scalar("High/ValueLoss", process_metrics.get("high_value_loss", 0.0), total_steps)
    writer.add_scalar("High/EntropyLoss", process_metrics.get("high_entropy_loss", 0.0), total_steps)
    writer.add_scalar("High/AuxLoss", process_metrics.get("high_aux_loss", 0.0), total_steps)
    writer.add_scalar("High/Entropy", process_metrics["high_entropy"], total_steps)
    writer.add_scalar("High/ReturnMean", process_metrics["high_return_mean"], total_steps)
    writer.add_scalar("High/EnvReturnMean", process_metrics.get("high_env_return_mean", 0.0), total_steps)
    writer.add_scalar("High/BootstrapValueMean", process_metrics.get("high_bootstrap_value_mean", 0.0), total_steps)
    writer.add_scalar(
        "High/BootstrapContributionMean",
        process_metrics.get("high_bootstrap_contribution_mean", 0.0),
        total_steps,
    )
    writer.add_scalar("High/SMDPDiscountMean", process_metrics.get("high_smdp_discount_mean", 0.0), total_steps)
    writer.add_scalar("High/ValueNormMean", process_metrics.get("high_value_norm_mean", 0.0), total_steps)
    writer.add_scalar("High/ValueNormStd", process_metrics.get("high_value_norm_std", 0.0), total_steps)
    writer.add_scalar("High/GradNorm", process_metrics.get("high_grad_norm", 0.0), total_steps)
    writer.add_scalar("High/CompactReturnLoss", process_metrics.get("compact_return_loss", 0.0), total_steps)
    writer.add_scalar("High/CompactReturnActive", process_metrics.get("compact_return_active", 0.0), total_steps)
    writer.add_scalar("High/TeamCodeEntropy", process_metrics.get("team_code_entropy", 0.0), total_steps)
    writer.add_scalar("High/CompactNormMean", process_metrics.get("compact_norm_mean", 0.0), total_steps)
    writer.add_scalar("High/OPTCDLoss", process_metrics.get("opt_cd_loss", 0.0), total_steps)
    writer.add_scalar("High/OPTCMILoss", process_metrics.get("opt_cmi_loss", 0.0), total_steps)
    writer.add_scalar("High/OPTAggregationEntropy", process_metrics.get("opt_aggregation_entropy", 0.0), total_steps)
    writer.add_scalar("Low/Loss", low_metrics["low_loss"], total_steps)
    writer.add_scalar("Low/PolicyLoss", low_metrics.get("low_policy_loss", 0.0), total_steps)
    writer.add_scalar("Low/ValueLoss", low_metrics.get("low_value_loss", 0.0), total_steps)
    writer.add_scalar("Low/EntropyLoss", low_metrics.get("low_entropy_loss", 0.0), total_steps)
    writer.add_scalar("Low/ActorLoss", low_metrics.get("low_actor_loss", 0.0), total_steps)
    writer.add_scalar("Low/CriticLoss", low_metrics.get("low_critic_loss", 0.0), total_steps)
    writer.add_scalar("Low/Entropy", low_metrics["low_entropy"], total_steps)
    writer.add_scalar("Low/SequenceChunks", low_metrics.get("low_sequence_chunks", 0.0), total_steps)
    writer.add_scalar("Low/ValueNormMean", low_metrics.get("low_value_norm_mean", 0.0), total_steps)
    writer.add_scalar("Low/ValueNormStd", low_metrics.get("low_value_norm_std", 0.0), total_steps)
    writer.add_scalar("Low/ValueErrorAbsMean", low_metrics.get("low_value_error_abs_mean", 0.0), total_steps)
    writer.add_scalar("Low/ValueErrorRMSE", low_metrics.get("low_value_error_rmse", 0.0), total_steps)
    writer.add_scalar("Low/AdvantageStd", low_metrics.get("low_advantage_std", 0.0), total_steps)
    writer.add_scalar("Low/RatioMean", low_metrics.get("low_ratio_mean", 0.0), total_steps)
    writer.add_scalar("Low/ClipFrac", low_metrics.get("low_clip_frac", 0.0), total_steps)
    writer.add_scalar("Low/ApproxKL", low_metrics.get("low_approx_kl", 0.0), total_steps)
    writer.add_scalar("Low/ActorGradNorm", low_metrics.get("low_actor_grad_norm", 0.0), total_steps)
    writer.add_scalar("Low/CriticGradNorm", low_metrics.get("low_critic_grad_norm", 0.0), total_steps)
    writer.add_scalar("Low/ActorHiddenNormMean", low_metrics.get("low_actor_h_norm_mean", 0.0), total_steps)
    writer.add_scalar("Low/CriticHiddenNormMean", low_metrics.get("low_critic_h_norm_mean", 0.0), total_steps)
    writer.add_scalar("LowSkill/UsageEntropy", low_metrics.get("low_skill_usage_entropy", 0.0), total_steps)
    writer.add_scalar("LowSkill/ReturnStd", low_metrics.get("low_skill_return_std", 0.0), total_steps)
    writer.add_scalar("LowSkill/ReturnRange", low_metrics.get("low_skill_return_range", 0.0), total_steps)
    writer.add_scalar("LowSkill/ValueErrorAbsStd", low_metrics.get("low_skill_value_error_abs_std", 0.0), total_steps)
    writer.add_scalar("LowSkill/EntropyStd", low_metrics.get("low_skill_entropy_std", 0.0), total_steps)
    writer.add_scalar("LowTeam/UsageEntropy", low_metrics.get("low_team_usage_entropy", 0.0), total_steps)
    writer.add_scalar("LowTeam/ReturnStd", low_metrics.get("low_team_return_std", 0.0), total_steps)
    writer.add_scalar("LowTeam/ReturnRange", low_metrics.get("low_team_return_range", 0.0), total_steps)
    writer.add_scalar("LowTeam/ValueErrorAbsStd", low_metrics.get("low_team_value_error_abs_std", 0.0), total_steps)
    writer.add_scalar("Low/ReturnMean", low_metrics["return_mean"], total_steps)
    # P2-lite recovery-window contribution credit (Pre-check 2 gate + diagnostics).
    writer.add_scalar("P2/Segments", process_metrics.get("p2_segments", 0.0), total_steps)
    writer.add_scalar("P2/AvailableFrac", process_metrics.get("p2_available_frac", 0.0), total_steps)
    writer.add_scalar("P2/WindowFrac", process_metrics.get("p2_window_frac", 0.0), total_steps)
    writer.add_scalar("P2/FTeamMean", process_metrics.get("p2_f_team_mean", 0.0), total_steps)
    writer.add_scalar("P2/CreditMean", process_metrics.get("p2_credit_mean", 0.0), total_steps)
    writer.add_scalar(
        "P2/DeltaPhiNonzeroFullDisconnect",
        process_metrics.get("delta_phi_soft_nonzero_rate_when_full_disconnect", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "P2/DeltaPhiNonzeroNearDisconnect",
        process_metrics.get("delta_phi_soft_nonzero_rate_when_near_disconnect", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "P2/CorrPhiRecoveryEvent",
        process_metrics.get("p2_corr_phi_recovery_event", 0.0),
        total_steps,
    )
    writer.add_scalar("P2/PartialRecoveryFrac", process_metrics.get("p2_partial_recovery_frac", 0.0), total_steps)
    writer.add_scalar("P2/DeltaBhFracMean", process_metrics.get("p2_delta_bh_frac_mean", 0.0), total_steps)
    writer.add_scalar(
        "P2/CorrCreditDeltaBhFrac",
        process_metrics.get("p2_corr_credit_delta_bh_frac", 0.0),
        total_steps,
    )
    writer.add_scalar(
        "P2/CreditByPartialRecovery",
        process_metrics.get("p2_credit_by_partial_recovery_event", 0.0),
        total_steps,
    )
    for key, value in process_metrics.items():
        if key.startswith("r28_g1_"):
            writer.add_scalar(f"R28G1/{key.removeprefix('r28_g1_')}", value, total_steps)
        elif key.startswith("r29_action_info_"):
            writer.add_scalar(
                f"R29ActionInfo/{key.removeprefix('r29_action_info_')}",
                value,
                total_steps,
            )
        elif key.startswith("r31_effect_"):
            writer.add_scalar(
                f"R31Effect/{key.removeprefix('r31_effect_')}",
                value,
                total_steps,
            )
        elif key.startswith("aem_"):
            writer.add_scalar(
                f"AEM/{key.removeprefix('aem_')}",
                value,
                total_steps,
            )
    writer.flush()

def export_update_metrics(
    args: argparse.Namespace,
    update_idx: int,
    total_steps: int,
    env_reward_mean: float,
    process_metrics: dict[str, float],
    low_metrics: dict[str, float],
) -> None:
    row = {
        "update": int(update_idx),
        "total_steps": int(total_steps),
        "env_reward_mean": float(env_reward_mean),
        **{key: float(value) for key, value in process_metrics.items()},
        **{key: float(value) for key, value in low_metrics.items()},
    }
    append_csv(Path(args.log_dir) / "metrics" / "train_updates.csv", row, UPDATE_FIELDS)
    if int(getattr(args, "plot_interval", 1)) > 0 and update_idx % int(args.plot_interval) == 0:
        save_update_plots(args.log_dir)

def log_eval_metrics(writer, total_steps: int, metrics: dict[str, float]) -> None:
    if writer is None:
        return
    for key, value in metrics.items():
        writer.add_scalar(f"Eval/{key}", value, total_steps)
    writer.flush()

def empty_r37_identity_metrics(config) -> dict[str, float]:
    enabled = bool(getattr(config, "r37_identity_gate_enabled", False))
    mode = str(getattr(config, "alice_bob_actor_identity_mode", "hidden")).lower()
    metrics = {field: 0.0 for field in R37_IDENTITY_METRIC_FIELDS}
    metrics["r37_identity_audit_active"] = float(enabled)
    metrics["r37_identity_mode_code"] = (
        1.0 if mode == "visible" else 0.0 if mode == "masked" else -1.0
    )
    return metrics

def audit_r37_identity_observation(config, observations, state) -> dict[str, float]:
    """Validate the R37 actor slots against the simultaneous critic identity."""

    metrics = empty_r37_identity_metrics(config)
    if metrics["r37_identity_audit_active"] == 0.0:
        return metrics
    obs = np.asarray(observations, dtype=np.float32)
    critic_state = np.asarray(state, dtype=np.float32).reshape(-1)
    if obs.shape != (2, 16):
        raise RuntimeError(f"R37 actor observation shape {obs.shape} != (2, 16)")
    if critic_state.shape != (19,):
        raise RuntimeError(f"R37 critic state shape {critic_state.shape} != (19,)")
    identity = critic_state[4:8]
    critic_error = max(
        abs(float(identity[:2].sum()) - 1.0),
        abs(float(identity[2:].sum()) - 1.0),
        float(np.max(np.minimum(np.abs(identity), np.abs(identity - 1.0)))),
    )
    mode = str(getattr(config, "alice_bob_actor_identity_mode", "")).lower()
    expected = identity if mode == "visible" else np.zeros(4, dtype=np.float32)
    slot_error = float(np.max(np.abs(obs[:, 12:16] - expected[None, :])))
    metrics["r37_identity_audit_rows"] = float(obs.shape[0])
    metrics["r37_identity_slot_max_abs_error"] = slot_error
    metrics["r37_critic_identity_max_abs_error"] = critic_error
    if slot_error > 1e-7 or critic_error > 1e-7:
        raise RuntimeError(
            "R37 identity audit failed: "
            f"slot_error={slot_error:.9g}, critic_error={critic_error:.9g}"
        )
    return metrics

def emit(args: argparse.Namespace, message: str) -> None:
    print(message)
    log_dir = Path(getattr(args, "log_dir", "logs/ha_ctse_process_standalone"))
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        with (log_dir / "standalone_train.log").open("a", encoding="utf-8") as handle:
            handle.write(message + "\n")
    except OSError:
        pass
