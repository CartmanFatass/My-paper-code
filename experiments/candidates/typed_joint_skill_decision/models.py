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
VENDOR_SHA256 = "cb77c34b3b5abfc1f59eb1a73357ad80238df397ffdddcfaf634c01949f89b3f"


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


class Dataset:
    def __init__(self, root: Path, manifest_sha256: str):
        if not root.is_absolute() or root.resolve() != root:
            raise ValueError("dataset root must be canonical absolute")
        self.root, self.manifest_sha256 = root, manifest_sha256
        self.files = verify_manifest(root,manifest_sha256)
        self.summary = self.json("summary.json")
        self.config = self.json("config.json")
        if self.summary["status"] != "complete" or self.summary["contract_sha256"] != c.digest(c.frozen_contract()):
            raise ValueError("incomplete or changed native contract")
        if self.summary["source_sha256"] != c.SOURCE_SHA256:
            raise ValueError("native source identity changed")
        self.records = []
        for address in c.worlds():
            world = address["world"]
            prefix = f"prepared/b{address['block']}/{address['split']}/{world}"
            features = self.json(prefix+"/features.json")
            c.validate_features(features)
            provenance = self.json(prefix+"/provenance.json")
            codec = self.json(prefix+"/codec.json")
            labels = self.json(f"worlds/b{address['block']}/{address['split']}/{world}/labels.json")
            identity = c.digest(features)
            if (provenance["address"] != address or labels["address"] != address
                    or any(value != identity for value in (provenance["feature_sha256"],
                         labels["feature_sha256"],codec["feature_sha256"]))):
                raise ValueError("dataset address/feature identity mismatch")
            slots = sorted(p["construction_slot"] for p in features["plans"])
            if labels["slot_order"] != slots or len(labels["Q"]) != len(slots):
                raise ValueError("dataset label mask mismatch")
            if labels["soft_targets"] != c.soft_targets(labels["Q"]):
                raise ValueError("dataset soft targets changed")
            self.records.append({"address":address,"features":features,"labels":labels,
                                 "provenance":provenance,"codec":codec})
        if self.summary["bill"]["delta_counters"]["worlds_completed"] != len(self.records):
            raise ValueError("dataset world completion count mismatch")

    def json(self, relative):
        if relative not in self.files or relative in {e.get("discarded_path") for e in self.files.values()}:
            raise ValueError(f"unbound input: {relative}")
        return json.loads((self.root/relative).read_bytes())

    def split(self, block, split):
        return [r for r in self.records if r["address"]["block"] == block and r["address"]["split"] == split]

    def require_source_sha(self,sha):
        if self.summary.get("launch_sha") != sha or self.config.get("admission",{}).get("sha") != sha:
            raise ValueError("native dataset source SHA differs from this sequential study")


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


def load_frozen_source(model_root: Path):
    """Local pinned checkpoint into the unchanged vendor architecture, float32 only."""
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    import torch
    from safetensors.torch import load_file
    from .vendor import laya_common as source
    if hash_file(Path(source.__file__)) != VENDOR_SHA256:
        raise ValueError("pinned vendor source bytes changed")
    cfg = json.loads((model_root/"rl_agent_config.json").read_bytes())
    if cfg.get("head_layers",2) != 2:
        raise ValueError("pinned head architecture mismatch")
    started = time.perf_counter()
    model = source.build_model(cfg,encoder_dir=str(model_root/"encoder"),pretrained=False)
    # ModernBERT 5.x otherwise enables its decorated compiled embedding/MLP
    # branches when Triton is installed and reference_compile was omitted.
    model.encoder.config.reference_compile = False
    for module in model.encoder.modules():
        if hasattr(module,"config") and hasattr(module.config,"reference_compile"):
            module.config.reference_compile = False
    if model.encoder.config.reference_compile is not False:
        raise AssertionError("fixed no-compile encoder contract not effective")
    weights = load_file(str(model_root/"model.safetensors"),device="cpu")
    model.load_state_dict(weights,strict=True)
    del weights
    model = model.float().to("cuda:0").eval()
    model.requires_grad_(False)
    if sum(p.numel() for p in model.scorer.parameters()) != 1_052_673:
        raise ValueError("pretrained scorer parameter count changed")
    return model, {"cold_load_wall_seconds":time.perf_counter()-started,"config":cfg,
                   "vendor_sha256":VENDOR_SHA256,"dtype":"float32","device":"cuda:0",
                   "reference_compile":model.encoder.config.reference_compile,
                   "frozen_state_sha256":parameter_digest(model.state_dict())}


def numeric_model(seed):
    import torch
    from torch import nn
    torch.manual_seed(seed)
    model = nn.Sequential(nn.Linear(153,256),nn.GELU(),nn.Linear(256,256),nn.GELU(),nn.Linear(256,1))
    if sum(p.numel() for p in model.parameters()) != 105_473:
        raise AssertionError("numeric parameter count changed")
    return model.float().to("cuda:0")


def pretrained_scorer(source):
    model = copy.deepcopy(source.scorer).float().to("cuda:0")
    model.requires_grad_(True)
    return model


def padded_contexts(records, inputs, *, device="cuda:0"):
    import torch
    width = len(inputs[0][0])
    x = torch.zeros((len(records),8,width),dtype=torch.float32,device=device)
    mask = torch.zeros((len(records),8),dtype=torch.bool,device=device)
    target = torch.zeros((len(records),8),dtype=torch.float32,device=device)
    slots = []
    for i,(record,array) in enumerate(zip(records,inputs)):
        order = record["features"]["display_order"]
        count = len(order)
        x[i,:count] = torch.as_tensor(array,dtype=torch.float32,device=device)
        mask[i,:count] = True
        label = dict(zip(record["labels"]["slot_order"],record["labels"]["soft_targets"]))
        target[i,:count] = torch.tensor([label[slot] for slot in order],dtype=torch.float32,device=device)
        slots.append(order)
    return x,mask,target,slots


def source_forward(model, encoded, bill, *, correctness=False):
    """Capture the actual pre-scorer input after upstream gather; no parallel backbone."""
    import torch
    if correctness:
        bill.enter("full_forward_correctness_calls")
    bill.enter("full_laya_forward_calls")
    bill.enter("source_scorer_contexts")
    bill.enter("source_act_head_contexts")
    captured = []
    handle = model.scorer.register_forward_pre_hook(lambda module,args:captured.append(args[0].detach().clone()))
    started = time.perf_counter()
    try:
        ids = torch.tensor([encoded["input_ids"]],dtype=torch.long,device="cuda:0")
        markers = torch.tensor([encoded["marker_pos"]],dtype=torch.long,device="cuda:0")
        with torch.inference_mode():
            logits,act_logits = model(ids,torch.ones_like(ids),markers,
                torch.ones_like(markers,dtype=torch.bool),torch.zeros((1,),dtype=torch.long,device="cuda:0"))
        torch.cuda.synchronize()
        if len(captured) != 1 or captured[0].shape != (1,len(encoded["marker_pos"]),1024):
            raise AssertionError("source scorer pre-hook shape/call changed")
        if captured[0].dtype != torch.float32 or logits.dtype != torch.float32:
            raise AssertionError("fixed float32 path changed")
        bill.complete("full_laya_forwards_completed")
        if correctness:
            bill.complete("full_forward_correctness_completed")
        return captured[0][0].cpu(),logits[0].cpu(),act_logits[0].cpu(),time.perf_counter()-started
    finally:
        handle.remove()
