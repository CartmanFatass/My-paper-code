from __future__ import annotations

import hashlib
import math


def counter_u64(namespace: str, *coordinates: object) -> int:
    payload = "\x1f".join((namespace, *(str(value) for value in coordinates))).encode("utf-8")
    return int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(), "little")


def counter_uniform(namespace: str, *coordinates: object) -> float:
    return ((counter_u64(namespace, *coordinates) >> 11) + 0.5) / float(1 << 53)


def counter_bit(namespace: str, *coordinates: object) -> int:
    return int(counter_u64(namespace, *coordinates) & 1)


def counter_bernoulli(probability: float, namespace: str, *coordinates: object) -> int:
    return int(counter_uniform(namespace, *coordinates) < probability)


def counter_permutation(length: int, namespace: str, *coordinates: object) -> tuple[int, ...]:
    return tuple(sorted(range(length), key=lambda index: counter_u64(namespace, *coordinates, index)))


def namespace_seed(namespace: str, *coordinates: object) -> int:
    return counter_u64(namespace, *coordinates) % (2**31 - 1)


def stationary_ready(namespace: str, *coordinates: object) -> int:
    # P(0->1)=.5 and P(1->0)=.1 gives pi(ready)=5/6.
    return int(counter_uniform(namespace, *coordinates) < (5.0 / 6.0))


def finite(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("non-finite numerical result")
    return float(value)
