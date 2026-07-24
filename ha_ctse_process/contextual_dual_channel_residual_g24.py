"""Actor-contextual frozen-anchor dual-channel residual for G24."""

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


class ContextualResidualContinuousRosterPolicy(ContinuousRosterPolicy):
    """Base actor plus an unrestricted current-set delayed proposal."""

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
        proposals = self.delayed_residual(features)
        return proposals * active_mask.to(proposals.dtype).unsqueeze(-1)


class ContextualDualChannelResidualPolicy(FastAnchoredResidualPolicy):
    """Frozen fast actor plus a direct actor-contextual residual head."""

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
            policy_type=ContextualResidualContinuousRosterPolicy,
        )


def optimize_contextual_dual_channel_update(
    model: ContextualDualChannelResidualPolicy,
    residual_optimizer: torch.optim.Optimizer,
    critic_optimizer: torch.optim.Optimizer,
    trajectory: AnchoredRosterTrajectory,
    *,
    device: torch.device,
    ppo_passes: int,
    gamma: float,
) -> dict[str, float]:
    """Update only the residual with equal immediate/successor PPO credit."""

    if model.phase != "delayed":
        raise RuntimeError("G24 delayed update requires delayed phase")
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
            "policy_loss",
            "immediate_policy_loss",
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
        immediate_policy_loss = _channel_policy_loss(
            replay, trajectory, credit.immediate_residual
        )
        successor_policy_loss = _channel_policy_loss(
            replay, trajectory, credit.successor_residual
        )
        policy_loss = 0.5 * (
            immediate_policy_loss + successor_policy_loss
        )
        residual_optimizer.zero_grad(set_to_none=True)
        policy_loss.backward()
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
        finite = finite and all(
            bool(torch.isfinite(value))
            for value in (
                policy_loss,
                immediate_policy_loss,
                successor_policy_loss,
                critic_loss,
                residual_gradient_norm,
                critic_gradient_norm,
            )
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
        totals["residual_gradient_norm"] += float(
            residual_gradient_norm.detach().cpu()
        )
        totals["critic_gradient_norm"] += float(
            critic_gradient_norm.detach().cpu()
        )
    for name in totals:
        totals[name] /= float(ppo_passes)
    totals.update(errors)
    totals["immediate_channel_weight"] = 0.5
    totals["successor_channel_weight"] = 0.5
    totals["finite_update"] = float(finite)
    totals["optimizer_steps"] = float(2 * ppo_passes)
    return totals
