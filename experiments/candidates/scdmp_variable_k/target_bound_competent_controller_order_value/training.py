"""Duration-correct PPO services for SCDMP TBCC revision 02.

The services consume only caller-supplied action variates, epoch permutations,
permits, rollout records, and in-memory state payloads.  They do not create a
random master, empirical identity, coordinate, episode, file, or result.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Final, Mapping, Protocol, Sequence, runtime_checkable

import torch
from torch import Tensor

from .contracts import ppo_tie_mean_min, strict_clip
from .model import (
    CARD_REVISION,
    FoundationActorCritic,
    LearnedOrderArm,
    OrderActorCritic,
    categorical_entropy,
    categorical_log_prob,
)


GAMMA: Final[float] = 0.995
GAE_LAMBDA: Final[float] = 0.93
ADVANTAGE_EPSILON: Final[float] = 1e-8
POLICY_CLIP_LOW: Final[float] = 0.80
POLICY_CLIP_HIGH: Final[float] = 1.20
VALUE_COEFFICIENT: Final[float] = 0.50
ENTROPY_COEFFICIENT: Final[float] = 0.010
GLOBAL_GRADIENT_CLIP: Final[float] = 0.8
EPOCHS_PER_UPDATE: Final[int] = 3
MINIBATCHES_PER_EPOCH: Final[int] = 4
OPTIMIZER_STEPS_PER_UPDATE: Final[int] = 12
FOUNDATION_UPDATES: Final[int] = 160
ORDER_UPDATES: Final[int] = 96
EPISODES_PER_UPDATE: Final[int] = 12
CHECKPOINT_SCHEMA: Final[str] = "SCDMP-TBCC-R02-IN-MEMORY-CHECKPOINT-V1"

ADAMW_BETA1: Final[float] = 0.9
ADAMW_BETA2: Final[float] = 0.999
ADAMW_EPSILON: Final[float] = 1e-8
ADAMW_LR: Final[float] = 3e-4
ADAMW_WEIGHT_DECAY: Final[float] = 1e-5


class TrainingContractError(ValueError):
    """A training service input differs from the frozen revision."""


@dataclass(frozen=True)
class EpisodeSlot:
    index: int
    k: int
    q: int


@dataclass(frozen=True)
class GAETargets:
    discounted_rewards: Tensor
    deltas: Tensor
    raw_advantages: Tensor
    value_targets: Tensor
    normalized_advantages: Tensor


@dataclass(frozen=True)
class EpochMinibatches:
    epoch: int
    permutation: tuple[int, ...]
    minibatches: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class JointLoss:
    total: Tensor
    policy: Tensor
    value: Tensor
    entropy: Tensor


@dataclass(frozen=True)
class FrozenParameterSnapshot:
    names: tuple[str, ...]
    values: tuple[Tensor, ...]
    digest: str

    @classmethod
    def from_model(cls, model: FoundationActorCritic | OrderActorCritic) -> "FrozenParameterSnapshot":
        rows = tuple((name, parameter.detach().clone()) for name, parameter in _trainable_named_parameters(model))
        names = tuple(name for name, _ in rows)
        values = tuple(value for _, value in rows)
        return cls(names, values, _named_tensor_digest(names, values))

    def validate_immutable(self) -> None:
        if _named_tensor_digest(self.names, self.values) != self.digest:
            raise RuntimeError("frozen old-parameter snapshot changed")

    def require_exact_current_model(self, model: FoundationActorCritic | OrderActorCritic) -> None:
        rows = _trainable_named_parameters(model)
        names = tuple(name for name, _ in rows)
        if names != self.names:
            raise RuntimeError("old-parameter names do not match the live model")
        current = tuple(parameter.detach() for _, parameter in rows)
        if _named_tensor_digest(names, current) != self.digest:
            raise RuntimeError("old parameters are stale or cross-wired")


@dataclass(frozen=True)
class FrozenUpdateBatch:
    arm: str
    replicate: int
    update: int
    schedule: tuple[EpisodeSlot, ...]
    episode_offsets: tuple[int, ...]
    observation: Tensor
    physical_q: Tensor | None
    announced_k: Tensor
    actions: Tensor
    primitive_rewards: tuple[tuple[float, ...], ...]
    nonterminal: Tensor
    old_log_probability: Tensor
    old_value: Tensor
    targets: GAETargets
    old_parameters: FrozenParameterSnapshot
    content_digest: str

    @property
    def record_count(self) -> int:
        return int(self.observation.shape[0])

    def validate_registered(self) -> None:
        _validate_kind(self.arm)
        _validate_replicate(self.replicate)
        limit = _update_limit(self.arm)
        if isinstance(self.update, bool) or not 1 <= self.update <= limit:
            raise TrainingContractError("PPO update is outside the exact arm budget")
        if self.schedule != registered_episode_schedule(self.arm):
            raise TrainingContractError("update episode schedule differs from revision 02")
        count = self.record_count
        if count < 4 or self.observation.dtype != torch.float32 or self.observation.shape != (count, 18):
            raise TrainingContractError("update requires at least four finite float32 [N,18] records")
        if not bool(torch.isfinite(self.observation).all()):
            raise TrainingContractError("update observations must be finite")
        if self.actions.dtype != torch.int64 or self.actions.shape != (count,):
            raise TrainingContractError("actions must be int64 [N]")
        if bool(torch.any((self.actions < 0) | (self.actions >= 18))):
            raise TrainingContractError("actions must index the lexicographic 18-action table")
        if self.announced_k.dtype not in (torch.int32, torch.int64) or self.announced_k.shape != (count,):
            raise TrainingContractError("announced k must be an integer [N] tensor")
        if self.nonterminal.dtype != torch.bool or self.nonterminal.shape != (count,):
            raise TrainingContractError("nonterminal must be bool [N]")
        _validate_episode_offsets(self.episode_offsets, count)
        for slot, start, stop in zip(self.schedule, self.episode_offsets[:-1], self.episode_offsets[1:]):
            if not bool(torch.all(self.announced_k[start:stop] == slot.k)):
                raise TrainingContractError("renewal k differs from its registered episode slot")
            if bool(self.nonterminal[stop - 1]):
                raise TrainingContractError("every allocated training episode must be complete")
            if self.arm == "FOUNDATION":
                if self.physical_q is not None:
                    raise TrainingContractError("foundation training batch must not expose q")
            else:
                if self.physical_q is None or self.physical_q.dtype != torch.float32 or self.physical_q.shape != (count,):
                    raise TrainingContractError("order-stage q must be float32 [N]")
                if not bool(torch.all(self.physical_q[start:stop] == float(slot.q))):
                    raise TrainingContractError("order-stage q differs from its registered episode slot")
        if len(self.primitive_rewards) != count or any(not row for row in self.primitive_rewards):
            raise TrainingContractError("every renewal requires a positive-duration primitive reward row")
        for tensor in (self.old_log_probability, self.old_value):
            if tensor.dtype != torch.float32 or tensor.shape != (count,) or not bool(torch.isfinite(tensor).all()):
                raise TrainingContractError("old policy/value tensors must be finite float32 [N]")
            if tensor.requires_grad:
                raise TrainingContractError("old policy/value tensors must be detached")
        for tensor in self.targets.__dict__.values():
            if tensor.dtype != torch.float32 or tensor.shape != (count,) or tensor.requires_grad:
                raise TrainingContractError("duration targets must be detached float32 [N]")
        self.old_parameters.validate_immutable()
        if _batch_digest(self) != self.content_digest:
            raise RuntimeError("frozen update batch changed")


@dataclass(frozen=True)
class MinibatchStepReceipt:
    optimizer_step: int
    update: int
    epoch: int
    minibatch: int
    record_count: int
    total_loss: float
    policy_loss: float
    value_loss: float
    entropy: float
    gradient_norm_before_clip: float
    gradient_scale: float


@dataclass(frozen=True)
class TrainingUpdateReceipt:
    arm: str
    replicate: int
    update: int
    optimizer_step: int
    schedule_digest: str
    batch_digest: str
    steps: tuple[MinibatchStepReceipt, ...]
    complete_checkpoint_eligible: bool


@dataclass(frozen=True)
class CheckpointValidationReceipt:
    schema: str
    arm: str
    replicate: int
    completed_updates: int
    optimizer_step: int
    parameter_digest: str
    optimizer_digest: str
    frozen_foundation_digest: str | None
    final_checkpoint: bool


@runtime_checkable
class ActionUniformSource(Protocol):
    """Caller-owned one-fresh-address action variate service."""

    def action_uniform(
        self,
        *,
        replicate: int,
        domain: str,
        update: int,
        episode_slot: int,
        renewal: int,
    ) -> float:
        """Return one address-stable U[0,1) variate."""


@runtime_checkable
class MinibatchPermutationSource(Protocol):
    def permutation_indices(
        self,
        *,
        replicate: int,
        arm: str,
        update: int,
        epoch: int,
        count: int,
    ) -> Sequence[int]:
        """Return one fresh full Fisher-Yates permutation for epoch 0, 1, or 2."""


@runtime_checkable
class TrainingActivityPermit(Protocol):
    """Future-runner authority interface; this module issues no permit."""

    def require_training_update(
        self,
        *,
        card_revision: str,
        replicate: int,
        arm: str,
        update: int,
        schedule: tuple[EpisodeSlot, ...],
    ) -> None:
        """Raise unless this exact training update is authorized."""

    def require_checkpoint_restore(
        self,
        *,
        card_revision: str,
        replicate: int,
        arm: str,
        completed_updates: int,
    ) -> None:
        """Raise unless restoring this already-bound in-memory frontier is authorized."""


def registered_episode_schedule(arm: str | LearnedOrderArm) -> tuple[EpisodeSlot, ...]:
    """Exact 12-slot k-major, graph-major address inventory for one update."""

    name = arm.value if isinstance(arm, LearnedOrderArm) else str(arm)
    _validate_kind(name)
    return tuple(
        EpisodeSlot(index, k, q)
        for index, (k, q) in enumerate(
            ((k, q) for k in (5, 11) for q in (0, 1) for _ in range(3))
        )
    )


def training_contract() -> dict[str, object]:
    return {
        "foundation_updates": FOUNDATION_UPDATES,
        "order_updates": ORDER_UPDATES,
        "episodes_per_update": EPISODES_PER_UPDATE,
        "schedule": tuple((slot.k, slot.q) for slot in registered_episode_schedule("FOUNDATION")),
        "gamma": GAMMA,
        "gae_lambda": GAE_LAMBDA,
        "policy_clip": (POLICY_CLIP_LOW, POLICY_CLIP_HIGH),
        "epochs_per_update": EPOCHS_PER_UPDATE,
        "minibatches_per_epoch": MINIBATCHES_PER_EPOCH,
        "optimizer_steps_per_update": OPTIMIZER_STEPS_PER_UPDATE,
        "optimizer_steps": {"FOUNDATION": 1_920, "TREAT": 1_152, "FREE": 1_152, "SET": 1_152},
        "optimizer": {
            "name": "one_persistent_all_trainable_parameter_AdamW",
            "lr": ADAMW_LR,
            "betas": (ADAMW_BETA1, ADAMW_BETA2),
            "epsilon": ADAMW_EPSILON,
            "weight_decay": ADAMW_WEIGHT_DECAY,
            "global_clip": GLOBAL_GRADIENT_CLIP,
            "decay_applies_to": "all_trainable_matrices_and_biases",
        },
        "shared_parameterization_across_k": True,
        "per_k_heads_updates_or_checkpoints": 0,
        "forbidden": (
            "early_stop",
            "learning_rate_schedule",
            "target_tuning",
            "checkpoint_selection",
            "auxiliary_loss",
            "reward_normalization",
            "running_observation_statistics",
        ),
    }


def _validate_kind(arm: str) -> None:
    if arm not in ("FOUNDATION", "TREAT", "FREE", "SET"):
        raise TrainingContractError("arm must be FOUNDATION, TREAT, FREE, or SET")


def _validate_replicate(replicate: int) -> None:
    if isinstance(replicate, bool) or not isinstance(replicate, int) or not 0 <= replicate < 24:
        raise TrainingContractError("replicate must be an integer in [0,24)")


def _update_limit(arm: str) -> int:
    return FOUNDATION_UPDATES if arm == "FOUNDATION" else ORDER_UPDATES


def _trainable_named_parameters(
    model: FoundationActorCritic | OrderActorCritic,
) -> tuple[tuple[str, Tensor], ...]:
    return tuple((name, parameter) for name, parameter in model.named_parameters() if parameter.requires_grad)


def _named_tensor_digest(names: Sequence[str], tensors: Sequence[Tensor]) -> str:
    digest = hashlib.sha256()
    if len(names) != len(tensors):
        raise RuntimeError("named tensor digest inputs differ")
    for name, value in zip(names, tensors):
        tensor = value.detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(str(tuple(tensor.shape)).encode("ascii"))
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def _schedule_digest(schedule: Sequence[EpisodeSlot]) -> str:
    payload = "|".join(f"{row.index}:{row.k}:{row.q}" for row in schedule)
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def _validate_episode_offsets(offsets: Sequence[int], count: int) -> tuple[int, ...]:
    values = tuple(offsets)
    if len(values) != EPISODES_PER_UPDATE + 1 or values[0] != 0 or values[-1] != count:
        raise TrainingContractError("episode offsets must delimit exactly 12 complete episodes")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in values):
        raise TrainingContractError("episode offsets must be integers")
    if any(left >= right for left, right in zip(values, values[1:])):
        raise TrainingContractError("each of the 12 episode spans must be nonempty")
    return values


def normalize_population_advantage(raw: Tensor) -> Tensor:
    if raw.dtype != torch.float32 or raw.ndim != 1 or raw.numel() < 1 or not bool(torch.isfinite(raw).all()):
        raise TrainingContractError("raw advantages must be a nonempty finite float32 vector")
    centered = raw - raw.mean()
    return centered / torch.sqrt(torch.mean(centered.square()) + ADVANTAGE_EPSILON)


def duration_correct_gae(
    *,
    primitive_rewards: Sequence[Sequence[float]],
    old_values: Tensor,
    nonterminal: Tensor,
    episode_offsets: Sequence[int],
) -> GAETargets:
    count = len(primitive_rewards)
    offsets = _validate_episode_offsets(episode_offsets, count)
    if old_values.dtype != torch.float32 or old_values.shape != (count,) or not bool(torch.isfinite(old_values).all()):
        raise TrainingContractError("old values must be finite float32 [N]")
    if nonterminal.dtype != torch.bool or nonterminal.shape != (count,):
        raise TrainingContractError("nonterminal must be bool [N]")
    if any(not row for row in primitive_rewards):
        raise TrainingContractError("every renewal duration must be positive")
    rewards = torch.empty(count, dtype=torch.float32)
    deltas = torch.empty(count, dtype=torch.float32)
    raw = torch.empty(count, dtype=torch.float32)
    for start, stop in zip(offsets[:-1], offsets[1:]):
        if bool(nonterminal[stop - 1]):
            raise TrainingContractError("a complete episode must end with nonterminal false")
        next_advantage = torch.tensor(0.0, dtype=torch.float32)
        for index in range(stop - 1, start - 1, -1):
            row = torch.tensor(tuple(primitive_rewards[index]), dtype=torch.float32)
            if not bool(torch.isfinite(row).all()):
                raise TrainingContractError("primitive rewards must be finite")
            duration = int(row.numel())
            discounts = torch.pow(torch.tensor(GAMMA, dtype=torch.float32), torch.arange(duration, dtype=torch.float32))
            rewards[index] = torch.sum(discounts * row)
            continuation = nonterminal[index].to(torch.float32)
            next_value = old_values[index + 1] if index + 1 < stop else torch.tensor(0.0, dtype=torch.float32)
            deltas[index] = rewards[index] + continuation * (GAMMA**duration) * next_value - old_values[index]
            raw[index] = deltas[index] + continuation * ((GAMMA * GAE_LAMBDA) ** duration) * next_advantage
            next_advantage = raw[index]
    targets = raw + old_values
    normalized = normalize_population_advantage(raw)
    return GAETargets(*(value.detach() for value in (rewards, deltas, raw, targets, normalized)))


def sample_actions_from_source(
    logits: Tensor,
    *,
    source: ActionUniformSource,
    replicate: int,
    arm: str | LearnedOrderArm,
    update: int,
    episode_slot: int,
    renewal_indices: Sequence[int],
) -> Tensor:
    """Consume exactly one caller-owned variate per real policy query."""

    name = arm.value if isinstance(arm, LearnedOrderArm) else str(arm)
    _validate_kind(name)
    if not isinstance(source, ActionUniformSource):
        raise TypeError("categorical sampling requires an injected action-uniform source")
    if logits.dtype != torch.float32 or logits.ndim != 2 or logits.shape[1] != 18 or not bool(torch.isfinite(logits).all()):
        raise TrainingContractError("sampling logits must be finite float32 [N,18]")
    renewals = tuple(renewal_indices)
    if len(renewals) != logits.shape[0] or any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in renewals):
        raise TrainingContractError("one nonnegative renewal address is required per policy query")
    domain = "FOUNDATION" if name == "FOUNDATION" else "ORDER_SHARED"
    values = tuple(
        source.action_uniform(
            replicate=replicate,
            domain=domain,
            update=update,
            episode_slot=episode_slot,
            renewal=renewal,
        )
        for renewal in renewals
    )
    uniforms = torch.tensor(values, dtype=torch.float32, device=logits.device)
    if not bool(torch.isfinite(uniforms).all()) or not bool(torch.all((uniforms >= 0.0) & (uniforms < 1.0))):
        raise TrainingContractError("action uniforms must be finite and lie in [0,1)")
    probabilities = torch.softmax(logits, dim=-1)
    cumulative = probabilities.cumsum(dim=-1)
    eligible = cumulative > uniforms.unsqueeze(-1)
    if not bool(eligible.any(dim=-1).all()):
        raise TrainingContractError("categorical row has no strict-boundary inverse-CDF action")
    return eligible.to(torch.int64).argmax(dim=-1)


def split_four_near_equal(permutation: Sequence[int]) -> tuple[tuple[int, ...], ...]:
    values = tuple(permutation)
    count = len(values)
    if count < 4 or sorted(values) != list(range(count)):
        raise TrainingContractError("minibatching requires a full permutation of at least four record IDs")
    quotient, remainder = divmod(count, 4)
    sizes = tuple(quotient + int(index < remainder) for index in range(4))
    rows = []
    start = 0
    for size in sizes:
        rows.append(values[start : start + size])
        start += size
    return tuple(rows)


def registered_minibatch_plan(
    source: MinibatchPermutationSource,
    *,
    replicate: int,
    arm: str | LearnedOrderArm,
    update: int,
    count: int,
) -> tuple[EpochMinibatches, ...]:
    name = arm.value if isinstance(arm, LearnedOrderArm) else str(arm)
    _validate_kind(name)
    if not isinstance(source, MinibatchPermutationSource):
        raise TypeError("PPO requires an injected permutation source")
    plans = []
    for epoch in range(EPOCHS_PER_UPDATE):
        permutation = tuple(
            source.permutation_indices(
                replicate=replicate, arm=name, update=update, epoch=epoch, count=count
            )
        )
        if len(permutation) != count or sorted(permutation) != list(range(count)):
            raise TrainingContractError("epoch source returned a partial or duplicate permutation")
        plans.append(EpochMinibatches(epoch, permutation, split_four_near_equal(permutation)))
    if len({row.permutation for row in plans}) != EPOCHS_PER_UPDATE:
        raise TrainingContractError("the three epoch permutations must be distinct")
    return tuple(plans)


def _model_output(
    model: FoundationActorCritic | OrderActorCritic,
    observation: Tensor,
    physical_q: Tensor | None,
    announced_k: Tensor,
) -> tuple[Tensor, Tensor]:
    if isinstance(model, FoundationActorCritic):
        if physical_q is not None:
            raise TrainingContractError("foundation model must not receive q")
        output = model(observation)
    elif isinstance(model, OrderActorCritic):
        if physical_q is None:
            raise TrainingContractError("order-stage model requires physical q")
        output = model(observation, physical_q, announced_k)
    else:
        raise TypeError("unregistered controller model")
    return output.logits, output.value


def _batch_digest(batch: FrozenUpdateBatch) -> str:
    names = (
        "observation",
        "physical_q",
        "announced_k",
        "actions",
        "nonterminal",
        "old_log_probability",
        "old_value",
        "discounted_rewards",
        "deltas",
        "raw_advantages",
        "value_targets",
        "normalized_advantages",
    )
    tensors = (
        batch.observation,
        torch.empty(0, dtype=torch.float32) if batch.physical_q is None else batch.physical_q,
        batch.announced_k,
        batch.actions,
        batch.nonterminal,
        batch.old_log_probability,
        batch.old_value,
        batch.targets.discounted_rewards,
        batch.targets.deltas,
        batch.targets.raw_advantages,
        batch.targets.value_targets,
        batch.targets.normalized_advantages,
    )
    digest = hashlib.sha256(_named_tensor_digest(names, tensors).encode("ascii"))
    digest.update(str(batch.episode_offsets).encode("ascii"))
    digest.update(str(batch.primitive_rewards).encode("ascii"))
    digest.update(_schedule_digest(batch.schedule).encode("ascii"))
    digest.update(batch.old_parameters.digest.encode("ascii"))
    return digest.hexdigest()


def freeze_update_batch(
    model: FoundationActorCritic | OrderActorCritic,
    *,
    replicate: int,
    update: int,
    observation: Tensor,
    physical_q: Tensor | None,
    announced_k: Tensor,
    actions: Tensor,
    primitive_rewards: Sequence[Sequence[float]],
    nonterminal: Tensor,
    episode_offsets: Sequence[int],
) -> FrozenUpdateBatch:
    """Freeze old-policy quantities for one already-collected complete update."""

    arm = "FOUNDATION" if isinstance(model, FoundationActorCritic) else model.arm.value
    schedule = registered_episode_schedule(arm)
    snapshot = FrozenParameterSnapshot.from_model(model)
    with torch.no_grad():
        logits, old_value = _model_output(model, observation, physical_q, announced_k)
        old_log_probability = categorical_log_prob(logits, actions)
    rewards = tuple(tuple(float(value) for value in row) for row in primitive_rewards)
    targets = duration_correct_gae(
        primitive_rewards=rewards,
        old_values=old_value.detach(),
        nonterminal=nonterminal,
        episode_offsets=episode_offsets,
    )
    placeholder = FrozenUpdateBatch(
        arm=arm,
        replicate=replicate,
        update=update,
        schedule=schedule,
        episode_offsets=tuple(episode_offsets),
        observation=observation.detach().clone(),
        physical_q=None if physical_q is None else physical_q.detach().clone(),
        announced_k=announced_k.detach().clone(),
        actions=actions.detach().clone(),
        primitive_rewards=rewards,
        nonterminal=nonterminal.detach().clone(),
        old_log_probability=old_log_probability.detach().clone(),
        old_value=old_value.detach().clone(),
        targets=targets,
        old_parameters=snapshot,
        content_digest="",
    )
    result = FrozenUpdateBatch(**{**placeholder.__dict__, "content_digest": _batch_digest(placeholder)})
    result.validate_registered()
    return result


def joint_ppo_loss_from_terms(
    *,
    current_log_probability: Tensor,
    current_value: Tensor,
    current_entropy: Tensor,
    old_log_probability: Tensor,
    value_target: Tensor,
    normalized_advantage: Tensor,
) -> JointLoss:
    shapes = {tuple(value.shape) for value in (current_log_probability, current_value, current_entropy, old_log_probability, value_target, normalized_advantage)}
    if len(shapes) != 1 or not shapes or next(iter(shapes)) == ():
        raise TrainingContractError("PPO loss terms must share one nonempty vector shape")
    if any(value.dtype != torch.float32 or not bool(torch.isfinite(value).all()) for value in (current_log_probability, current_value, current_entropy, old_log_probability, value_target, normalized_advantage)):
        raise TrainingContractError("PPO loss terms must be finite float32")
    ratio = torch.exp(current_log_probability - old_log_probability)
    unclipped = ratio * normalized_advantage
    clipped = strict_clip(ratio, POLICY_CLIP_LOW, POLICY_CLIP_HIGH) * normalized_advantage
    policy = -ppo_tie_mean_min(unclipped, clipped).mean()
    value = 0.5 * torch.mean((current_value - value_target) ** 2)
    entropy = current_entropy.mean()
    total = policy + VALUE_COEFFICIENT * value - ENTROPY_COEFFICIENT * entropy
    return JointLoss(total, policy, value, entropy)


def joint_ppo_loss(
    model: FoundationActorCritic | OrderActorCritic,
    batch: FrozenUpdateBatch,
    indices: Sequence[int],
) -> JointLoss:
    rows = torch.tensor(tuple(indices), dtype=torch.int64)
    physical = None if batch.physical_q is None else batch.physical_q[rows]
    logits, value = _model_output(model, batch.observation[rows], physical, batch.announced_k[rows])
    return joint_ppo_loss_from_terms(
        current_log_probability=categorical_log_prob(logits, batch.actions[rows]),
        current_value=value,
        current_entropy=categorical_entropy(logits),
        old_log_probability=batch.old_log_probability[rows],
        value_target=batch.targets.value_targets[rows],
        normalized_advantage=batch.targets.normalized_advantages[rows],
    )


def clip_combined_global_gradient(parameters: Sequence[Tensor]) -> tuple[float, float]:
    values = tuple(parameters)
    if not values:
        raise TrainingContractError("global clipping requires trainable parameters")
    gradients = tuple(value.grad for value in values)
    if any(value is None for value in gradients):
        raise RuntimeError("every trainable tensor must receive a gradient")
    typed = tuple(value for value in gradients if value is not None)
    if any(not bool(torch.isfinite(value).all()) for value in typed):
        raise RuntimeError("combined gradient contains a nonfinite value")
    norm_tensor = torch.sqrt(sum(torch.sum(value * value) for value in typed))
    norm = float(norm_tensor.detach().cpu())
    scale = 1.0 if norm <= GLOBAL_GRADIENT_CLIP else GLOBAL_GRADIENT_CLIP / norm
    if scale != 1.0:
        for gradient in typed:
            gradient.mul_(scale)
    return norm, scale


class ExactAdamW:
    """One persistent, globally indexed exact float32 AdamW optimizer."""

    def __init__(self, model: FoundationActorCritic | OrderActorCritic) -> None:
        self.arm = "FOUNDATION" if isinstance(model, FoundationActorCritic) else model.arm.value
        self._named_parameters = _trainable_named_parameters(model)
        self._parameter_ids = tuple(id(value) for _, value in self._named_parameters)
        self._first = tuple(torch.zeros_like(value) for _, value in self._named_parameters)
        self._second = tuple(torch.zeros_like(value) for _, value in self._named_parameters)
        self.step_index = 0

    @property
    def parameters(self) -> tuple[Tensor, ...]:
        return tuple(value for _, value in self._named_parameters)

    @property
    def parameter_names(self) -> tuple[str, ...]:
        return tuple(name for name, _ in self._named_parameters)

    def matches_model(self, model: FoundationActorCritic | OrderActorCritic) -> bool:
        return self._parameter_ids == tuple(id(value) for _, value in _trainable_named_parameters(model))

    def zero_grad(self) -> None:
        for parameter in self.parameters:
            parameter.grad = None

    @torch.no_grad()
    def step(self, *, expected_step: int) -> None:
        if expected_step != self.step_index + 1:
            raise TrainingContractError("AdamW steps must be consecutive and globally one-based")
        if expected_step > _update_limit(self.arm) * OPTIMIZER_STEPS_PER_UPDATE:
            raise TrainingContractError("AdamW step exceeds the exact arm budget")
        correction1 = 1.0 - ADAMW_BETA1**expected_step
        correction2 = 1.0 - ADAMW_BETA2**expected_step
        for (_, parameter), first, second in zip(self._named_parameters, self._first, self._second):
            gradient = parameter.grad
            if gradient is None:
                raise RuntimeError("AdamW requires one gradient for every trainable tensor")
            old = parameter.detach().clone()
            first.mul_(ADAMW_BETA1).add_(gradient, alpha=1.0 - ADAMW_BETA1)
            second.mul_(ADAMW_BETA2).addcmul_(gradient, gradient, value=1.0 - ADAMW_BETA2)
            first_hat = first / correction1
            second_hat = second / correction2
            parameter.copy_(old - ADAMW_LR * (first_hat / (torch.sqrt(second_hat) + ADAMW_EPSILON) + ADAMW_WEIGHT_DECAY * old))
        self.step_index = expected_step

    def moment_payload(self) -> dict[str, object]:
        return {
            "parameter_names": self.parameter_names,
            "step_index": self.step_index,
            "first_moments": {name: value.detach().clone() for name, value in zip(self.parameter_names, self._first)},
            "second_moments": {name: value.detach().clone() for name, value in zip(self.parameter_names, self._second)},
            "law": training_contract()["optimizer"],
        }

    @torch.no_grad()
    def restore_moments(self, payload: Mapping[str, object]) -> None:
        _validate_optimizer_payload(payload, self)
        first = payload["first_moments"]
        second = payload["second_moments"]
        assert isinstance(first, Mapping) and isinstance(second, Mapping)
        for name, target in zip(self.parameter_names, self._first):
            target.copy_(first[name])
        for name, target in zip(self.parameter_names, self._second):
            target.copy_(second[name])
        self.step_index = int(payload["step_index"])


class DurationCorrectPPOTrainer:
    """One exact foundation or order-stage trainer with in-memory receipts."""

    def __init__(
        self,
        model: FoundationActorCritic | OrderActorCritic,
        *,
        permit: TrainingActivityPermit,
        optimizer: ExactAdamW | None = None,
    ) -> None:
        if not isinstance(permit, TrainingActivityPermit):
            raise TypeError("training requires an explicit activity permit")
        self.model = model
        self.arm = "FOUNDATION" if isinstance(model, FoundationActorCritic) else model.arm.value
        self.replicate = model.replicate
        self.permit = permit
        self.optimizer = ExactAdamW(model) if optimizer is None else optimizer
        if self.optimizer.arm != self.arm or not self.optimizer.matches_model(model):
            raise TrainingContractError("optimizer is bound to a different arm or model")

    def train_update(
        self,
        batch: FrozenUpdateBatch,
        *,
        permutations: MinibatchPermutationSource,
    ) -> TrainingUpdateReceipt:
        batch.validate_registered()
        if batch.arm != self.arm or batch.replicate != self.replicate:
            raise TrainingContractError("update batch belongs to a different controller")
        batch.old_parameters.require_exact_current_model(self.model)
        expected_before = (batch.update - 1) * OPTIMIZER_STEPS_PER_UPDATE
        if self.optimizer.step_index != expected_before:
            raise TrainingContractError("persistent AdamW frontier differs from the requested update")
        self.permit.require_training_update(
            card_revision=CARD_REVISION,
            replicate=self.replicate,
            arm=self.arm,
            update=batch.update,
            schedule=batch.schedule,
        )
        plans = registered_minibatch_plan(
            permutations,
            replicate=self.replicate,
            arm=self.arm,
            update=batch.update,
            count=batch.record_count,
        )
        receipts = []
        for plan in plans:
            for minibatch_index, indices in enumerate(plan.minibatches):
                self.optimizer.zero_grad()
                loss = joint_ppo_loss(self.model, batch, indices)
                loss.total.backward()
                norm, scale = clip_combined_global_gradient(self.optimizer.parameters)
                step = self.optimizer.step_index + 1
                self.optimizer.step(expected_step=step)
                receipts.append(
                    MinibatchStepReceipt(
                        optimizer_step=step,
                        update=batch.update,
                        epoch=plan.epoch,
                        minibatch=minibatch_index,
                        record_count=len(indices),
                        total_loss=float(loss.total.detach().cpu()),
                        policy_loss=float(loss.policy.detach().cpu()),
                        value_loss=float(loss.value.detach().cpu()),
                        entropy=float(loss.entropy.detach().cpu()),
                        gradient_norm_before_clip=norm,
                        gradient_scale=scale,
                    )
                )
        if len(receipts) != OPTIMIZER_STEPS_PER_UPDATE:
            raise RuntimeError("each update must produce exactly 12 AdamW steps")
        batch.validate_registered()
        return TrainingUpdateReceipt(
            arm=self.arm,
            replicate=self.replicate,
            update=batch.update,
            optimizer_step=self.optimizer.step_index,
            schedule_digest=_schedule_digest(batch.schedule),
            batch_digest=batch.content_digest,
            steps=tuple(receipts),
            complete_checkpoint_eligible=batch.update == _update_limit(self.arm),
        )

    def checkpoint_payload(self, *, completed_updates: int) -> dict[str, object]:
        return make_checkpoint_payload(self.model, self.optimizer, completed_updates=completed_updates)

    def restore_checkpoint(self, payload: Mapping[str, object]) -> CheckpointValidationReceipt:
        receipt = validate_checkpoint_payload(payload, self.model, self.optimizer)
        self.permit.require_checkpoint_restore(
            card_revision=CARD_REVISION,
            replicate=self.replicate,
            arm=self.arm,
            completed_updates=receipt.completed_updates,
        )
        parameters = payload["parameters"]
        assert isinstance(parameters, Mapping)
        with torch.no_grad():
            for name, parameter in self.model.named_parameters():
                if parameter.requires_grad:
                    parameter.copy_(parameters[name])
        optimizer = payload["optimizer"]
        assert isinstance(optimizer, Mapping)
        self.optimizer.restore_moments(optimizer)
        if isinstance(self.model, OrderActorCritic):
            self.model.foundation.validate_immutable()
        return receipt


def _all_parameter_mapping(model: FoundationActorCritic | OrderActorCritic) -> dict[str, Tensor]:
    return {name: value.detach().clone() for name, value in model.named_parameters()}


def make_checkpoint_payload(
    model: FoundationActorCritic | OrderActorCritic,
    optimizer: ExactAdamW,
    *,
    completed_updates: int,
) -> dict[str, object]:
    arm = "FOUNDATION" if isinstance(model, FoundationActorCritic) else model.arm.value
    if optimizer.arm != arm or not optimizer.matches_model(model):
        raise TrainingContractError("checkpoint optimizer is bound to a different model")
    limit = _update_limit(arm)
    if isinstance(completed_updates, bool) or not 0 <= completed_updates <= limit:
        raise TrainingContractError("completed update count is outside the exact arm budget")
    if optimizer.step_index != completed_updates * OPTIMIZER_STEPS_PER_UPDATE:
        raise TrainingContractError("checkpoint update count and global optimizer index differ")
    if isinstance(model, OrderActorCritic):
        model.foundation.validate_immutable()
    return {
        "schema": CHECKPOINT_SCHEMA,
        "card_revision": CARD_REVISION,
        "arm": arm,
        "replicate": model.replicate,
        "completed_updates": completed_updates,
        "parameters": _all_parameter_mapping(model),
        "optimizer": optimizer.moment_payload(),
        "frozen_foundation_digest": model.foundation_digest if isinstance(model, OrderActorCritic) else None,
        "shared_parameterization_across_k": True,
        "per_k_state": None,
    }


def _validate_tensor_mapping(
    observed: object,
    expected: Mapping[str, Tensor],
    *,
    label: str,
) -> Mapping[str, Tensor]:
    if not isinstance(observed, Mapping) or set(observed) != set(expected):
        raise TrainingContractError(f"{label} tensor names differ")
    for name, reference in expected.items():
        value = observed[name]
        if not isinstance(value, Tensor) or value.dtype != torch.float32 or value.shape != reference.shape:
            raise TrainingContractError(f"{label} tensor shape or dtype differs for {name}")
        if not bool(torch.isfinite(value).all()):
            raise TrainingContractError(f"{label} tensor is nonfinite for {name}")
    return observed


def _validate_optimizer_payload(payload: Mapping[str, object], optimizer: ExactAdamW) -> None:
    required = {"parameter_names", "step_index", "first_moments", "second_moments", "law"}
    if set(payload) != required or tuple(payload.get("parameter_names", ())) != optimizer.parameter_names:
        raise TrainingContractError("optimizer payload names or fields differ")
    if payload.get("law") != training_contract()["optimizer"]:
        raise TrainingContractError("optimizer payload law differs")
    step = payload.get("step_index")
    maximum = _update_limit(optimizer.arm) * OPTIMIZER_STEPS_PER_UPDATE
    if isinstance(step, bool) or not isinstance(step, int) or not 0 <= step <= maximum:
        raise TrainingContractError("optimizer payload step is invalid")
    expected = {name: value for name, value in zip(optimizer.parameter_names, optimizer.parameters)}
    _validate_tensor_mapping(payload.get("first_moments"), expected, label="first moment")
    _validate_tensor_mapping(payload.get("second_moments"), expected, label="second moment")


def validate_checkpoint_payload(
    payload: Mapping[str, object],
    model: FoundationActorCritic | OrderActorCritic,
    optimizer: ExactAdamW,
) -> CheckpointValidationReceipt:
    required = {
        "schema",
        "card_revision",
        "arm",
        "replicate",
        "completed_updates",
        "parameters",
        "optimizer",
        "frozen_foundation_digest",
        "shared_parameterization_across_k",
        "per_k_state",
    }
    if not isinstance(payload, Mapping) or set(payload) != required:
        raise TrainingContractError("checkpoint payload fields differ")
    arm = "FOUNDATION" if isinstance(model, FoundationActorCritic) else model.arm.value
    if payload["schema"] != CHECKPOINT_SCHEMA or payload["card_revision"] != CARD_REVISION:
        raise TrainingContractError("checkpoint schema or card revision differs")
    if payload["arm"] != arm or payload["replicate"] != model.replicate:
        raise TrainingContractError("checkpoint arm or replicate differs")
    if payload["shared_parameterization_across_k"] is not True or payload["per_k_state"] is not None:
        raise TrainingContractError("checkpoint contains forbidden per-k state")
    completed = payload["completed_updates"]
    if isinstance(completed, bool) or not isinstance(completed, int) or not 0 <= completed <= _update_limit(arm):
        raise TrainingContractError("checkpoint completed-update count is invalid")
    parameters = _validate_tensor_mapping(payload["parameters"], dict(model.named_parameters()), label="parameter")
    optimizer_payload = payload["optimizer"]
    if not isinstance(optimizer_payload, Mapping):
        raise TrainingContractError("checkpoint optimizer payload is absent")
    _validate_optimizer_payload(optimizer_payload, optimizer)
    step = int(optimizer_payload["step_index"])
    if step != completed * OPTIMIZER_STEPS_PER_UPDATE:
        raise TrainingContractError("checkpoint update count and optimizer index differ")
    foundation_digest: str | None
    if isinstance(model, OrderActorCritic):
        model.foundation.validate_immutable()
        foundation_digest = model.foundation_digest
        if payload["frozen_foundation_digest"] != foundation_digest:
            raise TrainingContractError("checkpoint frozen-foundation digest differs")
        current = dict(model.named_parameters())
        for name, value in parameters.items():
            if name.startswith("foundation.") and not torch.equal(value, current[name]):
                raise TrainingContractError("checkpoint attempts to change the frozen foundation")
    else:
        foundation_digest = None
        if payload["frozen_foundation_digest"] is not None:
            raise TrainingContractError("foundation checkpoint cannot carry an adapter foundation digest")
    parameter_names = tuple(parameters)
    parameter_digest = _named_tensor_digest(parameter_names, tuple(parameters[name] for name in parameter_names))
    first = optimizer_payload["first_moments"]
    second = optimizer_payload["second_moments"]
    assert isinstance(first, Mapping) and isinstance(second, Mapping)
    optimizer_names = optimizer.parameter_names
    optimizer_digest = _named_tensor_digest(
        tuple(f"m:{name}" for name in optimizer_names) + tuple(f"v:{name}" for name in optimizer_names),
        tuple(first[name] for name in optimizer_names) + tuple(second[name] for name in optimizer_names),
    )
    return CheckpointValidationReceipt(
        schema=CHECKPOINT_SCHEMA,
        arm=arm,
        replicate=model.replicate,
        completed_updates=completed,
        optimizer_step=step,
        parameter_digest=parameter_digest,
        optimizer_digest=optimizer_digest,
        frozen_foundation_digest=foundation_digest,
        final_checkpoint=completed == _update_limit(arm),
    )


__all__ = [
    "ActionUniformSource",
    "CheckpointValidationReceipt",
    "DurationCorrectPPOTrainer",
    "EPOCHS_PER_UPDATE",
    "EPISODES_PER_UPDATE",
    "EpisodeSlot",
    "ExactAdamW",
    "FrozenParameterSnapshot",
    "FrozenUpdateBatch",
    "GAETargets",
    "MinibatchPermutationSource",
    "MinibatchStepReceipt",
    "OPTIMIZER_STEPS_PER_UPDATE",
    "TrainingActivityPermit",
    "TrainingContractError",
    "TrainingUpdateReceipt",
    "clip_combined_global_gradient",
    "duration_correct_gae",
    "freeze_update_batch",
    "joint_ppo_loss",
    "joint_ppo_loss_from_terms",
    "make_checkpoint_payload",
    "normalize_population_advantage",
    "registered_episode_schedule",
    "registered_minibatch_plan",
    "sample_actions_from_source",
    "split_four_near_equal",
    "training_contract",
    "validate_checkpoint_payload",
]
