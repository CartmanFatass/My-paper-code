"""Exact lossless 49-XOR-shear representation arms for CBSC-LR01."""

from __future__ import annotations

from enum import Enum
from typing import Final, Iterable, Sequence

from .contract import INPUT_BITS, SHEAR_OPERATIONS


class CodecArm(str, Enum):
    STRUCT = "STRUCTURED_CBSC"
    SHAM = "STRUCTURED_SHAM"
    RAW = "RAW_FLEX"


Shear = tuple[int, int]  # target, source


def _six_byte_shears(groups: Sequence[tuple[int, int]]) -> tuple[Shear, ...]:
    return tuple((target + bit, source + bit) for bit in range(8) for target, source in groups)


_STRUCT: Final = _six_byte_shears(
    ((16, 8), (32, 24), (40, 0), (48, 0), (56, 0), (64, 0))
) + ((107, 108),)
_SHAM: Final = _six_byte_shears(
    ((16, 24), (32, 0), (40, 8), (48, 24), (56, 8), (64, 24))
) + ((107, 109),)
_RAW_CANDIDATES: Final = tuple(
    (offset + target, offset + source)
    for offset in range(0, 104, 8)
    for target, source in ((1, 0), (3, 2), (5, 4), (7, 6))
)
_RAW: Final = _RAW_CANDIDATES[:SHEAR_OPERATIONS]

CODEC_SCHEDULES: Final = {
    CodecArm.STRUCT: _STRUCT,
    CodecArm.SHAM: _SHAM,
    CodecArm.RAW: _RAW,
}


def _arm(value: CodecArm | str) -> CodecArm:
    try:
        return value if isinstance(value, CodecArm) else CodecArm(value)
    except ValueError as error:
        raise ValueError(f"unknown CBSC-LR01 codec arm: {value!r}") from error


def _validated_bits(bits: Iterable[int]) -> list[int]:
    result = list(bits)
    if len(result) != INPUT_BITS:
        raise ValueError(f"CBSC-LR01 codec requires exactly {INPUT_BITS} bits")
    if any(type(bit) is not int or bit not in (0, 1) for bit in result):
        raise ValueError("CBSC-LR01 codec accepts only integer binary bits")
    return result


def _apply(bits: Iterable[int], schedule: Sequence[Shear]) -> tuple[int, ...]:
    result = _validated_bits(bits)
    for target, source in schedule:
        result[target] ^= result[source]
    return tuple(result)


def encode_bits(bits: Iterable[int], arm: CodecArm | str) -> tuple[int, ...]:
    """Apply the arm's exact ordered XOR-shear schedule."""

    return _apply(bits, CODEC_SCHEDULES[_arm(arm)])


def decode_bits(bits: Iterable[int], arm: CodecArm | str) -> tuple[int, ...]:
    """Invert an arm by applying its shear schedule in reverse order."""

    return _apply(bits, tuple(reversed(CODEC_SCHEDULES[_arm(arm)])))


if any(len(schedule) != SHEAR_OPERATIONS for schedule in CODEC_SCHEDULES.values()):
    raise RuntimeError("CBSC-LR01 codec schedule does not contain exactly 49 operations")
if any(
    target == source or not (0 <= target < INPUT_BITS and 0 <= source < INPUT_BITS)
    for schedule in CODEC_SCHEDULES.values()
    for target, source in schedule
):
    raise RuntimeError("CBSC-LR01 codec schedule contains an invalid shear")


__all__ = ["CODEC_SCHEDULES", "CodecArm", "Shear", "decode_bits", "encode_bits"]
