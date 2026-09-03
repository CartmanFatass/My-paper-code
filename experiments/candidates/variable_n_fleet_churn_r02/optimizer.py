"""Exact ordered scalar clipping and AdamW recurrence for VNFC R02."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence

from .contract import (
    BETA1,
    BETA2,
    ContractViolation,
    EPS,
    GRADIENT_CAP,
    LR,
    ScalarTranscendentals,
    WEIGHT_DECAY,
)
from .scalar import rn64


Shape = tuple[int, ...]


def _element_count(shape: Shape) -> int:
    if not shape or any(isinstance(size, bool) or not isinstance(size, int) or size <= 0 for size in shape):
        raise ContractViolation("parameter shape must have positive declared dimensions")
    count = 1
    for size in shape:
        count *= size
    return count


def _name(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise ContractViolation("parameter name must be nonempty")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ContractViolation("parameter names must be ASCII") from exc
    return value


def _values(values: Sequence[float], shape: Shape) -> tuple[float, ...]:
    result = tuple(rn64(value) for value in values)
    if len(result) != _element_count(shape):
        raise ContractViolation("C-order scalar count differs from declared shape")
    return result


@dataclass(frozen=True)
class ParameterTensor:
    name: str
    shape: Shape
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _name(self.name))
        object.__setattr__(self, "shape", tuple(self.shape))
        object.__setattr__(self, "values", _values(self.values, self.shape))


@dataclass(frozen=True)
class GradientTensor:
    name: str
    shape: Shape
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _name(self.name))
        object.__setattr__(self, "shape", tuple(self.shape))
        object.__setattr__(self, "values", _values(self.values, self.shape))


@dataclass(frozen=True)
class TensorAdamState:
    name: str
    shape: Shape
    m: tuple[float, ...]
    v: tuple[float, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _name(self.name))
        object.__setattr__(self, "shape", tuple(self.shape))
        object.__setattr__(self, "m", _values(self.m, self.shape))
        object.__setattr__(self, "v", _values(self.v, self.shape))

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "shape": list(self.shape), "m": list(self.m), "v": list(self.v)}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "TensorAdamState":
        if not isinstance(value, Mapping):
            raise ContractViolation("tensor Adam state must be a mapping")
        if set(value) != {"name", "shape", "m", "v"}:
            raise ContractViolation("tensor Adam state fields drifted")
        if not isinstance(value["name"], str):
            raise ContractViolation("serialized parameter name must remain a string")
        if not all(isinstance(value[field], list) for field in ("shape", "m", "v")):
            raise ContractViolation("serialized tensor shape and moments must remain lists")
        return cls(value["name"], tuple(value["shape"]), tuple(value["m"]), tuple(value["v"]))


@dataclass(frozen=True)
class AdamWState:
    step: int
    beta1_power: float
    beta2_power: float
    tensors: tuple[TensorAdamState, ...]

    def __post_init__(self) -> None:
        if isinstance(self.step, bool) or not isinstance(self.step, int) or self.step < 0:
            raise ContractViolation("optimizer step must be an unsigned integer")
        object.__setattr__(self, "beta1_power", rn64(self.beta1_power))
        object.__setattr__(self, "beta2_power", rn64(self.beta2_power))
        object.__setattr__(self, "tensors", tuple(self.tensors))
        _require_ascii_order(tuple(tensor.name for tensor in self.tensors))
        expected_b1 = 1.0
        expected_b2 = 1.0
        for _ in range(self.step):
            expected_b1 = rn64(expected_b1 * BETA1)
            expected_b2 = rn64(expected_b2 * BETA2)
        if self.beta1_power != expected_b1 or self.beta2_power != expected_b2:
            raise ContractViolation("AdamW bias powers do not match the serialized step")

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "beta1_power": self.beta1_power,
            "beta2_power": self.beta2_power,
            "tensors": [tensor.to_dict() for tensor in self.tensors],
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "AdamWState":
        if not isinstance(value, Mapping):
            raise ContractViolation("AdamW state must be a mapping")
        if set(value) != {"step", "beta1_power", "beta2_power", "tensors"}:
            raise ContractViolation("AdamW state fields drifted")
        tensors = value["tensors"]
        if not isinstance(tensors, list):
            raise ContractViolation("AdamW tensor state must be a list")
        return cls(
            step=value["step"],
            beta1_power=value["beta1_power"],
            beta2_power=value["beta2_power"],
            tensors=tuple(TensorAdamState.from_dict(tensor) for tensor in tensors),
        )


@dataclass(frozen=True)
class ClipResult:
    raw_norm: float
    multiplier: float
    gradients: tuple[GradientTensor, ...]


@dataclass(frozen=True)
class OptimizerStep:
    parameters: tuple[ParameterTensor, ...]
    state: AdamWState
    clipping: ClipResult


def _require_ascii_order(names: tuple[str, ...]) -> None:
    if any(_name(name) != name for name in names):
        raise ContractViolation("invalid parameter name")
    if names != tuple(sorted(names)) or len(set(names)) != len(names):
        raise ContractViolation("parameters must be unique and in ASCII-name order")


def _validate_parallel(
    parameters: Sequence[ParameterTensor], gradients: Sequence[GradientTensor]
) -> tuple[tuple[ParameterTensor, ...], tuple[GradientTensor, ...]]:
    params = tuple(parameters)
    grads = tuple(gradients)
    _require_ascii_order(tuple(parameter.name for parameter in params))
    _require_ascii_order(tuple(gradient.name for gradient in grads))
    if len(params) != len(grads):
        raise ContractViolation("parameter/gradient tensor count drift")
    for parameter, gradient in zip(params, grads):
        if parameter.name != gradient.name or parameter.shape != gradient.shape:
            raise ContractViolation("parameter/gradient name or shape drift")
    return params, grads


def initialize_adamw(parameters: Sequence[ParameterTensor]) -> AdamWState:
    params = tuple(parameters)
    _require_ascii_order(tuple(parameter.name for parameter in params))
    tensors = tuple(
        TensorAdamState(
            parameter.name,
            parameter.shape,
            (0.0,) * len(parameter.values),
            (0.0,) * len(parameter.values),
        )
        for parameter in params
    )
    return AdamWState(step=0, beta1_power=1.0, beta2_power=1.0, tensors=tensors)


def clip_raw_gradients(
    parameters: Sequence[ParameterTensor],
    gradients: Sequence[GradientTensor],
    kernel: ScalarTranscendentals,
) -> ClipResult:
    _, grads = _validate_parallel(parameters, gradients)
    squared_sum = 0.0
    for gradient in grads:
        for value in gradient.values:
            squared_sum = rn64(squared_sum + rn64(value * value))
    norm = rn64(kernel.sqrt_R02(squared_sum))
    multiplier = 1.0 if norm == 0.0 or norm <= GRADIENT_CAP else rn64(GRADIENT_CAP / norm)
    clipped = tuple(
        GradientTensor(gradient.name, gradient.shape, tuple(rn64(value * multiplier) for value in gradient.values))
        for gradient in grads
    )
    return ClipResult(norm, multiplier, clipped)


def adamw_step(
    parameters: Sequence[ParameterTensor],
    raw_gradients: Sequence[GradientTensor],
    state: AdamWState,
    kernel: ScalarTranscendentals,
) -> OptimizerStep:
    params, _ = _validate_parallel(parameters, raw_gradients)
    if len(params) != len(state.tensors):
        raise ContractViolation("parameter/optimizer tensor count drift")
    for parameter, tensor in zip(params, state.tensors):
        if parameter.name != tensor.name or parameter.shape != tensor.shape:
            raise ContractViolation("parameter/optimizer name or shape drift")

    clipping = clip_raw_gradients(params, raw_gradients, kernel)
    b1_power = rn64(state.beta1_power * BETA1)
    b2_power = rn64(state.beta2_power * BETA2)
    one_minus_b1 = rn64(1.0 - BETA1)
    one_minus_b2 = rn64(1.0 - BETA2)
    b1_correction = rn64(1.0 - b1_power)
    b2_correction = rn64(1.0 - b2_power)
    if b1_correction == 0.0 or b2_correction == 0.0:
        raise ContractViolation("AdamW bias correction denominator is zero")

    # Complete all moment and normalized-update calculations before changing a
    # parameter bit.  This is the source-owned interpretation of the frozen
    # "moment updates precede parameter updates" requirement.
    new_tensor_states: list[TensorAdamState] = []
    normalized_updates: list[tuple[float, ...]] = []
    for parameter, gradient, old in zip(params, clipping.gradients, state.tensors):
        new_m: list[float] = []
        new_v: list[float] = []
        updates: list[float] = []
        for g, m, v in zip(gradient.values, old.m, old.v):
            m_next = rn64(rn64(BETA1 * m) + rn64(one_minus_b1 * g))
            g_squared = rn64(g * g)
            v_next = rn64(rn64(BETA2 * v) + rn64(one_minus_b2 * g_squared))
            m_hat = rn64(m_next / b1_correction)
            v_hat = rn64(v_next / b2_correction)
            denominator = rn64(rn64(kernel.sqrt_R02(v_hat)) + EPS)
            if denominator == 0.0:
                raise ContractViolation("AdamW denominator is zero")
            updates.append(rn64(m_hat / denominator))
            new_m.append(m_next)
            new_v.append(v_next)
        new_tensor_states.append(TensorAdamState(parameter.name, parameter.shape, tuple(new_m), tuple(new_v)))
        normalized_updates.append(tuple(updates))

    new_parameters: list[ParameterTensor] = []
    for parameter, updates in zip(params, normalized_updates):
        decay = WEIGHT_DECAY if len(parameter.shape) >= 2 else 0.0
        decay_factor = rn64(1.0 - rn64(LR * decay))
        values: list[float] = []
        for value, update in zip(parameter.values, updates):
            decayed = rn64(value * decay_factor)
            values.append(rn64(decayed - rn64(LR * update)))
        new_parameters.append(ParameterTensor(parameter.name, parameter.shape, tuple(values)))

    new_state = AdamWState(
        step=state.step + 1,
        beta1_power=b1_power,
        beta2_power=b2_power,
        tensors=tuple(new_tensor_states),
    )
    return OptimizerStep(tuple(new_parameters), new_state, clipping)
