from __future__ import annotations

import itertools
from collections.abc import Sequence

import numpy as np
from scipy.stats import t

from .config import ARMS, SCORED_REGIMES


def summary(values: Sequence[float]) -> dict[str, object]:
    x = np.asarray(values, dtype=np.float64)
    if x.shape != (8,) or not np.all(np.isfinite(x)):
        raise RuntimeError("inference requires eight finite paired seed values")
    return {"values": x.tolist(), "n": 8, "mean": float(np.mean(x)),
            "sample_sd": float(np.std(x, ddof=1)), "standard_error": float(np.std(x, ddof=1) / np.sqrt(8.0))}


def bound(values: Sequence[float], confidence: float, side: str) -> dict[str, object]:
    facts = summary(values)
    displacement = float(t.ppf(confidence, df=7)) * float(facts["standard_error"])
    value = float(facts["mean"]) + (displacement if side == "upper" else -displacement)
    return {**facts, "df": 7, "confidence": confidence, "side": side, "bound": value}


def sign_randomization(values: Sequence[float]) -> dict[str, object]:
    x = np.asarray(values, dtype=np.float64)
    observed = float(np.mean(x))
    randomized = [float(np.mean(x * np.asarray(signs))) for signs in itertools.product((-1.0, 1.0), repeat=8)]
    return {"permutations": 256, "observed_mean": observed,
            "one_sided_positive_p": float(sum(v >= observed for v in randomized) / 256.0),
            "one_sided_negative_p": float(sum(v <= observed for v in randomized) / 256.0)}


def _contrast(seed_packets: list[dict[str, object]], name: str) -> list[float]:
    out = []
    for packet in seed_packets:
        arms = packet["audit"]["arms"]
        free, correct, shuffle = (arms[a]["by_class"] for a in ARMS)
        if name == "C_FREE": value = free["REAL"]["Dcorr"] - correct["REAL"]["Dcorr"]
        elif name == "C_SHUF": value = shuffle["REAL"]["Dcorr"] - correct["REAL"]["Dcorr"]
        elif name == "W_SHUF": value = correct["REAL"]["Dwrong"] - shuffle["REAL"]["Dwrong"]
        elif name == "P_FREE": value = free["REAL"]["Epred"] - correct["REAL"]["Epred"]
        elif name == "P_SHUF": value = shuffle["REAL"]["Epred"] - correct["REAL"]["Epred"]
        elif name == "A_FREE": value = free["REAL"]["Q"] - correct["REAL"]["Q"]
        elif name == "A_SHUF": value = shuffle["REAL"]["Q"] - correct["REAL"]["Q"]
        elif name == "ORDER": value = ((shuffle["REAL"]["Dcorr"] - correct["REAL"]["Dcorr"])
                                            - (shuffle["SHAM"]["Dcorr"] - correct["SHAM"]["Dcorr"]))
        else: raise KeyError(name)
        out.append(float(value))
    return out


def _scored(seed_packets: list[dict[str, object]]) -> dict[str, object]:
    confidence = 1.0 - 0.05 / 24.0
    members = []
    for regime in SCORED_REGIMES:
        for control in ("FREE-DIRECT", "SCDMP-ORDER-SHUFFLE"):
            reward_values, failure_values = [], []
            for packet in seed_packets:
                rows = [r for r in packet["scored_episodes"] if r["regime"] == regime
                        and r["dynamics_class"] == "REAL"]
                by_arm = {a: [r for r in rows if r["arm"] == a] for a in ("SCDMP-CORRECT", control)}
                reward_values.append(float(np.mean([r["normalized_return"] for r in by_arm["SCDMP-CORRECT"]])
                                                - np.mean([r["normalized_return"] for r in by_arm[control]])))
                failure_values.append(float(np.mean([r["failure"] for r in by_arm[control]])
                                                 - np.mean([r["failure"] for r in by_arm["SCDMP-CORRECT"]])))
            for metric, values, margin in (("reward", reward_values, -.010), ("failure", failure_values, -.040)):
                lower, upper = bound(values, confidence, "lower"), bound(values, confidence, "upper")
                members.append({"regime": regime, "control": control, "metric": metric,
                    "margin": margin, "lower": lower, "upper": upper,
                    "adverse_trigger": float(upper["bound"]) < margin,
                    "nonharm_pass": float(lower["bound"]) > margin,
                    "sign_randomization": sign_randomization(values)})
    return {"family_size": len(members), "per_estimand_confidence": confidence, "members": members,
            "any_adverse": any(x["adverse_trigger"] for x in members),
            "full_nonharm": all(x["nonharm_pass"] for x in members)}


def complete_inference(seed_packets: list[dict[str, object]]) -> dict[str, object]:
    if [p["algorithm_seed"] for p in seed_packets] != list(range(100, 108)):
        raise RuntimeError("B2 seed packet order mismatch")
    margins = {"C_FREE": .040, "C_SHUF": .040, "W_SHUF": .040, "P_FREE": .020,
               "P_SHUF": .020, "A_FREE": .004, "A_SHUF": .004, "ORDER": .020}
    contrasts = {}
    for name, margin in margins.items():
        values = _contrast(seed_packets, name)
        lower = bound(values, .95, "lower")
        upper = bound(values, .95, "upper")
        report = {"margin": margin, "lower_95": lower, "upper_95": upper,
                  "lower_gate_pass": float(lower["bound"]) > margin,
                  "upper_below_useful_margin": float(upper["bound"]) < margin,
                  "sign_randomization": sign_randomization(values)}
        if name in ("C_FREE", "P_FREE"):
            adjusted = bound(values, .975, "lower")
            report["lower_97_5"] = adjusted
            report["adjusted_free_pass"] = float(adjusted["bound"]) > margin
        contrasts[name] = report
    disagreement = {}
    for control in ("FREE-DIRECT", "SCDMP-ORDER-SHUFFLE"):
        values = [float(p["audit"]["correct_action_disagreement"][control]) for p in seed_packets]
        lower = bound(values, .95, "lower")
        disagreement[control] = {"lower_95": lower, "margin": .125,
                                 "pass": float(lower["bound"]) > .125,
                                 "sign_randomization": sign_randomization(values)}
    target_competence = {}
    for arm in ARMS:
        values = [float(p["audit"]["arms"][arm]["by_class"]["REAL"]["competence_ratio"])
                  for p in seed_packets]
        upper = bound(values, .95, "upper")
        target_competence[arm] = {"upper_95": upper, "mean_at_most_0_75": float(np.mean(values)) <= .75,
                                  "upper_below_0_90": float(upper["bound"]) < .90}
    gates = {
        "support_all_seeds": all(p["audit"]["support"]["continuous_gate_pass"] and
                                  p["audit"]["support"]["q_exact_membership_pass"] and
                                  p["structural_certificate"]["checks"]["action_support"] for p in seed_packets),
        "physical_order_all_seeds": all(p["audit"]["physical_order"]["REAL"]["median_max_score_difference_per_step"] >= .020
            and p["audit"]["physical_order"]["REAL"]["oracle_action_difference_fraction"] >= .20 for p in seed_packets),
        "sham_identity_all_seeds": all(p["audit"]["physical_order"]["SHAM"]["maximum_absolute_score_difference_per_step"] <= 1e-10
            and p["audit"]["physical_order"]["SHAM"]["oracle_actions_identical"] for p in seed_packets),
        "headroom": {arm: {"mean_fraction": float(np.mean([p["audit"]["arms"][arm]["by_class"]["REAL"]["oracle_regret_fraction_ge_0_015"] for p in seed_packets])),
                            "mean_regret": float(np.mean([p["audit"]["arms"][arm]["by_class"]["REAL"]["Q"] for p in seed_packets]))}
                     for arm in ("FREE-DIRECT", "SCDMP-ORDER-SHUFFLE")},
        "train_support_competence_all": all(p["train_support"][arm]["ratio"] <= .70 for p in seed_packets for arm in ARMS),
        "target_competence": target_competence,
        "output_health_all": all(p["audit"]["arms"][arm]["true_variance_denominators_valid"]
             and p["audit"]["arms"][arm]["F_bound_hit_fraction"] <= .02
             and all(.20 <= x <= 5.0 for x in p["audit"]["arms"][arm]["variance_ratios"].values())
             and p["audit"]["arms"][arm]["by_class"]["REAL"]["score_range_pass_fraction"] >= .90
             for p in seed_packets for arm in ARMS),
        "gradient_activity_all": all(len(p["training"]["gradient_trace"][arm]) == 1000
                                     for p in seed_packets for arm in ARMS),
    }
    for value in gates["headroom"].values():
        value["pass"] = value["mean_fraction"] >= .25 and value["mean_regret"] >= .008
    return {"contrasts": contrasts, "action_disagreement": disagreement,
            "adverse_and_nonharm": _scored(seed_packets), "gate_facts": gates,
            "scientific_interpretation": None,
            "interpretation_owner": "EM_semigroup_consistent_duration_model_policy"}
