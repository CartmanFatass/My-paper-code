"""Optimizer ownership for the frozen noncalendar commitment benchmark."""

from __future__ import annotations

import base64
import binascii
from copy import deepcopy
from dataclasses import replace
import hashlib
import math
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
from ha_ctse_process.dynamic_roster_testbed import ACTION_COUNT
from ha_ctse_process import event_commitment_evidence_common
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
    MARK_DIM,
    TrainingState,
)
from ha_ctse_process.noncalendar_commitment_testbed import (
    ADDED_PARAMETER_COUNT,
    FORMAL_UPDATES,
    OPTIMIZER_CLIP_EPSILON,
    OPTIMIZER_EVIDENCE_SCHEMA_VERSION,
    OPTIMIZER_LOSS_ATOL,
    OPTIMIZER_LOSS_RTOL,
    OPTIMIZER_NORM_ATOL,
    OPTIMIZER_NORM_RTOL,
    PARAMETER_COUNT,
    PRIMITIVE_ENTROPY_COEFFICIENT,
    VALUE_COEFFICIENT,
)


EVENT_ENTROPY_COEFFICIENT = 0.01

_BASE_PARAMETER_SPECS = (
    ("base.member_encoder.0.weight", (32, 15)),
    ("base.member_encoder.0.bias", (32,)),
    ("base.member_encoder.2.weight", (32, 32)),
    ("base.member_encoder.2.bias", (32,)),
    ("base.context_encoder.0.weight", (32, 33)),
    ("base.context_encoder.0.bias", (32,)),
    ("base.actor_rnn.weight_ih", (96, 67)),
    ("base.actor_rnn.weight_hh", (96, 32)),
    ("base.actor_rnn.bias_ih", (96,)),
    ("base.actor_rnn.bias_hh", (96,)),
    ("base.action_head.0.weight", (32, 35)),
    ("base.action_head.0.bias", (32,)),
    ("base.action_head.2.weight", (3, 32)),
    ("base.action_head.2.bias", (3,)),
    ("base.critic.0.weight", (32, 41)),
    ("base.critic.0.bias", (32,)),
    ("base.critic.2.weight", (1, 32)),
    ("base.critic.2.bias", (1,)),
)
_COMMITMENT_BASE_SPECS = (("W_z.weight", (3, 8)),)
_EVENT_PARAMETER_SPECS = (
    ("event_head.weight", (2, 87)),
    ("event_head.bias", (2,)),
    ("mark_head.weight", (16, 87)),
    ("mark_head.bias", (16,)),
)


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


def _expected_parameter_counts(arm: str) -> dict[str, int]:
    commitment_bias = MARK_DIM * ACTION_COUNT if arm != "OR" else 0
    return {
        "base_model": PARAMETER_COUNT,
        "added_model": 0 if arm == "OR" else ADDED_PARAMETER_COUNT,
        "base_optimizer": PARAMETER_COUNT + commitment_bias,
        "event_optimizer": (
            0 if arm == "OR" else ADDED_PARAMETER_COUNT - commitment_bias
        ),
    }


def _expected_optimizer_manifest(arm: str) -> dict[str, Any]:
    def records(specs: tuple[tuple[str, tuple[int, ...]], ...]) -> list[dict[str, Any]]:
        return [
            {
                "name": name,
                "shape": list(shape),
                "numel": int(math.prod(shape)),
            }
            for name, shape in specs
        ]

    base_specs = _BASE_PARAMETER_SPECS + (
        _COMMITMENT_BASE_SPECS if arm != "OR" else ()
    )
    return {
        "schema_version": OPTIMIZER_EVIDENCE_SCHEMA_VERSION,
        "arm": arm,
        "groups": {
            "base": records(base_specs),
            "event": records(_EVENT_PARAMETER_SPECS if arm != "OR" else ()),
        },
    }


def _optimizer_pass_valid(
    record: Any, *, group: str, pass_index: int, step_before: int,
    manifest: list[dict[str, Any]],
) -> tuple[bool, dict[str, int]]:
    required = {
        "schema_version", "group", "pass_index", "step_before", "step_after",
        "raw_loss", "loss_components", "unclipped_norm", "clip_coefficient",
        "parameters", "payload_raw_bytes", "payload_encoded_bytes",
        "record_digest",
    }
    if not isinstance(record, dict) or set(record) != required:
        return False, {}
    unsigned = {key: deepcopy(value) for key, value in record.items()
                if key != "record_digest"}
    if not (
        record["schema_version"] == OPTIMIZER_EVIDENCE_SCHEMA_VERSION
        and record["group"] == group
        and int(record["pass_index"]) == pass_index
        and int(record["step_before"]) == step_before
        and int(record["step_after"]) == step_before + 1
        and record["record_digest"]
        == event_commitment_evidence_common._digest_json(unsigned)
        and isinstance(record["parameters"], list)
        and len(record["parameters"]) == len(manifest)
    ):
        return False, {}
    loss = float(record["raw_loss"])
    norm = float(record["unclipped_norm"])
    coefficient = float(record["clip_coefficient"])
    if not all(math.isfinite(value) for value in (loss, norm, coefficient)):
        return False, {}
    components = record["loss_components"]
    if group == "base":
        if not isinstance(components, dict) or set(components) != {
            "policy_loss", "value_loss", "primitive_entropy"
        }:
            return False, {}
        recomputed_loss = (
            float(components["policy_loss"])
            + VALUE_COEFFICIENT * float(components["value_loss"])
            - PRIMITIVE_ENTROPY_COEFFICIENT * float(components["primitive_entropy"])
        )
    else:
        if not isinstance(components, dict) or set(components) != {
            "event_policy_loss", "categorical_entropy"
        }:
            return False, {}
        recomputed_loss = (
            float(components["event_policy_loss"])
            - EVENT_ENTROPY_COEFFICIENT * float(components["categorical_entropy"])
        )
    if not (
        all(math.isfinite(float(value)) for value in components.values())
        and math.isclose(
            loss, recomputed_loss,
            rel_tol=OPTIMIZER_LOSS_RTOL, abs_tol=OPTIMIZER_LOSS_ATOL,
        )
    ):
        return False, {}
    if norm < 0.0:
        return False, {}
    expected_coefficient = min(
        1.0, 0.5 / (norm + OPTIMIZER_CLIP_EPSILON)
    )
    if coefficient != expected_coefficient:
        return False, {}
    squared_sum = 0.0
    non_none = zero_tensors = nonfinite_values = 0
    parameter_keys = {
        "name", "shape", "numel", "dtype", "gradient_present",
        "nonfinite_count", "zero_count", "squared_l2", "maxabs",
        "preclip_gradient_digest",
        "gradient_payload",
    }
    raw_bytes = encoded_bytes = 0
    for summary, owner in zip(record["parameters"], manifest, strict=True):
        if not isinstance(summary, dict) or set(summary) != parameter_keys:
            return False, {}
        try:
            numel = int(summary["numel"])
            nonfinite = int(summary["nonfinite_count"])
            zeros = int(summary["zero_count"])
            squared = float(summary["squared_l2"])
            maximum = float(summary["maxabs"])
        except (TypeError, ValueError, OverflowError):
            return False, {}
        payload = summary["gradient_payload"]
        if summary["gradient_present"] is not True or not isinstance(payload, dict) or set(payload) != {
            "encoding", "dtype", "shape", "uncompressed_nbytes", "data"
        }:
            return False, {}
        try:
            compressed = base64.b64decode(payload["data"], validate=True)
            raw = zlib.decompress(compressed)
            array = np.frombuffer(raw, dtype=np.dtype(payload["dtype"])).reshape(
                tuple(int(value) for value in payload["shape"])
            )
        except (ValueError, TypeError, zlib.error, binascii.Error):
            return False, {}
        derived_nonfinite = int((~np.isfinite(array)).sum())
        derived_zeros = int((array == 0).sum())
        derived_squared = float(np.square(array.astype(np.float64)).sum())
        derived_maximum = float(np.abs(array.astype(np.float64)).max()) if array.size else 0.0
        derived_digest = hashlib.sha256(raw).hexdigest()
        raw_bytes += len(raw)
        encoded_bytes += len(payload["data"].encode("ascii"))
        if not (
            summary["name"] == owner["name"]
            and summary["shape"] == owner["shape"]
            and numel == owner["numel"]
            and summary["dtype"] == "<f4"
            and payload["encoding"] == "zlib9_base64"
            and payload["dtype"] == "<f4"
            and payload["shape"] == owner["shape"]
            and int(payload["uncompressed_nbytes"]) == owner["numel"] * 4
            and len(raw) == owner["numel"] * 4
            and 0 <= nonfinite <= numel
            and 0 <= zeros <= numel
            and nonfinite == 0
            and math.isfinite(squared) and squared >= 0.0
            and math.isfinite(maximum) and maximum >= 0.0
            and _is_sha256(summary["preclip_gradient_digest"])
            and nonfinite == derived_nonfinite
            and zeros == derived_zeros
            and squared == derived_squared
            and maximum == derived_maximum
            and summary["preclip_gradient_digest"] == derived_digest
            and ((zeros == numel) == (squared == 0.0 and maximum == 0.0))
        ):
            return False, {}
        squared_sum += squared
        non_none += 1
        zero_tensors += int(zeros == numel)
        nonfinite_values += nonfinite
    if not (
        int(record["payload_raw_bytes"]) == raw_bytes
        and int(record["payload_encoded_bytes"]) == encoded_bytes
    ):
        return False, {}
    recomputed_norm = math.sqrt(squared_sum)
    if not math.isclose(
        norm, recomputed_norm,
        rel_tol=OPTIMIZER_NORM_RTOL, abs_tol=OPTIMIZER_NORM_ATOL,
    ):
        return False, {}
    return True, {
        "non_none": non_none,
        "zero_tensors": zero_tensors,
        "nonfinite_values": nonfinite_values,
    }


def _is_sha256(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


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
