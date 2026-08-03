"""Standalone fail-closed training-contract predicates.

This module owns the train-entrypoint contract checks while keeping their
frozen semantics independent from CLI, runtime, and checkpoint orchestration.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping

import torch

from ha_ctse_process.env_factory import normalize_scenario


R30_PAIR_SOURCE_CHECKPOINT_PATH = (
    "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/"
    "standalone_process_core_final.pt"
)


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
        "p2_recovery_credit_reward_on",
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
        "p2_recovery_credit_reward_on",
    ):
        setattr(config, name, False)
    config.process_reward_injection = "none"
    config.outcome_residual_injection = "none"
    config.topology_role_injection = "none"
    config.parallel_selection = False
    config.use_autoregressive_selection = True
    config.ar_prefix_mode = "roster"



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
        source_path == R30_PAIR_SOURCE_CHECKPOINT_PATH
        or source_path.endswith(f"/{R30_PAIR_SOURCE_CHECKPOINT_PATH}")
    ):
        raise ValueError(
            "R30 pair requires the registered R25 arm0 source: "
            f"{R30_PAIR_SOURCE_CHECKPOINT_PATH}"
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
        "p2_recovery_reward_coef",
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
    config.team_bridge_type = "deterministic_expected"
    config.low_actor_condition_on_team_code = False
    config.parallel_selection = False
    config.use_autoregressive_selection = True
    config.ar_prefix_mode = "roster"
    config.r30_pair_gate = True
