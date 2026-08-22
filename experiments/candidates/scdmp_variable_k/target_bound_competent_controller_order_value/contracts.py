"""Static, fixture-only contracts for the TBCC revision-02 controller package.

This module deliberately contains no trainable module, checkpoint loader, random
master, environment, or rollout loop.  Tensor helpers operate only on caller-
provided deterministic TEST fixtures.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from typing import Final, Iterable, Sequence

import torch


class ContractError(ValueError):
    """A static TBCC contract was violated."""


OBSERVATION_WIDTH: Final[int] = 18
ACTION_COUNT: Final[int] = 18
FOUNDATION_HIDDEN_WIDTH: Final[int] = 96
ORDER_SCALE_HIDDEN_WIDTH: Final[int] = 32
ORDER_CRITIC_HIDDEN_WIDTH: Final[int] = 64
RESIDUAL_HIDDEN_WIDTH: Final[int] = 64
FOUNDATION_ACTOR_PARAMETER_COUNT: Final[int] = 12_882
FOUNDATION_CRITIC_PARAMETER_COUNT: Final[int] = 11_233
FOUNDATION_PARAMETER_COUNT: Final[int] = 24_115
TREAT_SCALE_PARAMETER_COUNT: Final[int] = 641
ORDER_CRITIC_PARAMETER_COUNT: Final[int] = 5_505
FREE_RESIDUAL_PARAMETER_COUNT: Final[int] = 6_610
TREAT_TRAINABLE_PARAMETER_COUNT: Final[int] = 6_146
FREE_TRAINABLE_PARAMETER_COUNT: Final[int] = 12_756
SET_TRAINABLE_PARAMETER_COUNT: Final[int] = 12_756
K_TRAIN: Final[tuple[int, int]] = (5, 11)
K_TARGET: Final[tuple[object, ...]] = (7, 13, (7, 13), (13, 7))
GAMMA: Final[float] = 0.995
GAE_LAMBDA: Final[float] = 0.93
GRADIENT_NORM_LIMIT: Final[float] = 0.8


@dataclass(frozen=True)
class AffineShape:
    name: str
    input_width: int
    output_width: int

    @property
    def parameter_count(self) -> int:
        return self.input_width * self.output_width + self.output_width


FOUNDATION_ACTOR_SHAPES: Final[tuple[AffineShape, ...]] = (
    AffineShape("actor.input", 18, 96),
    AffineShape("actor.hidden", 96, 96),
    AffineShape("actor.output", 96, 18),
)
FOUNDATION_CRITIC_SHAPES: Final[tuple[AffineShape, ...]] = (
    AffineShape("critic.input", 18, 96),
    AffineShape("critic.hidden", 96, 96),
    AffineShape("critic.output", 96, 1),
)


@dataclass(frozen=True)
class TensorInitialization:
    """One static tensor initialization witness; it allocates no parameter."""

    name: str
    shape: tuple[int, ...]
    law: str
    gain: float = 1.0
    constant: float | None = None

    @property
    def element_count(self) -> int:
        return math.prod(self.shape)


def initialization_schema() -> tuple[TensorInitialization, ...]:
    """Exact revision-02 initialization law for all frozen module schemas.

    Matrix shapes are ``(output_width,input_width)`` and therefore bind the
    row-major Xavier stream without constructing a controller instance.
    """

    rows: list[TensorInitialization] = []

    def affine(prefix: str, input_width: int, output_width: int, *, output: str = "global") -> None:
        if output == "scale":
            rows.append(TensorInitialization(f"{prefix}.weight", (output_width, input_width), "constant", constant=0.0))
            rows.append(TensorInitialization(f"{prefix}.bias", (output_width,), "constant", constant=0.001))
        elif output == "residual":
            rows.append(TensorInitialization(f"{prefix}.weight", (output_width, input_width), "constant", constant=0.0))
            rows.append(TensorInitialization(f"{prefix}.bias", (output_width,), "constant", constant=0.0))
        else:
            rows.append(TensorInitialization(f"{prefix}.weight", (output_width, input_width), "row_major_xavier_uniform", gain=1.0))
            rows.append(TensorInitialization(f"{prefix}.bias", (output_width,), "constant", constant=0.0))

    for name, input_width, output_width in (
        ("foundation.actor.input", 18, 96),
        ("foundation.actor.hidden", 96, 96),
        ("foundation.actor.output", 96, 18),
        ("foundation.critic.input", 18, 96),
        ("foundation.critic.hidden", 96, 96),
        ("foundation.critic.output", 96, 1),
        ("order.scale.hidden", 18, 32),
    ):
        affine(name, input_width, output_width)
    affine("order.scale.output", 32, 1, output="scale")
    for name, input_width, output_width in (
        ("order.critic.input", 19, 64),
        ("order.critic.hidden", 64, 64),
        ("order.critic.output", 64, 1),
        ("free.residual.input", 19, 64),
        ("free.residual.hidden", 64, 64),
    ):
        affine(name, input_width, output_width)
    affine("free.residual.output", 64, 18, output="residual")
    for name, input_width, output_width in (
        ("set.residual.input", 19, 64),
        ("set.residual.hidden", 64, 64),
    ):
        affine(name, input_width, output_width)
    affine("set.residual.output", 64, 18, output="residual")
    return tuple(rows)


def row_major_xavier_uniform_from_test_uniforms(
    uniforms: Sequence[float], *, input_width: int, output_width: int
) -> torch.Tensor:
    """Map deterministic TEST uniforms to gain-1 Xavier in row-major order."""

    if input_width < 1 or output_width < 1:
        raise ContractError("Xavier widths must be positive")
    if len(uniforms) != input_width * output_width:
        raise ContractError("Xavier TEST uniform count differs from matrix shape")
    values = torch.tensor(tuple(uniforms), dtype=torch.float32)
    if not torch.isfinite(values).all() or torch.any(values < 0.0) or torch.any(values >= 1.0):
        raise ContractError("Xavier TEST uniforms must lie in [0,1)")
    bound = torch.tensor(math.sqrt(6.0 / (input_width + output_width)), dtype=torch.float32)
    return ((2.0 * values - 1.0) * bound).reshape(output_width, input_width).contiguous()


def validate_foundation_schema() -> dict[str, object]:
    """Return the exact architecture without allocating any parameters."""

    actor_count = sum(item.parameter_count for item in FOUNDATION_ACTOR_SHAPES)
    critic_count = sum(item.parameter_count for item in FOUNDATION_CRITIC_SHAPES)
    if actor_count != FOUNDATION_ACTOR_PARAMETER_COUNT:
        raise ContractError("foundation actor parameter count differs")
    if critic_count != FOUNDATION_CRITIC_PARAMETER_COUNT:
        raise ContractError("foundation critic parameter count differs")
    return {
        "observation_width": OBSERVATION_WIDTH,
        "action_count": ACTION_COUNT,
        "actor_affines": FOUNDATION_ACTOR_SHAPES,
        "critic_affines": FOUNDATION_CRITIC_SHAPES,
        "activation": "SiLU",
        "actor_parameters": actor_count,
        "critic_parameters": critic_count,
        "total_parameters": actor_count + critic_count,
        "chronology_input": False,
        "graph_mode_input": False,
        "dtype": "float32",
    }


@dataclass(frozen=True)
class SharedParameterizationContract:
    parameterization_id: str
    train_k: tuple[int, ...]
    target_schedules: tuple[object, ...]
    per_k_heads: int = 0
    per_k_optimizers: int = 0
    per_k_checkpoints: int = 0
    switch_resets: bool = False

    def validate(self) -> None:
        if not self.parameterization_id:
            raise ContractError("one nonempty parameterization identifier is required")
        if self.train_k != K_TRAIN or self.target_schedules != K_TARGET:
            raise ContractError("external-k registry differs from revision 02")
        if any((self.per_k_heads, self.per_k_optimizers, self.per_k_checkpoints)):
            raise ContractError("per-k specialization is forbidden")
        if self.switch_resets:
            raise ContractError("external-k switch cannot reset controller state")


def inverse_cdf_index(probabilities: torch.Tensor, uniforms: torch.Tensor) -> torch.Tensor:
    """Strict-boundary inverse CDF in the supplied lexicographic order.

    Exact boundary contact advances to the next action because selection is the
    first cumulative mass *strictly greater* than ``u``.
    """

    if probabilities.dtype != torch.float32 or uniforms.dtype != torch.float32:
        raise ContractError("inverse-CDF TEST tensors must be float32")
    if probabilities.ndim != 2 or probabilities.shape[1] != ACTION_COUNT:
        raise ContractError("probabilities must have shape [batch,18]")
    if uniforms.shape != probabilities.shape[:1]:
        raise ContractError("one uniform is required per probability row")
    if not torch.isfinite(probabilities).all() or not torch.isfinite(uniforms).all():
        raise ContractError("inverse-CDF inputs must be finite")
    if torch.any(probabilities < 0):
        raise ContractError("categorical probabilities must be nonnegative")
    if not torch.allclose(
        probabilities.sum(dim=1),
        torch.ones(probabilities.shape[0], dtype=torch.float32),
        atol=1e-6,
        rtol=0.0,
    ):
        raise ContractError("categorical rows must sum to one")
    if torch.any(uniforms < 0) or torch.any(uniforms >= 1):
        raise ContractError("uniforms must lie in [0,1)")
    cumulative = probabilities.cumsum(dim=1)
    eligible = cumulative > uniforms.unsqueeze(1)
    if not eligible.any(dim=1).all():
        raise ContractError("categorical row has no strict inverse-CDF selection")
    return eligible.to(torch.int64).argmax(dim=1)


@dataclass(frozen=True)
class DurationTargets:
    discounted_rewards: torch.Tensor
    deltas: torch.Tensor
    raw_advantages: torch.Tensor
    value_targets: torch.Tensor
    normalized_advantages: torch.Tensor


def duration_correct_targets(
    primitive_rewards: Sequence[Sequence[float]],
    old_values: torch.Tensor,
    nonterminal: torch.Tensor,
) -> DurationTargets:
    """Compute the frozen duration-correct return/GAE law on TEST records."""

    count = len(primitive_rewards)
    if old_values.dtype != torch.float32 or old_values.shape != (count,):
        raise ContractError("old_values must be a float32 vector matching records")
    if nonterminal.dtype != torch.bool or nonterminal.shape != (count,):
        raise ContractError("nonterminal must be a bool vector matching records")
    if count == 0 or any(len(row) == 0 for row in primitive_rewards):
        raise ContractError("every renewal record requires positive duration")
    if not torch.isfinite(old_values).all():
        raise ContractError("old values must be finite")

    rewards = torch.empty(count, dtype=torch.float32)
    deltas = torch.empty(count, dtype=torch.float32)
    advantages = torch.empty(count, dtype=torch.float32)
    next_advantage = torch.tensor(0.0, dtype=torch.float32)
    for index in range(count - 1, -1, -1):
        row = torch.tensor(tuple(primitive_rewards[index]), dtype=torch.float32)
        if not torch.isfinite(row).all():
            raise ContractError("primitive rewards must be finite")
        duration = row.numel()
        discounts = torch.pow(
            torch.tensor(GAMMA, dtype=torch.float32),
            torch.arange(duration, dtype=torch.float32),
        )
        rewards[index] = torch.sum(discounts * row)
        bootstrap = old_values[index + 1] if index + 1 < count else torch.tensor(0.0)
        continuation = nonterminal[index].to(torch.float32)
        deltas[index] = (
            rewards[index]
            + continuation * (GAMMA**duration) * bootstrap
            - old_values[index]
        )
        advantages[index] = deltas[index] + continuation * (
            (GAMMA * GAE_LAMBDA) ** duration
        ) * next_advantage
        next_advantage = advantages[index]
    targets = advantages + old_values
    centered = advantages - advantages.mean()
    normalized = centered / torch.sqrt(torch.mean(centered * centered) + 1e-8)
    return DurationTargets(
        *(tensor.detach() for tensor in (rewards, deltas, advantages, targets, normalized))
    )


def _keyed_uint(key: str, counter: int) -> int:
    payload = f"TEST_ONLY_TBCC_FISHER_YATES|{key}|{counter}".encode("ascii")
    return int.from_bytes(hashlib.sha256(payload).digest(), "big")


def keyed_fisher_yates(count: int, *, key: str) -> tuple[int, ...]:
    """Deterministic TEST-only keyed Fisher-Yates permutation."""

    if isinstance(count, bool) or count < 1:
        raise ContractError("permutation count must be positive")
    if not key.startswith("TEST_ONLY:"):
        raise ContractError("fixture permutation key must be explicitly TEST-only")
    values = list(range(count))
    counter = 0
    for upper in range(count - 1, 0, -1):
        swap = _keyed_uint(key, counter) % (upper + 1)
        values[upper], values[swap] = values[swap], values[upper]
        counter += 1
    return tuple(values)


def three_epoch_permutations(
    count: int, *, replicate: int, arm: str, update: int
) -> tuple[tuple[int, ...], ...]:
    keys = tuple(
        f"TEST_ONLY:{replicate}:{arm}:{update}:{epoch}" for epoch in range(3)
    )
    values = tuple(keyed_fisher_yates(count, key=key) for key in keys)
    if len(set(values)) != 3:
        # This is a contract, not a retry or stochastic search.
        raise ContractError("the three registered epoch permutations must be distinct")
    return values


def four_minibatches(permutation: Sequence[int]) -> tuple[tuple[int, ...], ...]:
    count = len(permutation)
    if count < 4 or sorted(permutation) != list(range(count)):
        raise ContractError("minibatching requires a full permutation of at least four IDs")
    quotient, remainder = divmod(count, 4)
    sizes = tuple(quotient + (index < remainder) for index in range(4))
    result: list[tuple[int, ...]] = []
    start = 0
    for size in sizes:
        result.append(tuple(permutation[start : start + size]))
        start += size
    return tuple(result)


class _StrictClip(torch.autograd.Function):
    @staticmethod
    def forward(ctx, value: torch.Tensor, lower: float, upper: float) -> torch.Tensor:
        ctx.save_for_backward(value)
        ctx.lower = lower
        ctx.upper = upper
        return torch.clamp(value, lower, upper)

    @staticmethod
    def backward(ctx, gradient: torch.Tensor):
        (value,) = ctx.saved_tensors
        inside = (value > ctx.lower) & (value < ctx.upper)
        return gradient * inside.to(gradient.dtype), None, None


def strict_clip(value: torch.Tensor, lower: float, upper: float) -> torch.Tensor:
    if not lower < upper:
        raise ContractError("clip lower bound must precede upper bound")
    return _StrictClip.apply(value, float(lower), float(upper))


def ppo_tie_mean_min(left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    """Minimum with an explicit arithmetic-mean gradient at exact equality."""

    if left.shape != right.shape:
        raise ContractError("PPO min operands must have equal shapes")
    return torch.where(left < right, left, torch.where(right < left, right, 0.5 * (left + right)))


def clip_combined_gradient(gradients: Iterable[torch.Tensor]) -> tuple[torch.Tensor, ...]:
    values = tuple(gradients)
    if not values or any(not torch.isfinite(value).all() for value in values):
        raise ContractError("finite combined gradients are required")
    norm = torch.sqrt(sum(torch.sum(value * value) for value in values))
    scale = torch.where(
        norm > GRADIENT_NORM_LIMIT,
        torch.tensor(GRADIENT_NORM_LIMIT, dtype=norm.dtype) / norm,
        torch.tensor(1.0, dtype=norm.dtype),
    )
    return tuple(value * scale for value in values)


@dataclass(frozen=True)
class AdamWState:
    moment: torch.Tensor
    variance: torch.Tensor
    step: int


def adamw_step(
    parameter: torch.Tensor,
    gradient: torch.Tensor,
    state: AdamWState,
) -> tuple[torch.Tensor, AdamWState]:
    """One exact float32, globally one-based AdamW fixture step."""

    if parameter.dtype != gradient.dtype or parameter.dtype != torch.float32:
        raise ContractError("AdamW fixture tensors must be float32")
    if parameter.shape != gradient.shape or state.moment.shape != parameter.shape or state.variance.shape != parameter.shape:
        raise ContractError("AdamW tensor shapes differ")
    if state.step < 0:
        raise ContractError("AdamW prior step must be nonnegative")
    step = state.step + 1
    moment = torch.tensor(0.9, dtype=torch.float32) * state.moment + torch.tensor(0.1, dtype=torch.float32) * gradient
    variance = torch.tensor(0.999, dtype=torch.float32) * state.variance + torch.tensor(0.001, dtype=torch.float32) * gradient.square()
    mhat = moment / (1.0 - 0.9**step)
    vhat = variance / (1.0 - 0.999**step)
    updated = parameter - 3e-4 * (mhat / (torch.sqrt(vhat) + 1e-8) + 1e-5 * parameter)
    return updated, AdamWState(moment=moment, variance=variance, step=step)


def optimizer_index_contract(kind: str) -> tuple[int, int]:
    if kind == "FOUNDATION":
        return (1, 1_920)
    if kind in ("TREAT", "FREE", "SET"):
        return (1, 1_152)
    raise ContractError("unregistered optimizer kind")


# Freeze the arithmetic at import without allocating trainable tensors.
validate_foundation_schema()
if FOUNDATION_PARAMETER_COUNT != FOUNDATION_ACTOR_PARAMETER_COUNT + FOUNDATION_CRITIC_PARAMETER_COUNT:
    raise RuntimeError("foundation total parameter contract differs")
if TREAT_TRAINABLE_PARAMETER_COUNT != TREAT_SCALE_PARAMETER_COUNT + ORDER_CRITIC_PARAMETER_COUNT:
    raise RuntimeError("TREAT trainable parameter contract differs")
if FREE_TRAINABLE_PARAMETER_COUNT != TREAT_TRAINABLE_PARAMETER_COUNT + FREE_RESIDUAL_PARAMETER_COUNT:
    raise RuntimeError("FREE trainable parameter contract differs")
