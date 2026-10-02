"""Unchanged native endpoints and complete resource-assignment exposures."""
import numpy as np
from .contract import COMPARISON_ARMS, CONTRASTS
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.metrics import (
    episode_metrics as original_metrics, COMPARISON_FIELDS, describe, paired,
)
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.trace import CANDIDATE_DTYPE as OLD_DTYPE


def episode_metrics(raw):
    # The old endpoint reducer has a separate RF-candidate subsection. Empty that
    # view only, retain all native/user/route fields, and replace its exposure record.
    result = original_metrics(dict(raw, candidate_records=np.empty(0, dtype=OLD_DTYPE)))
    del result["assignment_exposure"]
    records = raw["candidate_records"]
    plans = []
    for k, step in enumerate(raw["plan_step"]):
        group = records[records["step"] == step]
        m = int(raw["plan_m"][k])
        if not len(group):
            continue
        selected = int(raw["plan_selected_candidate"][k])
        base = int(raw["plan_base_index"][k])
        if not 0 <= selected < len(group) or not 0 <= base < len(group):
            raise AssertionError("selected/base index outside complete group")
        new, old = group[selected], group[base]
        plans.append(dict(step=int(step), m=m, candidate_count=len(group),
            base_index=base, selected_index=selected, label_changed=selected != base,
            coordinate_alias=bool(raw["plan_selected_alias"][k]),
            base_columns=old["columns"][:m].tolist(), selected_columns=new["columns"][:m].tolist(),
            base_flight_wh=float(old["energy"]), selected_flight_wh=float(new["energy"]),
            base_sorted_slack=old["slacks"][:m].tolist(), selected_sorted_slack=new["slacks"][:m].tolist(),
            selected_member_changes=int(np.count_nonzero(old["columns"][:m] != new["columns"][:m]))))
    result["resource_assignment_exposure"] = dict(plans=plans, scored_plans=len(plans),
        sparse_fallback_plans=int(np.count_nonzero(raw["plan_fallback"] == 1)),
        changed_label_plans=sum(p["label_changed"] for p in plans),
        selected_coordinate_aliases=sum(p["coordinate_alias"] for p in plans),
        physical_intent_changes=sum(p["label_changed"] and not p["coordinate_alias"] for p in plans),
        candidate_criteria=len(records),
        scope="each arm's real decision menu; no accumulation of proxy differences as native savings")
    return result


def comparisons(rows):
    indexed = {(r["seed"], r["arm"]): r for r in rows}
    seeds = sorted({r["seed"] for r in rows})
    if len(indexed) != len(rows) or set(indexed) != {(s, a) for s in seeds for a in COMPARISON_ARMS}:
        raise ValueError("incomplete C/H/H_T/E/B exposed panel")
    levels = {a: {f: describe([indexed[s, a][f] for s in seeds]) for f in COMPARISON_FIELDS}
              for a in COMPARISON_ARMS}
    contrasts = {a + "-" + b: {f: paired([indexed[s, a][f] - indexed[s, b][f] for s in seeds], seeds)
                              for f in COMPARISON_FIELDS} for a, b in CONTRASTS}
    return dict(levels=levels, contrasts=contrasts,
        uncertainty="descriptive paired-world t95; exposed development panel; df=n-1; not confirmation",
        timing_scope="C/H/H_T timings are frozen historical observations, not simultaneous benchmarks")
