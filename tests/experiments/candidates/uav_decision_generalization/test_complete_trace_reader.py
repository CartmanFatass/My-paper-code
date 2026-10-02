import copy
import math
import json
from types import SimpleNamespace
import pytest
import numpy as np
from experiments.candidates.uav_decision_generalization import contract as c,reading as reader
from experiments.candidates.uav_decision_generalization.data import Bill,COUNTERS,Store,Trace


def make_store(tmp_path):
    out=tmp_path/'out'
    ledger={'schema':1,'prior_counters':dict.fromkeys(COUNTERS,0),'prior_cpu_seconds':0.,'prior_gpu_seconds':0.,'disk_roots':[str(tmp_path)]}
    return Store(out,Bill(ledger,out))

def literal_trace(store,*,bad_backhaul=False,zero_prefix=0):
    """Static literal valid poses/actions/association; no native/controller function."""
    xyz = [[100.+i,200.,100.] for i in range(6)]
    associations = [0,0]+[-1]*48
    mask = [True,True]+[False]*48
    reset = {"fields":{"uav_positions":xyz,"connections":[mask]+[[False]*50 for _ in range(5)],
                       "routing_paths":{"0":[["uav",0],["bs",0]]}}}
    targets = copy.deepcopy(xyz)
    trace = Trace(store,"raw/literal.gz",{"kind":"assigned_targets","assigned_targets_xyz":targets})
    trace.write({"kind":"reset","identity":reset})
    term = .2e6/(6*20e6*math.log2(1001))
    reward = .5*(.04+term)
    info = {"coverage_backhauled":.04,"contract_reward":reward,"throughput_term":term,
            "frontend_capacity_with_path_mbps":.2,"mean_relays_per_routed_uav":0.}
    for step in range(500):
        zero=step<zero_prefix
        current_info={**info,'coverage_backhauled':0. if zero else .04,'contract_reward':.5*((0. if zero else .04)+term)}
        current_mask=[False]*50 if zero else mask
        trace.write({"kind":"step_request","step":step,"positions_xyz":xyz,"actions":[[0.,0.,0.]]*6})
        trace.write({"kind":"step","step":step+1,"positions_xyz":xyz,"reward_info":current_info,
                     "rewards":{str(i):current_info["contract_reward"]/6 for i in range(6)},"terminations":{str(i):step==499 for i in range(6)},
                     "truncations":{str(i):False for i in range(6)},"user_association":associations,
                     "backhauled_users_mask":([True]+[False]*49 if bad_backhaul else current_mask),
                     "routing_paths":{} if zero else {"0":[["uav",0],["bs",0]]}})
    entry = trace.close("complete")
    result = {"Q":float(np.mean([0.]*zero_prefix+[.04]*(500-zero_prefix))),"association_change_count":0,"backhaul_loss_events":2 if zero_prefix else 0}
    for key in ("contract_reward","coverage_backhauled","frontend_capacity_with_path_mbps","mean_relays_per_routed_uav"):
        values=([0.]*zero_prefix+[.04]*(500-zero_prefix) if key=='coverage_backhauled' else
                [.5*term]*zero_prefix+[reward]*(500-zero_prefix) if key=='contract_reward' else [info[key]]*500)
        result[key+"_mean_all"] = float(np.mean(values))
        result[key+"_mean_final100"] = float(np.mean(values[-100:]))
    return SimpleNamespace(root=store.output,files={"raw/literal.gz":entry}),targets,reset,result


import math


def test_independent_reader_full_native_arithmetic_and_routing_mask(tmp_path):
    store = make_store(tmp_path)
    try:
        dataset,targets,reset,result = literal_trace(store)
        reading = reader.read_episode(dataset,"raw/literal.gz",targets,reset,result,store.bill)
        assert reading["steps"] == 500 and reading["Q"] == pytest.approx(.04)
        assert reading["max_pose_reconstruction_error"] == 0
        assert store.bill.delta["native_step_calls"] == 0
        assert store.bill.delta["reader_episode_reads"] == 1
    finally: store.close()


def test_independent_reader_rejects_backhaul_mask_inconsistent_with_routes(tmp_path):
    store = make_store(tmp_path)
    try:
        dataset,targets,reset,result = literal_trace(store,bad_backhaul=True)
        with pytest.raises(AssertionError,match="association/routing"):
            reader.read_episode(dataset,"raw/literal.gz",targets,reset,result,store.bill)
    finally: store.close()


def test_soft_targets_and_world_uncertainty_without_new_result_rng():
    assert reader.independent_soft_target([.4,.4]) == [.5,.5]
    for left,right in zip(reader.independent_soft_target([.1,.2,.5]),c.soft_targets([.1,.2,.5])):
        assert left == pytest.approx(right,abs=1e-14)
    reading = reader.uncertainty([-.1,0,.1])
    assert reading["n_worlds"] == 3 and reading["mean"] == 0


def test_complete_severe_zero_service_trace(tmp_path):
    store=make_store(tmp_path)
    try:
        dataset,targets,reset,result=literal_trace(store,zero_prefix=469)
        outcome=reader.read_episode(dataset,'raw/literal.gz',targets,reset,result,store.bill)
        assert outcome['Q']==pytest.approx(.04*31/500)
        assert outcome['service_tail']['zero_steps']==469
        assert outcome['service_tail']['longest_zero_run']==469
        assert outcome['service_tail']['p10']==0
        assert outcome['service_tail']['final100_mean']==pytest.approx(.04*31/100)
        assert store.bill.delta['native_step_calls']==0
    finally:
        store.close()
