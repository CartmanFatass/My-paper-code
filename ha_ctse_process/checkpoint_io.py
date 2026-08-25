"""Checkpoint persistence for the standalone HA-CTSE process core."""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, is_dataclass
import json
import math
from pathlib import Path
import random
from typing import Any

import numpy as np
import torch

from ha_ctse_process.standalone_agent import StandaloneProcessAgent


STANDALONE_STRICT_SCHEMA_VERSION = 4
STANDALONE_STRICT_RESUME_SEMANTICS = "strict_trajectory_v1"
STANDALONE_COLLECTOR_SNAPSHOT_CAPABILITY = "standalone_collector_training_state"
STANDALONE_COLLECTOR_SNAPSHOT_VERSION = 1

_STRICT_MODULE_FIELDS = (
    "high",
    "compact",
    "bridge",
    "low",
    "process",
    "process_posterior",
    "outcome_residual_probe",
    "topology_role_probe",
    "transition_discriminator",
    "prototype_discriminator",
    "compact_return_head",
    "situation_hazard",
    "team_transition",
    "team_discriminator",
    "high_value",
    "team_conditioned_qd_probe",
    "g_info_objective",
    "assignment_actionability",
    "team_effect_probe",
)
_STRICT_OPTIMIZER_FIELDS = (
    "high_opt",
    "low_opt",
    "low_actor_opt",
    "low_critic_opt",
    "process_opt",
    "prototype_disc_opt",
    "team_transition_opt",
    "team_disc_opt",
    "team_conditioned_qd_opt",
    "q_a_opt",
)
_STRICT_NORMALIZER_FIELDS = ("high_value_norm", "low_value_norm")

_OPERATIONAL_ARGUMENT_FIELDS = {
    "resume_from",
    "total_timesteps",
    "log_dir",
    "checkpoint_keep_last",
    "eval_checkpoint_name",
}
_OPERATIONAL_CONFIG_FIELDS = {
    "log_dir",
    "output_dir",
    "r24_qd_export_dir",
}
_AGENT_CONTRACT_EXCLUDED_FIELDS = {
    "assignment_actionability",
    "device",
    "q_a_opt",
    "r24_qd_export_dir",
    "team_effect_probe",
}
_CONTRACT_UNSUPPORTED = object()


def _normalize_contract_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, (float, np.floating)):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("training contract contains a non-finite float")
        return result
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (Path, torch.device)):
        return str(value)
    if is_dataclass(value):
        return _normalize_contract_value(asdict(value))
    if isinstance(value, dict):
        result = {}
        for key in sorted(value, key=lambda item: str(item)):
            normalized = _normalize_contract_value(value[key])
            if normalized is _CONTRACT_UNSUPPORTED:
                return _CONTRACT_UNSUPPORTED
            result[str(key)] = normalized
        return result
    if isinstance(value, (tuple, list)):
        result = []
        for item in value:
            normalized = _normalize_contract_value(item)
            if normalized is _CONTRACT_UNSUPPORTED:
                return _CONTRACT_UNSUPPORTED
            result.append(normalized)
        return result
    if isinstance(value, (set, frozenset)):
        normalized = [_normalize_contract_value(item) for item in value]
        if any(item is _CONTRACT_UNSUPPORTED for item in normalized):
            return _CONTRACT_UNSUPPORTED
        return sorted(normalized, key=lambda item: json.dumps(item, sort_keys=True))
    return _CONTRACT_UNSUPPORTED


def _namespace_contract(obj: Any, *, excluded: set[str]) -> dict[str, Any]:
    contract: dict[str, Any] = {}
    for name in sorted(name for name in dir(obj) if not name.startswith("_")):
        if name in excluded:
            continue
        value = getattr(obj, name)
        if callable(value):
            continue
        normalized = _normalize_contract_value(value)
        if normalized is _CONTRACT_UNSUPPORTED:
            raise TypeError(
                f"training contract field {name!r} has unsupported type "
                f"{type(value).__name__}"
            )
        contract[name] = normalized
    return contract


def _optimizer_hyperparameter_contract(agent: StandaloneProcessAgent) -> dict[str, Any]:
    contract: dict[str, Any] = {}
    for name in _STRICT_OPTIMIZER_FIELDS:
        if name == "q_a_opt":
            # q_A is created lazily after its feature dimensions are observed.
            # Its presence at a checkpoint is trajectory state, not an
            # effective-config difference from a fresh identical agent.  The
            # lazy spec and strict optimizer state validate/restore it below.
            contract[name] = {
                "managed_by": "lazy_module_specs.assignment_actionability"
            }
            continue
        optimizer = getattr(agent, name, None)
        if optimizer is None:
            contract[name] = None
            continue
        groups = []
        for group in optimizer.param_groups:
            normalized_group = {}
            for key, value in sorted(group.items()):
                if key == "params":
                    continue
                normalized = _normalize_contract_value(value)
                if normalized is _CONTRACT_UNSUPPORTED:
                    raise TypeError(
                        f"optimizer contract {name}.{key} has unsupported type"
                    )
                normalized_group[str(key)] = normalized
            groups.append(normalized_group)
        contract[name] = groups
    return contract


def effective_training_contract(
    agent: StandaloneProcessAgent,
    args: argparse.Namespace,
    config: Any,
) -> dict[str, Any]:
    """Normalize every effective update-semantic input before strict resume."""

    agent_fields: dict[str, Any] = {}
    for name, value in sorted(vars(agent).items()):
        if (
            name.startswith("_")
            or name.startswith("checkpoint_")
            or name in _AGENT_CONTRACT_EXCLUDED_FIELDS
        ):
            continue
        normalized = _normalize_contract_value(value)
        if normalized is not _CONTRACT_UNSUPPORTED:
            agent_fields[name] = normalized

    nested_config_sources = {}
    nested_exclusions = {
        "intrinsic_rewards": {"transition_normalizer", "segment_normalizer"},
        "outcome_extractor": {"normalizer"},
        "outcome_residual_extractor": {"normalizer"},
    }
    for name, exclusions in nested_exclusions.items():
        value = getattr(agent, name, None)
        if value is None:
            nested_config_sources[name] = None
            continue
        nested_config_sources[name] = _namespace_contract(
            value, excluded=exclusions
        )

    return {
        "training_contract_schema_version": 1,
        "resume_constraints": {
            # This target may only increase at resume time.  Keeping the
            # original floor prevents an apparent operational override from
            # silently shortening the frozen training treatment.
            "minimum_total_timesteps": int(args.total_timesteps),
        },
        "agent_effective": agent_fields,
        "agent_nested_config": nested_config_sources,
        "optimizer_hyperparameters": _optimizer_hyperparameter_contract(agent),
        "args": _namespace_contract(args, excluded=_OPERATIONAL_ARGUMENT_FIELDS),
        "config": _namespace_contract(config, excluded=_OPERATIONAL_CONFIG_FIELDS),
    }


def _validate_training_contract(
    saved_contract: Any,
    runtime_contract: dict[str, Any],
    *,
    checkpoint_total_steps: int,
) -> None:
    if not isinstance(saved_contract, dict):
        raise ValueError("schema-4 training contract must be a mapping")
    saved = deepcopy(saved_contract)
    runtime = deepcopy(runtime_contract)
    try:
        saved_minimum = int(
            saved.pop("resume_constraints")["minimum_total_timesteps"]
        )
        runtime_target = int(
            runtime.pop("resume_constraints")["minimum_total_timesteps"]
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("schema-4 training contract constraints mismatch") from exc
    if saved != runtime or runtime_target < max(
        saved_minimum, int(checkpoint_total_steps)
    ):
        raise ValueError(
            "schema-4 effective training contract mismatch; "
            "update-semantic configuration cannot change on strict resume"
        )


def capture_global_rng_state() -> dict[str, Any]:
    return {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch_cpu": torch.random.get_rng_state().clone(),
        "torch_cuda": (
            [state.clone() for state in torch.cuda.get_rng_state_all()]
            if torch.cuda.is_available()
            else None
        ),
    }


def restore_global_rng_state(state: dict[str, Any]) -> None:
    required = {"python", "numpy", "torch_cpu", "torch_cuda"}
    if not isinstance(state, dict) or set(state) != required:
        raise ValueError("global RNG state schema mismatch")
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.random.set_rng_state(torch.as_tensor(state["torch_cpu"], dtype=torch.uint8).cpu())
    cuda_state = state["torch_cuda"]
    if cuda_state is not None:
        if not torch.cuda.is_available():
            raise RuntimeError("checkpoint contains CUDA RNG state but CUDA is unavailable")
        if len(cuda_state) != torch.cuda.device_count():
            raise ValueError("CUDA RNG device-count mismatch")
        torch.cuda.set_rng_state_all(
            [torch.as_tensor(item, dtype=torch.uint8).cpu() for item in cuda_state]
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
        "resume_semantics": "weights_and_optimizer_warm_start_v1",
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


_STRICT_RUNNER_STATE_FIELDS = {
    "runner_state_schema_version",
    "num_envs",
    "observations",
    "states",
    "prev_state_info",
    "prev_reward_info",
    "last_eval_step",
    "proto_ratio_over05_count",
    "proto_ratio_consecutive_over05_count",
    "proto_ratio_kill_triggered_count",
    "team_disc_ratio_over05_count",
    "team_disc_ratio_consecutive_over05_count",
    "team_disc_ratio_kill_triggered_count",
    "combined_intrinsic_ratio_over05_count",
    "combined_intrinsic_ratio_consecutive_over05_count",
    "combined_intrinsic_ratio_kill_triggered_count",
}


def _validate_runner_state(state: dict[str, Any], *, num_envs: int) -> None:
    if not isinstance(state, dict) or set(state) != _STRICT_RUNNER_STATE_FIELDS:
        actual = sorted(state) if isinstance(state, dict) else type(state).__name__
        raise ValueError(
            "strict runner state schema mismatch: "
            f"expected={sorted(_STRICT_RUNNER_STATE_FIELDS)}, actual={actual}"
        )
    if int(state["runner_state_schema_version"]) != 1:
        raise ValueError("unsupported strict runner state schema")
    if int(state["num_envs"]) != int(num_envs):
        raise ValueError("strict runner state num_envs mismatch")
    for name in ("observations", "states", "prev_state_info", "prev_reward_info"):
        if not isinstance(state[name], (list, tuple)) or len(state[name]) != int(num_envs):
            raise ValueError(f"strict runner field {name} has the wrong environment count")


def _collector_snapshot(collector) -> dict[str, Any]:
    snapshot_fn = getattr(collector, "snapshot_training_state", None)
    if not callable(snapshot_fn):
        raise RuntimeError(
            "strict standalone checkpoint requires collector.snapshot_training_state()"
        )
    snapshot = deepcopy(snapshot_fn())
    if not isinstance(snapshot, dict):
        raise TypeError("collector training snapshot must be a mapping")
    if (
        snapshot.get("snapshot_capability_name")
        != STANDALONE_COLLECTOR_SNAPSHOT_CAPABILITY
        or int(snapshot.get("snapshot_capability_version", -1))
        != STANDALONE_COLLECTOR_SNAPSHOT_VERSION
    ):
        raise ValueError("collector training snapshot capability mismatch")
    return snapshot


def _lazy_module_specs(agent: StandaloneProcessAgent) -> dict[str, Any]:
    assignment = getattr(agent, "assignment_actionability", None)
    assignment_spec = None
    if assignment is not None:
        assignment_spec = {
            "xi_dim": int(assignment.xi_dim),
            "context_dim": int(assignment.context_dim),
            "num_team_codes": int(assignment.num_team_codes),
            "hidden_dim": int(agent.assignment_actionability_cfg.hidden_dim),
        }
    team_effect = getattr(agent, "team_effect_probe", None)
    team_effect_spec = None
    if team_effect is not None:
        team_effect_spec = {
            "target_dims": {
                str(name): int(head[0].normalized_shape[0])
                for name, head in team_effect.heads.items()
            },
            "num_team_codes": int(team_effect.num_team_codes),
            "hidden_dim": int(agent.team_effect_audit_hidden_dim),
            "lr": float(team_effect._lr),
        }
    return {
        "assignment_actionability": assignment_spec,
        "team_effect_probe": team_effect_spec,
    }


def _validate_strict_lazy_module_specs(
    agent: StandaloneProcessAgent,
    specs: Any,
    *,
    modules: dict[str, Any],
    optimizers: dict[str, Any],
    team_effect_optimizer: Any,
) -> None:
    """Validate lazy topology without instantiating or loading any state."""

    required = {"assignment_actionability", "team_effect_probe"}
    if not isinstance(specs, dict) or set(specs) != required:
        raise ValueError("strict lazy-module specification mismatch")

    assignment_spec = specs["assignment_actionability"]
    if assignment_spec is None:
        if modules["assignment_actionability"] is not None or optimizers["q_a_opt"] is not None:
            raise ValueError("assignment-actionability lazy presence mismatch")
    else:
        expected = {"xi_dim", "context_dim", "num_team_codes", "hidden_dim"}
        if not isinstance(assignment_spec, dict) or set(assignment_spec) != expected:
            raise ValueError("assignment-actionability constructor specification mismatch")
        if (
            int(assignment_spec["xi_dim"]) <= 0
            or int(assignment_spec["context_dim"]) < 0
            or int(assignment_spec["num_team_codes"]) != int(agent.num_team_codes)
            or int(assignment_spec["hidden_dim"])
            != int(agent.assignment_actionability_cfg.hidden_dim)
        ):
            raise ValueError("assignment-actionability constructor identity mismatch")
        if modules["assignment_actionability"] is None or optimizers["q_a_opt"] is None:
            raise ValueError("assignment-actionability strict state is incomplete")

    team_effect_spec = specs["team_effect_probe"]
    if team_effect_spec is None:
        if modules["team_effect_probe"] is not None or team_effect_optimizer is not None:
            raise ValueError("team-effect lazy presence mismatch")
    else:
        expected = {"target_dims", "num_team_codes", "hidden_dim", "lr"}
        if not isinstance(team_effect_spec, dict) or set(team_effect_spec) != expected:
            raise ValueError("team-effect constructor specification mismatch")
        target_dims = team_effect_spec["target_dims"]
        if (
            not isinstance(target_dims, dict)
            or not target_dims
            or any(int(value) <= 0 for value in target_dims.values())
            or int(team_effect_spec["num_team_codes"]) != int(agent.num_team_codes)
            or int(team_effect_spec["hidden_dim"])
            != int(agent.team_effect_audit_hidden_dim)
            or not math.isfinite(float(team_effect_spec["lr"]))
            or float(team_effect_spec["lr"]) <= 0.0
        ):
            raise ValueError("team-effect constructor identity mismatch")
        if modules["team_effect_probe"] is None:
            raise ValueError("team-effect strict module state is incomplete")

    current_specs = _lazy_module_specs(agent)
    for name in required:
        if current_specs[name] is not None and current_specs[name] != specs[name]:
            raise ValueError(f"runtime lazy-module identity mismatch for {name}")


def strict_checkpoint_payload(
    agent: StandaloneProcessAgent,
    args: argparse.Namespace,
    config,
    total_steps: int,
    update_idx: int,
    *,
    collector,
    runner_state: dict[str, Any],
) -> dict[str, Any]:
    _validate_runner_state(runner_state, num_envs=int(agent.num_envs))
    payload = checkpoint_payload(agent, args, config, total_steps, update_idx)
    collector_snapshot = _collector_snapshot(collector)
    agent_lifecycle = agent.standalone_lifecycle_state_dict()
    payload["checkpoint_schema_version"] = STANDALONE_STRICT_SCHEMA_VERSION
    payload["resume_semantics"] = STANDALONE_STRICT_RESUME_SEMANTICS
    payload["skill_interval"] = int(agent.skill_interval)
    payload["strict_trajectory"] = {
        "strict_trajectory_schema_version": 1,
        "modules": {
            name: (
                getattr(agent, name).state_dict()
                if getattr(agent, name, None) is not None
                else None
            )
            for name in _STRICT_MODULE_FIELDS
        },
        "optimizers": {
            name: (
                getattr(agent, name).state_dict()
                if getattr(agent, name, None) is not None
                else None
            )
            for name in _STRICT_OPTIMIZER_FIELDS
        },
        "normalizers": {
            name: (
                getattr(agent, name).state_dict()
                if getattr(agent, name, None) is not None
                else None
            )
            for name in _STRICT_NORMALIZER_FIELDS
        },
        "lazy_module_specs": _lazy_module_specs(agent),
        "team_effect_probe_optimizer": (
            agent.team_effect_probe.opt.state_dict()
            if getattr(agent, "team_effect_probe", None) is not None
            and agent.team_effect_probe.opt is not None
            else None
        ),
        "training_contract": effective_training_contract(agent, args, config),
        "agent_lifecycle": agent_lifecycle,
        "collector_snapshot": collector_snapshot,
        "runner_state": deepcopy(runner_state),
        # Capture this last so any snapshot serialization work is excluded from
        # the resumed trajectory's next process-global draw.
        "global_rng": capture_global_rng_state(),
    }
    return payload


def save_training_checkpoint(
    path: Path,
    agent: StandaloneProcessAgent,
    args: argparse.Namespace,
    config,
    total_steps: int,
    update_idx: int,
    *,
    collector,
    runner_state: dict[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        strict_checkpoint_payload(
            agent,
            args,
            config,
            total_steps,
            update_idx,
            collector=collector,
            runner_state=runner_state,
        ),
        path,
    )


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


def _materialize_strict_lazy_modules(
    agent: StandaloneProcessAgent,
    specs: dict[str, Any],
) -> None:
    required = {"assignment_actionability", "team_effect_probe"}
    if not isinstance(specs, dict) or set(specs) != required:
        raise ValueError("strict lazy-module specification mismatch")

    assignment_spec = specs["assignment_actionability"]
    if assignment_spec is not None and getattr(agent, "assignment_actionability", None) is None:
        from ha_ctse_process.assignment_actionability import (
            AssignmentActionabilityDiscriminator,
        )

        expected = {"xi_dim", "context_dim", "num_team_codes", "hidden_dim"}
        if not isinstance(assignment_spec, dict) or set(assignment_spec) != expected:
            raise ValueError("assignment-actionability constructor specification mismatch")
        agent.assignment_actionability = AssignmentActionabilityDiscriminator(
            xi_dim=int(assignment_spec["xi_dim"]),
            context_dim=int(assignment_spec["context_dim"]),
            num_team_codes=int(assignment_spec["num_team_codes"]),
            hidden_dim=int(assignment_spec["hidden_dim"]),
        ).to(agent.device)
        agent.q_a_opt = torch.optim.Adam(
            agent.assignment_actionability.parameters(), lr=1e-3
        )

    team_effect_spec = specs["team_effect_probe"]
    if team_effect_spec is not None and getattr(agent, "team_effect_probe", None) is None:
        from ha_ctse_process.team_effect_targets import TeamEffectTargetProbe

        expected = {"target_dims", "num_team_codes", "hidden_dim", "lr"}
        if not isinstance(team_effect_spec, dict) or set(team_effect_spec) != expected:
            raise ValueError("team-effect constructor specification mismatch")
        agent.team_effect_probe = TeamEffectTargetProbe(
            target_dims={
                str(name): int(value)
                for name, value in dict(team_effect_spec["target_dims"]).items()
            },
            num_team_codes=int(team_effect_spec["num_team_codes"]),
            hidden_dim=int(team_effect_spec["hidden_dim"]),
            lr=float(team_effect_spec["lr"]),
        ).to(agent.device)
        agent._team_effect_prior = torch.full(
            (int(agent.num_team_codes),),
            1.0 / float(agent.num_team_codes),
            device=agent.device,
        )


def _strict_presence_and_load(
    *,
    owner: Any,
    field: str,
    saved_state: Any,
    kind: str,
) -> None:
    target = getattr(owner, field, None)
    if (saved_state is None) != (target is None):
        raise ValueError(
            f"strict {kind} presence mismatch for {field}: "
            f"checkpoint={saved_state is not None}, runtime={target is not None}"
        )
    if target is None:
        return
    if kind == "module":
        target.load_state_dict(saved_state, strict=True)
    else:
        target.load_state_dict(saved_state)


def _load_schema4_agent_state(
    checkpoint: dict[str, Any],
    agent: StandaloneProcessAgent,
    *,
    load_optimizers: bool,
) -> dict[str, Any]:
    if int(checkpoint.get("checkpoint_schema_version", -1)) != STANDALONE_STRICT_SCHEMA_VERSION:
        raise ValueError("strict trajectory resume requires standalone schema-4")
    if checkpoint.get("resume_semantics") != STANDALONE_STRICT_RESUME_SEMANTICS:
        raise ValueError("schema-4 checkpoint has the wrong resume semantics")
    strict_identity = {
        "n_agents": int(agent.n_agents),
        "n_skills": int(agent.n_skills),
        "action_dim": int(agent.action_dim),
        "action_space_type": str(agent.action_space_type),
        "duration_candidates": tuple(int(value) for value in agent.duration_candidates),
        "skill_interval": int(agent.skill_interval),
        "high_controller": str(agent.high_controller),
        "use_recurrent_low_level": bool(agent.use_recurrent_low_level),
        "low_level_architecture": str(agent.low_level_architecture),
    }
    for name, expected in strict_identity.items():
        if name not in checkpoint:
            raise ValueError(f"schema-4 checkpoint is missing identity field {name}")
        actual = checkpoint[name]
        if name == "duration_candidates":
            actual = tuple(int(value) for value in actual)
        elif name in {"n_agents", "n_skills", "action_dim", "skill_interval"}:
            actual = int(actual)
        elif name == "use_recurrent_low_level":
            actual = bool(actual)
        else:
            actual = str(actual)
        if actual != expected:
            raise ValueError(
                f"schema-4 checkpoint identity mismatch for {name}: "
                f"checkpoint={actual!r}, runtime={expected!r}"
            )
    bundle = checkpoint.get("strict_trajectory")
    if not isinstance(bundle, dict):
        raise ValueError("schema-4 checkpoint is missing strict_trajectory")
    required = {
        "strict_trajectory_schema_version",
        "modules",
        "optimizers",
        "normalizers",
        "lazy_module_specs",
        "team_effect_probe_optimizer",
        "training_contract",
        "agent_lifecycle",
        "global_rng",
        "collector_snapshot",
        "runner_state",
    }
    if set(bundle) != required or int(bundle["strict_trajectory_schema_version"]) != 1:
        raise ValueError("schema-4 strict trajectory bundle mismatch")
    modules = bundle["modules"]
    optimizers = bundle["optimizers"]
    normalizers = bundle["normalizers"]
    if not isinstance(modules, dict) or set(modules) != set(_STRICT_MODULE_FIELDS):
        raise ValueError("schema-4 module schema mismatch")
    if not isinstance(optimizers, dict) or set(optimizers) != set(_STRICT_OPTIMIZER_FIELDS):
        raise ValueError("schema-4 optimizer schema mismatch")
    if not isinstance(normalizers, dict) or set(normalizers) != set(_STRICT_NORMALIZER_FIELDS):
        raise ValueError("schema-4 normalizer schema mismatch")

    _validate_strict_lazy_module_specs(
        agent,
        bundle["lazy_module_specs"],
        modules=modules,
        optimizers=optimizers,
        team_effect_optimizer=bundle["team_effect_probe_optimizer"],
    )
    _materialize_strict_lazy_modules(agent, bundle["lazy_module_specs"])
    for name in _STRICT_MODULE_FIELDS:
        _strict_presence_and_load(
            owner=agent, field=name, saved_state=modules[name], kind="module"
        )
    for name in _STRICT_NORMALIZER_FIELDS:
        _strict_presence_and_load(
            owner=agent, field=name, saved_state=normalizers[name], kind="normalizer"
        )
    if load_optimizers:
        for name in _STRICT_OPTIMIZER_FIELDS:
            _strict_presence_and_load(
                owner=agent,
                field=name,
                saved_state=optimizers[name],
                kind="optimizer",
            )
        saved_team_effect_opt = bundle["team_effect_probe_optimizer"]
        team_effect = getattr(agent, "team_effect_probe", None)
        if saved_team_effect_opt is None:
            if team_effect is not None and team_effect.opt is not None:
                raise ValueError("strict team-effect optimizer presence mismatch")
        else:
            if team_effect is None:
                raise ValueError("strict team-effect optimizer lacks its module")
            team_effect._ensure_opt()
            team_effect.opt.load_state_dict(saved_team_effect_opt)
    agent.checkpoint_source_controller = str(checkpoint["high_controller"])
    agent.checkpoint_migration_mode = "strict_schema4_resume"
    agent.checkpoint_migrated_high_keys = tuple(agent.high.state_dict().keys())
    return bundle


def load_training_checkpoint(
    path: str | Path,
    agent: StandaloneProcessAgent,
    *,
    collector,
    args: argparse.Namespace,
    config: Any,
) -> tuple[int, int, dict[str, Any]]:
    checkpoint = torch.load(
        Path(path), map_location=agent.device, weights_only=False
    )
    if int(checkpoint.get("checkpoint_schema_version", -1)) != STANDALONE_STRICT_SCHEMA_VERSION:
        raise ValueError(
            "strict training resume requires standalone schema-4; "
            "older checkpoints are warm-start/evaluation only"
        )
    bundle = checkpoint.get("strict_trajectory")
    if not isinstance(bundle, dict) or "training_contract" not in bundle:
        raise ValueError("schema-4 checkpoint is missing its training contract")
    expected_contract = effective_training_contract(agent, args, config)
    _validate_training_contract(
        bundle["training_contract"],
        expected_contract,
        checkpoint_total_steps=int(checkpoint.get("total_steps", 0)),
    )
    runner_state = deepcopy(bundle["runner_state"])
    _validate_runner_state(runner_state, num_envs=int(agent.num_envs))
    restore_fn = getattr(collector, "restore_training_state", None)
    if not callable(restore_fn):
        raise RuntimeError(
            "strict standalone resume requires collector.restore_training_state(snapshot)"
        )
    collector_snapshot = deepcopy(bundle["collector_snapshot"])
    if (
        not isinstance(collector_snapshot, dict)
        or collector_snapshot.get("snapshot_capability_name")
        != STANDALONE_COLLECTOR_SNAPSHOT_CAPABILITY
        or int(collector_snapshot.get("snapshot_capability_version", -1))
        != STANDALONE_COLLECTOR_SNAPSHOT_VERSION
    ):
        raise ValueError("schema-4 collector snapshot capability mismatch")
    bundle = _load_schema4_agent_state(checkpoint, agent, load_optimizers=True)
    restore_fn(collector_snapshot)
    agent.load_standalone_lifecycle_state_dict(bundle["agent_lifecycle"])
    # Restore process-global streams last: neither deserialization nor collector
    # restoration may consume a draw belonging to the resumed trajectory.
    restore_global_rng_state(bundle["global_rng"])
    return (
        int(checkpoint.get("total_steps", 0)),
        int(checkpoint.get("update_idx", 0)),
        runner_state,
    )


def load_checkpoint(
    path: str | Path,
    agent: StandaloneProcessAgent,
    load_optimizers: bool = True,
) -> tuple[int, int]:
    checkpoint = torch.load(
        Path(path), map_location=agent.device, weights_only=False
    )
    checkpoint_schema = int(checkpoint.get("checkpoint_schema_version", 1))
    if checkpoint_schema == STANDALONE_STRICT_SCHEMA_VERSION:
        if load_optimizers:
            raise ValueError(
                "schema-4 training resume requires load_training_checkpoint(); "
                "load_checkpoint() is evaluation/warm-start only"
            )
        _load_schema4_agent_state(checkpoint, agent, load_optimizers=False)
        return int(checkpoint.get("total_steps", 0)), int(
            checkpoint.get("update_idx", 0)
        )
    if checkpoint_schema == 3:
        raise ValueError("event schema-3 checkpoints require the event checkpoint loader")
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
        agent.process_posterior.load_state_dict(checkpoint["process_posterior"], strict=True)
    if (
        "outcome_residual_probe" in checkpoint
        and checkpoint.get("outcome_residual_probe") is not None
        and getattr(agent, "outcome_residual_probe", None) is not None
    ):
        agent.outcome_residual_probe.load_state_dict(checkpoint["outcome_residual_probe"], strict=True)
    if (
        "topology_role_probe" in checkpoint
        and checkpoint.get("topology_role_probe") is not None
        and getattr(agent, "topology_role_probe", None) is not None
    ):
        agent.topology_role_probe.load_state_dict(checkpoint["topology_role_probe"], strict=True)
    if (
        "transition_discriminator" in checkpoint
        and checkpoint.get("transition_discriminator") is not None
        and getattr(agent, "transition_discriminator", None) is not None
    ):
        agent.transition_discriminator.load_state_dict(checkpoint["transition_discriminator"], strict=True)
    if (
        "prototype_discriminator" in checkpoint
        and checkpoint.get("prototype_discriminator") is not None
        and getattr(agent, "prototype_discriminator", None) is not None
    ):
        agent.prototype_discriminator.load_state_dict(checkpoint["prototype_discriminator"], strict=True)
    if (
        "compact_return_head" in checkpoint
        and checkpoint.get("compact_return_head") is not None
        and getattr(agent, "compact_return_head", None) is not None
    ):
        agent.compact_return_head.load_state_dict(checkpoint["compact_return_head"], strict=True)
    if (
        "situation_hazard" in checkpoint
        and checkpoint.get("situation_hazard") is not None
        and getattr(agent, "situation_hazard", None) is not None
    ):
        agent.situation_hazard.load_state_dict(checkpoint["situation_hazard"], strict=True)
    if (
        "team_transition" in checkpoint
        and checkpoint.get("team_transition") is not None
        and getattr(agent, "team_transition", None) is not None
    ):
        agent.team_transition.load_state_dict(checkpoint["team_transition"], strict=True)
    if (
        "team_discriminator" in checkpoint
        and checkpoint.get("team_discriminator") is not None
        and getattr(agent, "team_discriminator", None) is not None
    ):
        agent.team_discriminator.load_state_dict(checkpoint["team_discriminator"], strict=True)
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
                agent.high_opt.load_state_dict(checkpoint["high_opt"])
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
        if "process_opt" in checkpoint:
            agent.process_opt.load_state_dict(checkpoint["process_opt"])
        if (
            "prototype_disc_opt" in checkpoint
            and checkpoint.get("prototype_disc_opt") is not None
            and getattr(agent, "prototype_disc_opt", None) is not None
        ):
            agent.prototype_disc_opt.load_state_dict(checkpoint["prototype_disc_opt"])
        if (
            "team_transition_opt" in checkpoint
            and checkpoint.get("team_transition_opt") is not None
            and getattr(agent, "team_transition_opt", None) is not None
        ):
            agent.team_transition_opt.load_state_dict(checkpoint["team_transition_opt"])
        if (
            "team_disc_opt" in checkpoint
            and checkpoint.get("team_disc_opt") is not None
            and getattr(agent, "team_disc_opt", None) is not None
        ):
            agent.team_disc_opt.load_state_dict(checkpoint["team_disc_opt"])
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
            "has_event_semantic": "event_semantic" in event,
        }
    manifest = _load_adjacent_run_manifest(path)

    def meta(name: str) -> Any:
        return checkpoint.get(name) if name in checkpoint else _manifest_lookup(manifest, name)

    return {
        "checkpoint_schema_version": checkpoint.get("checkpoint_schema_version", 1),
        "resume_semantics": checkpoint.get("resume_semantics"),
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
