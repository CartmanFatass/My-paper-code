"""Active-set-centered delayed action residual for G20."""

from __future__ import annotations

from typing import Any

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
from ha_ctse_process.continuous_roster_policy import ContinuousRosterPolicy


CENTERING_TOLERANCE = 1e-6


def center_active_residuals(
    proposals: torch.Tensor, active_mask: torch.Tensor
) -> torch.Tensor:
    """Remove each action coordinate's active-set common mode."""

    if proposals.ndim != 3:
        raise ValueError("G20 proposals must be [batch,member,action]")
    if active_mask.shape != proposals.shape[:2] or active_mask.dtype != torch.bool:
        raise ValueError("G20 active mask shape/dtype mismatch")
    if not bool(torch.isfinite(proposals).all()):
        raise ValueError("G20 proposals must be finite")
    active_count = active_mask.sum(dim=1)
    if bool((active_count <= 0).any()):
        raise ValueError("G20 centering requires an active lifecycle")
    weights = active_mask.to(proposals.dtype).unsqueeze(-1)
    active_mean = (proposals * weights).sum(dim=1, keepdim=True) / active_count.to(
        proposals.dtype
    ).view(-1, 1, 1)
    return (proposals - active_mean) * weights


class CenteredResidualContinuousRosterPolicy(ContinuousRosterPolicy):
    """Base actor plus a current-state active-centered delayed proposal."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.delayed_residual = nn.Sequential(
            nn.Linear(
                3 * self.hidden_dim + self.observation_dim,
                self.hidden_dim,
            ),
            nn.Tanh(),
            nn.Linear(self.hidden_dim, self.action_dim),
        )
        final = self.delayed_residual[-1]
        assert isinstance(final, nn.Linear)
        nn.init.zeros_(final.weight)
        nn.init.zeros_(final.bias)
        for parameter in self.delayed_residual.parameters():
            parameter.requires_grad_(False)
        self.maximum_centering_error = 0.0

    def reset_centering_audit(self) -> None:
        self.maximum_centering_error = 0.0

    def _step_action_mean_residuals(
        self,
        *,
        encoded: torch.Tensor,
        context: torch.Tensor,
        observations: torch.Tensor,
        active_mask: torch.Tensor,
        hidden: torch.Tensor,
    ) -> torch.Tensor:
        expanded_context = context.unsqueeze(1).expand(
            -1, self.member_capacity, -1
        )
        features = torch.cat(
            (
                encoded.detach(),
                expanded_context.detach(),
                hidden.detach(),
                observations.detach(),
            ),
            dim=-1,
        )
        centered = center_active_residuals(
            self.delayed_residual(features), active_mask
        )
        error = float(
            torch.abs(centered.sum(dim=1)).max().detach().cpu()
        )
        self.maximum_centering_error = max(
            self.maximum_centering_error, error
        )
        return centered


class ActiveSetCenteredResidualPolicy(FastAnchoredResidualPolicy):
    """G19 fast-anchor mechanics with a G20 centered residual core."""

    def __init__(
        self,
        observation_dim: int,
        critic_state_dim: int,
        *,
        member_capacity: int,
        action_dim: int,
        hidden_dim: int = 32,
        current_observation_residual: bool = True,
    ) -> None:
        super().__init__(
            observation_dim,
            critic_state_dim,
            member_capacity=member_capacity,
            action_dim=action_dim,
            hidden_dim=hidden_dim,
            current_observation_residual=current_observation_residual,
            policy_type=CenteredResidualContinuousRosterPolicy,
        )

    @property
    def maximum_centering_error(self) -> float:
        return float(self.policy.maximum_centering_error)

    def reset_centering_audit(self) -> None:
        self.policy.reset_centering_audit()


def optimize_centered_delayed_update(
    model: ActiveSetCenteredResidualPolicy,
    residual_optimizer: torch.optim.Optimizer,
    critic_optimizer: torch.optim.Optimizer,
    trajectory: AnchoredRosterTrajectory,
    *,
    device: torch.device,
    ppo_passes: int,
    gamma: float,
) -> dict[str, float]:
    """Update only the centered residual with successor-value actor credit."""

    if model.phase != "delayed":
        raise RuntimeError("G20 delayed update requires delayed phase")
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
    residual_parameters = model.residual_parameters()
    critic_parameters = model.critic_parameters()
    totals = {
        name: 0.0
        for name in (
            "fast_policy_loss",
            "successor_policy_loss",
            "slow_value_loss",
            "immediate_baseline_loss",
            "successor_baseline_loss",
            "residual_gradient_norm",
            "critic_gradient_norm",
        )
    }
    finite = True
    model.train()
    for _ in range(int(ppo_passes)):
        replay = replay_trajectory(model, trajectory, device=device)
        fast_loss = _channel_policy_loss(
            replay, trajectory, credit.immediate_residual
        )
        successor_loss = _channel_policy_loss(
            replay, trajectory, credit.successor_residual
        )
        residual_optimizer.zero_grad(set_to_none=True)
        successor_loss.backward()
        residual_gradient_norm = torch.nn.utils.clip_grad_norm_(
            residual_parameters, GRADIENT_CLIP
        )
        residual_optimizer.step()

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
        immediate_loss = F.mse_loss(
            replay.immediate_baselines,
            trajectory.rewards.to(device).detach(),
        )
        successor_baseline_loss = F.mse_loss(
            replay.successor_baselines,
            credit.successor_targets.to(device),
        )
        critic_loss = (
            slow_value_loss + immediate_loss + successor_baseline_loss
        )
        critic_optimizer.zero_grad(set_to_none=True)
        critic_loss.backward()
        critic_gradient_norm = torch.nn.utils.clip_grad_norm_(
            critic_parameters, GRADIENT_CLIP
        )
        critic_optimizer.step()
        finite = finite and all(
            bool(torch.isfinite(value))
            for value in (
                fast_loss,
                successor_loss,
                critic_loss,
                residual_gradient_norm,
                critic_gradient_norm,
            )
        )
        totals["fast_policy_loss"] += float(fast_loss.detach().cpu())
        totals["successor_policy_loss"] += float(successor_loss.detach().cpu())
        totals["slow_value_loss"] += float(slow_value_loss.detach().cpu())
        totals["immediate_baseline_loss"] += float(immediate_loss.detach().cpu())
        totals["successor_baseline_loss"] += float(
            successor_baseline_loss.detach().cpu()
        )
        totals["residual_gradient_norm"] += float(
            residual_gradient_norm.detach().cpu()
        )
        totals["critic_gradient_norm"] += float(
            critic_gradient_norm.detach().cpu()
        )
    for name in totals:
        totals[name] /= float(ppo_passes)
    totals.update(errors)
    totals["maximum_centering_error"] = model.maximum_centering_error
    totals["finite_update"] = float(finite)
    totals["optimizer_steps"] = float(2 * ppo_passes)
    return totals
