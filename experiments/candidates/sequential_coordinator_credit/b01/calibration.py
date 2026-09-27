"""Host-matched calibration sweep (``calibrate``): single-removal statistics, no training.

For each of the 12 configurations and each policy (``uniform`` over allowed labels; ``greedy``:
argmax_z of the noise-averaged R per context, ties to the lowest joint index), statistics are
pi-weighted exact expectations over the 16 contexts of ``CALIBRATION_SEED``'s stream, the
context's fixed evaluation noise draws (32 when sigma > 0, one otherwise) and all joints.

``D_i = R(x, z) - R(x, z with z_i := IDLE)`` for active agents (label != IDLE):
S1 = mean over samples with R > 0 of sum_i D_i / R; S2 = mean |D| over RELAY agents / mean |D|
over other active agents; S3 = fraction of active agent-samples with |D_i| / max_z R(x, z) < .01
(max over joints under the same noise draw); S4 = sum |D| over RELAY agents / sum |D| over all
active agents.  Delta = sum_k ((S_k - target_k) / scale_k)^2.  Pairwise: for active pairs,
(P_ij - D_i - D_j) / R over samples with R > 0, P_ij = R - R(z_i, z_j := IDLE), split by the
pair's labels (RELAY-SERVE, SERVE-SERVE, and RELAY-RELAY where it occurs).
"""

from __future__ import annotations

from itertools import combinations
from pathlib import Path

import numpy as np

from .chain_bandit import (
    BINDING_CORNER,
    CONFIGURATIONS,
    IDLE,
    JOINTS,
    K,
    N_JOINTS,
    RELAY,
    effective_labels,
    greedy_joints,
    joint_probs,
    make_contexts,
    masked_softmax,
    prefix_mask,
    reward_table,
    with_idle,
)

CALIBRATION_SEED = 1
POLICIES = ("uniform", "greedy")
TARGETS = {"S1": 0.40, "S2": 3.4, "S3": 0.37, "S4": 0.70}
SCALES = {"S1": 0.1, "S2": 1.0, "S3": 0.1, "S4": 0.1}
SPARSITY_THRESHOLD = 0.01
PAIR_CLASSES = ("relay_serve", "serve_serve", "relay_relay")


def _ratio(num: float, den: float):
    return float(num / den) if den > 0 else None


def policy_joint_weights(contexts, policy: str, r_bar: np.ndarray) -> np.ndarray:
    if policy == "uniform":
        P = masked_softmax(np.zeros((contexts.n, 85, 4)), prefix_mask(contexts.mask))
        return joint_probs(P)
    if policy == "greedy":
        out = np.zeros((contexts.n, N_JOINTS))
        out[np.arange(contexts.n), greedy_joints(r_bar)] = 1.0
        return out
    raise ValueError(policy)


def removal_statistics(rtab: np.ndarray, pj: np.ndarray, mask: np.ndarray) -> dict:
    """rtab (n, S, 256) under each noise draw; pj (n, 256) joint weights of the policy."""
    n, S, _ = rtab.shape
    w = np.broadcast_to(pj[:, None, :] / (n * S), rtab.shape)
    eff = effective_labels(JOINTS, mask)                                         # (256, K)
    active = (eff != IDLE)[None, None]
    relay = (eff == RELAY)[None, None]
    other = active & ~relay
    D = np.stack([rtab - rtab[..., with_idle(np.arange(N_JOINTS), i)] for i in range(K)], -1)
    absD = np.abs(D)
    positive = rtab > 0
    safe_R = np.where(positive, rtab, 1.0)
    w_pos = w * positive
    s1 = _ratio((w_pos * (D * active).sum(-1) / safe_R).sum(), w_pos.sum())
    relay_mean = _ratio((w[..., None] * absD * relay).sum(), (w[..., None] * relay).sum())
    other_mean = _ratio((w[..., None] * absD * other).sum(), (w[..., None] * other).sum())
    s2 = (_ratio(relay_mean, other_mean) if relay_mean is not None and other_mean is not None
          else None)
    max_r = rtab.max(axis=-1, keepdims=True)[..., None]                          # (n, S, 1, 1)
    sparse = (absD / max_r) < SPARSITY_THRESHOLD
    s3 = _ratio((w[..., None] * (sparse & active)).sum(), (w[..., None] * active).sum())
    s4 = _ratio((w[..., None] * absD * relay).sum(), (w[..., None] * absD * active).sum())
    pairs = {name: {"num": 0.0, "den": 0.0} for name in PAIR_CLASSES}
    for i, j in combinations(range(K), 2):
        both = (eff[:, i] != IDLE) & (eff[:, j] != IDLE)
        r_i, r_j = eff[:, i] == RELAY, eff[:, j] == RELAY
        classes = {"relay_serve": both & (r_i ^ r_j), "serve_serve": both & ~r_i & ~r_j,
                   "relay_relay": both & r_i & r_j}
        P_ij = rtab - rtab[..., with_idle(np.arange(N_JOINTS), (i, j))]
        comp = (P_ij - D[..., i] - D[..., j]) / safe_R
        for name, members in classes.items():
            weight = w_pos * members[None, None]
            pairs[name]["num"] += float((weight * comp).sum())
            pairs[name]["den"] += float(weight.sum())
    pairwise = {name: {"mean_complementarity": _ratio(v["num"], v["den"]),
                       "pair_mass": v["den"]} for name, v in pairs.items()}
    return {"S1": s1, "S2": s2, "S3": s3, "S4": s4,
            "relay_abs_D_mean": relay_mean, "other_abs_D_mean": other_mean,
            "pairwise": pairwise}


def distance(stats: dict) -> tuple[float | None, dict]:
    residuals = {}
    total = 0.0
    defined = True
    for key, target in TARGETS.items():
        value = stats[key]
        if value is None:
            residuals[key] = {"value": None, "difference": None, "scaled_squared": None}
            defined = False
            continue
        scaled = ((value - target) / SCALES[key]) ** 2
        residuals[key] = {"value": value, "difference": value - target,
                          "scaled_squared": scaled}
        total += scaled
    return (total if defined else None), residuals


def calibration_sweep(seed: int = CALIBRATION_SEED) -> dict:
    """The full table, the argmin per policy (ties to the lowest config index), residuals."""
    rows = []
    for index, config in enumerate(CONFIGURATIONS):
        contexts, _ = make_contexts(index, seed)
        rtab = reward_table(contexts.eval_demands(), contexts.q, contexts.mask, contexts.b0)
        r_bar = rtab.mean(axis=1)
        for policy in POLICIES:
            pj = policy_joint_weights(contexts, policy, r_bar)
            stats = removal_statistics(rtab, pj, contexts.mask)
            delta, residuals = distance(stats)
            rows.append({"config_index": index, **config.record(), "policy": policy,
                         "noise_draws": int(rtab.shape[1]), **stats, "delta": delta,
                         "residuals": residuals,
                         "is_binding_corner": config.key == BINDING_CORNER})
    argmins = {}
    for policy in POLICIES:
        candidates = [row for row in rows if row["policy"] == policy and row["delta"] is not None]
        if not candidates:
            argmins[policy] = None
            continue
        best = min(candidates, key=lambda row: (row["delta"], row["config_index"]))
        argmins[policy] = {"config_index": best["config_index"],
                           "beta": best["beta"], "s": best["s"], "sigma": best["sigma"],
                           "delta": best["delta"], "residuals": best["residuals"],
                           "is_binding_corner": best["is_binding_corner"]}
    return {"seed": int(seed), "targets": TARGETS, "scales": SCALES, "table": rows,
            "argmin": argmins,
            "pairwise": {f"{row['config_index']}:{row['policy']}": row["pairwise"]
                         for row in rows}}


def run_calibrate(*, out: Path, launch_sha: str, argv=None, seed: int = CALIBRATION_SEED) -> dict:
    """``calibrate`` phase: writes ``<out>/calibrate/{config.json, summary.json, progress.jsonl}``."""
    from .first_cell import base_config, finish, git_head, prepare_root, progress, sha256_file, \
        write_json
    import sys
    import time

    root = prepare_root(Path(out) / "calibrate")
    started = time.perf_counter()
    config = {**base_config(), "object_id": OBJECT_ID_CALIBRATE, "phase": "calibrate",
              "launch_sha": launch_sha, "git_head": git_head(),
              "argv": list(sys.argv if argv is None else argv), "calibration_seed": int(seed),
              "calibration_policies": list(POLICIES), "targets": TARGETS, "scales": SCALES,
              "sparsity_threshold": SPARSITY_THRESHOLD}
    write_json(root / "config.json", config)
    summary = {"object_id": OBJECT_ID_CALIBRATE, "phase": "calibrate", "status": "INCOMPLETE",
               "failure": None, "launch_sha": launch_sha,
               "counts": {"configurations": len(CONFIGURATIONS), "policies": len(POLICIES),
                          "started_trainings": 0},
               "artifacts": {"config.json": sha256_file(root / "config.json")}}
    write_json(root / "summary.json", summary)
    progress(root, {"event": "run_start", "phase": "calibrate"})
    try:
        summary.update(calibration_sweep(seed))
        summary["status"] = "COMPLETE"
        return summary
    except Exception as exc:
        summary["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        finish(root, summary, started)


OBJECT_ID_CALIBRATE = "SEQUENTIAL-COORDINATOR-CREDIT-B01-CALIBRATE"
