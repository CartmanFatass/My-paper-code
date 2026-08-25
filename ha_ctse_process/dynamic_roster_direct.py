"""Stage-B direct primitive-action AR access instrument.

This module is intentionally isolated from the HMASD/F0/F1 trainers.  It owns
only the small recurrent actor-critic, rollout ledger, PPO replay, and
evaluation path registered in ``F0_F1_DYNAMIC_ROSTER_TESTBED_CONTRACT.md``.
There are no skills, high-level actions, intrinsic rewards, or task-specific
reward additions here.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any, Callable, Iterable, Protocol, TypeVar, cast

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F

from ha_ctse_process.dynamic_roster_testbed import (
    ACTION_COUNT,
    HORIZON,
    MAX_LIFECYCLES,
    OBSERVATION_DIM,
    DynamicRosterLedger,
    EpisodeOutcome,
    GenericShortDynamicRosterEnv,
    make_dynamic_roster_ledger,
)


HIDDEN_DIM = 32
MAX_RECURRENT_CHUNK = 20
GAMMA = 0.99
GAE_LAMBDA = 0.95
PPO_CLIP = 0.20
VALUE_CLIP = 0.20
VALUE_COEFFICIENT = 0.50
ENTROPY_COEFFICIENT = 0.01
GRADIENT_CLIP = 0.50
LEARNING_RATE = 3e-4
PPO_PASSES = 4
SCHEMA_VERSION = 3

MODEL_INITIALIZATION_SEED = 57_056
TRAIN_LEDGER_SEED = 67_057
POLICY_ACTION_SEED = 87_057
EVAL_LEDGER_SEED = 97_057
BOOTSTRAP_SEED = 107_057
REPLAY_TOLERANCE = 1e-6


class DirectRosterLedger(Protocol):
    """Minimum ledger surface consumed by the direct active-set learner."""

    direct_frontier_priorities: np.ndarray


_LedgerT = TypeVar("_LedgerT")


def _shared_lifecycle_capacity(ledgers: Iterable[DirectRosterLedger]) -> int:
    capacities = {
        int(np.asarray(ledger.direct_frontier_priorities).shape[1])
        for ledger in ledgers
    }
    if len(capacities) != 1:
        raise ValueError("direct collection requires one shared operational capacity")
    capacity = capacities.pop()
    if capacity <= 0:
        raise ValueError("direct collection requires positive operational capacity")
    return capacity


def _make_direct_environments(
    episode_ids: tuple[int, ...],
    *,
    master_seed: int,
    ledger_factory: Callable[..., _LedgerT] | None,
    environment_factory: Callable[[_LedgerT], GenericShortDynamicRosterEnv] | None,
) -> tuple[tuple[_LedgerT, ...], list[GenericShortDynamicRosterEnv]]:
    make_ledger = (
        cast(Callable[..., _LedgerT], make_dynamic_roster_ledger)
        if ledger_factory is None
        else ledger_factory
    )
    make_environment = (
        cast(
            Callable[[_LedgerT], GenericShortDynamicRosterEnv],
            GenericShortDynamicRosterEnv,
        )
        if environment_factory is None
        else environment_factory
    )
    ledgers = tuple(
        make_ledger(episode_id, master_seed=master_seed)
        for episode_id in episode_ids
    )
    return ledgers, [make_environment(ledger) for ledger in ledgers]


@dataclass
class DirectStepOutput:
    actions: torch.Tensor
    token_log_probs: torch.Tensor
    token_entropies: torch.Tensor
    value: torch.Tensor
    next_hidden: torch.Tensor
    prefix_counts: torch.Tensor


@dataclass
class DirectPreparedStep:
    """One encoded source-policy step, reusable by an attached event head."""

    member_embeddings: torch.Tensor
    context_input: torch.Tensor
    context: torch.Tensor
    value: torch.Tensor


class DirectPrimitiveARPolicy(nn.Module):
    """Anonymous per-lifecycle recurrent actor with an active-set critic."""

    def __init__(
        self,
        hidden_dim: int = HIDDEN_DIM,
        *,
        autoregressive_prefix: str = "raw_count",
    ) -> None:
        super().__init__()
        self.hidden_dim = int(hidden_dim)
        if autoregressive_prefix not in {"raw_count", "active_fraction"}:
            raise ValueError("unknown direct autoregressive prefix")
        self.autoregressive_prefix = autoregressive_prefix
        self.member_encoder = nn.Sequential(
            nn.Linear(OBSERVATION_DIM, self.hidden_dim),
            nn.Tanh(),
            nn.Linear(self.hidden_dim, self.hidden_dim),
            nn.Tanh(),
        )
        self.context_encoder = nn.Sequential(
            nn.Linear(self.hidden_dim + 1, self.hidden_dim),
            nn.Tanh(),
        )
        self.actor_rnn = nn.GRUCell(
            2 * self.hidden_dim + ACTION_COUNT,
            self.hidden_dim,
        )
        self.action_head = nn.Sequential(
            nn.Linear(self.hidden_dim + ACTION_COUNT, self.hidden_dim),
            nn.Tanh(),
            nn.Linear(self.hidden_dim, ACTION_COUNT),
        )
        self.critic = nn.Sequential(
            nn.Linear(self.hidden_dim + 1 + 8, self.hidden_dim),
            nn.Tanh(),
            nn.Linear(self.hidden_dim, 1),
        )

    @property
    def parameter_count(self) -> int:
        return int(sum(parameter.numel() for parameter in self.parameters()))

    @property
    def roster_representation(self) -> dict[str, str]:
        return {
            "autoregressive_prefix": self.autoregressive_prefix,
        }

    def prepare_step(
        self,
        *,
        observations: torch.Tensor,
        active_mask: torch.Tensor,
        validated: bool = False,
    ) -> DirectPreparedStep:
        """Encode the ordinary observation and critic inputs exactly once."""

        if observations.ndim != 3:
            raise ValueError("direct actor observations must be [batch, members, fields]")
        batch, members, observation_dim = observations.shape
        if not validated and (members <= 0 or observation_dim != OBSERVATION_DIM):
            raise ValueError("direct actor observation shape mismatch")
        if not validated and tuple(active_mask.shape) != (batch, members):
            raise ValueError("direct actor active mask shape mismatch")
        active_count = active_mask.sum(dim=1)
        if not validated and bool((active_count <= 0).any()):
            raise ValueError("direct actor requires a non-empty active set")
        dtype = observations.dtype
        device = observations.device
        batch_index = torch.arange(batch, device=device)
        member_embeddings = self.member_encoder(observations)
        float_mask = active_mask.to(dtype).unsqueeze(-1)
        member_sum = (member_embeddings * float_mask).sum(dim=1)
        count_feature = torch.log1p(active_count.to(dtype)).unsqueeze(-1)
        context_input = torch.cat((member_sum, count_feature), dim=-1)
        context = self.context_encoder(context_input)
        first_active = torch.argmax(active_mask.to(torch.int64), dim=1)
        common_fields = observations[batch_index, first_active, :8]
        value = self.critic(torch.cat((context_input, common_fields), dim=-1)).squeeze(-1)
        return DirectPreparedStep(
            member_embeddings=member_embeddings,
            context_input=context_input,
            context=context,
            value=value,
        )

    def forward_step(
        self,
        *,
        observations: torch.Tensor,
        active_mask: torch.Tensor,
        order: torch.Tensor,
        hidden: torch.Tensor,
        sampling_uniforms: torch.Tensor | None = None,
        teacher_actions: torch.Tensor | None = None,
        deterministic: bool = False,
        primitive_logit_bias: torch.Tensor | None = None,
        prepared: DirectPreparedStep | None = None,
        validated: bool = False,
    ) -> DirectStepOutput:
        if observations.ndim != 3:
            raise ValueError("direct actor observations must be [batch, members, fields]")
        batch, members, observation_dim = observations.shape
        if not validated and (members <= 0 or observation_dim != OBSERVATION_DIM):
            raise ValueError("direct actor observation shape mismatch")
        if not validated and tuple(active_mask.shape) != (batch, members):
            raise ValueError("direct actor active mask shape mismatch")
        if not validated and tuple(order.shape) != (batch, members):
            raise ValueError("direct actor order shape mismatch")
        if not validated and tuple(hidden.shape) != (batch, members, self.hidden_dim):
            raise ValueError("direct actor hidden shape mismatch")
        modes = int(sampling_uniforms is not None) + int(
            teacher_actions is not None
        ) + int(bool(deterministic))
        if not validated and modes != 1:
            raise ValueError("choose exactly one sampling, replay, or deterministic mode")
        if not validated and sampling_uniforms is not None and tuple(sampling_uniforms.shape) != (
            batch,
            members,
        ):
            raise ValueError("direct actor sampling-uniform shape mismatch")
        if not validated and teacher_actions is not None and tuple(teacher_actions.shape) != (
            batch,
            members,
        ):
            raise ValueError("direct actor teacher-action shape mismatch")
        if not validated and primitive_logit_bias is not None and tuple(primitive_logit_bias.shape) != (
            batch,
            members,
            ACTION_COUNT,
        ):
            raise ValueError("direct actor primitive-logit-bias shape mismatch")

        active_count = active_mask.sum(dim=1)
        if not validated and bool((active_count <= 0).any()):
            raise ValueError("direct actor requires a non-empty active set")
        expected_positions = torch.arange(members, device=order.device).unsqueeze(0)
        position_mask = expected_positions < active_count.unsqueeze(1)
        if not validated:
            safe_order = order.clamp(min=0)
            order_active = torch.gather(active_mask, 1, safe_order)
            if not bool(torch.equal(order.ge(0), position_mask)):
                raise ValueError("direct actor order padding does not match active count")
            if not bool(order_active[position_mask].all()):
                raise ValueError("direct actor order contains an inactive lifecycle")
            sorted_order = torch.sort(
                torch.where(position_mask, order, torch.full_like(order, members)), dim=1
            ).values
            sorted_active = torch.sort(
                torch.where(
                    active_mask,
                    torch.arange(members, device=order.device).unsqueeze(0),
                    torch.full_like(order, members),
                ),
                dim=1,
            ).values
            if not bool(torch.equal(sorted_order, sorted_active)):
                raise ValueError("direct actor order is not a permutation of active members")

        dtype = observations.dtype
        device = observations.device
        batch_index = torch.arange(batch, device=device)
        encoded = self.prepare_step(
            observations=observations, active_mask=active_mask, validated=validated
        ) if prepared is None else prepared
        member_embeddings = encoded.member_embeddings
        context = encoded.context
        value = encoded.value

        next_hidden = hidden.clone()
        prefix = torch.zeros(
            (batch, ACTION_COUNT), dtype=dtype, device=device
        )
        actions = torch.full(
            (batch, members), -1, dtype=torch.long, device=device
        )
        log_probs = torch.zeros((batch, members), dtype=dtype, device=device)
        entropies = torch.zeros((batch, members), dtype=dtype, device=device)
        prefix_rows = torch.zeros(
            (batch, members, ACTION_COUNT), dtype=dtype, device=device
        )
        prefix_denominator = active_count.to(dtype).unsqueeze(-1)

        for position in range(members):
            valid = position_mask[:, position]
            if not validated and not bool(valid.any()):
                break
            focal = order[:, position].clamp(min=0)
            local_embedding = member_embeddings[batch_index, focal]
            local_hidden = next_hidden[batch_index, focal]
            prefix_input = (
                prefix / prefix_denominator
                if self.autoregressive_prefix == "active_fraction"
                else prefix
            )
            candidate_hidden = self.actor_rnn(
                torch.cat((local_embedding, context, prefix_input), dim=-1),
                local_hidden,
            )
            logits = self.action_head(
                torch.cat((candidate_hidden, prefix_input), dim=-1)
            )
            if primitive_logit_bias is not None:
                logits = logits + primitive_logit_bias[batch_index, focal]
            log_probability = F.log_softmax(logits, dim=-1)
            probability = torch.exp(log_probability)
            if teacher_actions is not None:
                selected = teacher_actions[batch_index, focal]
            elif deterministic:
                selected = torch.argmax(logits, dim=-1)
            else:
                assert sampling_uniforms is not None
                cumulative = torch.cumsum(probability, dim=-1)
                selected = torch.sum(
                    sampling_uniforms[:, position].unsqueeze(-1) > cumulative,
                    dim=-1,
                ).clamp(max=ACTION_COUNT - 1)
            if not validated and bool(((selected < 0) | (selected >= ACTION_COUNT))[valid].any()):
                raise ValueError("direct actor selected an invalid primitive action")
            safe_selected = selected.clamp(min=0, max=ACTION_COUNT - 1)

            selected_logp = torch.gather(
                log_probability, 1, safe_selected.unsqueeze(-1)
            ).squeeze(-1)
            entropy = -(probability * log_probability).sum(dim=-1)
            prefix_rows[:, position] = prefix
            valid_batch = batch_index[valid]
            valid_focal = focal[valid]
            next_hidden[valid_batch, valid_focal] = candidate_hidden[valid]
            actions[valid_batch, valid_focal] = safe_selected[valid]
            log_probs[valid_batch, valid_focal] = selected_logp[valid]
            entropies[valid_batch, valid_focal] = entropy[valid]
            prefix.scatter_add_(
                1,
                safe_selected.unsqueeze(-1),
                valid.to(dtype).unsqueeze(-1),
            )

        return DirectStepOutput(
            actions=actions,
            token_log_probs=log_probs,
            token_entropies=entropies,
            value=value,
            next_hidden=next_hidden,
            prefix_counts=prefix_rows,
        )


@dataclass
class DirectTrajectory:
    observations: torch.Tensor
    active_mask: torch.Tensor
    orders: torch.Tensor
    actions: torch.Tensor
    old_log_probs: torch.Tensor
    old_values: torch.Tensor
    rewards: torch.Tensor
    hidden_before: torch.Tensor
    hidden_after: torch.Tensor
    prefix_counts: torch.Tensor
    outcomes: tuple[EpisodeOutcome, ...]
    ledger_ids: tuple[int, ...]

    @property
    def environment_steps(self) -> int:
        return int(self.rewards.numel())

    @property
    def active_token_count(self) -> int:
        return int(self.active_mask.sum().item())


def _frontier_order(
    ledgers: Iterable[DirectRosterLedger],
    active_masks: np.ndarray,
    time: int,
) -> np.ndarray:
    capacity = int(active_masks.shape[1])
    rows: list[np.ndarray] = []
    for ledger, mask in zip(ledgers, active_masks):
        priorities = np.asarray(ledger.direct_frontier_priorities)
        if tuple(priorities.shape) != (HORIZON, capacity):
            raise ValueError("direct frontier priority shape mismatch")
        active = np.flatnonzero(mask)
        sorted_keys = active[
            np.argsort(priorities[time, active])
        ]
        row = np.full(capacity, -1, dtype=np.int64)
        row[: len(sorted_keys)] = sorted_keys
        rows.append(row)
    return np.stack(rows, axis=0)


def collect_direct_trajectory(
    model: DirectPrimitiveARPolicy,
    *,
    ledger_ids: Iterable[int],
    ledger_seed: int,
    action_seed: int = POLICY_ACTION_SEED,
    device: torch.device,
    ledger_factory: Callable[..., _LedgerT] | None = None,
    environment_factory: Callable[
        [_LedgerT], GenericShortDynamicRosterEnv
    ] | None = None,
) -> DirectTrajectory:
    ids = tuple(int(value) for value in ledger_ids)
    if not ids:
        raise ValueError("direct collection requires at least one environment")
    ledgers, environments = _make_direct_environments(
        ids,
        master_seed=ledger_seed,
        ledger_factory=ledger_factory,
        environment_factory=environment_factory,
    )
    capacity = _shared_lifecycle_capacity(ledgers)
    action_uniforms = make_action_uniforms(
        ids,
        lifecycle_capacity=capacity,
        action_seed=action_seed,
    )
    env_count = len(environments)
    hidden = torch.zeros(
        (env_count, capacity, model.hidden_dim),
        dtype=torch.float32,
        device=device,
    )

    observations_rows: list[torch.Tensor] = []
    active_rows: list[torch.Tensor] = []
    order_rows: list[torch.Tensor] = []
    action_rows: list[torch.Tensor] = []
    logp_rows: list[torch.Tensor] = []
    value_rows: list[torch.Tensor] = []
    reward_rows: list[torch.Tensor] = []
    hidden_before_rows: list[torch.Tensor] = []
    hidden_after_rows: list[torch.Tensor] = []
    prefix_rows: list[torch.Tensor] = []

    model.eval()
    with torch.no_grad():
        for time in range(HORIZON):
            obs_np = np.zeros(
                (env_count, capacity, OBSERVATION_DIM), dtype=np.float32
            )
            active_np = np.zeros(
                (env_count, capacity), dtype=np.bool_
            )
            views = []
            for env_index, environment in enumerate(environments):
                view = environment.observe()
                views.append(view)
                for row_index, key in enumerate(view.active_keys):
                    obs_np[env_index, key] = view.observations[row_index]
                    active_np[env_index, key] = True
            order_np = _frontier_order(ledgers, active_np, time)
            uniforms_np = action_uniforms[time]
            observations = torch.as_tensor(obs_np, device=device)
            active_mask = torch.as_tensor(active_np, device=device)
            order = torch.as_tensor(order_np, device=device)
            uniforms = torch.as_tensor(uniforms_np, device=device)
            hidden_before = hidden.clone()
            output = model.forward_step(
                observations=observations,
                active_mask=active_mask,
                order=order,
                hidden=hidden,
                sampling_uniforms=uniforms,
            )
            action_values = output.actions.detach().cpu().numpy()
            rewards = np.zeros(env_count, dtype=np.float32)
            for env_index, (environment, view) in enumerate(
                zip(environments, views)
            ):
                actions = {
                    key: int(action_values[env_index, key])
                    for key in view.active_keys
                }
                reward, _terminal, _info = environment.step(actions)
                rewards[env_index] = reward

            observations_rows.append(observations)
            active_rows.append(active_mask)
            order_rows.append(order)
            action_rows.append(output.actions)
            logp_rows.append(output.token_log_probs)
            value_rows.append(output.value)
            reward_rows.append(torch.from_numpy(rewards))
            hidden_before_rows.append(hidden_before)
            hidden_after_rows.append(output.next_hidden)
            prefix_rows.append(output.prefix_counts)
            hidden = output.next_hidden

    outcomes = tuple(environment.outcome() for environment in environments)
    return DirectTrajectory(
        observations=torch.stack(observations_rows).cpu(),
        active_mask=torch.stack(active_rows).cpu(),
        orders=torch.stack(order_rows).cpu(),
        actions=torch.stack(action_rows).cpu(),
        old_log_probs=torch.stack(logp_rows).cpu(),
        old_values=torch.stack(value_rows).cpu(),
        rewards=torch.stack(reward_rows),
        hidden_before=torch.stack(hidden_before_rows).cpu(),
        hidden_after=torch.stack(hidden_after_rows).cpu(),
        prefix_counts=torch.stack(prefix_rows).cpu(),
        outcomes=outcomes,
        ledger_ids=ids,
    )


def compute_gae(
    rewards: torch.Tensor,
    values: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    if rewards.shape != values.shape or rewards.ndim != 2:
        raise ValueError("direct GAE expects matching [time, env] tensors")
    advantages = torch.zeros_like(rewards)
    running = torch.zeros(rewards.shape[1], dtype=rewards.dtype)
    next_value = torch.zeros_like(running)
    for time in reversed(range(rewards.shape[0])):
        continuation = 0.0 if time == rewards.shape[0] - 1 else 1.0
        delta = rewards[time] + GAMMA * next_value * continuation - values[time]
        running = delta + GAMMA * GAE_LAMBDA * continuation * running
        advantages[time] = running
        next_value = values[time]
    returns = advantages + values
    mean = advantages.mean()
    std = advantages.std(unbiased=False).clamp_min(1e-8)
    return (advantages - mean) / std, returns


def hidden_lifecycle_contract_valid(trajectory: DirectTrajectory) -> bool:
    for env_index, episode_id in enumerate(trajectory.ledger_ids):
        ledger = make_dynamic_roster_ledger(
            episode_id, master_seed=TRAIN_LEDGER_SEED
        )
        for key in ledger.temporary_leave:
            frozen = trajectory.hidden_after[19, env_index, key]
            if not torch.equal(trajectory.hidden_before[20, env_index, key], frozen):
                return False
            if not torch.equal(trajectory.hidden_after[39, env_index, key], frozen):
                return False
            if not torch.equal(trajectory.hidden_before[40, env_index, key], frozen):
                return False
        for key in (4, 5):
            if not torch.equal(
                trajectory.hidden_before[40, env_index, key],
                torch.zeros_like(trajectory.hidden_before[40, env_index, key]),
            ):
                return False
    return True


def _chunk_time_env(tensor: torch.Tensor) -> torch.Tensor:
    if tensor.shape[0] != HORIZON:
        raise ValueError("direct recurrent packing requires a full horizon")
    env_count = tensor.shape[1]
    chunks = HORIZON // MAX_RECURRENT_CHUNK
    tail = tensor.shape[2:]
    return (
        tensor.reshape(chunks, MAX_RECURRENT_CHUNK, env_count, *tail)
        .permute(0, 2, 1, *range(3, tensor.ndim + 1))
        .reshape(chunks * env_count, MAX_RECURRENT_CHUNK, *tail)
    )


@dataclass
class DirectReplay:
    log_probs: torch.Tensor
    entropies: torch.Tensor
    values: torch.Tensor
    hidden_after: torch.Tensor
    prefix_counts: torch.Tensor
    active_mask: torch.Tensor


@dataclass
class DirectPackedTrajectory:
    observations: torch.Tensor
    active_mask: torch.Tensor
    orders: torch.Tensor
    actions: torch.Tensor
    initial_hidden: torch.Tensor
    old_log_probs: torch.Tensor
    old_values: torch.Tensor
    old_hidden_after: torch.Tensor
    old_prefix_counts: torch.Tensor


def _pack_direct_trajectory(
    trajectory: DirectTrajectory,
    *,
    device: torch.device,
    hidden_dim: int,
) -> DirectPackedTrajectory:
    lifecycle_capacity = int(trajectory.observations.shape[2])
    return DirectPackedTrajectory(
        observations=_chunk_time_env(trajectory.observations).to(device),
        active_mask=_chunk_time_env(trajectory.active_mask).to(device),
        orders=_chunk_time_env(trajectory.orders).to(device),
        actions=_chunk_time_env(trajectory.actions).to(device),
        initial_hidden=trajectory.hidden_before[::MAX_RECURRENT_CHUNK]
        .reshape(-1, lifecycle_capacity, hidden_dim)
        .to(device),
        old_log_probs=_chunk_time_env(trajectory.old_log_probs).to(device),
        old_values=_chunk_time_env(trajectory.old_values).to(device),
        old_hidden_after=_chunk_time_env(trajectory.hidden_after).to(device),
        old_prefix_counts=_chunk_time_env(trajectory.prefix_counts).to(device),
    )


def _replay_packed_direct_trajectory(
    model: DirectPrimitiveARPolicy,
    packed: DirectPackedTrajectory,
) -> DirectReplay:
    observations = packed.observations
    active_mask = packed.active_mask
    orders = packed.orders
    actions = packed.actions
    initial_hidden = packed.initial_hidden
    env_count = observations.shape[0] // (HORIZON // MAX_RECURRENT_CHUNK)
    chunk_count = HORIZON // MAX_RECURRENT_CHUNK
    chunk_log_probs: list[torch.Tensor] = []
    chunk_entropies: list[torch.Tensor] = []
    chunk_values: list[torch.Tensor] = []
    chunk_hidden_after: list[torch.Tensor] = []
    chunk_prefix_counts: list[torch.Tensor] = []
    for chunk_index in range(chunk_count):
        chunk_slice = slice(
            chunk_index * env_count, (chunk_index + 1) * env_count
        )
        hidden = initial_hidden[chunk_slice]
        logp_rows: list[torch.Tensor] = []
        entropy_rows: list[torch.Tensor] = []
        value_rows: list[torch.Tensor] = []
        hidden_rows: list[torch.Tensor] = []
        prefix_rows: list[torch.Tensor] = []
        for offset in range(MAX_RECURRENT_CHUNK):
            output = model.forward_step(
                observations=observations[chunk_slice, offset].contiguous(),
                active_mask=active_mask[chunk_slice, offset].contiguous(),
                order=orders[chunk_slice, offset].contiguous(),
                hidden=hidden,
                teacher_actions=actions[chunk_slice, offset].contiguous(),
            )
            logp_rows.append(output.token_log_probs)
            entropy_rows.append(output.token_entropies)
            value_rows.append(output.value)
            hidden_rows.append(output.next_hidden)
            prefix_rows.append(output.prefix_counts)
            hidden = output.next_hidden
        chunk_log_probs.append(torch.stack(logp_rows, dim=1))
        chunk_entropies.append(torch.stack(entropy_rows, dim=1))
        chunk_values.append(torch.stack(value_rows, dim=1))
        chunk_hidden_after.append(torch.stack(hidden_rows, dim=1))
        chunk_prefix_counts.append(torch.stack(prefix_rows, dim=1))
    return DirectReplay(
        log_probs=torch.cat(chunk_log_probs, dim=0),
        entropies=torch.cat(chunk_entropies, dim=0),
        values=torch.cat(chunk_values, dim=0),
        hidden_after=torch.cat(chunk_hidden_after, dim=0),
        prefix_counts=torch.cat(chunk_prefix_counts, dim=0),
        active_mask=active_mask,
    )


def replay_direct_trajectory(
    model: DirectPrimitiveARPolicy,
    trajectory: DirectTrajectory,
    *,
    device: torch.device,
) -> DirectReplay:
    return _replay_packed_direct_trajectory(
        model,
        _pack_direct_trajectory(
            trajectory, device=device, hidden_dim=model.hidden_dim
        ),
    )


def replay_errors(
    replay: DirectReplay,
    trajectory: DirectTrajectory,
) -> dict[str, float]:
    packed = _pack_direct_trajectory(
        trajectory,
        device=replay.log_probs.device,
        hidden_dim=trajectory.hidden_before.shape[-1],
    )
    return _replay_errors_packed(replay, packed)


def _replay_errors_packed(
    replay: DirectReplay,
    packed: DirectPackedTrajectory,
) -> dict[str, float]:
    old_logp = packed.old_log_probs
    old_value = packed.old_values
    old_hidden = packed.old_hidden_after
    old_prefix = packed.old_prefix_counts
    mask = replay.active_mask
    position_mask = (
        torch.arange(mask.shape[-1], device=mask.device)
        .view(1, 1, -1)
        .lt(mask.sum(dim=-1, keepdim=True))
    )
    token_difference = torch.abs(replay.log_probs - old_logp)
    joint_difference = torch.abs(
        torch.where(mask, replay.log_probs - old_logp, 0.0).sum(dim=-1)
    )
    return {
        "logp_max_error": float(
            torch.max(token_difference[mask]).detach().cpu()
        ),
        "joint_logp_max_error": float(
            torch.max(joint_difference).detach().cpu()
        ),
        "value_max_error": float(
            torch.max(torch.abs(replay.values - old_value)).detach().cpu()
        ),
        "hidden_max_error": float(
            torch.max(torch.abs(replay.hidden_after - old_hidden)).detach().cpu()
        ),
        "prefix_max_error": float(
            torch.max(
                torch.abs(replay.prefix_counts - old_prefix)[position_mask]
            ).detach().cpu()
        ),
    }


def ppo_loss(
    replay: DirectReplay,
    trajectory: DirectTrajectory,
    advantages: torch.Tensor,
    returns: torch.Tensor,
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    packed = _pack_direct_trajectory(
        trajectory,
        device=replay.log_probs.device,
        hidden_dim=trajectory.hidden_before.shape[-1],
    )
    return _ppo_loss_packed(
        replay,
        packed,
        _chunk_time_env(advantages).to(replay.log_probs.device),
        _chunk_time_env(returns).to(replay.log_probs.device),
    )


def _ppo_loss_packed(
    replay: DirectReplay,
    packed: DirectPackedTrajectory,
    chunk_advantages: torch.Tensor,
    chunk_returns: torch.Tensor,
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    old_logp = packed.old_log_probs
    old_values = packed.old_values
    mask = replay.active_mask

    ratio = torch.exp(replay.log_probs - old_logp)
    expanded_advantage = chunk_advantages.unsqueeze(-1)
    surrogate = torch.minimum(
        ratio * expanded_advantage,
        torch.clamp(ratio, 1.0 - PPO_CLIP, 1.0 + PPO_CLIP)
        * expanded_advantage,
    )
    active_count = mask.sum(dim=-1).clamp_min(1)
    policy_loss = -(
        torch.where(mask, surrogate, 0.0).sum(dim=-1) / active_count
    ).mean()
    entropy = (
        torch.where(mask, replay.entropies, 0.0).sum(dim=-1) / active_count
    ).mean()
    clipped_values = old_values + torch.clamp(
        replay.values - old_values, -VALUE_CLIP, VALUE_CLIP
    )
    value_loss = torch.maximum(
        torch.square(replay.values - chunk_returns),
        torch.square(clipped_values - chunk_returns),
    ).mean()
    total = policy_loss + VALUE_COEFFICIENT * value_loss - ENTROPY_COEFFICIENT * entropy
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
        "value_loss": value_loss,
        "entropy": entropy,
        "clip_fraction": clip_fraction,
    }


def optimize_direct_update(
    model: DirectPrimitiveARPolicy,
    optimizer: torch.optim.Optimizer,
    trajectory: DirectTrajectory,
    *,
    device: torch.device,
    ppo_passes: int = PPO_PASSES,
) -> dict[str, float]:
    advantages, returns = compute_gae(
        trajectory.rewards, trajectory.old_values
    )
    packed = _pack_direct_trajectory(
        trajectory, device=device, hidden_dim=model.hidden_dim
    )
    chunk_advantages = _chunk_time_env(advantages).to(device)
    chunk_returns = _chunk_time_env(returns).to(device)
    model.train()
    with torch.no_grad():
        first_replay = _replay_packed_direct_trajectory(model, packed)
        errors = _replay_errors_packed(first_replay, packed)

    totals = {name: 0.0 for name in (
        "policy_loss", "value_loss", "entropy", "clip_fraction", "gradient_norm"
    )}
    finite = True
    for _ in range(int(ppo_passes)):
        replay = _replay_packed_direct_trajectory(model, packed)
        loss, metrics = _ppo_loss_packed(
            replay, packed, chunk_advantages, chunk_returns
        )
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        gradient_norm = torch.nn.utils.clip_grad_norm_(
            model.parameters(), GRADIENT_CLIP
        )
        finite = finite and bool(torch.isfinite(loss)) and bool(
            torch.isfinite(gradient_norm)
        )
        optimizer.step()
        for name in ("policy_loss", "value_loss", "entropy", "clip_fraction"):
            totals[name] += float(metrics[name].detach().cpu())
        totals["gradient_norm"] += float(gradient_norm.detach().cpu())
    for name in totals:
        totals[name] /= float(ppo_passes)
    totals.update(errors)
    totals["finite_update"] = float(finite)
    totals["optimizer_steps"] = float(ppo_passes)
    return totals


def make_action_uniforms(
    episode_ids: Iterable[int],
    *,
    lifecycle_capacity: int = MAX_LIFECYCLES,
    action_seed: int = POLICY_ACTION_SEED,
) -> np.ndarray:
    ids = tuple(int(value) for value in episode_ids)
    capacity = int(lifecycle_capacity)
    if capacity <= 0:
        raise ValueError("action-uniform capacity must be positive")
    rows = []
    for episode_id in ids:
        rng = np.random.default_rng(
            np.random.SeedSequence([int(action_seed), episode_id, 0])
        )
        rows.append(
            rng.random((HORIZON, capacity), dtype=np.float32)
        )
    return np.stack(rows, axis=1)


def evaluate_direct_policy(
    model: DirectPrimitiveARPolicy,
    *,
    episode_ids: Iterable[int],
    deterministic: bool,
    device: torch.device,
    ledger_seed: int = EVAL_LEDGER_SEED,
    action_seed: int = POLICY_ACTION_SEED,
    uniforms: np.ndarray | None = None,
    ledger_factory: Callable[..., _LedgerT] | None = None,
    environment_factory: Callable[
        [_LedgerT], GenericShortDynamicRosterEnv
    ] | None = None,
) -> dict[str, Any]:
    ids = tuple(int(value) for value in episode_ids)
    ledgers, environments = _make_direct_environments(
        ids,
        master_seed=ledger_seed,
        ledger_factory=ledger_factory,
        environment_factory=environment_factory,
    )
    capacity = _shared_lifecycle_capacity(ledgers)
    env_count = len(environments)
    if not deterministic:
        if uniforms is None:
            uniforms = make_action_uniforms(
                ids,
                lifecycle_capacity=capacity,
                action_seed=action_seed,
            )
        if tuple(uniforms.shape) != (
            HORIZON,
            env_count,
            capacity,
        ):
            raise ValueError("evaluation uniform table shape mismatch")
    hidden = torch.zeros(
        (env_count, capacity, model.hidden_dim),
        dtype=torch.float32,
        device=device,
    )
    model.eval()
    with torch.no_grad():
        for time in range(HORIZON):
            obs_np = np.zeros(
                (env_count, capacity, OBSERVATION_DIM), dtype=np.float32
            )
            active_np = np.zeros(
                (env_count, capacity), dtype=np.bool_
            )
            views = []
            for env_index, environment in enumerate(environments):
                view = environment.observe()
                views.append(view)
                for row_index, key in enumerate(view.active_keys):
                    obs_np[env_index, key] = view.observations[row_index]
                    active_np[env_index, key] = True
            order_np = _frontier_order(ledgers, active_np, time)
            kwargs: dict[str, Any]
            if deterministic:
                kwargs = {"deterministic": True}
            else:
                assert uniforms is not None
                kwargs = {
                    "sampling_uniforms": torch.as_tensor(
                        uniforms[time], device=device
                    )
                }
            output = model.forward_step(
                observations=torch.as_tensor(obs_np, device=device),
                active_mask=torch.as_tensor(active_np, device=device),
                order=torch.as_tensor(order_np, device=device),
                hidden=hidden,
                **kwargs,
            )
            action_values = output.actions.detach().cpu().numpy()
            for env_index, (environment, view) in enumerate(
                zip(environments, views)
            ):
                environment.step(
                    {
                        key: int(action_values[env_index, key])
                        for key in view.active_keys
                    }
                )
            hidden = output.next_hidden
    outcomes = tuple(environment.outcome() for environment in environments)
    persistent = np.asarray(
        [outcome.persistent_score for outcome in outcomes], dtype=np.float64
    )
    short = np.asarray(
        [outcome.short_score for outcome in outcomes], dtype=np.float64
    )
    utility = np.asarray(
        [outcome.utility for outcome in outcomes], dtype=np.float64
    )
    return {
        "episode_ids": list(ids),
        "persistent": persistent,
        "short": short,
        "utility": utility,
        "persistent_mean": float(persistent.mean()),
        "short_mean": float(short.mean()),
        "utility_mean": float(utility.mean()),
    }


def paired_bootstrap_ci(
    differences: np.ndarray,
    *,
    repetitions: int = 10_000,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[float, float, float]:
    values = np.asarray(differences, dtype=np.float64)
    rng = np.random.default_rng(int(seed))
    indices = rng.integers(
        0, values.size, size=(int(repetitions), values.size), dtype=np.int64
    )
    estimates = values[indices].mean(axis=1)
    return (
        float(np.quantile(estimates, 0.025)),
        float(values.mean()),
        float(np.quantile(estimates, 0.975)),
    )


def model_state_copy(model: nn.Module) -> dict[str, torch.Tensor]:
    return {
        name: tensor.detach().cpu().clone()
        for name, tensor in model.state_dict().items()
    }


def maximum_state_difference(
    left: dict[str, torch.Tensor],
    right: dict[str, torch.Tensor],
) -> float:
    if left.keys() != right.keys():
        return float("inf")
    return max(
        float(torch.max(torch.abs(left[name] - right[name])))
        for name in left
    )


def state_dict_finite(state: dict[str, torch.Tensor]) -> bool:
    return all(bool(torch.isfinite(value).all()) for value in state.values())


def nested_state_maximum_difference(left: Any, right: Any) -> float:
    if isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor):
        if left.shape != right.shape:
            return float("inf")
        return float(
            torch.max(torch.abs(left.detach().cpu() - right.detach().cpu()))
        )
    if isinstance(left, dict) and isinstance(right, dict):
        if left.keys() != right.keys():
            return float("inf")
        return max(
            (nested_state_maximum_difference(left[key], right[key]) for key in left),
            default=0.0,
        )
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        if len(left) != len(right):
            return float("inf")
        return max(
            (
                nested_state_maximum_difference(left_value, right_value)
                for left_value, right_value in zip(left, right)
            ),
            default=0.0,
        )
    return 0.0 if left == right else float("inf")


def save_checkpoint(
    path: Path,
    *,
    model: DirectPrimitiveARPolicy,
    optimizer: torch.optim.Optimizer,
    completed_updates: int,
    next_ledger_id: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "schema_version": SCHEMA_VERSION,
            "kind": "dynamic_roster_direct_primitive_ar",
            "hidden_dim": model.hidden_dim,
            "completed_updates": int(completed_updates),
            "next_ledger_id": int(next_ledger_id),
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "model_initialization_seed": MODEL_INITIALIZATION_SEED,
            "train_ledger_seed": TRAIN_LEDGER_SEED,
            "policy_action_seed": POLICY_ACTION_SEED,
            "torch_rng_state": torch.get_rng_state(),
            "torch_cuda_rng_states": (
                torch.cuda.get_rng_state_all() if torch.cuda.is_available() else []
            ),
        },
        path,
    )


def load_checkpoint(
    path: Path,
    *,
    model: DirectPrimitiveARPolicy,
    optimizer: torch.optim.Optimizer,
) -> dict[str, Any]:
    bundle = torch.load(path, map_location="cpu", weights_only=False)
    required = {
        "schema_version",
        "kind",
        "hidden_dim",
        "completed_updates",
        "next_ledger_id",
        "model_state",
        "optimizer_state",
        "model_initialization_seed",
        "train_ledger_seed",
        "policy_action_seed",
        "torch_rng_state",
        "torch_cuda_rng_states",
    }
    if set(bundle) != required:
        raise ValueError("direct checkpoint key set mismatch")
    if bundle["schema_version"] != SCHEMA_VERSION:
        raise ValueError("direct checkpoint schema mismatch")
    if bundle["kind"] != "dynamic_roster_direct_primitive_ar":
        raise ValueError("direct checkpoint kind mismatch")
    if int(bundle["hidden_dim"]) != model.hidden_dim:
        raise ValueError("direct checkpoint architecture mismatch")
    if (
        int(bundle["model_initialization_seed"]) != MODEL_INITIALIZATION_SEED
        or int(bundle["train_ledger_seed"]) != TRAIN_LEDGER_SEED
        or int(bundle["policy_action_seed"]) != POLICY_ACTION_SEED
    ):
        raise ValueError("direct checkpoint RNG contract mismatch")
    model.load_state_dict(bundle["model_state"], strict=True)
    optimizer.load_state_dict(bundle["optimizer_state"])
    model_device = next(model.parameters()).device
    for state in optimizer.state.values():
        for key, value in state.items():
            if isinstance(value, torch.Tensor):
                state[key] = value.to(model_device)
    torch.set_rng_state(bundle["torch_rng_state"])
    if torch.cuda.is_available() and bundle["torch_cuda_rng_states"]:
        torch.cuda.set_rng_state_all(bundle["torch_cuda_rng_states"])
    return bundle


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return json_ready(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, torch.Tensor):
        return json_ready(value.detach().cpu().numpy())
    return value
