"""Standalone run-manifest serialization and export ownership."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from ha_ctse_process.standalone_agent import StandaloneProcessAgent


ALGORITHM_MANIFEST_FIELDS = (
    "algorithm",
    "network_scale_profile",
    "low_level_architecture",
    "policy_update_mode",
    "allow_off_policy_policy_updates",
    "process_segment_replay_enabled",
    "high_controller",
    "r30_keep_init",
    "r30_bridge_context_mode",
    "r30_high_buffer_version",
    "r30_high_ppo_epochs",
    "r30_high_actor_advantage_mode",
    "r30_force_refresh_every_check",
    "r39_native_categorical_edit",
    "r39_toy_fixed_skill_primitives",
    "r39_toy_direct_state_context",
    "r39_toy_fixed_skill_action_schema",
    "constant_skill_no_high",
    "aem_joint_novelty_enabled",
    "aem_joint_position_grid_size",
    "aem_joint_position_table_size",
    "aem_episode_horizon",
    "aem_position_view_name",
    "aem_bonus_formula",
    "r37_identity_gate_enabled",
    "alice_bob_actor_identity_mode",
    "alice_bob_actor_identity_slots",
    "alice_bob_actor_identity_schema",
    "alice_bob_semantic_reward_enabled",
    "r38_world_size",
    "r38_action_scale",
    "r38_zone_radius",
    "r38_anchor_required_steps",
    "r38_shuttle_stages",
    "r30_high_gae_lambda",
    "r31_effect_mode",
    "r31_effect_window",
    "r31_effect_coef",
    "r31_effect_clip",
    "r31_effect_hidden_dim",
    "r31_effect_schema_version",
    "r31_effect_view_name",
    "r31_effect_gate_status",
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
    "enable_team_conditioned_qd_probe",
    "team_conditioned_qd_hidden_dim",
    "team_conditioned_qd_lr",
    "team_conditioned_qd_min_samples",
    "enable_assignment_actionability_reward",
    "assignment_actionability_coef",
    "r24_qd_export_windows",
    "r24_qd_export_dir",
    "r24_qd_export_max_rows_per_update",
    "r24_qd_export_seed",
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
    "p2_recovery_credit_reward_on",
    "p2_recovery_reward_coef",
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
    "skill_forcing_reward_on",
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
    "lr_discoverer_actor",
    "lr_discoverer_critic",
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
    "low_gae_lambda",
    "low_value_clip",
    "low_value_loss_coef",
    "low_sequence_length",
    "low_sequence_batch_size",
    "low_ppo_epochs",
    "batch_size",
    "minibatch_size",
    "ppo_epochs",
    "rollout_length",
    "total_timesteps",
    "eval_interval",
    "r28_g1_arm",
    "r28_g1_scorer_path",
    "r29_action_info_mode",
    "r29_action_info_coef",
    "r29_action_info_clip",
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
            "high_controller": str(getattr(agent, "high_controller", "legacy_duration")),
            "k0": int(getattr(agent, "skill_interval", 10)),
            "r30_keep_init": float(getattr(agent, "r30_keep_init", 0.6)),
            "r30_high_buffer_version": int(
                getattr(agent, "r30_high_buffer_version", 1)
            ),
            "r30_high_ppo_epochs": int(
                getattr(agent, "high_ppo_epochs", 1)
            ),
            "r30_high_actor_advantage_mode": str(
                getattr(agent, "high_actor_advantage_mode", "smdp_gae")
            ),
            "constant_skill_no_high": bool(
                getattr(agent, "constant_skill_no_high", False)
            ),
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
            "fixed_skill_action_schema": str(
                getattr(agent, "r39_toy_fixed_skill_action_schema", "none")
            ),
            "direct_state_high_context": bool(
                getattr(agent, "r39_toy_direct_state_context", False)
            ),
            "fixed_skill_action_table": (
                agent.low.action_table.detach().cpu().tolist()
                if bool(getattr(agent, "r39_toy_fixed_skill_primitives", False))
                else None
            ),
            "parameter_counts": jsonable(agent.parameter_counts()),
        }
    with (metadata_dir / "run_manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
