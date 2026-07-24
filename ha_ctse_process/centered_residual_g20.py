"""Environment-neutral active-set-centered residual and Q_slow credit for G20.

G20 keeps the G17 continuous-roster actor as a trained-then-frozen fast path,
exactly as closed G19 did, and differs from G19 in precisely two mechanism
ways: gradient projection is deleted (not reused, not parameterized) in favor
of exact active-set centering of an observation-only pre-tanh residual, and
the shared scalar slow credit is replaced by a member-resolved leave-one-out
counterfactual advantage built from a slow action-critic ``Q_slow``.  Adam is
used for every trainable group in both phases.  This module owns only the
policy subclass, ``Q_slow``, the member-resolved credit algebra and both
update rules; it stays neutral to the calling environment/source exactly like
its G17/G18/G19 counterparts.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Callable

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


@dataclass
class CenteredStepOutput:
    actions: torch.Tensor
    pre_tanh_actions: torch.Tensor
    token_log_probs: torch.Tensor
    token_entropies: torch.Tensor
    value: torch.Tensor
    next_hidden: torch.Tensor
    prefix_action_sums: torch.Tensor
    likelihood_mask: torch.Tensor
    centered_residual: torch.Tensor


def center_residual_over_active_set(
    raw: torch.Tensor, active_mask: torch.Tensor
) -> torch.Tensor:
    """Exactly center an observation-only residual table over the active set.

    Member ``i`` receives ``f(o_i) - (1/N) * sum_{j active} f(o_j)``.  The
    result therefore sums to zero over the active set per action coordinate
    per batch row, and inactive rows receive exactly zero.
    """

    if raw.shape[:-1] != active_mask.shape:
        raise ValueError(
            "G20 centering shape mismatch between residual table and active mask"
        )
    if active_mask.dtype != torch.bool:
        raise ValueError("G20 centering active mask must be bool")
    dtype = raw.dtype
    mask = active_mask.to(dtype).unsqueeze(-1)
    active_count = active_mask.sum(dim=-1).to(dtype).clamp_min(1.0).unsqueeze(-1)
    active_mean = (raw * mask).sum(dim=-2) / active_count
    return torch.where(
        active_mask.unsqueeze(-1),
        raw - active_mean.unsqueeze(-2),
        torch.zeros_like(raw),
    )


class CenteredCounterfactualRosterPolicy(ContinuousRosterPolicy):
    """Continuous policy whose additive delayed head is exactly active-set centered.

    The delayed head is a pure function of each member's own observation
    (``f(o_i)``); there is no gradient projection anywhere.  ``forward_step``
    is overridden to precompute the per-step centered table (and the shared
    active mean it requires), and ``_action_mean_for_member`` applies the
    member-specific centered residual on top of the unchanged base mean.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.delayed_residual = nn.Sequential(
            nn.Linear(self.observation_dim, self.hidden_dim),
            nn.Tanh(),
            nn.Linear(self.hidden_dim, self.action_dim),
        )
        final = self.delayed_residual[-1]
        assert isinstance(final, nn.Linear)
        nn.init.zeros_(final.weight)
        nn.init.zeros_(final.bias)
        for parameter in self.delayed_residual.parameters():
            parameter.requires_grad_(False)
        self._pending_active_mean: torch.Tensor | None = None

    def forward_step(
        self,
        *,
        observations: torch.Tensor,
        active_mask: torch.Tensor,
        critic_state: torch.Tensor,
        hidden: torch.Tensor,
        sampling_noise: torch.Tensor | None = None,
        teacher_pre_tanh: torch.Tensor | None = None,
        deterministic: bool = False,
    ) -> CenteredStepOutput:
        expected_observation_shape = (self.member_capacity, self.observation_dim)
        if (
            observations.ndim != 3
            or observations.shape[1:] != expected_observation_shape
        ):
            raise ValueError("G20 centered policy observation shape mismatch")
        if active_mask.dtype != torch.bool:
            raise ValueError("G20 centered policy active mask must be bool")

        raw = self.delayed_residual(observations.detach())
        dtype = raw.dtype
        mask = active_mask.to(dtype).unsqueeze(-1)
        active_count = active_mask.sum(dim=-1).to(dtype).clamp_min(1.0).unsqueeze(-1)
        self._pending_active_mean = (raw * mask).sum(dim=-2) / active_count
        centered = center_residual_over_active_set(raw, active_mask)

        base_output = super().forward_step(
            observations=observations,
            active_mask=active_mask,
            critic_state=critic_state,
            hidden=hidden,
            sampling_noise=sampling_noise,
            teacher_pre_tanh=teacher_pre_tanh,
            deterministic=deterministic,
        )
        self._pending_active_mean = None
        return CenteredStepOutput(
            actions=base_output.actions,
            pre_tanh_actions=base_output.pre_tanh_actions,
            token_log_probs=base_output.token_log_probs,
            token_entropies=base_output.token_entropies,
            value=base_output.value,
            next_hidden=base_output.next_hidden,
            prefix_action_sums=base_output.prefix_action_sums,
            likelihood_mask=base_output.likelihood_mask,
            centered_residual=centered,
        )

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
        if self._pending_active_mean is None:
            raise RuntimeError(
                "G20 centered policy requires forward_step to precompute the active mean"
            )
        raw_member = self.delayed_residual(observation.detach())
        return anchor + (raw_member - self._pending_active_mean)


class FastCenteredCounterfactualResidualPolicy(nn.Module):
    """Two-phase policy: one immutable fast actor, one delayed centered head."""

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
        super().__init__()
        self.member_capacity = int(member_capacity)
        self.critic_state_dim = int(critic_state_dim)
        self.action_dim = int(action_dim)
        self.policy = CenteredCounterfactualRosterPolicy(
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
            nn.Linear(
                self.critic_state_dim
                + self.member_capacity
                + self.member_capacity * self.action_dim,
                hidden_dim,
            ),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )
        for parameter in self.slow_critic.parameters():
            parameter.requires_grad_(False)
        self.immediate_baseline = nn.Sequential(
            nn.Linear(self.critic_state_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
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

    def forward_step(self, **arguments: Any) -> CenteredStepOutput:
        output = self.policy.forward_step(**arguments)
        critic_state = arguments["critic_state"]
        active_mask = arguments["active_mask"]
        value = self.slow_action_value(
            critic_state, active_mask, output.centered_residual
        )
        return replace(output, value=value)

    def slow_action_value(
        self,
        critic_state: torch.Tensor,
        active_mask: torch.Tensor,
        residual_table: torch.Tensor,
    ) -> torch.Tensor:
        if critic_state.shape[-1] != self.critic_state_dim:
            raise ValueError("G20 slow critic state shape mismatch")
        if residual_table.shape[:-1] != active_mask.shape:
            raise ValueError("G20 slow critic residual/mask shape mismatch")
        flattened = residual_table.reshape(*residual_table.shape[:-2], -1)
        features = torch.cat(
            (critic_state, active_mask.to(critic_state.dtype), flattened), dim=-1
        )
        return self.slow_critic(features).squeeze(-1)

    def immediate_baseline_value(self, critic_states: torch.Tensor) -> torch.Tensor:
        if critic_states.shape[-1] != self.critic_state_dim:
            raise ValueError("G20 immediate baseline critic-state shape mismatch")
        return self.immediate_baseline(critic_states).squeeze(-1)

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
        return tuple(self.slow_critic.parameters())

    def anchor_state(self) -> dict[str, torch.Tensor]:
        return {
            name: value.detach().cpu().clone()
            for name, value in self.policy.state_dict().items()
            if not name.startswith("delayed_residual.")
        }

    def begin_delayed_phase(self) -> None:
        if self.phase != "fast":
            raise RuntimeError("G20 delayed phase may begin exactly once")
        if self.residual_output_layer_maximum_absolute_value() != 0.0:
            raise RuntimeError("G20 residual must be exact zero at phase change")
        for parameter in self.policy.parameters():
            parameter.requires_grad_(False)
        for parameter in self.immediate_baseline.parameters():
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
class CenteredRosterTrajectory:
    observations: torch.Tensor
    active_mask: torch.Tensor
    critic_states: torch.Tensor
    actions: torch.Tensor
    pre_tanh_actions: torch.Tensor
    old_log_probs: torch.Tensor
    old_values: torch.Tensor
    old_immediate_baselines: torch.Tensor
    old_centered_residual: torch.Tensor
    old_counterfactual_advantage: torch.Tensor
    rewards: torch.Tensor
    hidden_before: torch.Tensor
    hidden_after: torch.Tensor
    prefix_action_sums: torch.Tensor
    outcomes: tuple[Any, ...]
    ledgers: tuple[Any, ...]

    @property
    def active_token_count(self) -> int:
        return int(self.active_mask.sum().item())


@dataclass
class CenteredRosterReplay:
    log_probs: torch.Tensor
    entropies: torch.Tensor
    values: torch.Tensor
    immediate_baselines: torch.Tensor
    hidden_after: torch.Tensor
    prefix_action_sums: torch.Tensor
    active_mask: torch.Tensor
    centered_residual: torch.Tensor


def replay_trajectory(
    model: FastCenteredCounterfactualResidualPolicy,
    trajectory: Any,
    *,
    device: torch.device,
) -> CenteredRosterReplay:
    hidden = trajectory.hidden_before[0].to(device)
    outputs: list[CenteredStepOutput] = []
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
    immediate = model.immediate_baseline_value(trajectory.critic_states.to(device))
    return CenteredRosterReplay(
        log_probs=torch.stack([row.token_log_probs for row in outputs]),
        entropies=torch.stack([row.token_entropies for row in outputs]),
        values=torch.stack([row.value for row in outputs]),
        immediate_baselines=immediate,
        hidden_after=torch.stack([row.next_hidden for row in outputs]),
        prefix_action_sums=torch.stack([row.prefix_action_sums for row in outputs]),
        active_mask=trajectory.active_mask.to(device),
        centered_residual=torch.stack([row.centered_residual for row in outputs]),
    )


def replay_errors(
    replay: CenteredRosterReplay, trajectory: CenteredRosterTrajectory
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
        "centered_residual_max_error": float(
            torch.abs(
                replay.centered_residual
                - trajectory.old_centered_residual.to(device)
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
                replay.prefix_action_sums - trajectory.prefix_action_sums.to(device)
            )
            .max()
            .detach()
            .cpu()
        ),
        "inactive_logp_max_abs": float(
            torch.where(mask, 0.0, replay.log_probs).abs().max().detach().cpu()
        ),
    }


def compute_counterfactual_advantage(
    q_slow: Callable[[torch.Tensor, torch.Tensor, torch.Tensor], torch.Tensor],
    *,
    critic_state: torch.Tensor,
    active_mask: torch.Tensor,
    residual_table: torch.Tensor,
) -> torch.Tensor:
    """Member-resolved leave-one-out counterfactual advantage.

    ``A_slow[i] = Q_slow(s, R) - Q_slow(s, R with row i zeroed)``, detached,
    zero on every inactive row.
    """

    if residual_table.shape[:-1] != active_mask.shape:
        raise ValueError(
            "G20 counterfactual advantage residual/mask shape mismatch"
        )
    if active_mask.dtype != torch.bool:
        raise ValueError("G20 counterfactual advantage active mask must be bool")
    if not bool(torch.isfinite(residual_table).all()):
        raise ValueError("G20 counterfactual advantage received non-finite residual")
    capacity = residual_table.shape[-2]
    baseline = q_slow(critic_state, active_mask, residual_table)
    advantages = torch.zeros_like(active_mask, dtype=residual_table.dtype)
    for member in range(capacity):
        modified = residual_table.clone()
        modified[..., member, :] = 0.0
        counterfactual_value = q_slow(critic_state, active_mask, modified)
        advantages[..., member] = (baseline - counterfactual_value).detach()
    return torch.where(active_mask, advantages, torch.zeros_like(advantages))


def attach_slow_credit(
    model: FastCenteredCounterfactualResidualPolicy,
    trajectory: Any,
    *,
    device: torch.device,
) -> CenteredRosterTrajectory:
    with torch.no_grad():
        immediate = model.immediate_baseline_value(
            trajectory.critic_states.to(device)
        )
        replay = replay_trajectory(model, trajectory, device=device)
        advantage = compute_counterfactual_advantage(
            model.slow_action_value,
            critic_state=trajectory.critic_states.to(device),
            active_mask=trajectory.active_mask.to(device),
            residual_table=replay.centered_residual,
        )
    return CenteredRosterTrajectory(
        observations=trajectory.observations,
        active_mask=trajectory.active_mask,
        critic_states=trajectory.critic_states,
        actions=trajectory.actions,
        pre_tanh_actions=trajectory.pre_tanh_actions,
        old_log_probs=trajectory.old_log_probs,
        old_values=trajectory.old_values,
        old_immediate_baselines=immediate.detach().cpu(),
        old_centered_residual=replay.centered_residual.detach().cpu(),
        old_counterfactual_advantage=advantage.detach().cpu(),
        rewards=trajectory.rewards,
        hidden_before=trajectory.hidden_before,
        hidden_after=trajectory.hidden_after,
        prefix_action_sums=trajectory.prefix_action_sums,
        outcomes=tuple(trajectory.outcomes),
        ledgers=tuple(trajectory.ledgers),
    )


def normalize_team_advantage(advantage: torch.Tensor) -> torch.Tensor:
    if advantage.ndim != 2 or not bool(torch.isfinite(advantage).all()):
        raise ValueError("G20 team advantage must be finite [time,batch]")
    return (advantage - advantage.mean()) / (advantage.std(unbiased=False) + 1e-8)


def normalize_masked_advantage(
    advantage: torch.Tensor, active_mask: torch.Tensor
) -> torch.Tensor:
    if advantage.shape != active_mask.shape:
        raise ValueError("G20 masked advantage/active-mask shape mismatch")
    if not bool(torch.isfinite(advantage).all()):
        raise ValueError("G20 masked advantage must be finite")
    active = active_mask.to(advantage.dtype)
    count = active.sum().clamp_min(1.0)
    mean = (advantage * active).sum() / count
    variance = (torch.square(advantage - mean) * active).sum() / count
    std = torch.sqrt(variance)
    normalized = (advantage - mean) / (std + 1e-8)
    return torch.where(active_mask, normalized, torch.zeros_like(normalized))


def _team_policy_loss(
    replay: CenteredRosterReplay,
    trajectory: CenteredRosterTrajectory,
    advantage: torch.Tensor,
) -> torch.Tensor:
    device = replay.log_probs.device
    mask = replay.active_mask
    ratio = torch.exp(replay.log_probs - trajectory.old_log_probs.to(device))
    expanded = normalize_team_advantage(advantage.to(device)).unsqueeze(-1)
    surrogate = torch.minimum(
        ratio * expanded,
        torch.clamp(ratio, 1.0 - PPO_CLIP, 1.0 + PPO_CLIP) * expanded,
    )
    active_count = mask.sum(dim=-1).clamp_min(1)
    return -(
        torch.where(mask, surrogate, 0.0).sum(dim=-1) / active_count
    ).mean()


def _member_policy_loss(
    replay: CenteredRosterReplay,
    trajectory: CenteredRosterTrajectory,
    advantage: torch.Tensor,
) -> torch.Tensor:
    device = replay.log_probs.device
    mask = replay.active_mask
    ratio = torch.exp(replay.log_probs - trajectory.old_log_probs.to(device))
    normalized = normalize_masked_advantage(advantage.to(device), mask)
    surrogate = torch.minimum(
        ratio * normalized,
        torch.clamp(ratio, 1.0 - PPO_CLIP, 1.0 + PPO_CLIP) * normalized,
    )
    active_count = mask.sum().clamp_min(1)
    return -(torch.where(mask, surrogate, 0.0).sum() / active_count)


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


def optimize_fast_update(
    model: FastCenteredCounterfactualResidualPolicy,
    optimizer: torch.optim.Optimizer,
    trajectory: CenteredRosterTrajectory,
    *,
    device: torch.device,
    ppo_passes: int,
) -> dict[str, float]:
    if model.phase != "fast":
        raise RuntimeError("G20 fast update requires fast phase")
    with torch.no_grad():
        errors = replay_errors(
            replay_trajectory(model, trajectory, device=device), trajectory
        )
    advantage = (
        trajectory.rewards.to(device) - trajectory.old_immediate_baselines.to(device)
    ).detach()
    trainable = model.fast_actor_parameters() + tuple(
        model.immediate_baseline.parameters()
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
        policy_loss = _team_policy_loss(replay, trajectory, advantage)
        immediate_loss = F.mse_loss(
            replay.immediate_baselines, trajectory.rewards.to(device).detach()
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
        gradient_norm = torch.nn.utils.clip_grad_norm_(trainable, GRADIENT_CLIP)
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


def optimize_delayed_update(
    model: FastCenteredCounterfactualResidualPolicy,
    residual_optimizer: torch.optim.Optimizer,
    critic_optimizer: torch.optim.Optimizer,
    trajectory: CenteredRosterTrajectory,
    *,
    device: torch.device,
    ppo_passes: int,
    gamma: float,
) -> dict[str, float]:
    if model.phase != "delayed":
        raise RuntimeError("G20 delayed update requires delayed phase")
    terminals = torch.zeros_like(
        trajectory.rewards, dtype=torch.bool, device=device
    )
    terminals[-1] = True
    bootstrap = torch.zeros(
        trajectory.rewards.shape[1], dtype=trajectory.rewards.dtype, device=device
    )
    slow_return_targets = _discounted_returns(
        trajectory.rewards.to(device), terminals, bootstrap, gamma=float(gamma)
    )
    advantage = trajectory.old_counterfactual_advantage.to(device).detach()
    with torch.no_grad():
        errors = replay_errors(
            replay_trajectory(model, trajectory, device=device), trajectory
        )
    residual_parameters = model.residual_parameters()
    critic_parameters = model.critic_parameters()
    totals = {
        name: 0.0
        for name in (
            "delayed_policy_loss",
            "slow_value_loss",
            "entropy",
            "residual_gradient_norm",
            "critic_gradient_norm",
        )
    }
    finite = True
    model.train()
    for _ in range(int(ppo_passes)):
        replay = replay_trajectory(model, trajectory, device=device)
        policy_loss = _member_policy_loss(replay, trajectory, advantage)
        active_count = replay.active_mask.sum(dim=-1).clamp_min(1)
        entropy = (
            torch.where(replay.active_mask, replay.entropies, 0.0).sum(dim=-1)
            / active_count
        ).mean()
        actor_loss = policy_loss
        residual_optimizer.zero_grad(set_to_none=True)
        actor_loss.backward()
        residual_gradient_norm = torch.nn.utils.clip_grad_norm_(
            residual_parameters, GRADIENT_CLIP
        )
        residual_optimizer.step()

        with torch.no_grad():
            replay_for_critic = replay_trajectory(model, trajectory, device=device)
        values = model.slow_action_value(
            trajectory.critic_states.to(device),
            replay_for_critic.active_mask,
            replay_for_critic.centered_residual,
        )
        old_values = trajectory.old_values.to(device)
        clipped_values = old_values + torch.clamp(
            values - old_values, -VALUE_CLIP, VALUE_CLIP
        )
        slow_value_loss = torch.maximum(
            torch.square(values - slow_return_targets),
            torch.square(clipped_values - slow_return_targets),
        ).mean()
        critic_optimizer.zero_grad(set_to_none=True)
        slow_value_loss.backward()
        critic_gradient_norm = torch.nn.utils.clip_grad_norm_(
            critic_parameters, GRADIENT_CLIP
        )
        critic_optimizer.step()

        finite = finite and all(
            bool(torch.isfinite(value))
            for value in (
                actor_loss,
                slow_value_loss,
                residual_gradient_norm,
                critic_gradient_norm,
            )
        )
        totals["delayed_policy_loss"] += float(policy_loss.detach().cpu())
        totals["slow_value_loss"] += float(slow_value_loss.detach().cpu())
        totals["entropy"] += float(entropy.detach().cpu())
        totals["residual_gradient_norm"] += float(
            residual_gradient_norm.detach().cpu()
        )
        totals["critic_gradient_norm"] += float(
            critic_gradient_norm.detach().cpu()
        )
    for name in totals:
        totals[name] /= float(ppo_passes)
    totals.update(errors)
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
