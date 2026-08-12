"""Deterministic PCG64 streams for CRTO-B1.

The module deliberately separates the card's literal seed formulas from
episode-local engineering namespaces.  Callers must supply episode seeds; this
module never obtains entropy from the process, clock, Python hash seed, or an
ambient global NumPy generator.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import IntEnum
from math import exp, isfinite
from typing import Mapping, Sequence, TypeVar

import numpy as np
from numpy.random import Generator, PCG64, SeedSequence

from .config import (
    ALGORITHM_SEEDS,
    DERANGEMENT_SEED_BASE,
    DERANGEMENT_SEED_MULTIPLIER,
    LEARNED_INITIALIZATION_SEED_OFFSET,
    PREDICTOR_INITIALIZATION_SEED_OFFSET,
    PREDICTOR_PERMUTATION_SEED_OFFSET,
    PROBE_INITIALIZATION_SEED_OFFSET,
    PROBE_PERMUTATION_SEED_OFFSET,
)

TREND_MONTE_CARLO_SEED = 9_000_001


class StreamNamespace(IntEnum):
    """Stable episode-local stream identifiers.

    These identifiers only isolate deterministic mechanics.  They do not
    replace any literal seed formula specified by the science card.
    """

    PHYSICAL_TAPE = 1
    OPTION_SELECTION = 2
    RATE_CONTROL = 3
    MANIFEST_ORDER = 4


@dataclass(frozen=True)
class PCG64State:
    """A complete, JSON-compatible PCG64 state snapshot."""

    state: Mapping[str, object]

    @classmethod
    def capture(cls, generator: Generator) -> "PCG64State":
        _require_pcg64(generator)
        return cls(deepcopy(generator.bit_generator.state))

    def restore(self) -> Generator:
        generator = Generator(PCG64())
        generator.bit_generator.state = deepcopy(dict(self.state))
        _require_pcg64(generator)
        return generator


def _require_seed(seed: int) -> int:
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)):
        raise TypeError("PCG64 seed must be an integer")
    value = int(seed)
    if value < 0:
        raise ValueError("PCG64 seed must be nonnegative")
    return value


def _require_algorithm_seed(algorithm_seed: int) -> int:
    value = _require_seed(algorithm_seed)
    if value not in ALGORITHM_SEEDS:
        raise ValueError(f"unregistered CRTO-B1 algorithm seed: {value}")
    return value


def _require_pcg64(generator: Generator) -> None:
    if not isinstance(generator, Generator) or not isinstance(generator.bit_generator, PCG64):
        raise TypeError("generator must be numpy.random.Generator(PCG64)")


def pcg64(seed: int) -> Generator:
    """Return a fresh PCG64 generator initialized from a literal integer seed."""

    return Generator(PCG64(_require_seed(seed)))


def namespaced_pcg64(
    root_seed: int,
    namespace: StreamNamespace,
    *coordinates: int,
) -> Generator:
    """Return a deterministic, isolated episode-local PCG64 stream.

    ``SeedSequence`` receives only explicit nonnegative integers.  Consequently
    stream identity is stable across processes and Python versions and cannot
    depend on randomized string hashing.
    """

    if not isinstance(namespace, StreamNamespace):
        raise TypeError("namespace must be a StreamNamespace")
    entropy = [_require_seed(root_seed), int(namespace)]
    entropy.extend(_require_seed(value) for value in coordinates)
    return Generator(PCG64(SeedSequence(entropy)))


def clone_generator(generator: Generator) -> Generator:
    """Clone the complete PCG64 state, including cached uint32 state."""

    return PCG64State.capture(generator).restore()


def predictor_initialization_rng(algorithm_seed: int) -> Generator:
    return pcg64(PREDICTOR_INITIALIZATION_SEED_OFFSET + _require_algorithm_seed(algorithm_seed))


def predictor_example_order_rng(algorithm_seed: int) -> Generator:
    return pcg64(PREDICTOR_PERMUTATION_SEED_OFFSET + _require_algorithm_seed(algorithm_seed))


def probe_example_order_rng(algorithm_seed: int) -> Generator:
    return pcg64(PROBE_PERMUTATION_SEED_OFFSET + _require_algorithm_seed(algorithm_seed))


def probe_initialization_rng(algorithm_seed: int) -> Generator:
    return pcg64(PROBE_INITIALIZATION_SEED_OFFSET + _require_algorithm_seed(algorithm_seed))


def learned_components_initialization_rng(algorithm_seed: int) -> Generator:
    return pcg64(LEARNED_INITIALIZATION_SEED_OFFSET + _require_algorithm_seed(algorithm_seed))


def derangement_rng(algorithm_seed: int, cell_ordinal: int) -> Generator:
    seed = _require_algorithm_seed(algorithm_seed)
    ordinal = _require_seed(cell_ordinal)
    return pcg64(DERANGEMENT_SEED_BASE + DERANGEMENT_SEED_MULTIPLIER * seed + ordinal)


def trend_monte_carlo_rng() -> Generator:
    return pcg64(TREND_MONTE_CARLO_SEED)


def repeated_permutation_indices(
    size: int,
    updates: int,
    batch_size: int,
    generator: Generator,
) -> np.ndarray:
    """Materialize the card's one-permutation cyclic example order."""

    _require_pcg64(generator)
    if size <= 0 or updates < 0 or batch_size <= 0:
        raise ValueError("size and batch_size must be positive and updates nonnegative")
    count = updates * batch_size
    if count == 0:
        return np.empty(0, dtype=np.int64)
    permutation = generator.permutation(size).astype(np.int64, copy=False)
    return np.resize(permutation, count)


def uniform_derangement(
    size: int,
    generator: Generator,
    *,
    max_rejections: int = 10_000,
) -> tuple[int, ...]:
    """Draw the first fixed-point-free Fisher--Yates permutation.

    NumPy's ``Generator.permutation`` uses a uniform shuffle.  Rejecting every
    permutation with a fixed point therefore implements the frozen uniform
    derangement law without changing the attempt limit.
    """

    _require_pcg64(generator)
    if size < 2:
        raise ValueError("a derangement requires at least two records")
    if max_rejections != 10_000:
        raise ValueError("CRTO-B1 fixes max_rejections at 10,000")
    identity = np.arange(size, dtype=np.int64)
    for _ in range(max_rejections):
        permutation = generator.permutation(size).astype(np.int64, copy=False)
        if np.all(permutation != identity):
            return tuple(int(value) for value in permutation)
    raise RuntimeError("no fixed-point-free permutation in 10,000 draws")


T = TypeVar("T")


def categorical_from_logits(
    choices: Sequence[T],
    logits: Sequence[float],
    uniform: float,
) -> T:
    """Sample a temperature-one categorical with one preassigned uniform."""

    if not choices or len(choices) != len(logits):
        raise ValueError("choices and logits must have equal positive length")
    values = tuple(float(value) for value in logits)
    if not all(isfinite(value) for value in values):
        raise ValueError("categorical logits must be finite")
    u = float(uniform)
    if not isfinite(u) or u < 0.0 or u >= 1.0:
        raise ValueError("categorical uniform must lie in [0,1)")
    offset = max(values)
    weights = tuple(exp(value - offset) for value in values)
    total = sum(weights)
    threshold = u * total
    cumulative = 0.0
    for choice, weight in zip(choices, weights):
        cumulative += weight
        if threshold < cumulative:
            return choice
    return choices[-1]


def score_mapping(
    domain: Sequence[T],
    values: Mapping[T, float],
    *,
    label: str,
) -> tuple[float, ...]:
    """Validate and order a score mapping on an exact domain."""

    missing = [item for item in domain if item not in values]
    if missing:
        raise ValueError(f"{label} is missing {missing!r}")
    ordered = tuple(float(values[item]) for item in domain)
    if not all(isfinite(value) for value in ordered):
        raise ValueError(f"{label} must contain only finite values")
    return ordered


__all__ = [
    "ALGORITHM_SEEDS",
    "PCG64State",
    "StreamNamespace",
    "TREND_MONTE_CARLO_SEED",
    "categorical_from_logits",
    "clone_generator",
    "derangement_rng",
    "learned_components_initialization_rng",
    "namespaced_pcg64",
    "pcg64",
    "predictor_example_order_rng",
    "predictor_initialization_rng",
    "probe_example_order_rng",
    "probe_initialization_rng",
    "repeated_permutation_indices",
    "score_mapping",
    "trend_monte_carlo_rng",
    "uniform_derangement",
]
