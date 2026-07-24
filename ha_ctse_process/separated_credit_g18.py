"""Environment-neutral fast/slow actor-credit algebra for G18."""

from __future__ import annotations

from dataclasses import dataclass, replace
from types import SimpleNamespace
from typing import Any, Iterable, Sequence

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from ha_ctse_process.continuous_roster_policy import (
    ContinuousRosterPolicy,
    ContinuousStepOutput,
)
from ha_ctse_process.continuous_service_roster_proxy_g17 import (
    ENTROPY_COEFFICIENT,
    GRADIENT_CLIP,
    PPO_CLIP,
    VALUE_CLIP,
    VALUE_COEFFICIENT,
)
from ha_ctse_process import delayed_battery_roster_g18 as battery_source


@dataclass(frozen=True)
class SeparatedCredit:
    immediate_residual: torch.Tensor
    successor_targets: torch.Tensor
    successor_residual: torch.Tensor
    actor_advantage: torch.Tensor
    token_actor_advantage: torch.Tensor
    slow_return_targets: torch.Tensor


def _validate_inputs(
    *,
    rewards: torch.Tensor,
    slow_values: torch.Tensor,
    bootstrap_slow_values: torch.Tensor,
    immediate_baselines: torch.Tensor,
    successor_baselines: torch.Tensor,
    terminals: torch.Tensor,
    active_mask: torch.Tensor,
    gamma: float,
) -> None:
    if rewards.ndim != 2:
        raise ValueError("G18 separated credit expects [time,batch] rewards")
    if any(
        row.shape != rewards.shape
        for row in (slow_values, immediate_baselines, successor_baselines, terminals)
    ):
        raise ValueError("G18 separated credit scalar trajectory shape mismatch")
    if terminals.dtype != torch.bool:
        raise ValueError("G18 separated credit terminal mask must be bool")
    if active_mask.ndim != 3 or active_mask.shape[:2] != rewards.shape:
        raise ValueError("G18 separated credit active mask shape mismatch")
    if active_mask.dtype != torch.bool:
        raise ValueError("G18 separated credit active mask must be bool")
    if bootstrap_slow_values.shape != (rewards.shape[1],):
        raise ValueError("G18 separated credit bootstrap shape mismatch")
    if not 0.0 <= float(gamma) <= 1.0:
        raise ValueError("G18 separated credit gamma left [0,1]")
    floating_rows = (
        rewards,
        slow_values,
        bootstrap_slow_values,
        immediate_baselines,
        successor_baselines,
    )
    if any(not bool(torch.isfinite(row).all()) for row in floating_rows):
        raise ValueError("G18 separated credit received non-finite values")


def _next_values(
    slow_values: torch.Tensor, bootstrap_slow_values: torch.Tensor
) -> torch.Tensor:
    return torch.cat(
        (slow_values[1:], bootstrap_slow_values.unsqueeze(0)), dim=0
    )


def _discounted_returns(
    rewards: torch.Tensor,
    terminals: torch.Tensor,
    bootstrap_slow_values: torch.Tensor,
    *,
    gamma: float,
) -> torch.Tensor:
    targets = torch.empty_like(rewards)
    running = bootstrap_slow_values.detach()
    for time in range(rewards.shape[0] - 1, -1, -1):
        continuation = (~terminals[time]).to(rewards.dtype)
        running = rewards[time].detach() + float(gamma) * continuation * running
        targets[time] = running
    return targets


def compute_separated_credit(
    *,
    rewards: torch.Tensor,
    slow_values: torch.Tensor,
    bootstrap_slow_values: torch.Tensor,
    immediate_baselines: torch.Tensor,
    successor_baselines: torch.Tensor,
    terminals: torch.Tensor,
    active_mask: torch.Tensor,
    gamma: float,
) -> SeparatedCredit:
    """Keep immediate reward credit separate from centered successor value.

    The actor sees only detached residuals.  The successor term is evaluated
    once from the next state and centered by a current-state-only baseline.
    Inactive lifecycle rows receive exactly zero token advantage.
    """

    _validate_inputs(
        rewards=rewards,
        slow_values=slow_values,
        bootstrap_slow_values=bootstrap_slow_values,
        immediate_baselines=immediate_baselines,
        successor_baselines=successor_baselines,
        terminals=terminals,
        active_mask=active_mask,
        gamma=gamma,
    )
    detached_rewards = rewards.detach()
    immediate_residual = detached_rewards - immediate_baselines.detach()
    continuation = (~terminals).to(rewards.dtype)
    successor_targets = (
        float(gamma)
        * continuation
        * _next_values(slow_values, bootstrap_slow_values).detach()
    )
    successor_residual = successor_targets - successor_baselines.detach()
    actor_advantage = immediate_residual + successor_residual
    token_actor_advantage = actor_advantage.unsqueeze(-1) * active_mask.to(
        actor_advantage.dtype
    )
    slow_return_targets = _discounted_returns(
        rewards,
        terminals,
        bootstrap_slow_values,
        gamma=gamma,
    )
    return SeparatedCredit(
        immediate_residual=immediate_residual,
        successor_targets=successor_targets,
        successor_residual=successor_residual,
        actor_advantage=actor_advantage,
        token_actor_advantage=token_actor_advantage,
        slow_return_targets=slow_return_targets,
    )


def separated_critic_loss(
    *,
    slow_values: torch.Tensor,
    immediate_baselines: torch.Tensor,
    successor_baselines: torch.Tensor,
    credit: SeparatedCredit,
) -> torch.Tensor:
    if any(
        row.shape != credit.actor_advantage.shape
        for row in (slow_values, immediate_baselines, successor_baselines)
    ):
        raise ValueError("G18 separated critic shape mismatch")
    return (
        F.mse_loss(slow_values, credit.slow_return_targets)
        + F.mse_loss(immediate_baselines, credit.immediate_residual + immediate_baselines.detach())
        + F.mse_loss(successor_baselines, credit.successor_targets)
    )


class SeparatedCreditPolicy(nn.Module):
    """Continuous roster policy with current-state fast/successor baselines."""

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
        self.policy = ContinuousRosterPolicy(
            observation_dim,
            critic_state_dim,
            member_capacity=member_capacity,
            action_dim=action_dim,
            hidden_dim=hidden_dim,
            current_observation_residual=current_observation_residual,
        )
        self.critic_state_dim = int(critic_state_dim)
        for parameter in self.policy.critic.parameters():
            parameter.requires_grad_(False)
        self.slow_critic = nn.Sequential(
            nn.Linear(self.critic_state_dim + self.member_capacity, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )
        self.credit_baselines = nn.Sequential(
            nn.Linear(self.critic_state_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 2),
        )

    @property
    def hidden_dim(self) -> int:
        return self.policy.hidden_dim

    @property
    def parameter_count(self) -> int:
        return int(
            sum(
                parameter.numel()
                for parameter in self.parameters()
                if parameter.requires_grad
            )
        )

    @property
    def log_std(self) -> nn.Parameter:
        return self.policy.log_std

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
            raise ValueError("G18 separated baseline critic-state shape mismatch")
        values = self.credit_baselines(critic_states)
        return values[..., 0], values[..., 1]


@dataclass
class SeparatedRosterTrajectory:
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
    model: SeparatedCreditPolicy,
    trajectory: Any,
    *,
    device: torch.device,
) -> SeparatedRosterTrajectory:
    with torch.no_grad():
        immediate, successor = model.baseline_values(
            trajectory.critic_states.to(device)
        )
    return SeparatedRosterTrajectory(
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


def _battery_action_noise(
    episode_ids: Iterable[int], *, action_seed: int
) -> np.ndarray:
    rows = []
    for episode_id in episode_ids:
        rng = np.random.default_rng(
            np.random.SeedSequence([int(action_seed), int(episode_id), 180])
        )
        rows.append(
            rng.standard_normal(
                (
                    battery_source.HORIZON,
                    battery_source.CAPACITY,
                    battery_source.ACTION_DIM,
                )
            ).astype(np.float32)
        )
    if not rows:
        raise ValueError("G18 battery collection requires an episode")
    return np.stack(rows, axis=1)


def collect_battery_trajectory(
    model: SeparatedCreditPolicy,
    *,
    episode_ids: Iterable[int],
    action_seed: int,
    device: torch.device,
    deterministic: bool = False,
) -> SeparatedRosterTrajectory:
    ids = tuple(int(value) for value in episode_ids)
    if not ids:
        raise ValueError("G18 battery collection requires at least one episode")
    ledgers = tuple(
        battery_source.make_ledger(
            battery_source.GATE_SLOT_ORDERS[
                episode_id % len(battery_source.GATE_SLOT_ORDERS)
            ]
        )
        for episode_id in ids
    )
    environments = tuple(
        battery_source.BatteryRosterEnv(ledger) for ledger in ledgers
    )
    batch = len(ids)
    noise = _battery_action_noise(ids, action_seed=action_seed)
    hidden = torch.zeros(
        (batch, battery_source.CAPACITY, model.hidden_dim),
        dtype=torch.float32,
        device=device,
    )
    shapes = {
        "observations": (
            battery_source.HORIZON,
            batch,
            battery_source.CAPACITY,
            battery_source.OBSERVATION_DIM,
        ),
        "active_mask": (
            battery_source.HORIZON,
            batch,
            battery_source.CAPACITY,
        ),
        "critic_states": (
            battery_source.HORIZON,
            batch,
            battery_source.CRITIC_STATE_DIM,
        ),
        "actions": (
            battery_source.HORIZON,
            batch,
            battery_source.CAPACITY,
            battery_source.ACTION_DIM,
        ),
        "pre_tanh_actions": (
            battery_source.HORIZON,
            batch,
            battery_source.CAPACITY,
            battery_source.ACTION_DIM,
        ),
        "old_log_probs": (
            battery_source.HORIZON,
            batch,
            battery_source.CAPACITY,
        ),
        "old_values": (battery_source.HORIZON, batch),
        "rewards": (battery_source.HORIZON, batch),
        "hidden_before": (
            battery_source.HORIZON,
            batch,
            battery_source.CAPACITY,
            model.hidden_dim,
        ),
        "hidden_after": (
            battery_source.HORIZON,
            batch,
            battery_source.CAPACITY,
            model.hidden_dim,
        ),
        "prefix_action_sums": (
            battery_source.HORIZON,
            batch,
            battery_source.CAPACITY,
            battery_source.ACTION_DIM,
        ),
    }
    rows: dict[str, torch.Tensor] = {}
    for name, shape in shapes.items():
        dtype = torch.bool if name == "active_mask" else torch.float32
        rows[name] = torch.empty(shape, dtype=dtype)

    model.eval()
    with torch.no_grad():
        for time in range(battery_source.HORIZON):
            views = tuple(environment.observe() for environment in environments)
            observations = torch.as_tensor(
                np.stack([view.observations for view in views]), device=device
            )
            active_mask = torch.as_tensor(
                np.stack([view.active_mask for view in views]), device=device
            )
            critic_states = torch.as_tensor(
                np.stack([view.critic_state for view in views]), device=device
            )
            hidden_before = hidden.clone()
            arguments = {
                "observations": observations,
                "active_mask": active_mask,
                "critic_state": critic_states,
                "hidden": hidden,
            }
            if deterministic:
                output = model.forward_step(**arguments, deterministic=True)
            else:
                output = model.forward_step(
                    **arguments,
                    sampling_noise=torch.as_tensor(noise[time], device=device),
                )
            action_values = output.actions.detach().cpu().numpy()
            rewards = np.empty(batch, dtype=np.float32)
            for index, environment in enumerate(environments):
                reward, _terminal, _info = environment.step(action_values[index])
                rewards[index] = reward
            values = {
                "observations": observations,
                "active_mask": active_mask,
                "critic_states": critic_states,
                "actions": output.actions,
                "pre_tanh_actions": output.pre_tanh_actions,
                "old_log_probs": output.token_log_probs,
                "old_values": output.value,
                "rewards": torch.as_tensor(rewards, device=device),
                "hidden_before": hidden_before,
                "hidden_after": output.next_hidden,
                "prefix_action_sums": output.prefix_action_sums,
            }
            for name, value in values.items():
                rows[name][time].copy_(value.detach().cpu())
            hidden = output.next_hidden

    provisional = SimpleNamespace(
        **rows,
        outcomes=tuple(environment.outcome() for environment in environments),
        ledgers=ledgers,
    )
    return attach_credit_baselines(model, provisional, device=device)


@dataclass
class SeparatedRosterReplay:
    log_probs: torch.Tensor
    entropies: torch.Tensor
    values: torch.Tensor
    immediate_baselines: torch.Tensor
    successor_baselines: torch.Tensor
    hidden_after: torch.Tensor
    prefix_action_sums: torch.Tensor
    active_mask: torch.Tensor


def replay_separated_trajectory(
    model: SeparatedCreditPolicy,
    trajectory: SeparatedRosterTrajectory,
    *,
    device: torch.device,
) -> SeparatedRosterReplay:
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
    return SeparatedRosterReplay(
        log_probs=torch.stack([row.token_log_probs for row in outputs]),
        entropies=torch.stack([row.token_entropies for row in outputs]),
        values=torch.stack([row.value for row in outputs]),
        immediate_baselines=immediate,
        successor_baselines=successor,
        hidden_after=torch.stack([row.next_hidden for row in outputs]),
        prefix_action_sums=torch.stack([row.prefix_action_sums for row in outputs]),
        active_mask=trajectory.active_mask.to(device),
    )


def separated_replay_errors(
    replay: SeparatedRosterReplay,
    trajectory: SeparatedRosterTrajectory,
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


def separated_ppo_loss(
    replay: SeparatedRosterReplay,
    trajectory: SeparatedRosterTrajectory,
    credit: SeparatedCredit,
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    device = replay.log_probs.device
    mask = replay.active_mask
    old_log_probs = trajectory.old_log_probs.to(device)
    ratio = torch.exp(replay.log_probs - old_log_probs)
    active_count = mask.sum(dim=-1).clamp_min(1)

    def channel_policy_loss(advantage: torch.Tensor) -> torch.Tensor:
        normalized = normalize_advantage_channel(advantage.to(device))
        expanded = normalized.unsqueeze(-1)
        surrogate = torch.minimum(
            ratio * expanded,
            torch.clamp(ratio, 1.0 - PPO_CLIP, 1.0 + PPO_CLIP) * expanded,
        )
        return -(
            torch.where(mask, surrogate, 0.0).sum(dim=-1) / active_count
        ).mean()

    fast_policy_loss = channel_policy_loss(credit.immediate_residual)
    successor_policy_loss = channel_policy_loss(credit.successor_residual)
    policy_loss = 0.5 * (fast_policy_loss + successor_policy_loss)
    entropy = (
        torch.where(mask, replay.entropies, 0.0).sum(dim=-1) / active_count
    ).mean()
    old_values = trajectory.old_values.to(device)
    clipped_values = old_values + torch.clamp(
        replay.values - old_values, -VALUE_CLIP, VALUE_CLIP
    )
    return_targets = credit.slow_return_targets.to(device)
    slow_value_loss = torch.maximum(
        torch.square(replay.values - return_targets),
        torch.square(clipped_values - return_targets),
    ).mean()
    immediate_loss = F.mse_loss(
        replay.immediate_baselines, trajectory.rewards.to(device).detach()
    )
    successor_loss = F.mse_loss(
        replay.successor_baselines, credit.successor_targets.to(device)
    )
    critic_loss = slow_value_loss + immediate_loss + successor_loss
    total = (
        policy_loss
        + VALUE_COEFFICIENT * critic_loss
        - ENTROPY_COEFFICIENT * entropy
    )
    clip_fraction = (
        torch.where(
            mask,
            (torch.abs(ratio - 1.0) > PPO_CLIP).to(ratio.dtype),
            0.0,
        ).sum()
        / mask.sum().clamp_min(1)
    )
    return total, {
        "policy_loss": policy_loss,
        "fast_policy_loss": fast_policy_loss,
        "successor_policy_loss": successor_policy_loss,
        "slow_value_loss": slow_value_loss,
        "immediate_baseline_loss": immediate_loss,
        "successor_baseline_loss": successor_loss,
        "entropy": entropy,
        "clip_fraction": clip_fraction,
    }


def normalize_advantage_channel(advantage: torch.Tensor) -> torch.Tensor:
    """Normalize one actor-credit channel without mixing it with another."""

    if advantage.ndim != 2 or not bool(torch.isfinite(advantage).all()):
        raise ValueError("G18 advantage channel must be finite [time,batch]")
    return (advantage - advantage.mean()) / (
        advantage.std(unbiased=False) + 1e-8
    )


def optimize_separated_update(
    model: SeparatedCreditPolicy,
    optimizer: torch.optim.Optimizer,
    trajectory: SeparatedRosterTrajectory,
    *,
    device: torch.device,
    ppo_passes: int,
    gamma: float,
) -> dict[str, float]:
    terminals = torch.zeros_like(trajectory.rewards, dtype=torch.bool, device=device)
    terminals[-1] = True
    credit = compute_separated_credit(
        rewards=trajectory.rewards.to(device),
        slow_values=trajectory.old_values.to(device),
        bootstrap_slow_values=torch.zeros(
            trajectory.rewards.shape[1], dtype=torch.float32, device=device
        ),
        immediate_baselines=trajectory.old_immediate_baselines.to(device),
        successor_baselines=trajectory.old_successor_baselines.to(device),
        terminals=terminals,
        active_mask=trajectory.active_mask.to(device),
        gamma=float(gamma),
    )
    model.train()
    replay = replay_separated_trajectory(model, trajectory, device=device)
    with torch.no_grad():
        errors = separated_replay_errors(replay, trajectory)
    metric_names = (
        "policy_loss",
        "fast_policy_loss",
        "successor_policy_loss",
        "slow_value_loss",
        "immediate_baseline_loss",
        "successor_baseline_loss",
        "entropy",
        "clip_fraction",
        "gradient_norm",
    )
    totals = {name: 0.0 for name in metric_names}
    finite = True
    for pass_index in range(int(ppo_passes)):
        if pass_index:
            replay = replay_separated_trajectory(model, trajectory, device=device)
        loss, metrics = separated_ppo_loss(replay, trajectory, credit)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        gradient_norm = torch.nn.utils.clip_grad_norm_(
            model.parameters(), GRADIENT_CLIP
        )
        finite = finite and bool(torch.isfinite(loss)) and bool(
            torch.isfinite(gradient_norm)
        )
        optimizer.step()
        for name in metric_names[:-1]:
            totals[name] += float(metrics[name].detach().cpu())
        totals["gradient_norm"] += float(gradient_norm.detach().cpu())
    for name in totals:
        totals[name] /= float(ppo_passes)
    totals.update(errors)
    totals["finite_update"] = float(finite)
    totals["optimizer_steps"] = float(ppo_passes)
    return totals


def evaluate_battery_policy(
    model: SeparatedCreditPolicy,
    *,
    slot_orders: Sequence[Sequence[int]] = battery_source.GATE_SLOT_ORDERS,
    device: torch.device,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    model.eval()
    for slot_order in slot_orders:
        ledger = battery_source.make_ledger(slot_order)
        environment = battery_source.BatteryRosterEnv(ledger)
        hidden = torch.zeros(
            (1, battery_source.CAPACITY, model.hidden_dim),
            dtype=torch.float32,
            device=device,
        )
        rotating_effort = 0.0
        persistent_effort = 0.0
        inactive_action_zero = True
        with torch.no_grad():
            for time in range(battery_source.HORIZON):
                view = environment.observe()
                output = model.forward_step(
                    observations=torch.as_tensor(
                        view.observations[None, ...], device=device
                    ),
                    active_mask=torch.as_tensor(
                        view.active_mask[None, ...], device=device
                    ),
                    critic_state=torch.as_tensor(
                        view.critic_state[None, ...], device=device
                    ),
                    hidden=hidden,
                    deterministic=True,
                )
                actions = output.actions[0].detach().cpu().numpy()
                inactive_action_zero = inactive_action_zero and bool(
                    np.count_nonzero(actions[~view.active_mask]) == 0
                )
                if time < battery_source.TEMPORARY_LEAVE_TIME:
                    effort = (actions[:, 0].astype(np.float64) + 1.0) / 2.0
                    rotating_effort += float(effort[view.rotating_mask].sum())
                    persistent_effort += float(
                        effort[view.active_mask & ~view.rotating_mask].sum()
                    )
                environment.step(actions)
                hidden = output.next_hidden
        outcome = environment.outcome()
        total_low_effort = rotating_effort + persistent_effort
        rows.append(
            {
                "slot_order": [int(value) for value in slot_order],
                "utility": float(outcome.utility),
                "minimum_step_utility": float(outcome.minimum_step_utility),
                "spike_utility": float(
                    np.mean(
                        outcome.reward_trace[
                            battery_source.TEMPORARY_LEAVE_TIME : battery_source.RETURN_TIME
                        ]
                    )
                ),
                "future_service_deficit": float(outcome.future_service_deficit),
                "low_rotating_effort_share": (
                    rotating_effort / total_low_effort
                    if total_low_effort > 0.0
                    else 0.0
                ),
                "inactive_action_zero": inactive_action_zero,
                "roster_sizes": list(outcome.roster_sizes),
            }
        )
    return rows
