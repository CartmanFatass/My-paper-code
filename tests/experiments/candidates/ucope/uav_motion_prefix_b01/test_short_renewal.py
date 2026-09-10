"""P82 physical support, selected-label credit and literal action accounting."""
import json
import time

import numpy as np
import pytest
import torch

from experiments.candidates.ucope.uav_motion_prefix_b01 import learner, policy, study
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter


def scripted_labels(monkeypatch, choose):
    original = learner.sample
    step = [0]
    choices = []
    monkeypatch.setattr(torch, "multinomial", lambda *a, **k: torch.tensor([choices.pop(0)]))

    def sample(actor, mean, recurrent, active, opening, vrng, drng, duration_mask):
        choices.extend(choose(step[0], i) for i in range(5) if duration_mask[i])
        result = original(actor, mean, recurrent, active, opening, vrng, drng,
                          duration_mask=duration_mask)
        assert not choices
        step[0] += 1
        return result

    monkeypatch.setattr(learner, "sample", sample)


@pytest.mark.parametrize("short", [False, True])
def test_support_expiry_features_selected_label_density_and_credit(monkeypatch, short):
    actor, critic = policy.arm_copy(policy.templates(9001), True,
                                    duration_head_seed=900100012, freeze_duration=True)
    scripted_labels(monkeypatch, lambda t, i: int(t != 0 or i % 2 == 0))
    env = SyntheticAdapter(9001, 5)
    commands = []
    original_step = env.step

    def step(sent):
        commands.append(sent.copy())
        return original_step(sent)

    monkeypatch.setattr(env, "step", step)
    counts, rows, frames = study.new_counts(True, short=short), [], []
    options = {"duration_support": (1, 2)} if short else {}
    ep = learner.collect_episode(env, actor, critic, 5, 900100001,
                                 policy.generator(22), policy.generator(23),
                                 dict(arm="F", phase="train", episode=0), lambda: None,
                                 counts, rows.append, frames.append, [], diagnostics=True,
                                 ratio_grouping="agent_compound", renewal=True, **options)
    expected = torch.tensor([[1]*5, [0,1,0,1,0], [1,0,1,0,1] if short else [0]*5,
                             [0,1,0,1,0] if short else [0]*5, [1,0,1,0,1]], dtype=torch.bool)
    assert torch.equal(ep["velocity_mask"], expected) and torch.equal(ep["duration_mask"], expected)
    assert not ep["logp"][~expected].any()
    assert ep["durations"][4, [0,2,4]].tolist() == [1,1,1]  # Censored labels stay 1.
    assert counts["recurrent_observations"] == 25
    assert counts["duration_decisions"] == counts["velocity_decisions"] == (15 if short else 10)
    assert counts["suppressed_decisions"] == (10 if short else 15)
    assert counts["horizon_censored_holds"] == 3
    assert counts["d4"] == (0 if short else 8)
    if short:
        assert counts["d2"] == 13
    else:
        assert "d2" not in counts and "d2" not in rows[0]
    for key in ("duration_decisions", "d4", "suppressed_decisions", "horizon_censored_holds") + (("d2",) if short else ()):
        assert rows[0][key] == counts[key] == counts["train_" + key]
        assert counts["eval_" + key] == 0
    for frame in frames:
        t, i = frame["time"], int(frame["agent"][-1])
        assert frame["actual_decision"] == bool(expected[t, i])
        chosen = (1 + (1 if short else 3) * int(ep["durations"][t, i])) if expected[t, i] else None
        assert frame["chosen_duration"] == chosen
        assert ep["obs"][t, i, -1] == frame["remaining_hold"] / 4
        assert ep["critic"][t, -20:].reshape(5, 4)[i, -1] == frame["remaining_hold"] / 4
        if not expected[t, i]:
            np.testing.assert_array_equal(commands[t][i], commands[t-1][i])
    batch = {k: v[None] for k, v in ep.items()}
    mean, rec = learner.recurrent_outputs(actor, batch, 5)
    lp, _ = policy.joint_terms(actor, mean, rec, batch["u"], batch["durations"],
                               batch["velocity_mask"], batch["duration_mask"], "agent_compound")
    torch.testing.assert_close(lp[0], ep["logp"], rtol=1e-5, atol=1e-6)
    seen = []
    original_terms = learner.joint_terms

    def terms(*args):
        seen.append(tuple(v.clone() for v in args[4:7]))
        return original_terms(*args)

    monkeypatch.setattr(learner, "joint_terms", terms)
    learner.update(actor, critic, learner.optimizer_for(actor, critic), [ep, ep], 5,
                   lambda: None, counts, ratio_grouping="agent_compound", entropy_coef=0.)
    assert counts["optimizer_steps"] == len(seen) == 4
    for labels, vm, dm in seen:
        for actual, key in [(labels, "durations"), (vm, "velocity_mask"), (dm, "duration_mask")]:
            assert torch.equal(actual, torch.stack([ep[key], ep[key]]))


@pytest.mark.parametrize("fail_last", [False, True])
def test_short_final_selection_and_partial_censor(monkeypatch, fail_last):
    actor, critic = policy.arm_copy(policy.templates(9001), True,
                                    duration_head_seed=900100012, freeze_duration=True)
    scripted_labels(monkeypatch, lambda t, i: 1)
    env = SyntheticAdapter(9001, 3)
    original_step = env.step

    def step(sent):
        if fail_last and env.t == 2:
            raise RuntimeError("selected short partial")
        return original_step(sent)

    monkeypatch.setattr(env, "step", step)
    counts, rows = study.new_counts(True, short=True), []

    def collect():
        return learner.collect_episode(env, actor, critic, 3, 900100001,
                                       policy.generator(22), policy.generator(23),
                                       dict(arm="F", phase="eval", episode=0), lambda: None,
                                       counts, rows.append, lambda row: None, [],
                                       ratio_grouping="agent_compound", renewal=True, duration_support=(1,2))

    if fail_last:
        with pytest.raises(RuntimeError, match="selected short partial"):
            collect()
    else:
        ep = collect()
        assert ep["durations"][2].tolist() == [1]*5 and ep["duration_mask"][2].all()
    assert counts["d2"] == counts["eval_d2"] == 10 and counts["d4"] == 0
    assert counts["suppressed_decisions"] == 5
    assert counts["horizon_censored_holds"] == (0 if fail_last else 5)
    assert counts["team_steps"] == (2 if fail_last else 3) and bool(rows) != fail_last


def test_short_fixed_actual_publication_and_accounting(tmp_path):
    summary = study.run_pair(study.Config.engineering(pair="renewal_short_fixed_b01"), tmp_path, time.monotonic())
    assert summary["status"] == "COMPLETE" and summary["scientific_uav_calls"] == 0
    assert summary["object"] == study.SHORT_FIXED_OBJECT and summary["card"] == study.SHORT_FIXED_CARD
    assert summary["treatment_duration_support"] == [1,2] and summary["card_section"] == 7
    assert list(summary["arms"]) == ["F", "G"] and summary["counts"]["optimizer_steps"] == 8
    assert summary["counts"]["team_steps"] == 80 and summary["counts"]["d4"] == 0
    assert summary["counts"]["d2"] > 0 and summary["arms"]["F"]["duration_support"] == [1,2]
    rows = [json.loads(x) for x in (tmp_path / "episodes.jsonl").read_text().splitlines()]
    rolls = [json.loads(x) for x in (tmp_path / "rollouts.jsonl").read_text().splitlines()]
    for key in ("d2", "d4"):
        assert sum(x[key] for x in rows) == summary["counts"][key]
        for phase in ("train", "eval"):
            assert sum(x[key] for x in rows if x["phase"] == phase) == summary["counts"][phase + "_" + key]
        for a in "FG":
            assert sum(x[key] for x in rolls if x["arm"] == a) == summary["arms"][a]["training_counts"][key]
    assert all(x["d2"] == x["d4"] == 0 for x in rows if x["arm"] != "F")
    for a in "FG":
        ck = torch.load(tmp_path / f"final_{a}.pt", weights_only=True)
        assert ck["configuration"] == summary["configuration"] and ck["arm"] == a
    assert summary["arms"]["F"]["duration_frozen"] and summary["arms"]["F"]["exposure"]["duration"]["displacement"] == 0
    assert summary["primary"]["complete"] == summary["primary"]["F_minus_G"]["complete"]
    assert set(summary["primary"]["J"]) == {"F", "G", "H"}
    assert "selected_contrast" not in summary["primary"]
