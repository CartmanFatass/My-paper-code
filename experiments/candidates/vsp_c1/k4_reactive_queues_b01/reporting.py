"""Primary endpoint, descriptive full curve, and conditional evaluation noise."""
import json

import numpy as np


def write_read(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8"))


def auc(summary):
    updates = np.array([row["update"] for row in summary["curve"]])
    return {d: float(np.trapz([row["period_means"][d] for row in summary["curve"]], updates)
                     / summary["budget"]["updates"]) for d in ("2", "6")}


def reading(delta, periods, mei=0.025):
    tradeoff = (delta >= mei and min(periods.values()) <= -mei) or (
        min(periods.values()) <= -mei and max(periods.values()) >= mei)
    if tradeoff:
        return "period_tradeoff"
    if delta >= mei:
        return "favorable_local_signal"
    if delta <= -mei:
        return "favors_GENERIC_this_instance"
    return "insufficient_practical_gain"


def compare(factor, generic):
    # Missing or incomparable primary data cannot be interpreted as a scientific loss.
    if factor["status"] != "complete" or generic["status"] != "complete":
        return {"status": "incomplete", "reading": "no_dependent_performance_conclusion"}
    if (factor["arm"], generic["arm"]) != ("FACTOR", "GENERIC") or factor["budget"] != generic["budget"]:
        raise ValueError("Comparison requires FACTOR/GENERIC with the same fixed budget and seed")
    differences, means = {}, {}
    for d in ("2", "6"):
        f, g = factor["endpoint_episodes"][d], generic["endpoint_episodes"][d]
        if [row["episode"] for row in f] != [row["episode"] for row in g]:
            raise ValueError("Endpoint episode slots differ")
        differences[d] = np.array([x["J"] - y["J"] for x, y in zip(f, g)])
        means[d] = float(differences[d].mean())
    delta = float(np.mean(list(means.values())))
    se = float(0.5 * np.sqrt(sum(values.var(ddof=1) / len(values) for values in differences.values())))
    curves = {"FACTOR": auc(factor), "GENERIC": auc(generic)}
    auc_differences = {d: curves["FACTOR"][d] - curves["GENERIC"][d] for d in ("2", "6")}
    return {"status": "complete", "claim_ceiling": "one paired training instance",
            "seed": factor["seed"], "delta": delta, "delta_by_period": means,
            "endpoint_arm_means": {"FACTOR": factor["curve"][-1], "GENERIC": generic["curve"][-1]},
            "paired_episode_differences": {d: values.tolist() for d, values in differences.items()},
            "conditional_evaluation_SE": se, "SE_scope": "fixed models only; no training-population interval",
            "MEI": 0.025, "distance_to_nearest_MEI_boundary": min(abs(delta - 0.025), abs(delta + 0.025)),
            "reading": reading(delta, means),
            "precision_note": "Descriptive branch only; near-boundary sampling uncertainty limits the reading. No automatic extension.",
            "auc_by_arm_period": curves, "auc_by_arm": {arm: float(np.mean(list(v.values()))) for arm, v in curves.items()},
            "auc_delta_by_period": auc_differences, "auc_delta": float(np.mean(list(auc_differences.values()))),
            "auc_reading": reading(float(np.mean(list(auc_differences.values()))), auc_differences),
            "endpoint_primary": True}
