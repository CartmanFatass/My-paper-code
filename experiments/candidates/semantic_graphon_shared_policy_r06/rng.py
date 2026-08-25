from __future__ import annotations

import hashlib
import math

import numpy as np

from .authorization import ProductionPermit, require_active_permit
from .config import COUNTER_ROOT

_UINT64_RANGE = 1 << 64


def _digest(permit: ProductionPermit, *address: object) -> bytes:
    require_active_permit(permit)
    payload = "\x1f".join((COUNTER_ROOT, *(str(field) for field in address))).encode("utf-8")
    return hashlib.blake2b(payload, digest_size=16).digest()


def _uint64(permit: ProductionPermit, *address: object) -> int:
    return int.from_bytes(_digest(permit, *address)[:8], "little", signed=False)


def _uniform01(permit: ProductionPermit, *address: object) -> float:
    """Prospectively registered counter-addressed binary64 U[0,1)."""
    return (_uint64(permit, *address) >> 11) * (1.0 / (1 << 53))


def _bounded_integer(permit: ProductionPermit, bound: int, *address: object) -> int:
    """Unbiased integer in [0,bound), using counter-addressed rejection."""
    if bound <= 0 or bound > _UINT64_RANGE:
        raise ValueError("bound must be in [1,2^64]")
    limit = _UINT64_RANGE - (_UINT64_RANGE % bound)
    rejection = 0
    while True:
        value = _uint64(permit, *address, "bounded_rejection", rejection)
        if value < limit:
            return value % bound
        rejection += 1


def initialization_uniform(
    permit: ProductionPermit, seed: int, layer: str, row: int, column: int,
) -> float:
    return _uniform01(permit, seed, "initialization", layer, row, column)


def orientation_uniform(
    permit: ProductionPermit, phase: str, seed: int, n: int, regime: str, episode: int,
) -> float:
    return _uniform01(permit, phase, seed, n, regime, episode, "orientation")


def gaussian_member(
    permit: ProductionPermit,
    phase: str, seed: int, n: int, regime: str, episode: int,
    role: int, within_role_slot: int,
) -> float:
    prefix = (phase, seed, n, regime, episode, role, within_role_slot, "gaussian")
    u1 = max(_uniform01(permit, *prefix, "u1"), 2.0 ** -53)
    u2 = _uniform01(permit, *prefix, "u2")
    return math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)


def action_uniform(
    permit: ProductionPermit,
    phase: str, seed: int, n: int, regime: str, episode: int,
    role: int, within_role_slot: int,
) -> float:
    return _uniform01(
        permit, phase, seed, n, regime, episode, role, within_role_slot, "action",
    )


def _candidate_permutation(
    permit: ProductionPermit, n: int, phase: str, seed: int,
    regime: str, episode: int, attempt: int,
) -> np.ndarray:
    order = list(range(n))
    prefix = (
        phase, seed, n, regime, episode, "identity_replay_permutation", attempt,
    )
    for stop in range(n - 1, 0, -1):
        index = _bounded_integer(permit, stop + 1, *prefix, "shuffle_stop", stop)
        order[stop], order[index] = order[index], order[stop]
    return np.asarray(order, dtype=np.int64)


def forced_nonidentity_audit_permutation(
    permit: ProductionPermit, seed: int, n: int, regime: str, episode: int,
) -> np.ndarray:
    """Uniform permutation conditioned on nonidentity, with addressed attempts."""
    identity = np.arange(n, dtype=np.int64)
    attempt = 0
    while True:
        candidate = _candidate_permutation(
            permit, n, "evaluation", seed, regime, episode, attempt,
        )
        if not bool(np.array_equal(candidate, identity)):
            return candidate
        attempt += 1
