"""Exact 35,513-parameter FRRIE learned-arm architecture contract."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterator, Mapping

import numpy as np

from .contracts.core import ContractError, MODEL_PARAMETER_COUNT
from .rng import AddressedRNG, RNGAddress

LAYER_SHAPES: tuple[tuple[str, tuple[int, ...]], ...] = (
    ("message_encoder.weight_ih", (64, 22)),
    ("message_encoder.bias_ih", (64,)),
    ("message_encoder.weight_ho", (32, 64)),
    ("message_encoder.bias_ho", (32,)),
    ("gru.weight_input_zrn", (192, 55)),
    ("gru.weight_hidden_zrn", (192, 64)),
    ("gru.bias_zrn", (192,)),  # one mathematical bias, not two equivalent biases
    ("action_head.weight", (6, 64)),
    ("action_head.bias", (6,)),
    ("beta", (3, 3, 2)),
    ("critic.input.weight", (64, 66)),
    ("critic.input.bias", (64,)),
    ("critic.hidden.weight", (64, 64)),
    ("critic.hidden.bias", (64,)),
    ("critic.output.weight", (1, 64)),
    ("critic.output.bias", (1,)),
)
PROJECTION_BOXES = {"PHY_TRUST": (-0.15, 0.15), "EDGE_FLEX": (-1.50, 1.50)}
STRICT_CAPACITY_WITNESS = np.float32(0.60)
PARAMETER_BYTE_COUNT = MODEL_PARAMETER_COUNT * np.dtype("<f4").itemsize


def architecture_parameter_count() -> int:
    return sum(math.prod(shape) for _, shape in LAYER_SHAPES)


if architecture_parameter_count() != MODEL_PARAMETER_COUNT:  # import-time structural assertion only
    raise RuntimeError("FRRIE architecture count drift")


def architecture_shapes() -> dict[str, tuple[int, ...]]:
    return dict(LAYER_SHAPES)


def _initial_bytes(rng: AddressedRNG, seed_block: str, count: int) -> bytes:
    if not isinstance(rng, AddressedRNG):
        raise ContractError("initialization requires the FRRIE addressed RNG")
    if not isinstance(seed_block, str) or not seed_block.startswith("FRRIE-"):
        raise ContractError("initialization requires a fresh FRRIE seed-block literal")
    out = bytearray()
    draw = 0
    while len(out) < count:
        address = RNGAddress(
            seed_block=seed_block,
            purpose="INITIALIZE",
            roster=0,
            update=0,
            episode=0,
            step=0,
            entity=0,
            draw=draw,
            domain="INITIALIZATION",
        )
        out.extend(rng.block(address))
        draw += 1
    return bytes(out[:count])


def _initialize(rng: AddressedRNG, seed_block: str) -> dict[str, np.ndarray]:
    total = MODEL_PARAMETER_COUNT
    raw = np.frombuffer(_initial_bytes(rng, seed_block, total * 4), dtype="<u4").astype(np.float64)
    unit = (raw + 0.5) / 2**32
    values = ((unit * 2.0 - 1.0) * 0.05).astype("<f4")
    arrays: dict[str, np.ndarray] = {}
    cursor = 0
    for name, shape in LAYER_SHAPES:
        size = math.prod(shape)
        arrays[name] = values[cursor:cursor + size].reshape(shape).copy()
        cursor += size
    return arrays


@dataclass
class LearnedArm:
    arm_id: str
    parameters: dict[str, np.ndarray]

    def __post_init__(self) -> None:
        if self.arm_id not in PROJECTION_BOXES:
            raise ContractError("unknown learned arm")
        self._validate_parameters()

    def _validate_parameters(self) -> None:
        if set(self.parameters) != {name for name, _ in LAYER_SHAPES}:
            raise ContractError("learned arm parameter keys are not exact")
        if tuple((name, tuple(self.parameters[name].shape)) for name, _ in LAYER_SHAPES) != LAYER_SHAPES:
            raise ContractError("learned arm parameter names/shapes are not exact")
        if any(
            array.dtype != np.dtype("<f4") or not array.flags.c_contiguous
            or not np.isfinite(array).all()
            for array in self.parameters.values()
        ):
            raise ContractError("learned arm parameters must be finite C-order little-endian FP32")

    @property
    def projection_box(self) -> tuple[float, float]:
        return PROJECTION_BOXES[self.arm_id]

    @property
    def parameter_count(self) -> int:
        return sum(array.size for array in self.parameters.values())

    def parameter_bytes(self) -> bytes:
        self._validate_parameters()
        data = b"".join(self.parameters[name].tobytes(order="C") for name, _ in LAYER_SHAPES)
        if len(data) != PARAMETER_BYTE_COUNT:
            raise ContractError("learned arm parameter byte count drift")
        return data

    @classmethod
    def from_parameter_bytes(cls, arm_id: str, data: bytes) -> "LearnedArm":
        """Restore the exact fixed-order finite FP32 parameter representation."""
        if not isinstance(data, bytes) or len(data) != PARAMETER_BYTE_COUNT:
            raise ContractError(
                f"learned arm state must be exactly {PARAMETER_BYTE_COUNT} bytes"
            )
        flat = np.frombuffer(data, dtype="<f4")
        if flat.size != MODEL_PARAMETER_COUNT or not np.isfinite(flat).all():
            raise ContractError("learned arm state must contain exactly finite FP32 values")
        parameters: dict[str, np.ndarray] = {}
        cursor = 0
        for name, shape in LAYER_SHAPES:
            size = math.prod(shape)
            parameters[name] = flat[cursor:cursor + size].reshape(shape, order="C").copy()
            cursor += size
        arm = cls(arm_id=arm_id, parameters=parameters)
        if arm.parameter_bytes() != data:
            raise ContractError("learned arm state is not the canonical fixed-order FP32 layout")
        return arm

    def project_beta(self) -> None:
        low, high = self.projection_box
        np.clip(self.parameters["beta"], low, high, out=self.parameters["beta"])

    def accepts_witness(self, value: float = 0.60) -> bool:
        low, high = self.projection_box
        return low <= value <= high


def initialize_paired_arms(rng: AddressedRNG, seed_block: str) -> tuple[LearnedArm, LearnedArm]:
    """Return separate arrays with bit-identical pair initialization."""
    template = _initialize(rng, seed_block)
    phy = LearnedArm("PHY_TRUST", {name: value.copy() for name, value in template.items()})
    edge = LearnedArm("EDGE_FLEX", {name: value.copy() for name, value in template.items()})
    if phy.parameter_bytes() != edge.parameter_bytes():
        raise RuntimeError("paired initialization lost bit equality")
    return phy, edge


def assert_projection_only_difference(phy: LearnedArm, edge: LearnedArm) -> None:
    if (phy.arm_id, edge.arm_id) != ("PHY_TRUST", "EDGE_FLEX"):
        raise ContractError("paired arms must be PHY_TRUST then EDGE_FLEX")
    if phy.parameter_bytes() != edge.parameter_bytes():
        raise ContractError("paired initial parameter bytes differ")
    if phy.projection_box == edge.projection_box:
        raise ContractError("projection boxes must differ")
    if phy.accepts_witness() or not edge.accepts_witness():
        raise ContractError("literal beta=0.60 strict-capacity witness failed")


def relational_weight(k0: float, beta0: float, beta1: float, public_value: float) -> np.float32:
    """Frozen omega=K0*exp(beta0+beta1*v) relation weight."""
    if any(not math.isfinite(float(value)) for value in (k0, beta0, beta1, public_value)) or k0 < 0:
        raise ContractError("relational weight inputs are outside support")
    k0_fp32 = np.float32(k0)
    exponent = np.float32(beta0) + np.float32(beta1) * np.float32(public_value)
    return np.float32(k0_fp32 * np.exp(exponent))


def masked_action(logits: np.ndarray, legal_role_mask: np.ndarray) -> int:
    """Deterministic inspection helper; production sampling stays native."""
    if logits.shape != (6,) or legal_role_mask.shape != (6,) or legal_role_mask.dtype != np.bool_:
        raise ContractError("six-action logits and boolean legal role mask are required")
    if not legal_role_mask.any() or not np.isfinite(logits).all():
        raise ContractError("legal action support is empty or logits are nonfinite")
    masked = np.where(legal_role_mask, logits, -np.inf)
    return int(np.argmax(masked))
