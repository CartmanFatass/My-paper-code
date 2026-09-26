import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import torch
from torch.nn import functional as F

from experiments.candidates.finite_model_decision_value.b01.host import Worlds
from experiments.candidates.finite_model_decision_value.b01.study import sha256
from experiments.candidates.planning_policy_compression.b01.model import Student
from experiments.candidates.planning_policy_compression.b01.study import stage_weights, train_stage
from experiments.candidates.planning_policy_compression.b03.study import (
    Config, load_archive, run_study, stage_data, train_explicit, weight_maps,
)


@pytest.fixture
def small_archive(tmp_path):
    config = Config(initial_seeds=(1101,1102), order_seeds=(1201,1202),
        weight_seeds=(1301,1302), evaluation_seeds=(1401,1402),
        evaluation_model_seeds=(1501,1502),
        initial_contexts=1, rollout_contexts=1, evaluation_contexts=1,
        horizon=48, batch=1, train_batch=2, epochs=(1,1), particles=2)
    rng = np.random.default_rng(1707)
    n,h = 6,48
    x = rng.normal(size=(n,h,35)).astype(np.float32)
    y = np.zeros((n,h),np.float32)
    mask = np.zeros((n,h),bool)
    delta = np.zeros((n,h),np.float64)
    mc_se = np.zeros((n,h),np.float64)
    for seq in range(n):
        for base_tick in (0,4,8,12,16,20,24,28):
            tick = base_tick + seq%2
            mask[seq,tick] = True
            y[seq,tick] = (seq+base_tick//4)%2
            delta[seq,tick] = ((seq*7+base_tick//4)%13 - 6) / 20
            mc_se[seq,tick] = .01 + seq*.001
    context = np.repeat(np.arange(3,dtype=np.int64),2)
    agent = np.tile(np.arange(2,dtype=np.int64),3)
    path = tmp_path / "engineering_archive.npz"
    np.savez_compressed(path,x=x,y=y,mask=mask,delta=delta,mc_se=mc_se,
                        context=context,agent=agent)
    blob = path.read_bytes()
    return config,path,hashlib.sha256(blob).hexdigest(),len(blob)


def _load(small_archive):
    config,path,digest,size = small_archive
    return load_archive(path,config,digest,size)


def test_loader_schema_stage_and_digest(small_archive,tmp_path):
    config,path,digest,size = small_archive
    data,stage1,info = _load(small_archive)
    assert info["sha256"] == digest and info["bytes"] == size
    assert stage1.tolist() == [True,True,False,False,False,False]
    assert all(not value.flags.writeable for value in data.values())
    with pytest.raises(ValueError,match="digest/size"):
        load_archive(path,config,"0"*64,size)
    with np.load(path) as contents:
        broken = {name:contents[name].copy() for name in contents.files}
    broken["context"][2] = 0
    malformed = tmp_path / "bad-context.npz"
    np.savez_compressed(malformed,**broken)
    bad_blob = malformed.read_bytes()
    with pytest.raises(ValueError,match="context/agent"):
        load_archive(malformed,config,hashlib.sha256(bad_blob).hexdigest(),len(bad_blob))
    broken["context"][2] = 1
    broken["mask"][:2] = False
    malformed = tmp_path / "bad-stage.npz"
    np.savez_compressed(malformed,**broken)
    bad_blob = malformed.read_bytes()
    with pytest.raises(ValueError,match="stage assignment/eligibility"):
        load_archive(malformed,config,hashlib.sha256(bad_blob).hexdigest(),len(bad_blob))
    broken["mask"][:2] = True
    malformed = tmp_path / "bad-eligible-slot.npz"
    np.savez_compressed(malformed,**broken)
    bad_blob = malformed.read_bytes()
    with pytest.raises(ValueError,match="nonsender or forced"):
        load_archive(malformed,config,hashlib.sha256(bad_blob).hexdigest(),len(bad_blob))


def test_maps_input_immutability_and_b01_training_identity(small_archive):
    config,_,_,_ = small_archive
    data,stage1,_ = _load(small_archive)
    first = stage_data(data,stage1)
    digest_before = {key:hashlib.sha256(value.tobytes()).hexdigest() for key,value in data.items()}
    weights,identity = weight_maps(first,0,1,config.weight_seeds[0])
    assert identity["changed_assignments"] > 0
    repeated,_ = weight_maps(first,0,1,config.weight_seeds[0])
    for key in weights:
        np.testing.assert_array_equal(weights[key],repeated[key])
        assert identity["array_sha256"][key] == hashlib.sha256(weights[key].tobytes()).hexdigest()
    for label in (0,1):
        dest = weights[f"label{label}_destination"]
        source = weights[f"label{label}_source"]
        np.testing.assert_array_equal(np.sort(weights["shuffled"].ravel()[dest]),
                                      np.sort(weights["original"].ravel()[dest]))
        assert set(source.tolist()) == set(dest.tolist())
    assert {key:hashlib.sha256(value.tobytes()).hexdigest() for key,value in data.items()} == digest_before
    torch.manual_seed(241)
    initial_model = Student()
    initial = {name:value.clone() for name,value in initial_model.state_dict().items()}
    for arm,weighted,explicit in (("O",True,weights["original"]),
                                  ("BC",False,weights["unit"])):
        old,new = Student(),Student()
        old.load_state_dict(initial)
        new.load_state_dict(initial)
        old_opt = torch.optim.Adam(old.parameters(),lr=.001)
        new_opt = torch.optim.Adam(new.parameters(),lr=.001)
        old_curves,old_updates,old_rows,_ = train_stage(old,old_opt,first,
            weighted=weighted,model_seed=config.order_seeds[0],block=0,stage=1,
            epochs=1,batch=2,initial=initial)
        new_curves,new_updates,new_rows = train_explicit(new,new_opt,first,explicit,
            order_seed=config.order_seeds[0],pair=0,stage=1,epochs=1,batch=2,initial=initial)
        assert old_updates == new_updates == 1 and old_rows == new_rows == 96
        assert old_curves[0]["loss"] == pytest.approx(new_curves[0]["loss"],abs=1e-7)
        for name,value in old.state_dict().items():
            torch.testing.assert_close(value,new.state_dict()[name],rtol=0,atol=0)
        assert {int(state["step"]) for state in new_opt.state.values()} == {1}
        full_weights,_ = weight_maps(data,0,2,config.weight_seeds[0])
        original_stage2 = full_weights["original"] if weighted else full_weights["unit"]
        writable_stage2 = {name:np.array(value,copy=True) for name,value in data.items()}
        old_stage2,_,_,_ = train_stage(old,old_opt,writable_stage2,weighted=weighted,
            model_seed=config.order_seeds[0],block=0,stage=2,epochs=1,batch=2,initial=initial)
        new_stage2,_,_ = train_explicit(new,new_opt,data,original_stage2,
            order_seed=config.order_seeds[0],pair=0,stage=2,epochs=1,batch=2,initial=initial)
        assert old_stage2[0]["loss"] == pytest.approx(new_stage2[0]["loss"],abs=1e-7)
        for name,value in old.state_dict().items():
            torch.testing.assert_close(value,new.state_dict()[name],rtol=0,atol=0)
        assert {int(state["step"]) for state in new_opt.state.values()} == {4}


def test_shuffled_weights_change_actual_loss_and_gradient(small_archive):
    config,_,_,_ = small_archive
    data,stage1,_ = _load(small_archive)
    first = stage_data(data,stage1)
    weights,_ = weight_maps(first,0,1,config.weight_seeds[0])
    torch.manual_seed(91)
    model = Student()
    logits,_ = model(torch.tensor(first["x"]))
    valid = first["mask"]
    target = torch.tensor(first["y"])
    bce = F.binary_cross_entropy_with_logits(logits[valid],target[valid],reduction="none")
    o_loss = (bce*torch.tensor(weights["original"][valid])).sum()/int(valid.sum())
    s_loss = (bce*torch.tensor(weights["shuffled"][valid])).sum()/int(valid.sum())
    assert abs(float(o_loss-s_loss)) > 1e-7
    original_grad = torch.autograd.grad(o_loss,model.input.weight,retain_graph=True)[0]
    shuffled_grad = torch.autograd.grad(s_loss,model.input.weight)[0]
    assert not torch.allclose(original_grad,shuffled_grad,rtol=1e-6,atol=1e-8)


def test_tiny_complete_study_counts_pairing_and_artifacts(small_archive,tmp_path):
    config,path,digest,size = small_archive
    out = tmp_path / "run"
    summary = run_study(out,path,"fixture-sha",config,expected_sha=digest,expected_bytes=size)
    assert summary["state"] == "COMPLETE"
    counts = summary["counts"]
    assert counts["policy_fits_started"] == counts["policy_fits_completed"] == 6
    assert counts["optimizer_updates"] == 24
    assert counts["processed_agent_time_rows"] == 6*2*48*(1+3)
    assert counts["evaluation_team_ticks"] == 2*3*48
    assert counts["endpoint_diagnostic_agent_time_rows"] == 6*(2+6)*48
    assert counts["calibration_fits"] == 2 and counts["calibration_moves"] == 8
    assert counts["training_collection_team_ticks"] == counts["teacher_queries"] == counts["model_branch_transitions"] == 0
    assert len(summary["fits"]) == 6 and len(summary["endpoint_diagnostics"]) == 12
    assert all(fit["parameter_movement_l2"] > 0 for fit in summary["fits"])
    assert len(json.loads((out / "per_context.json").read_text())) == 2
    for pair in range(2):
        fits = [fit for fit in summary["fits"] if fit["pair"] == pair]
        assert len({fit["initial_state_sha256"] for fit in fits}) == 1
        assert all(fit["updates"] == 4 for fit in fits)
        for arm in ("O","S","BC"):
            stage1 = torch.load(out / "raw" / f"pair{pair}_{arm}_stage1.pt",weights_only=False)
            final = torch.load(out / "raw" / f"pair{pair}_{arm}_final.pt",weights_only=False)
            assert {int(state["step"]) for state in stage1["optimizer"]["state"].values()} == {1}
            assert {int(state["step"]) for state in final["optimizer"]["state"].values()} == {4}
            cost = [row for row in summary["batch_costs"] if row["pair"] == pair and row["arm"] == arm]
            assert len(cost) == 1 and cost[0]["model"] == {} and cost[0]["filter"] == {}
            assert cost[0]["optional_roots"] == 0
        reading = summary["descriptive_native_reading"]["pairs"][pair]
        diffs = reading["integer_completed_job_total_differences"]
        assert diffs["O-BC"] == diffs["O-S"]+diffs["S-BC"]
        assert all(key in reading["loss_worlds"] for key in diffs)
        assert len({row["theta"] for row in json.loads((out / "episodes.json").read_text())
                    if row["pair"] == pair}) == 1
        assert (out / "raw" / f"pair{pair}_evaluation_BC_0000.npz").is_file()
    worlds = [Worlds.make(seed,81,(0,),48,.75).advances for seed in config.evaluation_seeds]
    assert not np.array_equal(worlds[0],worlds[1])
    assert all(sha256(out / item["path"]) == item["sha256"] for item in summary["artifacts"])
    assert not (out / "raw" / "archive.npz").exists()
    with pytest.raises(FileExistsError):
        run_study(out,path,"fixture-sha",config,expected_sha=digest,expected_bytes=size)


def test_partial_fit_failure_keeps_counts_and_checkpoint(small_archive,tmp_path,monkeypatch):
    import experiments.candidates.planning_policy_compression.b03.study as b03
    real_train = b03.train_explicit
    def fail_after_one_epoch(*args,**kwargs):
        real_train(*args,**kwargs)
        raise RuntimeError("fixture optimizer interruption")
    monkeypatch.setattr(b03,"train_explicit",fail_after_one_epoch)
    config,path,digest,size = small_archive
    out = tmp_path / "failed"
    with pytest.raises(RuntimeError,match="fixture optimizer interruption"):
        run_study(out,path,"fixture-sha",config,expected_sha=digest,expected_bytes=size)
    summary = json.loads((out / "summary.json").read_text())
    assert summary["state"] == "FAILED" and "descriptive_native_reading" not in summary
    assert summary["status"]["policy_fits_started"] == 1
    assert summary["status"]["optimizer_updates"] == 1
    assert summary["status"]["processed_agent_time_rows"] == 96
    assert (out / "raw" / "pair0_O_initial.pt").is_file()
    assert (out / "raw" / "pair0_O_partial.pt").is_file()
    assert len(summary["weight_mappings"]) == 2


def test_later_evaluation_failure_keeps_completed_method_cost(small_archive,tmp_path,monkeypatch):
    import experiments.candidates.planning_policy_compression.b01.study as b01
    import experiments.candidates.planning_policy_compression.b03.study as b03
    real_batch, real_step = b03.episode_batch, b01._policy_step
    calls = [0]
    def fail_student_step(*args,**kwargs):
        calls[0] += 1
        if calls[0] == 3:
            raise RuntimeError("fixture deployment interruption")
        return real_step(*args,**kwargs)
    def later_arm(*args,**kwargs):
        if kwargs["arm"] == "S":
            monkeypatch.setattr(b01,"_policy_step",fail_student_step)
        return real_batch(*args,**kwargs)
    monkeypatch.setattr(b03,"episode_batch",later_arm)
    config,path,digest,size = small_archive
    out = tmp_path / "failed-evaluation"
    with pytest.raises(RuntimeError,match="fixture deployment interruption"):
        run_study(out,path,"fixture-sha",config,expected_sha=digest,expected_bytes=size)
    summary = json.loads((out / "summary.json").read_text())
    assert summary["state"] == "FAILED" and "descriptive_native_reading" not in summary
    assert summary["status"]["evaluation_team_ticks"] == 48
    assert summary["status"]["executed_evaluation_team_ticks"] == 49
    boundary = summary["pair_timing"]["0"]["deployment_costs"]
    assert boundary["O"]["state"] == "COMPLETE"
    assert boundary["O"]["conditional_total_seconds"] > 0
    assert boundary["S"]["state"] == "FAILED_DEPLOYMENT"
    assert boundary["S"]["attempted_batched_deployment_seconds"] > 0
    with np.load(out / "raw" / "pair0_evaluation_S_0000.npz") as trace:
        assert int(trace["executed_ticks"]) == 1
        assert int(trace["observed_ticks"]) == 2


def test_entry_refuses_before_science(tmp_path):
    root = Path(__file__).resolve().parents[5]
    out = tmp_path / "b03_osbc_archived_s926001_20260926"
    process = subprocess.run([sys.executable,
        str(root / "experiments/candidates/planning_policy_compression/b03/run.py"),
        "--out",str(out),"--data",str(tmp_path / "missing.npz"),
        "--launch-sha","unadmitted"],cwd=root,env=os.environ.copy(),
        capture_output=True,text=True)
    assert process.returncode != 0
    assert not out.exists()
