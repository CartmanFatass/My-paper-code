from __future__ import annotations

import hashlib
import hmac
import json
import os
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import TypeVar

from .config import DOMAIN_LABELS, HMAC_SEED_NAMESPACE, SEED_INDICES

T = TypeVar("T")
UINT64_LIMIT = 1 << 64


def sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def seed_key(master: bytes, seed_index: int) -> bytes:
    if len(master) != 32 or seed_index not in SEED_INDICES:
        raise ValueError("master must be 32 bytes and seed index must be 0,...,9")
    return hmac.new(
        master, HMAC_SEED_NAMESPACE + seed_index.to_bytes(4, "big"), hashlib.sha256,
    ).digest()


def domain_key(key: bytes, label: str) -> bytes:
    if label not in DOMAIN_LABELS:
        raise ValueError(f"unregistered SRF r03 RNG domain: {label}")
    return hmac.new(key, label.encode("utf-8"), hashlib.sha256).digest()


class HMACStream:
    """FIPS HMAC-SHA-256 stream yielding nonoverlapping big-endian uint64 words."""

    def __init__(self, key: bytes) -> None:
        if len(key) != 32:
            raise ValueError("HMAC stream keys must be 32 bytes")
        self.key = key
        self.counter = 0
        self._words: tuple[int, ...] = ()
        self._offset = 0
        self.draw_count = 0

    @classmethod
    def for_domain(cls, master: bytes, seed_index: int, label: str) -> "HMACStream":
        return cls(domain_key(seed_key(master, seed_index), label))

    def raw_u64(self) -> int:
        if self._offset == len(self._words):
            block = hmac.new(
                self.key, self.counter.to_bytes(8, "big"), hashlib.sha256,
            ).digest()
            self.counter += 1
            self._words = tuple(
                int.from_bytes(block[start:start + 8], "big")
                for start in range(0, 32, 8)
            )
            self._offset = 0
        value = self._words[self._offset]
        self._offset += 1
        self.draw_count += 1
        return value

    def uniform53(self) -> float:
        return (self.raw_u64() >> 11) * (2.0 ** -53)

    def uniform(self, low: float, high: float) -> float:
        return float(low + (high - low) * self.uniform53())

    def bounded(self, modulus: int) -> int:
        if modulus <= 0:
            raise ValueError("bounded integer modulus must be positive")
        limit = (UINT64_LIMIT // modulus) * modulus
        while True:
            raw = self.raw_u64()
            if raw < limit:
                return raw % modulus

    def shuffle(self, values: list[T]) -> None:
        for index in range(len(values) - 1, 0, -1):
            other = self.bounded(index + 1)
            values[index], values[other] = values[other], values[index]


def balanced_roster(values: Sequence[T], count: int, stream: HMACStream) -> list[T]:
    if not values or count < 0:
        raise ValueError("balanced roster needs nonempty values and nonnegative count")
    repeats, remainder = divmod(count, len(values))
    roster = list(values) * repeats
    if remainder:
        choices = list(values)
        stream.shuffle(choices)
        roster.extend(choices[:remainder])
    stream.shuffle(roster)
    return roster


def identity_digests(master: bytes) -> tuple[str, tuple[str, ...]]:
    return sha256_hex(master), tuple(
        sha256_hex(seed_key(master, seed_index)) for seed_index in SEED_INDICES
    )


def manifest_digests(root: Path) -> set[str]:
    digests: set[str] = set()
    if not root.exists():
        return digests
    for path in root.rglob("*.json"):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        stack: list[object] = [value]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                for key, child in item.items():
                    if key in {"panel_digest", "seed_digest", "master_digest"} \
                            and isinstance(child, str) and len(child) == 64:
                        try:
                            int(child, 16)
                        except ValueError:
                            pass
                        else:
                            digests.add(child.lower())
                    elif key == "seed_digests" and isinstance(child, list):
                        for digest in child:
                            if isinstance(digest, str) and len(digest) == 64:
                                try:
                                    int(digest, 16)
                                except ValueError:
                                    continue
                                digests.add(digest.lower())
                    else:
                        stack.append(child)
            elif isinstance(item, list):
                stack.extend(item)
    return digests


def sample_fresh_master(
    existing: Iterable[str], source: Callable[[int], bytes] = os.urandom,
) -> bytes:
    occupied = {value.lower() for value in existing}
    while True:
        master = source(32)
        if len(master) != 32:
            raise RuntimeError("operating-system master source returned the wrong byte count")
        panel, seeds = identity_digests(master)
        if panel not in occupied and occupied.isdisjoint(seeds):
            return master
