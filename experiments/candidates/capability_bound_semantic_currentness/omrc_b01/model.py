"""Authoritative FP32 recurrent actor-critic for CBSC-OMRC-B01.

The cell is deliberately written from the frozen reset/update/new equations;
it does not rely on a framework GRU gate layout.  The private address fallback
exists only so this bounded substrate is independently testable.  Production
assembly can inject the host's canonical ``u64`` implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Callable, Sequence

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from .addressing import u64 as canonical_u64


OBJECT_ID = "CBSC-OMRC-B01"
INPUT_DIM = 168
PRIMITIVE_DIM = 136
ADAPTER_DIM = 32
HIDDEN_DIM = 128
ACTION_COUNT = 4
ACTIVE_PARAMETER_COUNT = 121_349

WAIT = 0
SERVE = 1
REFRESH = 2
SAFE_FALLBACK = 3

AddressU64 = Callable[[Sequence[str | int]], int]


class ModelValidationError(ValueError):
    """Raised when an input would violate the frozen model semantics."""


def _default_u64(address: Sequence[str | int]) -> int:
    """Use the sole canonical PRF implementation from :mod:`addressing`."""

    return canonical_u64(tuple(address))


def _address_uniform(address: Sequence[str | int], u64: AddressU64) -> float:
    value = u64(address)
    if type(value) is not int or not 0 <= value < (1 << 64):
        raise ModelValidationError("u64 addressing function returned an invalid value")
    return (value + 0.5) / float(1 << 64)


def _autocast_enabled() -> bool:
    if torch.is_autocast_enabled():
        return True
    try:
        return bool(torch.is_autocast_enabled("cpu"))
    except TypeError:  # pragma: no cover - compatibility with older PyTorch
        return bool(torch.is_autocast_cpu_enabled())


def enforce_fp32_execution_mode() -> None:
    """Disable TF32 and reject an enclosing mixed-precision context."""

    if hasattr(torch.backends, "cuda") and hasattr(torch.backends.cuda, "matmul"):
        torch.backends.cuda.matmul.allow_tf32 = False
    if hasattr(torch.backends, "cudnn"):
        torch.backends.cudnn.allow_tf32 = False
    if _autocast_enabled():
        raise ModelValidationError("mixed-precision/autocast execution is forbidden")


def _empty_parameter(*shape: int) -> nn.Parameter:
    return nn.Parameter(torch.empty(shape, dtype=torch.float32))


def _fill_weight(
    parameter: nn.Parameter,
    *,
    seed: int,
    logical_name: str,
    fan_in: int,
    fan_out: int,
    u64: AddressU64,
    initialized_columns: int | None = None,
) -> None:
    if parameter.ndim != 2 or tuple(parameter.shape) != (fan_out, fan_in):
        raise ModelValidationError(f"{logical_name} has a noncanonical matrix shape")
    columns = fan_in if initialized_columns is None else initialized_columns
    if not 0 <= columns <= fan_in:
        raise ModelValidationError("initialized column count is invalid")
    bound = math.sqrt(6.0 / (fan_in + fan_out))
    values = np.zeros((fan_out, fan_in), dtype=np.float32)
    for row in range(fan_out):
        base = row * fan_in
        for column in range(columns):
            flat_index = base + column
            uniform = _address_uniform(
                (OBJECT_ID, "PARAM", seed, logical_name, flat_index), u64
            )
            values[row, column] = np.float32((2.0 * uniform - 1.0) * bound)
    with torch.no_grad():
        parameter.copy_(torch.from_numpy(values))


@dataclass(frozen=True)
class ActorCriticStep:
    logits: torch.Tensor
    value: torch.Tensor
    hidden: torch.Tensor


@dataclass(frozen=True)
class ActorCriticSequence:
    logits: torch.Tensor
    values: torch.Tensor
    final_hidden: torch.Tensor


@dataclass(frozen=True)
class ActionSelection:
    actions: torch.Tensor
    log_probabilities: torch.Tensor
    consumed_uniform: torch.Tensor


class ExplicitGRUCell(nn.Module):
    """Six-matrix GRU cell in literal reset, update, new gate order."""

    def __init__(self, input_dim: int = HIDDEN_DIM, hidden_dim: int = HIDDEN_DIM) -> None:
        super().__init__()
        if input_dim != HIDDEN_DIM or hidden_dim != HIDDEN_DIM:
            raise ModelValidationError("CBSC-OMRC-B01 requires a 128x128 GRU")
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.weight_ir = _empty_parameter(hidden_dim, input_dim)
        self.weight_iz = _empty_parameter(hidden_dim, input_dim)
        self.weight_in = _empty_parameter(hidden_dim, input_dim)
        self.weight_hr = _empty_parameter(hidden_dim, hidden_dim)
        self.weight_hz = _empty_parameter(hidden_dim, hidden_dim)
        self.weight_hn = _empty_parameter(hidden_dim, hidden_dim)
        self.bias_ir = _empty_parameter(hidden_dim)
        self.bias_iz = _empty_parameter(hidden_dim)
        self.bias_in = _empty_parameter(hidden_dim)
        self.bias_hr = _empty_parameter(hidden_dim)
        self.bias_hz = _empty_parameter(hidden_dim)
        self.bias_hn = _empty_parameter(hidden_dim)

    def forward(self, inputs: torch.Tensor, hidden: torch.Tensor) -> torch.Tensor:
        _validate_matrix(inputs, "GRU inputs", self.input_dim)
        _validate_matrix(hidden, "GRU hidden", self.hidden_dim)
        if inputs.shape[0] != hidden.shape[0] or inputs.device != hidden.device:
            raise ModelValidationError("GRU input and hidden batches/devices must match")
        reset = torch.sigmoid(
            F.linear(inputs, self.weight_ir, self.bias_ir)
            + F.linear(hidden, self.weight_hr, self.bias_hr)
        )
        update = torch.sigmoid(
            F.linear(inputs, self.weight_iz, self.bias_iz)
            + F.linear(hidden, self.weight_hz, self.bias_hz)
        )
        new = torch.tanh(
            F.linear(inputs, self.weight_in, self.bias_in)
            + reset * F.linear(hidden, self.weight_hn, self.bias_hn)
        )
        return (1.0 - update) * new + update * hidden


class CommonRecurrentActorCritic(nn.Module):
    """The one common 121,349-parameter network used by every B01 arm."""

    def __init__(self, seed: int, *, address_u64: AddressU64 | None = None) -> None:
        super().__init__()
        if type(seed) is not int:
            raise ModelValidationError("parameter seed must be an integer")
        enforce_fp32_execution_mode()
        self.seed = seed
        self.input_weight = _empty_parameter(HIDDEN_DIM, INPUT_DIM)
        self.input_bias = _empty_parameter(HIDDEN_DIM)
        self.recurrent = ExplicitGRUCell()
        self.actor_weight = _empty_parameter(ACTION_COUNT, HIDDEN_DIM)
        self.actor_bias = _empty_parameter(ACTION_COUNT)
        self.value_weight = _empty_parameter(1, HIDDEN_DIM)
        self.value_bias = _empty_parameter(1)
        self._initialize(address_u64 or _default_u64)
        if self.active_parameter_count != ACTIVE_PARAMETER_COUNT:
            raise ModelValidationError("active parameter count is not 121,349")
        self.initialization_digest = model_parameter_digest(self)

    @property
    def active_parameter_count(self) -> int:
        return sum(parameter.numel() for parameter in self.parameters())

    def _initialize(self, u64: AddressU64) -> None:
        _fill_weight(
            self.input_weight,
            seed=self.seed,
            logical_name="input.weight",
            fan_in=INPUT_DIM,
            fan_out=HIDDEN_DIM,
            u64=u64,
            initialized_columns=PRIMITIVE_DIM,
        )
        for gate in ("r", "z", "n"):
            _fill_weight(
                getattr(self.recurrent, f"weight_i{gate}"),
                seed=self.seed,
                logical_name=f"gru.weight_i{gate}",
                fan_in=HIDDEN_DIM,
                fan_out=HIDDEN_DIM,
                u64=u64,
            )
            _fill_weight(
                getattr(self.recurrent, f"weight_h{gate}"),
                seed=self.seed,
                logical_name=f"gru.weight_h{gate}",
                fan_in=HIDDEN_DIM,
                fan_out=HIDDEN_DIM,
                u64=u64,
            )
        _fill_weight(
            self.actor_weight,
            seed=self.seed,
            logical_name="actor.weight",
            fan_in=HIDDEN_DIM,
            fan_out=ACTION_COUNT,
            u64=u64,
        )
        _fill_weight(
            self.value_weight,
            seed=self.seed,
            logical_name="value.weight",
            fan_in=HIDDEN_DIM,
            fan_out=1,
            u64=u64,
        )
        with torch.no_grad():
            for name, parameter in self.named_parameters():
                if "bias" in name:
                    parameter.zero_()

    def initial_hidden(
        self, batch_size: int, *, device: torch.device | str | None = None
    ) -> torch.Tensor:
        if type(batch_size) is not int or batch_size <= 0:
            raise ModelValidationError("batch_size must be a positive integer")
        target = self.input_weight.device if device is None else torch.device(device)
        return torch.zeros((batch_size, HIDDEN_DIM), dtype=torch.float32, device=target)

    def forward_step(self, observation: torch.Tensor, hidden: torch.Tensor) -> ActorCriticStep:
        enforce_fp32_execution_mode()
        _validate_matrix(observation, "observation", INPUT_DIM)
        _validate_matrix(hidden, "hidden", HIDDEN_DIM)
        if observation.shape[0] != hidden.shape[0] or observation.device != hidden.device:
            raise ModelValidationError("observation and hidden batches/devices must match")
        encoded = torch.relu(F.linear(observation, self.input_weight, self.input_bias))
        next_hidden = self.recurrent(encoded, hidden)
        logits = F.linear(next_hidden, self.actor_weight, self.actor_bias)
        value = F.linear(next_hidden, self.value_weight, self.value_bias).squeeze(-1)
        return ActorCriticStep(logits, value, next_hidden)

    def forward_episode(self, observations: torch.Tensor) -> ActorCriticSequence:
        if not isinstance(observations, torch.Tensor) or observations.ndim != 3:
            raise ModelValidationError("episode observations must have shape [B,T,168]")
        if observations.shape[2] != INPUT_DIM or observations.dtype != torch.float32:
            raise ModelValidationError("episode observations must be FP32 with width 168")
        if not torch.isfinite(observations).all().item():
            raise ModelValidationError("episode observations must be finite")
        hidden = self.initial_hidden(observations.shape[0], device=observations.device)
        logits: list[torch.Tensor] = []
        values: list[torch.Tensor] = []
        for transition in range(observations.shape[1]):
            step = self.forward_step(observations[:, transition], hidden)
            logits.append(step.logits)
            values.append(step.value)
            hidden = step.hidden
        return ActorCriticSequence(
            torch.stack(logits, dim=1), torch.stack(values, dim=1), hidden
        )


def _validate_matrix(value: torch.Tensor, name: str, width: int) -> None:
    if not isinstance(value, torch.Tensor) or value.ndim != 2 or value.shape[1] != width:
        raise ModelValidationError(f"{name} must have shape [B,{width}]")
    if value.dtype != torch.float32 or not torch.isfinite(value).all().item():
        raise ModelValidationError(f"{name} must contain finite FP32 values")


def masked_action(
    logits: torch.Tensor,
    decision_mask: torch.Tensor,
    *,
    uniforms: torch.Tensor | None = None,
    evaluation: bool = False,
) -> ActionSelection:
    """Apply the exact action mask and common-uniform mapping to a batch."""

    _validate_matrix(logits, "actor logits", ACTION_COUNT)
    if (
        not isinstance(decision_mask, torch.Tensor)
        or decision_mask.shape != (logits.shape[0],)
        or decision_mask.dtype != torch.bool
        or decision_mask.device != logits.device
    ):
        raise ModelValidationError("decision_mask must be a matching boolean vector")
    decision_count = int(decision_mask.sum().item())
    if evaluation and uniforms is not None:
        raise ModelValidationError("evaluation does not consume action uniforms")
    if not evaluation:
        if uniforms is None or uniforms.shape != (decision_count,):
            raise ModelValidationError("training requires one uniform per decision only")
        if uniforms.dtype != torch.float64 or uniforms.device != logits.device:
            raise ModelValidationError("action uniforms must be matching float64 values")
        if not torch.all((uniforms >= 0.0) & (uniforms < 1.0)).item():
            raise ModelValidationError("action uniforms must lie in [0,1)")

    actions = torch.full(
        (logits.shape[0],), WAIT, dtype=torch.int64, device=logits.device
    )
    log_probabilities = torch.zeros(
        (logits.shape[0],), dtype=torch.float32, device=logits.device
    )
    consumed = torch.zeros((logits.shape[0],), dtype=torch.bool, device=logits.device)
    if decision_count == 0:
        return ActionSelection(actions, log_probabilities, consumed)

    decision_logits = logits[decision_mask, SERVE : SAFE_FALLBACK + 1]
    legal_log_prob = torch.log_softmax(decision_logits, dim=-1)
    if evaluation:
        selected = torch.argmax(decision_logits, dim=-1) + SERVE
    else:
        probabilities64 = torch.softmax(decision_logits, dim=-1).to(torch.float64)
        probabilities64 = probabilities64 / probabilities64.sum(dim=-1, keepdim=True)
        cumulative = torch.cumsum(probabilities64, dim=-1)
        comparisons = cumulative > uniforms.unsqueeze(-1)
        first = comparisons.to(torch.int64).argmax(dim=-1)
        any_selected = comparisons.any(dim=-1)
        first = torch.where(any_selected, first, torch.full_like(first, 2))
        selected = first + SERVE
    decision_log_prob = legal_log_prob.gather(
        1, (selected - SERVE).unsqueeze(-1)
    ).squeeze(-1)
    actions[decision_mask] = selected
    log_probabilities[decision_mask] = decision_log_prob
    consumed[decision_mask] = not evaluation
    return ActionSelection(actions, log_probabilities, consumed)


def greedy_action(logits: torch.Tensor, decision_mask: torch.Tensor) -> ActionSelection:
    return masked_action(logits, decision_mask, evaluation=True)


def model_parameter_digest(model: CommonRecurrentActorCritic) -> str:
    """Digest the ordered names, shapes, dtypes, and literal parameter bytes."""

    digest = hashlib.sha256()
    for name, parameter in model.named_parameters():
        array = parameter.detach().cpu().contiguous().numpy()
        digest.update(name.encode("utf-8"))
        digest.update(json.dumps(list(array.shape), separators=(",", ":")).encode("ascii"))
        digest.update(str(array.dtype).encode("ascii"))
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest()
