"""Standalone training entrypoint for the HA-CTSE process-core algorithm.

This file is deliberately not a wrapper around ``train_multiproc_config_1.py``
or ``hmasd.agent``.  It owns the new algorithm's train/eval/checkpoint flow and
only reuses the shared environment/config infrastructure.
"""

from __future__ import annotations

import argparse
import csv
from copy import deepcopy
from dataclasses import fields, is_dataclass
from datetime import datetime
import importlib
import json
import random
from pathlib import Path
import time
import traceback
from types import SimpleNamespace
from typing import Any, Mapping, Sequence

import numpy as np
import torch

try:
    from torch.utils.tensorboard import SummaryWriter
except ModuleNotFoundError:
    SummaryWriter = None

from ha_ctse_process.env_factory import EnvSpec, make_env, normalize_scenario
from ha_ctse_process.collectors import SubprocEnvCollector, SyncEnvCollector
from ha_ctse_process.plotting import (
    AEM_METRIC_FIELDS,
    EVAL_FIELDS,
    R37_IDENTITY_METRIC_FIELDS,
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
from ha_ctse_process.r28_g1_reward import (
    ARMS as R28_G1_ARMS,
    FINAL_CHECKPOINT_ID as R28_G1_SOURCE_CHECKPOINT_ID,
    FINAL_CHECKPOINT_PATH as R28_G1_SOURCE_CHECKPOINT_PATH,
)
from ha_ctse_process.r29_action_information_reward import (
    MODES as R29_ACTION_INFO_MODES,
    REWARD_CLIP as R29_ACTION_INFO_REWARD_CLIP,
    REWARD_COEF as R29_ACTION_INFO_REWARD_COEF,
)
from ha_ctse_process.team_conditioned_qd import TEAM_CONDITIONED_QD_METRIC_FIELDS
from ha_ctse_process.topology_viz import capture_topology_frame, save_topology_artifacts


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


def empty_aem_metrics(active: bool = False) -> dict[str, float]:
    metrics = {field: 0.0 for field in AEM_METRIC_FIELDS}
    metrics["aem_active"] = float(bool(active))
    return metrics


def empty_r30_no_high_metrics() -> dict[str, float]:
    return {
        "r30_high_rows": 0.0,
        "r30_decision_rows": 0.0,
        "high_optimizer_steps": 0.0,
    }


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


class EpisodicJointPositionNovelty:
    """Per-vector-env direct-table counts for the registered R36 bonus."""

    def __init__(self, num_envs: int, grid_size: int, episode_horizon: int):
        self.num_envs = int(num_envs)
        self.grid_size = int(grid_size)
        self.episode_horizon = int(episode_horizon)
        self.table_size = int(self.grid_size**4)
        self.counts = np.zeros((self.num_envs, self.table_size), dtype=np.int32)
        self._metrics = empty_aem_metrics(active=True)
        self._bonus_min = float("inf")

    def _cell_index(self, normalized_positions: np.ndarray) -> int:
        positions = np.asarray(normalized_positions, dtype=np.float32).reshape(-1)
        if positions.shape != (4,) or not np.all(np.isfinite(positions)):
            raise ValueError("R36 AEM requires exactly four finite normalized position values")
        bins = np.floor(np.clip(positions, 0.0, 1.0) * self.grid_size).astype(
            np.int64
        )
        bins = np.minimum(bins, self.grid_size - 1)
        cell = int(bins[0])
        for value in bins[1:]:
            cell = cell * self.grid_size + int(value)
        if not 0 <= cell < self.table_size:
            raise RuntimeError("R36 AEM direct joint-position index is out of range")
        return cell

    def observe(self, env_id: int, normalized_positions: np.ndarray) -> float:
        env_id = int(env_id)
        cell = self._cell_index(normalized_positions)
        count_before = int(self.counts[env_id, cell])
        expected = 1.0 / (
            float(self.episode_horizon) * float(np.sqrt(count_before + 1.0))
        )
        bonus = float(expected)
        self.counts[env_id, cell] = count_before + 1

        self._metrics["aem_bonus_applied_steps"] += 1.0
        self._metrics["aem_bonus_sum"] += bonus
        self._metrics["aem_bonus_max"] = max(
            self._metrics["aem_bonus_max"], bonus
        )
        self._bonus_min = min(self._bonus_min, bonus)
        self._metrics["aem_preincrement_count_max"] = max(
            self._metrics["aem_preincrement_count_max"], float(count_before)
        )
        self._metrics["aem_formula_max_abs_error"] = max(
            self._metrics["aem_formula_max_abs_error"], abs(bonus - expected)
        )
        return bonus

    def reset_env(self, env_id: int) -> None:
        self.counts[int(env_id)].fill(0)
        self._metrics["aem_count_resets"] += 1.0

    def pop_update_metrics(self) -> dict[str, float]:
        metrics = dict(self._metrics)
        steps = metrics["aem_bonus_applied_steps"]
        metrics["aem_bonus_mean"] = (
            metrics["aem_bonus_sum"] / steps if steps > 0.0 else 0.0
        )
        metrics["aem_bonus_min"] = self._bonus_min if steps > 0.0 else 0.0
        self._metrics = empty_aem_metrics(active=True)
        self._bonus_min = float("inf")
        return metrics


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


def checkpoint_payload(
    agent: StandaloneProcessAgent,
    args: argparse.Namespace,
    config,
    total_steps: int,
    update_idx: int,
) -> dict[str, Any]:
    return {
        "checkpoint_schema_version": 2,
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
        "effect_posterior": (
            agent.r31_effect_posterior.full_head.state_dict()
            if getattr(agent, "r31_effect_posterior", None) is not None
            else None
        ),
        "effect_context_posterior": (
            agent.r31_effect_posterior.context_head.state_dict()
            if getattr(agent, "r31_effect_posterior", None) is not None
            else None
        ),
        "effect_optimizer": (
            agent.r31_effect_opt.state_dict()
            if getattr(agent, "r31_effect_opt", None) is not None
            else None
        ),
        "r31_effect_mode": str(getattr(agent, "r31_effect_mode", "off")),
        "r31_effect_schema_version": int(
            getattr(agent, "r31_effect_schema_version", 0)
        ),
        "effect_gate_status": str(
            getattr(agent, "r31_effect_gate_status", "UNTESTED")
        ),
        "effect_view_name": str(getattr(agent, "r31_effect_view_name", "")),
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
        "r28_g1": agent.r28_g1_checkpoint_state(),
        "r29_action_information": agent.r29_action_info_checkpoint_state(),
        "r30_high_value": (
            agent.high_value.state_dict()
            if getattr(agent, "high_value", None) is not None
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
        "high_controller": str(getattr(agent, "high_controller", "legacy_duration")),
        "r30_contract": (
            {
                "k0": int(getattr(agent, "skill_interval", 10)),
                "keep_init": float(getattr(agent, "r30_keep_init", 0.6)),
                "bridge_context_mode": "deterministic_expected",
                "high_buffer_version": int(getattr(agent, "r30_high_buffer_version", 1)),
            }
            if bool(getattr(agent, "r30_enabled", False))
            else None
        ),
        "checkpoint_migration": {
            "mode": str(getattr(agent, "checkpoint_migration_mode", "fresh")),
            "source_controller": str(
                getattr(agent, "checkpoint_source_controller", "none")
            ),
            "migrated_high_keys": tuple(
                getattr(agent, "checkpoint_migrated_high_keys", ())
            ),
            "dropped_high_keys": tuple(
                getattr(agent, "checkpoint_dropped_high_keys", ())
            ),
        },
        "team_bridge_type": str(getattr(config, "team_bridge_type", "stochastic")),
        "n_agents": agent.n_agents,
        "n_skills": agent.n_skills,
        "duration_candidates": agent.duration_candidates,
        "skill_interval": int(args.skill_interval),
        "r28_g1_arm": str(getattr(agent, "r28_g1_arm", "off")),
        "r28_g1_scorer_path": str(getattr(agent, "r28_g1_scorer_path", "")),
        "r29_action_info_mode": str(
            getattr(agent, "r29_action_info_mode", "off")
        ),
        "r29_action_info_coef": float(
            getattr(agent, "r29_action_info_coef", R29_ACTION_INFO_REWARD_COEF)
        ),
        "r29_action_info_clip": float(
            getattr(agent, "r29_action_info_clip", R29_ACTION_INFO_REWARD_CLIP)
        ),
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
        "z_assignment_residual_gain": float(getattr(config, "z_assignment_residual_gain", 0.0) or 0.0),
        "team_disc_actionability_floor": float(
            getattr(config, "team_disc_actionability_floor", 0.0) or 0.0
        ),
        "enable_assignment_actionability_probe": bool(
            getattr(config, "enable_assignment_actionability_probe", False)
        ),
        "enable_assignment_actionability_reward": bool(
            getattr(config, "enable_assignment_actionability_reward", False)
        ),
        "assignment_actionability_coef": float(getattr(config, "assignment_actionability_coef", 0.0) or 0.0),
        "assignment_actionability_clip": float(getattr(config, "assignment_actionability_clip", 0.0) or 0.0),
        "assignment_actionability_warmup_steps": int(
            getattr(config, "assignment_actionability_warmup_steps", 0) or 0
        ),
        "assignment_actionability_include_soft": bool(
            getattr(config, "assignment_actionability_include_soft", True)
        ),
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


def migrate_legacy_high_to_r30(
    agent: StandaloneProcessAgent,
    source_state: dict[str, torch.Tensor],
) -> list[str]:
    """Explicit v1 whitelist migration; unmatched R30 parameters stay initialized."""

    target_state = agent.high.state_dict()
    migrated: list[str] = []
    allowed_prefixes = ("input.", "skill_head.")
    for name, target in target_state.items():
        if not name.startswith(allowed_prefixes):
            continue
        source = source_state.get(name)
        if not isinstance(source, torch.Tensor) or tuple(source.shape) != tuple(target.shape):
            continue
        target_state[name] = source.detach().to(device=target.device, dtype=target.dtype).clone()
        migrated.append(name)
    required = {"input.3.weight", "input.3.bias", "skill_head.weight", "skill_head.bias"}
    missing_required = sorted(required.difference(migrated))
    if missing_required:
        raise ValueError(
            "legacy_to_r30_v1 migration cannot reuse required actor parameters: "
            + ",".join(missing_required)
        )
    agent.high.load_state_dict(target_state, strict=True)
    return migrated


def load_reward_pure_legacy_high(
    agent: StandaloneProcessAgent,
    source_state: dict[str, torch.Tensor],
) -> list[str]:
    """Drop only the retired sampled-team residual heads for the pair comparator."""

    retired = {
        "z_skill_residual.weight",
        "z_skill_residual.bias",
        "z_duration_residual.weight",
        "z_duration_residual.bias",
    }
    dropped = set(source_state).intersection(retired)
    unknown = {
        name
        for name in source_state
        if name not in agent.high.state_dict() and name not in retired
    }
    if unknown:
        raise ValueError(
            "reward-pure legacy migration found unsupported high keys: "
            + ",".join(sorted(unknown))
        )
    filtered = {name: value for name, value in source_state.items() if name not in retired}
    agent.high.load_state_dict(filtered, strict=True)
    return sorted(dropped)


def load_checkpoint(
    path: str | Path,
    agent: StandaloneProcessAgent,
    load_optimizers: bool = True,
) -> tuple[int, int]:
    checkpoint = torch.load(Path(path), map_location=agent.device)
    source_controller = str(checkpoint.get("high_controller") or "legacy_duration")
    agent.checkpoint_source_controller = source_controller
    if bool(getattr(agent, "r30_enabled", False)):
        if source_controller == "r30_fixed_clock_ar_edit":
            agent.high.load_state_dict(checkpoint["high"], strict=True)
            if checkpoint.get("r30_high_value") is None or agent.high_value is None:
                raise ValueError("R30 checkpoint is missing its high critic")
            agent.high_value.load_state_dict(checkpoint["r30_high_value"], strict=True)
            agent.checkpoint_migration_mode = "strict_r30_resume"
            agent.checkpoint_migrated_high_keys = tuple(agent.high.state_dict().keys())
        elif source_controller == "legacy_duration":
            migrated = migrate_legacy_high_to_r30(agent, checkpoint["high"])
            agent.checkpoint_migration_mode = "legacy_to_r30_v1"
            agent.checkpoint_migrated_high_keys = tuple(migrated)
        else:
            raise ValueError(f"unsupported R30 migration source {source_controller!r}")
    else:
        if source_controller != "legacy_duration":
            raise ValueError(
                "legacy duration controller cannot load an R30 checkpoint"
            )
        if bool(getattr(agent, "r30_pair_gate", False)):
            dropped = load_reward_pure_legacy_high(agent, checkpoint["high"])
            agent.checkpoint_migration_mode = "reward_pure_legacy_v1"
            agent.checkpoint_migrated_high_keys = tuple(
                name for name in agent.high.state_dict().keys()
            )
            agent.checkpoint_dropped_high_keys = tuple(dropped)
        else:
            agent.high.load_state_dict(checkpoint["high"], strict=True)
            agent.checkpoint_migration_mode = "strict_legacy_resume"
            agent.checkpoint_migrated_high_keys = tuple(agent.high.state_dict().keys())
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
    if bool(getattr(agent, "r31_enabled", False)):
        effect_state = checkpoint.get("effect_posterior")
        context_state = checkpoint.get("effect_context_posterior")
        if (effect_state is None) != (context_state is None):
            raise ValueError("R31 checkpoint contains only one posterior head")
        if effect_state is not None:
            if agent.r31_effect_posterior is None:
                raise RuntimeError("R31 posterior was not initialized")
            schema = int(checkpoint.get("r31_effect_schema_version", -1))
            if schema != int(agent.r31_effect_schema_version):
                raise ValueError(
                    f"R31 effect schema mismatch: checkpoint={schema}, "
                    f"requested={agent.r31_effect_schema_version}"
                )
            view_name = str(checkpoint.get("effect_view_name", ""))
            if view_name != str(agent.r31_effect_view_name):
                raise ValueError("R31 checkpoint effect view does not match")
            agent.r31_effect_posterior.full_head.load_state_dict(
                effect_state,
                strict=True,
            )
            agent.r31_effect_posterior.context_head.load_state_dict(
                context_state,
                strict=True,
            )
            agent.r31_effect_gate_status = str(
                checkpoint.get("effect_gate_status", "UNTESTED")
            ).upper()
        elif bool(getattr(agent, "r31_reward_enabled", False)):
            raise ValueError("R31 real_reward requires a gate-passed posterior")
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
    # Value-normalization statistics are part of the frozen inference state,
    # not optimizer state.  Evaluation-only checkpoint loads must restore them
    # so critic values retain their source-checkpoint scale.
    restore_high_state = not (
        bool(getattr(agent, "r30_enabled", False))
        and source_controller == "legacy_duration"
    )
    restore_high_optimizer = restore_high_state and not bool(
        getattr(agent, "r30_pair_gate", False)
    )
    if (
        restore_high_state
        and checkpoint.get("high_value_norm") is not None
        and agent.high_value_norm is not None
    ):
        agent.high_value_norm.load_state_dict(checkpoint["high_value_norm"])
    if checkpoint.get("low_value_norm") is not None and agent.low_value_norm is not None:
        agent.low_value_norm.load_state_dict(checkpoint["low_value_norm"])
    if load_optimizers:
        if "high_opt" in checkpoint and restore_high_optimizer:
            if bool(getattr(agent, "r30_enabled", False)):
                agent.high_opt.load_state_dict(checkpoint["high_opt"])
            else:
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
        if "process_opt" in checkpoint and not bool(
            getattr(agent, "r31_enabled", False)
        ):
            try:
                agent.process_opt.load_state_dict(checkpoint["process_opt"])
            except ValueError:
                pass
        if (
            checkpoint.get("effect_optimizer") is not None
            and getattr(agent, "r31_effect_opt", None) is not None
        ):
            agent.r31_effect_opt.load_state_dict(checkpoint["effect_optimizer"])
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
    if getattr(agent, "r28_g1_enabled", False):
        continuation = checkpoint.get("r28_g1")
        frozen_actor_base = None
        if continuation is not None:
            if not isinstance(continuation, dict):
                raise ValueError("R28-G1 checkpoint state is malformed")
            if str(continuation.get("arm")) != str(agent.r28_g1_arm):
                raise ValueError("R28-G1 checkpoint arm mismatch")
            frozen_actor_base = continuation.get("frozen_actor_base")
            if not isinstance(frozen_actor_base, dict):
                raise ValueError("R28-G1 checkpoint is missing frozen actor-base state")
        agent.attach_r28_g1_reward(
            scorer_path=agent.r28_g1_scorer_path,
            frozen_actor_base_state=frozen_actor_base,
        )
    return int(checkpoint.get("total_steps", 0)), int(checkpoint.get("update_idx", 0))


def _load_adjacent_run_manifest(path: str | Path) -> dict[str, Any]:
    checkpoint_path = Path(path)
    manifest_path = checkpoint_path.parent / "metadata" / "run_manifest.json"
    if not manifest_path.exists():
        return {}
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _manifest_lookup(manifest: dict[str, Any], name: str) -> Any:
    args = manifest.get("args") if isinstance(manifest.get("args"), dict) else {}
    algorithm = manifest.get("algorithm_config") if isinstance(manifest.get("algorithm_config"), dict) else {}
    training = manifest.get("training_config") if isinstance(manifest.get("training_config"), dict) else {}

    if name == "assignment_actionability_include_soft":
        for container in (args, algorithm, training):
            if name in container:
                return container.get(name)
        if "no_assignment_actionability_soft" in args:
            return not bool(args.get("no_assignment_actionability_soft"))
        return None

    for container in (args, algorithm, training):
        if name in container:
            return container.get(name)
    return None


def load_checkpoint_metadata(path: str | Path) -> dict[str, Any]:
    # Checkpoints are project-owned local artifacts.  PyTorch 2.6 changed the
    # default to weights_only=True, which cannot decode the registered runtime
    # ledger and NumPy RNG state.  Explicit False preserves the historical
    # loader contract while keeping the trust boundary at the caller-selected
    # local path.
    checkpoint = torch.load(Path(path), map_location="cpu", weights_only=False)
    checkpoint_schema = int(checkpoint.get("checkpoint_schema_version", 1))
    if checkpoint_schema == 3:
        event = checkpoint.get("event_architecture")
        if checkpoint.get("high_controller") != "variable_roster_event":
            raise ValueError("schema-3 checkpoint has the wrong high controller")
        if not isinstance(event, dict):
            raise ValueError("schema-3 checkpoint is missing event_architecture")
        required_header = {
            "architecture_mode",
            "event_architecture_schema_version",
            "opportunity_schedule_name",
            "snapshot_capability_name",
            "snapshot_capability_version",
        }
        missing = sorted(required_header - set(event))
        if missing:
            raise ValueError(f"schema-3 event header is missing fields: {missing}")
        return {
            "checkpoint_schema_version": checkpoint_schema,
            "high_controller": "variable_roster_event",
            "event_architecture_mode": str(event["architecture_mode"]),
            "event_architecture_schema_version": int(
                event["event_architecture_schema_version"]
            ),
            "event_opportunity_schedule": str(event["opportunity_schedule_name"]),
            "snapshot_capability_name": str(event["snapshot_capability_name"]),
            "snapshot_capability_version": int(event["snapshot_capability_version"]),
        }
    manifest = _load_adjacent_run_manifest(path)
    raw_r28_g1 = checkpoint.get("r28_g1")
    r28_g1_metadata = None
    if isinstance(raw_r28_g1, dict):
        r28_g1_metadata = {
            name: raw_r28_g1.get(name)
            for name in (
                "arm",
                "scorer_path",
                "source_total_steps",
                "source_update_idx",
                "source_checkpoint_id",
                "engineering_smoke",
            )
        }
        r28_g1_metadata["has_frozen_actor_base"] = isinstance(
            raw_r28_g1.get("frozen_actor_base"), dict
        )
    raw_r29 = checkpoint.get("r29_action_information")
    r29_metadata = None
    if isinstance(raw_r29, dict):
        r29_metadata = {
            name: raw_r29.get(name)
            for name in (
                "variant",
                "mode",
                "coefficient",
                "clip",
                "skill_interval",
                "terminal_window",
            )
        }

    def meta(name: str) -> Any:
        return checkpoint.get(name) if name in checkpoint else _manifest_lookup(manifest, name)

    return {
        "checkpoint_schema_version": checkpoint.get("checkpoint_schema_version", 1),
        "high_controller": checkpoint.get("high_controller"),
        "r30_contract": checkpoint.get("r30_contract"),
        "checkpoint_migration": checkpoint.get("checkpoint_migration"),
        "duration_candidates": checkpoint.get("duration_candidates"),
        "n_agents": checkpoint.get("n_agents"),
        "n_skills": checkpoint.get("n_skills"),
        "opt_num_prototypes": checkpoint.get("opt_num_prototypes"),
        "preset": checkpoint.get("preset"),
        "scenario": checkpoint.get("scenario"),
        "action_space_type": checkpoint.get("action_space_type"),
        "action_dim": checkpoint.get("action_dim"),
        "use_recurrent_low_level": checkpoint.get("use_recurrent_low_level"),
        "low_level_architecture": checkpoint.get("low_level_architecture"),
        "skill_interval": meta("skill_interval"),
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
        "z_assignment_residual_gain": meta("z_assignment_residual_gain"),
        "team_disc_actionability_floor": meta("team_disc_actionability_floor"),
        "enable_assignment_actionability_probe": meta("enable_assignment_actionability_probe"),
        "enable_assignment_actionability_reward": meta("enable_assignment_actionability_reward"),
        "assignment_actionability_coef": meta("assignment_actionability_coef"),
        "assignment_actionability_clip": meta("assignment_actionability_clip"),
        "assignment_actionability_warmup_steps": meta("assignment_actionability_warmup_steps"),
        "assignment_actionability_include_soft": meta("assignment_actionability_include_soft"),
        "r28_g1": r28_g1_metadata,
        "r29_action_information": r29_metadata,
        "r31_effect_mode": checkpoint.get("r31_effect_mode"),
        "r31_effect_schema_version": checkpoint.get(
            "r31_effect_schema_version"
        ),
        "effect_gate_status": checkpoint.get("effect_gate_status"),
        "effect_view_name": checkpoint.get("effect_view_name"),
        "has_effect_posterior": (
            checkpoint.get("effect_posterior") is not None
            and checkpoint.get("effect_context_posterior") is not None
        ),
    }


def apply_checkpoint_structure(config, args: argparse.Namespace, metadata: dict[str, Any]) -> None:
    requested_controller = str(getattr(args, "high_controller", "") or "")
    source_controller = str(metadata.get("high_controller") or "legacy_duration")
    if int(metadata.get("checkpoint_schema_version", 1)) == 3:
        if source_controller != "variable_roster_event":
            raise ValueError("schema-3 checkpoint is not an event checkpoint")
        if requested_controller and requested_controller != source_controller:
            raise ValueError(
                "checkpoint high_controller mismatch: "
                f"requested={requested_controller}, source={source_controller}"
            )
        requested_mode = str(getattr(args, "event_architecture_mode", "") or "")
        source_mode = str(metadata.get("event_architecture_mode", ""))
        if requested_mode and requested_mode != source_mode:
            raise ValueError(
                "checkpoint event_architecture_mode mismatch: "
                f"requested={requested_mode}, source={source_mode}"
            )
        config.high_controller = source_controller
        config.event_architecture_mode = source_mode
        config.event_architecture_schema_version = int(
            metadata.get("event_architecture_schema_version", -1)
        )
        config.event_opportunity_schedule = str(
            metadata.get("event_opportunity_schedule", "")
        )
        return
    if not requested_controller:
        config.high_controller = source_controller
    elif requested_controller != source_controller:
        if not (
            requested_controller == "r30_fixed_clock_ar_edit"
            and source_controller == "legacy_duration"
        ):
            raise ValueError(
                "checkpoint high_controller mismatch: "
                f"requested={requested_controller}, source={source_controller}"
            )

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
    if metadata.get("z_assignment_residual_gain") is not None:
        config.z_assignment_residual_gain = float(metadata.get("z_assignment_residual_gain"))
    if metadata.get("team_disc_actionability_floor") is not None:
        config.team_disc_actionability_floor = float(metadata.get("team_disc_actionability_floor"))
    for name in (
        "enable_assignment_actionability_probe",
        "enable_assignment_actionability_reward",
        "assignment_actionability_include_soft",
    ):
        if metadata.get(name) is not None:
            setattr(config, name, bool(metadata.get(name)))
    for name in ("assignment_actionability_coef", "assignment_actionability_clip"):
        if metadata.get(name) is not None:
            setattr(config, name, float(metadata.get(name)))
    if metadata.get("assignment_actionability_warmup_steps") is not None:
        config.assignment_actionability_warmup_steps = int(metadata.get("assignment_actionability_warmup_steps"))
    if bool(getattr(config, "enable_team_intent", False)):
        if str(getattr(config, "team_bridge_type", "stochastic")) == "none":
            raise ValueError("checkpoint enables team intent but uses team_bridge_type='none'")
        config.low_actor_condition_on_team_code = False


def enforce_r28_g1_contract(
    config,
    args: argparse.Namespace,
    metadata: dict[str, Any] | None,
) -> None:
    """Apply the frozen G1 arm contract after checkpoint metadata restoration."""

    arm = str(getattr(args, "r28_g1_arm", "off"))
    engineering_smoke = bool(getattr(args, "r28_g1_engineering_smoke", False))
    config.r28_g1_arm = arm
    config.r28_g1_scorer_path = str(getattr(args, "r28_g1_scorer_path", "") or "")
    if arm == "off":
        if engineering_smoke:
            raise ValueError("R28-G1 engineering smoke requires r28_g1_arm=real_reward")
        return
    if arm not in R28_G1_ARMS:
        raise ValueError(f"unsupported R28-G1 arm {arm!r}")
    if not str(getattr(args, "resume_from", "")):
        raise ValueError("R28-G1 requires --resume_from")
    if not config.r28_g1_scorer_path:
        raise ValueError("R28-G1 requires --r28_g1_scorer_path")
    if metadata is None:
        raise ValueError("R28-G1 source checkpoint metadata was not loaded")
    if str(getattr(args, "device", "")) != "cuda":
        raise ValueError("R28-G1 is CUDA-only; CPU fallback is forbidden")
    if str(getattr(args, "eval_action_mode", "deterministic")) != "deterministic":
        raise ValueError("R28-G1 requires deterministic evaluation actions")
    if not torch.cuda.is_available():
        raise RuntimeError("R28-G1 requested CUDA but torch.cuda.is_available() is false")
    if int(getattr(args, "skill_interval", 0)) != 10:
        raise ValueError("R28-G1 requires skill_interval=10")
    if int(getattr(args, "rollout_length", 0)) != 500:
        raise ValueError("R28-G1 requires rollout_length=500")
    if str(getattr(args, "preset", "")) != "S7-S1":
        raise ValueError("R28-G1 requires preset S7-S1")
    if normalize_scenario(str(getattr(args, "scenario", ""))) != "energy":
        raise ValueError("R28-G1 requires the registered energy scenario")
    target_steps = int(getattr(args, "total_timesteps", 0))
    if engineering_smoke:
        if arm != "real_reward":
            raise ValueError("R28-G1 engineering smoke requires r28_g1_arm=real_reward")
        if int(getattr(args, "num_envs", 0)) != 1:
            raise ValueError("R28-G1 engineering smoke requires exactly one environment")
        if str(getattr(args, "collector_backend", "")) != "sync":
            raise ValueError("R28-G1 engineering smoke requires the single-process sync collector")
        if int(getattr(args, "low_ppo_epochs", 0)) != 1:
            raise ValueError("R28-G1 engineering smoke requires low_ppo_epochs=1")
        if target_steps != 1_000_500:
            raise ValueError("R28-G1 engineering smoke permits exactly one +500-step update")
        if int(getattr(args, "seed", -1)) != 28030:
            raise ValueError("R28-G1 engineering smoke requires seed 28030")
        if int(getattr(args, "eval_interval", -1)) != 0:
            raise ValueError("R28-G1 engineering smoke must not run evaluation")
    else:
        if int(getattr(args, "num_envs", 0)) != 16:
            raise ValueError("R28-G1 requires exactly 16 vector environments")
        if str(getattr(args, "collector_backend", "")) != "subproc":
            raise ValueError("R28-G1 requires the validated subproc collector")
        if int(getattr(args, "low_ppo_epochs", 0)) != 15:
            raise ValueError("R28-G1 requires low_ppo_epochs=15")
        if target_steps not in {1_008_000, 1_160_000}:
            raise ValueError("R28-G1 permits only the topology or registered +160k exposure")
        if target_steps == 1_008_000:
            if int(getattr(args, "seed", -1)) != 28030:
                raise ValueError("R28-G1 topology check requires seed 28030")
            if int(getattr(args, "eval_interval", -1)) != 0:
                raise ValueError("R28-G1 topology check must not run evaluation")
        else:
            if int(getattr(args, "seed", -1)) not in {28031, 28032, 28033}:
                raise ValueError("R28-G1 family run requires seed 28031, 28032, or 28033")
            if int(getattr(args, "eval_interval", 0)) != 80_000:
                raise ValueError("R28-G1 family run requires eval_interval=80000")
            if int(getattr(args, "eval_episodes", 0)) != 20:
                raise ValueError("R28-G1 family run requires eval_episodes=20")

    expected = {
        "n_agents": 6,
        "n_skills": 4,
        "action_space_type": "continuous",
        "use_recurrent_low_level": True,
        "low_level_architecture": "strict_hmasd_mappo",
    }
    for name, value in expected.items():
        if metadata.get(name) != value:
            raise ValueError(
                f"R28-G1 source {name} mismatch: {metadata.get(name)!r} != {value!r}"
            )
    if tuple(int(item) for item in metadata.get("duration_candidates") or ()) != (1, 2, 3, 4):
        raise ValueError("R28-G1 source duration candidates must be (1,2,3,4)")
    source_interval = metadata.get("skill_interval")
    if source_interval is not None and int(source_interval) != 10:
        raise ValueError("R28-G1 source checkpoint skill_interval is not 10")
    if bool(metadata.get("low_actor_condition_on_team_code")):
        raise ValueError("R28-G1 source low actor must remain blind to team code")

    continuation = metadata.get("r28_g1")
    if continuation is None:
        source_path = str(Path(args.resume_from)).replace("\\", "/")
        if not (
            source_path == R28_G1_SOURCE_CHECKPOINT_PATH
            or source_path.endswith(f"/{R28_G1_SOURCE_CHECKPOINT_PATH}")
        ):
            raise ValueError(
                "R28-G1 fresh start requires the registered R25 arm0 final path: "
                f"{R28_G1_SOURCE_CHECKPOINT_PATH}"
            )
        if int(metadata.get("total_steps", -1)) != 1_000_000:
            raise ValueError("R28-G1 must start from the R25 arm0 final 1,000,000-step source")
        if int(metadata.get("update_idx", -1)) != 32:
            raise ValueError("R28-G1 must start from source update_idx=32")
    else:
        if not isinstance(continuation, dict):
            raise ValueError("R28-G1 continuation state is malformed")
        if bool(continuation.get("engineering_smoke", False)):
            raise ValueError("R28-G1 engineering-smoke checkpoints are non-resumable")
        if str(continuation.get("arm")) != arm:
            raise ValueError("R28-G1 continuation arm does not match --r28_g1_arm")
        if int(continuation.get("source_total_steps", -1)) != 1_000_000:
            raise ValueError("R28-G1 continuation source total_steps drifted")
        if int(continuation.get("source_update_idx", -1)) != 32:
            raise ValueError("R28-G1 continuation source update_idx drifted")
        if str(continuation.get("source_checkpoint_id")) != R28_G1_SOURCE_CHECKPOINT_ID:
            raise ValueError("R28-G1 continuation source checkpoint identity drifted")
        saved_scorer = str(continuation.get("scorer_path") or "")
        if Path(saved_scorer).resolve() != Path(config.r28_g1_scorer_path).resolve():
            raise ValueError("R28-G1 continuation scorer path does not match the frozen run")
        if continuation.get("has_frozen_actor_base") is not True:
            raise ValueError("R28-G1 continuation is missing frozen actor-base state")

    disabled_false = (
        "enable_prototype_disc_reward",
        "enable_team_disc_reward",
        "enable_team_transition_reward",
        "enable_assignment_actionability_reward",
        "enable_g_info_objective",
        "enable_skill_forcing_reward",
        "skill_forcing_reward_on",
        "skill_effect_reward_on",
        "use_topology_potential_shaping",
        "p2_recovery_credit_reward_on",
        "duration_entropy_floor_enabled",
        "z_entropy_floor_enabled",
    )
    for name in disabled_false:
        setattr(config, name, False)
    disabled_zero = (
        "prototype_disc_reward_coef",
        "team_disc_coef",
        "team_transition_coef",
        "transition_skill_reward_coef",
        "outcome_residual_reward_coef",
        "topology_role_reward_coef",
        "topology_potential_coef",
        "p2_recovery_reward_coef",
        "skill_effect_ctrl_coef",
        "skill_effect_use_coef",
        "skill_force_disc_coef",
        "skill_force_effect_coef",
        "skill_force_duration_entropy_coef",
        "assignment_actionability_coef",
        "g_info_coef_skill",
        "g_info_coef_duration",
        "g_info_coef_edit",
        "situation_hazard_reward_coef",
        "duration_entropy_floor_coef",
        "z_entropy_floor_coef",
    )
    for name in disabled_zero:
        setattr(config, name, 0.0)
    config.use_process_reward_for_discoverer = False
    config.process_reward_mode = "none"
    config.process_reward_injection = "none"
    config.outcome_residual_injection = "none"
    config.topology_role_injection = "none"
    config.topology_potential_injection = "none"
    config.skill_effect_reward_injection = "none"
    config.skill_force_reward_injection = "none"


def enforce_r29_action_info_contract(
    config,
    args: argparse.Namespace,
) -> None:
    """Apply the lean, default-off R29 reward configuration."""

    mode = str(getattr(args, "r29_action_info_mode", "off"))
    coefficient = float(
        getattr(args, "r29_action_info_coef", R29_ACTION_INFO_REWARD_COEF)
    )
    clip = float(getattr(args, "r29_action_info_clip", R29_ACTION_INFO_REWARD_CLIP))
    config.r29_action_info_mode = mode
    config.r29_action_info_coef = coefficient
    config.r29_action_info_clip = clip
    if mode == "off":
        return
    if mode not in R29_ACTION_INFO_MODES:
        raise ValueError(f"unsupported R29 action-information mode {mode!r}")
    if mode == "real_reward":
        raise ValueError(
            "R29 online reward is retired; use probe_only for diagnostics"
        )
    if str(getattr(args, "r28_g1_arm", "off")) != "off":
        raise ValueError("R29 and R28 rewards cannot be enabled together")
    if not np.isfinite(coefficient) or coefficient <= 0.0:
        raise ValueError("R29 coefficient must be finite and positive")
    if not np.isfinite(clip) or clip <= 0.0:
        raise ValueError("R29 clip must be finite and positive")
    if int(getattr(args, "skill_interval", 0)) != 10:
        raise ValueError("R29-T10 requires skill_interval=10")
    if tuple(int(value) for value in config.skill_lifetime_candidates) != (1, 2, 3, 4):
        raise ValueError("R29-T10 requires skill lifetimes (1,2,3,4)")


def is_variable_roster_event(config) -> bool:
    return str(getattr(config, "high_controller", "")) == "variable_roster_event"


def enforce_variable_roster_event_contract(
    config,
    args: argparse.Namespace,
    metadata: dict[str, Any] | None,
) -> None:
    """Validate the event header without importing or constructing the runtime."""

    if not is_variable_roster_event(config):
        return
    mode = str(getattr(config, "event_architecture_mode", "")).lower()
    if mode not in {"f0", "f1"}:
        raise ValueError("variable_roster_event requires event_architecture_mode=f0|f1")
    if int(getattr(config, "event_architecture_schema_version", -1)) != 1:
        raise ValueError("variable_roster_event requires architecture schema version 1")
    if str(getattr(config, "event_opportunity_schedule", "")) != (
        "uniform_active_gap_v1"
    ):
        raise ValueError("variable_roster_event requires uniform_active_gap_v1")
    if metadata is not None and int(metadata.get("checkpoint_schema_version", -1)) != 3:
        raise ValueError("event resume rejects legacy/schema-1/schema-2 checkpoints")
    if str(getattr(args, "r28_g1_arm", "off")) != "off":
        raise ValueError("variable_roster_event rejects R28-G1")
    if str(getattr(args, "r29_action_info_mode", "off")) != "off":
        raise ValueError("variable_roster_event rejects R29 action information")
    if str(getattr(args, "r31_effect_mode", "off") or "off") != "off":
        raise ValueError("variable_roster_event rejects R31 effect objectives")


def dispatch_variable_roster_event_boundary(config) -> None:
    """Lazy event import and fail-closed stop before collector construction."""

    from ha_ctse_process.variable_roster_event import (
        assert_deterministic_trace_boundary,
    )

    assert_deterministic_trace_boundary(config)


def enforce_r30_contract(config, args: argparse.Namespace) -> None:
    """Fail closed around R30 and its explicit Alice--Bob toy lane."""

    mode = str(getattr(config, "high_controller", "legacy_duration"))
    if mode == "legacy_duration":
        return
    if mode != "r30_fixed_clock_ar_edit":
        raise ValueError(f"unsupported high_controller={mode!r}")

    if str(getattr(args, "r28_g1_arm", "off")) != "off":
        raise ValueError("R30 requires r28_g1_arm=off")
    if str(getattr(args, "r29_action_info_mode", "off")) != "off":
        raise ValueError("R30 requires r29_action_info_mode=off")
    skill_interval = int(getattr(args, "skill_interval", 0))
    native_toy = bool(getattr(config, "r39_native_categorical_edit", False))
    constant_skill_no_high = bool(getattr(config, "constant_skill_no_high", False))
    if native_toy:
        if normalize_scenario(str(getattr(args, "scenario", ""))) != (
            "two_timescale_role_free_actions"
        ):
            raise ValueError("R39 native categorical mode is restricted to its toy gate")
        if skill_interval != int(getattr(config, "r39_toy_k0", 0)):
            raise ValueError("R39 toy requires skill_interval=r39_toy_k0")
    elif not constant_skill_no_high and skill_interval != 10:
        raise ValueError("R30 requires skill_interval=10")
    if str(getattr(args, "device", "cuda")).lower() != "cuda":
        raise ValueError("R30 requires explicit CUDA")
    if not torch.cuda.is_available():
        raise RuntimeError("R30 requested CUDA but CUDA is unavailable")
    if bool(getattr(args, "enable_team_intent", False)):
        raise ValueError("R30 does not admit sampled team intent")
    if bool(getattr(args, "enable_low_actor_team_code", False)):
        raise ValueError("R30 preserves the low actor skill bottleneck")

    explicit_reward_args = (
        "enable_prototype_disc_reward",
        "enable_team_transition_reward",
        "enable_team_disc_reward",
        "enable_assignment_actionability_reward",
        "enable_skill_effect_reward",
        "enable_skill_forcing_reward",
        "p2_recovery_credit_reward_on",
        "enable_topology_potential_shaping",
    )
    enabled_rewards = [name for name in explicit_reward_args if bool(getattr(args, name, False))]
    transition_reward_coef = float(
        getattr(config, "transition_skill_reward_coef", 0.0)
    )
    alice_bob_semantic_lane = bool(
        normalize_scenario(str(getattr(args, "scenario", "")))
        == "alice_bob_asymmetric_cycles"
        and getattr(config, "alice_bob_semantic_reward_enabled", False)
    )
    if transition_reward_coef != 0.0 and not alice_bob_semantic_lane:
        enabled_rewards.append("transition_skill_reward_coef")
    injection_switches = (
        "process_reward_injection",
        "outcome_residual_injection",
        "topology_role_injection",
        "topology_potential_injection",
    )
    enabled_injections = [
        name
        for name in injection_switches
        if str(getattr(args, name, "")).lower() not in {"", "none"}
    ]
    if enabled_rewards or enabled_injections:
        raise ValueError(
            "R30 is reward-pure outside the explicit Alice--Bob semantic lane; "
            "disable intrinsic reward paths: "
            + ",".join(enabled_rewards + enabled_injections)
        )

    explicit_edit = getattr(args, "edit_penalty_alpha", None)
    explicit_switch = getattr(args, "switch_penalty_beta", None)
    if explicit_edit not in {None, 0, 0.0} or explicit_switch not in {None, 0, 0.0}:
        raise ValueError("R30 forbids edit and switch penalties")
    if bool(getattr(args, "enable_duration_entropy_floor", False)):
        raise ValueError("R30 forbids the duration entropy floor")

    if bool(getattr(config, "r39_toy_direct_state_context", False)):
        config.team_bridge_type = "none"
        config.r30_bridge_context_mode = "direct_state_zero_team"
    else:
        config.team_bridge_type = "deterministic_expected"
        config.r30_bridge_context_mode = "deterministic_expected"
    config.r30_keep_init = 0.6
    config.r30_high_buffer_version = 1
    config.high_keep_entropy_coef = 0.0
    config.edit_penalty_alpha = 0.0
    config.switch_penalty_beta = 0.0
    config.duration_entropy_floor_enabled = False
    config.z_entropy_floor_enabled = False
    config.enable_team_intent = False
    config.enable_team_disc_probe = False
    config.enable_assignment_actionability_probe = False
    config.enable_g_info_objective = False
    config.use_compact_return_head = False
    config.z_assignment_residual_gain = 0.0
    config.low_actor_condition_on_team_code = False
    for name in (
        "enable_prototype_disc_reward",
        "enable_team_transition_reward",
        "enable_team_disc_reward",
        "enable_assignment_actionability_reward",
        "skill_effect_reward_on",
        "enable_skill_forcing_reward",
        "p2_recovery_credit_reward_on",
        "use_topology_potential_shaping",
    ):
        setattr(config, name, False)
    config.process_reward_injection = "none"
    config.outcome_residual_injection = "none"
    config.topology_role_injection = "none"
    config.topology_potential_injection = "none"
    config.skill_effect_reward_injection = "none"
    config.skill_force_reward_injection = "none"
    config.parallel_selection = False
    config.use_autoregressive_selection = True
    config.ar_prefix_mode = "roster"
    config.r29_action_info_mode = "off"


def enforce_r31_contract(
    config,
    args: argparse.Namespace,
    metadata: dict[str, Any] | None,
) -> None:
    """Fail closed around the single accepted R31-CFEI route."""

    mode = str(getattr(config, "r31_effect_mode", "off")).lower()
    if mode == "off":
        return
    if mode not in {"probe_only", "real_reward"}:
        raise ValueError(f"unsupported r31_effect_mode={mode!r}")
    if mode == "real_reward":
        raise ValueError(
            "R31-CFEI real_reward is retired after a valid causal gate failure; "
            "R31 remains diagnostic-only via probe_only"
        )
    if normalize_scenario(str(getattr(args, "scenario", ""))) != "alice_bob_asymmetric_cycles":
        raise ValueError("R31 is restricted to the sparse Alice--Bob environment")
    if str(getattr(config, "high_controller", "")) != "r30_fixed_clock_ar_edit":
        raise ValueError("R31 requires the adaptive R30 fixed-clock controller")
    if bool(getattr(args, "r30_pair_gate", False)):
        raise ValueError("R31 is not part of the legacy/shared-k R30 pair gate")
    window = int(getattr(config, "r31_effect_window", 0))
    if window != 10 or window != int(getattr(args, "skill_interval", 0)):
        raise ValueError("R31 requires W=skill_interval=k0=10")
    if bool(getattr(config, "alice_bob_semantic_reward_enabled", False)):
        raise ValueError("R31 forbids the legacy one-step semantic reward")
    if float(getattr(config, "transition_skill_reward_coef", 0.0)) != 0.0:
        raise ValueError("R31 requires transition_skill_reward_coef=0")
    if float(getattr(config, "alice_bob_progress_reward_coef", 0.0)) != 0.0:
        raise ValueError("R31 requires the sparse unshaped Alice--Bob reward")
    if str(getattr(args, "r28_g1_arm", "off")) != "off":
        raise ValueError("R31 requires r28_g1_arm=off")
    if str(getattr(args, "r29_action_info_mode", "off")) != "off":
        raise ValueError("R31 requires r29_action_info_mode=off")
    coefficient = float(getattr(config, "r31_effect_coef", 0.02))
    clip = float(getattr(config, "r31_effect_clip", 0.05))
    if not np.isfinite(coefficient) or coefficient <= 0.0:
        raise ValueError("R31 effect coefficient must be finite and positive")
    if not np.isfinite(clip) or clip <= 0.0:
        raise ValueError("R31 effect clip must be finite and positive")
    view_name = "alice_bob_normalized_joint_positions_v1"
    configured_view = str(getattr(config, "r31_effect_view_name", view_name))
    if configured_view != view_name:
        raise ValueError("R31 admits only normalized joint agent positions v1")
    config.r31_effect_view_name = view_name
    config.r31_effect_gate_status = str(
        (metadata or {}).get("effect_gate_status") or "UNTESTED"
    ).upper()


def enforce_aem_contract(
    config,
    args: argparse.Namespace,
    metadata: dict[str, Any] | None,
) -> None:
    """Fail closed around the single registered R36-AEM treatment."""

    if not bool(getattr(config, "aem_joint_novelty_enabled", False)):
        return
    if normalize_scenario(str(getattr(args, "scenario", ""))) != "alice_bob_asymmetric_cycles":
        raise ValueError("R36 AEM is restricted to the sparse Alice--Bob environment")
    if not bool(getattr(config, "constant_skill_no_high", False)):
        raise ValueError("R36 AEM requires the constant-code no-high MAPPO path")
    if str(getattr(config, "high_controller", "")) != "r30_fixed_clock_ar_edit":
        raise ValueError("R36 AEM requires the architecture-matched R30 module layout")
    if int(getattr(config, "n_agents", 0)) != 2:
        raise ValueError("R36 AEM requires exactly two agents")

    exact_config = {
        "aem_joint_position_grid_size": 5,
        "aem_joint_position_table_size": 625,
        "aem_episode_horizon": 80,
        "episode_length": 80,
        "low_ppo_epochs": 5,
        "low_sequence_length": 10,
        "low_sequence_batch_size": 64,
    }
    for name, expected in exact_config.items():
        actual = int(getattr(config, name, -1))
        if actual != expected:
            raise ValueError(f"R36 AEM requires {name}={expected}, got {actual}")
    if str(getattr(config, "aem_position_view_name", "")) != (
        "alice_bob_normalized_joint_positions_v1"
    ):
        raise ValueError("R36 AEM admits only normalized joint agent positions v1")
    if str(getattr(config, "aem_bonus_formula", "")) != (
        "inverse_horizon_sqrt_preincrement_v1"
    ):
        raise ValueError("R36 AEM bonus formula does not match the registered contract")
    if bool(getattr(config, "alice_bob_semantic_reward_enabled", False)):
        raise ValueError("R36 AEM forbids the Alice--Bob semantic reward")
    if float(getattr(config, "transition_skill_reward_coef", 0.0)) != 0.0:
        raise ValueError("R36 AEM forbids transition-skill reward")
    if str(getattr(config, "r31_effect_mode", "off")).lower() != "off":
        raise ValueError("R36 AEM forbids R31 effect reward or diagnostics")

    if str(getattr(args, "mode", "train")) != "train":
        return
    if not str(getattr(args, "resume_from", "")) or metadata is None:
        raise ValueError("R36 AEM requires the shared neutral zero-step checkpoint")
    if int(metadata.get("total_steps", -1)) != 0 or int(
        metadata.get("update_idx", -1)
    ) != 0:
        raise ValueError("R36 AEM source checkpoint must have zero environment steps")
    exact_args = {
        "seed": 37031,
        "n_agents": 2,
        "num_envs": 16,
        "rollout_length": 80,
        "skill_interval": 10,
        "total_timesteps": 320_000,
        "eval_interval": 320_000,
        "eval_episodes": 64,
        "eval_max_steps": 80,
    }
    for name, expected in exact_args.items():
        actual = int(getattr(args, name, -1))
        if actual != expected:
            raise ValueError(f"R36 AEM requires {name}={expected}, got {actual}")
    if str(getattr(args, "collector_backend", "")) != "subproc":
        raise ValueError("R36 AEM requires the subproc collector")
    if str(getattr(args, "collector_start_method", "")) != "spawn":
        raise ValueError("R36 AEM requires spawn workers")
    if str(getattr(args, "device", "")).lower() != "cuda":
        raise ValueError("R36 AEM requires explicit CUDA")
    if str(getattr(args, "eval_action_mode", "")) != "stochastic":
        raise ValueError("R36 AEM requires stochastic final evaluation")


def enforce_r37_identity_contract(
    config,
    args: argparse.Namespace,
    metadata: dict[str, Any] | None,
) -> None:
    """Fail closed around the registered R37 observation-substrate gate."""

    if not bool(getattr(config, "r37_identity_gate_enabled", False)):
        return
    identity_mode = str(
        getattr(config, "alice_bob_actor_identity_mode", "")
    ).lower()
    if identity_mode not in {"masked", "visible"}:
        raise ValueError("R37 requires masked or visible identity slots")
    if normalize_scenario(str(getattr(args, "scenario", ""))) != (
        "alice_bob_asymmetric_cycles"
    ):
        raise ValueError("R37 is restricted to the sparse Alice--Bob environment")
    if not bool(getattr(config, "constant_skill_no_high", False)):
        raise ValueError("R37 requires the constant-code no-high MAPPO path")
    if str(getattr(config, "high_controller", "")) != "r30_fixed_clock_ar_edit":
        raise ValueError("R37 requires the architecture-matched R30 module layout")

    exact_config = {
        "n_agents": 2,
        "obs_dim": 16,
        "state_dim": 19,
        "alice_bob_actor_identity_slots": 4,
        "episode_length": 80,
        "low_ppo_epochs": 5,
        "low_sequence_length": 10,
        "low_sequence_batch_size": 64,
    }
    for name, expected in exact_config.items():
        actual = int(getattr(config, name, -1))
        if actual != expected:
            raise ValueError(f"R37 requires {name}={expected}, got {actual}")
    if str(getattr(config, "alice_bob_actor_identity_schema", "")) != (
        "active_plate_target_onehot_v1"
    ):
        raise ValueError("R37 identity schema does not match the registered contract")
    if bool(getattr(config, "aem_joint_novelty_enabled", False)):
        raise ValueError("R37 forbids the retired R36 novelty bonus")
    if bool(getattr(config, "alice_bob_semantic_reward_enabled", False)):
        raise ValueError("R37 forbids Alice--Bob semantic reward")
    if float(getattr(config, "transition_skill_reward_coef", 0.0)) != 0.0:
        raise ValueError("R37 forbids transition-skill reward")
    if str(getattr(config, "r31_effect_mode", "off")).lower() != "off":
        raise ValueError("R37 forbids R31 effect reward or diagnostics")

    if str(getattr(args, "mode", "train")) != "train":
        return
    exact_common = {
        "seed": 38031,
        "n_agents": 2,
        "rollout_length": 80,
        "skill_interval": 10,
        "eval_max_steps": 80,
    }
    for name, expected in exact_common.items():
        actual = int(getattr(args, name, -1))
        if actual != expected:
            raise ValueError(f"R37 requires {name}={expected}, got {actual}")
    if str(getattr(args, "device", "")).lower() != "cuda":
        raise ValueError("R37 requires explicit CUDA")
    if str(getattr(args, "eval_action_mode", "")) != "stochastic":
        raise ValueError("R37 requires stochastic evaluation")

    total_timesteps = int(getattr(args, "total_timesteps", -1))
    if total_timesteps == 0 and not str(getattr(args, "resume_from", "")):
        if identity_mode != "masked":
            raise ValueError("R37 neutral initialization must use masked identity slots")
        if int(getattr(args, "num_envs", -1)) != 1:
            raise ValueError("R37 neutral initialization requires one sync environment")
        if str(getattr(args, "collector_backend", "")) != "sync":
            raise ValueError("R37 neutral initialization requires the sync collector")
        if int(getattr(args, "eval_interval", -1)) != 0:
            raise ValueError("R37 neutral initialization requires eval_interval=0")
        return

    if not str(getattr(args, "resume_from", "")) or metadata is None:
        raise ValueError("R37 training requires the shared neutral zero-step checkpoint")
    if int(metadata.get("total_steps", -1)) != 0 or int(
        metadata.get("update_idx", -1)
    ) != 0:
        raise ValueError("R37 source checkpoint must have zero environment steps")
    source_manifest = _load_adjacent_run_manifest(args.resume_from)
    source_algorithm = source_manifest.get("algorithm_config", {})
    source_model = source_manifest.get("model_config", {})
    if not isinstance(source_algorithm, dict):
        source_algorithm = {}
    if not isinstance(source_model, dict):
        source_model = {}
    if str(source_algorithm.get("alice_bob_actor_identity_mode", "")) != "masked":
        raise ValueError("R37 source checkpoint must use masked identity slots")
    if int(source_model.get("obs_dim", -1)) != 16:
        raise ValueError("R37 source checkpoint must have obs_dim=16")

    exact_training = {
        "num_envs": 16,
        "total_timesteps": 320_000,
        "eval_interval": 320_000,
        "eval_episodes": 64,
    }
    for name, expected in exact_training.items():
        actual = int(getattr(args, name, -1))
        if actual != expected:
            raise ValueError(f"R37 requires {name}={expected}, got {actual}")
    if str(getattr(args, "collector_backend", "")) != "subproc":
        raise ValueError("R37 requires the subproc collector")
    if str(getattr(args, "collector_start_method", "")) != "spawn":
        raise ValueError("R37 requires spawn workers")


def enforce_r30_pair_gate(
    config,
    args: argparse.Namespace,
    metadata: dict[str, Any] | None,
) -> None:
    """Apply controls shared by both arms of the registered R30 pair."""

    if not bool(getattr(args, "r30_pair_gate", False)):
        return
    controller = str(getattr(config, "high_controller", "legacy_duration"))
    if controller not in {"legacy_duration", "r30_fixed_clock_ar_edit"}:
        raise ValueError(f"R30 pair does not admit high_controller={controller!r}")
    if metadata is None or not str(getattr(args, "resume_from", "")):
        raise ValueError("R30 pair requires the registered pre-R30 checkpoint")
    source_path = str(Path(args.resume_from)).replace("\\", "/")
    if not (
        source_path == R28_G1_SOURCE_CHECKPOINT_PATH
        or source_path.endswith(f"/{R28_G1_SOURCE_CHECKPOINT_PATH}")
    ):
        raise ValueError(
            "R30 pair requires the registered R25 arm0 source: "
            f"{R28_G1_SOURCE_CHECKPOINT_PATH}"
        )
    if int(metadata.get("total_steps", -1)) != 1_000_000:
        raise ValueError("R30 pair source must be the 1,000,000-step R25 checkpoint")
    if int(metadata.get("update_idx", -1)) != 32:
        raise ValueError("R30 pair source must be checkpoint update 32")
    if str(metadata.get("high_controller") or "legacy_duration") != "legacy_duration":
        raise ValueError("R30 pair source must use the legacy-duration controller")
    if int(metadata.get("n_agents", -1)) != 6 or int(metadata.get("n_skills", -1)) != 4:
        raise ValueError("R30 pair source must have six agents and four skills")
    if tuple(int(item) for item in metadata.get("duration_candidates") or ()) != (1, 2, 3, 4):
        raise ValueError("R30 pair source must have duration candidates (1,2,3,4)")

    exact = {
        "seed": 30031,
        "num_envs": 16,
        "rollout_length": 501,
        "skill_interval": 10,
        "total_timesteps": 1_320_000,
        "low_ppo_epochs": 15,
        "eval_interval": 320_000,
        "eval_episodes": 20,
    }
    for name, expected in exact.items():
        actual = int(getattr(args, name, -1))
        if actual != expected:
            raise ValueError(f"R30 pair requires {name}={expected}, got {actual}")
    if str(getattr(args, "preset", "")) != "S7-S1":
        raise ValueError("R30 pair requires preset S7-S1")
    if normalize_scenario(str(getattr(args, "scenario", ""))) != "energy":
        raise ValueError("R30 pair requires the energy scenario")
    if str(getattr(args, "collector_backend", "")) != "subproc":
        raise ValueError("R30 pair requires the subproc collector")
    if str(getattr(args, "collector_start_method", "")) != "spawn":
        raise ValueError("R30 pair requires spawn workers")
    if str(getattr(args, "device", "")).lower() != "cuda":
        raise ValueError("R30 pair requires explicit CUDA")
    if str(getattr(args, "eval_action_mode", "")) != "deterministic":
        raise ValueError("R30 pair requires deterministic evaluation")
    if not torch.cuda.is_available():
        raise RuntimeError("R30 pair requested CUDA but CUDA is unavailable")
    if str(getattr(args, "r28_g1_arm", "off")) != "off":
        raise ValueError("R30 pair requires r28_g1_arm=off")
    if str(getattr(args, "r29_action_info_mode", "off")) != "off":
        raise ValueError("R30 pair requires r29_action_info_mode=off")

    disabled_false = (
        "enable_prototype_disc_probe",
        "enable_prototype_disc_reward",
        "enable_team_transition_probe",
        "enable_team_transition_reward",
        "enable_team_intent",
        "enable_team_disc_probe",
        "enable_team_disc_reward",
        "enable_assignment_actionability_probe",
        "enable_assignment_actionability_reward",
        "enable_g_info_objective",
        "skill_effect_discovery_on",
        "skill_effect_intervention_probe_on",
        "skill_effect_reward_on",
        "skill_force_probe_on",
        "enable_skill_forcing_probe",
        "enable_skill_forcing_reward",
        "skill_forcing_reward_on",
        "use_topology_potential_shaping",
        "p2_recovery_credit_reward_on",
        "duration_entropy_floor_enabled",
        "z_entropy_floor_enabled",
        "use_compact_return_head",
    )
    for name in disabled_false:
        setattr(config, name, False)
    disabled_zero = (
        "prototype_disc_reward_coef",
        "team_transition_coef",
        "team_disc_coef",
        "assignment_actionability_coef",
        "transition_skill_reward_coef",
        "outcome_residual_reward_coef",
        "topology_role_reward_coef",
        "topology_potential_coef",
        "p2_recovery_reward_coef",
        "skill_effect_ctrl_coef",
        "skill_effect_use_coef",
        "skill_force_disc_coef",
        "skill_force_effect_coef",
        "skill_force_duration_entropy_coef",
        "g_info_coef_skill",
        "g_info_coef_duration",
        "g_info_coef_edit",
        "situation_hazard_reward_coef",
        "duration_entropy_floor_coef",
        "z_entropy_floor_coef",
        "edit_penalty_alpha",
        "switch_penalty_beta",
        "z_assignment_residual_gain",
    )
    for name in disabled_zero:
        setattr(config, name, 0.0)
    config.use_process_reward_for_discoverer = False
    config.process_reward_mode = "none"
    config.process_reward_injection = "none"
    config.outcome_residual_injection = "none"
    config.topology_role_injection = "none"
    config.topology_potential_injection = "none"
    config.skill_effect_reward_injection = "none"
    config.skill_force_reward_injection = "none"
    config.team_bridge_type = "deterministic_expected"
    config.low_actor_condition_on_team_code = False
    config.parallel_selection = False
    config.use_autoregressive_selection = True
    config.ar_prefix_mode = "roster"
    config.r29_action_info_mode = "off"
    config.r30_pair_gate = True


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
    active_duration_indices_backup = agent.active_duration_indices.copy()
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
    episode_steps_backup = agent.episode_steps.copy()
    episode_ids_backup = agent.episode_ids.copy()
    steps_to_check_backup = agent.steps_to_check.copy()
    high_check_buffer_backup = agent.high_check_buffer
    if bool(getattr(agent, "r30_enabled", False)):
        agent.high_check_buffer = type(high_check_buffer_backup)(
            agent.num_envs, agent.n_agents, agent.gamma
        )
    last_low_context_backup = list(agent._last_low_context)
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
    is_alice_bob = normalize_scenario(config.scenario) == "alice_bob_asymmetric_cycles"
    eval_seed_blocks = tuple(
        int(token.strip())
        for token in str(getattr(args, "eval_seed_blocks", "")).split(",")
        if token.strip()
    )
    episodes_per_seed = int(getattr(args, "eval_episodes_per_seed", 0))
    if eval_seed_blocks:
        if episodes_per_seed <= 0:
            raise ValueError("eval_seed_blocks requires eval_episodes_per_seed > 0")
        expected_episodes = len(eval_seed_blocks) * episodes_per_seed
        if int(episodes) != expected_episodes:
            raise ValueError(
                f"fixed eval seed blocks require {expected_episodes} episodes, got {episodes}"
            )

    def alice_bob_joint_cell(state_value) -> tuple[int, int, int, int] | None:
        if state_value is None:
            return None
        positions = np.asarray(state_value, dtype=np.float32).reshape(-1)[:4]
        if positions.size != 4 or not np.all(np.isfinite(positions)):
            return None
        return tuple(
            np.clip(np.floor(positions * 5.0), 0, 4)
            .astype(np.int64)
            .tolist()
        )

    try:
        for episode_idx in range(max(int(episodes), 1)):
            if eval_seed_blocks:
                block_index = episode_idx // episodes_per_seed
                within_block = episode_idx % episodes_per_seed
                block_seed = eval_seed_blocks[block_index]
                reset_seed = block_seed * 1000 + within_block
                if within_block == 0:
                    random.seed(block_seed)
                    np.random.seed(block_seed)
                    torch.manual_seed(block_seed)
                    if torch.cuda.is_available():
                        torch.cuda.manual_seed_all(block_seed)
            else:
                reset_seed = int(args.seed) + 100000 + episode_idx
            obs, info = env.reset(seed=reset_seed)
            state = info.get("state")
            agent.reset_env_state(0)
            episode_reward = 0.0
            episode_length = 0
            last_info = info
            backhaul_connected_steps: list[float] = []
            throughput_when_backhaul_connected_steps: list[float] = []
            coverage_eq1_steps: list[float] = []
            coverage_positive_steps: list[float] = []
            joint_position_cells: set[tuple[int, int, int, int]] = set()
            r37_eval_metrics = empty_r37_identity_metrics(config)
            initial_joint_cell = alice_bob_joint_cell(state) if is_alice_bob else None
            if initial_joint_cell is not None:
                joint_position_cells.add(initial_joint_cell)
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
                identity_audit = audit_r37_identity_observation(config, obs, state)
                r37_eval_metrics["r37_identity_audit_rows"] += identity_audit[
                    "r37_identity_audit_rows"
                ]
                for field in (
                    "r37_identity_slot_max_abs_error",
                    "r37_critic_identity_max_abs_error",
                ):
                    r37_eval_metrics[field] = max(
                        r37_eval_metrics[field], identity_audit[field]
                    )
                agent.maybe_assign_skills(
                    obs,
                    state=state,
                    step=episode_length,
                    k=int(args.skill_interval),
                    env_id=0,
                    deterministic=deterministic_eval,
                    collect_r31=False,
                )
                actions, _, _ = agent.act_low(obs, env_id=0, deterministic=deterministic_eval, state=state)
                obs, reward, terminated, truncated, last_info = env.step(actions)
                state = last_info.get("next_state", state)
                joint_cell = alice_bob_joint_cell(state) if is_alice_bob else None
                if joint_cell is not None:
                    joint_position_cells.add(joint_cell)
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
                agent.record_environment_step(
                    0,
                    reward=float(reward),
                    next_obs=obs,
                    next_state=state,
                    done=bool(done or hit_step_cap),
                    collect_r31=False,
                )
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
            if is_alice_bob:
                episode_metrics["alice_bob_joint_position_coverage_ratio"] = float(
                    len(joint_position_cells) / 625.0
                )
                episode_metrics["alice_bob_zero_cycle_episode_flag"] = float(
                    episode_metrics.get("alice_bob_targets_completed", 0.0) <= 0.0
                )
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
                "reset_seed": reset_seed,
                "action_mode_code": 0.0 if deterministic_eval else 1.0,
                "reward": episode_reward,
                "length": episode_length,
                "terminated_flag": float(bool(terminated)),
                "truncated_flag": float(bool(truncated)),
                **r37_eval_metrics,
                **episode_metrics,
            }
            eval_records.append(eval_record)
            if getattr(args, "log_dir", None):
                append_csv(
                    Path(args.log_dir) / "metrics" / "eval_episodes.csv",
                    eval_record,
                    EVAL_FIELDS,
                )
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
        agent.active_duration_indices = active_duration_indices_backup
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
        agent.episode_steps = episode_steps_backup
        agent.episode_ids = episode_ids_backup
        agent.steps_to_check = steps_to_check_backup
        agent.high_check_buffer = high_check_buffer_backup
        agent._last_low_context = last_low_context_backup

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
    if eval_records and getattr(args, "log_dir", None):
        save_eval_plots(
            args.log_dir,
            window=max(1, int(getattr(args, "eval_episodes", 1))),
        )

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


def enforce_variable_roster_event_resume_boundary(config, args: argparse.Namespace) -> None:
    if not is_variable_roster_event(config):
        return
    path = str(getattr(args, "resume_from", "") or "")
    if path and not Path(path).is_file():
        raise ValueError(
            "Stage C --resume_from fails closed because the checkpoint does not "
            f"exist: {path}"
        )


def _write_event_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(jsonable(dict(payload)), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(path)


def _write_event_arm_status(args: argparse.Namespace, **fields: Any) -> None:
    _write_event_json(
        Path(args.log_dir) / "arm_status.json",
        {
            **fields,
            "updated": datetime.now().astimezone().isoformat(timespec="seconds"),
        },
    )


def _write_event_csv_rows(
    path: Path,
    *,
    fieldnames: Sequence[str],
    rows: Sequence[Mapping[str, Any]],
) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows([dict(row) for row in rows])
    temporary.replace(path)


def _event_live_checkpoint_paths(
    checkpoint_dir: Path,
    *,
    update_idx: int,
    save_interval: int,
) -> tuple[Path, ...]:
    index = int(update_idx)
    interval = max(int(save_interval), 1)
    paths = [checkpoint_dir / "latest.pt"]
    if index == 0 or index % interval == 0 or index == 250:
        paths.append(checkpoint_dir / f"update_{index:03d}_live.pt")
    return tuple(paths)


def _event_identity_normalizers() -> dict[str, Any]:
    state = {"schema_version": 1, "enabled": False, "kind": "identity"}
    return {"high": deepcopy(state), "low": deepcopy(state)}


def _nested_state_maximum_difference(left: Any, right: Any) -> float:
    if isinstance(left, (torch.Tensor, np.ndarray)) or isinstance(
        right, (torch.Tensor, np.ndarray)
    ):
        lhs = torch.as_tensor(left).detach().cpu()
        rhs = torch.as_tensor(right).detach().cpu()
        if lhs.shape != rhs.shape:
            return float("inf")
        if lhs.numel() == 0:
            return 0.0
        return float(torch.max(torch.abs(lhs.float() - rhs.float())).item())
    if is_dataclass(left) or is_dataclass(right):
        if not (is_dataclass(left) and is_dataclass(right)) or type(left) is not type(
            right
        ):
            return float("inf")
        return _nested_state_maximum_difference(
            {field.name: getattr(left, field.name) for field in fields(left)},
            {field.name: getattr(right, field.name) for field in fields(right)},
        )
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        if set(left) != set(right):
            return float("inf")
        return max(
            (_nested_state_maximum_difference(left[key], right[key]) for key in left),
            default=0.0,
        )
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        if len(left) != len(right):
            return float("inf")
        return max(
            (_nested_state_maximum_difference(a, b) for a, b in zip(left, right)),
            default=0.0,
        )
    return 0.0 if left == right else float("inf")


def _event_state_dict_finite(core) -> bool:
    return all(
        bool(torch.isfinite(tensor).all().item())
        for module in (
            core.commitment_model,
            core.event_critic,
            core.low_actor,
            core.low_critic,
        )
        for tensor in module.state_dict().values()
    )


def _make_event_model_owner(config, device: torch.device):
    from ha_ctse_process.dynamic_roster_testbed import ACTION_COUNT, OBSERVATION_DIM
    from ha_ctse_process.variable_roster_event import VariableRosterEventCore

    return VariableRosterEventCore(
        architecture_mode=str(config.event_architecture_mode),
        obs_dim=OBSERVATION_DIM,
        critic_member_dim=OBSERVATION_DIM,
        critic_global_dim=8,
        n_skills=3,
        action_dim=ACTION_COUNT,
        member_hidden_dim=int(getattr(config, "event_member_hidden_dim", 64)),
        high_hidden_dim=int(getattr(config, "event_high_hidden_dim", 64)),
        low_hidden_dim=int(getattr(config, "event_low_hidden_dim", 64)),
        skill_embedding_dim=int(getattr(config, "event_skill_embedding_dim", 16)),
        gamma=0.99,
        gae_lambda=0.95,
        environment_index=-1,
        device=device,
    )


def _make_event_runtime(
    model_owner,
    *,
    environment_index: int,
    episode_id: int,
    event_master_seed: int,
    action_master_seed: int,
):
    from ha_ctse_process.variable_roster_event import VariableRosterEventCore

    return VariableRosterEventCore(
        architecture_mode=model_owner.architecture_mode,
        obs_dim=model_owner.obs_dim,
        critic_member_dim=model_owner.critic_member_dim,
        critic_global_dim=model_owner.critic_global_dim,
        n_skills=model_owner.n_skills,
        action_dim=model_owner.action_dim,
        member_hidden_dim=model_owner.member_hidden_dim,
        high_hidden_dim=model_owner.high_hidden_dim,
        low_hidden_dim=model_owner.low_hidden_dim,
        skill_embedding_dim=model_owner.skill_embedding_dim,
        gamma=model_owner.gamma,
        gae_lambda=model_owner.gae_lambda,
        environment_index=int(environment_index),
        opportunity_seed=int(event_master_seed),
        frontier_seed=int(event_master_seed),
        action_seed=int(action_master_seed),
        rng_episode_id=int(episode_id),
        opportunity_stream_id=0,
        frontier_stream_id=1,
        action_stream_id=0,
        device=model_owner.device,
        shared_models_from=model_owner,
    )


def _paired_mean_ci(
    values: Sequence[float],
    *,
    seed: int,
    repetitions: int = 10_000,
) -> list[float]:
    array = np.asarray(values, dtype=np.float64).reshape(-1)
    if array.size <= 0 or not np.isfinite(array).all():
        raise ValueError("bootstrap values must be finite and non-empty")
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([int(seed)])))
    draws = np.empty(int(repetitions), dtype=np.float64)
    for index in range(int(repetitions)):
        draws[index] = float(np.mean(array[rng.integers(0, array.size, array.size)]))
    return [
        float(np.quantile(draws, 0.025)),
        float(np.mean(array)),
        float(np.quantile(draws, 0.975)),
    ]


def _event_prefix_rows(core, rows, *, episode_id: int) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        if (
            int(row.physical_event_time) <= 0
            or len(row.frontier) < 2
            or int(row.token_position) <= 0
        ):
            continue
        initial = core.replay_token_distribution(row, summary_source="initial")
        working = core.replay_token_distribution(row, summary_source="working")
        actual_source = "initial" if core.architecture_mode == "f0" else "working"
        replayed_actual = core.replay_token_distribution(
            row, summary_source=actual_source
        )
        action = int(row.combined_action)
        replayed_action_probability = float(replayed_actual[action])
        replayed_action_log_probability = float(
            np.log(max(replayed_action_probability, np.finfo(np.float64).tiny))
        )
        stored_action_log_probability = float(row.old_token_log_probability)
        stored_action_probability = float(np.exp(stored_action_log_probability))
        owner_index = row.active_lifecycle_keys.index(row.owner_lifecycle_key)
        output.append(
            {
                "episode_id": int(episode_id),
                "physical_time": int(row.physical_event_time),
                "token_position": int(row.token_position),
                "owner_index": int(owner_index),
                "owner_incumbent_skill": int(
                    row.pre_token_working_skills[owner_index]
                ),
                "combined_action": action,
                "initial_skills": row.initial_skills.tolist(),
                "working_skills": row.pre_token_working_skills.tolist(),
                "legal_mask": row.exact_legal_mask.tolist(),
                "p_initial": initial.tolist(),
                "p_working": working.tolist(),
                "p_actual_replay": replayed_actual.tolist(),
                "stored_action_log_probability": stored_action_log_probability,
                "replayed_action_log_probability": replayed_action_log_probability,
                "stored_action_probability": stored_action_probability,
                "replayed_action_probability": replayed_action_probability,
                "actual_replay_logp_error": float(
                    abs(replayed_action_log_probability - stored_action_log_probability)
                ),
                "actual_replay_probability_error": float(
                    abs(replayed_action_probability - stored_action_probability)
                ),
                "working_initial_tv": float(0.5 * np.abs(working - initial).sum()),
                "common_support_applied_vs_initial_tv": float(
                    0.5 * np.abs(replayed_actual - initial).sum()
                ),
            }
        )
    return output


def _summarize_event_prefix_rows(
    prefix_rows: Sequence[Mapping[str, Any]],
    *,
    persistent_skill: int,
    architecture_mode: str,
) -> dict[str, Any]:
    replay_logp_max = max(
        (float(row["actual_replay_logp_error"]) for row in prefix_rows),
        default=0.0,
    )
    replay_probability_max = max(
        (float(row["actual_replay_probability_error"]) for row in prefix_rows),
        default=0.0,
    )
    tv_by_episode: dict[int, list[float]] = {}
    direction_by_episode: dict[int, list[float]] = {}
    direction_cases = {
        "no_persistent_in_roster": 0,
        "other_persistent_in_roster": 0,
        "excluded_focal_persistent": 0,
    }
    for row in prefix_rows:
        episode_id = int(row["episode_id"])
        tv_by_episode.setdefault(episode_id, []).append(
            float(row["common_support_applied_vs_initial_tv"])
        )
        working_skills = [int(value) for value in row["working_skills"]]
        owner_index = int(row["owner_index"])
        incumbent = int(row["owner_incumbent_skill"])
        if incumbent == int(persistent_skill):
            direction_cases["excluded_focal_persistent"] += 1
            continue
        p_initial = np.asarray(row["p_initial"], dtype=np.float64)
        p_working = np.asarray(row["p_working"], dtype=np.float64)
        other_skills = [
            skill for index, skill in enumerate(working_skills) if index != owner_index
        ]
        if int(persistent_skill) not in working_skills:
            direction = float(
                p_working[int(persistent_skill)] - p_initial[int(persistent_skill)]
            )
            direction_cases["no_persistent_in_roster"] += 1
        elif int(persistent_skill) in other_skills:
            direction = float(
                p_initial[int(persistent_skill)] - p_working[int(persistent_skill)]
            )
            direction_cases["other_persistent_in_roster"] += 1
        else:
            continue
        direction_by_episode.setdefault(episode_id, []).append(direction)
    tv_episode_means = [
        float(np.mean(tv_by_episode[key])) for key in sorted(tv_by_episode)
    ]
    direction_episode_means = [
        float(np.mean(direction_by_episode[key]))
        for key in sorted(direction_by_episode)
    ]
    return {
        "eligible_natural_rows": len(prefix_rows),
        "actual_replay_logp_max_error": replay_logp_max,
        "actual_replay_probability_max_error": replay_probability_max,
        "directional_eligible_rows": sum(
            len(values) for values in direction_by_episode.values()
        ),
        "directional_case_counts": direction_cases,
        "working_initial_tv_ci95": (
            _paired_mean_ci(tv_episode_means, seed=107_057)
            if tv_episode_means
            else [0.0, 0.0, 0.0]
        ),
        "directional_composition_shift_ci95": (
            _paired_mean_ci(direction_episode_means, seed=107_058)
            if direction_episode_means
            else [0.0, 0.0, 0.0]
        ),
        "f0_common_support_tv_max": (
            max(
                (
                    float(row["common_support_applied_vs_initial_tv"])
                    for row in prefix_rows
                ),
                default=0.0,
            )
            if str(architecture_mode) == "f0"
            else None
        ),
        "rows": list(prefix_rows),
    }


@torch.no_grad()
def _forced_event_snapshot_effects(
    *,
    model_owner,
    core,
    environment,
    snapshot,
    episode_id: int,
    audit_index: int,
) -> list[list[list[float]]]:
    from ha_ctse_process.collectors import SyncEnvCollector
    from ha_ctse_process.dynamic_roster_testbed import (
        DynamicRosterEventEnv,
        PERSIST,
        SHORT,
    )
    from ha_ctse_process.variable_roster_event import make_pcg64_rng

    if int(core.physical_time) <= 0 or int(core.physical_time) > 68:
        raise ValueError("forced audit snapshot must allow exactly 12 future steps")
    source_collector = SyncEnvCollector([environment])
    collector_snapshot = source_collector.snapshot_event_runtime()
    checkpoint = core.checkpoint_payload(
        collector_snapshot=collector_snapshot,
        current_observation_state_boundary={
            "physical_time": int(core.physical_time),
            "episode_id": int(episode_id),
            "fresh_eval": True,
        },
        optimizer_states={"high": {}, "low": {}},
        normalizer_states=_event_identity_normalizers(),
        pending_membership_transaction=core.pending_membership_transaction,
    )
    focal_key = snapshot.keys[int(audit_index) % len(snapshot.keys)]
    skill_results: list[list[list[float]]] = []
    for skill in range(model_owner.n_skills):
        replica_results: list[list[float]] = []
        for replica in range(2):
            branch_environment = DynamicRosterEventEnv(task_master_seed=97_057)
            branch_collector = SyncEnvCollector([branch_environment])
            branch_core = _make_event_runtime(
                model_owner,
                environment_index=0,
                episode_id=episode_id,
                event_master_seed=77_057,
                action_master_seed=87_057,
            )
            branch_core.restore_checkpoint_payload(checkpoint, collector=branch_collector)
            branch_core.action_rng = make_pcg64_rng(
                87_057, int(audit_index), 100 + int(replica)
            )
            branch_snapshot = deepcopy(snapshot)
            if branch_environment.environment is None:
                raise RuntimeError("forced audit environment restore failed")
            start_persistent = int(branch_environment.environment.persistent_units)
            start_short = int(branch_environment.environment.short_completed_total)
            wave = branch_environment.environment.current_wave
            short_denominator = 1 if wave is None else max(int(wave.required_work), 1)
            persist_actions = 0
            short_actions = 0
            for _step in range(12):
                if focal_key not in branch_core.records or (
                    branch_core.records[focal_key].status != "ACTIVE"
                ):
                    raise RuntimeError("forced focal lifecycle left before audit window closed")
                branch_core.records[focal_key].active_skill = int(skill)
                actions, _logp, _values = branch_core.low_step(
                    branch_snapshot, deterministic=False
                )
                routed = {
                    key: int(actions[index].detach().cpu())
                    for index, key in enumerate(branch_snapshot.keys)
                }
                focal_action = int(routed[focal_key])
                persist_actions += int(focal_action == PERSIST)
                short_actions += int(focal_action == SHORT)
                event_step = branch_environment.step_event_runtime(routed)
                branch_core.complete_primitive_transition(float(event_step.reward))
                if event_step.terminated or event_step.next_transaction is None:
                    raise RuntimeError("forced audit branch ended before 12 steps")
                bound = branch_core.bind_due_frontier(event_step.next_transaction)
                branch_core.apply_transaction(bound, deterministic_policy=False)
                branch_snapshot = bound.post_membership_pre_policy_snapshot
            assert branch_environment.environment is not None
            replica_results.append(
                [
                    float(persist_actions) / 12.0,
                    float(short_actions) / 12.0,
                    float(
                        branch_environment.environment.persistent_units
                        - start_persistent
                    )
                    / 12.0,
                    float(
                        branch_environment.environment.short_completed_total
                        - start_short
                    )
                    / float(short_denominator),
                ]
            )
        skill_results.append(replica_results)
    return skill_results


def _summarize_forced_audit(
    effects: Sequence[Any],
    *,
    natural_skill_counts: Sequence[int],
) -> dict[str, Any]:
    values = np.asarray(effects, dtype=np.float64)
    if values.shape != (128, 3, 2, 4):
        raise ValueError(f"forced audit effect shape mismatch: {values.shape}")
    skill_means = values.mean(axis=(0, 2))
    persistent_order = np.argsort(skill_means[:, 0])
    reactive_order = np.argsort(skill_means[:, 1])
    persistent_skill = int(persistent_order[-1])
    reactive_skill = int(reactive_order[-1])
    persistent_margin = float(
        skill_means[persistent_order[-1], 0]
        - skill_means[persistent_order[-2], 0]
    )
    reactive_margin = float(
        skill_means[reactive_order[-1], 1]
        - skill_means[reactive_order[-2], 1]
    )

    def rho_for(sample: np.ndarray) -> float:
        means = sample.mean(axis=2)
        between = []
        for left in range(3):
            for right in range(left + 1, 3):
                between.extend(np.linalg.norm(means[:, left] - means[:, right], axis=-1))
        within = np.linalg.norm(sample[:, :, 0] - sample[:, :, 1], axis=-1).reshape(-1)
        return float(np.median(between) / (np.median(within) + 1e-8))

    rho = rho_for(values)
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([107_057, 1])))
    bootstrap = np.empty(10_000, dtype=np.float64)
    for index in range(10_000):
        selected = rng.integers(0, values.shape[0], values.shape[0])
        bootstrap[index] = rho_for(values[selected])
    counts = np.asarray(natural_skill_counts, dtype=np.float64)
    shares = counts / max(float(counts.sum()), 1.0)
    executable = bool(
        float(np.quantile(bootstrap, 0.025)) > 1.0
        and persistent_skill != reactive_skill
        and persistent_margin > 0.15
        and reactive_margin > 0.15
        and bool(np.all(shares >= 0.10))
    )
    return {
        "snapshot_count": 128,
        "skills_per_snapshot": 3,
        "replicas_per_skill": 2,
        "steps_per_replica": 12,
        "forced_environment_steps": 128 * 3 * 2 * 12,
        "effect_shape": list(values.shape),
        "rho": rho,
        "rho_ci95": [
            float(np.quantile(bootstrap, 0.025)),
            rho,
            float(np.quantile(bootstrap, 0.975)),
        ],
        "skill_signature_means": skill_means.tolist(),
        "persistent_like_skill": persistent_skill,
        "reactive_like_skill": reactive_skill,
        "persistent_occupancy_margin": persistent_margin,
        "reactive_occupancy_margin": reactive_margin,
        "natural_skill_step_counts": counts.astype(np.int64).tolist(),
        "natural_skill_step_shares": shares.tolist(),
        "executable_naturally_used_skills": executable,
        "effects": values.tolist(),
    }


@torch.no_grad()
def _evaluate_event_model(
    model_owner,
    *,
    deterministic: bool,
    capture_prefix: bool,
    capture_forced_audit: bool,
) -> dict[str, Any]:
    from ha_ctse_process.dynamic_roster_testbed import DynamicRosterEventEnv, HORIZON

    modules = (
        model_owner.commitment_model,
        model_owner.event_critic,
        model_owner.low_actor,
        model_owner.low_critic,
    )
    previous_training = [module.training for module in modules]
    for module in modules:
        module.eval()
    episode_ids = tuple(range(256))
    persistent: list[float] = []
    short: list[float] = []
    utility: list[float] = []
    prefix_rows: list[dict[str, Any]] = []
    timing_rows: list[dict[str, Any]] = []
    natural_skill_counts = np.zeros(model_owner.n_skills, dtype=np.int64)
    forced_effects: list[Any] = []
    try:
        for episode_id in episode_ids:
            environment = DynamicRosterEventEnv(task_master_seed=97_057)
            core = _make_event_runtime(
                model_owner,
                environment_index=0,
                episode_id=episode_id,
                event_master_seed=77_057,
                action_master_seed=87_057,
            )
            transaction = environment.reset_event_runtime(episode_id)
            bound = core.bind_due_frontier(transaction)
            result = core.apply_transaction(
                bound, deterministic_policy=bool(deterministic)
            )
            snapshot = bound.post_membership_pre_policy_snapshot
            if capture_prefix:
                prefix_rows.extend(
                    _event_prefix_rows(core, result.token_rows, episode_id=episode_id)
                )
            selected_times = set()
            if capture_forced_audit and episode_id < 32:
                selected_times = {
                    1 + episode_id % 8,
                    20 + episode_id % 9,
                    40 + episode_id % 9,
                    60 + episode_id % 8,
                }
            for primitive_time in range(HORIZON):
                if primitive_time in selected_times:
                    forced_effects.append(
                        _forced_event_snapshot_effects(
                            model_owner=model_owner,
                            core=core,
                            environment=environment,
                            snapshot=snapshot,
                            episode_id=episode_id,
                            audit_index=len(forced_effects),
                        )
                    )
                skills_now = core.active_skills()
                for skill in skills_now.values():
                    natural_skill_counts[int(skill)] += 1
                environment_state = environment.environment
                if environment_state is None:
                    raise RuntimeError("evaluation environment is missing state")
                current_wave = environment_state.current_wave
                opportunity_keys = sorted(
                    {row.owner_lifecycle_key for row in result.token_rows}
                )
                short_completed_before = int(environment_state.short_completed_total)
                timing_row = {
                    "episode_id": episode_id,
                    "physical_time": primitive_time,
                    "active_keys": list(snapshot.keys),
                    "active_skills": [int(skills_now[key]) for key in snapshot.keys],
                    "opportunity_keys_at_time": opportunity_keys,
                    "wave_index": (
                        None if current_wave is None else int(current_wave.index)
                    ),
                    "wave_arrival_time": (
                        None
                        if current_wave is None
                        else int(current_wave.arrival_time)
                    ),
                    "wave_required": (
                        0 if current_wave is None else int(current_wave.required_work)
                    ),
                    "wave_completed_before_action": (
                        0 if current_wave is None else int(current_wave.completed_work)
                    ),
                    "persistent_owner_exists": bool(
                        environment_state.persistent_owner is not None
                    ),
                }
                actions, _logp, _values = core.low_step(
                    snapshot, deterministic=bool(deterministic)
                )
                routed = {
                    key: int(actions[index].detach().cpu())
                    for index, key in enumerate(snapshot.keys)
                }
                step = environment.step_event_runtime(routed)
                completed_this_action = max(
                    int(step.info["short_completed_total"]) - short_completed_before,
                    0,
                )
                timing_row["wave_completed_after_action"] = (
                    0
                    if current_wave is None
                    else min(
                        int(current_wave.required_work),
                        int(timing_row["wave_completed_before_action"])
                        + completed_this_action,
                    )
                )
                timing_row["persistent_owner_exists_after_action"] = bool(
                    environment.environment is not None
                    and environment.environment.persistent_owner is not None
                )
                timing_rows.append(timing_row)
                core.complete_primitive_transition(float(step.reward))
                if step.terminated:
                    core.close_terminal()
                    persistent.append(float(step.info["persistent_score"]))
                    short.append(float(step.info["short_score"]))
                    utility.append(float(step.info["utility"]))
                    break
                if step.next_transaction is None:
                    raise RuntimeError("evaluation nonterminal step lacks transaction")
                bound = core.bind_due_frontier(step.next_transaction)
                result = core.apply_transaction(
                    bound, deterministic_policy=bool(deterministic)
                )
                snapshot = bound.post_membership_pre_policy_snapshot
                if capture_prefix:
                    prefix_rows.extend(
                        _event_prefix_rows(
                            core, result.token_rows, episode_id=episode_id
                        )
                    )
        if len(persistent) != 256 or len(short) != 256 or len(utility) != 256:
            raise RuntimeError("Stage C evaluation episode count is not exact")
        payload: dict[str, Any] = {
            "episode_ids": list(episode_ids),
            "deterministic": bool(deterministic),
            "persistent": persistent,
            "short": short,
            "utility": utility,
            "persistent_mean": float(np.mean(persistent)),
            "short_mean": float(np.mean(short)),
            "utility_mean": float(np.mean(utility)),
            "environment_steps": 256 * HORIZON,
            "natural_skill_step_counts": natural_skill_counts.tolist(),
            "prefix_rows": prefix_rows,
            "timing_rows": timing_rows if capture_prefix else [],
        }
        if capture_forced_audit:
            payload["forced_audit"] = _summarize_forced_audit(
                forced_effects,
                natural_skill_counts=natural_skill_counts,
            )
        return payload
    finally:
        for module, was_training in zip(modules, previous_training):
            module.train(was_training)


def _run_variable_roster_event_branch(config, args: argparse.Namespace, writer):
    """Run one exact Stage-C arm, including fresh zero/final evidence."""

    from ha_ctse_process.collectors import SyncEnvCollector
    from ha_ctse_process.dynamic_roster_testbed import (
        DynamicRosterEventEnv,
        HORIZON,
        TRAIN_LEDGER_SEED,
    )
    from ha_ctse_process.variable_roster_event import (
        EVENT_ARCHITECTURE_SCHEMA_VERSION,
        apply_event_ppo_update,
        batched_low_step,
        event_model_only_checkpoint_payload,
        pack_event_ppo_data,
        restore_event_model_only_checkpoint,
        restore_vector_event_checkpoint,
        vector_event_checkpoint_payload,
    )

    enforce_variable_roster_event_resume_boundary(config, args)
    if normalize_scenario(str(getattr(config, "scenario", ""))) != (
        "generic_short_dynamic_roster"
    ):
        raise ValueError("variable_roster_event is restricted to generic-SHORT Stage C")
    num_envs = int(args.num_envs)
    if (num_envs, int(args.rollout_length), int(args.total_timesteps)) != (
        16,
        HORIZON,
        320_000,
    ):
        raise ValueError(
            "Stage C requires num_envs=16, rollout_length=80, total_timesteps=320000"
        )
    if int(getattr(config, "event_architecture_schema_version", -1)) != (
        EVENT_ARCHITECTURE_SCHEMA_VERSION
    ):
        raise ValueError("Stage C requires event architecture schema version 1")
    if str(getattr(args, "device", "cuda")).lower() != "cuda" or not torch.cuda.is_available():
        raise RuntimeError("Stage C training requires available CUDA; CPU fallback is forbidden")
    device = torch.device("cuda")
    config.dynamic_roster_task_ledger_seed = TRAIN_LEDGER_SEED
    output_root = Path(args.log_dir)
    checkpoint_dir = output_root / "checkpoints"
    evaluation_dir = output_root / "evaluation"
    result_dir = output_root / "result"
    for directory in (checkpoint_dir, evaluation_dir, result_dir):
        directory.mkdir(parents=True, exist_ok=True)

    with torch.random.fork_rng(devices=[torch.cuda.current_device()]):
        torch.manual_seed(57_057)
        torch.cuda.manual_seed_all(57_057)
        model_owner = _make_event_model_owner(config, device)
    high_optimizer = torch.optim.Adam(
        tuple(model_owner.commitment_model.parameters())
        + tuple(model_owner.event_critic.parameters()),
        lr=3e-4,
    )
    low_optimizer = torch.optim.Adam(
        tuple(model_owner.low_actor.parameters())
        + tuple(model_owner.low_critic.parameters()),
        lr=3e-4,
    )
    normalizer_states = _event_identity_normalizers()

    def model_state(core) -> dict[str, Any]:
        return {
            "commitment_model": deepcopy(core.commitment_model.state_dict()),
            "event_critic": deepcopy(core.event_critic.state_dict()),
            "low_actor": deepcopy(core.low_actor.state_dict()),
            "low_critic": deepcopy(core.low_critic.state_dict()),
        }

    zero_checkpoint_path = checkpoint_dir / "update_000_eval.pt"
    zero_evaluation_path = evaluation_dir / "update_000.json"
    if not str(getattr(args, "resume_from", "") or ""):
        torch.save(
            event_model_only_checkpoint_payload(
                model_owner=model_owner,
                normalizer_states=normalizer_states,
                total_steps=0,
                update_idx=0,
            ),
            zero_checkpoint_path,
        )
        zero_owner = _make_event_model_owner(config, device)
        restore_event_model_only_checkpoint(
            torch.load(zero_checkpoint_path, map_location=device, weights_only=False),
            model_owner=zero_owner,
        )
        initial_state = model_state(zero_owner)
        _write_event_arm_status(
            args,
            state="running",
            phase="zero_evaluation",
            mode=config.event_architecture_mode,
            update=0,
            updates_total=250,
            steps=0,
            steps_total=320_000,
            high_optimizer_steps=0,
            low_optimizer_steps=0,
            optimizer_steps_total=1_000,
        )
        zero_evaluation = {
            "deterministic": _evaluate_event_model(
                zero_owner,
                deterministic=True,
                capture_prefix=False,
                capture_forced_audit=False,
            ),
            "stochastic": _evaluate_event_model(
                zero_owner,
                deterministic=False,
                capture_prefix=False,
                capture_forced_audit=False,
            ),
        }
        _write_event_json(zero_evaluation_path, zero_evaluation)
    else:
        if not zero_checkpoint_path.is_file() or not zero_evaluation_path.is_file():
            raise FileNotFoundError(
                "Stage C resume requires the original zero checkpoint and evaluation"
            )
        zero_payload = torch.load(
            zero_checkpoint_path, map_location=device, weights_only=False
        )
        zero_owner = _make_event_model_owner(config, device)
        restore_event_model_only_checkpoint(zero_payload, model_owner=zero_owner)
        initial_state = model_state(zero_owner)
        zero_evaluation = json.loads(zero_evaluation_path.read_text(encoding="utf-8"))

    collector = create_collector(config, args, scale_mode="train", num_envs=num_envs)
    collector.event_runtime_capability()
    total_steps = 0
    update_idx = 0
    high_optimizer_steps = 0
    low_optimizer_steps = 0
    intrinsic_applied_count = 0
    next_episode_id = 0
    resumed_from = None
    maximum_replay_errors = {
        "high_logp_max_error": 0.0,
        "high_value_max_error": 0.0,
        "low_logp_max_error": 0.0,
        "low_value_max_error": 0.0,
    }
    finite_updates = True
    last_metrics: dict[str, float] = {}
    update_path = output_root / "train_updates.csv"
    latest_checkpoint_path = checkpoint_dir / "latest.pt"
    update_fields = [
        "update",
        "steps",
        "high_optimizer_steps",
        "low_optimizer_steps",
        *maximum_replay_errors,
        "high_loss",
        "low_loss",
        "finite_update",
    ]

    def prepare_episode_batch(episode_ids: Sequence[int]):
        transactions = collector.reset_event_runtime(episode_ids)
        prepared_cores = []
        prepared_snapshots = []
        for env_index, (episode_id, transaction) in enumerate(
            zip(episode_ids, transactions)
        ):
            core = _make_event_runtime(
                model_owner,
                environment_index=env_index,
                episode_id=int(episode_id),
                event_master_seed=77_057,
                action_master_seed=87_057,
            )
            bound = core.bind_due_frontier(transaction)
            core.apply_transaction(bound, deterministic_policy=False)
            prepared_cores.append(core)
            prepared_snapshots.append(bound.post_membership_pre_policy_snapshot)
        return prepared_cores, prepared_snapshots

    def save_live_checkpoint(path: Path, payload: Mapping[str, Any]) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        torch.save(dict(payload), temporary)
        temporary.replace(path)

    pending_cores = None
    pending_snapshots = None
    if str(getattr(args, "resume_from", "") or ""):
        resume_path = Path(args.resume_from).resolve()
        if resume_path.parent != checkpoint_dir.resolve():
            raise ValueError("Stage C resume checkpoint must belong to this arm root")
        resume_payload = torch.load(resume_path, map_location=device, weights_only=False)
        runtime_payloads = list(
            resume_payload["event_architecture"]["runtime_payloads"]
        )
        restore_cores = []
        for env_index, runtime_payload in enumerate(runtime_payloads):
            rng = runtime_payload["rng_ledger"]
            restore_cores.append(
                _make_event_runtime(
                    model_owner,
                    environment_index=env_index,
                    episode_id=int(rng["episode_id"]),
                    event_master_seed=int(rng["opportunity"]["master_seed"]),
                    action_master_seed=int(rng["policy_action"]["master_seed"]),
                )
            )
        optimizer_states, restored_normalizers, counters = (
            restore_vector_event_checkpoint(
                resume_payload,
                model_owner=model_owner,
                cores=restore_cores,
                collector=collector,
            )
        )
        high_optimizer.load_state_dict(optimizer_states["high"])
        low_optimizer.load_state_dict(optimizer_states["low"])
        normalizer_states = restored_normalizers
        total_steps = int(counters["total_steps"])
        update_idx = int(counters["update_idx"])
        high_optimizer_steps = int(counters["high_optimizer_steps"])
        low_optimizer_steps = int(counters["low_optimizer_steps"])
        next_episode_id = int(counters["next_episode_id"])
        intrinsic_applied_count = int(counters["intrinsic_applied_count"])
        if not 0 <= update_idx < 250:
            raise ValueError("Stage C resume update lies outside the active run")
        expected_next_episode_id = num_envs if update_idx == 0 else update_idx * num_envs
        if (
            total_steps != update_idx * num_envs * HORIZON
            or high_optimizer_steps != update_idx * 4
            or low_optimizer_steps != update_idx * 4
            or next_episode_id != expected_next_episode_id
            or intrinsic_applied_count != 0
        ):
            raise ValueError("Stage C resume counter ledger mismatch")
        if not update_path.is_file():
            raise FileNotFoundError("Stage C resume requires train_updates.csv")
        with update_path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) < update_idx:
            raise ValueError("Stage C resume training ledger trails its checkpoint")
        if len(rows) > update_idx:
            rows = rows[:update_idx]
            _write_event_csv_rows(
                update_path, fieldnames=update_fields, rows=rows
            )
        for name in maximum_replay_errors:
            maximum_replay_errors[name] = max(
                (float(row[name]) for row in rows), default=0.0
            )
        finite_updates = all(bool(int(float(row["finite_update"]))) for row in rows)
        if update_idx == 0:
            pending_cores = restore_cores
            pending_snapshots = [
                runtime_payload["current_observation_state_boundary"]["snapshot"]
                for runtime_payload in runtime_payloads
            ]
        resumed_from = str(resume_path)
    else:
        if update_path.exists():
            raise FileExistsError("fresh Stage C arm root already has train_updates.csv")
        _write_event_csv_rows(update_path, fieldnames=update_fields, rows=[])
        initial_episode_ids = tuple(range(num_envs))
        pending_cores, pending_snapshots = prepare_episode_batch(initial_episode_ids)
        next_episode_id = num_envs
        initial_boundaries = [
            {
                "physical_time": int(core.physical_time),
                "episode_id": int(core.rng_episode_id),
                "terminal": False,
                "snapshot": snapshot,
            }
            for core, snapshot in zip(pending_cores, pending_snapshots)
        ]
        update_zero_checkpoint = vector_event_checkpoint_payload(
            model_owner=model_owner,
            cores=pending_cores,
            collector_snapshot=collector.snapshot_event_runtime(),
            current_boundaries=initial_boundaries,
            optimizer_states={
                "high": high_optimizer.state_dict(),
                "low": low_optimizer.state_dict(),
            },
            normalizer_states=normalizer_states,
            counters={
                "total_steps": 0,
                "update_idx": 0,
                "high_optimizer_steps": 0,
                "low_optimizer_steps": 0,
                "next_episode_id": next_episode_id,
                "intrinsic_applied_count": 0,
            },
        )
        for path in _event_live_checkpoint_paths(
            checkpoint_dir, update_idx=0, save_interval=int(args.save_interval)
        ):
            save_live_checkpoint(path, update_zero_checkpoint)

    start_time = time.perf_counter()
    final_cores = None
    final_boundaries = None
    try:
        with update_path.open("a", encoding="utf-8", newline="") as handle:
            csv_writer = csv.DictWriter(handle, fieldnames=update_fields)
            for update_idx in range(update_idx + 1, 251):
                if pending_cores is not None and pending_snapshots is not None:
                    cores = pending_cores
                    snapshots = pending_snapshots
                    pending_cores = None
                    pending_snapshots = None
                else:
                    episode_ids = tuple(
                        range(next_episode_id, next_episode_id + num_envs)
                    )
                    next_episode_id += num_envs
                    cores, snapshots = prepare_episode_batch(episode_ids)

                for primitive_time in range(HORIZON):
                    low_batch = batched_low_step(cores, snapshots)
                    steps = collector.step_event_runtime(low_batch.routed_actions)
                    next_snapshots = []
                    for core, step in zip(cores, steps):
                        if bool(step.truncated):
                            raise RuntimeError(
                                "generic-SHORT Stage C does not admit truncation"
                            )
                        intrinsic_applied_count += int(
                            step.info.get("intrinsic_reward_applied_count", -1)
                        )
                        if float(step.info.get("intrinsic_reward", float("nan"))) != 0.0:
                            raise RuntimeError(
                                "Stage C intrinsic reward must remain exactly zero"
                            )
                        core.complete_primitive_transition(float(step.reward))
                        if bool(step.terminated):
                            if primitive_time != HORIZON - 1 or step.next_transaction is not None:
                                raise RuntimeError(
                                    "generic-SHORT terminal boundary is inconsistent"
                                )
                            core.close_terminal()
                            next_snapshots.append(None)
                        else:
                            if step.next_transaction is None:
                                raise RuntimeError(
                                    "nonterminal event step is missing its next transaction"
                                )
                            bound = core.bind_due_frontier(step.next_transaction)
                            core.apply_transaction(bound, deterministic_policy=False)
                            next_snapshots.append(
                                bound.post_membership_pre_policy_snapshot
                            )
                    snapshots = next_snapshots
                    total_steps += num_envs
                if intrinsic_applied_count != 0:
                    raise RuntimeError("Stage C intrinsic-applied count must be zero")
                first_pass_replay = None
                packed_ppo = pack_event_ppo_data(cores)
                for ppo_pass in range(4):
                    metrics = apply_event_ppo_update(
                        packed_ppo,
                        high_optimizer=high_optimizer,
                        low_optimizer=low_optimizer,
                    )
                    if ppo_pass == 0:
                        first_pass_replay = {
                            name: float(metrics[name])
                            for name in maximum_replay_errors
                        }
                    high_optimizer_steps += 1
                    low_optimizer_steps += 1
                assert first_pass_replay is not None
                for name, value in first_pass_replay.items():
                    maximum_replay_errors[name] = max(
                        maximum_replay_errors[name], value
                    )
                last_metrics = {name: float(value) for name, value in metrics.items()}
                finite_update = bool(
                    all(np.isfinite(value) for value in last_metrics.values())
                    and _event_state_dict_finite(model_owner)
                )
                finite_updates = finite_updates and finite_update
                update_row = {
                    "update": update_idx,
                    "steps": total_steps,
                    "high_optimizer_steps": high_optimizer_steps,
                    "low_optimizer_steps": low_optimizer_steps,
                    **maximum_replay_errors,
                    "high_loss": last_metrics["high_loss"],
                    "low_loss": last_metrics["low_loss"],
                    "finite_update": int(finite_update),
                }
                csv_writer.writerow(update_row)
                handle.flush()
                final_cores = cores
                final_boundaries = [
                    {
                        "physical_time": int(core.physical_time),
                        "episode_id": int(core.rng_episode_id),
                        "terminal": True,
                    }
                    for core in cores
                ]
                checkpoint = vector_event_checkpoint_payload(
                    model_owner=model_owner,
                    cores=cores,
                    collector_snapshot=collector.snapshot_event_runtime(),
                    current_boundaries=final_boundaries,
                    optimizer_states={
                        "high": high_optimizer.state_dict(),
                        "low": low_optimizer.state_dict(),
                    },
                    normalizer_states=normalizer_states,
                    counters={
                        "total_steps": total_steps,
                        "update_idx": update_idx,
                        "high_optimizer_steps": high_optimizer_steps,
                        "low_optimizer_steps": low_optimizer_steps,
                        "next_episode_id": next_episode_id,
                        "intrinsic_applied_count": intrinsic_applied_count,
                    },
                )
                for path in _event_live_checkpoint_paths(
                    checkpoint_dir,
                    update_idx=update_idx,
                    save_interval=int(args.save_interval),
                ):
                    save_live_checkpoint(path, checkpoint)
                _write_event_arm_status(
                    args,
                    state="running",
                    phase="training",
                    mode=config.event_architecture_mode,
                    update=update_idx,
                    updates_total=250,
                    steps=total_steps,
                    steps_total=320_000,
                    high_optimizer_steps=high_optimizer_steps,
                    low_optimizer_steps=low_optimizer_steps,
                    optimizer_steps_total=1_000,
                    checkpoint_path=str(latest_checkpoint_path),
                )
                if writer is not None:
                    for name, value in last_metrics.items():
                        writer.add_scalar(f"Event/{name}", value, total_steps)
                    writer.flush()
                emit(
                    args,
                    "event_update "
                    f"mode={config.event_architecture_mode} update={update_idx}/250 "
                    f"steps={total_steps} high_optimizer_steps={high_optimizer_steps} "
                    f"low_optimizer_steps={low_optimizer_steps}",
                )

        if final_cores is None or final_boundaries is None:
            raise RuntimeError("Stage C produced no final vector boundary")
        if (
            total_steps != 320_000
            or high_optimizer_steps != 1_000
            or low_optimizer_steps != 1_000
            or next_episode_id != 4_000
            or intrinsic_applied_count != 0
        ):
            raise RuntimeError("Stage C exposure ledger is not exact")

        final_eval_checkpoint = checkpoint_dir / "update_250_eval.pt"
        torch.save(
            event_model_only_checkpoint_payload(
                model_owner=model_owner,
                normalizer_states=normalizer_states,
                total_steps=total_steps,
                update_idx=update_idx,
            ),
            final_eval_checkpoint,
        )
        final_owner = _make_event_model_owner(config, device)
        restore_event_model_only_checkpoint(
            torch.load(final_eval_checkpoint, map_location=device, weights_only=False),
            model_owner=final_owner,
        )
        _write_event_arm_status(
            args,
            state="running",
            phase="final_evaluation",
            mode=config.event_architecture_mode,
            update=250,
            updates_total=250,
            steps=320_000,
            steps_total=320_000,
            high_optimizer_steps=1_000,
            low_optimizer_steps=1_000,
            optimizer_steps_total=1_000,
        )
        final_deterministic = _evaluate_event_model(
            final_owner,
            deterministic=True,
            capture_prefix=False,
            capture_forced_audit=False,
        )
        _write_event_arm_status(
            args,
            state="running",
            phase="forced_audit_and_stochastic_evaluation",
            mode=config.event_architecture_mode,
            update=250,
            updates_total=250,
            steps=320_000,
            steps_total=320_000,
            high_optimizer_steps=1_000,
            low_optimizer_steps=1_000,
            optimizer_steps_total=1_000,
        )
        final_stochastic = _evaluate_event_model(
            final_owner,
            deterministic=False,
            capture_prefix=True,
            capture_forced_audit=True,
        )

        live_payload = torch.load(
            latest_checkpoint_path, map_location=device, weights_only=False
        )
        verification_owner = _make_event_model_owner(config, device)
        verification_envs = [
            DynamicRosterEventEnv(task_master_seed=TRAIN_LEDGER_SEED)
            for _ in range(num_envs)
        ]
        verification_collector = SyncEnvCollector(verification_envs)
        runtime_payloads = live_payload["event_architecture"]["runtime_payloads"]
        verification_cores = []
        for env_index, runtime_payload in enumerate(runtime_payloads):
            rng = runtime_payload["rng_ledger"]
            verification_cores.append(
                _make_event_runtime(
                    verification_owner,
                    environment_index=env_index,
                    episode_id=int(rng["episode_id"]),
                    event_master_seed=int(rng["opportunity"]["master_seed"]),
                    action_master_seed=int(rng["policy_action"]["master_seed"]),
                )
            )
        restored_optimizers, restored_normalizers, restored_counters = (
            restore_vector_event_checkpoint(
                live_payload,
                model_owner=verification_owner,
                cores=verification_cores,
                collector=verification_collector,
            )
        )
        restored_collector_snapshot = verification_collector.snapshot_event_runtime()
        roundtrip_payload = vector_event_checkpoint_payload(
            model_owner=verification_owner,
            cores=verification_cores,
            collector_snapshot=restored_collector_snapshot,
            current_boundaries=[
                runtime_payload["current_observation_state_boundary"]
                for runtime_payload in runtime_payloads
            ],
            optimizer_states=restored_optimizers,
            normalizer_states=restored_normalizers,
            counters=restored_counters,
        )
        checkpoint_state_error = _nested_state_maximum_difference(
            model_state(model_owner), model_state(verification_owner)
        )
        checkpoint_runtime_error = _nested_state_maximum_difference(
            runtime_payloads,
            roundtrip_payload["event_architecture"]["runtime_payloads"],
        )
        checkpoint_collector_error = _nested_state_maximum_difference(
            live_payload["event_architecture"]["collector_snapshot"],
            restored_collector_snapshot,
        )
        checkpoint_optimizer_error = max(
            _nested_state_maximum_difference(
                high_optimizer.state_dict(), restored_optimizers["high"]
            ),
            _nested_state_maximum_difference(
                low_optimizer.state_dict(), restored_optimizers["low"]
            ),
        )
        checkpoint_normalizer_error = _nested_state_maximum_difference(
            normalizer_states, restored_normalizers
        )
        checkpoint_counter_error = _nested_state_maximum_difference(
            {
                "total_steps": total_steps,
                "update_idx": update_idx,
                "high_optimizer_steps": high_optimizer_steps,
                "low_optimizer_steps": low_optimizer_steps,
                "next_episode_id": next_episode_id,
                "intrinsic_applied_count": intrinsic_applied_count,
            },
            restored_counters,
        )
        verification_collector.close()

        final_state = model_state(model_owner)
        parameter_drift = _nested_state_maximum_difference(initial_state, final_state)
        forced_audit = final_stochastic["forced_audit"]
        prefix_rows = final_stochastic["prefix_rows"]
        persistent_skill = int(forced_audit["persistent_like_skill"])
        prefix_summary = _summarize_event_prefix_rows(
            prefix_rows,
            persistent_skill=persistent_skill,
            architecture_mode=model_owner.architecture_mode,
        )
        prefix_actual_replay_logp_max = float(
            prefix_summary["actual_replay_logp_max_error"]
        )
        prefix_actual_replay_probability_max = float(
            prefix_summary["actual_replay_probability_max_error"]
        )
        zero_det = zero_evaluation["deterministic"]
        final_det = final_deterministic
        improvement_ci = _paired_mean_ci(
            np.asarray(final_det["utility"], dtype=np.float64)
            - np.asarray(zero_det["utility"], dtype=np.float64),
            seed=107_057,
        )
        m0 = {
            "formal_contract_exact": True,
            "environment_steps_exact": total_steps == 320_000,
            "high_optimizer_steps_exact": high_optimizer_steps == 1_000,
            "low_optimizer_steps_exact": low_optimizer_steps == 1_000,
            "training_ledger_ids_exact": next_episode_id == 4_000,
            "zero_evaluation_exact": all(
                len(zero_evaluation[name]["utility"]) == 256
                for name in ("deterministic", "stochastic")
            ),
            "final_evaluation_exact": len(final_deterministic["utility"]) == 256
            and len(final_stochastic["utility"]) == 256,
            "forced_audit_exact": forced_audit["effect_shape"] == [128, 3, 2, 4]
            and forced_audit["forced_environment_steps"] == 9_216,
            "intrinsic_reward_and_count_zero": intrinsic_applied_count == 0,
            "sampling_replay_probability": max(
                maximum_replay_errors["high_logp_max_error"],
                maximum_replay_errors["low_logp_max_error"],
            )
            <= 1e-6,
            "sampling_replay_value": max(
                maximum_replay_errors["high_value_max_error"],
                maximum_replay_errors["low_value_max_error"],
            )
            <= 1e-6,
            "natural_probability_read_replay": max(
                prefix_actual_replay_logp_max,
                prefix_actual_replay_probability_max,
            )
            <= 1e-6,
            "all_updates_finite": bool(finite_updates),
            "final_parameters_finite": _event_state_dict_finite(model_owner),
            "parameter_update_nonzero": parameter_drift > 1e-8,
            "strict_vector_schema3_resume": checkpoint_state_error == 0.0
            and checkpoint_runtime_error == 0.0
            and checkpoint_collector_error == 0.0
            and checkpoint_optimizer_error == 0.0
            and checkpoint_normalizer_error == 0.0
            and checkpoint_counter_error == 0.0,
            "f0_common_support_reduction": model_owner.architecture_mode != "f0"
            or float(prefix_summary["f0_common_support_tv_max"] or 0.0) <= 1e-6,
        }
        implementation_valid = all(bool(value) for value in m0.values())
        final_deterministic_result = {
            key: value
            for key, value in final_deterministic.items()
            if key not in {"prefix_rows", "timing_rows", "forced_audit"}
        }
        final_stochastic_result = {
            key: value
            for key, value in final_stochastic.items()
            if key not in {"prefix_rows", "timing_rows", "forced_audit"}
        }
        arm_result = {
            "schema_version": 1,
            "stage": "stage_c_paired_f0_f1",
            "arm": model_owner.architecture_mode,
            "implementation_valid": implementation_valid,
            "m0": m0,
            "contract": {
                "num_envs": 16,
                "horizon": 80,
                "rollout_length": 80,
                "outer_updates": 250,
                "environment_transitions": 320_000,
                "ppo_passes_per_update": 4,
                "high_optimizer_steps": 1_000,
                "low_optimizer_steps": 1_000,
                "latent_skills": 3,
                "optimizer": "Adam",
                "learning_rate": 3e-4,
                "gamma": 0.99,
                "gae_lambda": 0.95,
                "policy_clip": 0.20,
                "value_clip": 0.20,
                "value_coefficient": 0.50,
                "entropy_coefficient": 0.01,
                "gradient_clip": 0.50,
                "evaluation_episodes_per_mode": 256,
                "bootstrap_repetitions": 10_000,
                "bootstrap_seed": 107_057,
                "selector": (
                    "initial_summary"
                    if model_owner.architecture_mode == "f0"
                    else "working_summary"
                ),
            },
            "counts": {
                "environment_steps": total_steps,
                "high_optimizer_steps": high_optimizer_steps,
                "low_optimizer_steps": low_optimizer_steps,
                "training_ledger_ids": next_episode_id,
                "intrinsic_applied_count": intrinsic_applied_count,
            },
            "resume": {
                "resumed_from": resumed_from,
                "strict_resume_verified": bool(m0["strict_vector_schema3_resume"]),
            },
            "replay": maximum_replay_errors,
            "parameter_drift_max_abs": parameter_drift,
            "checkpoint_state_max_error": checkpoint_state_error,
            "checkpoint_runtime_max_error": checkpoint_runtime_error,
            "checkpoint_collector_max_error": checkpoint_collector_error,
            "checkpoint_optimizer_max_error": checkpoint_optimizer_error,
            "checkpoint_normalizer_max_error": checkpoint_normalizer_error,
            "checkpoint_counter_max_error": checkpoint_counter_error,
            "zero": zero_evaluation,
            "final": {
                "deterministic": final_deterministic_result,
                "stochastic": final_stochastic_result,
            },
            "paired_final_minus_zero_deterministic_utility_ci95": improvement_ci,
            "prefix": prefix_summary,
            "forced_audit": forced_audit,
            "timing_rows": final_stochastic["timing_rows"],
            "last_update_metrics": last_metrics,
            "wall_seconds": time.perf_counter() - start_time,
        }
        arm_result_path = result_dir / "stage_c_arm.json"
        _write_event_json(arm_result_path, arm_result)
        _write_event_arm_status(
            args,
            state="complete",
            phase="terminal",
            mode=config.event_architecture_mode,
            update=250,
            updates_total=250,
            steps=320_000,
            steps_total=320_000,
            high_optimizer_steps=1_000,
            low_optimizer_steps=1_000,
            optimizer_steps_total=1_000,
            implementation_valid=implementation_valid,
            result_path=str(arm_result_path),
            checkpoint_path=str(latest_checkpoint_path),
        )
        return model_owner, total_steps, update_idx
    finally:
        collector.close()


def train_loop(config, args: argparse.Namespace, writer) -> tuple[StandaloneProcessAgent, int, int]:
    if is_variable_roster_event(config):
        enforce_variable_roster_event_resume_boundary(config, args)
        if not hasattr(config, "scenario") or not hasattr(args, "rollout_length"):
            dispatch_variable_roster_event_boundary(config)
        return _run_variable_roster_event_branch(config, args, writer)
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
        effect_views = [
            (
                np.asarray(info.get("intrinsic_effect_view"), dtype=np.float32).copy()
                if isinstance(info, dict) and info.get("intrinsic_effect_view") is not None
                else None
            )
            for info in _infos
        ]
        env = SimpleNamespace(**collector.spec)
        action_space_type, _, _ = action_space_details(env)
        state_dim = int(collector.spec.get("state_dim") or 0) or (
            int(np.asarray(states[0], dtype=np.float32).reshape(-1).size)
            if states and states[0] is not None
            else None
        )
        agent = create_agent(config, args, env, num_envs=num_envs, state_dim=state_dim)
        aem_enabled = bool(getattr(config, "aem_joint_novelty_enabled", False))
        if (bool(getattr(agent, "r31_enabled", False)) or aem_enabled) and any(
            view is None for view in effect_views
        ):
            raise RuntimeError(
                "active position-only objective requires intrinsic_effect_view"
            )
        aem_novelty = (
            EpisodicJointPositionNovelty(
                num_envs=num_envs,
                grid_size=int(getattr(config, "aem_joint_position_grid_size", 5)),
                episode_horizon=int(getattr(config, "aem_episode_horizon", 80)),
            )
            if aem_enabled
            else None
        )

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
            f"r24_qd_probe={bool(getattr(config, 'enable_team_conditioned_qd_probe', False))} "
            f"r24_qd_export={bool(getattr(config, 'r24_qd_export_windows', False))} "
            f"r24_qd_export_dir={getattr(config, 'r24_qd_export_dir', '')} "
            f"r24_qd_export_max_rows={int(getattr(config, 'r24_qd_export_max_rows_per_update', 0))} "
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
            r37_update_metrics = empty_r37_identity_metrics(config)
            for _local_step in range(int(args.rollout_length)):
                pre_obs = list(observations)
                rollout_base = len(rollout.rewards)
                pre_rollout_indices = [
                    rollout_base + env_id for env_id in range(num_envs)
                ]
                for env_id in range(num_envs):
                    obs = observations[env_id]
                    identity_audit = audit_r37_identity_observation(
                        config, obs, states[env_id]
                    )
                    r37_update_metrics["r37_identity_audit_rows"] += identity_audit[
                        "r37_identity_audit_rows"
                    ]
                    for field in (
                        "r37_identity_slot_max_abs_error",
                        "r37_critic_identity_max_abs_error",
                    ):
                        r37_update_metrics[field] = max(
                            r37_update_metrics[field], identity_audit[field]
                        )
                    rollout_idx = pre_rollout_indices[env_id]
                    agent.maybe_assign_skills(
                        obs,
                        state=states[env_id],
                        step=rollout_idx,
                        k=int(args.skill_interval),
                        env_id=env_id,
                        policy_update=int(update_idx + 1),
                        effect_view=effect_views[env_id],
                    )

                (
                    pre_actions_batch,
                    pre_logp_batch,
                    pre_values_batch,
                    pre_low_context,
                ) = agent.act_low_batch(
                    pre_obs,
                    env_ids=range(num_envs),
                    states=states,
                    return_context=True,
                )
                pre_actions = [pre_actions_batch[env_id] for env_id in range(num_envs)]
                pre_logp = [pre_logp_batch[env_id] for env_id in range(num_envs)]
                pre_values = [pre_values_batch[env_id] for env_id in range(num_envs)]

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
                    next_effect_view = info.get("intrinsic_effect_view")
                    if bool(getattr(agent, "r31_enabled", False)) or aem_enabled:
                        if next_effect_view is None:
                            raise RuntimeError(
                                "active position-only objective step did not expose "
                                "intrinsic_effect_view"
                            )
                        next_effect_view = np.asarray(
                            next_effect_view,
                            dtype=np.float32,
                        ).copy()
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
                    low_training_rewards = individual_rewards.copy()
                    if aem_novelty is not None:
                        bonus = aem_novelty.observe(env_id, next_effect_view)
                        low_training_rewards += np.float32(bonus)

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
                        deterministic_actions=low_context.get("deterministic_actions"),
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
                    if "deterministic_actions" in low_context:
                        rollout.deterministic_actions.append(
                            np.asarray(low_context["deterministic_actions"], dtype=np.float32).copy()
                        )
                    rollout.logp.append(logp.copy())
                    rollout.values.append(values.copy())
                    rollout.low_actor_hxs.append(np.asarray(low_context["actor_hxs"], dtype=np.float32))
                    rollout.low_critic_hxs.append(np.asarray(low_context["critic_hxs"], dtype=np.float32))
                    rollout.rewards.append(low_training_rewards)
                    rollout.dones.append(done)
                    episode_rewards.append(float(np.mean(individual_rewards)))

                    total_steps += 1
                    agent.record_environment_step(
                        env_id,
                        reward=float(reward),
                        next_obs=next_obs,
                        next_state=info.get("next_state", states[env_id]),
                        done=done,
                        effect_view=next_effect_view,
                        rollout_index=rollout_idx,
                    )
                    observations[env_id] = next_obs
                    states[env_id] = info.get("next_state", states[env_id])
                    effect_views[env_id] = next_effect_view
                    if done:
                        agent.segments.flush(env_id, reason="episode")
                        observations[env_id], info = collector.reset_one(env_id)
                        if aem_novelty is not None:
                            aem_novelty.reset_env(env_id)
                        states[env_id] = info.get("state")
                        # Re-seed pre-step info from the reset state for the next segment.
                        prev_state_info[env_id] = info.get("state_info", {}) or {}
                        prev_reward_info[env_id] = info.get("reward_info", {}) or {}
                        reset_effect_view = info.get("intrinsic_effect_view")
                        effect_views[env_id] = (
                            np.asarray(reset_effect_view, dtype=np.float32).copy()
                            if reset_effect_view is not None
                            else None
                        )
                        if bool(getattr(agent, "r31_enabled", False)) and effect_views[env_id] is None:
                            raise RuntimeError(
                                "R31 reset did not expose intrinsic_effect_view"
                            )
                        agent.reset_env_state(env_id)
                if total_steps >= int(args.total_timesteps):
                    break

            agent.truncate_high_rows_for_update(observations, states)
            agent.segments.flush(reason="update")
            rollout.bootstrap_values = agent.low_bootstrap_values(observations, states)
            r31_score_metrics = agent.r31_score_complete_windows(rollout)
            process_metrics = agent.process_update(
                rollout,
                total_steps=total_steps,
                update_idx=update_idx + 1,
            )
            process_metrics.update(
                aem_novelty.pop_update_metrics()
                if aem_novelty is not None
                else empty_aem_metrics(active=False)
            )
            process_metrics.update(r37_update_metrics)
            process_metrics.update(r31_score_metrics)
            low_metrics = agent.update_low(rollout)
            process_metrics.update(agent.r31_update_effect_posterior())
            if bool(getattr(agent, "constant_skill_no_high", False)):
                process_metrics.update(empty_r30_no_high_metrics())
            if bool(getattr(agent, "r30_enabled", False)) and not bool(
                getattr(agent, "constant_skill_no_high", False)
            ):
                process_metrics.update(
                    agent.update_high_from_checks(total_steps=total_steps)
                )
            update_idx += 1
            if bool(getattr(agent, "r30_enabled", False)) and not bool(
                getattr(agent, "constant_skill_no_high", False)
            ):
                agent.start_high_continuations_after_update(
                    observations,
                    states,
                    policy_update=update_idx + 1,
                )
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
                f"aem_active={process_metrics.get('aem_active', 0.0):.0f} "
                f"aem_bonus_applied_steps={process_metrics.get('aem_bonus_applied_steps', 0.0):.0f} "
                f"aem_bonus_sum={process_metrics.get('aem_bonus_sum', 0.0):.6f} "
                f"aem_bonus_max={process_metrics.get('aem_bonus_max', 0.0):.6f} "
                f"aem_count_resets={process_metrics.get('aem_count_resets', 0.0):.0f} "
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
                f"r31_windows={process_metrics.get('r31_effect_windows', 0.0):.0f} "
                f"r31_info={process_metrics.get('r31_effect_information_mean', 0.0):.6f} "
                f"r31_full_acc={process_metrics.get('r31_effect_full_acc', 0.0):.3f} "
                f"r31_ctx_acc={process_metrics.get('r31_effect_context_acc', 0.0):.3f} "
                f"r31_reward={process_metrics.get('r31_effect_reward_mean', 0.0):.6f} "
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
            if not bool(getattr(agent, "r30_enabled", False)):
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
    if is_variable_roster_event(config):
        dispatch_variable_roster_event_boundary(config)
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
    random.seed(int(args.seed))
    np.random.seed(int(args.seed))
    torch.manual_seed(int(args.seed))
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(int(args.seed))
    Path(args.log_dir).mkdir(parents=True, exist_ok=True)
    writer = SummaryWriter(args.log_dir) if SummaryWriter is not None else None
    config = load_config(args.config, args.preset or None)
    config.scenario = normalize_scenario(args.scenario)
    apply_standalone_overrides(config, args)
    enforce_variable_roster_event_resume_boundary(config, args)
    metadata = None
    if args.resume_from:
        metadata = load_checkpoint_metadata(args.resume_from)
        apply_checkpoint_structure(config, args, metadata)
    if is_variable_roster_event(config):
        enforce_variable_roster_event_contract(config, args, metadata)
        try:
            if args.dry_run_env_steps > 0:
                raise ValueError("event mode has no environment dry-run path")
            if args.mode != "train":
                raise ValueError("Stage C evaluation remains runner/analyzer-owned")
            train_loop(config, args, writer)
        except Exception as exc:
            Path(args.log_dir).mkdir(parents=True, exist_ok=True)
            (Path(args.log_dir) / "runner_stderr.log").write_text(
                traceback.format_exc(), encoding="utf-8"
            )
            _write_event_arm_status(
                args,
                state="failed",
                phase="runner",
                mode=str(getattr(config, "event_architecture_mode", "unknown")),
                error=f"{type(exc).__name__}: {exc}",
                error_path=str(Path(args.log_dir) / "runner_stderr.log"),
            )
            raise
        finally:
            if writer is not None:
                writer.close()
        return
    enforce_r28_g1_contract(config, args, metadata)
    enforce_r29_action_info_contract(config, args)
    enforce_r30_pair_gate(config, args, metadata)
    enforce_r30_contract(config, args)
    enforce_r31_contract(config, args, metadata)
    enforce_aem_contract(config, args, metadata)
    enforce_r37_identity_contract(config, args, metadata)

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
