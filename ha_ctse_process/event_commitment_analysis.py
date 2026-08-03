"""Analysis ownership for noncalendar event-commitment trajectories."""

from __future__ import annotations

import torch
import torch.nn.functional as F

from ha_ctse_process.dynamic_roster_testbed import ACTION_COUNT, OBSERVATION_DIM
from ha_ctse_process.event_commitment_collector import CREATE, KEEP, RENEW
from ha_ctse_process.event_commitment_types import (
    CommitmentArm,
    EventTrajectory,
    MARK_DIM,
)


def action_distribution_tv(
    logits_natural: torch.Tensor, logits_perm: torch.Tensor
) -> torch.Tensor:
    """Primitive action-distribution total variation from two logit vectors.

    `I_TV = 0.5 * sum_a |pi(a) - pi(a_perm)|`, where `pi`/`pi_perm` are the
    softmax distributions induced by `logits_natural`/`logits_perm` along
    their last dimension. This is exactly zero whenever the two logit
    vectors differ only by a constant (softmax is shift-invariant), and it
    always lies in `[0, 1]` because it is the total-variation distance
    between two categorical distributions over the same three actions.
    """

    pi_natural = torch.softmax(logits_natural, dim=-1)
    pi_perm = torch.softmax(logits_perm, dim=-1)
    return 0.5 * torch.abs(pi_natural - pi_perm).sum(dim=-1)


def batched_natural_and_permuted_action_tv(
    arm: CommitmentArm,
    trajectory: EventTrajectory,
    *,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Trajectory-batched teacher-forced `I_TV` with one AR-position loop.

    Time and environment are flattened into one batch. The only loop is the
    genuine autoregressive primitive position; focal-key gathers, prefix
    updates, ascending-key cyclic mark permutation and both W_z evaluations
    remain on device. The returned dense tensor and eligibility mask have
    shape `(time, environment, lifecycle)` and perform no host conversion.
    """

    shape = trajectory.active_mask.shape
    if arm.arm != "EHC" or arm.W_z is None:
        return (
            torch.zeros(shape, dtype=torch.float32, device=device),
            torch.zeros(shape, dtype=torch.bool, device=device),
        )
    time_steps, environments, lifecycles = shape
    batch = time_steps * environments
    observations = trajectory.observations.to(device).reshape(
        batch, lifecycles, OBSERVATION_DIM
    )
    active = trajectory.active_mask.to(device).reshape(batch, lifecycles)
    order = trajectory.orders.to(device).reshape(batch, lifecycles)
    hidden_before = trajectory.hidden_before.to(device).reshape(
        batch, lifecycles, -1
    )
    natural_actions = trajectory.actions.to(device).reshape(batch, lifecycles)
    z = trajectory.primitive_z.to(device).reshape(batch, lifecycles, MARK_DIM)
    batch_indices = torch.arange(batch, device=device)
    with torch.no_grad():
        prepared = arm.base.prepare_step(
            observations=observations, active_mask=active, validated=True
        )
        active_counts = active.sum(dim=1)
        prefix = torch.zeros(
            (batch, ACTION_COUNT), dtype=observations.dtype, device=device
        )
        base_logits = torch.zeros(
            (batch, lifecycles, ACTION_COUNT),
            dtype=observations.dtype,
            device=device,
        )
        for position in range(lifecycles):
            valid = position < active_counts
            focal = order[:, position].clamp(0, lifecycles - 1)
            local_embedding = prepared.member_embeddings[batch_indices, focal]
            local_hidden = hidden_before[batch_indices, focal]
            candidate_hidden = arm.base.actor_rnn(
                torch.cat((local_embedding, prepared.context, prefix), dim=-1),
                local_hidden,
            )
            logits = arm.base.action_head(
                torch.cat((candidate_hidden, prefix), dim=-1)
            )
            previous = base_logits[batch_indices, focal]
            base_logits[batch_indices, focal] = torch.where(
                valid.unsqueeze(-1), logits, previous
            )
            selected = natural_actions[batch_indices, focal].clamp(0, ACTION_COUNT - 1)
            prefix = prefix + F.one_hot(
                selected, num_classes=ACTION_COUNT
            ).to(prefix.dtype) * valid.unsqueeze(-1)

        keys = torch.arange(lifecycles, device=device)
        candidates = keys.view(1, 1, lifecycles)
        targets = keys.view(1, lifecycles, 1)
        lower_active = active.unsqueeze(1) & (candidates < targets)
        lower_key = torch.where(
            lower_active, candidates, torch.full_like(candidates, -1)
        ).amax(dim=-1)
        maximum_active = torch.where(
            active, keys.view(1, lifecycles), torch.full_like(active, -1, dtype=torch.long)
        ).amax(dim=-1, keepdim=True)
        predecessor = torch.where(lower_key >= 0, lower_key, maximum_active)
        predecessor = predecessor.clamp_min(0)
        permuted_z = z.gather(
            1, predecessor.unsqueeze(-1).expand(-1, -1, MARK_DIM)
        )
        natural_logits = base_logits + arm.W_z(z.detach())
        permuted_logits = base_logits + arm.W_z(permuted_z.detach())
        tv = action_distribution_tv(natural_logits, permuted_logits)
        eligible = active & active_counts.unsqueeze(-1).ge(2)
        tv = torch.where(eligible, tv, torch.zeros_like(tv))
    return (
        tv.reshape(time_steps, environments, lifecycles),
        eligible.reshape(time_steps, environments, lifecycles),
    )


def factor_counts(trajectory: EventTrajectory) -> dict[str, int]:
    return {"create": int((trajectory.event_kind == CREATE).sum()), "keep": int((trajectory.event_kind == KEEP).sum()), "renew": int((trajectory.event_kind == RENEW).sum()), "categorical": int(trajectory.event_cat_mask.sum()), "mark": int(trajectory.event_mark_mask.sum())}
