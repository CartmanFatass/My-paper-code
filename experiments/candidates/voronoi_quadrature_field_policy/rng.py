"""Counter-keyed random streams; no panel may consume another panel's stream."""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np
import torch


def _key_seed(*parts: Any) -> int:
    payload = repr(parts).encode("utf-8")
    return int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(), "little")


class CounterRNG:
    """Stateless deterministic draw factory keyed only by an explicit namespace."""

    def __init__(self, *namespace: Any) -> None:
        self.namespace = tuple(namespace)

    def child(self, *parts: Any) -> "CounterRNG":
        return CounterRNG(*self.namespace, *parts)

    def numpy(self, *parts: Any) -> np.random.Generator:
        return np.random.default_rng(_key_seed(*self.namespace, *parts))

    def uniform(self, shape: tuple[int, ...], *parts: Any, device: torch.device | None = None) -> torch.Tensor:
        values = self.numpy(*parts).random(shape, dtype=np.float64)
        return torch.as_tensor(values, dtype=torch.float32, device=device)

    def normal(self, shape: tuple[int, ...], mean: float, std: float, *parts: Any, device: torch.device | None = None) -> torch.Tensor:
        values = self.numpy(*parts).normal(mean, std, shape)
        return torch.as_tensor(values, dtype=torch.float32, device=device)

    def gamma(self, shape: tuple[int, ...], alpha: float, *parts: Any, device: torch.device | None = None) -> torch.Tensor:
        values = self.numpy(*parts).gamma(alpha, 1.0, shape)
        return torch.as_tensor(values, dtype=torch.float32, device=device)

    def permutation(self, n: int, *parts: Any, device: torch.device | None = None) -> torch.Tensor:
        values = self.numpy(*parts).permutation(n)
        return torch.as_tensor(values, dtype=torch.long, device=device)
