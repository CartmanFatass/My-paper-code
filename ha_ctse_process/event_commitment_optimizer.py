"""Optimizer ownership for the frozen noncalendar commitment benchmark."""

from __future__ import annotations

import base64
from dataclasses import replace
import hashlib
from typing import Any, Mapping
import zlib

import numpy as np
import torch
from torch import nn

from ha_ctse_process.dynamic_roster_direct import (
    ENTROPY_COEFFICIENT,
    GAE_LAMBDA,
    GAMMA,
    GRADIENT_CLIP,
    PPO_CLIP,
    PPO_PASSES,
    VALUE_CLIP,
    VALUE_COEFFICIENT,
)
from ha_ctse_process.event_commitment_collector import CREATE, KEEP, RENEW
from ha_ctse_process.event_commitment_replay import (
    _replay_event_heads,
    _replay_primitive,
    validate_replay,
)
from ha_ctse_process.event_commitment_rng import _canonical_json_digest
from ha_ctse_process.event_commitment_types import (
    CommitmentArm,
    EventTrajectory,
    TrainingState,
)
from ha_ctse_process.noncalendar_commitment_testbed import (
    FORMAL_UPDATES,
    OPTIMIZER_CLIP_EPSILON,
    OPTIMIZER_EVIDENCE_SCHEMA_VERSION,
)


EVENT_ENTROPY_COEFFICIENT = 0.01


def _pack_trajectory_once(trajectory: EventTrajectory, device: torch.device) -> EventTrajectory:
    """Transfer the collected tensor package once and reuse it for all epochs."""

    tensor_fields = (
        "observations", "active_mask", "orders", "actions", "old_log_probs",
        "old_values", "rewards", "terminal", "hidden_before", "hidden_after",
        "prefix_counts", "primitive_z", "event_kind", "event_inputs",
        "event_categorical_actions", "event_u", "event_new_z", "event_cat_mask",
        "event_mark_mask", "event_old_cat_logp", "event_old_mark_component_logp",
        "event_old_joint_logp", "event_z_pre", "candidate_u", "candidate_z",
        "membership_epoch", "segment_id", "q_before",
        "bootstrap_values",
    )
    return replace(
        trajectory,
        **{name: getattr(trajectory, name).to(device) for name in tensor_fields},
    )


def compute_gae(trajectory: EventTrajectory, *, device: torch.device) -> tuple[torch.Tensor, torch.Tensor]:
    rewards = trajectory.rewards.to(device); values = trajectory.old_values.to(device); terminal = trajectory.terminal.to(device); advantages = torch.zeros_like(rewards); running = torch.zeros(rewards.shape[1], device=device); next_value = trajectory.bootstrap_values.to(device)
    for time in reversed(range(rewards.shape[0])):
        continuation = (~terminal[time]).to(rewards.dtype); delta = rewards[time] + GAMMA * next_value * continuation - values[time]; running = delta + GAMMA * GAE_LAMBDA * continuation * running; advantages[time] = running; next_value = values[time]
    returns = advantages + values; return (advantages - advantages.mean()) / advantages.std(unbiased=False).clamp_min(1e-8), returns


def optimizer_ownership_manifest(arm: CommitmentArm) -> dict[str, Any]:
    """Canonical ordered optimizer ownership for the frozen arm architecture."""

    names = {id(parameter): name for name, parameter in arm.named_parameters()}

    def group(parameters: list[nn.Parameter]) -> list[dict[str, Any]]:
        return [
            {
                "name": names[id(parameter)],
                "shape": [int(value) for value in parameter.shape],
                "numel": int(parameter.numel()),
            }
            for parameter in parameters
        ]

    return {
        "schema_version": OPTIMIZER_EVIDENCE_SCHEMA_VERSION,
        "arm": arm.arm,
        "groups": {
            "base": group(arm.base_optimizer_parameters()),
            "event": group(arm.event_parameters()),
        },
    }


def _gradient_summaries(
    arm: CommitmentArm, parameters: list[nn.Parameter]
) -> list[dict[str, Any]]:
    names = {id(parameter): name for name, parameter in arm.named_parameters()}
    summaries: list[dict[str, Any]] = []
    for parameter in parameters:
        gradient = parameter.grad
        present = gradient is not None
        if gradient is None:
            nonfinite = zero = 0
            squared_l2 = maxabs = 0.0
            digest = hashlib.sha256(b"").hexdigest()
            dtype = "<f4"
            payload = None
        else:
            contiguous = gradient.detach().contiguous()
            cpu = contiguous.cpu()
            array = np.asarray(
                cpu.numpy(), dtype=np.dtype(cpu.numpy().dtype).newbyteorder("<"),
                order="C",
            )
            raw = array.tobytes(order="C")
            widened = array.astype(np.float64)
            nonfinite = int((~np.isfinite(array)).sum())
            zero = int((array == 0).sum())
            squared_l2 = float(np.square(widened).sum())
            maxabs = float(np.abs(widened).max()) if array.size else 0.0
            encoded = base64.b64encode(zlib.compress(raw, level=9)).decode("ascii")
            digest = hashlib.sha256(raw).hexdigest()
            dtype = array.dtype.str
            payload = {
                "encoding": "zlib9_base64", "dtype": dtype,
                "shape": [int(value) for value in parameter.shape],
                "uncompressed_nbytes": len(raw), "data": encoded,
            }
        summaries.append({
            "name": names[id(parameter)],
            "shape": [int(value) for value in parameter.shape],
            "numel": int(parameter.numel()),
            "dtype": dtype,
            "gradient_present": bool(present),
            "nonfinite_count": nonfinite,
            "zero_count": zero,
            "squared_l2": squared_l2,
            "maxabs": maxabs,
            "preclip_gradient_digest": digest,
            "gradient_payload": payload,
        })
    return summaries


def _optimizer_pass_record(
    *, group: str, pass_index: int, step_before: int,
    loss: torch.Tensor, summaries: list[dict[str, Any]],
    loss_components: Mapping[str, float],
    unclipped_norm: torch.Tensor,
) -> dict[str, Any]:
    norm = float(unclipped_norm.detach().cpu())
    clip_coefficient = min(1.0, GRADIENT_CLIP / (norm + OPTIMIZER_CLIP_EPSILON))
    record = {
        "schema_version": OPTIMIZER_EVIDENCE_SCHEMA_VERSION,
        "group": group,
        "pass_index": int(pass_index),
        "step_before": int(step_before),
        "step_after": int(step_before) + 1,
        "raw_loss": float(loss.detach().cpu()),
        "loss_components": dict(loss_components),
        "unclipped_norm": norm,
        "clip_coefficient": clip_coefficient,
        "parameters": summaries,
        "payload_raw_bytes": sum(
            int(value["gradient_payload"]["uncompressed_nbytes"])
            for value in summaries if value["gradient_payload"] is not None
        ),
        "payload_encoded_bytes": sum(
            len(value["gradient_payload"]["data"].encode("ascii"))
            for value in summaries if value["gradient_payload"] is not None
        ),
    }
    record["record_digest"] = _canonical_json_digest(record)
    return record


def optimize_update(
    arm: CommitmentArm,
    base_optimizer: torch.optim.Optimizer,
    event_optimizer: torch.optim.Optimizer | None,
    state: TrainingState,
    trajectory: EventTrajectory,
    *,
    device: torch.device,
    ppo_passes: int = PPO_PASSES,
) -> dict[str, Any]:
    if trajectory.cutoff:
        raise ValueError("updates require a complete episode rollout")
    packed = _pack_trajectory_once(trajectory, device)
    arm.train()
    _validated_replay, replay_evidence = validate_replay(
        arm, packed, device=device
    )
    advantages, returns = compute_gae(packed, device=device)
    active = packed.active_mask
    old_logp = packed.old_log_probs
    old_values = packed.old_values
    event_mask = packed.event_kind.eq(CREATE) | packed.event_kind.eq(KEEP) | packed.event_kind.eq(RENEW)
    old_joint = packed.event_old_joint_logp
    has_categorical_events = bool(
        (packed.event_kind.eq(KEEP) | packed.event_kind.eq(RENEW)).any().detach().cpu()
    )
    metrics: dict[str, Any] = {
        "replay": replay_evidence,
        "base_steps": 0,
        "event_steps": 0,
        "primitive_replays": 0,
        "event_head_replays": 0,
        "packed_trajectory_count": 1,
        "base_non_none_gradients": [],
        "base_zero_gradients": [],
        "base_nonfinite_gradient_values": [],
        "base_nonfinite_loss_values": [],
        "base_nonfinite_norm_values": [],
        "event_non_none_gradients": [],
        "event_zero_gradients": [],
        "event_nonfinite_gradient_values": [],
        "event_nonfinite_loss_values": [],
        "event_nonfinite_norm_values": [],
        "ownership_manifest": optimizer_ownership_manifest(arm),
        "base_passes": [],
        "event_passes": [],
    }
    for pass_index in range(int(ppo_passes)):
        primitive = _replay_primitive(arm, packed, device=device)
        metrics["primitive_replays"] += 1
        ratio = torch.exp(primitive[0] - old_logp)
        expanded_advantage = advantages.unsqueeze(-1)
        surrogate = torch.minimum(
            ratio * expanded_advantage,
            torch.clamp(ratio, 1.0 - PPO_CLIP, 1.0 + PPO_CLIP)
            * expanded_advantage,
        )
        counts = active.sum(-1).clamp_min(1)
        policy_loss = -(
            torch.where(active, surrogate, 0.0).sum(-1) / counts
        ).mean()
        entropy = (
            torch.where(active, primitive[1], 0.0).sum(-1) / counts
        ).mean()
        clipped_values = old_values + torch.clamp(
            primitive[2] - old_values, -VALUE_CLIP, VALUE_CLIP
        )
        value_loss = torch.maximum(
            (primitive[2] - returns).square(),
            (clipped_values - returns).square(),
        ).mean()
        base_loss = (
            policy_loss + VALUE_COEFFICIENT * value_loss
            - ENTROPY_COEFFICIENT * entropy
        )
        base_optimizer.zero_grad(set_to_none=True)
        base_loss.backward()
        base_parameters = arm.base_optimizer_parameters()
        base_gradient_evidence = _gradient_summaries(
            arm, base_parameters
        )
        base_norm = torch.nn.utils.clip_grad_norm_(base_parameters, GRADIENT_CLIP)
        metrics["base_nonfinite_loss_values"].append(
            int((~torch.isfinite(base_loss)).sum().detach().cpu())
        )
        metrics["base_nonfinite_norm_values"].append(
            int((~torch.isfinite(base_norm)).sum().detach().cpu())
        )
        metrics["base_non_none_gradients"].append(
            sum(parameter.grad is not None for parameter in base_parameters)
        )
        metrics["base_zero_gradients"].append(
            sum(
                parameter.grad is not None
                and bool(torch.count_nonzero(parameter.grad).eq(0).detach().cpu())
                for parameter in base_parameters
            )
        )
        metrics["base_nonfinite_gradient_values"].append(sum(
            int((~torch.isfinite(parameter.grad)).sum().detach().cpu())
            for parameter in base_parameters if parameter.grad is not None
        ))
        base_record = _optimizer_pass_record(
            group="base", pass_index=pass_index + 1,
            step_before=state.base_optimizer_steps + metrics["base_steps"],
            loss=base_loss, summaries=base_gradient_evidence,
            loss_components={
                "policy_loss": float(policy_loss.detach().cpu()),
                "value_loss": float(value_loss.detach().cpu()),
                "primitive_entropy": float(entropy.detach().cpu()),
            },
            unclipped_norm=base_norm,
        )
        metrics["base_passes"].append(base_record)
        base_optimizer.step()
        metrics["base_steps"] += 1

        if event_optimizer is not None:
            events = _replay_event_heads(
                arm, packed, device=device, contexts=None
            )
            metrics["event_head_replays"] += 1
            event_advantage = advantages.unsqueeze(-1).expand_as(event_mask)[event_mask]
            event_ratio = torch.exp(events[7][event_mask] - old_joint[event_mask])
            event_surrogate = torch.minimum(
                event_ratio * event_advantage,
                torch.clamp(event_ratio, 1.0 - PPO_CLIP, 1.0 + PPO_CLIP)
                * event_advantage,
            )
            categorical_mask = events[1]
            categorical_entropy = (
                events[8][categorical_mask].mean()
                if has_categorical_events
                else torch.zeros((), device=device)
            )
            event_loss = (
                -event_surrogate.mean()
                - EVENT_ENTROPY_COEFFICIENT * categorical_entropy
            )
            event_optimizer.zero_grad(set_to_none=True)
            event_loss.backward()
            event_parameters = arm.event_parameters()
            event_gradient_evidence = _gradient_summaries(
                arm, event_parameters
            )
            event_norm = torch.nn.utils.clip_grad_norm_(
                event_parameters, GRADIENT_CLIP
            )
            metrics["event_nonfinite_loss_values"].append(
                int((~torch.isfinite(event_loss)).sum().detach().cpu())
            )
            metrics["event_nonfinite_norm_values"].append(
                int((~torch.isfinite(event_norm)).sum().detach().cpu())
            )
            metrics["event_non_none_gradients"].append(
                sum(parameter.grad is not None for parameter in event_parameters)
            )
            metrics["event_zero_gradients"].append(
                sum(
                    parameter.grad is not None
                    and bool(torch.count_nonzero(parameter.grad).eq(0).detach().cpu())
                    for parameter in event_parameters
                )
            )
            metrics["event_nonfinite_gradient_values"].append(sum(
                int((~torch.isfinite(parameter.grad)).sum().detach().cpu())
                for parameter in event_parameters if parameter.grad is not None
            ))
            event_record = _optimizer_pass_record(
                group="event", pass_index=pass_index + 1,
                step_before=state.event_optimizer_steps + metrics["event_steps"],
                loss=event_loss, summaries=event_gradient_evidence,
                loss_components={
                    "event_policy_loss": float((-event_surrogate.mean()).detach().cpu()),
                    "categorical_entropy": float(categorical_entropy.detach().cpu()),
                },
                unclipped_norm=event_norm,
            )
            metrics["event_passes"].append(event_record)
            event_optimizer.step()
            metrics["event_steps"] += 1
    if metrics["primitive_replays"] != int(ppo_passes):
        raise RuntimeError("primitive replay count drift")
    all_passes = metrics["base_passes"] + metrics["event_passes"]
    encoded_bytes = sum(int(value["payload_encoded_bytes"]) for value in all_passes)
    raw_bytes = sum(int(value["payload_raw_bytes"]) for value in all_passes)
    metrics["evidence_storage"] = {
        "raw_bytes": raw_bytes,
        "encoded_bytes": encoded_bytes,
        "formal_scale_projected_encoded_bytes": encoded_bytes * FORMAL_UPDATES,
    }
    state.completed_update += 1
    state.base_optimizer_steps += int(ppo_passes)
    state.event_optimizer_steps += int(
        ppo_passes if event_optimizer is not None else 0
    )
    return metrics
