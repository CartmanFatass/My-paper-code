"""Exact diagnostics, seed-level inference, and result assembly for CRTO-B1."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass, is_dataclass
import math
from typing import Mapping, Sequence

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.special import expit
from scipy.stats import rankdata
from scipy.stats import t as student_t

from .config import LEDGER_MAX_STEPS, OPTIONS, REGISTERED_MAX_STEPS
from .controls import (
    COSTS,
    EVENT_ORDER,
    REGIME_ORDER,
    REGISTERED_SEEDS,
    TARGET_REGIMES,
    DerangementPlan,
    fit_logistic_lbfgs,
)


FloatArray = NDArray[np.float64]
OPTION_ORDER = OPTIONS
HORIZONS = (4, 8, 12, 16)
REVISION = "CRTO-B1-SCIENCE-20260812-04"

STEP_CEILINGS = dict(LEDGER_MAX_STEPS)
REGISTERED_MAXIMUM_STEPS = REGISTERED_MAX_STEPS


def _finite_vector(values: ArrayLike, *, name: str, size: int | None = None) -> FloatArray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or (size is not None and array.size != size) or not np.isfinite(array).all():
        suffix = "" if size is None else f" of length {size}"
        raise ValueError(f"{name} must be a finite vector{suffix}")
    return array


def one_sided_student_t_bound(
    values: Sequence[float],
    *,
    confidence: float,
    side: str,
    require_registered_seeds: bool = True,
) -> dict[str, object]:
    """Frozen model-based one-sided Student-t bound on algorithm-seed effects."""

    array = _finite_vector(values, name="seed effects")
    if require_registered_seeds and array.size != 8:
        raise ValueError("a CRTO-B1 decision requires exactly eight algorithm-seed effects")
    if array.size < 2:
        raise ValueError("Student-t inference requires at least two seed effects")
    if side not in ("lower", "upper") or not 0.5 < confidence < 1.0:
        raise ValueError("invalid one-sided bound request")
    mean = float(array.mean())
    standard_deviation = float(array.std(ddof=1))
    standard_error = standard_deviation / math.sqrt(array.size)
    critical = float(student_t.ppf(confidence, array.size - 1))
    bound = mean if standard_deviation == 0.0 else (
        mean - critical * standard_error if side == "lower" else mean + critical * standard_error
    )
    return {
        "n": int(array.size),
        "seed_effects": array.tolist(),
        "mean": mean,
        "sample_standard_deviation": standard_deviation,
        "standard_error": standard_error,
        "degrees_of_freedom": int(array.size - 1),
        "confidence": confidence,
        "side": side,
        "bound": float(bound),
        "model": "iid Normal(theta,sigma^2) independent algorithm-seed effects",
        "distribution_free": False,
        "design_exact": False,
    }


def mann_whitney_auc(labels: ArrayLike, scores: ArrayLike) -> float:
    """Mann-Whitney AUC with average ranks, hence 0.5 credit for score ties."""

    y = _finite_vector(labels, name="AUC labels")
    score = _finite_vector(scores, name="AUC scores")
    if y.shape != score.shape or not np.isin(y, (0.0, 1.0)).all():
        raise ValueError("AUC labels/scores must align and labels must be binary")
    positive = y == 1.0
    n_positive = int(positive.sum())
    n_negative = int(y.size - n_positive)
    if n_positive == 0 or n_negative == 0:
        raise ValueError("AUC requires both donor and recipient observations")
    ranks = rankdata(score, method="average")
    u = float(ranks[positive].sum() - n_positive * (n_positive + 1) / 2.0)
    return u / (n_positive * n_negative)


def _one_hot(value: str, order: Sequence[str], *, name: str) -> tuple[float, ...]:
    if value not in order:
        raise ValueError(f"unknown {name}: {value!r}")
    return tuple(float(value == member) for member in order)


def donor_balance_feature_vectors(
    *,
    residual_r: ArrayLike,
    residual_p: ArrayLike,
    residual_a: ArrayLike,
    cholesky: ArrayLike,
    joint_option_counts: ArrayLike,
    location_counts: ArrayLike,
    current_option: str,
    current_k: int,
    age: int,
    legal_mask_bits: Sequence[int],
    event_class: str,
    phase: int,
    visible_cue: str,
    cost: float,
    regime: str,
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Construct the exact continuous and frozen balance-classifier features."""

    r = _finite_vector(residual_r, name="r", size=8)
    p = _finite_vector(residual_p, name="p", size=8)
    a = _finite_vector(residual_a, name="a", size=8)
    chol = np.asarray(cholesky, dtype=np.float64)
    if chol.shape != (8, 8) or not np.isfinite(chol).all():
        raise ValueError("Cholesky factor must be finite 8x8")
    if np.any(np.triu(chol, 1) != 0.0) or np.any(np.diag(chol) < 1e-3):
        raise ValueError("Cholesky factor must be lower triangular with diagonal at least 1e-3")
    option_counts = _finite_vector(joint_option_counts, name="option counts", size=7)
    locations = _finite_vector(location_counts, name="location counts", size=3)
    if not math.isclose(float(option_counts.sum()), 4.0, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("joint option counts must sum to four agents")
    if not math.isclose(float(locations.sum()), 4.0, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("location counts must sum to four agents")
    covariance_diagonal = np.sum(chol * chol, axis=1)
    continuous = (
        float(np.linalg.norm(r)), float(np.linalg.norm(p)), float(np.linalg.norm(a)),
        *(0.5 * np.log(covariance_diagonal)).tolist(),
        float(2.0 * np.log(np.diag(chol)).sum()),
        *(option_counts / 4.0).tolist(), *(locations / 4.0).tolist(),
    )
    if current_k not in (4, 8, 16) or age <= 0 or age % 4:
        raise ValueError("invalid K or age in balance features")
    if len(legal_mask_bits) != 7 or any(bit not in (0, 1) for bit in legal_mask_bits):
        raise ValueError("balance legal mask must have seven bits")
    if event_class not in EVENT_ORDER or visible_cue not in ("none", "L", "R"):
        raise ValueError("invalid event or cue in balance features")
    if cost not in COSTS or regime not in REGIME_ORDER:
        raise ValueError("invalid cost or regime in balance features")
    frozen = (
        *_one_hot(current_option, OPTION_ORDER, name="option"),
        current_k / 16.0, age / 16.0, *map(float, legal_mask_bits),
        *_one_hot(event_class, EVENT_ORDER, name="event"), phase / 5.0,
        *_one_hot(visible_cue, ("none", "L", "R"), name="visible cue"),
        cost / 4.0, *_one_hot(regime, tuple(REGIME_ORDER), name="regime"),
    )
    return tuple(map(float, continuous)), tuple(map(float, frozen))


@dataclass(frozen=True)
class BalanceRow:
    pair_id: str
    seed: int
    regime: str
    label: int  # recipient=0, assigned donor's original row=1
    continuous: tuple[float, ...]
    frozen: tuple[float, ...]


def donor_recipient_balance_diagnostic(rows: Sequence[BalanceRow]) -> dict[str, object]:
    """Eight-fold leave-one-seed-out fit and target-regime pooled AUC gates."""

    if not rows:
        return {"available": False, "pass": False, "failure_reasons": ["no balance rows"]}
    pairs: dict[tuple[int, str, str], list[int]] = defaultdict(list)
    continuous_size, frozen_size = len(rows[0].continuous), len(rows[0].frozen)
    for index, row in enumerate(rows):
        if row.seed not in REGISTERED_SEEDS or row.regime not in REGIME_ORDER or row.label not in (0, 1):
            raise ValueError("unregistered balance row")
        if len(row.continuous) != continuous_size or len(row.frozen) != frozen_size:
            raise ValueError("balance feature dimensions must be constant")
        _finite_vector(row.continuous, name="continuous balance features")
        _finite_vector(row.frozen, name="frozen balance features")
        pairs[(row.seed, row.regime, row.pair_id)].append(index)
    malformed = [key for key, indices in pairs.items() if len(indices) != 2 or {rows[i].label for i in indices} != {0, 1}]
    if malformed:
        raise ValueError(f"each supported scored recipient needs one 0/1 pair; malformed={malformed[:5]}")
    if set(row.seed for row in rows) != set(REGISTERED_SEEDS):
        return {"available": False, "pass": False, "failure_reasons": ["not all eight seeds have balance rows"]}

    held_out: list[dict[str, object]] = []
    fits: dict[str, object] = {}
    failures: list[str] = []
    for held_seed in REGISTERED_SEEDS:
        train_rows = [row for row in rows if row.seed != held_seed]
        test_rows = [row for row in rows if row.seed == held_seed]
        train_cont = np.asarray([row.continuous for row in train_rows], dtype=np.float64)
        mean = train_cont.mean(axis=0)
        scale = train_cont.std(axis=0, ddof=0)
        scale[scale == 0.0] = 1.0

        def matrix(selected: Sequence[BalanceRow]) -> FloatArray:
            cont = (np.asarray([row.continuous for row in selected], dtype=np.float64) - mean) / scale
            frozen = np.asarray([row.frozen for row in selected], dtype=np.float64)
            return np.column_stack((np.ones(len(selected)), cont, frozen))

        train_x, test_x = matrix(train_rows), matrix(test_rows)
        fit = fit_logistic_lbfgs(train_x, [row.label for row in train_rows])
        fits[str(held_seed)] = {
            "converged": fit.converged, "iterations": fit.iterations,
            "gradient_inf_norm": fit.gradient_inf_norm, "message": fit.message,
        }
        if not fit.converged:
            failures.append(f"held-out seed {held_seed} balance L-BFGS did not converge")
        probabilities = expit(test_x @ fit.coefficients)
        held_out.extend({
            "seed": held_seed, "regime": row.regime, "label": row.label,
            "pair_id": row.pair_id, "probability": float(probability),
        } for row, probability in zip(test_rows, probabilities, strict=True))
    auc_by_regime: dict[str, float | None] = {}
    for regime in REGIME_ORDER:
        selected = [row for row in held_out if row["regime"] == regime]
        try:
            auc_by_regime[regime] = mann_whitney_auc(
                [int(row["label"]) for row in selected],
                [float(row["probability"]) for row in selected],
            )
        except ValueError:
            auc_by_regime[regime] = None
            failures.append(f"regime {regime} lacks both AUC classes")
    target_pass = all(auc_by_regime[regime] is not None and float(auc_by_regime[regime]) <= 0.60
                      for regime in TARGET_REGIMES)
    if not target_pass:
        failures.append("at least one target-regime donor/recipient AUC exceeds 0.60")
    return {
        "available": not any("did not converge" in reason or "lacks both" in reason for reason in failures),
        "pass": not failures and target_pass,
        "auc_by_regime": auc_by_regime,
        "fold_fits": fits,
        "held_out_predictions": held_out,
        "failure_reasons": failures,
        "interpretation": "registered-feature validity diagnostic, not distributional equality proof",
    }


def empirical_mid_cdf(calibration_values: ArrayLike, value: float) -> float:
    samples = _finite_vector(calibration_values, name="calibration residuals")
    if samples.size == 0 or not math.isfinite(value):
        raise ValueError("empirical CDF requires samples and a finite query")
    less = int(np.count_nonzero(samples < value))
    equal = int(np.count_nonzero(samples == value))
    return (less + 0.5 * equal + 0.5) / (samples.size + 1.0)


@dataclass(frozen=True)
class CalibrationObservation:
    seed: int
    regime: str
    horizon: int
    whitened: tuple[float, ...]
    pit: tuple[float, ...]


def make_calibration_observation(
    *, seed: int, regime: str, horizon: int, whitened: ArrayLike,
    training_calibration_by_coordinate: Sequence[ArrayLike],
) -> CalibrationObservation:
    e = _finite_vector(whitened, name="whitened residual", size=8)
    if len(training_calibration_by_coordinate) != 8:
        raise ValueError("one frozen empirical CDF table is required per coordinate")
    pit = tuple(empirical_mid_cdf(table, float(e[d])) for d, table in enumerate(training_calibration_by_coordinate))
    return CalibrationObservation(seed, regime, horizon, tuple(e.tolist()), pit)


def calibration_diagnostic(observations: Sequence[CalibrationObservation]) -> dict[str, object]:
    """Seed-balanced ellipsoid, PIT-ECE, and |e|>=6 saturation diagnostics."""

    grouped: dict[tuple[str, int, int], list[CalibrationObservation]] = defaultdict(list)
    for row in observations:
        if row.seed not in REGISTERED_SEEDS or row.regime not in REGIME_ORDER or row.horizon not in HORIZONS:
            raise ValueError("unregistered calibration observation")
        e = _finite_vector(row.whitened, name="whitened residual", size=8)
        u = _finite_vector(row.pit, name="PIT values", size=8)
        if np.any((u < 0.0) | (u > 1.0)):
            raise ValueError("PIT values must lie in [0,1]")
        grouped[(row.regime, row.horizon, row.seed)].append(row)

    report: dict[str, object] = {}
    failures: list[str] = []
    for regime in TARGET_REGIMES:
        horizon_rows: dict[str, object] = {}
        for horizon in HORIZONS:
            per_seed: dict[str, object] = {}
            coverages: list[float] = []
            pit_frequencies: list[FloatArray] = []
            saturations: list[float] = []
            for seed in REGISTERED_SEEDS:
                selected = grouped.get((regime, horizon, seed), [])
                if not selected:
                    continue
                e = np.asarray([row.whitened for row in selected], dtype=np.float64)
                u = np.asarray([row.pit for row in selected], dtype=np.float64)
                coverage = float(np.mean(np.sum(e * e, axis=1) <= 13.3615661365))
                frequencies = np.zeros((8, 10), dtype=np.float64)
                bins = np.minimum(9, np.floor(10.0 * u).astype(np.int64))
                for coordinate in range(8):
                    frequencies[coordinate] = np.bincount(bins[:, coordinate], minlength=10) / len(selected)
                saturation = float(np.mean(np.abs(e) >= 6.0))
                per_seed[str(seed)] = {
                    "eligible_targets": len(selected), "coverage": coverage,
                    "pit_bin_frequencies": frequencies.tolist(), "saturation": saturation,
                }
                coverages.append(coverage)
                pit_frequencies.append(frequencies)
                saturations.append(saturation)
            complete = len(coverages) == 8
            if regime == "K16" and (not complete or any(int(per_seed[str(seed)]["eligible_targets"]) < 32
                                                        for seed in REGISTERED_SEEDS if str(seed) in per_seed)):
                failures.append(f"K16 horizon {horizon} lacks 32 eligible targets in every seed")
            coverage_mean = float(np.mean(coverages)) if complete else None
            mean_frequencies = np.mean(pit_frequencies, axis=0) if complete else None
            ece = (0.5 * np.sum(np.abs(mean_frequencies - 0.1), axis=1)) if complete else None
            saturation_mean = float(np.mean(saturations)) if complete else None
            gate = bool(
                complete and coverage_mean is not None and 0.80 <= coverage_mean <= 0.98
                and ece is not None and float(np.max(ece)) <= 0.10
                and saturation_mean is not None and saturation_mean < 0.05
            ) if regime == "K16" else None
            if regime == "K16" and not gate:
                failures.append(f"K16 horizon {horizon} calibration margin failed")
            horizon_rows[str(horizon)] = {
                "per_seed": per_seed, "seed_balanced_coverage": coverage_mean,
                "seed_balanced_pit_bin_frequencies": mean_frequencies.tolist() if mean_frequencies is not None else None,
                "PIT_ECE_by_coordinate": ece.tolist() if ece is not None else None,
                "max_PIT_ECE": float(np.max(ece)) if ece is not None else None,
                "seed_balanced_saturation": saturation_mean,
                "fixed_K16_gate": gate,
            }
        report[regime] = horizon_rows
    return {"available": not failures, "pass": not failures, "by_regime_horizon": report,
            "failure_reasons": failures}


@dataclass(frozen=True)
class AuditState:
    seed: int
    regime: str
    episode_index: int
    event_class: str
    cost: float
    s_adv: float
    a16_replan: float
    aligned_action: str | None = None
    deranged_action: str | None = None
    aligned_regret: float | None = None
    deranged_regret: float | None = None
    # True only when this scored recipient survived exact-stratum support
    # filtering and received a persisted fixed derangement assignment.  G16,
    # headroom, trend, and shadow populations do not condition on this flag.
    # Kept last so older positional construction fails closed to False rather
    # than shifting action/regret fields.
    derangement_supported: bool = False


def adverse_residual_trend(
    states: Sequence[AuditState], *, permutations: int = 100_000,
) -> dict[str, object]:
    """Exact blocked 100,000-replicate PCG64 adverse-residual trend diagnostic."""

    if permutations != 100_000:
        raise ValueError("CRTO-B1 freezes exactly 100000 trend permutations")
    selected = [
        state for state in states
        if state.regime in TARGET_REGIMES
        and state.event_class == "UNANNOUNCED-DIFFERENTIAL"
        and state.cost == 0.25
    ]
    failures: list[str] = []
    indexed: list[tuple[AuditState, int]] = []
    seed_quintile_means: dict[str, dict[str, float]] = {}
    for seed in REGISTERED_SEEDS:
        seed_states = [state for state in selected if state.seed == seed]
        if len(seed_states) < 5:
            failures.append(f"seed {seed} has fewer than five trend states")
            continue
        if any(not any(state.regime == regime for state in seed_states) for regime in TARGET_REGIMES):
            failures.append(f"seed {seed} lacks a target regime in the trend population")
            continue
        ordered = sorted(seed_states, key=lambda state: (
            state.s_adv, REGIME_ORDER[state.regime], state.episode_index,
        ))
        quintiles: dict[int, list[float]] = defaultdict(list)
        for rank, state in enumerate(ordered, start=1):
            quintile = 1 + math.floor(5 * (rank - 1) / len(ordered))
            quintiles[quintile].append(state.a16_replan)
            indexed.append((state, quintile))
        if set(quintiles) != {1, 2, 3, 4, 5}:
            failures.append(f"seed {seed} does not populate all trend quintiles")
            continue
        seed_quintile_means[str(seed)] = {
            str(q): float(np.mean(quintiles[q])) for q in range(1, 6)
        }
    if failures:
        return {"available": False, "pass": False, "failure_reasons": failures}

    aggregate = [
        float(np.mean([seed_quintile_means[str(seed)][str(q)] for seed in REGISTERED_SEEDS]))
        for q in range(1, 6)
    ]
    nondecreasing = all(aggregate[index] <= aggregate[index + 1] for index in range(4))
    observed = sum(
        (q - 3) * seed_quintile_means[str(seed)][str(q)]
        for seed in REGISTERED_SEEDS for q in range(1, 6)
    ) / 8.0

    # Express T as a fixed weighted sum.  The null shuffles only A16 values
    # within (seed,regime), leaving states, S_adv ranks, and quintiles fixed.
    blocks: list[tuple[FloatArray, FloatArray]] = []
    for seed in REGISTERED_SEEDS:
        for regime in TARGET_REGIMES:
            block = [(state, quintile) for state, quintile in indexed
                     if state.seed == seed and state.regime == regime]
            block.sort(key=lambda item: item[0].episode_index)
            values = np.asarray([item[0].a16_replan for item in block], dtype=np.float64)
            counts = {q: sum(item[1] == q for item in indexed if item[0].seed == seed) for q in range(1, 6)}
            weights = np.asarray([(quintile - 3) / (8.0 * counts[quintile]) for _, quintile in block],
                                 dtype=np.float64)
            blocks.append((values, weights))
    generator = np.random.Generator(np.random.PCG64(9_000_001))
    exceedances = 0
    for _ in range(permutations):
        statistic = 0.0
        for values, weights in blocks:
            statistic += float(generator.permutation(values) @ weights)
        exceedances += int(statistic >= observed)
    p_value = (1 + exceedances) / 100_001.0
    return {
        "available": True, "pass": nondecreasing and p_value <= 0.05,
        "seed_quintile_means": seed_quintile_means,
        "aggregate_quintile_means": aggregate, "nondecreasing": nondecreasing,
        "T_observed": observed, "permutations": permutations,
        "T_perm_ge_observed": exceedances, "plus_one_p_value": p_value,
        "association_not_design_exact_causal": True, "failure_reasons": [],
    }


@dataclass(frozen=True)
class ShadowScore:
    seed: int
    regime: str
    event_class: str
    cost: float
    a16_replan: float
    p_term_crto: float
    p_term_full: float


def shortcut_shadow_diagnostic(rows: Sequence[ShadowScore]) -> dict[str, object]:
    """Exact same-history shadow-score populations and 95% upper bounds."""

    populations = {
        "COMMON-SENSOR": lambda row: row.event_class == "COMMON-SENSOR",
        "CUED-DIFFERENTIAL": lambda row: row.event_class == "CUED-DIFFERENTIAL",
        "c_high_A16_nonpositive": lambda row: row.cost == 4.0 and row.a16_replan <= 0.0,
    }
    output: dict[str, object] = {}
    failures: list[str] = []
    for name, predicate in populations.items():
        seed_effects: list[float] = []
        per_seed_regime: dict[str, object] = {}
        for seed in REGISTERED_SEEDS:
            regime_means: list[float] = []
            seed_detail: dict[str, float] = {}
            for regime in TARGET_REGIMES:
                selected = [row for row in rows if row.seed == seed and row.regime == regime and predicate(row)]
                if not selected:
                    failures.append(f"shadow population {name} empty for seed {seed}, regime {regime}")
                    continue
                differences = []
                for row in selected:
                    if not (0.0 <= row.p_term_crto <= 1.0 and 0.0 <= row.p_term_full <= 1.0):
                        raise ValueError("shadow termination masses must lie in [0,1]")
                    differences.append(row.p_term_crto - row.p_term_full)
                mean = float(np.mean(differences))
                seed_detail[regime] = mean
                regime_means.append(mean)
            if len(regime_means) == 3:
                seed_effects.append(float(np.mean(regime_means)))
                per_seed_regime[str(seed)] = seed_detail
        if len(seed_effects) == 8:
            upper = one_sided_student_t_bound(seed_effects, confidence=0.95, side="upper")
            passes = float(upper["bound"]) <= 0.05
        else:
            upper, passes = None, False
        if not passes:
            failures.append(f"shadow population {name} upper-bound condition failed")
        output[name] = {
            "per_seed_regime": per_seed_regime, "seed_equal_regime_effects": seed_effects,
            "student_t_95_upper": upper, "pass": passes,
        }
    return {"available": not any("empty" in reason for reason in failures),
            "pass": not failures, "populations": output, "failure_reasons": failures}


@dataclass(frozen=True)
class EpisodeOutcome:
    method: str
    seed: int
    regime: str
    scenario_id: str
    normalized_return: float
    failure: float


def _paired_seed_regime_effects(
    rows: Sequence[EpisodeOutcome], *, left: str, right: str, metric: str,
) -> dict[int, dict[str, float]]:
    lookup: dict[tuple[str, int, str, str], float] = {}
    for row in rows:
        if row.seed not in REGISTERED_SEEDS or row.regime not in REGIME_ORDER:
            raise ValueError("unregistered outcome seed or regime")
        value = float(getattr(row, metric))
        if not math.isfinite(value):
            raise ValueError("episode outcome must be finite")
        key = (row.method, row.seed, row.regime, row.scenario_id)
        if key in lookup:
            raise ValueError(f"duplicate episode outcome {key}")
        lookup[key] = value
    effects: dict[int, dict[str, float]] = {seed: {} for seed in REGISTERED_SEEDS}
    for seed in REGISTERED_SEEDS:
        for regime in REGIME_ORDER:
            left_ids = {key[3] for key in lookup if key[:3] == (left, seed, regime)}
            right_ids = {key[3] for key in lookup if key[:3] == (right, seed, regime)}
            if not left_ids and not right_ids:
                continue
            if left_ids != right_ids:
                raise ValueError(f"paired scenario mismatch for {left}/{right}, seed {seed}, regime {regime}")
            effects[seed][regime] = float(np.mean([
                lookup[(left, seed, regime, scenario)] - lookup[(right, seed, regime, scenario)]
                for scenario in sorted(left_ids)
            ]))
    return effects


def _equal_target_effects(per_seed_regime: Mapping[int, Mapping[str, float]]) -> list[float]:
    values = []
    for seed in REGISTERED_SEEDS:
        if any(regime not in per_seed_regime.get(seed, {}) for regime in TARGET_REGIMES):
            raise ValueError(f"seed {seed} lacks a target-regime effect")
        values.append(float(np.mean([per_seed_regime[seed][regime] for regime in TARGET_REGIMES])))
    return values


def primary_estimands(rows: Sequence[EpisodeOutcome]) -> dict[str, object]:
    utility = _paired_seed_regime_effects(rows, left="CRTO", right="FULL-HISTORY-AUX-TERM",
                                          metric="normalized_return")
    failure = _paired_seed_regime_effects(rows, left="CRTO", right="FULL-HISTORY-AUX-TERM",
                                          metric="failure")
    delta_j = _equal_target_effects(utility)
    delta_f = _equal_target_effects(failure)
    j_lower_975 = one_sided_student_t_bound(delta_j, confidence=0.975, side="lower")
    f_upper_975 = one_sided_student_t_bound(delta_f, confidence=0.975, side="upper")
    j_lower_95 = one_sided_student_t_bound(delta_j, confidence=0.95, side="lower")
    performance = float(j_lower_975["bound"]) > 0.02
    robustness = float(f_upper_975["bound"]) < -0.05 and float(j_lower_95["bound"]) > -0.01
    nonharm: dict[str, object] = {}
    for regime in TARGET_REGIMES:
        utility_values = [utility[seed][regime] for seed in REGISTERED_SEEDS]
        failure_values = [failure[seed][regime] for seed in REGISTERED_SEEDS]
        utility_bound = one_sided_student_t_bound(
            utility_values, confidence=1.0 - 0.05 / 6.0, side="lower",
        )
        failure_bound = one_sided_student_t_bound(
            failure_values, confidence=1.0 - 0.05 / 6.0, side="upper",
        )
        nonharm[regime] = {
            "utility_lower": utility_bound, "failure_upper": failure_bound,
            "pass": float(utility_bound["bound"]) > -0.02 and float(failure_bound["bound"]) < 0.05,
        }
    degradation: dict[str, object] = {}
    for method in ("CRTO", "FULL-HISTORY-AUX-TERM"):
        by_method = {}
        for seed in REGISTERED_SEEDS:
            grouped = defaultdict(list)
            for row in rows:
                if row.method == method and row.seed == seed and row.regime in ("K8", "K16"):
                    grouped[row.regime].append(row.normalized_return)
            if set(grouped) == {"K8", "K16"}:
                by_method[str(seed)] = float(np.mean(grouped["K16"]) - np.mean(grouped["K8"]))
        degradation[method] = by_method
    return {
        "per_seed_per_regime": {
            str(seed): {regime: {"Delta_J": utility[seed].get(regime), "Delta_F": failure[seed].get(regime)}
                        for regime in REGIME_ORDER}
            for seed in REGISTERED_SEEDS
        },
        "Delta_J": {"seed_effects": delta_j, "lower_97_5": j_lower_975, "lower_95": j_lower_95},
        "Delta_F": {"seed_effects": delta_f, "upper_97_5": f_upper_975},
        "performance_route": performance, "robustness_route": robustness,
        "primary_route": performance or robustness,
        "six_nonharm_conditions": nonharm,
        "nonharm_pass": all(bool(value["pass"]) for value in nonharm.values()),
        "degradation_J16_minus_J8": degradation,
    }


def mechanism_estimand(
    rows: Sequence[EpisodeOutcome], *, left: str, right: str, label: str,
    margin: float, available: bool = True,
) -> dict[str, object]:
    effects = _paired_seed_regime_effects(rows, left=left, right=right, metric="normalized_return")
    seed_effects = _equal_target_effects(effects)
    lower = one_sided_student_t_bound(seed_effects, confidence=0.95, side="lower")
    return {
        "label": label, "per_seed_per_regime": {str(seed): effects[seed] for seed in REGISTERED_SEEDS},
        "seed_equal_regime_effects": seed_effects, "student_t_95_lower": lower,
        "margin": margin, "available": available,
        "pass": available and float(lower["bound"]) > margin,
    }


def audit_mechanism_diagnostics(states: Sequence[AuditState]) -> dict[str, object]:
    """Audit diagnostics with the frozen all-state/supported-state split.

    Recovery headroom uses every eligible scored audit state.  Decision
    disagreement and ``Delta_regret`` use only exact-stratum-supported scored
    recipients.  Missing supported seed/regime populations make those
    diagnostics unavailable; unsupported states are never represented as
    artificial aligned actions or zero regrets.
    """

    disagreement: list[float] = []
    regret_seed_regime: dict[int, dict[str, float]] = {seed: {} for seed in REGISTERED_SEEDS}
    headroom: dict[str, float | None] = {}
    all_counts: dict[str, dict[str, int]] = {}
    supported_counts: dict[str, dict[str, int]] = {}
    headroom_failures: list[str] = []
    first_stage_failures: list[str] = []
    regret_failures: list[str] = []
    for seed in REGISTERED_SEEDS:
        seed_states = [
            state for state in states if state.seed == seed and state.regime in TARGET_REGIMES
        ]
        all_counts[str(seed)] = {
            regime: sum(state.regime == regime for state in seed_states)
            for regime in TARGET_REGIMES
        }
        missing_all = [regime for regime, count in all_counts[str(seed)].items() if count == 0]
        if not seed_states or missing_all:
            headroom[str(seed)] = None
            headroom_failures.append(
                f"seed {seed} lacks all-audit states for regimes {missing_all or list(TARGET_REGIMES)}"
            )
        else:
            headroom[str(seed)] = float(np.mean([
                state.a16_replan >= 0.02 for state in seed_states
            ]))

        supported = [state for state in seed_states if state.derangement_supported]
        supported_counts[str(seed)] = {
            regime: sum(state.regime == regime for state in supported)
            for regime in TARGET_REGIMES
        }
        if not supported:
            first_stage_failures.append(f"seed {seed} has no supported derangement recipients")
        elif any(state.aligned_action is None or state.deranged_action is None for state in supported):
            first_stage_failures.append(f"seed {seed} has supported recipients without both actions")
        else:
            disagreement.append(float(np.mean([
                state.aligned_action != state.deranged_action for state in supported
            ])))
        for regime in TARGET_REGIMES:
            selected = [state for state in supported if state.regime == regime]
            if not selected:
                regret_failures.append(f"seed {seed}, regime {regime} has no supported recipients")
                continue
            if any(state.aligned_regret is None or state.deranged_regret is None for state in selected):
                regret_failures.append(
                    f"seed {seed}, regime {regime} has supported recipients without both regrets"
                )
                continue
            regret_seed_regime[seed][regime] = float(np.mean([
                float(state.deranged_regret) - float(state.aligned_regret) for state in selected
            ]))

    headroom_available = not headroom_failures
    headroom_pass = headroom_available and all(
        value is not None and value >= 0.20 for value in headroom.values()
    )
    first_stage_available = not first_stage_failures and len(disagreement) == 8
    first_stage = (
        one_sided_student_t_bound(disagreement, confidence=0.95, side="lower")
        if first_stage_available else None
    )
    first_stage_pass = bool(
        first_stage is not None and float(first_stage["bound"]) > 0.05
    )
    regret_available = not regret_failures and all(
        all(regime in regret_seed_regime[seed] for regime in TARGET_REGIMES)
        for seed in REGISTERED_SEEDS
    )
    regret_effects = _equal_target_effects(regret_seed_regime) if regret_available else []
    regret_lower = (
        one_sided_student_t_bound(regret_effects, confidence=0.95, side="lower")
        if regret_available else None
    )
    regret_pass = bool(regret_lower is not None and float(regret_lower["bound"]) > 0.0)
    failures = [*headroom_failures, *first_stage_failures, *regret_failures]
    return {
        "available": headroom_available and first_stage_available and regret_available,
        "all_audit_state_counts": all_counts,
        "supported_derangement_recipient_counts": supported_counts,
        "decision_disagreement": {
            "population": "exact-stratum-supported scored recipients only",
            "available": first_stage_available,
            "seed_fractions": disagreement if first_stage_available else None,
            "student_t_95_lower": first_stage,
            "pass": first_stage_pass,
            "failure_reasons": first_stage_failures,
        },
        "headroom_population": "every eligible scored audit state",
        "headroom_available": headroom_available,
        "headroom_fraction_by_seed": headroom, "headroom_pass": headroom_pass,
        "headroom_failure_reasons": headroom_failures,
        "Delta_regret": {
            "population": "exact-stratum-supported scored recipients only",
            "available": regret_available,
            "per_seed_per_regime": {str(seed): regret_seed_regime[seed] for seed in REGISTERED_SEEDS},
            "seed_equal_regime_effects": regret_effects if regret_available else None,
            "student_t_95_lower": regret_lower,
            "pass": regret_pass,
            "failure_reasons": regret_failures,
        },
        "pass": first_stage_pass and headroom_pass and regret_pass,
        "failure_reasons": failures,
    }


def resource_conformance(
    actual_steps: Mapping[str, int], *, wall_seconds: float, peak_rss_bytes: int,
    gpu_used: bool, cpu_count: int,
) -> dict[str, object]:
    failures: list[str] = []
    if set(actual_steps) != set(STEP_CEILINGS):
        missing = sorted(set(STEP_CEILINGS) - set(actual_steps))
        extra = sorted(set(actual_steps) - set(STEP_CEILINGS))
        failures.append(f"step-ledger categories mismatch missing={missing} extra={extra}")
    for category, ceiling in STEP_CEILINGS.items():
        value = actual_steps.get(category)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            failures.append(f"invalid step count for {category}")
        elif value > ceiling:
            failures.append(f"{category} exceeds {ceiling}")
    total = sum(value for value in actual_steps.values() if isinstance(value, int) and not isinstance(value, bool))
    if total > REGISTERED_MAXIMUM_STEPS:
        failures.append("registered total primitive-team-step maximum exceeded")
    if not math.isfinite(wall_seconds) or wall_seconds > 7_200.0 or wall_seconds < 0.0:
        failures.append("120-minute wall-time ceiling violated")
    if peak_rss_bytes < 0 or peak_rss_bytes > 2 * 1024 ** 3:
        failures.append("2-GiB resident-memory ceiling violated")
    if gpu_used or cpu_count != 1:
        failures.append("one-CPU/no-GPU envelope violated")
    return {
        "pass": not failures, "actual_steps": dict(actual_steps), "category_ceilings": STEP_CEILINGS,
        "actual_total_steps": total, "registered_maximum_steps": REGISTERED_MAXIMUM_STEPS,
        "wall_seconds": wall_seconds, "peak_rss_bytes": peak_rss_bytes,
        "gpu_used": gpu_used, "cpu_count": cpu_count, "failure_reasons": failures,
    }


def validity_decisions(
    *,
    conformance: Mapping[str, bool],
    probe_by_seed: Mapping[int, Mapping[str, float]],
    target_action_counts: Mapping[str, Mapping[str, int]],
    audit_boundary_counts: Mapping[int, Mapping[str, int]],
    derangement: DerangementPlan,
    hazard_fit_converged: bool,
    hazard_target_support_pass: bool,
    rate_balance: Mapping[str, object],
    balance_diagnostic: Mapping[str, object],
    calibration: Mapping[str, object],
    audit: Mapping[str, object],
) -> dict[str, object]:
    """Fail-closed whole-package and residual-mechanism validity decisions."""

    core_required = (
        "all_eight_seeds", "all_frozen_evaluation_cells", "finite_returns",
        "identical_scenario_counts", "exact_action_cost_parity", "no_test_leakage",
    )
    core_failures = [name for name in core_required if not bool(conformance.get(name, False))]
    probe_failures = [
        str(seed) for seed in REGISTERED_SEEDS
        if seed not in probe_by_seed
        or float(probe_by_seed[seed].get("normalized_mse", math.inf)) > 0.01
        or float(probe_by_seed[seed].get("sign_accuracy", -math.inf)) < 0.95
    ]
    action_failures = []
    for regime in TARGET_REGIMES:
        counts = target_action_counts.get(regime, {})
        reviews = int(counts.get("legal_reviews", 0))
        keep = int(counts.get("keep", 0))
        changed = int(counts.get("changed_option", 0))
        if reviews < 512 or keep < 0.10 * reviews or changed < 0.10 * reviews:
            action_failures.append(regime)
    boundary_failures = [
        f"{seed}:{regime}" for seed in REGISTERED_SEEDS for regime in TARGET_REGIMES
        if int(audit_boundary_counts.get(seed, {}).get(regime, 0)) < 48
    ]
    whole_valid = not core_failures and not probe_failures
    mechanism_failures = []
    if action_failures:
        mechanism_failures.append(f"action support failed: {action_failures}")
    if boundary_failures:
        mechanism_failures.append(f"audit boundary availability failed: {boundary_failures}")
    if not derangement.alignment_available:
        mechanism_failures.append("derangement support/technical completion failed")
    if not hazard_fit_converged or not hazard_target_support_pass:
        mechanism_failures.append("hazard convergence or target-cell support failed")
    if not bool(rate_balance.get("pass", False)):
        mechanism_failures.append("scored own-trajectory rate balance failed")
    if not bool(balance_diagnostic.get("pass", False)):
        mechanism_failures.append("donor/recipient AUC diagnostic failed")
    if not bool(calibration.get("pass", False)):
        mechanism_failures.append("fixed-K16 calibration failed")
    if not bool(audit.get("decision_disagreement", {}).get("pass", False)):
        mechanism_failures.append("derangement first stage failed")
    if not bool(audit.get("headroom_pass", False)):
        mechanism_failures.append("recovery headroom failed")
    return {
        "whole_algorithm_valid": whole_valid,
        "residual_mechanism_valid": whole_valid and not mechanism_failures,
        "core_conformance_failures": core_failures,
        "probe_failures": probe_failures,
        "action_support_failures": action_failures,
        "audit_boundary_failures": boundary_failures,
        "mechanism_failure_reasons": mechanism_failures,
        "delta_rate_available": (
            hazard_fit_converged and hazard_target_support_pass and bool(rate_balance.get("pass", False))
        ),
    }


def registered_package_and_mechanism_decisions(
    *,
    primary: Mapping[str, object],
    validity: Mapping[str, object],
    delta_align: Mapping[str, object],
    delta_q: Mapping[str, object],
    delta_rate: Mapping[str, object],
    audit: Mapping[str, object],
    trend: Mapping[str, object],
    shortcut: Mapping[str, object],
) -> dict[str, object]:
    """Apply the frozen distinction between package value and mechanism support."""

    package_value = bool(
        validity.get("whole_algorithm_valid", False)
        and primary.get("primary_route", False)
        and primary.get("nonharm_pass", False)
    )
    mechanism_conditions = {
        "residual_mechanism_validity": bool(validity.get("residual_mechanism_valid", False)),
        "Delta_align": bool(delta_align.get("pass", False)),
        "Delta_Q": bool(delta_q.get("pass", False)),
        "Delta_rate": bool(delta_rate.get("pass", False)),
        "Delta_regret": bool(audit.get("Delta_regret", {}).get("pass", False)),
        "adverse_residual_trend": bool(trend.get("pass", False)),
        "shortcut_shadow_scores": bool(shortcut.get("pass", False)),
    }
    mechanism = all(mechanism_conditions.values())
    return {
        "package_value": package_value,
        "registered_residual_mechanism": mechanism,
        "direct_algorithm_value_plus_residual_mechanism": package_value and mechanism,
        "package_value_without_residual_attribution": package_value and not mechanism,
        "residual_use_without_algorithm_value": mechanism and not package_value,
        "mechanism_conditions": mechanism_conditions,
        "claim_scope": "exact B1 package and registered local interventions only",
    }


def exact_b1_retirement_decision(
    *,
    validity_and_all_mechanism_gates_pass: bool,
    per_metric_seed_regime_effects: Mapping[str, Mapping[int, Mapping[str, float]]],
) -> dict[str, object]:
    """Evaluate the exact 18-bound package-retirement branch.

    Effects must be oriented so larger is beneficial: ``Delta_R`` is
    ``-Delta_F`` and the other names follow the science card.
    """

    margins = {
        "Delta_J": 0.02, "Delta_R": 0.05, "Delta_align": 0.01,
        "Delta_Q": 0.005, "Delta_rate": 0.005, "Delta_regret": 0.005,
    }
    bounds: dict[str, object] = {}
    failures: list[str] = []
    for metric, margin in margins.items():
        metric_effects = per_metric_seed_regime_effects.get(metric)
        if metric_effects is None:
            failures.append(f"missing retirement metric {metric}")
            continue
        metric_bounds: dict[str, object] = {}
        for regime in TARGET_REGIMES:
            try:
                values = [float(metric_effects[seed][regime]) for seed in REGISTERED_SEEDS]
            except (KeyError, TypeError, ValueError):
                failures.append(f"missing retirement effects for {metric}:{regime}")
                continue
            try:
                upper = one_sided_student_t_bound(
                    values, confidence=1.0 - 0.05 / 18.0, side="upper",
                )
            except ValueError as error:
                failures.append(f"invalid retirement effects for {metric}:{regime}: {error}")
                continue
            below = float(upper["bound"]) < margin
            if not below:
                failures.append(f"absence unresolved for {metric}:{regime}")
            metric_bounds[regime] = {"upper": upper, "margin": margin, "below_margin": below}
        bounds[metric] = metric_bounds
    retire = validity_and_all_mechanism_gates_pass and not failures
    return {
        "retire_exact_B1_package": retire,
        "validity_and_all_mechanism_gates_pass": validity_and_all_mechanism_gates_pass,
        "bonferroni_99_7222pct_upper_bounds": bounds,
        "failure_or_unresolved_reasons": failures,
        "does_not_delete_general_CRTO_family": True,
        "does_not_establish_warehouse_or_UAV_value": True,
    }


def retirement_decision_from_analysis_outputs(
    *,
    validity_and_all_mechanism_gates_pass: bool,
    primary: Mapping[str, object],
    delta_align: Mapping[str, object],
    delta_q: Mapping[str, object],
    delta_rate: Mapping[str, object],
    audit: Mapping[str, object],
) -> dict[str, object]:
    """Map existing registered outputs into the exact 18-bound retirement input.

    This is an aggregation/schema helper, not scientific interpretation.  The
    caller supplies the already-decided prerequisite-gate boolean.  Primary
    effects come from ``primary.per_seed_per_regime``; robustness is oriented as
    ``Delta_R=-Delta_F``.  The three rollout/alignment effects come from each
    mechanism output's ``per_seed_per_regime``.  ``Delta_regret`` must come from
    ``audit.Delta_regret.per_seed_per_regime``, which in turn must have been
    computed only over supported derangement recipients.  Missing support or a
    missing seed/regime returns an unavailable, non-retiring result.
    """

    effects: dict[str, dict[int, dict[str, float]]] = {
        metric: {seed: {} for seed in REGISTERED_SEEDS}
        for metric in (
            "Delta_J", "Delta_R", "Delta_align", "Delta_Q", "Delta_rate", "Delta_regret",
        )
    }
    failures: list[str] = []

    def seed_row(source: object, seed: int, *, label: str) -> Mapping[str, object] | None:
        if not isinstance(source, Mapping):
            failures.append(f"{label} lacks per_seed_per_regime mapping")
            return None
        row = source.get(str(seed), source.get(seed))
        if not isinstance(row, Mapping):
            failures.append(f"{label} lacks seed {seed}")
            return None
        return row

    primary_rows = primary.get("per_seed_per_regime")
    for seed in REGISTERED_SEEDS:
        row = seed_row(primary_rows, seed, label="primary")
        if row is None:
            continue
        for regime in TARGET_REGIMES:
            cell = row.get(regime)
            if not isinstance(cell, Mapping):
                failures.append(f"primary lacks seed {seed}, regime {regime}")
                continue
            try:
                delta_j = float(cell["Delta_J"])
                delta_f = float(cell["Delta_F"])
            except (KeyError, TypeError, ValueError):
                failures.append(f"primary has invalid seed {seed}, regime {regime} effects")
                continue
            if not math.isfinite(delta_j) or not math.isfinite(delta_f):
                failures.append(f"primary has nonfinite seed {seed}, regime {regime} effects")
                continue
            effects["Delta_J"][seed][regime] = delta_j
            effects["Delta_R"][seed][regime] = -delta_f

    mechanism_sources = {
        "Delta_align": delta_align.get("per_seed_per_regime"),
        "Delta_Q": delta_q.get("per_seed_per_regime"),
        "Delta_rate": delta_rate.get("per_seed_per_regime"),
    }
    regret_section = audit.get("Delta_regret")
    if not isinstance(regret_section, Mapping) or not bool(regret_section.get("available", False)):
        failures.append("Delta_regret is unavailable on supported derangement recipients")
        regret_source: object = None
    else:
        regret_source = regret_section.get("per_seed_per_regime")
    mechanism_sources["Delta_regret"] = regret_source

    for metric, source in mechanism_sources.items():
        for seed in REGISTERED_SEEDS:
            row = seed_row(source, seed, label=metric)
            if row is None:
                continue
            for regime in TARGET_REGIMES:
                try:
                    value = float(row[regime])
                except (KeyError, TypeError, ValueError):
                    failures.append(f"{metric} lacks seed {seed}, regime {regime}")
                    continue
                if not math.isfinite(value):
                    failures.append(f"{metric} has nonfinite seed {seed}, regime {regime}")
                    continue
                effects[metric][seed][regime] = value

    # Deduplicate repeated structural failures without obscuring their first
    # occurrence order in the result packet.
    failures = list(dict.fromkeys(failures))
    inputs_available = not failures and all(
        all(regime in effects[metric][seed] for regime in TARGET_REGIMES)
        for metric in effects for seed in REGISTERED_SEEDS
    )
    decision = exact_b1_retirement_decision(
        validity_and_all_mechanism_gates_pass=(
            validity_and_all_mechanism_gates_pass and inputs_available
        ),
        per_metric_seed_regime_effects=effects,
    )
    if failures:
        decision["failure_or_unresolved_reasons"] = [
            *failures, *decision["failure_or_unresolved_reasons"],
        ]
    return {
        "inputs_available": inputs_available,
        "input_failure_reasons": failures,
        "per_metric_seed_regime_effects": effects,
        "decision": decision,
        "registered_bound_count": 18,
    }


def _jsonable(value: object) -> object:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def build_result_packet(
    *,
    question_relevant_output_exists: bool,
    primary: Mapping[str, object],
    mechanisms: Mapping[str, object],
    validity: Mapping[str, object],
    activity_counts: Mapping[str, object],
    calibration: Mapping[str, object],
    donor_diagnostics: Mapping[str, object],
    causal_audit: Mapping[str, object],
    rate_diagnostics: Mapping[str, object],
    descriptive_metrics: Mapping[str, object],
    resources: Mapping[str, object],
    anomalies: Sequence[str],
) -> dict[str, object]:
    """Assemble the required noninterpretive, JSON-safe CM/EM result packet."""

    sections = {
        "primary": primary, "mechanisms": mechanisms, "validity": validity,
        "activity_counts": activity_counts, "calibration": calibration,
        "donor_diagnostics": donor_diagnostics, "causal_audit": causal_audit,
        "rate_diagnostics": rate_diagnostics, "descriptive_metrics": descriptive_metrics,
        "resources": resources,
    }
    missing = [name for name, value in sections.items() if not value]
    packet = {
        "direction": "commitment_residual_triggered_options",
        "candidate": "CRTO-B1", "revision": REVISION,
        "question_relevant_output_exists": bool(question_relevant_output_exists),
        **{name: _jsonable(value) for name, value in sections.items()},
        "anomalies": list(anomalies),
        "required_sections_complete": not missing,
        "missing_required_sections": missing,
        "scientific_interpretation_in_packet": False,
        "claim_ceiling": (
            "finite four-agent service-relay DGP, registered K regimes, budget, "
            "independent-Gaussian seed-effect model, and only the registered local interventions"
        ),
    }
    if missing:
        packet["question_relevant_output_exists"] = False
    return packet
