"""Endpoint R205441; constructors and forwards are called only inside admission."""
from __future__ import annotations
import hashlib
import math
import time
from . import contract as c, evidence as e


def fields(features, indices=None):
    import numpy as np
    m=c.validate_features(features)
    indices=list(range(m)) if indices is None else list(indices)
    if any(type(i) is not int or not 0<=i<m for i in indices):
        raise ValueError('legal raw indices required')
    targets=np.asarray(features['layouts_xyz'],dtype=np.float64)[indices]/5000.
    users=np.asarray(features['users_xy'],dtype=np.float64)/5000.
    bs=np.asarray(features['bs_xyz'],dtype=np.float64)/5000.
    n=len(indices)
    user_xyz=np.concatenate((users,np.zeros((50,1))),axis=-1)
    peers=np.asarray([[j for j in range(6) if j!=i] for i in range(6)])
    def edge(a,b):
        delta=a-b
        return np.concatenate((delta,np.sum(delta*delta,axis=-1,keepdims=True)),axis=-1)
    result={'U':np.concatenate((targets,np.broadcast_to(np.eye(6),(n,6,6))),axis=-1),
            'Y':np.broadcast_to(np.concatenate((users,np.eye(50)),axis=-1),(n,50,52)).copy(),
            'B':np.broadcast_to(bs,(n,3)).copy(),
            'M':np.asarray([[float(features['kinds'][i]==k) for k in c.KINDS]+[float(features['ks'][i]==k) for k in (4,5,6)] for i in indices]),
            'E_UY':edge(targets[:,:,None,:],user_xyz[None,None,:,:]),
            'E_UU':edge(targets[:,:,None,:],targets[:,peers,:]),'E_UB':edge(targets,bs)}
    return {k:np.asarray(v,dtype=np.float32) for k,v in result.items()}


def build(seed):
    import torch
    from torch import nn
    torch.manual_seed(seed)
    def two(width,final=False):
        layers=[nn.Linear(width,64),nn.GELU(),nn.Linear(64,64)]
        if final:
            layers.append(nn.GELU())
        return nn.Sequential(*layers)
    class EndpointR(nn.Module):
        def __init__(self):
            super().__init__()
            self.encoders=nn.ModuleDict({k:two(w,True) for k,w in [('U',9),('Y',52),('B',3)]})
            self.messages=nn.ModuleList([nn.ModuleDict({k:two(132) for k in ('UY','UU','UB')}) for _ in range(3)])
            self.updates=nn.ModuleList([two(256) for _ in range(3)])
            self.readout=nn.Sequential(nn.Linear(198,64),nn.GELU(),nn.Linear(64,1))
        def forward(self,t):
            u,y,b=[self.encoders[k](t[k]) for k in ('U','Y','B')]
            peers=torch.tensor([[j for j in range(6) if j!=i] for i in range(6)],device=u.device)
            for messages,update in zip(self.messages,self.updates):
                uy=messages['UY'](torch.cat((u.unsqueeze(-2).expand(*u.shape[:-1],50,64),
                    y.unsqueeze(-3).expand(*u.shape[:-2],6,50,64),t['E_UY']),dim=-1)).mean(-2)
                uu=messages['UU'](torch.cat((u.unsqueeze(-2).expand(*u.shape[:-1],5,64),u[...,peers,:],t['E_UU']),dim=-1)).mean(-2)
                ub=messages['UB'](torch.cat((u,b.unsqueeze(-2).expand(*u.shape[:-2],6,64),t['E_UB']),dim=-1))
                u=torch.nn.functional.gelu(u+update(torch.cat((u,uy,uu,ub),dim=-1)))
            return self.readout(torch.cat((u.mean(-2),y.mean(-2),b,t['M']),dim=-1)).squeeze(-1)
    model=EndpointR().float()
    if sum(p.numel() for p in model.parameters())!=c.PARAMETERS:
        raise AssertionError('fixed parameter count mismatch')
    return model


def digest(state):
    h=hashlib.sha256()
    for key,value in sorted(state.items()):
        a=value.detach().cpu().contiguous().numpy()
        h.update(e.encoded({'name':key,'dtype':str(a.dtype),'shape':list(a.shape)}));h.update(a.tobytes())
    return h.hexdigest()


def movement(state, initial):
    squares,maximum=0.,0.
    for key,value in state.items():
        delta=value.detach().cpu().double()-initial[key].double()
        squares+=float(delta.square().sum());maximum=max(maximum,float(delta.abs().max()))
    return {'l2':math.sqrt(squares),'max_absolute':maximum}


def choose(logits,indices=None):
    indices=list(range(len(logits))) if indices is None else list(indices)
    if not logits or len(indices)!=len(logits) or not all(math.isfinite(float(v)) for v in logits):
        raise ValueError('finite logits and raw marker inversion required')
    return indices[max(range(len(indices)),key=lambda i:(float(logits[i]),-indices[i]))]


def score(model, features, bill, phase, order=None):
    import torch
    n=c.validate_features(features)
    order=list(range(n)) if order is None else list(order)
    if sorted(order)!=list(range(n)):
        raise ValueError('complete raw display order required')
    output=[None]*n
    active=0.
    model.eval()
    with torch.inference_mode():
        for begin in range(0,n,c.CHUNK):
            indices=order[begin:begin+c.CHUNK]
            packed=fields(features,indices)
            bill.rows(phase,len(indices))
            t=time.perf_counter()
            tensors={k:torch.from_numpy(v).to('cuda:0') for k,v in packed.items()}
            logits=model(tensors)
            torch.cuda.synchronize()
            active+=time.perf_counter()-t
            if not torch.isfinite(logits).all():
                raise FloatingPointError('nonfinite complete-menu scores')
            values=logits.detach().cpu().tolist()
            bill.rows_done(phase,len(indices));bill.check()
            for i,v in zip(indices,values):
                output[i]=v
    return output, {'active_gpu_call_seconds':active,'chunk':64,'physical_candidates':n}
