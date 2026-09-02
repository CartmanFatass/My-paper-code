"""untied_toys.py -- standalone numerical study (numpy only; no torch, no repository code).

Part K1: commitment vs reactivity vs identifiability as a function of skill duration k.
Part K2: composed (semigroup-consistent) vs direct multi-horizon prediction, held-out durations.
Part N1: coordination coverage / index-space size / churn under variable N (exact combinatorics).

Writes RESULTS.md next to this file and mirrors everything to stdout.
"""
from __future__ import annotations

import time
from math import comb, factorial
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
MD: list[str] = []
STATS: dict[str, object] = {}
T0 = time.time()


def emit(line: str = "") -> None:
    MD.append(line)
    print(line)


def f4(v: float) -> str:
    if not np.isfinite(v):
        return "inf" if v > 0 else ("-inf" if v < 0 else "nan")
    if abs(v) < 100:
        return f"{v:.4f}"
    return f"{v:.3g}"


# ----------------------------------------------------------------------------
# Part K1
# ----------------------------------------------------------------------------
K_GRID = [1, 2, 3, 5, 7, 9, 13, 20, 40]
LAMBDAS = [0.005, 0.02, 0.05, 0.1, 0.2]
M_VALUES = [4, 8]
SIGMAS = [1.0, 2.0, 4.0]
N_SEG = 20000
R_DRIFT = 1.0


def commitment(k: int, lam: float) -> float:
    t = np.arange(k, dtype=float)
    return float(np.mean((1.0 - lam) ** t))


def bayes_accuracy(k: int, M: int, sigma: float, n: int = N_SEG, r: float = R_DRIFT) -> float:
    """MC estimate of Bayes-optimal accuracy of identifying z from the k-step displacement sum.

    sum = k*mu_z + sigma*sqrt(k)*N(0, I_2); isotropic equal-norm means -> MAP = argmax <sum, mu_z>.
    """
    rng = np.random.default_rng([90210, M, int(sigma), k])
    ang = 2.0 * np.pi * np.arange(M) / M
    mus = np.stack([r * np.cos(ang), r * np.sin(ang)], axis=1)  # (M, 2)
    z = rng.integers(0, M, size=n)
    s = k * mus[z] + sigma * np.sqrt(k) * rng.standard_normal((n, 2))
    pred = np.argmax(s @ mus.T, axis=1)
    return float(np.mean(pred == z))


def part_k1() -> None:
    emit("## Part K1 - commitment vs reactivity vs identifiability as a function of skill duration k")
    emit()

    # (i)
    emit("### K1(i) Commitment loss")
    emit()
    emit("Computed: C(k, lambda) = (1/k) * sum_{t=0}^{k-1} (1-lambda)^t, the expected fraction of the "
         "k committed steps during which the goal that was current at skill-selection time is still current; "
         "the latent goal switches each step with hazard lambda. Exact, no sampling. "
         f"k in {K_GRID}, lambda in {LAMBDAS}.")
    emit()
    emit("| k | " + " | ".join(f"lambda={l:g}" for l in LAMBDAS) + " |")
    emit("| ---: | " + " | ".join("---:" for _ in LAMBDAS) + " |")
    C = {}
    for k in K_GRID:
        cells = []
        for lam in LAMBDAS:
            C[(k, lam)] = commitment(k, lam)
            cells.append(f"{C[(k, lam)]:.4f}")
        emit(f"| {k} | " + " | ".join(cells) + " |")
    emit()

    # (ii)
    emit("### K1(ii) Identifiability")
    emit()
    emit("Computed: Monte-Carlo estimate of Bayes-optimal accuracy A(k) for identifying which of M skills "
         "generated a k-step segment. Skill z has drift mu_z on a circle of radius r=1 (M drifts evenly "
         "spaced); each step displacement = mu_z + sigma*N(0, I_2). The k-step sum is sufficient: "
         "sum ~ N(k*mu_z, k*sigma^2 I), so the Bayes rule under a uniform prior is argmax_z <sum, mu_z> "
         f"(valid because all ||mu_z|| are equal). {N_SEG} segments per setting, fixed per-setting seeds. "
         f"M in {M_VALUES}, sigma in {[int(s) for s in SIGMAS]}, k in {K_GRID}.")
    emit()
    cols = [(M, s) for M in M_VALUES for s in SIGMAS]
    emit("| k | " + " | ".join(f"M={M}, sig={s:g}" for M, s in cols) + " |")
    emit("| ---: | " + " | ".join("---:" for _ in cols) + " |")
    A = {}
    for k in K_GRID:
        cells = []
        for M, s in cols:
            A[(k, M, s)] = bayes_accuracy(k, M, s)
            cells.append(f"{A[(k, M, s)]:.4f}")
        emit(f"| {k} | " + " | ".join(cells) + " |")
    emit()
    emit(f"Chance level: M=4 -> 0.2500, M=8 -> 0.1250. Maximum MC standard error at n={N_SEG} is "
         f"0.5/sqrt(n) = {0.5 / np.sqrt(N_SEG):.4f}.")
    emit()

    # (iii)
    emit("### K1(iii) Combined per-step score and argmax k*")
    emit()
    emit("Computed: J(k) = C(k, lambda) * A(k) on the same k grid; each cell reports the grid argmax k* and "
         "the value J(k*). C is exact, A is the MC estimate from K1(ii), so k* inherits that MC noise. "
         f"Rows = (M, sigma), columns = lambda. k grid = {K_GRID}.")
    emit()
    emit("| M, sigma | " + " | ".join(f"lambda={l:g}" for l in LAMBDAS) + " |")
    emit("| --- | " + " | ".join("---:" for _ in LAMBDAS) + " |")
    kstars = {}
    for M, s in cols:
        cells = []
        for lam in LAMBDAS:
            js = [C[(k, lam)] * A[(k, M, s)] for k in K_GRID]
            i = int(np.argmax(js))
            kstars[(M, s, lam)] = K_GRID[i]
            cells.append(f"k*={K_GRID[i]} (J={js[i]:.4f})")
        emit(f"| M={M}, sig={s:g} | " + " | ".join(cells) + " |")
    emit()
    n_max = sum(1 for v in kstars.values() if v == K_GRID[-1])
    STATS["kstar_at_grid_max"] = n_max
    STATS["kstar_cells"] = len(kstars)
    STATS["kstar_row_M4s1"] = [kstars[(4, 1.0, lam)] for lam in LAMBDAS]
    emit(f"In {n_max} of the {len(kstars)} cells the argmax lands on the largest grid point "
         f"(k={K_GRID[-1]}), so k* is right-censored by the grid there.")
    emit()


# ----------------------------------------------------------------------------
# Part K2
# ----------------------------------------------------------------------------
D = 4
T_LEN = 40
SIGMA_W = 0.1
K_TRAIN = [1, 3, 5, 7, 9]
K_HELD = [2, 4, 6, 8]
K_EXT = [11, 13]
ALL_K = sorted(K_TRAIN + K_HELD + K_EXT)
KMAX = max(ALL_K)
N_TEST = 5000
RIDGE = 1e-6


def _rot(theta: float) -> np.ndarray:
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s], [s, c]])


ROT = np.zeros((D, D))
ROT[:2, :2] = _rot(0.3)
ROT[2:, 2:] = _rot(0.7)
A_LIN = 0.95 * ROT
A_NL = 1.60 * ROT


def simulate(n: int, kind: str, rng: np.random.Generator, T: int = T_LEN) -> np.ndarray:
    X = np.empty((n, T, D))
    x = rng.standard_normal((n, D))
    X[:, 0, :] = x
    for t in range(1, T):
        if kind == "linear":
            x = x @ A_LIN.T + SIGMA_W * rng.standard_normal((n, D))
        else:
            x = np.tanh(x @ A_NL.T) + SIGMA_W * rng.standard_normal((n, D))
        X[:, t, :] = x
    return X


def make_pairs(n: int, kind: str, rng: np.random.Generator):
    """One independent trajectory per sample; one uniformly random origin index per trajectory."""
    X = simulate(n, kind, rng)
    t0 = rng.integers(0, T_LEN - KMAX, size=n)  # origin in [0, 26] so that t0 + 13 <= 39
    idx = np.arange(n)
    x0 = X[idx, t0, :]
    fut = np.stack([X[idx, t0 + k, :] for k in range(1, KMAX + 1)], axis=1)  # (n, KMAX, D)
    return x0, fut


def feat(x: np.ndarray, kind: str) -> np.ndarray:
    ones = np.ones((x.shape[0], 1))
    if kind == "linear":
        return np.concatenate([x, ones], axis=1)
    return np.concatenate([x, x ** 2, ones], axis=1)


def kfeat(x: np.ndarray, k: int, kind: str) -> np.ndarray:
    b = x if kind == "linear" else np.concatenate([x, x ** 2], axis=1)
    ones = np.ones((x.shape[0], 1))
    return np.concatenate([b, k * b, (k ** 2) * b, ones, k * ones, (k ** 2) * ones], axis=1)


def fit_ridge(Phi: np.ndarray, Y: np.ndarray, lam: float = RIDGE) -> np.ndarray:
    d = Phi.shape[1]
    G = Phi.T @ Phi + lam * np.eye(d)
    try:
        return np.linalg.solve(G, Phi.T @ Y)
    except np.linalg.LinAlgError:
        return np.linalg.pinv(G) @ (Phi.T @ Y)


def nmse(pred: np.ndarray, true: np.ndarray) -> float:
    with np.errstate(over="ignore", invalid="ignore"):
        mse = np.mean((pred - true) ** 2, axis=0)
    var = np.var(true, axis=0)
    return float(np.mean(mse / var))


def run_k2_case(kind: str, n_train: int, kidx: int):
    rng_tr = np.random.default_rng([20260901, kidx, n_train])
    rng_te = np.random.default_rng([20260901, kidx, 999])
    x0tr, ftr = make_pairs(n_train, kind, rng_tr)
    x0te, fte = make_pairs(N_TEST, kind, rng_te)

    Phi_tr = feat(x0tr, kind)
    W1 = fit_ridge(Phi_tr, ftr[:, 0, :])
    Wd = {k: fit_ridge(Phi_tr, ftr[:, k - 1, :]) for k in K_TRAIN}
    Phi_k = np.concatenate([kfeat(x0tr, k, kind) for k in K_TRAIN], axis=0)
    Y_k = np.concatenate([ftr[:, k - 1, :] for k in K_TRAIN], axis=0)
    Wk = fit_ridge(Phi_k, Y_k)

    def composed(X, k):
        with np.errstate(over="ignore", invalid="ignore"):
            x = X
            for _ in range(k):
                x = feat(x, kind) @ W1
        return x

    def direct(X, k):
        with np.errstate(over="ignore", invalid="ignore"):
            if k in Wd:
                return feat(X, kind) @ Wd[k]
            if k in K_HELD:
                lo = max(kk for kk in K_TRAIN if kk < k)
                hi = min(kk for kk in K_TRAIN if kk > k)
                P = feat(X, kind)
                return 0.5 * (P @ Wd[lo] + P @ Wd[hi])
            kn = min(K_TRAIN, key=lambda kk: abs(kk - k))
            return feat(X, kind) @ Wd[kn]

    def kin(X, k):
        with np.errstate(over="ignore", invalid="ignore"):
            return kfeat(X, k, kind) @ Wk

    rows = {"COMPOSED": {}, "DIRECT-k": {}, "DIRECT-k-as-input": {}}
    for k in ALL_K:
        true = fte[:, k - 1, :]
        rows["COMPOSED"][k] = nmse(composed(x0te, k), true)
        rows["DIRECT-k"][k] = nmse(direct(x0te, k), true)
        rows["DIRECT-k-as-input"][k] = nmse(kin(x0te, k), true)

    inc = {}
    for (k1, k2) in [(3, 4), (5, 4)]:
        with np.errstate(over="ignore", invalid="ignore"):
            a = direct(x0te, k1 + k2)
            b = direct(direct(x0te, k1), k2)
            num = np.linalg.norm(a - b, axis=1)
            den = np.linalg.norm(fte[:, k1 + k2 - 1, :], axis=1)
        inc[(k1, k2)] = float(np.mean(num / den))

    return rows, inc, rows["COMPOSED"][1]


def part_k2() -> None:
    emit("## Part K2 - composed (semigroup-consistent) vs direct multi-horizon prediction")
    emit()
    emit("Setup shared by every K2 table: d=4 state. LINEAR x_{t+1} = A x_t + w_t with "
         "A = 0.95 * blockdiag(Rot(0.3), Rot(0.7)); NONLINEAR x_{t+1} = tanh(A' x_t) + w_t with "
         "A' = 1.6 * the same block rotation; w_t ~ N(0, 0.1^2 I). x_0 ~ N(0, I), trajectory length 40, "
         "one uniformly random origin t0 in [0, 26] per trajectory (so t0 + 13 <= 39); n_train training "
         "origin pairs, 5000 test origin pairs (the test set is fixed per dynamics and shared by both "
         "n_train). Feature map: [x, 1] linear, [x, x^2, 1] nonlinear. All fits are ordinary least squares "
         "with ridge 1e-6. COMPOSED = one-step fit composed k times. DIRECT-k = one regressor per k in "
         "K_train; at a held-out k the mean of the two nearest trained k, at an extrapolation k the nearest "
         "trained k (k=9). DIRECT-k-as-input = one regressor on [x, k*x, k^2*x, 1, k, k^2] (with the x^2 "
         "terms added in the nonlinear case) trained jointly on all of K_train. Metric: normalized MSE = "
         "MSE / Var(x_{t+k}) averaged over the 4 coordinates (1.0 = no better than predicting the marginal "
         "mean). Column groups: T = trained (K_train {1,3,5,7,9}), H = held-out interior "
         "(K_held {2,4,6,8}), E = extrapolation (K_ext {11,13}).")
    emit()
    groups = {k: ("T" if k in K_TRAIN else "H" if k in K_HELD else "E") for k in ALL_K}
    for kidx, kind in enumerate(["linear", "nonlinear"]):
        for n_train in [200, 2000]:
            rows, inc, one_step = run_k2_case(kind, n_train, kidx)
            emit(f"### K2 {kind.upper()} dynamics, n_train = {n_train} origin pairs")
            emit()
            emit(f"Computed: normalized MSE per model and per horizon k for the {kind} system, "
                 f"n_train = {n_train} training origin pairs, 5000 test origin pairs.")
            emit()
            emit("| model | " + " | ".join(f"k={k} ({groups[k]})" for k in ALL_K) + " |")
            emit("| --- | " + " | ".join("---:" for _ in ALL_K) + " |")
            for name in ["COMPOSED", "DIRECT-k", "DIRECT-k-as-input"]:
                emit(f"| {name} | " + " | ".join(f4(rows[name][k]) for k in ALL_K) + " |")
            emit()
            emit(f"One-step model's own normalized MSE (the k=1 fit that COMPOSED iterates): {f4(one_step)}.")
            emit()
            emit("DIRECT inconsistency INC = mean_x ||DIRECT_(k1+k2)(x) - DIRECT_k2(DIRECT_k1(x))|| / "
                 "||x_(t+k1+k2)|| over the 5000 test origins (k2=4 is the interpolated held-out operator; "
                 f"the 7- and 9-step targets are trained models): INC(3,4) = {f4(inc[(3, 4)])}, "
                 f"INC(5,4) = {f4(inc[(5, 4)])}. COMPOSED has INC = 0 by construction.")
            emit()


# ----------------------------------------------------------------------------
# Part N1
# ----------------------------------------------------------------------------
def stirling2(n: int, k: int) -> int:
    if k > n:
        return 0
    prev = [0] * (k + 1)
    prev[0] = 1
    for i in range(1, n + 1):
        cur = [0] * (k + 1)
        for j in range(1, min(i, k) + 1):
            cur[j] = j * prev[j] + prev[j - 1]
        prev = cur
    return prev[k]


def p_cover(N: int, K: int) -> float:
    return (factorial(K) * stirling2(N, K)) / (K ** N)


def part_n1() -> None:
    emit("## Part N1 - coordination coverage under variable N")
    emit()

    # (i)
    emit("### N1(i) Coverage under exchangeable independent sampling")
    emit()
    emit("Computed: exact P(all K roles covered) = K! * S(N, K) / K^N when each of N agents independently "
         "picks one of K roles uniformly at random (a shared policy with no symmetry breaking). S is the "
         "Stirling number of the second kind, evaluated in exact integer arithmetic. K in {2,3,4,6}; "
         "N in {K, K+1, K+2, K+4, 2K, 3K, 20}; each cell shows the probability and the N it used, since the "
         "labels collide for small K.")
    emit()
    labels = ["K", "K+1", "K+2", "K+4", "2K", "3K", "20"]
    emit("| K | " + " | ".join(f"N={l}" for l in labels) + " |")
    emit("| ---: | " + " | ".join("---:" for _ in labels) + " |")
    for K in [2, 3, 4, 6]:
        Ns = [K, K + 1, K + 2, K + 4, 2 * K, 3 * K, 20]
        emit(f"| {K} | " + " | ".join(f"{p_cover(N, K):.6f} (N={N})" for N in Ns) + " |")
    emit()
    rng = np.random.default_rng(4242)
    n_mc = 200000
    samp = rng.integers(0, 4, size=(n_mc, 8))
    hit = np.stack([(samp == r).any(axis=1) for r in range(4)], axis=1)
    p_hat = float(hit.all(axis=1).mean())
    p_ex = p_cover(8, 4)
    se = float(np.sqrt(p_hat * (1 - p_hat) / n_mc))
    emit(f"Monte-Carlo check of one row (K=4, N=8; {n_mc} independent samples, seed 4242): "
         f"exact = {p_ex:.6f}, MC = {p_hat:.6f}, difference = {p_hat - p_ex:+.6f}, "
         f"MC standard error = {se:.6f} ({abs(p_hat - p_ex) / se:.2f} SE).")
    emit()

    # (ii)
    emit("### N1(ii) Size of a team-skill index space")
    emit()
    emit("Computed: exact sizes of the joint assignment space K^N (agent-identified: who does what) versus "
         "the role-multiplicity / count space C(N+K-1, K-1) (agent-anonymous: how many agents per role), and "
         "their ratio. K in {3,4,8}, N in {3,5,7,9,15,21}. Exact integer arithmetic.")
    emit()
    emit("| K | N | K^N | C(N+K-1, K-1) | ratio K^N / count space |")
    emit("| ---: | ---: | ---: | ---: | ---: |")
    for K in [3, 4, 8]:
        for N in [3, 5, 7, 9, 15, 21]:
            joint = K ** N
            cnt = comb(N + K - 1, K - 1)
            emit(f"| {K} | {N} | {joint:,} | {cnt:,} | {joint / cnt:,.1f} |")
    emit()

    # (iii)
    emit("### N1(iii) Churn: expected roles left uncovered after removing one agent")
    emit()
    emit("Computed: an assignment covers all K roles with multiplicities as even as possible "
         "(N = q*K + rem, so rem roles hold q+1 agents and K-rem hold q). One agent is removed uniformly at "
         "random; a role can only become uncovered if it held exactly one agent, so "
         "E[# roles left uncovered] = (# roles with m_r = 1) / N. Exact. K in {3,4,8}, N from K to 3K; the "
         "smallest N at which the expectation is zero is marked.")
    emit()
    for K in [3, 4, 8]:
        emit(f"**K = {K}**")
        emit()
        emit("| N | multiplicities | # roles with m=1 | E[uncovered] | |")
        emit("| ---: | --- | ---: | ---: | --- |")
        first_zero = None
        for N in range(K, 3 * K + 1):
            q, rem = divmod(N, K)
            mult = [q + 1] * rem + [q] * (K - rem)
            ones = sum(1 for m in mult if m == 1)
            e = ones / N
            mark = ""
            if e == 0.0 and first_zero is None:
                first_zero = N
                mark = "<- smallest N with E = 0"
            emit(f"| {N} | {'+'.join(str(m) for m in mult)} | {ones} | {e:.4f} | {mark} |")
        emit()
        emit(f"Smallest N with E[uncovered] = 0 for K={K}: N = {first_zero} (= 2K).")
        emit()


# ----------------------------------------------------------------------------
def main() -> None:
    emit("# Untied-k / untied-N toy study")
    emit()
    emit("Standalone numpy-only numerical study. Every random draw is seeded explicitly, so rerunning "
         "`untied_toys.py` reproduces these numbers exactly.")
    emit()
    part_k1()
    part_k2()
    part_n1()

    emit("## Caveats")
    emit()
    emit("- **Monte-Carlo error, K1(ii).** Accuracies come from 20,000 segments per setting, so the standard "
         "error is at most 0.5/sqrt(20000) = 0.0035. Differences between adjacent k smaller than about 0.01 "
         "are inside noise, and the argmax k* in K1(iii) inherits that noise wherever J(k) is flat near its "
         "peak, which it often is.")
    emit("- **Monte-Carlo error, N1(i) check.** The 200,000-sample check has a standard error near 0.001; it "
         "verifies the closed form rather than measuring anything independently.")
    emit("- **Feature-map choice, K2.** The linear system's map [x, 1] contains the true one-step model, so "
         "COMPOSED is correctly specified there up to estimation error. The nonlinear map [x, x^2, 1] does "
         "not contain tanh, so every nonlinear model is misspecified; COMPOSED's nonlinear numbers are about "
         "compounding a *biased* one-step model, not about compounding estimation noise alone. A different "
         "feature map would move the nonlinear tables much more than the linear ones.")
    emit("- **Composing a quadratic map.** With the nonlinear feature map, composing the one-step model k "
         "times yields a polynomial of degree 2^k. At larger k this can overflow float64 on some test "
         "points; such entries appear as very large values, `inf` or `nan`, and are reported as computed "
         "rather than clipped.")
    emit("- **Sample budget is per model, not per horizon.** n_train counts origin pairs. COMPOSED and each "
         "DIRECT-k regressor see n_train rows; DIRECT-k-as-input sees 5*n_train rows because it pools all of "
         "K_train. The one-step model is fit only from the (x_t, x_{t+1}) pair of each sampled origin, not "
         "from all 39 consecutive transitions of the trajectory. That keeps the budget comparable across "
         "models but makes COMPOSED's one-step fit noisier than full trajectory reuse would.")
    emit("- **Conditioning of the k-as-input model.** Its features include k^2*x, which reaches 81*x at k=9 "
         "and 169*x at k=13, so the design matrix is badly scaled and ridge 1e-6 regularizes almost nothing. "
         "Its extrapolation columns are a quadratic-in-k extrapolation, which is why they can behave very "
         "differently from anything inside K_train.")
    emit("- **INC uses an interpolated operator.** For (k1,k2) = (3,4) and (5,4) the k2=4 step is the "
         "held-out interpolated DIRECT model (mean of the k=3 and k=5 regressors), because 4 is not in "
         "K_train; only the composite targets 7 and 9 are trained models. INC therefore measures the "
         "inconsistency of the DIRECT scheme as it would actually be deployed, interpolation rule included.")
    emit("- **Test targets are stochastic.** Targets come from the true noisy dynamics, so a perfect model "
         "still has nonzero normalized MSE, and that floor grows with k as process noise accumulates.")
    emit(f"- **Grid censoring in K1(iii).** The argmax is taken over the fixed grid "
         f"{K_GRID}, and in {STATS['kstar_at_grid_max']} of the {STATS['kstar_cells']} cells it lands on the "
         f"largest grid point k={K_GRID[-1]}. For those cells the tabulated k* is a lower bound on the "
         "unconstrained optimum, not a located interior maximum. J(k) is also flat near its peak in many "
         "cells, so k* is only identified to within a grid step or two.")
    emit("- **Surprises.** (1) In K1(iii) hazard and noise push k* in opposite directions and neither "
         f"dominates: at fixed (M, sigma) k* falls monotonically as lambda rises (M=4, sigma=1 gives "
         f"{STATS['kstar_row_M4s1']} across lambda = {LAMBDAS}), but the direction of the sigma effect flips "
         "with hazard: at lambda = 0.005-0.02 k* is non-decreasing in sigma (noisier segments need a longer "
         "commitment before the discriminator separates the skills), while at lambda = 0.1-0.2 it is "
         "non-increasing (M=8, lambda=0.2 gives k* = 5, 3, 1 for sigma = 1, 2, 4 - once identifiability is "
         "hopeless at any affordable k, the score just buys back commitment). lambda = 0.05 is the turning "
         "point and is non-monotone in sigma. The low-hazard/high-noise corner is exactly where the grid "
         "runs out. (2) The churn expectation in "
         "N1(iii) is exactly zero for every N >= 2K and strictly positive below it, so the whole "
         "interesting regime is the narrow band N in [K, 2K). (3) In the nonlinear K2 tables COMPOSED stays "
         "within about 1.5x of DIRECT-k out to k=4 and then diverges by many orders of magnitude within a "
         "few more steps, while DIRECT-k degrades smoothly; the extra training data (2000 vs 200 origins) "
         "moves the point where COMPOSED's normalized MSE first exceeds 1.0 from k=6 to k=9 but does not "
         "prevent the divergence.")
    emit()
    emit(f"Total runtime: {time.time() - T0:.1f} s.")

    (HERE / "RESULTS.md").write_text("\n".join(MD) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
