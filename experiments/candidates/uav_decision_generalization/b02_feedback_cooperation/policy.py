"""One actual navigation state; only the chosen original source is queried."""
from collections import deque
import numpy as np
from experiments.candidates.uav_fleet_adaptation.b02.controllers import initial_nav
from experiments.candidates.uav_fleet_transmission.b05_score_sampling.policies import FixedPolicy
from experiments.candidates.uav_fleet_transmission.b06_cadence.gate import own_count
from . import contract as c


class Switch:
    def __init__(self,arm):
        if arm not in c.ARMS:raise ValueError('unknown fixed program')
        self.arm=arm;self.window=deque(maxlen=4);self.next_tick=0
        self.count_decodes=self.gate_checks=0
    def observe(self,row,tick):
        if tick!=self.next_tick or type(tick)!=int:raise ValueError('requires consecutive primitive ticks')
        self.next_tick+=1
        q=-1;takeover=False
        if self.arm in c.PARENTS:
            q=own_count(row);self.count_decodes+=1;self.window.append(q)
            if tick>=4 and tick%4==0:
                self.gate_checks+=1;takeover=all(v==0 for v in self.window)
        source='C' if takeover else c.PARENTS.get(self.arm,self.arm)
        return {'query':tick%4==0,'q':q,'takeover':takeover,'source':source if tick%4==0 else ''}


class AgentProgram:
    def __init__(self,arm,row,*,world,agent,sampling_root,actors,factory=FixedPolicy):
        self.arm=arm;self.switch=Switch(arm);self.nav=initial_nav(row)
        self.command=np.zeros(3,dtype=np.float32);self.held=-1
        self.sources={}
        parent=c.PARENTS.get(arm,arm)
        for source in (('C',parent) if arm in c.PARENTS else (parent,)):
            actor=None if source in ('C','G') else actors[1 if source=='SL1' else 0]
            self.sources[source]=factory(c.OLD_ARMS[source],actor,world=world,agent=agent,sampling_root=sampling_root)
    def step(self,row,tick):
        gate=self.switch.observe(row,tick)
        if not gate['query']:return None
        source=gate['source'];before=self.nav
        answer=self.sources[source].query(row.copy(),tick,self.nav)
        self.nav=int(answer['next_nav']);self.command=answer['command'].copy();self.held=int(answer['action_index'])
        return {**gate,'nav_pre':before,'answer':answer}
    def counters(self):
        return {source:dict(policy.counters) for source,policy in self.sources.items()}
