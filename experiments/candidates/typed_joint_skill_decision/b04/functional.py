"""Independent field construction and literal CPU layers; never production forward."""
from __future__ import annotations
import math
from . import contract as c


def fields(features, indices=None):
    import torch
    c.validate_features(features)
    indices=list(range(len(features['layouts_xyz']))) if indices is None else list(indices)
    users=[[float(v)/5000. for v in row] for row in features['users_xy']]
    bs=[float(v)/5000. for v in features['bs_xyz']]
    packed={k:[] for k in c.SHAPES}
    def edge(a,b):
        delta=[a[j]-b[j] for j in range(3)]
        return delta+[sum(v*v for v in delta)]
    for raw in indices:
        target=[[float(v)/5000. for v in row] for row in features['layouts_xyz'][raw]]
        packed['U'].append([target[i]+[float(i==j) for j in range(6)] for i in range(6)])
        packed['Y'].append([users[i]+[float(i==j) for j in range(50)] for i in range(50)])
        packed['B'].append(bs)
        packed['M'].append([float(features['kinds'][raw]==kind) for kind in c.KINDS]+[float(features['ks'][raw]==k) for k in (4,5,6)])
        packed['E_UY'].append([[edge(target[i],users[j]+[0.]) for j in range(50)] for i in range(6)])
        packed['E_UU'].append([[edge(target[i],target[j]) for j in range(6) if j!=i] for i in range(6)])
        packed['E_UB'].append([edge(target[i],bs) for i in range(6)])
    return {k:torch.tensor(v,dtype=torch.float32) for k,v in packed.items()}


def logits(state,x):
    import torch
    import torch.nn.functional as F
    if any(t.dtype!=torch.float32 or t.device.type!='cpu' for t in state.values()):
        raise ValueError('CPU float32 source states required')
    used=set()
    def linear(v,name):
        used.update((name+'.weight',name+'.bias'))
        return F.linear(v,state[name+'.weight'],state[name+'.bias'])
    def two(v,p,final=False):
        v=linear(F.gelu(linear(v,p+'0'),approximate='none'),p+'2')
        return F.gelu(v,approximate='none') if final else v
    with torch.inference_mode():
        u=two(x['U'],'encoders.U.',True);y=two(x['Y'],'encoders.Y.',True);b=two(x['B'],'encoders.B.',True)
        # Independently assemble receiver rows and sender axes; shared primitive arithmetic.
        for layer in range(3):
            incoming=[]
            for receiver in range(6):
                a=u[:,receiver,:]
                uy=two(torch.cat((a[:,None,:].expand(-1,50,-1),y,x['E_UY'][:,receiver,:,:]),-1),f'messages.{layer}.UY.').mean(1)
                peers=[j for j in range(6) if j!=receiver]
                uu=two(torch.cat((a[:,None,:].expand(-1,5,-1),u[:,peers,:],x['E_UU'][:,receiver,:,:]),-1),f'messages.{layer}.UU.').mean(1)
                ub=two(torch.cat((a,b,x['E_UB'][:,receiver,:]),-1),f'messages.{layer}.UB.')
                incoming.append(F.gelu(a+two(torch.cat((a,uy,uu,ub),-1),f'updates.{layer}.'),approximate='none'))
            u=torch.stack(incoming,1)
        output=linear(F.gelu(linear(torch.cat((u.mean(1),y.mean(1),b,x['M']),-1),'readout.0'),approximate='none'),'readout.2').squeeze(-1)
    if used!=set(state) or not torch.isfinite(output).all():
        raise ValueError('functional parameter schema/nonfinite result')
    return output.tolist()


def score(state,features,bill,phase='functional_reader',order=None):
    n=c.validate_features(features)
    order=list(range(n)) if order is None else list(order)
    if sorted(order)!=list(range(n)):
        raise ValueError('complete functional candidate order required')
    out=[None]*n
    for begin in range(0,n,64):
        indices=order[begin:begin+64]
        x=fields(features,indices)
        bill.rows(phase,len(indices))
        result=logits(state,x)
        bill.rows_done(phase,len(indices));bill.check()
        for i,v in zip(indices,result):
            out[i]=v
    return out


def compare(a,b):
    if len(a)!=len(b) or not all(math.isfinite(float(x)) for x in list(a)+list(b)):
        raise ValueError('functional component identity/nonfinite mismatch')
    flags=[abs(x-y)<=1e-6+1e-5*abs(y) for x,y in zip(a,b)]
    pick=lambda xs:max(range(len(xs)),key=lambda i:(xs[i],-i))
    return {'all_within_tolerance':all(flags),'component_flags':flags,'max_abs_error':max(abs(x-y) for x,y in zip(a,b)),
            'functional_choice':pick(a),'GPU_choice':pick(b),'choice_discrepancy':pick(a)!=pick(b),
            'tolerance':{'atol':1e-6,'rtol':1e-5}}
