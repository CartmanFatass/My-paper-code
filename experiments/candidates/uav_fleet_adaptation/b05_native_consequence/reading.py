"""Complete endpoints, paired contrasts and honest acquisition/verification work."""
import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.reading import METRICS as BASE_METRICS, numeric_summary, sum_counts
from .contract import ARMS, HEADS, WINNERS, evaluation_arms


METRICS = (*BASE_METRICS, "fallback_decisions", "zero_displacement_uav_ticks",
           "nominal_entropy_mean", "behavior_entropy_mean")
PAIRS = (("CONT", "S"), ("CONT", "CAL"), ("CONT", "Bstar"), ("CAL", "S"), ("CAL", "Bstar"),
         ("CONT", "Q"), ("CONT", "C"), ("CAL", "Q"), ("CAL", "C"), ("S", "Q"),
         ("Bstar", "S"), ("Bstar", "Q"), ("Bstar", "C"), ("Q", "C"))


def comparisons(rows, protocol):
    lineages = []
    for lineage in range(2):
        final = [r for r in rows if r["kind"] == "evaluation" and r["lineage"] == lineage]
        by_key = {(r["arm"], r["world"]): r for r in final}
        worlds = protocol.evaluation_worlds[lineage]
        if len(by_key) != len(final) or set(by_key) != {(arm, w) for arm in evaluation_arms(lineage) for w in worlds}:
            raise AssertionError("every fixed final program/world is required exactly once")
        lookup = {(arm, w): by_key["S" if lineage == 1 and arm == "Bstar" else arm, w]
                  for arm in ARMS for w in worlds}
        means = {arm: {metric: numeric_summary([lookup[arm, w][metric] for w in worlds])
                       for metric in METRICS} for arm in ARMS}
        paired = {}
        for left, right in PAIRS:
            paired[left + "-" + right] = {}
            for metric in METRICS:
                delta = np.array([lookup[left, w][metric] - lookup[right, w][metric] for w in worlds])
                paired[left + "-" + right][metric] = {
                    **numeric_summary(delta), "differences": delta.tolist(),
                    "positive": int(np.count_nonzero(delta > 0)), "negative": int(np.count_nonzero(delta < 0)),
                    "zero": int(np.count_nonzero(delta == 0)),
                }
        shadows = {}
        for arm in HEADS:
            values = [lookup[arm, w]["shadow"] for w in worlds]
            shadows[arm] = {k: sum(r[k] for r in values)
                            for k in ("rows", "requested_changes", "physical_changes", "modal_changes")}
            shadows[arm].update(total_variation_mean=float(np.mean([r["total_variation_mean"] for r in values])),
                                total_variation_max=max(r["total_variation_max"] for r in values))
        lineages.append(dict(lineage=lineage, worlds=list(worlds), means=means, paired=paired, shadow=shadows,
                             Bstar=dict(winner=WINNERS[lineage], reused=lineage == 1,
                                        reference_arm="S" if lineage == 1 else "Bstar"),
                             per_world=[{k: r[k] for k in ("arm", "world", *METRICS)} for r in final]))
    return dict(lineages=lineages,
                equal_weight_effects={a + "-" + b: {m: {
                    "lineage_effects": [r["paired"][a + "-" + b][m]["mean"] for r in lineages],
                    "mean": float(np.mean([r["paired"][a + "-" + b][m]["mean"] for r in lineages])),
                } for m in METRICS} for a, b in PAIRS},
                scope="two fixed exploratory inherited lineages; conditional paired-world t95 only, no training-population inference, equivalence or automatic adoption")


def cost_totals(rows, counts):
    c = sum_counts(r["policy_counts"] for r in rows if r["arm"] in ("C", "Q"))
    s = sum_counts(r["policy_counts"] for r in rows if r["arm"] not in ("C", "Q"))
    native = (counts["constructor_resets"] + counts["explicit_resets"] + counts["native_steps"]) * 275
    c_links = c.get("candidate_links", 0) + c.get("setup_links", 0)
    s_links = s.get("helper_setup_links", 0) + s.get("helper_extreme_links", 0)
    return dict(full_C=c, student=s, native_dense_power_slots=native, controller_power_links=c_links + s_links,
                combined_power_work=native + c_links + s_links, head_optimizer_steps=counts["head_optimizer_steps"],
                head_training_rows=counts["head_training_rows"], intervention_draws=counts["intervention_draws"],
                shadow_decisions=counts["shadow_decisions"], shadow_motion_ticks=counts["shadow_motion_ticks"],
                scope="actual completed calls; native dense slots include A2A placeholders; separate episode-cache bytes are not concurrent RSS; reader and support additional")


def expected_order(protocol):
    order = []
    for lineage in range(2):
        order.extend((lineage, "acquisition", "S", world, branch)
                     for world in protocol.acquisition_worlds[lineage] for branch in ("a", "b"))
    for lineage in range(2):
        arms = evaluation_arms(lineage)
        for wi, world in enumerate(protocol.evaluation_worlds[lineage]):
            r = wi % len(arms)
            order.extend((lineage, "evaluation", arm, world, None) for arm in arms[r:] + arms[:r])
    return order


def validate_counts(batch, protocol):
    e, actual = protocol.expected(), batch["actual"]
    if batch["expected"] != e:
        raise AssertionError("declared B05 exposure changed")
    for key in ("acquisition_contexts", "acquisition_episodes", "evaluation_episodes", "complete_episodes",
                "native_steps", "acquisition_native_steps", "evaluation_native_steps", "head_optimizer_steps",
                "head_training_rows", "intervention_draws", "shadow_decisions", "shadow_motion_ticks",
                "new_calibrations", "critic_rows", "expert_labels"):
        if actual[key] != e[key]:
            raise AssertionError(f"actual {key}={actual[key]} differs from {e[key]}")
    if any(actual[k] != 4 for k in ("head_fits_started", "head_fits_completed")):
        raise AssertionError("four actual head fits required")
    if any(actual[k] != 1 for k in ("constructor_calls", "constructors", "constructor_resets")):
        raise AssertionError("exactly one native constructor/reset required")
    if (actual["explicit_reset_calls"] != e["complete_episodes"]
            or actual["explicit_resets"] != e["complete_episodes"] or actual["native_step_calls"] != e["native_steps"]):
        raise AssertionError("native calls were missing or repeated")
    found = [(r["lineage"], r["kind"], r["arm"], r["world"],
              r["intervention"]["branch"] if r["intervention"] is not None else None) for r in batch["rows"]]
    if found != expected_order(protocol):
        raise AssertionError("collection order/pair branch identity changed")
    cost = cost_totals(batch["rows"], actual)
    if cost != batch["costs"]:
        raise AssertionError("saved computation reduction changed")
    if cost["full_C"].get("requests", 0) != e["ordinary_requests"] or cost["student"].get("requests", 0) != e["student_requests"]:
        raise AssertionError("policy request count changed")
    if cost["student"]["sampled_draws"] != e["student_requests"] or cost["full_C"]["sampled_draws"] != e["ordinary_requests"] // 2:
        raise AssertionError("original private innovation count changed")


def acquisition_summary(data):
    delta = data["delta_j"]
    return dict(contexts=len(delta), delta_j=numeric_summary(delta),
                positive=int(np.count_nonzero(delta > 0)), negative=int(np.count_nonzero(delta < 0)),
                zero=int(np.count_nonzero(delta == 0)), equal_categories=int(np.count_nonzero(data["action_a"] == data["action_b"])),
                mu_min=float(data["mu"].min()), mu_max=float(data["mu"].max()),
                weight_sum=float(data["weight"].sum()), weight_min=float(data["weight"].min()),
                weight_max=float(data["weight"].max()),
                scope="one pair per world/address, with equal/aliased/zero consequences retained; no iid claim for repeated minibatches")
