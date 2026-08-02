"""Standalone fail-closed training-contract predicates.

This module owns the train-entrypoint contract checks while keeping their
frozen semantics independent from CLI, runtime, and checkpoint orchestration.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import torch

from ha_ctse_process.checkpoint_io import _load_adjacent_run_manifest
from ha_ctse_process.env_factory import normalize_scenario
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


def is_iteration5_process_semantics(config) -> bool:
    return str(getattr(config, "iteration5_process_semantics_arm", "") or "") in {
        "c1_semantic_on",
        "c1_semantic_off",
    }


def enforce_iteration5_process_semantics_contract(
    config,
    args: argparse.Namespace,
    metadata: Mapping[str, Any] | None = None,
) -> None:
    if not is_iteration5_process_semantics(config):
        if metadata is not None and bool(metadata.get("has_event_semantic", False)):
            raise ValueError("non-Iteration-5 mode rejects an event semantic bundle")
        return
    if not is_variable_roster_event(config):
        raise ValueError("Iteration-5 process semantics requires variable_roster_event")
    if str(getattr(config, "event_architecture_mode", "")).lower() != "f0":
        raise ValueError("Iteration-5 hierarchical arms require exact F0 execution semantics")
    if metadata is not None and not bool(metadata.get("has_event_semantic", False)):
        raise ValueError("Iteration-5 resume requires an event semantic bundle")
    if str(getattr(args, "r28_g1_arm", "off")) != "off" or str(
        getattr(args, "r29_action_info_mode", "off")
    ) != "off" or str(getattr(args, "r31_effect_mode", "off") or "off") != "off":
        raise ValueError("Iteration-5 rejects retired intrinsic/effect objectives")


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
