"""Return-to-go successor credit with G30 direction balancing."""

from __future__ import annotations

import torch

from ha_ctse_process.anchored_residual_g19 import (
    AnchoredCredit,
    AnchoredRosterTrajectory,
    _discounted_returns,
)
from ha_ctse_process.direction_balanced_full_actor_g30 import (
    DirectionBalancedFullActorPolicy,
    optimize_direction_balanced_credit_update,
)


def compute_return_to_go_credit(
    *,
    rewards: torch.Tensor,
    slow_values: torch.Tensor,
    immediate_baselines: torch.Tensor,
    successor_baselines: torch.Tensor,
    terminals: torch.Tensor,
    gamma: float,
) -> AnchoredCredit:
    """Build a detached future tail excluding the current reward."""

    rows = (slow_values, immediate_baselines, successor_baselines, terminals)
    if rewards.ndim != 2 or any(row.shape != rewards.shape for row in rows):
        raise ValueError("G31 credit expects matching [time,batch] rows")
    if terminals.dtype != torch.bool:
        raise ValueError("G31 terminal mask must be bool")
    if not 0.0 <= float(gamma) <= 1.0:
        raise ValueError("G31 gamma left [0,1]")
    if any(
        not bool(torch.isfinite(row).all())
        for row in (
            rewards,
            slow_values,
            immediate_baselines,
            successor_baselines,
        )
    ):
        raise ValueError("G31 credit received non-finite values")
    future_targets = torch.empty_like(rewards)
    running = torch.zeros(
        rewards.shape[1], dtype=rewards.dtype, device=rewards.device
    )
    for time in range(rewards.shape[0] - 1, -1, -1):
        future = (
            float(gamma)
            * (~terminals[time]).to(rewards.dtype)
            * running
        )
        future_targets[time] = future
        running = rewards[time].detach() + future
    future_targets = future_targets.detach()
    return AnchoredCredit(
        immediate_residual=(
            rewards.detach() - immediate_baselines.detach()
        ),
        successor_targets=future_targets,
        successor_residual=(
            future_targets - successor_baselines.detach()
        ),
        slow_return_targets=_discounted_returns(
            rewards, terminals, torch.zeros_like(running), gamma=float(gamma)
        ),
    )


class ReturnToGoDirectionBalancedFullActorPolicy(
    DirectionBalancedFullActorPolicy
):
    """Fresh G31 checkpoint identity over the unchanged G30 actor."""


def optimize_return_to_go_direction_balanced_update(
    model: ReturnToGoDirectionBalancedFullActorPolicy,
    actor_optimizer: torch.optim.Optimizer,
    critic_optimizer: torch.optim.Optimizer,
    trajectory: AnchoredRosterTrajectory,
    *,
    device: torch.device,
    ppo_passes: int,
    gamma: float,
) -> dict[str, float]:
    metrics = optimize_direction_balanced_credit_update(
        model,
        actor_optimizer,
        critic_optimizer,
        trajectory,
        device=device,
        ppo_passes=ppo_passes,
        gamma=gamma,
        credit_function=compute_return_to_go_credit,
    )
    terminals = torch.zeros_like(
        trajectory.rewards, dtype=torch.bool, device=device
    )
    terminals[-1] = True
    credit = compute_return_to_go_credit(
        rewards=trajectory.rewards.to(device),
        slow_values=trajectory.old_values.to(device),
        immediate_baselines=trajectory.old_immediate_baselines.to(device),
        successor_baselines=trajectory.old_successor_baselines.to(device),
        terminals=terminals,
        gamma=float(gamma),
    )
    metrics["maximum_return_to_go_target_absolute_value"] = float(
        credit.successor_targets.detach().abs().max().cpu()
    )
    metrics["terminal_return_to_go_error"] = float(
        credit.successor_targets[terminals].detach().abs().max().cpu()
    )
    return metrics
