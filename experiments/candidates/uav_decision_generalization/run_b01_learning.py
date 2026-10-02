"""Admitted six fixed numerical fits on original training records only."""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys
import time
if __package__ in (None, ''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments.candidates.uav_decision_generalization import contract as c,models,phases
from experiments.candidates.uav_decision_generalization.phases import save_torch


def endpoint(store,model,records,arm,stage,block,split):
    import torch
    model.eval();predictions=[];input_seconds=0.;scorer_seconds=0.
    for record in records:
        store.bill.enter(f'endpoint_{arm}_contexts')
        started=time.perf_counter();x=models.context_input(record,arm)
        torch.cuda.synchronize();input_seconds+=time.perf_counter()-started
        started=time.perf_counter()
        with torch.inference_mode():
            logits=model(x).squeeze(-1).cpu().tolist()
        torch.cuda.synchronize();scorer_seconds+=time.perf_counter()-started
        slots=list(record['features']['display_order'])
        predictions.append({'world':record['address']['world'],'feature_sha256':c.digest(record['features']),
                            'slots':slots,'logits':logits,'selected_slot':models.select_slot(logits,slots)})
    store.write_json(f'fits/b{block}/{arm}/{stage}-{split}.json',{'predictions':predictions,
                     'input_wall_seconds':input_seconds,'scorer_wall_seconds':scorer_seconds},kind='endpoint')


def fit(store,dataset,block,arm):
    import numpy as np
    import torch
    store.bill.enter("fit_calls")
    base = c.BASES[block-1]
    model_seed = base+(41001 if arm=="A" else 42001)
    model = models.make_model(arm,model_seed)
    initial = {k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
    initial_sha = models.parameter_digest(initial)
    prefix = f"fits/b{block}/{arm}"
    train = dataset.split(block,"train")
    if len(train) != 256:
        raise ValueError("fixed fit split size changed")
    save_torch(store,prefix+"/initial.pt",initial,kind="initial_weights")
    model_seed = base+(41001 if arm=="A" else 42001)
    order_seed = base+20002
    rng = np.random.Generator(np.random.PCG64(order_seed))
    rng_initial = rng.bit_generator.state
    training_x,mask,target = models.training_batch(train,arm)
    optimizer = torch.optim.AdamW(model.parameters(),lr=1e-3,weight_decay=1e-4)
    store.write_json(prefix+"/config.json",{"block":block,"arm":arm,"model_seed":model_seed,"order_seed":order_seed,
                    "order_rng_initial":rng_initial,"epochs":64,"batch_size":32,
                    "optimizer":"torch.optim.AdamW","lr":1e-3,"weight_decay":1e-4,
                    "adam_betas":[.9,.999],"adam_eps":1e-8,"dtype":"float32","initial_sha256":initial_sha,
                    "parameters":sum(p.numel() for p in model.parameters()),
                    "dataset_manifest_sha256":dataset.manifest_sha256},kind="fit_config")
    endpoint(store,model,train,arm,"initial",block,"train")
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
                logits = model(models.slice_input(training_x,indices)).squeeze(-1).masked_fill(~mask[indices],-1e4)
                loss = -(target[indices]*torch.log_softmax(logits,dim=-1)).sum(-1).mean()
                if not torch.isfinite(loss):
                    raise ArithmeticError("nonfinite fixed soft CE")
                loss.backward()
                gradients = {k:p.grad for k,p in model.named_parameters()}
                if any(g is None or not torch.isfinite(g).all() for g in gradients.values()):
                    raise ArithmeticError("missing/nonfinite scorer gradient")
                grad_l2 = math_sqrt_sum(gradients)
                grad_max = max(float(g.detach().abs().max()) for g in gradients.values())
                if grad_l2<=0:
                    raise ArithmeticError("zero total scorer gradient")
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
    endpoint(store,model,train,arm,"final",block,"train")
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
    args=phases.parser(__doc__,('dataset-input',)).parse_args(argv)
    from scripts.hmasd_admission import ENVIRONMENT_KEY,require_admission
    import os
    paths=json.loads(os.environ.get(ENVIRONMENT_KEY,'{}'))
    admission=require_admission(__file__,direction='uav_decision_generalization')
    store,admission,prior,root=phases.accepted_store(__file__,args,admission,paths)
    try:
        threads=models.cpu_thread_environment()
        phases.verify_sources(root)
        dataset,locator=phases.bound_dataset(args.dataset_input,args.dataset_input_sha256,old=True,training_only=True)
        phases.register_external_roots(store,dataset.root)
        store.write_json('config.json',{'admission':admission,'contract':c.frozen_contract(),'direction_source_sha256':phases.source_identity(root),
            'dataset_locator':locator,'dataset_locator_sha256':args.dataset_input_sha256,
            'prior_bill_sha256':args.budget_ledger_sha256,'threads':threads},kind='fit_config')
        store.bill.start_gpu()
        models.configure_float32()
        import torch
        import numpy as np
        if torch.__version__!='2.7.0+cu118' or np.__version__!='1.26.3':
            raise RuntimeError('frozen numerical dependency versions unavailable')
        torch.cuda.reset_peak_memory_stats()
        for block in (1,2,3):
            for arm in ('A','R'):
                fit(store,dataset,block,arm)
        torch.cuda.synchronize();store.bill.stop_gpu()
        endpoint_contexts=sum(store.bill.delta['endpoint_'+arm+'_contexts'] for arm in ('A','R','N'))
        if (store.bill.delta['optimizer_updates_completed']!=3072 or store.bill.delta['fits_completed']!=6
                or endpoint_contexts!=3072):
            raise AssertionError('incomplete fixed fits')
        status=store.status('complete')
        store.write_json('summary.json',{**status,'launch_sha':args.launch_sha,
            'contract_sha256':c.digest(c.frozen_contract()),'dataset_manifest_sha256':locator['manifest_sha256'],
            'weights_frozen_before_fresh':True,'endpoint_contexts':endpoint_contexts,
            'torch_version':torch.__version__,'numpy_version':np.__version__,
            'gpu_peak_allocated_bytes':torch.cuda.max_memory_allocated(),
            'gpu_peak_reserved_bytes':torch.cuda.max_memory_reserved()},kind='fit_summary')
        return 0
    except BaseException as exc:
        store.bill.stop_gpu();phases.failure(store,exc);raise
    finally:
        store.close()


if __name__=='__main__':
    raise SystemExit(main())
