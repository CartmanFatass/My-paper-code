"""Fixed B01 numeric/scorer package and exact dataset identities.

Imports are effect-free: torch/model/tokenizer loading and RNG draws occur only in
explicit functions called by admitted runners. Reader functional arithmetic lives
separately in read_b01.py, not in these candidate predictors.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from pathlib import Path
import time

from . import contract as c
from .data import hash_file

FLOAT_TOLERANCE = {"rtol": 1e-5, "atol": 1e-6}


def numeric_rows(features, *, reverse=False):
    """139 geometry values + kind3/k3/slot8, same information as the typed table."""
    c.validate_features(features)
    order = list(features["display_order"])
    if reverse:
        order.reverse()
    shared = [x/5000 for row in features["initial_uav_xyz"] for x in row]
    shared += [x/5000 for row in features["user_xy"] for x in row]
    shared += [x/5000 for x in features["bs_xyz"]]
    plans = {p["construction_slot"]:p for p in features["plans"]}
    result = []
    for slot in order:
        p = plans[slot]
        row = shared + [x/5000 for xyz in p["assigned_targets_xyz"] for x in xyz]
        row += [float(p["kind"] == kind) for kind in c.KINDS]
        row += [float(p["k"] == k) for k in (4,5,6)]
        row += [float(slot == s) for s in range(8)]
        if len(row) != 153:
            raise AssertionError("numeric schema width changed")
        result.append(row)
    return result, order


def select_slot(logits, slots):
    if len(logits) != len(slots) or not logits or not all(math.isfinite(float(x)) for x in logits):
        raise ValueError("invalid prediction/marker inversion")
    # Exact logit ties keep the first displayed option, common to both packages.
    return slots[max(range(len(slots)),key=lambda i:float(logits[i]))]


def verify_manifest(root: Path, expected_sha256: str):
    """Verify every retained scientific byte object; audit aliases must bind a retained trace."""
    manifest = root/"manifest.jsonl"
    if hash_file(manifest) != expected_sha256:
        raise ValueError("complete input manifest digest changed")
    entries = [json.loads(line) for line in manifest.read_bytes().splitlines()]
    aliases = {e["discarded_path"]:e for e in entries if e.get("kind") == "audit_trace_alias"}
    files = {}
    for e in entries:
        if "path" not in e:
            if e.get("kind") != "audit_trace_alias":
                raise ValueError("unknown manifest entry")
            continue
        relative = e["path"]
        path = root/relative
        if path.resolve() != path or not path.is_relative_to(root) or relative in files:
            raise ValueError("invalid or repeated manifest path")
        files[relative] = e
        if relative in aliases:
            alias = aliases[relative]
            if e.get("status") != "identical_audit" or alias["logical_sha256"] != e["logical_sha256"]:
                raise ValueError("invalid discarded audit identity")
            continue
        if not path.is_file() or path.stat().st_size != e["bytes"] or hash_file(path) != e["sha256"]:
            raise ValueError(f"input file drift: {relative}")
    for relative, alias in aliases.items():
        retained = files.get(alias["retained_path"])
        if (relative not in files or retained is None or not (root/alias["retained_path"]).is_file()
                or retained.get("logical_sha256") != alias["logical_sha256"]):
            raise ValueError("audit alias has no identical retained evidence")
    return files



def parameter_digest(state):
    """Canonical tensor identity: name, dtype, shape and raw contiguous CPU bytes."""
    h = hashlib.sha256()
    for name,tensor in sorted(state.items()):
        array = tensor.detach().cpu().contiguous().numpy()
        h.update(c.encode_json({"name":name,"dtype":str(array.dtype),"shape":list(array.shape)}))
        h.update(array.tobytes())
    return h.hexdigest()


def tensor_movement(state, initial):
    import torch
    square, max_abs, initial_square = 0.,0.,0.
    for key,value in state.items():
        delta = value.detach().cpu().double()-initial[key].double()
        square += float(delta.square().sum())
        max_abs = max(max_abs,float(delta.abs().max()))
        initial_square += float(initial[key].double().square().sum())
    return {"l2":math.sqrt(square),"max_absolute":max_abs,
            "relative_l2":math.sqrt(square)/max(math.sqrt(initial_square),1e-30)}


def configure_float32():
    import torch
    torch.set_default_dtype(torch.float32)
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.set_float32_matmul_precision("highest")
    if not torch.cuda.is_available():
        raise RuntimeError("fixed cuda:0 runtime unavailable; no alternate precision/device")


def cpu_thread_environment():
    for key in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS","NUMEXPR_NUM_THREADS"):
        os.environ[key] = "1"
    return {key:os.environ[key] for key in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS","NUMEXPR_NUM_THREADS")}


def geometry_tensors(features):
    """Coordinates are normalized before edges; original row identities stay paired."""
    import numpy as np
    c.validate_features(features)
    initial = np.asarray(features['initial_uav_xyz'],dtype=np.float64)/5000
    users = np.asarray(features['user_xy'],dtype=np.float64)/5000
    bs = np.asarray(features['bs_xyz'],dtype=np.float64)/5000
    user_xyz = np.concatenate((users,np.zeros((50,1))),axis=-1)
    peers = np.asarray([[j for j in range(6) if j != i] for i in range(6)])
    by_slot = {p['construction_slot']:p for p in features['plans']}
    result = {key:[] for key in c.TENSOR_SHAPES}
    def edges(a,b):
        delta = a-b
        return np.concatenate((delta,np.sum(delta**2,axis=-1,keepdims=True)),axis=-1)
    for slot in features['display_order']:
        plan = by_slot[slot]
        target = np.asarray(plan['assigned_targets_xyz'],dtype=np.float64)/5000
        result['U'].append(np.concatenate((initial,target,np.eye(6)),axis=-1))
        result['Y'].append(np.concatenate((users,np.eye(50)),axis=-1))
        result['B'].append(bs)
        result['M'].append([float(plan['kind']==kind) for kind in c.KINDS]
                          +[float(plan['k']==k) for k in (4,5,6)]+[float(slot==s) for s in range(8)])
        result['E_UY'].append(np.concatenate((edges(initial[:,None,:],user_xyz[None,:,:]),
                                               edges(target[:,None,:],user_xyz[None,:,:])),axis=-1))
        result['E_UU'].append(np.concatenate((edges(initial[:,None,:],initial[peers]),
                                               edges(target[:,None,:],target[peers])),axis=-1))
        result['E_UB'].append(np.concatenate((edges(initial,bs),edges(target,bs)),axis=-1))
    return {key:np.asarray(value,dtype=np.float32) for key,value in result.items()}


def flatten_tensors(tensors):
    import torch
    return torch.cat([tensors[k].flatten(start_dim=-len(shape)) for k,shape in c.TENSOR_SHAPES.items()],dim=-1)


def make_model(arm, seed=None, *, device='cuda:0'):
    import torch
    from torch import nn
    if seed is not None:
        torch.manual_seed(seed)
    if arm in ('A','N'):
        width,hidden = (5377,64) if arm=='A' else (153,256)
        model = nn.Sequential(nn.Linear(width,hidden),nn.GELU(),nn.Linear(hidden,hidden),nn.GELU(),nn.Linear(hidden,1))
    elif arm == 'R':
        def two(width, final_gelu=False):
            layers=[nn.Linear(width,64),nn.GELU(),nn.Linear(64,64)]
            if final_gelu:
                layers.append(nn.GELU())
            return nn.Sequential(*layers)
        class Relational(nn.Module):
            def __init__(self):
                super().__init__()
                self.encoders=nn.ModuleDict({k:two(w,True) for k,w in [('U',12),('Y',52),('B',3)]})
                self.messages=nn.ModuleList([nn.ModuleDict({k:two(136) for k in ('UY','UU','UB')}) for _ in range(3)])
                self.updates=nn.ModuleList([two(256) for _ in range(3)])
                self.readout=nn.Sequential(nn.Linear(206,64),nn.GELU(),nn.Linear(64,1))
            def forward(self,t):
                u,y,b=[self.encoders[k](t[k]) for k in ('U','Y','B')]
                peers=torch.tensor([[j for j in range(6) if j!=i] for i in range(6)],device=u.device)
                for messages,update in zip(self.messages,self.updates):
                    uy=messages['UY'](torch.cat((u.unsqueeze(-2).expand(*u.shape[:-1],50,64),
                        y.unsqueeze(-3).expand(*u.shape[:-2],6,50,64),t['E_UY']),dim=-1)).mean(-2)
                    uu=messages['UU'](torch.cat((u.unsqueeze(-2).expand(*u.shape[:-1],5,64),u[...,peers,:],t['E_UU']),dim=-1)).mean(-2)
                    ub=messages['UB'](torch.cat((u,b.unsqueeze(-2).expand(*u.shape[:-2],6,64),t['E_UB']),dim=-1))
                    u=torch.nn.functional.gelu(u+update(torch.cat((u,uy,uu,ub),dim=-1)))
                return self.readout(torch.cat((u.mean(-2),y.mean(-2),b,t['M']),dim=-1))
        model=Relational()
    else:
        raise ValueError('unknown frozen arm')
    if sum(p.numel() for p in model.parameters()) != c.PARAMETERS[arm]:
        raise AssertionError('frozen parameter count changed')
    return model.float().to(device)


def context_input(record,arm,*,device='cuda:0'):
    import torch
    features=record['features']
    if arm=='N':
        return torch.tensor(numeric_rows(features)[0],dtype=torch.float32,device=device)
    t={k:torch.as_tensor(v,dtype=torch.float32,device=device) for k,v in geometry_tensors(features).items()}
    return flatten_tensors(t) if arm=='A' else t


def training_batch(records,arm,*,device='cuda:0'):
    import torch
    arrays=[context_input(r,arm,device=device) for r in records]
    def pad(values):
        x=torch.zeros((len(records),8,*values[0].shape[1:]),dtype=torch.float32,device=device)
        for i,value in enumerate(values):
            x[i,:len(value)]=value
        return x
    inputs={k:pad([v[k] for v in arrays]) for k in arrays[0]} if arm=='R' else pad(arrays)
    mask=torch.zeros((len(records),8),dtype=torch.bool,device=device)
    target=torch.zeros((len(records),8),dtype=torch.float32,device=device)
    for i,r in enumerate(records):
        slots=r['features']['display_order'];mask[i,:len(slots)]=True
        p=dict(zip(r['labels']['slot_order'],r['labels']['soft_targets']))
        target[i,:len(slots)]=torch.tensor([p[s] for s in slots],dtype=torch.float32,device=device)
    return inputs,mask,target


def slice_input(x,indices):
    return {k:v[indices] for k,v in x.items()} if isinstance(x,dict) else x[indices]
