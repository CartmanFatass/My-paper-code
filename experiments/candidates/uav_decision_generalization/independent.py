"""Independent field and functional layer reconstruction; no candidate predictor calls."""
from __future__ import annotations
import math


def fields(features,arm):
    import torch
    expected={'initial_uav_xyz','user_xy','bs_xyz','plans','legal_mask','display_order'}
    if set(features)!=expected:
        raise ValueError('independent reader feature schema mismatch')
    slots=features['display_order'][:]
    plans={p['construction_slot']:p for p in features['plans']}
    if sorted(slots)!=sorted(plans) or features['legal_mask']!=[i in plans for i in range(8)]:
        raise ValueError('independent reader legal/display inversion mismatch')
    xyz=[[float(v)/5000 for v in row] for row in features['initial_uav_xyz']]
    users=[[float(v)/5000 for v in row] for row in features['user_xy']]
    bs=[float(v)/5000 for v in features['bs_xyz']]
    packed={key:[] for key in ('U','Y','B','M','E_UY','E_UU','E_UB')}
    nrows=[]
    def edge(a,b):
        delta=[a[i]-b[i] for i in range(3)]
        return delta+[sum(v*v for v in delta)]
    for slot in slots:
        p=plans[slot];target=[[float(v)/5000 for v in row] for row in p['assigned_targets_xyz']]
        metadata=[float(p['kind']==k) for k in ('kmeans_plain','subset_relay','subset_flat')]
        metadata +=[float(p['k']==k) for k in (4,5,6)]+[float(slot==i) for i in range(8)]
        nrows.append([v for row in xyz for v in row]+[v for row in users for v in row]+bs+[v for row in target for v in row]+metadata)
        packed['U'].append([xyz[i]+target[i]+[float(i==j) for j in range(6)] for i in range(6)])
        packed['Y'].append([users[i]+[float(i==j) for j in range(50)] for i in range(50)])
        packed['B'].append(bs);packed['M'].append(metadata)
        packed['E_UY'].append([[edge(xyz[i],users[j]+[0.])+edge(target[i],users[j]+[0.]) for j in range(50)] for i in range(6)])
        packed['E_UU'].append([[edge(xyz[i],xyz[j])+edge(target[i],target[j]) for j in range(6) if i!=j] for i in range(6)])
        packed['E_UB'].append([edge(xyz[i],bs)+edge(target[i],bs) for i in range(6)])
    if arm=='N':
        return torch.tensor(nrows,dtype=torch.float32),slots
    t={k:torch.tensor(v,dtype=torch.float32) for k,v in packed.items()}
    if arm=='A':
        return torch.cat([t[k].reshape(len(slots),-1) for k in packed],dim=-1),slots
    if arm!='R':
        raise ValueError('unknown independent arm')
    return t,slots


def logits(state,x,arm):
    import torch
    import torch.nn.functional as F
    used=set()
    if any(t.dtype!=torch.float32 or t.device.type!='cpu' for t in state.values()):
        raise ValueError('independent float32 CPU weights required')
    def linear(value,name):
        used.update((name+'.weight',name+'.bias'))
        return F.linear(value,state[name+'.weight'],state[name+'.bias'])
    def two(value,prefix,final=False):
        value=linear(F.gelu(linear(value,prefix+'0'),approximate='none'),prefix+'2')
        return F.gelu(value,approximate='none') if final else value
    with torch.inference_mode():
        if arm in ('A','N'):
            result=linear(F.gelu(linear(F.gelu(linear(x,'0'),approximate='none'),'2'),approximate='none'),'4')
        elif arm=='R':
            u=two(x['U'],'encoders.U.',True);y=two(x['Y'],'encoders.Y.',True);b=two(x['B'],'encoders.B.',True)
            for layer in range(3):
                incoming=[]
                for receiver in range(6):
                    uy=[];uu=[]
                    for sender in range(50):
                        uy.append(two(torch.cat((u[...,receiver,:],y[...,sender,:],x['E_UY'][...,receiver,sender,:]),-1),f'messages.{layer}.UY.'))
                    peers=[j for j in range(6) if j!=receiver]
                    for position,sender in enumerate(peers):
                        uu.append(two(torch.cat((u[...,receiver,:],u[...,sender,:],x['E_UU'][...,receiver,position,:]),-1),f'messages.{layer}.UU.'))
                    ub=two(torch.cat((u[...,receiver,:],b,x['E_UB'][...,receiver,:]),-1),f'messages.{layer}.UB.')
                    aggregate=torch.cat((u[...,receiver,:],torch.stack(uy,-2).mean(-2),torch.stack(uu,-2).mean(-2),ub),-1)
                    incoming.append(F.gelu(u[...,receiver,:]+two(aggregate,f'updates.{layer}.'),approximate='none'))
                u=torch.stack(incoming,-2)
            result=linear(F.gelu(linear(torch.cat((u.mean(-2),y.mean(-2),b,x['M']),-1),'readout.0'),approximate='none'),'readout.2')
        else:
            raise ValueError('unknown independent arm')
    if used!=set(state) or not torch.isfinite(result).all():
        raise ValueError('independent parameter schema/nonfinite output')
    return result.squeeze(-1).tolist()


def comparison(independent,saved):
    if len(independent)!=len(saved):
        raise ValueError('logit dimensions changed')
    flags=[abs(a-b)<=1e-6+1e-5*abs(b) for a,b in zip(independent,saved)]
    return {'component_within_tolerance':flags,'all_within_tolerance':all(flags),
            'max_absolute':max(abs(a-b) for a,b in zip(independent,saved)),'tolerance':{'rtol':1e-5,'atol':1e-6}}
