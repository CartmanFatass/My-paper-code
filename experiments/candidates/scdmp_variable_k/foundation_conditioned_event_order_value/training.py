"""Schedule-independent fixed-13 PPO/GAE/AdamW structure for FCEOV.

This module exposes the exact algebra and resume state.  It deliberately has
no rollout driver, result branch, seed selection, retry, or training CLI.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence

import torch
from torch import Tensor

from .contracts import (
    EPISODES_PER_UPDATE,
    FOUNDATION_UPDATES,
    GRAPHS,
    HORIZON_TICKS,
    K_TARGET,
    RESOURCE_MAXIMA,
    validate_resource_request,
)
from .rng import AddressRNG


GAMMA = 0.995
GAE_LAMBDA = 0.93
POLICY_CLIP_LOW = 0.80
POLICY_CLIP_HIGH = 1.20
VALUE_COEFFICIENT = 0.50
ENTROPY_COEFFICIENT = 0.010
GLOBAL_GRADIENT_CLIP = 0.8
ADAMW_BETA1 = 0.9
ADAMW_BETA2 = 0.999
ADAMW_EPSILON = 1e-8
ADAMW_LR = 3e-4
ADAMW_WEIGHT_DECAY = 1e-5
EPOCHS_PER_UPDATE = 3
MINIBATCHES_PER_EPOCH = 4
OPTIMIZER_STEPS_PER_UPDATE = 12
TRAINING_INITIAL_DOMAIN = "foundation-training-initial-state"
TRAINING_DISTURBANCE_DOMAIN = "foundation-training-disturbance"
TRAINING_ACTION_DOMAIN = "foundation-training-categorical"
TRAINING_MINIBATCH_DOMAIN = "foundation-minibatch"
DISTURBANCE_MAGNITUDES = {
    "eta_v": 0.003,
    "eta_y": 0.002,
    "eta_omega": 0.004,
}


class TrainingContractError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class EpisodeSlot:
    update: int
    episode: int
    graph: str
    q: int
    k: int = K_TARGET

    @property
    def pair(self) -> int:
        return self.episode // 2

    @property
    def initialization_address(self) -> tuple[int, int]:
        return (self.update, self.pair)

    @property
    def disturbance_address_prefix(self) -> tuple[int, int]:
        return (self.update, self.pair)

    def action_address(self, renewal: int) -> tuple[int, int, int]:
        if isinstance(renewal, bool) or not isinstance(renewal, int) or not 0 <= renewal < 28:
            raise TrainingContractError("training renewal address must lie in [0,28)")
        return (self.update, self.episode, renewal)


def build_training_plan() -> tuple[EpisodeSlot, ...]:
    """Return all 1,920 fixed-13 episode slots in frozen call order."""

    return tuple(
        EpisodeSlot(update, episode, GRAPHS[episode % 2], 1 if episode % 2 == 0 else 0)
        for update in range(1, FOUNDATION_UPDATES + 1)
        for episode in range(EPISODES_PER_UPDATE)
    )


def initial_public_draws(uniforms: Sequence[float]) -> tuple[float, float, float]:
    """Prospectively completed independent-product initialization transform."""

    raw = tuple(uniforms)
    if len(raw) != 3 or any(
        isinstance(value, bool) or not isinstance(value, (int, float)) for value in raw
    ):
        raise TrainingContractError("foundation initialization requires three real U[0,1) values")
    values = tuple(float(value) for value in raw)
    if any(not math.isfinite(value) or not 0 <= value < 1 for value in values):
        raise TrainingContractError("foundation initialization requires three U[0,1) values")
    return (0.03 * values[0], 0.02 * values[1] - 0.01, 0.02 * values[2] - 0.01)


def _validate_episode_slot(slot: EpisodeSlot) -> None:
    if not isinstance(slot, EpisodeSlot):
        raise TrainingContractError("training address requires an EpisodeSlot")
    if (
        isinstance(slot.update, bool)
        or not isinstance(slot.update, int)
        or isinstance(slot.episode, bool)
        or not isinstance(slot.episode, int)
        or not 1 <= slot.update <= FOUNDATION_UPDATES
        or not 0 <= slot.episode < EPISODES_PER_UPDATE
    ):
        raise TrainingContractError("training episode address is outside the fixed plan")
    expected_graph = GRAPHS[slot.episode % 2]
    expected_q = 1 if slot.episode % 2 == 0 else 0
    if slot.graph != expected_graph or slot.q != expected_q or slot.k != K_TARGET:
        raise TrainingContractError("training episode differs from the fixed balanced plan")


def training_initial_draws(source: AddressRNG, slot: EpisodeSlot) -> tuple[float, float, float]:
    _validate_episode_slot(slot)
    if not isinstance(source, AddressRNG):
        raise TypeError("training initial state requires the addressed FCEOV RNG")
    return initial_public_draws(
        tuple(
            source.uniform53(TRAINING_INITIAL_DOMAIN, slot.initialization_address + (component,))
            for component in ("v", "y", "phi")
        )
    )


def training_disturbance(
    source: AddressRNG,
    slot: EpisodeSlot,
    *,
    tick: int,
    component: str,
) -> float:
    _validate_episode_slot(slot)
    if not isinstance(source, AddressRNG):
        raise TypeError("training disturbance requires the addressed FCEOV RNG")
    if isinstance(tick, bool) or not isinstance(tick, int) or not 0 <= tick < HORIZON_TICKS:
        raise TrainingContractError("training disturbance tick is outside the horizon")
    if component not in DISTURBANCE_MAGNITUDES:
        raise TrainingContractError("training disturbance component differs")
    magnitude = DISTURBANCE_MAGNITUDES[component]
    address = slot.disturbance_address_prefix + (tick, component)
    return magnitude if source.bernoulli(0.5, domain=TRAINING_DISTURBANCE_DOMAIN, address=address) else -magnitude


def training_action_uniform(source: AddressRNG, slot: EpisodeSlot, *, renewal: int) -> float:
    _validate_episode_slot(slot)
    if not isinstance(source, AddressRNG):
        raise TypeError("training action requires the addressed FCEOV RNG")
    return source.uniform24(TRAINING_ACTION_DOMAIN, slot.action_address(renewal))


def validate_training_rng_contract() -> dict[str, int]:
    plan = build_training_plan()
    initialization = tuple(row.initialization_address for row in plan)
    disturbances = tuple(row.disturbance_address_prefix for row in plan)
    actions = tuple((row.update, row.episode) for row in plan)
    for update in range(1, FOUNDATION_UPDATES + 1):
        rows = plan[(update - 1) * EPISODES_PER_UPDATE : update * EPISODES_PER_UPDATE]
        for left, right in zip(rows[::2], rows[1::2]):
            if (
                (left.graph, right.graph) != ("HR", "RH")
                or left.initialization_address != right.initialization_address
                or left.disturbance_address_prefix != right.disturbance_address_prefix
            ):
                raise RuntimeError("training HR/RH prospective pairing differs")
    domains = {
        "foundation-initialization",
        TRAINING_INITIAL_DOMAIN,
        TRAINING_DISTURBANCE_DOMAIN,
        TRAINING_ACTION_DOMAIN,
        TRAINING_MINIBATCH_DOMAIN,
        "foundation-competence-initialization",
        "foundation-competence-disturbance",
        "assay-disturbance",
    }
    if len(domains) != 8:
        raise RuntimeError("FCEOV RNG namespaces are not disjoint")
    if len(set(initialization)) != FOUNDATION_UPDATES * 6:
        raise RuntimeError("training initial-state pair inventory differs")
    if len(set(disturbances)) != FOUNDATION_UPDATES * 6 or len(set(actions)) != len(plan):
        raise RuntimeError("training RNG address inventory differs")
    return {
        "paired_initial_state_prefixes": len(set(initialization)),
        "paired_disturbance_prefixes": len(set(disturbances)),
        "episode_action_prefixes": len(set(actions)),
        "domains": len(domains),
    }


def summarize_resource_usage() -> dict[str, int]:
    """Return the exact maximum registered end-to-end inventory."""

    value = dict(RESOURCE_MAXIMA)
    validate_resource_request(value)
    if value["foundation_queries"] != (
        1_920 * 28 + 120 * 28 + 144 * 27
    ):
        raise RuntimeError("foundation-query ceiling decomposition differs")
    return value


@dataclass(frozen=True, slots=True)
class GAETargets:
    discounted_rewards: Tensor
    deltas: Tensor
    raw_advantages: Tensor
    value_targets: Tensor
    normalized_advantages: Tensor


def duration_correct_gae(
    primitive_rewards: Sequence[Sequence[float]],
    old_values: Tensor,
    nonterminal: Tensor,
    *,
    episode_offsets: Sequence[int],
) -> GAETargets:
    count = len(primitive_rewards)
    if count < 1 or old_values.dtype != torch.float32 or old_values.shape != (count,):
        raise TrainingContractError("old values must be a nonempty float32 record vector")
    if nonterminal.dtype != torch.bool or nonterminal.shape != (count,):
        raise TrainingContractError("nonterminal mask must match renewal records")
    if not bool(torch.isfinite(old_values).all()):
        raise TrainingContractError("old values must be finite")
    if old_values.requires_grad:
        raise TrainingContractError("old values must be a detached rollout snapshot")
    if any(
        not isinstance(row, Sequence)
        or len(row) < 1
        or len(row) > K_TARGET
        or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            for value in row
        )
        for row in primitive_rewards
    ):
        raise TrainingContractError("each record duration must be in [1,13]")
    delimiters = tuple(episode_offsets)
    if (
        len(delimiters) != EPISODES_PER_UPDATE + 1
        or delimiters[0] != 0
        or delimiters[-1] != count
        or any(isinstance(item, bool) or not isinstance(item, int) for item in delimiters)
        or any(left >= right for left, right in zip(delimiters, delimiters[1:]))
    ):
        raise TrainingContractError("episode offsets must be 13 strict delimiters from zero through record count")
    offsets = delimiters[:-1]
    ends = delimiters[1:]
    if any(bool(nonterminal[end - 1]) for end in ends):
        raise TrainingContractError("every complete episode must end with nonterminal=False")
    if any(not bool(nonterminal[index]) for start, end in zip(offsets, ends) for index in range(start, end - 1)):
        raise TrainingContractError("only the final record of a complete episode may be terminal")
    rewards = torch.empty(count, dtype=torch.float32)
    deltas = torch.empty(count, dtype=torch.float32)
    advantages = torch.empty(count, dtype=torch.float32)
    gamma = torch.tensor(GAMMA, dtype=torch.float32)
    for start, end in zip(offsets, ends):
        next_advantage = torch.tensor(0.0, dtype=torch.float32)
        for index in range(end - 1, start - 1, -1):
            row = torch.tensor(tuple(primitive_rewards[index]), dtype=torch.float32)
            duration = len(row)
            rewards[index] = torch.sum(
                torch.pow(gamma, torch.arange(duration, dtype=torch.float32)) * row
            )
            bootstrap = (
                old_values[index + 1]
                if index + 1 < end
                else torch.tensor(0.0, dtype=torch.float32)
            )
            keep = nonterminal[index].to(torch.float32)
            deltas[index] = (
                rewards[index]
                + keep * (GAMMA ** duration) * bootstrap
                - old_values[index]
            )
            advantages[index] = (
                deltas[index]
                + keep * ((GAMMA * GAE_LAMBDA) ** duration) * next_advantage
            )
            next_advantage = advantages[index]
    targets = (advantages + old_values).detach()
    centered = advantages - advantages.mean()
    normalized = (centered / torch.sqrt(torch.mean(centered.square()) + 1e-8)).detach()
    return GAETargets(rewards.detach(), deltas.detach(), advantages.detach(), targets, normalized)


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
        return gradient * ((value > ctx.lower) & (value < ctx.upper)).to(gradient.dtype), None, None


def strict_clip(value: Tensor, lower: float, upper: float) -> Tensor:
    return _StrictClip.apply(value, lower, upper)


def tie_mean_min(left: Tensor, right: Tensor) -> Tensor:
    if left.shape != right.shape:
        raise TrainingContractError("PPO operands differ in shape")
    return torch.where(left < right, left, torch.where(right < left, right, 0.5 * (left + right)))


@dataclass(frozen=True, slots=True)
class JointLoss:
    total: Tensor
    policy: Tensor
    value: Tensor
    entropy: Tensor


def joint_ppo_loss(
    *,
    current_log_probability: Tensor,
    current_value: Tensor,
    current_entropy: Tensor,
    old_log_probability: Tensor,
    value_target: Tensor,
    normalized_advantage: Tensor,
) -> JointLoss:
    rows = (current_log_probability, current_value, current_entropy, old_log_probability, value_target, normalized_advantage)
    if (
        len({tuple(row.shape) for row in rows}) != 1
        or current_log_probability.ndim != 1
        or current_log_probability.numel() == 0
        or any(row.dtype != torch.float32 for row in rows)
        or any(row.requires_grad for row in (old_log_probability, value_target, normalized_advantage))
    ):
        raise TrainingContractError("PPO terms must share one finite float32 vector shape")
    if any(not bool(torch.isfinite(row).all()) for row in rows):
        raise TrainingContractError("PPO term is nonfinite")
    ratio = torch.exp(current_log_probability - old_log_probability)
    unclipped = ratio * normalized_advantage
    clipped = strict_clip(ratio, POLICY_CLIP_LOW, POLICY_CLIP_HIGH) * normalized_advantage
    policy = -tie_mean_min(unclipped, clipped).mean()
    value = 0.5 * torch.mean((current_value - value_target).square())
    entropy = current_entropy.mean()
    return JointLoss(policy + VALUE_COEFFICIENT * value - ENTROPY_COEFFICIENT * entropy, policy, value, entropy)


def split_four_near_equal(permutation: Sequence[int]) -> tuple[tuple[int, ...], ...]:
    values = tuple(permutation)
    if len(values) < 4 or tuple(sorted(values)) != tuple(range(len(values))):
        raise TrainingContractError("minibatching requires a full permutation of at least four records")
    quotient, remainder = divmod(len(values), 4)
    sizes = tuple(quotient + int(index < remainder) for index in range(4))
    result: list[tuple[int, ...]] = []
    start = 0
    for size in sizes:
        result.append(values[start : start + size])
        start += size
    return tuple(result)


def three_epoch_minibatches(
    permutations: Sequence[Sequence[int]],
) -> tuple[tuple[tuple[int, ...], ...], ...]:
    rows = tuple(tuple(item) for item in permutations)
    if len(rows) != EPOCHS_PER_UPDATE or len(set(rows)) != EPOCHS_PER_UPDATE:
        raise TrainingContractError("each update requires three distinct epoch permutations")
    return tuple(split_four_near_equal(row) for row in rows)


def strict_inverse_cdf(probabilities: Tensor, uniforms: Tensor) -> Tensor:
    """One fresh uniform per row; exact CDF contact advances to the next action."""

    if probabilities.dtype != torch.float32 or probabilities.ndim != 2 or probabilities.shape[1] != 18:
        raise TrainingContractError("categorical probabilities must be float32 [batch,18]")
    if uniforms.dtype != torch.float32 or uniforms.shape != probabilities.shape[:1]:
        raise TrainingContractError("one float32 uniform is required per categorical row")
    if not bool(torch.isfinite(probabilities).all()) or not bool(torch.isfinite(uniforms).all()):
        raise TrainingContractError("categorical inputs must be finite")
    if bool(torch.any(probabilities < 0)) or not bool(torch.allclose(
        probabilities.sum(dim=1), torch.ones(probabilities.shape[0], dtype=torch.float32), atol=1e-6, rtol=0.0
    )):
        raise TrainingContractError("categorical rows must be nonnegative and sum to one")
    if bool(torch.any(uniforms < 0)) or bool(torch.any(uniforms >= 1)):
        raise TrainingContractError("categorical uniforms must lie in [0,1)")
    eligible = probabilities.cumsum(dim=1) > uniforms.unsqueeze(1)
    if not bool(eligible.any(dim=1).all()):
        raise TrainingContractError("categorical row has no strict inverse-CDF selection")
    return eligible.to(torch.int64).argmax(dim=1)


def sample_actions_from_logits(logits: Tensor, uniforms: Tensor) -> Tensor:
    if logits.dtype != torch.float32 or logits.ndim != 2 or logits.shape[1] != 18:
        raise TrainingContractError("categorical logits must be float32 [batch,18]")
    if not bool(torch.isfinite(logits).all()):
        raise TrainingContractError("categorical logits must be finite")
    return strict_inverse_cdf(torch.softmax(logits, dim=1), uniforms)


def sample_training_actions(
    logits: Tensor,
    source: AddressRNG,
    slots: Sequence[EpisodeSlot],
    renewal_indices: Sequence[int],
) -> Tensor:
    rows = tuple(slots)
    renewals = tuple(renewal_indices)
    if len(rows) != logits.shape[0] or len(renewals) != logits.shape[0]:
        raise TrainingContractError("one addressed action uniform is required per policy query")
    uniforms = torch.tensor(
        tuple(
            training_action_uniform(source, slot, renewal=renewal)
            for slot, renewal in zip(rows, renewals)
        ),
        dtype=torch.float32,
        device=logits.device,
    )
    return sample_actions_from_logits(logits, uniforms)


def epoch_keyed_minibatches(source: object, *, update: int, record_count: int):
    if isinstance(update, bool) or not isinstance(update, int) or not 1 <= update <= FOUNDATION_UPDATES:
        raise TrainingContractError("minibatch update is outside the foundation schedule")
    if isinstance(record_count, bool) or not isinstance(record_count, int) or record_count < 4:
        raise TrainingContractError("minibatch record count must be at least four")
    method = getattr(source, "permutation", None)
    if not callable(method):
        raise TypeError("epoch minibatches require an address-keyed permutation source")
    permutations = tuple(
        tuple(method(record_count, domain=TRAINING_MINIBATCH_DOMAIN, address=(update, epoch)))
        for epoch in range(EPOCHS_PER_UPDATE)
    )
    return three_epoch_minibatches(permutations)


def clip_global_gradient(parameters: Sequence[Tensor]) -> tuple[float, float]:
    gradients = tuple(value.grad for value in parameters)
    if not gradients or any(value is None for value in gradients):
        raise TrainingContractError("every trainable parameter requires one gradient")
    typed = tuple(value for value in gradients if value is not None)
    if any(not bool(torch.isfinite(value).all()) for value in typed):
        raise TrainingContractError("combined gradient is nonfinite")
    norm_tensor = torch.sqrt(sum(torch.sum(value.square()) for value in typed))
    if not bool(torch.isfinite(norm_tensor)):
        raise TrainingContractError("combined gradient is nonfinite")
    norm = float(norm_tensor)
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
    def __init__(self, named_parameters: Sequence[tuple[str, Tensor]]) -> None:
        self._rows = tuple(named_parameters)
        names = tuple(name for name, _ in self._rows)
        parameters = tuple(value for _, value in self._rows)
        if (
            not self._rows
            or len(set(names)) != len(names)
            or len({id(value) for value in parameters}) != len(parameters)
            or any(not isinstance(name, str) or not name for name in names)
            or any(
                not isinstance(value, Tensor)
                or value.dtype != torch.float32
                or not bool(torch.isfinite(value).all())
                for _, value in self._rows
            )
        ):
            raise TrainingContractError("AdamW requires named float32 parameters")
        self.first = [torch.zeros_like(value) for _, value in self._rows]
        self.second = [torch.zeros_like(value) for _, value in self._rows]
        self.step_index = 0

    @property
    def parameters(self) -> tuple[Tensor, ...]:
        return tuple(value for _, value in self._rows)

    def matches_named_parameters(self, rows: Sequence[tuple[str, Tensor]]) -> bool:
        values = tuple(rows)
        return (
            tuple(name for name, _ in values) == tuple(name for name, _ in self._rows)
            and tuple(id(value) for _, value in values) == tuple(id(value) for _, value in self._rows)
        )

    @torch.no_grad()
    def step(self) -> None:
        if self.step_index >= 1_920:
            raise TrainingContractError("AdamW step exceeds the foundation budget")
        step = self.step_index + 1
        gradients = tuple(parameter.grad for _, parameter in self._rows)
        if any(gradient is None or not bool(torch.isfinite(gradient).all()) for gradient in gradients):
            raise TrainingContractError("AdamW gradient is absent or nonfinite")
        candidate_first = []
        candidate_second = []
        candidate_parameters = []
        for (_, parameter), first, second, gradient in zip(self._rows, self.first, self.second, gradients):
            assert gradient is not None
            old = parameter.detach().clone()
            # Preserve the allowlisted in-place float32 operation order on
            # clones, then commit only after every candidate is valid.
            next_first = first.detach().clone()
            next_first.mul_(ADAMW_BETA1).add_(gradient, alpha=1.0 - ADAMW_BETA1)
            next_second = second.detach().clone()
            next_second.mul_(ADAMW_BETA2).addcmul_(
                gradient, gradient, value=1.0 - ADAMW_BETA2
            )
            first_hat = next_first / (1.0 - ADAMW_BETA1**step)
            second_hat = next_second / (1.0 - ADAMW_BETA2**step)
            next_parameter = old - ADAMW_LR * (first_hat / (torch.sqrt(second_hat) + ADAMW_EPSILON) + ADAMW_WEIGHT_DECAY * old)
            if not all(bool(torch.isfinite(value).all()) for value in (next_first, next_second, next_parameter)):
                raise TrainingContractError("AdamW candidate state is nonfinite")
            candidate_first.append(next_first)
            candidate_second.append(next_second)
            candidate_parameters.append(next_parameter)
        for target, source in zip(self.first, candidate_first):
            target.copy_(source)
        for target, source in zip(self.second, candidate_second):
            target.copy_(source)
        for parameter, source in zip(self.parameters, candidate_parameters):
            parameter.copy_(source)
        self.step_index = step

    def snapshot(self) -> OptimizerSnapshot:
        return OptimizerSnapshot(
            self.step_index,
            tuple(name for name, _ in self._rows),
            tuple(value.detach().clone() for value in self.first),
            tuple(value.detach().clone() for value in self.second),
        )

    def validate_snapshot(self, snapshot: OptimizerSnapshot) -> None:
        """Validate the complete direct optimizer state without mutation."""

        names = tuple(name for name, _ in self._rows)
        if (
            not isinstance(snapshot, OptimizerSnapshot)
            or isinstance(snapshot.step, bool)
            or not isinstance(snapshot.step, int)
            or snapshot.names != names
            or len(set(snapshot.names)) != len(snapshot.names)
            or not 0 <= snapshot.step <= 1_920
        ):
            raise TrainingContractError("optimizer resume structure differs")
        if len(snapshot.first) != len(self.first) or len(snapshot.second) != len(self.second):
            raise TrainingContractError("optimizer resume tensor count differs")
        moments = snapshot.first + snapshot.second
        if len({id(value) for value in moments}) != len(moments):
            raise TrainingContractError("optimizer resume tensors must be direct nonaliased state")
        for source, parameter in zip(snapshot.first, self.parameters):
            if (
                not isinstance(source, Tensor)
                or source.dtype != torch.float32
                or source.shape != parameter.shape
                or not bool(torch.isfinite(source).all())
            ):
                raise TrainingContractError("optimizer first-moment resume tensor differs")
        for source, parameter in zip(snapshot.second, self.parameters):
            if (
                not isinstance(source, Tensor)
                or source.dtype != torch.float32
                or source.shape != parameter.shape
                or not bool(torch.isfinite(source).all())
            ):
                raise TrainingContractError("optimizer second-moment resume tensor differs")
            if bool(torch.any(source < 0.0)):
                raise TrainingContractError("optimizer second moment must be nonnegative")

    @torch.no_grad()
    def restore(self, snapshot: OptimizerSnapshot) -> None:
        self.validate_snapshot(snapshot)
        for source, target in zip(snapshot.first, self.first):
            target.copy_(source)
        for source, target in zip(snapshot.second, self.second):
            target.copy_(source)
        self.step_index = snapshot.step


PLAN = build_training_plan()
if len(PLAN) != 1_920:
    raise RuntimeError("foundation episode plan differs")
for update in range(1, 161):
    rows = PLAN[(update - 1) * 12 : update * 12]
    if sum(row.graph == "HR" for row in rows) != 6 or sum(row.graph == "RH" for row in rows) != 6:
        raise RuntimeError("foundation graph balance differs")
    if any(row.k != 13 for row in rows):
        raise RuntimeError("foundation training is not fixed-13")


__all__ = [
    "ADAMW_LR", "EpisodeSlot", "ExactAdamW", "GAETargets", "GAMMA", "GAE_LAMBDA",
    "JointLoss", "OptimizerSnapshot", "TrainingContractError", "build_training_plan",
    "clip_global_gradient", "duration_correct_gae", "epoch_keyed_minibatches", "initial_public_draws",
    "joint_ppo_loss", "sample_actions_from_logits", "sample_training_actions",
    "split_four_near_equal", "strict_clip", "training_action_uniform", "training_disturbance",
    "training_initial_draws", "validate_training_rng_contract",
    "strict_inverse_cdf", "summarize_resource_usage",
    "three_epoch_minibatches", "tie_mean_min",
]
