"""Exact-revision counter-addressed PCG64 namespaces."""

from __future__ import annotations

import hashlib
import json

import numpy as np

from .authorization import ProductionPermit, require_active_permit
from .config import DIRECTION, REVISION


def _seed(address: tuple[object, ...]) -> int:
    payload = json.dumps(
        [DIRECTION, REVISION, *address], separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    return int.from_bytes(hashlib.blake2b(payload, digest_size=16).digest(), "little")


def generator(permit: ProductionPermit, *address: object) -> np.random.Generator:
    require_active_permit(permit)
    return np.random.Generator(np.random.PCG64(_seed(address)))


def uniform(permit: ProductionPermit, *address: object) -> float:
    return float(generator(permit, *address).random())


def categorical4(permit: ProductionPermit, *address: object) -> int:
    return int(generator(permit, *address).integers(0, 4))


def permutation4(permit: ProductionPermit, *address: object) -> np.ndarray:
    return generator(permit, *address).permutation(4).astype(np.int64, copy=False)
