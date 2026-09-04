"""Deterministic construction of the frozen B3 fixed-policy families."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Mapping, Sequence

import numpy as np

from .config import EXPOSURE_MAX, EXPOSURE_SPLIT, LAMBDA_REF, LOGIT_OFFSETS


def exposure_bin(exposure: float) -> str:
    value = float(exposure)
    if not 0.0 <= value <= EXPOSURE_MAX:
        raise ValueError(f"exposure outside frozen [0,32] range: {value}")
    return "low" if value < EXPOSURE_SPLIT else "high"


def q_from_exposures(exposures: Iterable[float], rate: float = LAMBDA_REF) -> float:
    values = np.asarray(tuple(exposures), dtype=np.float64)
    if values.size == 0 or np.any(values <= 0.0) or np.any(values > EXPOSURE_MAX):
        raise ValueError("F0 requires one or more legal exposures in (0,32]")
    if rate < 0.0 or not math.isfinite(rate):
        raise ValueError("rate must be finite and nonnegative")
    return float(np.mean(-np.expm1(-np.float64(rate) * values), dtype=np.float64))


def shifted_probability_grid(q0: float) -> tuple[float, ...]:
    if not 0.0 < q0 < 1.0:
        raise ValueError("q0 must be strictly between zero and one")
    logit = math.log(q0) - math.log1p(-q0)
    return tuple(1.0 / (1.0 + math.exp(-(logit + offset))) for offset in LOGIT_OFFSETS)


def solve_marginal_lambda(exposures: Iterable[float], target: float) -> float:
    values = np.asarray(tuple(exposures), dtype=np.float64)
    if values.size == 0 or np.any(values <= 0.0) or np.any(values > EXPOSURE_MAX):
        raise ValueError("lambda solving requires legal F0 exposures in (0,32]")
    if not 0.0 < target < 1.0:
        raise ValueError("target must be strictly between zero and one")

    def marginal(rate: float) -> float:
        return float(np.mean(-np.expm1(-np.float64(rate) * values), dtype=np.float64))

    low, high = 0.0, 1.0
    while marginal(high) < target:
        high *= 2.0
        if not math.isfinite(high):
            raise ArithmeticError("failed to bracket marginal lambda")
    for _ in range(100):
        midpoint = (low + high) / 2.0
        if marginal(midpoint) < target:
            low = midpoint
        else:
            high = midpoint
    return (low + high) / 2.0


@dataclass(frozen=True)
class FixedPolicy:
    policy_id: str
    family: str
    grid_index: tuple[int, ...]
    p_low: float | None = None
    p_high: float | None = None
    probability: float | None = None
    rate: float | None = None
    force_keep: bool = False

    @property
    def separation(self) -> float:
        if self.p_low is None or self.p_high is None:
            return 0.0
        return float(self.p_high - self.p_low)

    def event_probabilities(self, exposure: np.ndarray) -> np.ndarray:
        values = np.asarray(exposure, dtype=np.float64)
        if np.any(values < 0.0) or np.any(values > EXPOSURE_MAX):
            raise ValueError("policy received exposure outside [0,32]")
        if self.force_keep:
            return np.zeros_like(values)
        if self.family == "stratified":
            assert self.p_low is not None and self.p_high is not None
            result = np.where(values < EXPOSURE_SPLIT, self.p_low, self.p_high)
        elif self.family in ("global_p", "shell"):
            assert self.probability is not None
            result = np.full_like(values, self.probability)
        elif self.family == "global_lambda":
            assert self.rate is not None
            result = -np.expm1(-np.float64(self.rate) * values)
        else:
            raise ValueError(f"unknown fixed-policy family: {self.family}")
        return np.where(values > 0.0, result, 0.0).astype(np.float64, copy=False)

    def policy(self, features: np.ndarray, exposure: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        del features
        probabilities = self.event_probabilities(exposure)
        safe = np.clip(probabilities, np.finfo(np.float64).tiny, 1.0 - np.finfo(np.float64).eps)
        logits = np.log(safe) - np.log1p(-safe)
        values = np.asarray(exposure, dtype=np.float64)
        rates = np.zeros_like(values)
        np.divide(-np.log1p(-safe), values, out=rates, where=values > 0.0)
        return logits.astype(np.float64), rates.astype(np.float64), probabilities

    def value(self, features: np.ndarray) -> float:
        del features
        return 0.0

    def joint_log_probability(
        self, features: np.ndarray, exposure: np.ndarray,
        actions: np.ndarray, policy_mask: np.ndarray,
    ) -> float:
        del features
        probabilities = self.event_probabilities(exposure)
        total = 0.0
        for probability, action, enabled in zip(probabilities, actions, policy_mask, strict=True):
            if not enabled:
                continue
            if int(action) == 0:
                total += math.log1p(-float(probability))
            else:
                total += math.log(float(probability)) + math.log(0.5)
        return total


def discovery_grid(exposures: Sequence[float]) -> tuple[float, tuple[float, ...], tuple[FixedPolicy, ...]]:
    q0 = q_from_exposures(exposures)
    grid = shifted_probability_grid(q0)
    policies: list[FixedPolicy] = []
    for low_index, p_low in enumerate(grid):
        for high_index, p_high in enumerate(grid):
            policies.append(FixedPolicy(
                policy_id=f"STRATIFIED-{low_index}-{high_index}", family="stratified",
                grid_index=(low_index, high_index), p_low=p_low, p_high=p_high,
            ))
    policies.extend(FixedPolicy(
        policy_id=f"GLOBAL-P-{index}", family="global_p", grid_index=(index,), probability=value,
    ) for index, value in enumerate(grid))
    policies.extend(FixedPolicy(
        policy_id=f"GLOBAL-LAMBDA-{index}", family="global_lambda", grid_index=(index,),
        rate=solve_marginal_lambda(exposures, value),
    ) for index, value in enumerate(grid))
    return q0, grid, tuple(policies)


KEEP_POLICY = FixedPolicy("KEEP", "keep", (), force_keep=True)


def matched_shell(candidate: FixedPolicy, low_weight: float, high_weight: float) -> FixedPolicy:
    if candidate.family != "stratified" or candidate.p_low is None or candidate.p_high is None:
        raise ValueError("matched shell requires a stratified candidate")
    if min(low_weight, high_weight) < 0.0 or not math.isclose(low_weight + high_weight, 1.0, abs_tol=1e-12):
        raise ValueError("shell weights must be nonnegative and sum to one")
    probability = low_weight * candidate.p_low + high_weight * candidate.p_high
    return FixedPolicy("MATCHED-SHELL", "shell", (), probability=float(probability))


def select_best(
    policies: Sequence[FixedPolicy], root_metrics: Mapping[str, Mapping[int, Mapping[str, float]]],
    roots: Sequence[int],
) -> FixedPolicy:
    if not policies or not roots:
        raise ValueError("selection requires policies and roots")

    def key(policy: FixedPolicy) -> tuple[float, float, float, tuple[int, ...]]:
        rows = [root_metrics[policy.policy_id][int(root)] for root in roots]
        mean_return = float(np.mean([float(row["direct_return"]) for row in rows], dtype=np.float64))
        activity = float(np.mean([float(row["activity"]) for row in rows], dtype=np.float64))
        return -mean_return, activity, policy.separation, policy.grid_index

    return min(policies, key=key)
