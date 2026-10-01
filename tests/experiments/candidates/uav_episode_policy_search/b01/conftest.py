"""Explicit Python synthetic adapter; no native environment, pinned P0 or deployment panel."""
from dataclasses import replace
import numpy as np
import pytest
import torch
from experiments.candidates.uav_episode_policy_search.b01.contract import FROZEN
from experiments.candidates.uav_episode_policy_search.b01.study import _execute
from experiments.candidates.uav_fleet_adaptation.b02.model import make_student,state_digest
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.environment import original_layout
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.physics import scalar_state

class SyntheticEnv:
    def __init__(self,horizon):
        self.env=self;self.n_uavs=5;self.horizon=horizon
        self._path_loss_cache_generation=1;self._path_loss_cache_misses=260
        self.steps=0;self.fail_at=None
    def _state(self):
        self.state=scalar_state(self.uav_positions,self.users,self.transmitter_mask,self.current_step,self.horizon)
        self.sinr_matrix=self.state['sinr'];self.uav_sinr_matrix=self.state['peer_sinr'];self.connections=self.state['connections']
        return self.state['observations'].copy()
    def _info(self):
        global_info=dict(connections=self.connections.copy(),sinr_matrix=self.sinr_matrix.copy(),served_users=self.state['served'])
        return dict(state_info=dict(uav_positions=self.uav_positions.copy(),user_positions=self.users.copy()),
                    infos_dict={'uav_0':{'global':global_info}},rewards_dict={'uav_0':self.state['reward']})
    def reset(self,seed):
        self.uav_positions,self.users=original_layout(seed);self.transmitter_mask=np.ones(5,dtype=bool);self.current_step=0
        self._path_loss_cache_generation+=1;self._path_loss_cache_misses=260
        return self._state(),self._info()
    def set_transmitter_mask(self,mask):
        self.transmitter_mask=mask.copy();return self._state()
    def _dict_to_array(self,rows): return rows
    def step(self,commands):
        if self.fail_at==self.steps: raise RuntimeError('synthetic interrupted step')
        self.uav_positions=np.clip(self.uav_positions+commands.astype(np.float64)*30.,[0.,0.,50.],[1000.,1000.,150.])
        self.current_step+=1;self.steps+=1;self._path_loss_cache_generation+=1;self._path_loss_cache_misses=260
        obs=self._state();return obs,None,self.current_step==self.horizon,False,self._info()

@pytest.fixture(scope='module')
def tiny(tmp_path_factory):
    root=tmp_path_factory.mktemp('episode_search_synthetic')
    for name in ('raw','search'): (root/name).mkdir()
    protocol=replace(FROZEN,iterations=2,directions=2,horizon=8,training_bases=(90100,90200),worlds=(90300,90301),
                     training_motion_roots=(90400,90401),perturbation_root=90500,evaluation_motion_roots=(90600,90601),
                     bootstrap_seed=90700,constructor_seed=90800,bootstrap_resamples=31).validate()
    torch.set_num_threads(1)
    actor=make_student(90900).eval().requires_grad_(False)
    env=SyntheticEnv(protocol.horizon)
    batch=dict(scientific_execution=False,actual=dict(fits_started=0,fits_completed=0,updates=0,constructor_calls=1,
               constructor_resets=1,native_dense_power_slots=275,native_unique_distance_pairs=260,zero_decisions=0),
               inflight={},search_artifacts=[],initial_parent_state_sha256=state_digest(actor.state_dict()))
    _execute(root,actor,env,protocol,batch,lambda:None)
    return root,protocol,actor,batch,env
