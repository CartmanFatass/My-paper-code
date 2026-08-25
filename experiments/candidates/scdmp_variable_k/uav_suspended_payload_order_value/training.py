"""Exact duration-correct PPO/AdamW contract for SCDMP UAV r02.

The pure target, loss, and plan validators are identity-free.  Model snapshots,
optimizer state, and parameter updates are reachable only through a model that
was constructed with an explicit future activity/identity permit.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from typing import Final, Protocol, Sequence

import torch
from torch import Tensor

from .config import CARD_REVISION
from .model import (
    LearnedArm,
    ModelActivityIdentityPermit,
    SCDMPUAVActorCritic,
    categorical_entropy,
    categorical_log_prob,
    model_schema,
)


GAMMA: Final[float] = 0.996
GAE_LAMBDA: Final[float] = 0.94
ADVANTAGE_EPSILON: Final[float] = 1e-8
POLICY_CLIP_LOW: Final[float] = 0.82
POLICY_CLIP_HIGH: Final[float] = 1.18
VALUE_COEFFICIENT: Final[float] = 0.55
ENTROPY_COEFFICIENT: Final[float] = 0.012
GLOBAL_GRADIENT_CLIP: Final[float] = 0.9

PPO_UPDATES_PER_ARM: Final[int] = 144
SLOTS_PER_UPDATE: Final[int] = 12
EPOCHS_PER_UPDATE: Final[int] = 4
MINIBATCHES_PER_EPOCH: Final[int] = 4
OPTIMIZER_STEPS_PER_UPDATE: Final[int] = 16
MAX_OPTIMIZER_STEP: Final[int] = 2_304

ADAMW_LR: Final[float] = 2.5e-4
ADAMW_BETA1: Final[float] = 0.9
ADAMW_BETA2: Final[float] = 0.999
ADAMW_EPSILON: Final[float] = 1e-8
ADAMW_WEIGHT_DECAY: Final[float] = 2e-5


class MinibatchPermutationSource(Protocol):
    """Adapter for the future registered training-minibatch-order stream."""

    def permutation_indices(
        self,
        *,
        replicate: int,
        arm: str,
        update: int,
        epoch: int,
        count: int,
    ) -> tuple[int, ...]:
        """Return the permutation keyed by exactly these coordinates."""


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
    sha256: str

    @classmethod
    def from_model(cls, model: SCDMPUAVActorCritic) -> "FrozenParameterSnapshot":
        names: list[str] = []
        values: list[Tensor] = []
        for name, parameter in model.named_parameters():
            names.append(name)
            values.append(parameter.detach().clone())
        digest = _parameter_digest(tuple(names), tuple(values))
        return cls(tuple(names), tuple(values), digest)

    def validate_immutable(self) -> None:
        if any(value.requires_grad for value in self.values):
            raise RuntimeError("old parameter snapshot must be stop-gradient")
        if _parameter_digest(self.names, self.values) != self.sha256:
            raise RuntimeError("old parameter snapshot was mutated")

    def require_exact_current_model(self, model: SCDMPUAVActorCritic) -> None:
        current = tuple(model.named_parameters())
        current_names = tuple(name for name, _ in current)
        current_values = tuple(parameter.detach() for _, parameter in current)
        if current_names != self.names:
            raise RuntimeError("old parameter snapshot names do not match the current model")
        if _parameter_digest(current_names, current_values) != self.sha256:
            raise RuntimeError("stale or cross-wired old parameter snapshot")


@dataclass(frozen=True)
class FrozenUpdateBatch:
    arm: LearnedArm
    observations: Tensor
    true_q: Tensor
    actions: Tensor
    old_logp: Tensor
    old_values: Tensor
    targets: GAETargets
    slot_offsets: tuple[int, ...]
    old_parameters: FrozenParameterSnapshot
    old_data_sha256: str

    @property
    def record_count(self) -> int:
        return int(self.actions.numel())

    def validate_registered(self) -> None:
        count = self.record_count
        if self.observations.shape != (count, 14):
            raise ValueError("registered observations must have shape [records,14]")
        expected_vector = (count,)
        tensors = (
            self.true_q,
            self.actions,
            self.old_logp,
            self.old_values,
            self.targets.discounted_rewards,
            self.targets.deltas,
            self.targets.raw_advantages,
            self.targets.value_targets,
            self.targets.normalized_advantages,
        )
        if any(tensor.shape != expected_vector for tensor in tensors):
            raise ValueError("every registered update field must cover the identical valid records")
        if len(self.slot_offsets) != SLOTS_PER_UPDATE + 1:
            raise ValueError("a registered update must contain exactly 12 complete slots")
        _validate_slot_offsets(self.slot_offsets, count)
        if self.actions.dtype != torch.int64:
            raise TypeError("actions must use int64")
        if any(
            tensor.dtype != torch.float32
            for tensor in (
                self.observations,
                self.true_q,
                self.old_logp,
                self.old_values,
                self.targets.discounted_rewards,
                self.targets.deltas,
                self.targets.raw_advantages,
                self.targets.value_targets,
                self.targets.normalized_advantages,
            )
        ):
            raise TypeError("registered model/training tensors must use float32")
        if not bool(torch.all((self.true_q == 0.0) | (self.true_q == 1.0))):
            raise ValueError("rollout records must retain exact physical q in {0,1}")
        self.old_parameters.validate_immutable()
        immutable_names = (
            "old_logp",
            "old_values",
            "discounted_rewards",
            "deltas",
            "raw_advantages",
            "value_targets",
            "normalized_advantages",
        )
        immutable_values = (
            self.old_logp,
            self.old_values,
            self.targets.discounted_rewards,
            self.targets.deltas,
            self.targets.raw_advantages,
            self.targets.value_targets,
            self.targets.normalized_advantages,
        )
        if _tensor_digest(immutable_names, immutable_values) != self.old_data_sha256:
            raise RuntimeError("immutable old-policy targets or advantages were mutated")


def training_contract() -> dict[str, object]:
    """Return the complete static trainer constants without model activity."""

    return {
        "gamma": GAMMA,
        "gae_lambda": GAE_LAMBDA,
        "advantage_population_epsilon": ADVANTAGE_EPSILON,
        "policy_clip": (POLICY_CLIP_LOW, POLICY_CLIP_HIGH),
        "value_coefficient": VALUE_COEFFICIENT,
        "entropy_coefficient": ENTROPY_COEFFICIENT,
        "global_gradient_clip": GLOBAL_GRADIENT_CLIP,
        "updates_per_arm": PPO_UPDATES_PER_ARM,
        "slots_per_update": SLOTS_PER_UPDATE,
        "epochs_per_update": EPOCHS_PER_UPDATE,
        "minibatches_per_epoch": MINIBATCHES_PER_EPOCH,
        "optimizer_steps_per_update": OPTIMIZER_STEPS_PER_UPDATE,
        "optimizer_steps_per_arm": MAX_OPTIMIZER_STEP,
        "optimizer": {
            "name": "single_persistent_all_parameter_AdamW",
            "lr": ADAMW_LR,
            "betas": (ADAMW_BETA1, ADAMW_BETA2),
            "epsilon": ADAMW_EPSILON,
            "weight_decay": ADAMW_WEIGHT_DECAY,
            "decay_applies_to": "all_matrices_and_biases",
            "amsgrad": False,
            "maximize": False,
            "globally_one_based_steps": (1, MAX_OPTIMIZER_STEP),
        },
        "forbidden": (
            "trainer_menu",
            "architecture_search",
            "learning_rate_search",
            "early_stop",
            "running_normalization",
            "per_k_head",
            "per_k_optimizer",
            "per_k_update",
            "value_clipping",
            "huber_loss",
            "kl_term",
            "primitive_time_loss_weighting",
        ),
    }


def _parameter_digest(names: Sequence[str], values: Sequence[Tensor]) -> str:
    digest = hashlib.sha256()
    for name, value in zip(names, values):
        contiguous = value.detach().to(device="cpu", dtype=torch.float32).contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(tuple(contiguous.shape)).encode("ascii"))
        digest.update(contiguous.numpy().tobytes(order="C"))
    return digest.hexdigest()


def _tensor_digest(names: Sequence[str], values: Sequence[Tensor]) -> str:
    return _parameter_digest(names, values)


def _validate_slot_offsets(offsets: Sequence[int], count: int) -> tuple[int, ...]:
    frozen = tuple(int(value) for value in offsets)
    if not frozen or frozen[0] != 0 or frozen[-1] != count:
        raise ValueError("slot offsets must start at zero and end at record count")
    if any(left >= right for left, right in zip(frozen, frozen[1:])):
        raise ValueError("every slot must be nonempty and offsets strictly increasing")
    return frozen


def normalize_population_advantage(raw_advantage: Tensor) -> Tensor:
    if raw_advantage.dtype != torch.float32 or raw_advantage.ndim != 1 or raw_advantage.numel() == 0:
        raise ValueError("raw advantages must be a nonempty float32 vector")
    if not bool(torch.isfinite(raw_advantage).all()):
        raise ValueError("raw advantages must be finite")
    frozen = raw_advantage.detach()
    mean = frozen.mean()
    population_variance = ((frozen - mean) ** 2).mean()
    return ((frozen - mean) / torch.sqrt(population_variance + ADVANTAGE_EPSILON)).detach()


def duration_correct_gae(
    primitive_rewards: Sequence[Sequence[float] | Tensor],
    old_values: Tensor,
    nonterminal: Tensor,
    slot_offsets: Sequence[int],
) -> GAETargets:
    """Compute the frozen primitive-clock return, delta, GAE, and value target."""

    if old_values.dtype != torch.float32 or old_values.ndim != 1:
        raise TypeError("old_values must be a float32 vector")
    count = int(old_values.numel())
    if len(primitive_rewards) != count:
        raise ValueError("primitive reward sequences must match old_values")
    if nonterminal.dtype != torch.bool or nonterminal.shape != (count,):
        raise TypeError("nonterminal must be a bool vector matching old_values")
    offsets = _validate_slot_offsets(slot_offsets, count)
    if not bool(torch.isfinite(old_values).all()):
        raise ValueError("old values must be finite")

    device = old_values.device
    discounted_rewards = torch.empty_like(old_values)
    durations: list[int] = []
    for index, rewards in enumerate(primitive_rewards):
        values = torch.as_tensor(rewards, dtype=torch.float32, device=device).detach()
        if values.ndim != 1 or values.numel() == 0:
            raise ValueError("each valid renewal must contain one or more primitive rewards")
        if not bool(torch.isfinite(values).all()):
            raise ValueError("primitive rewards must be finite")
        duration = int(values.numel())
        durations.append(duration)
        powers = torch.pow(
            torch.tensor(GAMMA, dtype=torch.float32, device=device),
            torch.arange(duration, dtype=torch.float32, device=device),
        )
        discounted_rewards[index] = torch.sum(powers * values)

    deltas = torch.empty_like(old_values)
    raw_advantages = torch.empty_like(old_values)
    for start, stop in zip(offsets, offsets[1:]):
        if bool(nonterminal[stop - 1]):
            raise ValueError("the final renewal in every complete slot must be terminal")
        for index in range(start, stop):
            continuing = bool(nonterminal[index])
            if continuing and index + 1 >= stop:
                raise ValueError("nonterminal renewal has no same-slot successor")
            bootstrap = old_values[index + 1] if continuing else old_values.new_zeros(())
            gamma_h = GAMMA ** durations[index]
            deltas[index] = (
                discounted_rewards[index]
                + float(gamma_h) * bootstrap
                - old_values[index]
            )
        next_advantage = old_values.new_zeros(())
        for index in range(stop - 1, start - 1, -1):
            continuing = bool(nonterminal[index])
            trace = (GAMMA * GAE_LAMBDA) ** durations[index]
            raw_advantages[index] = deltas[index] + (
                float(trace) * next_advantage if continuing else 0.0
            )
            next_advantage = raw_advantages[index]

    frozen_old_values = old_values.detach()
    raw_advantages = raw_advantages.detach()
    return GAETargets(
        discounted_rewards=discounted_rewards.detach(),
        deltas=deltas.detach(),
        raw_advantages=raw_advantages,
        value_targets=(raw_advantages + frozen_old_values).detach(),
        normalized_advantages=normalize_population_advantage(raw_advantages),
    )


def _validate_permutation(permutation: Sequence[int], count: int) -> tuple[int, ...]:
    frozen = tuple(permutation)
    if len(frozen) != count:
        raise ValueError("minibatch source returned the wrong permutation length")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in frozen):
        raise TypeError("permutation indices must be integers")
    if tuple(sorted(frozen)) != tuple(range(count)):
        raise ValueError("minibatch source must return an exact permutation")
    return frozen


def split_four_near_equal(permutation: Sequence[int]) -> tuple[tuple[int, ...], ...]:
    frozen = tuple(permutation)
    if len(frozen) < MINIBATCHES_PER_EPOCH:
        raise ValueError("four nonempty minibatches require at least four valid records")
    quotient, remainder = divmod(len(frozen), MINIBATCHES_PER_EPOCH)
    batches: list[tuple[int, ...]] = []
    cursor = 0
    for batch_index in range(MINIBATCHES_PER_EPOCH):
        size = quotient + (1 if batch_index < remainder else 0)
        batches.append(frozen[cursor : cursor + size])
        cursor += size
    if max(map(len, batches)) - min(map(len, batches)) > 1 or any(not batch for batch in batches):
        raise RuntimeError("four-way minibatch split violated the frozen balance law")
    return tuple(batches)


def registered_minibatch_plan(
    source: MinibatchPermutationSource,
    *,
    replicate: int,
    arm: LearnedArm | str,
    update: int,
    count: int,
) -> tuple[EpochMinibatches, ...]:
    learned_arm = arm if isinstance(arm, LearnedArm) else LearnedArm(arm)
    if isinstance(replicate, bool) or not isinstance(replicate, int) or not 0 <= replicate < 18:
        raise ValueError("replicate must be an integer in [0,18)")
    if isinstance(update, bool) or not isinstance(update, int) or not 1 <= update <= PPO_UPDATES_PER_ARM:
        raise ValueError("update must be globally one-based in [1,144]")
    if count < MINIBATCHES_PER_EPOCH:
        raise ValueError("an update requires at least four valid decision records")
    plans: list[EpochMinibatches] = []
    for epoch in range(1, EPOCHS_PER_UPDATE + 1):
        permutation = _validate_permutation(
            source.permutation_indices(
                replicate=replicate,
                arm=learned_arm.value,
                update=update,
                epoch=epoch,
                count=count,
            ),
            count,
        )
        plans.append(EpochMinibatches(epoch, permutation, split_four_near_equal(permutation)))
    return tuple(plans)


def joint_ppo_loss_from_terms(
    *,
    current_logp: Tensor,
    current_value: Tensor,
    current_entropy: Tensor,
    old_logp: Tensor,
    value_target: Tensor,
    normalized_advantage: Tensor,
) -> JointLoss:
    shape = current_logp.shape
    tensors = (
        current_logp,
        current_value,
        current_entropy,
        old_logp,
        value_target,
        normalized_advantage,
    )
    if not shape or any(tensor.shape != shape for tensor in tensors):
        raise ValueError("all PPO loss terms must have the identical nonempty shape")
    if any(tensor.dtype != torch.float32 for tensor in tensors):
        raise TypeError("all PPO loss terms must use float32")
    if any(not bool(torch.isfinite(tensor).all()) for tensor in tensors):
        raise ValueError("all PPO loss terms must be finite")
    ratio = torch.exp(current_logp - old_logp.detach())
    advantage = normalized_advantage.detach()
    unclipped = ratio * advantage
    clipped = torch.clamp(ratio, POLICY_CLIP_LOW, POLICY_CLIP_HIGH) * advantage
    policy = -torch.minimum(unclipped, clipped).mean()
    value = 0.5 * ((current_value - value_target.detach()) ** 2).mean()
    entropy = current_entropy.mean()
    total = policy + VALUE_COEFFICIENT * value - ENTROPY_COEFFICIENT * entropy
    return JointLoss(total=total, policy=policy, value=value, entropy=entropy)


def freeze_update_batch(
    model: SCDMPUAVActorCritic,
    *,
    observations: Tensor,
    true_q: Tensor,
    actions: Tensor,
    primitive_rewards: Sequence[Sequence[float] | Tensor],
    nonterminal: Tensor,
    slot_offsets: Sequence[int],
) -> FrozenUpdateBatch:
    """Snapshot the complete old model and all immutable per-update quantities."""

    snapshot = FrozenParameterSnapshot.from_model(model)
    with torch.no_grad():
        output = model(observations, true_q)
        old_logp = categorical_log_prob(output.logits, actions).detach().clone()
        old_values = output.value.detach().clone()
    targets = duration_correct_gae(primitive_rewards, old_values, nonterminal, slot_offsets)
    batch = FrozenUpdateBatch(
        arm=model.arm,
        observations=observations.detach().clone(),
        true_q=true_q.detach().clone(),
        actions=actions.detach().clone(),
        old_logp=old_logp,
        old_values=old_values,
        targets=targets,
        slot_offsets=tuple(slot_offsets),
        old_parameters=snapshot,
        old_data_sha256=_tensor_digest(
            (
                "old_logp",
                "old_values",
                "discounted_rewards",
                "deltas",
                "raw_advantages",
                "value_targets",
                "normalized_advantages",
            ),
            (
                old_logp,
                old_values,
                targets.discounted_rewards,
                targets.deltas,
                targets.raw_advantages,
                targets.value_targets,
                targets.normalized_advantages,
            ),
        ),
    )
    batch.validate_registered()
    return batch


def joint_ppo_loss(
    model: SCDMPUAVActorCritic,
    batch: FrozenUpdateBatch,
    indices: Sequence[int],
) -> JointLoss:
    selected = torch.tensor(tuple(indices), dtype=torch.int64, device=batch.actions.device)
    if selected.numel() == 0:
        raise ValueError("a minibatch must be nonempty")
    output = model(batch.observations[selected], batch.true_q[selected])
    current_logp = categorical_log_prob(output.logits, batch.actions[selected])
    entropy = categorical_entropy(output.logits)
    return joint_ppo_loss_from_terms(
        current_logp=current_logp,
        current_value=output.value,
        current_entropy=entropy,
        old_logp=batch.old_logp[selected],
        value_target=batch.targets.value_targets[selected],
        normalized_advantage=batch.targets.normalized_advantages[selected],
    )


def clip_combined_global_gradient(parameters: Sequence[Tensor]) -> tuple[float, float]:
    gradients = []
    for parameter in parameters:
        if parameter.grad is None:
            raise RuntimeError("the single joint loss must differentiate every trainable parameter")
        if parameter.grad.dtype != torch.float32 or not bool(torch.isfinite(parameter.grad).all()):
            raise RuntimeError("combined gradients must be finite float32 tensors")
        gradients.append(parameter.grad)
    if not gradients:
        raise RuntimeError("optimizer received no trainable parameters")
    device = gradients[0].device
    squared = torch.zeros((), dtype=torch.float32, device=device)
    for gradient in gradients:
        squared = squared + torch.sum(gradient * gradient)
    norm = torch.sqrt(squared)
    scale = torch.ones((), dtype=torch.float32, device=device)
    if bool(norm > GLOBAL_GRADIENT_CLIP):
        scale = torch.tensor(GLOBAL_GRADIENT_CLIP, dtype=torch.float32, device=device) / norm
        for gradient in gradients:
            gradient.mul_(scale)
    return float(norm.detach().cpu()), float(scale.detach().cpu())


class ExactAdamW:
    """Unfused, persistent, globally one-based all-parameter AdamW."""

    def __init__(
        self,
        model: SCDMPUAVActorCritic,
        *,
        permit: ModelActivityIdentityPermit,
    ) -> None:
        if permit is not model.activity_permit:
            raise PermissionError("optimizer must use the model's exact activity/identity permit")
        permit.require_training(card_revision=CARD_REVISION, arm=model.arm.value)
        self.arm = model.arm
        self._named_parameters = tuple(model.named_parameters())
        if sum(parameter.numel() for _, parameter in self._named_parameters) != model_schema(model.arm).parameter_count:
            raise RuntimeError("optimizer must cover the complete arm parameter set")
        if len({id(parameter) for _, parameter in self._named_parameters}) != len(self._named_parameters):
            raise RuntimeError("optimizer parameter list contains aliases")
        self._m = tuple(torch.zeros_like(parameter) for _, parameter in self._named_parameters)
        self._v = tuple(torch.zeros_like(parameter) for _, parameter in self._named_parameters)
        self.step_index = 0

    @property
    def parameters(self) -> tuple[Tensor, ...]:
        return tuple(parameter for _, parameter in self._named_parameters)

    def matches_model(self, model: SCDMPUAVActorCritic) -> bool:
        return tuple(id(parameter) for parameter in self.parameters) == tuple(
            id(parameter) for parameter in model.parameters()
        )

    def zero_grad(self) -> None:
        for parameter in self.parameters:
            parameter.grad = None

    @torch.no_grad()
    def step(self, *, expected_step: int) -> None:
        if expected_step != self.step_index + 1:
            raise ValueError("AdamW steps must be consecutive and globally one-based")
        if expected_step > MAX_OPTIMIZER_STEP:
            raise ValueError("AdamW step exceeds the frozen 2,304-step arm budget")
        beta1_correction = 1.0 - ADAMW_BETA1**expected_step
        beta2_correction = 1.0 - ADAMW_BETA2**expected_step
        for (_, parameter), first, second in zip(self._named_parameters, self._m, self._v):
            gradient = parameter.grad
            if gradient is None:
                raise RuntimeError("AdamW requires a gradient for every named scalar")
            old_parameter = parameter.detach().clone()
            first.mul_(ADAMW_BETA1).add_(gradient, alpha=1.0 - ADAMW_BETA1)
            second.mul_(ADAMW_BETA2).addcmul_(gradient, gradient, value=1.0 - ADAMW_BETA2)
            first_hat = first / beta1_correction
            second_hat = second / beta2_correction
            exact_update = (
                first_hat / (torch.sqrt(second_hat) + ADAMW_EPSILON)
                + ADAMW_WEIGHT_DECAY * old_parameter
            )
            parameter.copy_(old_parameter - ADAMW_LR * exact_update)
        self.step_index = expected_step

    def state_dict(self) -> dict[str, object]:
        return {
            "arm": self.arm.value,
            "step_index": self.step_index,
            "parameter_names": tuple(name for name, _ in self._named_parameters),
            "first_moments": tuple(moment.detach().clone() for moment in self._m),
            "second_moments": tuple(moment.detach().clone() for moment in self._v),
            "law": training_contract()["optimizer"],
        }

    def load_state_dict(self, state: dict[str, object]) -> None:
        if state.get("arm") != self.arm.value or state.get("law") != training_contract()["optimizer"]:
            raise ValueError("AdamW state identity or law mismatch")
        names = tuple(name for name, _ in self._named_parameters)
        if tuple(state.get("parameter_names", ())) != names:
            raise ValueError("AdamW state parameter names mismatch")
        step = state.get("step_index")
        if isinstance(step, bool) or not isinstance(step, int) or not 0 <= step <= MAX_OPTIMIZER_STEP:
            raise ValueError("AdamW state step index is invalid")
        first = tuple(state.get("first_moments", ()))
        second = tuple(state.get("second_moments", ()))
        if len(first) != len(self._m) or len(second) != len(self._v):
            raise ValueError("AdamW state moment count mismatch")
        with torch.no_grad():
            for target, source in zip(self._m + self._v, first + second):
                if not isinstance(source, Tensor) or source.shape != target.shape or source.dtype != torch.float32:
                    raise ValueError("AdamW state moment tensor mismatch")
                if not bool(torch.isfinite(source).all()):
                    raise ValueError("AdamW state moments must be finite")
                target.copy_(source)
        self.step_index = step


@dataclass(frozen=True)
class MinibatchStepRecord:
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


class DurationCorrectPPOTrainer:
    """One frozen trainer; no menus, search, stopping rule, or normalization."""

    def __init__(
        self,
        model: SCDMPUAVActorCritic,
        *,
        permit: ModelActivityIdentityPermit,
        optimizer: ExactAdamW | None = None,
    ) -> None:
        if permit is not model.activity_permit:
            raise PermissionError("trainer must use the model's exact activity/identity permit")
        permit.require_training(card_revision=CARD_REVISION, arm=model.arm.value)
        self.model = model
        self.optimizer = optimizer if optimizer is not None else ExactAdamW(model, permit=permit)
        if self.optimizer.arm is not model.arm:
            raise ValueError("trainer and optimizer arms differ")
        if not self.optimizer.matches_model(model):
            raise ValueError("trainer optimizer is bound to a different model instance")

    def train_update(
        self,
        batch: FrozenUpdateBatch,
        *,
        replicate: int,
        update: int,
        permutations: MinibatchPermutationSource,
    ) -> tuple[MinibatchStepRecord, ...]:
        batch.validate_registered()
        if batch.arm is not self.model.arm:
            raise ValueError("update batch belongs to a different learned arm")
        # This is intentionally before permutation calls, backward, clipping,
        # or optimizer mutation.  PPO old quantities must bind the exact live
        # pre-update parameter vector, not merely a same-shaped arm.
        batch.old_parameters.require_exact_current_model(self.model)
        expected_before = (update - 1) * OPTIMIZER_STEPS_PER_UPDATE
        if self.optimizer.step_index != expected_before:
            raise ValueError("persistent AdamW frontier does not match the requested PPO update")
        plans = registered_minibatch_plan(
            permutations,
            replicate=replicate,
            arm=self.model.arm,
            update=update,
            count=batch.record_count,
        )
        batch.old_parameters.validate_immutable()
        records: list[MinibatchStepRecord] = []
        for plan in plans:
            for minibatch_number, indices in enumerate(plan.minibatches, start=1):
                self.optimizer.zero_grad()
                loss = joint_ppo_loss(self.model, batch, indices)
                loss.total.backward()  # exactly one combined backward pass
                gradient_norm, gradient_scale = clip_combined_global_gradient(
                    self.optimizer.parameters
                )
                optimizer_step = self.optimizer.step_index + 1
                self.optimizer.step(expected_step=optimizer_step)
                records.append(
                    MinibatchStepRecord(
                        optimizer_step=optimizer_step,
                        update=update,
                        epoch=plan.epoch,
                        minibatch=minibatch_number,
                        record_count=len(indices),
                        total_loss=float(loss.total.detach().cpu()),
                        policy_loss=float(loss.policy.detach().cpu()),
                        value_loss=float(loss.value.detach().cpu()),
                        entropy=float(loss.entropy.detach().cpu()),
                        gradient_norm_before_clip=gradient_norm,
                        gradient_scale=gradient_scale,
                    )
                )
        if len(records) != OPTIMIZER_STEPS_PER_UPDATE:
            raise RuntimeError("each PPO update must perform exactly 16 joint AdamW steps")
        batch.validate_registered()
        return tuple(records)


__all__ = [
    "ADVANTAGE_EPSILON",
    "DurationCorrectPPOTrainer",
    "EPOCHS_PER_UPDATE",
    "EpochMinibatches",
    "ExactAdamW",
    "FrozenParameterSnapshot",
    "FrozenUpdateBatch",
    "GAETargets",
    "GAMMA",
    "GAE_LAMBDA",
    "GLOBAL_GRADIENT_CLIP",
    "JointLoss",
    "MAX_OPTIMIZER_STEP",
    "MINIBATCHES_PER_EPOCH",
    "MinibatchPermutationSource",
    "MinibatchStepRecord",
    "OPTIMIZER_STEPS_PER_UPDATE",
    "POLICY_CLIP_HIGH",
    "POLICY_CLIP_LOW",
    "PPO_UPDATES_PER_ARM",
    "SLOTS_PER_UPDATE",
    "clip_combined_global_gradient",
    "duration_correct_gae",
    "freeze_update_batch",
    "joint_ppo_loss",
    "joint_ppo_loss_from_terms",
    "normalize_population_advantage",
    "registered_minibatch_plan",
    "split_four_near_equal",
    "training_contract",
]
