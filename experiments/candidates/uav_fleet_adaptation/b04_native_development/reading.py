"""Fixed calibration selection, exact reference reuse and complete native contrasts."""
import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.reading import METRICS as BASE_METRICS, numeric_summary, sum_counts
from .contract import BASE_ARMS, CANDIDATES, candidate_spec, evaluation_plan


METRICS = (*BASE_METRICS, "fallback_decisions", "zero_displacement_uav_ticks", "nominal_entropy_mean", "behavior_entropy_mean")
PAIRS = (("R", "S"), ("R", "Bstar"), ("R", "Q"), ("R", "C"), ("Bstar", "S"), ("Bstar", "Q"), ("Bstar", "C"), ("S", "Q"), ("Q", "C"))


def calibration_result(rows, lineage, protocol):
    selected = [r for r in rows if r["lineage"] == lineage and r["kind"] == "calibration"]
    by_key = {(r["arm"], r["world"]): r for r in selected}
    worlds = protocol.calibration_worlds(lineage)
    if len(selected) != len(CANDIDATES) * len(worlds) or len(by_key) != len(selected):
        raise ValueError("calibration must contain every declared candidate/world exactly once")
    if set(by_key) != {(candidate, world) for candidate in CANDIDATES for world in worlds}:
        raise ValueError("calibration panel identities changed")
    means = {candidate: {metric: numeric_summary([by_key[candidate, w][metric] for w in worlds])
                         for metric in METRICS} for candidate in CANDIDATES}
    winner = max(CANDIDATES, key=lambda candidate: means[candidate]["J"]["mean"])
    return {"lineage": lineage, "worlds": list(worlds), "candidate_order": list(CANDIDATES),
            "winner": winner, "means": means, "selection_metric": "mean complete-episode native J",
            "tie_rule": "first candidate in frozen order on an exact tie", "paid_episodes": len(selected),
            "scope": "reward-based discrete selection on calibration data; no holdout dominance inferred"}


def comparisons(rows, protocol, evaluations):
    results = []
    for lineage in range(2):
        selected = [r for r in rows if r["lineage"] == lineage and r["kind"] == "evaluation"]
        by_key = {(r["arm"], r["world"]): r for r in selected}
        worlds = protocol.evaluation_worlds[lineage]
        reference = evaluations[lineage]["reference_arm"]
        arms = (*BASE_ARMS, "Bstar")
        actual_arms = BASE_ARMS if evaluations[lineage]["reused"] else arms
        if len(by_key) != len(selected) or set(by_key) != {(arm, w) for arm in actual_arms for w in worlds}:
            raise ValueError("incomplete/duplicated final panel")
        lookup = {(arm, w): by_key[reference if arm == "Bstar" else arm, w] for arm in arms for w in worlds}
        means = {arm: {metric: numeric_summary([lookup[arm, w][metric] for w in worlds])
                       for metric in METRICS} for arm in arms}
        paired = {}
        for left, right in PAIRS:
            paired[left + "-" + right] = {}
            for metric in METRICS:
                difference = np.array([lookup[left, w][metric] - lookup[right, w][metric] for w in worlds], dtype=np.float64)
                paired[left + "-" + right][metric] = {
                    **numeric_summary(difference), "differences": difference.tolist(),
                    "positive": int(np.count_nonzero(difference > 0)), "negative": int(np.count_nonzero(difference < 0)),
                    "zero": int(np.count_nonzero(difference == 0))}
        shadow_rows = [by_key["R", w]["shadow"] for w in worlds]
        shadow = {k: sum(r[k] for r in shadow_rows) for k in ("rows", "requested_changes", "physical_changes", "modal_changes")}
        shadow.update(total_variation_mean=float(np.mean([r["total_variation_mean"] for r in shadow_rows])),
                      total_variation_max=max(r["total_variation_max"] for r in shadow_rows))
        results.append({"lineage": lineage, "worlds": list(worlds), "means": means, "paired": paired,
                        "calibration_reference": evaluations[lineage], "shadow": shadow,
                        "zero_service_worlds": {arm: [w for w in worlds if lookup[arm, w]["zero_service_steps"] > 0] for arm in arms},
                        "point_improvement_over_S_and_Bstar": all(paired[p]["J"]["mean"] > 0 for p in ("R-S", "R-Bstar"))})
    equal_weight = {pair: {metric: {"lineage_effects": [r["paired"][pair][metric]["mean"] for r in results],
                                   "mean": float(np.mean([r["paired"][pair][metric]["mean"] for r in results]))}
                           for metric in METRICS} for pair in (a + "-" + b for a, b in PAIRS)}
    return {"lineages": results, "equal_weight_effects": equal_weight,
            "scope": "two fixed exploratory fitted lineages; paired-world intervals conditional on each endpoint, not 64 training replications; R-S/R-Bstar do not imply R-Q/R-C; no automatic confirmation or extension"}


def cost_totals(rows, counts):
    c = sum_counts(r["policy_counts"] for r in rows if candidate_spec(r["candidate"])["family"] == "C")
    s = sum_counts(r["policy_counts"] for r in rows if candidate_spec(r["candidate"])["family"] == "S")
    native = (counts["constructor_resets"] + counts["explicit_resets"] + counts["native_steps"]) * 275
    c_links = c.get("candidate_links", 0) + c.get("setup_links", 0)
    helper_links = s.get("helper_setup_links", 0) + s.get("helper_extreme_links", 0)
    return {"full_C": c, "student": s, "native_dense_power_slots": native,
            "controller_power_links": c_links + helper_links,
            "combined_power_work": native + c_links + helper_links,
            "actor_replay_rows": counts["actor_replay_rows"], "critic_replay_rows": counts["critic_replay_rows"],
            "critic_collection_rows": counts["collected_critic_rows"], "shadow_actor_rows": counts["shadow_actor_rows"],
            "shadow_motion_ticks": counts["shadow_motion_ticks"],
            "scope": "completed actual query work, native dense slots include A2A diagonal placeholders; cache payload bytes sum separate episode caches, not simultaneous RSS; reader and engineering additional"}


def expected_order(protocol, calibrations, evaluations):
    order = []
    for lineage in range(2):
        order.extend((lineage, "training", "R", "S_T1", w, i // 2) for i, w in enumerate(protocol.training_worlds[lineage]))
    for lineage in range(2):
        for i, world in enumerate(protocol.calibration_worlds(lineage)):
            rotation = i % len(CANDIDATES)
            order.extend((lineage, "calibration", candidate, candidate, world, None)
                         for candidate in CANDIDATES[rotation:] + CANDIDATES[:rotation])
    for lineage in range(2):
        candidates = {"C": "C_0", "Q": "C_.10", "S": "S_T1", "R": "S_T1", "Bstar": calibrations[lineage]["winner"]}
        arms = BASE_ARMS if evaluations[lineage]["reused"] else (*BASE_ARMS, "Bstar")
        for i, world in enumerate(protocol.evaluation_worlds[lineage]):
            rotation = i % len(arms)
            order.extend((lineage, "evaluation", arm, candidates[arm], world, None) for arm in arms[rotation:] + arms[:rotation])
    return order


def validate_counts(batch, protocol):
    flags = tuple(not e["reused"] for e in batch["evaluations"])
    expected, actual = protocol.expected(flags), batch["actual"]
    if batch["expected_maximum"] != protocol.expected() or batch["expected_realized"] != expected:
        raise AssertionError("declared exposure envelope changed")
    for key, value in expected.items():
        if key not in ("fits", "calibrations") and actual[key] != value:
            raise AssertionError(f"actual {key}={actual[key]} differs from frozen {value}")
    if (actual["fits_started"] != 2 or actual["fits_completed"] != 2
            or actual["calibrations_started"] != 2 or actual["calibrations_completed"] != 2
            or actual["constructor_calls"] != 1 or actual["constructors"] != 1 or actual["constructor_resets"] != 1
            or actual["explicit_reset_calls"] != expected["complete_episodes"]
            or actual["explicit_resets"] != expected["complete_episodes"]
            or actual["native_step_calls"] != expected["native_steps"]):
        raise AssertionError("fit/calibration/reset/call counts changed")
    found = [(r["lineage"], r["kind"], r["arm"], r["candidate"], r["world"], r["group"]) for r in batch["rows"]]
    if found != expected_order(protocol, batch["calibrations"], batch["evaluations"]):
        raise AssertionError("stage/lineage/arm/world order changed")
    costs = cost_totals(batch["rows"], actual)
    if costs != batch["costs"]:
        raise AssertionError("query/model work not counted exactly once")
    decisions = protocol.horizon // 4 * 5
    if costs["full_C"].get("requests", 0) + costs["student"].get("requests", 0) != expected["complete_episodes"] * decisions:
        raise AssertionError("policy requests missing or duplicated")
    for family, key in (("C", "full_C"), ("S", "student")):
        sampled = sum(decisions for r in batch["rows"] if candidate_spec(r["candidate"])["family"] == family
                      and ((candidate_spec(r["candidate"])["epsilon"] > 0) if family == "C" else candidate_spec(r["candidate"])["temperature"] is not None))
        if costs[key].get("sampled_draws", 0) != sampled:
            raise AssertionError("fresh private draws changed")
