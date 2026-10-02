"""Zero policy/model/native-effect fixtures for the changed independent reader contract."""
import copy
import json
from pathlib import Path
import numpy as np
import pytest
from experiments.candidates.uav_fleet_transmission.b11_travel_ties.reader import check_assignment_contract
from experiments.candidates.uav_fleet_transmission.b11_travel_ties.contract import (
    jobs,source_binding,reference_evidence,COST_ENVELOPE)
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.trace import empty_candidate,CANDIDATE_DTYPE
from experiments.candidates.uav_fleet_transmission.b08_anonymous_memory.controller import TRACK_DTYPE


def fixture():
    ordinary=np.arange(16,dtype=np.float64).reshape(8,2)*100.
    users=np.full((1,30,2),np.nan);users[0,:3]=[[200.,200.],[400.,400.],[600.,600.]]
    velocity=np.full((1,30,2),np.nan);velocity[0,:3]=0.
    tracks=np.zeros((1,30),dtype=TRACK_DTYPE)
    rows=[]
    for i,pair in enumerate(((-1,-1),(2,3),(2,4),(3,4))):
        xy=ordinary.copy()
        if i:xy[list(pair)]=xy[list(pair[::-1])]
        r=empty_candidate(0,i,pair,np.column_stack((xy,np.full(8,100.))),3)
        r["ticks"]=r["ticks_started"]=30;r["rf_started"]=r["rf_completed"]=3
        r["completed"]=True;r["accepted"]=i<2;r["selected"]=i==2
        r["qos"][0]=0. if i==0 else .1;r["score"]=float(i>0)
        r["forecast_travel"]=[100.,90.,30.,30.][i];rows.append(r)
    priority=np.full((1,8,2),np.nan);priority[0,:5]=ordinary[:5]
    ring=np.full((1,8,2),np.nan);ring[0,:3]=ordinary[5:]
    raw=dict(plan_step=np.array([0]),plan_assignment_role=np.array([[1,1,2,2,2,3,3,3]]),
        plan_assignment_call=np.array([[1,1,1,1,1,2,2,2]]),plan_assignment_column=np.array([[0,1,2,3,4,0,1,2]]),
        plan_ordinary_targets=ordinary[None],plan_targets=rows[2]["targets"][None,:,:2].copy(),
        plan_priority=priority,plan_priority_count=np.array([5]),plan_relay_count=np.array([2]),
        plan_ring=ring,plan_ring_count=np.array([3]),plan_eligible=np.array([[0,0,1,1,1,0,0,0]],bool),
        plan_fallback=np.array([0]),plan_bs=np.array([[0.,0.]]),plan_user_count=np.array([3]),
        trace_current_count=np.array([3]),plan_users=users,trace_canonical=users,
        candidate_records=np.asarray(rows,dtype=CANDIDATE_DTYPE),plan_candidate_count=np.array([4]),
        plan_selected_candidate=np.array([2]),plan_selected_pair=np.array([[2,4]]),
        plan_current_velocities=velocity,trace_tracks=tracks,plan_prediction_xy=np.repeat(users[:,None],3,axis=1),
        plan_h_selected=np.array([1]),plan_tie_changed=np.array([True]),
        plan_top_score_mask=np.array([[False,True,True,True]+[False]*12]),
        plan_min_travel_mask=np.array([[False,False,True,True]+[False]*12]))
    return raw


def test_independent_tie_and_commit_audit():
    raw=fixture();before=copy.deepcopy(raw)
    check_assignment_contract(raw)
    for k in raw:
        np.testing.assert_equal(raw[k],before[k])
    for field in ("plan_selected_candidate","plan_h_selected","plan_selected_pair","plan_targets","plan_assignment_role"):
        bad=copy.deepcopy(raw);bad[field].flat[0]+=1
        with pytest.raises(AssertionError):check_assignment_contract(bad)
    bad=copy.deepcopy(raw);bad["candidate_records"]["forecast_travel"][2]=91.
    with pytest.raises(AssertionError):check_assignment_contract(bad)
    bad=copy.deepcopy(raw);bad["candidate_records"]["accepted"][2]=True
    with pytest.raises(AssertionError):check_assignment_contract(bad)
    bad=copy.deepcopy(raw);bad["candidate_records"]["forecast_travel"][2]=np.nan
    with pytest.raises(AssertionError):check_assignment_contract(bad)


def test_reference_binding_and_panel_are_read_only():
    from experiments.candidates.uav_fleet_transmission.b11_travel_ties.contract import ROOT
    binding=source_binding()
    for phase,n in (("engineering",2),("scientific",32)):
        assert len(jobs(phase))==n and {j["arm"] for j in jobs(phase)}=={"H_T"}
        evidence=reference_evidence(ROOT,phase,verify_raw=False)
        assert len(evidence["rows"])==2*n
        assert evidence["new_controller_calls"]==evidence["new_model_calls"]==evidence["new_native_calls"]==0
    assert COST_ENVELOPE["native_steps"]==34*3000
    assert COST_ENVELOPE["candidate_forecasts"]==34*100*16*2+576
    assert binding["construction_contract_sha"]=="95ecc08021c0f0a3fffd1efe94323fb77ff31f24"


def test_output_based_external_reference_locator():
    from experiments.candidates.uav_fleet_transmission.b11_travel_ties.contract import reference_root_for_output,failed_setup_costs
    canonical=Path("/home/wu/projects/HMASD")
    out=canonical/"runs/uav_fleet_transmission/b11_travel_ties_engineering_a02"
    assert reference_root_for_output(out)==canonical
    with pytest.raises(ValueError):reference_root_for_output(canonical/"arbitrary/path")
    cpu,evidence=failed_setup_costs()
    assert cpu==1.931557566 and len(evidence)==1
