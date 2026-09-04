"""Fail-closed, atomic, complete-only BELIEF result publication."""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
from typing import Any,Mapping
import math,os,tempfile
from .analysis import analyze_acquisition
from .checkpoint import CHECKPOINT_FORMAT
from .contract import (
    CONTRACT_ID,
    FEATURE_NAMES,
    K_TEST,
    K_TRAIN,
    MODEL_SPEC,
    OPTIMIZER_SPEC,
    PRODUCTION_MODE,
    SCHEMA_VERSION,
    SEED_SLOTS,
    context_id,
    contexts,
    default_manifest,
)
from .evaluation import audit_discrete_policy
from .rng import rng_contract
from .schema import BeliefResult,SeedEvaluation,canonical_bytes
RESULT_FORMAT="UCOPE_CPA_COMPLETE_BELIEF_RESULT_V2"

def _checkpoint_record(record, seed, preflight_record):
    fields={"format","schema_version","contract_id","seed_slot","feature_names","train_periods","model_spec","optimizer_spec","completed_batches","total_batches","optimizer_updates","mode","contract_spec","support_record","rng_contract"}
    if not isinstance(record,Mapping) or set(record)!=fields: raise ValueError("checkpoint record field inventory mismatch")
    expected_batches=8*preflight_record["episodes_per_context"]//256
    if (
        record["format"]!=CHECKPOINT_FORMAT
        or type(record["schema_version"]) is not int
        or record["schema_version"]!=SCHEMA_VERSION
        or record["contract_id"]!=CONTRACT_ID
        or record["seed_slot"]!=seed
        or tuple(record["feature_names"])!=FEATURE_NAMES
        or tuple(record["train_periods"])!=K_TRAIN
        or record["model_spec"]!=MODEL_SPEC
        or record["optimizer_spec"]!=OPTIMIZER_SPEC
        or type(record["completed_batches"]) is not int
        or type(record["total_batches"]) is not int
        or type(record["optimizer_updates"]) is not int
        or record["completed_batches"]!=expected_batches
        or record["total_batches"]!=expected_batches
        or record["optimizer_updates"]!=expected_batches
        or record["mode"]!=PRODUCTION_MODE
        or record["contract_spec"]!=preflight_record["contract_spec"]
        or record["support_record"]!=preflight_record
        or record["rng_contract"]!=rng_contract()
    ): raise ValueError("checkpoint record values do not match the frozen production structure")
    return dict(record)

def build_complete_result(*,preflight_record:Mapping[str,Any],checkpoint_records:Mapping[str,Any],seed_evaluations):
    evaluations=tuple(seed_evaluations)
    from .support import validate_support
    preflight_record=validate_support(preflight_record)
    if preflight_record.get("mode")!=PRODUCTION_MODE or preflight_record.get("contract_spec")!=default_manifest()["contract_spec"]: raise ValueError("production preflight structure required")
    if not isinstance(checkpoint_records,Mapping) or set(checkpoint_records)!=set(SEED_SLOTS) or any(not e.result_eligible or checkpoint_records.get(e.seed_slot)!=e.checkpoint_record for e in evaluations): raise ValueError("checkpoint/evaluation structure mismatch")
    checkpoint_records={seed:_checkpoint_record(record,seed,preflight_record) for seed,record in checkpoint_records.items()}
    a=analyze_acquisition(evaluations); result=BeliefResult(SCHEMA_VERSION,CONTRACT_ID,"BELIEF",dict(preflight_record),PRODUCTION_MODE,dict(checkpoint_records),evaluations,a["competence_pass"],a["competent_seed_count"],a["acquisition_all_flips"],a["panel_min_signed_specificity"],a["acquisition_pass"],True,a["fixed_panel_disposition"])
    return validate_complete_result({"format":RESULT_FORMAT,"result":asdict(result)})
def _seed(value):
    if not isinstance(value,Mapping) or set(value)!=set(SeedEvaluation.__dataclass_fields__): raise ValueError("seed field inventory mismatch")
    e=SeedEvaluation(**value); cells={context_id(c) for c in contexts()}
    if e.seed_slot not in SEED_SLOTS or type(e.result_eligible)is not bool or not e.result_eligible or e.checkpoint_record.get("mode")!=PRODUCTION_MODE or any(type(getattr(e,n))is not bool for n in ("root_unique","tail_unique","target_flip")): raise ValueError("seed checkpoint structure mismatch")
    if set(e.root_scores)!=cells or set(e.tail_scores)!=cells: raise ValueError("score context inventory mismatch")
    roots={}; tails={}; rm=[]; tm=[]
    for cell in cells:
        rs=e.root_scores[cell]; labels={"PROBE",*(f"IMMEDIATE:{k}" for k in K_TEST)}
        if set(rs)!=labels or any(type(v)not in(int,float) or isinstance(v,bool) or not math.isfinite(v) for v in rs.values()): raise ValueError("root scores invalid")
        ordered=["PROBE",*(f"IMMEDIATE:{k}" for k in K_TEST)]; ranked=sorted((rs[k],-i,k) for i,k in enumerate(ordered)); roots[cell]=ranked[-1][2]; rm.append(ranked[-1][0]-ranked[-2][0]); tails[cell]={}
        if set(e.tail_scores[cell])!={str(n) for n in range(7)}: raise ValueError("tail count inventory mismatch")
        for count,scores in e.tail_scores[cell].items():
            if set(scores)!={str(k) for k in K_TEST} or any(type(v)not in(int,float) or isinstance(v,bool) or not math.isfinite(v) for v in scores.values()): raise ValueError("tail score inventory mismatch")
            ranked=sorted((scores[str(k)],-i,k) for i,k in enumerate(K_TEST)); tails[cell][count]=ranked[-1][2]; tm.append(ranked[-1][0]-ranked[-2][0])
    audit=audit_discrete_policy(roots,tails)
    if roots!=e.root_selected_actions or tails!=e.tail_selected_periods or e.action_vector!=audit["action_vector"] or e.oracle_action_vector!=audit["oracle_action_vector"] or e.cell_evidence!=audit["cell_evidence"]: raise ValueError("policy evidence mismatch")
    if any(type(getattr(e,name)) not in (int,float) or isinstance(getattr(e,name),bool) or not math.isfinite(getattr(e,name)) for name in ("min_root_margin","min_tail_margin")): raise ValueError("score margins must be finite numbers")
    if e.root_unique!=(min(rm)>0) or e.tail_unique!=(min(tm)>0) or abs(e.min_root_margin-min(rm))>1e-12 or abs(e.min_tail_margin-min(tm))>1e-12: raise ValueError("score margin mismatch")
    if e.cell_tail_agreement!=audit["cell_tail_agreement"] or e.target_flip!=audit["target_flip"]: raise ValueError("stored policy summary mismatch")
    for name in ("max_regret","forced_probe_tail_agreement"):
        if not math.isfinite(getattr(e,name)) or abs(getattr(e,name)-audit[name])>1e-12: raise ValueError("derived metric mismatch")
    if e.minimum_seed_signed_specificity!=audit["minimum_seed_signed_specificity"]: raise ValueError("exact seed specificity minimum mismatch")
    return e
def validate_complete_result(value):
    if not isinstance(value,Mapping) or set(value)!={"format","result"} or value["format"]!=RESULT_FORMAT: raise ValueError("result envelope mismatch")
    r=value["result"]
    from .support import validate_support
    if set(r)!=set(BeliefResult.__dataclass_fields__) or type(r["schema_version"])is not int or r["schema_version"]!=SCHEMA_VERSION or r["contract_id"]!=CONTRACT_ID or r["phase"]!="BELIEF" or r["preflight_mode"]!=PRODUCTION_MODE or not isinstance(r["preflight_record"],dict) or validate_support(r["preflight_record"])["contract_spec"]!=default_manifest()["contract_spec"]: raise ValueError("result structure mismatch")
    ev=tuple(_seed(x) for x in r["seed_evaluations"])
    if len(ev)!=10 or {e.seed_slot for e in ev}!=set(SEED_SLOTS) or not isinstance(r["checkpoint_records"],dict) or set(r["checkpoint_records"])!=set(SEED_SLOTS) or any(r["checkpoint_records"][e.seed_slot]!=e.checkpoint_record for e in ev): raise ValueError("result seed/checkpoint structure mismatch")
    for seed,record in r["checkpoint_records"].items(): _checkpoint_record(record,seed,r["preflight_record"])
    a=analyze_acquisition(ev)
    for n in ("competence_pass","competent_seed_count","acquisition_all_flips","panel_min_signed_specificity","acquisition_pass","fixed_panel_disposition"):
        if r[n]!=a[n]: raise ValueError("analysis field mismatch")
    if type(r["complete"])is not bool or not r["complete"] or any(type(r[n])is not bool for n in ("competence_pass","acquisition_all_flips","acquisition_pass")) or type(r["competent_seed_count"])is not int or isinstance(r["competent_seed_count"],bool) or r["panel_min_signed_specificity"]!=a["panel_min_signed_specificity"] or r["fixed_panel_disposition"] not in {"STOP_FIXED_PANEL_COMPETENCE","STOP_FIXED_PANEL_ACQUISITION","FIXED_PANEL_ACQUISITION_SUPPORTED"} or r["representation_conclusion"]!="NONE" or r["claim_ceiling"]!="TEN_FIXED_SEED_SLOTS_FINITE_HOST_ONLY_NO_SEED_SUPERPOPULATION": raise ValueError("partial/deferred phase mismatch")
    return dict(value)
def _atomic_create_bytes(path,payload):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); h,t=tempfile.mkstemp(prefix=f".{p.name}.",suffix=".tmp",dir=p.parent)
    try:
        with os.fdopen(h,"wb") as f:f.write(payload);f.flush();os.fsync(f.fileno())
        os.link(t,p)
        os.unlink(t)
    except BaseException:
        try:os.unlink(t)
        except FileNotFoundError:pass
        raise
    return p
def publish_complete_result(result,output_path):
    value=validate_complete_result(result)
    return _atomic_create_bytes(output_path,canonical_bytes(value))
