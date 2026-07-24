"""Direction-balanced full-actor optimization for G30."""

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
    replay_errors,
    replay_trajectory,
)


@dataclass(frozen=True)
class DirectionBalancedComposition:
    gradients: tuple[torch.Tensor, ...]
    immediate_norm: float
    successor_norm: float
    immediate_dot: float
    identity_error: float
    immediate_zero: bool
    successor_zero: bool


@dataclass(frozen=True)
class DirectionBalancedAdamStep:
    composition: DirectionBalancedComposition
    gradient_norm: torch.Tensor
    optimizer_step_increment: float


def _gradient_dot(
    left: tuple[torch.Tensor, ...], right: tuple[torch.Tensor, ...]
) -> torch.Tensor:
    return sum(
        (left_row.to(torch.float64) * right_row.to(torch.float64)).sum()
        for left_row, right_row in zip(left, right)
    )


def _materialize_gradients(
    rows: tuple[torch.Tensor | None, ...],
    parameters: tuple[nn.Parameter, ...],
) -> tuple[torch.Tensor, ...]:
    if len(rows) != len(parameters) or not parameters:
        raise ValueError("G30 gradient inventory mismatch")
    materialized = tuple(
        torch.zeros_like(parameter) if row is None else row.detach()
        for row, parameter in zip(rows, parameters)
    )
    if any(
        row.shape != parameter.shape or not bool(torch.isfinite(row).all())
        for row, parameter in zip(materialized, parameters)
    ):
        raise ValueError("G30 received invalid actor gradients")
    return materialized


def compose_direction_balanced_gradients(
    immediate: tuple[torch.Tensor | None, ...],
    successor: tuple[torch.Tensor | None, ...],
    parameters: tuple[nn.Parameter, ...],
) -> DirectionBalancedComposition:
    """Equally combine exact global unit directions without an epsilon."""

    immediate_rows = _materialize_gradients(immediate, parameters)
    successor_rows = _materialize_gradients(successor, parameters)
    immediate_norm = torch.sqrt(_gradient_dot(immediate_rows, immediate_rows))
    successor_norm = torch.sqrt(_gradient_dot(successor_rows, successor_rows))
    immediate_zero = bool(immediate_norm.detach() == 0.0)
    successor_zero = bool(successor_norm.detach() == 0.0)
    immediate_directions = tuple(
        (
            torch.zeros_like(row, dtype=torch.float64)
            if immediate_zero
            else row.to(torch.float64) / immediate_norm
        )
        for row in immediate_rows
    )
    successor_directions = tuple(
        (
            torch.zeros_like(row, dtype=torch.float64)
            if successor_zero
            else row.to(torch.float64) / successor_norm
        )
        for row in successor_rows
    )
    expected = tuple(
        0.5 * (left + right)
        for left, right in zip(
            immediate_directions, successor_directions
        )
    )
    applied = tuple(
        row.to(parameter.dtype)
        for row, parameter in zip(expected, parameters)
    )
    if any(not bool(torch.isfinite(row).all()) for row in applied):
        raise RuntimeError("G30 direction composition became nonfinite")
    immediate_dot = _gradient_dot(applied, immediate_rows)
    identity_error = max(
        float(
            (row - reference.to(row.dtype)).detach().abs().max().cpu()
        )
        for row, reference in zip(applied, expected)
    )
    return DirectionBalancedComposition(
        gradients=applied,
        immediate_norm=float(immediate_norm.detach().cpu()),
        successor_norm=float(successor_norm.detach().cpu()),
        immediate_dot=float(immediate_dot.detach().cpu()),
        identity_error=identity_error,
        immediate_zero=immediate_zero,
        successor_zero=successor_zero,
    )


def _optimizer_step_value(
    optimizer: torch.optim.Adam, parameter: nn.Parameter
) -> float:
    state = optimizer.state.get(parameter, {})
    step = state.get("step", 0.0)
    if isinstance(step, torch.Tensor):
        return float(step.detach().cpu())
    return float(step)


def apply_direction_balanced_adam_step(
    optimizer: torch.optim.Optimizer,
    parameters: tuple[nn.Parameter, ...],
    immediate: tuple[torch.Tensor | None, ...],
    successor: tuple[torch.Tensor | None, ...],
) -> DirectionBalancedAdamStep:
    """Advance ordinary Adam once with the direction-balanced gradient."""

    if not isinstance(optimizer, torch.optim.Adam):
        raise TypeError("G30 direction balance requires Adam")
    owned = tuple(
        parameter
        for group in optimizer.param_groups
        for parameter in group["params"]
    )
    if len(owned) != len(parameters) or {
        id(parameter) for parameter in owned
    } != {id(parameter) for parameter in parameters}:
        raise ValueError("G30 Adam inventory does not match the full actor")
    composition = compose_direction_balanced_gradients(
        immediate, successor, parameters
    )
    optimizer.zero_grad(set_to_none=True)
    for parameter, gradient in zip(parameters, composition.gradients):
        parameter.grad = gradient.clone()
    gradient_norm = torch.nn.utils.clip_grad_norm_(
        parameters, GRADIENT_CLIP
    )
    if not bool(torch.isfinite(gradient_norm)):
        raise RuntimeError("G30 actor gradient norm is nonfinite")
    steps_before = tuple(
        _optimizer_step_value(optimizer, parameter)
        for parameter in parameters
    )
    optimizer.step()
    steps_after = tuple(
        _optimizer_step_value(optimizer, parameter)
        for parameter in parameters
    )
    if any(
        after != before + 1.0
        for before, after in zip(steps_before, steps_after)
    ):
        raise RuntimeError("G30 Adam state did not advance exactly once")
    for parameter in parameters:
        if any(
            isinstance(value, torch.Tensor)
            and not bool(torch.isfinite(value).all())
            for value in optimizer.state[parameter].values()
        ):
            raise RuntimeError("G30 Adam state became nonfinite")
    return DirectionBalancedAdamStep(
        composition=composition,
        gradient_norm=gradient_norm,
        optimizer_step_increment=1.0,
    )


class DirectionBalancedFullActorPolicy(FastAnchoredResidualPolicy):
    """G30 wrapper with a zero residual and a trainable full actor."""

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

    def begin_direction_balanced_phase(self) -> None:
        if self.phase != "fast":
            raise RuntimeError("G30 direction-balanced phase may begin exactly once")
        if self.residual_output_layer_maximum_absolute_value() != 0.0:
            raise RuntimeError("G30 residual must remain exact zero")
        for name, parameter in self.policy.named_parameters():
            parameter.requires_grad_(
                not name.startswith("delayed_residual.")
                and not name.startswith("critic.")
            )
        for parameter in self.slow_critic.parameters():
            parameter.requires_grad_(True)
        for parameter in self.credit_baselines.parameters():
            parameter.requires_grad_(True)
        self.phase = "direction_balanced"


def optimize_direction_balanced_update(
    model: DirectionBalancedFullActorPolicy,
    actor_optimizer: torch.optim.Optimizer,
    critic_optimizer: torch.optim.Optimizer,
    trajectory: AnchoredRosterTrajectory,
    *,
    device: torch.device,
    ppo_passes: int,
    gamma: float,
) -> dict[str, float]:
    """Update the full actor with equal global gradient directions."""

    if model.phase != "direction_balanced":
        raise RuntimeError("G30 update requires direction-balanced phase")
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
    model.train()
    replay = replay_trajectory(model, trajectory, device=device)
    with torch.no_grad():
        errors = replay_errors(replay, trajectory)
    actor_parameters = model.full_actor_parameters()
    critic_parameters = model.critic_parameters()
    if not actor_parameters or not critic_parameters:
        raise RuntimeError("G30 optimizer inventory is empty")
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
            "direction_immediate_norm",
            "direction_successor_norm",
            "direction_immediate_dot",
            "direction_immediate_zero",
            "direction_successor_zero",
        )
    }
    maximum_identity_error = 0.0
    minimum_direction_dot = float("inf")
    minimum_actor_optimizer_step_increment = float("inf")
    finite = True
    for pass_index in range(int(ppo_passes)):
        if pass_index:
            replay = replay_trajectory(model, trajectory, device=device)
        immediate_policy_loss = _channel_policy_loss(
            replay, trajectory, credit.immediate_residual
        )
        successor_policy_loss = _channel_policy_loss(
            replay, trajectory, credit.successor_residual
        )
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
        actor_step = apply_direction_balanced_adam_step(
            actor_optimizer,
            actor_parameters,
            immediate_gradients,
            successor_gradients,
        )
        actor_gradient_norm = actor_step.gradient_norm

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

        composition = actor_step.composition
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
        minimum_direction_dot = min(
            minimum_direction_dot, composition.immediate_dot
        )
        maximum_identity_error = max(
            maximum_identity_error, composition.identity_error
        )
        minimum_actor_optimizer_step_increment = min(
            minimum_actor_optimizer_step_increment,
            actor_step.optimizer_step_increment,
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
        totals["direction_immediate_norm"] += composition.immediate_norm
        totals["direction_successor_norm"] += composition.successor_norm
        totals["direction_immediate_dot"] += composition.immediate_dot
        totals["direction_immediate_zero"] += float(
            composition.immediate_zero
        )
        totals["direction_successor_zero"] += float(
            composition.successor_zero
        )
    for name in totals:
        totals[name] /= float(ppo_passes)
    totals.update(errors)
    totals["immediate_channel_weight"] = 0.5
    totals["successor_channel_weight"] = 0.5
    totals["minimum_direction_immediate_dot"] = float(
        minimum_direction_dot
    )
    totals["maximum_direction_composition_identity_error"] = float(
        maximum_identity_error
    )
    totals["minimum_actor_optimizer_step_increment"] = float(
        minimum_actor_optimizer_step_increment
    )
    totals["finite_update"] = float(finite)
    totals["optimizer_steps"] = float(2 * ppo_passes)
    return totals
