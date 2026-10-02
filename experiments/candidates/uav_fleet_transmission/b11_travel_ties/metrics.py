"""Unchanged native endpoints, exact tie exposure, and exposed-world contrasts."""
import numpy as np
from .contract import COMPARISON_ARMS
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.metrics import (
    episode_metrics as b10_episode_metrics, COMPARISON_FIELDS, describe, paired,
)


def episode_metrics(raw):
    result=b10_episode_metrics(raw)
    records=raw["candidate_records"]
    rows=[]
    for k,step in enumerate(raw["plan_step"]):
        group=records[records["step"]==step]
        if not len(group):
            continue
        old=int(raw["plan_h_selected"][k]);new=int(raw["plan_selected_candidate"][k])
        rows.append(dict(step=int(step),base_score=float(group[0]["score"]),
            maximum_score=float(group[new]["score"]),old_h_index=old,selected_index=new,
            exact_top_candidates=int(raw["plan_top_score_mask"][k].sum()),
            minimum_travel_top_candidates=int(raw["plan_min_travel_mask"][k].sum()),
            choice_changed=bool(raw["plan_tie_changed"][k]),
            old_h_nominal_travel=float(group[old]["forecast_travel"]),
            selected_nominal_travel=float(group[new]["forecast_travel"])))
    result["tie_exposure"]=dict(scored_plans=len(rows),
        strict_above_base_top_ties=sum(r["maximum_score"]>r["base_score"] and r["exact_top_candidates"]>1 for r in rows),
        changed_choices=sum(r["choice_changed"] for r in rows),
        base_at_maximum=sum(r["maximum_score"]==r["base_score"] for r in rows),
        plans=rows,scope="same H_T decision candidates only; nominal differences are not cumulative actual savings")
    return result


def comparisons(rows):
    indexed={(r["seed"],r["arm"]):r for r in rows}
    seeds=sorted({r["seed"] for r in rows})
    if len(indexed)!=len(rows) or set(indexed)!={(s,a) for s in seeds for a in COMPARISON_ARMS}:
        raise ValueError("incomplete C/H_A/H_T exposed-world panel")
    levels={a:{f:describe([indexed[s,a][f] for s in seeds]) for f in COMPARISON_FIELDS} for a in COMPARISON_ARMS}
    contrasts={}
    for left,right in (("H_T","H_A"),("H_T","C"),("H_A","C")):
        contrasts[left+"-"+right]={f:paired([indexed[s,left][f]-indexed[s,right][f] for s in seeds],seeds)
            for f in COMPARISON_FIELDS}
    return dict(levels=levels,contrasts=contrasts,
        uncertainty="descriptive paired-world Student t95; exposed panel; df=n-1",
        timing_scope="C/H_A cost is original historical B10 measurement, not a simultaneous benchmark")
