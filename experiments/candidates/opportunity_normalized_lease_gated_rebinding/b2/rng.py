"""Fresh B2-only counter-keyed random domains."""

from __future__ import annotations

import hashlib

_PREFIX = "ONLGR_B2_REV02"


def counter_u64(domain: str, *coordinates: object) -> int:
    payload = "\x1f".join((_PREFIX, domain, *(str(v) for v in coordinates))).encode("utf-8")
    return int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(), "little")


def counter_uniform(domain: str, *coordinates: object) -> float:
    return ((counter_u64(domain, *coordinates) >> 11) + 0.5) / float(1 << 53)


def counter_bit(domain: str, *coordinates: object) -> int:
    return int(counter_u64(domain, *coordinates) & 1)


def counter_bernoulli(probability: float, domain: str, *coordinates: object) -> int:
    return int(counter_uniform(domain, *coordinates) < probability)


def namespace_seed(domain: str, *coordinates: object) -> int:
    return counter_u64(domain, *coordinates) % (2**31 - 1)
