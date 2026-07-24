"""Net-immediate-descent full-actor optimization for G28."""

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
class NetDescentGradientComposition:
    gradients: tuple[torch.Tensor, ...]
    successor_gradients: tuple[torch.Tensor, ...]
    pre_dot: float
    post_dot: float
    conflict: bool
    identity_error: float
    lattice_correction: float


@dataclass(frozen=True)
class NetDescentProjection:
    gradients: tuple[torch.Tensor, ...]
    pre_dot: float
    post_dot: float
    conflict: bool
    lattice_correction: float


def _gradient_dot(
    left: tuple[torch.Tensor, ...], right: tuple[torch.Tensor, ...]
) -> torch.Tensor:
    return sum(
        (left_row.to(torch.float64) * right_row.to(torch.float64)).sum()
        for left_row, right_row in zip(left, right)
    )


def project_successor_for_net_immediate_descent(
    successor: tuple[torch.Tensor | None, ...],
    immediate: tuple[torch.Tensor | None, ...],
    parameters: tuple[nn.Parameter, ...],
) -> NetDescentProjection:
    """Protect immediate descent of the equal combined actor gradient.

    Successor conflict is retained while ``dot(g_i, g_s) >= -||g_i||^2``.
    Larger conflict is moved to that boundary. Algebra is evaluated in
    float64; one coordinate receives the minimum representable repair only if
    the actor dtype conversion lands outside the closed combined half-space.
    """

    if not (
        len(successor) == len(immediate) == len(parameters)
    ) or not parameters:
        raise ValueError("G28 gradient projection inventory mismatch")
    successor_rows = tuple(
        torch.zeros_like(parameter) if row is None else row
        for row, parameter in zip(successor, parameters)
    )
    immediate_rows = tuple(
        torch.zeros_like(parameter) if row is None else row
        for row, parameter in zip(immediate, parameters)
    )
    if any(
        row.shape != parameter.shape or not bool(torch.isfinite(row).all())
        for rows in (successor_rows, immediate_rows)
        for row, parameter in zip(rows, parameters)
    ):
        raise ValueError("G28 gradient projection received invalid rows")
    successor_dot = _gradient_dot(successor_rows, immediate_rows)
    immediate_norm = _gradient_dot(immediate_rows, immediate_rows)
    conflict = bool(
        immediate_norm.detach() > 0.0
        and successor_dot.detach() < -immediate_norm.detach()
    )
    if conflict:
        coefficient = (-immediate_norm - successor_dot) / immediate_norm
        applied = tuple(
            (
                left.to(torch.float64)
                + coefficient * right.to(torch.float64)
            ).to(left.dtype)
            for left, right in zip(successor_rows, immediate_rows)
        )
    else:
        applied = successor_rows
    combined = tuple(
        0.5 * (left + right)
        for left, right in zip(immediate_rows, applied)
    )
    pre = 0.5 * (immediate_norm + successor_dot)
    post = _gradient_dot(combined, immediate_rows)
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
        repaired_rows = list(applied)
        repaired = repaired_rows[row_index].clone()
        repaired_flat = repaired.reshape(-1)
        immediate_value = immediate_rows[row_index].reshape(-1)[flat_index]
        original_value = repaired_flat[flat_index].clone()
        direction = torch.full_like(
            repaired_flat[flat_index],
            (
                float("inf")
                if float(immediate_value.detach().cpu()) > 0.0
                else -float("inf")
            ),
        )
        reverse_direction = torch.full_like(
            repaired_flat[flat_index],
            (
                -float("inf")
                if float(immediate_value.detach().cpu()) > 0.0
                else float("inf")
            ),
        )
        repaired_rows[row_index] = repaired
        applied = tuple(repaired_rows)

        # A single float64 residual correction can still undershoot after the
        # successor and the equal average are each rounded to float32. Walk the
        # same coordinate to the first closed lattice point; this changes no
        # gradient weight or tolerance.
        for _ in range(64):
            current_value = repaired_flat[flat_index].clone()
            required_delta = (
                -2.0 * post / immediate_value.to(torch.float64)
            )
            candidate = (
                current_value.to(torch.float64) + required_delta
            ).to(repaired.dtype)
            if bool(
                candidate.detach() == current_value.detach()
            ) or bool(
                (
                    (candidate - current_value)
                    * immediate_value
                ).detach()
                <= 0.0
            ):
                candidate = torch.nextafter(current_value, direction)
            repaired_flat[flat_index] = candidate
            combined = tuple(
                0.5 * (left + right)
                for left, right in zip(immediate_rows, applied)
            )
            post = _gradient_dot(combined, immediate_rows)
            if bool(post.detach() >= 0.0):
                break
        else:
            raise RuntimeError("G28 could not close the float gradient half-space")

        # The analytical step may round one lattice point past the boundary.
        # Walk back while the predecessor remains closed, then retain the first
        # representable value whose predecessor violates the invariant.
        for _ in range(64):
            current_value = repaired_flat[flat_index].clone()
            predecessor = torch.nextafter(current_value, reverse_direction)
            if bool(
                (
                    (predecessor - original_value)
                    * immediate_value
                ).detach()
                < 0.0
            ):
                break
            repaired_flat[flat_index] = predecessor
            predecessor_combined = tuple(
                0.5 * (left + right)
                for left, right in zip(immediate_rows, applied)
            )
            predecessor_post = _gradient_dot(
                predecessor_combined, immediate_rows
            )
            if bool(predecessor_post.detach() < 0.0):
                repaired_flat[flat_index] = current_value
                break
            combined = predecessor_combined
            post = predecessor_post
        else:
            raise RuntimeError(
                "G28 could not certify the minimum float gradient closure"
            )
        lattice_correction = float(
            (repaired_flat[flat_index] - original_value)
            .detach()
            .abs()
            .cpu()
        )
    return NetDescentProjection(
        gradients=applied,
        pre_dot=float(pre.detach().cpu()),
        post_dot=float(post.detach().cpu()),
        conflict=conflict,
        lattice_correction=lattice_correction,
    )


def compose_net_immediate_descent_gradients(
    immediate: tuple[torch.Tensor | None, ...],
    successor: tuple[torch.Tensor | None, ...],
    parameters: tuple[nn.Parameter, ...],
) -> NetDescentGradientComposition:
    """Average immediate credit with net-descent-protected successor credit."""

    projection = project_successor_for_net_immediate_descent(
        successor, immediate, parameters
    )
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
    return NetDescentGradientComposition(
        gradients=applied,
        successor_gradients=projection.gradients,
        pre_dot=projection.pre_dot,
        post_dot=projection.post_dot,
        conflict=projection.conflict,
        identity_error=identity_error,
        lattice_correction=projection.lattice_correction,
    )


class NetImmediateDescentFullActorPolicy(FastAnchoredResidualPolicy):
    """G28 wrapper with a zero residual and a trainable full delayed actor."""

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

    def begin_net_descent_phase(self) -> None:
        if self.phase != "fast":
            raise RuntimeError("G28 net-descent phase may begin exactly once")
        if self.residual_output_layer_maximum_absolute_value() != 0.0:
            raise RuntimeError("G28 residual must remain exact zero")
        for name, parameter in self.policy.named_parameters():
            parameter.requires_grad_(
                not name.startswith("delayed_residual.")
                and not name.startswith("critic.")
            )
        for parameter in self.slow_critic.parameters():
            parameter.requires_grad_(True)
        for parameter in self.credit_baselines.parameters():
            parameter.requires_grad_(True)
        self.phase = "net_descent"


def optimize_net_immediate_descent_update(
    model: NetImmediateDescentFullActorPolicy,
    actor_optimizer: torch.optim.Optimizer,
    critic_optimizer: torch.optim.Optimizer,
    trajectory: AnchoredRosterTrajectory,
    *,
    device: torch.device,
    ppo_passes: int,
    gamma: float,
) -> dict[str, float]:
    """Update the full actor while protecting net immediate descent."""

    if model.phase != "net_descent":
        raise RuntimeError("G28 update requires net-descent phase")
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
        raise RuntimeError("G28 optimizer inventory is empty")
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
            "projection_lattice_correction",
        )
    }
    maximum_identity_error = 0.0
    maximum_lattice_correction = 0.0
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
        composition = compose_net_immediate_descent_gradients(
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
        maximum_lattice_correction = max(
            maximum_lattice_correction, composition.lattice_correction
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
        totals["projection_lattice_correction"] += (
            composition.lattice_correction
        )
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
    totals["maximum_projection_lattice_correction"] = float(
        maximum_lattice_correction
    )
    totals["finite_update"] = float(finite)
    totals["optimizer_steps"] = float(2 * ppo_passes)
    return totals
