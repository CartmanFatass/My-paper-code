"""Optimizer-realized-tangent full-actor optimization for G29."""

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
class RealizedParameterProjection:
    parameters: tuple[torch.Tensor, ...]
    pre_dot: float
    post_dot: float
    conflict: bool
    lattice_correction: float


@dataclass(frozen=True)
class RealizedAdamStep:
    pre_dot: float
    post_dot: float
    conflict: bool
    lattice_correction: float
    parameter_identity_error: float
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
        raise ValueError("G29 gradient inventory mismatch")
    materialized = tuple(
        torch.zeros_like(parameter) if row is None else row.detach()
        for row, parameter in zip(rows, parameters)
    )
    if any(
        row.shape != parameter.shape or not bool(torch.isfinite(row).all())
        for row, parameter in zip(materialized, parameters)
    ):
        raise ValueError("G29 received invalid actor gradients")
    return materialized


def project_realized_parameters(
    before: tuple[torch.Tensor, ...],
    proposed_after: tuple[torch.Tensor, ...],
    immediate: tuple[torch.Tensor | None, ...],
    parameters: tuple[nn.Parameter, ...],
) -> RealizedParameterProjection:
    """Project the actual Adam parameter movement, not its input gradient."""

    if not (
        len(before)
        == len(proposed_after)
        == len(immediate)
        == len(parameters)
    ) or not parameters:
        raise ValueError("G29 realized parameter inventory mismatch")
    immediate_rows = _materialize_gradients(immediate, parameters)
    if any(
        left.shape != parameter.shape
        or right.shape != parameter.shape
        or not bool(torch.isfinite(left).all())
        or not bool(torch.isfinite(right).all())
        for left, right, parameter in zip(
            before, proposed_after, parameters
        )
    ):
        raise ValueError("G29 received invalid realized parameters")
    proposed_displacements = tuple(
        left - right for left, right in zip(before, proposed_after)
    )
    pre = _gradient_dot(proposed_displacements, immediate_rows)
    immediate_norm = _gradient_dot(immediate_rows, immediate_rows)
    conflict = bool(
        immediate_norm.detach() > 0.0
        and pre.detach() < 0.0
    )
    if conflict:
        coefficient = -pre / immediate_norm
        projected_displacements = tuple(
            (
                displacement.to(torch.float64)
                + coefficient * right.to(torch.float64)
            )
            for displacement, right in zip(
                proposed_displacements, immediate_rows
            )
        )
        applied = tuple(
            (
                left.to(torch.float64) - displacement
            ).to(left.dtype)
            for left, displacement in zip(before, projected_displacements)
        )
    else:
        applied = proposed_after
    actual_displacements = tuple(
        left - right for left, right in zip(before, applied)
    )
    post = _gradient_dot(actual_displacements, immediate_rows)
    lattice_correction = 0.0
    if bool(post.detach() < 0.0):
        row_index, flat_index = max(
            (
                (
                    row_index,
                    int(row.detach().abs().reshape(-1).argmax().cpu()),
                )
                for row_index, row in enumerate(immediate_rows)
                if row.numel()
            ),
            key=lambda item: float(
                immediate_rows[item[0]].detach().abs().reshape(-1)[
                    item[1]
                ].cpu()
            ),
        )
        repaired_rows = [row.clone() for row in applied]
        repaired = repaired_rows[row_index]
        repaired_flat = repaired.reshape(-1)
        immediate_value = immediate_rows[row_index].reshape(-1)[flat_index]
        original_value = repaired_flat[flat_index].clone()
        direction = torch.full_like(
            repaired_flat[flat_index],
            (
                -float("inf")
                if float(immediate_value.detach().cpu()) > 0.0
                else float("inf")
            ),
        )
        reverse_direction = torch.full_like(
            repaired_flat[flat_index],
            (
                float("inf")
                if float(immediate_value.detach().cpu()) > 0.0
                else -float("inf")
            ),
        )
        repaired_rows[row_index] = repaired
        applied = tuple(repaired_rows)

        # Parameter subtraction adds a second float32 rounding after the
        # analytical displacement projection. Close the actual realized step
        # on one coordinate without changing the registered zero boundary.
        for _ in range(64):
            current_value = repaired_flat[flat_index].clone()
            required_delta = (
                -post / immediate_value.to(torch.float64)
            )
            candidate = (
                current_value.to(torch.float64) - required_delta
            ).to(repaired.dtype)
            if bool(
                candidate.detach() == current_value.detach()
            ) or bool(
                (
                    (current_value - candidate)
                    * immediate_value
                ).detach()
                <= 0.0
            ):
                candidate = torch.nextafter(current_value, direction)
            repaired_flat[flat_index] = candidate
            actual_displacements = tuple(
                left - right for left, right in zip(before, applied)
            )
            post = _gradient_dot(actual_displacements, immediate_rows)
            if bool(post.detach() >= 0.0):
                break
        else:
            raise RuntimeError(
                "G29 could not close the realized parameter half-space"
            )

        # Retain the first closed parameter lattice point.
        for _ in range(64):
            current_value = repaired_flat[flat_index].clone()
            predecessor = torch.nextafter(current_value, reverse_direction)
            if bool(
                (
                    (original_value - predecessor)
                    * immediate_value
                ).detach()
                < 0.0
            ):
                break
            repaired_flat[flat_index] = predecessor
            predecessor_displacements = tuple(
                left - right for left, right in zip(before, applied)
            )
            predecessor_post = _gradient_dot(
                predecessor_displacements, immediate_rows
            )
            if bool(predecessor_post.detach() < 0.0):
                repaired_flat[flat_index] = current_value
                break
            actual_displacements = predecessor_displacements
            post = predecessor_post
        else:
            raise RuntimeError(
                "G29 could not certify the first realized parameter closure"
            )
        lattice_correction = float(
            (repaired_flat[flat_index] - original_value)
            .detach()
            .abs()
            .cpu()
        )
    return RealizedParameterProjection(
        parameters=applied,
        pre_dot=float(pre.detach().cpu()),
        post_dot=float(post.detach().cpu()),
        conflict=conflict,
        lattice_correction=lattice_correction,
    )


def _optimizer_step_value(
    optimizer: torch.optim.Adam, parameter: nn.Parameter
) -> float:
    state = optimizer.state.get(parameter, {})
    step = state.get("step", 0.0)
    if isinstance(step, torch.Tensor):
        return float(step.detach().cpu())
    return float(step)


def apply_optimizer_realized_tangent_step(
    optimizer: torch.optim.Optimizer,
    parameters: tuple[nn.Parameter, ...],
    immediate: tuple[torch.Tensor | None, ...],
    successor: tuple[torch.Tensor | None, ...],
) -> RealizedAdamStep:
    """Take Adam once, then constrain only its realized actor displacement."""

    if not isinstance(optimizer, torch.optim.Adam):
        raise TypeError("G29 realized tangent requires Adam")
    owned = tuple(
        parameter
        for group in optimizer.param_groups
        for parameter in group["params"]
    )
    if len(owned) != len(parameters) or {
        id(parameter) for parameter in owned
    } != {id(parameter) for parameter in parameters}:
        raise ValueError("G29 Adam inventory does not match the full actor")
    immediate_rows = _materialize_gradients(immediate, parameters)
    successor_rows = _materialize_gradients(successor, parameters)
    combined = tuple(
        0.5 * (left + right)
        for left, right in zip(immediate_rows, successor_rows)
    )
    optimizer.zero_grad(set_to_none=True)
    for parameter, gradient in zip(parameters, combined):
        parameter.grad = gradient.clone()
    gradient_norm = torch.nn.utils.clip_grad_norm_(
        parameters, GRADIENT_CLIP
    )
    if not bool(torch.isfinite(gradient_norm)):
        raise RuntimeError("G29 actor gradient norm is nonfinite")
    before = tuple(parameter.detach().clone() for parameter in parameters)
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
        after != before_step + 1.0
        for before_step, after in zip(steps_before, steps_after)
    ):
        raise RuntimeError("G29 Adam state did not advance exactly once")
    for parameter in parameters:
        if any(
            isinstance(value, torch.Tensor)
            and not bool(torch.isfinite(value).all())
            for value in optimizer.state[parameter].values()
        ):
            raise RuntimeError("G29 Adam state became nonfinite")
    proposed_after = tuple(
        parameter.detach().clone() for parameter in parameters
    )
    projection = project_realized_parameters(
        before, proposed_after, immediate, parameters
    )
    if projection.conflict:
        with torch.no_grad():
            for parameter, expected in zip(
                parameters, projection.parameters
            ):
                parameter.copy_(expected)
    identity_error = max(
        float((parameter - expected).detach().abs().max().cpu())
        for parameter, expected in zip(
            parameters,
            (
                projection.parameters
                if projection.conflict
                else proposed_after
            ),
        )
    )
    return RealizedAdamStep(
        pre_dot=projection.pre_dot,
        post_dot=projection.post_dot,
        conflict=projection.conflict,
        lattice_correction=projection.lattice_correction,
        parameter_identity_error=identity_error,
        gradient_norm=gradient_norm,
        optimizer_step_increment=1.0,
    )


class OptimizerRealizedTangentFullActorPolicy(FastAnchoredResidualPolicy):
    """G29 wrapper with a zero residual and a trainable full actor."""

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

    def begin_realized_tangent_phase(self) -> None:
        if self.phase != "fast":
            raise RuntimeError("G29 realized-tangent phase may begin exactly once")
        if self.residual_output_layer_maximum_absolute_value() != 0.0:
            raise RuntimeError("G29 residual must remain exact zero")
        for name, parameter in self.policy.named_parameters():
            parameter.requires_grad_(
                not name.startswith("delayed_residual.")
                and not name.startswith("critic.")
            )
        for parameter in self.slow_critic.parameters():
            parameter.requires_grad_(True)
        for parameter in self.credit_baselines.parameters():
            parameter.requires_grad_(True)
        self.phase = "realized_tangent"


def optimize_optimizer_realized_tangent_update(
    model: OptimizerRealizedTangentFullActorPolicy,
    actor_optimizer: torch.optim.Optimizer,
    critic_optimizer: torch.optim.Optimizer,
    trajectory: AnchoredRosterTrajectory,
    *,
    device: torch.device,
    ppo_passes: int,
    gamma: float,
) -> dict[str, float]:
    """Update the full actor while protecting realized immediate descent."""

    if model.phase != "realized_tangent":
        raise RuntimeError("G29 update requires realized-tangent phase")
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
        raise RuntimeError("G29 optimizer inventory is empty")
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
            "realized_displacement_pre_dot",
            "realized_displacement_post_dot",
            "realized_displacement_conflict",
            "realized_displacement_lattice_correction",
        )
    }
    maximum_identity_error = 0.0
    maximum_lattice_correction = 0.0
    minimum_realized_displacement_post_dot = float("inf")
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
        actor_step = apply_optimizer_realized_tangent_step(
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
        minimum_realized_displacement_post_dot = min(
            minimum_realized_displacement_post_dot, actor_step.post_dot
        )
        maximum_identity_error = max(
            maximum_identity_error, actor_step.parameter_identity_error
        )
        maximum_lattice_correction = max(
            maximum_lattice_correction, actor_step.lattice_correction
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
        totals["realized_displacement_pre_dot"] += actor_step.pre_dot
        totals["realized_displacement_post_dot"] += actor_step.post_dot
        totals["realized_displacement_conflict"] += float(
            actor_step.conflict
        )
        totals["realized_displacement_lattice_correction"] += (
            actor_step.lattice_correction
        )
    for name in totals:
        totals[name] /= float(ppo_passes)
    totals.update(errors)
    totals["immediate_channel_weight"] = 0.5
    totals["successor_channel_weight"] = 0.5
    totals["minimum_realized_displacement_post_dot"] = float(
        minimum_realized_displacement_post_dot
    )
    totals["maximum_applied_parameter_identity_error"] = float(
        maximum_identity_error
    )
    totals["maximum_realized_displacement_lattice_correction"] = float(
        maximum_lattice_correction
    )
    totals["minimum_actor_optimizer_step_increment"] = float(
        minimum_actor_optimizer_step_increment
    )
    totals["finite_update"] = float(finite)
    totals["optimizer_steps"] = float(2 * ppo_passes)
    return totals
