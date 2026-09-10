"""P85 execution-mode semantics and same-fit publication, without native work."""
import importlib.util
import json
from pathlib import Path
import sys
import time

import numpy as np
import pytest
import torch

from experiments.candidates.ucope.uav_motion_prefix_b01 import learner, policy, study
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter


def test_mean_has_no_gaussian_draws_and_preserves_categorical_stream(monkeypatch):
    actor, _ = policy.arm_copy(policy.templates(9001), True, 900100012, True)
    mean = torch.arange(15, dtype=torch.float32).reshape(5, 3) / 10
    recurrent = torch.zeros(5, 64)
    active = np.array([True, False, True, True, False])
    velocity = policy.generator(100)
    duration = policy.generator(200)
    v0 = velocity.get_state().clone()
    # Independent equal-seed generator reproduces the exact fixed categorical draws.
    expected_rng = policy.generator(200)
    expected = [torch.multinomial(torch.tensor([.5, .5]), 1, generator=expected_rng).item()
                for _ in range(int(active.sum()))]
    monkeypatch.setattr(torch, "randn", lambda *a, **k: pytest.fail("mean drew Gaussian noise"))
    u, labels = policy.sample(actor, mean, recurrent, active, False, velocity, duration,
                              duration_mask=active, velocity_mode="mean")
    assert torch.equal(u[active], mean[active]) and not u[~active].any()
    assert labels[active].tolist() == expected
    assert torch.equal(velocity.get_state(), v0)
    assert torch.equal(duration.get_state(), expected_rng.get_state())


def test_sampled_default_keeps_exact_draw_order():
    actor, _ = policy.arm_copy(policy.templates(9001), True, 900100012, True)
    mean, recurrent = torch.ones(5, 3), torch.zeros(5, 64)
    active = np.array([True, False, True, True, False])
    vrng, drng = policy.generator(100), policy.generator(200)
    ref_v, ref_d = policy.generator(100), policy.generator(200)
    expected_u, expected_d = torch.zeros(5, 3), torch.zeros(5, dtype=torch.long)
    for i in range(5):
        if active[i]:
            expected_u[i] = mean[i] + actor.log_std.clamp(-5, 2).exp() * torch.randn(3, generator=ref_v)
            expected_d[i] = torch.multinomial(torch.tensor([.5, .5]), 1, generator=ref_d)[0]
    u, labels = policy.sample(actor, mean, recurrent, active, False, vrng, drng, duration_mask=active)
    assert torch.equal(u, expected_u) and torch.equal(labels, expected_d)
    assert torch.equal(vrng.get_state(), ref_v.get_state())
    assert torch.equal(drng.get_state(), ref_d.get_state())


def test_mean_episode_restarts_recurrence_hold_and_parameters(monkeypatch):
    actor, critic = policy.arm_copy(policy.templates(9001), True, 900100012, True)
    initial = policy.snapshot(actor, critic)
    env = SyntheticAdapter(9001, 8)
    records, frames = [], []
    original = learner.sample
    def sample(*args, **kwargs):
        assert kwargs["velocity_mode"] == "mean"
        u, labels = original(*args, **kwargs)
        assert torch.equal(u[args[3]], args[1][args[3]])
        return u, labels
    monkeypatch.setattr(learner, "sample", sample)
    for e in range(2):
        counts = study.new_counts(True, short=True)
        records.append(learner.collect_episode(
            env, actor, critic, 8, 900102000, None, policy.generator(900106000),
            {"arm": "F_mean", "phase": "eval", "episode": e}, lambda: None,
            counts, lambda row: None, frames.append, [], diagnostics=True,
            ratio_grouping="agent_compound", renewal=True, duration_support=(1, 2), velocity_mode="mean"))
    for key in records[0]:
        assert torch.equal(records[0][key], records[1][key]), key
    assert not records[0]["hidden"][0].any()
    starts = [f for f in frames if f["time"] == 0]
    assert all(f["remaining_hold"] == 0 and f["actual_decision"] for f in starts)
    assert all(x["displacement"] == 0 for x in policy.exposure(initial, actor, critic).values())


@pytest.mark.parametrize("fixture,seed", [(False, 8401), (True, 9001)])
def test_mean_cli_binding(tmp_path, monkeypatch, fixture, seed):
    spec = importlib.util.spec_from_file_location("p85_runner", "scripts/run_ucope_uav_motion_prefix_b01.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda n: None)
    def run(config, out, start):
        assert config.seed == seed and config.fixture == fixture
        assert config.pair == "renewal_mean_velocity_b01"
        assert config.ratio_grouping == "agent_compound" and config.entropy_coef == 0
        assert config.treatment_duration_head_seed == seed * 100000 + 12
        assert config.train_episodes == (2 if fixture else 512)
        return {"mode": "test", "status": "COMPLETE", "primary": {}}
    monkeypatch.setattr(runner, "run_pair", run)
    monkeypatch.setattr(sys, "argv", ["runner", "--pair", "renewal_mean_velocity_b01",
        "--seed", str(seed), "--out", str(tmp_path)] + (["--engineering-fixture"] if fixture else []))
    assert runner.main() == 0
    assert study.declared_masters("renewal_mean_velocity_b01") == (8401,)
    with pytest.raises(ValueError, match="no multi-pair aggregate"):
        study.aggregate([], "renewal_mean_velocity_b01")


def test_mean_same_fit_full_publication(tmp_path, monkeypatch):
    torch.set_num_threads(1)
    calls, updates, fits = [], [], []
    original_collect, original_update, original_save = learner.collect_episode, learner.update, torch.save
    def collect(*args, **kwargs):
        meta = args[7]
        calls.append((meta.copy(), args[4], args[5], args[6], kwargs.get("velocity_mode", "sampled")))
        if meta["phase"] == "train":
            assert "velocity_mode" not in kwargs
        return original_collect(*args, **kwargs)
    def update(*args, **kwargs):
        updates.append(kwargs.copy())
        return original_update(*args, **kwargs)
    def save(payload, path):
        fits.append(payload["arm"])
        original_save(payload, path)
    monkeypatch.setattr(learner, "collect_episode", collect)
    monkeypatch.setattr(learner, "update", update)
    monkeypatch.setattr(torch, "save", save)
    result = study.run_pair(study.Config.engineering(pair="renewal_mean_velocity_b01"), tmp_path, time.monotonic())
    assert result["status"] == "COMPLETE" and result["diagnostics_complete"]
    assert result["object"] == study.MEAN_VELOCITY_OBJECT and result["card"] == study.MEAN_VELOCITY_CARD
    assert result["card_section"] == 7 and fits == ["F", "G"]
    assert updates == [{"ratio_grouping": "agent_compound", "entropy_coef": 0.0}] * 2
    assert [c[0]["arm"] for c in calls] == [a for a in ("F", "F_sampled", "F_mean", "G", "G_sampled", "G_mean", "H") for _ in range(2)]
    mode_calls = {label: [c for c in calls if c[0]["arm"] == label]
                  for label in ("F_sampled", "F_mean", "G_sampled", "G_mean", "H")}
    for label, episodes in mode_calls.items():
        assert [c[1] for c in episodes] == [900102000, 900102001]
        if label.endswith("mean") or label == "H":
            assert all(c[2] is None for c in episodes)
        for e, c in enumerate(episodes):
            if label.startswith("F"):
                assert c[3].initial_seed() == 900106000 + e
            if label.startswith("G"):
                assert c[3].initial_seed() == 900104000 + e
    assert mode_calls["F_sampled"][0][3] is not mode_calls["F_mean"][0][3]
    assert torch.equal(mode_calls["F_sampled"][0][3].get_state(), mode_calls["F_mean"][0][3].get_state())
    for arm in ("F", "G"):
        for mode in ("sampled", "mean"):
            report = result["arms"][arm]["evaluation_modes"][mode]
            assert report["buffers_unchanged"]
            assert all(x["displacement"] == 0 for x in report["parameter_exposure_from_final_fit"].values())
    primary = result["primary"]
    assert primary["selected_contrast"] == "F_mean_minus_G_mean"
    assert primary["all_modes_complete"] and len(primary["J"]) == 5
    assert len([k for k in primary if "_minus_" in k]) == 8
    for key in [k for k in primary if "_minus_" in k]:
        a, b = key.split("_minus_")
        assert primary[key]["differences"] == [x-y for x,y in zip(primary["J"][a], primary["J"][b])]
    assert result["counts"]["team_steps"] == 112 and result["counts"]["optimizer_steps"] == 8
    assert result["counts"]["eval_episodes"] == 10
    assert json.loads((tmp_path / "summary.json").read_text())["primary"] == primary


@pytest.mark.parametrize("missing", ["F_sampled", "G_sampled", "H", "F_mean", "G_mean"])
def test_mean_primary_is_independent_of_other_mode_completeness(missing):
    rows = [{"arm": arm, "phase": "eval", "episode": e, "J": value + e}
            for arm, value in {"F_mean": 1., "G_mean": 2., "F_sampled": 9., "G_sampled": 0., "H": 8.}.items()
            if arm != missing for e in range(2)]
    result = study.primary_from_rows(rows, 2, renewal=True, fixed=True, mean_velocity=True)
    assert result["complete"] == (missing not in ("F_mean", "G_mean"))
    assert not result["all_modes_complete"] and result["selected_contrast"] == "F_mean_minus_G_mean"
    if result["complete"]:
        assert result["F_mean_minus_G_mean"]["mean"] == -1
