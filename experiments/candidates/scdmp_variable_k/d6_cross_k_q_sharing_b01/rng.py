"""Addressed scientific randomness; digests are used only as a counter PRF."""

from __future__ import annotations

import hashlib
import math
import struct

from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.native_state import (
    DisturbanceHold,
)


def _frame(value: object) -> bytes:
    if isinstance(value, int):
        return b"i" + struct.pack("<q", value)
    encoded = str(value).encode("utf-8")
    return b"s" + struct.pack("<I", len(encoded)) + encoded


def bits(seed: int, domain: str, address: tuple[object, ...], counter: int = 0) -> int:
    message = b"".join(_frame(item) for item in (seed, domain, *address, counter))
    return int.from_bytes(hashlib.blake2b(message, digest_size=8).digest(), "little")


def uniform(seed: int, domain: str, address: tuple[object, ...], counter: int = 0) -> float:
    return (bits(seed, domain, address, counter) + 0.5) / 2**64


def xavier_values(seed: int, address: tuple[object, ...], count: int, fan_in: int, fan_out: int):
    bound = math.sqrt(6.0 / (fan_in + fan_out))
    return [
        (2.0 * uniform(seed, "model-init", address, index) - 1.0) * bound
        for index in range(count)
    ]


def disturbance_tape(
    seed: int, domain: str, address: tuple[object, ...], holds: int = 64,
) -> tuple[DisturbanceHold, ...]:
    rows = []
    for hold in range(holds):
        channels = []
        for channel, magnitude in enumerate((0.003, 0.002, 0.004)):
            channels.append(tuple(
                magnitude if bits(seed, domain, (*address, hold, tick, channel)) & 1 else -magnitude
                for tick in range(13)
            ))
        rows.append(DisturbanceHold(*channels))
    return tuple(rows)


__all__ = ["bits", "disturbance_tape", "uniform", "xavier_values"]
