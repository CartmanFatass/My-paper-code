"""Stateless, arm-independent BLAKE2b counter-addressed randomness."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Iterable, Sequence, TypeVar

import torch

from .authorization import ProductionPermit
from .config import (
    COUNTER_ROOT, DEVICE, EVALUATION_EPISODES,
    REGISTERED_ROSTERS, SEEDS, TRAINING_DTYPE, TRAINING_UPDATES,
    TRAIN_ROSTERS, EPISODES_PER_UPDATE,
)


T = TypeVar("T")
_INV_TWO_POW_53 = 1.0 / (1 << 53)
_UINT64_RANGE = 1 << 64


def _payload(root: str, address: Sequence[object]) -> bytes:
    # This is the registered blake2b-counter-v1 framing used by the project.
    return "\x1f".join((root, *(str(field) for field in address))).encode("utf-8")


@dataclass(frozen=True)
class Coordinate:
    """One arm-independent world coordinate."""

    phase: str
    seed: int
    roster: int
    episode: int
    update: int | None = None

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Fail closed on every coordinate outside the frozen panel geometry."""
        if self.seed not in SEEDS:
            raise ValueError("coordinate seed is outside the frozen panel")
        if self.phase == "training":
            if self.update not in range(1, TRAINING_UPDATES + 1):
                raise ValueError("training coordinate update must be 1..512")
            if self.episode not in range(EPISODES_PER_UPDATE):
                raise ValueError("training coordinate episode must be 0..63")
            expected_roster = TRAIN_ROSTERS[self.episode % 2]
            if self.roster != expected_roster:
                raise ValueError(
                    "training coordinate roster must follow the frozen alternating batch order"
                )
        elif self.phase == "evaluation":
            if self.roster not in REGISTERED_ROSTERS:
                raise ValueError("evaluation coordinate roster is not registered")
            if self.update is not None:
                raise ValueError("evaluation coordinates have no training update")
            if self.episode not in range(EVALUATION_EPISODES):
                raise ValueError("evaluation coordinate episode must be 0..255")
        else:
            raise ValueError("coordinate phase must be training or evaluation")

    def address(self) -> tuple[object, ...]:
        self.validate()
        return (
            "phase", self.phase,
            "training_seed", self.seed,
            "roster", self.roster,
            "update", self.update,
            "episode", self.episode,
        )


class CounterRNG:
    """Random-access potential outcomes with no mutable or conditional stream."""

    def __init__(self, permit: ProductionPermit, root: str = COUNTER_ROOT) -> None:
        if not isinstance(permit, ProductionPermit):
            raise PermissionError("validated ProductionPermit is required")
        permit.assert_local_validity()
        if root != COUNTER_ROOT:
            raise ValueError("the r03 counter root is immutable")
        self._permit = permit
        self.root = root

    def _require(self) -> None:
        if not isinstance(self._permit, ProductionPermit):
            raise PermissionError("validated ProductionPermit is required")
        self._permit.assert_local_validity()

    def require_same_permit(self, permit: ProductionPermit) -> None:
        if not isinstance(permit, ProductionPermit):
            raise PermissionError("validated ProductionPermit is required")
        permit.assert_local_validity()
        self._require()
        if permit is not self._permit:
            raise PermissionError("CounterRNG belongs to a different ProductionPermit")

    def uint64(self, *address: object) -> int:
        self._require()
        digest = hashlib.blake2b(_payload(self.root, address), digest_size=16).digest()
        return int.from_bytes(digest[:8], byteorder="little", signed=False)

    def uniform(self, *address: object) -> float:
        self._require()
        # Prospectively registered binary64 U[0,1) construction.
        mantissa = self.uint64(*address) >> 11
        return mantissa * _INV_TWO_POW_53

    def bernoulli(self, probability: float, *address: object) -> bool:
        self._require()
        if not 0.0 <= probability <= 1.0:
            raise ValueError("probability must be in [0,1]")
        return self.uniform(*address) < probability

    def bounded_integer(self, bound: int, *address: object) -> int:
        """Unbiased addressed integer in [0,bound), including addressed rejection."""
        self._require()
        if bound <= 0 or bound > _UINT64_RANGE:
            raise ValueError("bound must be in [1,2^64]")
        limit = _UINT64_RANGE - (_UINT64_RANGE % bound)
        rejection = 0
        while True:
            value = self.uint64(*address, "bounded-rejection", rejection)
            if value < limit:
                return value % bound
            rejection += 1

    def normal(self, *address: object) -> float:
        self._require()
        # Box-Muller uses two separately named potential outcomes at this exact
        # semantic address; it never advances a stream.
        u1 = max(self.uniform(*address, "normal-u1"), 2.0 ** -53)
        u2 = self.uniform(*address, "normal-u2")
        return math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)

    def sample_without_replacement(
        self, population: Sequence[T], count: int, *address: object
    ) -> tuple[T, ...]:
        self._require()
        if count < 0 or count > len(population):
            raise ValueError("invalid sample count")
        order = list(range(len(population)))
        for stop in range(len(order) - 1, 0, -1):
            index = self.bounded_integer(stop + 1, *address, "shuffle-stop", stop)
            order[stop], order[index] = order[index], order[stop]
        return tuple(population[index] for index in order[:count])

    def uniform_tensor(
        self,
        shape: Iterable[int],
        low: float,
        high: float,
        *address: object,
        dtype: torch.dtype = TRAINING_DTYPE,
    ) -> torch.Tensor:
        self._require()
        dims = tuple(int(dim) for dim in shape)
        count = math.prod(dims)
        values = [
            low + (high - low) * self.uniform(*address, "flat-index", index)
            for index in range(count)
        ]
        return torch.tensor(values, dtype=dtype, device=DEVICE).reshape(dims)

    def normal_tensor(
        self,
        shape: Iterable[int],
        *address: object,
        dtype: torch.dtype = TRAINING_DTYPE,
    ) -> torch.Tensor:
        self._require()
        dims = tuple(int(dim) for dim in shape)
        count = math.prod(dims)
        values = [self.normal(*address, "flat-index", index) for index in range(count)]
        return torch.tensor(values, dtype=dtype, device=DEVICE).reshape(dims)


def inverse_cdf_index(probabilities: Sequence[float], uniform: float) -> int:
    """Sample an index from a supplied addressed uniform without renormalizing."""
    if not 0.0 <= uniform < 1.0:
        raise ValueError("the addressed uniform must be in [0,1)")
    cumulative = 0.0
    for index, probability in enumerate(probabilities):
        if probability < 0.0 or not math.isfinite(probability):
            raise ValueError("invalid categorical probability")
        cumulative += probability
        if uniform < cumulative:
            return index
    if not probabilities or abs(cumulative - 1.0) > 1.0e-5:
        raise ValueError("categorical probabilities do not sum to one")
    return len(probabilities) - 1
