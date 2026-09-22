"""The B01 dense typed-slot encoder and its local HMASD installation hook."""
from __future__ import annotations

import time
from dataclasses import dataclass

import torch
from torch import nn


OBS_DIM = 104
SELF_SLICE = slice(0, 3)
USER_SLICE = slice(3, 63)
NEIGHBOR_SLICE = slice(63, 103)
TIME_SLICE = slice(103, 104)
USER_SLOTS = 20
NEIGHBOR_SLOTS = 10


class DenseObservationEncoder(nn.Module):
    """Encode the unchanged S1 observation as dense typed rank slots.

    Rank embeddings describe the environment's current SINR-sorted slot positions. They do
    not represent persistent entities. No padding or truth mask is accepted: zero slots take
    part in attention and in the two type means like every other slot.
    """

    output_size = 256

    def __init__(self, width: int = 64, heads: int = 4):
        super().__init__()
        if width != 64 or heads != 4:
            raise ValueError("B01 fixes width=64 and heads=4")
        self.self_projection = nn.Linear(3, width)
        self.user_projection = nn.Linear(3, width)
        self.neighbor_projection = nn.Linear(4, width)
        self.time_projection = nn.Linear(1, width)
        self.user_rank = nn.Embedding(USER_SLOTS, width)
        self.neighbor_rank = nn.Embedding(NEIGHBOR_SLOTS, width)
        self.attention = nn.MultiheadAttention(width, heads, dropout=0.0, batch_first=True)
        self.attention_norm = nn.LayerNorm(width)
        self.feed_forward = nn.Sequential(
            nn.Linear(width, 2 * width), nn.GELU(), nn.Linear(2 * width, width)
        )
        self.feed_forward_norm = nn.LayerNorm(width)
        self.output_projection = nn.Linear(4 * width, self.output_size)

    @staticmethod
    def split_observation(observation: torch.Tensor):
        if observation.shape[-1] != OBS_DIM:
            raise ValueError(f"dense B01 encoder requires {OBS_DIM} floats, got {observation.shape[-1]}")
        leading = observation.shape[:-1]
        users = observation[..., USER_SLICE].reshape(*leading, USER_SLOTS, 3)
        neighbors = observation[..., NEIGHBOR_SLICE].reshape(*leading, NEIGHBOR_SLOTS, 4)
        return observation[..., SELF_SLICE], users, neighbors, observation[..., TIME_SLICE]

    def forward(self, observation: torch.Tensor) -> torch.Tensor:
        if not torch.is_tensor(observation):
            observation = torch.as_tensor(observation, dtype=torch.float32)
        observation = observation.to(dtype=self.self_projection.weight.dtype,
                                     device=self.self_projection.weight.device)
        if observation.shape[-1] != OBS_DIM:
            raise ValueError(
                f"dense B01 encoder requires {OBS_DIM} floats, got {observation.shape[-1]}"
            )
        leading = observation.shape[:-1]
        flat = observation.reshape(-1, OBS_DIM)
        own, users, neighbors, step = self.split_observation(flat)

        own_token = self.self_projection(own).unsqueeze(1)
        user_tokens = self.user_projection(users) + self.user_rank.weight.unsqueeze(0)
        neighbor_tokens = (
            self.neighbor_projection(neighbors) + self.neighbor_rank.weight.unsqueeze(0)
        )
        time_token = self.time_projection(step).unsqueeze(1)
        tokens = torch.cat((own_token, user_tokens, neighbor_tokens, time_token), dim=1)
        attended, _ = self.attention(tokens, tokens, tokens, need_weights=False)
        tokens = self.attention_norm(tokens + attended)
        tokens = self.feed_forward_norm(tokens + self.feed_forward(tokens))

        pooled = torch.cat(
            (tokens[:, 0], tokens[:, -1],
             tokens[:, 1:1 + USER_SLOTS].mean(dim=1),
             tokens[:, 1 + USER_SLOTS:1 + USER_SLOTS + NEIGHBOR_SLOTS].mean(dim=1)),
            dim=-1,
        )
        return self.output_projection(pooled).reshape(*leading, self.output_size)


@dataclass
class ActorTiming:
    forward_seconds: float = 0.0
    forward_calls: int = 0
    evaluate_actions_seconds: float = 0.0
    evaluate_actions_calls: int = 0

    def as_dict(self):
        return {
            "forward_seconds": self.forward_seconds,
            "forward_calls": self.forward_calls,
            "evaluate_actions_seconds": self.evaluate_actions_seconds,
            "evaluate_actions_calls": self.evaluate_actions_calls,
            "total_seconds": self.forward_seconds + self.evaluate_actions_seconds,
            "total_calls": self.forward_calls + self.evaluate_actions_calls,
        }


def instrument_actor(actor) -> ActorTiming:
    """Time the real actor entry points without changing module/state-dict structure."""
    timing = ActorTiming()
    original_forward = actor.forward
    original_evaluate_actions = actor.evaluate_actions

    def timed_forward(*args, **kwargs):
        started = time.perf_counter()
        try:
            return original_forward(*args, **kwargs)
        finally:
            timing.forward_seconds += time.perf_counter() - started
            timing.forward_calls += 1

    def timed_evaluate_actions(*args, **kwargs):
        started = time.perf_counter()
        try:
            return original_evaluate_actions(*args, **kwargs)
        finally:
            timing.evaluate_actions_seconds += time.perf_counter() - started
            timing.evaluate_actions_calls += 1

    actor.forward = timed_forward
    actor.evaluate_actions = timed_evaluate_actions
    return timing


def _rebuild_actor_optimizer(agent) -> None:
    old = agent.discoverer_actor_optimizer
    if len(old.param_groups) != 1:
        raise RuntimeError("B01 requires the standing single-group discoverer actor Adam")
    if getattr(agent, "discoverer_actor_scheduler", None) is not None:
        raise RuntimeError("B01 does not permit an actor learning-rate schedule")
    group_options = {key: value for key, value in old.param_groups[0].items()
                     if key not in {"params", "initial_lr"}}
    parameters = agent.skill_discoverer.actor_update_parameters()
    if agent.low_level_compact_extractor is not None:
        parameters = parameters + list(agent.low_level_compact_extractor.parameters())
    agent.discoverer_actor_optimizer = type(old)(parameters, **group_options)
    owned = {id(parameter) for group in agent.discoverer_actor_optimizer.param_groups
             for parameter in group["params"]}
    expected = {id(parameter) for parameter in parameters}
    if owned != expected:
        raise RuntimeError("rebuilt actor optimizer does not own exactly the active actor parameters")


def install_actor_encoder(agent, arm: str):
    """Install B01's actor base while preserving the caller's torch RNG stream."""
    actor = agent.skill_discoverer.actor
    if int(agent.config.obs_dim) != OBS_DIM or int(actor.hidden_size) != 256:
        raise ValueError("B01 is bound to the S1 104-float observation and 256-wide actor")
    original_type = type(actor.base).__name__
    if arm == "DENSE":
        rng_state = torch.random.get_rng_state()
        try:
            replacement = DenseObservationEncoder().to(**actor.tpdv)
        finally:
            torch.random.set_rng_state(rng_state)
        actor.base = replacement
        _rebuild_actor_optimizer(agent)
    elif arm != "ORIGINAL":
        raise ValueError(f"unknown encoder arm {arm}")
    timing = instrument_actor(actor)
    active = actor.base
    return {
        "arm": arm,
        "original_base_type": original_type,
        "active_base_type": type(active).__name__,
        "encoder_parameters": sum(parameter.numel() for parameter in active.parameters()),
        "actor_parameters": sum(parameter.numel() for parameter in actor.parameters()),
        "timing": timing,
    }
