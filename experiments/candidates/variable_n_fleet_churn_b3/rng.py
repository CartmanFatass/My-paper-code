from __future__ import annotations

import hashlib
from typing import Iterable

import numpy as np

NAMESPACE = "vnfc-b3-sp-rda-v1"


def counter_seed(*keys: object) -> int:
    payload = "\x1f".join((NAMESPACE, *(str(k) for k in keys))).encode("utf-8")
    return int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(), "little")


def generator(*keys: object) -> np.random.Generator:
    return np.random.default_rng(counter_seed(*keys))


def opaque_handle(seed: int, split: str, sequence: int, block: int, row: int) -> str:
    raw = f"{NAMESPACE}|{seed}|{split}|{sequence}|{block}|{row}".encode()
    return hashlib.blake2b(raw, digest_size=12).hexdigest()


def stable_rank(handle: str, *world_keys: object) -> int:
    return counter_seed("tie-rank", *world_keys, handle)


def counter_permutation(values: Iterable[int], *keys: object) -> list[int]:
    values = list(values)
    return [values[i] for i in generator("perm", *keys).permutation(len(values))]
