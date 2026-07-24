"""Source-neutral fast-anchor and projected delayed-residual policy for G19."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Sequence

import torch
from torch import nn
from torch.nn import functional as F

from ha_ctse_process.continuous_roster_policy import (
    ContinuousRosterPolicy,
    ContinuousStepOutput,
)


PPO_CLIP = 0.20
VALUE_CLIP = 0.20
VALUE_COEFFICIENT = 0.50
ENTROPY_COEFFICIENT = 0.01
GRADIENT_CLIP = 0.50


class ResidualContinuousRosterPolicy(ContinuousRosterPolicy):
    """Continuous policy whose additive delayed head starts at exact zero."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.delayed_residual = nn.Sequential(
            nn.Linear(
                self.hidden_dim + self.action_dim + self.observation_dim,
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

    def _action_mean_for_member(
        self,
        *,
        candidate: torch.Tensor,
        prefix_fraction: torch.Tensor,
        observation: torch.Tensor,
    ) -> torch.Tensor:
        anchor = super()._action_mean_for_member(
            candidate=candidate,
            prefix_fraction=prefix_fraction,
            observation=observation,
        )
        features = torch.cat(
            (
                candidate.detach(),
                prefix_fraction.detach(),
                observation.detach(),
            ),
            dim=-1,
        )
        return anchor + self.delayed_residual(features)


class FastAnchoredResidualPolicy(nn.Module):
    """Two-phase policy with one immutable fast actor and one delayed head."""

    def __init__(
        self,
        observation_dim: int,
        critic_state_dim: int,
        *,
        member_capacity: int,
        action_dim: int,
        hidden_dim: int = 32,
        current_observation_residual: bool = True,
        policy_type: type[ContinuousRosterPolicy] = ResidualContinuousRosterPolicy,
    ) -> None:
        super().__init__()
        self.member_capacity = int(member_capacity)
        self.critic_state_dim = int(critic_state_dim)
        self.policy = policy_type(
            observation_dim,
            critic_state_dim,
            member_capacity=member_capacity,
            action_dim=action_dim,
            hidden_dim=hidden_dim,
            current_observation_residual=current_observation_residual,
        )
        for parameter in self.policy.critic.parameters():
            parameter.requires_grad_(False)
        self.slow_critic = nn.Sequential(
            nn.Linear(self.critic_state_dim + self.member_capacity, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )
        for parameter in self.slow_critic.parameters():
            parameter.requires_grad_(False)
        self.credit_baselines = nn.Sequential(
            nn.Linear(self.critic_state_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 2),
        )
        self.phase = "fast"

    @property
    def hidden_dim(self) -> int:
        return self.policy.hidden_dim

    @property
    def log_std(self) -> nn.Parameter:
        return self.policy.log_std

    @property
    def parameter_count(self) -> int:
        return int(sum(parameter.numel() for parameter in self.parameters()))

    def forward_step(self, **arguments: Any) -> ContinuousStepOutput:
        output = self.policy.forward_step(**arguments)
        critic_state = arguments["critic_state"]
        active_mask = arguments["active_mask"]
        slow_value = self.slow_critic(
            torch.cat(
                (critic_state, active_mask.to(critic_state.dtype)), dim=-1
            )
        ).squeeze(-1)
        return replace(output, value=slow_value)

    def baseline_values(
        self, critic_states: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if critic_states.shape[-1] != self.critic_state_dim:
            raise ValueError("G19 baseline critic-state shape mismatch")
        values = self.credit_baselines(critic_states)
        return values[..., 0], values[..., 1]

    def fast_actor_parameters(self) -> tuple[nn.Parameter, ...]:
        return tuple(
            parameter
            for name, parameter in self.policy.named_parameters()
            if not name.startswith("delayed_residual.")
            and not name.startswith("critic.")
            and parameter.requires_grad
        )

    def residual_parameters(self) -> tuple[nn.Parameter, ...]:
        return tuple(self.policy.delayed_residual.parameters())

    def critic_parameters(self) -> tuple[nn.Parameter, ...]:
        return tuple(self.slow_critic.parameters()) + tuple(
            self.credit_baselines.parameters()
        )

    def anchor_state(self) -> dict[str, torch.Tensor]:
        return {
            name: value.detach().cpu().clone()
            for name, value in self.policy.state_dict().items()
            if not name.startswith("delayed_residual.")
        }

    def begin_delayed_phase(self) -> None:
        if self.phase != "fast":
            raise RuntimeError("G19 delayed phase may begin exactly once")
        if self.residual_output_layer_maximum_absolute_value() != 0.0:
            raise RuntimeError("G19 residual must be exact zero at phase change")
        for parameter in self.policy.parameters():
            parameter.requires_grad_(False)
        for parameter in self.policy.delayed_residual.parameters():
            parameter.requires_grad_(True)
        for parameter in self.slow_critic.parameters():
            parameter.requires_grad_(True)
        self.phase = "delayed"

    def residual_maximum_absolute_value(self) -> float:
        return max(
            float(parameter.detach().abs().max().cpu())
            for parameter in self.policy.delayed_residual.parameters()
        )

    def residual_output_layer_maximum_absolute_value(self) -> float:
        final = self.policy.delayed_residual[-1]
        assert isinstance(final, nn.Linear)
        return max(
            float(parameter.detach().abs().max().cpu())
            for parameter in final.parameters()
        )


@dataclass
class AnchoredRosterTrajectory:
    observations: torch.Tensor
    active_mask: torch.Tensor
    critic_states: torch.Tensor
    actions: torch.Tensor
    pre_tanh_actions: torch.Tensor
    old_log_probs: torch.Tensor
    old_values: torch.Tensor
    old_immediate_baselines: torch.Tensor
    old_successor_baselines: torch.Tensor
    rewards: torch.Tensor
    hidden_before: torch.Tensor
    hidden_after: torch.Tensor
    prefix_action_sums: torch.Tensor
    outcomes: tuple[Any, ...]
    ledgers: tuple[Any, ...]

    @property
    def active_token_count(self) -> int:
        return int(self.active_mask.sum().item())


def attach_credit_baselines(
    model: FastAnchoredResidualPolicy,
    trajectory: Any,
    *,
    device: torch.device,
) -> AnchoredRosterTrajectory:
    with torch.no_grad():
        immediate, successor = model.baseline_values(
            trajectory.critic_states.to(device)
        )
    return AnchoredRosterTrajectory(
        observations=trajectory.observations,
        active_mask=trajectory.active_mask,
        critic_states=trajectory.critic_states,
        actions=trajectory.actions,
        pre_tanh_actions=trajectory.pre_tanh_actions,
        old_log_probs=trajectory.old_log_probs,
        old_values=trajectory.old_values,
        old_immediate_baselines=immediate.detach().cpu(),
        old_successor_baselines=successor.detach().cpu(),
        rewards=trajectory.rewards,
        hidden_before=trajectory.hidden_before,
        hidden_after=trajectory.hidden_after,
        prefix_action_sums=trajectory.prefix_action_sums,
        outcomes=tuple(trajectory.outcomes),
        ledgers=tuple(trajectory.ledgers),
    )


@dataclass
class AnchoredRosterReplay:
    log_probs: torch.Tensor
    entropies: torch.Tensor
    values: torch.Tensor
    immediate_baselines: torch.Tensor
    successor_baselines: torch.Tensor
    hidden_after: torch.Tensor
    prefix_action_sums: torch.Tensor
    active_mask: torch.Tensor


def replay_trajectory(
    model: FastAnchoredResidualPolicy,
    trajectory: AnchoredRosterTrajectory,
    *,
    device: torch.device,
) -> AnchoredRosterReplay:
    hidden = trajectory.hidden_before[0].to(device)
    outputs: list[ContinuousStepOutput] = []
    for time in range(trajectory.rewards.shape[0]):
        output = model.forward_step(
            observations=trajectory.observations[time].to(device),
            active_mask=trajectory.active_mask[time].to(device),
            critic_state=trajectory.critic_states[time].to(device),
            hidden=hidden,
            teacher_pre_tanh=trajectory.pre_tanh_actions[time].to(device),
        )
        outputs.append(output)
        hidden = output.next_hidden
    immediate, successor = model.baseline_values(
        trajectory.critic_states.to(device)
    )
    return AnchoredRosterReplay(
        log_probs=torch.stack([row.token_log_probs for row in outputs]),
        entropies=torch.stack([row.token_entropies for row in outputs]),
        values=torch.stack([row.value for row in outputs]),
        immediate_baselines=immediate,
        successor_baselines=successor,
        hidden_after=torch.stack([row.next_hidden for row in outputs]),
        prefix_action_sums=torch.stack([row.prefix_action_sums for row in outputs]),
        active_mask=trajectory.active_mask.to(device),
    )


def replay_errors(
    replay: AnchoredRosterReplay, trajectory: AnchoredRosterTrajectory
) -> dict[str, float]:
    device = replay.log_probs.device
    mask = replay.active_mask
    old_log_probs = trajectory.old_log_probs.to(device)
    return {
        "logp_max_error": float(
            torch.abs(replay.log_probs - old_log_probs)[mask].max().detach().cpu()
        ),
        "joint_logp_max_error": float(
            torch.abs(
                torch.where(mask, replay.log_probs - old_log_probs, 0.0).sum(dim=-1)
            )
            .max()
            .detach()
            .cpu()
        ),
        "value_max_error": float(
            torch.abs(replay.values - trajectory.old_values.to(device))
            .max()
            .detach()
            .cpu()
        ),
        "immediate_baseline_max_error": float(
            torch.abs(
                replay.immediate_baselines
                - trajectory.old_immediate_baselines.to(device)
            )
            .max()
            .detach()
            .cpu()
        ),
        "successor_baseline_max_error": float(
            torch.abs(
                replay.successor_baselines
                - trajectory.old_successor_baselines.to(device)
            )
            .max()
            .detach()
            .cpu()
        ),
        "hidden_max_error": float(
            torch.abs(replay.hidden_after - trajectory.hidden_after.to(device))
            .max()
            .detach()
            .cpu()
        ),
        "prefix_max_error": float(
            torch.abs(
                replay.prefix_action_sums
                - trajectory.prefix_action_sums.to(device)
            )
            .max()
            .detach()
            .cpu()
        ),
        "inactive_logp_max_abs": float(
            torch.where(mask, 0.0, replay.log_probs).abs().max().detach().cpu()
        ),
    }


@dataclass(frozen=True)
class AnchoredCredit:
    immediate_residual: torch.Tensor
    successor_targets: torch.Tensor
    successor_residual: torch.Tensor
    slow_return_targets: torch.Tensor


def _discounted_returns(
    rewards: torch.Tensor,
    terminals: torch.Tensor,
    bootstrap: torch.Tensor,
    *,
    gamma: float,
) -> torch.Tensor:
    targets = torch.empty_like(rewards)
    running = bootstrap.detach()
    for time in range(rewards.shape[0] - 1, -1, -1):
        running = rewards[time].detach() + float(gamma) * (
            ~terminals[time]
        ).to(rewards.dtype) * running
        targets[time] = running
    return targets


def compute_anchored_credit(
    *,
    rewards: torch.Tensor,
    slow_values: torch.Tensor,
    immediate_baselines: torch.Tensor,
    successor_baselines: torch.Tensor,
    terminals: torch.Tensor,
    gamma: float,
) -> AnchoredCredit:
    rows = (slow_values, immediate_baselines, successor_baselines, terminals)
    if rewards.ndim != 2 or any(row.shape != rewards.shape for row in rows):
        raise ValueError("G19 credit expects matching [time,batch] rows")
    if terminals.dtype != torch.bool:
        raise ValueError("G19 terminal mask must be bool")
    if not 0.0 <= float(gamma) <= 1.0:
        raise ValueError("G19 gamma left [0,1]")
    if any(
        not bool(torch.isfinite(row).all())
        for row in (rewards, slow_values, immediate_baselines, successor_baselines)
    ):
        raise ValueError("G19 credit received non-finite values")
    bootstrap = torch.zeros(
        rewards.shape[1], dtype=rewards.dtype, device=rewards.device
    )
    next_values = torch.cat((slow_values[1:], bootstrap.unsqueeze(0)), dim=0)
    successor_targets = (
        float(gamma)
        * (~terminals).to(rewards.dtype)
        * next_values.detach()
    )
    return AnchoredCredit(
        immediate_residual=rewards.detach() - immediate_baselines.detach(),
        successor_targets=successor_targets,
        successor_residual=successor_targets - successor_baselines.detach(),
        slow_return_targets=_discounted_returns(
            rewards, terminals, bootstrap, gamma=float(gamma)
        ),
    )


def normalize_advantage(advantage: torch.Tensor) -> torch.Tensor:
    if advantage.ndim != 2 or not bool(torch.isfinite(advantage).all()):
        raise ValueError("G19 advantage must be finite [time,batch]")
    return (advantage - advantage.mean()) / (
        advantage.std(unbiased=False) + 1e-8
    )


def _channel_policy_loss(
    replay: AnchoredRosterReplay,
    trajectory: AnchoredRosterTrajectory,
    advantage: torch.Tensor,
) -> torch.Tensor:
    device = replay.log_probs.device
    mask = replay.active_mask
    ratio = torch.exp(replay.log_probs - trajectory.old_log_probs.to(device))
    expanded = normalize_advantage(advantage.to(device)).unsqueeze(-1)
    surrogate = torch.minimum(
        ratio * expanded,
        torch.clamp(ratio, 1.0 - PPO_CLIP, 1.0 + PPO_CLIP) * expanded,
    )
    active_count = mask.sum(dim=-1).clamp_min(1)
    return -(
        torch.where(mask, surrogate, 0.0).sum(dim=-1) / active_count
    ).mean()


def optimize_fast_anchor_update(
    model: FastAnchoredResidualPolicy,
    optimizer: torch.optim.Optimizer,
    trajectory: AnchoredRosterTrajectory,
    *,
    device: torch.device,
    ppo_passes: int,
) -> dict[str, float]:
    if model.phase != "fast":
        raise RuntimeError("G19 fast update requires fast phase")
    with torch.no_grad():
        errors = replay_errors(
            replay_trajectory(model, trajectory, device=device), trajectory
        )
    advantage = (
        trajectory.rewards.to(device)
        - trajectory.old_immediate_baselines.to(device)
    ).detach()
    trainable = model.fast_actor_parameters() + tuple(
        model.credit_baselines.parameters()
    )
    totals = {
        name: 0.0
        for name in (
            "fast_policy_loss",
            "immediate_baseline_loss",
            "entropy",
            "gradient_norm",
        )
    }
    finite = True
    model.train()
    for _ in range(int(ppo_passes)):
        replay = replay_trajectory(model, trajectory, device=device)
        policy_loss = _channel_policy_loss(replay, trajectory, advantage)
        immediate_loss = F.mse_loss(
            replay.immediate_baselines,
            trajectory.rewards.to(device).detach(),
        )
        active_count = replay.active_mask.sum(dim=-1).clamp_min(1)
        entropy = (
            torch.where(replay.active_mask, replay.entropies, 0.0).sum(dim=-1)
            / active_count
        ).mean()
        loss = (
            policy_loss
            + VALUE_COEFFICIENT * immediate_loss
            - ENTROPY_COEFFICIENT * entropy
        )
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        gradient_norm = torch.nn.utils.clip_grad_norm_(
            trainable, GRADIENT_CLIP
        )
        finite = finite and bool(torch.isfinite(loss)) and bool(
            torch.isfinite(gradient_norm)
        )
        optimizer.step()
        totals["fast_policy_loss"] += float(policy_loss.detach().cpu())
        totals["immediate_baseline_loss"] += float(immediate_loss.detach().cpu())
        totals["entropy"] += float(entropy.detach().cpu())
        totals["gradient_norm"] += float(gradient_norm.detach().cpu())
    for name in totals:
        totals[name] /= float(ppo_passes)
    totals.update(errors)
    totals["finite_update"] = float(finite)
    totals["optimizer_steps"] = float(ppo_passes)
    return totals


@dataclass(frozen=True)
class ProjectionResult:
    gradients: tuple[torch.Tensor, ...]
    pre_dot: float
    post_dot: float
    conflict: bool


def project_delayed_gradients(
    delayed: Sequence[torch.Tensor | None],
    immediate: Sequence[torch.Tensor | None],
    parameters: Sequence[nn.Parameter],
) -> ProjectionResult:
    if not (len(delayed) == len(immediate) == len(parameters)) or not parameters:
        raise ValueError("G19 gradient projection inventory mismatch")
    delayed_rows = tuple(
        torch.zeros_like(parameter) if row is None else row
        for row, parameter in zip(delayed, parameters)
    )
    immediate_rows = tuple(
        torch.zeros_like(parameter) if row is None else row
        for row, parameter in zip(immediate, parameters)
    )
    if any(
        row.shape != parameter.shape or not bool(torch.isfinite(row).all())
        for rows in (delayed_rows, immediate_rows)
        for row, parameter in zip(rows, parameters)
    ):
        raise ValueError("G19 gradient projection received invalid rows")
    dot = sum(
        (left * right).sum()
        for left, right in zip(delayed_rows, immediate_rows)
    )
    immediate_norm = sum((row * row).sum() for row in immediate_rows)
    conflict = bool(dot.detach() < 0.0 and immediate_norm.detach() > 0.0)
    if conflict:
        coefficient = dot / immediate_norm
        applied = tuple(
            left - coefficient * right
            for left, right in zip(delayed_rows, immediate_rows)
        )
    else:
        applied = delayed_rows
    post = sum(
        (left * right).sum()
        for left, right in zip(applied, immediate_rows)
    )
    return ProjectionResult(
        gradients=applied,
        pre_dot=float(dot.detach().cpu()),
        post_dot=float(post.detach().cpu()),
        conflict=conflict,
    )


def optimize_delayed_residual_update(
    model: FastAnchoredResidualPolicy,
    residual_optimizer: torch.optim.Optimizer,
    critic_optimizer: torch.optim.Optimizer,
    trajectory: AnchoredRosterTrajectory,
    *,
    device: torch.device,
    ppo_passes: int,
    gamma: float,
) -> dict[str, float]:
    if model.phase != "delayed":
        raise RuntimeError("G19 delayed update requires delayed phase")
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
            "projection_pre_dot",
            "projection_post_dot",
            "projection_conflict",
        )
    }
    finite = True
    minimum_projection_post_dot = float("inf")
    model.train()
    for _ in range(int(ppo_passes)):
        replay = replay_trajectory(model, trajectory, device=device)
        fast_loss = _channel_policy_loss(
            replay, trajectory, credit.immediate_residual
        )
        successor_loss = _channel_policy_loss(
            replay, trajectory, credit.successor_residual
        )
        fast_gradients = torch.autograd.grad(
            fast_loss,
            residual_parameters,
            retain_graph=True,
            allow_unused=True,
        )
        delayed_gradients = torch.autograd.grad(
            successor_loss,
            residual_parameters,
            allow_unused=True,
        )
        projection = project_delayed_gradients(
            delayed_gradients, fast_gradients, residual_parameters
        )
        residual_optimizer.zero_grad(set_to_none=True)
        for parameter, gradient in zip(
            residual_parameters, projection.gradients
        ):
            parameter.grad = gradient.detach().clone()
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
        totals["projection_pre_dot"] += projection.pre_dot
        totals["projection_post_dot"] += projection.post_dot
        totals["projection_conflict"] += float(projection.conflict)
        minimum_projection_post_dot = min(
            minimum_projection_post_dot, projection.post_dot
        )
    for name in totals:
        totals[name] /= float(ppo_passes)
    totals.update(errors)
    totals["minimum_projection_post_dot"] = float(
        minimum_projection_post_dot
    )
    totals["finite_update"] = float(finite)
    totals["optimizer_steps"] = float(2 * ppo_passes)
    return totals


def maximum_state_difference(
    left: dict[str, torch.Tensor], right: dict[str, torch.Tensor]
) -> float:
    if left.keys() != right.keys():
        return float("inf")
    return max(
        float(torch.max(torch.abs(left[name] - right[name])).item())
        for name in left
    )
