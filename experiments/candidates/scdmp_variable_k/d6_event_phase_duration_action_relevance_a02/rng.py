"""Outcome-blind primitive-indexed disturbances for A02."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct

from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.native_state import (
    DisturbanceHold,
    HORIZON_TICKS,
    MAX_HOLD_TICKS,
)


def _frame(value: object) -> bytes:
    if isinstance(value, int):
        return b"i" + struct.pack("<q", value)
    encoded = str(value).encode("utf-8")
    return b"s" + struct.pack("<I", len(encoded)) + encoded


def _sign(seed: int, domain: str, address: tuple[object, ...]) -> int:
    message = b"".join(_frame(item) for item in (seed, domain, *address))
    return 1 if int.from_bytes(hashlib.blake2b(message, digest_size=8).digest(), "little") & 1 else -1


@dataclass(frozen=True, slots=True)
class PrimitiveTape:
    eta_v: tuple[float, ...]
    eta_y: tuple[float, ...]
    eta_omega: tuple[float, ...]

    def hold(self, primitive_tick: int) -> DisturbanceHold:
        stop = primitive_tick + MAX_HOLD_TICKS
        return DisturbanceHold(
            self.eta_v[primitive_tick:stop],
            self.eta_y[primitive_tick:stop],
            self.eta_omega[primitive_tick:stop],
        )


def materialize_tape(
    seed: int,
    domain: str,
    address: tuple[object, ...],
) -> PrimitiveTape:
    """Freeze a tape addressed only by base, tape, primitive tick and channel."""

    # The final twelve values are fixed unused ABI tail inputs when a hold is
    # truncated by the horizon; every primitive actually executed is <364.
    length = HORIZON_TICKS + MAX_HOLD_TICKS - 1
    channels = []
    for channel, magnitude in enumerate((0.003, 0.002, 0.004)):
        channels.append(tuple(
            magnitude * _sign(seed, domain, (*address, tick, channel))
            for tick in range(length)
        ))
    return PrimitiveTape(*channels)


__all__ = ["PrimitiveTape", "materialize_tape"]
