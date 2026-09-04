"""Event processes for the relay corridor host (pure NumPy + :mod:`math`).

Mechanics page, "Hazard":

* E3 draws one Bernoulli event per region per transition at rate
  :math:`\\lambda_r`.
* E4 instead holds :math:`\\theta_r` for a positive-integer duration ``D``.
  Deterministic episodes start with a **full** dwell of length ``D``, so events
  occur at ``D, 2D, ...`` and fixed boundaries ``0, D, 2D, ...`` are aligned; no
  stationary residual-life phase is sampled.  Deterministic ``D`` has variance
  ``0``; "discrete exponential" means geometric with mean ``mu`` and variance
  ``mu * (mu - 1)``; discrete lognormal uses ``D = max(1, floor(X + 1/2))`` with
  the log-location calibrated to ``E[D] = mu`` and the variance summed from its
  CDF-bin masses.  **Only** ``E[D]`` is matched across the three laws.

Every law is represented to the host and to the dynamic programme by the same
object: a *discrete hazard table* ``h(a) = P(D = a + 1 | D > a)`` indexed by the
dwell age ``a`` (age ``0`` immediately after an event, and at reset).  Stepping
by hazard reproduces the dwell law exactly, is one vectorized comparison per
transition, and makes the "full initial dwell" convention automatic: at reset
the age is ``0``, so the first dwell is a complete draw from ``D``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from typing import Tuple

import numpy as np

__all__ = [
    "RenewalLaw",
    "BernoulliHazard",
    "DeterministicLaw",
    "GeometricLaw",
    "RoundedLognormalLaw",
    "make_renewal_law",
    "normal_cdf",
]

_SQRT2 = math.sqrt(2.0)
_ERF = np.vectorize(math.erf, otypes=[np.float64])


def normal_cdf(z: np.ndarray) -> np.ndarray:
    """Standard normal CDF, ``math.erf`` based (no SciPy dependency)."""
    return 0.5 * (1.0 + _ERF(np.asarray(z, dtype=np.float64) / _SQRT2))


@dataclass(frozen=True)
class RenewalLaw:
    """Base class: a positive-integer dwell law expressed as a hazard table."""

    name: str

    def mean(self) -> float:
        raise NotImplementedError

    def variance(self) -> float:
        raise NotImplementedError

    def hazard_table(self, max_age: int) -> np.ndarray:
        """``h[a]`` for ``a = 0 .. max_age``."""
        raise NotImplementedError

    def dp_age_cap(self, horizon: int) -> int:
        """Smallest age ``A`` beyond which the hazard is constant.

        The dynamic programme collapses every age ``>= A`` onto ``A``; this is
        exact whenever ``h(a) == h(A)`` for all ``a >= A``.
        """
        raise NotImplementedError


@dataclass(frozen=True)
class BernoulliHazard(RenewalLaw):
    """E3: one Bernoulli event per transition at rate ``lam``.

    Equivalent to a geometric dwell with ``p = lam``; kept as its own class so
    that the E3 configuration reads as the mechanics page writes it.
    """

    lam: float = 0.0

    def mean(self) -> float:
        if self.lam <= 0.0:
            return math.inf
        return 1.0 / self.lam

    def variance(self) -> float:
        if self.lam <= 0.0:
            return math.inf
        mu = 1.0 / self.lam
        return mu * (mu - 1.0)

    def hazard_table(self, max_age: int) -> np.ndarray:
        return np.full(int(max_age) + 1, float(self.lam), dtype=np.float64)

    def dp_age_cap(self, horizon: int) -> int:
        return 1


@dataclass(frozen=True)
class DeterministicLaw(RenewalLaw):
    """``D`` is the constant positive integer ``duration``; ``Var(D) = 0``."""

    duration: int = 1

    def mean(self) -> float:
        return float(self.duration)

    def variance(self) -> float:
        return 0.0

    def hazard_table(self, max_age: int) -> np.ndarray:
        table = np.zeros(int(max_age) + 1, dtype=np.float64)
        # Ages beyond duration - 1 are unreachable; pinning them to 1.0 keeps
        # the table total even if a caller asks for a longer one.
        table[min(self.duration - 1, int(max_age)):] = 1.0
        return table

    def dp_age_cap(self, horizon: int) -> int:
        return max(1, int(self.duration) - 1)


@dataclass(frozen=True)
class GeometricLaw(RenewalLaw):
    """Discrete exponential: ``P(D = d) = (1 - p)^(d - 1) p`` with ``p = 1 / mu``."""

    mu: float = 1.0

    @property
    def p(self) -> float:
        return 1.0 / float(self.mu)

    def mean(self) -> float:
        return float(self.mu)

    def variance(self) -> float:
        mu = float(self.mu)
        return mu * (mu - 1.0)

    def hazard_table(self, max_age: int) -> np.ndarray:
        return np.full(int(max_age) + 1, self.p, dtype=np.float64)

    def dp_age_cap(self, horizon: int) -> int:
        return 1


@lru_cache(maxsize=32)
def _calibrate_lognormal(mu: float, shape: float) -> Tuple[float, int]:
    """Solve for the log-location that makes ``E[max(1, floor(X + 1/2))] = mu``.

    Returns ``(log_location, dmax)`` where ``dmax`` is the support truncation
    used for the calibration and for the reported moments.
    """
    s = float(shape)
    target = float(mu)
    if s <= 0.0:
        raise ValueError("lognormal_shape must be positive")
    if target < 1.0:
        raise ValueError("renewal_mean must be at least 1 for a positive-integer dwell")

    m0 = math.log(target) - 0.5 * s * s
    dmax = int(min(500_000, max(2_000, math.ceil(math.exp(m0 + 9.0 * s)))))

    def mean_at(m: float, cap: int) -> float:
        return float(_lognormal_moments(m, s, cap)[0])

    # Stage 1: cheap bisection on a coarse truncation to bracket the root.
    coarse = min(dmax, 4_000)
    lo, hi = m0 - 4.0 * s - 2.0, m0 + 4.0 * s + 2.0
    for _ in range(90):
        mid = 0.5 * (lo + hi)
        if mean_at(mid, coarse) < target:
            lo = mid
        else:
            hi = mid
    m1 = 0.5 * (lo + hi)

    # Stage 2: secant refinement on the full truncation.
    a, b = m1 - 1e-3, m1 + 1e-3
    fa = mean_at(a, dmax) - target
    fb = mean_at(b, dmax) - target
    for _ in range(60):
        if fb == fa:
            break
        c = b - fb * (b - a) / (fb - fa)
        fc = mean_at(c, dmax) - target
        a, fa, b, fb = b, fb, c, fc
        if abs(fc) <= 1e-12 * target:
            break
    return float(b), dmax


@lru_cache(maxsize=256)
def _lognormal_moments(m: float, s: float, dmax: int) -> Tuple[float, float, float]:
    """``(mean, second moment, total mass)`` of ``max(1, floor(X + 1/2))``."""
    d = np.arange(1, int(dmax) + 1, dtype=np.float64)
    upper = normal_cdf((np.log(d + 0.5) - m) / s)
    lower = normal_cdf((np.log(d - 0.5) - m) / s)
    pmf = upper - lower
    # D = 1 absorbs every X < 1.5 (the lognormal support is (0, inf)).
    pmf[0] = upper[0]
    mean = float(np.dot(d, pmf))
    second = float(np.dot(d * d, pmf))
    return mean, second, float(pmf.sum())


@dataclass(frozen=True)
class RoundedLognormalLaw(RenewalLaw):
    """``D = max(1, floor(X + 1/2))`` with ``X`` lognormal, mean-calibrated."""

    mu: float = 1.0
    shape: float = 1.0

    @property
    def log_location(self) -> float:
        return _calibrate_lognormal(float(self.mu), float(self.shape))[0]

    @property
    def support_cap(self) -> int:
        return _calibrate_lognormal(float(self.mu), float(self.shape))[1]

    def _moments(self) -> Tuple[float, float, float]:
        m, dmax = _calibrate_lognormal(float(self.mu), float(self.shape))
        return _lognormal_moments(m, float(self.shape), dmax)

    def mean(self) -> float:
        return self._moments()[0]

    def variance(self) -> float:
        mean, second, _mass = self._moments()
        return second - mean * mean

    def pmf(self, dmax: int) -> np.ndarray:
        m = self.log_location
        s = float(self.shape)
        d = np.arange(1, int(dmax) + 1, dtype=np.float64)
        upper = normal_cdf((np.log(d + 0.5) - m) / s)
        lower = normal_cdf((np.log(d - 0.5) - m) / s)
        out = upper - lower
        out[0] = upper[0]
        return out

    def hazard_table(self, max_age: int) -> np.ndarray:
        # h(a) = P(D = a + 1) / P(D > a); ages 0 .. max_age need P(D = 1 .. max_age + 1).
        n = int(max_age) + 1
        pmf = self.pmf(n)
        survivor = 1.0 - np.concatenate(([0.0], np.cumsum(pmf)[:-1]))  # P(D > a)
        with np.errstate(divide="ignore", invalid="ignore"):
            hazard = np.where(survivor > 0.0, pmf / survivor, 1.0)
        return np.clip(hazard, 0.0, 1.0)

    def dp_age_cap(self, horizon: int) -> int:
        # The hazard is genuinely age dependent; ages above H - 1 are unreachable
        # inside an H-step episode, so that is an exact cap.
        return max(1, int(horizon) - 1)


def make_renewal_law(law: str, mean: float, shape: float = 1.0) -> RenewalLaw:
    """Build one of the three mean-matched E4 laws."""
    key = str(law).lower()
    if key == "deterministic":
        duration = int(round(float(mean)))
        if abs(duration - float(mean)) > 1e-9:
            raise ValueError(
                f"deterministic renewal_mean must be a positive integer, got {mean!r}"
            )
        if duration < 1:
            raise ValueError("deterministic dwell must be at least 1")
        return DeterministicLaw(name="deterministic", duration=duration)
    if key == "geometric":
        if not (float(mean) >= 1.0):
            raise ValueError("geometric renewal_mean must be at least 1")
        return GeometricLaw(name="geometric", mu=float(mean))
    if key == "lognormal":
        return RoundedLognormalLaw(name="lognormal", mu=float(mean), shape=float(shape))
    raise ValueError(
        f"renewal_law must be one of deterministic|geometric|lognormal, got {law!r}"
    )
