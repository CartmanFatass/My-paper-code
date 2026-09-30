"""Synthetic geometry/history only; no environment step or scientific fit."""
import numpy as np
import pytest

from experiments.candidates.uav_user_waiting.b02 import protocol as p
from experiments.candidates.uav_user_waiting.b02.scheduler import Scheduler as Frozen
from experiments.candidates.uav_user_waiting.b02.storage import pack_records
from experiments.candidates.uav_user_waiting.b03.scheduler import Scheduler
from experiments.candidates.uav_user_waiting.b03.history import ServiceHistory,ExecutionHistory
from experiments.candidates.uav_user_waiting.b03.features import FEATURE_SLICES,pack_features
from experiments.candidates.uav_user_waiting.b03.read_core import reference_features,verify_stage,verify_decisions
from experiments.candidates.uav_user_waiting.b03.data import episode_rows


def inputs():
    positions=np.array([[100,100,80],[300,200,100],[600,400,120],[800,700,90],[400,800,110]],float)
    sites=np.array([[50+100*x,100+180*y] for x in range(10) for y in range(5)])
    actual=np.zeros((5,3));proposals=np.array([[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,-1]])
    nav=np.arange(5,dtype=np.uint8)
    return (positions-(0,0,50))/(1000,1000,100),actual,proposals,nav,p.encode_map(sites)


class Zero:
    def __init__(self): self.rows=[]
    def evaluate(self,x,tick):
        self.rows.append((x.copy(),tick))
        return 0.,0.


@pytest.mark.parametrize('arm',['M','S'])
def test_ordinary_decisions_preserve_frozen_laws_and_private_memory(arm):
    own,actual,proposed,nav,packet=inputs()
    new=Scheduler(arm,packet,lambda:0.,lambda:0.,horizon=8)
    old=Frozen(arm,packet,lambda:0.,lambda:0.,horizon=8)
    for tick in (0,4):
        if tick:
            for t in range(4):
                new.executed(t,actual,7);old.executed(t,actual,7)
        left=new.decide(own,actual,proposed,tick,7,nav)
        right=old.decide(own,actual,proposed,tick,7,nav)
        assert (left['selected_q'],left['selected_mask'])==(right['selected_q'],right['selected_mask'])
        np.testing.assert_array_equal(left['commands'],right['commands'])
        l,r=left['record']['current'],right['record']['current']
        for key in ('request_pairs','evaluated_pairs','contacts','native','age_cost'):
            np.testing.assert_array_equal(l[key],r[key])
        np.testing.assert_array_equal(new.execution.history.maximum,l['input_maximum'])
        assert left['counts']['value_queries']==0


def test_zero_value_matches_g0_and_value_sees_exact_pre_next_c_commitment():
    own,actual,proposed,nav,packet=inputs();zero=Zero()
    learned=Scheduler('LN',packet,lambda:0.,lambda:0.,horizon=8,value=zero)
    control=Scheduler('G0',packet,lambda:0.,lambda:0.,horizon=8)
    l=learned.decide(own,actual,proposed,0,7,nav)
    r=control.decide(own,actual,proposed,0,7,nav)
    assert l['timely'] and r['timely'] and l['candidate_requests']==r['candidate_requests']==349
    assert (l['selected_q'],l['selected_mask'])==(r['selected_q'],r['selected_mask'])
    stage=l['record']['current']
    np.testing.assert_array_equal(stage['request_pairs'],r['record']['current']['request_pairs'])
    assert 0<len(zero.rows)<=117 and len(zero.rows)==int(stage['value_valid'].sum())
    for x,tick in zero.rows:
        assert tick==4
        np.testing.assert_array_equal(x[FEATURE_SLICES['previous_nav']].reshape(5,10).argmax(axis=1),nav)
        assert x[FEATURE_SLICES['clock']][0]==4/256
        command=x[FEATURE_SLICES['commands']].reshape(5,3)
        np.testing.assert_array_equal(command[1:],proposed[1:])
    verify_stage(stage,p.decode_map(packet),arm='LN',value=Zero(),horizon=8,full_physics=False,
                 extra_physics=[l['record']['requested_pair']])
    assert not learned.execution.history.maximum.any()
    for tick in range(4): learned.executed(tick,actual,7)
    before=len(zero.rows)
    end=learned.decide(own,actual,proposed,4,7,nav)
    assert len(zero.rows)==before and end['counts']['value_queries']==0
    assert end['counts']['terminal_value_zeros']>0


def test_missing_origin_uses_completed_m_without_fabricated_value():
    own,actual,proposed,nav,packet=inputs();zero=Zero()
    actor=Scheduler('LR',packet,lambda:0.,lambda:0.,horizon=8,value=zero)
    for tick in range(4): actor.executed(tick,actual,7)
    result=actor.decide(own,actual,proposed,4,7,nav)
    assert result['timely'] and result['candidate_requests']==232
    assert result['record']['missing_maximum_m_fallback'] and not zero.rows
    assert result['record']['history_start']==4
    np.testing.assert_array_equal(result['record']['requested_pair'],result['record']['m_pair'])


def test_late_value_after_complete_m_keeps_old_action_and_retains_work():
    own,actual,proposed,nav,packet=inputs();clock=[0.]
    class Slow:
        def evaluate(self,x,tick):
            clock[0]=2.
            return 1.,1.
    actor=Scheduler('LN',packet,lambda:clock[0],lambda:0.,horizon=8,value=Slow())
    result=actor.decide(own,actual,proposed,0,7,nav)
    assert not result['timely'] and result['record']['actual_timeout']
    assert result['record']['current']['searches']['W']['completed']
    assert result['counts']['candidate_requests']==233 and result['counts']['value_queries']==1
    np.testing.assert_array_equal(result['commands'],actual)
    assert result['mask']==7 and len(result['command_packet'])==0


def test_maximum_history_copy_and_atomic_interruption():
    history=ServiceHistory();private=history.copy()
    served=np.zeros(50,bool);served[0]=True
    for tick in range(4): private.update(tick,served)
    assert not history.maximum.any() and private.maximum[0]==0 and np.all(private.maximum[1:]==4)
    execution=ExecutionHistory(np.zeros((50,2)))
    execution.anchor(0,np.tile([500.,500.,100.],(5,1)))
    for tick in range(4): execution.append(tick,np.zeros((5,3)),31)
    checks=[0]
    def check():
        checks[0]+=1
        if checks[0]==2: raise TimeoutError
    with pytest.raises(TimeoutError):
        execution.settle(4,check,evaluate=lambda *args:(served,np.zeros(3)))
    assert execution.next_unsettled==1 and np.all(execution.history.maximum[1:]==1)


def synthetic_m_raw():
    own,commands,proposals,nav,packet=inputs()
    contacts=np.ones((256,50),bool)
    actual=np.ones((256,5,50),bool);actual[:]=False;actual[:,0,1:]=True
    records=[]
    postnav=np.array([(nav+i)%10 for i in range(64)],np.uint8)
    for i,tick in enumerate(range(0,256,4)):
        windows=np.zeros((4,50),bool)
        windows[np.arange(4)*64<tick]=True
        records.append(dict(arm='M',tick=tick,decoded_anchor=True,history_start=0,history_after=tick,
            history_last=np.full(50,tick-1),history_windows=windows,history_maximum=np.zeros(50,np.int64),
            report_packets=np.array([np.frombuffer(v,np.uint8) for v in p.encode_reports(own,commands,proposals,tick,postnav[i])]),
            perturbation_applied=False))
    raw=dict(program=np.array('M'),completed_steps=np.array(256),model_contacts=contacts,
        model_valid=np.ones(256,bool),connections=actual,map_packet=np.frombuffer(packet,np.uint8),
        mask=np.full(256,31),post_c_nav=postnav)
    raw.update(pack_records(records))
    return raw,records


def test_target_is_actual_remaining_increment_and_current_c_is_not_a_feature():
    raw,records=synthetic_m_raw()
    data=episode_rows(raw)
    assert len(data['y'])==63
    np.testing.assert_array_equal(data['y'],(256-data['ticks'])/50.)
    assert data['y'][-1]==4/50 and data['y'][-1]!=256/50
    index=6
    original=data['X'][index-1].copy()
    raw['post_c_nav'][index]=(raw['post_c_nav'][index]+3)%10
    changed=episode_rows(raw)
    np.testing.assert_array_equal(changed['X'][index-1],original)
    assert not np.array_equal(changed['X'][index],data['X'][index])
    records[5]['history_after']=19
    raw.update(pack_records(records))
    missing=episode_rows(raw)
    assert missing['missing_ticks']==[20] and len(missing['y'])==62
    suffix=episode_rows(raw,minimum_tick=48)
    assert suffix['ticks'][0]==48 and len(suffix['y'])==52


def test_independent_basis_matches_legal_state_formula():
    own,commands,_,nav,packet=inputs()
    kwargs=dict(sites=p.decode_map(packet),positions=np.rint(own*(1000,1000,100)+(0,0,50)),
        commands=commands,mask=19,previous_nav=nav,last=np.full(50,-1,np.int64),
        maximum=np.full(50,12,np.int64),windows=np.zeros((4,50),bool),tick=12)
    np.testing.assert_array_equal(reference_features(**kwargs),pack_features(**kwargs,history_start=0,history_after=12))


@pytest.mark.parametrize('arm',['LR','LN'])
def test_complete_decision_reader_keeps_model_through_history_loops(arm):
    """Source-only delayed trajectory; no native environment/C call is made."""
    from experiments.candidates.uav_user_waiting.b02.study import allocate_raw,record_round
    from experiments.candidates.uav_registered_service.b01.history import model
    from experiments.candidates.uav_service_age.b01.metrics import actual_ages
    own,actual,proposed,nav,packet=inputs();sites=p.decode_map(packet)
    value=Zero();actor=Scheduler(arm,packet,lambda:0.,lambda:0.,horizon=8,value=value)
    raw=allocate_raw(8,arm,sites,packet);position=np.rint(own*(1000,1000,100)+(0,0,50))
    mask,pending,records=7,None,[];contacts=[]
    for tick in range(8):
        raw['commands'][tick]=actual;raw['proposals'][tick]=proposed;raw['mask'][tick]=mask
        raw['observations'][tick,:,:3]=(position-(0,0,50))/(1000,1000,100)
        if tick%4==0:
            raw['post_c_nav'][tick//4]=nav
            pending=actor.decide(raw['observations'][tick,:,:3],actual,proposed,tick,mask,nav)
            records.append(pending['record']);record_round(raw,pending,tick)
        position=np.clip(position+30*actual,p.LOW,p.HIGH)
        served,_=model(position,sites,mask);contacts.append(served)
        actor.executed(tick,actual,mask)
        if tick%4==1:
            actual=pending['commands'].copy();mask=pending['mask']
    before=actor.execution.next_unsettled
    actor.execution.settle(8)
    raw.update(completed_steps=np.array(8),actual_ages=actual_ages(np.array(contacts)),
        model_valid=np.ones(8,bool),model_contacts=np.array([actor.execution.predicted[t] for t in range(8)]),
        terminal_history_reductions=np.array(8-before),terminal_history_start=np.array(0),
        terminal_history_complete=np.array(True),terminal_burden_unknown=np.array(False),
        terminal_last=actor.execution.history.last.copy(),terminal_windows=actor.execution.history.windows.copy(),
        terminal_burden=actor.execution.history.burden.copy(),terminal_maximum=actor.execution.history.maximum.copy())
    result=verify_decisions(dict(steps=8,arm=arm),raw,records,value_model=value)
    assert result['verified_model_transitions']==8
