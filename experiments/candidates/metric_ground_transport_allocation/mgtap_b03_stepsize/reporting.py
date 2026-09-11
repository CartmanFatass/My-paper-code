"""B03 global development-panel selection and ordered result rule."""

import numpy as np

from ..config import LOADS, TRAIN_SIZES
from ..mgtap_b02_curves.reporting import MAIN_GRID

MAIN_SEEDS = (307, 311, 313)
RATES = (0.1, 0.3, 1.0, 3.0)
ARMS = ("METRIC", "FREE")


def auc_summary(curve):
    grid = [p["update"] for p in curve]
    def area(values):
        return float(np.trapz(values, grid) / grid[-1])
    return {
        "return": area([p["return"] for p in curve]),
        "by_load": {load: area([p["by_load"][load] for p in curve]) for load in LOADS},
        "by_n": {str(n): {
            "return": area([p["by_n"][str(n)]["return"] for p in curve]),
            "by_load": {load: area([p["by_n"][str(n)]["by_load"][load] for p in curve])
                        for load in LOADS}} for n in TRAIN_SIZES},
    }


def statistics(values):
    return {"values": list(values), "mean": float(np.mean(values)),
            "range": [min(values), max(values)], "sample_sd": float(np.std(values, ddof=1))}


def result_branch(deltas):
    mean = float(np.mean(deltas))
    if mean >= 0.01 and sum(d > 0 for d in deltas) >= 2:
        return "B03_METRIC_RESIDUAL_SIGNAL"
    if mean <= -0.01 and sum(d < 0 for d in deltas) >= 2:
        return "B03_FREE_SELECTED_SIGNAL"
    if abs(mean) < 0.01:
        return "B03_SELECTED_INSIDE_MEI"
    return "B03_MIXED_SEEDS"


def summarize(packets):
    """Publish complete main panels only; retain all configurations and seed values."""
    complete = len(packets) == 3 and sorted(p["seed"] for p in packets) == list(MAIN_SEEDS)
    for packet in packets:
        complete = complete and packet["mode"] == "main" and packet["status"] == "complete"
        for arm in ARMS:
            for rate in RATES:
                row = packet["arms"].get(arm, {}).get(str(rate), {})
                complete = complete and row.get("status") == "complete" and row.get("updates") == 256
                complete = complete and [p["update"] for p in row.get("curve", [])] == list(MAIN_GRID)
    if not complete:
        return {"branch": None, "status": "incomplete_panel"}
    packets = sorted(packets, key=lambda p: p["seed"])
    auc = {arm: {str(rate): [auc_summary(p["arms"][arm][str(rate)]["curve"])
                           for p in packets] for rate in RATES} for arm in ARMS}
    means = {a: {r: float(np.mean([v["return"] for v in rows])) for r, rows in rates.items()}
             for a, rates in auc.items()}
    if not all(np.isfinite(value) for rates in means.values() for value in rates.values()):
        return {"branch": None, "status": "nonfinite_measurements"}
    selected = {a: min(RATES, key=lambda r: (-means[a][str(r)], r)) for a in ARMS}
    def values(arm, rate):
        return np.asarray([v["return"] for v in auc[arm][str(rate)]])
    metric, free = (values(a, selected[a]) for a in ARMS)
    anchor_metric, anchor_free = (values(a, 0.1) for a in ARMS)
    deltas = (metric - free).tolist()
    by_seed = {str(p["seed"]): {
        "selected_auc_contrast": deltas[i],
        "anchor_auc_contrast": float(anchor_metric[i] - anchor_free[i]),
        "H": float(free[i] - anchor_metric[i]),
        "auc": {a: {r: rows[i] for r, rows in rates.items()} for a, rates in auc.items()},
        "arms": p["arms"], "oracle": p["oracle"], "launch_sha": p["launch_sha"],
        "source_summary": p["output_root"] + "/summary.json",
    } for i, p in enumerate(packets)}
    free_curves = [[v["return"] for v in p["arms"]["FREE"][str(selected["FREE"])]["curve"]]
                   for p in packets]
    gaps = [[p["oracle"]["return"] - v for v in curve] for p, curve in zip(packets, free_curves)]
    count_keys = ("updates", "training_decisions", "training_agent_steps", "evaluation_episodes",
                  "evaluation_decisions", "evaluation_agent_steps")
    return {
        "status": "complete", "branch": result_branch(deltas), "by_seed": by_seed,
        "selected_rates": selected, "mean_auc": means,
        "edge_of_grid_winner": {a: selected[a] in (RATES[0], RATES[-1]) for a in ARMS},
        "selection_exposure": {"configurations_per_actor": 4, "seeds_per_configuration": 3,
                               "fits": 24, "same_panel_selection": True},
        "selected_auc_contrast": statistics(deltas),
        "anchor_auc_contrast": statistics((anchor_metric - anchor_free).tolist()),
        "selection_gain": {a: statistics((values(a, selected[a]) - values(a, 0.1)).tolist()) for a in ARMS},
        "H": statistics((free - anchor_metric).tolist()), "grid": list(MAIN_GRID),
        "selected_free_mean_curve": np.mean(free_curves, axis=0).tolist(),
        "selected_free_oracle_gap_curve": np.mean(gaps, axis=0).tolist(),
        "selected_free_endpoint_headroom": statistics([g[-1] for g in gaps]),
        "counts": {key: sum(p["arms"][a][str(r)][key] for p in packets for a in ARMS for r in RATES)
                   for key in count_keys},
        "budget": {"shared_setup_seconds": sum(p["shared_setup_seconds"] for p in packets),
                   "configuration_wall_seconds": {a: {str(r): sum(p["arms"][a][str(r)]["wall_seconds"]
                       for p in packets) for r in RATES} for a in ARMS}},
    }
