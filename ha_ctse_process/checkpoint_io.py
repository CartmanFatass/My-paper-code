"""Checkpoint persistence for the standalone HA-CTSE process core."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import torch

from ha_ctse_process.r29_action_information_reward import (
    REWARD_CLIP as R29_ACTION_INFO_REWARD_CLIP,
    REWARD_COEF as R29_ACTION_INFO_REWARD_COEF,
)
from ha_ctse_process.standalone_agent import StandaloneProcessAgent


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
            "has_event_semantic": "event_semantic" in event,
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
