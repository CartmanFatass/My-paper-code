"""Causal online learners for the B05 unknown joint-law comparison.

This module deliberately has no environment truth interface.  Its learners consume
only public keys, pre-outcome law estimates, and observations produced by collection.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np


SAFE = 0
COOPERATIVE = 1
PRIOR_MEAN = 0.5
OUTCOMES = 4
VERSIONS = 2

FAMILIES = ("response_all", "fingerprint_full", "fingerprint_recent")
REPRESENTATIONS = ("response", "law", "cell", "hybrid")


def _number_id(value: float) -> str:
    return format(float(value), ".12g")


@dataclass(frozen=True)
class Spec:
    """One declared decision setting from the finite B05 development bank."""

    family: str
    representation: str
    prior_strength: float
    recent_window: int | None = None

    def __post_init__(self) -> None:
        if self.family not in FAMILIES:
            raise ValueError(f"family must be one of {FAMILIES}")
        if not np.isfinite(self.prior_strength) or self.prior_strength <= 0.0:
            raise ValueError("prior_strength must be finite and positive")
        if self.family == "response_all":
            if self.representation != "response" or self.recent_window is not None:
                raise ValueError("response_all requires response and no recent window")
        elif self.family == "fingerprint_full":
            if self.representation not in ("law", "cell", "hybrid"):
                raise ValueError("fingerprint_full requires law, cell, or hybrid")
            if self.recent_window is not None:
                raise ValueError("fingerprint_full has no recent window")
        else:
            if self.representation not in ("law", "cell", "hybrid"):
                raise ValueError("fingerprint_recent requires law, cell, or hybrid")
            if self.recent_window is None or self.recent_window <= 0:
                raise ValueError("fingerprint_recent requires a positive recent window")

    @property
    def id(self) -> str:
        parts = [self.family, self.representation, f"prior{_number_id(self.prior_strength)}"]
        if self.recent_window is not None:
            parts.append(f"window{self.recent_window}")
        return "__".join(parts)


def development_specs() -> list[Spec]:
    """Return the prospectively fixed 20-setting bank in stable order."""
    specs = [Spec("response_all", "response", prior) for prior in (2.0, 16.0)]
    specs.extend(
        Spec("fingerprint_full", representation, prior)
        for representation in ("law", "cell", "hybrid")
        for prior in (2.0, 16.0)
    )
    specs.extend(
        Spec("fingerprint_recent", representation, prior, window)
        for representation in ("law", "cell", "hybrid")
        for prior in (2.0, 16.0)
        for window in (64, 256)
    )
    return specs


class SharedLawLearner:
    """Action-conditional Dirichlet tables for public (version, context) keys."""

    def __init__(self, contexts: int):
        if contexts <= 0:
            raise ValueError("contexts must be positive")
        self.contexts = int(contexts)
        self.counts = np.zeros((VERSIONS, self.contexts, OUTCOMES), dtype=np.int64)
        self.prior_centers = np.full((VERSIONS, OUTCOMES), 0.25, dtype=np.float64)
        self.version_started = np.array([True, False], dtype=np.bool_)
        self.updates = 0

    def _check_key(self, version: int, context: int) -> None:
        if version not in (0, 1) or not 0 <= context < self.contexts:
            raise ValueError("invalid public key")

    def predict(self, *, version: int, context: int) -> np.ndarray:
        self._check_key(version, context)
        if not self.version_started[version]:
            raise RuntimeError("public version must be activated before prediction")
        counts = self.counts[version, context]
        # Every table has total mass two around its version's frozen prior center.
        return (counts + 2.0 * self.prior_centers[version]) / (counts.sum() + 2.0)

    def activate_version(self, version: int) -> np.ndarray:
        """Freeze a new version's center from earlier-version posterior tables."""
        if version != 1:
            raise ValueError("B05 only activates version one after version zero")
        if self.version_started[version]:
            raise RuntimeError("version one was already activated")
        previous = np.stack(
            [self.predict(version=0, context=context) for context in range(self.contexts)]
        )
        self.prior_centers[version] = previous.mean(axis=0)
        self.version_started[version] = True
        return self.prior_centers[version].copy()

    def prior_center(self, version: int) -> np.ndarray:
        if version not in (0, 1) or not self.version_started[version]:
            raise RuntimeError("public version has no active prior center")
        return self.prior_centers[version].copy()

    def count(self, *, version: int, context: int) -> int:
        self._check_key(version, context)
        return int(self.counts[version, context].sum())

    def observe(
        self, *, action: int, version: int, context: int, outcome: int
    ) -> bool:
        """Update only for a cooperative observation; return whether it updated."""
        self._check_key(version, context)
        if action == SAFE:
            return False
        if action != COOPERATIVE or not 0 <= outcome < OUTCOMES:
            raise ValueError("invalid collected action or outcome")
        self.counts[version, context, outcome] += 1
        self.updates += 1
        return True

    def estimate_vector(self) -> np.ndarray:
        estimates = np.empty_like(self.counts, dtype=np.float64)
        for version in range(VERSIONS):
            for context in range(self.contexts):
                counts = self.counts[version, context]
                estimates[version, context] = (
                    counts + 2.0 * self.prior_centers[version]
                ) / (counts.sum() + 2.0)
        return estimates.reshape(-1)

    def export_state(self) -> dict[str, np.ndarray]:
        return {
            "counts": self.counts.copy(),
            "estimated_law": self.estimate_vector().reshape(
                VERSIONS, self.contexts, OUTCOMES
            ),
            "posterior_updates": np.array([self.updates], dtype=np.int64),
            "prior_centers": self.prior_centers.copy(),
            "version_started": self.version_started.copy(),
        }


@dataclass
class _Record:
    macro_index: int
    reward: float
    feature: np.ndarray
    version: int
    context: int


class DecisionLearner:
    """One B05 decision fit with a common competent SAFE estimator."""

    def __init__(self, spec: Spec, contexts: int):
        if contexts <= 0:
            raise ValueError("contexts must be positive")
        self.spec = spec
        self.contexts = int(contexts)
        self.safe_count = 0
        self.safe_reward_sum = 0.0
        self.cooperative_updates = 0
        self.safe_updates = 0
        self.solve_calls = 0
        self.expiration_recomputations = 0
        self.window: deque[_Record] = deque()

        self.response_counts = np.zeros(OUTCOMES, dtype=np.int64)
        self.response_reward_sums = np.zeros(OUTCOMES, dtype=np.float64)
        self.cell_counts = np.zeros((VERSIONS, self.contexts), dtype=np.int64)
        self.cell_reward_sums = np.zeros((VERSIONS, self.contexts), dtype=np.float64)

        self.dimension = 0
        self.prior_coefficients = np.empty(0, dtype=np.float64)
        self.xtx = np.empty((0, 0), dtype=np.float64)
        self.xty = np.empty(0, dtype=np.float64)
        self.coefficients = np.empty(0, dtype=np.float64)
        if self.spec.representation in ("law", "hybrid"):
            self.dimension = OUTCOMES + (
                VERSIONS * self.contexts
                if self.spec.representation == "hybrid"
                else 0
            )
            self.prior_coefficients = np.zeros(self.dimension, dtype=np.float64)
            self.prior_coefficients[:OUTCOMES] = PRIOR_MEAN
            self.xtx = np.zeros((self.dimension, self.dimension), dtype=np.float64)
            self.xty = np.zeros(self.dimension, dtype=np.float64)
            self.coefficients = self.prior_coefficients.copy()

    def _safe_mean(self) -> float:
        # SAFE is fixed to total Beta mass two in every setting.
        return (self.safe_reward_sum + 1.0) / (self.safe_count + 2.0)

    def response_means(self) -> np.ndarray:
        if self.spec.family != "response_all":
            raise ValueError("conditional response means exist only for response_all")
        strength = self.spec.prior_strength
        return (
            self.response_reward_sums + strength * PRIOR_MEAN
        ) / (self.response_counts + strength)

    def _cell_mean(self, *, version: int, context: int) -> float:
        strength = self.spec.prior_strength
        return float(
            (self.cell_reward_sums[version, context] + strength * PRIOR_MEAN)
            / (self.cell_counts[version, context] + strength)
        )

    def _feature(
        self, *, version: int, context: int, estimated_law: np.ndarray
    ) -> np.ndarray:
        law = np.asarray(estimated_law, dtype=np.float64)
        if law.shape != (OUTCOMES,):
            raise ValueError("estimated_law must have shape (4,)")
        if self.spec.representation == "law":
            return law.copy()
        if self.spec.representation != "hybrid":
            raise ValueError("features exist only for regression representations")
        feature = np.zeros(self.dimension, dtype=np.float64)
        feature[:OUTCOMES] = law
        feature[OUTCOMES + version * self.contexts + context] = 1.0
        return feature

    def _solve(self, *, expiration: bool) -> None:
        precision = self.spec.prior_strength
        matrix = self.xtx + precision * np.eye(self.dimension, dtype=np.float64)
        rhs = self.xty + precision * self.prior_coefficients
        self.coefficients = np.linalg.solve(matrix, rhs)
        self.solve_calls += 1
        if expiration:
            self.expiration_recomputations += 1

    def expire_before(self, macro_index: int) -> int:
        """Expire cooperative records older than t-window before prediction at t."""
        if self.spec.family != "fingerprint_recent":
            return 0
        threshold = int(macro_index) - int(self.spec.recent_window)
        removed = 0
        while self.window and self.window[0].macro_index < threshold:
            record = self.window.popleft()
            removed += 1
            if self.spec.representation == "cell":
                self.cell_counts[record.version, record.context] -= 1
                self.cell_reward_sums[record.version, record.context] -= record.reward
            else:
                self.xtx -= np.outer(record.feature, record.feature)
                self.xty -= record.feature * record.reward
        if removed and self.spec.representation in ("law", "hybrid"):
            self._solve(expiration=True)
        return removed

    def predict(
        self, *, version: int, context: int, estimated_law: np.ndarray
    ) -> np.ndarray:
        if version not in (0, 1) or not 0 <= context < self.contexts:
            raise ValueError("invalid public key")
        if self.spec.family == "response_all":
            cooperative = float(np.asarray(estimated_law) @ self.response_means())
        elif self.spec.representation == "cell":
            cooperative = self._cell_mean(version=version, context=context)
        else:
            feature = self._feature(
                version=version, context=context, estimated_law=estimated_law
            )
            cooperative = float(feature @ self.coefficients)
        return np.array([self._safe_mean(), cooperative], dtype=np.float64)

    def observe(
        self,
        *,
        macro_index: int,
        action: int,
        version: int,
        context: int,
        estimated_law: np.ndarray,
        outcome: int,
        reward: int,
    ) -> None:
        if action not in (SAFE, COOPERATIVE) or reward not in (0, 1):
            raise ValueError("invalid collected action or reward")
        if action == SAFE:
            self.safe_count += 1
            self.safe_reward_sum += reward
            self.safe_updates += 1
            return
        if not 0 <= outcome < OUTCOMES:
            raise ValueError("invalid cooperative outcome")
        self.cooperative_updates += 1
        if self.spec.family == "response_all":
            self.response_counts[outcome] += 1
            self.response_reward_sums[outcome] += reward
            return
        if self.spec.representation == "cell":
            self.cell_counts[version, context] += 1
            self.cell_reward_sums[version, context] += reward
            feature = np.empty(0, dtype=np.float64)
        else:
            # The causal pre-outcome law feature is copied permanently into the record.
            feature = self._feature(
                version=version, context=context, estimated_law=estimated_law
            )
            self.xtx += np.outer(feature, feature)
            self.xty += feature * reward
            self._solve(expiration=False)
        if self.spec.family == "fingerprint_recent":
            self.window.append(
                _Record(
                    macro_index=int(macro_index),
                    reward=float(reward),
                    feature=feature.copy(),
                    version=int(version),
                    context=int(context),
                )
            )

    def estimate_vector(self) -> np.ndarray:
        safe = np.array([self._safe_mean()], dtype=np.float64)
        if self.spec.family == "response_all":
            cooperative = self.response_means()
        elif self.spec.representation == "cell":
            strength = self.spec.prior_strength
            cooperative = (
                self.cell_reward_sums + strength * PRIOR_MEAN
            ) / (self.cell_counts + strength)
            cooperative = cooperative.reshape(-1)
        else:
            cooperative = self.coefficients
        return np.concatenate((safe, cooperative))

    def export_state(self) -> dict[str, np.ndarray]:
        cooperative_posterior_updates = (
            self.cooperative_updates
            if self.spec.family == "response_all" or self.spec.representation == "cell"
            else 0
        )
        regression_statistic_updates = (
            self.cooperative_updates
            if self.spec.representation in ("law", "hybrid")
            else 0
        )
        state = {
            "estimate": self.estimate_vector(),
            "safe_count": np.array([self.safe_count], dtype=np.int64),
            "safe_reward_sum": np.array([self.safe_reward_sum], dtype=np.float64),
            "safe_posterior_updates": np.array([self.safe_updates], dtype=np.int64),
            "cooperative_observations": np.array(
                [self.cooperative_updates], dtype=np.int64
            ),
            "cooperative_posterior_updates": np.array(
                [cooperative_posterior_updates], dtype=np.int64
            ),
            "regression_statistic_updates": np.array(
                [regression_statistic_updates], dtype=np.int64
            ),
            "regression_solves": np.array([self.solve_calls], dtype=np.int64),
            "expiration_recomputations": np.array(
                [self.expiration_recomputations], dtype=np.int64
            ),
            "response_counts": self.response_counts.copy(),
            "response_reward_sums": self.response_reward_sums.copy(),
            "cell_counts": self.cell_counts.copy(),
            "cell_reward_sums": self.cell_reward_sums.copy(),
            "coefficients": self.coefficients.copy(),
            "xtx": self.xtx.copy(),
            "xty": self.xty.copy(),
            "window_macro_index": np.array(
                [record.macro_index for record in self.window], dtype=np.int64
            ),
            "window_reward": np.array(
                [record.reward for record in self.window], dtype=np.float64
            ),
            "window_version": np.array(
                [record.version for record in self.window], dtype=np.int8
            ),
            "window_context": np.array(
                [record.context for record in self.window], dtype=np.int16
            ),
        }
        if self.dimension:
            state["window_features"] = np.array(
                [record.feature for record in self.window], dtype=np.float64
            ).reshape(len(self.window), self.dimension)
        else:
            state["window_features"] = np.empty((len(self.window), 0), dtype=np.float64)
        return state
