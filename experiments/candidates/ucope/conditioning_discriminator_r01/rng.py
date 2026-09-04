"""Dedicated counter-addressed RNG; process-global RNG state is never used."""

from __future__ import annotations

import hashlib
import math
import struct
from typing import Iterable

from .contract import OBJECT_ID, RNG_VERSION

NAMESPACES = frozenset({
    "regime", "display-regime", "mark", "display-mark", "tail-service",
    "eval-regime", "eval-display-regime", "eval-mark", "eval-display-mark",
    "eval-tail-service", "bc-init",
})


def _payload(namespace: str, keys: Iterable[object], counter: int) -> bytes:
    if namespace not in NAMESPACES or type(counter) is not int or counter < 0:
        raise ValueError("invalid counter RNG address")
    return "\x1f".join((OBJECT_ID, RNG_VERSION, namespace, *(str(key) for key in keys), str(counter))).encode("utf-8")


def uint64(namespace: str, *keys: object, counter: int = 0) -> int:
    return struct.unpack(">Q", hashlib.sha256(_payload(namespace, keys, counter)).digest()[:8])[0]


def uniform(namespace: str, *keys: object, counter: int = 0) -> float:
    return (uint64(namespace, *keys, counter=counter) >> 11) * (1.0 / (1 << 53))


def bernoulli(probability: float, namespace: str, *keys: object, counter: int = 0) -> bool:
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability outside [0,1]")
    return uniform(namespace, *keys, counter=counter) < probability


def glorot_vector(size: int, *keys: object) -> list[float]:
    if type(size) is not int or size <= 0:
        raise ValueError("invalid Glorot size")
    limit = math.sqrt(6.0 / (size + 1))
    return [(2 * uniform("bc-init", *keys, index) - 1) * limit for index in range(size)]


def contract_record() -> dict[str, object]:
    return {"version": RNG_VERSION, "counter_addressed": True, "namespaces": sorted(NAMESPACES)}
