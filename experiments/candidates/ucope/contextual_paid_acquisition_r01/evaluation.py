"""Explicit held-out finite enumeration; never invoked by import or current CLI."""
from __future__ import annotations
from fractions import Fraction
from pathlib import Path
from typing import Any
from .checkpoint import load_checkpoint
from .contract import K_TEST, SEED_SLOTS, as_fraction, context_id, contexts, fraction_json
from .model import build_shared_model, displayed_belief, feature_vector, validate_shared_model
from .oracle import construct_flip_certificate, direct_probe_value, expected_tail_value, informed_value, joint_count_probability, optimal_tail
from .schema import SeedEvaluation

def _torch():
    try: import torch
    except ImportError as exc: raise RuntimeError("evaluation requires PyTorch") from exc
    return torch

def _score(model: Any, scorer: str, features) -> list[float]:
    torch=_torch()
    with torch.no_grad():
        tensor=torch.tensor(features,dtype=torch.float32)
        values=model.score_root(tensor) if scorer=="root" else model.score_tail(tensor)
    return [float(v) for v in values.cpu().tolist()]

def audit_discrete_policy(root_selected_actions: dict[str,str], tail_selected_periods: dict[str,dict[str,int]]) -> dict[str,Any]:
    """Recompute exact external values solely from a finite discrete held-out policy."""
    certificate=construct_flip_certificate(); oracle_vector={cell.context_id:cell.test_action for cell in certificate.cells}
    context_keys={context_id(c) for c in contexts()}
    if set(root_selected_actions)!=context_keys or set(tail_selected_periods)!=context_keys: raise ValueError("policy context inventory mismatch")
    actions={}; evidence={}; agreements={}; regrets=[]
    for context in contexts():
        cell=context_id(context); root=root_selected_actions[cell]
        if root not in {"PROBE",*(f"IMMEDIATE:{k}" for k in K_TEST)}: raise ValueError("invalid root policy action")
        tail_policy=tail_selected_periods[cell]
        if set(tail_policy)!={str(n) for n in range(7)} or any(type(k) is not int or k not in K_TEST for k in tail_policy.values()): raise ValueError("invalid tail policy")
        p=as_fraction(context["reliability"]); cost=as_fraction(context["total_cost"])
        learned_tail=agreement=Fraction(0)
        for count in range(7):
            belief=displayed_belief(context["link"],p,count); k=tail_policy[str(count)]
            mass=joint_count_probability("SHORT",p,count)+joint_count_probability("LONG",p,count)
            learned_tail += mass*expected_tail_value(k,belief)
            if k==optimal_tail(K_TEST,belief)[0]: agreement+=mass
        B=optimal_tail(K_TEST,Fraction(1,2))[1]; D=direct_probe_value(cost); A0=B+D; A=learned_tail+D; I=A-A0; Gamma=A-B
        oracle_tail=informed_value(p,K_TEST) if context["link"]=="LINKED" else B
        V_star=max(B,oracle_tail+D)
        J=A if root=="PROBE" else expected_tail_value(int(root.split(":")[1]),Fraction(1,2))
        G=J-B; regret=V_star-J; actions[cell]="PROBE" if root=="PROBE" else "IMMEDIATE"; agreements[cell]=agreement; regrets.append(regret)
        evidence[cell]={name:fraction_json(value) for name,value in {"B":B,"A0":A0,"A":A,"I":I,"D":D,"Gamma":Gamma,"J":J,"G":G,"V_star":V_star,"regret":regret,"tail_agreement":agreement}.items()}
    target="LINKED-p17_20-c9_100"
    specificity=min(
        as_fraction(evidence[target]["A"])-as_fraction(evidence[target]["B"]),
        *(as_fraction(evidence[cell]["B"])-as_fraction(evidence[cell]["A"]) for cell in evidence if cell!=target),
    )
    return {"oracle_action_vector":oracle_vector,"action_vector":actions,"cell_evidence":evidence,
        "cell_tail_agreement":{k:float(v) for k,v in agreements.items()},"max_regret":float(max(regrets)),
        "forced_probe_tail_agreement":float(min(agreements.values())),"target_flip":actions==oracle_vector,"minimum_seed_signed_specificity":fraction_json(specificity)}

def evaluate_heldout_cells(model_or_checkpoint: Any, seed_slot: str|None=None, *, test_only: bool=False) -> SeedEvaluation:
    if isinstance(model_or_checkpoint,(str,Path)):
        raw=load_checkpoint(model_or_checkpoint)
        if raw["completed_batches"]==0 or raw["completed_batches"]!=raw["total_batches"]: raise ValueError("complete checkpoint required")
        seed,checkpoint_record,eligible=raw["seed_slot"],{k:raw[k] for k in raw if k not in ("model_state","optimizer_state")},raw["mode"]=="PRODUCTION"; model=build_shared_model(seed); model.load_state_dict(raw["model_state"],strict=True)
    else:
        if not test_only: raise ValueError("in-memory evaluation is TEST_ONLY and result-ineligible")
        if seed_slot not in SEED_SLOTS: raise ValueError("explicit frozen seed required")
        seed,checkpoint_record,eligible=seed_slot,{"mode":"TEST_ONLY","seed_slot":seed_slot},False; model=model_or_checkpoint
    validate_shared_model(model); model.eval(); root_selected={}; tail_selected={}; root_scores={}; tail_scores={}; root_margins=[]; tail_margins=[]; root_unique=tail_unique=True
    for context in contexts():
        cell=context_id(context); labels=["PROBE",*(f"IMMEDIATE:{k}" for k in K_TEST)]
        features=[feature_vector(context,action_is_probe=True,period=0)]+[feature_vector(context,action_is_probe=False,period=k) for k in K_TEST]
        score_values=_score(model,"root",features); root_scores[cell]=dict(zip(labels,score_values)); ranking=sorted(zip(score_values,labels),key=lambda x:x[0],reverse=True); root_unique &= ranking[0][0]!=ranking[1][0]; root_margins.append(ranking[0][0]-ranking[1][0]); root_selected[cell]=ranking[0][1]
        p=as_fraction(context["reliability"]); tail_selected[cell]={}; tail_scores[cell]={}
        for count in range(7):
            belief=displayed_belief(context["link"],p,count); score_values=_score(model,"tail",[feature_vector(context,belief_short=belief,action_is_probe=False,period=k) for k in K_TEST]); tail_scores[cell][str(count)]={str(k):v for k,v in zip(K_TEST,score_values)}; ranking=sorted(zip(score_values,K_TEST),key=lambda x:x[0],reverse=True)
            tail_unique &= ranking[0][0]!=ranking[1][0]; tail_margins.append(ranking[0][0]-ranking[1][0]); tail_selected[cell][str(count)]=ranking[0][1]
    audit=audit_discrete_policy(root_selected,tail_selected)
    return SeedEvaluation(seed,checkpoint_record,eligible,audit["action_vector"],root_selected,tail_selected,root_scores,tail_scores,audit["cell_evidence"],audit["oracle_action_vector"],audit["max_regret"],audit["forced_probe_tail_agreement"],audit["cell_tail_agreement"],root_unique,min(root_margins),tail_unique,min(tail_margins),audit["target_flip"],audit["minimum_seed_signed_specificity"])

def validate_competence(evaluations) -> dict[str,Any]:
    if len(evaluations)!=10 or {e.seed_slot for e in evaluations}!=set(SEED_SLOTS): raise ValueError("competence requires ten frozen seeds")
    certificate=construct_flip_certificate(); oracle_vector={c.context_id:c.test_action for c in certificate.cells}; competent={}
    for item in evaluations:
        audit=audit_discrete_policy(item.root_selected_actions,item.tail_selected_periods)
        competent[item.seed_slot]=bool(item.oracle_action_vector==oracle_vector and item.action_vector==oracle_vector and item.action_vector==audit["action_vector"] and item.cell_evidence==audit["cell_evidence"] and item.root_unique and item.tail_unique and item.min_root_margin>0 and item.min_tail_margin>0 and audit["max_regret"]<=.02 and audit["forced_probe_tail_agreement"]>=.95)
    count=sum(competent.values()); return {"competent_seed_count":count,"competence_pass":count>=9,"per_seed":{s:competent[s] for s in SEED_SLOTS}}
