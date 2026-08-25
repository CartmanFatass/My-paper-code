"""Counter-keyed randomness; all exogenous and coupling coordinates are explicit."""

from __future__ import annotations

import hashlib


def counter_u64(namespace: str, *coordinates: object) -> int:
    payload = "\x1f".join((namespace, *(str(v) for v in coordinates))).encode("utf-8")
    return int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(), "little")


def counter_uniform(namespace: str, *coordinates: object) -> float:
    return ((counter_u64(namespace, *coordinates) >> 11) + 0.5) / float(1 << 53)


def counter_bit(namespace: str, *coordinates: object) -> int:
    return int(counter_u64(namespace, *coordinates) & 1)


def counter_bernoulli(probability: float, namespace: str, *coordinates: object) -> int:
    return int(counter_uniform(namespace, *coordinates) < probability)


def namespace_seed(namespace: str, *coordinates: object) -> int:
    return counter_u64(namespace, *coordinates) % (2**31 - 1)
