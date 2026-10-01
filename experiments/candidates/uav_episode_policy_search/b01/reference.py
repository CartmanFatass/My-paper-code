"""Independent reader head arithmetic; no candidate worker/search imports."""
import numpy as np
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.reference import ReferencePolicy as OriginalReference
from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS

class ReferencePolicy:
    def __init__(self,parent,actor,*,world,agent,sampling_root,family=None,theta=None,zero_check=False):
        self.base=OriginalReference(parent,actor,world=world,agent=agent,sampling_root=sampling_root)
        self.counters=self.base.counters
        self.family,self.theta,self.zero_check=family,theta,zero_check
        self.counters.update(head_requests=0,head_mac_terms=0,zero_head_requests=0, zero_head_mac_terms=0)
    def query(self,row,tick,nav):
        result=self.base.query(row,tick,nav)
        if self.family is None: return result
        original=result['probabilities'].copy()
        initial=result['action_index']
        hidden=result['hidden'].astype(np.float64)
        normalized=hidden/max(1.,float(np.sqrt(np.sum(hidden*hidden,dtype=np.float64))))
        parameters=self.theta
        if parameters.dtype!=np.float64 or parameters.shape!=((28,) if self.family=='CAL' else (3484,)) or not np.isfinite(parameters).all():
            raise AssertionError('reference parameter contract')
        residual=parameters[1:28].copy()
        if self.family=='CONT': residual+=np.matmul(parameters[28:].reshape(27,128),normalized)
        logits=result['logits'].astype(np.float64)/np.exp(min(np.log(2.),max(-np.log(2.),float(parameters[0]))))+np.tanh(residual)
        if not np.isfinite(logits).all(): raise FloatingPointError('reference head nonfinite')
        weights=np.exp(logits-np.max(logits)); probability=weights/np.sum(weights,dtype=np.float64)
        cumulative=np.cumsum(probability,dtype=np.float64); cumulative[-1]=1.
        choice=int(np.searchsorted(cumulative,result['innovation'],side='right'))
        zero_error=0.
        if self.zero_check:
            # Explicitly evaluate each zero-head operation using the paid l0/h and innovation.
            zeros=np.zeros_like(parameters)
            zr=zeros[1:28].copy()
            if self.family=='CONT': zr+=np.matmul(zeros[28:].reshape(27,128),normalized)
            zl=result['logits'].astype(np.float64)/np.exp(zeros[0])+np.tanh(zr)
            zw=np.exp(zl-np.max(zl)); zp=zw/np.sum(zw,dtype=np.float64)
            zcdf=np.cumsum(zp,dtype=np.float64); zcdf[-1]=1.
            zero_error=float(np.max(np.abs(zp-original)))
            if zero_error!=0. or int(np.searchsorted(zcdf,result['innovation'],side='right'))!=initial:
                raise AssertionError('reference zero head identity')
            self.counters['zero_head_requests']+=1
            self.counters['zero_head_mac_terms']+=3456 if self.family=='CONT' else 0
        self.counters['head_requests']+=1
        self.counters['head_mac_terms']+=3456 if self.family=='CONT' else 0
        positive=probability>0
        result.update(head_logits=logits,hbar=normalized,p0_probabilities=original,p0_action_index=initial,
                      zero_head_error=zero_error,probabilities=probability,action_index=choice,command=COMMANDS[choice].copy(),
                      entropy=float(-np.sum(probability[positive]*np.log(probability[positive]))))
        return result
