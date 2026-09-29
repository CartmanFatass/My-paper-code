"""P3 interaction reader for coupled_host_joint_skills_stage1 b01 (T4, disposition item 5).

One commitment table (``collect_commitments.py``) -> one pre-specified reading, worded
"pre-specified non-additive predictive structure on a competent checkpoint: supported /
unsupported / unreadable".  Competence is the P2 reading's business, not this reader's.

Response ``y = segment_mean_r`` (mean contract team r of the ten executed steps).

Reduced model R (OLS; column names as written to the JSON):

* ``intercept``; ``time`` = t0 / 500; ``c_bh_t0``; ``sd_t0`` (pre-commitment C_bh and S/D);
* per UAV i = 0..5: ``relay_i``, ``routed_i``, ``serving_i`` (pre-commitment roles at t0);
* agent-index-specific single-label additive terms ``agent{i}_label{z}`` = 1[agent_labels[i] = z]
  for z = 1..5 (label 0 dropped per agent).
* The declared control "number of routed UAVs at t0" is **not** a separate column: it equals
  sum_i routed_i exactly, so it is already in R's span.

R columns with zero variance on the table are dropped (listed in the output).

Full model F = R + an added block of 72 pre-specified columns:

* label-count block, 15 columns ``n{z}*n{z'}`` for 0 <= z < z' <= 5, where n_z = #agents holding
  label z.  Contrasts: with sum_z n_z = 6 and each n_z = sum_i 1[agent_labels[i] = z] inside R's
  additive span (label 0's indicator = 1 - the other five), every square is spanned:
  n_z^2 = 6 n_z - sum_{z' != z} n_z n_z'.  Degree-2 polynomials on the simplex {sum n = 6} have
  dimension 21 of which 6 are affine, so the 15 pairwise products are exactly the independent
  quadratic contrasts beyond the additive terms (the squares add no column);
* relay-service block, 36 columns ``rs_{z}to{z'}`` (ordered, z = z' included): the number of
  pre-commitment relations "UAV i is an interior node of UAV j's BS path" with label_i = z and
  label_j = z';
* relay-pair block, 21 columns ``rp_{z}_{z'}`` (z <= z'): the number of unordered pairs of
  distinct UAVs that are both relays at t0 (each an interior node of some other UAV's BS path,
  not necessarily on the same path) with labels {z, z'}.

Support and readability (DM decision T4b; fixed on the design, never on the response).  All
non-intercept columns are standardised with full-table mean/SD (a linear re-parametrisation:
OLS predictions are unchanged).  An added column is SUPPORTED iff its non-zero rows >=
max(8, ceil(0.01 * rows)) (128 at 12,800 rows) AND its non-zero episodes >= 8.  F = R + the
supported columns of the 72-column block; unsupported columns are listed under
``missing_support.unsupported`` with their facts and are never read as zero effects.  READABLE
iff (a) at least 10 of the 15 label-count products are supported, (b) the numerical rank
(``numpy.linalg.matrix_rank``'s tolerance) of [R_kept | supported] exceeds that of R_kept by the
number of supported columns (otherwise the spanned columns are listed, by Gram-Schmidt in the
declared order, and the reading is unreadable), and (c) all K folds are non-empty.

Secondary reading (pre-specified): the same rule, folds, draws and pass rule on R + the
supported product columns alone, reported as ``omnibus_products_only`` with its own decision
``decision_products_only``.  The primary decision is the full supported block's.

Omnibus statistic.  Fixed grouped K-fold CV, K = 8, groups = episodes = (lane, episode)
pairs; fold(g) = int.from_bytes(sha256(f"lane{lane}:episode{episode}")[:8], "big") % 8.
Delta = mean over folds of (MSE_R - MSE_F), each fold fitted by OLS on the other folds and
scored on its own rows.

Calibration under the additive null.  Fit R on all rows: fitted f, residual e.  For b = 1..1000,
w_b = ``default_rng(20260929 + b).integers(0, 2, size=G) * 2 - 1`` (one Rademacher draw per
episode, episodes in sorted (lane, episode) order); y*_b = f + e * w_b[group]; Delta*_b with the
same folds.  Pass = Delta > 0 and Delta > ``numpy.quantile(Delta*, 0.95)``.

The 1,000 refits are computed exactly through linearity rather than 1,000 loops: every y*_b is
f + sum_g w_bg e_g (e_g = e on episode g, zero elsewhere) and the observed y is the all-ones
vector of the same basis; per fold and model, one OLS solve with the 1 + G basis columns
(normal equations on the standardised design when lambda_min/lambda_max of X'X > 1e-10, else
min-norm ``lstsq`` on the fold's rows) gives the held-out residual of each basis vector, their
Gram matrix M, and every fold MSE as v' M v / n_fold with v = (1, w_b).  This is algebraically
identical to refitting OLS on each y*_b (the solution is linear in y); the observed Delta is
cross-checked against a direct ``lstsq`` refit and the test suite compares direct refits for a
few draws.

Placebo (conditional diagnostic, not a veto): the same statistic and null draws with the
team-label one-hot (``team_label{z}``, z = 1..5) added to R instead of the interaction block.
The structural zero check (team-label change at fixed individual labels, state and actor hidden
state) is run by the collector on the live agent and copied here from ``meta.json``.
"""
from __future__ import annotations

import time
PROCESS_START = time.perf_counter()

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import sys
import traceback

for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from scripts.hmasd_admission import require_admission

SCHEMA = 1
DIRECTION = "coupled_host_joint_skills_stage1"
N_UAVS = 6
N_LABELS = 6
HORIZON = 500
K_FOLDS = 8
N_BOOT = 1000
BOOT_SEED_BASE = 20260929
PASS_QUANTILE = 0.95
READING_WORDING = ("pre-specified non-additive predictive structure on a competent checkpoint: "
                   "supported / unsupported / unreadable")
GRAM_SCHMIDT_TOL = 1e-8
#: Support rule (DM, T4b): fixed on the design, never on the response.
SUPPORT_ROW_FRACTION = 0.01
SUPPORT_MIN_ROWS_FLOOR = 8
SUPPORT_MIN_EPISODES = 8
MIN_SUPPORTED_PRODUCTS = 10
SUPPORT_RULE_TEXT = ("an added column is SUPPORTED iff its non-zero rows >= max(8, ceil(0.01 * rows)) "
                     "(128 at 12,800 rows) AND its non-zero episodes >= 8; F = R + the supported columns "
                     "of the 72-column block; unsupported columns are listed under missing_support.unsupported "
                     "with their facts and are never treated as zero effects")
READABILITY_RULE_TEXT = ("READABLE iff (a) at least 10 of the 15 label-count-product columns are supported, "
                         "(b) the rank increment of R + supported columns over R equals the number of supported "
                         "columns (otherwise the spanned ones are listed and the reading is unreadable), and "
                         "(c) all K folds are non-empty; the secondary products-only reading applies the same "
                         "rule to R + the supported product columns")
#: Fold fits use the normal equations when lambda_min / lambda_max of X'X exceeds this
#: (cond(X) < 1e5 on the standardised design); otherwise min-norm lstsq on the fold's rows.
NORMAL_EQUATIONS_MIN_RATIO = 1e-10
DIRECT_CHECK_RTOL = 1e-7
SNAPSHOT_PARENT = "hmasd-launch-sources"
TABLE_KEYS = ("lane", "episode", "t0", "c_bh_t0", "sd_t0", "routed", "relay", "serving",
              "agent_labels", "team_label", "relay_matrix", "segment_mean_r")

COUNT_PAIRS = tuple((z, w) for z in range(N_LABELS) for w in range(z + 1, N_LABELS))
RS_PAIRS = tuple((z, w) for z in range(N_LABELS) for w in range(N_LABELS))
RP_PAIRS = tuple((z, w) for z in range(N_LABELS) for w in range(z, N_LABELS))
COUNT_NAMES = tuple(f"n{z}*n{w}" for z, w in COUNT_PAIRS)
RS_NAMES = tuple(f"rs_{z}to{w}" for z, w in RS_PAIRS)
RP_NAMES = tuple(f"rp_{z}_{w}" for z, w in RP_PAIRS)
ADDED_NAMES = COUNT_NAMES + RS_NAMES + RP_NAMES
REDUCED_NAMES = (("intercept", "time", "c_bh_t0", "sd_t0")
                 + tuple(f"{role}_{i}" for role in ("relay", "routed", "serving") for i in range(N_UAVS))
                 + tuple(f"agent{i}_label{z}" for i in range(N_UAVS) for z in range(1, N_LABELS)))
PLACEBO_NAMES = tuple(f"team_label{z}" for z in range(1, N_LABELS))


# ------------------------------------------------------------------------------ paths


def _data_root(path):
    parts = Path(path).parts
    for index in range(len(parts) - 2):
        if parts[index] == ".git" and parts[index + 1] == SNAPSHOT_PARENT:
            return Path(*parts[:index])
    return Path(path)


DATA_ROOT = _data_root(ROOT)


def resolve_input(path):
    """Relative inputs resolve against the checkout holding ``runs/`` (snapshot-safe)."""
    path = Path(path)
    if not path.is_absolute():
        return (DATA_ROOT / path).resolve()
    parts = path.parts
    for index in range(len(parts) - 3):
        if parts[index] == ".git" and parts[index + 1] == SNAPSHOT_PARENT:
            return Path(*parts[:index], *parts[index + 3:]).resolve()
    return path.resolve()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def jsonable(value):
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return jsonable(value.tolist())
    if isinstance(value, np.generic):
        return jsonable(value.item())
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        return "inf" if value > 0 else ("-inf" if value < 0 else "nan")
    return value


def write_json(path, value):
    encoded = json.dumps(jsonable(value), indent=2, allow_nan=False) + "\n"
    partial = Path(path).with_suffix(Path(path).suffix + ".partial")
    partial.write_text(encoded, encoding="utf-8")
    partial.replace(path)


def cpu_seconds():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return float(usage.ru_utime + usage.ru_stime)


# ------------------------------------------------------------------------------ design


def load_table(path):
    with np.load(path) as data:
        return {key: np.asarray(data[key]) for key in TABLE_KEYS}


def check_table(table):
    n = np.asarray(table["segment_mean_r"]).shape[0]
    shapes = {"routed": (n, N_UAVS), "relay": (n, N_UAVS), "serving": (n, N_UAVS),
              "agent_labels": (n, N_UAVS), "relay_matrix": (n, N_UAVS, N_UAVS)}
    for key in TABLE_KEYS:
        value = np.asarray(table[key])
        expected = shapes.get(key, (n,))
        if value.shape != expected:
            raise ValueError(f"table column {key} has shape {value.shape}, expected {expected}")
    for key in ("agent_labels", "team_label"):
        labels = np.asarray(table[key])
        if np.any((labels < 0) | (labels >= N_LABELS)):
            raise ValueError(f"{key} outside [0, {N_LABELS})")
    if not np.all(np.isfinite(np.asarray(table["segment_mean_r"], dtype=float))):
        raise ValueError("non-finite response")
    matrix = np.asarray(table["relay_matrix"], dtype=bool)
    if np.any(matrix[:, np.arange(N_UAVS), np.arange(N_UAVS)]):
        raise ValueError("a UAV relays for itself")
    if not np.array_equal(matrix.any(axis=2), np.asarray(table["relay"], dtype=bool)):
        raise ValueError("relay indicators disagree with the relay matrix")
    return n


def reduced_block(table):
    n = np.asarray(table["segment_mean_r"]).shape[0]
    labels = np.asarray(table["agent_labels"], dtype=np.int64)
    columns = [np.ones(n), np.asarray(table["t0"], float) / HORIZON,
               np.asarray(table["c_bh_t0"], float), np.asarray(table["sd_t0"], float)]
    for role in ("relay", "routed", "serving"):
        values = np.asarray(table[role], float)
        columns += [values[:, i] for i in range(N_UAVS)]
    for i in range(N_UAVS):
        columns += [(labels[:, i] == z).astype(float) for z in range(1, N_LABELS)]
    return np.column_stack(columns)


def added_block(table):
    labels = np.asarray(table["agent_labels"], dtype=np.int64)
    n = labels.shape[0]
    onehot = np.zeros((n, N_UAVS, N_LABELS))
    onehot[np.arange(n)[:, None], np.arange(N_UAVS)[None, :], labels] = 1.0
    counts = onehot.sum(axis=1)  # n_z
    count_cols = [counts[:, z] * counts[:, w] for z, w in COUNT_PAIRS]
    matrix = np.asarray(table["relay_matrix"], float)  # [i relays for j]
    # rs[z, w] = sum_{i, j} 1[label_i = z] M[i, j] 1[label_j = w]
    rs = np.einsum("niz,nij,njw->nzw", onehot, matrix, onehot)
    rs_cols = [rs[:, z, w] for z, w in RS_PAIRS]
    relay = np.asarray(table["relay"], float)
    relay_counts = np.einsum("ni,niz->nz", relay, onehot)  # relays holding label z
    # Unordered pairs of distinct relays: m_z m_w for z != w, m_z (m_z - 1) / 2 for z = w.
    rp_cols = [relay_counts[:, z] * (relay_counts[:, z] - 1.0) / 2.0 if z == w
               else relay_counts[:, z] * relay_counts[:, w] for z, w in RP_PAIRS]
    return np.column_stack(count_cols + rs_cols + rp_cols)


def placebo_block(table):
    team = np.asarray(table["team_label"], dtype=np.int64)
    return np.column_stack([(team == z).astype(float) for z in range(1, N_LABELS)])


def standardise(block):
    """Centre/scale every column with full-table moments; zero-variance columns -> zeros."""
    block = np.asarray(block, dtype=np.float64)
    mean = block.mean(axis=0)
    sd = block.std(axis=0)
    zero = sd <= 1e-12 * np.maximum(1.0, np.abs(mean))
    scaled = np.where(zero, 0.0, (block - mean) / np.where(zero, 1.0, sd))
    return scaled, zero


def rank_and_condition(matrix):
    """Numerical rank (``numpy.linalg.matrix_rank``'s SVD tolerance) and sigma_max / sigma_min
    (inf when rank-deficient) from one SVD."""
    s = np.linalg.svd(matrix, compute_uv=False)
    tol = s[0] * max(matrix.shape) * np.finfo(float).eps
    rank = int(np.sum(s > tol))
    return rank, (float(s[0] / s[-1]) if rank == min(matrix.shape) else float("inf"))


def spanned_columns(base, block, names):
    """Declared-order Gram-Schmidt: names of ``block`` columns spanned by ``base`` + earlier ones."""
    q, s, _ = np.linalg.svd(base, full_matrices=False)
    basis = q[:, s > s[0] * max(base.shape) * np.finfo(float).eps]
    spanned = []
    for index, name in enumerate(names):
        column = block[:, index]
        norm = float(np.linalg.norm(column))
        if norm == 0.0:
            continue
        residual = column - basis @ (basis.T @ column)
        residual -= basis @ (basis.T @ residual)
        if np.linalg.norm(residual) <= GRAM_SCHMIDT_TOL * norm:
            spanned.append(name)
        else:
            basis = np.column_stack([basis, residual / np.linalg.norm(residual)])
    return spanned


def groups_and_folds(table, k_folds=K_FOLDS):
    lane = np.asarray(table["lane"], dtype=np.int64)
    episode = np.asarray(table["episode"], dtype=np.int64)
    keys = sorted(set(zip(lane.tolist(), episode.tolist())))
    index = {key: g for g, key in enumerate(keys)}
    group = np.asarray([index[key] for key in zip(lane.tolist(), episode.tolist())], dtype=np.int64)
    fold_of_group = np.asarray([
        int.from_bytes(hashlib.sha256(f"lane{l}:episode{e}".encode("utf-8")).digest()[:8], "big") % k_folds
        for l, e in keys], dtype=np.int64)
    assignment = [[int(l), int(e), int(f)] for (l, e), f in zip(keys, fold_of_group)]
    assignment_hash = hashlib.sha256(json.dumps(assignment).encode("utf-8")).hexdigest()
    return group, fold_of_group[group], keys, fold_of_group, assignment_hash


def rademacher(n_groups, draws, base=BOOT_SEED_BASE):
    """Row b-1 = the draw with seed ``base + b`` (b = 1..draws)."""
    return np.stack([np.random.default_rng(base + b).integers(0, 2, size=n_groups) * 2 - 1
                     for b in range(1, draws + 1)]).astype(np.float64)


def _solve_fold(xtx, xtb, x_train, b_train):
    """OLS coefficients on one training fold.  Normal equations on the standardised design when
    they are well conditioned; otherwise the min-norm ``lstsq`` solution on the fold's rows."""
    w = np.linalg.eigvalsh(xtx)
    if w[0] > NORMAL_EQUATIONS_MIN_RATIO * w[-1]:
        return np.linalg.solve(xtx, xtb), int(xtx.shape[0]), "normal_equations"
    coef, _, rank, _ = np.linalg.lstsq(x_train, b_train, rcond=None)
    return coef, int(rank), "lstsq"


def fold_grams(design, basis, fold, k_folds):
    """Held-out residual Gram matrix of every basis column, per fold."""
    xtx_all = design.T @ design
    xtb_all = design.T @ basis
    grams, sizes, ranks, solvers = [], [], [], []
    for k in range(k_folds):
        test = fold == k
        x_test, b_test = design[test], basis[test]
        coef, rank, solver = _solve_fold(xtx_all - x_test.T @ x_test, xtb_all - x_test.T @ b_test,
                                         design[~test], basis[~test])
        residual = b_test - x_test @ coef
        grams.append(residual.T @ residual)
        sizes.append(int(test.sum()))
        ranks.append(rank)
        solvers.append(solver)
    return grams, sizes, ranks, solvers


def fold_mse(grams, sizes, vectors):
    """MSE per fold (rows) and vector (columns) for coefficient vectors ``vectors`` (basis x m)."""
    return np.stack([np.sum(vectors * (gram @ vectors), axis=0) / size for gram, size in zip(grams, sizes)])


def direct_cv_delta(design_r, design_f, y, fold, k_folds):
    """Delta by explicit per-fold refits (cross-check of the Gram route)."""
    per_fold = []
    for k in range(k_folds):
        test = fold == k
        train = ~test
        mse = []
        for design in (design_r, design_f):
            coef = np.linalg.lstsq(design[train], y[train], rcond=None)[0]
            mse.append(float(np.mean((y[test] - design[test] @ coef) ** 2)))
        per_fold.append(mse[0] - mse[1])
    return float(np.mean(per_fold)), per_fold


def _summary(values):
    values = np.asarray(values, dtype=float)
    return {"mean": float(values.mean()), "sd": float(values.std(ddof=1)) if values.size > 1 else 0.0,
            "min": float(values.min()), "q50": float(np.quantile(values, .5)),
            "q90": float(np.quantile(values, .9)), "q95": float(np.quantile(values, .95)),
            "q99": float(np.quantile(values, .99)), "max": float(values.max())}


def support_facts(block, names, group):
    facts = {}
    for index, name in enumerate(names):
        nonzero = block[:, index] != 0
        facts[name] = {"nonzero_rows": int(nonzero.sum()),
                       "nonzero_episodes": int(np.unique(group[nonzero]).size)}
    return facts


def support_threshold_rows(n_rows):
    """Minimum non-zero rows of a supported column: 1 % of the table's rows, at least 8."""
    return max(SUPPORT_MIN_ROWS_FLOOR, int(math.ceil(SUPPORT_ROW_FRACTION * int(n_rows))))


def block_support(raw_block, names, group, n_rows):
    """Support facts and the SUPPORTED mask of a block (a design-only rule; never the response)."""
    min_rows = support_threshold_rows(n_rows)
    facts = support_facts(raw_block, names, group)
    supported = np.asarray([facts[name]["nonzero_rows"] >= min_rows
                            and facts[name]["nonzero_episodes"] >= SUPPORT_MIN_EPISODES for name in names])
    for name, ok in zip(names, supported):
        facts[name]["supported"] = bool(ok)
    return facts, supported


def _block_design(x_r, block_std, supported, names, facts, min_products, product_names):
    """Readability of R + the supported columns of one block (rule (a) and (b))."""
    used = [name for name, ok in zip(names, supported) if ok]
    x_block = block_std[:, supported]
    x_full = np.column_stack([x_r, x_block])
    rank_r, _ = rank_and_condition(x_r)
    rank_f, cond_f = rank_and_condition(x_full)
    increment = rank_f - rank_r
    products_supported = sum(1 for name in used if name in product_names)
    spanned = spanned_columns(x_r, x_block, used) if increment < len(used) else []
    reasons = []
    if products_supported < min_products:
        reasons.append(f"{products_supported} of {len(product_names)} label-count products supported "
                       f"(at least {min_products} required)")
    if increment != len(used):
        reasons.append(f"supported columns raise the rank by {increment} of {len(used)}; spanned: {spanned}")
    return {
        "columns_used": used,
        "unsupported": {name: facts[name] for name, ok in zip(names, supported) if not ok},
        "spanned": spanned,
        "products_supported": products_supported,
        "rank": {"reduced": rank_r, "full": rank_f, "full_columns": int(x_full.shape[1]),
                 "added_increment": increment, "added_supported_columns": len(used)},
        "condition_number_full": cond_f,
        "readable": not reasons,
        "reasons": reasons,
    }, x_full


def _omnibus(grams_r, grams_f, sizes, vectors, ranks_r, ranks_f, solvers_r, solvers_f):
    mse_r = fold_mse(grams_r, sizes, vectors)
    mse_f = fold_mse(grams_f, sizes, vectors)
    per_fold = mse_r - mse_f
    deltas = per_fold.mean(axis=0)
    observed, null = float(deltas[0]), deltas[1:]
    threshold = float(np.quantile(null, PASS_QUANTILE))
    passed = bool(observed > 0.0 and observed > threshold)
    return {"delta": observed, "delta_per_fold": per_fold[:, 0].tolist(),
            "mse_reduced_per_fold": mse_r[:, 0].tolist(), "mse_full_per_fold": mse_f[:, 0].tolist(),
            "null_quantile_95": threshold, "null_fraction_below_observed": float(np.mean(null < observed)),
            "null_summary": _summary(null), "passed": passed, "decision": "supported" if passed else "unsupported",
            "fold_rank_reduced": ranks_r, "fold_rank_full": ranks_f,
            "fold_solver_reduced": solvers_r, "fold_solver_full": solvers_f}


def read_table(table, *, n_boot=N_BOOT, boot_seed_base=BOOT_SEED_BASE, k_folds=K_FOLDS,
               direct_check=True):
    """The pre-specified reading of one commitment table (a dict of arrays)."""
    timing = {}
    started = time.perf_counter()
    n = check_table(table)
    y = np.asarray(table["segment_mean_r"], dtype=np.float64)
    group, fold, keys, fold_of_group, assignment_hash = groups_and_folds(table, k_folds)
    n_groups = len(keys)

    reduced_raw = reduced_block(table)
    reduced_std, reduced_zero = standardise(reduced_raw[:, 1:])
    reduced_names = [name for name, zero in zip(REDUCED_NAMES[1:], reduced_zero) if not zero]
    x_r = np.column_stack([np.ones(n), reduced_std[:, ~reduced_zero]])
    rank_r, cond_r = rank_and_condition(x_r)
    added_raw = added_block(table)
    added_std, _ = standardise(added_raw)
    facts, supported = block_support(added_raw, ADDED_NAMES, group, n)
    placebo_raw = placebo_block(table)
    placebo_std, _ = standardise(placebo_raw)
    x_p = np.column_stack([x_r, placebo_std])
    rank_p, cond_p = rank_and_condition(x_p)
    folds_nonempty = [int(np.sum(fold_of_group == k)) for k in range(k_folds)]
    folds_ok = min(folds_nonempty) > 0

    primary, x_f = _block_design(x_r, added_std, supported, ADDED_NAMES, facts, MIN_SUPPORTED_PRODUCTS,
                                 COUNT_NAMES)
    n_products = len(COUNT_NAMES)
    secondary, x_q = _block_design(x_r, added_std[:, :n_products], supported[:n_products], COUNT_NAMES,
                                   facts, MIN_SUPPORTED_PRODUCTS, COUNT_NAMES)
    for block in (primary, secondary):
        if not folds_ok:
            block["reasons"].append(f"empty folds: groups per fold {folds_nonempty}")
            block["readable"] = False
    placebo_readable = rank_p - rank_r == len(PLACEBO_NAMES) and folds_ok

    design = {
        "response": "segment_mean_r (mean contract team r of the ten executed steps)",
        "reduced_columns_declared": list(REDUCED_NAMES),
        "reduced_columns_used": ["intercept"] + reduced_names,
        "reduced_columns_dropped_zero_variance": [name for name, zero in zip(REDUCED_NAMES[1:], reduced_zero) if zero],
        "reduced_note": "n_routed_t0 omitted: it equals sum_i routed_i exactly",
        "added_columns_declared": list(ADDED_NAMES),
        "added_blocks": {"label_count_products": list(COUNT_NAMES), "relay_service": list(RS_NAMES),
                         "relay_pair": list(RP_NAMES)},
        "count_contrasts": ("the 15 products n_z*n_z' (z < z'); squares are spanned by R's additive terms "
                            "and the products because n_z^2 = 6 n_z - sum_{z' != z} n_z n_z'"),
        "relay_pair_definition": "unordered pairs of distinct UAVs both relays at t0 (any paths)",
        "support_rule": SUPPORT_RULE_TEXT,
        "support_threshold": {"min_nonzero_rows": support_threshold_rows(n),
                              "min_nonzero_episodes": SUPPORT_MIN_EPISODES,
                              "min_supported_products": MIN_SUPPORTED_PRODUCTS},
        "readability_rule": READABILITY_RULE_TEXT,
        "added_support": facts,
        "full_columns_used": ["intercept"] + reduced_names + primary["columns_used"],
        "missing_support": {"unsupported": primary["unsupported"], "spanned": primary["spanned"]},
        "placebo_columns": list(PLACEBO_NAMES),
        "placebo_support": support_facts(placebo_raw, PLACEBO_NAMES, group),
        "standardisation": "non-intercept columns centred and scaled by full-table mean/SD",
        "rank": {"reduced": rank_r, "reduced_columns": int(x_r.shape[1]), "full": primary["rank"]["full"],
                 "full_columns": primary["rank"]["full_columns"],
                 "added_increment": primary["rank"]["added_increment"],
                 "added_supported_columns": primary["rank"]["added_supported_columns"],
                 "products_only_increment": secondary["rank"]["added_increment"],
                 "products_supported": primary["products_supported"],
                 "placebo_increment": rank_p - rank_r,
                 "rank_rule": "numpy.linalg.matrix_rank's SVD tolerance on the standardised design"},
        "condition_number": {"reduced": cond_r, "full": primary["condition_number_full"],
                             "products_only": secondary["condition_number_full"], "placebo": cond_p,
                             "definition": "sigma_max / sigma_min of the standardised design (inf if rank-deficient)"},
        "products_only": {key: secondary[key] for key in ("columns_used", "unsupported", "spanned",
                                                          "products_supported", "rank", "readable", "reasons")},
    }
    folds = {"k": k_folds, "groups": n_groups, "group_definition": "(lane, episode)",
             "assignment_rule": 'int.from_bytes(sha256(f"lane{lane}:episode{episode}")[:8], "big") % K',
             "assignment_sha256": assignment_hash, "groups_per_fold": folds_nonempty,
             "rows_per_fold": [int(np.sum(fold == k)) for k in range(k_folds)]}
    reading = {"schema": SCHEMA, "direction": DIRECTION, "reading_wording": READING_WORDING,
               "rows": int(n), "design": design, "folds": folds,
               "bootstrap": {"draws": int(n_boot), "seed_rule": f"numpy default_rng({boot_seed_base} + b), b = 1..{n_boot}",
                             "multiplier": "Rademacher, one per episode (sorted (lane, episode) order)",
                             "null": "y*_b = fitted_R + e * w_b[group] (R fitted on all rows)",
                             "pass_rule": "Delta > 0 and Delta > numpy.quantile(Delta*, 0.95)",
                             "refit_method": ("exact linear-algebra equivalent of refitting OLS on each y*_b: "
                                              "per fold/model one OLS solve on the (1 + G) basis {fitted_R, e_g} "
                                              "(normal equations when well conditioned, else min-norm lstsq), "
                                              "held-out residual Gram, quadratic forms")},
               "decision": None, "reason": None, "omnibus": None,
               "decision_products_only": None, "reason_products_only": None, "omnibus_products_only": None,
               "placebo": None}
    timing["design_seconds"] = time.perf_counter() - started
    if not primary["readable"]:
        reading.update(decision="unreadable", reason="; ".join(primary["reasons"]))
    if not secondary["readable"]:
        reading.update(decision_products_only="unreadable", reason_products_only="; ".join(secondary["reasons"]))
    if not (primary["readable"] or secondary["readable"]):
        reading["timing"] = timing
        return reading

    tick = time.perf_counter()
    beta_r = np.linalg.lstsq(x_r, y, rcond=None)[0]
    timing["one_fit_reduced_seconds"] = time.perf_counter() - tick
    tick = time.perf_counter()
    np.linalg.lstsq(x_f, y, rcond=None)
    timing["one_fit_full_seconds"] = time.perf_counter() - tick
    fitted = x_r @ beta_r
    residual = y - fitted
    basis = np.zeros((n, 1 + n_groups))
    basis[:, 0] = fitted
    basis[np.arange(n), 1 + group] = residual
    weights = rademacher(n_groups, n_boot, boot_seed_base)
    vectors = np.vstack([np.ones((1, n_boot + 1)), np.column_stack([np.ones(n_groups), weights.T])])

    tick = time.perf_counter()
    grams_r, sizes, ranks_r, solvers_r = fold_grams(x_r, basis, fold, k_folds)
    if primary["readable"]:
        grams_f, _, ranks_f, solvers_f = fold_grams(x_f, basis, fold, k_folds)
        omnibus = _omnibus(grams_r, grams_f, sizes, vectors, ranks_r, ranks_f, solvers_r, solvers_f)
        omnibus["reduced_fit_residual_sd"] = float(residual.std())
        reading.update(decision=omnibus["decision"], omnibus=omnibus)
        if direct_check:
            check = time.perf_counter()
            direct, _ = direct_cv_delta(x_r, x_f, y, fold, k_folds)
            timing["direct_observed_cv_seconds"] = time.perf_counter() - check
            # Floor at 1e-3 of the fold MSE: the two routes (normal equations vs gelsd) differ at
            # MSE-level rounding, which does not shrink when Delta is near zero.
            scale = max(abs(direct), float(np.mean(omnibus["mse_reduced_per_fold"])) * 1e-3, 1e-300)
            if abs(direct - omnibus["delta"]) > DIRECT_CHECK_RTOL * scale:
                raise AssertionError(f"Gram route {omnibus['delta']!r} != direct refit {direct!r}")
            omnibus["direct_refit_delta"] = direct
    if secondary["readable"]:
        grams_q, _, ranks_q, solvers_q = fold_grams(x_q, basis, fold, k_folds)
        secondary_omnibus = _omnibus(grams_r, grams_q, sizes, vectors, ranks_r, ranks_q, solvers_r, solvers_q)
        reading.update(decision_products_only=secondary_omnibus["decision"],
                       omnibus_products_only=secondary_omnibus)
    placebo = {"readable": placebo_readable, "role": "conditional diagnostic, not a veto"}
    if placebo_readable:
        grams_p, _, ranks_p, solvers_p = fold_grams(x_p, basis, fold, k_folds)
        p = _omnibus(grams_r, grams_p, sizes, vectors, ranks_r, ranks_p, solvers_r, solvers_p)
        placebo.update({key: p[key] for key in ("delta", "delta_per_fold", "null_quantile_95",
                                                "null_fraction_below_observed", "null_summary", "passed")},
                       fold_rank=ranks_p)
    reading["placebo"] = placebo
    timing["fold_fits_and_bootstrap_seconds"] = time.perf_counter() - tick
    timing["total_seconds"] = time.perf_counter() - started
    reading["timing"] = timing
    return reading


# ------------------------------------------------------------------------------ CLI


def smoke_refusal(out):
    temp_root = (ROOT / "temp").resolve()
    resolved = Path(out).resolve()
    if resolved != temp_root and temp_root not in resolved.parents:
        return f"--smoke-no-admission needs --out under {temp_root}"
    return None


def run_reader(table_path, out, *, n_boot=N_BOOT, launch_sha=None, admission=None, smoke=False):
    out = Path(out)
    if (out / "summary.json").exists():
        raise ValueError("existing summary; reconcile the original attempt")
    out.mkdir(parents=True, exist_ok=True)
    started, cpu0 = time.perf_counter(), cpu_seconds()
    table_path = Path(table_path)
    summary = {"schema": SCHEMA, "direction": DIRECTION, "kind": "p3_interaction_reading", "status": "running",
               "failure": None, "table": str(table_path), "launch_sha": launch_sha, "admission": admission,
               "smoke": bool(smoke), "bootstrap_draws": int(n_boot), "bootstrap_seed_base": BOOT_SEED_BASE}
    write_json(out / "summary.json", summary)
    try:
        meta_path = table_path.parent / "meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else None
        table_sha = file_sha256(table_path)
        summary["table_sha256"] = table_sha
        if meta is None:
            raise ValueError("meta.json is missing beside the table")
        if meta.get("table_sha256") != table_sha:
            raise ValueError("table sha256 differs from its meta.json record")
        if not smoke and meta.get("smoke"):
            raise ValueError("an admitted reading refuses a smoke table")
        reading = read_table(load_table(table_path), n_boot=n_boot)
        reading.update(table=str(table_path), table_sha256=table_sha, bootstrap_seed_base=BOOT_SEED_BASE,
                       fit_seed=meta.get("fit_seed"), checkpoint_sha256=meta.get("checkpoint_sha256"),
                       checkpoint=meta.get("checkpoint"),
                       structural_zero_check=meta.get("structural_zero_check"),
                       collection_counters=meta.get("counters"), launch_sha=launch_sha, smoke=bool(smoke))
        usage = resource.getrusage(resource.RUSAGE_SELF)
        reading["resources"] = {"wall_seconds": time.perf_counter() - started, "cpu_seconds": cpu_seconds() - cpu0,
                                "peak_rss_kib": usage.ru_maxrss, "rss_scope": "RUSAGE_SELF"}
        write_json(out / "interaction_reading.json", reading)
        summary.update(status="complete", decision=reading["decision"],
                       decision_products_only=reading["decision_products_only"],
                       reading="interaction_reading.json")
        code = 0
    except Exception as exc:
        summary.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        (out / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        code = 1
    usage = resource.getrusage(resource.RUSAGE_SELF)
    summary["resources"] = {"wall_seconds": time.perf_counter() - started,
                            "command_wall_seconds": time.perf_counter() - PROCESS_START,
                            "cpu_seconds": cpu_seconds() - cpu0, "peak_rss_kib": usage.ru_maxrss}
    write_json(out / "summary.json", summary)
    print(json.dumps({"status": summary["status"], "decision": summary.get("decision"),
                      "decision_products_only": summary.get("decision_products_only")}), flush=True)
    return code


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--table", type=Path, required=True,
                        help="commitments.npz (relative paths resolve against the checkout holding runs/)")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", default=None, help="required unless --smoke-no-admission")
    parser.add_argument("--n-boot", type=int, default=N_BOOT, help="smoke only; the admitted reading uses 1000")
    parser.add_argument("--smoke-no-admission", action="store_true",
                        help="engineering smoke only: --out under temp/")
    args = parser.parse_args(argv)
    if args.smoke_no_admission:
        refusal = smoke_refusal(args.out)
        if refusal:
            print(f"error: {refusal}", file=sys.stderr)
            return 2
        admission, launch_sha = "skipped (engineering smoke: temp output)", args.launch_sha or "smoke"
    else:
        if args.launch_sha is None:
            parser.error("--launch-sha is required for an admitted reading")
        if args.n_boot != N_BOOT:
            parser.error("the admitted reading uses 1000 bootstrap draws")
        admission = dict(require_admission(__file__, direction="coupled_host_joint_skills_stage1"))
        if args.launch_sha != admission["sha"]:
            raise ValueError("launch SHA disagrees with admission")
        launch_sha = args.launch_sha
    return run_reader(resolve_input(args.table), args.out, n_boot=args.n_boot, launch_sha=launch_sha,
                      admission=admission, smoke=args.smoke_no_admission)


if __name__ == "__main__":
    raise SystemExit(main())
