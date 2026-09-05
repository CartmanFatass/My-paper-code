"""The prior outcome-blind addressed disturbance law, with no global RNG state."""

from __future__ import annotations

import hashlib
import struct

from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.native_state import (
    DisturbanceHold,
)


def _frame(value: object) -> bytes:
    if isinstance(value, int):
        return b"i" + struct.pack("<q", value)
    encoded = str(value).encode("utf-8")
    return b"s" + struct.pack("<I", len(encoded)) + encoded


def _bit(seed: int, domain: str, address: tuple[object, ...], counter: int = 0) -> int:
    message = b"".join(_frame(item) for item in (seed, domain, *address, counter))
    return int.from_bytes(hashlib.blake2b(message, digest_size=8).digest(), "little") & 1


def disturbance_tape(
    seed: int,
    domain: str,
    address: tuple[object, ...],
    *,
    holds: int = 64,
) -> tuple[DisturbanceHold, ...]:
    rows: list[DisturbanceHold] = []
    for hold in range(holds):
        channels: list[tuple[float, ...]] = []
        for channel, magnitude in enumerate((0.003, 0.002, 0.004)):
            channels.append(tuple(
                magnitude
                if _bit(seed, domain, (*address, hold, tick, channel))
                else -magnitude
                for tick in range(13)
            ))
        rows.append(DisturbanceHold(*channels))
    return tuple(rows)


__all__ = ["disturbance_tape"]
