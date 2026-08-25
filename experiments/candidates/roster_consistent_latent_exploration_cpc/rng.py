"""Exact-revision counter-addressed CPC product-family materializer."""

from __future__ import annotations

import hashlib
import json

import numpy as np

from .authorization import ProductionPermit, require_active_permit
from .config import DIRECTION, REVISION, RNG_BINDING


def _seed(address: tuple[object, ...]) -> int:
    payload = json.dumps(
        [DIRECTION, REVISION, RNG_BINDING, *address], separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    return int.from_bytes(hashlib.blake2b(payload, digest_size=16).digest(), "little")


def generator(permit: ProductionPermit, *address: object) -> np.random.Generator:
    require_active_permit(permit)
    return np.random.Generator(np.random.PCG64(_seed(address)))


def uniform(permit: ProductionPermit, *address: object) -> float:
    return float(generator(permit, *address).random())

