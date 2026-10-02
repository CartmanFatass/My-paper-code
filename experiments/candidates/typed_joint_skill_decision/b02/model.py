"""Fixed float64 features and one ridge solution; no imports with numerical effects."""
from __future__ import annotations

import itertools
import math

KINDS = ("kmeans_plain", "subset_relay", "subset_flat", "flat_result_incumbent")
FEATURES = ("initial_reward", "initial_C_bh", "initial_potential_over_5000",
            *KINDS, "k_over_6", "rank_over_2", "mean_site_bs_xy_over_5000",
            "mean_user_nearest_site_xy_over_5000", "radius_gyration_xy_over_5000",
            "mean_height_minus_50_over_100", "max_matching_travel_over_5000",
            "mean_matching_travel_over_5000")
PAIRS = tuple(itertools.combinations_with_replacement(range(15), 2))
TOLERANCES = {"float64_rtol": 1e-10, "float64_atol": 1e-10,
              "position_atol_m": 1e-8, "normal_equation_relative": 1e-8,
              "normal_equation_vector_atol": 1e-8, "action_atol": 1e-12, "team_reward_atol": 1e-9,
              "source_query_path": "exact bytes under current pinned CPU/NumPy source", "rank_origin_permutation": "exact"}


def fallback(branch_reward, best_initial_reward):
    return float(branch_reward) < float(best_initial_reward) - 1e-12


def choose_rank(initial_rewards, predicted_gains):
    values = [float(a) + float(b) for a, b in zip(initial_rewards, predicted_gains)]
    if len(values) != 3 or not all(math.isfinite(x) for x in values):
        raise ValueError("three finite pre-search estimates required")
    return max(range(3), key=lambda r: (values[r], -r))


def features(candidate, rank, initial, users, bs, assign):
    """Only already-paid scores and initial geometry; `assign` is the original matching."""
    import numpy as np
    kind = candidate["kind"]
    if kind not in KINDS or rank not in range(3):
        raise ValueError("undeclared kind/rank")
    sites = np.asarray(candidate["positions_xyz"], dtype=np.float64)
    start = np.asarray(initial, dtype=np.float64)
    user = np.asarray(users, dtype=np.float64)[:, :2]
    if sites.shape != (6, 3) or start.shape != (6, 3) or user.shape != (50, 2):
        raise ValueError("fixed host geometry required")
    distances = np.linalg.norm(sites[assign(start, sites)] - start, axis=1)
    xy = sites[:, :2]
    values = [float(candidate["contract_reward"]), float(candidate["coverage_backhauled"]),
              float(candidate["potential"]) / 5000,
              *[float(kind == k) for k in KINDS],
              (0 if candidate["k"] is None else float(candidate["k"]) / 6), rank / 2,
              float(np.linalg.norm(xy - np.asarray(bs)[:2], axis=1).mean()) / 5000,
              float(np.linalg.norm(user[:, None, :] - xy[None, :, :], axis=2).min(axis=1).mean()) / 5000,
              float(np.sqrt(np.square(xy - xy.mean(axis=0)).sum(axis=1).mean())) / 5000,
              float(((sites[:, 2] - 50) / 100).mean()),
              float(distances.max()) / 5000, float(distances.mean()) / 5000]
    if len(values) != 15 or not all(math.isfinite(x) for x in values):
        raise ValueError("non-finite feature")
    return values


def expand(z):
    import numpy as np
    z = np.asarray(z, dtype=np.float64)
    return np.concatenate((z, np.stack([z[..., i] * z[..., j] for i, j in PAIRS], axis=-1)), axis=-1)


def transform(x, state):
    import numpy as np
    z = (np.asarray(x, dtype=np.float64) - state["base_mean"]) / state["base_sd"]
    q = (expand(z) - state["basis_mean"]) / state["basis_sd"]
    return np.concatenate((np.ones((*q.shape[:-1], 1), dtype=np.float64), q), axis=-1)


def predict(x, state, initial=False):
    import numpy as np
    weights = state["initial_coefficients"] if initial else state["coefficients"]
    return transform(x, state) @ np.asarray(weights, dtype=np.float64)


def fit_once(rows):
    """Called exactly once in the admitted operation; tests use only synthetic rows."""
    import numpy as np
    x = np.asarray([r["features"] for r in rows], dtype=np.float64)
    y = np.asarray([r["target_gain"] for r in rows], dtype=np.float64)
    if x.shape != (192, 15) or y.shape != (192,) or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("exactly 192 finite rows required")
    mu, sd = x.mean(axis=0), x.std(axis=0)
    sd = np.where(sd == 0, 1.0, sd)
    q = expand((x - mu) / sd)
    qm, qs = q.mean(axis=0), q.std(axis=0)
    qs = np.where(qs == 0, 1.0, qs)
    state = {"dtype": "float64", "lambda_sum_loss": 1.0, "features": list(FEATURES),
             "pairs": [list(p) for p in PAIRS], "base_mean": mu.tolist(), "base_sd": sd.tolist(),
             "basis_mean": qm.tolist(), "basis_sd": qs.tolist(), "initial_coefficients": [0.0] * 136}
    a = transform(x, state)
    penalty = np.diag([0.0] + [1.0] * 135)
    normal, rhs = a.T @ a + penalty, a.T @ y
    w = np.linalg.solve(normal, rhs)  # The sole fit/solve; never replayed by the reader.
    residual = normal @ w - rhs
    state.update(coefficients=w.tolist(), normal_equation_max_abs=float(np.max(np.abs(residual))),
                 normal_equation_residual=residual.tolist(), training_residuals=(a @ w - y).tolist(),
                 normal_equation_relative=float(np.linalg.norm(residual) / max(1.0, np.linalg.norm(rhs))),
                 normal_matrix_condition=float(np.linalg.cond(normal)),
                 movement_l2_from_zero=float(np.linalg.norm(w)),
                 training_predictions=(a @ w).tolist(), training_initial_predictions=[0.0] * 192,
                 training_mse_initial=float(np.mean(y ** 2)),
                 training_mse_final=float(np.mean((a @ w - y) ** 2)),
                 sum_loss_plus_penalty=float(np.sum((a @ w - y) ** 2) + np.sum(w[1:] ** 2)))
    state["numerically_valid"] = bool(np.isfinite(w).all() and math.isfinite(state["normal_equation_relative"])
                                     and state["normal_equation_relative"] <= TOLERANCES["normal_equation_relative"])
    # Caller persists the complete attempted solution before refusing a dependent deployment.
    return state


def archive_rows(record, assign):
    search = record["static"]["P_relay"]
    starts = search["starts"]
    if len(starts) != 3 or [s["start"] for s in starts] != [0, 1, 2]:
        raise ValueError("archive requires the original three starts")
    best_initial = starts[0]["start_reward"]
    rows = []
    for rank, s in enumerate(starts):
        c = dict(search["candidates"][s["candidate_index"]])
        h = next(h for h in search["history"] if h["stage"] == "start" and h["start"] == rank)
        c["potential"] = h["potential"]
        adjusted = best_initial if fallback(s["final_reward"], best_initial) else s["final_reward"]
        rows.append({"world": record["world"], "rank": rank, "candidate_index": c["index"],
                     "initial_candidate": c,
                     "features": features(c, rank, record["initial_positions_xyz"],
                                          record["user_positions_xy"], [2500, 2500, 30], assign),
                     "branch_final_reward": s["final_reward"], "fallback": fallback(s["final_reward"], best_initial),
                     "executable_final_reward": adjusted, "target_gain": adjusted - s["start_reward"]})
    return rows
