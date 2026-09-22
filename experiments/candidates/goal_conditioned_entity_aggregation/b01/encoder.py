"""Goal-conditioned entity encoders and their local B01 actor installation hook."""
from __future__ import annotations

import time
from dataclasses import dataclass

import torch
import torch.nn.functional as F
from torch import nn

from hmasd.networks import R_Actor
from hmasd.r_mappo_utils import check


OBS_DIM = 104
SELF_SLICE = slice(0, 3)
USER_SLICE = slice(3, 63)
PEER_SLICE = slice(63, 103)
TIME_SLICE = slice(103, 104)
USER_SLOTS = 20
PEER_SLOTS = 10
SKILLS = 6
WIDTH = 64
OUTPUT_DIM = 256


def _two_layer_mlp(input_width: int) -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(input_width, WIDTH),
        nn.ReLU(),
        nn.Linear(WIDTH, WIDTH),
        nn.ReLU(),
    )


class _TypedSlotEncoder(nn.Module):
    """Common parsing and held-skill validation for the two fixed B01 encoders."""

    output_size = OUTPUT_DIM

    def __init__(self) -> None:
        super().__init__()
        self.register_buffer(
            "user_rank",
            torch.arange(USER_SLOTS, dtype=torch.float32) / (USER_SLOTS - 1),
        )
        self.register_buffer(
            "peer_rank",
            torch.arange(PEER_SLOTS, dtype=torch.float32) / (PEER_SLOTS - 1),
        )

    @staticmethod
    def split_observation(observation: torch.Tensor):
        if observation.shape[-1] != OBS_DIM:
            raise ValueError(
                f"GCEA B01 requires {OBS_DIM} observation floats, "
                f"got {observation.shape[-1]}"
            )
        leading = observation.shape[:-1]
        users = observation[..., USER_SLICE].reshape(*leading, USER_SLOTS, 3)
        peers = observation[..., PEER_SLICE].reshape(*leading, PEER_SLOTS, 4)
        ego_time = torch.cat(
            (observation[..., SELF_SLICE], observation[..., TIME_SLICE]), dim=-1
        )
        return ego_time, users, peers

    def _prepare(self, observation, held_skill):
        parameter = next(self.parameters())
        if not torch.is_tensor(observation):
            observation = torch.as_tensor(observation)
        observation = observation.to(device=parameter.device, dtype=parameter.dtype)
        if observation.shape[-1] != OBS_DIM:
            raise ValueError(
                f"GCEA B01 requires {OBS_DIM} observation floats, "
                f"got {observation.shape[-1]}"
            )

        if not torch.is_tensor(held_skill):
            held_skill = torch.as_tensor(held_skill)
        held_skill = held_skill.to(device=observation.device)
        leading = observation.shape[:-1]
        if held_skill.shape == leading + (1,):
            held_skill = held_skill.squeeze(-1)
        if held_skill.shape != leading:
            raise ValueError(
                "held skill batch shape must match the observation batch shape: "
                f"{tuple(held_skill.shape)} versus {tuple(leading)}"
            )
        if held_skill.is_floating_point():
            if not bool(torch.isfinite(held_skill).all()) or not bool(
                torch.equal(held_skill, held_skill.round())
            ):
                raise ValueError("held skill must contain integer-valued labels")
        held_skill = held_skill.long()
        if held_skill.numel() and (
            int(held_skill.min().item()) < 0 or int(held_skill.max().item()) >= SKILLS
        ):
            raise ValueError(f"held skill labels must be in [0, {SKILLS - 1}]")
        skill_one_hot = F.one_hot(held_skill, num_classes=SKILLS).to(
            dtype=observation.dtype
        )
        return observation, skill_one_hot

    @staticmethod
    def _rank_feature(rank: torch.Tensor, leading: tuple[int, ...]) -> torch.Tensor:
        return rank.reshape(*((1,) * len(leading)), rank.numel(), 1).expand(
            *leading, rank.numel(), 1
        )


class EarlyAttentionEncoder(_TypedSlotEncoder):
    """Arm E: use held skill only in two bare typed-attention queries."""

    def __init__(self) -> None:
        super().__init__()
        self.ego_mlp = _two_layer_mlp(4)
        self.user_mlp = _two_layer_mlp(4)
        self.peer_mlp = _two_layer_mlp(5)
        self.skill_query = nn.Linear(SKILLS, WIDTH, bias=False)
        self.user_attention = nn.MultiheadAttention(
            WIDTH, 4, dropout=0.0, batch_first=True
        )
        self.peer_attention = nn.MultiheadAttention(
            WIDTH, 4, dropout=0.0, batch_first=True
        )
        self.output_projection = nn.Sequential(nn.Linear(3 * WIDTH, OUTPUT_DIM), nn.ReLU())

    def forward(self, observation, held_skill):
        observation, skill_one_hot = self._prepare(observation, held_skill)
        leading = observation.shape[:-1]
        flat_observation = observation.reshape(-1, OBS_DIM)
        flat_skill = skill_one_hot.reshape(-1, SKILLS)
        ego_time, users, peers = self.split_observation(flat_observation)

        user_inputs = torch.cat(
            (users, self._rank_feature(self.user_rank, (flat_observation.shape[0],))),
            dim=-1,
        )
        peer_inputs = torch.cat(
            (peers, self._rank_feature(self.peer_rank, (flat_observation.shape[0],))),
            dim=-1,
        )
        ego = self.ego_mlp(ego_time)
        query = (ego + self.skill_query(flat_skill)).unsqueeze(1)
        user_tokens = self.user_mlp(user_inputs)
        peer_tokens = self.peer_mlp(peer_inputs)
        user_pool, _ = self.user_attention(
            query, user_tokens, user_tokens, need_weights=False
        )
        peer_pool, _ = self.peer_attention(
            query, peer_tokens, peer_tokens, need_weights=False
        )
        pooled = torch.cat((user_pool[:, 0], peer_pool[:, 0], ego), dim=-1)
        return self.output_projection(pooled).reshape(*leading, OUTPUT_DIM)


class ConditionalDeepSetsEncoder(_TypedSlotEncoder):
    """Arm P: condition each typed element transform before its first nonlinearity."""

    def __init__(self) -> None:
        super().__init__()
        self.ego_mlp = _two_layer_mlp(4)
        self.user_mlp = _two_layer_mlp(14)
        self.peer_mlp = _two_layer_mlp(15)
        self.output_projection = nn.Sequential(nn.Linear(5 * WIDTH, OUTPUT_DIM), nn.ReLU())

    @staticmethod
    def _repeat_context(context: torch.Tensor, slots: int) -> torch.Tensor:
        return context.unsqueeze(1).expand(-1, slots, -1)

    def forward(self, observation, held_skill):
        observation, skill_one_hot = self._prepare(observation, held_skill)
        leading = observation.shape[:-1]
        flat_observation = observation.reshape(-1, OBS_DIM)
        flat_skill = skill_one_hot.reshape(-1, SKILLS)
        ego_time, users, peers = self.split_observation(flat_observation)
        context = torch.cat((ego_time, flat_skill), dim=-1)

        user_inputs = torch.cat(
            (
                users,
                self._rank_feature(self.user_rank, (flat_observation.shape[0],)),
                self._repeat_context(context, USER_SLOTS),
            ),
            dim=-1,
        )
        peer_inputs = torch.cat(
            (
                peers,
                self._rank_feature(self.peer_rank, (flat_observation.shape[0],)),
                self._repeat_context(context, PEER_SLOTS),
            ),
            dim=-1,
        )
        user_tokens = self.user_mlp(user_inputs)
        peer_tokens = self.peer_mlp(peer_inputs)
        ego = self.ego_mlp(ego_time)
        pooled = torch.cat(
            (
                user_tokens.mean(dim=1),
                user_tokens.amax(dim=1),
                peer_tokens.mean(dim=1),
                peer_tokens.amax(dim=1),
                ego,
            ),
            dim=-1,
        )
        return self.output_projection(pooled).reshape(*leading, OUTPUT_DIM)


class GoalConditionedActor(R_Actor):
    """R_Actor entry points with an explicit held-skill base call for arms E/P."""

    def _candidate_features(self, observation, held_skill):
        features = self.base(observation, held_skill)
        expected = observation.shape[:-1] + (self.hidden_size,)
        if self.hidden_size != OUTPUT_DIM or features.shape != expected:
            raise RuntimeError(
                f"GCEA B01 actor base must return shape {tuple(expected)}, "
                f"got {tuple(features.shape)}"
            )
        return features

    def forward(
        self,
        obs,
        rnn_states,
        masks,
        agent_skill,
        available_actions=None,
        deterministic=False,
    ):
        obs = check(obs).to(**self.tpdv)
        rnn_states = check(rnn_states).to(**self.tpdv)
        masks = check(masks).to(**self.tpdv)
        agent_skill = check(agent_skill).to(**self.tpdv)
        if available_actions is not None:
            available_actions = check(available_actions).to(**self.tpdv)

        actor_features = self._candidate_features(obs, agent_skill)
        skill_one_hot = F.one_hot(
            agent_skill.long(), num_classes=self.film_generator.in_features
        ).float()
        gamma, beta = torch.chunk(self.film_generator(skill_one_hot), 2, dim=-1)
        actor_features = gamma * actor_features + beta
        if self._use_naive_recurrent_policy or self._use_recurrent_policy:
            actor_features, rnn_states = self.rnn(actor_features, rnn_states, masks)
        actions, action_log_probs = self.act(
            actor_features, available_actions, deterministic
        )
        return actions, action_log_probs, rnn_states

    def evaluate_actions(
        self,
        obs,
        rnn_states,
        action,
        masks,
        agent_skill,
        available_actions=None,
        active_masks=None,
    ):
        obs = check(obs).to(**self.tpdv)
        rnn_states = check(rnn_states).to(**self.tpdv)
        action = check(action).to(**self.tpdv)
        masks = check(masks).to(**self.tpdv)
        agent_skill = check(agent_skill).to(**self.tpdv)
        if available_actions is not None:
            available_actions = check(available_actions).to(**self.tpdv)
        if active_masks is not None:
            active_masks = check(active_masks).to(**self.tpdv)

        actor_features = self._candidate_features(obs, agent_skill)
        skill_one_hot = F.one_hot(
            agent_skill.long(), num_classes=self.film_generator.in_features
        ).float()
        gamma, beta = torch.chunk(self.film_generator(skill_one_hot), 2, dim=-1)
        actor_features = gamma * actor_features + beta
        if self._use_naive_recurrent_policy or self._use_recurrent_policy:
            actor_features, rnn_states = self.rnn(actor_features, rnn_states, masks)
        return self.act.evaluate_actions(
            actor_features,
            action,
            available_actions,
            active_masks=active_masks if self._use_policy_active_masks else None,
        )


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


def _instrument_actor(actor) -> ActorTiming:
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
        raise RuntimeError("GCEA B01 requires the standing single-group actor optimizer")
    if getattr(agent, "discoverer_actor_scheduler", None) is not None:
        raise RuntimeError("GCEA B01 does not permit an actor learning-rate schedule")
    group_options = {
        key: value
        for key, value in old.param_groups[0].items()
        if key not in {"params", "initial_lr"}
    }
    parameters = agent.skill_discoverer.actor_update_parameters()
    if agent.low_level_compact_extractor is not None:
        parameters = parameters + list(agent.low_level_compact_extractor.parameters())
    agent.discoverer_actor_optimizer = type(old)(parameters, **group_options)
    owned = [
        parameter
        for group in agent.discoverer_actor_optimizer.param_groups
        for parameter in group["params"]
    ]
    if len(owned) != len(parameters) or {id(p) for p in owned} != {
        id(p) for p in parameters
    }:
        raise RuntimeError(
            "rebuilt actor optimizer does not own exactly the active actor parameters"
        )


def install_actor_encoder(agent, arm: str):
    """Install O/P/E before training while preserving the caller's torch RNG stream."""
    actor = agent.skill_discoverer.actor
    if int(agent.config.obs_dim) != OBS_DIM or int(actor.hidden_size) != OUTPUT_DIM:
        raise ValueError("GCEA B01 is bound to a 104-float observation and 256-wide actor")
    original_type = type(actor.base).__name__
    if arm in {"P", "E"}:
        rng_state = torch.random.get_rng_state()
        try:
            replacement = (
                ConditionalDeepSetsEncoder() if arm == "P" else EarlyAttentionEncoder()
            ).to(**actor.tpdv)
        finally:
            torch.random.set_rng_state(rng_state)
        actor.base = replacement
        actor.__class__ = GoalConditionedActor
    elif arm != "O":
        raise ValueError(f"unknown GCEA B01 arm {arm!r}; expected one of O, P, E")

    _rebuild_actor_optimizer(agent)
    timing = _instrument_actor(actor)
    return {
        "arm": arm,
        "original_base_type": original_type,
        "active_base_type": type(actor.base).__name__,
        "encoder_parameters": sum(p.numel() for p in actor.base.parameters()),
        "actor_parameters": sum(p.numel() for p in actor.parameters()),
        "timing": timing,
    }
