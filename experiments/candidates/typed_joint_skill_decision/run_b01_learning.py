"""Admitted fixed B01 representation extraction and six final-endpoint fits.

Science has no CLI knobs. External paths are bound by admitted literal SHA256s.
No native calls, extra endpoint passes, model alternatives, fit retries or network.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback

if __package__ in (None, ""):
    sys.path.insert(0,str(Path(__file__).resolve().parents[3]))

from experiments.candidates.typed_joint_skill_decision import contract as c, models
from experiments.candidates.typed_joint_skill_decision.data import Bill, Store, hash_file
from experiments.candidates.typed_joint_skill_decision.run_b01_native import load_bound_json, verify_assets, verify_sources


def accepted_store(script_file, args, admission, paths):
    root = Path(script_file).resolve().parents[3]
    output = args.out_dir.absolute()
    if (args.launch_sha != admission["sha"] or str(output) != paths.get("output_root")
            or output.resolve() != output or str(root) != paths.get("source_root")):
        raise ValueError("admitted source/output/sha binding mismatch")
    launch = json.loads((output/"launch-manifest.json").read_bytes())
    if any(launch.get(k) != v for k,v in {"source_root":str(root),"output_root":str(output),
        "direction":c.DIRECTION,"sha":admission["sha"],"command_sha256":admission["command_sha256"]}.items()):
        raise ValueError("launcher manifest differs from admitted phase")
    prior = load_bound_json(args.budget_ledger,args.budget_ledger_sha256)
    bill = Bill(prior,output,source_root=root)
    return Store(output,bill),admission,prior,root


def dataset_locator(path,sha):
    value = load_bound_json(path,sha)
    if set(value) != {"root","manifest_sha256","summary_sha256"}:
        raise ValueError("invalid immutable dataset/learning locator")
    root = Path(value["root"])
    if not root.is_absolute() or root.resolve() != root:
        raise ValueError("locator root must be canonical absolute")
    if hash_file(root/"summary.json") != value["summary_sha256"]:
        raise ValueError("locator terminal summary changed")
    return root,value


def save_torch(store,relative,value,*,kind):
    import torch
    # Parameter/cache payload sizes are small and known. Reserve tensors plus
    # serialization overhead conservatively before writing a new scientific file.
    def size(item):
        if torch.is_tensor(item):
            return item.numel()*item.element_size()
        if isinstance(item,dict):
            return sum(size(x) for x in item.values())
        if isinstance(item,(tuple,list)):
            return sum(size(x) for x in item)
        return 0
    store.bill.check(disk=True,pending_bytes=size(value)+1024*1024)
    path = store.locate(relative)
    with path.open("xb") as stream:
        torch.save(value,stream)
        stream.flush()
        os.fsync(stream.fileno())
    store.bill.observe_file(path)
    return store.record_file(path,kind=kind)


def assert_prior(prior,summary):
    previous = summary["bill"]
    if prior["prior_counters"] != previous["cumulative_counters"]:
        raise ValueError("phase counters do not continue exact previous cumulative bill")
    if (prior["prior_cpu_seconds"] < previous["cumulative_cpu_seconds"]
            or prior["prior_gpu_seconds"] < previous["cumulative_gpu_seconds"]):
        raise ValueError("phase underprices prior CPU/GPU work")


def representation_key(record,reverse=False):
    a = record["address"]
    return f"cache/b{a['block']}/{a['split']}/{a['world']}{'-reverse' if reverse else ''}.pt"


def extract(store,dataset,source,model_root):
    import torch
    from experiments.candidates.typed_joint_skill_decision.codec import encode_features
    entries = {}
    for record in dataset.records:
        for reverse in ((False,True) if record["address"]["split"] == "test" else (False,)):
            store.current = {**record["address"],"phase":"representation","reverse":reverse}
            started = time.perf_counter()
            encoded = encode_features(record["features"],model_root,reverse=reverse)
            codec_seconds = time.perf_counter()-started
            features,logits,act,forward_seconds = models.source_forward(source,encoded,store.bill)
            key = representation_key(record,reverse)
            value = {"schema":1,"feature_sha256":c.digest(record["features"]),
                     "state_sha256":encoded["state_sha256"],"slots":encoded["construction_slots"],
                     "post_head_features":features,"source_logits":logits,"source_act_logits":act,
                     "reverse":reverse,"dtype":"float32","full_tokens":encoded["full_tokens"],
                     "codec_wall_seconds":codec_seconds,"full_forward_wall_seconds":forward_seconds}
            identity = save_torch(store,key,value,kind="post_head_cache")
            entries[key] = identity
            store.status("extracting")
    # Exactly the first sixteen training worlds of block1, never outcome selected.
    correctness = []
    for record in dataset.split(1,"train")[:16]:
        key = representation_key(record)
        cached = torch.load(store.output/key,map_location="cpu",weights_only=True)
        encoded = encode_features(record["features"],model_root)
        features,logits,act,seconds = models.source_forward(source,encoded,store.bill,correctness=True)
        store.bill.enter("correctness_adapter_contexts")
        with torch.inference_mode():
            adapted = source.scorer(cached["post_head_features"].to("cuda:0")).squeeze(-1).cpu()
        torch.cuda.synchronize()
        def comparison(a,b):
            delta = (a-b).abs()
            return {"max_absolute":float(delta.max()),
                    "max_relative":float((delta/b.abs().clamp_min(1e-30)).max())}
        evidence = {"world":record["address"]["world"],"feature_error":comparison(features,cached["post_head_features"]),
                    "logit_error":comparison(logits,adapted),"act_error":comparison(act,cached["source_act_logits"]),
                    "source_slot":models.select_slot(logits.tolist(),cached["slots"]),
                    "cache_slot":models.select_slot(adapted.tolist(),cached["slots"]),
                    "forward_wall_seconds":seconds,"tolerance":models.FLOAT_TOLERANCE}
        store.write_json(f"correctness/{record['address']['world']}.json",evidence,kind="source_cache_agreement")
        torch.testing.assert_close(features,cached["post_head_features"],**models.FLOAT_TOLERANCE)
        torch.testing.assert_close(logits,cached["source_logits"],**models.FLOAT_TOLERANCE)
        torch.testing.assert_close(logits,adapted,**models.FLOAT_TOLERANCE)
        torch.testing.assert_close(act,cached["source_act_logits"],**models.FLOAT_TOLERANCE)
        if evidence["source_slot"] != evidence["cache_slot"]:
            raise AssertionError("correctness tolerance hides a changed selected candidate")
        correctness.append(evidence)
        store.status("correctness")
    store.write_json("cache_index.json",{"entries":entries,"dataset_manifest_sha256":dataset.manifest_sha256,
                     "correctness":correctness,"dtype":"float32","source_scorer_sha256":models.parameter_digest(source.scorer.state_dict())},kind="cache_index")


def inputs_for(store,records,arm,*,reverse=False):
    import torch
    arrays = []
    for record in records:
        if arm == "N":
            rows,slots = models.numeric_rows(record["features"],reverse=reverse)
            arrays.append(rows)
        else:
            cache = torch.load(store.output/representation_key(record,reverse),map_location="cpu",weights_only=True)
            expected = list(record["features"]["display_order"])
            if reverse:
                expected.reverse()
            if (cache["feature_sha256"] != c.digest(record["features"]) or cache["slots"] != expected
                    or cache["post_head_features"].dtype != torch.float32):
                raise ValueError("cached input/marker/dtype binding changed")
            arrays.append(cache["post_head_features"])
    return arrays


def endpoint(store,model,records,arm,stage,block,*,reverse=False):
    import torch
    model.eval()
    predictions = []
    active_seconds = 0.
    for record,array in zip(records,inputs_for(store,records,arm,reverse=reverse)):
        store.bill.enter(f"endpoint_{arm}_contexts")
        started = time.perf_counter()
        with torch.inference_mode():
            logits = model(torch.as_tensor(array,dtype=torch.float32,device="cuda:0")).squeeze(-1).cpu().tolist()
        torch.cuda.synchronize()
        active_seconds += time.perf_counter()-started
        slots = list(record["features"]["display_order"])
        if reverse:
            slots.reverse()
        predictions.append({"world":record["address"]["world"],"feature_sha256":c.digest(record["features"]),
                            "slots":slots,"logits":logits,"selected_slot":models.select_slot(logits,slots)})
    store.write_json(f"fits/b{block}/{arm}/{stage}{'-reverse' if reverse else ''}-test.json",
                     {"predictions":predictions,"active_scorer_wall_seconds":active_seconds,
                      "warm_scorer_seconds_per_world":active_seconds/len(records)},kind="endpoint")
    return active_seconds


def fit(store,dataset,source,block,arm):
    import numpy as np
    import torch
    store.bill.enter("fit_calls")
    base = c.BASES[block-1]
    model = models.numeric_model(base+20001) if arm == "N" else models.pretrained_scorer(source)
    initial = {k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
    initial_sha = models.parameter_digest(initial)
    prefix = f"fits/b{block}/{arm}"
    train,test = dataset.split(block,"train"),dataset.split(block,"test")
    if len(train) != 256 or len(test) != 128:
        raise ValueError("fixed fit split size changed")
    save_torch(store,prefix+"/initial.pt",initial,kind="initial_weights")
    model_seed = base+20001
    order_seed = base+20002
    rng = np.random.Generator(np.random.PCG64(order_seed))
    rng_initial = rng.bit_generator.state
    training_x,mask,target,slots = models.padded_contexts(train,inputs_for(store,train,arm))
    optimizer = torch.optim.AdamW(model.parameters(),lr=1e-3 if arm == "N" else 1e-4,weight_decay=1e-4)
    store.write_json(prefix+"/config.json",{"block":block,"arm":arm,"model_seed":model_seed,"order_seed":order_seed,
                    "order_rng_initial":rng_initial,"epochs":64,"batch_size":32,
                    "optimizer":"torch.optim.AdamW","lr":1e-3 if arm == "N" else 1e-4,"weight_decay":1e-4,
                    "adam_betas":[.9,.999],"adam_eps":1e-8,"dtype":"float32","initial_sha256":initial_sha,
                    "parameters":sum(p.numel() for p in model.parameters()),
                    "dataset_manifest_sha256":dataset.manifest_sha256},kind="fit_config")
    endpoint(store,model,test,arm,"initial",block)
    model.train()
    path = store.locate(prefix+"/updates.jsonl")
    stream = path.open("xb")
    updates,previous,active_seconds = 0,initial_sha,0.
    try:
        for epoch in range(64):
            permutation = rng.permutation(256).tolist()
            for start in range(0,256,32):
                indices = permutation[start:start+32]
                store.current = {"phase":"fit","block":block,"arm":arm,"epoch":epoch,"update":updates+1}
                store.bill.enter("optimizer_update_calls")
                store.bill.enter(f"training_{arm}_contexts",32)
                started = time.perf_counter()
                optimizer.zero_grad(set_to_none=True)
                logits = model(training_x[indices]).squeeze(-1).masked_fill(~mask[indices],-1e4)
                loss = -(target[indices]*torch.log_softmax(logits,dim=-1)).sum(-1).mean()
                if not torch.isfinite(loss):
                    raise ArithmeticError("nonfinite fixed soft CE")
                loss.backward()
                gradients = {k:p.grad for k,p in model.named_parameters()}
                if any(g is None or not torch.isfinite(g).all() for g in gradients.values()):
                    raise ArithmeticError("missing/nonfinite scorer gradient")
                grad_l2 = math_sqrt_sum(gradients)
                grad_max = max(float(g.detach().abs().max()) for g in gradients.values())
                grad_sha = models.parameter_digest(gradients)
                optimizer.step()
                torch.cuda.synchronize()
                active_seconds += time.perf_counter()-started
                store.bill.complete("optimizer_updates_completed")
                updates += 1
                after = models.parameter_digest(model.state_dict())
                row = {"update":updates,"epoch":epoch,"batch":start//32,
                       "indices":indices,"worlds":[train[i]["address"]["world"] for i in indices],
                       "feature_sha256":[c.digest(train[i]["features"]) for i in indices],
                       "loss":float(loss.detach()),"grad_l2":grad_l2,"grad_max_absolute":grad_max,
                       "gradient_sha256":grad_sha,"parameter_before_sha256":previous,"parameter_after_sha256":after,
                       "movement_from_initial":models.tensor_movement(model.state_dict(),initial)}
                payload = c.encode_json(row)
                store.bill.check(disk=True,pending_bytes=len(payload))
                stream.write(payload)
                stream.flush()
                store.bill.observe_file(path)
                previous = after
                store.status("fitting")
        if updates != 512:
            raise AssertionError("fixed optimizer count changed")
    finally:
        stream.flush()
        os.fsync(stream.fileno())
        stream.close()
        store.record_file(path,kind="optimizer_update_chain",updates=updates,status="complete" if updates==512 else "partial")
    final = {k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
    save_torch(store,prefix+"/final.pt",final,kind="final_weights")
    save_torch(store,prefix+"/optimizer.pt",optimizer.state_dict(),kind="endpoint_optimizer")
    endpoint(store,model,test,arm,"final",block)
    endpoint(store,model,test,arm,"final",block,reverse=True)
    store.write_json(prefix+"/summary.json",{"updates":updates,"context_exposures":updates*32,
                     "initial_sha256":initial_sha,"final_sha256":models.parameter_digest(final),
                     "movement_from_initial":models.tensor_movement(final,initial),
                     "order_rng_final":rng.bit_generator.state,"active_training_wall_seconds":active_seconds,
                     "dtype":"float32","parameters":sum(p.numel() for p in model.parameters())},kind="fit_summary")
    store.bill.complete("fits_completed")
    del model,optimizer,training_x,mask,target


def math_sqrt_sum(tensors):
    import math
    return math.sqrt(sum(float(value.detach().double().square().sum()) for value in tensors.values()))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed",type=int,required=True,choices=(0,))
    parser.add_argument("--launch-sha",required=True)
    parser.add_argument("--out","--out-dir",dest="out_dir",type=Path,required=True)
    parser.add_argument("--budget-ledger",type=Path,required=True)
    parser.add_argument("--budget-ledger-sha256",required=True)
    parser.add_argument("--asset-manifest",type=Path,required=True)
    parser.add_argument("--asset-manifest-sha256",required=True)
    parser.add_argument("--dataset-input",type=Path,required=True)
    parser.add_argument("--dataset-input-sha256",required=True)
    args = parser.parse_args(argv)
    from scripts.hmasd_admission import ENVIRONMENT_KEY,require_admission
    paths = json.loads(os.environ.get(ENVIRONMENT_KEY,"{}"))
    admission = require_admission(__file__,direction="typed_joint_skill_decision")
    store,admission,prior,root = accepted_store(__file__,args,admission,paths)
    try:
        verify_sources(root)
        threads = models.cpu_thread_environment()
        model_root,assets = verify_assets(args.asset_manifest,args.asset_manifest_sha256)
        dataset_root,locator = dataset_locator(args.dataset_input,args.dataset_input_sha256)
        dataset = models.Dataset(dataset_root,locator["manifest_sha256"])
        dataset.require_source_sha(admission["sha"])
        assert_prior(prior,dataset.summary)
        if dataset.config["asset_manifest_sha256"] != args.asset_manifest_sha256:
            raise ValueError("native/learning pinned asset identity differs")
        if any(not any(p.is_relative_to(r) for r in store.bill.roots) for p in (model_root,dataset_root)):
            raise ValueError("model/dataset missing from global disk bill")
        import torch
        cuda_cache = model_root.parent/"cuda-cache"
        if cuda_cache.resolve() != cuda_cache or not any(cuda_cache.is_relative_to(r) for r in store.bill.roots):
            raise ValueError("owned CUDA driver cache is outside declared disk roots")
        cuda_cache.mkdir(exist_ok=True)
        os.environ["CUDA_CACHE_PATH"] = str(cuda_cache)
        models.configure_float32()
        store.bill.start_gpu()
        torch.cuda.reset_peak_memory_stats()
        source,source_identity = models.load_frozen_source(model_root)
        store.write_json("config.json",{"schema":1,"contract_sha256":c.digest(c.frozen_contract()),
                         "admission":admission,"asset_manifest":assets,"asset_manifest_sha256":args.asset_manifest_sha256,
                         "dataset_root":str(dataset_root),"dataset_manifest_sha256":locator["manifest_sha256"],
                         "dataset_locator":locator,"dataset_locator_sha256":args.dataset_input_sha256,
                         "prior_bill":prior,"prior_bill_sha256":args.budget_ledger_sha256,
                         "torch_version":torch.__version__,"numpy_version":__import__("numpy").__version__,
                         "float32":True,"tf32":False,"autocast":False,"source":source_identity,
                         "cpu_thread_environment":threads,"torch_cpu_intraop_threads":1,"torch_cpu_interop_threads":1,
                         "cuda_driver_cache":str(cuda_cache),
                         "tolerance":models.FLOAT_TOLERANCE},kind="learning_config")
        extract(store,dataset,source,model_root)
        for block in (1,2,3):
            for arm in ("N","L"):
                fit(store,dataset,source,block,arm)
        expected = {"full_laya_forward_calls":1552,"full_laya_forwards_completed":1552,
                    "full_forward_correctness_calls":16,"correctness_adapter_contexts":16,
                    "source_scorer_contexts":1552,"source_act_head_contexts":1552,
                    "fits_completed":6,"optimizer_updates_completed":3072,
                    "training_N_contexts":49152,"training_L_contexts":49152,
                    "endpoint_N_contexts":1152,"endpoint_L_contexts":1152}
        if any(store.bill.delta[k] != v for k,v in expected.items()):
            raise AssertionError("complete fixed learning bill does not match its exact exposure")
        if models.parameter_digest(source.state_dict()) != source_identity["frozen_state_sha256"]:
            raise AssertionError("frozen encoder/head/type/act/scorer state changed during fits")
        peak_gpu = {"max_allocated_bytes":torch.cuda.max_memory_allocated(),
                    "max_reserved_bytes":torch.cuda.max_memory_reserved()}
        torch.cuda.synchronize()
        del source
        torch.cuda.empty_cache()
        store.bill.stop_gpu()
        status = store.status("complete")
        store.write_json("summary.json",{**status,"contract_sha256":c.digest(c.frozen_contract()),
                         "dataset_manifest_sha256":locator["manifest_sha256"],"launch_sha":args.launch_sha,
                         "frozen_state_sha256":source_identity["frozen_state_sha256"],"gpu_peak":peak_gpu,
                         "reader_pending":True,"scientific_interpretation":"complete fixed fits; saved-artifact reading pending"},kind="learning_summary")
        return 0
    except BaseException as exc:
        store.bill.stop_gpu()
        failed = store.status("failed_partial",exception_type=type(exc).__name__,exception=str(exc))
        (store.output/"failure.json").write_bytes(c.encode_json({**failed,"traceback":traceback.format_exc()}))
        raise
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())
