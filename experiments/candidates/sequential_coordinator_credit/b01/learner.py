"""Tabular prefix-conditioned softmax coordinator trained by HMASD's joint-PPO form (NumPy).

Mirrors ``hmasd/agent.py`` 6040-6073 / ``hmasd/networks.py`` 870-959: per-agent log-probabilities
teacher-forced on the executed prefix, one clipped surrogate per agent averaged over batch x
agents, all per-agent advantages normalised jointly with the constant-label team advantage
(one mean, one std: ``std(ddof=1) + 1e-8`` as ``torch.Tensor.std``), minus lambda_h times the
per-sample summed per-agent entropy.  The team label is constant (n_Z = 1), so its ratio is 1
and its surrogate contributes no gradient; it enters only the normalisation.

Differences from ``agent.py`` fixed by the L0: the joint normalisation is taken once over the
whole update batch (1024 x 4 + 1024 team terms), not per minibatch; no value loss (the context
baseline is an EMA); no gradient-norm clipping (not in the L0).
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from . import estimators as est
from .chain_bandit import (
    CONFIGURATIONS,
    IDLE,
    JOINTS,
    K,
    N_LABELS,
    N_PREFIXES,
    RELAY,
    exact_J,
    greedy_joints,
    joint_index,
    joint_probs,
    make_contexts,
    masked_softmax,
    mean_reward_table,
    noisy_demands,
    prefix_mask,
    prefix_rows,
    reward,
    reward_table,
    sample_joints,
    suffix_products,
    prefix_values,
)

SAMPLES_PER_CONTEXT = 64
PPO_EPOCHS = 4
MINIBATCH = 256
LEARNING_RATE = 0.05
ADAM_BETAS = (0.9, 0.999)
ADAM_EPS = 1e-8
CLIP_EPS = 0.2
VALUE_RATE = 0.1
NORM_EPS = 1e-8
UPDATES = 300
# (label, lambda_h at u = 0, lambda_h at u = U); linear as agent.py 7449: progress = u / U.
ENTROPY_SETTINGS = (("constant", 0.00125, 0.00125), ("annealed", 0.2, 0.01))


def entropy_coefficient(entropy_index: int, update: int, updates: int) -> float:
    _, start, end = ENTROPY_SETTINGS[entropy_index]
    return float(start + (end - start) * min(update / updates, 1.0))


def policy_stream(config_idx: int, arm_index: int, entropy_index: int,
                  seed: int) -> np.random.Generator:
    """Policy samples, E3 continuations and minibatch permutations of one training."""
    return np.random.default_rng([int(config_idx), int(arm_index), int(entropy_index), int(seed)])


class Adam:
    """torch.optim.Adam defaults (no weight decay, no amsgrad) on one parameter array."""

    def __init__(self, shape, lr: float = LEARNING_RATE, betas=ADAM_BETAS, eps: float = ADAM_EPS):
        self.lr, (self.beta1, self.beta2), self.eps = float(lr), betas, float(eps)
        self.m = np.zeros(shape)
        self.v = np.zeros(shape)
        self.t = 0

    def step(self, param: np.ndarray, grad: np.ndarray) -> None:
        self.t += 1
        self.m = self.beta1 * self.m + (1.0 - self.beta1) * grad
        self.v = self.beta2 * self.v + (1.0 - self.beta2) * grad * grad
        bias1 = 1.0 - self.beta1 ** self.t
        bias2 = 1.0 - self.beta2 ** self.t
        denom = np.sqrt(self.v) / np.sqrt(bias2) + self.eps
        param -= (self.lr / bias1) * self.m / denom


def joint_normalise(A: np.ndarray, team: np.ndarray, eps: float = NORM_EPS):
    """One mean and one std over all per-agent advantages and the team advantages."""
    values = np.concatenate([np.ravel(A), np.ravel(team)])
    mean = values.mean()
    std = values.std(ddof=1) + eps
    return (A - mean) / std, (team - mean) / std, float(mean), float(std)


def scatter_rows(x: np.ndarray, rows: np.ndarray, vectors: np.ndarray, n: int) -> np.ndarray:
    """Sum (..., N_LABELS) vectors into a (n, 85, 4) array at (x, rows)."""
    flat = (np.asarray(x) * N_PREFIXES + np.asarray(rows)).ravel()
    out = np.empty((n * N_PREFIXES, N_LABELS))
    vec = vectors.reshape(-1, N_LABELS)
    for k in range(N_LABELS):
        out[:, k] = np.bincount(flat, weights=vec[:, k], minlength=n * N_PREFIXES)
    return out.reshape(n, N_PREFIXES, N_LABELS)


def ppo_loss_grad(theta: np.ndarray, pmask: np.ndarray, x: np.ndarray, rows: np.ndarray,
                  z: np.ndarray, adv: np.ndarray, logp_old: np.ndarray,
                  lambda_h: float, clip: float = CLIP_EPS):
    """Loss and its exact gradient on the logits for one minibatch.

    x (B,), rows / z / adv / logp_old (B, K).  loss = -mean_{B x K} min(r A, clip(r) A)
    - lambda_h * mean_B sum_i H(pi(. | x, z_<i)).
    """
    B = z.shape[0]
    P = masked_softmax(theta, pmask)
    probs = P[x[:, None], rows]                                                  # (B, K, 4)
    p_exec = np.take_along_axis(probs, z[..., None], axis=-1)[..., 0]
    logp = np.log(p_exec)
    ratio = np.exp(logp - logp_old)
    clipped = np.clip(ratio, 1.0 - clip, 1.0 + clip)
    surrogate = np.minimum(ratio * adv, clipped * adv)
    logp_all = np.where(probs > 0, np.log(np.where(probs > 0, probs, 1.0)), 0.0)
    entropy = -(probs * logp_all).sum(axis=-1)                                   # (B, K)
    loss = -surrogate.mean() - lambda_h * entropy.sum(axis=1).mean()
    # d surrogate / d log pi = r A unless the clipped branch is the (strictly) smaller one.
    active = ~(((adv > 0) & (ratio > 1.0 + clip)) | ((adv < 0) & (ratio < 1.0 - clip)))
    coef = -(active * ratio * adv) / (B * K)
    onehot = np.zeros_like(probs)
    np.put_along_axis(onehot, z[..., None], 1.0, axis=-1)
    row_grad = coef[..., None] * (onehot - probs)
    d_entropy = -probs * (logp_all + entropy[..., None])
    row_grad += (-lambda_h / B) * d_entropy
    grad = scatter_rows(np.broadcast_to(x[:, None], rows.shape), rows, row_grad, theta.shape[0])
    return float(loss), grad


def ppo_update(theta: np.ndarray, adam: Adam, pmask: np.ndarray, z: np.ndarray,
               adv_norm: np.ndarray, logp_old: np.ndarray, lambda_h: float,
               rng: np.random.Generator, epochs: int = PPO_EPOCHS,
               minibatch: int = MINIBATCH) -> None:
    """4 epochs x (batch / minibatch) Adam steps; one permutation per epoch from ``rng``."""
    n, M, _ = z.shape
    x = np.repeat(np.arange(n), M)
    rows = prefix_rows(z).reshape(n * M, K)
    zf = z.reshape(n * M, K)
    af = adv_norm.reshape(n * M, K)
    lf = logp_old.reshape(n * M, K)
    size = n * M
    for _ in range(epochs):
        order = rng.permutation(size)
        for start in range(0, size, minibatch):
            idx = order[start:start + minibatch]
            _, grad = ppo_loss_grad(theta, pmask, x[idx], rows[idx], zf[idx], af[idx], lf[idx],
                                    lambda_h)
            adam.step(theta, grad)


def executed_log_probs(P: np.ndarray, z: np.ndarray) -> np.ndarray:
    n = P.shape[0]
    rows = prefix_rows(z)
    probs = P[np.arange(n)[:, None, None], rows]
    return np.log(np.take_along_axis(probs, z[..., None], axis=-1)[..., 0])


def batch_advantages(arm: str, P: np.ndarray, contexts, z: np.ndarray, d: np.ndarray,
                     R: np.ndarray, V: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """(n, M, K) advantages of one arm for the sampled batch (realised noisy demands d)."""
    if arm == "E1":
        return np.repeat((R - V[:, None])[..., None], K, axis=-1)
    if arm == "E3":
        return est.seqau_ridge(P, z, R, rng)
    if arm == "E4":
        removed = []
        for i in range(K):
            z_removed = z.copy()
            z_removed[..., i] = IDLE
            removed.append(reward(d, contexts.q[:, None], z_removed, contexts.mask, contexts.b0))
        return R[..., None] - np.stack(removed, axis=-1)
    jidx = joint_index(z)[..., None]                                              # (n, M, 1)
    rtab = reward_table(d, contexts.q, contexts.mask, contexts.b0)                # (n, M, 256)
    levels = prefix_values(suffix_products(P), rtab)
    if arm == "E3*":
        return est.seqau_exact(P, rtab, jidx, levels)[:, :, 0]
    if arm == "E4*":
        return est.removal_resampled(P, rtab, jidx, levels)[:, :, 0]
    raise ValueError(f"unknown arm {arm!r}")


def label_statistics(P: np.ndarray, contexts, r_bar: np.ndarray) -> dict:
    """At the final policy: relay fraction among relay-capable agents; greedy-optimal joint."""
    pj = joint_probs(P)
    relay_agents = np.flatnonzero(contexts.mask[:, RELAY])
    relay = [(pj * (JOINTS[:, agent] == RELAY)).sum(axis=-1) for agent in relay_agents]
    greedy = greedy_joints(r_bar)
    mode = np.argmax(pj, axis=-1)
    return {"relay_fraction": float(np.mean(relay)) if relay else float("nan"),
            "greedy_optimal_fraction": float(np.mean(mode == greedy)),
            "greedy_optimal_mass": float(np.take_along_axis(pj, greedy[:, None], -1).mean())}


@dataclass(frozen=True)
class TrainingTask:
    config_index: int
    arm_index: int
    entropy_index: int
    seed: int
    updates: int
    snapshots: tuple[int, ...] = ()


def train(task: TrainingTask) -> dict:
    """One training; bitwise reproducible from the task alone."""
    started = time.perf_counter()
    arm = est.ARMS[task.arm_index]
    contexts, ctx_rng = make_contexts(task.config_index, task.seed)
    rng = policy_stream(task.config_index, task.arm_index, task.entropy_index, task.seed)
    config = CONFIGURATIONS[task.config_index]
    n = contexts.n
    pmask = prefix_mask(contexts.mask)
    r_bar = mean_reward_table(contexts)
    j_star = float(r_bar.max(axis=-1).mean())
    theta = np.zeros((n, N_PREFIXES, N_LABELS))
    adam = Adam(theta.shape)
    V = None
    U = int(task.updates)
    J = np.empty(U + 1)
    snapshots = {}
    for u in range(U):
        if u in task.snapshots:
            snapshots[u] = theta.copy()
        P = masked_softmax(theta, pmask)
        J[u] = exact_J(P, r_bar)
        z = sample_joints(P, SAMPLES_PER_CONTEXT, rng)
        xi = ctx_rng.standard_normal((n, SAMPLES_PER_CONTEXT, contexts.d.shape[1]))
        d = noisy_demands(contexts.d[:, None, :], xi, config.sigma)
        R = reward(d, contexts.q[:, None], z, contexts.mask, contexts.b0)
        batch_mean = R.mean(axis=1)
        V = batch_mean.copy() if V is None else V + VALUE_RATE * (batch_mean - V)
        A = batch_advantages(arm, P, contexts, z, d, R, V, rng)
        adv_norm, _, _, _ = joint_normalise(A, R - V[:, None])
        logp_old = executed_log_probs(P, z)
        ppo_update(theta, adam, pmask, z, adv_norm, logp_old,
                   entropy_coefficient(task.entropy_index, u, U), rng)
    if U in task.snapshots:
        snapshots[U] = theta.copy()
    P = masked_softmax(theta, pmask)
    J[U] = exact_J(P, r_bar)
    return {
        "task": task, "arm": arm, "J": J, "J_star": j_star,
        "regret": float(np.mean(j_star - J[:U])), "final_J": float(J[U]),
        **label_statistics(P, contexts, r_bar),
        "snapshots": snapshots, "wall_seconds": time.perf_counter() - started,
    }
