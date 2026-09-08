"""Bounded synthetic checks; this file never imports or calls the real UAV base."""
import os
for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[name] = "1"

import copy
import json
import math
from pathlib import Path
import sys
import tempfile
import time

import numpy as np
import pytest
import torch

torch.set_num_threads(1)
torch.set_num_interop_threads(1)

from experiments.candidates.ucope.uav_motion_prefix_b01 import environment as envmod
from experiments.candidates.ucope.uav_motion_prefix_b01 import learner
from experiments.candidates.ucope.uav_motion_prefix_b01 import study
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import (
    arm_copy, exposure, generator, joint_terms, sample, snapshot, tanh_log_prob, templates)


@pytest.fixture
def tmp_path():
    root = Path("temp/directions/ucope/test/uav_motion_prefix_b01_unit")
    root.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(dir=root))


def test_lazy_factory_and_information_mapping():
    before = {key for key in sys.modules if key.startswith("envs.pettingzoo")}
    kwargs = {}
    class Base:
        def __init__(self, **values):
            kwargs.update(values)
    class Adapter:
        def __init__(self, base, seed):
            self.env, self.seed = base, seed
    result = envmod.make_real(44, Base, Adapter)
    assert result.seed == 44 and isinstance(result.env, Base)
    assert kwargs == dict(n_uavs=5, n_users=50, area_size=1000, height_range=(50, 150),
                         max_speed=30, time_step=1., max_steps=256, user_distribution="uniform",
                         channel_model="free_space", render_mode=None, seed=44,
                         max_observed_users=20, max_observed_uavs=10, use_shadowing=False,
                         paper_reward=False, use_fdma=False, bandwidth=20e6,
                         ground_bs_tx_power=30, step_path_loss_cache=True, channel_backend="vectorized")
    assert before == {key for key in sys.modules if key.startswith("envs.pettingzoo")}
    obs = np.arange(520, dtype=np.float32).reshape(5, 104)
    last = np.arange(15, dtype=np.float32).reshape(5, 3) / 20
    remaining = np.array([0, 1, 2, 3, 0])
    x = envmod.actor_features(obs, last, remaining)
    assert x.shape == (5, 108) and x.dtype == np.float32
    np.testing.assert_array_equal(x[:, :104], obs)
    np.testing.assert_array_equal(x[:, 104:107], last)
    np.testing.assert_array_equal(x[:, 107], remaining / 4)
    state = np.concatenate((np.tile([500, 250, 100], 5), np.full(100, 750), [.5]))
    cx = envmod.critic_features(state, last, remaining)
    np.testing.assert_allclose(cx[:15].reshape(5, 3), np.tile([.5, .25, .5], (5, 1)))
    np.testing.assert_array_equal(cx[15:115], .75)
    assert cx[115] == .5 and cx.shape == (136,)
    np.testing.assert_array_equal(cx[116:].reshape(5, 4)[:, :3], last)
    actor, _ = templates(9001)
    with torch.no_grad():
        original = actor(torch.tensor(x)[None], torch.zeros(1, 5, 64))[0][0, 0].clone()
    # Other-agent and global canaries never enter agent zero's forward path.
    obs[1:] = -999
    state[:] = 12345
    modified = envmod.actor_features(obs, last, remaining)
    with torch.no_grad():
        changed = actor(torch.tensor(modified)[None], torch.zeros(1, 5, 64))[0][0, 0]
    torch.testing.assert_close(changed, original, rtol=0, atol=0)
    saved = cx.copy()
    last[:] = -1
    remaining[:] = 4
    np.testing.assert_array_equal(cx, saved)  # Pre-decision features own their bytes.


def collect(env, actor, critic, seed=101, diagnostics=False, counts=None, check=lambda: None):
    counts = study.new_counts() if counts is None else counts
    rows, frames, limits = [], [], []
    data = learner.collect_episode(env, actor, critic, 8, seed, generator(22), generator(23),
                                    {"arm": "T" if actor.duration is not None else "G",
                                     "phase": "train", "episode": 0, "pair_master": 9001},
                                    check, counts, rows.append, frames.append, limits,
                                    diagnostics=diagnostics)
    return data, counts, rows, frames, limits


def test_mixed_hold_timing_history_and_reset(monkeypatch):
    actor, critic = arm_copy(templates(9001), True)
    def scripted(actor, mean, recurrent, active, opening, vrng, drng):
        return torch.full((5, 3), .3), torch.tensor([0, 1, 0, 1, 1]) if opening else torch.zeros(5, dtype=torch.long)
    monkeypatch.setattr(learner, "sample", scripted)
    env = envmod.SyntheticAdapter(1)
    data, counts, rows, frames, _ = collect(env, actor, critic, diagnostics=True)
    mask = data["velocity_mask"]
    assert mask[0].all() and mask[4:].all()
    assert mask[1:4, [0, 2]].all() and not mask[1:4, [1, 3, 4]].any()
    assert counts["velocity_decisions"] == 40 - 3 * 3
    assert counts["duration_decisions"] == 5 and counts["d4"] == 3
    assert data["duration_mask"][0].all() and not data["duration_mask"][1:].any()
    assert torch.count_nonzero(data["hidden"][0]) == 0
    assert torch.all(torch.linalg.vector_norm(data["hidden"][2] - data["hidden"][1], dim=-1) > 0)
    assert data["obs"][0, 1, -1] == 0
    assert data["obs"][1, 1, -1] == .75 and data["obs"][4, 1, -1] == 0
    torch.testing.assert_close(data["obs"][1, :, 104:107], torch.full((5, 3), .3).tanh())
    # Synthetic time observation changes only on the next observation.
    assert data["obs"][0, 0, 103] == 0 and data["obs"][1, 0, 103] == 1/8
    assert data["critic"][0, 116:].count_nonzero() == 0
    assert data["critic"][1, 123] == .75
    assert len(frames) == 25 and env.index_calls == 50
    assert frames[0]["local_user_indices"] == list(range(20))
    again, *_ = collect(env, actor, critic)
    assert not again["hidden"][0].any() and not again["obs"][0, :, 104:].any()
    assert rows[0]["prefix_path_length"][0] > 0


def test_rewards_returns_and_partial_episode():
    assert envmod.team_reward({"rewards_dict": {a: .02 for a in envmod.AGENTS}}) == .1
    values = torch.tensor([[.1, .2, .3, .4], [5., 6., 7., 8.]])
    target = learner.returns_to_go(values)
    torch.testing.assert_close(target, torch.tensor([[1., .9, .7, .4], [26., 21., 15., 8.]]))
    actor, critic = arm_copy(templates(9001), False)
    class Early(envmod.SyntheticAdapter):
        def step(self, action):
            obs, scalar, _, trunc, info = super().step(action)
            return obs, scalar, self.t == 3, trunc, info
    counts, rows = study.new_counts(), []
    with pytest.raises(RuntimeError, match="boundary at 3/8"):
        learner.collect_episode(Early(1), actor, critic, 8, 2, generator(3), generator(4),
                                {"arm": "G", "phase": "train", "episode": 0}, lambda: None,
                                counts, rows.append, lambda x: None, [])
    assert counts["team_steps"] == 3 and counts["completed_episode_steps"] == 0 and rows == []


def test_stable_density_masks_and_single_joint_clip():
    u = torch.tensor([[80., -80., .2], [.4, -.5, .7]])
    mean = torch.tensor([[.1, .2, -.1], [.2, -.1, .3]])
    std = torch.tensor([-.2, .1, .3])
    actual = tanh_log_prob(u, mean, std)
    # Float64 independent stable log(cosh) identity, including saturated actions.
    ud, md, sd = u.double(), mean.double(), std.double()
    jac = 2 * (math.log(2) - torch.logaddexp(ud, -ud))
    expected = (-.5 * ((ud-md)/sd.exp()).square() - sd - .5*math.log(2*math.pi) - jac).sum(-1)
    torch.testing.assert_close(actual.double(), expected, rtol=2e-6, atol=2e-4)
    assert torch.isfinite(actual).all()
    actor, _ = arm_copy(templates(9001), True)
    means = torch.zeros(2, 5, 3, requires_grad=True)
    rec = torch.zeros(2, 5, 64)
    samples = torch.zeros(2, 5, 3)
    vm = torch.tensor([[True, False, True, False, False], [False]*5])
    dm = torch.tensor([[True]*5, [False]*5])
    lp, ent = joint_terms(actor, means, rec, samples, torch.zeros(2, 5, dtype=torch.long), vm, dm)
    per = tanh_log_prob(samples, means, actor.log_std)
    torch.testing.assert_close(lp[0], per[0, 0] + per[0, 2] - 5*math.log(2))
    assert lp[1] == 0 and ent[1] == 0
    loss = learner.clipped_policy_loss(lp[1:], lp[1:].detach(), torch.tensor([2.])) - .01*ent[1]
    loss.backward()
    assert not means.grad.any()
    assert actor.log_std.grad is not None and not actor.log_std.grad.any()
    assert all(p.grad is None or not p.grad.any() for p in actor.duration.parameters())
    # Two active agents' ratios multiply BEFORE a single clip: 1.1^2 -> 1.2.
    result = learner.clipped_policy_loss(torch.tensor([2 * math.log(1.1)]), torch.zeros(1), torch.ones(1))
    assert result.item() == pytest.approx(-1.2)
    assert learner.clipped_policy_loss(torch.tensor([math.log(2.)]), torch.zeros(1), -torch.ones(1)) == 2


def test_initialization_streams_chunk_boundaries_and_actual_updates():
    global_before = torch.random.get_rng_state().clone()
    common = templates(9001)
    ta, tc = arm_copy(common, True)
    ga, gc = arm_copy(common, False)
    assert torch.equal(global_before, torch.random.get_rng_state())
    for key, value in ga.state_dict().items():
        assert torch.equal(value, ta.state_dict()[key])
    for left, right in zip(tc.parameters(), gc.parameters()):
        assert torch.equal(left, right)
    initial = snapshot(ta, tc)
    assert initial["common_actor"].numel() == 32134 and initial["critic"].numel() == 34177
    assert initial["total"].numel() == 66441 and snapshot(ga, gc)["total"].numel() == 66311
    assert not ta.duration.weight.any() and not ta.duration.bias.any()
    assert torch.equal(ta.duration(torch.zeros(5, 64)).softmax(-1), torch.full((5, 2), .5))
    va, vb, da = generator(90), generator(90), generator(91)
    dr_before = da.get_state().clone()
    with torch.no_grad():
        t_u, _ = sample(ta, torch.zeros(5, 3), torch.zeros(5, 64), np.ones(5, bool), True, va, da)
        g_u, _ = sample(ga, torch.zeros(5, 3), torch.zeros(5, 64), np.ones(5, bool), True, vb, None)
    assert torch.equal(t_u, g_u) and torch.equal(va.get_state(), vb.get_state())
    assert not torch.equal(dr_before, da.get_state())
    data1, *_ = collect(envmod.SyntheticAdapter(1), ta, tc, seed=10)
    data2, *_ = collect(envmod.SyntheticAdapter(1), ta, tc, seed=11)
    rollout = {key: torch.stack([data1[key], data2[key]]) for key in data1}
    # Perturb weights so h0 must be collected state, not recomputed episode history.
    with torch.no_grad():
        ta.encoder.bias.add_(.03)
    batched, _ = learner.recurrent_outputs(ta, rollout, 4)
    for ep in range(2):
        for start in (0, 4):
            reference, _, _ = ta(rollout["obs"][ep, start:start+4],
                                  rollout["hidden"][ep, start][None])
            torch.testing.assert_close(batched[ep, start:start+4], reference)
    # Real 32-step chunk shape and nonzero per-chunk h0, without environment calls.
    long = {"obs": torch.randn(2, 64, 5, 108), "hidden": torch.randn(2, 64, 5, 64)}
    full, _ = learner.recurrent_outputs(ta, long, 32)
    reference, _, _ = ta(long["obs"][1, 32:], long["hidden"][1, 32][None])
    torch.testing.assert_close(full[1, 32:], reference)
    optimizer = learner.optimizer_for(ta, tc)
    counts = study.new_counts()
    epochs = learner.update(ta, tc, optimizer, [data1, data2], 8, lambda: None, counts)
    assert len(epochs) == counts["optimizer_steps"] == 4
    assert all(int(state["step"]) == 4 for state in optimizer.state.values())
    observed = exposure(initial, ta, tc)
    assert observed["total"]["displacement"] > 0
    assert observed["total"]["relative_displacement"] > 0
    assert all(math.isfinite(row["loss"]) for row in epochs)


def pair(seed, differences, hover=True):
    rows = []
    for e, d in enumerate(differences):
        for arm, value in (("T", d), ("G", 0), ("H", 1)):
            if arm != "H" or hover:
                rows.append(dict(arm=arm, phase="eval", episode=e, J=value))
    return dict(seed=seed, mode="ENGINEERING_FIXTURE", primary=study.primary_from_rows(rows, 2))


def test_primary_uncertainty_and_dependencies():
    first, second = pair(1, [1, 3], False), pair(2, [4, 6])
    first["limits"] = ["source diagnostics unavailable"]
    result = study.aggregate([first, second])
    p = result["primary"]
    assert p["complete"] and p["pair_means"] == [2, 5] and p["mean"] == 3.5
    assert first["primary"]["T_minus_G"]["conditional_se"] == 1
    assert second["primary"]["T_minus_G"]["conditional_se"] == 1
    assert p["conditional_se"] == pytest.approx(math.sqrt(.5))
    assert p["training_endpoint_sample_sd"] == pytest.approx(math.sqrt(4.5))
    assert not first["primary"]["hover_complete"] and p["reading"] == "UP"
    negative = study.aggregate([pair(1, [-1, -3]), pair(2, [-4, -6])])
    assert negative["primary"]["reading"] == "DOWN" and negative["primary"]["mean"] == -3.5
    assert study.aggregate([pair(1, [.01, .01]), pair(2, [.01, .01])])["primary"]["reading"] == "WITHIN"
    first["primary"] = study.primary_from_rows([dict(arm="T", phase="eval", episode=0, J=-7)], 2)
    partial = study.aggregate([first, second])
    assert not partial["primary"]["complete"]
    assert partial["pairs"][0]["primary"]["J"]["T"] == [-7]
    with pytest.raises(ValueError, match="independent"):
        study.aggregate([second, second])


class Clock:
    def __init__(self, now=0):
        self.now = now
    def __call__(self):
        return self.now


def test_deadline_startup_and_no_step_after_detection(tmp_path):
    clock = Clock(1801)
    factory_calls = []
    summary = study.run_pair(study.Config.engineering(), tmp_path, 0, clock,
                             factory=lambda seed: factory_calls.append(seed))
    assert not factory_calls and summary["counts"]["team_steps"] == 0
    assert summary["status"] == "CAP_BREACH" and summary["pair_elapsed_wall"] == 1801
    # Once detected, advancing a phase or moving the clock backwards cannot restart work.
    deadline = study.Deadline(0, 10, 20, clock)
    with pytest.raises(TimeoutError):
        deadline.check()
    clock.now = 0
    with pytest.raises(TimeoutError):
        deadline.start_g()


def test_step_overrun_preserves_partial_counts():
    actor, critic = arm_copy(templates(9001), False)
    clock = Clock()
    deadline = study.Deadline(0, 10, 20, clock)
    class Slow(envmod.SyntheticAdapter):
        def step(self, actions):
            value = super().step(actions)
            clock.now = 11
            return value
    counts = study.new_counts()
    with pytest.raises(TimeoutError):
        collect(Slow(1), actor, critic, counts=counts, check=deadline.check)
    assert counts["step_calls"] == counts["team_steps"] == 1
    assert counts["train_episodes"] == 0


def test_clock_t_publication_hover_and_pair_publication(tmp_path, monkeypatch):
    # Script only workload duration and rows; the separate optimizer test is real.
    clock = Clock(2)
    def fake_episode(env, actor, critic, horizon, seed, vrng, drng, metadata,
                     check, counts, emit, emit_diag, limits, **kwargs):
        check()
        clock.now += 1
        counts["team_steps"] += horizon
        counts[f"{metadata['phase']}_team_steps"] += horizon
        counts["completed_episode_steps"] += horizon
        if metadata["arm"] == "T":
            counts["duration_decisions"] += 5
        emit(dict(metadata, steps=horizon, J=-.1 if metadata["arm"] == "T" else .2))
        check()
        return {}
    def fake_update(actor, critic, optimizer, episodes, chunk, check, counts):
        counts["optimizer_steps"] += 4
        return []
    def fake_save(*args, **kwargs):
        clock.now += 3  # Both checkpoint publications belong to their arms.
    monkeypatch.setattr(learner, "collect_episode", fake_episode)
    monkeypatch.setattr(learner, "update", fake_update)
    monkeypatch.setattr(torch, "save", fake_save)
    def publish(path, summary):
        clock.now += 5
        study.write_summary(path, summary)
    result = study.run_pair(study.Config.engineering(), tmp_path, 0, clock, publish=publish)
    assert result["arms"]["T"]["elapsed_wall"] == 9  # startup 2 + train/eval 4 + save 3
    assert result["arms"]["G"]["elapsed_wall"] == 14  # train/eval/H 6 + save 3 + pair write 5
    assert result["pair_elapsed_wall"] == 23 and result["primary"]["complete"]
    readback = json.loads((tmp_path / "summary.json").read_text())
    assert readback["pair_elapsed_wall"] == 23
    config = study.Config.engineering()
    config.arm_cap = 12
    clock.now = 2
    capped = study.run_pair(config, tmp_path / "capped", 0, clock, publish=publish)
    assert capped["status"] == "CAP_BREACH" and capped["primary"]["complete"]


def test_missing_diagnostics_and_hover_keep_primary(tmp_path, monkeypatch):
    actor, critic = arm_copy(templates(9001), True)
    class Missing(envmod.SyntheticAdapter):
        def _local_user_entries(self, i):
            raise RuntimeError("selected index missing")
    data, counts, rows, frames, limits = collect(Missing(1), actor, critic, diagnostics=True)
    assert len(rows) == 1 and data["reward"].shape == (8,) and len(frames) == 25
    assert limits and "diagnostics" in limits[0]
    # H failure handling through the actual study's dependency boundary, no extra learner.
    def fake_episode(env, actor, critic, horizon, seed, vrng, drng, metadata,
                     check, counts, emit, emit_diag, limits, **kwargs):
        if metadata["arm"] == "H":
            raise RuntimeError("hover unavailable")
        if metadata["arm"] == "T":
            counts["duration_decisions"] += 5
        emit(dict(metadata, J=-1 if metadata["arm"] == "T" else 0))
        return {}
    monkeypatch.setattr(learner, "collect_episode", fake_episode)
    monkeypatch.setattr(learner, "update", lambda *args: [])
    monkeypatch.setattr(torch, "save", lambda *args: None)
    result = study.run_pair(study.Config.engineering(), tmp_path, time.monotonic())
    assert result["primary"]["complete"] and not result["primary"]["hover_complete"]
    assert result["primary"]["T_minus_G"]["mean"] == -1
    assert result["status"] == "PRIMARY_COMPLETE_WITH_LIMITS"


def test_nonfinite_json_is_explicit_null(tmp_path):
    path = tmp_path / "summary.json"
    study.write_summary(path, {"value": float("nan"), "limits": []})
    result = json.loads(path.read_text())
    assert result["value"] is None and result["limits"]


def test_complete_fit_is_saved_before_failed_evaluation(tmp_path, monkeypatch):
    saved = []
    def collect_until_eval(env, actor, critic, horizon, seed, vrng, drng, metadata, *args, **kwargs):
        if metadata["phase"] == "eval":
            raise RuntimeError("evaluation unavailable")
        return {}
    monkeypatch.setattr(learner, "collect_episode", collect_until_eval)
    monkeypatch.setattr(learner, "update", lambda *args: [])
    monkeypatch.setattr(torch, "save", lambda content, path: saved.append((content, path.name)))
    result = study.run_pair(study.Config.engineering(), tmp_path, time.monotonic())
    assert [name for _, name in saved] == ["final_T.pt"]
    assert set(saved[0][0]) == {"actor", "critic", "configuration", "arm"}
    assert result["arms"]["T"]["fit_complete"] and not result["primary"]["complete"]
