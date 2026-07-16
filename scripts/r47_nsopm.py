"""Registered mathematics for R47-NSOPM-G0.

This module is deliberately policy- and environment-agnostic.  It turns the
registered seven-dimensional process view into frozen natural-support spectral
modes and exposes the exact statistics used by the standalone R47 gate.  It
does not read task reward, skill labels, or task-specific simulator fields.
"""

from __future__ import annotations

import itertools
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np


EXPERIMENT_ID = "EXP-20260716-r47-nsopm-g0"
SCHEMA_VERSION = 1
SOURCE_CHECKPOINT = Path(
    "logs/r30_alice_bob_paired_64k_20260714_163908/"
    "runs/adaptive_keep_set/seed30031/standalone_process_core_final.pt"
)

SOURCE_TOTAL_STEPS = 64_000
SOURCE_UPDATE = 50
N_AGENTS = 2
N_SKILLS = 4
K0 = 10
EPISODE_STEPS = 80
WORLD_SIZE = 8.0
VIEW_DIM = 7
FEATURE_DIM = 35
LAGS = (1, 5)

NATURAL_SEED = 47_041
NATURAL_GROUPS = 64
NATURAL_WINDOWS_PER_GROUP = 8
NATURAL_WINDOWS = NATURAL_GROUPS * NATURAL_WINDOWS_PER_GROUP
FIT_GROUPS = tuple(range(0, 32))
HALF_A_GROUPS = tuple(range(0, 16))
HALF_B_GROUPS = tuple(range(16, 32))
HELDOUT_GROUPS = tuple(range(32, 64))
NUISANCE_TRAIN_GROUPS = tuple(range(32, 48))
NUISANCE_TEST_GROUPS = tuple(range(48, 64))

CAUSAL_CONTEXTS = 64
REPLICAS = 2
FORCED_HORIZON = 40
FORCED_BRANCHES = CAUSAL_CONTEXTS * N_SKILLS * REPLICAS
FORCED_STEPS = FORCED_BRANCHES * FORCED_HORIZON
BRANCH_SEED = 67_041

WHITEN_RIDGE = 1e-4
C_ABS_FLOOR = 1e-8
C_REL_FLOOR = 1e-6
G_ABS_FLOOR = 1e-10
G_REL_FLOOR = 1e-6
SCALE_FLOOR = 1e-6
SUPPORT_QUANTILE = 0.95
SUPPORT_POINTS_MIN = 9
SUPPORT_RATIO_MIN = 0.80

TEMPORAL_NULL_SEED = 57_041
TEMPORAL_NULL_REPLICATES = 256
BOOTSTRAP_SEED = 62_047
BOOTSTRAP_REPETITIONS = 10_000
NUISANCE_RIDGE = 1e-3


def seven_dimensional_process_view(position_frames: np.ndarray) -> np.ndarray:
    """Return registered transition views with shape ``[agent, time, 7]``.

    ``position_frames`` contains normalized-world positions only in physical
    coordinates and has shape ``[time + 1, N, 2]``.  No task state is accepted.
    The population covariance is used for the teammate-relative set.  With the
    registered N=2 source that set is a singleton, so its three vech fields are
    exactly zero.
    """

    frames = np.asarray(position_frames, dtype=np.float64)
    if frames.ndim != 3 or frames.shape[1:] != (N_AGENTS, 2):
        raise ValueError(f"position frame shape must be [T+1,{N_AGENTS},2]")
    if frames.shape[0] < 2 or not np.isfinite(frames).all():
        raise ValueError("position frames must be finite and contain transitions")
    normalized = frames / WORLD_SIZE
    state_views = np.empty((N_AGENTS, frames.shape[0], VIEW_DIM), dtype=np.float64)
    for focal in range(N_AGENTS):
        teammate = 1 - focal
        relative = (normalized[:, teammate] - normalized[:, focal])[:, None, :]
        mean_relative = relative.mean(axis=1)
        centered = relative - mean_relative[:, None, :]
        covariance = np.einsum("tni,tnj->tij", centered, centered) / float(
            relative.shape[1]
        )
        state_views[focal, :, 0:2] = normalized[:, focal]
        state_views[focal, :, 2:4] = mean_relative
        state_views[focal, :, 4] = covariance[:, 0, 0]
        state_views[focal, :, 5] = covariance[:, 0, 1]
        state_views[focal, :, 6] = covariance[:, 1, 1]
    return np.diff(state_views, axis=1).astype(np.float32)


def fit_normalization(views: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    rows = np.asarray(views, dtype=np.float64).reshape(-1, VIEW_DIM)
    if rows.size == 0 or not np.isfinite(rows).all():
        raise ValueError("normalization requires finite process-view rows")
    mean = rows.mean(axis=0)
    scale = rows.std(axis=0, ddof=0)
    scale = np.where(scale < SCALE_FLOOR, 1.0, scale)
    return mean, scale


def initial_centered_views(
    views: np.ndarray, mean: np.ndarray, scale: np.ndarray
) -> np.ndarray:
    raw = np.asarray(views, dtype=np.float64)
    if raw.ndim != 3 or raw.shape[1:] != (K0, VIEW_DIM):
        raise ValueError(f"natural view shape must be [window,{K0},{VIEW_DIM}]")
    standardized = (raw - np.asarray(mean)) / np.asarray(scale)
    return standardized - standardized[:, 0:1, :]


def quadratic_features(centered_views: np.ndarray) -> np.ndarray:
    """Map 7-D centered views to the fixed 35-D upper-triangular feature map."""

    u = np.asarray(centered_views, dtype=np.float64)
    if u.shape[-1] != VIEW_DIM:
        raise ValueError("quadratic feature input must end in seven fields")
    products = [u[..., a] * u[..., b] for a in range(VIEW_DIM) for b in range(a, VIEW_DIM)]
    result = np.concatenate([u, np.stack(products, axis=-1)], axis=-1)
    if result.shape[-1] != FEATURE_DIM:
        raise RuntimeError("registered feature dimension changed")
    return result


def _descending_eigh(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    values, vectors = np.linalg.eigh(np.asarray(matrix, dtype=np.float64))
    order = np.argsort(-values, kind="stable")
    return values[order], vectors[:, order]


def _orient_vector(vector: np.ndarray) -> np.ndarray:
    oriented = np.asarray(vector, dtype=np.float64).copy()
    max_abs = float(np.max(np.abs(oriented)))
    candidates = np.flatnonzero(np.isclose(np.abs(oriented), max_abs, rtol=0.0, atol=1e-14))
    index = int(candidates[0])
    if oriented[index] < 0.0:
        oriented *= -1.0
    return oriented


def fit_spectral_from_centered(centered_views: np.ndarray) -> dict[str, Any]:
    """Fit the exact pooled-lag whitened Gram estimator to centered windows."""

    u = np.asarray(centered_views, dtype=np.float64)
    if u.ndim != 3 or u.shape[1:] != (K0, VIEW_DIM):
        raise ValueError("spectral fit requires [window,10,7] centered views")
    features = quadratic_features(u)
    source_by_lag = {lag: features[:, :-lag, :].reshape(-1, FEATURE_DIM) for lag in LAGS}
    target_by_lag = {lag: features[:, lag:, :].reshape(-1, FEATURE_DIM) for lag in LAGS}
    pooled_source = np.concatenate([source_by_lag[lag] for lag in LAGS], axis=0)
    pooled_target = np.concatenate([target_by_lag[lag] for lag in LAGS], axis=0)
    source_mean = pooled_source.mean(axis=0)
    target_mean = pooled_target.mean(axis=0)
    x = pooled_source - source_mean
    y = pooled_target - target_mean
    c00 = (x.T @ x) / float(len(x))
    c11 = (y.T @ y) / float(len(y))

    eig0, vec0 = _descending_eigh(c00)
    eig1, vec1 = _descending_eigh(c11)
    floor0 = max(C_ABS_FLOOR, C_REL_FLOOR * max(float(eig0[0]), 0.0))
    floor1 = max(C_ABS_FLOOR, C_REL_FLOOR * max(float(eig1[0]), 0.0))
    keep0 = eig0 > floor0
    keep1 = eig1 > floor1
    retained0 = eig0[keep0]
    retained1 = eig1[keep1]
    basis0 = vec0[:, keep0]
    basis1 = vec1[:, keep1]
    w0 = (
        (1.0 / np.sqrt(retained0 + WHITEN_RIDGE))[:, None] * basis0.T
        if retained0.size
        else np.zeros((0, FEATURE_DIM), dtype=np.float64)
    )
    w1 = (
        basis1 * (1.0 / np.sqrt(retained1 + WHITEN_RIDGE))[None, :]
        if retained1.size
        else np.zeros((FEATURE_DIM, 0), dtype=np.float64)
    )

    operators: dict[int, np.ndarray] = {}
    for lag in LAGS:
        xl = source_by_lag[lag] - source_mean
        yl = target_by_lag[lag] - target_mean
        c01 = (xl.T @ yl) / float(len(xl))
        operators[lag] = w0 @ c01 @ w1
    if w0.shape[0]:
        gram = sum(operators[lag] @ operators[lag].T for lag in LAGS) / float(len(LAGS))
        gram_values, gram_vectors = _descending_eigh(gram)
        gram_vectors = np.stack(
            [_orient_vector(gram_vectors[:, q]) for q in range(gram_vectors.shape[1])],
            axis=1,
        )
        gram_floor = max(G_ABS_FLOOR, G_REL_FLOOR * max(float(gram_values[0]), 0.0))
    else:
        gram = np.zeros((0, 0), dtype=np.float64)
        gram_values = np.zeros(0, dtype=np.float64)
        gram_vectors = np.zeros((0, 0), dtype=np.float64)
        gram_floor = G_ABS_FLOOR
    finite_arrays: Iterable[np.ndarray] = (
        source_mean,
        target_mean,
        c00,
        c11,
        w0,
        w1,
        gram,
        gram_values,
        gram_vectors,
        *operators.values(),
    )
    if not all(np.isfinite(array).all() for array in finite_arrays):
        raise FloatingPointError("non-finite R47 spectral estimator")
    return {
        "source_mean": source_mean,
        "target_mean": target_mean,
        "c00": c00,
        "c11": c11,
        "c00_eigenvalues": eig0,
        "c11_eigenvalues": eig1,
        "c00_floor": float(floor0),
        "c11_floor": float(floor1),
        "w0": w0,
        "w1": w1,
        "operators": operators,
        "gram": gram,
        "eigenvalues": gram_values,
        "modes": gram_vectors,
        "gram_floor": float(gram_floor),
        "retained_c00_rank": int(retained0.size),
        "retained_c11_rank": int(retained1.size),
        "nontrivial_mode_count": int(np.count_nonzero(gram_values > gram_floor)),
    }


def fit_spectral(views: np.ndarray) -> dict[str, Any]:
    mean, scale = fit_normalization(views)
    centered = initial_centered_views(views, mean, scale)
    model = fit_spectral_from_centered(centered)
    model["view_mean"] = mean
    model["view_scale"] = scale
    return model


def centered_for_model(model: dict[str, Any], views: np.ndarray) -> np.ndarray:
    return initial_centered_views(views, model["view_mean"], model["view_scale"])


def mode_activations(
    model: dict[str, Any], views: np.ndarray, *, mode_count: int = N_SKILLS
) -> np.ndarray:
    if int(model["nontrivial_mode_count"]) < mode_count:
        raise ValueError("spectral model has fewer than four nontrivial modes")
    features = quadratic_features(centered_for_model(model, views))
    whitened = (features - model["source_mean"]) @ model["w0"].T
    return whitened @ model["modes"][:, :mode_count]


def support_distances(model: dict[str, Any], views: np.ndarray) -> np.ndarray:
    features = quadratic_features(centered_for_model(model, views))
    whitened = (features - model["source_mean"]) @ model["w0"].T
    return np.sum(np.square(whitened), axis=-1)


def lag_correlation(sequence: np.ndarray, lag: int) -> float:
    values = np.asarray(sequence, dtype=np.float64).reshape(-1)
    left = values[:-lag]
    right = values[lag:]
    denominator = math.sqrt(float(np.dot(left, left) * np.dot(right, right))) + 1e-8
    return float(np.dot(left, right) / denominator)


def window_mode_statistics(activations: np.ndarray) -> dict[str, np.ndarray]:
    """Return per-window/mode E, X, C and g for frozen activations."""

    modes = np.asarray(activations, dtype=np.float64)
    if modes.ndim != 3 or modes.shape[1:] != (K0, N_SKILLS):
        raise ValueError("mode activations must be [window,10,4]")
    energy = np.mean(np.square(modes), axis=1)
    share = energy / (energy.sum(axis=1, keepdims=True) + 1e-8)
    correlations = np.empty((len(modes), N_SKILLS, len(LAGS)), dtype=np.float64)
    for window in range(len(modes)):
        for mode in range(N_SKILLS):
            for lag_index, lag in enumerate(LAGS):
                correlations[window, mode, lag_index] = lag_correlation(
                    modes[window, :, mode], lag
                )
    coherence = correlations.mean(axis=-1)
    score = coherence * share
    return {
        "energy": energy,
        "share": share,
        "lag_correlations": correlations,
        "coherence": coherence,
        "g": score,
    }


def pearson_correlation(left: np.ndarray, right: np.ndarray) -> float:
    x = np.asarray(left, dtype=np.float64).reshape(-1)
    y = np.asarray(right, dtype=np.float64).reshape(-1)
    if x.shape != y.shape or x.size == 0:
        raise ValueError("correlation inputs must be nonempty and shape matched")
    x = x - x.mean()
    y = y - y.mean()
    denominator = math.sqrt(float(np.dot(x, x) * np.dot(y, y)))
    return float(np.dot(x, y) / denominator) if denominator > 0.0 else 0.0


def align_half_to_primary(
    primary: np.ndarray, half: np.ndarray
) -> tuple[np.ndarray, tuple[int, ...], np.ndarray]:
    """Exhaustively align four half-basis activations to primary mode rank."""

    primary = np.asarray(primary, dtype=np.float64).reshape(-1, N_SKILLS)
    half = np.asarray(half, dtype=np.float64).reshape(-1, N_SKILLS)
    correlations = np.asarray(
        [
            [pearson_correlation(primary[:, q], half[:, h]) for h in range(N_SKILLS)]
            for q in range(N_SKILLS)
        ],
        dtype=np.float64,
    )
    best_permutation: tuple[int, ...] | None = None
    best_score = -math.inf
    for permutation in itertools.permutations(range(N_SKILLS)):
        score = float(sum(abs(correlations[q, permutation[q]]) for q in range(N_SKILLS)))
        if score > best_score + 1e-14 or (
            abs(score - best_score) <= 1e-14
            and (best_permutation is None or permutation < best_permutation)
        ):
            best_score = score
            best_permutation = tuple(permutation)
    assert best_permutation is not None
    aligned = np.empty_like(half)
    matched = np.empty(N_SKILLS, dtype=np.float64)
    for q, source in enumerate(best_permutation):
        sign = 1.0 if correlations[q, source] >= 0.0 else -1.0
        aligned[:, q] = sign * half[:, source]
        matched[q] = abs(correlations[q, source])
    return aligned, best_permutation, matched


def nonidentity_permutation(rng: np.random.Generator, length: int) -> np.ndarray:
    identity = np.arange(length)
    while True:
        permutation = rng.permutation(length)
        if not np.array_equal(permutation, identity):
            return permutation


def temporal_null_eigenvalues(
    primary_centered: np.ndarray,
    *,
    repetitions: int = TEMPORAL_NULL_REPLICATES,
    seed: int = TEMPORAL_NULL_SEED,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    centered = np.asarray(primary_centered, dtype=np.float64)
    result = np.zeros((repetitions, N_SKILLS), dtype=np.float64)
    for repetition in range(repetitions):
        permuted = np.empty_like(centered)
        for window in range(len(centered)):
            permutation = nonidentity_permutation(rng, K0)
            permuted[window] = centered[window, permutation]
        model = fit_spectral_from_centered(permuted)
        count = min(N_SKILLS, len(model["eigenvalues"]))
        result[repetition, :count] = model["eigenvalues"][:count]
    return result


def coherence_null_mean(
    activations: np.ndarray,
    *,
    repetitions: int = TEMPORAL_NULL_REPLICATES,
    seed: int = TEMPORAL_NULL_SEED,
) -> np.ndarray:
    """Return [window, lag] mean frozen-basis temporal-null coherence."""

    modes = np.asarray(activations, dtype=np.float64)
    rng = np.random.default_rng(seed)
    accumulated = np.zeros((len(modes), len(LAGS)), dtype=np.float64)
    for _ in range(repetitions):
        for window in range(len(modes)):
            permutation = nonidentity_permutation(rng, K0)
            permuted = modes[window, permutation, :]
            for lag_index, lag in enumerate(LAGS):
                accumulated[window, lag_index] += float(
                    np.mean(
                        [lag_correlation(permuted[:, q], lag) for q in range(N_SKILLS)]
                    )
                )
    return accumulated / float(repetitions)


def group_mean(values: np.ndarray, group_ids: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    groups = np.unique(np.asarray(group_ids, dtype=np.int64))
    means = np.asarray(
        [np.asarray(values, dtype=np.float64)[np.asarray(group_ids) == group].mean(axis=0) for group in groups]
    )
    return groups, means


def bootstrap_mean_interval(
    cluster_values: np.ndarray,
    *,
    repetitions: int = BOOTSTRAP_REPETITIONS,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, float]:
    rows = np.asarray(cluster_values, dtype=np.float64).reshape(len(cluster_values), -1)
    if not len(rows):
        return {"lower_95": math.nan, "mean": math.nan, "upper_95": math.nan}
    if rows.shape[1] != 1:
        raise ValueError("bootstrap_mean_interval expects one scalar per cluster")
    rng = np.random.default_rng(seed)
    samples = rng.integers(0, len(rows), size=(repetitions, len(rows)))
    replicates = rows[samples, 0].mean(axis=1)
    return {
        "lower_95": float(np.quantile(replicates, 0.025)),
        "mean": float(rows[:, 0].mean()),
        "upper_95": float(np.quantile(replicates, 0.975)),
    }


def bootstrap_ratio_interval(
    numerators: np.ndarray,
    denominators: np.ndarray,
    *,
    repetitions: int = BOOTSTRAP_REPETITIONS,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, float]:
    numerator = np.asarray(numerators, dtype=np.float64).reshape(-1)
    denominator = np.asarray(denominators, dtype=np.float64).reshape(-1)
    if numerator.shape != denominator.shape or not len(numerator):
        return {"lower_95": math.nan, "mean": math.nan, "upper_95": math.nan}
    rng = np.random.default_rng(seed)
    samples = rng.integers(0, len(numerator), size=(repetitions, len(numerator)))
    boot_num = numerator[samples].mean(axis=1)
    boot_den = denominator[samples].mean(axis=1)
    replicates = boot_num / (boot_den + 1e-8)
    return {
        "lower_95": float(np.quantile(replicates, 0.025)),
        "mean": float(numerator.mean() / (denominator.mean() + 1e-8)),
        "upper_95": float(np.quantile(replicates, 0.975)),
    }


def nuisance_ridge_audit(
    features: np.ndarray,
    targets: np.ndarray,
    group_ids: np.ndarray,
) -> dict[str, Any]:
    x = np.asarray(features, dtype=np.float64)
    y = np.asarray(targets, dtype=np.float64)
    groups = np.asarray(group_ids, dtype=np.int64)
    train_mask = np.isin(groups, NUISANCE_TRAIN_GROUPS)
    test_mask = np.isin(groups, NUISANCE_TEST_GROUPS)
    if x.shape[1] != 10 or y.shape[1] != N_SKILLS:
        raise ValueError("nuisance audit requires 10 features and four targets")
    x_train = x[train_mask]
    y_train = y[train_mask]
    x_test = x[test_mask]
    y_test = y[test_mask]
    mean = x_train.mean(axis=0)
    scale = x_train.std(axis=0, ddof=0)
    scale = np.where(scale < SCALE_FLOOR, 1.0, scale)
    x_train = (x_train - mean) / scale
    x_test = (x_test - mean) / scale
    x_mean = x_train.mean(axis=0)
    y_mean = y_train.mean(axis=0)
    xc = x_train - x_mean
    yc = y_train - y_mean
    weights = np.linalg.solve(
        xc.T @ xc + NUISANCE_RIDGE * np.eye(xc.shape[1], dtype=np.float64),
        xc.T @ yc,
    )
    intercept = y_mean - x_mean @ weights
    prediction = x_test @ weights + intercept
    residual = np.square(y_test - prediction)
    per_mode: list[float] = []
    for q in range(N_SKILLS):
        sse = float(residual[:, q].sum())
        sst = float(np.square(y_test[:, q] - y_test[:, q].mean()).sum())
        per_mode.append(0.0 if sst == 0.0 else 1.0 - sse / sst)
    pooled_sse = float(residual.sum())
    pooled_sst = float(np.square(y_test - y_test.mean(axis=0, keepdims=True)).sum())
    pooled = 0.0 if pooled_sst == 0.0 else 1.0 - pooled_sse / pooled_sst
    return {
        "per_mode_r2": per_mode,
        "pooled_r2": float(pooled),
        "maximum_r2": float(max([pooled, *per_mode])),
        "train_windows": int(train_mask.sum()),
        "test_windows": int(test_mask.sum()),
    }


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value
