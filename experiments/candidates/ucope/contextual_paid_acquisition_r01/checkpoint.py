"""Atomic single-checkpoint persistence with explicit structural binding."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping
import os,tempfile
from .contract import CONTRACT_ID,FEATURE_NAMES,K_TRAIN,MODEL_SPEC,OPTIMIZER_SPEC,SCHEMA_VERSION,SEED_SLOTS,contract_spec
from .rng import rng_contract
CHECKPOINT_FORMAT="UCOPE_CPA_SINGLE_SHARED_CHECKPOINT_V1"
def _torch():
    try: import torch
    except ImportError as exc: raise RuntimeError("checkpoint operations require PyTorch") from exc
    return torch
def checkpoint_payload(model,optimizer,*,seed_slot,completed_batches,optimizer_updates,total_batches,mode,contract_spec,support_record):
    if seed_slot not in SEED_SLOTS or mode not in ("PRODUCTION","TEST_ONLY"): raise ValueError("checkpoint seed/mode invalid")
    if any(type(v)is not int or v<0 for v in (completed_batches,optimizer_updates,total_batches)) or completed_batches>total_batches or optimizer_updates!=completed_batches: raise ValueError("checkpoint progress invalid")
    model_state={name:tensor.detach().cpu().clone() for name,tensor in model.state_dict().items()}
    optimizer_state=deepcopy(optimizer.state_dict())
    value={"format":CHECKPOINT_FORMAT,"schema_version":SCHEMA_VERSION,"contract_id":CONTRACT_ID,"seed_slot":seed_slot,"feature_names":FEATURE_NAMES,"train_periods":K_TRAIN,"model_spec":deepcopy(MODEL_SPEC),"optimizer_spec":deepcopy(OPTIMIZER_SPEC),"completed_batches":completed_batches,"total_batches":total_batches,"optimizer_updates":optimizer_updates,"mode":mode,"contract_spec":deepcopy(contract_spec),"support_record":deepcopy(support_record),"rng_contract":rng_contract(),"model_state":model_state,"optimizer_state":optimizer_state}
    return validate_checkpoint_payload(value)
def validate_checkpoint_payload(value:Mapping[str,Any]):
    required={"format","schema_version","contract_id","seed_slot","feature_names","train_periods","model_spec","optimizer_spec","completed_batches","total_batches","optimizer_updates","mode","contract_spec","support_record","rng_contract","model_state","optimizer_state"}
    if not isinstance(value,Mapping) or set(value)!=required: raise ValueError("checkpoint field inventory mismatch")
    if value["format"]!=CHECKPOINT_FORMAT or type(value["schema_version"]) is not int or value["schema_version"]!=SCHEMA_VERSION or value["contract_id"]!=CONTRACT_ID or value["seed_slot"] not in SEED_SLOTS: raise ValueError("checkpoint structure mismatch")
    if tuple(value["feature_names"])!=FEATURE_NAMES or tuple(value["train_periods"])!=K_TRAIN or value["model_spec"]!=MODEL_SPEC or value["optimizer_spec"]!=OPTIMIZER_SPEC: raise ValueError("checkpoint learner structure mismatch")
    if value["mode"] not in ("PRODUCTION","TEST_ONLY") or any(type(value[n])is not int or value[n]<0 for n in ("completed_batches","total_batches","optimizer_updates")) or value["completed_batches"]>value["total_batches"] or value["optimizer_updates"]!=value["completed_batches"]: raise ValueError("checkpoint progress mismatch")
    from .support import validate_support
    support=validate_support(value["support_record"])
    episodes=support["episodes_per_context"]
    if value["contract_spec"]!=contract_spec(value["mode"],episodes) or support["mode"]!=value["mode"] or support["contract_spec"]!=value["contract_spec"] or (8*episodes)%256 or value["total_batches"]!=8*episodes//256: raise ValueError("checkpoint support/batch structure mismatch")
    if value["rng_contract"]!=rng_contract(): raise ValueError("checkpoint RNG structure mismatch")
    torch=_torch(); expected={}
    for s in ("root","tail"): expected.update({f"{s}.layers.0.weight":(64,9),f"{s}.layers.0.bias":(64,),f"{s}.layers.2.weight":(64,64),f"{s}.layers.2.bias":(64,),f"{s}.layers.4.weight":(1,64),f"{s}.layers.4.bias":(1,)})
    if set(value["model_state"])!=set(expected): raise ValueError("checkpoint model tensor inventory mismatch")
    for n,t in value["model_state"].items():
        if not isinstance(t,torch.Tensor) or t.dtype!=torch.float32 or tuple(t.shape)!=expected[n] or not torch.isfinite(t).all().item(): raise ValueError("checkpoint tensor invalid")
    optimizer=value["optimizer_state"]
    if not isinstance(optimizer,dict) or set(optimizer)!={"state","param_groups"} or not isinstance(optimizer["param_groups"],list) or len(optimizer["param_groups"])!=1: raise ValueError("optimizer structure invalid")
    group=optimizer["param_groups"][0]
    expected_group={"lr":3e-4,"betas":(0.9,0.999),"eps":1e-8,"weight_decay":1e-4,"amsgrad":False,"maximize":False,"foreach":None,"capturable":False,"differentiable":False,"fused":None,"decoupled_weight_decay":True}
    if set(group)!={*expected_group,"params"} or any(group[name]!=expected_value for name,expected_value in expected_group.items()): raise ValueError("optimizer hyperparameter drift")
    if group.get("params")!=list(range(12)): raise ValueError("optimizer parameter inventory mismatch")
    if value["optimizer_updates"]==0 and optimizer["state"]: raise ValueError("zero-update optimizer must have empty state")
    if value["optimizer_updates"]>0 and set(optimizer["state"])!=set(range(12)): raise ValueError("updated optimizer state incomplete")
    parameter_names=[]
    for scorer in ("root","tail"):
        parameter_names.extend((f"{scorer}.layers.0.weight",f"{scorer}.layers.0.bias",f"{scorer}.layers.2.weight",f"{scorer}.layers.2.bias",f"{scorer}.layers.4.weight",f"{scorer}.layers.4.bias"))
    for index,state in optimizer["state"].items():
        if not isinstance(state,dict) or set(state)!={"step","exp_avg","exp_avg_sq"}: raise ValueError("optimizer state field mismatch")
        parameter=value["model_state"][parameter_names[index]]
        step=state["step"]
        if not isinstance(step,torch.Tensor) or step.numel()!=1 or not torch.isfinite(step).all().item() or float(step.item())!=float(value["optimizer_updates"]): raise ValueError("optimizer step mismatch")
        for name in ("exp_avg","exp_avg_sq"):
            moment=state[name]
            if not isinstance(moment,torch.Tensor) or moment.dtype!=torch.float32 or tuple(moment.shape)!=tuple(parameter.shape) or not torch.isfinite(moment).all().item(): raise ValueError("optimizer moment structure mismatch")
    return dict(value)
def save_checkpoint(path,payload):
    value=validate_checkpoint_payload(payload); destination=Path(path); destination.parent.mkdir(parents=True,exist_ok=True); handle,temp=tempfile.mkstemp(prefix=f".{destination.name}.",suffix=".tmp",dir=destination.parent); os.close(handle)
    try:
        _torch().save(value,temp)
        with open(temp,"r+b") as stream: os.fsync(stream.fileno())
        os.replace(temp,destination)
    except BaseException:
        try: os.unlink(temp)
        except FileNotFoundError: pass
        raise
    return destination
def load_checkpoint(path,model=None,optimizer=None):
    torch=_torch()
    try: value=torch.load(Path(path),map_location="cpu",weights_only=False)
    except TypeError: value=torch.load(Path(path),map_location="cpu")
    value=validate_checkpoint_payload(value)
    if model is not None: model.load_state_dict(value["model_state"],strict=True)
    if optimizer is not None: optimizer.load_state_dict(value["optimizer_state"])
    return value
def _equal(a,b):
    torch=_torch()
    if isinstance(a,torch.Tensor): return isinstance(b,torch.Tensor) and torch.equal(a,b)
    if isinstance(a,dict): return isinstance(b,dict) and set(a)==set(b) and all(_equal(a[k],b[k]) for k in a)
    if isinstance(a,(list,tuple)): return type(a)==type(b) and len(a)==len(b) and all(_equal(x,y) for x,y in zip(a,b))
    return a==b
def validate_cold_resume(path,model_factory,optimizer_factory):
    first=load_checkpoint(path); model=model_factory(first["seed_slot"]); optimizer=optimizer_factory(model.parameters()); load_checkpoint(path,model,optimizer)
    if not _equal(first["model_state"],model.state_dict()) or not _equal(first["optimizer_state"],optimizer.state_dict()): raise ValueError("cold resume state mismatch")
    return first
