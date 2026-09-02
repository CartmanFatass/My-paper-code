"""Call-order-independent counter RNG for the MF-RS-MK object.

The only admissible roots are the two prospectively prescribed integer
training seeds.  The B01 schema prefix makes these streams independent of all
historical FCEOV byte-master namespaces.
"""

from __future__ import annotations

import hashlib
import hmac
import struct
from typing import Final, Sequence

from .contracts import (
    DEVELOPMENT_TAPES, HELDOUT_NAMESPACE_TOKEN, HELDOUT_TAPES, SCIENTIFIC_RNG_NAMESPACE,
    STATE_SPECS, TRAINING_SEEDS, StateSpec,
)
from .native_state import DisturbanceHold, TapeAddress, TapeNamespace


class RNGContractError(ValueError):
    pass


_PREFIX: Final[bytes] = (SCIENTIFIC_RNG_NAMESPACE + "\x00COUNTER-RNG-V1\x00").encode("ascii")
MAX_UNIFORM24: Final[float] = 1.0 - 2.0**-24


def _frame(value: object) -> bytes:
    if isinstance(value, bool):
        raise RNGContractError("boolean RNG address components are forbidden")
    if isinstance(value, int):
        # Text is framed and type-tagged, so negative and arbitrary-size ints
        # remain injective without a platform-width assumption.
        payload = str(value).encode("ascii")
        return b"i" + struct.pack(">I", len(payload)) + payload
    if isinstance(value, str):
        payload = value.encode("utf-8")
        return b"s" + struct.pack(">I", len(payload)) + payload
    raise RNGContractError("RNG addresses contain only typed int/string components")


def _message(domain: str, address: tuple[object, ...], counter: int) -> bytes:
    if not isinstance(domain, str) or not domain or "\x00" in domain:
        raise RNGContractError("RNG domain must be a nonempty explicit string")
    if not isinstance(address, tuple):
        raise RNGContractError("RNG address must be a tuple")
    if isinstance(counter, bool) or not isinstance(counter, int) or counter < 0:
        raise RNGContractError("RNG counter must be a nonnegative integer")
    framed_domain = _frame(domain)
    framed_address = b"".join(_frame(item) for item in address)
    return (
        _PREFIX
        + framed_domain
        + struct.pack(">I", len(address))
        + framed_address
        + b"c"
        + counter.to_bytes(max(1, (counter.bit_length() + 7) // 8), "big")
    )


class CounterRNG:
    """HMAC-SHA256 counter source addressed by `(seed, domain, address)`."""

    def __init__(self, seed: int) -> None:
        if isinstance(seed, bool) or not isinstance(seed, int) or seed not in TRAINING_SEEDS:
            raise RNGContractError(f"seed must be one of the prescribed roots {TRAINING_SEEDS}")
        self.seed = seed
        self._key = _PREFIX + seed.to_bytes(8, "big", signed=False)

    def block(self, domain: str, address: tuple[object, ...], counter: int = 0) -> bytes:
        return hmac.new(self._key, _message(domain, address, counter), hashlib.sha256).digest()

    def uint64(self, domain: str, address: tuple[object, ...], counter: int = 0) -> int:
        return int.from_bytes(self.block(domain, address, counter)[:8], "big")

    def uniform53(self, domain: str, address: tuple[object, ...]) -> float:
        return (self.uint64(domain, address) >> 11) * 2.0**-53

    def uniform24(self, domain: str, address: tuple[object, ...]) -> float:
        return (self.uint64(domain, address) >> 40) * 2.0**-24

    def uniforms(
        self, domain: str, address: tuple[object, ...], count: int
    ) -> tuple[float, ...]:
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise RNGContractError("uniform count must be a nonnegative integer")
        return tuple(
            (self.uint64(domain, address, index) >> 11) * 2.0**-53
            for index in range(count)
        )

    def bernoulli(self, probability: float, *, domain: str, address: tuple[object, ...]) -> bool:
        if isinstance(probability, bool) or not isinstance(probability, (int, float)):
            raise RNGContractError("Bernoulli probability must be real")
        value = float(probability)
        if not 0.0 <= value <= 1.0:
            raise RNGContractError("Bernoulli probability must lie in [0,1]")
        return self.uniform53(domain, address) < value

    def _randbelow(self, upper: int, *, domain: str, address: tuple[object, ...]) -> int:
        if isinstance(upper, bool) or not isinstance(upper, int) or upper <= 0:
            raise RNGContractError("randbelow upper bound must be positive")
        modulus = 1 << 64
        limit = modulus - modulus % upper
        counter = 0
        while True:
            value = self.uint64(domain, address, counter)
            if value < limit:
                return value % upper
            counter += 1

    def permutation(
        self, size: int, *, domain: str, address: tuple[object, ...]
    ) -> tuple[int, ...]:
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise RNGContractError("permutation size must be nonnegative")
        values = list(range(size))
        for right in range(size - 1, 0, -1):
            left = self._randbelow(
                right + 1,
                domain=domain + ".fisher-yates",
                address=address + (right,),
            )
            values[left], values[right] = values[right], values[left]
        return tuple(values)

    def initialization_uniforms(
        self, *, replicate: int, arm: str, tensor_name: str, count: int
    ) -> Sequence[float]:
        if replicate != 0 or arm != "FOUNDATION":
            raise RNGContractError("MF-RS-MK initializes one foundation per prescribed seed")
        return tuple(
            self.uniform24("foundation-initialization", (tensor_name, flat_index))
            for flat_index in range(count)
        )


def rng_for_seed(seed: int) -> CounterRNG:
    return CounterRNG(seed)


def _state(state_id: str) -> StateSpec:
    rows = tuple(row for row in STATE_SPECS if row.cell == state_id)
    if len(rows) != 1:
        raise RNGContractError("state is outside the six-state checkerboard")
    return rows[0]


def development_tape_address(state_id: str, tape: int) -> TapeAddress:
    state = _state(state_id)
    if tape not in DEVELOPMENT_TAPES:
        raise RNGContractError("development tape address lies outside RUN-01")
    return TapeAddress(TapeNamespace.DEVELOPMENT, state.source_seed, f"{state_id}/{tape}")


def source_tape_address(state: StateSpec, scan: int) -> TapeAddress:
    if state not in STATE_SPECS:
        raise RNGContractError("state is outside the six-state checkerboard")
    if isinstance(scan, bool) or not isinstance(scan, int) or scan not in range(8):
        raise RNGContractError("source scan lies outside the frozen eight-tape frontier")
    return TapeAddress(TapeNamespace.SOURCE, state.source_seed, f"{state.cell}/{scan}")


def heldout_tape_address(token: str, state_id: str, tape: int) -> TapeAddress:
    state = _state(state_id)
    if token != HELDOUT_NAMESPACE_TOKEN:
        raise RNGContractError("held-out namespace token differs")
    if tape not in HELDOUT_TAPES:
        raise RNGContractError("held-out tape address lies outside RUN-01")
    return TapeAddress(TapeNamespace.HELDOUT, state.source_seed, f"{token}/{state_id}/{tape}")


def source_reset_values(address: TapeAddress) -> tuple[float, float, float]:
    if address.namespace is not TapeNamespace.SOURCE:
        raise RNGContractError("source reset requires a SOURCE address")
    source = CounterRNG(address.seed)
    return (
        0.03 * source.uniform53("source-reset", (address.tape_id, "v")),
        -0.01 + 0.02 * source.uniform53("source-reset", (address.tape_id, "y")),
        -0.01 + 0.02 * source.uniform53("source-reset", (address.tape_id, "phi")),
    )


def materialize_disturbance_tape(address: TapeAddress, *, holds: int = 64) -> tuple[DisturbanceHold, ...]:
    """Derive an exact addressed tape; callers cannot substitute tape values."""

    if not isinstance(address, TapeAddress):
        raise TypeError("disturbance tape requires a typed address")
    if isinstance(holds, bool) or not isinstance(holds, int) or holds != 64:
        raise RNGContractError("B01 disturbance tapes contain exactly 64 hold rows")
    source = CounterRNG(address.seed)
    magnitudes = (0.003, 0.002, 0.004)
    rows = []
    for hold in range(holds):
        channels = []
        for channel, magnitude in enumerate(magnitudes):
            channels.append(tuple(
                magnitude if source.bernoulli(
                    0.5,
                    domain=f"{address.namespace.value.lower()}-disturbance-sign",
                    address=(address.tape_id, hold, tick, channel),
                ) else -magnitude
                for tick in range(13)
            ))
        rows.append(DisturbanceHold(*channels))
    return tuple(rows)


__all__ = [
    "CounterRNG", "MAX_UNIFORM24", "RNGContractError", "development_tape_address",
    "heldout_tape_address", "materialize_disturbance_tape", "rng_for_seed",
    "source_reset_values", "source_tape_address",
]
