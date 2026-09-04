"""Address-stable RNG primitives used only for FCEOV stochastic draws."""

from __future__ import annotations

import hmac
import hashlib
import math
import secrets
from typing import Sequence


MAX_UNIFORM24 = 1.0 - 2.0**-24


class RNGContractError(ValueError):
    pass


def fresh_master() -> bytes:
    """Create the sole master for one new result root using the OS CSPRNG."""

    value = secrets.token_bytes(32)
    if not isinstance(value, bytes) or len(value) != 32:
        raise RNGContractError("operating-system RNG did not return one 256-bit master")
    return value


class AddressRNG:
    """HMAC-SHA256 counter RNG; addresses, never call order, determine draws."""

    def __init__(self, master: bytes) -> None:
        if not isinstance(master, bytes) or len(master) != 32:
            raise RNGContractError("FCEOV RNG master must contain exactly 256 bits")
        self._master = master

    def _block(self, domain: str, address: Sequence[object], counter: int) -> bytes:
        if (
            not isinstance(domain, str)
            or not domain
            or "\x1f" in domain
            or domain.startswith("TEST_ONLY")
        ):
            raise RNGContractError("production RNG domain must be explicit and non-test")
        if not isinstance(address, tuple) or any(
            isinstance(item, bool)
            or not isinstance(item, (int, str))
            or (isinstance(item, str) and "\x1f" in item)
            for item in address
        ):
            raise RNGContractError("RNG addresses must be typed int/string tuples")
        if isinstance(counter, bool) or not isinstance(counter, int) or counter < 0:
            raise RNGContractError("RNG counter must be nonnegative")
        encoded = "\x1f".join((domain, *(str(item) for item in address), str(counter))).encode("utf-8")
        return hmac.new(self._master, encoded, hashlib.sha256).digest()

    def uniforms(self, domain: str, address: Sequence[object], count: int) -> tuple[float, ...]:
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise RNGContractError("uniform count must be nonnegative")
        values: list[float] = []
        counter = 0
        while len(values) < count:
            block = self._block(domain, address, counter)
            for offset in range(0, len(block), 8):
                # The top 53 bits map exactly into binary64 [0,1).
                word = int.from_bytes(block[offset : offset + 8], "big") >> 11
                values.append(word * (2.0**-53))
                if len(values) == count:
                    break
            counter += 1
        return tuple(values)

    def uniform53(self, domain: str, address: tuple[object, ...]) -> float:
        block = self._block(domain, address, 0)
        return (int.from_bytes(block[:8], "big") >> 11) * (2.0**-53)

    def uniform24(self, domain: str, address: tuple[object, ...]) -> float:
        """Return an exactly float32-representable U[0,1) draw."""

        block = self._block(domain, address, 0)
        return (int.from_bytes(block[:8], "big") >> 40) * (2.0**-24)

    def bernoulli(self, probability: float, *, domain: str, address: Sequence[object]) -> bool:
        if (
            isinstance(probability, bool)
            or not isinstance(probability, (int, float))
            or not math.isfinite(probability)
            or not 0.0 <= probability <= 1.0
        ):
            raise RNGContractError("Bernoulli probability must lie in [0,1]")
        return self.uniforms(domain, address, 1)[0] < probability

    def permutation(self, count: int, *, domain: str, address: Sequence[object]) -> tuple[int, ...]:
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            raise RNGContractError("permutation width must be positive")
        values = list(range(count))
        draws = self.uniforms(domain, address, count - 1)
        for draw, upper in zip(draws, range(count - 1, 0, -1)):
            swap = min(int(draw * (upper + 1)), upper)
            values[upper], values[swap] = values[swap], values[upper]
        return tuple(values)

    def initialization_uniforms(
        self,
        *,
        replicate: int,
        arm: str,
        tensor_name: str,
        count: int,
    ) -> tuple[float, ...]:
        if replicate != 0 or arm != "FOUNDATION":
            raise RNGContractError("FCEOV materializes one foundation at replicate zero")
        return tuple(
            self.uniform24(
                "foundation-initialization", (replicate, arm, tensor_name, flat_index)
            )
            for flat_index in range(count)
        )


class TestAddressRNG(AddressRNG):
    """Explicit deterministic fixture source; unavailable to the runner result path."""

    def _block(self, domain: str, address: Sequence[object], counter: int) -> bytes:
        encoded = "\x1f".join(("TEST_ONLY_FCEOV", domain, *(str(item) for item in address), str(counter))).encode("utf-8")
        return hmac.new(self._master, encoded, hashlib.sha256).digest()


__all__ = ["AddressRNG", "MAX_UNIFORM24", "RNGContractError", "TestAddressRNG", "fresh_master"]
