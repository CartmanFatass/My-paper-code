"""Immediate-tangent protected full-actor optimization for G27."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn
from torch.nn import functional as F

from ha_ctse_process.anchored_residual_g19 import (
    GRADIENT_CLIP,
    VALUE_CLIP,
    AnchoredRosterTrajectory,
    FastAnchoredResidualPolicy,
    _channel_policy_loss,
    compute_anchored_credit,
    project_delayed_gradients,
    replay_errors,
    replay_trajectory,
)


@dataclass(frozen=True)
class TangentGradientComposition:
    gradients: tuple[torch.Tensor, ...]
    successor_gradients: tuple[torch.Tensor, ...]
    pre_dot: float
    post_dot: float
    conflict: bool
    identity_error: float


def compose_tangent_protected_gradients(
    immediate: tuple[torch.Tensor | None, ...],
    successor: tuple[torch.Tensor | None, ...],
    parameters: tuple[nn.Parameter, ...],
) -> TangentGradientComposition:
    """Average immediate credit with successor credit after one-way projection."""

    projection = project_delayed_gradients(successor, immediate, parameters)
    immediate_rows = tuple(
        torch.zeros_like(parameter) if row is None else row
        for row, parameter in zip(immediate, parameters)
    )
    applied = tuple(
        0.5 * (left + right)
        for left, right in zip(immediate_rows, projection.gradients)
    )
    identity_error = max(
        float(
            (
                row - 0.5 * (left + right)
            ).detach().abs().max().cpu()
        )
        for row, left, right in zip(
            applied, immediate_rows, projection.gradients
        )
    )
    return TangentGradientComposition(
        gradients=applied,
        successor_gradients=projection.gradients,
        pre_dot=projection.pre_dot,
        post_dot=projection.post_dot,
        conflict=projection.conflict,
        identity_error=identity_error,
    )


class ImmediateTangentProtectedFullActorPolicy(FastAnchoredResidualPolicy):
    """G19 wrapper with a zero residual and a trainable full delayed actor."""

    def full_actor_parameters(self) -> tuple[nn.Parameter, ...]:
        return tuple(
            parameter
            for name, parameter in self.policy.named_parameters()
            if not name.startswith("delayed_residual.")
            and not name.startswith("critic.")
        )

    def full_actor_parameter_names(self) -> tuple[str, ...]:
        return tuple(
            name
            for name, _ in self.policy.named_parameters()
            if not name.startswith("delayed_residual.")
            and not name.startswith("critic.")
        )

    def begin_tangent_phase(self) -> None:
        if self.phase != "fast":
            raise RuntimeError("G27 tangent phase may begin exactly once")
        if self.residual_output_layer_maximum_absolute_value() != 0.0:
            raise RuntimeError("G27 residual must remain exact zero")
        for name, parameter in self.policy.named_parameters():
            parameter.requires_grad_(
                not name.startswith("delayed_residual.")
                and not name.startswith("critic.")
            )
        for parameter in self.slow_critic.parameters():
            parameter.requires_grad_(True)
        for parameter in self.credit_baselines.parameters():
            parameter.requires_grad_(True)
        self.phase = "tangent"


def optimize_tangent_protected_update(
    model: ImmediateTangentProtectedFullActorPolicy,
    actor_optimizer: torch.optim.Optimizer,
    critic_optimizer: torch.optim.Optimizer,
    trajectory: AnchoredRosterTrajectory,
    *,
    device: torch.device,
    ppo_passes: int,
    gamma: float,
) -> dict[str, float]:
    """Update the full actor while projecting successor/immediate conflicts."""

    if model.phase != "tangent":
        raise RuntimeError("G27 update requires tangent phase")
    terminals = torch.zeros_like(
        trajectory.rewards, dtype=torch.bool, device=device
    )
    terminals[-1] = True
    credit = compute_anchored_credit(
        rewards=trajectory.rewards.to(device),
        slow_values=trajectory.old_values.to(device),
        immediate_baselines=trajectory.old_immediate_baselines.to(device),
        successor_baselines=trajectory.old_successor_baselines.to(device),
        terminals=terminals,
        gamma=float(gamma),
    )
    with torch.no_grad():
        errors = replay_errors(
            replay_trajectory(model, trajectory, device=device), trajectory
        )
    actor_parameters = model.full_actor_parameters()
    critic_parameters = model.critic_parameters()
    if not actor_parameters or not critic_parameters:
        raise RuntimeError("G27 optimizer inventory is empty")
    totals = {
        name: 0.0
        for name in (
            "policy_loss",
            "immediate_policy_loss",
            "successor_policy_loss",
            "slow_value_loss",
            "immediate_baseline_loss",
            "successor_baseline_loss",
            "actor_gradient_norm",
            "critic_gradient_norm",
            "projection_pre_dot",
            "projection_post_dot",
            "projection_conflict",
        )
    }
    maximum_identity_error = 0.0
    minimum_projection_post_dot = float("inf")
    finite = True
    model.train()
    for _ in range(int(ppo_passes)):
        replay = replay_trajectory(model, trajectory, device=device)
        immediate_policy_loss = _channel_policy_loss(
            replay, trajectory, credit.immediate_residual
        )
        successor_policy_loss = _channel_policy_loss(
            replay, trajectory, credit.successor_residual
        )
        actor_optimizer.zero_grad(set_to_none=True)
        immediate_gradients = torch.autograd.grad(
            immediate_policy_loss,
            actor_parameters,
            retain_graph=True,
            allow_unused=True,
        )
        successor_gradients = torch.autograd.grad(
            successor_policy_loss,
            actor_parameters,
            allow_unused=True,
        )
        composition = compose_tangent_protected_gradients(
            immediate_gradients, successor_gradients, actor_parameters
        )
        for parameter, gradient in zip(
            actor_parameters, composition.gradients
        ):
            parameter.grad = gradient.detach().clone()
        actor_gradient_norm = torch.nn.utils.clip_grad_norm_(
            actor_parameters, GRADIENT_CLIP
        )
        actor_optimizer.step()

        replay = replay_trajectory(model, trajectory, device=device)
        old_values = trajectory.old_values.to(device)
        clipped_values = old_values + torch.clamp(
            replay.values - old_values, -VALUE_CLIP, VALUE_CLIP
        )
        slow_value_loss = torch.maximum(
            torch.square(replay.values - credit.slow_return_targets.to(device)),
            torch.square(
                clipped_values - credit.slow_return_targets.to(device)
            ),
        ).mean()
        immediate_baseline_loss = F.mse_loss(
            replay.immediate_baselines,
            trajectory.rewards.to(device).detach(),
        )
        successor_baseline_loss = F.mse_loss(
            replay.successor_baselines,
            credit.successor_targets.to(device),
        )
        critic_loss = (
            slow_value_loss
            + immediate_baseline_loss
            + successor_baseline_loss
        )
        critic_optimizer.zero_grad(set_to_none=True)
        critic_loss.backward()
        critic_gradient_norm = torch.nn.utils.clip_grad_norm_(
            critic_parameters, GRADIENT_CLIP
        )
        critic_optimizer.step()

        policy_loss = 0.5 * (
            immediate_policy_loss + successor_policy_loss
        )
        finite = finite and all(
            bool(torch.isfinite(value))
            for value in (
                policy_loss,
                immediate_policy_loss,
                successor_policy_loss,
                critic_loss,
                actor_gradient_norm,
                critic_gradient_norm,
            )
        )
        minimum_projection_post_dot = min(
            minimum_projection_post_dot, composition.post_dot
        )
        maximum_identity_error = max(
            maximum_identity_error, composition.identity_error
        )
        totals["policy_loss"] += float(policy_loss.detach().cpu())
        totals["immediate_policy_loss"] += float(
            immediate_policy_loss.detach().cpu()
        )
        totals["successor_policy_loss"] += float(
            successor_policy_loss.detach().cpu()
        )
        totals["slow_value_loss"] += float(slow_value_loss.detach().cpu())
        totals["immediate_baseline_loss"] += float(
            immediate_baseline_loss.detach().cpu()
        )
        totals["successor_baseline_loss"] += float(
            successor_baseline_loss.detach().cpu()
        )
        totals["actor_gradient_norm"] += float(
            actor_gradient_norm.detach().cpu()
        )
        totals["critic_gradient_norm"] += float(
            critic_gradient_norm.detach().cpu()
        )
        totals["projection_pre_dot"] += composition.pre_dot
        totals["projection_post_dot"] += composition.post_dot
        totals["projection_conflict"] += float(composition.conflict)
    for name in totals:
        totals[name] /= float(ppo_passes)
    totals.update(errors)
    totals["immediate_channel_weight"] = 0.5
    totals["successor_channel_weight"] = 0.5
    totals["minimum_projection_post_dot"] = float(
        minimum_projection_post_dot
    )
    totals["maximum_applied_gradient_identity_error"] = float(
        maximum_identity_error
    )
    totals["finite_update"] = float(finite)
    totals["optimizer_steps"] = float(2 * ppo_passes)
    return totals
