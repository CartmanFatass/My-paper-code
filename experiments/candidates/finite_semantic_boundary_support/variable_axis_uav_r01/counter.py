from __future__ import annotations

import hashlib
from collections.abc import Sequence


NAMESPACE = "FSBS-VN1-R01"


def _text(value: str | int) -> str:
    if isinstance(value, bool):
        raise TypeError("Boolean coordinates are not registered R01 text or integers")
    if isinstance(value, int):
        if value < 0:
            raise ValueError("R01 integer coordinates must be unsigned")
        return str(value)
    if isinstance(value, str):
        return value
    raise TypeError(f"unsupported R01 coordinate type: {type(value).__name__}")


def address(seed: int, family: str, coordinates: Sequence[str | int], rejection: int) -> bytes:
    fields = [NAMESPACE, _text(seed), family]
    fields.extend(_text(value) for value in coordinates)
    fields.append(_text(rejection))
    return "\0".join(fields).encode("utf-8")


def categorical(
    domain_size: int, seed: int, family: str, coordinates: Sequence[str | int]
) -> int:
    if domain_size <= 0:
        raise ValueError("domain_size must be positive")
    limit = ((1 << 256) // domain_size) * domain_size
    rejection = 0
    while True:
        value = int.from_bytes(
            hashlib.sha256(address(seed, family, coordinates, rejection)).digest(),
            "big",
        )
        if value < limit:
            return value % domain_size
        rejection += 1


def permutation(
    size: int, seed: int, family: str, coordinates: Sequence[str | int]
) -> list[int]:
    values = list(range(size))
    for swap_position in range(size - 1, 0, -1):
        selected = categorical(
            swap_position + 1,
            seed,
            family,
            (*coordinates, swap_position),
        )
        values[swap_position], values[selected] = values[selected], values[swap_position]
    return values
