"""Synthetic data checks; no native environment or frozen evaluation-world queries."""
from collections import Counter

import numpy as np
import pytest

from experiments.candidates.uav_user_waiting.b02 import protocol as wire
from experiments.candidates.uav_user_waiting.b02.study import record_round
from experiments.candidates.uav_user_waiting.b02.storage import pack_records, unpack_records
from experiments.candidates.uav_user_waiting.b05 import protocol as fair
from experiments.candidates.uav_user_waiting.b07.collect import allocate_raw
from experiments.candidates.uav_user_waiting.b07.manager import Scheduler
from experiments.candidates.uav_user_waiting.b07.read_model import verify_decisions
from experiments.candidates.uav_user_waiting.b07.outcomes import replay_lrs,compact_row
from experiments.candidates.uav_user_waiting.b07.read_outcomes import verify_lrs,reference_paired
from experiments.candidates.uav_user_waiting.b07.metrics import paired_reading
from experiments.candidates.uav_user_waiting.b05.reader import compare_tree


def saved_synthetic():
    sites=np.column_stack((np.arange(50)*19.,np.arange(50)*17.))
    positions=np.asarray([[100,150,90],[950,950,149],[0,500,50],[400,300,100],[800,0,70]],float)
    packet=wire.encode_map(sites)
    raw=allocate_raw(8,sites,packet)
    actor=Scheduler(packet,horizon=8,clock=lambda:0.,cpu_clock=lambda:0.)
    actual=np.zeros((5,3),np.float32)
    proposals=np.tile([1.,0.,-1.],(5,1)).astype(np.float32)
    mask=31
    records=[]
    raw['positions'][0]=positions
    for tick in range(8):
        raw['commands'][tick],raw['proposals'][tick],raw['mask'][tick]=actual,proposals,mask
        raw['observations'][tick,:,:3]=(positions-wire.LOW)/(wire.HIGH-wire.LOW)
        if tick%4==0:
            nav=np.arange(5,dtype=np.uint8)
            raw['post_c_nav'][tick//4]=nav
            pending=actor.decide(raw['observations'][tick,:,:3],actual,proposals,tick,mask,nav)
            records.append(pending['record'])
            record_round(raw,pending,tick)
        positions=np.clip(positions+30.*actual,wire.LOW,wire.HIGH)
        raw['positions'][tick+1]=positions
        if tick%4==1:
            actual,mask=pending['commands'].copy(),pending['mask']
    raw.update(pack_records(records),completed_steps=np.array(8))
    return raw


def test_all_masks_and_tail_are_physically_recalculated():
    raw=saved_synthetic();paid=Counter()
    result=verify_decisions(raw,paid)
    assert result['independent_candidate_checks']==30
    assert paid['modeled_physics_completed']==90
    assert paid['modeled_geometry_completed']==6
    assert paid['modeled_sinr_link_entries']==22500
    assert result['model_work']['candidate_requests']==30
    assert result['model_work']['prefix_ticks']==4
    assert not any('history' in key for key in raw)


@pytest.mark.parametrize('corrupt',['nonwinner_count','distinct','prefix','key','menu','proposal','wire','paid','delivery','deadline'])
def test_full_reader_rejects_nonwinner_and_control_corruption(corrupt):
    raw=saved_synthetic();records=unpack_records(raw);record=records[0]
    nonwinner=next(i for i in range(15) if i!=record['selected_index'])
    if corrupt=='nonwinner_count': record['eligible_counts'][nonwinner,0,0]+=1
    elif corrupt=='distinct': record['distinct_users'][nonwinner,49]^=True
    elif corrupt=='prefix': record['prefix_positions'][0,0,0]+=1
    elif corrupt=='key': record['keys'][nonwinner,0]+=1
    elif corrupt=='menu': record['mask_menu'][0]=31
    elif corrupt=='proposal': record['returned_commands'][0,1]=1
    elif corrupt=='wire': record['delivered_command_packet'][0]^=1
    elif corrupt=='paid': record['counts']['radio_calls_attempted']+=1
    elif corrupt=='delivery': raw['commands'][2,0,0]=-1
    elif corrupt=='deadline': record['actual_timeout']=True
    raw.update(pack_records(records))
    with pytest.raises((AssertionError,ValueError)):
        verify_decisions(raw,Counter())


def analytical_outcome():
    values=np.full((8,5,50),-20.,np.float64)
    values[:,0,:12]=10.
    values[3:6,0,11]=-20.
    greedy=np.zeros_like(values,bool);greedy[:,0,:10]=True
    raw=dict(completed_steps=np.array(8),commands=np.zeros((8,5,3)),sinr=values,mask=np.full(8,31),
             connections=greedy,served=np.full(8,10),quality=np.full(8,7./30.),reward=np.full(8,.21))
    collector=dict(arm='C2',seed=17,**{name:0. for name in fair.INHERITED_METRICS})
    full,arrays,_=replay_lrs(raw,collector,Counter());raw.update(arrays)
    return raw,collector,full,compact_row(full)


def test_complete_native_lrs_gaps_and_all_four_signed_contrasts():
    raw,collector,full,compact=analytical_outcome()
    checked=verify_lrs(raw,full,compact,collector,Counter(),{})
    assert checked['package']=='C2:LRS'
    assert checked['per_user'][49]['gaps']==[[0,8,1,1,0,8]]
    assert checked['changed_grant_user_ticks']>0
    rows=[];refs={}
    for seed in (17,18):
        rows.append(dict(checked,seed=seed,max_unserved_gap=seed-10))
        for name,delta in [('S_F',1),('S',2),('M',3),('U',4)]:
            refs[name+':LRS',seed]=dict(checked,package=name+':LRS',program=name,seed=seed,max_unserved_gap=seed-10+delta)
    left=paired_reading(rows,refs,seeds=(17,18));right=reference_paired(rows,refs,seeds=(17,18))
    compare_tree(left,right,'paired',{})
    assert left['primary']['contrast']=='C2:LRS-S_F:LRS'
    assert left['primary']['mean_difference']==-1
    assert len(left['contrasts'])==4
    assert left['contrasts']['C2:LRS-U:LRS']['max_unserved_gap']['values']==[-4.,-4.]
