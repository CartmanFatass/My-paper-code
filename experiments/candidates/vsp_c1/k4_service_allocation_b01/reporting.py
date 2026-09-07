"""Three paired endpoint contrasts and five-point descriptive curves; no selection."""
import json

import numpy as np


def write_read(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8"))


def auc(summary):
    updates = [row["update"] for row in summary["curve"]]
    return {d: float(np.trapz([row["period_means"][d] for row in summary["curve"]], updates)
                     / summary["budget"]["updates"]) for d in ("2", "6")}


def contrast(left, right):
    differences = {}
    for d in ("2", "6"):
        a, b = left["endpoint_episodes"][d], right["endpoint_episodes"][d]
        if [row["episode"] for row in a] != [row["episode"] for row in b]:
            raise ValueError("Contrast requires matching endpoint episode slots")
        differences[d] = np.array([x["J"] - y["J"] for x, y in zip(a, b)])
    means = {d: float(v.mean()) for d, v in differences.items()}
    mean = float(np.mean(list(means.values())))
    return {"mean": mean, "period_means": means,
            "paired_episode_differences": {d: v.tolist() for d, v in differences.items()},
            "conditional_evaluation_SE": float(0.5 * np.sqrt(sum(
                v.var(ddof=1) / len(v) for v in differences.values()))),
            "distance_to_nearest_MEI_boundary": min(abs(mean - 0.025), abs(mean + 0.025))}


def readings(delta, factor_rule=None, generic_rule=None, mei=0.025):
    """Overlapping numerical branches; uncertainty/usefulness interpretation stays with DM."""
    labels = []
    d = delta["mean"]
    if d <= -mei:
        labels.append("favors_GENERIC_this_instance")
    if min(delta["period_means"].values()) <= -mei:
        labels.append("primary_period_loss")
    if factor_rule is None or generic_rule is None:
        labels.append("rule_relative_value_unresolved")
        return labels
    f, g = factor_rule["mean"], generic_rule["mean"]
    if (d >= mei and min(delta["period_means"].values()) > -mei
            and f >= mei and min(factor_rule["period_means"].values()) > -mei):
        labels.append("local_FACTOR_gain_over_both_comparators")
    if d >= mei and f < 0 and g < 0:
        labels.append("learner_ranking_gain_both_below_rule")
    useful_rule_gain = max(f, g) >= mei
    if useful_rule_gain and d < mei:
        labels.append("local_learned_policy_usefulness_not_factorization")
    if abs(d) < mei and not useful_rule_gain:
        labels.append("no_practical_continuation_reason")
    return labels


def mean_change(left, right):
    means = {d: left["period_means"][d] - right["period_means"][d] for d in ("2", "6")}
    return {"mean": float(np.mean(list(means.values()))), "period_means": means}


def compare(factor, generic, rule=None):
    if factor["status"] != "complete" or generic["status"] != "complete":
        return {"status": "incomplete", "readings": ["no_conclusion_on_damaged_learner_dependency"]}
    budgets = [dict(s["budget"]) for s in (factor, generic)]
    for budget in budgets:
        if isinstance(budget.get("checkpoints"), (list, tuple)):
            budget["checkpoints"] = tuple(budget["checkpoints"])
    if ((factor["arm"], generic["arm"]) != ("FACTOR", "GENERIC")
            or budgets[0] != budgets[1]):
        raise ValueError("Comparison requires FACTOR/GENERIC with the same fixed budget and seed")
    delta = contrast(factor, generic)
    models = {"FACTOR": factor, "GENERIC": generic}
    curves = {arm: auc(s) for arm, s in models.items()}
    auc_delta = {d: curves["FACTOR"][d] - curves["GENERIC"][d] for d in ("2", "6")}
    result = {
        "object": "VSPC1-K4-SERVICE-ALLOCATION-B01", "seed": factor["seed"],
        "status": "learner_contrast_only", "claim_ceiling": "one paired training instance",
        "endpoint_primary": True, "MEI": 0.025,
        "contrasts": {"FACTOR-GENERIC": delta},
        "endpoint_means": {arm: s["curve"][-1] for arm, s in models.items()},
        "endpoint_episodes": {arm: s["endpoint_episodes"] for arm, s in models.items()},
        "learner_curves": {arm: s["curve"] for arm, s in models.items()},
        "initial_to_final": {arm: mean_change(s["curve"][-1], s["curve"][0]) for arm, s in models.items()},
        "auc_by_arm_period": curves,
        "auc_by_arm": {arm: float(np.mean(list(v.values()))) for arm, v in curves.items()},
        "auc_delta_by_period": auc_delta, "auc_delta": float(np.mean(list(auc_delta.values()))),
        "SE_scope": "Conditional evaluation noise of these fixed policies; no training-population interval.",
        "contrast_dependency": "E_FACTOR - E_GENERIC = Delta; three correlated contrasts, not three independent successes.",
        "precision_note": "Numerical branch flags do not resolve near-boundary uncertainty or authorize more calls. Five-point AUC is descriptive and does not resolve every transient.",
        "readings": readings(delta),
    }
    if rule is not None and rule["status"] == "complete":
        if rule["arm"] != "LQ-EXCLUDE" or rule["seed"] != factor["seed"]:
            raise ValueError("Rule must be LQ-EXCLUDE on the same seed's external tapes")
        fr, gr = contrast(factor, rule), contrast(generic, rule)
        result["contrasts"].update({"FACTOR-LQ-EXCLUDE": fr, "GENERIC-LQ-EXCLUDE": gr})
        result["endpoint_means"]["LQ-EXCLUDE"] = {
            k: rule[k] for k in ("period_means", "mean_J", "consequence_means")}
        result["endpoint_episodes"]["LQ-EXCLUDE"] = rule["endpoint_episodes"]
        result["initial_relative_to_rule"] = {arm: mean_change(s["curve"][0], rule) for arm, s in models.items()}
        result["readings"] = readings(delta, fr, gr)
        result["status"] = "complete"
    result["material_period_losses"] = {
        name: [d for d, mean in c["period_means"].items() if mean <= -0.025]
        for name, c in result["contrasts"].items()}
    return result


def publish_comparison(path, factor, generic, rule=None):
    return write_read(path, compare(factor, generic, rule))
