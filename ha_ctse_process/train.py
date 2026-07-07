"""Standalone training entrypoint for the HA-CTSE process-core algorithm.

This file is deliberately not a wrapper around ``train_multiproc_config_1.py``
or ``hmasd.agent``.  It owns the new algorithm's train/eval/checkpoint flow and
only reuses the shared environment/config infrastructure.
"""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import torch

try:
    from torch.utils.tensorboard import SummaryWriter
except ModuleNotFoundError:
    SummaryWriter = None

from ha_ctse_process.env_factory import EnvSpec, make_env, normalize_scenario
from ha_ctse_process.collectors import SubprocEnvCollector, SyncEnvCollector
from ha_ctse_process.plotting import (
    EVAL_FIELDS,
    UPDATE_FIELDS,
    append_csv,
    extract_uav_metrics,
    save_eval_plots,
    save_update_plots,
)
from ha_ctse_process.standalone_agent import (
    Rollout,
    SegmentManager,
    StandaloneProcessAgent,
)
from ha_ctse_process.topology_viz import capture_topology_frame, save_topology_artifacts


ALGORITHM_MANIFEST_FIELDS = (
    "algorithm",
    "network_scale_profile",
    "low_level_architecture",
    "policy_update_mode",
    "allow_off_policy_policy_updates",
    "process_segment_replay_enabled",
    "n_z",
    "skill_lifetime_candidates",
    "process_segment_mode",
    "allow_early_duration_termination",
    "opt_compact_dim",
    "opt_num_prototypes",
    "opt_use_sparsemax",
    "opt_cd_coef",
    "opt_cmi_coef",
    "use_prototype_response_skills",
    "prototype_skill_extra_codes",
    "legacy_n_skills_override",
    "use_autoregressive_selection",
    "parallel_selection",
    "high_condition_on_omega",
    "use_agent_prototype_relevance",
    "prototype_bank_ema_tau",
    "use_per_agent_kappa",
    "enable_prototype_disc_probe",
    "enable_prototype_disc_reward",
    "prototype_disc_reward_coef",
    "prototype_disc_clip",
    "prototype_disc_warmup_steps",
    "prototype_disc_condition",
    "prototype_disc_lr",
    "prototype_disc_hidden_dim",
    "prototype_disc_use_learned_prior",
    "prototype_disc_prior_coef",
    "use_compact_return_head",
    "compact_return_coef",
    "team_bridge_type",
    "team_code_dim",
    "num_team_codes",
    "enable_team_intent",
    "enable_team_disc_probe",
    "enable_team_disc_reward",
    "team_intent_k",
    "team_disc_coef",
    "team_disc_clip",
    "team_disc_warmup_steps",
    "team_disc_lr",
    "team_disc_hidden_dim",
    "process_encoder_embedding_dim",
    "lr_process_encoder",
    "process_contrast_coef",
    "process_outcome_coef",
    "process_reward_mode",
    "process_reward_injection",
    "process_reward_coef",
    "process_reward_contrast_coef",
    "process_reward_outcome_coef",
    "process_reward_clip",
    "normalize_process_outcomes",
    "use_process_reward_for_discoverer",
    "use_process_posterior_mi",
    "use_residual_process_posterior",
    "process_posterior_condition_on_team",
    "process_shortcut_coef",
    "use_context_skill_shortcut",
    "context_shortcut_coef",
    "intrinsic_phase_bins",
    "process_shortcut_margin",
    "process_shortcut_margin_coef",
    "process_reward_warmup_steps",
    "use_transition_skill_discriminator",
    "transition_skill_condition_on_team",
    "transition_skill_coef",
    "transition_skill_prior_coef",
    "transition_context_shortcut_coef",
    "transition_skill_reward_coef",
    "transition_skill_reward_warmup_steps",
    "transition_skill_reward_clip",
    "transition_skill_max_samples",
    "use_outcome_residual_probe",
    "outcome_residual_horizon",
    "outcome_residual_coef",
    "outcome_residual_hidden_dim",
    "normalize_outcome_residual_targets",
    "outcome_residual_injection",
    "outcome_residual_reward_coef",
    "outcome_residual_reward_clip",
    "use_topology_role_probe",
    "topology_role_coef",
    "topology_role_hidden_dim",
    "topology_role_min_score",
    "topology_role_injection",
    "topology_role_reward_coef",
    "topology_role_reward_clip",
    "use_topology_potential_shaping",
    "topology_potential_injection",
    "topology_potential_coef",
    "topology_potential_clip",
    "topology_potential_warmup_steps",
    "topology_potential_discount_mode",
    "topology_potential_positive_only",
    "skill_effect_discovery_on",
    "skill_effect_reward_on",
    "skill_effect_reward_injection",
    "skill_effect_horizons",
    "skill_effect_stride",
    "skill_effect_max_windows",
    "skill_effect_hidden_dim",
    "skill_effect_group_balanced_loss",
    "skill_effect_intervention_probe_on",
    "skill_effect_intervention_max_samples",
    "skill_effect_warmup_steps",
    "skill_effect_ctrl_coef",
    "skill_effect_use_coef",
    "skill_effect_reward_clip",
    "skill_effect_min_gain",
    "skill_effect_min_positive_frac",
    "skill_force_probe_on",
    "enable_skill_forcing_reward",
    "skill_force_reward_injection",
    "skill_force_disc_coef",
    "skill_force_effect_coef",
    "skill_force_duration_entropy_coef",
    "skill_force_warmup_steps",
    "skill_force_clip",
    "skill_force_shortcut_margin",
    "skill_force_kill_on_shortcut",
    "skill_force_use_comm_fields",
    "semantic_shortcut_hard_stop_enabled",
    "semantic_shortcut_hard_stop_margin",
    "semantic_shortcut_hard_stop_min_segments",
    "semantic_shortcut_hard_stop_raise",
    "use_g_intervention_kl_diagnostic",
    "g_intervention_kl_max_segments",
    "use_g_info_diagnostic",
    "enable_g_info_objective",
    "g_info_coef_skill",
    "g_info_coef_duration",
    "g_info_coef_edit",
    "g_info_warmup_steps",
    "g_info_anneal_steps",
    "g_info_max_segments",
    "situation_substrate_source",
    "situation_num_kappa",
    "situation_debounce_steps",
    "enable_situation_diagnostics",
    "enable_situation_hazard_control",
    "situation_hazard_mode",
    "situation_hazard_check_interval",
    "situation_hazard_min_age",
    "situation_hazard_hidden_dim",
    "situation_hazard_entropy_coef",
    "situation_hazard_value_coef",
    "situation_hazard_clip_epsilon",
    "situation_hazard_reward_coef",
    "situation_hazard_conservative_guard",
    "situation_hazard_min_dwell_checks",
    "situation_hazard_confirm_changes",
    "situation_hazard_max_force_rate",
    "situation_hazard_rate_window",
    "enable_team_transition_probe",
    "enable_team_transition_reward",
    "team_transition_coef",
    "team_transition_clip",
    "team_transition_warmup_steps",
    "team_transition_lr",
    "team_transition_hidden_dim",
    "intrinsic_segment_gate_enabled",
    "intrinsic_segment_gate_margin",
    "intrinsic_segment_gate_min_segments",
    "intrinsic_segment_gate_min_residual_mi",
    "intrinsic_segment_gate_min_posterior_acc",
    "intrinsic_reward_normalize",
    "process_prior_coef",
    "use_smdp_discounted_high_return",
    "use_smdp_bootstrap",
    "smdp_bootstrap_coef",
    "use_high_value_norm",
    "use_recurrent_low_level",
    "use_centralized_low_value",
    "use_low_value_norm",
    "low_rnn_hidden_size",
    "low_sequence_length",
    "low_sequence_batch_size",
    "low_ppo_epochs",
    "low_gae_lambda",
    "low_value_clip",
    "low_value_loss_coef",
    "low_clip_epsilon",
    "low_max_grad_norm",
    "edit_penalty_alpha",
    "switch_penalty_beta",
)

TRAINING_MANIFEST_FIELDS = (
    "gamma",
    "clip_epsilon",
    "low_clip_epsilon",
    "high_entropy_coef",
    "low_entropy_coef",
    "duration_entropy_floor_enabled",
    "duration_entropy_floor_threshold",
    "duration_entropy_floor_coef",
    "duration_entropy_floor_warmup_steps",
    "z_entropy_floor_enabled",
    "z_entropy_floor_threshold",
    "z_entropy_floor_coef",
    "z_entropy_floor_warmup_steps",
    "reward_ratio_guard_mode",
    "high_max_grad_norm",
    "low_max_grad_norm",
    "lr",
    "lr_actor",
    "lr_critic",
    "lr_high",
    "batch_size",
    "minibatch_size",
    "ppo_epochs",
    "rollout_length",
    "total_timesteps",
    "eval_interval",
)

MODEL_MANIFEST_FIELDS = (
    "hidden_size",
    "embedding_dim",
    "n_heads",
    "n_encoder_layers",
    "n_decoder_layers",
    "gru_hidden_size",
    "state_dim",
    "obs_dim",
    "action_dim",
    "n_agents",
    "n_uavs",
)

PHYSICAL_MANIFEST_FIELDS = (
    "scenario",
    "experiment_preset",
    "area_size",
    "max_steps",
    "episode_length",
    "n_users",
    "n_uavs",
    "n_agents",
    "n_ground_bs",
    "max_connections",
    "coverage_radius",
    "communication_range",
    "uav_communication_range",
    "ground_bs_communication_range",
    "bandwidth",
    "carrier_frequency",
    "tx_power",
    "noise_power",
    "routing_protocol",
    "max_hops",
    "backhaul_margin_target_mbps",
    "backhaul_guard_min_capacity_mbps",
    "enable_backhaul_action_guard",
    "battery_enabled",
    "battery_capacity_wh",
    "initial_battery_ratio",
    "low_battery_threshold",
    "critical_battery_threshold",
    "depleted_battery_threshold",
    "n_charging_stations",
    "max_energy_charging_stations",
    "charging_radius_m",
    "scenario7_reward_model",
    "scenario7_reward_variant",
    "scenario7_experiment_arm",
    "return_cost_cap",
    "lambda_return",
    "cutoff_event_penalty",
    "depletion_event_penalty",
)


def jsonable(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return jsonable(value.tolist())
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (tuple, list)):
        return [jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, Path):
        return str(value)
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def pick_attrs(obj: Any, names: tuple[str, ...]) -> dict[str, Any]:
    result = {}
    for name in names:
        if hasattr(obj, name):
            result[name] = jsonable(getattr(obj, name))
    return result


def export_run_manifest(
    args: argparse.Namespace,
    config,
    env: Any | None = None,
    agent: StandaloneProcessAgent | None = None,
    total_steps: int = 0,
    update_idx: int = 0,
    mode: str = "train",
) -> None:
    """Write the experiment parameters that explain the scalar plots."""

    metadata_dir = Path(args.log_dir) / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    env_state = {}
    if env is not None and hasattr(env, "get_current_state"):
        try:
            env_state = env.get_current_state() or {}
        except Exception:
            env_state = {}
    manifest = {
        "mode": mode,
        "total_steps": int(total_steps),
        "update_idx": int(update_idx),
        "args": jsonable(vars(args)),
        "algorithm_config": pick_attrs(config, ALGORITHM_MANIFEST_FIELDS),
        "training_config": pick_attrs(config, TRAINING_MANIFEST_FIELDS),
        "model_config": pick_attrs(config, MODEL_MANIFEST_FIELDS),
        "physical_env_config": pick_attrs(config, PHYSICAL_MANIFEST_FIELDS),
        "env_runtime_spec": {},
        "agent_runtime_spec": {},
    }
    if env is not None:
        for name in ("obs_dim", "state_dim", "action_dim", "n_uavs", "n_agents", "n_users"):
            if hasattr(env, name):
                manifest["env_runtime_spec"][name] = jsonable(getattr(env, name))
    if env_state:
        for name in (
            "area_size",
            "max_steps",
            "n_charging_stations",
            "charging_radius_m",
            "battery_enabled",
            "energy_stage",
        ):
            if name in env_state:
                manifest["env_runtime_spec"][name] = jsonable(env_state[name])
    if agent is not None:
        manifest["agent_runtime_spec"] = {
            "obs_dim": int(agent.obs_dim),
            "action_dim": int(agent.action_dim),
            "n_agents": int(agent.n_agents),
            "n_skills": int(agent.n_skills),
            "duration_candidates": jsonable(agent.duration_candidates),
            "action_space_type": str(agent.action_space_type),
            "device": str(agent.device),
            "use_recurrent_low_level": bool(agent.use_recurrent_low_level),
            "low_level_architecture": str(agent.low_level_architecture),
            "low_actor_condition_on_team_code": bool(getattr(agent, "low_actor_condition_on_team_code", False)),
            "use_prototype_response_skills": bool(getattr(agent, "use_prototype_response_skills", False)),
            "use_autoregressive_selection": bool(getattr(agent, "use_autoregressive_selection", False)),
            "parallel_selection": bool(getattr(agent, "parallel_selection", False)),
            "ar_prefix_mode": str(getattr(agent, "ar_prefix_mode", "none")),
            "prototype_disc_use_learned_prior": bool(
                getattr(agent, "prototype_disc_use_learned_prior", False)
            ),
            "low_rnn_hidden_size": int(agent.low_rnn_hidden_size),
            "parameter_counts": jsonable(agent.parameter_counts()),
        }
    with (metadata_dir / "run_manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)


def emit(args: argparse.Namespace, message: str) -> None:
    print(message)
    log_dir = Path(getattr(args, "log_dir", "logs/ha_ctse_process_standalone"))
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        with (log_dir / "standalone_train.log").open("a", encoding="utf-8") as handle:
            handle.write(message + "\n")
    except OSError:
        pass


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
    parser.add_argument("--num_envs", type=int, default=1)
    parser.add_argument("--n_agents", type=int, default=0)
    parser.add_argument("--collector_backend", choices=("sync", "subproc"), default="sync")
    parser.add_argument("--collector_start_method", choices=("spawn", "forkserver", "fork"), default="spawn")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--save_interval", type=int, default=10)
    parser.add_argument("--checkpoint_keep_last", type=int, default=3)
    parser.add_argument("--resume_from", default="")
    parser.add_argument("--eval_interval", type=int, default=0)
    parser.add_argument("--eval_episodes", type=int, default=3)
    parser.add_argument("--eval_max_steps", type=int, default=0)
    parser.add_argument(
        "--eval_action_mode",
        choices=("deterministic", "stochastic"),
        default="deterministic",
    )
    parser.add_argument("--save_topology", action="store_true")
    parser.add_argument("--topology_interval", type=int, default=25)
    parser.add_argument("--topology_episodes", type=int, default=1)
    parser.add_argument("--topology_max_frames", type=int, default=160)
    parser.add_argument("--plot_interval", type=int, default=1)
    parser.add_argument("--skill_lifetime_candidates", default="")
    parser.add_argument("--team_bridge_type", choices=("none", "deterministic", "stochastic"), default="")
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


def checkpoint_payload(
    agent: StandaloneProcessAgent,
    args: argparse.Namespace,
    config,
    total_steps: int,
    update_idx: int,
) -> dict[str, Any]:
    return {
        "high": agent.high.state_dict(),
        "compact": agent.compact.state_dict(),
        "bridge": agent.bridge.state_dict(),
        "low": agent.low.state_dict(),
        "process": agent.process.state_dict(),
        "process_posterior": agent.process_posterior.state_dict(),
        "outcome_residual_probe": (
            agent.outcome_residual_probe.state_dict()
            if getattr(agent, "outcome_residual_probe", None) is not None
            else None
        ),
        "topology_role_probe": (
            agent.topology_role_probe.state_dict()
            if getattr(agent, "topology_role_probe", None) is not None
            else None
        ),
        "transition_discriminator": (
            agent.transition_discriminator.state_dict()
            if getattr(agent, "transition_discriminator", None) is not None
            else None
        ),
        "prototype_discriminator": (
            agent.prototype_discriminator.state_dict()
            if getattr(agent, "prototype_discriminator", None) is not None
            else None
        ),
        "compact_return_head": (
            agent.compact_return_head.state_dict()
            if getattr(agent, "compact_return_head", None) is not None
            else None
        ),
        "situation_hazard": (
            agent.situation_hazard.state_dict()
            if getattr(agent, "situation_hazard", None) is not None
            else None
        ),
        "skill_effect_discovery": (
            agent.skill_effect_discovery.state_dict()
            if getattr(agent, "skill_effect_discovery", None) is not None
            else None
        ),
        "team_transition": (
            agent.team_transition.state_dict()
            if getattr(agent, "team_transition", None) is not None
            else None
        ),
        "team_discriminator": (
            agent.team_discriminator.state_dict()
            if getattr(agent, "team_discriminator", None) is not None
            else None
        ),
        "team_intent_prior_counts": (
            torch.as_tensor(
                np.asarray(getattr(agent, "team_intent_prior_counts", []), dtype=np.float64),
                dtype=torch.float64,
            )
            if getattr(agent, "enable_team_intent", False)
            else None
        ),
        "high_opt": agent.high_opt.state_dict(),
        "low_opt": agent.low_opt.state_dict() if agent.low_opt is not None else None,
        "low_actor_opt": agent.low_actor_opt.state_dict() if agent.low_actor_opt is not None else None,
        "low_critic_opt": agent.low_critic_opt.state_dict() if agent.low_critic_opt is not None else None,
        "high_value_norm": agent.high_value_norm.state_dict() if agent.high_value_norm is not None else None,
        "low_value_norm": agent.low_value_norm.state_dict() if agent.low_value_norm is not None else None,
        "process_opt": agent.process_opt.state_dict(),
        "prototype_disc_opt": (
            agent.prototype_disc_opt.state_dict()
            if getattr(agent, "prototype_disc_opt", None) is not None
            else None
        ),
        "skill_effect_opt": (
            agent.skill_effect_discovery.opt.state_dict()
            if getattr(agent, "skill_effect_discovery", None) is not None
            else None
        ),
        "team_transition_opt": (
            agent.team_transition_opt.state_dict()
            if getattr(agent, "team_transition_opt", None) is not None
            else None
        ),
        "team_disc_opt": (
            agent.team_disc_opt.state_dict()
            if getattr(agent, "team_disc_opt", None) is not None
            else None
        ),
        "total_steps": int(total_steps),
        "update_idx": int(update_idx),
        "config_name": args.config,
        "preset": args.preset,
        "scenario": config.scenario,
        "action_space_type": agent.action_space_type,
        "action_dim": agent.action_dim,
        "team_bridge_type": str(getattr(config, "team_bridge_type", "stochastic")),
        "n_agents": agent.n_agents,
        "n_skills": agent.n_skills,
        "duration_candidates": agent.duration_candidates,
        "opt_num_prototypes": int(getattr(agent, "opt_num_prototypes", getattr(config, "opt_num_prototypes", 0))),
        "use_recurrent_low_level": bool(agent.use_recurrent_low_level),
        "low_level_architecture": str(agent.low_level_architecture),
        "low_actor_condition_on_team_code": bool(getattr(agent, "low_actor_condition_on_team_code", False)),
        "use_prototype_response_skills": bool(getattr(agent, "use_prototype_response_skills", False)),
        "prototype_skill_extra_codes": int(getattr(agent, "prototype_skill_extra_codes", 0)),
        "legacy_n_skills_override": int(getattr(config, "legacy_n_skills_override", 0)),
        "use_autoregressive_selection": bool(getattr(agent, "use_autoregressive_selection", True)),
        "parallel_selection": bool(getattr(agent, "parallel_selection", False)),
        "ar_prefix_mode": str(getattr(agent, "ar_prefix_mode", "none")),
        "high_condition_on_omega": bool(getattr(agent, "high_condition_on_omega", False)),
        "use_agent_prototype_relevance": bool(getattr(agent, "use_agent_prototype_relevance", False)),
        "use_per_agent_kappa": bool(getattr(agent, "use_per_agent_kappa", False)),
        "enable_prototype_disc_probe": bool(getattr(agent, "enable_prototype_disc_probe", False)),
        "enable_prototype_disc_reward": bool(getattr(agent, "enable_prototype_disc_reward", False)),
        "prototype_disc_condition": str(getattr(agent, "prototype_disc_condition", "kappa")),
        "prototype_disc_use_learned_prior": bool(getattr(agent, "prototype_disc_use_learned_prior", False)),
        "use_compact_return_head": bool(getattr(agent, "use_compact_return_head", False)),
        "enable_team_transition_probe": bool(getattr(agent, "enable_team_transition_probe", False)),
        "enable_team_transition_reward": bool(getattr(agent, "enable_team_transition_reward", False)),
        "team_transition_coef": float(getattr(agent, "team_transition_coef", 0.0)),
        "team_transition_clip": float(getattr(agent, "team_transition_clip", 0.0)),
        "team_transition_warmup_steps": int(getattr(agent, "team_transition_warmup_steps", 0)),
        "enable_team_intent": bool(getattr(agent, "enable_team_intent", False)),
        "team_intent_k": int(getattr(agent, "team_intent_k", 0)),
        "enable_team_disc_probe": bool(getattr(agent, "enable_team_disc_probe", False)),
        "enable_team_disc_reward": bool(getattr(agent, "enable_team_disc_reward", False)),
        "team_disc_coef": float(getattr(agent, "team_disc_coef", 0.0)),
        "team_disc_clip": float(getattr(agent, "team_disc_clip", 0.0)),
        "team_disc_warmup_steps": int(getattr(agent, "team_disc_warmup_steps", 0)),
        "team_disc_hidden_dim": int(getattr(config, "team_disc_hidden_dim", 128)),
        "z_entropy_floor_enabled": bool(getattr(agent, "z_entropy_floor_enabled", False)),
        "z_entropy_floor_threshold": float(getattr(agent, "z_entropy_floor_threshold", 0.0)),
        "z_entropy_floor_coef": float(getattr(agent, "z_entropy_floor_coef", 0.0)),
        "z_entropy_floor_warmup_steps": int(getattr(agent, "z_entropy_floor_warmup_steps", 0)),
        "algorithm": "ha_ctse_process_standalone",
    }


def save_checkpoint(
    path: Path,
    agent: StandaloneProcessAgent,
    args: argparse.Namespace,
    config,
    total_steps: int,
    update_idx: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint_payload(agent, args, config, total_steps, update_idx), path)


def prune_periodic_checkpoints(log_dir: str | Path, keep_last: int) -> None:
    keep_last = int(keep_last)
    if keep_last <= 0:
        return
    paths = sorted(
        Path(log_dir).glob("standalone_process_core_update_*.pt"),
        key=lambda path: path.stat().st_mtime,
    )
    for path in paths[:-keep_last]:
        try:
            path.unlink()
        except OSError:
            pass


def load_checkpoint(
    path: str | Path,
    agent: StandaloneProcessAgent,
    load_optimizers: bool = True,
) -> tuple[int, int]:
    checkpoint = torch.load(Path(path), map_location=agent.device)
    agent.high.load_state_dict(checkpoint["high"])
    if "compact" in checkpoint:
        agent.compact.load_state_dict(checkpoint["compact"])
    if "bridge" in checkpoint:
        agent.bridge.load_state_dict(checkpoint["bridge"])
    try:
        agent.low.load_state_dict(checkpoint["low"])
    except RuntimeError as exc:
        raise RuntimeError(
            "Low-level checkpoint architecture does not match the current agent. "
            "If this is an older feedforward checkpoint, rerun with "
            "--disable_recurrent_low_level; if it is a recurrent checkpoint, "
            "keep recurrent low-level enabled and match low_rnn_hidden_size."
        ) from exc
    agent.process.load_state_dict(checkpoint["process"])
    if "process_posterior" in checkpoint:
        agent.process_posterior.load_state_dict(checkpoint["process_posterior"], strict=False)
    if (
        "outcome_residual_probe" in checkpoint
        and checkpoint.get("outcome_residual_probe") is not None
        and getattr(agent, "outcome_residual_probe", None) is not None
    ):
        agent.outcome_residual_probe.load_state_dict(checkpoint["outcome_residual_probe"], strict=False)
    if (
        "topology_role_probe" in checkpoint
        and checkpoint.get("topology_role_probe") is not None
        and getattr(agent, "topology_role_probe", None) is not None
    ):
        agent.topology_role_probe.load_state_dict(checkpoint["topology_role_probe"], strict=False)
    if (
        "transition_discriminator" in checkpoint
        and checkpoint.get("transition_discriminator") is not None
        and getattr(agent, "transition_discriminator", None) is not None
    ):
        agent.transition_discriminator.load_state_dict(checkpoint["transition_discriminator"], strict=False)
    if (
        "prototype_discriminator" in checkpoint
        and checkpoint.get("prototype_discriminator") is not None
        and getattr(agent, "prototype_discriminator", None) is not None
    ):
        agent.prototype_discriminator.load_state_dict(checkpoint["prototype_discriminator"], strict=False)
    if (
        "compact_return_head" in checkpoint
        and checkpoint.get("compact_return_head") is not None
        and getattr(agent, "compact_return_head", None) is not None
    ):
        agent.compact_return_head.load_state_dict(checkpoint["compact_return_head"], strict=False)
    if (
        "situation_hazard" in checkpoint
        and checkpoint.get("situation_hazard") is not None
        and getattr(agent, "situation_hazard", None) is not None
    ):
        agent.situation_hazard.load_state_dict(checkpoint["situation_hazard"], strict=False)
    if (
        "skill_effect_discovery" in checkpoint
        and checkpoint.get("skill_effect_discovery") is not None
        and getattr(agent, "skill_effect_discovery", None) is not None
    ):
        try:
            agent.skill_effect_discovery.load_state_dict(checkpoint["skill_effect_discovery"], strict=False)
        except RuntimeError:
            pass
    if (
        "team_transition" in checkpoint
        and checkpoint.get("team_transition") is not None
        and getattr(agent, "team_transition", None) is not None
    ):
        agent.team_transition.load_state_dict(checkpoint["team_transition"], strict=False)
    if (
        "team_discriminator" in checkpoint
        and checkpoint.get("team_discriminator") is not None
        and getattr(agent, "team_discriminator", None) is not None
    ):
        agent.team_discriminator.load_state_dict(checkpoint["team_discriminator"], strict=False)
    if "team_intent_prior_counts" in checkpoint and checkpoint.get("team_intent_prior_counts") is not None:
        raw_prior_counts = checkpoint["team_intent_prior_counts"]
        if isinstance(raw_prior_counts, torch.Tensor):
            prior_counts = raw_prior_counts.detach().cpu().numpy().astype(np.float64).reshape(-1)
        else:
            prior_counts = np.asarray(raw_prior_counts, dtype=np.float64).reshape(-1)
        if prior_counts.size > 0 and hasattr(agent, "team_intent_prior_counts"):
            fitted = np.ones_like(agent.team_intent_prior_counts, dtype=np.float64)
            fitted[: min(fitted.size, prior_counts.size)] = prior_counts[: min(fitted.size, prior_counts.size)]
            agent.team_intent_prior_counts = np.maximum(fitted, 1e-6)
    if load_optimizers:
        if "high_opt" in checkpoint:
            try:
                agent.high_opt.load_state_dict(checkpoint["high_opt"])
            except ValueError:
                pass
        if "low_opt" in checkpoint and checkpoint.get("low_opt") is not None and agent.low_opt is not None:
            agent.low_opt.load_state_dict(checkpoint["low_opt"])
        if (
            "low_actor_opt" in checkpoint
            and checkpoint.get("low_actor_opt") is not None
            and agent.low_actor_opt is not None
        ):
            agent.low_actor_opt.load_state_dict(checkpoint["low_actor_opt"])
        if (
            "low_critic_opt" in checkpoint
            and checkpoint.get("low_critic_opt") is not None
            and agent.low_critic_opt is not None
        ):
            agent.low_critic_opt.load_state_dict(checkpoint["low_critic_opt"])
        if checkpoint.get("high_value_norm") is not None and agent.high_value_norm is not None:
            agent.high_value_norm.load_state_dict(checkpoint["high_value_norm"])
        if checkpoint.get("low_value_norm") is not None and agent.low_value_norm is not None:
            agent.low_value_norm.load_state_dict(checkpoint["low_value_norm"])
        if "process_opt" in checkpoint:
            try:
                agent.process_opt.load_state_dict(checkpoint["process_opt"])
            except ValueError:
                pass
        if (
            "prototype_disc_opt" in checkpoint
            and checkpoint.get("prototype_disc_opt") is not None
            and getattr(agent, "prototype_disc_opt", None) is not None
        ):
            try:
                agent.prototype_disc_opt.load_state_dict(checkpoint["prototype_disc_opt"])
            except ValueError:
                pass
        if (
            "skill_effect_opt" in checkpoint
            and checkpoint.get("skill_effect_opt") is not None
            and getattr(agent, "skill_effect_discovery", None) is not None
        ):
            try:
                agent.skill_effect_discovery.opt.load_state_dict(checkpoint["skill_effect_opt"])
            except ValueError:
                pass
        if (
            "team_transition_opt" in checkpoint
            and checkpoint.get("team_transition_opt") is not None
            and getattr(agent, "team_transition_opt", None) is not None
        ):
            try:
                agent.team_transition_opt.load_state_dict(checkpoint["team_transition_opt"])
            except ValueError:
                pass
        if (
            "team_disc_opt" in checkpoint
            and checkpoint.get("team_disc_opt") is not None
            and getattr(agent, "team_disc_opt", None) is not None
        ):
            try:
                agent.team_disc_opt.load_state_dict(checkpoint["team_disc_opt"])
            except ValueError:
                pass
    return int(checkpoint.get("total_steps", 0)), int(checkpoint.get("update_idx", 0))


def load_checkpoint_metadata(path: str | Path) -> dict[str, Any]:
    checkpoint = torch.load(Path(path), map_location="cpu")
    return {
        "duration_candidates": checkpoint.get("duration_candidates"),
        "n_agents": checkpoint.get("n_agents"),
        "n_skills": checkpoint.get("n_skills"),
        "opt_num_prototypes": checkpoint.get("opt_num_prototypes"),
        "preset": checkpoint.get("preset"),
        "scenario": checkpoint.get("scenario"),
        "team_bridge_type": checkpoint.get("team_bridge_type"),
        "total_steps": checkpoint.get("total_steps"),
        "update_idx": checkpoint.get("update_idx"),
        "low_actor_condition_on_team_code": checkpoint.get("low_actor_condition_on_team_code"),
        "use_prototype_response_skills": checkpoint.get("use_prototype_response_skills"),
        "prototype_skill_extra_codes": checkpoint.get("prototype_skill_extra_codes"),
        "legacy_n_skills_override": checkpoint.get("legacy_n_skills_override"),
        "use_autoregressive_selection": checkpoint.get("use_autoregressive_selection"),
        "parallel_selection": checkpoint.get("parallel_selection"),
        "ar_prefix_mode": checkpoint.get("ar_prefix_mode"),
        "high_condition_on_omega": checkpoint.get("high_condition_on_omega"),
        "use_agent_prototype_relevance": checkpoint.get("use_agent_prototype_relevance"),
        "use_per_agent_kappa": checkpoint.get("use_per_agent_kappa"),
        "enable_prototype_disc_probe": checkpoint.get("enable_prototype_disc_probe"),
        "enable_prototype_disc_reward": checkpoint.get("enable_prototype_disc_reward"),
        "prototype_disc_condition": checkpoint.get("prototype_disc_condition"),
        "prototype_disc_use_learned_prior": checkpoint.get("prototype_disc_use_learned_prior"),
        "use_compact_return_head": checkpoint.get("use_compact_return_head"),
        "enable_team_transition_probe": checkpoint.get("enable_team_transition_probe"),
        "enable_team_transition_reward": checkpoint.get("enable_team_transition_reward"),
        "team_transition_coef": checkpoint.get("team_transition_coef"),
        "team_transition_clip": checkpoint.get("team_transition_clip"),
        "team_transition_warmup_steps": checkpoint.get("team_transition_warmup_steps"),
        "enable_team_intent": checkpoint.get("enable_team_intent"),
        "team_intent_k": checkpoint.get("team_intent_k"),
        "enable_team_disc_probe": checkpoint.get("enable_team_disc_probe"),
        "enable_team_disc_reward": checkpoint.get("enable_team_disc_reward"),
        "team_disc_coef": checkpoint.get("team_disc_coef"),
        "team_disc_clip": checkpoint.get("team_disc_clip"),
        "team_disc_warmup_steps": checkpoint.get("team_disc_warmup_steps"),
        "team_disc_hidden_dim": checkpoint.get("team_disc_hidden_dim"),
    }


def apply_checkpoint_structure(config, args: argparse.Namespace, metadata: dict[str, Any]) -> None:
    duration_candidates = metadata.get("duration_candidates")
    if duration_candidates:
        config.skill_lifetime_candidates = tuple(int(v) for v in duration_candidates)

    checkpoint_agents = metadata.get("n_agents")
    if checkpoint_agents is not None:
        checkpoint_agents = int(checkpoint_agents)
        requested_agents = int(getattr(args, "n_agents", 0) or 0)
        if requested_agents > 0 and requested_agents != checkpoint_agents:
            raise ValueError(
                "--n_agents does not match checkpoint: "
                f"requested={requested_agents}, checkpoint={checkpoint_agents}"
            )
        config.n_agents = checkpoint_agents
        config.n_uavs = checkpoint_agents
        config.max_observed_uavs = max(
            checkpoint_agents,
            int(getattr(config, "max_observed_uavs", checkpoint_agents)),
        )

    if metadata.get("low_actor_condition_on_team_code") is not None:
        config.low_actor_condition_on_team_code = bool(metadata.get("low_actor_condition_on_team_code"))
    if metadata.get("team_bridge_type"):
        config.team_bridge_type = str(metadata.get("team_bridge_type"))
    for name in (
        "use_prototype_response_skills",
        "high_condition_on_omega",
        "use_agent_prototype_relevance",
        "use_per_agent_kappa",
        "enable_prototype_disc_probe",
        "enable_prototype_disc_reward",
        "use_autoregressive_selection",
        "parallel_selection",
        "prototype_disc_use_learned_prior",
        "use_compact_return_head",
        "enable_team_transition_probe",
        "enable_team_transition_reward",
        "enable_team_intent",
        "enable_team_disc_probe",
        "enable_team_disc_reward",
        "z_entropy_floor_enabled",
    ):
        if metadata.get(name) is not None:
            setattr(config, name, bool(metadata.get(name)))
    if bool(getattr(config, "enable_team_transition_probe", False)):
        config.enable_situation_diagnostics = True
    if metadata.get("ar_prefix_mode"):
        config.ar_prefix_mode = str(metadata.get("ar_prefix_mode"))
    if metadata.get("prototype_skill_extra_codes") is not None:
        config.prototype_skill_extra_codes = int(metadata.get("prototype_skill_extra_codes"))
    if metadata.get("legacy_n_skills_override") is not None:
        config.legacy_n_skills_override = int(metadata.get("legacy_n_skills_override"))
    if metadata.get("opt_num_prototypes") is not None:
        config.opt_num_prototypes = int(metadata.get("opt_num_prototypes"))
    if metadata.get("prototype_disc_condition"):
        config.prototype_disc_condition = str(metadata.get("prototype_disc_condition"))
    for name in ("team_transition_coef", "team_transition_clip"):
        if metadata.get(name) is not None:
            setattr(config, name, float(metadata.get(name)))
    if metadata.get("team_transition_warmup_steps") is not None:
        config.team_transition_warmup_steps = int(metadata.get("team_transition_warmup_steps"))
    for name in ("team_disc_coef", "team_disc_clip"):
        if metadata.get(name) is not None:
            setattr(config, name, float(metadata.get(name)))
    for name in ("z_entropy_floor_threshold", "z_entropy_floor_coef"):
        if metadata.get(name) is not None:
            setattr(config, name, float(metadata.get(name)))
    if metadata.get("team_intent_k") is not None:
        config.team_intent_k = int(metadata.get("team_intent_k"))
    if metadata.get("team_disc_warmup_steps") is not None:
        config.team_disc_warmup_steps = int(metadata.get("team_disc_warmup_steps"))
    if metadata.get("z_entropy_floor_warmup_steps") is not None:
        config.z_entropy_floor_warmup_steps = int(metadata.get("z_entropy_floor_warmup_steps"))
    if metadata.get("team_disc_hidden_dim") is not None:
        config.team_disc_hidden_dim = int(metadata.get("team_disc_hidden_dim"))
    if bool(getattr(config, "enable_team_intent", False)):
        if str(getattr(config, "team_bridge_type", "stochastic")) == "none":
            raise ValueError("checkpoint enables team intent but uses team_bridge_type='none'")
        config.low_actor_condition_on_team_code = False


def run_env_dry_check(config, args: argparse.Namespace) -> None:
    """Check the standalone env path without touching HMASD training code."""

    env = create_env(config, config.scenario, args.seed, rank=0, scale_mode="train")
    try:
        obs, info = env.reset(seed=args.seed)
        state = np.asarray(info["state"], dtype=np.float32)
        emit(
            args,
            "standalone_env_reset "
            f"scenario={normalize_scenario(args.scenario)} "
            f"state_shape={tuple(state.shape)} obs_shape={tuple(obs.shape)} "
            f"action_space={env.action_space}"
        )

        for step in range(int(args.dry_run_env_steps)):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            done = bool(terminated or truncated)
            emit(
                args,
                "standalone_env_step "
                f"step={step + 1} reward={float(reward):.6f} done={done}"
            )
            if done:
                obs, info = env.reset()
    finally:
        env.close()


def numeric_metric(value) -> float | None:
    if value is None:
        return None
    try:
        arr = np.asarray(value, dtype=np.float32)
    except (TypeError, ValueError):
        return None
    if arr.size == 0:
        return None
    scalar = float(np.nanmean(arr))
    return scalar if np.isfinite(scalar) else None


def extract_eval_metrics(info: dict[str, Any]) -> dict[str, float]:
    metrics = extract_uav_metrics(info)
    if "coverage_ratio" in metrics:
        metrics["coverage"] = metrics["coverage_ratio"]
    if "qos_satisfaction_ratio" in metrics:
        metrics["qos"] = metrics["qos_satisfaction_ratio"]
    if "system_throughput_mbps" in metrics:
        metrics["throughput"] = metrics["system_throughput_mbps"]
    if "battery_min_ratio" in metrics:
        metrics["battery_min"] = metrics["battery_min_ratio"]
    if "energy_failure_uav_count" in metrics:
        metrics["energy_failures"] = metrics["energy_failure_uav_count"]
    return metrics


def evaluate(
    agent: StandaloneProcessAgent,
    config,
    args: argparse.Namespace,
    episodes: int,
    total_steps: int,
) -> dict[str, float]:
    """Run standalone eval without changing training segments."""

    env = create_env(config, config.scenario, int(args.seed) + 100000, rank=0, scale_mode="eval")
    deterministic_eval = str(getattr(args, "eval_action_mode", "deterministic")) == "deterministic"
    active_backup = agent.active_skills.copy()
    duration_backup = agent.duration_remaining.copy()
    age_backup = agent.skill_age.copy()
    has_active_backup = agent.has_active_skill.copy()
    team_code_backup = agent.active_team_codes.copy()
    team_intent_remaining_backup = getattr(agent, "team_intent_remaining", None)
    if team_intent_remaining_backup is not None:
        team_intent_remaining_backup = team_intent_remaining_backup.copy()
    team_intent_age_backup = getattr(agent, "team_intent_age", None)
    if team_intent_age_backup is not None:
        team_intent_age_backup = team_intent_age_backup.copy()
    low_actor_hxs_backup = agent.low_actor_hxs.copy()
    low_critic_hxs_backup = agent.low_critic_hxs.copy()
    segments_backup = agent.segments
    agent.segments = SegmentManager(agent.num_envs, agent.n_agents)

    rewards: list[float] = []
    lengths: list[int] = []
    metric_values: dict[str, list[float]] = {}
    eval_records: list[dict[str, float]] = []
    save_topology = bool(getattr(args, "save_topology", False))
    topology_interval = max(1, int(getattr(args, "topology_interval", 25)))
    topology_episodes = max(0, int(getattr(args, "topology_episodes", 1)))
    topology_max_frames = max(1, int(getattr(args, "topology_max_frames", 160)))
    try:
        for episode_idx in range(max(int(episodes), 1)):
            obs, info = env.reset(seed=int(args.seed) + 100000 + episode_idx)
            state = info.get("state")
            agent.reset_env_state(0)
            episode_reward = 0.0
            episode_length = 0
            last_info = info
            backhaul_connected_steps: list[float] = []
            throughput_when_backhaul_connected_steps: list[float] = []
            coverage_eq1_steps: list[float] = []
            coverage_positive_steps: list[float] = []
            zero_throughput_steps: list[float] = []
            throughput_gt5_steps: list[float] = []
            capture_topology = save_topology and episode_idx < topology_episodes
            topology_frames = []
            if capture_topology:
                topology_frames.append(
                    capture_topology_frame(
                        env,
                        info,
                        agent,
                        episode=episode_idx,
                        step=episode_length,
                        reward=episode_reward,
                        metrics={},
                    )
                )
            while True:
                agent.maybe_assign_skills(
                    obs,
                    state=state,
                    step=episode_length,
                    k=int(args.skill_interval),
                    env_id=0,
                    deterministic=deterministic_eval,
                )
                actions, _, _ = agent.act_low(obs, env_id=0, deterministic=deterministic_eval, state=state)
                obs, reward, terminated, truncated, last_info = env.step(actions)
                state = last_info.get("next_state", state)
                episode_reward += float(reward)
                episode_length += 1
                step_metrics = extract_eval_metrics(last_info)
                backhaul_flag = float(step_metrics.get("backhaul_connected_flag", 0.0))
                backhaul_connected_steps.append(backhaul_flag)
                step_throughput = step_metrics.get("throughput")
                step_coverage = step_metrics.get("coverage", step_metrics.get("coverage_ratio"))
                if step_coverage is not None:
                    coverage_value = float(step_coverage)
                    coverage_eq1_steps.append(1.0 if coverage_value >= 0.999 else 0.0)
                    coverage_positive_steps.append(1.0 if coverage_value > 1e-6 else 0.0)
                if step_throughput is not None:
                    throughput_value = float(step_throughput)
                    zero_throughput_steps.append(1.0 if throughput_value <= 1e-6 else 0.0)
                    throughput_gt5_steps.append(1.0 if throughput_value > 5.0 else 0.0)
                if backhaul_flag >= 0.5 and step_throughput is not None:
                    throughput_when_backhaul_connected_steps.append(float(step_throughput))
                done = bool(terminated or truncated)
                hit_step_cap = int(args.eval_max_steps) > 0 and episode_length >= int(args.eval_max_steps)
                if capture_topology and len(topology_frames) < topology_max_frames:
                    should_capture = (
                        episode_length % topology_interval == 0
                        or done
                        or hit_step_cap
                    )
                    if should_capture:
                        topology_frames.append(
                            capture_topology_frame(
                                env,
                                last_info,
                                agent,
                                episode=episode_idx,
                                step=episode_length,
                                reward=episode_reward,
                                metrics=extract_eval_metrics(last_info),
                            )
                        )
                if done or hit_step_cap:
                    break
            rewards.append(episode_reward)
            lengths.append(episode_length)
            episode_metrics = extract_eval_metrics(last_info)
            if backhaul_connected_steps:
                episode_metrics["backhaul_connected_step_fraction"] = float(np.mean(backhaul_connected_steps))
            if coverage_eq1_steps:
                episode_metrics["coverage_eq1_step_fraction"] = float(np.mean(coverage_eq1_steps))
                episode_metrics["coverage_has_eq1_step_flag"] = float(np.max(coverage_eq1_steps))
                episode_metrics["coverage_episode_all_eq1_flag"] = float(np.min(coverage_eq1_steps))
            if coverage_positive_steps:
                episode_metrics["coverage_positive_step_fraction"] = float(np.mean(coverage_positive_steps))
            final_coverage = episode_metrics.get("coverage", episode_metrics.get("coverage_ratio"))
            if final_coverage is not None:
                episode_metrics["coverage_final_eq1_flag"] = 1.0 if float(final_coverage) >= 0.999 else 0.0
            if zero_throughput_steps:
                episode_metrics["zero_throughput_step_fraction"] = float(np.mean(zero_throughput_steps))
                episode_metrics["zero_throughput_episode_flag"] = float(np.min(zero_throughput_steps))
            if throughput_gt5_steps:
                episode_metrics["throughput_gt5_step_fraction"] = float(np.mean(throughput_gt5_steps))
                episode_metrics["throughput_gt5_episode_flag"] = float(np.max(throughput_gt5_steps))
            if throughput_when_backhaul_connected_steps:
                episode_metrics["throughput_when_backhaul_connected_mbps"] = float(
                    np.mean(throughput_when_backhaul_connected_steps)
                )
            else:
                episode_metrics.pop("throughput_when_backhaul_connected_mbps", None)
            eval_record = {
                "checkpoint": str(getattr(args, "eval_checkpoint_name", "")),
                "total_steps": int(total_steps),
                "episode": episode_idx,
                "action_mode_code": 0.0 if deterministic_eval else 1.0,
                "reward": episode_reward,
                "length": episode_length,
                **episode_metrics,
            }
            eval_records.append(eval_record)
            append_csv(Path(args.log_dir) / "metrics" / "eval_episodes.csv", eval_record, EVAL_FIELDS)
            for key, value in episode_metrics.items():
                if value is None or not np.isfinite(float(value)):
                    continue
                metric_values.setdefault(key, []).append(value)
            if capture_topology and topology_frames:
                try:
                    artifacts = save_topology_artifacts(
                        topology_frames,
                        args.log_dir,
                        total_steps=total_steps,
                        episode=episode_idx,
                        checkpoint_name=str(getattr(args, "eval_checkpoint_name", "")),
                    )
                    if artifacts:
                        artifact_text = " ".join(f"{key}={value}" for key, value in artifacts.items())
                        emit(
                            args,
                            "standalone_topology "
                            f"total_steps={int(total_steps)} episode={episode_idx} frames={len(topology_frames)} "
                            f"{artifact_text}",
                        )
                except Exception as exc:
                    emit(
                        args,
                        "standalone_topology_failed "
                        f"total_steps={int(total_steps)} episode={episode_idx} error={exc}",
                    )
    finally:
        env.close()
        agent.segments = segments_backup
        agent.active_skills = active_backup
        agent.duration_remaining = duration_backup
        agent.skill_age = age_backup
        agent.has_active_skill = has_active_backup
        agent.active_team_codes = team_code_backup
        if team_intent_remaining_backup is not None:
            agent.team_intent_remaining = team_intent_remaining_backup
        if team_intent_age_backup is not None:
            agent.team_intent_age = team_intent_age_backup
        agent.low_actor_hxs = low_actor_hxs_backup
        agent.low_critic_hxs = low_critic_hxs_backup

    metrics = {
        "reward_mean": float(np.mean(rewards)) if rewards else 0.0,
        "reward_std": float(np.std(rewards)) if rewards else 0.0,
        "length_mean": float(np.mean(lengths)) if lengths else 0.0,
        "action_mode_code": 0.0 if deterministic_eval else 1.0,
    }
    for key, values in metric_values.items():
        metrics[key] = float(np.mean(values)) if values else 0.0
    if "coverage_has_eq1_step_flag" in metrics:
        metrics["coverage_eq1_episode_fraction"] = float(metrics["coverage_has_eq1_step_flag"])
    if "coverage_final_eq1_flag" in metrics:
        metrics["coverage_final_eq1_episode_fraction"] = float(metrics["coverage_final_eq1_flag"])
    if "zero_throughput_episode_flag" in metrics:
        metrics["zero_throughput_episode_fraction"] = float(metrics["zero_throughput_episode_flag"])
    if "throughput_gt5_episode_flag" in metrics:
        metrics["throughput_gt5_episode_fraction"] = float(metrics["throughput_gt5_episode_flag"])
    if eval_records:
        save_eval_plots(args.log_dir, window=max(1, int(getattr(args, "eval_episodes", 1))))

    emit(
        args,
        "standalone_eval "
        f"total_steps={int(total_steps)} episodes={max(int(episodes), 1)} "
        f"action_mode={getattr(args, 'eval_action_mode', 'deterministic')} "
        f"reward_mean={metrics['reward_mean']:.6f} "
        f"reward_std={metrics['reward_std']:.6f} "
        f"length_mean={metrics['length_mean']:.1f} "
        f"coverage={metrics.get('coverage', 0.0):.6f} "
        f"qos={metrics.get('qos', 0.0):.6f} "
        f"throughput={metrics.get('throughput', 0.0):.6f} "
        f"backhaul_connected_frac={metrics.get('backhaul_connected_step_fraction', metrics.get('backhaul_connected_flag', 0.0)):.6f} "
        f"throughput_when_backhaul_connected={metrics.get('throughput_when_backhaul_connected_mbps', 0.0):.6f} "
        f"battery_min={metrics.get('battery_min', 0.0):.6f} "
        f"coverage_eq1_step_frac={metrics.get('coverage_eq1_step_fraction', 0.0):.6f} "
        f"coverage_eq1_ep_frac={metrics.get('coverage_eq1_episode_fraction', 0.0):.6f} "
        f"zero_throughput_ep_frac={metrics.get('zero_throughput_episode_fraction', 0.0):.6f} "
        f"throughput_gt5_step_frac={metrics.get('throughput_gt5_step_fraction', 0.0):.6f}"
    )
    return metrics


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


def train_loop(config, args: argparse.Namespace, writer) -> tuple[StandaloneProcessAgent, int, int]:
    num_envs = max(int(args.num_envs), 1)
    collector = create_collector(config, args, scale_mode="train", num_envs=num_envs)
    try:
        observations, states, _infos = collector.reset_all(seed=int(args.seed))
        # Per-env pre-step state/reward info: the post-step state of step t is the
        # pre-step (true segment-start) state of step t+1.  Seeded from reset info.
        def _seed_info(infos, key):
            out = [{} for _ in range(num_envs)]
            if isinstance(infos, (list, tuple)):
                for i in range(min(num_envs, len(infos))):
                    info_i = infos[i]
                    if isinstance(info_i, dict) and isinstance(info_i.get(key), dict):
                        out[i] = dict(info_i[key])
            return out

        prev_state_info = _seed_info(_infos, "state_info")
        prev_reward_info = _seed_info(_infos, "reward_info")
        env = SimpleNamespace(**collector.spec)
        action_space_type, _, _ = action_space_details(env)
        state_dim = int(collector.spec.get("state_dim") or 0) or (
            int(np.asarray(states[0], dtype=np.float32).reshape(-1).size)
            if states and states[0] is not None
            else None
        )
        agent = create_agent(config, args, env, num_envs=num_envs, state_dim=state_dim)

        total_steps = 0
        update_idx = 0
        if args.resume_from:
            total_steps, update_idx = load_checkpoint(args.resume_from, agent, load_optimizers=True)
            emit(
                args,
                "standalone_resume "
                f"path={args.resume_from} total_steps={total_steps} update_idx={update_idx}"
            )

        export_run_manifest(
            args,
            config,
            env=env,
            agent=agent,
            total_steps=total_steps,
            update_idx=update_idx,
            mode="train",
        )
        param_counts = agent.parameter_counts()
        emit(
            args,
            "standalone_train_start "
            f"scenario={config.scenario} preset={args.preset or 'none'} "
            f"num_envs={num_envs} n_agents={env.n_uavs} obs_dim={env.obs_dim} action_dim={env.action_dim} "
            f"action_space_type={action_space_type} collector={args.collector_backend} "
            f"policy_update=on_policy "
            f"process_reward_mode={getattr(config, 'process_reward_mode', 'mi_outcome')} "
            f"process_reward_injection={getattr(config, 'process_reward_injection', 'none')} "
            f"process_warmup_steps={int(getattr(config, 'process_reward_warmup_steps', 0))} "
            f"process_shortcut_margin={float(getattr(config, 'process_shortcut_margin', 0.0))} "
            f"process_shortcut_margin_coef={float(getattr(config, 'process_shortcut_margin_coef', 0.0))} "
            f"context_shortcut={bool(getattr(config, 'use_context_skill_shortcut', True))} "
            f"context_shortcut_coef={float(getattr(config, 'context_shortcut_coef', 0.0))} "
            f"transition_context_shortcut_coef={float(getattr(config, 'transition_context_shortcut_coef', 0.0))} "
            f"intrinsic_phase_bins={int(getattr(config, 'intrinsic_phase_bins', 0))} "
            f"transition_disc={bool(getattr(config, 'use_transition_skill_discriminator', True))} "
            f"transition_coef={float(getattr(config, 'transition_skill_coef', 0.0))} "
            f"transition_reward_coef={float(getattr(config, 'transition_skill_reward_coef', 0.0))} "
            f"transition_reward_warmup={int(getattr(config, 'transition_skill_reward_warmup_steps', 0))} "
            f"transition_max_samples={int(getattr(config, 'transition_skill_max_samples', 0))} "
            f"topology_role_probe={bool(getattr(config, 'use_topology_role_probe', True))} "
            f"topology_role_coef={float(getattr(config, 'topology_role_coef', 0.0))} "
            f"topology_role_injection={getattr(config, 'topology_role_injection', 'none')} "
            f"topology_role_reward_coef={float(getattr(config, 'topology_role_reward_coef', 0.0))} "
            f"skill_effect_probe={bool(getattr(config, 'skill_effect_discovery_on', False))} "
            f"skill_effect_reward={bool(getattr(config, 'skill_effect_reward_on', False))} "
            f"skill_effect_horizons={tuple(getattr(config, 'skill_effect_horizons', ())) } "
            f"skill_effect_stride={int(getattr(config, 'skill_effect_stride', 0))} "
            f"skill_effect_max_windows={int(getattr(config, 'skill_effect_max_windows', 0))} "
            f"skill_effect_hidden_dim={int(getattr(config, 'skill_effect_hidden_dim', 0))} "
            f"skill_effect_group_balanced_loss={bool(getattr(config, 'skill_effect_group_balanced_loss', True))} "
            f"skill_effect_intervention_probe={bool(getattr(config, 'skill_effect_intervention_probe_on', False))} "
            f"skill_effect_intervention_max_samples={int(getattr(config, 'skill_effect_intervention_max_samples', 0))} "
            f"skill_force_probe={bool(getattr(config, 'skill_force_probe_on', False))} "
            f"skill_force_reward={bool(getattr(config, 'enable_skill_forcing_reward', False))} "
            f"skill_force_injection={getattr(config, 'skill_force_reward_injection', 'low_only')} "
            f"skill_force_disc_coef={float(getattr(config, 'skill_force_disc_coef', 0.0))} "
            f"skill_force_effect_coef={float(getattr(config, 'skill_force_effect_coef', 0.0))} "
            f"skill_force_duration_entropy_coef={float(getattr(config, 'skill_force_duration_entropy_coef', 0.0))} "
            f"skill_force_warmup={int(getattr(config, 'skill_force_warmup_steps', 0))} "
            f"skill_force_shortcut_gate={bool(getattr(config, 'skill_force_kill_on_shortcut', True))} "
            f"skill_force_use_comm_fields={bool(getattr(config, 'skill_force_use_comm_fields', False))} "
            f"semantic_shortcut_hard_stop={bool(getattr(config, 'semantic_shortcut_hard_stop_enabled', True))} "
            f"semantic_shortcut_margin={float(getattr(config, 'semantic_shortcut_hard_stop_margin', 0.0))} "
            f"g_intervention_kl={bool(getattr(config, 'use_g_intervention_kl_diagnostic', True))} "
            f"g_info_diag={bool(getattr(config, 'use_g_info_diagnostic', True))} "
            f"g_info_obj={bool(getattr(config, 'enable_g_info_objective', False))} "
            f"g_info_coef_skill={float(getattr(config, 'g_info_coef_skill', 0.0))} "
            f"g_info_coef_duration={float(getattr(config, 'g_info_coef_duration', 0.0))} "
            f"g_info_coef_edit={float(getattr(config, 'g_info_coef_edit', 0.0))} "
            f"g_info_warmup={int(getattr(config, 'g_info_warmup_steps', 0))} "
            f"g_info_anneal={int(getattr(config, 'g_info_anneal_steps', 0))} "
            f"situation_diag={bool(getattr(config, 'enable_situation_diagnostics', False))} "
            f"situation_hazard_control={bool(getattr(config, 'enable_situation_hazard_control', False))} "
            f"situation_source={getattr(config, 'situation_substrate_source', 'omega')} "
            f"situation_num_kappa={int(getattr(config, 'situation_num_kappa', 0))} "
            f"situation_debounce={int(getattr(config, 'situation_debounce_steps', 0))} "
            f"situation_hazard_mode={getattr(config, 'situation_hazard_mode', 'diagnostic')} "
            f"situation_hazard_interval={int(getattr(config, 'situation_hazard_check_interval', 0))} "
            f"situation_hazard_min_age={int(getattr(config, 'situation_hazard_min_age', 0))} "
            f"situation_hazard_hidden={int(getattr(config, 'situation_hazard_hidden_dim', 0))} "
            f"situation_hazard_entropy_coef={float(getattr(config, 'situation_hazard_entropy_coef', 0.0))} "
            f"situation_hazard_value_coef={float(getattr(config, 'situation_hazard_value_coef', 0.0))} "
            f"situation_hazard_clip_epsilon={float(getattr(config, 'situation_hazard_clip_epsilon', 0.0))} "
            f"situation_hazard_reward_coef={float(getattr(config, 'situation_hazard_reward_coef', 0.0))} "
            f"situation_hazard_conservative_guard={bool(getattr(config, 'situation_hazard_conservative_guard', False))} "
            f"situation_hazard_min_dwell={int(getattr(config, 'situation_hazard_min_dwell_checks', 0))} "
            f"situation_hazard_confirm_changes={int(getattr(config, 'situation_hazard_confirm_changes', 0))} "
            f"situation_hazard_max_force_rate={float(getattr(config, 'situation_hazard_max_force_rate', 1.0))} "
            f"situation_hazard_rate_window={int(getattr(config, 'situation_hazard_rate_window', 0))} "
            f"team_transition_probe={bool(getattr(config, 'enable_team_transition_probe', False))} "
            f"team_transition_reward={bool(getattr(config, 'enable_team_transition_reward', False))} "
            f"team_transition_coef={float(getattr(config, 'team_transition_coef', 0.0))} "
            f"team_transition_clip={float(getattr(config, 'team_transition_clip', 0.0))} "
            f"team_transition_warmup={int(getattr(config, 'team_transition_warmup_steps', 0))} "
            f"team_intent={bool(getattr(config, 'enable_team_intent', False))} "
            f"team_intent_k={int(getattr(config, 'team_intent_k', 0))} "
            f"team_disc_probe={bool(getattr(config, 'enable_team_disc_probe', False))} "
            f"team_disc_reward={bool(getattr(config, 'enable_team_disc_reward', False))} "
            f"team_disc_coef={float(getattr(config, 'team_disc_coef', 0.0))} "
            f"team_disc_clip={float(getattr(config, 'team_disc_clip', 0.0))} "
            f"team_disc_warmup={int(getattr(config, 'team_disc_warmup_steps', 0))} "
            f"intrinsic_segment_gate={bool(getattr(config, 'intrinsic_segment_gate_enabled', True))} "
            f"intrinsic_gate_margin={float(getattr(config, 'intrinsic_segment_gate_margin', 0.0))} "
            f"intrinsic_gate_min_segments={int(getattr(config, 'intrinsic_segment_gate_min_segments', 0))} "
            f"smdp_discount={bool(getattr(config, 'use_smdp_discounted_high_return', True))} "
            f"smdp_bootstrap={bool(getattr(config, 'use_smdp_bootstrap', True))} "
            f"smdp_bootstrap_coef={float(getattr(config, 'smdp_bootstrap_coef', 1.0))} "
            f"duration_entropy_floor={bool(getattr(config, 'duration_entropy_floor_enabled', False))} "
            f"duration_entropy_floor_threshold={float(getattr(config, 'duration_entropy_floor_threshold', 0.0))} "
            f"duration_entropy_floor_coef={float(getattr(config, 'duration_entropy_floor_coef', 0.0))} "
            f"duration_entropy_floor_warmup={int(getattr(config, 'duration_entropy_floor_warmup_steps', 0))} "
            f"z_entropy_floor={bool(getattr(config, 'z_entropy_floor_enabled', False))} "
            f"z_entropy_floor_threshold={float(getattr(config, 'z_entropy_floor_threshold', 0.0))} "
            f"z_entropy_floor_coef={float(getattr(config, 'z_entropy_floor_coef', 0.0))} "
            f"z_entropy_floor_warmup={int(getattr(config, 'z_entropy_floor_warmup_steps', 0))} "
            f"reward_ratio_guard_mode={str(getattr(config, 'reward_ratio_guard_mode', 'kill'))} "
            f"high_value_norm={bool(getattr(config, 'use_high_value_norm', True))} "
            f"recurrent_low={bool(getattr(config, 'use_recurrent_low_level', True))} "
            f"low_arch={getattr(config, 'low_level_architecture', 'strict_hmasd_mappo')} "
            f"low_actor_team_code={bool(getattr(config, 'low_actor_condition_on_team_code', False))} "
            f"prototype_response={bool(getattr(config, 'use_prototype_response_skills', False))} "
            f"prototype_extra_codes={int(getattr(config, 'prototype_skill_extra_codes', 0))} "
            f"legacy_n_skills={int(getattr(config, 'legacy_n_skills_override', 0))} "
            f"ar_selection={bool(getattr(agent, 'use_autoregressive_selection', False))} "
            f"parallel_selection={bool(getattr(agent, 'parallel_selection', False))} "
            f"ar_prefix_mode={str(getattr(agent, 'ar_prefix_mode', 'none'))} "
            f"high_omega={bool(getattr(config, 'high_condition_on_omega', False))} "
            f"agent_proto_rel={bool(getattr(config, 'use_agent_prototype_relevance', False))} "
            f"per_agent_kappa={bool(getattr(config, 'use_per_agent_kappa', False))} "
            f"proto_disc_probe={bool(getattr(config, 'enable_prototype_disc_probe', False))} "
            f"proto_disc_reward={bool(getattr(config, 'enable_prototype_disc_reward', False))} "
            f"proto_disc_learned_prior={bool(getattr(config, 'prototype_disc_use_learned_prior', False))} "
            f"proto_disc_condition={getattr(config, 'prototype_disc_condition', 'kappa')} "
            f"proto_disc_coef={float(getattr(config, 'prototype_disc_reward_coef', 0.0))} "
            f"compact_return_head={bool(getattr(config, 'use_compact_return_head', False))} "
            f"network_scale={getattr(config, 'network_scale_profile', 'custom')} "
            f"low_value_norm={bool(getattr(config, 'use_low_value_norm', True))} "
            f"low_seq_len={int(getattr(config, 'low_sequence_length', 0))} "
            f"clip={float(getattr(config, 'clip_epsilon', 0.2))} "
            f"low_clip={float(getattr(config, 'low_clip_epsilon', getattr(config, 'clip_epsilon', 0.2)))} "
            f"params_total={param_counts.get('total_trainable', 0)} "
            f"params_high_stack={param_counts.get('high_stack', 0)} "
            f"params_low={param_counts.get('low', 0)} "
            f"params_process_stack={param_counts.get('process_stack', 0)} "
            f"params_skill_effect={param_counts.get('skill_effect_discovery', 0)} "
            f"params_team_transition={param_counts.get('team_transition', 0)} "
            f"params_team_disc={param_counts.get('team_discriminator', 0)} "
            f"duration_candidates={tuple(getattr(config, 'skill_lifetime_candidates', ())) } "
            f"rollout_length={args.rollout_length} total_timesteps={args.total_timesteps} "
            f"save_interval={args.save_interval} checkpoint_keep_last={args.checkpoint_keep_last}"
        )

        last_eval_step = int(total_steps)
        proto_ratio_over05_count = 0
        proto_ratio_consecutive_over05_count = 0
        proto_ratio_kill_triggered_count = 0
        proto_ratio_guard_warmup_steps = int(getattr(config, "prototype_disc_warmup_steps", 0))
        reward_ratio_guard_mode = str(getattr(config, "reward_ratio_guard_mode", "kill")).lower()
        if reward_ratio_guard_mode not in {"kill", "warn"}:
            reward_ratio_guard_mode = "kill"
        team_disc_ratio_over05_count = 0
        team_disc_ratio_consecutive_over05_count = 0
        team_disc_ratio_kill_triggered_count = 0
        team_disc_ratio_guard_warmup_steps = int(getattr(config, "team_disc_warmup_steps", 0))
        combined_intrinsic_ratio_over05_count = 0
        combined_intrinsic_ratio_consecutive_over05_count = 0
        combined_intrinsic_ratio_kill_triggered_count = 0
        while total_steps < int(args.total_timesteps):
            rollout = Rollout()
            episode_rewards = []
            for _local_step in range(int(args.rollout_length)):
                pre_obs = []
                pre_actions = []
                pre_logp = []
                pre_values = []
                pre_low_context = []
                pre_rollout_indices = []
                for env_id in range(num_envs):
                    obs = observations[env_id]
                    rollout_idx = len(rollout.rewards) + len(pre_rollout_indices)
                    agent.maybe_assign_skills(
                        obs,
                        state=states[env_id],
                        step=rollout_idx,
                        k=int(args.skill_interval),
                        env_id=env_id,
                    )
                    actions, logp, values, low_context = agent.act_low(
                        obs,
                        env_id=env_id,
                        state=states[env_id],
                        return_context=True,
                    )
                    pre_obs.append(obs)
                    pre_actions.append(actions)
                    pre_logp.append(logp)
                    pre_values.append(values)
                    pre_low_context.append(low_context)
                    pre_rollout_indices.append(rollout_idx)

                step_results = collector.step(pre_actions)
                for env_id, result in enumerate(step_results):
                    obs = pre_obs[env_id]
                    actions = pre_actions[env_id]
                    logp = pre_logp[env_id]
                    values = pre_values[env_id]
                    low_context = pre_low_context[env_id]
                    rollout_idx = pre_rollout_indices[env_id]
                    next_obs = result.obs
                    reward = result.reward
                    terminated = result.terminated
                    truncated = result.truncated
                    info = result.info
                    done = bool(terminated or truncated)
                    reward_components = info.get("reward_components", {})
                    individual_rewards = np.asarray(
                        reward_components.get(
                            "individual_rewards",
                            [float(reward)] * int(env.n_uavs),
                        ),
                        dtype=np.float32,
                    )
                    if individual_rewards.shape[0] != int(env.n_uavs):
                        individual_rewards = np.full(int(env.n_uavs), float(reward), dtype=np.float32)

                    agent.segments.append(
                        env_id,
                        obs,
                        actions,
                        individual_rewards,
                        next_obs,
                        rollout_idx,
                        reward_info=info.get("reward_info", {}),
                        state_info=info.get("state_info", {}),
                        next_state=info.get("next_state", states[env_id]),
                        done=done,
                        pre_state_info=prev_state_info[env_id],
                        pre_reward_info=prev_reward_info[env_id],
                    )
                    # This step's post-step state is the next step's pre-step state.
                    prev_state_info[env_id] = info.get("state_info", {}) or {}
                    prev_reward_info[env_id] = info.get("reward_info", {}) or {}
                    rollout.env_ids.append(int(env_id))
                    rollout.obs.append(np.asarray(obs, dtype=np.float32))
                    rollout.states.append(np.asarray(low_context["state"], dtype=np.float32))
                    rollout.next_states.append(np.asarray(info.get("next_state", states[env_id]), dtype=np.float32))
                    rollout.skills.append(agent.active_skills[env_id].copy())
                    rollout.team_codes.append(int(low_context["team_code"]))
                    rollout.actions.append(actions.copy())
                    rollout.logp.append(logp.copy())
                    rollout.values.append(values.copy())
                    rollout.low_actor_hxs.append(np.asarray(low_context["actor_hxs"], dtype=np.float32))
                    rollout.low_critic_hxs.append(np.asarray(low_context["critic_hxs"], dtype=np.float32))
                    rollout.rewards.append(individual_rewards.copy())
                    rollout.dones.append(done)
                    episode_rewards.append(float(np.mean(individual_rewards)))

                    total_steps += 1
                    observations[env_id] = next_obs
                    states[env_id] = info.get("next_state", states[env_id])
                    if done:
                        agent.segments.flush(env_id)
                        observations[env_id], info = collector.reset_one(env_id)
                        states[env_id] = info.get("state")
                        # Re-seed pre-step info from the reset state for the next segment.
                        prev_state_info[env_id] = info.get("state_info", {}) or {}
                        prev_reward_info[env_id] = info.get("reward_info", {}) or {}
                        agent.reset_env_state(env_id)
                if total_steps >= int(args.total_timesteps):
                    break

            agent.segments.flush()
            rollout.bootstrap_values = agent.low_bootstrap_values(observations, states)
            process_metrics = agent.process_update(rollout, total_steps=total_steps)
            low_metrics = agent.update_low(rollout)
            update_idx += 1
            env_reward_mean = float(np.mean(episode_rewards)) if episode_rewards else 0.0
            proto_ratio = float(process_metrics.get("proto_disc_reward_env_ratio", 0.0))
            proto_reward_steps = float(process_metrics.get("proto_disc_reward_applied_steps", 0.0))
            proto_ratio_guard_active = (
                proto_reward_steps > 0.0 and int(total_steps) >= int(proto_ratio_guard_warmup_steps)
            )
            proto_ratio_kill_message = ""
            if proto_ratio_guard_active and not np.isfinite(proto_ratio):
                proto_ratio_kill_message = (
                    "prototype discriminator reward/env ratio became non-finite "
                    f"at update={update_idx} total_steps={total_steps}"
                )
            elif proto_ratio_guard_active:
                if proto_ratio > 0.5:
                    proto_ratio_over05_count += 1
                    proto_ratio_consecutive_over05_count += 1
                else:
                    proto_ratio_consecutive_over05_count = 0
                if proto_ratio > 1.0:
                    proto_ratio_kill_message = (
                        "prototype discriminator reward/env ratio exceeded instant guard "
                        f"ratio={proto_ratio:.6f} update={update_idx} total_steps={total_steps}"
                    )
                elif proto_ratio_consecutive_over05_count >= 5:
                    proto_ratio_kill_message = (
                        "prototype discriminator reward/env ratio exceeded sustained guard "
                        f"ratio={proto_ratio:.6f} count={proto_ratio_consecutive_over05_count} "
                        f"update={update_idx} total_steps={total_steps}"
                    )
            else:
                proto_ratio_consecutive_over05_count = 0
            if proto_ratio_kill_message:
                proto_ratio_kill_triggered_count += 1
            process_metrics["proto_disc_reward_env_ratio_over05_count"] = float(proto_ratio_over05_count)
            process_metrics["proto_disc_reward_env_ratio_guard_active"] = float(proto_ratio_guard_active)
            process_metrics["proto_disc_reward_env_ratio_kill_triggered"] = float(
                proto_ratio_kill_triggered_count
            )
            team_disc_ratio = float(process_metrics.get("team_disc_reward_env_ratio", 0.0))
            team_disc_reward_steps = float(process_metrics.get("team_disc_reward_applied_steps", 0.0))
            team_disc_ratio_guard_active = (
                team_disc_reward_steps > 0.0 and int(total_steps) >= int(team_disc_ratio_guard_warmup_steps)
            )
            team_disc_ratio_kill_message = ""
            if team_disc_ratio_guard_active and not np.isfinite(team_disc_ratio):
                team_disc_ratio_kill_message = (
                    "team discriminator reward/env ratio became non-finite "
                    f"at update={update_idx} total_steps={total_steps}"
                )
            elif team_disc_ratio_guard_active:
                if team_disc_ratio > 0.5:
                    team_disc_ratio_over05_count += 1
                    team_disc_ratio_consecutive_over05_count += 1
                else:
                    team_disc_ratio_consecutive_over05_count = 0
                if team_disc_ratio > 1.0:
                    team_disc_ratio_kill_message = (
                        "team discriminator reward/env ratio exceeded instant guard "
                        f"ratio={team_disc_ratio:.6f} update={update_idx} total_steps={total_steps}"
                    )
                elif team_disc_ratio_consecutive_over05_count >= 5:
                    team_disc_ratio_kill_message = (
                        "team discriminator reward/env ratio exceeded sustained guard "
                        f"ratio={team_disc_ratio:.6f} count={team_disc_ratio_consecutive_over05_count} "
                        f"update={update_idx} total_steps={total_steps}"
                    )
            else:
                team_disc_ratio_consecutive_over05_count = 0
            if team_disc_ratio_kill_message:
                team_disc_ratio_kill_triggered_count += 1
            process_metrics["team_disc_reward_env_ratio_over05_count"] = float(team_disc_ratio_over05_count)
            process_metrics["team_disc_reward_env_ratio_guard_active"] = float(team_disc_ratio_guard_active)
            process_metrics["team_disc_reward_env_ratio_kill_triggered"] = float(
                team_disc_ratio_kill_triggered_count
            )
            proto_component_ratio = float(abs(proto_ratio)) if proto_reward_steps > 0.0 else 0.0
            team_disc_component_ratio = float(abs(team_disc_ratio)) if team_disc_reward_steps > 0.0 else 0.0
            combined_intrinsic_ratio = float(proto_component_ratio + team_disc_component_ratio)
            combined_intrinsic_reward_steps = proto_reward_steps + team_disc_reward_steps
            combined_intrinsic_guard_active = bool(
                combined_intrinsic_reward_steps > 0.0
                and (proto_ratio_guard_active or team_disc_ratio_guard_active)
            )
            combined_intrinsic_kill_message = ""
            if combined_intrinsic_guard_active and not np.isfinite(combined_intrinsic_ratio):
                combined_intrinsic_kill_message = (
                    "combined intrinsic reward/env ratio became non-finite "
                    f"at update={update_idx} total_steps={total_steps}"
                )
            elif combined_intrinsic_guard_active:
                if combined_intrinsic_ratio > 0.5:
                    combined_intrinsic_ratio_over05_count += 1
                    combined_intrinsic_ratio_consecutive_over05_count += 1
                else:
                    combined_intrinsic_ratio_consecutive_over05_count = 0
                if combined_intrinsic_ratio > 1.0:
                    combined_intrinsic_kill_message = (
                        "combined intrinsic reward/env ratio exceeded instant guard "
                        f"ratio={combined_intrinsic_ratio:.6f} update={update_idx} total_steps={total_steps}"
                    )
                elif combined_intrinsic_ratio_consecutive_over05_count >= 5:
                    combined_intrinsic_kill_message = (
                        "combined intrinsic reward/env ratio exceeded sustained guard "
                        f"ratio={combined_intrinsic_ratio:.6f} "
                        f"count={combined_intrinsic_ratio_consecutive_over05_count} "
                        f"update={update_idx} total_steps={total_steps}"
                    )
            else:
                combined_intrinsic_ratio_consecutive_over05_count = 0
            if combined_intrinsic_kill_message:
                combined_intrinsic_ratio_kill_triggered_count += 1
            process_metrics["combined_intrinsic_env_ratio"] = float(combined_intrinsic_ratio)
            process_metrics["combined_intrinsic_env_ratio_over05_count"] = float(
                combined_intrinsic_ratio_over05_count
            )
            process_metrics["combined_intrinsic_env_ratio_guard_active"] = float(
                combined_intrinsic_guard_active
            )
            process_metrics["combined_intrinsic_env_ratio_kill_triggered"] = float(
                combined_intrinsic_ratio_kill_triggered_count
            )
            emit(
                args,
                "standalone_update "
                f"update={update_idx} total_steps={total_steps} "
                f"env_reward_mean={env_reward_mean:.6f} "
                f"process_segments={process_metrics['process_segments']:.0f} "
                f"process_loss={process_metrics['process_loss']:.6f} "
                f"process_mi={process_metrics.get('process_mi_estimate_mean', 0.0):.6f} "
                f"process_resid_mi={process_metrics.get('process_residual_mi_mean', 0.0):.6f} "
                f"process_shortcut_acc={process_metrics.get('process_shortcut_max_acc', 0.0):.3f} "
                f"process_margin_loss={process_metrics.get('process_shortcut_margin_loss', 0.0):.6f} "
                f"process_warmup={process_metrics.get('process_reward_warmup_active', 0.0):.0f} "
                f"trans_samples={process_metrics.get('transition_skill_samples', 0.0):.0f} "
                f"trans_acc={process_metrics.get('transition_skill_acc', 0.0):.3f} "
                f"trans_ctx_acc={process_metrics.get('transition_skill_context_acc', 0.0):.3f} "
                f"trans_mi={process_metrics.get('transition_skill_mi_mean', 0.0):.6f} "
                f"trans_resid_mi={process_metrics.get('transition_skill_residual_mi_mean', 0.0):.6f} "
                f"trans_reward={process_metrics.get('transition_skill_reward_mean', 0.0):.6f} "
                f"trans_active={process_metrics.get('transition_skill_reward_active', 0.0):.0f} "
                f"team_t_samples={process_metrics.get('team_transition_samples', 0.0):.0f} "
                f"team_t_mi={process_metrics.get('team_transition_mi_mean', 0.0):.6f} "
                f"team_t_self={process_metrics.get('team_transition_self_frac', 0.0):.3f} "
                f"team_t_rew={process_metrics.get('team_transition_reward_high_mean', 0.0):.6f} "
                f"team_t_ratio={process_metrics.get('team_transition_reward_env_ratio', 0.0):.3f} "
                f"team_t_renew_corr={process_metrics.get('team_transition_reward_renewal_corr', 0.0):.3f} "
                f"z_ent={process_metrics.get('z_usage_entropy', 0.0):.3f} "
                f"z_ent_floor={process_metrics.get('z_entropy_floor_active', 0.0):.0f} "
                f"z_ent_gap={process_metrics.get('z_entropy_floor_gap', 0.0):.3f} "
                f"z_dwell={process_metrics.get('z_dwell', 0.0):.2f} "
                f"z_trunc={process_metrics.get('z_boundary_trunc_rate', 0.0):.3f} "
                f"z_trunc_d3={process_metrics.get('z_boundary_trunc_rate_dur3', 0.0):.3f} "
                f"z_trunc_d7={process_metrics.get('z_boundary_trunc_rate_dur7', 0.0):.3f} "
                f"z_trunc_d13={process_metrics.get('z_boundary_trunc_rate_dur13', 0.0):.3f} "
                f"z_trunc_d24={process_metrics.get('z_boundary_trunc_rate_dur24', 0.0):.3f} "
                f"z_itv={process_metrics.get('z_assignment_itv', 0.0):.6f} "
                f"team_disc_acc={process_metrics.get('team_disc_acc', 0.0):.3f} "
                f"team_disc_resid={process_metrics.get('team_disc_residual_mean', 0.0):.6f} "
                f"team_disc_reward={process_metrics.get('team_disc_reward_mean', 0.0):.6f} "
                f"team_disc_steps={process_metrics.get('team_disc_reward_applied_steps', 0.0):.0f} "
                f"team_disc_ratio={process_metrics.get('team_disc_reward_env_ratio', 0.0):.3f} "
                f"team_disc_guard={process_metrics.get('team_disc_reward_env_ratio_guard_active', 0.0):.0f} "
                f"team_disc_o05={process_metrics.get('team_disc_reward_env_ratio_over05_count', 0.0):.0f} "
                f"team_disc_kill={process_metrics.get('team_disc_reward_env_ratio_kill_triggered', 0.0):.0f} "
                f"combined_intr_ratio={process_metrics.get('combined_intrinsic_env_ratio', 0.0):.3f} "
                f"combined_intr_guard={process_metrics.get('combined_intrinsic_env_ratio_guard_active', 0.0):.0f} "
                f"combined_intr_o05={process_metrics.get('combined_intrinsic_env_ratio_over05_count', 0.0):.0f} "
                f"combined_intr_kill={process_metrics.get('combined_intrinsic_env_ratio_kill_triggered', 0.0):.0f} "
                f"proto_acc={process_metrics.get('proto_disc_acc', 0.0):.3f} "
                f"proto_prior_acc={process_metrics.get('proto_disc_prior_acc', 0.0):.3f} "
                f"proto_null={process_metrics.get('proto_disc_null_logp_mean', 0.0):.6f} "
                f"proto_ar_kl={process_metrics.get('proto_ar_parallel_kl', 0.0):.6f} "
                f"roster_kl_shuf={process_metrics.get('roster_ar_kl_shuffled', 0.0):.6f} "
                f"sel_def={process_metrics.get('selection_independence_deficit', 0.0):.6f} "
                f"proto_resid={process_metrics.get('proto_disc_residual_mean', 0.0):.6f} "
                f"proto_reward={process_metrics.get('proto_disc_reward_mean', 0.0):.6f} "
                f"proto_steps={process_metrics.get('proto_disc_reward_applied_steps', 0.0):.0f} "
                f"proto_ratio_guard={process_metrics.get('proto_disc_reward_env_ratio_guard_active', 0.0):.0f} "
                f"proto_ratio_o05={process_metrics.get('proto_disc_reward_env_ratio_over05_count', 0.0):.0f} "
                f"proto_ratio_kill={process_metrics.get('proto_disc_reward_env_ratio_kill_triggered', 0.0):.0f} "
                f"proto_skill_ent={process_metrics.get('proto_skill_selection_entropy', 0.0):.3f} "
                f"proto_kappa_ent={process_metrics.get('proto_skill_usage_entropy_by_kappa', 0.0):.3f} "
                f"proto_align={process_metrics.get('proto_skill_relevance_alignment', 0.0):.3f} "
                f"proto_rel_dwell={process_metrics.get('proto_rel_argmax_dwell_median', 0.0):.1f} "
                f"proto_rel_stab={process_metrics.get('proto_rel_stability_cos', 0.0):.3f} "
                f"high_intr_gate={process_metrics.get('intrinsic_segment_high_gate_active', 0.0):.0f} "
                f"high_intr_score={process_metrics.get('intrinsic_segment_high_gate_score', 0.0):.6f} "
                f"high_intr_reason={process_metrics.get('intrinsic_segment_high_gate_reason_code', 0.0):.0f} "
                f"posterior_gap_short={process_metrics.get('posterior_acc_minus_shortcut_max', 0.0):.3f} "
                f"posterior_gap_ctx={process_metrics.get('posterior_acc_minus_context_shortcut', 0.0):.3f} "
                f"posterior_acc={process_metrics.get('process_posterior_acc', 0.0):.3f} "
                f"ctx_short_acc={process_metrics.get('process_shortcut_context_acc', 0.0):.3f} "
                f"process_reward_mean={process_metrics['process_reward_mean']:.6f} "
                f"process_reward_raw={process_metrics.get('process_reward_unclipped_mean', 0.0):.6f} "
                f"process_mi_reward={process_metrics.get('process_reward_mi_component_mean', 0.0):.6f} "
                f"process_reward_high={process_metrics.get('process_reward_high_mean', 0.0):.6f} "
                f"process_reward_low={process_metrics.get('process_reward_low_mean', 0.0):.6f} "
                f"semantic_stop={process_metrics.get('semantic_shortcut_hard_stop_triggered', 0.0):.0f} "
                f"semantic_stop_apply={process_metrics.get('semantic_shortcut_hard_stop_applied', 0.0):.0f} "
                f"semantic_stop_score={process_metrics.get('semantic_shortcut_hard_stop_score', 0.0):.3f} "
                f"outcome_available={process_metrics['outcome_available_mean']:.3f} "
                f"outcome_abs_mean={process_metrics['outcome_abs_mean']:.6f} "
                f"out_full_loss={process_metrics.get('outcome_residual_full_loss', 0.0):.6f} "
                f"out_base_loss={process_metrics.get('outcome_residual_base_loss', 0.0):.6f} "
                f"out_gain={process_metrics.get('outcome_residual_gain_mean', 0.0):.6f} "
                f"out_pos={process_metrics.get('outcome_residual_gain_positive_frac', 0.0):.3f} "
                f"out_active={process_metrics.get('outcome_residual_reward_active', 0.0):.0f} "
                f"role_avail={process_metrics.get('topology_role_available_frac', 0.0):.3f} "
                f"role_acc={process_metrics.get('topology_role_acc', 0.0):.3f} "
                f"role_ctx_acc={process_metrics.get('topology_role_shortcut_acc', 0.0):.3f} "
                f"role_gain={process_metrics.get('topology_role_resid_gain_mean', 0.0):.6f} "
                f"role_pos={process_metrics.get('topology_role_resid_gain_positive_frac', 0.0):.3f} "
                f"role_z_mi={process_metrics.get('topology_role_z_mi', 0.0):.3f} "
                f"topo_pot_active={process_metrics.get('topology_potential_active', 0.0):.0f} "
                f"topo_pot_raw={process_metrics.get('topology_potential_raw_mean', 0.0):.6f} "
                f"topo_pot_rew={process_metrics.get('topology_potential_reward_mean', 0.0):.6f} "
                f"topo_pot_low={process_metrics.get('topology_potential_low_mean', 0.0):.6f} "
                f"topo_phi_start={process_metrics.get('topology_potential_phi_start_mean', 0.0):.6f} "
                f"topo_phi_end={process_metrics.get('topology_potential_phi_end_mean', 0.0):.6f} "
                f"effect_windows={process_metrics.get('effect_windows', 0.0):.0f} "
                f"effect_loss_full={process_metrics.get('effect_loss_full', 0.0):.6f} "
                f"effect_loss_base={process_metrics.get('effect_loss_base', 0.0):.6f} "
                f"effect_gain={process_metrics.get('effect_gain_mean', 0.0):.6f} "
                f"effect_gbal={process_metrics.get('effect_gain_group_balanced_mean', 0.0):.6f} "
                f"effect_nonmotion={process_metrics.get('effect_gain_nonmotion', 0.0):.6f} "
                f"effect_pos={process_metrics.get('effect_gain_positive_frac', 0.0):.3f} "
                f"effect_motion={process_metrics.get('effect_gain_motion', 0.0):.6f} "
                f"effect_service={process_metrics.get('effect_gain_service', 0.0):.6f} "
                f"effect_energy={process_metrics.get('effect_gain_energy', 0.0):.6f} "
                f"effect_topology={process_metrics.get('effect_gain_topology', 0.0):.6f} "
                f"effect_h0={process_metrics.get('effect_gain_horizon_0', 0.0):.6f} "
                f"effect_h1={process_metrics.get('effect_gain_horizon_1', 0.0):.6f} "
                f"effect_h2={process_metrics.get('effect_gain_horizon_2', 0.0):.6f} "
                f"effect_act_eta={process_metrics.get('effect_action_skill_eta2', 0.0):.3f} "
                f"effect_tgt_eta={process_metrics.get('effect_target_skill_eta2', 0.0):.3f} "
                f"effect_obs_tgt_l2={process_metrics.get('effect_observed_target_skill_l2_mean', 0.0):.6f} "
                f"effect_obs_nm_l2={process_metrics.get('effect_observed_target_skill_l2_nonmotion', 0.0):.6f} "
                f"effect_act_tgt_corr={process_metrics.get('effect_observed_action_target_corr', 0.0):.3f} "
                f"effect_end_avail={process_metrics.get('effect_endstate_available_frac', 0.0):.3f} "
                f"effect_mean_avail={process_metrics.get('effect_window_mean_available_frac', 0.0):.3f} "
                f"effect_skill_ent={process_metrics.get('effect_skill_usage_entropy', 0.0):.3f} "
                f"effect_gap_dur={process_metrics.get('effect_gain_minus_duration_baseline', 0.0):.6f} "
                f"effect_gap_rew={process_metrics.get('effect_gain_minus_reward_baseline', 0.0):.6f} "
                f"effect_low_rew={process_metrics.get('effect_reward_low_mean', 0.0):.6f} "
                f"effect_steps={process_metrics.get('effect_reward_applied_steps', 0.0):.0f} "
                f"force_rew={process_metrics.get('force_reward_low_mean', 0.0):.6f} "
                f"force_steps={process_metrics.get('force_reward_applied_steps', 0.0):.0f} "
                f"force_disc_acc={process_metrics.get('force_disc_acc', 0.0):.3f} "
                f"force_resid={process_metrics.get('force_disc_residual_mean', 0.0):.6f} "
                f"force_eff_resid={process_metrics.get('force_effect_residual_mean', 0.0):.6f} "
                f"force_shortcut_acc={process_metrics.get('force_shortcut_best_acc', 0.0):.3f} "
                f"force_margin={process_metrics.get('force_shortcut_margin', 0.0):.3f} "
                f"force_gate={process_metrics.get('force_gate_active', 0.0):.0f} "
                f"force_reason={process_metrics.get('force_gate_reason', 0.0):.0f} "
                f"effect_itv_samples={process_metrics.get('effect_intervention_samples', 0.0):.0f} "
                f"effect_itv_act_l2={process_metrics.get('effect_intervention_action_l2_mean', 0.0):.6f} "
                f"effect_itv_pred_l2={process_metrics.get('effect_intervention_pred_effect_l2_mean', 0.0):.6f} "
                f"duration_only_acc={process_metrics.get('duration_only_accuracy', 0.0):.3f} "
                f"length_only_acc={process_metrics.get('length_only_accuracy', 0.0):.3f} "
                f"reward_sum_only_acc={process_metrics.get('reward_sum_only_accuracy', 0.0):.3f} "
                f"posterior_gap_dur={process_metrics.get('posterior_acc_minus_duration_only', 0.0):.3f} "
                f"posterior_gap_len={process_metrics.get('posterior_acc_minus_length_only', 0.0):.3f} "
                f"posterior_gap_rew={process_metrics.get('posterior_acc_minus_reward_sum_only', 0.0):.3f} "
                f"switch_rate={process_metrics.get('skill_switch_rate', 0.0):.3f} "
                f"seg_len_mean={process_metrics.get('segment_length_mean', 0.0):.2f} "
                f"high_loss={process_metrics['high_loss']:.6f} "
                f"high_value_loss={process_metrics.get('high_value_loss', 0.0):.6f} "
                f"high_entropy={process_metrics['high_entropy']:.6f} "
                f"high_return_mean={process_metrics['high_return_mean']:.6f} "
                f"high_env_return={process_metrics.get('high_env_return_mean', 0.0):.6f} "
                f"high_bootstrap={process_metrics.get('high_bootstrap_value_mean', 0.0):.6f} "
                f"high_bootstrap_contrib={process_metrics.get('high_bootstrap_contribution_mean', 0.0):.6f} "
                f"high_vnorm_mean={process_metrics.get('high_value_norm_mean', 0.0):.6f} "
                f"high_vnorm_std={process_metrics.get('high_value_norm_std', 0.0):.6f} "
                f"high_grad_norm={process_metrics.get('high_grad_norm', 0.0):.6f} "
                f"skill_entropy={process_metrics.get('skill_usage_entropy', 0.0):.3f} "
                f"duration_entropy={process_metrics.get('duration_usage_entropy', 0.0):.3f} "
                f"duration_policy_entropy={process_metrics.get('duration_policy_entropy_norm', 0.0):.3f} "
                f"dur_ent_floor={process_metrics.get('duration_entropy_floor_active', 0.0):.0f} "
                f"dur_ent_gap={process_metrics.get('duration_entropy_floor_gap', 0.0):.3f} "
                f"dur_ent_loss={process_metrics.get('duration_entropy_floor_loss', 0.0):.6f} "
                f"z_ent={process_metrics.get('z_usage_entropy', 0.0):.3f} "
                f"z_ent_floor={process_metrics.get('z_entropy_floor_active', 0.0):.0f} "
                f"z_ent_gap={process_metrics.get('z_entropy_floor_gap', 0.0):.3f} "
                f"z_pol_ent={process_metrics.get('z_policy_entropy_norm', 0.0):.3f} "
                f"z_decisions={process_metrics.get('z_decisions_per_update', 0.0):.0f} "
                f"z_adv_mean={process_metrics.get('z_advantage_mean', 0.0):.6f} "
                f"z_adv_std={process_metrics.get('z_advantage_std', 0.0):.6f} "
                f"z_trunc={process_metrics.get('z_boundary_trunc_rate', 0.0):.3f} "
                f"z_trunc_d3={process_metrics.get('z_boundary_trunc_rate_dur3', 0.0):.3f} "
                f"z_trunc_d7={process_metrics.get('z_boundary_trunc_rate_dur7', 0.0):.3f} "
                f"z_trunc_d13={process_metrics.get('z_boundary_trunc_rate_dur13', 0.0):.3f} "
                f"z_trunc_d24={process_metrics.get('z_boundary_trunc_rate_dur24', 0.0):.3f} "
                f"g_entropy={process_metrics.get('team_code_usage_entropy', 0.0):.3f} "
                f"g_skill_mi={process_metrics.get('team_code_skill_mi', 0.0):.3f} "
                f"g_dur_mi={process_metrics.get('team_code_duration_mi', 0.0):.3f} "
                f"g_edit_mi={process_metrics.get('team_code_edit_mi', 0.0):.3f} "
                f"g_ikl={process_metrics.get('g_intervention_kl_mean', 0.0):.6f} "
                f"g_itv={process_metrics.get('g_intervention_tv_mean', 0.0):.6f} "
                f"g_info_active={process_metrics.get('g_info_active', 0.0):.0f} "
                f"g_info_obj={process_metrics.get('g_info_objective_active', 0.0):.0f} "
                f"g_info_loss={process_metrics.get('g_info_loss', 0.0):.6f} "
                f"g_mi_z={process_metrics.get('g_info_skill_mi', 0.0):.6f} "
                f"g_mi_dur={process_metrics.get('g_info_duration_mi', 0.0):.6f} "
                f"g_itv_z={process_metrics.get('g_itv_tv_skill', 0.0):.6f} "
                f"g_itv_dur={process_metrics.get('g_itv_tv_duration', 0.0):.6f} "
                f"g_joint_dist={process_metrics.get('g_joint_assignment_distance', 0.0):.6f} "
                f"situation_enabled={process_metrics.get('situation_enabled', 0.0):.0f} "
                f"situation_change={process_metrics.get('situation_change_rate', 0.0):.3f} "
                f"situation_kappa={process_metrics.get('situation_unique_kappa', 0.0):.0f} "
                f"situation_seg_change={process_metrics.get('situation_segment_change_frac', 0.0):.3f} "
                f"situation_hazard_enabled={process_metrics.get('situation_hazard_control_enabled', 0.0):.0f} "
                f"situation_hazard_force={process_metrics.get('situation_hazard_forced_renewal_rate', 0.0):.3f} "
                f"situation_hazard_mode={process_metrics.get('situation_hazard_mode_code', 0.0):.0f} "
                f"situation_guard={process_metrics.get('situation_hazard_conservative_guard', 0.0):.0f} "
                f"situation_guard_events={process_metrics.get('situation_hazard_guard_event_count', 0.0):.0f} "
                f"situation_guard_allow={process_metrics.get('situation_hazard_guard_allow_rate', 0.0):.3f} "
                f"situation_guard_confirm={process_metrics.get('situation_hazard_guard_confirm_block_rate', 0.0):.3f} "
                f"situation_guard_dwell={process_metrics.get('situation_hazard_guard_dwell_block_rate', 0.0):.3f} "
                f"situation_guard_ratecap={process_metrics.get('situation_hazard_guard_rate_cap_block_rate', 0.0):.3f} "
                f"situation_guard_recent_force={process_metrics.get('situation_hazard_guard_recent_force_rate', 0.0):.3f} "
                f"credit_disc={process_metrics.get('credit_full_disconnect_mean', 0.0):.3f} "
                f"credit_recover={process_metrics.get('credit_recovery_rate', 0.0):.3f} "
                f"credit_collapse={process_metrics.get('credit_collapse_rate', 0.0):.3f} "
                f"credit_bh_frac={process_metrics.get('credit_backhaul_connected_step_fraction', 0.0):.3f} "
                f"credit_bh_thr={process_metrics.get('credit_throughput_when_backhaul_connected_mbps', 0.0):.6f} "
                f"credit_d_conn={process_metrics.get('credit_delta_connectivity_ratio_mean', 0.0):.6f} "
                f"credit_d_served={process_metrics.get('credit_delta_backhaul_served_users_mean', 0.0):.6f} "
                f"credit_d_outage={process_metrics.get('credit_delta_backhaul_outage_ratio_mean', 0.0):.6f} "
                f"p2_seg={process_metrics.get('p2_segments', 0.0):.0f} "
                f"p2_avail={process_metrics.get('p2_available_frac', 0.0):.3f} "
                f"p2_window={process_metrics.get('p2_window_frac', 0.0):.3f} "
                f"p2_dphi_full={process_metrics.get('delta_phi_soft_nonzero_rate_when_full_disconnect', 0.0):.3f} "
                f"p2_dphi_near={process_metrics.get('delta_phi_soft_nonzero_rate_when_near_disconnect', 0.0):.3f} "
                f"p2_corr_rec={process_metrics.get('p2_corr_phi_recovery_event', 0.0):.3f} "
                f"p2_partial={process_metrics.get('p2_partial_recovery_frac', 0.0):.3f} "
                f"p2_corr_dbh={process_metrics.get('p2_corr_credit_delta_bh_frac', 0.0):.3f} "
                f"p2_dbh={process_metrics.get('p2_delta_bh_frac_mean', 0.0):.6f} "
                f"p2_fteam={process_metrics.get('p2_f_team_mean', 0.0):.6f} "
                f"low_loss={low_metrics['low_loss']:.6f} "
                f"low_value_loss={low_metrics.get('low_value_loss', 0.0):.6f} "
                f"low_actor_loss={low_metrics.get('low_actor_loss', 0.0):.6f} "
                f"low_critic_loss={low_metrics.get('low_critic_loss', 0.0):.6f} "
                f"low_chunks={low_metrics.get('low_sequence_chunks', 0.0):.0f} "
                f"low_vnorm_mean={low_metrics.get('low_value_norm_mean', 0.0):.6f} "
                f"low_vnorm_std={low_metrics.get('low_value_norm_std', 0.0):.6f} "
                f"low_verr={low_metrics.get('low_value_error_abs_mean', 0.0):.6f} "
                f"low_vrmse={low_metrics.get('low_value_error_rmse', 0.0):.6f} "
                f"low_adv_std={low_metrics.get('low_advantage_std', 0.0):.6f} "
                f"low_ratio={low_metrics.get('low_ratio_mean', 0.0):.6f} "
                f"low_clip={low_metrics.get('low_clip_frac', 0.0):.6f} "
                f"low_kl={low_metrics.get('low_approx_kl', 0.0):.6f} "
                f"low_agn={low_metrics.get('low_actor_grad_norm', 0.0):.6f} "
                f"low_cgn={low_metrics.get('low_critic_grad_norm', 0.0):.6f} "
                f"low_ahn={low_metrics.get('low_actor_h_norm_mean', 0.0):.6f} "
                f"low_chn={low_metrics.get('low_critic_h_norm_mean', 0.0):.6f} "
                f"low_sent={low_metrics.get('low_skill_usage_entropy', 0.0):.3f} "
                f"low_sret_std={low_metrics.get('low_skill_return_std', 0.0):.6f} "
                f"low_sret_rng={low_metrics.get('low_skill_return_range', 0.0):.6f} "
                f"low_sverr_std={low_metrics.get('low_skill_value_error_abs_std', 0.0):.6f} "
                f"low_sent_std={low_metrics.get('low_skill_entropy_std', 0.0):.6f} "
                f"low_tent={low_metrics.get('low_team_usage_entropy', 0.0):.3f} "
                f"low_tret_std={low_metrics.get('low_team_return_std', 0.0):.6f} "
                f"low_tret_rng={low_metrics.get('low_team_return_range', 0.0):.6f} "
                f"low_tverr_std={low_metrics.get('low_team_value_error_abs_std', 0.0):.6f} "
                f"return_mean={low_metrics['return_mean']:.6f}"
            )
            log_train_metrics(writer, total_steps, episode_rewards, process_metrics, low_metrics)
            export_update_metrics(args, update_idx, total_steps, env_reward_mean, process_metrics, low_metrics)
            if proto_ratio_kill_message:
                if reward_ratio_guard_mode == "warn":
                    emit(args, f"standalone_runtime_guard_warn mode=warn {proto_ratio_kill_message}")
                else:
                    emit(args, f"standalone_runtime_guard mode=kill {proto_ratio_kill_message}")
                    raise RuntimeError(proto_ratio_kill_message)
            if team_disc_ratio_kill_message:
                if reward_ratio_guard_mode == "warn":
                    emit(args, f"standalone_runtime_guard_warn mode=warn {team_disc_ratio_kill_message}")
                else:
                    emit(args, f"standalone_runtime_guard mode=kill {team_disc_ratio_kill_message}")
                    raise RuntimeError(team_disc_ratio_kill_message)
            if combined_intrinsic_kill_message:
                if reward_ratio_guard_mode == "warn":
                    emit(args, f"standalone_runtime_guard_warn mode=warn {combined_intrinsic_kill_message}")
                else:
                    emit(args, f"standalone_runtime_guard mode=kill {combined_intrinsic_kill_message}")
                    raise RuntimeError(combined_intrinsic_kill_message)
            agent.reset_all_policy_state()

            if int(args.save_interval) > 0 and update_idx % int(args.save_interval) == 0:
                save_checkpoint(
                    Path(args.log_dir) / f"standalone_process_core_update_{update_idx}.pt",
                    agent,
                    args,
                    config,
                    total_steps,
                    update_idx,
                )
                prune_periodic_checkpoints(args.log_dir, int(args.checkpoint_keep_last))

            if int(args.eval_interval) > 0 and total_steps - last_eval_step >= int(args.eval_interval):
                eval_metrics = evaluate(
                    agent,
                    config,
                    args,
                    episodes=int(args.eval_episodes),
                    total_steps=total_steps,
                )
                log_eval_metrics(writer, total_steps, eval_metrics)
                last_eval_step = int(total_steps)

        save_checkpoint(
            Path(args.log_dir) / "standalone_process_core_final.pt",
            agent,
            args,
            config,
            total_steps,
            update_idx,
        )
        export_run_manifest(
            args,
            config,
            env=env,
            agent=agent,
            total_steps=total_steps,
            update_idx=update_idx,
            mode="train",
        )
        return agent, total_steps, update_idx
    finally:
        collector.close()


def eval_loop(config, args: argparse.Namespace, writer) -> None:
    if not args.resume_from:
        raise ValueError("--mode eval requires --resume_from pointing to a standalone checkpoint")
    env = create_env(config, config.scenario, args.seed, rank=0, scale_mode="eval")
    try:
        _obs, info = env.reset(seed=args.seed)
        state_dim = int(np.asarray(info.get("state"), dtype=np.float32).reshape(-1).size) if info.get("state") is not None else None
        agent = create_agent(config, args, env, num_envs=1, state_dim=state_dim)
    finally:
        env.close()
    total_steps, update_idx = load_checkpoint(args.resume_from, agent, load_optimizers=False)
    export_run_manifest(
        args,
        config,
        env=env,
        agent=agent,
        total_steps=total_steps,
        update_idx=update_idx,
        mode="eval",
    )
    emit(
        args,
        "standalone_eval_start "
        f"path={args.resume_from} total_steps={total_steps} update_idx={update_idx} "
        f"action_mode={getattr(args, 'eval_action_mode', 'deterministic')} "
        f"duration_candidates={tuple(getattr(config, 'skill_lifetime_candidates', ())) }"
    )
    args.eval_checkpoint_name = Path(args.resume_from).name
    metrics = evaluate(
        agent,
        config,
        args,
        episodes=int(args.eval_episodes),
        total_steps=total_steps,
    )
    log_eval_metrics(writer, total_steps, metrics)


def main() -> None:
    args = parse_args()
    Path(args.log_dir).mkdir(parents=True, exist_ok=True)
    writer = SummaryWriter(args.log_dir) if SummaryWriter is not None else None
    config = load_config(args.config, args.preset or None)
    config.scenario = normalize_scenario(args.scenario)
    apply_standalone_overrides(config, args)
    if args.resume_from:
        metadata = load_checkpoint_metadata(args.resume_from)
        apply_checkpoint_structure(config, args, metadata)

    try:
        if args.dry_run_env_steps > 0:
            run_env_dry_check(config, args)
            return
        if args.mode == "eval":
            eval_loop(config, args, writer)
        else:
            train_loop(config, args, writer)
    finally:
        if writer is not None:
            writer.close()


if __name__ == "__main__":
    main()
