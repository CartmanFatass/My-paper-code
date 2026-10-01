"""Exactly one declared two artificial-world/six-cell H24 pipeline."""
from copy import deepcopy
from dataclasses import replace
import json
import time
import numpy as np
import pytest
import torch
from experiments.candidates.uav_fleet_adaptation.b02.model import Student,make_student
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.environment import original_layout
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.physics import scalar_state
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.study import load_raw
from experiments.candidates.uav_fleet_adaptation.b11_silence_commitment import audit,policies,reference
from experiments.candidates.uav_fleet_adaptation.b11_silence_commitment.contract import FROZEN,PROGRAMS,CONTRASTS,OBJECT
from experiments.candidates.uav_fleet_adaptation.b11_silence_commitment.read import _read_all,read_result
from experiments.candidates.uav_fleet_adaptation.b11_silence_commitment.study import _execute,run_batch

@pytest.fixture(scope="module")
def paid_checks():
    started=time.perf_counter()
    cpu=time.process_time()
    counts=dict(student_rows=0,reader_scalar_states=0,fake_scalar_states=0,fake_steps=0,worker_off_scores=0,reader_off_scores=0,partial_reference_requests=0,partial_reference_paths=0,partial_reference_ticks=0)
    saved=[]
    def wrap(owner,key,count,amount):
        old=getattr(owner,key)
        saved.append((owner,key,old))
        def call(*args,**kwargs):
            result=old(*args,**kwargs)
            counts[count]+=amount(result)
            return result
        setattr(owner,key,call)
    wrap(Student,"forward","student_rows",lambda x:x.shape[0])
    wrap(audit,"scalar_state","reader_scalar_states",lambda x:1)
    wrap(policies,"off_score","worker_off_scores",lambda x:1)
    wrap(reference,"_off","reader_off_scores",lambda x:1)
    threads=torch.get_num_threads()
    torch.set_num_threads(1)
    yield counts
    for owner,key,old in reversed(saved):
        setattr(owner,key,old)
    torch.set_num_threads(threads)
    print("B11 ACTUAL fake pipeline/support exposure:",json.dumps(counts,sort_keys=True),
        "wall_seconds=",time.perf_counter()-started,"cpu_seconds=",time.process_time()-cpu,"native/result/fits=0")

class FakeEnv:
    def __init__(self, seed, counts, horizon=8):
        self.env, self.n_uavs, self.horizon, self.counts = self, 5, horizon, counts
        self._path_loss_cache_generation = 0
        self._path_loss_cache_misses = 260  # synthetic constructor ledger, no extra physical query

    def _refresh(self, physical=True):
        self.radio = scalar_state(self.uav_positions, self.user_positions, self.transmitter_mask, self.current_step, self.horizon)
        self.counts["fake_scalar_states"] += 1
        self.sinr_matrix, self.uav_sinr_matrix, self.connections = (self.radio[key].copy() for key in ("sinr", "peer_sinr", "connections"))
        if physical:
            self._path_loss_cache_generation += 1
            self._path_loss_cache_misses = 260

    def _state(self):
        return np.r_[self.uav_positions.ravel(), self.user_positions.ravel(), self.current_step / self.horizon].astype(np.float32)

    def _info(self, initial):
        return {"state" if initial else "next_state": self._state(),
                "state_info": dict(uav_positions=self.uav_positions.copy(), user_positions=self.user_positions.copy()),
                "rewards_dict": {f"uav_{i}": self.radio["reward"] / 5. for i in range(5)},
                "infos_dict": {"uav_0": {"global": dict(connections=self.connections.copy(), sinr_matrix=self.sinr_matrix.copy(),
                                                         served_users=self.radio["served"])}}}

    def reset(self, seed):
        self.current_step = 0
        self.uav_positions, self.user_positions = original_layout(seed)
        self.transmitter_mask = np.ones(5, dtype=bool)
        self._refresh()
        return self.radio["observations"].copy(), self._info(True)

    def set_transmitter_mask(self, mask):
        self.transmitter_mask = mask.copy(); self._refresh(physical=False)
        return self.radio["observations"].copy()

    def _dict_to_array(self, rows):
        return rows.copy()

    def step(self, commands):
        self.uav_positions = np.clip(self.uav_positions + commands.astype(np.float64) * 30., [0., 0., 50.], [1000., 1000., 150.])
        self.current_step += 1; self.counts["fake_steps"] += 1; self._refresh()
        return self.radio["observations"].copy(), self.radio["reward"], self.current_step == self.horizon, False, self._info(False)



@pytest.fixture(scope="module")
def tiny(tmp_path_factory,paid_checks):
    out=tmp_path_factory.mktemp("b11_complete_fake")
    (out/"raw").mkdir()
    protocol=replace(FROZEN,worlds=(95001,95002),horizon=24,bootstrap_resamples=11).validate()
    parent=make_student(95031).eval().requires_grad_(False)
    env=FakeEnv(95033,paid_checks,horizon=24)
    counts=dict(fits=0,optimizer_steps=0,new_acquisition_targets=0,gate_draws=0,
        constructor_calls=1,constructor_resets=1,native_dense_power_slots=275,native_unique_distance_pairs=260)
    batch=dict(launch_sha="synthetic-b11",protocol=protocol.to_dict(),expected=protocol.expected(),actual=counts,inflight={},rows=[])
    _execute(out,parent,env,protocol,batch,lambda **kwargs:None)
    report=dict(actual=dict(native_steps=0,optimizer_steps=0,refits=0),inflight={},policy_costs={})
    _read_all(batch,out,parent,protocol,report,lambda **kwargs:None)
    print("B11 complete pipeline only exposure:",json.dumps(paid_checks,sort_keys=True))
    print("B11 fake worker/reader costs:",json.dumps(dict(worker=batch["costs"],reader=report["policy_costs"],reader_actual=report["actual"]),sort_keys=True))
    return out,protocol,parent,batch,report


def test_fixed_bill_no_scientific_query():
    expected=FROZEN.expected()
    for key,value in dict(fits=0,optimizer_steps=0,complete_episodes=192,native_steps=49152,
        native_uav_ticks=245760,motion_requests=61440,motion_draws=20480,mask_installs=12288,
        native_dense_power_slots=16949075,native_unique_distance_pairs=12829700,
        CJ_off_scores=6144,Hdirect_target_vectors=40960,C_path_ceiling=1658880,
        C_model_tick_ceiling=6635520,C_link_ceiling=138854400,controller_link_ceiling=139468800,
        reader_scalar_states=61632,reader_local_rows=308160,reader_scalar_power_links=16640640,
        reader_distance_pairs=16024320,reader_dense_sinr_slots=16948800,worker_layout_draws=22195,
        layout_verification_draws=22080,bootstrap_integers=640000).items():
        assert expected[key]==value
    assert len(PROGRAMS)==5 and len(CONTRASTS)==9 and len(FROZEN.episode_order(0))==6
    assert FROZEN.episode_order(1)==tuple(reversed(FROZEN.episode_order(0)[1:]+FROZEN.episode_order(0)[:1]))
    assert FROZEN.from_dict(FROZEN.to_dict())==FROZEN


def test_complete_fake_pipeline(tiny,paid_checks):
    out,protocol,parent,batch,report=tiny
    assert len(batch["rows"])==12
    assert batch["actual"]["native_steps"]==288 # Explicitly fake ledger, never native exposure.
    assert report["actual"]["scalar_states"]==372 and report["actual"]["scalar_power_links"]==100440
    assert paid_checks["fake_steps"]==288 and paid_checks["fake_scalar_states"]==372
    assert paid_checks["reader_scalar_states"]==372 and paid_checks["student_rows"]<=240 # <=120 per worker/reader pass.
    assert paid_checks["worker_off_scores"]==paid_checks["reader_off_scores"]==36
    assert len(report["comparisons"]["levels"])==5 and len(report["comparisons"]["contrasts"])==9
    assert len(report["per_world_behavior"])==2
    assert report["actual"]["native_steps"]==report["actual"]["optimizer_steps"]==report["actual"]["refits"]==0
    assert report["policy_costs"]==batch["costs"]["all_policy"]
    assert all(row["noneligible_off_requests"]==0 for row in batch["rows"])
    assert all(p.grad is None and not p.requires_grad for p in parent.parameters())
    assert len(list((out/"raw").glob("*.npz")))==12


def test_schema_and_order_corruptions_fail_before_replay(tiny,paid_checks):
    out,protocol,parent,batch,report=tiny
    row=batch["rows"][0]
    raw=load_raw(out/row["raw"]["path"])
    before=paid_checks.copy()
    raw["pending_after"]=raw["pending_after"].astype(np.int64)
    with pytest.raises(AssertionError,match="dtype"):
        audit.audit_episode(raw,row,protocol,parent)
    bad=deepcopy(batch)
    bad["rows"][0],bad["rows"][1]=bad["rows"][1],bad["rows"][0]
    with pytest.raises(AssertionError,match="execution order"):
        _read_all(bad,out,parent,protocol,dict(actual={},inflight={}),lambda **kwargs:None)
    assert paid_checks==before


def test_guard_corruption_rejected_at_first_decision(tiny,paid_checks):
    out,protocol,parent,batch,report=tiny
    row=batch["rows"][0]
    raw=load_raw(out/row["raw"]["path"])
    raw["memory_created"][0,0]=not raw["memory_created"][0,0]
    inflight={}
    with pytest.raises(AssertionError,match="memory_created"):
        audit.audit_episode(raw,row,protocol,parent,inflight=inflight)
    charge_partial(paid_checks,inflight)


def test_production_refuses_before_effects(tmp_path):
    with pytest.raises(ValueError,match="admission"):
        run_batch(tmp_path/"untouched","none",admission=None,asset_paths={})
    assert not (tmp_path/"untouched").exists()
    out=tmp_path/"invalid"
    out.mkdir()
    (out/"summary.json").write_text(json.dumps(dict(object=OBJECT,state="FAILED",scientific_execution=True)))
    with pytest.raises(AssertionError,match="production result"):
        read_result(out,tmp_path)
    assert json.loads((out/"reading.json").read_text())["status"]=="FAILED"
    with pytest.raises(FileExistsError):
        read_result(out,tmp_path)


def charge_partial(paid_checks,inflight):
    for counter in inflight.get("policy_agents",[]):
        paid_checks["partial_reference_requests"]+=counter["policy_requests"]
        paid_checks["partial_reference_paths"]+=counter["trajectories"]
        paid_checks["partial_reference_ticks"]+=counter["model_ticks"]


@pytest.mark.parametrize("field",("origin_agent","origin_tick","origin_row","origin_nav","stored_index"))
def test_saved_memory_origin_corruptions(tiny,paid_checks,field):
    out,protocol,parent,batch,report=tiny
    row=next(row for row in batch["rows"] if row["program"]=="CJ_RETURN" and row["memory_consumed"]>0)
    raw=load_raw(out/row["raw"]["path"])
    di,agent=np.argwhere(raw["memory_consumed"])[0]
    if field=="origin_row":
        raw[field][di,agent,0]+=.125
    else:
        raw[field][di,agent]+=1
    inflight={}
    with pytest.raises(AssertionError,match=field):
        audit.audit_episode(raw,row,protocol,parent,inflight=inflight)
    charge_partial(paid_checks,inflight)


def test_consumed_physical_events_are_retained(tiny):
    out,protocol,parent,batch,report=tiny
    events=[event for audit_row in report["episodes"] for event in audit_row["memory_events"]]
    assert len(events)==2
    for event in events:
        assert event["consumed_tick"]==event["origin_tick"]+4
        assert event["raw_path"].endswith(".npz")
        assert event["consumed_hold_travel_m"]>=0
        assert len(event["consumed_hold_net_displacement_m"])==3
        assert 0<=event["consumed_hold_moving_ticks"]<=4
        assert 0<=event["consumed_hold_clipped_ticks"]<=4
