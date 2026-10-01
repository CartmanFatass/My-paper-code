"""Eight data-only checks. All scientific entrypoints are replaced by doubles."""

from collections import Counter
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import time

import numpy as np
import pytest

from experiments.candidates.uav_radio_information_cost.b02_integrated_package import (
    config, dispatch, entry, reader, reductions, source, study,
)
from experiments.candidates.uav_radio_uncertainty.b01.io import (
    identity, write_json, save_evidence,
)


def data(program, world=29661900):
    """Small primitive arrays, with no sampling, control or radio computation."""
    h = 8
    raw = dict(program=np.array(program),arm=np.array(config.ARMS[program]),
        world=np.array(world),horizon=np.array(h),completed_steps=np.array(h),
        users=np.zeros((50,2)),map_packet=np.zeros(400,np.uint8),
        positions=np.zeros((h+1,5,3)),residual=np.zeros((h+1,5,50)),
        commands=np.zeros((h,5,3)),proposals=np.zeros((2,5,3)),post_c_nav=np.zeros((2,5)),
        mask=np.full(h,31),reward=np.arange(h,dtype=float),served=np.arange(h,dtype=float),
        quality=np.ones(h),refresh_completed=np.zeros(h+1,bool))
    d = config.PACKAGES[program]["delivery"]
    raw["refresh_completed"][d:h+1:4] = True
    weights = np.ones(h)
    if program == "U32_FULL":
        weights[::4] = .9
    arrays = dict(weights=weights,ages=np.tile(np.arange(h)[:,None],(1,50)),
                  contacts=np.zeros((h,50),bool))
    return raw, arrays


def row(program, world, outcome=None):
    raw, arrays = data(program,world)
    return dict(program=program,world=world,arm=config.ARMS[program],steps=8,
        failure=None,physical_counts={"episodes":1},controller_counts={"calls":10},
        model_counts={"candidate_fleet_scores":5,"model_normal_values":0},
        outcome=outcome or dict(payload_J=1.,raw_J=2.,per_user_mean_age=[1.]*50,
            per_user_service_ticks=[2]*50,per_user_max_gap=[3]*50),
        companions=reductions.companions(raw,arrays,program))


def worker_fixture(tmp_path):
    root = tmp_path/"worker"
    root.mkdir()
    spec = config.specification("check")
    bindings = source.verify_sources()
    worker = dict(status="COMPLETE",kind="check",launch_sha="a"*40,
        source_bindings=bindings,rows=[],artifacts=[],constructor={},
        counts=dict(fits=0,optimizer_updates=0,training_episodes=0,
                    complete_episodes=2,native_steps=16,constructor_attempts=1),
        physical_counts={"constructor":1,"episodes":2},controller_counts={"calls":20},
        model_counts={"candidate_fleet_scores":10,"model_normal_values":0})
    write_json(root/"config.json",dict(spec,launch_sha=worker["launch_sha"],source_bindings=bindings))
    worker["config"] = identity(root/"config.json")
    save_evidence(root/"raw"/"constructor.npz",dict(world=np.array(spec["constructor_seed"]),
        horizon=np.array(8)),worker["artifacts"],worker["constructor"])
    raws = []
    for p in config.PROGRAMS:
        raw, arrays = data(p)
        r = row(p,29661900)
        r.update(raw={},outcome_arrays={})
        worker["rows"].append(r)
        save_evidence(root/"raw"/(p+".npz"),raw,worker["artifacts"],r["raw"])
        save_evidence(root/"outcomes"/(p+".npz"),arrays,worker["artifacts"],r["outcome_arrays"])
        raws.append(raw)
    worker["paired_actions"] = [reductions.pair_actions(*raws)]
    worker["paired"] = reductions.paired(worker["rows"],spec)
    write_json(root/"summary.json",worker)
    return root, worker, spec


def test_fixed_order_and_literal_arm_rejection():
    spec = config.specification("main")
    expected = config.expected_order(spec)
    assert len(expected) == 64
    assert expected[:4] == [("U32_FULL",29661000),("P_PRIOR",29661000),
                            ("P_PRIOR",29661001),("U32_FULL",29661001)]
    assert expected[-2:] == [("P_PRIOR",29661031),("U32_FULL",29661031)]
    rows = [dict(program=p,world=w,arm=config.ARMS[p],steps=256,failure=None) for p,w in expected]
    config.validate_rows(rows,spec)
    for bad in (rows[:-1],rows[::-1],rows[:1]+rows[:-1]):
        with pytest.raises(ValueError):
            config.validate_rows(bad,spec)
    bad = copy.deepcopy(rows)
    bad[0]["arm"] = "U32_FULL"
    with pytest.raises(ValueError,match="alias"):
        config.validate_rows(bad,spec)
    check = config.specification("check")
    assert check["worlds"] == [29661900] and check["constructor_seed"] == 29661998
    assert check["horizon"] == 8 and check["order"] == [list(config.PROGRAMS)]


def test_qualified_dispatch_preserves_literal_arm(monkeypatch):
    calls = []
    def import_double(name):
        def collect(env,world,arm,*,horizon):
            calls.append((name,world,arm,horizon))
            return {"arm":np.array(arm)},dict(arm=arm),None
        return SimpleNamespace(__file__=str(source.ROOT/(name.replace(".","/")+".py")),collect_episode=collect)
    monkeypatch.setattr(dispatch,"import_module",import_double)
    for p in config.PROGRAMS:
        raw,r,failure = dispatch.collect(object(),29661900,p,8)
        assert str(raw["program"]) == r["program"] == p
        assert str(raw["arm"]) == r["arm"] == config.ARMS[p]
        assert failure is None
    assert [x[2] for x in calls] == ["U32","P_PRIOR"]
    assert calls[0][0].endswith("uav_radio_uncertainty.b01.collect")
    assert calls[1][0].endswith("uav_radio_information_cost.b01.collect")
    raw,r,_ = dispatch.collect(object(),29661900,"U32_FULL",8)
    raw["arm"] = np.array("U32_FULL")
    with pytest.raises(ValueError,match="identity"):
        dispatch.verify_episode("U32_FULL",raw,r,{},Counter())


def test_both_source_closures_fail_on_drift(tmp_path):
    manifest = source.verify_sources()
    assert manifest["U32_FULL"]["commit"] == config.SOURCES["U32_FULL"]
    assert manifest["P_PRIOR"]["commit"] == config.SOURCES["P_PRIOR"]
    for program in config.PROGRAMS:
        assert "envs/pettingzoo/uav_env.py" in manifest[program]["files"]
        assert "experiments/candidates/uav_local_history/b01/controller.py" in manifest[program]["files"]
    # Copies contain only versioned source bytes, below pytest-owned tmp_path.
    root = tmp_path/"source"
    paths = {p for closure in manifest.values() for p in closure["files"]}
    for p in paths:
        target = root/p
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((source.ROOT/p).read_bytes())
    source.verify_sources(root)
    for program in config.PROGRAMS:
        p = next(x for x in manifest[program]["files"] if x.endswith("/collect.py") and dispatch.PREFIXES[program].replace(".","/") in x)
        original = (root/p).read_bytes()
        (root/p).write_bytes(original+b"\n# drift\n")
        with pytest.raises(ValueError,match="drift"):
            source.verify_sources(root)
        (root/p).write_bytes(original)


def test_pairing_and_windows_preserve_history():
    full, fa = data("U32_FULL")
    prior, pa = data("P_PRIOR")
    prior["residual"][1:] = 42.  # Later residual equality is expressly unnecessary.
    prior["commands"][3,2,0] = 1.
    prior["mask"][4] = 30
    prior["proposals"][1,0,0] = 1.
    prior["post_c_nav"][1,0] = 1
    difference = reductions.pair_actions(full,prior)
    reductions.verify_actions(full,prior,difference)
    assert difference["command_difference_ticks"] == 1
    assert difference["mask_difference_ticks"] == 1
    for p,raw,a in (("U32_FULL",full,fa),("P_PRIOR",prior,pa)):
        window = reductions.companions(raw,a,p)
        reductions.verify_companions(raw,a,p,window)
        assert window["startup"]["ticks"] == config.PACKAGES[p]["delivery"]
        assert window["final4"]["mean_age"] == 5.5
        assert window["delivery"]["last_candidate_ticks"] == (1 if p=="U32_FULL" else 2)
    prior["residual"][0,0,0] = 1.
    with pytest.raises(AssertionError):
        reductions.pair_actions(full,prior)


def test_full_world_reductions_and_independent_scalar_check():
    spec = config.specification("main")
    rows = []
    for p,w in config.expected_order(spec):
        r = row(p,w)
        r["steps"] = 256
        r["outcome"]["payload_J"] = float(w-spec["worlds"][0])+(2. if p=="U32_FULL" else 0.)
        rows.append(r)
    panel = reductions.paired(rows,spec)
    reductions.verify_pairing(rows,spec,panel)
    effect = panel["complete"]["contrast_U32_FULL_minus_PRIOR"]["payload_J"]
    assert effect["n"] == 32 and effect["values"] == [2.]*32
    assert effect["mean"] == 2. and effect["descriptive_196se"] == [2.,2.]
    assert len(panel["per_world_user_differences"]) == 32
    panel["complete"]["levels"]["U32_FULL"]["payload_J"]["mean"] += 1
    with pytest.raises(ValueError):
        reductions.verify_pairing(rows,spec,panel)


def test_complete_reader_routing_and_incomplete_identity_failures(tmp_path,monkeypatch):
    root, worker, spec = worker_fixture(tmp_path)
    seen = []
    def ctor(raw,counts):
        counts.update(reference_native_normal_values=250,reference_native_geometry_uniform_values=115,
                      reference_native_user_sinr_calls=1,reference_native_constructors_verified=1)
        return dict(physical_counts={"constructor":1})
    def episode(program,raw,r,arrays,counts):
        seen.append((program,str(raw["arm"]),r["arm"]))
        counts.update(reference_native_normal_values=2250,reference_native_geometry_uniform_values=115,
            reference_native_user_sinr_calls=11,reference_current_c_calls=20,
            reference_decisions=2,reference_native_episodes_verified=1,
            reference_user_age_updates=400,reference_candidate_fleet_scores=5)
        if program == "U32_FULL":
            counts.update(reference_native_sensor_link_entries=500,reference_native_pilot_slots=100)
        return dict(native={"verified":True})
    monkeypatch.setattr(dispatch,"module",lambda *args:SimpleNamespace(verify_constructor=ctor))
    monkeypatch.setattr(dispatch,"verify_episode",episode)
    import torch
    monkeypatch.setattr(torch,"set_num_threads",lambda value:None)
    summary = root/"summary.json"
    result = reader.read_result(summary,tmp_path/"read",identity(summary)["sha256"],
        "a"*40,{"sha":"b"*40},time.perf_counter(),kind="check")
    assert result["status"] == "VERIFIED_COMPLETE",result.get("error")
    assert seen == [("U32_FULL","U32","U32"),("P_PRIOR","P_PRIOR","P_PRIOR")]
    assert result["counts"]["new_native_steps"] == 0
    for i,mutate in enumerate((
        lambda w:w.update(status="RUNNING"),
        lambda w:w["rows"].pop(),
        lambda w:w["rows"][0].update(arm="U32_FULL"),
        lambda w:w["rows"][1].update(raw=w["rows"][0]["raw"]),
        lambda w:w["rows"][0]["raw"].update(sha256="0"*64),
    )):
        bad = copy.deepcopy(worker)
        mutate(bad)
        write_json(summary,bad)
        failed = reader.read_result(summary,tmp_path/f"bad{i}",identity(summary)["sha256"],
            "a"*40,{"sha":"b"*40},time.perf_counter(),kind="check")
        assert failed["status"] == "INCOMPLETE_READING_FAILURE"
        assert (tmp_path/f"bad{i}"/"summary.json").is_file()
    write_json(summary,worker)
    failed = reader.read_result(summary,tmp_path/"digest", "0"*64,"a"*40,
        {"sha":"b"*40},time.perf_counter(),kind="check")
    assert failed["status"] == "INCOMPLETE_READING_FAILURE"


def test_admission_precedes_effects_and_fixed_check_route(tmp_path,monkeypatch):
    import scripts.hmasd_admission as admission
    events = []
    monkeypatch.setattr(admission,"require_admission",lambda script,**kw:
        (events.append(("admit",script,kw)),{"sha":"a"*40})[1])
    monkeypatch.setattr(entry,"verify_sources",lambda:events.append(("source",)))
    monkeypatch.setattr(study,"run_batch",lambda *args:events.append(("run",)) or {"status":"COMPLETE"})
    monkeypatch.setattr(study,"run_check",lambda *args:events.append(("check",)) or {"status":"VERIFIED_COMPLETE"})
    monkeypatch.setattr(reader,"read_result",lambda *args:events.append(("read",)) or {"status":"VERIFIED_COMPLETE"})
    for mode,seed in (("run",29661000),("check",29661900),("read",29661000)):
        args = ["--out",str(tmp_path/mode),"--seed",str(seed),"--launch-sha","a"*40]
        if mode == "read":
            args += ["--generic-summary",str(tmp_path/"unused"),"--worker-summary-sha256","c"*64,"--worker-launch-sha","d"*40]
        events.clear()
        entry.main(mode+".py",mode,args)
        assert [x[0] for x in events] == ["admit","source",mode]
        events.clear()
        args[args.index("--seed")+1] = "1"
        with pytest.raises(SystemExit):
            entry.main(mode+".py",mode,args)
        assert events == []


def test_worker_partial_persistence_and_check_full_read_route(tmp_path,monkeypatch):
    import torch
    import experiments.candidates.uav_user_waiting.b02.storage as storage
    monkeypatch.setattr(torch,"set_num_threads",lambda value:None)
    monkeypatch.setattr(torch,"set_num_interop_threads",lambda value:None)
    env = SimpleNamespace(env=SimpleNamespace(physical_counters={"constructor":1,"episodes":1}),close=lambda:None)
    monkeypatch.setattr(dispatch,"module",lambda p,c:SimpleNamespace(
        make_env=lambda *a,**kw:env,constructor_witness=lambda e:dict(world=np.array(29661998),horizon=np.array(8))))
    def collect(*args):
        raw,_ = data("U32_FULL")
        r = row("U32_FULL",29661900)
        r.update(steps=2,failure={"type":"ValueError","message":"paid partial"})
        return raw,r,ValueError("paid partial")
    monkeypatch.setattr(dispatch,"collect",collect)
    monkeypatch.setattr(dispatch,"outcomes",lambda *args:pytest.fail("reduced failed episode"))
    result = study.run_batch(tmp_path/"failed","a"*40,{"sha":"a"*40},time.perf_counter(),kind="check")
    assert result["status"] == "INCOMPLETE_TECHNICAL_FAILURE"
    assert result["counts"]["native_steps"] == 2 and result["counts"]["complete_episodes"] == 0
    assert result["rows"][0]["raw"]["write_status"] == "complete"
    assert Path(result["rows"][0]["raw"]["path"]).is_file()
    with pytest.raises(FileExistsError):
        study.run_batch(tmp_path/"failed","a"*40,{"sha":"a"*40},time.perf_counter(),kind="check")
    # check orchestration binds the exact saved worker digest and calls the full
    # generic reader at kind=check, without either original correctness recipe.
    calls = []
    target = tmp_path/"check"
    target.mkdir()
    def batch(out,sha,admission,started,kind):
        calls.append(("worker",kind))
        write_json(out/"summary.json",{"status":"COMPLETE"})
        return dict(status="COMPLETE",counts={"native_steps":16})
    def reading(summary,out,digest,worker_sha,admission,started,kind):
        calls.append(("reader",kind,digest,worker_sha))
        assert digest == identity(summary)["sha256"]
        write_json(out/"summary.json",{"status":"VERIFIED_COMPLETE"})
        return dict(status="VERIFIED_COMPLETE",counts={"new_native_steps":0})
    monkeypatch.setattr(study,"run_batch",batch)
    monkeypatch.setattr(reader,"read_result",reading)
    result = study.run_check(target,"a"*40,{"sha":"a"*40},time.perf_counter())
    assert result["status"] == "VERIFIED_COMPLETE"
    assert [x[:2] for x in calls] == [("worker","check"),("reader","check")]
