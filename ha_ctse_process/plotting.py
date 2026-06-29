"""Metrics export and plotting for standalone HA-CTSE UAV experiments."""

from __future__ import annotations

import csv
import re
import argparse
from pathlib import Path
from typing import Any

import numpy as np

from ha_ctse_process.cooperation_credit import COOPERATION_CREDIT_FIELDS
from ha_ctse_process.topology_potential import TOPOLOGY_POTENTIAL_FIELDS

try:
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
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
)


UPDATE_FIELDS = (
    "update",
    "total_steps",
    "env_reward_mean",
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
    "skill_duration_mi",
    "team_code_usage_entropy",
    "team_code_usage_max_frac",
    "team_code_skill_mi",
    "g_intervention_kl_active",
    "g_intervention_kl_samples",
    "g_intervention_kl_mean",
    "g_intervention_kl_max",
    "g_intervention_tv_mean",
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
        ("team_code_usage_entropy", "Team-code usage entropy"),
        ("skill_usage_max_frac", "Skill max fraction"),
        ("duration_usage_max_frac", "Duration max fraction"),
        ("team_code_usage_max_frac", "Team-code max fraction"),
        ("skill_duration_mi", "Skill-duration MI"),
        ("team_code_skill_mi", "Team-code/skill MI"),
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
