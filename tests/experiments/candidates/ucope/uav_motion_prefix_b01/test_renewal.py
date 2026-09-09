"""Renewal's actual collector, primitive learner and publication boundaries."""
import json
import time

import numpy as np
import pytest
import torch

from experiments.candidates.ucope.uav_motion_prefix_b01 import learner, policy, study
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter


def scripted_samples(monkeypatch, labels):
    original = learner.sample
    calls = []
    choices = []
    monkeypatch.setattr(torch, "multinomial", lambda *a, **k: torch.tensor([choices.pop(0)]))

    def sample(actor, mean, recurrent, active, opening, vrng, drng, duration_mask):
        t = len(calls)
        assert np.array_equal(active, duration_mask)
        choices.extend(labels(t, i) for i in range(5) if active[i])
        before_v, before_d = vrng.get_state(), drng.get_state()
        result = original(actor, mean, recurrent, active, opening, vrng, drng,
                          duration_mask=duration_mask)
        assert not choices
        if not active.any():
            assert torch.equal(before_v, vrng.get_state())
            assert torch.equal(before_d, drng.get_state())
        calls.append((active.copy(), result[1].clone()))
        return result

    monkeypatch.setattr(learner, "sample", sample)
    return calls


def collect(env, actor, critic, counts, rows, horizon):
    return learner.collect_episode(
        env, actor, critic, horizon, 900100001, policy.generator(22), policy.generator(23),
        {"arm": "T", "phase": "train", "episode": 0}, lambda: None,
        counts, rows.append, lambda row: None, [], ratio_grouping="agent_compound", renewal=True)


def test_heterogeneous_expiry_all_held_recurrence_density_and_real_update(monkeypatch):
    actor, critic = policy.arm_copy(policy.templates(9001), True, duration_head_seed=900100012)
    with torch.no_grad():
        actor.duration[2].weight[0].fill_(.1)
        actor.duration[2].weight[1].fill_(-.1)
    calls = scripted_samples(monkeypatch, lambda t, i: int(t != 0 or i in (0, 2, 4)))
    inputs = []
    hook = actor.duration.register_forward_pre_hook(lambda m, a: inputs.append(a[0].detach().clone()))
    counts, rows = study.new_counts(True), []
    ep = collect(SyntheticAdapter(9001), actor, critic, counts, rows, 8)
    expected = torch.tensor([[1,1,1,1,1], [0,1,0,1,0], [0]*5, [0]*5,
                             [1,0,1,0,1], [0,1,0,1,0], [0]*5, [0]*5], dtype=torch.bool)
    assert torch.equal(ep["velocity_mask"], expected)
    assert torch.equal(ep["duration_mask"], expected)
    assert not ep["logp"][~expected].any()
    assert counts["recurrent_observations"] == 40 and ep["critic"].shape == (8, 136)
    assert counts["duration_decisions"] == counts["velocity_decisions"] == 12
    assert counts["d4"] == 10 and counts["suppressed_decisions"] == 28
    assert counts["horizon_censored_holds"] == 2
    for key in ("d4", "duration_decisions", "velocity_decisions", "suppressed_decisions", "horizon_censored_holds"):
        assert rows[0][key] == counts[key] == counts["train_" + key]
        assert counts["eval_" + key] == 0
    assert len(calls) == 8
    assert [tuple(x.shape) for x in inputs] == ([(67,)]*5 + [(5,67)] + [(67,)]*2 + [(2,67)]
                                                + [(67,)]*3 + [(3,67)] + [(67,)]*2 + [(2,67)])
    rollout = {key: value[None].clone() for key, value in ep.items()}
    rollout["obs"].requires_grad_()
    mean, rec = learner.recurrent_outputs(actor, rollout, 8)
    lp, _ = policy.joint_terms(actor, mean, rec, rollout["u"], rollout["durations"],
                               rollout["velocity_mask"], rollout["duration_mask"], "agent_compound")
    torch.testing.assert_close(lp[0], ep["logp"], rtol=1e-5, atol=1e-6)
    grad, = torch.autograd.grad(lp[0, 4].sum(), rollout["obs"])
    assert grad[0, 2].abs().sum() > 0  # Held observations influence later decisions.
    inputs.clear()
    initial = policy.snapshot(actor, critic)
    records = learner.update(actor, critic, learner.optimizer_for(actor, critic), [ep, ep], 8,
                             lambda: None, counts, ratio_grouping="agent_compound", entropy_coef=0.)
    assert len(records) == counts["optimizer_steps"] == 4
    assert len(inputs) == 4 and all(x.shape == (24, 67) for x in inputs)
    condition = torch.cat([ep["u"][expected].tanh()]*2)
    for x in inputs:
        torch.testing.assert_close(x[:, 64:], condition, rtol=0, atol=0)
    assert policy.exposure(initial, actor, critic)["duration_hidden"]["displacement"] > 0
    hook.remove()


@pytest.mark.parametrize("fail_last", [False, True])
def test_t254_t255_original_labels_actual_suppression_and_partial_censor(monkeypatch, fail_last):
    actor, critic = policy.arm_copy(policy.templates(9001), True, duration_head_seed=900100012)
    calls = scripted_samples(monkeypatch, lambda t, i: int((t, i) in ((254, 0), (255, 1))))
    env = SyntheticAdapter(9001, 256)
    original_step = env.step
    def step(sent):
        if fail_last and env.t == 255:
            raise RuntimeError("selected partial fixture")
        return original_step(sent)
    monkeypatch.setattr(env, "step", step)
    counts, rows = study.new_counts(True), []
    if fail_last:
        with pytest.raises(RuntimeError, match="selected partial fixture"):
            collect(env, actor, critic, counts, rows, 256)
    else:
        ep = collect(env, actor, critic, counts, rows, 256)
        assert ep["durations"][254, 0] == ep["durations"][255, 1] == 1
        assert ep["durations"][255, 2] == 0
        assert not ep["duration_mask"][255, 0] and ep["duration_mask"][255, 1:].all()
        # Labels 1 and 4 at t255 both execute one step; neither is relabelled.
        assert len(rows) == 1 and rows[0]["steps"] == 256
    assert len(calls) == 256 and env.t == (255 if fail_last else 256)
    assert counts["d4"] == 2  # Both actual selections survive a failing environment step.
    assert counts["suppressed_decisions"] == (0 if fail_last else 1)
    assert counts["horizon_censored_holds"] == (0 if fail_last else 2)
    assert counts["team_steps"] == (255 if fail_last else 256)
    assert bool(rows) != fail_last


@pytest.mark.parametrize("pair", ["renewal_b01", "renewal_b02"])
def test_actual_short_pair_primary_counts_checkpoint_and_identity(tmp_path, pair):
    config = study.Config.engineering(pair=pair)
    summary = study.run_pair(config, tmp_path, time.monotonic())
    assert summary["status"] == "COMPLETE" and summary["scientific_uav_calls"] == 0
    expected_object, expected_card = ((study.RENEWAL_B02_OBJECT, study.RENEWAL_B02_CARD) if pair == "renewal_b02"
                                      else (study.RENEWAL_OBJECT, study.RENEWAL_CARD))
    assert summary["object"] == expected_object and summary["card"] == expected_card
    assert summary["card_section"] == 7
    assert summary["commitment"] == "own_expiry"
    assert summary["counts"]["team_steps"] == 80 and summary["counts"]["optimizer_steps"] == 8
    rows = [json.loads(line) for line in (tmp_path / "episodes.jsonl").read_text().splitlines()]
    primary = summary["primary"]
    for arm in ("T", "G", "H"):
        values = [r["reward_sum"] / 8 for r in rows if r["arm"] == arm and r["phase"] == "eval"]
        assert primary["J"][arm] == values
        assert primary["arm_means"][arm] == pytest.approx(sum(values) / 2)
    for a, b in (("T", "G"), ("T", "H"), ("G", "H")):
        differences = [x-y for x,y in zip(primary["J"][a], primary["J"][b])]
        observed = primary[a + "_minus_" + b]
        assert observed["differences"] == differences
        assert observed["conditional_se"] == pytest.approx(abs(differences[0]-differences[1])/2)
    for arm in ("T", "G"):
        checkpoint = torch.load(tmp_path / f"final_{arm}.pt", weights_only=True)
        assert checkpoint["configuration"] == summary["configuration"] and checkpoint["arm"] == arm
        assert sum(v.numel() for field in ("actor", "critic") for v in checkpoint[field].values()) == (68553 if arm == "T" else 66311)
    for phase in ("train", "eval"):
        for key in ("d4", "suppressed_decisions", "horizon_censored_holds", "duration_decisions"):
            assert summary["counts"][f"{phase}_{key}"] == sum(r[key] for r in rows if r["phase"] == phase)
