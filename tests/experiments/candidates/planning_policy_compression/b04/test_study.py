import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import torch

from experiments.candidates.planning_policy_compression.b04.study import Config, run_study


@pytest.fixture
def tiny_config():
    return Config(initial_seeds=(3101,3102),order_seeds=(3201,3202),
        collection_seeds=(3301,3302),collection_model_seeds=(3401,3402),
        evaluation_seeds=(3501,3502),evaluation_model_seeds=(3601,3602),
        prefix_contexts=1,rollin_contexts=1,evaluation_contexts=1,
        horizon=48,batch=1,train_batch=2,epochs=(1,1),particles=2)


def test_tiny_complete_own_data_pairing_cost_and_counts(tiny_config,tmp_path,monkeypatch):
    import experiments.candidates.planning_policy_compression.b04.study as b04
    original_episode=b04.episode_batch
    original_train=b04.train_stage
    rollin_calls={}
    trained_stage2=[]
    sentinels={"O_ROLLIN":7.,"BC_ROLLIN":13.}
    def marked_episode(*args,**kwargs):
        rows,data,cost=original_episode(*args,**kwargs)
        if kwargs["arm"] in sentinels:
            block=kwargs["seed"]
            rollin_calls[(block,kwargs["arm"])]=dict(ids=tuple(args[0]),
                theta=np.array(args[1],copy=True),posterior=np.array(args[2],copy=True),
                moves=np.array(args[3],copy=True),phase=kwargs["phase"],
                model_seed=kwargs["model_seed"],model_phase=kwargs["model_phase"])
            data["x"][:,:,34]=sentinels[kwargs["arm"]]
        return rows,data,cost
    def inspected_train(model,optimizer,data,**kwargs):
        if kwargs["stage"]==2:
            tail=data["x"][2:,:,34]
            expected=sentinels["O_ROLLIN" if kwargs["weighted"] else "BC_ROLLIN"]
            assert np.all(tail==expected)
            trained_stage2.append((kwargs["block"],kwargs["weighted"]))
        return original_train(model,optimizer,data,**kwargs)
    monkeypatch.setattr(b04,"episode_batch",marked_episode)
    monkeypatch.setattr(b04,"train_stage",inspected_train)
    out=tmp_path/"tiny"
    result=run_study(out,"fixture-sha",tiny_config)
    counts=result["counts"]
    assert result["state"]=="COMPLETE"
    assert counts["policy_fits_started"]==counts["policy_fits_completed"]==4
    assert counts["optimizer_updates"]==12
    assert counts["processed_agent_time_rows"]==4*2*48*(1+2)
    assert counts["collection_team_ticks"]==2*(1+2)*48
    assert counts["evaluation_team_ticks"]==2*4*48
    assert counts["endpoint_diagnostic_agent_time_rows"]==8*48*(2+1)
    assert counts["calibration_fits"]==6 and counts["calibration_moves"]==24
    assert len(result["endpoint_diagnostics"])==8
    for block in range(2):
        prefix=np.load(out/"raw"/f"block{block}_prefix.npz")
        datasets={arm:np.load(out/"raw"/f"block{block}_{arm}_training.npz")
                  for arm in ("O","BC")}
        roll={arm:np.load(out/"raw"/f"block{block}_{arm}_rollin.npz")
              for arm in ("O","BC")}
        for arm in ("O","BC"):
            data=datasets[arm]
            assert data["context"].tolist()==[0,0,1,1]
            for name in prefix.files:
                np.testing.assert_array_equal(data[name][:2],prefix[name])
                np.testing.assert_array_equal(data[name][2:],roll[arm][name])
            fit=next(f for f in result["fits"] if f["block"]==block and f["arm"]==arm)
            assert fit["updates"]==3 and fit["parameter_movement_l2"]>0
            stage1=torch.load(out/"raw"/f"block{block}_{arm}_stage1.pt",weights_only=False)
            final=torch.load(out/"raw"/f"block{block}_{arm}_final.pt",weights_only=False)
            assert {int(s["step"]) for s in stage1["optimizer"]["state"].values()}=={1}
            assert {int(s["step"]) for s in final["optimizer"]["state"].values()}=={3}
            charged=next(c for c in result["standalone_method_costs"]
                         if c["block"]==block and c["arm"]==arm)
            assert charged["prefix_charged_in_full"]
            assert charged["required_acquisition_team_ticks"]==2*48
            assert charged["required_calibration_contexts"]==2
            eval_cost=next(c for c in result["batch_costs"] if c["block"]==block and
                c["group"]=="evaluation" and c["arm"]==arm)
            assert eval_cost["model"]==eval_cost["filter"]=={}
            assert eval_cost["optional_roots"]==0
        p=[x for x in result["data_provenance"] if x["block"]==block]
        assert len(p)==3
        assert p[1]["calibration"]["sha256"]==p[2]["calibration"]["sha256"]
        assert p[1]["world_seed"]==p[2]["world_seed"]
        assert p[1]["world_phase"]==p[2]["world_phase"]
        call_o=rollin_calls[(tiny_config.collection_seeds[block],"O_ROLLIN")]
        call_bc=rollin_calls[(tiny_config.collection_seeds[block],"BC_ROLLIN")]
        for name in ("ids","theta","posterior","moves","phase","model_seed","model_phase"):
            np.testing.assert_array_equal(call_o[name],call_bc[name])
        assert call_o["ids"]==(1,)
        assert call_o["phase"]==tiny_config.rollin_phases[1]
        assert call_o["model_phase"]==tiny_config.rollin_phases[2]
        fits=[f for f in result["fits"] if f["block"]==block]
        assert fits[0]["initial_state_sha256"]==fits[1]["initial_state_sha256"]
        reading=result["descriptive_native_reading"]["blocks"][block]
        diff=reading["integer_completed_job_total_differences"]
        assert diff["O-AF"]==diff["O-BC"]+diff["BC-AF"]
        assert set(reading["loss_worlds"])==set(diff)
        assert all(d["data_scope"]==f"{d['arm']}_own_prefix_plus_rollin_descriptive"
                   for d in result["endpoint_diagnostics"] if d["block"]==block and d["stage"]==2)
        prefix_cost=next(c for c in result["batch_costs"] if c["block"]==block and c["group"]=="prefix")
        prefix_cal=p[0]["calibration"]
        for arm in ("O","BC"):
            own_cost=next(c for c in result["batch_costs"] if c["block"]==block and
                          c["group"]=="rollin" and c["arm"]==f"{arm}_ROLLIN")
            own_cal=next(x for x in p if x["owner"]==arm)["calibration"]
            charged=next(c for c in result["standalone_method_costs"]
                         if c["block"]==block and c["arm"]==arm)
            expected=(prefix_cost["wall_seconds"]+own_cost["wall_seconds"]+
                prefix_cal["generation_seconds"]+prefix_cal["posterior_seconds"]+
                own_cal["generation_seconds"]+own_cal["posterior_seconds"])
            assert charged["required_acquisition_wall_seconds"]==pytest.approx(expected)
    # One-context fixtures may happen to induce identical action histories; ownership,
    # storage and each stage-two input are still distinct.
    assert result["data_provenance"][1]["dataset"]["path"] != result["data_provenance"][2]["dataset"]["path"]
    assert sorted(trained_stage2)==[(0,False),(0,True),(1,False),(1,True)]
    with pytest.raises(FileExistsError):
        run_study(out,"fixture-sha",tiny_config)


def test_partial_fit_keeps_purchased_data_updates_checkpoint(tiny_config,tmp_path,monkeypatch):
    import experiments.candidates.planning_policy_compression.b04.study as b04
    original=b04.train_stage
    def fail_after_stage(*args,**kwargs):
        answer=original(*args,**kwargs)
        if kwargs["stage"]==2:
            raise RuntimeError("fixture stage2 interruption")
        return answer
    monkeypatch.setattr(b04,"train_stage",fail_after_stage)
    out=tmp_path/"partial-fit"
    with pytest.raises(RuntimeError,match="fixture stage2 interruption"):
        run_study(out,"fixture-sha",tiny_config)
    summary=json.loads((out/"summary.json").read_text())
    assert summary["state"]=="FAILED" and "descriptive_native_reading" not in summary
    assert summary["status"]["policy_fits_started"]==2
    assert summary["status"]["optimizer_updates"]==4
    assert summary["status"]["collection_team_ticks"]==3*48
    assert (out/"raw"/"block0_O_partial.pt").is_file()
    assert (out/"raw"/"block0_O_rollin.npz").is_file()
    assert (out/"raw"/"block0_BC_rollin.npz").is_file()
    assert len(summary["data_provenance"])==3


def test_failed_later_deployment_retains_completed_arm_and_trace(tiny_config,tmp_path,monkeypatch):
    import experiments.candidates.planning_policy_compression.b04.study as b04
    import experiments.candidates.finite_model_decision_value.b01.host as host
    original=b04.episode_batch
    def fail_later(*args,**kwargs):
        if kwargs["arm"]=="BC" and not kwargs["labels"]:
            real_step=host.CrossingHost.step
            calls=0
            def fail_step(self,requested):
                nonlocal calls
                calls+=1
                if calls==2:
                    raise RuntimeError("fixture later deployment")
                return real_step(self,requested)
            with monkeypatch.context() as local:
                local.setattr(host.CrossingHost,"step",fail_step)
                return original(*args,**kwargs)
        return original(*args,**kwargs)
    monkeypatch.setattr(b04,"episode_batch",fail_later)
    out=tmp_path/"partial-evaluation"
    with pytest.raises(RuntimeError,match="fixture later deployment"):
        run_study(out,"fixture-sha",tiny_config)
    summary=json.loads((out/"summary.json").read_text())
    assert summary["state"]=="FAILED"
    deployment=summary["block_timing"]["0"]["deployment_costs"]
    assert deployment["O"]["state"]=="COMPLETE"
    assert deployment["BC"]["state"]=="FAILED_DEPLOYMENT"
    assert summary["status"]["evaluation_team_ticks"]==48
    assert summary["status"]["executed_evaluation_team_ticks"]==49
    assert (out/"raw"/"block0_evaluation_O_0000.npz").is_file()
    failed=np.load(out/"raw"/"block0_evaluation_BC_0000.npz")
    assert int(failed["executed_ticks"])==1
    assert int(failed["observed_ticks"])==2
    assert summary["batch_costs"][-1]["state"]=="FAILED"
    assert not summary["completed_block_results"]


def test_unadmitted_entry_refuses_before_science(tmp_path):
    entry=Path(__file__).resolve().parents[5]/"experiments"/"candidates"/"planning_policy_compression"/"b04"/"run.py"
    out=tmp_path/"b04_standalone_rollin_s926501_20260926"
    result=subprocess.run([sys.executable,str(entry),"--out",str(out),
        "--seed","926501","--launch-sha","fixture-sha"],
        capture_output=True,text=True,env={**os.environ,"HMASD_ADMISSION_FILE":""})
    assert result.returncode!=0
    assert not (out/"raw").exists() and not (out/"summary.json").exists()
