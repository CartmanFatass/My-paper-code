"""Counter-addressed deterministic pseudo-random tapes.

Registered calls are made only by production. Tests use a ``fixture`` phase.
"""

from __future__ import annotations

import hashlib
import json
from typing import Iterable

import numpy as np

from .config import REVISION


def _seed(address: Iterable[object]) -> int:
    payload = json.dumps([REVISION, *address], separators=(",", ":"), ensure_ascii=True).encode()
    return int.from_bytes(hashlib.blake2b(payload, digest_size=16).digest(), "little")


def generator(*address: object) -> np.random.Generator:
    return np.random.Generator(np.random.PCG64(_seed(address)))


def nonidentity_permutation(rng: np.random.Generator, n: int) -> np.ndarray:
    identity = np.arange(n, dtype=np.int16)
    while True:
        candidate = rng.permutation(n).astype(np.int16, copy=False)
        if not np.array_equal(candidate, identity):
            return candidate


def tapes_for_decisions(
    phase: str,
    seed: int,
    group: tuple[object, ...],
    batch: int,
    n: int,
    *,
    include_training_presentations: bool = False,
) -> dict[str, np.ndarray]:
    rng = generator(phase, seed, *group)
    priorities = np.empty((batch, n), dtype=np.int16)
    uniforms = rng.random((batch, n), dtype=np.float64)
    row_permutations = np.empty((batch, n), dtype=np.int16)
    task_permutations = np.empty((batch, 4), dtype=np.int16)
    for i in range(batch):
        priorities[i] = rng.permutation(n)
        if include_training_presentations:
            row_permutations[i] = rng.permutation(n)
            task_permutations[i] = rng.permutation(4)
        else:
            row_permutations[i] = np.arange(n, dtype=np.int16)
            task_permutations[i] = np.arange(4, dtype=np.int16)
    return {
        "priority_ranks": priorities,
        "action_uniforms": uniforms,
        "row_permutations": row_permutations,
        "task_permutations": task_permutations,
    }


def replay_permutations(seed: int, group: tuple[object, ...], batch: int, n: int) -> dict[str, np.ndarray]:
    rng = generator("evaluation_replay", seed, *group)
    rows = np.empty((batch, n), dtype=np.int16)
    tasks = np.empty((batch, 4), dtype=np.int16)
    for i in range(batch):
        rows[i] = nonidentity_permutation(rng, n)
        tasks[i] = nonidentity_permutation(rng, 4)
    return {"row_permutations": rows, "task_permutations": tasks}
