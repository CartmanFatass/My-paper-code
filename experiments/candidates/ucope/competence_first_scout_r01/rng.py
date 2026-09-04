"""Fresh counter-addressed RNG with no process-global state."""

from __future__ import annotations

import hashlib
import math
import struct
from typing import Iterable

from .contract import OBJECT_ID, RNG_VERSION

NAMESPACES = frozenset(
    {
        "regime",
        "display-regime",
        "mark",
        "display-mark",
        "tail-service",
        "eval-regime",
        "eval-display-regime",
        "eval-mark",
        "eval-display-mark",
        "eval-tail-service",
        "flex-init",
        "bc-init",
    }
)


def _payload(namespace: str, keys: Iterable[object], counter: int) -> bytes:
    if namespace not in NAMESPACES:
        raise ValueError(f"unknown fresh RNG namespace: {namespace}")
    if type(counter) is not int or counter < 0:
        raise ValueError("counter must be a nonnegative integer")
    fields = (OBJECT_ID, RNG_VERSION, namespace, *(str(key) for key in keys), str(counter))
    return "\x1f".join(fields).encode("utf-8")


def uint64(namespace: str, *keys: object, counter: int = 0) -> int:
    return struct.unpack(">Q", hashlib.sha256(_payload(namespace, keys, counter)).digest()[:8])[0]


def uniform(namespace: str, *keys: object, counter: int = 0) -> float:
    return (uint64(namespace, *keys, counter=counter) >> 11) * (1.0 / (1 << 53))


def bernoulli(probability: float, namespace: str, *keys: object, counter: int = 0) -> bool:
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability outside [0,1]")
    return uniform(namespace, *keys, counter=counter) < probability


def glorot(rows: int, columns: int, *keys: object, namespace: str) -> list[list[float]]:
    if rows <= 0 or columns <= 0:
        raise ValueError("Glorot dimensions must be positive")
    limit = math.sqrt(6.0 / (rows + columns))
    return [
        [(2.0 * uniform(namespace, *keys, row, column) - 1.0) * limit for column in range(columns)]
        for row in range(rows)
    ]


def rng_contract() -> dict[str, object]:
    return {"version": RNG_VERSION, "counter_addressed": True, "namespaces": sorted(NAMESPACES)}
