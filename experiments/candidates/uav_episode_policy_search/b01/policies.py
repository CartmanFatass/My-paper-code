"""One original paid FP32 P0 query, one innovation, and a whole-episode head."""
import numpy as np
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.policies import Policy as OriginalPolicy
from experiments.candidates.uav_fleet_adaptation.b02.policies import categorical_probabilities,categorical_index
from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS
from .search import head

class Policy:
    def __init__(self,parent,actor,*,world,agent,sampling_root,family=None,theta=None,zero_check=False):
        self.base=OriginalPolicy(parent,actor,world=world,agent=agent,sampling_root=sampling_root)
        self.counters=self.base.counters
        self.family,self.theta,self.zero_check=family,theta,zero_check
        self.counters.update(head_requests=0,head_mac_terms=0,zero_head_requests=0, zero_head_mac_terms=0)
    def query(self,row,tick,nav):
        answer=self.base.query(row,tick,nav)
        if self.family is None: return answer
        p0=answer['probabilities'].copy()
        initial_choice=answer['action_index']
        logits,hbar=head(answer['logits'],answer['hidden'],self.theta,self.family)
        probabilities=categorical_probabilities(logits)
        choice=categorical_index(probabilities,answer['innovation'])
        self.counters['head_requests']+=1
        self.counters['head_mac_terms']+=3456 if self.family=='CONT' else 0
        zero_error=0.
        if self.zero_check:
            zero,_=head(answer['logits'],answer['hidden'],np.zeros_like(self.theta),self.family)
            zp=categorical_probabilities(zero)
            zero_error=float(np.max(np.abs(zp-p0)))
            if zero_error!=0. or categorical_index(zp,answer['innovation'])!=initial_choice:
                raise AssertionError('zero head observed-context identity failed')
            self.counters['zero_head_requests']+=1
            self.counters['zero_head_mac_terms']+=3456 if self.family=='CONT' else 0
        positive=probabilities>0
        answer.update(head_logits=logits,hbar=hbar,p0_probabilities=p0,p0_action_index=initial_choice,
                      zero_head_error=zero_error,probabilities=probabilities,action_index=choice,command=COMMANDS[choice].copy(),
                      entropy=float(-np.sum(probabilities[positive]*np.log(probabilities[positive]))))
        return answer
