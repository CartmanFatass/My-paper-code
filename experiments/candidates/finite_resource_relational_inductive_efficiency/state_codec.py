"""Direct FRRIE Adam-state codec with no pickle, hash, or authentication."""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from typing import Any, Final

import numpy as np

from .arms import LAYER_SHAPES, PARAMETER_BYTE_COUNT, LearnedArm
from .contracts.core import ContractError, MODEL_PARAMETER_COUNT
from .policy import FRRIEActorCritic, TORCH_AVAILABLE, require_torch

if TORCH_AVAILABLE:
    import torch


OPTIMIZER_STATE_MAGIC: Final[bytes] = b"FRRIEOPT"
OPTIMIZER_STATE_VERSION: Final[int] = 1
MAX_TRAINING_UPDATE: Final[int] = 512
_HEADER: Final[struct.Struct] = struct.Struct("<8sII")
_STEP: Final[struct.Struct] = struct.Struct("<Q")
OPTIMIZER_PAYLOAD_BYTE_COUNT: Final[int] = 2 * PARAMETER_BYTE_COUNT + _STEP.size
OPTIMIZER_STATE_BYTE_COUNT: Final[int] = _HEADER.size + OPTIMIZER_PAYLOAD_BYTE_COUNT


@dataclass(frozen=True)
class DecodedAdamState:
    first_moment: dict[str, np.ndarray]
    second_moment: dict[str, np.ndarray]
    step: int


def optimizer_state_layout() -> tuple[tuple[str, tuple[int, ...]], ...]:
    """Structural inventory used once for m and again for v."""

    return LAYER_SHAPES


def _arrays_from_flat(flat: np.ndarray) -> dict[str, np.ndarray]:
    arrays: dict[str, np.ndarray] = {}
    cursor = 0
    for name, shape in LAYER_SHAPES:
        size = math.prod(shape)
        arrays[name] = flat[cursor:cursor + size].reshape(shape, order="C").copy()
        cursor += size
    if cursor != MODEL_PARAMETER_COUNT:
        raise RuntimeError("FRRIE optimizer inventory count drift")
    return arrays


def decode_optimizer_state(data: bytes) -> DecodedAdamState:
    """Decode exact ordered m/v FP32 arrays and the single uint64 Adam step."""

    if not isinstance(data, bytes) or len(data) != OPTIMIZER_STATE_BYTE_COUNT:
        raise ContractError(
            f"FRRIE optimizer state must be exactly {OPTIMIZER_STATE_BYTE_COUNT} bytes"
        )
    magic, version, payload_length = _HEADER.unpack_from(data, 0)
    if magic != OPTIMIZER_STATE_MAGIC:
        raise ContractError("FRRIE optimizer state magic differs")
    if version != OPTIMIZER_STATE_VERSION:
        raise ContractError("FRRIE optimizer state version differs")
    if payload_length != OPTIMIZER_PAYLOAD_BYTE_COUNT:
        raise ContractError("FRRIE optimizer payload length header differs")
    payload = memoryview(data)[_HEADER.size:]
    m_end = PARAMETER_BYTE_COUNT
    v_end = 2 * PARAMETER_BYTE_COUNT
    first_flat = np.frombuffer(payload[:m_end], dtype="<f4")
    second_flat = np.frombuffer(payload[m_end:v_end], dtype="<f4")
    if first_flat.size != MODEL_PARAMETER_COUNT or second_flat.size != MODEL_PARAMETER_COUNT:
        raise ContractError("FRRIE optimizer moment count differs")
    if not np.isfinite(first_flat).all() or not np.isfinite(second_flat).all():
        raise ContractError("FRRIE optimizer moments must be finite FP32")
    step = _STEP.unpack_from(payload, v_end)[0]
    return DecodedAdamState(
        _arrays_from_flat(first_flat), _arrays_from_flat(second_flat), step
    )


def _optimizer_parameters(model: FRRIEActorCritic, optimizer: Any) -> tuple[Any, ...]:
    if not isinstance(model, FRRIEActorCritic):
        raise ContractError("optimizer codec requires the fresh FRRIE actor/critic")
    if not isinstance(optimizer, torch.optim.Adam) or len(optimizer.param_groups) != 1:
        raise ContractError("optimizer codec requires one-group Torch Adam")
    expected = model.ordered_parameters()
    actual = tuple(optimizer.param_groups[0]["params"])
    if len(actual) != len(expected) or any(a is not b for a, b in zip(actual, expected)):
        raise ContractError("optimizer parameter order differs from LAYER_SHAPES")
    return expected


def _step_as_int(value: Any) -> int:
    if isinstance(value, torch.Tensor):
        if value.numel() != 1 or not bool(torch.isfinite(value).item()):
            raise ContractError("Adam step must be one finite scalar")
        numeric = float(value.detach().cpu().item())
    else:
        numeric = float(value)
    if not numeric.is_integer() or numeric < 0 or numeric > 2**64 - 1:
        raise ContractError("Adam step is outside uint64 support")
    return int(numeric)


def encode_optimizer_state(model: FRRIEActorCritic, optimizer: Any) -> bytes:
    """Encode only Adam m/v/step; model parameter bytes remain a separate object."""

    require_torch()
    parameters = _optimizer_parameters(model, optimizer)
    first_chunks: list[bytes] = []
    second_chunks: list[bytes] = []
    common_step: int | None = None
    any_state = any(bool(optimizer.state.get(parameter)) for parameter in parameters)
    for parameter in parameters:
        state = optimizer.state.get(parameter, {})
        if not state:
            if any_state:
                raise ContractError("Adam state is incomplete across the parameter inventory")
            first = torch.zeros_like(parameter)
            second = torch.zeros_like(parameter)
            step = 0
        else:
            if set(state) != {"step", "exp_avg", "exp_avg_sq"}:
                raise ContractError("Adam state contains an unsupported field")
            first = state["exp_avg"]
            second = state["exp_avg_sq"]
            step = _step_as_int(state["step"])
            if first.shape != parameter.shape or second.shape != parameter.shape:
                raise ContractError("Adam moment shape differs from its parameter")
            if first.dtype != torch.float32 or second.dtype != torch.float32:
                raise ContractError("Adam moments must remain FP32")
            if first.device.type != "cpu" or second.device.type != "cpu":
                raise ContractError("Adam moments must remain on CPU")
            if not bool(torch.isfinite(first).all().item()) or not bool(
                torch.isfinite(second).all().item()
            ):
                raise ContractError("Adam moments must be finite")
        if common_step is None:
            common_step = step
        elif step != common_step:
            raise ContractError("FRRIE Adam parameters do not share one update step")
        first_chunks.append(
            np.asarray(first.detach().numpy(), dtype="<f4", order="C").tobytes(order="C")
        )
        second_chunks.append(
            np.asarray(second.detach().numpy(), dtype="<f4", order="C").tobytes(order="C")
        )
    step_value = 0 if common_step is None else common_step
    if step_value > MAX_TRAINING_UPDATE:
        raise ContractError("FRRIE Adam step exceeds the sole 512-update budget")
    payload = b"".join(first_chunks) + b"".join(second_chunks) + _STEP.pack(step_value)
    if len(payload) != OPTIMIZER_PAYLOAD_BYTE_COUNT:
        raise ContractError("FRRIE optimizer payload byte count drift")
    return _HEADER.pack(
        OPTIMIZER_STATE_MAGIC, OPTIMIZER_STATE_VERSION, len(payload)
    ) + payload


def load_actor_and_optimizer_state(
    model: FRRIEActorCritic,
    optimizer: Any,
    arm_parameter_bytes: bytes,
    optimizer_state_bytes: bytes,
    *,
    expected_update: int,
) -> int:
    """Atomically validate then load separate actor bytes and Adam state bytes."""

    require_torch()
    _optimizer_parameters(model, optimizer)
    arm = LearnedArm.from_parameter_bytes(model.arm_id, arm_parameter_bytes)
    decoded = decode_optimizer_state(optimizer_state_bytes)
    if type(expected_update) is not int or not 0 <= expected_update <= MAX_TRAINING_UPDATE:
        raise ContractError("expected FRRIE update must be an integer in [0,512]")
    if decoded.step > MAX_TRAINING_UPDATE or decoded.step != expected_update:
        raise ContractError("serialized Adam step does not equal the expected FRRIE update")
    # All parsing and validation precedes mutation.
    model.load_learned_arm(arm)
    optimizer.state.clear()
    for (name, _), parameter in zip(LAYER_SHAPES, model.ordered_parameters()):
        optimizer.state[parameter] = {
            # Exact uninterrupted Torch 2.7 CPU Adam scalar representation.
            "step": torch.tensor(float(decoded.step), dtype=torch.float32),
            "exp_avg": torch.from_numpy(decoded.first_moment[name].copy()),
            "exp_avg_sq": torch.from_numpy(decoded.second_moment[name].copy()),
        }
    return decoded.step
