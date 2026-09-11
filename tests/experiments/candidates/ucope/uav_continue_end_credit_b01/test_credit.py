"""Focused synthetic contracts; no native environment or master8801 execution."""
import copy
import json
import math
import time

import pytest
import torch

from experiments.candidates.ucope.uav_continue_end_credit_b01 import credit, study
from experiments.candidates.ucope.uav_motion_prefix_b01 import learner, policy
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter
from experiments.candidates.ucope.uav_motion_prefix_b01.study import new_counts


def test_suffix_targets_mask_denominator_and_independent_clips():
    rollout = dict(reward=torch.tensor([[2., 3., 5.]]), value=torch.tensor([[1., 2., 3.]]),
                   residual_old=torch.ones(1, 3, 5))
    returns, av, ad, residual_target = credit.fixed_targets(rollout)
    torch.testing.assert_close(returns, torch.tensor([[10., 8., 5.]]))
    raw = torch.tensor([[9., 6., 2.]])
    sigma = raw.std(unbiased=False) + 1e-8
    torch.testing.assert_close(av, (raw-raw.mean())/sigma)
    torch.testing.assert_close(residual_target, torch.tensor([[[7.], [3.], [-3.]]]))
    torch.testing.assert_close(ad, (residual_target-1).expand(1, 3, 5)/sigma)
    assert abs(float(ad.mean())) > .1  # No duration recentering.
    vm = torch.tensor([[[True, False], [True, True]]])
    dm = torch.tensor([[[True, False], [False, False]]])
    vlp = torch.full((1, 2, 2), math.log(1.5), requires_grad=True)
    dlp = torch.full((1, 2, 2), math.log(.5), requires_grad=True)
    zeros = torch.zeros(1, 2, 2)
    loss = credit.masked_surrogate(vlp, zeros, torch.ones(1, 2, 1), vm)
    loss = loss + credit.masked_surrogate(dlp, zeros, torch.full((1, 2, 2), 2.), dm)
    torch.testing.assert_close(loss, torch.tensor(-(3*1.2+1.)/2))
    loss.backward()
    assert dlp.grad[0, 0, 0] != 0 and torch.count_nonzero(dlp.grad) == 1
    assert not vlp.grad.any()  # Velocity factor clips independently of duration.


def test_collection_old_path_rng_and_detached_conditional_records():
    torch.set_num_threads(1)
    actor, critic = policy.arm_copy(policy.templates(9003), True, duration_head_seed=900300012)
    residual = credit.residual_baseline(900300013)
    assert sum(p.numel() for p in residual.parameters()) == 2209
    captured = []
    handle = residual.register_forward_hook(lambda module, inputs, out: captured.append(inputs[0].clone()))
    outcomes = []
    for baseline in (None, residual):
        counts = new_counts(renewal=True, short=True)
        counts["duration_credit_rows"] = 0
        vrng, drng = policy.generator(900300041), policy.generator(900300042)
        episode = learner.collect_episode(SyntheticAdapter(1, 4), actor, critic, 4, 2,
            vrng, drng, dict(phase="train", arm="L"), lambda: None, counts, lambda row: None,
            lambda row: None, [], renewal=True, duration_support=(1, 2),
            ratio_grouping="agent_compound", credit_baseline=baseline)
        outcomes.append((episode, counts, vrng.get_state(), drng.get_state()))
    handle.remove()
    old, new = outcomes[0][0], outcomes[1][0]
    for key in old:
        torch.testing.assert_close(old[key], new[key])
    assert torch.equal(outcomes[0][2], outcomes[1][2]) and torch.equal(outcomes[0][3], outcomes[1][3])
    assert torch.equal(new["credit_mask"][:-1], new["duration_mask"][:-1])
    assert not new["credit_mask"][-1].any() and outcomes[1][1]["duration_decisions"] >= int(new["credit_mask"].sum())
    assert sum(x.shape[0] for x in captured) == outcomes[1][1]["duration_credit_rows"]
    assert all(x.shape[1] == 67 and not x.requires_grad for x in captured)
    torch.testing.assert_close(new["baseline_input"][..., -3:], new["u"].tanh())
    assert not any(x.requires_grad for x in new.values())
    # Regression can train only its own parameters on stored acting features.
    residual(new["baseline_input"][new["credit_mask"]]).square().add(1).mean().backward()
    assert all(p.grad is None for p in actor.parameters()) and all(p.grad is None for p in critic.parameters())


def test_complete_synthetic_pair_and_publication(tmp_path, monkeypatch):
    torch.set_num_threads(1)
    fitted, calls, residual_evals = {}, [], []
    original_copy, original_collect = policy.arm_copy, learner.collect_episode
    original_update = credit.update

    def copied(*args, **kwargs):
        models = original_copy(*args, **kwargs)
        arm = "F" if kwargs["freeze_duration"] else "L"
        fitted[arm] = dict(actor=models[0], initial=copy.deepcopy(models[0].state_dict()))
        return models

    def collection(*args, **kwargs):
        meta = args[7]
        calls.append((meta.copy(), args[4], args[5].initial_seed(), args[6].initial_seed()))
        assert kwargs["renewal"] and kwargs["duration_support"] == (1, 2)
        if meta["phase"] == "eval":
            residual_evals.append(kwargs["credit_baseline"])
        return original_collect(*args, **kwargs)

    def updating(*args, **kwargs):
        before = [p.detach().clone() for p in args[2].parameters()]
        result = original_update(*args, **kwargs)
        fitted["L"]["residual_moved"] = any(not torch.equal(a, b) for a, b in zip(before, args[2].parameters()))
        assert {int(s["step"]) for s in args[3].state.values()} == {4}
        return result

    monkeypatch.setattr(policy, "arm_copy", copied)
    monkeypatch.setattr(learner, "collect_episode", collection)
    monkeypatch.setattr(credit, "update", updating)
    config = study.Config(seed=9003, fixture=True, horizon=4, train_episodes=2, eval_episodes=2, chunk=2)
    result = study.run_pair(config, tmp_path, time.monotonic())
    assert result["status"] == "COMPLETE", result["limits"]
    assert result["counts"]["team_steps"] == 32 and result["counts"]["optimizer_steps"] == 8
    assert result["counts"]["scientific_uav_calls"] == 0 and result["counts"]["duration_credit_rows"] > 0
    assert [c[0]["arm"] for c in calls] == ["L"]*4+["F"]*4
    assert [c[0]["phase"] for c in calls] == ["train"]*2+["eval"]*2+["train"]*2+["eval"]*2
    assert all(x is None for x in residual_evals)
    for meta, reset, velocity, duration in calls:
        e, arm, train = meta["episode"], meta["arm"], meta["phase"] == "train"
        assert reset == 900300000+(10000 if train else 20000)+e
        expected = (41 if arm == "L" else 31) if train else (72000 if arm == "L" else 32000)+e
        assert velocity == 900300000+expected
        assert duration == velocity+(1 if train else 10000)
    for arm, params in (("L", 70762), ("F", 66311)):
        info = result["arms"][arm]
        assert info["trainable_parameters"] == params and info["exposure"]["total"]["displacement"] > 0
        assert all(x["displacement"] == 0 for x in info["evaluation_parameter_exposure"].values())
        checkpoint = torch.load(tmp_path/f"final_{arm}.pt", weights_only=True)
        assert ("residual" in checkpoint) == (arm == "L")
        assert checkpoint["counts"]["optimizer_steps"] == 4
        assert checkpoint["configuration"]["train_episodes"] == 2
        for name, p in checkpoint["actor"].items():
            torch.testing.assert_close(p, fitted[arm]["actor"].state_dict()[name])
            torch.testing.assert_close(fitted["L"]["initial"][name], fitted["F"]["initial"][name])
            if arm == "F" and name.startswith("duration."):
                assert torch.equal(p, fitted[arm]["initial"][name])
    assert fitted["L"]["residual_moved"]
    assert result["arms"]["L"]["exposure"]["duration_final"]["displacement"] > 0
    saved = json.loads((tmp_path/"summary.json").read_text())
    assert saved["primary"]["mean"] == result["primary"]["mean"]
    rows = [json.loads(line) for line in (tmp_path/"episodes.jsonl").read_text().splitlines()]
    assert all(r["J"] == r["reward_sum"]/4 for r in rows)


@pytest.mark.parametrize("delta,reading", [(.0101,"UP"),(.01,"WITHIN"),(-.01,"WITHIN"),(-.0101,"DOWN"),(-.001,"WITHIN")])
def test_rule_and_missing_primary(delta, reading):
    rows = [dict(arm=a, phase="eval", episode=e, J=delta if a == "L" else 0.) for a in ("L","F") for e in range(2)]
    assert study.primary_from_rows(rows, 2)["reading"] == reading
    assert study.primary_from_rows(rows[:-1], 2)["reading"] is None


def test_failure_stops_before_f_and_preserves_partial_primary(tmp_path):
    def broken(seed):
        raise RuntimeError("synthetic construction fault")
    result = study.run_pair(study.Config(seed=9003, fixture=True), tmp_path, time.monotonic(), factory=broken)
    assert set(result["arms"]) == {"L"} and result["status"] == "INCOMPLETE"
    assert result["primary"]["reading"] is None and (tmp_path/"summary.json").exists()


def test_publication_failure_is_retained(tmp_path):
    def broken(path, value):
        raise OSError("synthetic publication fault")
    config = study.Config(seed=9003, fixture=True, horizon=2, train_episodes=2, eval_episodes=2, chunk=2)
    result = study.run_pair(config, tmp_path, time.monotonic(), publish=broken)
    assert result["status"] == "PUBLICATION_FAILED" and result["primary"]["complete"]
    assert "publication" in result["limits"][-1]
