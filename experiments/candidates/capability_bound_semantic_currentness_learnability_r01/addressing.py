"""Stateless SHA-256 addressing for initialization, order, and inference."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Final

from .support import Purpose


UINT64_SPACE: Final = 1 << 64


def canonical_address_bytes(parts: list[Any]) -> bytes:
    return json.dumps(
        parts,
        ensure_ascii=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")


def address_digest(parts: list[Any]) -> bytes:
    return hashlib.sha256(canonical_address_bytes(parts)).digest()


def addressed_u64(parts: list[Any]) -> int:
    return int.from_bytes(address_digest(parts)[:8], "big", signed=False)


def block_id(purpose: Purpose, block: int) -> str:
    limit = 24 if purpose is Purpose.MAIN else 4
    if type(block) is not int or not 0 <= block < limit:
        raise ValueError(f"{purpose.value} block must be in [0,{limit})")
    prefix = "MAIN" if purpose is Purpose.MAIN else "COMP"
    return f"CBSC-LR01-{prefix}-B{block:02d}"


def glorot_scalar(panel: str, identity: str, parameter_name: str, flat_index: int,
                  fan_in: int, fan_out: int) -> float:
    if flat_index < 0 or fan_in <= 0 or fan_out <= 0:
        raise ValueError("invalid addressed Glorot coordinate")
    value = addressed_u64(["CBSC-LR01-INIT", panel, identity, parameter_name, flat_index])
    uniform = (value + 0.5) / UINT64_SPACE
    return (2.0 * uniform - 1.0) * math.sqrt(6.0 / (fan_in + fan_out))


def ordered_batch_ids(panel: str, identity: str, epoch: int) -> tuple[int, ...]:
    if type(epoch) is not int or epoch < 0:
        raise ValueError("epoch must be a nonnegative integer")
    return tuple(sorted(
        range(8),
        key=lambda batch_id: (
            address_digest(["CBSC-LR01-ORDER", panel, identity, epoch, batch_id]),
            batch_id,
        ),
    ))


__all__ = [
    "address_digest", "addressed_u64", "block_id",
    "canonical_address_bytes", "glorot_scalar", "ordered_batch_ids",
]
