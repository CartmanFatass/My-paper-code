"""Standalone CLI and environment wiring for HA-CTSE process-core runs."""

from __future__ import annotations

import argparse
import importlib
from pathlib import Path
from typing import Any

import numpy as np
import torch

from ha_ctse_process.collectors import SubprocEnvCollector, SyncEnvCollector
from ha_ctse_process.env_factory import EnvSpec, make_env, normalize_scenario
from ha_ctse_process.r28_g1_reward import ARMS as R28_G1_ARMS
from ha_ctse_process.r29_action_information_reward import (
    MODES as R29_ACTION_INFO_MODES,
    REWARD_CLIP as R29_ACTION_INFO_REWARD_CLIP,
    REWARD_COEF as R29_ACTION_INFO_REWARD_COEF,
)
from ha_ctse_process.standalone_agent import StandaloneProcessAgent


def _nonnegative_int(text: str) -> int:
    value = int(text)
    if value < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return value


def load_config(config_name: str, preset: str | None):
    module = importlib.import_module(config_name)
    return module.Config(preset=preset) if preset else module.Config()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train or evaluate the standalone HA-CTSE process-core algorithm."
    )
    parser.add_argument("--mode", choices=("train", "eval"), default="train")
    parser.add_argument("--config", default="ha_ctse_process.config")
    parser.add_argument("--preset", default="")
    parser.add_argument("--scenario", default="energy")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--log_dir", default="logs/ha_ctse_process_standalone")
    parser.add_argument("--dry_run_env_steps", type=int, default=0)
    parser.add_argument("--total_timesteps", type=int, default=320000)
    parser.add_argument("--rollout_length", type=int, default=500)
    parser.add_argument("--skill_interval", type=int, default=10)
    parser.add_argument(
        "--high_controller",
        choices=(
            "legacy_duration",
            "r30_fixed_clock_ar_edit",
            "variable_roster_event",
        ),
        default="",
    )
    parser.add_argument(
        "--event_architecture_mode",
        choices=("f0", "f1"),
        default="",
    )
    parser.add_argument(
        "--iteration5_process_semantics_arm",
        choices=("", "c1_semantic_on", "c1_semantic_off"),
        default="",
        help="Enter the separate Iteration-5 spatial F0/process-semantics branch.",
    )
    parser.add_argument(
        "--iteration5_smoke",
        action="store_true",
        help="Permit a reduced, explicitly non-scientific Iteration-5 operational run.",
    )
    parser.add_argument(
        "--r30_pair_gate",
        action="store_true",
        help=(
            "Apply the registered reward-pure R30 mechanism-pair contract to "
            "either the legacy-duration or fixed-clock controller."
        ),
    )
    parser.add_argument("--num_envs", type=int, default=1)
    parser.add_argument("--n_agents", type=int, default=0)
    parser.add_argument("--collector_backend", choices=("sync", "subproc"), default="sync")
    parser.add_argument("--collector_start_method", choices=("spawn", "forkserver", "fork"), default="spawn")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--save_interval", type=int, default=10)
    parser.add_argument("--infrastructure-profile-interval", type=_nonnegative_int, default=0)
    parser.add_argument("--checkpoint_keep_last", type=int, default=3)
    parser.add_argument("--resume_from", default="")
    parser.add_argument(
        "--r28_g1_arm",
        choices=("off", *R28_G1_ARMS),
        default="off",
    )
    parser.add_argument("--r28_g1_scorer_path", default="")
    parser.add_argument(
        "--r28_g1_engineering_smoke",
        action="store_true",
        help=(
            "Permit only the registered local one-environment, one-update "
            "R28-G1 integration smoke. This never authorizes a scientific run."
        ),
    )
    parser.add_argument(
        "--r29_action_info_mode",
        choices=("off", *R29_ACTION_INFO_MODES),
        default="off",
    )
    parser.add_argument(
        "--r29_action_info_coef", type=float, default=R29_ACTION_INFO_REWARD_COEF
    )
    parser.add_argument(
        "--r29_action_info_clip", type=float, default=R29_ACTION_INFO_REWARD_CLIP
    )
    parser.add_argument(
        "--r31_effect_mode",
        choices=("", "off", "probe_only", "real_reward"),
        default="",
    )
    parser.add_argument("--eval_interval", type=int, default=0)
    parser.add_argument("--eval_episodes", type=int, default=3)
    parser.add_argument("--eval_max_steps", type=int, default=0)
    parser.add_argument(
        "--eval_action_mode",
        choices=("deterministic", "stochastic"),
        default="deterministic",
    )
    parser.add_argument(
        "--eval_seed_blocks",
        default="",
        help="Comma-separated environment seed blocks for fixed final evaluation.",
    )
    parser.add_argument(
        "--eval_episodes_per_seed",
        type=int,
        default=0,
        help="Episodes per eval seed block; reset seed is block*1000+episode.",
    )
    parser.add_argument("--save_topology", action="store_true")
    parser.add_argument("--topology_interval", type=int, default=25)
    parser.add_argument("--topology_episodes", type=int, default=1)
    parser.add_argument("--topology_max_frames", type=int, default=160)
    parser.add_argument("--plot_interval", type=int, default=1)
    parser.add_argument("--skill_lifetime_candidates", default="")
    parser.add_argument(
        "--team_bridge_type",
        choices=("none", "deterministic", "stochastic", "deterministic_expected"),
        default="",
    )
    parser.add_argument(
        "--low_level_architecture",
        choices=("strict_hmasd_mappo", "gru_ctde", "feedforward"),
        default="",
    )
    parser.add_argument("--opt_compact_dim", type=int, default=0)
    parser.add_argument("--opt_num_prototypes", type=int, default=0)
    parser.add_argument("--enable_prototype_response_skills", action="store_true")
    parser.add_argument("--prototype_skill_extra_codes", type=int, default=-1)
    parser.add_argument("--legacy_n_skills", type=int, default=0)
    parser.add_argument("--parallel_selection", action="store_true")
    parser.add_argument("--ar_prefix_mode", choices=("same_check", "roster"), default="")
    parser.add_argument("--enable_high_omega_conditioning", action="store_true")
    parser.add_argument("--enable_agent_prototype_relevance", action="store_true")
    parser.add_argument("--prototype_bank_ema_tau", type=float, default=None)
    parser.add_argument("--enable_per_agent_kappa", action="store_true")
    parser.add_argument("--enable_prototype_disc_probe", action="store_true")
    parser.add_argument("--enable_prototype_disc_reward", action="store_true")
    parser.add_argument("--prototype_disc_reward_coef", type=float, default=None)
    parser.add_argument("--prototype_disc_clip", type=float, default=None)
    parser.add_argument("--prototype_disc_warmup_steps", type=int, default=-1)
    parser.add_argument("--prototype_disc_condition", choices=("kappa", "omega", "none"), default="")
    parser.add_argument("--prototype_disc_lr", type=float, default=None)
    parser.add_argument("--prototype_disc_hidden_dim", type=int, default=0)
    parser.add_argument("--prototype_disc_use_learned_prior", action="store_true")
    parser.add_argument("--prototype_disc_prior_coef", type=float, default=None)
    parser.add_argument("--enable_compact_return_head", action="store_true")
    parser.add_argument("--compact_return_coef", type=float, default=None)
    parser.add_argument(
        "--process_reward_mode",
        choices=(
            "mi_outcome",
            "mi_only",
            "positive_mi",
            "centered_mi",
            "residual_mi",
            "positive_residual_mi",
            "centered_residual_mi",
            "residual_mi_outcome",
            "none",
        ),
        default="",
    )
    parser.add_argument(
        "--process_reward_injection",
        choices=("high_only", "high_and_low", "low_only", "none"),
        default="",
    )
    parser.add_argument("--process_reward_coef", type=float, default=None)
    parser.add_argument("--process_reward_clip", type=float, default=None)
    parser.add_argument("--process_contrast_coef", type=float, default=None)
    parser.add_argument("--process_outcome_coef", type=float, default=None)
    parser.add_argument("--process_reward_contrast_coef", type=float, default=None)
    parser.add_argument("--process_reward_outcome_coef", type=float, default=None)
    parser.add_argument("--process_prior_coef", type=float, default=None)
    parser.add_argument("--process_shortcut_coef", type=float, default=None)
    parser.add_argument("--context_shortcut_coef", type=float, default=None)
    parser.add_argument("--intrinsic_phase_bins", type=int, default=0)
    parser.add_argument("--process_shortcut_margin", type=float, default=None)
    parser.add_argument("--process_shortcut_margin_coef", type=float, default=None)
    parser.add_argument("--process_reward_warmup_steps", type=int, default=-1)
    parser.add_argument("--transition_skill_coef", type=float, default=None)
    parser.add_argument("--transition_skill_prior_coef", type=float, default=None)
    parser.add_argument("--transition_context_shortcut_coef", type=float, default=None)
    parser.add_argument("--transition_skill_reward_coef", type=float, default=None)
    parser.add_argument("--transition_skill_reward_warmup_steps", type=int, default=-1)
    parser.add_argument("--transition_skill_reward_clip", type=float, default=None)
    parser.add_argument("--transition_skill_max_samples", type=int, default=0)
    parser.add_argument("--outcome_residual_horizon", type=int, default=0)
    parser.add_argument("--outcome_residual_coef", type=float, default=None)
    parser.add_argument("--outcome_residual_hidden_dim", type=int, default=0)
    parser.add_argument(
        "--outcome_residual_injection",
        choices=("high_only", "high_and_low", "low_only", "none"),
        default="",
    )
    parser.add_argument("--outcome_residual_reward_coef", type=float, default=None)
    parser.add_argument("--outcome_residual_reward_clip", type=float, default=None)
    parser.add_argument("--topology_role_coef", type=float, default=None)
    parser.add_argument("--topology_role_hidden_dim", type=int, default=0)
    parser.add_argument("--topology_role_min_score", type=float, default=None)
    parser.add_argument(
        "--topology_role_injection",
        choices=("high_only", "high_and_low", "low_only", "none"),
        default="",
    )
    parser.add_argument("--topology_role_reward_coef", type=float, default=None)
    parser.add_argument("--topology_role_reward_clip", type=float, default=None)
    parser.add_argument(
        "--topology_potential_injection",
        choices=("high_only", "high_and_low", "low_only", "none"),
        default="",
    )
    parser.add_argument("--topology_potential_coef", type=float, default=None)
    parser.add_argument("--topology_potential_clip", type=float, default=None)
    parser.add_argument("--topology_potential_warmup_steps", type=int, default=-1)
    parser.add_argument(
        "--topology_potential_discount_mode",
        choices=("delta", "one_step", "smdp"),
        default="",
    )
    parser.add_argument("--skill_effect_horizons", default="")
    parser.add_argument("--skill_effect_stride", type=int, default=0)
    parser.add_argument("--skill_effect_max_windows", type=int, default=0)
    parser.add_argument("--skill_effect_hidden_dim", type=int, default=0)
    parser.add_argument("--disable_skill_effect_group_balanced_loss", action="store_true")
    parser.add_argument("--skill_effect_intervention_max_samples", type=int, default=0)
    parser.add_argument("--skill_effect_warmup_steps", type=int, default=-1)
    parser.add_argument("--skill_effect_ctrl_coef", type=float, default=None)
    parser.add_argument("--skill_effect_use_coef", type=float, default=None)
    parser.add_argument("--skill_effect_reward_clip", type=float, default=None)
    parser.add_argument("--skill_effect_min_gain", type=float, default=None)
    parser.add_argument("--skill_effect_min_positive_frac", type=float, default=None)
    parser.add_argument(
        "--skill_effect_reward_injection",
        choices=("none", "low_only"),
        default="",
    )
    parser.add_argument(
        "--skill_force_reward_injection",
        choices=("none", "low_only"),
        default="",
    )
    parser.add_argument("--skill_force_disc_coef", type=float, default=None)
    parser.add_argument("--skill_force_effect_coef", type=float, default=None)
    parser.add_argument("--skill_force_duration_entropy_coef", type=float, default=None)
    parser.add_argument("--skill_force_warmup_steps", type=int, default=-1)
    parser.add_argument("--skill_force_clip", type=float, default=None)
    parser.add_argument("--skill_force_shortcut_margin", type=float, default=None)
    parser.add_argument("--disable_skill_force_shortcut_gate", action="store_true")
    parser.add_argument("--skill_force_use_comm_fields", action="store_true")
    parser.add_argument("--semantic_shortcut_hard_stop_margin", type=float, default=None)
    parser.add_argument("--semantic_shortcut_hard_stop_min_segments", type=int, default=0)
    parser.add_argument("--g_intervention_kl_max_segments", type=int, default=0)
    parser.add_argument("--g_info_coef_skill", type=float, default=None)
    parser.add_argument("--g_info_coef_duration", type=float, default=None)
    parser.add_argument("--g_info_coef_edit", type=float, default=None)
    parser.add_argument("--g_info_warmup_steps", type=int, default=-1)
    parser.add_argument("--g_info_anneal_steps", type=int, default=-1)
    parser.add_argument("--g_info_max_segments", type=int, default=0)
    parser.add_argument("--enable_situation_diagnostics", action="store_true")
    parser.add_argument("--enable_situation_hazard_control", action="store_true")
    parser.add_argument("--situation_substrate_source", choices=("omega", "compact_cluster"), default="")
    parser.add_argument("--situation_num_kappa", type=int, default=0)
    parser.add_argument("--situation_debounce_steps", type=int, default=0)
    parser.add_argument(
        "--situation_hazard_mode",
        choices=("diagnostic", "oracle_change", "learned_beta"),
        default="",
    )
    parser.add_argument("--situation_hazard_check_interval", type=int, default=0)
    parser.add_argument("--situation_hazard_min_age", type=int, default=0)
    parser.add_argument("--situation_hazard_hidden_dim", type=int, default=0)
    parser.add_argument("--situation_hazard_entropy_coef", type=float, default=None)
    parser.add_argument("--situation_hazard_value_coef", type=float, default=None)
    parser.add_argument("--situation_hazard_clip_epsilon", type=float, default=None)
    parser.add_argument("--situation_hazard_reward_coef", type=float, default=None)
    parser.add_argument("--enable_situation_hazard_conservative_guard", action="store_true")
    parser.add_argument("--situation_hazard_min_dwell_checks", type=int, default=0)
    parser.add_argument("--situation_hazard_confirm_changes", type=int, default=0)
    parser.add_argument("--situation_hazard_max_force_rate", type=float, default=None)
    parser.add_argument("--situation_hazard_rate_window", type=int, default=0)
    parser.add_argument("--enable_team_transition_probe", action="store_true")
    parser.add_argument("--enable_team_transition_reward", action="store_true")
    parser.add_argument("--team_transition_coef", type=float, default=None)
    parser.add_argument("--team_transition_clip", type=float, default=None)
    parser.add_argument("--team_transition_warmup_steps", type=int, default=-1)
    parser.add_argument("--team_transition_lr", type=float, default=None)
    parser.add_argument("--team_transition_hidden_dim", type=int, default=0)
    parser.add_argument("--enable_team_intent", action="store_true")
    parser.add_argument("--enable_team_disc_probe", action="store_true")
    parser.add_argument("--enable_team_disc_reward", action="store_true")
    parser.add_argument("--team_intent_k", type=int, default=0)
    parser.add_argument("--team_disc_coef", type=float, default=None)
    parser.add_argument("--team_disc_clip", type=float, default=None)
    parser.add_argument("--team_disc_warmup_steps", type=int, default=-1)
    parser.add_argument("--team_disc_lr", type=float, default=None)
    parser.add_argument("--team_disc_hidden_dim", type=int, default=0)
    parser.add_argument("--z_assignment_residual_gain", type=float, default=None)
    parser.add_argument("--team_disc_actionability_floor", type=float, default=None)
    parser.add_argument("--assignment_actionability_coef", type=float, default=None)
    parser.add_argument("--assignment_actionability_clip", type=float, default=None)
    parser.add_argument("--assignment_actionability_warmup_steps", type=int, default=None)
    parser.add_argument("--intrinsic_segment_gate_margin", type=float, default=None)
    parser.add_argument("--intrinsic_segment_gate_min_segments", type=int, default=0)
    parser.add_argument("--intrinsic_segment_gate_min_residual_mi", type=float, default=None)
    parser.add_argument("--intrinsic_segment_gate_min_posterior_acc", type=float, default=None)
    parser.add_argument("--high_entropy_coef", type=float, default=None)
    parser.add_argument("--low_entropy_coef", type=float, default=None)
    parser.add_argument("--enable_duration_entropy_floor", action="store_true")
    parser.add_argument("--duration_entropy_floor_threshold", type=float, default=None)
    parser.add_argument("--duration_entropy_floor_coef", type=float, default=None)
    parser.add_argument("--duration_entropy_floor_warmup_steps", type=int, default=-1)
    parser.add_argument("--enable_z_entropy_floor", action="store_true")
    parser.add_argument("--z_entropy_floor_threshold", type=float, default=None)
    parser.add_argument("--z_entropy_floor_coef", type=float, default=None)
    parser.add_argument("--z_entropy_floor_warmup_steps", type=int, default=-1)
    parser.add_argument("--reward_ratio_guard_mode", choices=("kill", "warn"), default="")
    parser.add_argument("--high_max_grad_norm", type=float, default=None)
    parser.add_argument("--low_max_grad_norm", type=float, default=None)
    parser.add_argument("--low_rnn_hidden_size", type=int, default=0)
    parser.add_argument("--low_sequence_length", type=int, default=0)
    parser.add_argument("--low_sequence_batch_size", type=int, default=0)
    parser.add_argument("--low_ppo_epochs", type=int, default=0)
    parser.add_argument("--low_value_loss_coef", type=float, default=None)
    parser.add_argument("--low_clip_epsilon", type=float, default=None)
    parser.add_argument("--smdp_bootstrap_coef", type=float, default=None)
    parser.add_argument("--edit_penalty_alpha", type=float, default=None)
    parser.add_argument("--switch_penalty_beta", type=float, default=None)
    parser.add_argument("--opt_cd_coef", type=float, default=None)
    parser.add_argument("--opt_cmi_coef", type=float, default=None)
    parser.add_argument("--disable_process_reward", action="store_true")
    parser.add_argument("--disable_process_posterior_mi", action="store_true")
    parser.add_argument("--disable_residual_process_posterior", action="store_true")
    parser.add_argument("--disable_context_skill_shortcut", action="store_true")
    parser.add_argument("--disable_transition_skill_discriminator", action="store_true")
    parser.add_argument("--disable_transition_skill_team_conditioning", action="store_true")
    parser.add_argument("--disable_outcome_residual_probe", action="store_true")
    parser.add_argument("--disable_outcome_residual_norm", action="store_true")
    parser.add_argument("--disable_topology_role_probe", action="store_true")
    parser.add_argument("--disable_semantic_shortcut_hard_stop", action="store_true")
    parser.add_argument("--semantic_shortcut_hard_stop_raise", action="store_true")
    parser.add_argument("--disable_g_intervention_kl_diagnostic", action="store_true")
    parser.add_argument("--disable_g_info_diagnostic", action="store_true")
    parser.add_argument("--enable_g_info_objective", action="store_true")
    parser.add_argument("--enable_assignment_actionability_probe", action="store_true")
    parser.add_argument("--enable_assignment_actionability_reward", action="store_true")
    parser.add_argument("--no_assignment_actionability_soft", action="store_true")
    parser.add_argument("--enable_team_effect_target_audit", action="store_true")
    parser.add_argument("--team_effect_audit_targets", type=str, default=None)
    parser.add_argument("--team_effect_audit_horizons", type=str, default=None)
    parser.add_argument("--enable_team_conditioned_qd_probe", action="store_true")
    parser.add_argument("--team_conditioned_qd_hidden_dim", type=int, default=None)
    parser.add_argument("--team_conditioned_qd_lr", type=float, default=None)
    parser.add_argument("--team_conditioned_qd_min_samples", type=int, default=None)
    parser.add_argument("--r24_qd_export_windows", action="store_true")
    parser.add_argument("--r24_qd_export_dir", default="")
    parser.add_argument("--r24_qd_export_max_rows_per_update", type=int, default=None)
    parser.add_argument("--r24_qd_export_seed", type=int, default=None)
    parser.add_argument("--disable_intrinsic_segment_gate", action="store_true")
    parser.add_argument("--enable_intrinsic_reward_norm", action="store_true")
    parser.add_argument("--disable_smdp_discounted_high_return", action="store_true")
    parser.add_argument("--disable_smdp_bootstrap", action="store_true")
    parser.add_argument("--disable_high_value_norm", action="store_true")
    parser.add_argument("--disable_recurrent_low_level", action="store_true")
    parser.add_argument("--disable_low_value_norm", action="store_true")
    parser.add_argument("--enable_low_actor_team_code", action="store_true")
    parser.add_argument("--enable_topology_potential_shaping", action="store_true")
    parser.add_argument("--topology_potential_positive_only", action="store_true")
    parser.add_argument("--enable_skill_effect_probe", action="store_true")
    parser.add_argument("--enable_skill_effect_intervention_probe", action="store_true")
    parser.add_argument("--enable_skill_effect_reward", action="store_true")
    parser.add_argument("--enable_skill_forcing_probe", action="store_true")
    parser.add_argument("--enable_skill_forcing_reward", action="store_true")
    # P2-lite recovery-window contribution credit (default OFF).
    parser.add_argument("--enable_p2_recovery_compute", action="store_true")
    parser.add_argument("--enable_p2_recovery_reward", action="store_true")
    parser.add_argument("--p2_recovery_reward_level", type=str, default=None,
                        choices=["high_team", "high_per_agent", "low_only"])
    parser.add_argument("--p2_recovery_reward_coef", type=float, default=None)
    parser.add_argument("--p2_recovery_reward_clip", type=float, default=None)
    return parser.parse_args()


def parse_int_tuple(text: str) -> tuple[int, ...]:
    values = []
    for chunk in str(text or "").replace(";", ",").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        values.append(int(chunk))
    return tuple(values)


def apply_standalone_overrides(config, args: argparse.Namespace) -> None:
    config.skill_interval = int(args.skill_interval)
    if str(getattr(args, "high_controller", "")):
        config.high_controller = str(args.high_controller)
    if str(getattr(args, "event_architecture_mode", "")):
        config.event_architecture_mode = str(args.event_architecture_mode)
    config.iteration5_process_semantics_arm = str(
        getattr(args, "iteration5_process_semantics_arm", "") or ""
    )
    config.iteration5_smoke = bool(getattr(args, "iteration5_smoke", False))
    if str(getattr(config, "high_controller", "")) == "variable_roster_event":
        config.event_architecture_schema_version = 1
        config.event_opportunity_schedule = "uniform_active_gap_v1"
    config.r28_g1_arm = str(getattr(args, "r28_g1_arm", "off"))
    config.r28_g1_scorer_path = str(getattr(args, "r28_g1_scorer_path", "") or "")
    config.r28_g1_engineering_smoke = bool(
        getattr(args, "r28_g1_engineering_smoke", False)
    )
    config.r29_action_info_mode = str(
        getattr(args, "r29_action_info_mode", "off")
    )
    config.r29_action_info_coef = float(
        getattr(args, "r29_action_info_coef", R29_ACTION_INFO_REWARD_COEF)
    )
    config.r29_action_info_clip = float(
        getattr(args, "r29_action_info_clip", R29_ACTION_INFO_REWARD_CLIP)
    )
    if str(getattr(args, "r31_effect_mode", "")):
        config.r31_effect_mode = str(args.r31_effect_mode)
    if int(args.n_agents) > 0:
        config.n_agents = int(args.n_agents)
        config.n_uavs = int(args.n_agents)
        config.max_observed_uavs = max(int(args.n_agents), int(getattr(config, "max_observed_uavs", args.n_agents)))
    candidates = parse_int_tuple(args.skill_lifetime_candidates)
    if candidates:
        config.skill_lifetime_candidates = candidates
    if args.team_bridge_type:
        config.team_bridge_type = args.team_bridge_type
    if getattr(args, "z_assignment_residual_gain", None) is not None:
        config.z_assignment_residual_gain = float(args.z_assignment_residual_gain)
    if getattr(args, "team_disc_actionability_floor", None) is not None:
        config.team_disc_actionability_floor = float(args.team_disc_actionability_floor)
    if getattr(args, "assignment_actionability_coef", None) is not None:
        config.assignment_actionability_coef = float(args.assignment_actionability_coef)
    if getattr(args, "assignment_actionability_clip", None) is not None:
        config.assignment_actionability_clip = float(args.assignment_actionability_clip)
    if getattr(args, "assignment_actionability_warmup_steps", None) is not None:
        config.assignment_actionability_warmup_steps = int(args.assignment_actionability_warmup_steps)
    if args.low_level_architecture:
        config.low_level_architecture = args.low_level_architecture
    if int(args.opt_compact_dim) > 0:
        config.opt_compact_dim = int(args.opt_compact_dim)
    if int(args.opt_num_prototypes) > 0:
        config.opt_num_prototypes = int(args.opt_num_prototypes)
    if args.process_reward_mode:
        config.process_reward_mode = args.process_reward_mode
    if args.process_reward_injection:
        config.process_reward_injection = args.process_reward_injection
    optional_scalars = (
        "process_reward_coef",
        "process_reward_clip",
        "process_contrast_coef",
        "process_outcome_coef",
        "process_reward_contrast_coef",
        "process_reward_outcome_coef",
        "process_prior_coef",
        "process_shortcut_coef",
        "context_shortcut_coef",
        "process_shortcut_margin",
        "process_shortcut_margin_coef",
        "transition_skill_coef",
        "transition_skill_prior_coef",
        "transition_context_shortcut_coef",
        "transition_skill_reward_coef",
        "transition_skill_reward_clip",
        "outcome_residual_coef",
        "outcome_residual_reward_coef",
        "outcome_residual_reward_clip",
        "topology_role_coef",
        "topology_role_min_score",
        "topology_role_reward_coef",
        "topology_role_reward_clip",
        "topology_potential_coef",
        "topology_potential_clip",
        "skill_effect_ctrl_coef",
        "skill_effect_use_coef",
        "skill_effect_reward_clip",
        "skill_effect_min_gain",
        "skill_effect_min_positive_frac",
        "skill_force_disc_coef",
        "skill_force_effect_coef",
        "skill_force_duration_entropy_coef",
        "skill_force_clip",
        "skill_force_shortcut_margin",
        "semantic_shortcut_hard_stop_margin",
        "g_info_coef_skill",
        "g_info_coef_duration",
        "g_info_coef_edit",
        "intrinsic_segment_gate_margin",
        "intrinsic_segment_gate_min_residual_mi",
        "intrinsic_segment_gate_min_posterior_acc",
        "high_entropy_coef",
        "low_entropy_coef",
        "duration_entropy_floor_threshold",
        "duration_entropy_floor_coef",
        "z_entropy_floor_threshold",
        "z_entropy_floor_coef",
        "high_max_grad_norm",
        "low_max_grad_norm",
        "low_value_loss_coef",
        "low_clip_epsilon",
        "smdp_bootstrap_coef",
        "edit_penalty_alpha",
        "switch_penalty_beta",
        "opt_cd_coef",
        "opt_cmi_coef",
        "prototype_bank_ema_tau",
        "prototype_disc_reward_coef",
        "prototype_disc_clip",
        "prototype_disc_lr",
        "prototype_disc_prior_coef",
        "compact_return_coef",
        "team_transition_coef",
        "team_transition_clip",
        "team_transition_lr",
        "team_disc_coef",
        "team_disc_clip",
        "team_disc_lr",
    )
    for name in optional_scalars:
        value = getattr(args, name)
        if value is not None:
            setattr(config, name, value)
    if int(args.process_reward_warmup_steps) >= 0:
        config.process_reward_warmup_steps = int(args.process_reward_warmup_steps)
    if int(args.transition_skill_reward_warmup_steps) >= 0:
        config.transition_skill_reward_warmup_steps = int(args.transition_skill_reward_warmup_steps)
    if int(args.prototype_skill_extra_codes) >= 0:
        config.prototype_skill_extra_codes = int(args.prototype_skill_extra_codes)
    if int(args.legacy_n_skills) > 0:
        config.legacy_n_skills_override = int(args.legacy_n_skills)
    if int(args.prototype_disc_warmup_steps) >= 0:
        config.prototype_disc_warmup_steps = int(args.prototype_disc_warmup_steps)
    if int(args.prototype_disc_hidden_dim) > 0:
        config.prototype_disc_hidden_dim = int(args.prototype_disc_hidden_dim)
    if args.prototype_disc_condition:
        config.prototype_disc_condition = args.prototype_disc_condition
    if int(args.transition_skill_max_samples) > 0:
        config.transition_skill_max_samples = int(args.transition_skill_max_samples)
    if int(args.outcome_residual_horizon) > 0:
        config.outcome_residual_horizon = int(args.outcome_residual_horizon)
    if int(args.outcome_residual_hidden_dim) > 0:
        config.outcome_residual_hidden_dim = int(args.outcome_residual_hidden_dim)
    if args.outcome_residual_injection:
        config.outcome_residual_injection = args.outcome_residual_injection
    if int(args.topology_role_hidden_dim) > 0:
        config.topology_role_hidden_dim = int(args.topology_role_hidden_dim)
    if args.topology_role_injection:
        config.topology_role_injection = args.topology_role_injection
    if args.topology_potential_injection:
        config.topology_potential_injection = args.topology_potential_injection
    if args.topology_potential_discount_mode:
        config.topology_potential_discount_mode = args.topology_potential_discount_mode
    if int(args.topology_potential_warmup_steps) >= 0:
        config.topology_potential_warmup_steps = int(args.topology_potential_warmup_steps)
    effect_horizons = parse_int_tuple(args.skill_effect_horizons)
    if effect_horizons:
        config.skill_effect_horizons = effect_horizons
    if int(args.skill_effect_stride) > 0:
        config.skill_effect_stride = int(args.skill_effect_stride)
    if int(args.skill_effect_max_windows) > 0:
        config.skill_effect_max_windows = int(args.skill_effect_max_windows)
    if int(args.skill_effect_hidden_dim) > 0:
        config.skill_effect_hidden_dim = int(args.skill_effect_hidden_dim)
    if args.disable_skill_effect_group_balanced_loss:
        config.skill_effect_group_balanced_loss = False
    if int(args.skill_effect_intervention_max_samples) > 0:
        config.skill_effect_intervention_max_samples = int(args.skill_effect_intervention_max_samples)
    if int(args.skill_effect_warmup_steps) >= 0:
        config.skill_effect_warmup_steps = int(args.skill_effect_warmup_steps)
    if args.skill_effect_reward_injection:
        config.skill_effect_reward_injection = args.skill_effect_reward_injection
    if args.skill_force_reward_injection:
        config.skill_force_reward_injection = args.skill_force_reward_injection
    if int(args.skill_force_warmup_steps) >= 0:
        config.skill_force_warmup_steps = int(args.skill_force_warmup_steps)
    if args.disable_skill_force_shortcut_gate:
        config.skill_force_kill_on_shortcut = False
    if args.skill_force_use_comm_fields:
        config.skill_force_use_comm_fields = True
    if args.enable_skill_effect_probe:
        config.skill_effect_discovery_on = True
    if args.enable_skill_effect_intervention_probe:
        config.skill_effect_discovery_on = True
        config.skill_effect_intervention_probe_on = True
    if args.enable_skill_effect_reward:
        config.skill_effect_reward_on = True
        config.skill_effect_discovery_on = True
        if not getattr(config, "skill_effect_reward_injection", "none") or config.skill_effect_reward_injection == "none":
            config.skill_effect_reward_injection = "low_only"
    if args.enable_skill_forcing_probe:
        config.skill_force_probe_on = True
        config.skill_effect_discovery_on = True
    if args.enable_skill_forcing_reward:
        config.enable_skill_forcing_reward = True
        config.skill_force_probe_on = True
        config.skill_effect_discovery_on = True
        if not hasattr(config, "skill_force_reward_injection"):
            config.skill_force_reward_injection = "low_only"
    if args.enable_p2_recovery_compute:
        config.p2_recovery_credit_compute_on = True
    if args.enable_p2_recovery_reward:
        config.p2_recovery_credit_reward_on = True
        config.p2_recovery_credit_compute_on = True  # reward requires compute
    if args.p2_recovery_reward_level:
        config.p2_recovery_reward_level = args.p2_recovery_reward_level
    if args.p2_recovery_reward_coef is not None:
        config.p2_recovery_reward_coef = float(args.p2_recovery_reward_coef)
    if args.p2_recovery_reward_clip is not None:
        config.p2_recovery_reward_clip = float(args.p2_recovery_reward_clip)
    if int(args.semantic_shortcut_hard_stop_min_segments) > 0:
        config.semantic_shortcut_hard_stop_min_segments = int(args.semantic_shortcut_hard_stop_min_segments)
    if int(args.g_intervention_kl_max_segments) > 0:
        config.g_intervention_kl_max_segments = int(args.g_intervention_kl_max_segments)
    if int(args.g_info_warmup_steps) >= 0:
        config.g_info_warmup_steps = int(args.g_info_warmup_steps)
    if int(args.g_info_anneal_steps) >= 0:
        config.g_info_anneal_steps = int(args.g_info_anneal_steps)
    if int(args.g_info_max_segments) > 0:
        config.g_info_max_segments = int(args.g_info_max_segments)
    if args.enable_situation_diagnostics:
        config.enable_situation_diagnostics = True
    if args.enable_situation_hazard_control:
        config.enable_situation_hazard_control = True
    if args.enable_situation_hazard_conservative_guard:
        config.situation_hazard_conservative_guard = True
    if args.situation_substrate_source:
        config.situation_substrate_source = args.situation_substrate_source
    if args.situation_hazard_mode:
        config.situation_hazard_mode = args.situation_hazard_mode
    for name in (
        "situation_num_kappa",
        "situation_debounce_steps",
        "situation_hazard_check_interval",
        "situation_hazard_min_age",
        "situation_hazard_hidden_dim",
        "situation_hazard_min_dwell_checks",
        "situation_hazard_confirm_changes",
        "situation_hazard_rate_window",
    ):
        value = int(getattr(args, name, 0))
        if value > 0:
            setattr(config, name, value)
    for name in (
        "situation_hazard_entropy_coef",
        "situation_hazard_value_coef",
        "situation_hazard_clip_epsilon",
        "situation_hazard_reward_coef",
    ):
        value = getattr(args, name, None)
        if value is not None:
            setattr(config, name, float(value))
    if args.situation_hazard_max_force_rate is not None:
        config.situation_hazard_max_force_rate = float(args.situation_hazard_max_force_rate)
    if args.enable_team_transition_probe:
        config.enable_team_transition_probe = True
        config.enable_situation_diagnostics = True
    if args.enable_team_transition_reward:
        config.enable_team_transition_probe = True
        config.enable_team_transition_reward = True
        config.enable_situation_diagnostics = True
    if int(args.team_transition_warmup_steps) >= 0:
        config.team_transition_warmup_steps = int(args.team_transition_warmup_steps)
    if int(args.team_transition_hidden_dim) > 0:
        config.team_transition_hidden_dim = int(args.team_transition_hidden_dim)
    if args.enable_team_intent:
        config.enable_team_intent = True
    if args.enable_team_disc_probe:
        config.enable_team_disc_probe = True
        config.enable_team_intent = True
    if args.enable_team_disc_reward:
        config.enable_team_disc_probe = True
        config.enable_team_disc_reward = True
        config.enable_team_intent = True
    if int(args.team_intent_k) > 0:
        config.team_intent_k = int(args.team_intent_k)
    if int(args.team_disc_warmup_steps) >= 0:
        config.team_disc_warmup_steps = int(args.team_disc_warmup_steps)
    if int(args.team_disc_hidden_dim) > 0:
        config.team_disc_hidden_dim = int(args.team_disc_hidden_dim)
    if int(args.intrinsic_phase_bins) > 0:
        config.intrinsic_phase_bins = int(args.intrinsic_phase_bins)
    if int(args.intrinsic_segment_gate_min_segments) > 0:
        config.intrinsic_segment_gate_min_segments = int(args.intrinsic_segment_gate_min_segments)
    for name in (
        "low_rnn_hidden_size",
        "low_sequence_length",
        "low_sequence_batch_size",
        "low_ppo_epochs",
    ):
        value = int(getattr(args, name))
        if value > 0:
            setattr(config, name, value)
    if args.disable_process_reward:
        config.use_process_reward_for_discoverer = False
    if args.disable_process_posterior_mi:
        config.use_process_posterior_mi = False
    if args.disable_residual_process_posterior:
        config.use_residual_process_posterior = False
    if args.disable_context_skill_shortcut:
        config.use_context_skill_shortcut = False
    if args.disable_transition_skill_discriminator:
        config.use_transition_skill_discriminator = False
    if args.disable_transition_skill_team_conditioning:
        config.transition_skill_condition_on_team = False
    if args.disable_outcome_residual_probe:
        config.use_outcome_residual_probe = False
    if args.disable_outcome_residual_norm:
        config.normalize_outcome_residual_targets = False
    if args.disable_topology_role_probe:
        config.use_topology_role_probe = False
    if args.disable_semantic_shortcut_hard_stop:
        config.semantic_shortcut_hard_stop_enabled = False
    if args.semantic_shortcut_hard_stop_raise:
        config.semantic_shortcut_hard_stop_raise = True
    if args.disable_g_intervention_kl_diagnostic:
        config.use_g_intervention_kl_diagnostic = False
    if args.disable_g_info_diagnostic:
        config.use_g_info_diagnostic = False
    if args.enable_g_info_objective:
        config.enable_g_info_objective = True
    if args.enable_assignment_actionability_probe:
        config.enable_assignment_actionability_probe = True
    if args.enable_assignment_actionability_reward:
        config.enable_assignment_actionability_reward = True
    if args.no_assignment_actionability_soft:
        config.assignment_actionability_include_soft = False
    if args.enable_team_effect_target_audit:
        config.enable_team_effect_target_audit = True
    if getattr(args, "team_effect_audit_targets", None) is not None:
        config.team_effect_audit_targets = str(args.team_effect_audit_targets)
    if getattr(args, "team_effect_audit_horizons", None) is not None:
        config.team_effect_audit_horizons = str(args.team_effect_audit_horizons)
    if args.enable_team_conditioned_qd_probe:
        config.enable_team_conditioned_qd_probe = True
    if getattr(args, "team_conditioned_qd_hidden_dim", None) is not None:
        config.team_conditioned_qd_hidden_dim = int(args.team_conditioned_qd_hidden_dim)
    if getattr(args, "team_conditioned_qd_lr", None) is not None:
        config.team_conditioned_qd_lr = float(args.team_conditioned_qd_lr)
    if getattr(args, "team_conditioned_qd_min_samples", None) is not None:
        config.team_conditioned_qd_min_samples = int(args.team_conditioned_qd_min_samples)
    if args.r24_qd_export_windows:
        config.r24_qd_export_windows = True
    if args.r24_qd_export_dir:
        config.r24_qd_export_dir = str(args.r24_qd_export_dir)
    if getattr(args, "r24_qd_export_max_rows_per_update", None) is not None:
        config.r24_qd_export_max_rows_per_update = int(args.r24_qd_export_max_rows_per_update)
    if getattr(args, "r24_qd_export_seed", None) is not None:
        config.r24_qd_export_seed = int(args.r24_qd_export_seed)
    if bool(getattr(config, "r24_qd_export_windows", False)) and not str(
        getattr(config, "r24_qd_export_dir", "") or ""
    ):
        config.r24_qd_export_dir = str(Path(args.log_dir) / "r24_qd_windows")
    if args.enable_duration_entropy_floor:
        config.duration_entropy_floor_enabled = True
    if int(args.duration_entropy_floor_warmup_steps) >= 0:
        config.duration_entropy_floor_warmup_steps = int(args.duration_entropy_floor_warmup_steps)
    if args.enable_z_entropy_floor:
        config.z_entropy_floor_enabled = True
    if int(args.z_entropy_floor_warmup_steps) >= 0:
        config.z_entropy_floor_warmup_steps = int(args.z_entropy_floor_warmup_steps)
    if args.reward_ratio_guard_mode:
        config.reward_ratio_guard_mode = str(args.reward_ratio_guard_mode)
    if args.disable_intrinsic_segment_gate:
        config.intrinsic_segment_gate_enabled = False
    if args.enable_intrinsic_reward_norm:
        config.intrinsic_reward_normalize = True
    if args.disable_smdp_discounted_high_return:
        config.use_smdp_discounted_high_return = False
    if args.disable_smdp_bootstrap:
        config.use_smdp_bootstrap = False
    if args.disable_high_value_norm:
        config.use_high_value_norm = False
    if args.disable_recurrent_low_level:
        config.use_recurrent_low_level = False
    if args.disable_low_value_norm:
        config.use_low_value_norm = False
    if args.enable_low_actor_team_code:
        config.low_actor_condition_on_team_code = True
    if args.enable_prototype_response_skills:
        config.use_prototype_response_skills = True
        config.high_condition_on_omega = True
    if args.parallel_selection:
        config.parallel_selection = True
        config.use_autoregressive_selection = False
    if args.ar_prefix_mode:
        config.ar_prefix_mode = args.ar_prefix_mode
    if args.enable_high_omega_conditioning:
        config.high_condition_on_omega = True
    if args.enable_agent_prototype_relevance:
        config.use_agent_prototype_relevance = True
    if args.enable_per_agent_kappa:
        config.use_per_agent_kappa = True
        config.enable_situation_diagnostics = True
    if args.enable_prototype_disc_probe:
        config.enable_prototype_disc_probe = True
    if args.enable_prototype_disc_reward:
        config.enable_prototype_disc_probe = True
        config.enable_prototype_disc_reward = True
    if args.prototype_disc_use_learned_prior:
        config.prototype_disc_use_learned_prior = True
    if args.enable_compact_return_head:
        config.use_compact_return_head = True
    if args.enable_topology_potential_shaping:
        config.use_topology_potential_shaping = True
    if args.topology_potential_positive_only:
        config.topology_potential_positive_only = True
    if bool(getattr(config, "enable_team_intent", False)):
        if str(getattr(config, "team_bridge_type", "stochastic")) == "none":
            raise ValueError("--enable_team_intent requires team_bridge_type to be deterministic or stochastic, not none")
        config.low_actor_condition_on_team_code = False


def resolve_device(requested: str) -> str:
    if requested == "cuda" and not torch.cuda.is_available():
        return "cpu"
    return requested


def create_env(config, scenario: str, seed: int, rank: int, scale_mode: str):
    return make_env(
        config,
        EnvSpec(
            scenario=normalize_scenario(scenario),
            seed=int(seed),
            rank=int(rank),
            scale_mode=scale_mode,
        ),
    )()


def create_envs(config, args: argparse.Namespace, scale_mode: str, num_envs: int):
    return [
        create_env(
            config,
            scenario=config.scenario,
            seed=int(args.seed),
            rank=env_id,
            scale_mode=scale_mode,
        )
        for env_id in range(max(int(num_envs), 1))
    ]


def create_collector(config, args: argparse.Namespace, scale_mode: str, num_envs: int):
    if args.collector_backend == "subproc":
        return SubprocEnvCollector(
            config=config,
            scenario=config.scenario,
            seed=int(args.seed),
            num_envs=max(int(num_envs), 1),
            scale_mode=scale_mode,
            start_method=args.collector_start_method,
        )
    return SyncEnvCollector(create_envs(config, args, scale_mode=scale_mode, num_envs=num_envs))


def action_space_details(env) -> tuple[str, Any, Any]:
    action_dtype = getattr(env.action_space, "dtype", np.int64)
    action_space_type = "continuous" if np.issubdtype(action_dtype, np.floating) else "discrete"
    action_low = env.action_space.low[0] if action_space_type == "continuous" else None
    action_high = env.action_space.high[0] if action_space_type == "continuous" else None
    return action_space_type, action_low, action_high


def create_agent(
    config,
    args: argparse.Namespace,
    env,
    num_envs: int,
    state_dim: int | None = None,
) -> StandaloneProcessAgent:
    action_space_type, action_low, action_high = action_space_details(env)
    return StandaloneProcessAgent(
        obs_dim=int(env.obs_dim),
        action_dim=int(env.action_dim),
        n_agents=int(env.n_uavs),
        config=config,
        device=resolve_device(args.device),
        action_space_type=action_space_type,
        action_low=action_low,
        action_high=action_high,
        num_envs=max(int(num_envs), 1),
        state_dim=state_dim or getattr(env, "state_dim", None),
    )
