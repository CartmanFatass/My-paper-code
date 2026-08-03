"""Ragged active-only batching for variable-roster event low-policy steps."""

from __future__ import annotations

from typing import Sequence

import numpy as np
import torch

from ha_ctse_process.variable_roster_event import (
    SUPPLIED_EXECUTOR_RUNTIME,
    VariableRosterEventCore,
)
from ha_ctse_process.variable_roster_event_types import (
    ActiveRoutingView,
    BatchedLowStepResult,
    BoundarySnapshot,
    PackedActiveBatch,
)


def batched_low_step(
    cores: Sequence[VariableRosterEventCore],
    snapshots: Sequence[BoundarySnapshot],
    *,
    deterministic: bool = False,
) -> BatchedLowStepResult:
    """Run one ragged active-only low step across all environments.

    RNG draws are still made one core at a time in input order, exactly as in
    the scalar loop.  Model calls and device-to-host ledger transfers are
    combined across the ragged active rows.
    """

    core_rows = tuple(cores)
    snapshot_rows = tuple(snapshots)
    if not core_rows or len(core_rows) != len(snapshot_rows):
        raise ValueError("batched low step requires one snapshot per core")
    if any(core.runtime_mode == SUPPLIED_EXECUTOR_RUNTIME for core in core_rows):
        raise RuntimeError(
            "batched low policy step is unavailable in supplied-executor/no-low-path mode"
        )
    owner = core_rows[0]
    if any(
        core.low_actor is not owner.low_actor or core.low_critic is not owner.low_critic
        for core in core_rows
    ):
        raise ValueError("batched low step requires one shared low parameter graph")
    if any(core.device != owner.device for core in core_rows):
        raise ValueError("batched low step requires one shared device")
    if any(core.action_space_type != owner.action_space_type for core in core_rows):
        raise ValueError("batched low step requires one action-space type")

    packed_rows: list[PackedActiveBatch] = []
    routing_rows: list[ActiveRoutingView] = []
    actor_hidden_before_rows: list[torch.Tensor] = []
    critic_hidden_before_rows: list[torch.Tensor] = []
    uniform_rows: list[np.ndarray] = []
    offsets = [0]
    for core, snapshot in zip(core_rows, snapshot_rows):
        packed, routing = core.pack_active(snapshot)
        if bool(torch.any(packed.skills < 0).item()):
            raise RuntimeError("low actor cannot run before genuine joins receive SET")
        packed_rows.append(packed)
        routing_rows.append(routing)
        actor_hidden_before_rows.append(packed.low_actor_hidden.clone())
        critic_hidden_before_rows.append(packed.low_critic_hidden.clone())
        if not deterministic and owner.action_space_type == "discrete":
            uniform_rows.append(
                np.asarray(
                    core.action_rng.random(len(routing.lifecycle_keys)),
                    dtype=np.float64,
                )
            )
        offsets.append(offsets[-1] + len(routing.lifecycle_keys))

    member_obs = torch.cat([packed.member_obs for packed in packed_rows], dim=0)
    critic_member_features = torch.cat(
        [packed.critic_member_features for packed in packed_rows], dim=0
    )
    skills = torch.cat([packed.skills for packed in packed_rows], dim=0)
    actor_hidden_before = torch.cat(actor_hidden_before_rows, dim=0)
    critic_hidden_before = torch.cat(critic_hidden_before_rows, dim=0)
    global_features = torch.cat(
        [packed.critic_global_features for packed in packed_rows], dim=0
    )
    env_ptr = torch.as_tensor(offsets, dtype=torch.long, device=owner.device)
    sampling_uniforms = (
        np.concatenate(uniform_rows, axis=0) if uniform_rows else None
    )
    with torch.no_grad():
        actions, logp, actor_hidden = owner.low_actor.actor_step(
            member_obs,
            skills,
            actor_hidden_before,
            deterministic=deterministic,
            sampling_uniforms=sampling_uniforms,
        )
        values, critic_hidden, critic_source = owner.low_critic.critic_step(
            critic_member_features,
            skills,
            env_ptr,
            global_features,
            critic_hidden_before,
        )

    bulk_cpu = {
        "member_obs": member_obs.detach().cpu().numpy(),
        "skills": skills.detach().cpu().numpy(),
        "critic_member_features": critic_member_features.detach().cpu().numpy(),
        "critic_global_features": global_features.detach().cpu().numpy(),
        "actor_hidden_before": actor_hidden_before.detach().cpu().numpy(),
        "critic_hidden_before": critic_hidden_before.detach().cpu().numpy(),
        "actions": actions.detach().cpu().numpy(),
        "logp": logp.detach().cpu().numpy(),
        "values": values.detach().cpu().numpy(),
        "actor_hidden": actor_hidden.detach().cpu().numpy(),
        "critic_hidden": critic_hidden.detach().cpu().numpy(),
        "critic_source": critic_source.detach().cpu().numpy(),
    }
    per_core: list[tuple[torch.Tensor, torch.Tensor, torch.Tensor]] = []
    routed_actions: list[dict[str, int]] = []
    for core_index, (core, packed, routing) in enumerate(
        zip(core_rows, packed_rows, routing_rows)
    ):
        start, end = offsets[core_index], offsets[core_index + 1]
        core_uniforms = (
            None
            if sampling_uniforms is None
            else sampling_uniforms[start:end]
        )
        cpu = {
            "member_obs": bulk_cpu["member_obs"][start:end],
            "skills": bulk_cpu["skills"][start:end],
            "critic_member_features": bulk_cpu["critic_member_features"][start:end],
            "critic_global_features": bulk_cpu["critic_global_features"][
                core_index : core_index + 1
            ],
            "actor_hidden_before": bulk_cpu["actor_hidden_before"][start:end],
            "critic_hidden_before": bulk_cpu["critic_hidden_before"][start:end],
            "actions": bulk_cpu["actions"][start:end],
            "logp": bulk_cpu["logp"][start:end],
            "values": bulk_cpu["values"][start:end],
            "actor_hidden": bulk_cpu["actor_hidden"][start:end],
            "critic_hidden": bulk_cpu["critic_hidden"][start:end],
            "critic_source": bulk_cpu["critic_source"][start:end],
        }
        result = core._record_low_step(
            packed=packed,
            routing=routing,
            actions=actions[start:end],
            logp=logp[start:end],
            values=values[start:end],
            actor_hidden=actor_hidden[start:end],
            critic_hidden=critic_hidden[start:end],
            critic_source=critic_source[start:end],
            actor_hidden_before=actor_hidden_before[start:end],
            critic_hidden_before=critic_hidden_before[start:end],
            sampling_uniforms=core_uniforms,
            cpu=cpu,
        )
        per_core.append(result)
        if owner.action_space_type != "discrete":
            raise ValueError("Stage C routed actions require a discrete low policy")
        routed_actions.append(
            {
                key: int(np.asarray(cpu["actions"][index]).reshape(-1)[0])
                for index, key in enumerate(routing.lifecycle_keys)
            }
        )
    return BatchedLowStepResult(tuple(per_core), tuple(routed_actions))
