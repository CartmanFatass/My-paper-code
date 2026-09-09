"""Continuous fits and curve publication using synthetic master9001 only."""
import copy
import importlib.util
import json
import math
import statistics
import sys
import time

import pytest
import torch

from experiments.candidates.ucope.uav_short_fixed_renewal_continuous_b01 import study
from experiments.candidates.ucope.uav_motion_prefix_b01 import learner, policy
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter


def equal_tree(a, b):
    if isinstance(a, torch.Tensor):
        assert torch.equal(a, b)
    elif isinstance(a, dict):
        assert a.keys() == b.keys()
        for k in a: equal_tree(a[k], b[k])
    elif isinstance(a, (tuple, list)):
        assert len(a) == len(b)
        for x, y in zip(a, b): equal_tree(x, y)
    else:
        assert a == b


def test_continuous_fit_rng_optimizer_and_publication(tmp_path, monkeypatch):
    torch.set_num_threads(1)
    calls, fits, events = [], {}, []
    collect, update, make_optimizer = learner.collect_episode, learner.update, learner.optimizer_for
    def optimizer(actor, critic):
        arm = "F" if actor.duration is not None else "G"
        opt = make_optimizer(actor, critic)
        fits[arm] = dict(actor=actor, critic=critic, optimizer=opt, updates=0,
                         initial=copy.deepcopy(actor.state_dict()))
        if arm == "F":
            assert sum(p.numel() for p in actor.duration.parameters()) == 2242
            assert all(not p.requires_grad for p in actor.duration.parameters())
            assert actor.duration[0].weight.count_nonzero() > 0
            assert actor.duration[2].weight.count_nonzero() == actor.duration[2].bias.count_nonzero() == 0
        return opt
    def collection(*args, **kwargs):
        env, actor, critic, horizon, reset, velocity, duration, meta = args[:8]
        arm = meta["arm"]
        assert kwargs["value_moments"] is None and kwargs["renewal"]
        assert kwargs["duration_support"] == (1, 2) and kwargs["ratio_grouping"] == "agent_compound"
        assert "velocity_mode" not in kwargs
        assert reset == 900100000+(10000 if meta["phase"] == "train" else 20000)+meta["episode"]
        calls.append((meta.copy(), reset, velocity, duration, env))
        events.append((arm, meta["phase"], meta["episode"], meta["checkpoint"]))
        if arm == "H":
            assert actor is critic is velocity is duration is None
            return collect(*args, **kwargs)
        fit = fits[arm]
        assert actor is fit["actor"] and critic is fit["critic"]
        if meta["phase"] == "train":
            if "velocity" in fit:
                assert velocity is fit["velocity"] and duration is fit["duration"]
            fit.update(velocity=velocity, duration=duration)
            return collect(*args, **kwargs)
        assert fit["updates"] == meta["checkpoint"] // 2
        before = copy.deepcopy((actor.state_dict(), critic.state_dict(), fit["optimizer"].state_dict(),
                                fit["velocity"].get_state(), fit["duration"].get_state(), torch.get_rng_state()))
        result = collect(*args, **kwargs)
        equal_tree(before, (actor.state_dict(), critic.state_dict(), fit["optimizer"].state_dict(),
                           fit["velocity"].get_state(), fit["duration"].get_state(), torch.get_rng_state()))
        return result
    def updating(*args, **kwargs):
        actor, critic, opt = args[:3]
        arm = "F" if actor.duration is not None else "G"
        fit = fits[arm]
        assert opt is fit["optimizer"] and actor is fit["actor"] and critic is fit["critic"]
        assert kwargs == dict(ratio_grouping="agent_compound", entropy_coef=0., value_moments=None)
        result = update(*args, **kwargs)
        fit["updates"] += 1
        assert {int(v["step"]) for v in opt.state.values()} == {4*fit["updates"]}
        if arm == "F":
            for key, value in actor.state_dict().items():
                if key.startswith("duration."): assert torch.equal(value, fit["initial"][key])
        return result
    monkeypatch.setattr(learner, "optimizer_for", optimizer)
    monkeypatch.setattr(learner, "collect_episode", collection)
    monkeypatch.setattr(learner, "update", updating)
    result = study.run_pair(study.Config.engineering(), tmp_path, time.monotonic())
    assert result["status"] == "COMPLETE", result["limits"]
    assert result["scientific_uav_calls"] == 0
    assert result["counts"]["team_steps"] == 208 and result["counts"]["optimizer_steps"] == 24
    assert result["counts"]["explicit_resets"] == 26 and result["counts"]["constructors"] == result["counts"]["constructor_resets"] == 2
    assert result["counts"]["d4"] == 0 and result["counts"]["d2"] > 0
    assert len({id(c[4]) for c in calls}) == 2
    expected = []
    for arm in ("F", "G"):
        for j, c in enumerate((2,4,6)):
            expected += [(arm,"train",e,None) for e in range(c-2,c)]
            expected += [(arm,"eval",e,c) for e in range(2)]
    expected += [("H","eval",e,None) for e in range(2)]
    assert events == expected
    for arm, offset in (("F",30),("G",20)):
        train = [c for c in calls if c[0]["arm"] == arm and c[0]["phase"] == "train"]
        assert train[0][2].initial_seed() == 900100000+offset+1
        assert train[0][3].initial_seed() == 900100000+offset+2
        ev = [c for c in calls if c[0]["arm"] == arm and c[0]["phase"] == "eval"]
        for j in range(3):
            for e in range(2):
                c = ev[2*j+e]
                assert c[2].initial_seed() == 900100000+(30000 if arm == "F" else 50000)+1000*j+e
                assert c[3].initial_seed() == 900100000+(40000 if arm == "F" else 60000)+1000*j+e
        assert result["arms"][arm]["trainable_parameters"] == 66311
        for point in result["arms"][arm]["checkpoints"].values():
            assert all(x["displacement"] == 0 for x in point["evaluation_parameter_exposure"].values())
        saved = torch.load(tmp_path/f"final_{arm}.pt", weights_only=True)
        assert saved["value_moments"] is None
        equal_tree(saved["actor"], fits[arm]["actor"].state_dict())
    rows = [json.loads(line) for line in (tmp_path/"episodes.jsonl").read_text().splitlines()]
    assert all(r["J"] == r["reward_sum"]/8 for r in rows)
    assert len([r for r in rows if r["arm"] == "H"]) == 2
    assert result["primary"] == result["curve"][-1] and result["primary"]["checkpoint"] == 6
    assert all(p["J"]["H"] == result["curve"][0]["J"]["H"] for p in result["curve"])
    assert json.loads((tmp_path/"summary.json").read_text())["curve"] == result["curve"]


def rows_for_curve():
    return [dict(arm=a, phase="eval", episode=e, checkpoint=c, J=x)
            for c in (512,1024,2048) for a, values in
            {"F": ([3.,2.,1.] if c < 2048 else [-1.,0.,1.]), "G": [0.,0.,0.]}.items()
            for e,x in enumerate(values)] + [dict(arm="H", phase="eval", episode=e, checkpoint=None, J=2.) for e in range(3)]


@pytest.mark.parametrize("missing", [None, "H", "F_512", "F_2048"])
def test_curve_identity_partial_and_final_primary(missing):
    rows = [r for r in rows_for_curve() if not (missing == "H" and r["arm"] == "H")
            and not (missing in ("F_512","F_2048") and r["arm"] == "F" and r["checkpoint"] == int(missing[2:]))]
    curve = [study.panel_from_rows(rows, 3, c) for c in (512,1024,2048)]
    assert curve[-1]["complete"] == (missing != "F_2048")
    assert all(p["all_outcomes_complete"] for p in curve) == (missing is None)
    if curve[-1]["complete"]:
        assert curve[-1]["reading"] == "WITHIN" and curve[-1]["F_minus_G"]["differences"] == [-1.,0.,1.]
        assert curve[-1]["F_minus_G"]["conditional_se"] == statistics.stdev([-1.,0.,1.])/math.sqrt(3)
        assert all(curve[-1]["F_minus_G"][key] == 1 for key in ("positive","negative","zero"))
    else:
        assert curve[-1]["reading"] is None and curve[0]["reading"] == "UP"


@pytest.mark.parametrize("delta,reading", [(.0100001,"UP"),(.01,"WITHIN"),(-.01,"WITHIN"),(-.0100001,"DOWN")])
def test_mei(delta, reading):
    rows = [dict(phase="eval", arm=a, checkpoint=2048, episode=0, J=x) for a,x in (("F",delta),("G",0.))]
    p = study.panel_from_rows(rows, 1, 2048)
    assert p["reading"] == reading and p["distance_to_lower"] == delta+.01 and p["distance_to_upper"] == delta-.01


def test_failure_after_first_panel_does_not_rescue_primary(tmp_path, monkeypatch):
    original = learner.collect_episode
    def collect(*args, **kwargs):
        if args[7]["phase"] == "train" and args[7]["episode"] == 2:
            raise RuntimeError("fixture stop after first panel")
        return original(*args, **kwargs)
    monkeypatch.setattr(learner,"collect_episode",collect)
    result = study.run_pair(study.Config.engineering(), tmp_path, time.monotonic())
    assert result["status"] == "INCOMPLETE" and not result["primary"]["complete"]
    assert result["curve"][0]["J"]["F"] and result["curve"][-1]["J"]["F"] == []
    assert result["counts"]["train_episodes"] == result["counts"]["eval_episodes"] == 2
    assert not result["arms"]["F"]["fit_complete"]


def test_cli_and_real_seed_domains_without_scientific_rng(tmp_path, monkeypatch):
    c = study.Config()
    assert (c.seed,c.horizon,c.train_episodes,c.checkpoints,c.eval_episodes) == (8601,256,2048,(512,1024,2048),64)
    b = c.seed*100000
    domains = [set(range(b+10000,b+10000+2048)),set(range(b+20000,b+20000+64))]
    domains += [set(range(b+offset+1000*j,b+offset+1000*j+64)) for offset in (30000,40000,50000,60000) for j in range(3)]
    assert sum(map(len,domains)) == len(set.union(*domains))
    spec=importlib.util.spec_from_file_location("continuous_runner","scripts/run_ucope_uav_short_fixed_renewal_continuous_b01.py")
    runner=importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    monkeypatch.setattr(torch,"set_num_interop_threads",lambda n:None)
    seen=[]
    monkeypatch.setattr(runner,"run_pair",lambda c,*args:seen.append(c) or dict(mode="stub",status="COMPLETE",primary={},counts={}))
    for seed, fixture in ((8601,False),(9001,True)):
        monkeypatch.setattr(sys,"argv",["runner","--seed",str(seed),"--out",str(tmp_path)]+(["--engineering-fixture"] if fixture else []))
        assert runner.main() == 0 and seen[-1].fixture == fixture
    monkeypatch.setattr(sys,"argv",["runner","--seed","8501","--out",str(tmp_path)])
    with pytest.raises(SystemExit): runner.main()
    assert len(seen) == 2


@pytest.mark.parametrize("failure_arm", ["F", "H"])
def test_final_evaluation_failure_preserves_fit_and_primary(tmp_path, monkeypatch, failure_arm):
    original = learner.collect_episode
    def collect(*args, **kwargs):
        meta = args[7]
        if meta["arm"] == failure_arm and meta["phase"] == "eval" and (failure_arm == "H" or meta["checkpoint"] == 6):
            raise RuntimeError("fixture final evaluation failure")
        return original(*args, **kwargs)
    monkeypatch.setattr(learner,"collect_episode",collect)
    result = study.run_pair(study.Config.engineering(), tmp_path, time.monotonic())
    assert result["arms"]["F"]["fit_complete"] and (tmp_path/"final_F.pt").exists()
    assert result["arms"]["F"]["counts"]["optimizer_steps"] == 12
    assert result["primary"]["complete"] == (failure_arm == "H")
    assert result["status"] == ("PRIMARY_COMPLETE_WITH_LIMITS" if failure_arm == "H" else "INCOMPLETE")
    assert not result["all_panels_complete"] and not result["primary"]["hover_complete"]
