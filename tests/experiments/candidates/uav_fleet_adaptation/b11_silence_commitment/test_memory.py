"""Focused branch fixtures: no physical/native rollout or model fitting."""
from copy import deepcopy
import numpy as np
import pytest
from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, WAYPOINTS, _features, MemoC
from experiments.candidates.uav_fleet_adaptation.b02.policies import indexed_uniform
from experiments.candidates.uav_fleet_adaptation.b02.model import make_student
from experiments.candidates.uav_fleet_adaptation.b08_local_gate import policies as ordinary
from experiments.candidates.uav_fleet_adaptation.b11_silence_commitment import policies,reference
from experiments.candidates.uav_fleet_adaptation.b11_silence_commitment.reading import paired_behavior


def observation(count=1,nav=6):
    row=np.zeros(104,dtype=np.float32)
    row[:3]=(* (WAYPOINTS[nav]/1000.),.5)
    for i in range(count):
        row[3+i*3:6+i*3]=(.1,.1,.3)
    return row


def response(row,nav,index=7,zero_service=False):
    n=int(np.count_nonzero(row[3:63].reshape(20,3)[:,2]>0))
    return dict(action_index=index,c_index=index,command=COMMANDS[index].copy(),next_nav=nav,
        fallback=not n,features=_features(row,nav,not n),n_current=n,n_peers=0,memo_hit=False,
        scores=np.full(27,.1),served=np.full(27,0. if zero_service else 1.),
        probabilities=np.eye(27,dtype=np.float64)[index],innovation=-1.,entropy=0.)


def pair(monkeypatch,program,agent=0,count=1,index=7,zero_service=False,off_score=.2,off_service=1.):
    candidate=policies.Policy(program,None,world=1,agent=agent,sampling_root=None)
    independent=reference.Reference(program,None,world=1,agent=agent,sampling_root=None)
    monkeypatch.setattr(candidate.base,"query",lambda row,tick,nav:response(row,nav,index,zero_service))
    monkeypatch.setattr(independent.original,"query",lambda row,tick,nav:response(row,nav,index,zero_service))
    monkeypatch.setattr(policies,"off_score",lambda row:(off_score,off_service,count))
    monkeypatch.setattr(reference,"_off",lambda row:(off_score,off_service,count))
    return candidate,independent


def compare(a,b):
    assert set(a)==set(b)
    for key in a:
        assert np.array_equal(a[key],b[key],equal_nan=True),key


@pytest.mark.parametrize("program",("CJ_KEEP","CJ_RETURN"))
@pytest.mark.parametrize("agent",range(5))
def test_creation_consume_once_nav_suppression_all_roles(monkeypatch,program,agent):
    c,r=pair(monkeypatch,program,agent)
    row=observation()
    tick=agent*4
    first=c.query(row,tick,6)
    independent=r.query(row.copy(),tick,6)
    compare(first,independent)
    assert first["requested_off"] and first["memory_created"] and first["n_current"]==1
    assert first["action_index"]==0 and first["origin_c_index"]==7
    assert first["stored_index"]==(0 if program=="CJ_KEEP" else 7)
    assert np.array_equal(first["origin_row"],row)
    # Changing caller row cannot change the stored source row.
    row[3]=.7
    empty=observation(0)
    expected_nav=MemoC().query(empty,tick+4,6)["next_nav"]
    assert expected_nav==7 # An ordinary empty-row query would mutate navigation.
    def forbidden(*args,**kwargs):
        raise AssertionError("bypass called scoring/forward/RNG")
    monkeypatch.setattr(c.base,"query",forbidden)
    monkeypatch.setattr(r.original,"query",forbidden)
    monkeypatch.setattr(policies,"off_score",forbidden)
    monkeypatch.setattr(reference,"_off",forbidden)
    next_answer=c.query(empty,tick+4,6)
    reference_answer=r.query(empty,tick+4,6)
    compare(next_answer,reference_answer)
    assert next_answer["memory_consumed"] and not next_answer["pending_after"]
    assert not next_answer["requested_off"] and not next_answer["eligible"]
    assert next_answer["next_nav"]==6 and np.isnan(next_answer["features"]).all()
    assert np.isnan(next_answer["scores"]).all() and next_answer["c_index"]==-1
    assert next_answer["origin_row"][3]==pytest.approx(.1)
    assert c.counters["memory_created"]==c.counters["memory_consumed"]==1
    monkeypatch.setattr(c.base,"query",lambda row,tick,nav:response(row,nav))
    monkeypatch.setattr(r.original,"query",lambda row,tick,nav:response(row,nav))
    again=c.query(empty,tick+8,6)
    compare(again,r.query(empty,tick+8,6))
    assert not again["memory_consumed"] and again["c_available"]


@pytest.mark.parametrize("program",("CJ","CJ_KEEP","CJ_RETURN"))
@pytest.mark.parametrize("count,zero_service,score,service,off",(
    (1,False,.1,1.,False), # Stable ON tie.
    (1,False,.09,1.,False), # Strict service/score loss.
    (1,False,.2,0.,False), # Positive service required.
    (1,True,0.,0.,False), # All-zero-service with positive users retains ON.
    (0,True,0.,0.,True), # Empty row OFF fallback retains C category, no guard.
    (1,False,.2,1.,True)))
def test_cj_strict_tie_zero_fallback(monkeypatch,program,count,zero_service,score,service,off):
    c,r=pair(monkeypatch,program,count=count,zero_service=zero_service,off_score=score,off_service=service)
    a=c.query(observation(count),0,6)
    compare(a,r.query(observation(count),0,6))
    assert a["requested_off"]==off
    assert a["memory_created"]==(program!="CJ" and off and count>0)
    if count==0:
        assert a["action_index"]==7 and not a["memory_created"]


@pytest.mark.parametrize("program",("CJ_KEEP","CJ_RETURN"))
def test_terminal_pending_and_reset(monkeypatch,program):
    c,r=pair(monkeypatch,program,agent=3)
    a=c.query(observation(),252,6)
    compare(a,r.query(observation(),252,6))
    assert c.pending is not None and r.remembered is not None
    fresh=policies.Policy(program,None,world=2,agent=3,sampling_root=None)
    assert fresh.pending is None and fresh.counters["memory_created"]==0


@pytest.mark.parametrize("count",(0,1,12))
def test_zero_control_never_creates_positive_count_memory(monkeypatch,count):
    c,r=pair(monkeypatch,"C_ZERO",count=count)
    a=c.query(observation(count),0,6)
    compare(a,r.query(observation(count),0,6))
    assert a["requested_off"]==(count==0)
    assert a["gate_count"]==min(count,10) and not a["memory_created"]


def test_hdirect_cache_keeps_addressed_draw_and_target_work(monkeypatch):
    parent=make_student(95031).eval().requires_grad_(False)
    # Isolate the sampling/cache branch without additional fabricated P0 forwards.
    monkeypatch.setattr(ordinary,"_forward",lambda actor,feature:(np.zeros(27,dtype=np.float32),np.zeros(128,dtype=np.float32)))
    c=policies.Policy("Hdirect_ZERO",parent,world=95001,agent=0,sampling_root=30022031)
    empty=observation(0)
    a=c.query(empty,0,6)
    b=c.query(empty,4,6)
    assert not a["memo_hit"] and b["memo_hit"]
    assert a["innovation"]==indexed_uniform(30022031,95001,0,0)
    assert b["innovation"]==indexed_uniform(30022031,95001,4,0)
    assert a["innovation"]!=b["innovation"]
    assert c.counters["neural_rows"]==1 and c.counters["sampled_draws"]==2 and c.counters["target_vectors"]==4
    assert not a["memory_created"] and not b["memory_created"]


def test_clipping_category_difference_can_be_physically_identical():
    positions=np.zeros((5,5,3),dtype=np.float64)
    positions[...,2]=50.
    a=dict(positions=positions,commands=np.zeros((4,5,3),dtype=np.float32),transmitter_mask=np.ones((4,5),dtype=bool),action_index=np.zeros((1,5),dtype=int))
    b=deepcopy(a)
    b["commands"][:,0,2]=-1.
    b["action_index"][0,0]=1
    result=paired_behavior(a,b)
    assert result["category_difference_decisions"]==1 and result["position_difference_uav_states"]==0
    assert result["first_execution_difference_tick"]==0 and result["shared_prefix_steps"]==0
