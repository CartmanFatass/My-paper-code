"""Six final assets; fixed batches, continuous prefix orders and retained exposures."""
from __future__ import annotations
import hashlib
import math
import time
from . import contract as c, evidence as e, bank, model


class ContinuousOrder:
    def __init__(self,n,rng):
        self.n,self.rng,self.pending,self.cursor=n,rng,[],0
    def batch(self,size=32):
        out=[]
        while len(out)<size:
            if self.cursor==len(self.pending):
                self.pending=self.rng.permutation(self.n).tolist();self.cursor=0
            take=min(size-len(out),len(self.pending)-self.cursor)
            out.extend(self.pending[self.cursor:self.cursor+take]);self.cursor+=take
        return out


def subset_indices(rewards,rng):
    import numpy as np
    rewards=np.asarray(rewards,dtype=np.float64)
    if rewards.ndim!=1 or len(rewards)==0 or not np.isfinite(rewards).all():
        raise ValueError('finite complete label vector')
    best=int(np.argmax(rewards))
    if len(rewards)<=16:
        ids=list(range(len(rewards)))
    else:
        others=np.delete(np.arange(len(rewards)),best)
        ids=sorted([best]+rng.choice(others,15,replace=False).tolist())
    valid=[True]*len(ids)+[False]*(16-len(ids))
    padded=ids+[0]*(16-len(ids))
    q=np.zeros(16,dtype=np.float64)
    selected=rewards[ids];logq=(selected-selected.max())/.02
    logq=logq-math.log(float(np.exp(logq).sum()))
    q[:len(ids)]=np.exp(logq)
    entropy=-float(np.sum(q[:len(ids)]*logq))
    return padded,valid,q.astype(np.float32),entropy


def training_batch(records,subrng):
    import numpy as np
    packed={k:[] for k in c.SHAPES};ids=[];masks=[];qs=[];entropies=[];js=[]
    for record in records:
        rewards=bank.rewards(record)
        indices,mask,q,entropy=subset_indices(rewards,subrng)
        t=model.fields(bank.features(record),indices)
        for k in packed:
            packed[k].append(t[k])
        ids.append(indices);masks.append(mask);qs.append(q);entropies.append(entropy)
        js.append([rewards[i] for i in indices])
    return ({k:np.concatenate(v,axis=0) for k,v in packed.items()},ids,np.asarray(masks),
            np.asarray(qs),entropies,np.asarray(js))


def endpoint(store,network,view,fit,split,exposure=None):
    import numpy as np
    choices=[];scores=[];offsets=[0];errors=[];counts=[];records=[]
    start=c.TRAIN_START if split=='train' else c.FRESH_START
    for world in range(start,start+512):
        r=view.load(world);f=bank.features(r)
        logits,timing=model.score(network,f,store.bill,'endpoint')
        store.bill.charge('endpoint_contexts')
        selected=model.choose(logits)
        rewards=np.asarray(bank.rewards(r),dtype=np.float64)
        # Ranking error uses the full soft target; absolute logits have an arbitrary offset.
        z=np.asarray(logits,dtype=np.float64); logp=z-np.log(np.exp(z-z.max()).sum())-z.max()
        logq=(rewards-rewards.max())/.02;logq-=np.log(np.exp(logq).sum());q=np.exp(logq)
        candidate_error=-q*logp
        errors.extend(candidate_error.tolist());scores.extend(logits);offsets.append(len(scores))
        local_counts=([0]*len(logits) if exposure is None else exposure[world-c.TRAIN_START].tolist())
        counts.extend(local_counts)
        entropy=-float(np.sum(q*logq));ce=-float(np.sum(q*logp))
        records.append({'world':world,'choice':selected,'teacher':int(rewards.argmax()),'J':float(rewards[selected]),
                        'regret':float(rewards.max()-rewards[selected]),'CE':ce,'target_entropy':entropy,'KL':ce-entropy,
                        'logit_margin':float(sorted(logits,reverse=True)[0]-sorted(logits,reverse=True)[1]) if len(logits)>1 else None,
                        'timing':timing,'candidate_training_count_zero':sum(x==0 for x in local_counts) if exposure is not None else None})
        choices.append(selected)
    relative=f'raw/endpoints/{fit["id"]}/{split}.npz'
    e.npz_write(store,relative,{'scores':np.asarray(scores,dtype=np.float32),'offsets':np.asarray(offsets,dtype=np.int64),
                              'per_candidate_CE_terms':np.asarray(errors,dtype=np.float64),'training_counts':np.asarray(counts,dtype=np.int64),
                              'records':np.asarray(e.encoded(records).decode('ascii'))})
    store.write(f'endpoints/{fit["id"]}/{split}-summary.json',{'fit':fit,'split':split,'scope':'common512 probe' if split=='train' else 'common512 fresh',
                'mean_regret':float(np.mean([r['regret'] for r in records])),'max_regret':max(r['regret'] for r in records),
                'mean_KL':float(np.mean([r['KL'] for r in records])),'choices':choices,'full_candidate_artifact':relative})
    return relative


def fit_once(store,view,fit,initial_hashes,engineering):
    import numpy as np
    import torch
    store.bill.charge('fits')
    network=model.build(fit['model_seed'])
    initial={k:v.detach().cpu().clone() for k,v in network.state_dict().items()}
    initial_digest=model.digest(initial)
    stream=fit['stream']
    if stream in initial_hashes and initial_hashes[stream]!=initial_digest:
        raise AssertionError('same-stream initial weights differ')
    if stream not in initial_hashes:
        initial_hashes[stream]=initial_digest
        e.torch_write(store,f'raw/initial/stream{stream}.pt',{'state':initial,'seed':fit['model_seed'],'state_sha256':initial_digest})
    world_rng=np.random.default_rng(fit['order_seed']);subset_rng=np.random.default_rng(fit['subset_seed'])
    order=ContinuousOrder(fit['n'],world_rng)
    sizes=[len(bank.rewards(view.load(c.TRAIN_START+i))) for i in range(fit['n'])]
    exposures=[np.zeros(n,dtype=np.uint32) for n in sizes];world_exposure=np.zeros(fit['n'],dtype=np.uint32)
    update_path=f'raw/fit/{fit["id"]}/updates.jsonl.gz'
    trace=e.Trace(e.relative_path(store.root,update_path),store.bill)
    previous=initial_digest
    started=time.perf_counter()
    try:
        with store.bill.gpu():
            c.configure(cuda=True,expected=store.input_manifest['runtime'])
            network=network.to('cuda:0')
            if engineering:
                from .reader import engineering_checks
                engineering_checks(store,network,initial,view)
            optimizer=torch.optim.AdamW(network.parameters(),lr=.001,weight_decay=.0001,betas=(.9,.999),eps=1e-8)
            network.train()
            for update in range(1,4097):
                local_worlds=order.batch(32);worlds=[c.TRAIN_START+i for i in local_worlds]
                records=[view.load(w) for w in worlds]
                packed,ids,mask,q,hq,rewards=training_batch(records,subset_rng)
                valid=int(mask.sum())
                subset_digest=hashlib.sha256(e.encoded({'worlds':worlds,'ids':ids,'mask':mask})).hexdigest()
                trace.write({'type':'attempt','fit':fit['id'],'update':update,'worlds':worlds,
                             'raw_indices':ids,'valid_mask':mask,'subset_identity_sha256':subset_digest})
                store.bill.charge('updates');store.bill.charge('training_world_presentations',32)
                store.bill.rows('training',512,valid)
                for i,subset,valid_mask in zip(local_worlds,ids,mask):
                    world_exposure[i]+=1
                    for j,okay in zip(subset,valid_mask):
                        if okay:
                            exposures[i][j]+=1
                t=time.perf_counter()
                tensors={k:torch.from_numpy(v).to('cuda:0') for k,v in packed.items()}
                q_t=torch.from_numpy(q).to('cuda:0');mask_t=torch.from_numpy(mask).to('cuda:0')
                optimizer.zero_grad(set_to_none=True)
                z=network(tensors).reshape(32,16)
                if not torch.isfinite(z).all():
                    raise FloatingPointError('nonfinite training logits')
                z=z.masked_fill(~mask_t,-torch.inf)
                logp=torch.log_softmax(z,dim=-1).masked_fill(~mask_t,0.)
                ce=-(q_t*logp).sum(-1);loss=ce.mean()
                loss.backward()
                grad_square=0.
                for parameter in network.parameters():
                    if parameter.grad is None or not torch.isfinite(parameter.grad).all():
                        raise FloatingPointError('nonfinite/missing gradient')
                    grad_square+=float(parameter.grad.detach().double().square().sum())
                optimizer.step();torch.cuda.synchronize()
                active_seconds=time.perf_counter()-t
                state={k:v.detach().cpu().clone() for k,v in network.state_dict().items()}
                if not torch.isfinite(loss) or any(not torch.isfinite(v).all() for v in state.values()):
                    raise FloatingPointError('nonfinite loss/parameter')
                p=torch.softmax(z,dim=-1).detach().cpu().numpy()
                pred_entropy=-np.sum(np.where(p>0,p*np.log(np.maximum(p,1e-45)),0),axis=-1)
                choices=z.argmax(-1).detach().cpu().numpy()
                subset_regret=rewards.max(-1)-rewards[np.arange(32),choices]
                digest=model.digest(state)
                store.bill.rows_done('training',512);store.bill.charge('updates_completed')
                trace.write({'type':'complete','fit':fit['id'],'update':update,'worlds':worlds,'raw_indices':ids,'valid_mask':mask,
                             'CE':ce.detach().cpu().tolist(),'target_entropy':hq,'KL':(ce.detach().cpu().numpy()-hq),
                             'prediction_entropy':pred_entropy,'subset_regret':subset_regret,'grad_norm':math.sqrt(grad_square),
                             'parameter_movement':model.movement(state,initial),'before_sha256':previous,'after_sha256':digest,
                             'subset_identity_sha256':subset_digest,
                             'finite':True,'active_gpu_call_seconds':active_seconds,
                             'counters_before_post_update_resource_check':store.bill.counter_snapshot()})
                store.bill.check()
                previous=digest
                if update%128==0:
                    store.progress('fit',fit=fit['id'],updates=update)
            checkpoint={'state':state,'fit':fit,'initial_sha256':initial_digest,'final_sha256':previous,
                        'launch_sha':store.launch_sha,'input_sha256':store.input_sha256,'updates':4096,'world_presentations':131072,
                        'optimizer':cpu_state(optimizer.state_dict()),'fit_wall_seconds':time.perf_counter()-started}
            path=e.torch_write(store,f'raw/fit/{fit["id"]}/final.pt',checkpoint)
            offsets=np.concatenate(([0],np.cumsum(sizes)))
            e.npz_write(store,f'raw/fit/{fit["id"]}/exposure.npz',{'world_counts':world_exposure,
                         'candidate_counts':np.concatenate(exposures),'offsets':offsets})
            endpoint(store,network,view,fit,'train',exposures)
            del optimizer,network
            torch.cuda.empty_cache()
        store.bill.charge('fits_completed')
        return {'fit':fit,'path':str(path.relative_to(store.root)),'sha256':e.sha(path),'initial_sha256':initial_digest,'final_sha256':previous}
    finally:
        trace.close();store.register(update_path)


def cpu_state(value):
    """Detach optimizer storage before ending the GPU reservation."""
    if isinstance(value,dict):
        return {k:cpu_state(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):
        return type(value)(cpu_state(v) for v in value)
    return value.detach().cpu().clone() if hasattr(value,'detach') else value


def completed_updates(rows):
    """Read exactly one preserved pre-effect identity and completion per update."""
    rows=iter(rows)
    for attempted in rows:
        complete=next(rows,None)
        keys=('fit','update','worlds','raw_indices','valid_mask','subset_identity_sha256')
        if (attempted.get('type')!='attempt' or complete is None or complete.get('type')!='complete'
            or any(e.encoded(attempted[k])!=e.encoded(complete[k]) for k in keys)):
            raise AssertionError('incomplete or changed attempted-update identity')
        yield complete
