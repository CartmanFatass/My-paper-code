"""Pure parsing/accounting and explicitly fake model hooks; no real neural/RNG call."""
import ast
import copy
import hashlib
import json
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
import sys

import numpy as np
import pytest

from experiments.candidates.typed_joint_skill_decision import contract as c,models,read_b01 as reader
from experiments.candidates.typed_joint_skill_decision.data import Bill,COUNTERS,Store,Trace,BudgetExceeded,hash_file
from experiments.candidates.typed_joint_skill_decision.run_b01_learning import dataset_locator


def features():
    return c.make_features([[100.+i,200.,100.] for i in range(6)],[[float(i),float(i+1)] for i in range(50)],
                          [2500.,2500.,30.],[{"construction_slot":slot,"kind":"subset_relay","k":4,
                          "assigned_targets_xyz":[[100.+i+slot,200.,100.] for i in range(6)]} for slot in (0,3)])


def ledger(root):
    return {"schema":1,"prior_counters":dict.fromkeys(COUNTERS,0),"prior_cpu_seconds":0,
            "prior_gpu_seconds":0,"disk_roots":[str(root)]}


def make_store(tmp_path):
    out = tmp_path/"out"
    return Store(out,Bill(ledger(tmp_path),out))


def test_numeric_same_information_independent_field_mapping_and_order():
    value = features()
    candidate,slots = models.numeric_rows(value)
    independent,other_slots = reader.independent_numeric(value)
    assert candidate == independent and slots == other_slots
    assert len(candidate) == 2 and all(len(row)==153 for row in candidate)
    assert candidate[0][:18] == [x/5000 for p in value["initial_uav_xyz"] for x in p]
    reversed_rows,reversed_slots = reader.independent_numeric(value,reverse=True)
    assert reversed_rows == candidate[::-1] and reversed_slots == slots[::-1]
    assert (153+1)*256+(256+1)*256+(256+1) == 105473
    assert 2*1024+(1024+1)*1024+(1024+1) == 1052673


def test_exact_declared_model_reader_context_bill_and_gpu_wall(tmp_path,monkeypatch):
    import experiments.candidates.typed_joint_skill_decision.data as data
    clock = [100.]
    monkeypatch.setattr(data.time,"perf_counter",lambda:clock[0])
    bill = Bill(ledger(tmp_path),tmp_path/"out")
    bill.start_gpu()
    clock[0] += 10
    assert bill.snapshot()["cumulative_gpu_seconds"] == 10
    bill.stop_gpu()
    clock[0] += 50
    assert bill.snapshot()["cumulative_gpu_seconds"] == 10
    for name,cap in (("full_laya_forward_calls",1552),("endpoint_N_contexts",1152),
                     ("reader_N_contexts",2688),("reader_L_contexts",2688),("optimizer_update_calls",3072)):
        bill.enter(name,cap)
        with pytest.raises(BudgetExceeded):
            bill.enter(name)
    assert 3*64*256 == 49152 and 3*(256*2+128*3) == 2688
    assert 1152+384+16 == 1552


def test_source_snapshot_is_automatically_charged_and_deduplicated(tmp_path):
    source = tmp_path/"source"
    source.mkdir()
    (source/"tracked.txt").write_text("scientific input")
    bill = Bill(ledger(tmp_path),tmp_path/"out",source_root=source)
    assert source in bill.roots
    from experiments.candidates.typed_joint_skill_decision.data import allocated_bytes
    assert bill.disk_other+bill.disk_own == allocated_bytes([tmp_path])


def test_same_published_source_sha_is_required_before_model_effects():
    dataset = models.Dataset.__new__(models.Dataset)
    dataset.summary = {"launch_sha":"a"*40}
    dataset.config = {"admission":{"sha":"a"*40}}
    dataset.require_source_sha("a"*40)
    with pytest.raises(ValueError,match="source SHA"):
        dataset.require_source_sha("b"*40)
    dataset.config["admission"]["sha"] = "b"*40
    with pytest.raises(ValueError,match="source SHA"):
        dataset.require_source_sha("a"*40)


def test_unlisted_consumed_artifact_and_changed_locator_are_refused(tmp_path):
    reader.require_members({"summary.json":{}},["summary.json"])
    with pytest.raises(ValueError,match="absent from bound manifest"):
        reader.require_members({"config.json":{}},["summary.json"])
    summary = tmp_path/"summary.json"
    summary.write_bytes(c.encode_json({"status":"complete"}))
    locator = tmp_path/"outside-input.json"
    locator.write_bytes(c.encode_json({"root":str(tmp_path),"manifest_sha256":"a"*64,"summary_sha256":hash_file(summary)}))
    sha = hash_file(locator)
    assert dataset_locator(locator,sha)[0] == tmp_path
    summary.write_bytes(c.encode_json({"status":"failed_partial"}))
    with pytest.raises(ValueError,match="summary changed"):
        dataset_locator(locator,sha)


def test_all_runner_ast_guards_and_canonical_output_alias():
    from scripts.hmasd_launch import _validate_guard_contract,OUTPUT_ARGUMENTS
    assert "--out" in OUTPUT_ARGUMENTS
    root = Path.cwd()/"experiments/candidates/typed_joint_skill_decision"
    for name in ("run_b01_native.py","run_b01_learning.py","read_b01.py"):
        path = root/name
        _validate_guard_contract(path,c.DIRECTION)
        tree = ast.parse(path.read_text())
        adds = [node for node in ast.walk(tree) if isinstance(node,ast.Call)
                and isinstance(node.func,ast.Attribute) and node.func.attr=="add_argument"]
        assert any(any(isinstance(arg,ast.Constant) and arg.value=="--out" for arg in node.args)
                   and any(k.arg=="dest" and isinstance(k.value,ast.Constant) and k.value.value=="out_dir" for k in node.keywords)
                   for node in adds)


def test_manifest_retained_hash_and_alias_binding(tmp_path):
    raw = tmp_path/"retained.txt"
    raw.write_text("fixture")
    retained = {"path":"retained.txt","sha256":hash_file(raw),"bytes":7,"kind":"native_trace",
                "logical_sha256":"a"*64,"status":"complete"}
    discarded = {"path":"discarded.gz","sha256":"c"*64,"bytes":99,"kind":"native_trace",
                 "logical_sha256":"a"*64,"status":"identical_audit"}
    alias = {"kind":"audit_trace_alias","discarded_path":"discarded.gz","retained_path":"retained.txt",
             "logical_sha256":"a"*64}
    manifest = tmp_path/"manifest.jsonl"
    manifest.write_bytes(b"".join(c.encode_json(e) for e in (retained,discarded,alias)))
    assert set(models.verify_manifest(tmp_path,hash_file(manifest))) == {"retained.txt","discarded.gz"}
    raw.write_text("changed")
    with pytest.raises(ValueError,match="input file drift"):
        models.verify_manifest(tmp_path,hash_file(manifest))


class FakeTensor:
    dtype = "float32"
    def __init__(self,shape):
        self.shape = shape
    def detach(self): return self
    def clone(self): return FakeTensor(self.shape)
    def cpu(self): return self
    def __getitem__(self,item): return FakeTensor(self.shape[1:])


class FakeScorer:
    def __init__(self): self.hook=None;self.removed=False
    def register_forward_pre_hook(self,callback):
        self.hook = callback
        def remove(): self.hook=None;self.removed=True
        return SimpleNamespace(remove=remove)


class FakeSource:
    def __init__(self,fail=False): self.scorer=FakeScorer();self.fail=fail
    def __call__(self,ids,mask,markers,marker_mask,qtype):
        if self.fail: raise RuntimeError("fake forward failure")
        count = markers.shape[1]
        self.scorer.hook(self.scorer,(FakeTensor((1,count,1024)),))
        return FakeTensor((1,count)),FakeTensor((1,2))


def fake_torch():
    return SimpleNamespace(float32="float32",long="long",bool="bool",
        tensor=lambda values,**kw:FakeTensor((len(values),len(values[0]))),
        ones_like=lambda value,**kw:FakeTensor(value.shape),zeros=lambda shape,**kw:FakeTensor(shape),
        inference_mode=lambda:nullcontext(),cuda=SimpleNamespace(synchronize=lambda:None))


def test_paid_source_pre_hook_capture_counter_and_hook_restoration(tmp_path,monkeypatch):
    monkeypatch.setitem(sys.modules,"torch",fake_torch())
    bill = Bill(ledger(tmp_path),tmp_path/"out")
    encoded = {"input_ids":[1,2,3],"marker_pos":[0,2]}
    source = FakeSource()
    features,logits,act,seconds = models.source_forward(source,encoded,bill,correctness=True)
    assert features.shape == (2,1024) and logits.shape == (2,) and source.scorer.removed
    assert bill.delta["full_laya_forward_calls"] == bill.delta["full_laya_forwards_completed"] == 1
    assert bill.delta["source_scorer_contexts"] == bill.delta["source_act_head_contexts"] == 1
    assert bill.delta["full_forward_correctness_calls"] == bill.delta["full_forward_correctness_completed"] == 1
    failed = FakeSource(fail=True)
    with pytest.raises(RuntimeError,match="fake forward"):
        models.source_forward(failed,encoded,bill)
    assert failed.scorer.removed
    assert bill.delta["full_laya_forward_calls"] == 2 and bill.delta["full_laya_forwards_completed"] == 1


def literal_trace(store,*,bad_backhaul=False):
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
        trace.write({"kind":"step_request","step":step,"positions_xyz":xyz,"actions":[[0.,0.,0.]]*6})
        trace.write({"kind":"step","step":step+1,"positions_xyz":xyz,"reward_info":info,
                     "rewards":{str(i):reward/6 for i in range(6)},"terminations":{str(i):step==499 for i in range(6)},
                     "truncations":{str(i):False for i in range(6)},"user_association":associations,
                     "backhauled_users_mask":([True]+[False]*49 if bad_backhaul else mask),
                     "routing_paths":{"0":[["uav",0],["bs",0]]}})
    entry = trace.close("complete")
    result = {"Q":float(np.mean([.04]*500)),"association_change_count":0,"backhaul_loss_events":0}
    for key in ("contract_reward","coverage_backhauled","frontend_capacity_with_path_mbps","mean_relays_per_routed_uav"):
        result[key+"_mean_all"] = float(np.mean([info[key]]*500))
        result[key+"_mean_final100"] = float(np.mean([info[key]]*100))
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
