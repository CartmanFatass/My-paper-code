"""``chain_bandit`` host at K = 4 with exact enumeration (NumPy only, float64).

Joint labellings are indexed base-4 with agent 0 the most significant digit:
``joint = sum_i z_i * 4**(K - 1 - i)``.  Every prefix ``z_<i`` then owns one contiguous block
of ``4**(K - i)`` joints, which is what makes the exact prefix values a reshape-and-sum.

The tabular policy has one logit row per (context, prefix): prefix rows of agent i start at
``PREFIX_OFFSET[i]`` and are indexed by the base-4 code of ``z_<i`` (1 + 4 + 16 + 64 = 85).
Labels outside an agent's capability mask have probability exactly 0 (logit mask) and count as
IDLE in R.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import numpy as np

K = 4
IDLE, RELAY, SERVE_1, SERVE_2 = 0, 1, 2, 3
LABELS = ("IDLE", "RELAY", "SERVE_1", "SERVE_2")
N_LABELS = 4
C = 2
SERVE_LABEL = (SERVE_1, SERVE_2)          # cluster c is served by label SERVE_LABEL[c]
B_RELAYED = 1.0
N_CONTEXTS = 16
N_JOINTS = N_LABELS ** K                   # 256
DEMAND_RANGE = (0.3, 1.0)
QUALITY_RANGE = (0.3, 1.0)
DEMAND_CLIP = (0.05, 1.0)
N_NOISE_DRAWS = 32                         # fixed evaluation noise draws per context (sigma > 0)

BETAS = (0.0, 0.5, 0.9)
SUBSTITUTABILITY = (1, 2)
SIGMAS = (0.0, 0.2)
MASK_LABELS = {
    1: ((RELAY,), (SERVE_1,), (SERVE_2,), (SERVE_1, SERVE_2)),
    2: ((RELAY, SERVE_1), (RELAY, SERVE_2), (SERVE_1, SERVE_2), (SERVE_1, SERVE_2)),
}
BINDING_CORNER = (0.9, 1, 0.2)

PREFIX_OFFSET = (0, 1, 5, 21)
N_PREFIXES = 85
PREFIX_AGENT = np.repeat(np.arange(K), [N_LABELS ** i for i in range(K)])       # (85,)
JOINTS = np.array(list(product(range(N_LABELS), repeat=K)), dtype=np.int64)    # (256, K)
PLACE = np.array([N_LABELS ** (K - 1 - i) for i in range(K)], dtype=np.int64)   # (4,)


@dataclass(frozen=True)
class Configuration:
    beta: float
    s: int
    sigma: float

    @property
    def key(self) -> tuple:
        return (float(self.beta), int(self.s), float(self.sigma))

    @property
    def b0(self) -> float:
        return (1.0 - self.beta) * B_RELAYED

    def record(self) -> dict:
        return {"beta": self.beta, "s": self.s, "sigma": self.sigma, "b0": self.b0}


# Fixed ordering: beta outer, then s, then sigma.  ``config_index`` is the position here.
CONFIGURATIONS = tuple(Configuration(beta, s, sigma)
                       for beta in BETAS for s in SUBSTITUTABILITY for sigma in SIGMAS)


def config_index(key) -> int:
    """Index of (beta, s, sigma) in ``CONFIGURATIONS``; ValueError if not in the grid."""
    beta, s, sigma = key
    for index, config in enumerate(CONFIGURATIONS):
        if (np.isclose(config.beta, float(beta)) and config.s == int(s)
                and np.isclose(config.sigma, float(sigma))):
            return index
    raise ValueError(f"configuration {tuple(key)} is not in the calibration grid")


def capability_mask(s: int) -> np.ndarray:
    """(K, N_LABELS) bool; IDLE always allowed."""
    mask = np.zeros((K, N_LABELS), dtype=bool)
    mask[:, IDLE] = True
    for agent, labels in enumerate(MASK_LABELS[int(s)]):
        mask[agent, list(labels)] = True
    return mask


def prefix_mask(mask: np.ndarray) -> np.ndarray:
    """(85, N_LABELS) bool: each prefix row carries its agent's capability mask."""
    return mask[PREFIX_AGENT]


# ----------------------------------------------------------------------------- indexing

def joint_index(z) -> np.ndarray:
    return np.asarray(z, dtype=np.int64) @ PLACE


def prefix_code(z, i: int) -> np.ndarray:
    """Base-4 code of ``z[..., :i]`` (0 for the empty prefix)."""
    z = np.asarray(z, dtype=np.int64)
    code = np.zeros(z.shape[:-1], dtype=np.int64)
    for j in range(i):
        code = code * N_LABELS + z[..., j]
    return code


def prefix_rows(z) -> np.ndarray:
    """(..., K) prefix row of each agent for executed joints ``z`` (..., K)."""
    z = np.asarray(z, dtype=np.int64)
    rows = np.empty(z.shape, dtype=np.int64)
    code = np.zeros(z.shape[:-1], dtype=np.int64)
    for i in range(K):
        rows[..., i] = PREFIX_OFFSET[i] + code
        code = code * N_LABELS + z[..., i]
    return rows


JOINT_PREFIX = prefix_rows(JOINTS)                                              # (256, K)


def with_idle(joint, agents) -> np.ndarray:
    """Joint index with the given agents' labels replaced by IDLE."""
    joint = np.asarray(joint, dtype=np.int64)
    out = joint.copy()
    for agent in np.atleast_1d(agents):
        out = out - ((out // PLACE[agent]) % N_LABELS) * PLACE[agent]
    return out


# ----------------------------------------------------------------------------- contexts

@dataclass(frozen=True)
class Contexts:
    """16 fixed contexts of one (configuration, seed) with the stream's fixed evaluation noise."""
    config: Configuration
    d: np.ndarray            # (16, C) nominal demands
    q: np.ndarray            # (16, K, C) service qualities
    xi_eval: np.ndarray      # (16, N_NOISE_DRAWS, C) standard normal
    mask: np.ndarray         # (K, N_LABELS)

    @property
    def n(self) -> int:
        return int(self.d.shape[0])

    @property
    def b0(self) -> float:
        return self.config.b0

    def eval_demands(self) -> np.ndarray:
        """(16, n_eval, C) demands of the fixed evaluation set (one draw when sigma = 0)."""
        if self.config.sigma > 0:
            return noisy_demands(self.d[:, None, :], self.xi_eval, self.config.sigma)
        return self.d[:, None, :].copy()


def context_stream(config_idx: int, seed: int) -> np.random.Generator:
    """Contexts and every noise draw (evaluation set, then per-update training noise)."""
    return np.random.default_rng([int(config_idx), int(seed)])


def draw_contexts(config: Configuration, rng: np.random.Generator,
                  n: int = N_CONTEXTS) -> Contexts:
    d = rng.uniform(DEMAND_RANGE[0], DEMAND_RANGE[1], size=(n, C))
    q = rng.uniform(QUALITY_RANGE[0], QUALITY_RANGE[1], size=(n, K, C))
    xi_eval = rng.standard_normal((n, N_NOISE_DRAWS, C))
    return Contexts(config=config, d=d, q=q, xi_eval=xi_eval, mask=capability_mask(config.s))


def make_contexts(config_idx: int, seed: int) -> tuple[Contexts, np.random.Generator]:
    rng = context_stream(config_idx, seed)
    return draw_contexts(CONFIGURATIONS[config_idx], rng), rng


def noisy_demands(d, xi, sigma: float) -> np.ndarray:
    """``clip(d + sigma * xi, .05, 1)``: noise enters inside the min."""
    return np.clip(np.asarray(d) + float(sigma) * np.asarray(xi), DEMAND_CLIP[0], DEMAND_CLIP[1])


# ----------------------------------------------------------------------------- reward

def effective_labels(z, mask: np.ndarray) -> np.ndarray:
    """Masked labels count as IDLE."""
    z = np.asarray(z, dtype=np.int64)
    allowed = mask[np.arange(K), z]
    return np.where(allowed, z, IDLE)


def reward(d, q, z, mask: np.ndarray, b0: float) -> np.ndarray:
    """R(x, z) = sum_c min(d_c, access_c, backhaul) with broadcasting.

    d (..., C), q (..., K, C), z (..., K).  backhaul = B if any effective label is RELAY else b0.
    """
    eff = effective_labels(z, mask)
    q = np.asarray(q, dtype=np.float64)
    d = np.asarray(d, dtype=np.float64)
    total = 0.0
    backhaul = np.where((eff == RELAY).any(axis=-1), B_RELAYED, float(b0))
    for c in range(C):
        access = (q[..., c] * (eff == SERVE_LABEL[c])).sum(axis=-1)
        total = total + np.minimum(np.minimum(d[..., c], access), backhaul)
    return np.asarray(total, dtype=np.float64)


def access_table(q: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """(n, 256, C) access of every joint (masked labels as IDLE)."""
    eff = effective_labels(JOINTS, mask)                                     # (256, K)
    serve = np.stack([(eff == SERVE_LABEL[c]) for c in range(C)], axis=-1)   # (256, K, C)
    return np.einsum("nic,jic->njc", q, serve.astype(np.float64))


def backhaul_table(mask: np.ndarray, b0: float) -> np.ndarray:
    eff = effective_labels(JOINTS, mask)
    return np.where((eff == RELAY).any(axis=-1), B_RELAYED, float(b0))


def reward_table(d, q: np.ndarray, mask: np.ndarray, b0: float) -> np.ndarray:
    """R for all 256 joints.  d (n, S, C) demands per context and draw -> (n, S, 256)."""
    d = np.asarray(d, dtype=np.float64)
    access = access_table(q, mask)                                           # (n, 256, C)
    backhaul = backhaul_table(mask, b0)                                      # (256,)
    total = np.zeros(d.shape[:2] + (N_JOINTS,))
    for c in range(C):
        total += np.minimum(np.minimum(d[:, :, None, c], access[:, None, :, c]),
                            backhaul[None, None, :])
    return total


def mean_reward_table(contexts: Contexts) -> np.ndarray:
    """(16, 256): R averaged over the fixed evaluation noise set (exact R when sigma = 0)."""
    return reward_table(contexts.eval_demands(), contexts.q, contexts.mask,
                        contexts.b0).mean(axis=1)


def greedy_joints(r_bar: np.ndarray) -> np.ndarray:
    """argmax_z per context, ties to the lowest joint index (np.argmax returns the first)."""
    return np.argmax(r_bar, axis=-1)


# ----------------------------------------------------------------------------- policy

def masked_softmax(theta: np.ndarray, pmask: np.ndarray) -> np.ndarray:
    """theta (..., 85, 4), pmask (85, 4) -> probabilities with masked entries exactly 0."""
    logits = np.where(pmask, theta, -np.inf)
    logits = logits - logits.max(axis=-1, keepdims=True)
    e = np.where(pmask, np.exp(logits), 0.0)
    return e / e.sum(axis=-1, keepdims=True)


def joint_probs(P: np.ndarray) -> np.ndarray:
    """(n, 85, 4) prefix probabilities -> (n, 256) joint probabilities."""
    out = np.ones((P.shape[0], N_JOINTS))
    for i in range(K):
        out = out * P[:, JOINT_PREFIX[:, i], JOINTS[:, i]]
    return out


def suffix_products(P: np.ndarray) -> np.ndarray:
    """(n, 256, K + 1): sp[..., i] = prod_{j >= i} pi_j(z_j | z_<j); sp[..., K] = 1."""
    factors = np.stack([P[:, JOINT_PREFIX[:, i], JOINTS[:, i]] for i in range(K)], axis=-1)
    sp = np.ones(factors.shape[:2] + (K + 1,))
    for i in range(K - 1, -1, -1):
        sp[..., i] = sp[..., i + 1] * factors[..., i]
    return sp


def prefix_values(sp: np.ndarray, rtab: np.ndarray) -> list[np.ndarray]:
    """Exact Q(x, z_<i) for every prefix at levels i = 0..K.

    sp (n, 256, K + 1); rtab (n, S, 256).  Returns a list whose element i has shape
    (n, S, 4**i): the expectation of R over z_>=i ~ pi given the prefix (level K is R itself).
    """
    out = []
    for i in range(K + 1):
        prod = sp[:, None, :, i] * rtab
        out.append(prod.reshape(prod.shape[:2] + (N_LABELS ** i, N_LABELS ** (K - i))).sum(-1))
    return out


def exact_J(P: np.ndarray, r_bar: np.ndarray) -> float:
    """mean over contexts of E_pi[R] on the (noise-averaged) reward table (n, 256)."""
    return float((joint_probs(P) * r_bar).sum(axis=-1).mean())


def score_rows(P: np.ndarray, x: np.ndarray, rows: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """grad of log pi(label | row) wrt the row's logits: onehot(label) - pi(. | row) (masked 0)."""
    probs = P[x, rows]
    onehot = np.zeros_like(probs)
    np.put_along_axis(onehot, labels[..., None], 1.0, axis=-1)
    return onehot - probs


def expected_score_update(P: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """sum over joints and agents of weights[x, n, i] * grad log pi_i(z_i | x, z_<i).

    P (n, 85, 4); weights (n, 256, K) already include pi(z | x) and any context weighting.
    Returns (n, 85, 4).
    """
    n = P.shape[0]
    grad = np.zeros((n, N_PREFIXES, N_LABELS))
    x = np.arange(n)[:, None]
    for i in range(K):
        rows = JOINT_PREFIX[:, i][None, :]                                    # (1, 256)
        w = weights[:, :, i]                                                  # (n, 256)
        flat_row = (x * N_PREFIXES + rows).ravel()
        flat_label = flat_row * N_LABELS + np.broadcast_to(JOINTS[:, i], w.shape).ravel()
        grad += np.bincount(flat_label, weights=w.ravel(),
                            minlength=n * N_PREFIXES * N_LABELS).reshape(grad.shape)
        mass = np.bincount(flat_row, weights=w.ravel(), minlength=n * N_PREFIXES)
        grad -= mass.reshape(n, N_PREFIXES, 1) * P
    return grad


def exact_grad_J(P: np.ndarray, r_bar: np.ndarray) -> np.ndarray:
    """Exact grad of J = mean_x E_pi[R] on the tabular logits (score-function identity)."""
    pj = joint_probs(P)
    weights = (pj * r_bar)[:, :, None] * np.ones((1, 1, K)) / P.shape[0]
    return expected_score_update(P, weights)


def sample_labels(probs: np.ndarray, u: np.ndarray) -> np.ndarray:
    """Inverse-CDF sampling; zero-probability labels are never chosen."""
    cum = np.cumsum(probs, axis=-1)
    cum = cum / cum[..., -1:]
    return (cum < u[..., None]).sum(axis=-1).astype(np.int64)


def sample_joints(P: np.ndarray, n_samples: int, rng: np.random.Generator) -> np.ndarray:
    """Ancestral sampling: (n, n_samples, K) labels, one uniform per (context, sample, agent)."""
    n = P.shape[0]
    z = np.zeros((n, n_samples, K), dtype=np.int64)
    code = np.zeros((n, n_samples), dtype=np.int64)
    x = np.arange(n)[:, None]
    for i in range(K):
        probs = P[x, PREFIX_OFFSET[i] + code]
        z[..., i] = sample_labels(probs, rng.random((n, n_samples)))
        code = code * N_LABELS + z[..., i]
    return z
