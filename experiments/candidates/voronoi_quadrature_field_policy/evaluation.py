"""Frozen checkpoint panels, replay cut, structural controls, and bypass records."""

from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Callable

import torch

from .config import CONTROLS, FrozenConfig, HELDOUT_N, REGIMES
from .geometry import restore_volumes, shifted_volumes
from .host import Episode, make_episode
from .models import Arm, VQFPModel
from .rng import CounterRNG
from .trainer import EpisodeReport, _actor_step, categorical_from_uniform, compact_report, rollout_episode


@dataclass(slots=True)
class ReplayEpisode:
    quadrature_error_delta: torch.Tensor
    action_tv: torch.Tensor
    intact_return: torch.Tensor
    cut_return: torch.Tensor
    intact_raw_mass: torch.Tensor
    cut_raw_mass: torch.Tensor
    true_local_mass: torch.Tensor
    local_volume: torch.Tensor
    intact_actions: torch.Tensor
    association_difference: torch.Tensor
    intact_report: EpisodeReport
    cut_report: EpisodeReport


@dataclass(slots=True)
class ControlResult:
    name: str
    passed: bool
    maximum_error: float
    states: int


@dataclass(slots=True)
class CheckpointPanels:
    ordinary_intact: dict[tuple[int, str], torch.Tensor] = field(default_factory=dict)
    ordinary_cut: dict[tuple[int, str], torch.Tensor] = field(default_factory=dict)
    conflict_replay: dict[int, list[ReplayEpisode]] = field(default_factory=dict)
    conflict_intact: dict[int, torch.Tensor] = field(default_factory=dict)
    conflict_cut: dict[int, torch.Tensor] = field(default_factory=dict)
    noisy: dict[int, torch.Tensor] = field(default_factory=dict)
    controls: dict[tuple[int, str], ControlResult] = field(default_factory=dict)
    volume_cv: dict[tuple[int, str], torch.Tensor] = field(default_factory=dict)
    association_conflict: dict[int, torch.Tensor] = field(default_factory=dict)
    ordinary_traces: dict[tuple[int, str], list[EpisodeReport]] = field(default_factory=dict)
    ordinary_cut_traces: dict[tuple[int, str], list[EpisodeReport]] = field(default_factory=dict)
    noisy_traces: dict[int, list[EpisodeReport]] = field(default_factory=dict)


def _edge(model: VQFPModel, episode: Episode, signal: torch.Tensor, previous: torch.Tensor) -> torch.Tensor:
    return model.edge_inputs(episode.positions, episode.gaps, episode.predecessor, episode.triplets, signal, previous)


@torch.no_grad()
def replay_conflict_episode(model: VQFPModel, episode: Episode, uniforms: torch.Tensor, episode_index: int) -> ReplayEpisode:
    """Capture intact/cut outputs from the same intact-trajectory pre-input state."""
    hidden = torch.zeros((episode.n, 64), dtype=episode.positions.dtype, device=episode.positions.device)
    previous = torch.full((episode.n,), -1, dtype=torch.long, device=episode.positions.device)
    errors, tvs, raw_i, raw_c, q_values, action_values, association = [], [], [], [], [], [], []
    for tick in range(32):
        signal = episode.cell_averages(tick)
        edge = _edge(model, episode, signal, previous)
        intact_logits, next_hidden, intact_mass, _ = model.actor(edge, episode.volumes[episode.triplets], episode.n, hidden)
        cut_logits, _, cut_mass, _ = model.actor(edge, shifted_volumes(episode.volumes, episode.triplets, episode_index), episode.n, hidden)
        q = torch.sum(episode.volumes[episode.triplets] * signal[episode.triplets], dim=-1)
        association.append((q.div(episode.volumes[episode.triplets].sum(-1)) - signal[episode.triplets].mean(-1)).abs())
        errors.append((cut_mass.sub(q).abs().div(episode.volumes[episode.triplets].sum(-1))
                       - intact_mass.sub(q).abs().div(episode.volumes[episode.triplets].sum(-1))).mean())
        tvs.append(0.5 * (torch.softmax(intact_logits, -1) - torch.softmax(cut_logits, -1)).abs().sum(-1).mean())
        raw_i.append(intact_mass)
        raw_c.append(cut_mass)
        q_values.append(q)
        action, _ = categorical_from_uniform(intact_logits, uniforms[tick])
        action_values.append(action)
        previous, hidden = action, next_hidden
    denominator = episode.oracle_rewards().sum()
    intact_trace = rollout_episode(model, episode, uniforms, cut=False, episode_index=episode_index,
                                   oracle_denominator=denominator)
    cut_trace = rollout_episode(model, episode, uniforms, cut=True, episode_index=episode_index,
                                oracle_denominator=denominator)
    local_volume = episode.volumes[episode.triplets].sum(-1)
    return ReplayEpisode(torch.stack(errors).mean(), torch.stack(tvs).mean(), intact_trace.normalized_return, cut_trace.normalized_return,
                         torch.stack(raw_i), torch.stack(raw_c), torch.stack(q_values), local_volume,
                         torch.stack(action_values), torch.stack(association), compact_report(intact_trace), compact_report(cut_trace))


def _control_outputs(model: VQFPModel, episode: Episode, name: str, state_index: int,
                     rng: CounterRNG) -> tuple[torch.Tensor, torch.Tensor]:
    """Return the registered base and transformed vector with zero hidden/START tokens."""
    signal = episode.cell_averages(0)
    previous = torch.full((episode.n,), -1, dtype=torch.long, device=episode.positions.device)
    hidden = torch.zeros((episode.n, 64), dtype=episode.positions.dtype, device=episode.positions.device)
    edge = _edge(model, episode, signal, previous)
    volumes = episode.volumes[episode.triplets]
    receiver_signal = edge[:, 1, 0:1]
    receiver_previous = edge[:, 1, 1:5]
    base_message, _, _ = model.aggregate(edge, volumes)
    base_logits, _, _, _ = model.actor(edge, volumes, episode.n, hidden)
    if name == "WHOLE-TUPLE-PERMUTE":
        fixed = (2, 0, 1) if state_index % 2 == 0 else (1, 2, 0)
        order = torch.tensor(fixed, dtype=torch.long, device=episode.positions.device).expand(episode.n, -1)
        transformed_edge = torch.gather(edge, 1, order[..., None].expand_as(edge))
        transformed_volumes = torch.gather(volumes, 1, order)
    elif name == "EQUAL-VOLUME" or name == "CONSTANT-FIELD":
        transformed_edge = edge
        transformed_volumes = shifted_volumes(episode.volumes, episode.triplets, state_index)
    elif name == "IDENTITY-RESTORE":
        transformed_edge = edge
        transformed_volumes = restore_volumes(episode.volumes, episode.triplets, state_index)
    else:
        raise ValueError(f"unregistered control {name}")
    transformed_message, _, _ = model.aggregate(transformed_edge, transformed_volumes)
    transformed_logits, _, _, _ = model.actor(
        transformed_edge, transformed_volumes, episode.n, hidden,
        self_signal=receiver_signal, self_previous=receiver_previous,
    )
    if name == "CONSTANT-FIELD":
        return base_message[:, :1], transformed_message[:, :1]
    return torch.cat((base_message, base_logits), -1), torch.cat((transformed_message, transformed_logits), -1)


@torch.no_grad()
def run_control(model: VQFPModel, seed: int, n: int, name: str, config: FrozenConfig,
                *, device: torch.device | None = None) -> ControlResult:
    """Evaluate exactly one independently sampled 128-state control bank per arm."""
    if name not in CONTROLS:
        raise ValueError("only the four registered structural controls have state banks")
    maximum = 0.0
    passed = True
    for state_index in range(config.control_states):
        key = CounterRNG(seed, "control", name, n, state_index)
        if name in ("WHOLE-TUPLE-PERMUTE", "IDENTITY-RESTORE"):
            episode = make_episode(n, "CLUSTER", key, conflict=True, device=device)
        elif name == "EQUAL-VOLUME":
            episode = make_episode(n, "EQUAL", key, device=device)
        else:
            episode = make_episode(n, "CLUSTER", key, constant_field=True, device=device)
        base, transformed = _control_outputs(model, episode, name, state_index, key)
        maximum = max(maximum, float((base - transformed).abs().max().cpu()))
        if not torch.allclose(base, transformed, atol=config.control_atol, rtol=config.control_rtol):
            passed = False
    return ControlResult(name, passed, maximum, config.control_states)


@torch.no_grad()
def evaluate_checkpoint(model: VQFPModel, seed: int, config: FrozenConfig,
                        *, device: torch.device | None = None,
                        consume: Callable[[str, int], None] | None = None) -> CheckpointPanels:
    """Evaluate the complete frozen bank for one arm/seed without any model selection."""
    panels = CheckpointPanels()
    for n in (4, 6, 10, 14):
        for regime in REGIMES:
            returns, traces = [], []
            volume_cvs = []
            for episode_index in range(config.ordinary_episodes):
                key = CounterRNG(seed, "ordinary", n, regime, episode_index)
                episode = make_episode(n, regime, key, device=device)
                if regime == "CLUSTER":
                    volume_cvs.append(torch.sqrt(((episode.volumes - 1.0 / n).square()).mean()).div(1.0 / n))
                tape = key.uniform((32, n), "action_uniforms", device=device)
                trace = rollout_episode(model, episode, tape, episode_index=episode_index)
                returns.append(trace.normalized_return)
                traces.append(compact_report(trace))
            panels.ordinary_intact[(n, regime)] = torch.stack(returns).cpu()
            panels.ordinary_traces[(n, regime)] = traces
            if consume is not None:
                consume("ordinary_intact", config.ordinary_episodes * config.horizon)
            if regime == "CLUSTER":
                panels.volume_cv[(n, "CLUSTER")] = torch.stack(volume_cvs).cpu()
            if n in HELDOUT_N:
                cuts, cut_traces = [], []
                for episode_index in range(config.ordinary_episodes):
                    key = CounterRNG(seed, "ordinary", n, regime, episode_index)
                    episode = make_episode(n, regime, key, device=device)
                    tape = key.uniform((32, n), "action_uniforms", device=device)
                    trace = rollout_episode(model, episode, tape, cut=True, episode_index=episode_index)
                    cuts.append(trace.normalized_return)
                    cut_traces.append(compact_report(trace))
                panels.ordinary_cut[(n, regime)] = torch.stack(cuts).cpu()
                panels.ordinary_cut_traces[(n, regime)] = cut_traces
                if consume is not None:
                    consume("ordinary_cut", config.ordinary_episodes * config.horizon)
    for n in HELDOUT_N:
        replay, intact, cut, conflict_cv, association = [], [], [], [], []
        for episode_index in range(config.conflict_episodes):
            key = CounterRNG(seed, "conflict", n, episode_index)
            episode = make_episode(n, "CLUSTER", key, conflict=True, device=device)
            tape = key.uniform((32, n), "action_uniforms", device=device)
            result = replay_conflict_episode(model, episode, tape, episode_index)
            replay.append(result)
            intact.append(result.intact_return)
            cut.append(result.cut_return)
            conflict_cv.append(torch.sqrt(((episode.volumes - 1.0 / n).square()).mean()).div(1.0 / n))
            # Equal-weight every registered tick and receiver, not a tick-zero proxy.
            association.append(result.association_difference.mean())
        panels.conflict_replay[n] = replay
        panels.conflict_intact[n] = torch.stack(intact).cpu()
        panels.conflict_cut[n] = torch.stack(cut).cpu()
        panels.volume_cv[(n, "MEASURE-CONFLICT")] = torch.stack(conflict_cv).cpu()
        panels.association_conflict[n] = torch.stack(association).cpu()
        if consume is not None:
            consume("conflict_intact_cut", 2 * config.conflict_episodes * config.horizon)
        noisy, noisy_traces = [], []
        for episode_index in range(config.noisy_episodes):
            key = CounterRNG(seed, "noisy", n, "CLUSTER", episode_index)
            episode = make_episode(n, "CLUSTER", key, device=device)
            tape = key.uniform((32, n), "action_uniforms", device=device)
            noise = key.normal((32, n), 0.0, 0.15, "observation_noise", device=device)
            trace = rollout_episode(model, episode, tape, observation_noise=noise, episode_index=episode_index)
            noisy.append(trace.normalized_return)
            noisy_traces.append(compact_report(trace))
        panels.noisy[n] = torch.stack(noisy).cpu()
        panels.noisy_traces[n] = noisy_traces
        if consume is not None:
            consume("noisy", config.noisy_episodes * config.horizon)
        for name in CONTROLS:
            panels.controls[(n, name)] = run_control(model, seed, n, name, config, device=device)
            if consume is not None:
                consume("controls", config.control_states)
    return panels
