"""Deterministic units, private fit wiring and partial publication; no native calls."""
import importlib.util
import json
import sys
import time

import pytest
import torch

from experiments.candidates.ucope.uav_feedback_value_normalization_b01 import study
from experiments.candidates.ucope.uav_feedback_value_normalization_b01.value_normalization import ValueMoments
from experiments.candidates.ucope.uav_motion_prefix_b01 import learner, policy
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter


def test_population_moments_reference_order_floor_and_detachment():
    m = ValueMoments()
    assert m.n == m.updates == 0 and m.scale == 1
    batches = [torch.tensor([1., 2., 5., 8.], requires_grad=True), torch.tensor([-3., 9.])]
    first = batches[0].detach()
    mean, M2 = first.mean(), (first-first.mean()).square().sum()
    m.update(batches[0])
    assert torch.equal(m.mean, mean) and torch.equal(m.M2, M2)
    second = batches[1]
    delta = second.mean()-mean
    expected_mean = mean+delta*2/6
    expected_M2 = M2+(second-second.mean()).square().sum()+delta*delta*4*2/6
    m.update(second)
    assert m.n == 6 and m.updates == 2
    assert torch.equal(m.mean, expected_mean) and torch.equal(m.M2, expected_M2)
    assert m.mean.dtype == m.M2.dtype == torch.float32 and m.mean.device.type == "cpu"
    assert not m.mean.requires_grad and not m.normalize(batches[0]).requires_grad
    assert torch.equal(m.scale, (expected_M2/6).clamp_min(1e-8).sqrt())
    constant = ValueMoments(); constant.update(torch.ones(4))
    assert torch.equal(constant.scale, torch.tensor(1e-8, dtype=torch.float32).sqrt())
    checkpoint = m.checkpoint()
    assert set(checkpoint) == {"n", "updates", "mean", "M2"}
    m.mean.add_(1)
    assert torch.equal(checkpoint["mean"], expected_mean)


def test_shared_update_raw_advantages_then_one_merge_four_frozen_epochs(monkeypatch):
    torch.set_num_threads(1)
    actor, critic = policy.arm_copy(policy.templates(9001), False)
    moments = ValueMoments(); moments.update(torch.tensor([10., 14.]))
    counts = study.new_counts()
    episodes = [learner.collect_episode(SyntheticAdapter(9001, 8), actor, critic, 8, 900101000+e,
        policy.generator(21+e), policy.generator(31+e), dict(arm="G_normalized", phase="train", episode=e),
        lambda: None, counts, lambda row: None, lambda row: None, [],
        ratio_grouping="agent_compound", value_moments=moments) for e in range(2)]
    for ep in episodes:
        assert torch.allclose(ep["value"], moments.decode(critic(ep["critic"]).detach()))
    targets = learner.returns_to_go(torch.stack([e["reward"] for e in episodes]))
    stored = torch.stack([e["value"] for e in episodes])
    raw = targets-stored
    expected_advantage = (raw-raw.mean())/(raw.std(unbiased=False)+1e-8)
    expected_moments = ValueMoments(); expected_moments.update(torch.tensor([10., 14.])); expected_moments.update(targets)
    expected_target = expected_moments.normalize(targets)
    seen, frozen = [], []
    original_loss = learner.clipped_policy_loss
    def loss(new, old, advantage, mask):
        assert not advantage.requires_grad and torch.equal(advantage, expected_advantage)
        assert moments.n == 18 and moments.updates == 2
        frozen.append(moments.state())
        return original_loss(new, old, advantage, mask)
    monkeypatch.setattr(learner, "clipped_policy_loss", loss)
    handle = critic.register_forward_hook(lambda module, args, value: seen.append(value.detach().clone()))
    records = learner.update(actor, critic, learner.optimizer_for(actor, critic), episodes, 8,
        lambda: None, counts, ratio_grouping="agent_compound", entropy_coef=0., value_moments=moments)
    handle.remove()
    assert len(records) == len(seen) == 4 and all(x == frozen[0] for x in frozen)
    for prediction, record in zip(seen, records):
        assert record["value_loss"] == float((prediction-expected_target).square().mean())
        assert record["value_loss_units"] == "normalized_squared"
    assert counts["optimizer_steps"] == 4 and torch.equal(stored, torch.stack([e["value"] for e in episodes]))


def test_driver_private_streams_checkpoints_and_frozen_evaluation(tmp_path, monkeypatch):
    torch.set_num_threads(1)
    calls, updates = [], []
    original_collect, original_update = learner.collect_episode, learner.update
    def collect(*args, **kwargs):
        calls.append((args[7].copy(), args[4], args[5], args[6], kwargs["value_moments"]))
        assert args[1] is None or args[1].duration is None
        assert "velocity_mode" not in kwargs and kwargs["ratio_grouping"] == "agent_compound"
        return original_collect(*args, **kwargs)
    def update(*args, **kwargs):
        updates.append(kwargs.copy())
        return original_update(*args, **kwargs)
    monkeypatch.setattr(learner, "collect_episode", collect)
    monkeypatch.setattr(learner, "update", update)
    result = study.run_pair(study.Config.engineering(), tmp_path, time.monotonic())
    assert result["status"] == "COMPLETE" and result["scientific_uav_calls"] == 0
    assert result["counts"]["team_steps"] == 80 and result["counts"]["optimizer_steps"] == 8
    assert result["counts"]["duration_decisions"] == 0
    assert [x[0]["arm"] for x in calls] == [a for a in ("G_normalized", "G_normalized", "G_raw", "G_raw", "H") for _ in range(2)]
    for arm, offset in (("G_normalized", 30), ("G_raw", 20)):
        train = [x for x in calls if x[0]["arm"] == arm and x[0]["phase"] == "train"]
        assert train[0][2] is train[1][2] and train[0][2].initial_seed() == 900100000+offset+1
        assert train[0][3].initial_seed() == 900100000+offset+2
        ev = [x for x in calls if x[0]["arm"] == arm and x[0]["phase"] == "eval"]
        assert ev[0][2] is not ev[1][2]
        assert [x[2].initial_seed() for x in ev] == [900100000+(5000 if offset==30 else 3000)+e for e in range(2)]
        info = result["arms"][arm]
        assert info["trainable_parameters"] == 66311
        assert info["value_moments"] == info["evaluation_value_moments"]
        assert all(x["displacement"] == 0 for x in info["evaluation_parameter_exposure"].values())
        ck = torch.load(tmp_path/f"final_{arm}.pt", weights_only=True)
        assert not any(k.startswith("duration") for k in ck["actor"])
        if offset == 30:
            assert ck["value_moments"]["n"] == 16 and ck["value_moments"]["updates"] == 1
            assert ck["value_moments"]["mean"].dtype == torch.float32
        else:
            assert ck["value_moments"] is None and all(x[4] is None for x in train+ev)
    assert updates[0]["value_moments"] is not None and updates[1]["value_moments"] is None
    assert all(x["entropy_coef"] == 0 and x["ratio_grouping"] == "agent_compound" for x in updates)
    assert all(x[1] == 900100000+(1000 if x[0]["phase"]=="train" else 2000)+x[0]["episode"] for x in calls)
    assert all(x[2] is x[3] is None for x in calls if x[0]["arm"] == "H")
    rows = [json.loads(line) for line in (tmp_path/"episodes.jsonl").read_text().splitlines()]
    assert all(x["J"] == x["reward_sum"]/8 for x in rows)
    assert json.loads((tmp_path/"summary.json").read_text())["primary"] == result["primary"]


@pytest.mark.parametrize("missing", [None, "H", "G_raw", "G_normalized"])
def test_primary_partial_sign_counts_and_rule(missing):
    rows = [dict(arm=a, phase="eval", episode=i, J=x) for a, values in
            {"G_normalized": [1., 2., 3.], "G_raw": [0., 2., 4.], "H": [0., 0., 0.]}.items()
            if a != missing for i,x in enumerate(values)]
    result = study.primary_from_rows(rows, 3)
    assert result["complete"] == (missing in (None, "H"))
    assert result["all_outcomes_complete"] == (missing is None)
    if result["complete"]:
        pair = result["G_normalized_minus_G_raw"]
        assert pair["differences"] == [1., 0., -1.]
        assert pair["positive"] == pair["zero"] == pair["negative"] == 1
        assert result["reading"] == "WITHIN"
    else:
        assert result["reading"] is None


@pytest.mark.parametrize("delta,reading", [(.0100001,"UP"),(.01,"WITHIN"),(-.01,"WITHIN"),(-.0100001,"DOWN")])
def test_boundaries(delta, reading):
    rows = [dict(arm=a, phase="eval", episode=0, J=v) for a,v in (("G_normalized",delta),("G_raw",0.),("H",0.))]
    assert study.primary_from_rows(rows, 1)["reading"] == reading


def test_cli_checks_master_before_workload(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("normalization_runner", "scripts/run_ucope_uav_feedback_value_normalization_b01.py")
    runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda n: None)
    seen = []
    monkeypatch.setattr(runner, "run_pair", lambda c,*a: seen.append(c) or dict(mode="stub", status="COMPLETE", primary={}, counts={}))
    for seed,fixture in ((8501,False),(9001,True)):
        monkeypatch.setattr(sys,"argv",["runner","--seed",str(seed),"--out",str(tmp_path)]+(["--engineering-fixture"] if fixture else []))
        assert runner.main() == 0 and seen[-1].fixture == fixture
    monkeypatch.setattr(sys,"argv",["runner","--seed","8401","--out",str(tmp_path)])
    with pytest.raises(SystemExit): runner.main()
    assert len(seen) == 2


def test_failure_publishes_actual_partial_counts(tmp_path):
    class Broken(SyntheticAdapter):
        def step(self, action):
            raise RuntimeError("fixture failure")
    result = study.run_pair(study.Config.engineering(), tmp_path, time.monotonic(), factory=lambda seed: Broken(seed,8))
    assert result["status"] == "INCOMPLETE" and not result["primary"]["complete"]
    assert result["counts"]["step_calls"] == 1 and result["counts"]["team_steps"] == 0
    assert result["primary"]["J"] == {a:[] for a in study.LABELS}
    assert "fixture failure" in result["limits"][0]
