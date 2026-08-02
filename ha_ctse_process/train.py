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

from ha_ctse_process.env_factory import normalize_scenario
from ha_ctse_process.standalone_evaluation import evaluate
from ha_ctse_process.standalone_metrics import (
    audit_r37_identity_observation,
    emit,
    empty_r37_identity_metrics,
    export_update_metrics,
    log_eval_metrics,
    log_train_metrics,
)
from ha_ctse_process.collectors import SyncEnvCollector
from ha_ctse_process.checkpoint_io import (
    apply_checkpoint_structure,
    load_checkpoint,
    load_checkpoint_metadata,
    prune_periodic_checkpoints,
    save_checkpoint,
)
from ha_ctse_process.plotting import AEM_METRIC_FIELDS
from ha_ctse_process.standalone_agent import (
    Rollout,
    StandaloneProcessAgent,
)
from ha_ctse_process.standalone_cli import (
    action_space_details,
    apply_standalone_overrides,
    create_agent,
    create_collector,
    create_env,
    create_envs,
    load_config,
    parse_args,
    parse_int_tuple,
    resolve_device,
)
from ha_ctse_process.standalone_contracts import (
    dispatch_variable_roster_event_boundary,
    enforce_aem_contract,
    enforce_iteration5_process_semantics_contract,
    enforce_r28_g1_contract,
    enforce_r29_action_info_contract,
    enforce_r30_contract,
    enforce_r30_pair_gate,
    enforce_r31_contract,
    enforce_r37_identity_contract,
    enforce_variable_roster_event_contract,
    is_iteration5_process_semantics,
    is_variable_roster_event,
)



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
    _replace_event_file(temporary, path)


def _replace_event_file(temporary: Path, path: Path) -> None:
    """Bounded Windows fallback for the desktop's transient replace denial."""

    for attempt in range(10):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt == 9:
                path.write_bytes(temporary.read_bytes())
                try:
                    temporary.unlink(missing_ok=True)
                except PermissionError:
                    pass
                return
            time.sleep(0.05)


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
    _replace_event_file(temporary, path)


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


def _event_semantic_primitive_probabilities(
    model_owner,
    rows: Sequence[Any],
) -> list[list[float]]:
    """Replay already-emitted low rows without sampling or advancing a runtime."""

    if not rows:
        return []
    if int(model_owner.action_dim) != 3 or str(model_owner.action_space_type) != (
        "discrete"
    ):
        raise ValueError("semantic provenance requires three discrete primitives")
    actor = model_owner.low_actor
    observations = torch.as_tensor(
        np.stack([row.observation for row in rows]),
        dtype=torch.float32,
        device=model_owner.device,
    )
    skills = torch.as_tensor(
        [int(row.skill) for row in rows],
        dtype=torch.long,
        device=model_owner.device,
    )
    hidden = torch.as_tensor(
        np.stack([row.actor_hidden_before for row in rows]),
        dtype=torch.float32,
        device=model_owner.device,
    )
    features = actor._features(observations, skills)
    features, _unused_hidden = actor.actor_rnn(
        features,
        hidden,
        torch.ones(
            features.shape[0], 1, dtype=torch.float32, device=model_owner.device
        ),
    )
    probabilities = actor.actor_act.action_out(features).probs.detach().cpu().numpy()
    if probabilities.shape != (len(rows), 3) or not np.isfinite(probabilities).all():
        raise RuntimeError("semantic provenance primitive probabilities are invalid")
    output = probabilities.astype(np.float64).tolist()
    for row, probability in zip(rows, output):
        action_values = np.asarray(row.action).reshape(-1)
        if action_values.size != 1:
            raise RuntimeError("semantic provenance requires scalar discrete actions")
        action = int(action_values[0])
        replayed_logp = float(
            np.log(max(float(probability[action]), np.finfo(np.float64).tiny))
        )
        if abs(replayed_logp - float(row.old_log_probability)) > 1e-5:
            raise RuntimeError("semantic provenance low-policy replay mismatch")
    return output


def _project_event_semantic_natural_row(
    row,
    *,
    arm: str,
    episode_id: int,
    active_set_size: int,
    primitive_probabilities: Sequence[float],
) -> dict[str, Any]:
    """Project one emitted low row into the leakage-free natural schema."""

    action_values = np.asarray(row.action).reshape(-1)
    probabilities = np.asarray(primitive_probabilities, dtype=np.float64).reshape(-1)
    if action_values.size != 1 or probabilities.shape != (3,):
        raise ValueError("semantic provenance natural row has invalid action shape")
    if not np.isfinite(probabilities).all():
        raise ValueError("semantic provenance natural probabilities must be finite")
    return {
        "arm": str(arm),
        "task_master_seed": 97_057,
        "episode_id": int(episode_id),
        "physical_time": int(row.physical_time),
        "lifecycle_key": str(row.lifecycle_key),
        "membership_epoch": int(row.membership_epoch),
        "observation": np.asarray(row.observation, dtype=np.float32).tolist(),
        "actor_hidden_before": np.asarray(
            row.actor_hidden_before, dtype=np.float32
        ).tolist(),
        "natural_skill": int(row.skill),
        "natural_action": int(action_values[0]),
        "natural_action_log_probability": float(row.old_log_probability),
        "primitive_legal_support": [0, 1, 2],
        "primitive_probabilities": probabilities.tolist(),
        "active_set_size": int(active_set_size),
    }


def _capture_event_semantic_source(
    *,
    core,
    snapshot,
    transaction,
    focal_key: str,
) -> dict[str, Any]:
    """Capture source-only routing and owned-PCG64 state before branch cloning."""

    key = str(focal_key)
    if key not in snapshot.keys:
        raise ValueError("semantic provenance focal key is not active")
    active_skills = core.active_skills()
    if set(active_skills) != set(snapshot.keys):
        raise RuntimeError("semantic provenance active skill routing is incomplete")
    return {
        "focal_index": int(snapshot.keys.index(key)),
        "active_keys": list(snapshot.keys),
        "active_membership_epochs": [
            int(member.membership_epoch) for member in snapshot.members
        ],
        "active_skills": [int(active_skills[active]) for active in snapshot.keys],
        "frontier": list(snapshot.frontier),
        "membership_deltas": [
            {
                "kind": str(delta.kind),
                "lifecycle_key": str(delta.lifecycle_key),
                "expected_membership_epoch": int(delta.expected_membership_epoch),
            }
            for delta in transaction.atomic_membership_delta
        ],
        "source_rng_ledger": {
            "episode_id": int(core.rng_episode_id),
            "opportunity": {
                "master_seed": int(core.opportunity_master_seed),
                "stream_id": int(core.opportunity_stream_id),
            },
            "frontier_order": {
                "master_seed": int(core.frontier_master_seed),
                "stream_id": int(core.frontier_stream_id),
            },
            "policy_action": {
                "master_seed": int(core.action_master_seed),
                "stream_id": int(core.action_stream_id),
            },
        },
        "source_rng_states": {
            "opportunity": deepcopy(core.opportunity_rng.bit_generator.state),
            "frontier_order": deepcopy(core.frontier_rng.bit_generator.state),
            "policy_action": deepcopy(core.action_rng.bit_generator.state),
        },
    }


def _project_event_semantic_forced_source(
    natural_row: Mapping[str, Any],
    *,
    source: Mapping[str, Any],
    forced_effects: Sequence[Any],
) -> dict[str, Any]:
    """Join a captured source to its already-produced focal natural row."""

    effects = np.asarray(forced_effects, dtype=np.float64)
    if effects.shape != (3, 2, 4) or not np.isfinite(effects).all():
        raise ValueError("semantic provenance forced effects have invalid shape")
    focal_index = int(source["focal_index"])
    if str(source["active_keys"][focal_index]) != str(natural_row["lifecycle_key"]):
        raise RuntimeError("semantic provenance focal source does not match natural row")
    if int(source["active_membership_epochs"][focal_index]) != int(
        natural_row["membership_epoch"]
    ):
        raise RuntimeError("semantic provenance focal epoch does not match natural row")
    return {
        **deepcopy(dict(natural_row)),
        **deepcopy(dict(source)),
        "forced_effects": effects.tolist(),
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
    focal_key: str | None = None,
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
    selected_focal_key = (
        snapshot.keys[int(audit_index) % len(snapshot.keys)]
        if focal_key is None
        else str(focal_key)
    )
    if selected_focal_key not in snapshot.keys:
        raise ValueError("forced audit focal key is not active in the source snapshot")
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
                if selected_focal_key not in branch_core.records or (
                    branch_core.records[selected_focal_key].status != "ACTIVE"
                ):
                    raise RuntimeError("forced focal lifecycle left before audit window closed")
                branch_core.records[selected_focal_key].active_skill = int(skill)
                actions, _logp, _values = branch_core.low_step(
                    branch_snapshot, deterministic=False
                )
                routed = {
                    key: int(actions[index].detach().cpu())
                    for index, key in enumerate(branch_snapshot.keys)
                }
                focal_action = int(routed[selected_focal_key])
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
    capture_semantic_provenance: bool = False,
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
    semantic_natural_rows: list[dict[str, Any]] = []
    semantic_forced_sources: list[dict[str, Any]] = []
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
            if (capture_forced_audit or capture_semantic_provenance) and episode_id < 32:
                selected_times = {
                    1 + episode_id % 8,
                    20 + episode_id % 9,
                    40 + episode_id % 9,
                    60 + episode_id % 8,
                }
            for primitive_time in range(HORIZON):
                semantic_source = None
                source_forced_effects = None
                if primitive_time in selected_times:
                    audit_index = len(forced_effects)
                    focal_key = snapshot.keys[audit_index % len(snapshot.keys)]
                    if capture_semantic_provenance:
                        semantic_source = _capture_event_semantic_source(
                            core=core,
                            snapshot=snapshot,
                            transaction=bound,
                            focal_key=focal_key,
                        )
                    source_forced_effects = _forced_event_snapshot_effects(
                        model_owner=model_owner,
                        core=core,
                        environment=environment,
                        snapshot=snapshot,
                        episode_id=episode_id,
                        audit_index=audit_index,
                        focal_key=focal_key,
                    )
                    forced_effects.append(source_forced_effects)
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
                low_ledger_start = (
                    len(core.low_ledger)
                    if capture_semantic_provenance and episode_id < 32
                    else None
                )
                actions, _logp, _values = core.low_step(
                    snapshot, deterministic=bool(deterministic)
                )
                if low_ledger_start is not None:
                    emitted_low_rows = core.low_ledger[low_ledger_start:]
                    if len(emitted_low_rows) != len(snapshot.keys) or {
                        (str(row.lifecycle_key), int(row.membership_epoch))
                        for row in emitted_low_rows
                    } != {
                        (str(member.lifecycle_key), int(member.membership_epoch))
                        for member in snapshot.members
                    }:
                        raise RuntimeError(
                            "semantic provenance low-ledger source slice is not exact"
                        )
                    probability_rows = _event_semantic_primitive_probabilities(
                        model_owner, emitted_low_rows
                    )
                    projected_rows = [
                        _project_event_semantic_natural_row(
                            row,
                            arm=model_owner.architecture_mode,
                            episode_id=episode_id,
                            active_set_size=len(snapshot.keys),
                            primitive_probabilities=probabilities,
                        )
                        for row, probabilities in zip(
                            emitted_low_rows, probability_rows
                        )
                    ]
                    semantic_natural_rows.extend(projected_rows)
                    if semantic_source is not None:
                        focal_index = int(semantic_source["focal_index"])
                        focal_key = str(semantic_source["active_keys"][focal_index])
                        focal_epoch = int(
                            semantic_source["active_membership_epochs"][focal_index]
                        )
                        focal_rows = [
                            row
                            for row in projected_rows
                            if str(row["lifecycle_key"]) == focal_key
                            and int(row["membership_epoch"]) == focal_epoch
                        ]
                        if len(focal_rows) != 1 or source_forced_effects is None:
                            raise RuntimeError(
                                "semantic provenance forced source lacks one natural match"
                            )
                        semantic_forced_sources.append(
                            _project_event_semantic_forced_source(
                                focal_rows[0],
                                source=semantic_source,
                                forced_effects=source_forced_effects,
                            )
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
        if capture_semantic_provenance:
            if len(semantic_forced_sources) != 128:
                raise RuntimeError("semantic provenance forced source count is not exact")
            payload["semantic_provenance"] = {
                "schema": 1,
                "natural_rows": semantic_natural_rows,
                "forced_sources": semantic_forced_sources,
            }
        return payload
    finally:
        for module, was_training in zip(modules, previous_training):
            module.train(was_training)


def _iteration5_semantic_checkpoint(
    base_payload: Mapping[str, Any],
    *,
    trainer,
    ledgers,
    intrinsic_applied_count: int,
    replay: Mapping[str, float],
    high_intrinsic_isolated: bool,
    posterior_policy_gradient_isolated: bool,
) -> dict[str, Any]:
    from ha_ctse_process.process_semantics import snapshot_event_semantic_bundle

    payload = deepcopy(dict(base_payload))
    event = payload.get("event_architecture")
    if (
        not isinstance(event, dict)
        or "event_semantic" in event
        or "iteration5_evidence_state" in event
    ):
        raise ValueError("Iteration-5 checkpoint requires one clean event bundle")
    event["event_semantic"] = snapshot_event_semantic_bundle(
        trainer=trainer,
        ledgers=ledgers,
        intrinsic_applied_count=int(intrinsic_applied_count),
    )
    replay_value = {str(name): float(value) for name, value in dict(replay).items()}
    required_replay = {
        "high_logp_max_error",
        "high_value_max_error",
        "low_logp_max_error",
        "low_value_max_error",
    }
    if set(replay_value) != required_replay or any(
        not np.isfinite(value) or value < 0.0 for value in replay_value.values()
    ):
        raise ValueError("Iteration-5 checkpoint replay evidence is invalid")
    event["iteration5_evidence_state"] = {
        "schema_version": 1,
        "replay": replay_value,
        "high_intrinsic_isolated": bool(high_intrinsic_isolated),
        "posterior_policy_gradient_isolated": bool(
            posterior_policy_gradient_isolated
        ),
    }
    return payload


def _restore_iteration5_vector_checkpoint(
    payload: Mapping[str, Any],
    *,
    model_owner,
    cores,
    collector,
    trainer,
    ledgers,
):
    from ha_ctse_process.process_semantics import restore_event_semantic_bundle
    from ha_ctse_process.variable_roster_event import restore_vector_event_checkpoint

    value = deepcopy(dict(payload))
    event = value.get("event_architecture")
    if (
        not isinstance(event, dict)
        or "event_semantic" not in event
        or "iteration5_evidence_state" not in event
    ):
        raise ValueError("Iteration-5 checkpoint is missing semantic/evidence state")
    semantic = event.pop("event_semantic")
    evidence = deepcopy(dict(event.pop("iteration5_evidence_state")))
    if set(evidence) != {
        "schema_version",
        "replay",
        "high_intrinsic_isolated",
        "posterior_policy_gradient_isolated",
    } or int(evidence["schema_version"]) != 1:
        raise ValueError("Iteration-5 checkpoint evidence schema mismatch")
    replay = {str(name): float(value) for name, value in dict(evidence["replay"]).items()}
    if set(replay) != {
        "high_logp_max_error",
        "high_value_max_error",
        "low_logp_max_error",
        "low_value_max_error",
    } or any(not np.isfinite(value) or value < 0.0 for value in replay.values()):
        raise ValueError("Iteration-5 restored replay evidence is invalid")
    evidence["replay"] = replay
    evidence["high_intrinsic_isolated"] = bool(
        evidence["high_intrinsic_isolated"]
    )
    evidence["posterior_policy_gradient_isolated"] = bool(
        evidence["posterior_policy_gradient_isolated"]
    )
    optimizer_states, normalizers, counters = restore_vector_event_checkpoint(
        value, model_owner=model_owner, cores=cores, collector=collector
    )
    semantic_count = restore_event_semantic_bundle(
        semantic, trainer=trainer, ledgers=ledgers
    )
    if int(counters["intrinsic_applied_count"]) != int(semantic_count):
        raise ValueError("Iteration-5 intrinsic counters disagree across bundles")
    return optimizer_states, normalizers, counters, evidence


def _open_iteration5_window(
    *, ledger, core, snapshot, lifecycle_key: str, process_state: float
) -> None:
    key = str(lifecycle_key)
    member_index = snapshot.keys.index(key)
    member = snapshot.members[member_index]
    record = core.records[key]
    if record.active_skill is None:
        raise RuntimeError("Iteration-5 active lifecycle has no skill")
    ledger.open_window(
        lifecycle_key=key,
        membership_epoch=int(record.membership_epoch),
        policy_version=int(core.policy_version),
        skill=int(record.active_skill),
        start_observation=np.asarray(member.observation, dtype=np.float32),
        start_actor_hidden=np.asarray(record.low_actor_hidden, dtype=np.float32),
        start_process_state=float(process_state),
    )


def _apply_iteration5_transaction_hooks(
    *, ledger, core, transaction, result, snapshot, process_state: Mapping[str, float]
) -> None:
    from ha_ctse_process.variable_roster_event import event_action_hooks

    member_by_key = {str(member.lifecycle_key): member for member in snapshot.members}
    for hook in event_action_hooks(result):
        key = str(hook.lifecycle_key)
        ledger_key = (key, int(hook.membership_epoch), int(hook.policy_version))
        if ledger_key not in ledger.open_keys:
            _open_iteration5_window(
                ledger=ledger,
                core=core,
                snapshot=snapshot,
                lifecycle_key=key,
                process_state=float(process_state[key]),
            )
            continue
        record = core.records[key]
        member = member_by_key[key]
        ledger.apply_event_boundary(
            lifecycle_key=key,
            membership_epoch=int(hook.membership_epoch),
            policy_version=int(hook.policy_version),
            action_kind=str(hook.action_kind),
            next_skill=int(hook.next_skill),
            observation=np.asarray(member.observation, dtype=np.float32),
            actor_hidden=np.asarray(record.low_actor_hidden, dtype=np.float32),
            process_state=float(process_state[key]),
        )
    for key in snapshot.keys:
        record = core.records[str(key)]
        ledger_key = (str(key), int(record.membership_epoch), int(core.policy_version))
        if ledger_key not in ledger.open_keys:
            _open_iteration5_window(
                ledger=ledger,
                core=core,
                snapshot=snapshot,
                lifecycle_key=str(key),
                process_state=float(process_state[str(key)]),
            )


@torch.no_grad()
def _evaluate_iteration5_spatial_model(
    model_owner,
    *,
    deterministic: bool,
    episodes: int,
) -> dict[str, Any]:
    from ha_ctse_process.dynamic_roster_spatial_testbed import (
        HORIZON,
        SpatialDynamicRosterEventEnv,
    )
    from ha_ctse_process.collectors import SyncEnvCollector
    from ha_ctse_process.variable_roster_event import batched_low_step

    persistent: list[float] = []
    short: list[float] = []
    utility: list[float] = []
    skill_counts = np.zeros(model_owner.n_skills, dtype=np.int64)
    episode_count = int(episodes)
    if episode_count <= 0:
        raise ValueError("Iteration-5 evaluation requires at least one episode")
    environments = [
        SpatialDynamicRosterEventEnv(task_master_seed=97_057)
        for _episode_id in range(episode_count)
    ]
    collector = SyncEnvCollector(environments)
    try:
        transactions = collector.reset_event_runtime(tuple(range(episode_count)))
        cores = []
        snapshots = []
        for episode_id, transaction in enumerate(transactions):
            core = _make_event_runtime(
                model_owner,
                environment_index=0,
                episode_id=episode_id,
                event_master_seed=77_057,
                action_master_seed=87_057,
            )
            bound = core.bind_due_frontier(transaction)
            core.apply_transaction(bound, deterministic_policy=bool(deterministic))
            cores.append(core)
            snapshots.append(bound.post_membership_pre_policy_snapshot)
        for physical_time in range(HORIZON):
            for core in cores:
                for skill in core.active_skills().values():
                    skill_counts[int(skill)] += 1
            low = batched_low_step(
                cores, snapshots, deterministic=bool(deterministic)
            )
            steps = collector.step_event_runtime(low.routed_actions)
            terminal_flags = tuple(bool(step.terminated) for step in steps)
            for core, step in zip(cores, steps):
                core.complete_primitive_transition(float(step.reward))
            if any(terminal_flags):
                if not all(terminal_flags) or physical_time != HORIZON - 1:
                    raise RuntimeError(
                        "Iteration-5 evaluation episodes lost their shared horizon"
                    )
                for core, step in zip(cores, steps):
                    core.close_terminal()
                    persistent.append(float(step.info["persistent_score"]))
                    short.append(float(step.info["short_score"]))
                    utility.append(float(step.info["utility"]))
                break
            next_snapshots = []
            for core, step in zip(cores, steps):
                if step.next_transaction is None:
                    raise RuntimeError(
                        "Iteration-5 evaluation lost its next transaction"
                    )
                bound = core.bind_due_frontier(step.next_transaction)
                core.apply_transaction(
                    bound, deterministic_policy=bool(deterministic)
                )
                next_snapshots.append(bound.post_membership_pre_policy_snapshot)
            snapshots = next_snapshots
        if len(persistent) != episode_count:
            raise RuntimeError("Iteration-5 evaluation did not complete every episode")
    finally:
        collector.close()
    counts = skill_counts.astype(np.float64)
    return {
        "episodes": int(episodes),
        "deterministic": bool(deterministic),
        "persistent": persistent,
        "short": short,
        "utility": utility,
        "persistent_mean": float(np.mean(persistent)),
        "short_mean": float(np.mean(short)),
        "utility_mean": float(np.mean(utility)),
        "natural_skill_step_counts": skill_counts.tolist(),
        "natural_skill_step_shares": (counts / max(float(counts.sum()), 1.0)).tolist(),
    }


def _run_iteration5_process_semantics_branch(config, args: argparse.Namespace, writer):
    """Separate spatial F0 branch with rollout-frozen process semantics."""

    from ha_ctse_process.collectors import SyncEnvCollector
    from ha_ctse_process.dynamic_roster_spatial_testbed import (
        HORIZON,
        SpatialDynamicRosterEventEnv,
    )
    from ha_ctse_process.process_semantics import (
        ConditionalProcessPosterior,
        ProcessSemanticTrainer,
        ProcessWindowLedger,
    )
    from ha_ctse_process.variable_roster_event import (
        apply_event_ppo_update,
        batched_low_step,
        event_model_only_checkpoint_payload,
        event_action_hooks,
        lifecycle_boundary_hooks,
        low_row_index_hooks,
        pack_event_ppo_data,
        vector_event_checkpoint_payload,
    )

    enforce_iteration5_process_semantics_contract(config, args)
    arm = str(config.iteration5_process_semantics_arm)
    smoke = bool(getattr(config, "iteration5_smoke", False))
    num_envs = int(args.num_envs)
    rollout = int(args.rollout_length)
    total_target = int(args.total_timesteps)
    if rollout != HORIZON or total_target <= 0 or total_target % (num_envs * HORIZON):
        raise ValueError("Iteration-5 requires whole 80-step vector rollouts")
    updates_total = total_target // (num_envs * HORIZON)
    if not smoke and (num_envs, updates_total, total_target) != (16, 250, 320_000):
        raise ValueError("formal Iteration-5 requires 16 envs, 250 updates and 320000 steps")
    if str(getattr(args, "device", "cuda")).lower() != "cuda" or not torch.cuda.is_available():
        raise RuntimeError("Iteration-5 training requires available CUDA")
    device = torch.device("cuda")
    beta = 0.05 if arm == "c1_semantic_on" else 0.0
    output_root = Path(args.log_dir)
    checkpoint_dir = output_root / "checkpoints"
    result_dir = output_root / "result"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    result_dir.mkdir(parents=True, exist_ok=True)

    with torch.random.fork_rng(devices=[torch.cuda.current_device()]):
        torch.manual_seed(57_057)
        torch.cuda.manual_seed_all(57_057)
        model_owner = _make_event_model_owner(config, device)
        posterior = ConditionalProcessPosterior(
            observation_dim=model_owner.obs_dim,
            actor_hidden_dim=model_owner.low_hidden_dim,
            n_skills=model_owner.n_skills,
            hidden_dim=32,
        )
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
    semantic_trainer = ProcessSemanticTrainer(
        posterior, beta=beta, device=device, sampler_seed=67_057
    )
    normalizers = _event_identity_normalizers()
    environments = [
        SpatialDynamicRosterEventEnv(task_master_seed=57_057) for _ in range(num_envs)
    ]
    collector = SyncEnvCollector(environments)
    ledgers = [ProcessWindowLedger(max_window_length=12) for _ in range(num_envs)]
    zero_checkpoint_path = checkpoint_dir / "update_000_eval.pt"
    if not str(getattr(args, "resume_from", "") or ""):
        zero_base = event_model_only_checkpoint_payload(
            model_owner=model_owner,
            normalizer_states=normalizers,
            total_steps=0,
            update_idx=0,
        )
        zero_payload = _iteration5_semantic_checkpoint(
            zero_base,
            trainer=semantic_trainer,
            ledgers=ledgers,
            intrinsic_applied_count=0,
            replay={
                "high_logp_max_error": 0.0,
                "high_value_max_error": 0.0,
                "low_logp_max_error": 0.0,
                "low_value_max_error": 0.0,
            },
            high_intrinsic_isolated=True,
            posterior_policy_gradient_isolated=True,
        )
        zero_temporary = zero_checkpoint_path.with_suffix(".pt.tmp")
        torch.save(zero_payload, zero_temporary)
        _replace_event_file(zero_temporary, zero_checkpoint_path)
    elif not zero_checkpoint_path.is_file():
        raise FileNotFoundError("Iteration-5 resume requires its update-0 checkpoint")
    zero_payload = torch.load(
        zero_checkpoint_path, map_location=device, weights_only=False
    )
    zero_event = zero_payload.get("event_architecture")
    if not isinstance(zero_event, Mapping) or "event_semantic" not in zero_event:
        raise ValueError("Iteration-5 update-0 checkpoint is incomplete")
    zero_owner = _make_event_model_owner(config, device)
    zero_owner.commitment_model.load_state_dict(
        zero_event["commitment_model_state"], strict=True
    )
    zero_owner.event_critic.load_state_dict(zero_event["event_critic_state"], strict=True)
    zero_owner.low_actor.load_state_dict(zero_event["low_actor_state"], strict=True)
    zero_owner.low_critic.load_state_dict(zero_event["low_critic_state"], strict=True)
    total_steps = 0
    update_idx = 0
    high_steps = 0
    low_steps = 0
    posterior_steps = 0
    intrinsic_count = 0
    next_episode_id = 0
    posterior_policy_gradient_isolated = True
    high_intrinsic_isolated = True
    replay = {
        "high_logp_max_error": 0.0,
        "high_value_max_error": 0.0,
        "low_logp_max_error": 0.0,
        "low_value_max_error": 0.0,
    }

    def prepare(episode_ids: Sequence[int]):
        transactions = collector.reset_event_runtime(episode_ids)
        cores = []
        snapshots = []
        for env_index, (episode_id, transaction) in enumerate(zip(episode_ids, transactions)):
            core = _make_event_runtime(
                model_owner,
                environment_index=env_index,
                episode_id=int(episode_id),
                event_master_seed=77_057,
                action_master_seed=87_057,
            )
            bound = core.bind_due_frontier(transaction)
            result = core.apply_transaction(bound, deterministic_policy=False)
            snapshot = bound.post_membership_pre_policy_snapshot
            process = environments[env_index].process_state_mapping(snapshot.keys)
            _apply_iteration5_transaction_hooks(
                ledger=ledgers[env_index],
                core=core,
                transaction=bound,
                result=result,
                snapshot=snapshot,
                process_state=process,
            )
            cores.append(core)
            snapshots.append(snapshot)
        return cores, snapshots

    resume_path = str(getattr(args, "resume_from", "") or "")
    if resume_path:
        resolved_resume = Path(resume_path).resolve()
        if resolved_resume.parent != checkpoint_dir.resolve():
            raise ValueError("Iteration-5 resume checkpoint must belong to this arm root")
        payload = torch.load(resolved_resume, map_location=device, weights_only=False)
        runtime_payloads = list(payload["event_architecture"]["runtime_payloads"])
        cores = []
        for env_index, runtime_payload in enumerate(runtime_payloads):
            rng = runtime_payload["rng_ledger"]
            cores.append(
                _make_event_runtime(
                    model_owner,
                    environment_index=env_index,
                    episode_id=int(rng["episode_id"]),
                    event_master_seed=int(rng["opportunity"]["master_seed"]),
                    action_master_seed=int(rng["policy_action"]["master_seed"]),
                )
            )
        optimizer_states, normalizers, counters, evidence = (
            _restore_iteration5_vector_checkpoint(
                payload,
                model_owner=model_owner,
                cores=cores,
                collector=collector,
                trainer=semantic_trainer,
                ledgers=ledgers,
            )
        )
        high_optimizer.load_state_dict(optimizer_states["high"])
        low_optimizer.load_state_dict(optimizer_states["low"])
        total_steps = int(counters["total_steps"])
        update_idx = int(counters["update_idx"])
        high_steps = int(counters["high_optimizer_steps"])
        low_steps = int(counters["low_optimizer_steps"])
        next_episode_id = int(counters["next_episode_id"])
        intrinsic_count = int(counters["intrinsic_applied_count"])
        posterior_steps = int(semantic_trainer.posterior_steps)
        replay = dict(evidence["replay"])
        high_intrinsic_isolated = bool(evidence["high_intrinsic_isolated"])
        posterior_policy_gradient_isolated = bool(
            evidence["posterior_policy_gradient_isolated"]
        )
        if not 0 < update_idx < updates_total:
            raise ValueError("Iteration-5 resume update lies outside the active run")
        if (
            total_steps != update_idx * num_envs * HORIZON
            or high_steps != update_idx * 4
            or low_steps != update_idx * 4
            or posterior_steps != update_idx * 4
            or next_episode_id != update_idx * num_envs
            or intrinsic_count < 0
        ):
            raise ValueError("Iteration-5 resume counter ledger mismatch")
        if any(ledger.open_keys for ledger in ledgers):
            raise ValueError("Iteration-5 terminal resume retained an open semantic window")
        # Live checkpoints are emitted only after a complete 80-step episode batch.
        # Restore validates their runtime/collector state, then the next update starts
        # a fresh registered episode batch; terminal boundaries intentionally have no
        # observation snapshot to resume inside an episode.
        cores = []
        snapshots = []
    else:
        cores = []
        snapshots = []

    zero_episodes = 2 if smoke else 256
    zero = {
        "deterministic": _evaluate_iteration5_spatial_model(
            zero_owner, deterministic=True, episodes=zero_episodes
        ),
        "stochastic": _evaluate_iteration5_spatial_model(
            zero_owner, deterministic=False, episodes=zero_episodes
        ),
    }
    update_rows: list[dict[str, Any]] = []
    try:
        for update in range(update_idx + 1, updates_total + 1):
            if not cores:
                episode_ids = tuple(range(next_episode_id, next_episode_id + num_envs))
                next_episode_id += num_envs
                cores, snapshots = prepare(episode_ids)
            for _physical_time in range(HORIZON):
                starts = [len(core.low_ledger) for core in cores]
                low = batched_low_step(cores, snapshots)
                steps = collector.step_event_runtime(low.routed_actions)
                next_snapshots = []
                for env_index, (core, step) in enumerate(zip(cores, steps)):
                    ledger = ledgers[env_index]
                    core.complete_primitive_transition(float(step.reward))
                    post_process = dict(step.info.get("process_state", {}))
                    for hook in low_row_index_hooks(core, starts[env_index]):
                        ledger.observe_transition(
                            lifecycle_key=hook.lifecycle_key,
                            membership_epoch=hook.membership_epoch,
                            policy_version=hook.policy_version,
                            low_row_index=hook.low_row_index,
                            post_process_state=float(post_process[hook.lifecycle_key]),
                        )
                    if step.terminated:
                        for key, epoch, version in tuple(ledger.open_keys):
                            ledger.apply_lifecycle_boundary(
                                lifecycle_key=key,
                                membership_epoch=epoch,
                                policy_version=version,
                                boundary_kind="EPISODE_TERMINAL",
                            )
                        core.close_terminal()
                        next_snapshots.append(None)
                        continue
                    if step.next_transaction is None:
                        raise RuntimeError("Iteration-5 nonterminal step lost transaction")
                    transaction = step.next_transaction
                    for boundary in lifecycle_boundary_hooks(transaction):
                        if boundary.boundary_kind in {"TEMPORARY_LEAVE", "TERMINAL_LEAVE"}:
                            record = core.records.get(boundary.lifecycle_key)
                            if record is not None:
                                ledger.apply_lifecycle_boundary(
                                    lifecycle_key=boundary.lifecycle_key,
                                    membership_epoch=int(record.membership_epoch),
                                    policy_version=int(core.policy_version),
                                    boundary_kind=boundary.boundary_kind,
                                )
                    bound = core.bind_due_frontier(transaction)
                    result = core.apply_transaction(bound, deterministic_policy=False)
                    next_snapshot = bound.post_membership_pre_policy_snapshot
                    next_process = environments[env_index].process_state_mapping(next_snapshot.keys)
                    member_by_key = {
                        str(member.lifecycle_key): member for member in next_snapshot.members
                    }
                    for key, epoch, version in tuple(ledger.open_keys):
                        if key in next_snapshot.keys:
                            record = core.records[key]
                            member = member_by_key[key]
                            ledger.roll_full_window(
                                lifecycle_key=key,
                                membership_epoch=epoch,
                                policy_version=version,
                                observation=np.asarray(member.observation, dtype=np.float32),
                                actor_hidden=np.asarray(record.low_actor_hidden, dtype=np.float32),
                                process_state=float(next_process[key]),
                            )
                    _apply_iteration5_transaction_hooks(
                        ledger=ledger,
                        core=core,
                        transaction=bound,
                        result=result,
                        snapshot=next_snapshot,
                        process_state=next_process,
                    )
                    next_snapshots.append(next_snapshot)
                snapshots = next_snapshots
                total_steps += num_envs

            windows_by_env = []
            for ledger in ledgers:
                ledger.close_rollout()
                windows_by_env.append(ledger.drain_closed_windows())
            all_windows = [window for rows in windows_by_env for window in rows]
            packed_windows = semantic_trainer.pack_closed_windows(all_windows)
            scores = semantic_trainer.score_closed_windows(packed_windows)
            high_rewards_before = [
                tuple(
                    (float(row.discounted_reward), float(row.return_target))
                    for row in core.closed_event_rows
                )
                for core in cores
            ]
            score_offset = 0
            for core, owned_windows in zip(cores, windows_by_env):
                owned_scores = scores[score_offset : score_offset + len(owned_windows)]
                score_offset += len(owned_windows)
                if owned_windows:
                    intrinsic_count += semantic_trainer.apply_low_rewards(
                        core.low_ledger,
                        owned_windows,
                        owned_scores,
                    )
            high_intrinsic_isolated = high_intrinsic_isolated and all(
                before
                == tuple(
                    (float(row.discounted_reward), float(row.return_target))
                    for row in core.closed_event_rows
                )
                for before, core in zip(high_rewards_before, cores)
            )
            posterior_metrics = semantic_trainer.update_posterior(
                packed_windows, passes=4
            )
            posterior_steps += int(posterior_metrics["posterior_steps"])
            posterior_policy_gradient_isolated = (
                posterior_policy_gradient_isolated
                and all(
                    parameter.grad is None
                    for module in (
                        model_owner.commitment_model,
                        model_owner.event_critic,
                        model_owner.low_actor,
                        model_owner.low_critic,
                    )
                    for parameter in module.parameters()
                )
            )
            packed = pack_event_ppo_data(cores)
            metrics = None
            first_pass_replay = None
            for ppo_pass in range(4):
                metrics = apply_event_ppo_update(
                    packed,
                    high_optimizer=high_optimizer,
                    low_optimizer=low_optimizer,
                )
                high_steps += 1
                low_steps += 1
                if ppo_pass == 0:
                    first_pass_replay = {
                        name: float(metrics[name]) for name in replay
                    }
            high_optimizer.zero_grad(set_to_none=True)
            low_optimizer.zero_grad(set_to_none=True)
            assert metrics is not None
            assert first_pass_replay is not None
            for name in replay:
                replay[name] = max(replay[name], first_pass_replay[name])
            update_idx = update
            update_rows.append(
                {
                    "update": update,
                    "steps": total_steps,
                    "high_optimizer_steps": high_steps,
                    "low_optimizer_steps": low_steps,
                    "posterior_optimizer_steps": posterior_steps,
                    "intrinsic_applied_count": intrinsic_count,
                    **replay,
                }
            )
            checkpoint_interval = max(int(args.save_interval), 1)
            checkpoint_due = (
                update_idx % checkpoint_interval == 0
                or update_idx == updates_total
            )
            if checkpoint_due:
                boundaries = [
                    {
                        "physical_time": int(core.physical_time),
                        "episode_id": int(core.rng_episode_id),
                        "terminal": True,
                    }
                    for core in cores
                ]
                base = vector_event_checkpoint_payload(
                    model_owner=model_owner,
                    cores=cores,
                    collector_snapshot=collector.snapshot_event_runtime(),
                    current_boundaries=boundaries,
                    optimizer_states={
                        "high": high_optimizer.state_dict(),
                        "low": low_optimizer.state_dict(),
                    },
                    normalizer_states=normalizers,
                    counters={
                        "total_steps": total_steps,
                        "update_idx": update_idx,
                        "high_optimizer_steps": high_steps,
                        "low_optimizer_steps": low_steps,
                        "next_episode_id": next_episode_id,
                        "intrinsic_applied_count": intrinsic_count,
                    },
                )
                payload = _iteration5_semantic_checkpoint(
                    base,
                    trainer=semantic_trainer,
                    ledgers=ledgers,
                    intrinsic_applied_count=intrinsic_count,
                    replay=replay,
                    high_intrinsic_isolated=high_intrinsic_isolated,
                    posterior_policy_gradient_isolated=(
                        posterior_policy_gradient_isolated
                    ),
                )
                latest = checkpoint_dir / "latest.pt"
                temporary = latest.with_suffix(".pt.tmp")
                torch.save(payload, temporary)
                _replace_event_file(temporary, latest)
            cores = []
            snapshots = []
            _write_event_arm_status(
                args,
                state="running",
                phase="training",
                mode=arm,
                update=update_idx,
                updates_total=updates_total,
                steps=total_steps,
                steps_total=total_target,
            )

        eval_episodes = 2 if smoke else 256
        final = {
            "deterministic": _evaluate_iteration5_spatial_model(
                model_owner, deterministic=True, episodes=eval_episodes
            ),
            "stochastic": _evaluate_iteration5_spatial_model(
                model_owner, deterministic=False, episodes=eval_episodes
            ),
        }
        live_payload = torch.load(
            checkpoint_dir / "latest.pt", map_location=device, weights_only=False
        )
        verification_owner = _make_event_model_owner(config, device)
        verification_trainer = ProcessSemanticTrainer(
            ConditionalProcessPosterior(
                observation_dim=verification_owner.obs_dim,
                actor_hidden_dim=verification_owner.low_hidden_dim,
                n_skills=verification_owner.n_skills,
                hidden_dim=32,
            ),
            beta=beta,
            device=device,
            sampler_seed=1,
        )
        verification_ledgers = [
            ProcessWindowLedger(max_window_length=12) for _ in range(num_envs)
        ]
        verification_environments = [
            SpatialDynamicRosterEventEnv(task_master_seed=1) for _ in range(num_envs)
        ]
        verification_collector = SyncEnvCollector(verification_environments)
        runtime_payloads = list(live_payload["event_architecture"]["runtime_payloads"])
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
        (
            restored_optimizers,
            restored_normalizers,
            restored_counters,
            restored_evidence,
        ) = (
            _restore_iteration5_vector_checkpoint(
                live_payload,
                model_owner=verification_owner,
                cores=verification_cores,
                collector=verification_collector,
                trainer=verification_trainer,
                ledgers=verification_ledgers,
            )
        )
        checkpoint_roundtrip_error = max(
            _nested_state_maximum_difference(
                model_owner.commitment_model.state_dict(),
                verification_owner.commitment_model.state_dict(),
            ),
            _nested_state_maximum_difference(
                model_owner.event_critic.state_dict(),
                verification_owner.event_critic.state_dict(),
            ),
            _nested_state_maximum_difference(
                model_owner.low_actor.state_dict(),
                verification_owner.low_actor.state_dict(),
            ),
            _nested_state_maximum_difference(
                model_owner.low_critic.state_dict(),
                verification_owner.low_critic.state_dict(),
            ),
            _nested_state_maximum_difference(
                semantic_trainer.state_dict(), verification_trainer.state_dict()
            ),
            _nested_state_maximum_difference(normalizers, restored_normalizers),
            _nested_state_maximum_difference(
                {
                    "total_steps": total_steps,
                    "update_idx": update_idx,
                    "high_optimizer_steps": high_steps,
                    "low_optimizer_steps": low_steps,
                    "next_episode_id": next_episode_id,
                    "intrinsic_applied_count": intrinsic_count,
                },
                restored_counters,
            ),
            _nested_state_maximum_difference(
                high_optimizer.state_dict(), restored_optimizers["high"]
            ),
            _nested_state_maximum_difference(
                low_optimizer.state_dict(), restored_optimizers["low"]
            ),
            _nested_state_maximum_difference(
                {
                    "schema_version": 1,
                    "replay": replay,
                    "high_intrinsic_isolated": high_intrinsic_isolated,
                    "posterior_policy_gradient_isolated": (
                        posterior_policy_gradient_isolated
                    ),
                },
                restored_evidence,
            ),
        )
        verification_collector.close()
        formal_counts = (
            total_steps == total_target
            and high_steps == updates_total * 4
            and low_steps == updates_total * 4
            and posterior_steps == updates_total * 4
        )
        m0 = {
            "exposure_exact": bool(formal_counts),
            "sampling_replay_probability": max(
                replay["high_logp_max_error"], replay["low_logp_max_error"]
            ) <= 1e-6,
            "sampling_replay_value": max(
                replay["high_value_max_error"], replay["low_value_max_error"]
            ) <= 1e-6,
            "high_intrinsic_count_zero": bool(high_intrinsic_isolated),
            "posterior_policy_gradient_isolated": bool(
                posterior_policy_gradient_isolated
            ),
            "strict_semantic_checkpoint_round_trip": checkpoint_roundtrip_error
            == 0.0,
        }
        result = {
            "schema_version": 1,
            "stage": "iteration5_process_semantics",
            "scientific": not smoke,
            "arm": arm,
            "implementation_valid": all(m0.values()),
            "m0": m0,
            "contract": {
                "num_envs": num_envs,
                "horizon": HORIZON,
                "updates": updates_total,
                "transitions": total_target,
                "ppo_passes": 4,
                "posterior_passes": 4,
                "beta": beta,
            },
            "counts": update_rows[-1] if update_rows else {},
            "replay": replay,
            "checkpoint_roundtrip_max_error": checkpoint_roundtrip_error,
            "zero": zero,
            "final": final,
        }
        path = result_dir / "iteration5_arm.json"
        _write_event_json(path, result)
        _write_event_arm_status(
            args,
            state="complete",
            phase="terminal",
            mode=arm,
            update=update_idx,
            updates_total=updates_total,
            steps=total_steps,
            steps_total=total_target,
            result_path=str(path),
        )
        return model_owner, total_steps, update_idx
    finally:
        collector.close()


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
    if is_iteration5_process_semantics(config):
        enforce_iteration5_process_semantics_contract(config, args)
        return _run_iteration5_process_semantics_branch(config, args, writer)
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
    enforce_iteration5_process_semantics_contract(config, args, metadata)
    if is_variable_roster_event(config):
        enforce_variable_roster_event_contract(config, args, metadata)
        try:
            if args.dry_run_env_steps > 0:
                raise ValueError("event mode has no environment dry-run path")
            if args.mode != "train":
                raise ValueError("event evaluation remains runner/analyzer-owned")
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
