"""Real float32 PPO/GAE/AdamW kernels for SCDMP MF-RS-MK.

The module is runner-free: it provides bounded training and checkpoint seams,
but cannot launch RUN-01 or create a result artifact.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Final, Mapping, Sequence

import torch
from torch import Tensor

from .contracts import (
    EPISODES_PER_UPDATE,
    FOUNDATION_UPDATES,
    GRAPHS,
    K_VALUES,
)
from .foundation import FoundationActorCritic
from .rng import CounterRNG


GAMMA: Final[float] = 0.995
GAE_LAMBDA: Final[float] = 0.93
POLICY_CLIP_LOW: Final[float] = 0.80
POLICY_CLIP_HIGH: Final[float] = 1.20
VALUE_COEFFICIENT: Final[float] = 0.50
ENTROPY_COEFFICIENT: Final[float] = 0.010
GLOBAL_GRADIENT_CLIP: Final[float] = 0.8
ADAMW_BETA1: Final[float] = 0.9
ADAMW_BETA2: Final[float] = 0.999
ADAMW_EPSILON: Final[float] = 1e-8
ADAMW_LR: Final[float] = 3e-4
ADAMW_WEIGHT_DECAY: Final[float] = 1e-5
EPOCHS_PER_UPDATE: Final[int] = 3
MINIBATCHES_PER_EPOCH: Final[int] = 4
OPTIMIZER_STEPS_PER_UPDATE: Final[int] = 12


class TrainingContractError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class EpisodeSlot:
    update: int
    episode: int
    graph: str
    k: int

    @property
    def cell_replicate(self) -> int:
        return self.episode // 4

    @property
    def paired_environment_address(self) -> tuple[int, int, int]:
        return (self.update, self.cell_replicate, self.k)

    def action_address(self, renewal: int) -> tuple[int, int, int]:
        if isinstance(renewal, bool) or not isinstance(renewal, int) or renewal < 0:
            raise TrainingContractError("renewal address must be nonnegative")
        return (self.update, self.episode, renewal)


def build_training_plan() -> tuple[EpisodeSlot, ...]:
    cells = (("HR", 7), ("RH", 7), ("HR", 13), ("RH", 13))
    return tuple(
        EpisodeSlot(update, episode, *cells[episode % len(cells)])
        for update in range(1, FOUNDATION_UPDATES + 1)
        for episode in range(EPISODES_PER_UPDATE)
    )


@dataclass(frozen=True, slots=True)
class GAETargets:
    discounted_rewards: Tensor
    deltas: Tensor
    raw_advantages: Tensor
    value_targets: Tensor
    normalized_advantages: Tensor


def _validated_offsets(offsets: Sequence[int], count: int) -> tuple[int, ...]:
    result = tuple(offsets)
    if (
        len(result) < 2
        or result[0] != 0
        or result[-1] != count
        or any(isinstance(item, bool) or not isinstance(item, int) for item in result)
        or any(left >= right for left, right in zip(result, result[1:]))
    ):
        raise TrainingContractError("episode offsets must strictly partition all renewal records")
    return result


def duration_correct_gae(
    primitive_rewards: Sequence[Sequence[float]],
    old_values: Tensor,
    nonterminal: Tensor,
    *,
    episode_offsets: Sequence[int],
) -> GAETargets:
    """Compute semi-Markov GAE using the actual primitive duration per renewal."""

    rewards_by_record = tuple(tuple(row) for row in primitive_rewards)
    count = len(rewards_by_record)
    if (
        count < 1
        or old_values.dtype != torch.float32
        or old_values.shape != (count,)
        or old_values.requires_grad
        or not bool(torch.isfinite(old_values).all())
    ):
        raise TrainingContractError("old values must be a detached finite float32 record vector")
    if nonterminal.dtype != torch.bool or nonterminal.shape != (count,):
        raise TrainingContractError("nonterminal mask must match renewal records")
    if any(
        not 1 <= len(row) <= max(K_VALUES)
        or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            for value in row
        )
        for row in rewards_by_record
    ):
        raise TrainingContractError("each renewal must contain one through thirteen finite rewards")
    offsets = _validated_offsets(episode_offsets, count)
    for start, end in zip(offsets[:-1], offsets[1:]):
        if bool(nonterminal[end - 1]) or any(
            not bool(nonterminal[index]) for index in range(start, end - 1)
        ):
            raise TrainingContractError("only each complete episode's final renewal may terminate")

    discounted = torch.empty(count, dtype=torch.float32)
    deltas = torch.empty(count, dtype=torch.float32)
    advantages = torch.empty(count, dtype=torch.float32)
    gamma = torch.tensor(GAMMA, dtype=torch.float32)
    for start, end in zip(offsets[:-1], offsets[1:]):
        next_advantage = torch.tensor(0.0, dtype=torch.float32)
        for index in range(end - 1, start - 1, -1):
            row = torch.tensor(rewards_by_record[index], dtype=torch.float32)
            duration = len(rewards_by_record[index])
            discounted[index] = torch.sum(
                torch.pow(gamma, torch.arange(duration, dtype=torch.float32)) * row
            )
            next_value = old_values[index + 1] if index + 1 < end else torch.tensor(0.0)
            keep = nonterminal[index].to(torch.float32)
            deltas[index] = (
                discounted[index]
                + keep * (GAMMA**duration) * next_value
                - old_values[index]
            )
            advantages[index] = (
                deltas[index]
                + keep * ((GAMMA * GAE_LAMBDA) ** duration) * next_advantage
            )
            next_advantage = advantages[index]
    value_targets = (advantages + old_values).detach()
    centered = advantages - advantages.mean()
    normalized = (centered / torch.sqrt(torch.mean(centered.square()) + 1e-8)).detach()
    return GAETargets(
        discounted.detach(),
        deltas.detach(),
        advantages.detach(),
        value_targets,
        normalized,
    )


@dataclass(frozen=True, slots=True)
class RolloutBatch:
    observations: Tensor
    actions: Tensor
    old_log_probabilities: Tensor
    old_values: Tensor
    primitive_rewards: tuple[tuple[float, ...], ...]
    nonterminal: Tensor
    episode_offsets: tuple[int, ...]
    episode_slots: tuple[EpisodeSlot, ...]

    def validate(self) -> None:
        count = self.observations.shape[0] if self.observations.ndim == 2 else -1
        if (
            self.observations.dtype != torch.float32
            or self.observations.shape != (count, 18)
            or count < 4
            or not bool(torch.isfinite(self.observations).all())
        ):
            raise TrainingContractError("rollout observations must be finite float32 [records,18]")
        if (
            self.actions.dtype != torch.int64
            or self.actions.shape != (count,)
            or bool(torch.any(self.actions < 0))
            or bool(torch.any(self.actions >= 18))
        ):
            raise TrainingContractError("rollout actions must be int64 catalogue indices")
        for name, value in (
            ("old log probabilities", self.old_log_probabilities),
            ("old values", self.old_values),
        ):
            if (
                value.dtype != torch.float32
                or value.shape != (count,)
                or value.requires_grad
                or not bool(torch.isfinite(value).all())
            ):
                raise TrainingContractError(f"{name} must be a detached finite float32 vector")
        if len(self.primitive_rewards) != count or self.nonterminal.shape != (count,):
            raise TrainingContractError("rollout reward/mask record count differs")
        _validated_offsets(self.episode_offsets, count)
        if len(self.episode_slots) != EPISODES_PER_UPDATE or any(
            not isinstance(row, EpisodeSlot) for row in self.episode_slots
        ):
            raise TrainingContractError("rollout requires twelve typed graph-by-k episode slots")


@dataclass(frozen=True, slots=True)
class UpdateReceipt:
    update: int
    episodes_complete: int
    records: int
    transitions: int
    optimizer_step: int
    mean_loss: float


def _split_four(permutation: Sequence[int]) -> tuple[tuple[int, ...], ...]:
    values = tuple(permutation)
    if len(values) < 4 or tuple(sorted(values)) != tuple(range(len(values))):
        raise TrainingContractError("minibatching requires one full permutation")
    quotient, remainder = divmod(len(values), 4)
    result = []
    start = 0
    for index in range(4):
        size = quotient + int(index < remainder)
        result.append(values[start : start + size])
        start += size
    return tuple(result)


def _epoch_minibatches(source: CounterRNG, *, update: int, count: int):
    return tuple(
        _split_four(
            source.permutation(
                count,
                domain="foundation-minibatch",
                address=(update, epoch),
            )
        )
        for epoch in range(EPOCHS_PER_UPDATE)
    )


class _StrictClip(torch.autograd.Function):
    @staticmethod
    def forward(ctx, value: Tensor, lower: float, upper: float) -> Tensor:
        ctx.save_for_backward(value)
        ctx.lower = lower
        ctx.upper = upper
        return torch.clamp(value, lower, upper)

    @staticmethod
    def backward(ctx, gradient: Tensor):
        (value,) = ctx.saved_tensors
        mask = ((value > ctx.lower) & (value < ctx.upper)).to(gradient.dtype)
        return gradient * mask, None, None


def _mean_min(left: Tensor, right: Tensor) -> Tensor:
    return torch.where(
        left < right,
        left,
        torch.where(right < left, right, 0.5 * (left + right)),
    )


def joint_ppo_loss(
    *,
    current_log_probability: Tensor,
    current_value: Tensor,
    current_entropy: Tensor,
    old_log_probability: Tensor,
    value_target: Tensor,
    normalized_advantage: Tensor,
) -> Tensor:
    rows = (
        current_log_probability,
        current_value,
        current_entropy,
        old_log_probability,
        value_target,
        normalized_advantage,
    )
    if (
        current_log_probability.ndim != 1
        or current_log_probability.numel() == 0
        or len({tuple(row.shape) for row in rows}) != 1
        or any(row.dtype != torch.float32 or not bool(torch.isfinite(row).all()) for row in rows)
        or any(row.requires_grad for row in (old_log_probability, value_target, normalized_advantage))
    ):
        raise TrainingContractError("PPO terms must share one finite float32 vector shape")
    ratio = torch.exp(current_log_probability - old_log_probability)
    unclipped = ratio * normalized_advantage
    clipped = _StrictClip.apply(ratio, POLICY_CLIP_LOW, POLICY_CLIP_HIGH) * normalized_advantage
    policy = -_mean_min(unclipped, clipped).mean()
    value = 0.5 * torch.mean((current_value - value_target).square())
    entropy = current_entropy.mean()
    return policy + VALUE_COEFFICIENT * value - ENTROPY_COEFFICIENT * entropy


def clip_global_gradient(parameters: Sequence[Tensor]) -> tuple[float, float]:
    rows = tuple(parameters)
    gradients = tuple(parameter.grad for parameter in rows)
    if not rows or any(gradient is None for gradient in gradients):
        raise TrainingContractError("every foundation parameter requires a gradient")
    typed = tuple(gradient for gradient in gradients if gradient is not None)
    if any(not bool(torch.isfinite(gradient).all()) for gradient in typed):
        raise TrainingContractError("foundation gradient is nonfinite")
    norm_tensor = torch.sqrt(sum(torch.sum(gradient.square()) for gradient in typed))
    norm = float(norm_tensor)
    if not math.isfinite(norm):
        raise TrainingContractError("combined gradient norm is nonfinite")
    scale = 1.0 if norm <= GLOBAL_GRADIENT_CLIP else GLOBAL_GRADIENT_CLIP / norm
    if scale != 1.0:
        for gradient in typed:
            gradient.mul_(scale)
    return norm, scale


@dataclass(frozen=True, slots=True)
class OptimizerSnapshot:
    step: int
    names: tuple[str, ...]
    first: tuple[Tensor, ...]
    second: tuple[Tensor, ...]


class ExactAdamW:
    """Float32 AdamW with direct, independently cloneable optimizer state."""

    def __init__(self, named_parameters: Sequence[tuple[str, Tensor]]) -> None:
        self._rows = tuple(named_parameters)
        names = tuple(name for name, _ in self._rows)
        parameters = tuple(parameter for _, parameter in self._rows)
        if (
            not self._rows
            or len(set(names)) != len(names)
            or len({id(parameter) for parameter in parameters}) != len(parameters)
            or any(
                not name
                or parameter.dtype != torch.float32
                or not parameter.requires_grad
                or not bool(torch.isfinite(parameter).all())
                for name, parameter in self._rows
            )
        ):
            raise TrainingContractError("AdamW requires unique named float32 parameters")
        self.first = [torch.zeros_like(parameter) for parameter in parameters]
        self.second = [torch.zeros_like(parameter) for parameter in parameters]
        self.step_index = 0

    @property
    def parameters(self) -> tuple[Tensor, ...]:
        return tuple(parameter for _, parameter in self._rows)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(name for name, _ in self._rows)

    def matches(self, named_parameters: Sequence[tuple[str, Tensor]]) -> bool:
        rows = tuple(named_parameters)
        return (
            tuple(name for name, _ in rows) == self.names
            and tuple(id(parameter) for _, parameter in rows)
            == tuple(id(parameter) for parameter in self.parameters)
        )

    @torch.no_grad()
    def step(self) -> None:
        if self.step_index >= 1_920:
            raise TrainingContractError("AdamW exceeds the per-foundation 1,920-step budget")
        gradients = tuple(parameter.grad for parameter in self.parameters)
        if any(gradient is None or not bool(torch.isfinite(gradient).all()) for gradient in gradients):
            raise TrainingContractError("AdamW gradient is absent or nonfinite")
        next_step = self.step_index + 1
        candidates = []
        for parameter, first, second, gradient in zip(
            self.parameters, self.first, self.second, gradients
        ):
            assert gradient is not None
            next_first = first.detach().clone()
            next_first.mul_(ADAMW_BETA1).add_(gradient, alpha=1.0 - ADAMW_BETA1)
            next_second = second.detach().clone()
            next_second.mul_(ADAMW_BETA2).addcmul_(
                gradient, gradient, value=1.0 - ADAMW_BETA2
            )
            first_hat = next_first / (1.0 - ADAMW_BETA1**next_step)
            second_hat = next_second / (1.0 - ADAMW_BETA2**next_step)
            next_parameter = parameter.detach().clone() - ADAMW_LR * (
                first_hat / (torch.sqrt(second_hat) + ADAMW_EPSILON)
                + ADAMW_WEIGHT_DECAY * parameter.detach()
            )
            if not all(bool(torch.isfinite(value).all()) for value in (next_first, next_second, next_parameter)):
                raise TrainingContractError("AdamW candidate state is nonfinite")
            candidates.append((next_first, next_second, next_parameter))
        for first, second, parameter, (new_first, new_second, new_parameter) in zip(
            self.first, self.second, self.parameters, candidates
        ):
            first.copy_(new_first)
            second.copy_(new_second)
            parameter.copy_(new_parameter)
        self.step_index = next_step

    def snapshot(self) -> OptimizerSnapshot:
        return OptimizerSnapshot(
            self.step_index,
            self.names,
            tuple(value.detach().clone() for value in self.first),
            tuple(value.detach().clone() for value in self.second),
        )

    def restore(self, snapshot: OptimizerSnapshot) -> None:
        if (
            not isinstance(snapshot, OptimizerSnapshot)
            or snapshot.names != self.names
            or isinstance(snapshot.step, bool)
            or not isinstance(snapshot.step, int)
            or not 0 <= snapshot.step <= 1_920
            or len(snapshot.first) != len(self.first)
            or len(snapshot.second) != len(self.second)
        ):
            raise TrainingContractError("optimizer snapshot structure differs")
        for source, target in zip(snapshot.first, self.first):
            if source.dtype != torch.float32 or source.shape != target.shape or not bool(torch.isfinite(source).all()):
                raise TrainingContractError("optimizer first moment differs")
        for source, target in zip(snapshot.second, self.second):
            if (
                source.dtype != torch.float32
                or source.shape != target.shape
                or not bool(torch.isfinite(source).all())
                or bool(torch.any(source < 0))
            ):
                raise TrainingContractError("optimizer second moment differs")
        with torch.no_grad():
            for source, target in zip(snapshot.first, self.first):
                target.copy_(source)
            for source, target in zip(snapshot.second, self.second):
                target.copy_(source)
        self.step_index = snapshot.step


@dataclass(frozen=True, slots=True)
class NamedTensor:
    name: str
    tensor: Tensor


@dataclass(frozen=True, slots=True)
class FoundationCheckpoint:
    seed: int
    update: int
    optimizer_step: int
    parameters: tuple[NamedTensor, ...]
    optimizer: OptimizerSnapshot


def make_final_checkpoint(
    model: FoundationActorCritic,
    optimizer: ExactAdamW,
    *,
    update: int,
) -> FoundationCheckpoint:
    if not isinstance(model, FoundationActorCritic) or not isinstance(optimizer, ExactAdamW):
        raise TypeError("final checkpoint requires the MF-RS-MK foundation and AdamW")
    if update != FOUNDATION_UPDATES:
        raise TrainingContractError("the only assay checkpoint is update 160 for a prescribed seed")
    if not optimizer.matches(tuple(model.named_parameters())) or optimizer.step_index != 1_920:
        raise TrainingContractError("checkpoint requires the same model's 1,920-step optimizer frontier")
    parameters = tuple(
        NamedTensor(name, parameter.detach().clone())
        for name, parameter in model.named_parameters()
    )
    snapshot = optimizer.snapshot()
    return FoundationCheckpoint(model.foundation_seed, update, snapshot.step, parameters, snapshot)


def _validate_checkpoint(
    model: FoundationActorCritic,
    optimizer: ExactAdamW,
    checkpoint: FoundationCheckpoint,
    *,
    expected_seed: int,
) -> None:
    from .contracts import TRAINING_SEEDS

    if (
        not isinstance(checkpoint, FoundationCheckpoint)
        or expected_seed not in TRAINING_SEEDS
        or checkpoint.seed != expected_seed
        or checkpoint.update != FOUNDATION_UPDATES
        or checkpoint.optimizer_step != 1_920
        or checkpoint.optimizer.step != checkpoint.optimizer_step
        or not optimizer.matches(tuple(model.named_parameters()))
    ):
        raise TrainingContractError("checkpoint frontier, seed, or target binding differs")
    targets = tuple(model.named_parameters())
    if tuple(row.name for row in checkpoint.parameters) != tuple(name for name, _ in targets):
        raise TrainingContractError("checkpoint parameter names differ")
    tensors = tuple(row.tensor for row in checkpoint.parameters)
    if len({id(tensor) for tensor in tensors}) != len(tensors):
        raise TrainingContractError("checkpoint parameters must be independent direct tensors")
    for source, (_, target) in zip(tensors, targets):
        if (
            not isinstance(source, Tensor)
            or source.dtype != torch.float32
            or source.shape != target.shape
            or not bool(torch.isfinite(source).all())
        ):
            raise TrainingContractError("checkpoint parameter tensor differs")
    # Optimizer restore performs complete moment validation without mutation.
    temporary = ExactAdamW(targets)
    temporary.restore(checkpoint.optimizer)


def restore_final_checkpoint(
    model: FoundationActorCritic,
    optimizer: ExactAdamW,
    checkpoint: FoundationCheckpoint,
    *,
    expected_seed: int,
) -> None:
    if not isinstance(model, FoundationActorCritic) or not isinstance(optimizer, ExactAdamW):
        raise TypeError("checkpoint restore requires the MF-RS-MK foundation and AdamW")
    _validate_checkpoint(model, optimizer, checkpoint, expected_seed=expected_seed)
    with torch.no_grad():
        for source, (_, target) in zip(checkpoint.parameters, model.named_parameters()):
            target.copy_(source.tensor)
    optimizer.restore(checkpoint.optimizer)
    model.foundation_seed = checkpoint.seed


def train_one_update(
    model: FoundationActorCritic,
    optimizer: ExactAdamW,
    source: CounterRNG,
    rollout: RolloutBatch,
    *,
    update: int,
) -> UpdateReceipt:
    if not isinstance(model, FoundationActorCritic) or not isinstance(optimizer, ExactAdamW):
        raise TypeError("MF-RS-MK training requires its foundation and AdamW")
    if not isinstance(source, CounterRNG):
        raise TypeError("training requires the seed-bound counter RNG")
    if source.seed != model.foundation_seed:
        raise TrainingContractError("model and optimizer must remain seed-bound to the RNG root")
    if isinstance(update, bool) or not isinstance(update, int) or not 1 <= update <= FOUNDATION_UPDATES:
        raise TrainingContractError("training update lies outside [1,160]")
    if not optimizer.matches(tuple(model.named_parameters())):
        raise TrainingContractError("optimizer is not bound to this foundation schema")
    if optimizer.step_index != (update - 1) * OPTIMIZER_STEPS_PER_UPDATE:
        raise TrainingContractError("optimizer does not match the requested update frontier")
    rollout.validate()
    expected_slots = build_training_plan()[
        (update - 1) * EPISODES_PER_UPDATE : update * EPISODES_PER_UPDATE
    ]
    if rollout.episode_slots != expected_slots:
        raise TrainingContractError("rollout graph-by-k slots differ from the update plan")
    if len(rollout.episode_offsets) - 1 != EPISODES_PER_UPDATE:
        raise TrainingContractError("each update requires twelve complete episodes")
    targets = duration_correct_gae(
        rollout.primitive_rewards,
        rollout.old_values,
        rollout.nonterminal,
        episode_offsets=rollout.episode_offsets,
    )
    losses = []
    for epoch in _epoch_minibatches(source, update=update, count=len(rollout.actions)):
        for minibatch in epoch:
            index = torch.tensor(minibatch, dtype=torch.int64)
            for parameter in optimizer.parameters:
                parameter.grad = None
            output = model(rollout.observations[index])
            log_probabilities = torch.log_softmax(output.logits, dim=1)
            probabilities = torch.softmax(output.logits, dim=1)
            current_log_probability = log_probabilities.gather(
                1, rollout.actions[index].unsqueeze(1)
            ).squeeze(1)
            entropy = -torch.sum(probabilities * log_probabilities, dim=1)
            loss = joint_ppo_loss(
                current_log_probability=current_log_probability,
                current_value=output.value,
                current_entropy=entropy,
                old_log_probability=rollout.old_log_probabilities[index],
                value_target=targets.value_targets[index],
                normalized_advantage=targets.normalized_advantages[index],
            )
            loss.backward()
            clip_global_gradient(optimizer.parameters)
            optimizer.step()
            losses.append(float(loss.detach()))
    expected_step = update * OPTIMIZER_STEPS_PER_UPDATE
    if optimizer.step_index != expected_step:
        raise TrainingContractError("optimizer did not reach the exact update frontier")
    return UpdateReceipt(
        update=update,
        episodes_complete=EPISODES_PER_UPDATE,
        records=len(rollout.actions),
        transitions=sum(len(row) for row in rollout.primitive_rewards),
        optimizer_step=optimizer.step_index,
        mean_loss=math.fsum(losses) / len(losses),
    )


_PLAN = build_training_plan()
if len(_PLAN) != 1_920:
    raise RuntimeError("foundation training plan size drifted")
for _update in range(1, FOUNDATION_UPDATES + 1):
    _rows = _PLAN[(_update - 1) * EPISODES_PER_UPDATE : _update * EPISODES_PER_UPDATE]
    if any(sum(row.graph == graph and row.k == k for row in _rows) != 3 for graph in GRAPHS for k in K_VALUES):
        raise RuntimeError("foundation graph-by-k training balance drifted")


__all__ = [
    "ADAMW_BETA1", "ADAMW_BETA2", "ADAMW_EPSILON", "ADAMW_LR",
    "ADAMW_WEIGHT_DECAY", "ENTROPY_COEFFICIENT", "EPOCHS_PER_UPDATE", "EpisodeSlot",
    "GAETargets", "GAE_LAMBDA", "GAMMA", "GLOBAL_GRADIENT_CLIP",
    "ExactAdamW", "FoundationCheckpoint", "MINIBATCHES_PER_EPOCH", "NamedTensor",
    "OPTIMIZER_STEPS_PER_UPDATE", "OptimizerSnapshot", "POLICY_CLIP_HIGH",
    "POLICY_CLIP_LOW", "TrainingContractError", "VALUE_COEFFICIENT",
    "RolloutBatch", "UpdateReceipt", "build_training_plan", "clip_global_gradient",
    "duration_correct_gae", "joint_ppo_loss", "make_final_checkpoint",
    "restore_final_checkpoint", "train_one_update",
]
