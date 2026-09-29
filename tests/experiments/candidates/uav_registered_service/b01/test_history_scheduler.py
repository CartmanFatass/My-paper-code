import inspect

import numpy as np
import pytest

from experiments.candidates.uav_registered_service.b01 import history as h, scheduler as s
from experiments.candidates.uav_radio_activation.b03 import protocol as p
from experiments.candidates.uav_local_history.b01.controller import COMMANDS


def fixture_inputs():
    own=np.tile([.5,.5,.5],(5,1)).astype(np.float32)
    actual=np.tile([0,0,0],(5,1))
    proposed=np.tile([1,0,0],(5,1))
    packet=p.encode_map(np.tile([500,500],(50,1)))
    return own,actual,proposed,packet


def test_registry_duplicate_rows_are_distinct_and_api_is_legal():
    own,actual,proposed,packet=fixture_inputs()
    actor=s.Scheduler('P',packet,lambda:0.,lambda:0.,horizon=8)
    result=actor.decide(own,actual,proposed,0,31)
    assert actor.sites.shape==(50,2) and len(set(map(tuple,actor.sites)))==1
    assert set(inspect.signature(actor.executed).parameters)=={'tick','commands','mask'}
    assert 'connections' not in inspect.signature(actor.decide).parameters
    assert 'true_sites' not in inspect.signature(actor.decide).parameters
    assert result['timely'] and result['key_length']==8
    assert actor.execution.history.last.tolist()==[-1]*50
    assert not actor.execution.history.windows.any()
    assert len(actor.execution.predicted)==0
    # Duplicate rows are still individual native assignment identities.
    assert result['candidate_contacts'].shape==(27,32,4,50)
    assert result['candidate_requests']==116
    assert result['state_reductions']==4*result['candidate_plans']


def test_distinct_counts_unreachable_oldest_and_no_row_priority():
    history=h.ServiceHistory()
    history.last[:]=10
    history.last[:2]=-1
    history.last[2:4]=2
    groups=h.age_groups(history)
    served=np.zeros((4,50),bool)
    served[:,2]=True
    served[1,3]=True
    counts=[int((served.any(axis=0)&g).sum()) for g in groups]
    assert counts==[0,2,0]
    # Even with oldest unreachable, the full age vector beats native J.
    a=s.ordering('O',1,1,[0.,1.,0.],[0,2,0],0,0)
    b=s.ordering('O',0,31,[1.,50.,1.],[0,1,49],0,0)
    assert a>b
    permutation=np.arange(50)[::-1]
    shuffled=h.ServiceHistory(0,history.last[permutation],history.windows[:,permutation])
    assert counts==[int((served[:,permutation].any(axis=0)&g).sum()) for g in h.age_groups(shuffled)]
    assert s.ordering('P',0,31,[1.,50.,1.],[0,1,49],1,0)>s.ordering('P',1,1,[0.,1.,0.],[0,2,0],0,0)


def test_new_window_pairs_and_persistent_age_at63_64():
    history=h.ServiceHistory()
    served=np.zeros(50,bool)
    served[[3,4]]=True
    assert history.update(63,served)==2
    assert history.update(64,served)==2
    assert history.update(65,served)==0
    assert history.last[3]==65 and history.last[0]==-1
    assert history.windows[:2,3].all() and not history.windows[2:].any()


def test_atomic_interruption_replays_saved_anchor_at_its_time():
    execution=h.ExecutionHistory(np.zeros((50,2)))
    zero=np.zeros((5,3))
    initial=np.tile([100,100,100],(5,1))
    later=np.tile([700,700,100],(5,1))
    execution.anchor(0,initial)
    execution.anchor(4,later)
    for tick in range(8):
        execution.append(tick,zero,31)
    calls=[0]
    def check():
        calls[0]+=1
        if calls[0]==4:
            raise s.DeadlineExceeded
    positions=[]
    def evaluate(position,sites,mask):
        positions.append(position.copy())
        served=np.zeros(50,bool)
        served[len(positions)-1]=True
        return served,np.zeros(3)
    with pytest.raises(s.DeadlineExceeded):
        execution.settle(4,check,evaluate)
    assert execution.next_unsettled==2
    assert execution.history.last[:3].tolist()==[0,1,-1]
    execution.anchor(8,np.tile([900,900,100],(5,1)))
    execution.settle(8,evaluate=evaluate)
    assert execution.next_unsettled==8 and len(execution.predicted)==8
    np.testing.assert_array_equal(positions[:4],np.tile(initial,(4,1,1)))
    np.testing.assert_array_equal(positions[4:],np.tile(later,(4,1,1)))
    np.testing.assert_array_equal(execution.position,np.tile([900,900,100],(5,1)))
    assert execution.history.last[:8].tolist()==list(range(8))


def test_inner_orders_use_history_not_native_finalist_rerank():
    native=np.zeros((27,32,3))
    # Native alone favors(2,1); history inner steps lead to(1,2).
    native[2,1,0]=100
    keys=np.zeros((27,32,2))
    keys[1,1]=[2,0]
    keys[1,2]=[3,0]
    keys[0,3]=[2.5,0]
    keys[4,3]=[2.8,0]
    calls=[]
    def score(q,mask):
        calls.append((q,mask))
        return native[q,mask]
    assert s.sequential_search(score,lambda q,m:tuple(keys[q,m]),1,0)==(1,2)
    assert len(calls)==116
    assert calls[:27]==[(q,1) for q in range(27)]
    assert calls[27:58]==[(1,m) for m in range(1,32)]
    assert calls[58:89]==[(0,m) for m in range(1,32)]
    assert calls[89:]==[(q,3) for q in range(27)]


def test_prefix_and_candidates_never_persist_and_independent_candidates(monkeypatch):
    monkeypatch.setattr(s,'model',lambda positions,sites,mask:(np.ones(50,bool),np.zeros(3)))
    own,actual,proposed,packet=fixture_inputs()
    actor=s.Scheduler('P',packet,lambda:0.,lambda:0.,horizon=8)
    result=actor.decide(own,actual,proposed,0,31)
    assert actor.execution.next_unsettled==0
    assert not actor.execution.history.windows.any()
    assert result['prefix_windows'].any()
    # Every scored pair computes new pairs against the identical saved prefix.
    for q,mask in result['evaluated_pairs']:
        window=result['prefix_windows'].copy()
        new=0
        for served in result['candidate_contacts'][q,mask]:
            new+=int((served&~window[0]).sum())
            window[0]|=served
        assert result['ordering_keys'][q,mask,0]==new


@pytest.mark.parametrize('arm',['O','P'])
def test_first_undecoded_report_recovers_with_explicit_censored_prefix(arm):
    own,actual,proposed,packet=fixture_inputs()
    actor=s.Scheduler(arm,packet,lambda:2.,lambda:0.,horizon=12)
    initial=actor.decide(own,actual,proposed,0,7,started=0.)
    assert not initial['decoded_anchor'] and not initial['reports']
    assert actor.execution.anchors=={} and actor.execution.position is None
    for tick in range(4):
        actor.executed(tick,actual,7)
    actor.clock=lambda:0.
    late=actor.decide(own,actual,proposed,4,7)
    assert late['timely'] and late['fallback_reason']==''
    assert late['history_start']==4 and late['history_reductions']==0
    assert late['window_valid'].tolist()==[False,True,True,True]
    assert late['unknown_age'].all()
    assert set(actor.execution.anchors)=={4}
    assert actor.execution.next_unsettled==4 and actor.execution.predicted=={}
    assert actor.execution.history.last.tolist()==[-1]*50
    assert late['selected_q'] is not None and late['command_packet']
    if arm=='P':
        assert all(late['ordering_keys'][q,m,0]==0 for q,m in late['evaluated_pairs'])


def test_encode_and_final_decode_overruns_retain_entire_team(monkeypatch):
    own,actual,proposed,packet=fixture_inputs()
    now=[0.]
    original=s.encode_reports
    def late_encode(*args):
        result=original(*args)
        now[0]=2.
        return result
    monkeypatch.setattr(s,'encode_reports',late_encode)
    actor=s.Scheduler('P',packet,lambda:now[0],lambda:0.,horizon=8)
    result=actor.decide(own,actual,proposed,0,7)
    assert result['reports'] and not result['decoded_anchor'] and actor.execution.anchors=={}
    np.testing.assert_array_equal(result['commands'],actual)
    assert result['recurring_bytes']==120
    monkeypatch.setattr(s,'encode_reports',original)
    original_decode=s.decode_command
    def late_decode(*args):
        result=original_decode(*args)
        now[0]=2.
        return result
    now[0]=0.
    monkeypatch.setattr(s,'decode_command',late_decode)
    actor=s.Scheduler('P',packet,lambda:now[0],lambda:0.,horizon=8)
    result=actor.decide(own,actual,proposed,0,7)
    assert not result['timely'] and result['candidate_plans']>0 and result['decoded_anchor']
    assert result['command_packet']==b'' and result['mask']==7
    np.testing.assert_array_equal(result['commands'],actual)
    assert not actor.execution.history.windows.any()


def test_censored_window0_no_p_credit_and_crossing64_eligible():
    history=h.ServiceHistory(start_tick=4)
    served=np.zeros(50,bool)
    served[[7,8]]=True
    assert history.update(62,served)==0
    assert history.update(63,served)==0
    assert history.update(64,served)==2
    assert history.update(65,served)==0
    assert history.windows[:2,7].all()
    assert history.last[7]==65


def test_no_decoded_report_keeps_whole_episode_pending_and_fallback():
    own,actual,proposed,packet=fixture_inputs()
    actor=s.Scheduler('P',packet,lambda:2.,lambda:0.,horizon=8)
    for tick in range(8):
        if tick%4==0:
            result=actor.decide(own,actual,proposed,tick,7,started=0.)
            assert not result['timely'] and result['history_start']==-1
            assert result['actual_timeout'] and not result['decoded_anchor']
            np.testing.assert_array_equal(result['commands'],actual)
            assert result['mask']==7
        actor.executed(tick,actual,7)
    assert actor.execution.settle(8)==(0,False)
    assert len(actor.execution.actions)==8 and actor.execution.predicted=={}
    assert actor.execution.next_unsettled==0 and actor.execution.start_tick is None


def test_interrupted_postanchor_backlog_cannot_be_censored_again():
    execution=h.ExecutionHistory(np.zeros((50,2)))
    commands=np.zeros((5,3))
    for tick in range(12):
        execution.append(tick,commands,31)
    execution.anchor(4,np.tile([100,100,100],(5,1)))
    count=[0]
    def evaluate(position,sites,mask):
        count[0]+=1
        return np.ones(50,bool),np.zeros(3)
    def check():
        if count[0]==2:
            raise s.DeadlineExceeded
    with pytest.raises(s.DeadlineExceeded):
        execution.settle(8,check,evaluate)
    assert execution.next_unsettled==6 and sorted(execution.predicted)==[4,5]
    execution.anchor(8,np.tile([600,600,100],(5,1)))
    execution.anchor(12,np.tile([900,900,100],(5,1)))
    completed,ready=execution.settle(12,evaluate=evaluate)
    assert ready and completed==6
    assert sorted(execution.predicted)==list(range(4,12))
    assert execution.start_tick==4 and len(execution.actions)==12


def test_censored_p_crossing_candidate62_65_and_terminal254_255():
    own,actual,_,packet=fixture_inputs()
    actor=s.Scheduler('P',packet,lambda:0.,lambda:0.)
    for tick in range(60):
        actor.executed(tick,actual,1)
    actor.execution.anchor(4,np.tile([500,500,100],(5,1)))
    result=actor.decide(own,actual,actual,60,1)
    assert result['timely'] and result['history_start']==4
    assert result['history_reductions']==56
    assert result['prefix_valid'] and result['snapshot_valid']
    q=p.command_index([0,0,0])
    assert (q,1) in result['evaluated_pairs']
    contacts=result['candidate_contacts'][q,1]
    assert contacts.sum(axis=1).tolist()==[10,10,10,10]
    # Window0 is censored; window1 gains exactly10 distinct user-window pairs.
    assert result['ordering_keys'][q,1,0]==10
    assert not actor.execution.history.windows[1].any()
    for tick in range(60,252):
        actor.executed(tick,actual,1)
    result=actor.decide(own,actual,actual,252,1)
    assert result['timely'] and result['scored_length']==2
    assert result['forecast'].shape==(27,2,5,3)
    assert result['candidate_contacts'].shape==(27,32,2,50)
    assert result['history_after']==252
    assert max(actor.execution.predicted)==251
    # Chosen terminal forecasts do not become executed history.
    for tick in (252,253,254,255):
        actor.executed(tick,actual,1)
    assert actor.execution.next_unsettled==252


def test_first_uncached_interrupted_request_is_not_a_cache_hit(monkeypatch):
    from envs.pettingzoo import uav_radio
    own,actual,proposed,packet=fixture_inputs()
    now=[0.]
    original=uav_radio.service_metrics
    calls=[0]
    def late_metric(*args,**kwargs):
        value=original(*args,**kwargs)
        calls[0]+=1
        # Two common prefix transitions precede the first candidate transition.
        if calls[0]==3:
            now[0]=2.
        return value
    monkeypatch.setattr(uav_radio,'service_metrics',late_metric)
    monkeypatch.setattr(h,'service_metrics',late_metric)
    actor=s.Scheduler('P',packet,lambda:now[0],lambda:0.,horizon=8)
    result=actor.decide(own,actual,proposed,0,7)
    assert not result['timely'] and result['candidate_plans']==0
    assert result['candidate_requests']==result['candidate_uncached_requests']==1
    assert result['candidate_cache_hits']==0 and result['interrupted_candidate_requests']==1
    assert result['state_reductions']==1
    assert result['mask']==7 and result['command_packet']==b''
