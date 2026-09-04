"""Curve measurements and the card's ordered full-panel reading rule."""

import numpy as np

from ..config import LOADS, TRAIN_SIZES

MAIN_SEEDS = (203, 211, 223)
MAIN_GRID = tuple(range(0, 257, 16))


def curve_point(update, values, oracle):
    by_n = {}
    for i, n in enumerate(TRAIN_SIZES):
        by_n[str(n)] = {
            "return": float(values[i].mean()),
            "oracle_gap": float(oracle[i].mean() - values[i].mean()),
            "by_load": {load: float(values[i, :, j].mean()) for j, load in enumerate(LOADS)},
        }
    return {
        "update": update, "return": float(values.mean()), "by_n": by_n,
        "by_load": {load: float(values[:, :, j].mean()) for j, load in enumerate(LOADS)},
        "oracle_gap": float(oracle.mean() - values.mean()),
        "evaluation_episodes": int(values.size), "evaluation_decisions": int(2 * values.size),
        "evaluation_agent_steps": int(sum(2 * n * values[i].size for i, n in enumerate(TRAIN_SIZES))),
    }


def cost_law(update_seconds, updates, evaluation_seconds, evaluations):
    u = update_seconds / updates if updates else None
    e = evaluation_seconds / evaluations if evaluations else None
    return {"seconds_per_update": u, "seconds_per_full_evaluation": e,
            "projection_formula": "2*3*(256*u_A+17*e_A)",
            "projected_main_seconds_all_three_seeds": None if u is None or e is None else 2 * 3 * (256 * u + 17 * e)}


def result_branch(deltas):
    mean = float(np.mean(deltas))
    if mean >= 0.01 and sum(d > 0 for d in deltas) >= 2:
        return "B02_METRIC_CURVE_SIGNAL"
    if mean <= -0.01 and sum(d < 0 for d in deltas) >= 2:
        return "B02_FREE_CURVE_SIGNAL"
    if abs(mean) < 0.01:
        return "B02_INSIDE_MEI"
    return "B02_MIXED_SEEDS"


def summarize(packets):
    """Offline aggregation of three published main seed summaries; never launches."""
    complete = len(packets) == 3 and sorted(p["seed"] for p in packets) == list(MAIN_SEEDS)
    for packet in packets:
        complete = complete and packet["mode"] == "main" and packet["status"] == "complete"
        for arm in ("METRIC", "FREE"):
            row = packet["arms"].get(arm, {})
            complete = complete and row.get("status") == "complete"
            complete = complete and row.get("updates") == 256
            complete = complete and [v["update"] for v in row.get("curve", [])] == list(MAIN_GRID)
    if not complete:
        return {"branch": None, "status": "incomplete_panel"}
    seeds = {}
    for packet in sorted(packets, key=lambda p: p["seed"]):
        curves = {a: np.asarray([v["return"] for v in packet["arms"][a]["curve"]]) for a in ("METRIC", "FREE")}
        auc = {a: float(np.trapz(v, MAIN_GRID) / 256.0) for a, v in curves.items()}
        contrast = curves["METRIC"] - curves["FREE"]
        seeds[str(packet["seed"])] = {
            "auc": auc, "auc_contrast": auc["METRIC"] - auc["FREE"],
            "curve_contrasts": contrast.tolist(),
            "named_budget_contrasts": {str(t): float(contrast[MAIN_GRID.index(t)]) for t in (16, 64, 256)},
            "curves": {a: packet["arms"][a]["curve"] for a in curves},
        }
    deltas = [row["auc_contrast"] for row in seeds.values()]
    mean_curves = {a: np.mean([[v["return"] for v in p["arms"][a]["curve"]] for p in packets], axis=0).tolist()
                   for a in ("METRIC", "FREE")}
    return {"status": "complete", "branch": result_branch(deltas), "by_seed": seeds,
            "auc_contrast_mean": float(np.mean(deltas)), "auc_contrast_range": [min(deltas), max(deltas)],
            "auc_contrast_sample_sd": float(np.std(deltas, ddof=1)),
            "grid": list(MAIN_GRID), "mean_curves": mean_curves,
            "mean_named_budget_contrasts": {str(t): mean_curves["METRIC"][MAIN_GRID.index(t)] - mean_curves["FREE"][MAIN_GRID.index(t)] for t in (16, 64, 256)}}
