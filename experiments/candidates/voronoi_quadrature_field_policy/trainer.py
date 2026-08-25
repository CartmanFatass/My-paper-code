"""Synchronous full-episode BPTT actor-critic training for the frozen B1 law."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable

import torch

from .config import FrozenConfig
from .geometry import shifted_volumes
from .host import EFFORTS, Episode, make_episode
from .models import VQFPModel
from .rng import CounterRNG


@dataclass(slots=True)
class EpisodeTrace:
    rewards: list[torch.Tensor]
    values: list[torch.Tensor]
    logp_joint: list[torch.Tensor]
    actions: list[torch.Tensor]
    raw_mass: list[torch.Tensor]
    logits: list[torch.Tensor]
    normalized_return: torch.Tensor
    raw_return: torch.Tensor
    service_mass: torch.Tensor
    cost: torch.Tensor
    action_frequency: torch.Tensor


@dataclass(slots=True)
class EpisodeReport:
    """Detached CPU evaluation retention containing only registered telemetry."""
    raw_return: torch.Tensor
    service_mass: torch.Tensor
    cost: torch.Tensor
    action_frequency: torch.Tensor


def compact_report(trace: EpisodeTrace) -> EpisodeReport:
    return EpisodeReport(trace.raw_return.detach().cpu(), trace.service_mass.detach().cpu(), trace.cost.detach().cpu(),
                         trace.action_frequency.detach().cpu())


def categorical_from_uniform(logits: torch.Tensor, uniforms: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Inverse-CDF categorical sample, allowing exact paired uniform tapes."""
    log_probs = torch.log_softmax(logits, dim=-1)
    probs = log_probs.exp()
    actions = torch.sum(uniforms[:, None] > torch.cumsum(probs, dim=-1), dim=-1).clamp_max(2).long()
    selected = log_probs.gather(-1, actions[:, None]).squeeze(-1)
    return actions, selected


def _actor_step(model: VQFPModel, episode: Episode, signal: torch.Tensor, previous: torch.Tensor,
                hidden: torch.Tensor, *, cut: bool, episode_index: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    edge = model.edge_inputs(episode.positions, episode.gaps, episode.predecessor, episode.triplets, signal, previous)
    port_volumes = shifted_volumes(episode.volumes, episode.triplets, episode_index) if cut else episode.volumes[episode.triplets]
    return model.actor(edge, port_volumes, episode.n, hidden)


def rollout_episode(model: VQFPModel, episode: Episode, action_uniforms: torch.Tensor, *,
                    cut: bool = False, episode_index: int = 0,
                    observation_noise: torch.Tensor | None = None,
                    compute_normalized_return: bool = True,
                    oracle_denominator: torch.Tensor | None = None) -> EpisodeTrace:
    """One simultaneous 32-tick rollout; hidden state resets exactly at entry."""
    if action_uniforms.shape != (32, episode.n):
        raise ValueError("the registered action tape is 32 by active N")
    hidden = torch.zeros((episode.n, 64), dtype=episode.positions.dtype, device=episode.positions.device)
    previous = torch.full((episode.n,), -1, dtype=torch.long, device=episode.positions.device)
    rewards: list[torch.Tensor] = []
    values: list[torch.Tensor] = []
    logp_joint: list[torch.Tensor] = []
    actions_out: list[torch.Tensor] = []
    raw_masses: list[torch.Tensor] = []
    logits_out: list[torch.Tensor] = []
    service_terms: list[torch.Tensor] = []
    cost_terms: list[torch.Tensor] = []
    oracle_total = oracle_denominator
    for tick in range(32):
        true_signal = episode.cell_averages(tick)
        signal = true_signal if observation_noise is None else (true_signal + observation_noise[tick]).clamp(0.0, 1.0)
        logits, hidden, raw_mass, _ = _actor_step(model, episode, signal, previous, hidden, cut=cut, episode_index=episode_index)
        value = model.critic(episode.positions, episode.volumes, signal, previous, episode.n, tick,
                             episode.phi1, episode.phi2, episode.omega1, episode.omega2)
        action, selected_logp = categorical_from_uniform(logits, action_uniforms[tick])
        reward = episode.reward(EFFORTS.to(action.device)[action], tick)
        effort_values = EFFORTS.to(action.device)[action]
        intensity = effort_values + 0.5 * effort_values[episode.predecessor] + 0.5 * effort_values[episode.successor]
        service_terms.append(torch.sum(episode.volumes * true_signal * (1.0 - torch.exp(-intensity))))
        cost_terms.append(0.08 * torch.sum(episode.volumes * effort_values.square()))
        rewards.append(reward)
        values.append(value)
        logp_joint.append(selected_logp.sum())
        actions_out.append(action)
        raw_masses.append(raw_mass)
        logits_out.append(logits)
        previous = action
    if compute_normalized_return:
        if oracle_total is None:
            oracle_total = episode.oracle_rewards().sum()
        normalized_return = torch.stack(rewards).sum() / oracle_total
    else:
        normalized_return = episode.positions.new_zeros(())
    action_tensor = torch.stack(actions_out)
    action_frequency = torch.bincount(action_tensor.flatten(), minlength=3).to(dtype=torch.float32).div(action_tensor.numel())
    return EpisodeTrace(rewards, values, logp_joint, actions_out, raw_masses, logits_out, normalized_return,
                        torch.stack(rewards).sum(), torch.stack(service_terms).sum(), torch.stack(cost_terms).sum(),
                        action_frequency)


def _loss_for_trace(trace: EpisodeTrace, config: FrozenConfig) -> torch.Tensor:
    values = trace.values
    advantages: list[torch.Tensor] = [values[0].new_zeros(()) for _ in range(config.horizon)]
    next_advantage = values[0].new_zeros(())  # A_32 = 0
    next_value = values[0].new_zeros(())      # V_32 = 0
    for tick in range(config.horizon - 1, -1, -1):
        delta = trace.rewards[tick] + config.gamma * next_value.detach() - values[tick].detach()
        advantage = delta + config.gamma * config.gae_lambda * next_advantage
        advantages[tick] = advantage
        next_advantage = advantage
        next_value = values[tick]
    terms = []
    for tick, advantage in enumerate(advantages):
        target = (advantage + values[tick]).detach()
        terms.append(-advantage.detach() * trace.logp_joint[tick] + 0.5 * (values[tick] - target).square())
    return torch.stack(terms).mean()


def make_optimizer(model: VQFPModel, config: FrozenConfig) -> torch.optim.Adam:
    return torch.optim.Adam(model.parameters(), lr=config.learning_rate,
                            betas=(config.adam_beta1, config.adam_beta2), eps=config.adam_epsilon,
                            weight_decay=0.0, amsgrad=False)


def train_update(model: VQFPModel, optimizer: torch.optim.Adam, seed: int, update: int,
                 config: FrozenConfig, *, device: torch.device | None = None,
                 before_step: Callable[[int], None] | None = None,
                 after_step: Callable[[int], None] | None = None) -> tuple[torch.Tensor, torch.Tensor]:
    """Exactly eight full episodes, a single backward pass, global clip, and Adam step."""
    cells = ((6, "IID"), (6, "CLUSTER"), (10, "IID"), (10, "CLUSTER"))
    traces: list[EpisodeTrace] = []
    for replicate in range(2):
        for n, regime in cells:
            key = CounterRNG(seed, "train", update, replicate, n, regime)
            episode = make_episode(n, regime, key, device=device)
            uniforms = key.uniform((config.horizon, n), "action_uniforms", device=device)
            traces.append(rollout_episode(model, episode, uniforms, compute_normalized_return=False))
    loss = torch.stack([_loss_for_trace(trace, config) for trace in traces]).mean()
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    gradients = [parameter for parameter in model.parameters() if parameter.grad is not None]
    torch.nn.utils.clip_grad_norm_(gradients, config.gradient_clip)
    if before_step is not None:
        before_step(config.team_transitions_per_update)
    optimizer.step()
    if after_step is not None:
        after_step(config.team_transitions_per_update)
    summary = torch.stack([torch.stack((trace.raw_return, trace.service_mass, trace.cost, *trace.action_frequency))
                           for trace in traces]).detach().cpu()
    return loss.detach(), summary


def train_seed(model: VQFPModel, seed: int, config: FrozenConfig, *, device: torch.device | None = None,
               before_step: Callable[[int], None] | None = None,
               after_step: Callable[[int], None] | None = None) -> tuple[VQFPModel, list[float], torch.Tensor]:
    """Apply the exactly 375 frozen updates and return only the final checkpoint."""
    optimizer = make_optimizer(model, config)
    losses: list[float] = []
    summaries: list[torch.Tensor] = []
    for update in range(config.updates):
        loss, summary = train_update(model, optimizer, seed, update, config, device=device,
                                     before_step=before_step, after_step=after_step)
        losses.append(float(loss.cpu()))
        summaries.append(summary)
    return model, losses, torch.stack(summaries)
