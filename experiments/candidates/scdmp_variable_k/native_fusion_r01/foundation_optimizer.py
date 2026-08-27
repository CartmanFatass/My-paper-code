"""Pure result-blind arithmetic for CLOSED-R01 foundation updates."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable

import torch
from torch import Tensor

from .foundation_contract import (
    EPOCHS_PER_UPDATE,
    MINIBATCHES_PER_EPOCH,
    STEPS_PER_UPDATE,
    UPDATE_COUNT,
)


GAMMA = 0.996
GAE_LAMBDA = 0.94
ADVANTAGE_EPSILON = 1e-8
PPO_CLIP_LOW = 0.82
PPO_CLIP_HIGH = 1.18
VALUE_COEFFICIENT = 0.55
ENTROPY_COEFFICIENT = 0.012
GLOBAL_GRADIENT_NORM = 0.9
ADAMW_LEARNING_RATE = 2.5e-4
ADAMW_BETAS = (0.9, 0.999)
ADAMW_EPSILON = 1e-8
ADAMW_WEIGHT_DECAY = 2e-5


@dataclass(frozen=True)
class DurationCorrectBatch:
    discounted_rewards: Tensor
    raw_advantages: Tensor
    targets: Tensor
    normalized_advantages: Tensor
    old_values: Tensor
    old_log_prob: Tensor


@dataclass(frozen=True)
class PpoLosses:
    policy: Tensor
    value: Tensor
    entropy: Tensor
    total: Tensor


@dataclass(frozen=True)
class PersistentStepClock:
    completed_updates: int
    global_one_based_index: int

    @classmethod
    def initial(cls) -> "PersistentStepClock":
        return cls(completed_updates=0, global_one_based_index=0)

    def complete_update(self, *, epoch_minibatch_count: int) -> "PersistentStepClock":
        if self.completed_updates >= UPDATE_COUNT:
            raise ValueError("foundation budget is exactly 192 updates")
        expected = EPOCHS_PER_UPDATE * MINIBATCHES_PER_EPOCH
        if epoch_minibatch_count != expected or expected != STEPS_PER_UPDATE:
            raise ValueError("each update must contain exactly 16 persistent steps")
        return PersistentStepClock(
            completed_updates=self.completed_updates + 1,
            global_one_based_index=self.global_one_based_index + STEPS_PER_UPDATE,
        )


def fisher_yates_fixture(count: int, *, swap_indices: tuple[int, ...]) -> tuple[int, ...]:
    """Apply explicit nonrandom Fisher-Yates choices for technical fixtures."""

    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError("count must be a positive integer")
    if len(swap_indices) != count - 1:
        raise ValueError("swap fixture must contain count-1 choices")
    values = list(range(count))
    for choice, upper in zip(swap_indices, range(count - 1, 0, -1)):
        if isinstance(choice, bool) or not isinstance(choice, int) or not 0 <= choice <= upper:
            raise ValueError("Fisher-Yates choice is outside its inclusive bound")
        values[upper], values[choice] = values[choice], values[upper]
    return tuple(values)


def partition_permutation(permutation: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    """Split one complete permutation into four quotient/remainder minibatches."""

    count = len(permutation)
    if count < MINIBATCHES_PER_EPOCH or sorted(permutation) != list(range(count)):
        raise ValueError("permutation must cover every record once and form four batches")
    quotient, remainder = divmod(count, MINIBATCHES_PER_EPOCH)
    batches: list[tuple[int, ...]] = []
    offset = 0
    for index in range(MINIBATCHES_PER_EPOCH):
        size = quotient + (1 if index < remainder else 0)
        batches.append(permutation[offset : offset + size])
        offset += size
    return tuple(batches)


def build_adamw(parameters: Iterable[Tensor]) -> torch.optim.AdamW:
    tensors = tuple(parameters)
    if not tensors or any(parameter.dtype is not torch.float32 for parameter in tensors):
        raise ValueError("AdamW requires the complete nonempty float32 foundation")
    return torch.optim.AdamW(
        tensors,
        lr=ADAMW_LEARNING_RATE,
        betas=ADAMW_BETAS,
        eps=ADAMW_EPSILON,
        weight_decay=ADAMW_WEIGHT_DECAY,
    )


def clip_global_gradients(parameters: Iterable[Tensor]) -> Tensor:
    tensors = tuple(parameters)
    if not tensors or any(parameter.grad is None for parameter in tensors):
        raise ValueError("combined foundation gradients must all be present")
    return torch.nn.utils.clip_grad_norm_(tensors, max_norm=GLOBAL_GRADIENT_NORM)


def _require_float32_vector(value: Tensor, name: str, length: int | None = None) -> None:
    if value.dtype is not torch.float32 or value.ndim != 1:
        raise ValueError(f"{name} must be a float32 vector")
    if length is not None and value.numel() != length:
        raise ValueError(f"{name} length differs")


def duration_correct_batch(
    *,
    primitive_rewards: tuple[Tensor, ...],
    nonterminal: Tensor,
    old_values: Tensor,
    next_old_values: Tensor,
    old_log_prob: Tensor,
) -> DurationCorrectBatch:
    count = len(primitive_rewards)
    if count == 0:
        raise ValueError("duration batch cannot be empty")
    _require_float32_vector(old_values, "old_values", count)
    _require_float32_vector(next_old_values, "next_old_values", count)
    _require_float32_vector(old_log_prob, "old_log_prob", count)
    if nonterminal.dtype is not torch.bool or nonterminal.shape != (count,):
        raise ValueError("nonterminal must be a bool vector matching the batch")
    discounted: list[Tensor] = []
    durations: list[int] = []
    for rewards in primitive_rewards:
        _require_float32_vector(rewards, "primitive reward")
        if rewards.numel() == 0:
            raise ValueError("realized duration must be positive")
        durations.append(rewards.numel())
        powers = torch.arange(rewards.numel(), dtype=torch.float32, device=rewards.device)
        discounted.append(torch.sum(torch.pow(torch.tensor(GAMMA), powers) * rewards))
    discounted_rewards = torch.stack(discounted).detach()
    old_snapshot = old_values.detach().clone()
    next_snapshot = next_old_values.detach().clone()
    nonterminal_snapshot = nonterminal.detach().clone()
    raw = torch.empty(count, dtype=torch.float32)
    running = torch.tensor(0.0, dtype=torch.float32)
    for index in range(count - 1, -1, -1):
        duration = durations[index]
        continuation = nonterminal_snapshot[index].to(torch.float32)
        delta = (
            discounted_rewards[index]
            + continuation * (GAMMA**duration) * next_snapshot[index]
            - old_snapshot[index]
        )
        running = delta + continuation * ((GAMMA * GAE_LAMBDA) ** duration) * running
        raw[index] = running
    targets = (raw + old_snapshot).detach()
    raw = raw.detach()
    centered = raw - torch.mean(raw)
    population_std = torch.sqrt(torch.mean(centered * centered))
    normalized = (centered / (population_std + ADVANTAGE_EPSILON)).detach()
    return DurationCorrectBatch(
        discounted_rewards=discounted_rewards,
        raw_advantages=raw,
        targets=targets,
        normalized_advantages=normalized,
        old_values=old_snapshot,
        old_log_prob=old_log_prob.detach().clone(),
    )


def ppo_losses(
    *,
    new_log_prob: Tensor,
    old_log_prob: Tensor,
    normalized_advantage: Tensor,
    value: Tensor,
    target: Tensor,
    entropy: Tensor,
) -> PpoLosses:
    count = new_log_prob.numel()
    for name, item in (
        ("new_log_prob", new_log_prob),
        ("old_log_prob", old_log_prob),
        ("normalized_advantage", normalized_advantage),
        ("value", value),
        ("target", target),
        ("entropy", entropy),
    ):
        _require_float32_vector(item, name, count)
    old_snapshot = old_log_prob.detach()
    advantage_snapshot = normalized_advantage.detach()
    target_snapshot = target.detach()
    ratio = torch.exp(new_log_prob - old_snapshot)
    unclipped = ratio * advantage_snapshot
    clipped = torch.clamp(ratio, PPO_CLIP_LOW, PPO_CLIP_HIGH) * advantage_snapshot
    policy = -torch.mean(torch.minimum(unclipped, clipped))
    value_loss = 0.5 * torch.mean((value - target_snapshot) ** 2)
    entropy_loss = torch.mean(entropy)
    total = policy + VALUE_COEFFICIENT * value_loss - ENTROPY_COEFFICIENT * entropy_loss
    return PpoLosses(policy, value_loss, entropy_loss, total)
