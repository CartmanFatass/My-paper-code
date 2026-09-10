import importlib.util
import json
import math
from pathlib import Path
import sys

import pytest
import torch

from experiments.candidates.ucope.uav_motion_prefix_b01 import learner, policy
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter
from experiments.candidates.scdmp_variable_k.native_hold_residual_b01 import study, learner as residual_learner
from experiments.candidates.scdmp_variable_k.native_hold_residual_b01.learner import R_COLUMNS

def models(common, arm):
    return policy.arm_copy(common, True)


def rows_for(delta=.02):
    return [dict(arm=a, phase="eval", episode=e, reset_seed=2000+e,
                 J=(delta if a == "RESIDUAL-MC" else 0.) + e*.125)
            for a in (*study.ARMS, "H") for e in range(2)]


@pytest.mark.parametrize("delta,reading", [(.02,"UP"),(-.02,"DOWN"),(0.,"WITHIN")])
def test_primary_identity_arithmetic_and_negative(delta, reading):
    rows = rows_for(delta)
    result = study.primary_from_rows(list(reversed(rows)), 2, 2000)
    assert result["complete"] and result["reading"] == reading
    assert result["RESIDUAL-MC_minus_MLP-MC"]["mean"] == pytest.approx(delta)
    for x,y,z in zip(result["RESIDUAL-MC_minus_H"]["differences"], result["MLP-MC_minus_H"]["differences"], result["RESIDUAL-MC_minus_MLP-MC"]["differences"]):
        assert x-y == pytest.approx(z)
    rows[1]["J"] += .125
    result = study.primary_from_rows(rows, 2, 2000)
    assert result["RESIDUAL-MC_minus_MLP-MC"]["conditional_se"] == pytest.approx(.0625)


@pytest.mark.parametrize("delta", [-.01, .01])
def test_inclusive_mei_endpoints(delta):
    rows = rows_for(0)
    for r in rows:
        r["J"] = delta if r["arm"] == "RESIDUAL-MC" else 0
    assert study.primary_from_rows(rows, 2, 2000)["reading"] == "WITHIN"


def test_missing_primary_and_h_and_bad_identity():
    rows = rows_for()
    result = study.primary_from_rows(rows[:-2], 2, 2000)
    assert result["complete"] and not result["hover_complete"]
    assert result["RESIDUAL-MC_minus_H"]["mean"] is None
    for damaged in (rows[1:], rows+[rows[0]], [dict(r, reset_seed=9) if i==0 else r for i,r in enumerate(rows)]):
        result = study.primary_from_rows(damaged, 2, 2000)
        assert not result["complete"] and result["reading"] is None
        assert result["RESIDUAL-MC_minus_MLP-MC"]["mean"] is None


def test_scripted_predecision_hold_collector(monkeypatch):
    actor, critic = models(policy.templates(9001), "RESIDUAL-MC")
    def scripted(actor, mean, recurrent, active, opening, *rng):
        return torch.ones_like(mean)*.1, torch.ones(5,dtype=torch.long)
    monkeypatch.setattr(learner, "sample", scripted)
    counts = study.new_counts()
    rows = []
    data = learner.collect_episode(SyntheticAdapter(1), actor, critic, 8, 2,
        policy.generator(3), policy.generator(4), dict(arm="RESIDUAL-MC", phase="train", episode=0),
        lambda: None, counts, rows.append, lambda r: None, [], ratio_grouping="agent_compound")
    torch.testing.assert_close(data["critic"][:5, R_COLUMNS], torch.tensor([0,.75,.5,.25,0])[:,None].expand(5,5))
    assert data["logp"].shape == (8,5)
    assert not data["velocity_mask"][1:4].any()
    assert data["velocity_mask"][[0,4,5,6,7]].all()
    assert data["duration_mask"][0].all() and not data["duration_mask"][1:].any()
    assert not torch.equal(data["hidden"][1], data["hidden"][2])
    assert data["reward"].shape == (8,) and counts["recurrent_observations"] == 40
    assert rows[0]["reward_sum"] == pytest.approx(float(data["reward"].sum()))


def install_stubs(monkeypatch, time_state=None, fail_h=False, partial=False):
    calls, fits = [], []
    def collect(env, actor, critic, horizon, reset_seed, vrng, drng, metadata,
                check, counts, emit, diagnostic, limits, **kwargs):
        assert kwargs == dict(real=False, diagnostics=False, ratio_grouping="agent_compound")
        check()
        phase, arm = metadata["phase"], metadata["arm"]
        if arm == "H" and time_state is not None:
            time_state[0] = 1801
            check()
        if arm == "H" and fail_h:
            counts["step_calls"] += 1
            raise RuntimeError("synthetic H failure")
        if partial and phase == "train":
            counts["team_steps"] += 1
            counts["train_team_steps"] += 1
            counts["step_calls"] += 1
            raise RuntimeError("partial synthetic episode")
        if actor is not None:
            assert actor.duration is not None
            if phase == "eval":
                assert any(a is actor for a in fits)
        else:
            assert arm == "H" and critic is None
        calls.append((arm,phase,metadata["episode"],reset_seed,
                      vrng.initial_seed() if vrng else None, drng.initial_seed() if drng else None, env, vrng, drng))
        counts["explicit_resets"] += 1
        counts["step_calls"] += horizon
        counts["team_steps"] += horizon
        counts[phase+"_team_steps"] += horizon
        counts[phase+"_episodes"] += 1
        counts["completed_episode_steps"] += horizon
        if actor is not None:
            counts["duration_decisions"] += 5
        emit(dict(metadata, reset_seed=reset_seed, J=.1 if arm=="RESIDUAL-MC" else .2, steps=horizon))
        return {"critic": torch.zeros(horizon,136)}
    def update(actor, critic, optimizer, episodes, chunk, check, counts, **kwargs):
        assert kwargs == dict(ratio_grouping="agent_compound", residual=len(fits)==0)
        assert len(episodes)==2 and chunk==8
        counts["optimizer_steps"] += 4
        fits.append(actor)
        return [dict(epoch=e, loss=0.) for e in range(4)]
    monkeypatch.setattr(learner, "collect_episode", collect)
    monkeypatch.setattr(residual_learner, "update", update)
    return calls


@pytest.mark.parametrize("use_b02", [False, True])
def test_study_plumbing_counts_seeds_final_only_and_readback(monkeypatch,tmp_path,use_b02):
    calls = install_stubs(monkeypatch)
    constructors=[]
    def factory(seed):
        env=object();constructors.append((seed,env));return env
    identity = dict(object_name="SCDMP-NATIVE-HOLD-RESIDUAL-B02",
                    card_path=study.CARD.replace("B01_SCIENCE_CARD_20260909", "B02_SCIENCE_CARD_20260910")) if use_b02 else {}
    result = study.run_pair(study.Config.engineering(), tmp_path, 0, clock=lambda:0, factory=factory, **identity)
    assert result["status"] == "COMPLETE" and result["publication_readback"] == "complete"
    assert result["object"] == identity.get("object_name", study.OBJECT)
    assert result["card"] == identity.get("card_path", study.CARD)
    assert study.checkpoint_identity(study.Config(), study.ARMS[0], "unused")["object"] == "SCDMP-NATIVE-HOLD-RESIDUAL-B01"
    assert result["counts"]["team_steps"]==80 and result["counts"]["optimizer_steps"]==8
    assert result["counts"]["eval_episodes"]==6 and result["counts"]["constructor_resets"]==2
    assert result["primary"]["reading"]=="DOWN"
    assert [x[0] for x in constructors]==[900101000]*2
    assert calls[-1][6] is constructors[1][1]
    for arm, phase, e, reset, vrng, drng, *_ in calls:
        assert reset==900100000+(1000 if phase=="train" else 2000)+e
        assert vrng==(None if arm=="H" else 900100021 if phase=="train" else 900103000+e)
        assert drng==(None if arm=="H" else 900100022 if phase=="train" else 900104000+e)
    assert calls[0][7] is calls[1][7] and calls[0][7] is not calls[4][7]
    loaded=json.loads((tmp_path/"summary.json").read_text())
    assert loaded["primary"]==result["primary"]
    assert (loaded["object"], loaded["card"]) == (result["object"], result["card"])
    assert len((tmp_path/"episodes.jsonl").read_text().splitlines())==10
    for arm in study.ARMS:
        saved=torch.load(tmp_path/f"final_{arm}.pt",weights_only=True)
        assert saved["algorithm"]==arm and saved["seed"]==9001
        assert saved["object"]==result["object"]
        assert saved["ratio_grouping"]=="agent_compound"
        assert "duration.weight" in saved["actor"]


@pytest.mark.parametrize("failure", ["H","partial","publication"])
def test_failure_preserves_available_rows(monkeypatch,tmp_path,failure):
    install_stubs(monkeypatch,fail_h=failure=="H",partial=failure=="partial")
    def publish(path,summary):
        if failure=="publication":
            raise OSError("synthetic publication fault")
        study.write_summary(path,summary)
    result=study.run_pair(study.Config.engineering(),tmp_path,0,clock=lambda:0,factory=lambda s:object(),publish=publish)
    assert result["primary"]["complete"] == (failure!="partial")
    assert json.loads((tmp_path/"summary.json").read_text())["primary"]==result["primary"]
    if failure=="partial":
        assert result["counts"]["partial_episode_steps"]==1
        assert not result["arms"]["RESIDUAL-MC"]["fit_complete"]
    elif failure=="H":
        assert result["status"]=="PRIMARY_COMPLETE_WITH_LIMITS"
    else:
        assert result["status"]=="PUBLICATION_FAILED"


def test_continuous_deadline_and_late_publication(monkeypatch,tmp_path):
    t=[0.]
    deadline=study.Deadline(0,10,18,lambda:t[0])
    t[0]=9;deadline.next_arm()
    t[0]=18;deadline.check()
    t[0]=18.1
    with pytest.raises(TimeoutError):deadline.check()
    deadline=study.Deadline(0,10,20,lambda:11)
    with pytest.raises(TimeoutError):deadline.next_arm()
    assert deadline.arm=="RESIDUAL-MC"
    install_stubs(monkeypatch)
    t[0]=0
    def publish(path,summary):
        study.write_summary(path,summary);t[0]=1801
    result=study.run_pair(study.Config.engineering(),tmp_path,0,clock=lambda:t[0],factory=lambda s:object(),publish=publish)
    assert result["status"]=="CAP_BREACH" and result["primary"]["complete"]
    assert result["mlp_start_pair_elapsed"]==0
    assert result["complete_exit_cap_conformance"].startswith("unmeasured:")
    assert result["arms"]["MLP-MC"]["elapsed_wall"]==1801
    assert json.loads((tmp_path/"summary.json").read_text())["cap_breach"]
    t[0]=0
    install_stubs(monkeypatch,time_state=t)
    result=study.run_pair(study.Config.engineering(),tmp_path/"h_overrun",0,
                          clock=lambda:t[0],factory=lambda s:object())
    assert result["status"]=="CAP_BREACH" and result["primary"]["complete"]
    assert not result["primary"]["hover_complete"]
    assert result["mlp_start_pair_elapsed"]==0
    assert result["complete_exit_cap_conformance"].startswith("unmeasured:")
    assert result["arms"]["MLP-MC"]["elapsed_wall"]==1801
    assert result["arms"]["MLP-MC"]["hover_counts"]["team_steps"]==0


def test_cli_fixed_configuration_without_running_fixture(monkeypatch,tmp_path):
    path=Path(__file__).resolve().parents[5]/"scripts/run_scdmp_native_hold_residual_b01.py"
    spec=importlib.util.spec_from_file_location("vspc1_cli",path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    monkeypatch.setattr(torch,"set_num_threads",lambda n:None)
    monkeypatch.setattr(torch,"set_num_interop_threads",lambda n:None)
    captured=[]
    def fake(config,out,start):
        captured.append(config);return dict(mode="fixture",status="COMPLETE")
    monkeypatch.setattr(study,"run_pair",fake)
    assert module.main(["--engineering-fixture","--seed","9001","--out",str(tmp_path)])==0
    assert captured[-1]==study.Config.engineering()
    assert module.main(["--seed","8201","--out",str(tmp_path)])==0
    assert captured[-1]==study.Config()
    with pytest.raises(SystemExit):module.main(["--seed","9001","--out",str(tmp_path)])


def test_b02_cli_fixed_master_and_identity_without_training(monkeypatch,tmp_path):
    path=Path(__file__).resolve().parents[5]/"scripts/run_scdmp_native_hold_residual_b02.py"
    spec=importlib.util.spec_from_file_location("scdmp_b02_cli",path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    monkeypatch.setattr(torch,"set_num_threads",lambda n:None)
    monkeypatch.setattr(torch,"set_num_interop_threads",lambda n:None)
    captured=[]
    def fake(config,out,start,**identity):
        captured.append((config,identity));return dict(mode="UAV_B_EXPLORE",status="COMPLETE")
    monkeypatch.setattr(study,"run_pair",fake)
    assert module.main(["--seed","8202","--out",str(tmp_path)])==0
    assert captured == [(study.Config(seed=8202), dict(object_name=module.OBJECT, card_path=module.CARD))]
    assert module.OBJECT == "SCDMP-NATIVE-HOLD-RESIDUAL-B02"
    assert module.CARD.endswith("SCDMP_NATIVE_HOLD_RESIDUAL_B02_SCIENCE_CARD_20260910.md")
    with pytest.raises(SystemExit):module.main(["--seed","8201","--out",str(tmp_path)])
    assert len(captured)==1
