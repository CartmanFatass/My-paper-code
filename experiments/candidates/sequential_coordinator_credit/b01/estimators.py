"""Per-agent advantage estimators and exact oracle readings on ``chain_bandit`` (K = 4).

Conventions.  ``rtab`` (n, S, 256) holds R of every joint under the demands of one draw
(training: one row per sample with that sample's noisy demands; readings: one row per fixed
evaluation noise draw).  ``jidx`` (n, S, J) are joint indices evaluated against the same row
(training: J = 1, the executed joint; readings: J = 256, every joint).  Every function returns
per-agent arrays of shape (n, S, J, K).  Removal is always "label := IDLE".

Arms: ``E1`` shared return minus the context baseline; ``E3`` ridge additive fit with
fictitious continuations (the DM's reading of COSAC's SeqAU); ``E4`` exact removal difference
with the others' realised labels fixed; oracle ``E3*`` exact SeqAU Q(x, z_<=i) - Q(x, z_<i);
oracle ``E4*`` removal with the suffix resampled given the IDLE prefix.
"""

from __future__ import annotations

from itertools import combinations
from math import factorial

import numpy as np

from .chain_bandit import (
    IDLE,
    JOINT_PREFIX,
    JOINTS,
    K,
    N_JOINTS,
    N_LABELS,
    PREFIX_OFFSET,
    prefix_values,
    sample_labels,
    suffix_products,
    with_idle,
)

ARMS = ("E1", "E3", "E4", "E3*", "E4*")
RIDGE_LAMBDA = 0.01
N_CONTINUATIONS = 8


def gather(table: np.ndarray, jidx: np.ndarray) -> np.ndarray:
    """table (n, S, 256), jidx broadcastable to (n, S, J) -> (n, S, J)."""
    shape = table.shape[:2] + (np.shape(jidx)[-1],)
    return np.take_along_axis(table, np.broadcast_to(jidx, shape), axis=-1)


def all_joints(n: int, S: int) -> np.ndarray:
    return np.broadcast_to(np.arange(N_JOINTS), (n, S, N_JOINTS))


# ----------------------------------------------------------------------------- arms (exact forms)

def shared_return(rtab: np.ndarray, jidx: np.ndarray, V: np.ndarray) -> np.ndarray:
    """E1: A_i = R - V(x) for every agent."""
    R = gather(rtab, jidx)
    return np.repeat((R - np.asarray(V)[:, None, None])[..., None], K, axis=-1)


def removal_difference(rtab: np.ndarray, jidx: np.ndarray) -> np.ndarray:
    """E4: D_i = R(x, z) - R(x, z with z_i := IDLE), the others' realised labels fixed."""
    R = gather(rtab, jidx)
    return np.stack([R - gather(rtab, with_idle(jidx, i)) for i in range(K)], axis=-1)


def _levels(P: np.ndarray, rtab: np.ndarray) -> list[np.ndarray]:
    return prefix_values(suffix_products(P), rtab)


def seqau_exact(P: np.ndarray, rtab: np.ndarray, jidx: np.ndarray,
                levels: list[np.ndarray] | None = None) -> np.ndarray:
    """E3*: A_i = Q(x, z_<=i) - Q(x, z_<i) under the current policy (exact)."""
    levels = _levels(P, rtab) if levels is None else levels
    jidx = np.asarray(jidx, dtype=np.int64)
    out = []
    for i in range(K):
        upper = gather(levels[i + 1], jidx // N_LABELS ** (K - i - 1))
        lower = gather(levels[i], jidx // N_LABELS ** (K - i))
        out.append(upper - lower)
    return np.stack(out, axis=-1)


def removal_resampled(P: np.ndarray, rtab: np.ndarray, jidx: np.ndarray,
                      levels: list[np.ndarray] | None = None) -> np.ndarray:
    """E4*: A_i = R(x, z) - E_{z_>i ~ pi(.|x, z_<i, IDLE)}[R(x, z_<i, IDLE, z_>i)] (exact)."""
    levels = _levels(P, rtab) if levels is None else levels
    jidx = np.asarray(jidx, dtype=np.int64)
    R = gather(rtab, jidx)
    out = []
    for i in range(K):
        code = (jidx // N_LABELS ** (K - i)) * N_LABELS + IDLE
        out.append(R - gather(levels[i + 1], code))
    return np.stack(out, axis=-1)


# ----------------------------------------------------------------------------- E3 (estimated)

def ridge_additive_fit(z: np.ndarray, R: np.ndarray, ridge: float = RIDGE_LAMBDA):
    """Per context: R ~ a + sum_i w[i, z_i] (one-hot per agent x label), ridge on w only.

    z (n, M, K), R (n, M) -> a (n,), w (n, K, N_LABELS).  The intercept is not penalised.
    """
    n, M, _ = z.shape
    X = np.zeros((n, M, 1 + K * N_LABELS))
    X[..., 0] = 1.0
    for i in range(K):
        np.put_along_axis(X, (1 + i * N_LABELS + z[..., i])[..., None], 1.0, axis=-1)
    penalty = np.diag(np.r_[0.0, np.full(K * N_LABELS, float(ridge))])
    lhs = np.einsum("nmf,nmg->nfg", X, X) + penalty
    rhs = np.einsum("nmf,nm->nf", X, R)
    beta = solve_spd(lhs, rhs)
    return beta[:, 0], beta[:, 1:].reshape(n, K, N_LABELS)


def solve_spd(lhs: np.ndarray, rhs: np.ndarray) -> np.ndarray:
    """Batched Gaussian elimination without pivoting for symmetric positive-definite systems.

    Elementwise NumPy only (no BLAS/LAPACK), so the result is bitwise independent of the
    BLAS thread count (``np.linalg.solve`` differs at 1e-14 between 1 and several threads).
    lhs (n, F, F), rhs (n, F) -> (n, F).
    """
    A = np.array(lhs, dtype=np.float64, copy=True)
    b = np.array(rhs, dtype=np.float64, copy=True)
    F = A.shape[-1]
    for k in range(F - 1):
        factor = A[:, k + 1:, k] / A[:, k, k][:, None]
        A[:, k + 1:, k:] -= factor[:, :, None] * A[:, None, k, k:]
        b[:, k + 1:] -= factor * b[:, k:k + 1]
    x = np.zeros_like(b)
    for k in range(F - 1, -1, -1):
        x[:, k] = (b[:, k] - (A[:, k, k + 1:] * x[:, k + 1:]).sum(axis=-1)) / A[:, k, k]
    return x


def seqau_ridge(P: np.ndarray, z: np.ndarray, R: np.ndarray, rng: np.random.Generator,
                ridge: float = RIDGE_LAMBDA, n_continuations: int = N_CONTINUATIONS,
                fit=None) -> np.ndarray:
    """E3: COSAC-style SeqAU estimate from the batch (z, R) of each context.

    A_hat(x, z_<=i) = a + sum_{j<=i} w[j, z_j] + (1/L) sum_l sum_{j>i} w[j, z_j^(l)],
    z_>i^(l) ~ pi_old(. | x, z_<=i); A_i = A_hat(x, z_<=i) - sum_z' pi_old(z'|x, z_<i)
    A_hat(x, z_<i, z').  Every alternative z' (all four labels, masked ones weighted 0) gets its
    own L continuations; the executed label's A_hat is its alternative's value.  Random draws:
    for i = 0..K-1, for j = i+1..K-1, one uniform array (n, M, 4, L).
    """
    n, M, _ = z.shape
    a, w = ridge_additive_fit(z, R, ridge) if fit is None else fit
    x = np.arange(n)[:, None]
    x4 = np.arange(n)[:, None, None, None]
    L = int(n_continuations)
    A = np.empty((n, M, K))
    prefix_sum = np.repeat(a[:, None], M, axis=1)
    code = np.zeros((n, M), dtype=np.int64)
    for i in range(K):
        pi_alt = P[x, PREFIX_OFFSET[i] + code]                                  # (n, M, 4)
        own = w[:, i, :][:, None, :]                                            # (n, 1, 4)
        cont = np.zeros((n, M, N_LABELS))
        if i < K - 1:
            ccode = (code[..., None, None] * N_LABELS
                     + np.arange(N_LABELS)[None, None, :, None]) * np.ones((1, 1, 1, L), np.int64)
            total = np.zeros((n, M, N_LABELS, L))
            for j in range(i + 1, K):
                probs = P[x4, PREFIX_OFFSET[j] + ccode]                         # (n, M, 4, L, 4)
                label = sample_labels(probs, rng.random((n, M, N_LABELS, L)))
                total += w[x4, j, label]
                ccode = ccode * N_LABELS + label
            cont = total.mean(axis=-1)
        a_hat = prefix_sum[..., None] + own + cont                              # (n, M, 4)
        executed = np.take_along_axis(a_hat, z[..., i:i + 1], axis=-1)[..., 0]
        A[..., i] = executed - (pi_alt * a_hat).sum(axis=-1)
        prefix_sum = prefix_sum + w[x, i, z[..., i]]
        code = code * N_LABELS + z[..., i]
    return A


# ----------------------------------------------------------------------------- Shapley readings

SUBSETS = tuple(tuple(agent for agent in range(K) if (mask >> agent) & 1)
                for mask in range(2 ** K))


def shapley_values(rtab: np.ndarray, jidx: np.ndarray) -> np.ndarray:
    """Exact Shapley value of each agent over coalitions of the realised labels (16 subsets).

    v(T) = R(x, z with every agent outside T := IDLE); v(empty) = R(all IDLE) = 0.
    """
    jidx = np.asarray(jidx, dtype=np.int64)
    values = {}
    for members in SUBSETS:
        outside = [agent for agent in range(K) if agent not in members]
        values[members] = gather(rtab, with_idle(jidx, outside) if outside else jidx)
    phi = np.zeros(np.broadcast_shapes(rtab.shape[:2] + (1,), jidx.shape) + (K,))
    for i in range(K):
        others = [agent for agent in range(K) if agent != i]
        for size in range(K):
            weight = factorial(size) * factorial(K - size - 1) / factorial(K)
            for T in combinations(others, size):
                with_i = tuple(sorted(T + (i,)))
                phi[..., i] += weight * (values[with_i] - values[tuple(T)])
    return phi


def _suffix_value(factors: np.ndarray, rtab: np.ndarray, jidx: np.ndarray, i: int,
                  resampled: tuple[int, ...]) -> np.ndarray:
    """E over the resampled downstream agents (given the prefix with z_i := IDLE and the other
    downstream agents' realised labels) of R; exact."""
    target = with_idle(jidx, i)
    if not resampled:
        return gather(rtab, target)
    f = np.prod(factors[:, :, list(resampled)], axis=-1)                         # (n, 256)
    prod = (f[:, None, :] * rtab).reshape(rtab.shape[:2] + (N_LABELS,) * K)
    summed = prod.sum(axis=tuple(2 + agent for agent in resampled), keepdims=True)
    full = np.broadcast_to(summed, prod.shape).reshape(rtab.shape)
    return gather(full, target)


def suffix_shapley(P: np.ndarray, rtab: np.ndarray, jidx: np.ndarray) -> np.ndarray:
    """Attribution of E4_i - E4*_i to downstream agents j > i (out[..., i, j]; 0 for j <= i).

    Players: downstream agents j > i.  v(S) = E[R] with the agents in S resampled from pi given
    the prefix with z_i := IDLE (sequentially, each conditioned on its actual prefix) and the
    other downstream agents at their realised labels.  v(all) - v(empty) = E4_i - E4*_i.
    """
    jidx = np.asarray(jidx, dtype=np.int64)
    factors = np.stack([P[:, JOINT_PREFIX[:, j], JOINTS[:, j]] for j in range(K)], axis=-1)
    shape = np.broadcast_shapes(rtab.shape[:2] + (1,), jidx.shape)
    out = np.zeros(shape + (K, K))
    for i in range(K - 1):
        downstream = tuple(range(i + 1, K))
        size_n = len(downstream)
        values = {}
        for size in range(size_n + 1):
            for S in combinations(downstream, size):
                values[S] = _suffix_value(factors, rtab, jidx, i, S)
        for j in downstream:
            others = [agent for agent in downstream if agent != j]
            for size in range(size_n):
                weight = factorial(size) * factorial(size_n - size - 1) / factorial(size_n)
                for T in combinations(others, size):
                    out[..., i, j] += weight * (values[tuple(sorted(T + (j,)))] - values[T])
    return out


def exact_advantages(arm: str, P: np.ndarray, rtab: np.ndarray, jidx: np.ndarray,
                     V: np.ndarray | None = None) -> np.ndarray:
    """Exact per-agent advantages of the exactly computable arms (E1 needs V)."""
    if arm == "E1":
        return shared_return(rtab, jidx, V)
    if arm == "E4":
        return removal_difference(rtab, jidx)
    if arm == "E3*":
        return seqau_exact(P, rtab, jidx)
    if arm == "E4*":
        return removal_resampled(P, rtab, jidx)
    raise ValueError(f"arm {arm!r} has no exact form")

