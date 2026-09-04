"""Frozen CRTO-B1 mechanism controls and finite-horizon audit helpers.

This module is intentionally independent of the simulator.  The launcher supplies
development rows, audit-boundary records, and branch rewards; these functions bind
the exact frozen statistical/control laws without gaining access to actor inputs or
postdecision quantities.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Hashable, Mapping, Sequence

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import minimize
from scipy.special import expit

from .config import ALGORITHM_SEEDS, COST_REGIMES, EVENT_CLASSES, REGIMES


FloatArray = NDArray[np.float64]

REGISTERED_SEEDS = ALGORITHM_SEEDS
REGIME_ORDER = {regime: index for index, regime in enumerate(REGIMES)}
TARGET_REGIMES = REGIMES[1:]
PANEL_ORDER = {"scored": 0, "donor": 1}
EVENT_ORDER = EVENT_CLASSES
COSTS = COST_REGIMES


def _as_finite_matrix(values: ArrayLike, *, name: str) -> FloatArray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 2 or array.shape[0] == 0 or array.shape[1] == 0:
        raise ValueError(f"{name} must be a nonempty two-dimensional array")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must contain only finite values")
    return array


def _as_binary_vector(values: ArrayLike, *, count: int, name: str) -> FloatArray:
    array = np.asarray(values, dtype=np.float64)
    if array.shape != (count,) or not np.isfinite(array).all():
        raise ValueError(f"{name} must be a finite vector of length {count}")
    if not np.isin(array, (0.0, 1.0)).all():
        raise ValueError(f"{name} must contain only zero and one")
    return array


def logistic_objective_and_gradient(
    coefficients: ArrayLike,
    features: ArrayLike,
    labels: ArrayLike,
    *,
    penalty: float = 1e-3,
) -> tuple[float, FloatArray]:
    """Mean BCE plus the frozen non-intercept L2 penalty and its gradient.

    Column zero is the literal intercept and must be all ones.  This shared
    implementation is used by the hazard and donor-balance fits.
    """

    x = _as_finite_matrix(features, name="features")
    y = _as_binary_vector(labels, count=x.shape[0], name="labels")
    beta = np.asarray(coefficients, dtype=np.float64)
    if beta.shape != (x.shape[1],) or not np.isfinite(beta).all():
        raise ValueError("coefficient shape/finiteness mismatch")
    if not np.array_equal(x[:, 0], np.ones(x.shape[0], dtype=np.float64)):
        raise ValueError("feature column zero must be the exact intercept")
    if penalty < 0.0 or not math.isfinite(penalty):
        raise ValueError("penalty must be finite and nonnegative")

    logits = x @ beta
    objective = float(np.mean(np.logaddexp(0.0, logits) - y * logits))
    objective += 0.5 * penalty * float(beta[1:] @ beta[1:])
    gradient = (x.T @ (expit(logits) - y)) / x.shape[0]
    gradient[1:] += penalty * beta[1:]
    return objective, np.asarray(gradient, dtype=np.float64)


@dataclass(frozen=True)
class LogisticFit:
    coefficients: FloatArray
    converged: bool
    iterations: int
    objective: float
    gradient_inf_norm: float
    message: str


@dataclass(frozen=True)
class FeatureStandardizer:
    """Development-only centering/scaling frozen for scored hazard use."""

    columns: tuple[int, ...]
    means: FloatArray
    scales: FloatArray
    development_rows: int

    def transform(self, features: ArrayLike) -> FloatArray:
        x = _as_finite_matrix(features, name="features").copy()
        if self.means.shape != (len(self.columns),) or self.scales.shape != (len(self.columns),):
            raise RuntimeError("malformed frozen feature standardizer")
        if self.columns and max(self.columns) >= x.shape[1]:
            raise ValueError("feature matrix has fewer columns than the frozen standardizer")
        x[:, self.columns] = (x[:, self.columns] - self.means) / self.scales
        return x


def fit_feature_standardizer(
    features: ArrayLike, continuous_columns: Sequence[int],
) -> FeatureStandardizer:
    x = _as_finite_matrix(features, name="features")
    columns = tuple(int(column) for column in continuous_columns)
    if len(set(columns)) != len(columns) or any(column <= 0 or column >= x.shape[1] for column in columns):
        raise ValueError("continuous columns must be unique, in range, and exclude intercept column zero")
    means = x[:, columns].mean(axis=0) if columns else np.empty(0, dtype=np.float64)
    scales = x[:, columns].std(axis=0, ddof=0) if columns else np.empty(0, dtype=np.float64)
    scales[scales == 0.0] = 1.0
    return FeatureStandardizer(columns, np.asarray(means), np.asarray(scales), x.shape[0])


def fit_logistic_lbfgs(
    features: ArrayLike,
    labels: ArrayLike,
    *,
    penalty: float = 1e-3,
    max_iterations: int = 500,
    memory: int = 20,
    gradient_tolerance: float = 1e-8,
) -> LogisticFit:
    """Run the registered deterministic zero-start L-BFGS fit.

    ``converged`` is based only on the terminal penalized-gradient infinity norm.
    A library success code based on objective reduction cannot make the control
    available.
    """

    x = _as_finite_matrix(features, name="features")
    y = _as_binary_vector(labels, count=x.shape[0], name="labels")
    if not np.array_equal(x[:, 0], np.ones(x.shape[0], dtype=np.float64)):
        raise ValueError("feature column zero must be the exact intercept")
    if (max_iterations, memory, gradient_tolerance) != (500, 20, 1e-8):
        raise ValueError("CRTO-B1 fixes L-BFGS at 500 iterations, memory 20, tolerance 1e-8")

    def objective(beta: FloatArray) -> tuple[float, FloatArray]:
        return logistic_objective_and_gradient(beta, x, y, penalty=penalty)

    result = minimize(
        objective,
        np.zeros(x.shape[1], dtype=np.float64),
        method="L-BFGS-B",
        jac=True,
        options={
            "maxiter": max_iterations,
            "maxcor": memory,
            "gtol": gradient_tolerance,
            # Disable the relative-objective stopping route.  Terminal
            # availability is independently guarded by the exact gradient test.
            "ftol": 0.0,
            "maxls": 20,
        },
    )
    terminal_objective, terminal_gradient = objective(np.asarray(result.x, dtype=np.float64))
    gradient_inf = float(np.max(np.abs(terminal_gradient)))
    finite = bool(
        np.isfinite(result.x).all()
        and math.isfinite(terminal_objective)
        and math.isfinite(gradient_inf)
    )
    converged = finite and gradient_inf <= gradient_tolerance and int(result.nit) <= max_iterations
    return LogisticFit(
        coefficients=np.asarray(result.x, dtype=np.float64).copy(),
        converged=converged,
        iterations=int(result.nit),
        objective=float(terminal_objective),
        gradient_inf_norm=gradient_inf,
        message=str(result.message),
    )


@dataclass(frozen=True, order=True)
class HazardCellKey:
    regime: str
    current_k: int
    age: int
    cost: float

    def __post_init__(self) -> None:
        if self.regime not in REGIME_ORDER:
            raise ValueError(f"unknown regime {self.regime!r}")
        if self.current_k not in (4, 8, 16):
            raise ValueError("current_k must be 4, 8, or 16")
        if self.age <= 0 or self.age % 4:
            raise ValueError("hazard age must be a positive multiple of four")
        if self.cost not in COSTS:
            raise ValueError("cost must be one of the two frozen regimes")


@dataclass(frozen=True)
class HazardCellFit:
    key: HazardCellKey
    review_count: int
    empirical_rate: float
    supported: bool
    intercept_offset: float | None
    constant_probability: float | None
    matched_probability: float | None
    converged: bool
    reason: str | None


@dataclass(frozen=True)
class HazardPreprocessingAudit:
    """Literal v4 hazard design-matrix preservation witness.

    The evaluation owner defines column meaning and passes the four continuous
    column indices.  Controls neither create features nor infer/drop one-hot
    references; they verify that every remaining slope column is literal binary
    and that the optimizer penalizes every slope while exempting only column 0.
    """

    development_rows: int
    raw_columns: int
    continuous_columns: tuple[int, ...]
    indicator_columns: tuple[int, ...]
    standardized_columns: tuple[int, ...]
    literal_unscaled_columns: tuple[int, ...]
    penalized_slope_columns: tuple[int, ...]
    unpenalized_columns: tuple[int, ...]
    l2_penalty: float
    columns_retained: bool
    reference_columns_dropped: bool
    indicator_values_literal_binary: bool


@dataclass(frozen=True)
class HazardControlFit:
    base: LogisticFit
    standardizer: FeatureStandardizer
    preprocessing: HazardPreprocessingAudit
    cells: Mapping[HazardCellKey, HazardCellFit]
    available: bool
    failure_reasons: tuple[str, ...]

    def probabilities(
        self,
        features: ArrayLike,
        cells: Sequence[HazardCellKey],
    ) -> FloatArray:
        """Return frozen probabilities; unsupported/unseen cells use base logits."""

        x = self.standardizer.transform(features)
        if x.shape[1] != self.base.coefficients.size or len(cells) != x.shape[0]:
            raise ValueError("hazard prediction shape mismatch")
        if not np.array_equal(x[:, 0], np.ones(x.shape[0], dtype=np.float64)):
            raise ValueError("hazard feature column zero must be the exact intercept")
        logits = x @ self.base.coefficients
        probabilities = np.asarray(expit(logits), dtype=np.float64)
        for index, key in enumerate(cells):
            fitted = self.cells.get(key)
            if fitted is None or not fitted.supported:
                continue
            if fitted.constant_probability is not None:
                probabilities[index] = fitted.constant_probability
            elif fitted.intercept_offset is not None:
                probabilities[index] = float(expit(logits[index] + fitted.intercept_offset))
            else:  # A supported cell must have one of the two registered solutions.
                raise RuntimeError(f"malformed supported hazard cell: {key}")
        return probabilities

    def sampled_terminations(
        self,
        features: ArrayLike,
        cells: Sequence[HazardCellKey],
        preassigned_uniforms: ArrayLike,
    ) -> NDArray[np.bool_]:
        probabilities = self.probabilities(features, cells)
        uniforms = np.asarray(preassigned_uniforms, dtype=np.float64)
        if uniforms.shape != probabilities.shape or not np.isfinite(uniforms).all():
            raise ValueError("one finite preassigned uniform is required per legal review")
        if np.any((uniforms < 0.0) | (uniforms >= 1.0)):
            raise ValueError("preassigned uniforms must lie in [0,1)")
        return uniforms < probabilities


def _bisect_intercept_offset(
    base_logits: FloatArray,
    target_rate: float,
) -> tuple[float | None, float | None, bool, str | None]:
    if target_rate == 0.0 or target_rate == 1.0:
        return None, target_rate, True, None
    if not 0.0 < target_rate < 1.0:
        return None, None, False, "empirical rate outside [0,1]"

    lower, upper = -40.0, 40.0

    def residual(offset: float) -> float:
        return float(np.mean(expit(base_logits + offset)) - target_rate)

    f_lower, f_upper = residual(lower), residual(upper)
    if f_lower > 0.0 or f_upper < 0.0:
        return None, None, False, "bisection bracket [-40,40] does not contain the root"
    for _ in range(200):
        midpoint = 0.5 * (lower + upper)
        f_midpoint = residual(midpoint)
        if abs(f_midpoint) <= 1e-10:
            return midpoint, None, True, None
        if f_midpoint < 0.0:
            lower = midpoint
        else:
            upper = midpoint
    midpoint = 0.5 * (lower + upper)
    if abs(residual(midpoint)) <= 1e-10:
        return midpoint, None, True, None
    return None, None, False, "bisection did not attain absolute rate tolerance 1e-10"


def fit_rate_matched_hazard(
    features: ArrayLike,
    labels: ArrayLike,
    cell_keys: Sequence[HazardCellKey],
    *,
    continuous_columns: Sequence[int],
) -> HazardControlFit:
    """Fit v4 base hazard slopes and exact supported-cell intercept offsets.

    ``features`` is the complete four-regime development panel constructed by
    the evaluation owner.  This routine does not invent, collapse, interact, or
    reference-drop columns.  Exactly four caller-identified continuous columns
    are standardized from that complete panel; every other non-intercept column
    must remain a literal 0/1 indicator.
    """

    raw_x = _as_finite_matrix(features, name="features")
    y = _as_binary_vector(labels, count=raw_x.shape[0], name="labels")
    if len(cell_keys) != raw_x.shape[0]:
        raise ValueError("one hazard cell key is required for every development review")
    continuous = tuple(int(column) for column in continuous_columns)
    if len(continuous) != 4 or len(set(continuous)) != 4:
        raise ValueError(
            "CRTO-B1 v4 requires exactly four distinct continuous columns: "
            "K/16, age/16, age/K, and cost/4 as identified by evaluation"
        )
    if any(column <= 0 or column >= raw_x.shape[1] for column in continuous):
        raise ValueError("v4 continuous columns must be in range and exclude intercept column zero")
    if not np.array_equal(raw_x[:, 0], np.ones(raw_x.shape[0], dtype=np.float64)):
        raise ValueError("hazard feature column zero must be the exact unpenalized intercept")
    indicator_columns = tuple(
        column for column in range(1, raw_x.shape[1]) if column not in continuous
    )
    indicators_literal = bool(np.isin(raw_x[:, indicator_columns], (0.0, 1.0)).all())
    if not indicators_literal:
        raise ValueError(
            "every non-continuous v4 hazard slope must be a literal unscaled 0/1 indicator"
        )
    standardizer = fit_feature_standardizer(raw_x, continuous)
    x = standardizer.transform(raw_x)
    columns_retained = x.shape == raw_x.shape
    indicators_unchanged = bool(np.array_equal(x[:, indicator_columns], raw_x[:, indicator_columns]))
    if not columns_retained or not indicators_unchanged:
        raise RuntimeError("v4 hazard preprocessing changed or dropped an indicator column")
    preprocessing = HazardPreprocessingAudit(
        development_rows=raw_x.shape[0], raw_columns=raw_x.shape[1],
        continuous_columns=continuous, indicator_columns=indicator_columns,
        standardized_columns=continuous, literal_unscaled_columns=indicator_columns,
        penalized_slope_columns=tuple(range(1, raw_x.shape[1])),
        unpenalized_columns=(0,), l2_penalty=1e-3,
        columns_retained=columns_retained, reference_columns_dropped=False,
        indicator_values_literal_binary=indicators_literal and indicators_unchanged,
    )
    base = fit_logistic_lbfgs(x, y)
    grouped: dict[HazardCellKey, list[int]] = {}
    for index, key in enumerate(cell_keys):
        grouped.setdefault(key, []).append(index)

    cells: dict[HazardCellKey, HazardCellFit] = {}
    failures: list[str] = []
    base_logits = x @ base.coefficients
    if not base.converged:
        failures.append(
            f"base L-BFGS terminal gradient {base.gradient_inf_norm:.17g} exceeds 1e-8"
        )
    for key in sorted(grouped):
        indices = np.asarray(grouped[key], dtype=np.int64)
        count = int(indices.size)
        rate = float(np.mean(y[indices]))
        if count < 32:
            cells[key] = HazardCellFit(
                key, count, rate, False, None, None, None, True,
                "fewer than 32 development reviews",
            )
            continue
        offset, constant, converged, reason = _bisect_intercept_offset(base_logits[indices], rate)
        matched = (
            constant
            if constant is not None
            else float(np.mean(expit(base_logits[indices] + float(offset))))
            if offset is not None
            else None
        )
        cells[key] = HazardCellFit(
            key, count, rate, True, offset, constant, matched, converged, reason,
        )
        if not converged:
            failures.append(f"{key}: {reason}")
    return HazardControlFit(
        base, standardizer, preprocessing, cells,
        base.converged and not failures, tuple(failures),
    )


def hazard_target_support(
    fit: HazardControlFit,
    encountered_cells: Sequence[HazardCellKey],
) -> dict[str, object]:
    """Check the mechanism-support law over encountered target-regime cells."""

    target = sorted({key for key in encountered_cells if key.regime in TARGET_REGIMES})
    unsupported = [
        key for key in target
        if key not in fit.cells or not fit.cells[key].supported or not fit.cells[key].converged
    ]
    return {
        "available": fit.base.converged and not unsupported,
        "encountered_target_cells": len(target),
        "unsupported": [
            {"regime": key.regime, "K": key.current_k, "age": key.age, "cost": key.cost}
            for key in unsupported
        ],
    }


@dataclass(frozen=True)
class RateCount:
    method: str
    seed: int
    regime: str
    event: str
    cost: float
    episodes: int
    legal_discretionary_reviews: int
    changed_option_terminations: int

    def __post_init__(self) -> None:
        if self.method not in ("CRTO", "RATE-MATCHED-HAZARD-CRTO"):
            raise ValueError("rate rows must be CRTO or RATE-MATCHED-HAZARD-CRTO")
        if self.seed not in REGISTERED_SEEDS or self.regime not in REGIME_ORDER:
            raise ValueError("unregistered seed or regime")
        if self.event not in EVENT_ORDER or self.cost not in COSTS:
            raise ValueError("unregistered event or cost")
        if min(self.episodes, self.legal_discretionary_reviews, self.changed_option_terminations) < 0:
            raise ValueError("rate counts cannot be negative")
        if self.changed_option_terminations > self.legal_discretionary_reviews:
            raise ValueError("changed terminations cannot exceed legal reviews")


def evaluation_rate_balance(rows: Sequence[RateCount]) -> dict[str, object]:
    """Compute exact own-trajectory rate balance overall and by event/cost."""

    aggregated: dict[tuple[str, int, str, str, float], list[int]] = {}
    for row in rows:
        key = (row.method, row.seed, row.regime, row.event, row.cost)
        counts = aggregated.setdefault(key, [0, 0, 0])
        counts[0] += row.episodes
        counts[1] += row.legal_discretionary_reviews
        counts[2] += row.changed_option_terminations

    output: dict[str, object] = {}
    failures: list[str] = []
    methods = ("CRTO", "RATE-MATCHED-HAZARD-CRTO")
    for regime in TARGET_REGIMES:
        cell_output: dict[str, object] = {}
        overall_by_method: dict[tuple[str, int], list[int]] = {
            (method, seed): [0, 0, 0] for method in methods for seed in REGISTERED_SEEDS
        }
        for event in EVENT_ORDER:
            for cost in COSTS:
                label = f"{event}|{cost:g}"
                signed_rho: list[float] = []
                signed_lambda: list[float] = []
                seed_rows: dict[str, object] = {}
                for seed in REGISTERED_SEEDS:
                    rates: dict[str, tuple[float, float]] = {}
                    for method in methods:
                        key = (method, seed, regime, event, cost)
                        if key not in aggregated:
                            failures.append(f"missing scored rate cell {key}")
                            continue
                        episodes, reviews, terms = aggregated[key]
                        combined = overall_by_method[(method, seed)]
                        combined[0] += episodes
                        combined[1] += reviews
                        combined[2] += terms
                        if reviews == 0 or episodes == 0:
                            failures.append(f"zero denominator in scored rate cell {key}")
                            continue
                        rates[method] = (terms / reviews, terms / (256.0 * episodes))
                    if len(rates) == 2:
                        rho_diff = rates["CRTO"][0] - rates["RATE-MATCHED-HAZARD-CRTO"][0]
                        lambda_diff = rates["CRTO"][1] - rates["RATE-MATCHED-HAZARD-CRTO"][1]
                        signed_rho.append(rho_diff)
                        signed_lambda.append(lambda_diff)
                        seed_rows[str(seed)] = {
                            "rho_CRTO_minus_hazard": rho_diff,
                            "lambda_CRTO_minus_hazard": lambda_diff,
                            "CRTO": {"rho": rates["CRTO"][0], "lambda": rates["CRTO"][1]},
                            "hazard": {
                                "rho": rates["RATE-MATCHED-HAZARD-CRTO"][0],
                                "lambda": rates["RATE-MATCHED-HAZARD-CRTO"][1],
                            },
                        }
                b_rho = float(np.mean(np.abs(signed_rho))) if len(signed_rho) == 8 else None
                b_lambda = float(np.mean(np.abs(signed_lambda))) if len(signed_lambda) == 8 else None
                passes = bool(b_rho is not None and b_rho <= 0.05 and b_lambda is not None and b_lambda <= 0.01)
                if not passes:
                    failures.append(f"event/cost rate-balance margin failed: {regime}:{label}")
                cell_output[label] = {
                    "B_rho": b_rho, "B_lambda": b_lambda, "pass": passes,
                    "per_seed": seed_rows,
                }

        overall_seed: dict[str, object] = {}
        overall_rho: list[float] = []
        overall_lambda: list[float] = []
        for seed in REGISTERED_SEEDS:
            rates = {}
            for method in methods:
                episodes, reviews, terms = overall_by_method[(method, seed)]
                if reviews == 0 or episodes == 0:
                    failures.append(f"zero overall scored denominator: {method}:{seed}:{regime}")
                    continue
                rates[method] = (terms / reviews, terms / (256.0 * episodes))
            if len(rates) == 2:
                rho_diff = rates["CRTO"][0] - rates["RATE-MATCHED-HAZARD-CRTO"][0]
                lambda_diff = rates["CRTO"][1] - rates["RATE-MATCHED-HAZARD-CRTO"][1]
                overall_rho.append(rho_diff)
                overall_lambda.append(lambda_diff)
                overall_seed[str(seed)] = {
                    "rho_CRTO_minus_hazard": rho_diff,
                    "lambda_CRTO_minus_hazard": lambda_diff,
                }
        b_rho = float(np.mean(np.abs(overall_rho))) if len(overall_rho) == 8 else None
        b_lambda = float(np.mean(np.abs(overall_lambda))) if len(overall_lambda) == 8 else None
        overall_pass = bool(b_rho is not None and b_rho <= 0.02 and b_lambda is not None and b_lambda <= 0.005)
        if not overall_pass:
            failures.append(f"overall rate-balance margin failed: {regime}")
        output[regime] = {
            "overall": {"B_rho": b_rho, "B_lambda": b_lambda, "pass": overall_pass,
                        "per_seed": overall_seed},
            "event_cost": cell_output,
            "pass": overall_pass and all(bool(value["pass"]) for value in cell_output.values()),
        }
    return {
        "available": not failures,
        "pass": not failures and all(bool(output[r]["pass"]) for r in TARGET_REGIMES),
        "target_regimes": output,
        "failure_reasons": failures,
        "delta_rate_withheld": bool(failures),
    }


@dataclass(frozen=True)
class BoundaryRecord:
    record_id: str
    seed: int
    regime: str
    panel: str
    episode_index: int
    target_agent_slot: int
    current_option: str
    current_k: int
    age: int
    legal_mask_bits: tuple[int, ...]
    event_class: str
    phase: int
    visible_cue: str
    cost: float

    def __post_init__(self) -> None:
        if not self.record_id:
            raise ValueError("record_id cannot be empty")
        if self.seed not in REGISTERED_SEEDS or self.regime not in REGIME_ORDER:
            raise ValueError("unregistered boundary seed or regime")
        if self.panel not in PANEL_ORDER:
            raise ValueError("panel must be scored or donor")
        if self.target_agent_slot not in range(4):
            raise ValueError("target agent environment slot must be in [0,3]")
        if len(self.legal_mask_bits) != 7 or any(bit not in (0, 1) for bit in self.legal_mask_bits):
            raise ValueError("legal mask must contain exactly seven bits")
        if self.event_class not in EVENT_ORDER or self.cost not in COSTS:
            raise ValueError("unregistered boundary event or cost")

    @property
    def match_key(self) -> tuple[object, ...]:
        return (
            self.current_option, self.current_k, self.age, self.legal_mask_bits,
            self.event_class, self.phase, self.visible_cue, self.cost,
        )

    @property
    def canonical_key(self) -> tuple[object, ...]:
        return (
            REGIME_ORDER[self.regime], PANEL_ORDER[self.panel], self.episode_index,
            self.target_agent_slot,
        )


@dataclass(frozen=True)
class DerangementAssignment:
    seed: int
    stratum_ordinal: int
    stratum_key: tuple[object, ...]
    recipient_record_id: str
    donor_record_id: str
    recipient_panel: str
    recipient_regime: str
    supported: bool


@dataclass(frozen=True)
class DerangementPlan:
    assignments: tuple[DerangementAssignment, ...]
    unsupported_cells: tuple[dict[str, object], ...]
    supported_scored_recipients: int
    eligible_scored_recipients: int
    scored_support_fraction: float | None
    alignment_available: bool
    technically_complete: bool
    failure_reasons: tuple[str, ...]


def uniform_derangement(size: int, seed: int) -> NDArray[np.int64] | None:
    """First of at most 10,000 rejection-sampled PCG64 Fisher-Yates derangements."""

    if size < 2:
        return None
    generator = np.random.Generator(np.random.PCG64(seed))
    identity = np.arange(size, dtype=np.int64)
    for _ in range(10_000):
        # Generator.permutation is NumPy's uniform in-place Fisher-Yates path;
        # using it also keeps this control byte-for-byte aligned with rng.py.
        permutation = generator.permutation(size).astype(np.int64, copy=False)
        if not np.any(permutation == identity):
            return permutation
    return None


def build_derangement_plan(records: Sequence[BoundaryRecord]) -> DerangementPlan:
    """Canonical exact-stratum partition and uniform intact-record derangement."""

    identifiers = [record.record_id for record in records]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("boundary record_id values must be globally unique")
    episode_ids = [
        (record.seed, record.regime, record.panel, record.episode_index) for record in records
    ]
    if len(set(episode_ids)) != len(episode_ids):
        raise ValueError("each episode may contribute at most one eligible boundary record")

    assignments: list[DerangementAssignment] = []
    unsupported: list[dict[str, object]] = []
    failures: list[str] = []
    supported_scored = 0
    eligible_scored = sum(record.panel == "scored" for record in records)
    for seed in REGISTERED_SEEDS:
        seed_records = sorted(
            (record for record in records if record.seed == seed),
            key=lambda record: record.canonical_key,
        )
        partitions: dict[tuple[object, ...], list[BoundaryRecord]] = {}
        for record in seed_records:
            partitions.setdefault(record.match_key, []).append(record)
        for ordinal, key in enumerate(sorted(partitions)):
            cell = partitions[key]
            if len(cell) < 8:
                unsupported.append({
                    "seed": seed, "stratum_ordinal": ordinal, "stratum_key": key,
                    "records": len(cell), "scored_recipients": sum(r.panel == "scored" for r in cell),
                })
                for recipient in cell:
                    assignments.append(DerangementAssignment(
                        seed, ordinal, key, recipient.record_id, "", recipient.panel,
                        recipient.regime, False,
                    ))
                continue
            permutation = uniform_derangement(
                len(cell), 7_000_003 + 1_009 * seed + ordinal,
            )
            if permutation is None:
                failures.append(f"seed {seed} stratum {ordinal}: no derangement in 10000 draws")
                for recipient in cell:
                    assignments.append(DerangementAssignment(
                        seed, ordinal, key, recipient.record_id, "", recipient.panel,
                        recipient.regime, False,
                    ))
                continue
            for recipient_index, donor_index in enumerate(permutation.tolist()):
                recipient, donor = cell[recipient_index], cell[donor_index]
                if recipient.record_id == donor.record_id:
                    raise RuntimeError("fixed point escaped derangement guard")
                assignments.append(DerangementAssignment(
                    seed, ordinal, key, recipient.record_id, donor.record_id,
                    recipient.panel, recipient.regime, True,
                ))
                supported_scored += int(recipient.panel == "scored")

    fraction = supported_scored / eligible_scored if eligible_scored else None
    available = not failures and fraction is not None and fraction >= 0.80
    if fraction is None:
        failures.append("no eligible scored recipients")
    elif fraction < 0.80:
        failures.append(f"supported scored-recipient fraction {fraction:.17g} is below 0.80")
    return DerangementPlan(
        tuple(assignments), tuple(unsupported), supported_scored, eligible_scored,
        fraction, available, not any("no derangement" in reason for reason in failures),
        tuple(failures),
    )


def terminal_potential(
    *,
    source_queues: Sequence[float],
    relay_buffers: Sequence[float],
    energies: Sequence[float],
) -> float:
    """Evaluation-only physical terminal potential Phi(s)."""

    queues = np.asarray(source_queues, dtype=np.float64)
    buffers = np.asarray(relay_buffers, dtype=np.float64)
    energy = np.asarray(energies, dtype=np.float64)
    if queues.shape != (2,) or buffers.shape != (2,) or energy.shape != (4,):
        raise ValueError("Phi requires two physical queues, two buffers, and four energies")
    if not (np.isfinite(queues).all() and np.isfinite(buffers).all() and np.isfinite(energy).all()):
        raise ValueError("Phi inputs must be finite")
    return float(-0.02 * (queues.sum() + buffers.sum()) - 0.01 * np.sum(32.0 - energy))


def discounted_g16(
    rewards: Sequence[float],
    *,
    total_physical_arrivals_on_episode_tape: float,
    physical_terminal_potential: float,
) -> float:
    """Exact normalized 16-step discounted audit return.

    ``rewards[0]`` must already include the enumerated action's immediate charge
    exactly once.  The function refuses shorter or longer branches.
    """

    values = np.asarray(rewards, dtype=np.float64)
    if values.shape != (16,) or not np.isfinite(values).all():
        raise ValueError("G16 requires exactly sixteen finite branch rewards")
    if not math.isfinite(total_physical_arrivals_on_episode_tape) or total_physical_arrivals_on_episode_tape < 0:
        raise ValueError("total physical arrivals must be finite and nonnegative")
    if not math.isfinite(physical_terminal_potential):
        raise ValueError("physical terminal potential must be finite")
    discounts = np.power(0.99, np.arange(16, dtype=np.float64))
    denominator = max(1.0, float(total_physical_arrivals_on_episode_tape))
    return float(
        (values @ discounts + (0.99 ** 16) * physical_terminal_potential) / denominator
    )


def audit_advantage_and_regret(
    action_returns: Mapping[str, float],
    *,
    aligned_action: str,
    deranged_action: str,
    printed_option_order: Sequence[str],
) -> dict[str, object]:
    """Apply the frozen legal-action, advantage, regret, and tie equations."""

    order = ("KEEP", *tuple(printed_option_order))
    if "KEEP" not in action_returns:
        raise ValueError("audit action set must contain KEEP")
    if aligned_action not in action_returns or deranged_action not in action_returns:
        raise ValueError("aligned and deranged actions must be legal enumerated actions")
    unknown = set(action_returns) - set(order)
    if unknown:
        raise ValueError(f"audit action set contains unregistered actions: {sorted(unknown)}")
    replacements = [action for action in order[1:] if action in action_returns]
    if not replacements:
        raise ValueError("audit boundary requires at least one different legal replacement")
    values = {action: float(action_returns[action]) for action in action_returns}
    if not all(math.isfinite(value) for value in values.values()):
        raise ValueError("audit action returns must be finite")
    legal_order = [action for action in order if action in values]
    maximum = max(values.values())
    maximizing_action = next(action for action in legal_order if values[action] == maximum)
    best_replacement = max(values[action] for action in replacements)
    advantage = best_replacement - values["KEEP"]
    aligned_regret = maximum - values[aligned_action]
    deranged_regret = maximum - values[deranged_action]
    return {
        "legal_action_order": legal_order,
        "maximizing_action": maximizing_action,
        "A16_replan": advantage,
        "aligned_regret16": 0.0 if values[aligned_action] == maximum else aligned_regret,
        "deranged_regret16": 0.0 if values[deranged_action] == maximum else deranged_regret,
        "delta_regret": (
            (0.0 if values[deranged_action] == maximum else deranged_regret)
            - (0.0 if values[aligned_action] == maximum else aligned_regret)
        ),
        "negative_or_nonpositive_advantage": advantage <= 0.0,
        "recovery_headroom": advantage >= 0.02,
    }


def termination_mass(relative_replacement_logits: Sequence[float]) -> float:
    """Stable temperature-one categorical termination mass with KEEP mass one."""

    logits = np.asarray(relative_replacement_logits, dtype=np.float64)
    if logits.ndim != 1 or logits.size == 0 or not np.isfinite(logits).all():
        raise ValueError("termination mass requires finite logits for legal replacements")
    maximum = max(0.0, float(np.max(logits)))
    keep = math.exp(-maximum)
    replacement_mass = float(np.exp(logits - maximum).sum())
    return replacement_mass / (keep + replacement_mass)
