"""Pure arithmetic/schema/dispatch checks: zero controller, native or RF calls."""
from concurrent.futures import Future
from pathlib import Path
import numpy as np
import pytest
from experiments.candidates.uav_fleet_transmission.b10_service_assignment import budget
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.reader import (
    check_spells, check_assignment_contract, validate_candidate_records, numeric_row_equal)
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.trace import empty_candidate,CANDIDATE_DTYPE
from experiments.candidates.uav_fleet_transmission.b08_anonymous_memory.controller import TRACK_DTYPE


def test_cpu_stop_and_no_more_dispatch(tmp_path,monkeypatch):
    monkeypatch.setattr(budget,"children_cpu",lambda:2.)
    monkeypatch.setattr(budget,"active_descendant_cpu",lambda pid:(3.,1))
    monkeypatch.setattr(budget.time,"process_time",lambda:6.)
    meter=budget.CpuBudget(tmp_path,prior_cpu_seconds=10.,cpu_origin=1.,child_origin=1.,limit=19.)
    assert not meter.poll()  # 10 + 5 parent + 1 reaped + 3 live.
    assert meter.last["checkpoint_cpu_seconds"]==19.
    with pytest.raises(budget.BudgetStop):
        budget.check_worker_stop(tmp_path)
    class Pool:
        def submit(self,*args):
            raise AssertionError("dispatch after budget stop")
    rows=[];submitted=[]
    budget.execute_budgeted(Pool(),[dict(job_key="synthetic")],1,lambda j:j,
        rows.append,submitted,worker_fn=lambda x:x,budget=meter)
    assert not rows and not submitted


def test_reaped_snapshot_retry_counts_no_double_charge(tmp_path,monkeypatch):
    reaped=iter((2.,4.,4.,4.))
    monkeypatch.setattr(budget,"children_cpu",lambda:next(reaped))
    live=iter(((5.,1),(0.,0)))
    monkeypatch.setattr(budget,"active_descendant_cpu",lambda pid:next(live))
    monkeypatch.setattr(budget.time,"process_time",lambda:1.)
    meter=budget.CpuBudget(tmp_path,0.,cpu_origin=0.,child_origin=0.,limit=10.)
    assert meter.poll() and meter.last["checkpoint_cpu_seconds"]==5.
    assert meter.last["stable_reap_snapshot"]


def test_dispatch_failure_preserves_rows_and_stops(tmp_path):
    class Meter:
        def poll(self):return True
    class Pool:
        def submit(self,fn,payload):
            f=Future();f.set_result(dict(**payload,status="failed",preserved="prefix"));return f
    rows=[];submitted=[]
    plan=[dict(job_key=str(i)) for i in range(3)]
    budget.execute_budgeted(Pool(),plan,1,lambda j:j,rows.append,submitted,worker_fn=lambda x:x,budget=Meter())
    assert submitted==["0"] and rows==[dict(job_key="0",status="failed",preserved="prefix")]


def test_all_gap_censoring_and_nested_reduction():
    records=[dict(start=0,stop=2,length=2,left_censored=True,right_censored=False),
             dict(start=3,stop=4,length=1,left_censored=False,right_censored=True)]
    check_spells(records,[1,1,0,1],"fixture")
    numeric_row_equal({"gaps":[records,[]]},{"gaps":[records,[]]},"ragged")
    with pytest.raises(AssertionError):
        check_spells(records[:1],[1,1,0,1],"omitted-tail")


def assignment_fixture():
    ordinary=np.arange(16,dtype=np.float64).reshape(8,2)*100.
    users=np.full((1,30,2),np.nan);users[0,:2]=[[200.,200.],[400.,400.]]
    velocity=np.full((1,30,2),np.nan);velocity[0,:2]=0.
    tracks=np.zeros((1,30),dtype=TRACK_DTYPE)
    selected=ordinary.copy();selected[[2,3]]=selected[[3,2]]
    rows=[]
    for index,pair in enumerate(((-1,-1),(2,3))):
        xy=ordinary if index==0 else selected
        row=empty_candidate(0,index,pair,np.column_stack((xy,np.full(8,100.))),2)
        row["ticks"]=row["ticks_started"]=30;row["rf_started"]=row["rf_completed"]=3
        row["completed"]=row["accepted"]=True;row["selected"]=index==1
        row["qos"][0]=index*.1;row["score"]=float(index);rows.append(row)
    priority=np.full((1,8,2),np.nan);priority[0,:4]=ordinary[:4]
    ring=np.full((1,8,2),np.nan);ring[0,:4]=ordinary[4:]
    return dict(plan_step=np.array([0]),plan_assignment_role=np.array([[1,1,2,2,3,3,3,3]]),
        plan_assignment_call=np.array([[1,1,1,1,2,2,2,2]]),
        plan_assignment_column=np.array([[0,1,2,3,0,1,2,3]]),
        plan_ordinary_targets=ordinary[None],plan_targets=selected[None],
        plan_priority=priority,plan_priority_count=np.array([4]),plan_relay_count=np.array([2]),
        plan_ring=ring,plan_ring_count=np.array([4]),plan_eligible=np.array([[0,0,1,1,0,0,0,0]],bool),
        plan_fallback=np.array([0]),plan_bs=np.array([[0.,0.]]),
        plan_user_count=np.array([2]),trace_current_count=np.array([2]),plan_users=users,trace_canonical=users,
        candidate_records=np.asarray(rows,dtype=CANDIDATE_DTYPE),plan_candidate_count=np.array([2]),
        plan_selected_candidate=np.array([1]),plan_selected_pair=np.array([[2,3]]),
        plan_current_velocities=velocity,trace_tracks=tracks,
        plan_prediction_xy=np.repeat(users[:,None],3,axis=1))


@pytest.mark.parametrize("arm",["H_A","F_A"])
def test_independent_menu_and_role_rejection(arm):
    raw=assignment_fixture()
    validate_candidate_records(raw,arm,True)
    check_assignment_contract(raw,arm)
    raw["plan_assignment_role"][0,2]=1
    with pytest.raises(AssertionError):
        check_assignment_contract(raw,arm)
