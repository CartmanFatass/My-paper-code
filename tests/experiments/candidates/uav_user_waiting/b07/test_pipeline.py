"""Stubbed collection/failure tests, with no production native or C queries."""
from collections import Counter
import json
from pathlib import Path

import numpy as np
import pytest

from experiments.candidates.uav_user_waiting.b02 import protocol as wire
from experiments.candidates.uav_user_waiting.b07 import collect,study,protocol as p
from experiments.candidates.uav_user_waiting.b07.manager import Scheduler


class StubC:
    def __init__(self,history):
        assert history is False
        self.counters={'calls':0};self._nav_index=0
    def act(self,observation,tick):
        self.counters['calls']+=1
        return np.array([int(tick>=4),0,0],np.float32),dict(fallback=False,selected_index=13)


class StubEnv:
    def __init__(self):
        self.env=self;self.agents=[f'uav_{i}' for i in range(5)]
        self.sites=np.column_stack((np.arange(50)*19.,np.arange(50)*17.))
        self.initial=np.asarray([[100,150,90],[950,950,149],[0,500,50],[400,300,100],[800,0,70]],float)
        self.transmitter_mask=np.ones(5,bool);self.tick=0;self.position=self.initial.copy();self.refreshes=0
        self.last_values=None
    def _get_observation(self,agent):
        i=int(agent[-1]);obs=np.zeros(104,np.float32)
        obs[:3]=(self.position[i]-wire.LOW)/(wire.HIGH-wire.LOW);obs[-1]=self.tick/8
        return obs
    def _dict_to_array(self,rows): return np.stack([rows[a] for a in self.agents])
    def observations(self): return self._dict_to_array({a:self._get_observation(a) for a in self.agents})
    def reset(self,seed):
        self.position=self.initial.copy();self.tick=0;self.transmitter_mask[:]=True
        return self.observations(),dict(state_info=dict(uav_positions=self.position.copy(),user_positions=self.sites.copy()))
    def set_transmitter_mask(self,mask):
        self.refreshes+=1;self.transmitter_mask=np.array(mask,copy=True)
        if self.last_values is not None: self.last_values[:]=np.nan
    def step(self,commands):
        self.tick+=1;self.position=np.clip(self.position+30.*commands,wire.LOW,wire.HIGH)
        values=np.full((5,50),-np.inf)
        values[self.transmitter_mask]=-20.
        connected=np.zeros((5,50),bool)
        if self.transmitter_mask[0]: values[0,0]=10.;connected[0,0]=True
        served=int(connected.sum());reward=.7*served/50+.3*(7./30. if served else 0.)
        self.last_values=values
        info=dict(infos_dict={'uav_0':{'global':dict(sinr_matrix=values,connections=connected)}},
            rewards_dict={'uav_0':reward},state_info=dict(uav_positions=self.position.copy()))
        return self.observations(),None,False,self.tick==8,info
    def close(self): pass


def setup(monkeypatch,tmp_path):
    env=StubEnv();obs,info=env.reset(123)
    baseline=dict(positions=np.asarray([env.initial]),true_sites=env.sites,
                  map_packet=np.frombuffer(wire.encode_map(env.sites),np.uint8),observations=np.asarray([obs]))
    monkeypatch.setattr(collect.p,'load_raw',lambda *args:baseline)
    (tmp_path/'raw').mkdir()
    return env,dict(path='synthetic-only',sha256='a'*64,bytes=1)


def test_delayed_collection_cadence_no_modeled_history_and_copy_before_refresh(monkeypatch,tmp_path):
    env,identity=setup(monkeypatch,tmp_path);counts=Counter();accounting={}
    row,raw,_=collect.collect_episode(env,123,tmp_path,counts,identity,horizon=8,controller_type=StubC,accounting=accounting)
    assert counts['team_steps']==8 and counts['worker_current_c_calls']==10
    assert counts['mask_refreshes']==env.refreshes==2
    assert not np.isnan(raw['sinr']).any()
    assert raw['mask'][0]==raw['mask'][1]==31
    assert np.all(raw['commands'][:6]==0) and np.all(raw['commands'][6:,:,0]==1)
    assert not any('history' in key for key in raw)
    assert not bool(raw['grant_feedback_used'])
    assert row['proposal_command_edits']==0
    assert accounting['model_work']['candidate_requests']==30


def test_c_exception_preserves_original_and_partial_paid_raw(monkeypatch,tmp_path):
    env,identity=setup(monkeypatch,tmp_path);counts=Counter();accounting={}
    class BrokenC(StubC):
        def act(self,observation,tick):
            self.counters['calls']+=1
            raise RuntimeError('original C failure')
    with pytest.raises(RuntimeError,match='original C failure'):
        collect.collect_episode(env,123,tmp_path,counts,identity,horizon=8,controller_type=BrokenC,accounting=accounting)
    assert counts['worker_current_c_calls_attempted']==1 and counts['worker_current_c_calls_failed']==1
    with np.load(tmp_path/'raw/C2_123.npz',allow_pickle=False) as raw:
        assert str(raw['episode_failure_message'])=='original C failure'
        assert int(raw['completed_steps'])==0 and raw['current_c_attempted'].sum()==1
    assert accounting['current_c_failed']==1


def test_reset_pairing_fails_before_any_controller_call(monkeypatch,tmp_path):
    env,identity=setup(monkeypatch,tmp_path);env.initial[0,0]+=1
    counts=Counter()
    with pytest.raises(ValueError,match='reset pairing'):
        collect.collect_episode(env,123,tmp_path,counts,identity,horizon=8,controller_type=StubC)
    assert counts['worker_current_c_calls_attempted']==0


def test_base_raw_survives_reducer_and_close_failure(monkeypatch,tmp_path):
    monkeypatch.setattr(study.torch,'set_num_threads',lambda n:None)
    monkeypatch.setattr(study.torch,'set_num_interop_threads',lambda n:None)
    monkeypatch.setattr(study.p,'SEEDS',(123,))
    monkeypatch.setattr(study.p,'load_baselines',lambda root,**kwargs:({}, {},{123:{}},{}))
    monkeypatch.setattr(study.p,'frozen_config',lambda *args:{'fixed':'synthetic'})
    class Env:
        env=None
        def __init__(self): self.env=self
        def close(self): raise RuntimeError('secondary close failure')
    monkeypatch.setattr(study,'factory',lambda seed:Env())
    monkeypatch.setattr(study,'collect_episode',lambda *args,**kwargs:({'seed':123},{'completed_steps':np.array(8),'evidence':np.arange(8)},{}))
    def fail(*args): raise ValueError('primary reduction failure')
    monkeypatch.setattr(study,'replay_lrs',fail)
    result=study.run_batch(tmp_path,'synthetic','b'*40)
    assert result['status']=='INCOMPLETE_TECHNICAL_FAILURE'
    assert result['error']['message']=='primary reduction failure'
    assert result['accounting_errors'][0]['phase']=='environment_close'
    assert len(result['incomplete_raw'])==1
    with np.load(tmp_path/'raw/C2_123.npz',allow_pickle=False) as raw:
        np.testing.assert_array_equal(raw['evidence'],np.arange(8))


def test_canonical_baseline_locator_stays_outside_source_snapshot():
    assert p.baseline_directory(Path('/author/main/runs/uav_user_waiting/b07'))==Path('/author/main/runs/uav_user_waiting/b06_fair_model_a01/raw')
    with pytest.raises(ValueError): p.baseline_directory(Path('relative'))


def test_collector_reducer_failure_preserves_complete_paid_trajectory(monkeypatch,tmp_path):
    env,identity=setup(monkeypatch,tmp_path);counts=Counter();accounting={}
    def fail(*args): raise ValueError('collector reducer failure')
    monkeypatch.setattr(collect,'episode_metrics',fail)
    with pytest.raises(ValueError,match='collector reducer failure'):
        collect.collect_episode(env,123,tmp_path,counts,identity,horizon=8,controller_type=StubC,accounting=accounting)
    assert counts['team_steps']==8 and counts['worker_current_c_calls']==10
    assert accounting['model_work']['candidate_requests']==30
    with np.load(tmp_path/'raw/C2_123.npz',allow_pickle=False) as raw:
        assert int(raw['completed_steps'])==8
        assert str(raw['episode_failure_message'])=='collector reducer failure'
        assert not np.isnan(raw['sinr']).any()
        assert raw['current_c_completed'].sum()==10
