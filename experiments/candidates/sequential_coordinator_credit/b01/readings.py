"""Exact gradient readings at policy snapshots (item 5a) and the free Shapley oracle readings.

At a snapshot policy pi and for each arm, the expected update ``g_est = E[sum_i grad log
pi_i(z_i | x, z_<i) A_i]`` with x uniform over the 16 contexts, z ~ pi(. | x) enumerated
exactly, and the demand noise averaged over the context's fixed evaluation set (one draw when
sigma = 0).  ``grad J`` is exact on the same set.  E1 uses V(x) = E_pi[R | x] (exact).  E3 is
averaged over ``E3_READING_DRAWS`` independent batches (64 samples per context; each sample's
demand is a uniformly drawn member of the context's evaluation set) with jackknife SEs.

Three calibrations of the advantages: ``raw``; ``native`` (one mean and one std over all
per-agent advantages and the team advantage R - V(x)); ``per_agent`` (each agent's stream
standardised on its own).  The scale-free reading is the ``raw`` cosine (invariant to the joint
scale).  Exact arms use population moments (std + 1e-8); E3 uses each batch's moments
(``std(ddof=1) + 1e-8``, the learner's form).

``variance`` = E_{x,z,noise} ||g - g_est||^2 in the full logit space (x uniform over contexts);
``variance_within_context`` = mean_x E ||g_x - gbar_x||^2 (the stratified-batch variance per
sample; extra, not in the L0).
"""

from __future__ import annotations

import numpy as np

from . import estimators as est
from .chain_bandit import (
    JOINT_PREFIX,
    JOINTS,
    K,
    N_JOINTS,
    joint_probs,
    masked_softmax,
    prefix_mask,
    prefix_rows,
    reward,
    reward_table,
    exact_grad_J,
    expected_score_update,
    sample_joints,
)
from .learner import SAMPLES_PER_CONTEXT, joint_normalise, scatter_rows

READING_SNAPSHOTS = (0, 40, 200)
E3_READING_DRAWS = 32
CALIBRATIONS = ("raw", "native", "per_agent")
METRICS = ("cosine", "projection", "variance", "variance_within_context")
READING_STREAM_TAG = 7


def reading_stream(config_idx: int, entropy_index: int, seed: int,
                   snapshot: int) -> np.random.Generator:
    """E3 reading batches at one snapshot (5-word key, distinct from the 2/4-word keys)."""
    return np.random.default_rng([READING_STREAM_TAG, int(config_idx), int(entropy_index),
                                  int(seed), int(snapshot)])


def _score_sq(P: np.ndarray) -> np.ndarray:
    """(n, 256, K) ||onehot(z_i) - pi(. | x, z_<i)||^2."""
    probs = P[:, JOINT_PREFIX, :]                                                # (n, 256, K, 4)
    onehot = np.zeros(probs.shape)
    np.put_along_axis(onehot, JOINTS[None, :, :, None], 1.0, axis=-1)
    return ((onehot - probs) ** 2).sum(axis=-1)


def calibrate_exact(A: np.ndarray, team: np.ndarray, w: np.ndarray, which: str) -> np.ndarray:
    """A (n, S, 256, K), team (n, S, 256), w (n, S, 256) summing to 1."""
    if which == "raw":
        return A
    if which == "native":
        mean = (w * (A.sum(-1) + team)).sum() / (K + 1)
        var = (w * (((A - mean) ** 2).sum(-1) + (team - mean) ** 2)).sum() / (K + 1)
        return (A - mean) / (np.sqrt(var) + 1e-8)
    if which == "per_agent":
        mean = (w[..., None] * A).sum(axis=(0, 1, 2))
        var = (w[..., None] * (A - mean) ** 2).sum(axis=(0, 1, 2))
        return (A - mean) / (np.sqrt(var) + 1e-8)
    raise ValueError(which)


def _dot(a: np.ndarray, b: np.ndarray):
    """Elementwise product and sum (no BLAS: bitwise independent of the thread count)."""
    return (a * b).sum(axis=-1)


def _metrics(g_est: np.ndarray, grad_j: np.ndarray, mean_sq: float) -> dict:
    n = g_est.shape[0]
    gj = grad_j.ravel()
    g = g_est.ravel()
    gg = float(_dot(g, g))
    jj = float(_dot(gj, gj))
    norm = np.sqrt(gg) * np.sqrt(jj)
    return {"cosine": float(_dot(g, gj) / norm) if norm > 0 else float("nan"),
            "projection": float(_dot(g, gj) / jj) if jj > 0 else float("nan"),
            "variance": float(mean_sq - gg),
            "variance_within_context": float(mean_sq - n * gg)}


def exact_reading(A: np.ndarray, team: np.ndarray, P: np.ndarray, pj: np.ndarray,
                  score_sq: np.ndarray, grad_j: np.ndarray) -> dict:
    n, S = A.shape[:2]
    w = np.broadcast_to(pj[:, None, :] / (n * S), A.shape[:3])
    out = {}
    for which in CALIBRATIONS:
        Ac = calibrate_exact(A, team, w, which)
        g_est = expected_score_update(P, (w[..., None] * Ac).sum(axis=1))
        mean_sq = float((w[..., None] * Ac ** 2 * score_sq[:, None]).sum())
        out[which] = _metrics(g_est, grad_j, mean_sq)
    return out


def _batch_calibrate(A: np.ndarray, team: np.ndarray, which: str) -> np.ndarray:
    if which == "raw":
        return A
    if which == "native":
        return joint_normalise(A, team)[0]
    flat = A.reshape(-1, K)
    return (A - flat.mean(axis=0)) / (flat.std(axis=0, ddof=1) + 1e-8)


def e3_reading(P: np.ndarray, contexts, V: np.ndarray, grad_j: np.ndarray,
               rng: np.random.Generator, draws: int = E3_READING_DRAWS) -> dict:
    n = contexts.n
    demands = contexts.eval_demands()                                            # (n, S, C)
    x = np.arange(n)[:, None]
    g_draw = {which: [] for which in CALIBRATIONS}
    sq = {which: 0.0 for which in CALIBRATIONS}
    count = 0
    for _ in range(draws):
        z = sample_joints(P, SAMPLES_PER_CONTEXT, rng)
        pick = rng.integers(0, demands.shape[1], size=(n, SAMPLES_PER_CONTEXT))
        d = demands[x, pick]
        R = reward(d, contexts.q[:, None], z, contexts.mask, contexts.b0)
        A = est.seqau_ridge(P, z, R, rng)
        team = R - V[:, None]
        rows = prefix_rows(z)
        probs = P[x[..., None], rows]
        onehot = np.zeros(probs.shape)
        np.put_along_axis(onehot, z[..., None], 1.0, axis=-1)
        score = onehot - probs                                                   # (n, M, K, 4)
        score_sq = (score ** 2).sum(-1)
        for which in CALIBRATIONS:
            Ac = _batch_calibrate(A, team, which)
            g = scatter_rows(np.broadcast_to(x[..., None], rows.shape), rows,
                             Ac[..., None] * score, n) / (n * SAMPLES_PER_CONTEXT)
            g_draw[which].append(g)
            sq[which] += float((Ac ** 2 * score_sq).sum())
        count += n * SAMPLES_PER_CONTEXT
    out = {}
    for which in CALIBRATIONS:
        stack = np.stack(g_draw[which])                                          # (D, n, 85, 4)
        g_est = stack.mean(axis=0)
        metrics = _metrics(g_est, grad_j, sq[which] / count)
        D = stack.shape[0]
        if D > 1:
            loo = (D * g_est[None] - stack) / (D - 1)
            gj = grad_j.ravel()
            flat = loo.reshape(D, -1)
            cos = _dot(flat, gj) / (np.sqrt(_dot(flat, flat)) * np.sqrt(_dot(gj, gj)))
            proj = _dot(flat, gj) / _dot(gj, gj)
            for key, values in (("cosine", cos), ("projection", proj)):
                metrics[f"{key}_se"] = float(np.sqrt((D - 1) / D
                                                     * ((values - values.mean()) ** 2).sum()))
        metrics["draws"] = D
        out[which] = metrics
    return out


def shapley_reading(P: np.ndarray, pj: np.ndarray, rtab: np.ndarray) -> dict:
    """pi-weighted means over contexts, noise and joints of phi_i, D_i (E4) and suffix Shapley."""
    n, S = rtab.shape[:2]
    jidx = est.all_joints(n, S)
    w = np.broadcast_to(pj[:, None, :] / (n * S), (n, S, N_JOINTS))
    phi = est.shapley_values(rtab, jidx)
    D = est.removal_difference(rtab, jidx)
    suffix = est.suffix_shapley(P, rtab, jidx)
    R = est.gather(rtab, jidx)

    def mean(values):
        extra = values.ndim - 3
        return (w.reshape(w.shape + (1,) * extra) * values).sum(axis=(0, 1, 2))

    return {"shapley_mean": mean(phi).tolist(), "shapley_abs_mean": mean(np.abs(phi)).tolist(),
            "removal_mean": mean(D).tolist(), "removal_abs_mean": mean(np.abs(D)).tolist(),
            "suffix_shapley_mean": mean(suffix).tolist(),
            "suffix_shapley_abs_mean": mean(np.abs(suffix)).tolist(),
            "shapley_efficiency_max_abs_error": float(np.abs(phi.sum(-1) - R).max())}


def snapshot_readings(theta: np.ndarray, contexts, rng: np.random.Generator,
                      e3_draws: int = E3_READING_DRAWS) -> dict:
    """All arms' gradient readings plus the Shapley readings at one policy snapshot."""
    n = contexts.n
    P = masked_softmax(theta, prefix_mask(contexts.mask))
    pj = joint_probs(P)
    rtab = reward_table(contexts.eval_demands(), contexts.q, contexts.mask, contexts.b0)
    r_bar = rtab.mean(axis=1)
    grad_j = exact_grad_J(P, r_bar)
    V = (pj * r_bar).sum(axis=-1)
    jidx = est.all_joints(n, rtab.shape[1])
    team = rtab - V[:, None, None]
    score_sq = _score_sq(P)
    arms = {}
    for arm in est.ARMS:
        if arm == "E3":
            arms[arm] = e3_reading(P, contexts, V, grad_j, rng, e3_draws)
        else:
            A = est.exact_advantages(arm, P, rtab, jidx, V)
            arms[arm] = exact_reading(A, team, P, pj, score_sq, grad_j)
    flat_j = grad_j.ravel()
    return {"J": float(V.mean()), "grad_J_norm": float(np.sqrt(_dot(flat_j, flat_j))),
            "arms": arms,
            "shapley": shapley_reading(P, pj, rtab)}

