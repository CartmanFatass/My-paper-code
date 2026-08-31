"""Counter-keyed RNG: named, order-independent, and restart-independent."""

from __future__ import annotations

from typing import Iterable
import hashlib
import math
import struct

from .contract import CONTRACT_ID, RNG_VERSION_SPEC

RNG_VERSION = RNG_VERSION_SPEC
NAMESPACES = (
    "regime-rank",
    "display-regime-rank",
    "mark-uniform",
    "display-mark",
    "tail-service",
    "glorot",
)


def _payload(namespace: str, keys: Iterable[object], counter: int) -> bytes:
    if namespace not in NAMESPACES:
        raise ValueError(f"unknown RNG namespace: {namespace}")
    fields = [CONTRACT_ID, RNG_VERSION, namespace, *(str(key) for key in keys), str(counter)]
    return "\x1f".join(fields).encode("utf-8")


def uint64(namespace: str, *keys: object, counter: int = 0) -> int:
    raw = hashlib.sha256(_payload(namespace, keys, counter)).digest()
    return struct.unpack(">Q", raw[:8])[0]


def uniform(namespace: str, *keys: object, counter: int = 0) -> float:
    # Exact 53-bit construction in [0, 1), independent of platform PRNG state.
    return (uint64(namespace, *keys, counter=counter) >> 11) * (1.0 / (1 << 53))


def bernoulli(probability: float, namespace: str, *keys: object, counter: int = 0) -> bool:
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability outside [0,1]")
    return uniform(namespace, *keys, counter=counter) < probability


def balanced_binary_assignments(size: int, namespace: str, *keys: object) -> tuple[bool, ...]:
    if size <= 0 or size % 2:
        raise ValueError("balanced assignment size must be positive and even")
    ranked = sorted(range(size), key=lambda i: (uint64(namespace, *keys, i), i))
    selected = set(ranked[: size // 2])
    return tuple(index in selected for index in range(size))


def glorot_values(rows: int, columns: int, *keys: object) -> list[list[float]]:
    limit = math.sqrt(6.0 / (rows + columns))
    return [
        [(2.0 * uniform("glorot", *keys, row, column) - 1.0) * limit for column in range(columns)]
        for row in range(rows)
    ]

def rng_contract() -> dict[str, object]:
    return {"version": RNG_VERSION, "namespaces": list(NAMESPACES), "counter_addressed": True}
