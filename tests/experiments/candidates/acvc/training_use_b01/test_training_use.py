"""Changed contracts on deterministic non-UAV fixtures; no scientific fit."""
from collections import defaultdict
import importlib.util
import json
from pathlib import Path
import time

import numpy as np
import pytest
import torch

from experiments.candidates.acvc.training_use_b01.protocol import (
    CAPS, CARD, EVALUATION_NAMESPACE, MASTER, OBJECT, FixedF, paired_primary,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import collect_episode, recurrent_outputs
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator, joint_terms


class TinyActor(torch.nn.Module):
    duration = None

    def __init__(self):
        super().__init__()
        self.log_std = torch.nn.Parameter(torch.full((3,), -5.0))

    def forward(self, x, hidden):
        outputs = []
        h = hidden[0]
        for row in x:
            h = .5 * h + torch.nn.functional.pad(row[:, 104:107], (0, 61))
            outputs.append(h)
        recurrent = torch.stack(outputs)
        return 2.0 + .1 * recurrent[..., :3], recurrent, h[None]


class TinyCritic(torch.nn.Module):
    def forward(self, x):
        return x[..., -20:].sum(-1) * .01


class LossFixture(SyntheticAdapter):
    def reset(self, seed=None):
        self.sent = []
        return super().reset(seed)

    def _obs(self):
        obs = super()._obs()
        obs[:, 3:63] = 0
        # Alternate a uniquely visible absolute anchor to force private link loss.
        obs[:, 3:5] = (.05 if self.t % 2 else .1) - obs[:, :2]
        obs[:, 5] = .5
        return obs

    def step(self, actions):
        self.sent.append(actions.copy())
        return super().step(actions)


def episode(filter_):
    env = LossFixture(19, horizon=64)
    actor = TinyActor()
    result = collect_episode(
        env, actor, TinyCritic(), 64, 20, generator(21), generator(22),
        {"phase": "train", "episode": 0}, lambda: None, defaultdict(int),
        lambda _row: None, lambda _row: None, [], ratio_grouping="agent_compound",
        execution_filter=filter_,
    )
    return actor, result, np.stack(env.sent)


def test_sample_density_actual_feedback_chunk_replay_and_episode_reset():
    fixed = FixedF()
    actor, data, sent = episode(fixed)
    proposal = data["u"].tanh().numpy()
    overridden = np.max(abs(sent - proposal), axis=-1) > .01
    assert overridden.any() and not overridden[0].any()
    # A triggered retrace may nearly equal the current proposal; event != magnitude.
    assert fixed.counts["training_F_retrace"] == 63 * 5
    np.testing.assert_array_equal(data["obs"][1:, :, 104:107], sent[:-1])
    np.testing.assert_array_equal(data["critic"][1:, -20:].reshape(63, 5, 4)[..., :3], sent[:-1])
    np.testing.assert_array_equal(data["obs"][0, :, 104:], 0)
    assert data["velocity_mask"].all() and not data["duration_mask"].any()
    assert data["logp"].shape == (64, 5)
    replay = {key: value[None] for key, value in data.items()}
    mean, recurrent = recurrent_outputs(actor, replay, 32)
    new_logp, _ = joint_terms(actor, mean, recurrent, replay["u"], replay["durations"],
                             replay["velocity_mask"], replay["duration_mask"], "agent_compound")
    torch.testing.assert_close(new_logp, replay["logp"], atol=1e-6, rtol=0)
    wrong_u = torch.from_numpy(sent).clamp(-.999999, .999999).atanh()[None]
    wrong_logp, _ = joint_terms(actor, mean, recurrent, wrong_u, replay["durations"],
                               replay["velocity_mask"], replay["duration_mask"], "agent_compound")
    assert (wrong_logp[0][overridden] - data["logp"][overridden]).abs().min() > 1
    _a, reset_data, reset_sent = episode(FixedF())
    np.testing.assert_array_equal(reset_sent, sent)
    torch.testing.assert_close(reset_data["hidden"], data["hidden"], atol=0, rtol=0)


def test_disabled_filter_preserves_default_bytes():
    _a, default, sent = episode(None)
    _b, identity, identity_sent = episode(lambda _obs, proposal: proposal)
    np.testing.assert_array_equal(sent, identity_sent)
    for key in default:
        torch.testing.assert_close(default[key], identity[key], atol=0, rtol=0)


def panel(delta=0):
    return [{"phase": "eval", "arm": "F", "episode": e, "reset_seed": 3026102000 + e,
             "J": delta, "S": delta * 256} for e in range(64)]


@pytest.mark.parametrize("delta,expected", [(.010001, "UP"), (.01, "WITHIN"),
    (-.01, "WITHIN"), (-.010001, "DOWN")])
def test_primary_frozen_boundaries(delta, expected):
    result = paired_primary(panel(), panel(delta))
    assert result["reading"] == expected and result["n_training_pairs"] == 1
    assert result["mean_S"] == pytest.approx(256 * delta)
    assert result["conditional_SE_J"] == pytest.approx(0, abs=1e-15)


@pytest.mark.parametrize("defect", ["missing", "duplicate", "world", "nonfinite"])
def test_no_partial_or_unmatched_primary(defect):
    damaged = panel(.1)
    if defect == "missing":
        damaged.pop()
    elif defect == "duplicate":
        damaged[-1]["episode"] = 0
    elif defect == "world":
        damaged[-1]["reset_seed"] += 1
    else:
        damaged[-1]["J"] = float("nan")
    result = paired_primary(panel(), damaged)
    assert result["reading"] == "INCOMPLETE" and "mean_J" not in result


@pytest.mark.parametrize("train_rule", ["C", "F"])
def test_common_F_only_orchestration_and_publication(tmp_path, monkeypatch, train_rule):
    script = Path(__file__).resolve().parents[5] / "scripts/run_acvc_fresh_dense_reuse_b01.py"
    spec = importlib.util.spec_from_file_location("training_use_runner", script)
    runner = importlib.util.module_from_spec(spec)
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda _threads: None)
    spec.loader.exec_module(runner)
    # No model construction, scientific RNG, optimization or real environment.
    actor, critic = torch.nn.Identity(), torch.nn.Identity()
    filters, loads, eval_arms, constructors = [], [], [], []
    monkeypatch.setattr(runner, "templates", lambda _seed: (actor, critic))
    monkeypatch.setattr(runner, "NativeGeometryActor", lambda *_args: actor)
    monkeypatch.setattr(runner, "generator", lambda seed: seed)
    monkeypatch.setattr(runner, "optimizer_for", lambda *_args: None)
    monkeypatch.setattr(runner, "geometry_snapshot", lambda *_args: {})
    monkeypatch.setattr(runner, "geometry_exposure", lambda *_args: {})
    monkeypatch.setattr(runner, "parameter_count", lambda *_args: 0)
    def load(path, seed):
        loads.append((path, seed))
        assert torch.load(path, weights_only=False)["object"] == OBJECT
        return actor
    monkeypatch.setattr(runner, "load_base", load)
    def training(env, actor, critic, horizon, seed, vr, dr, metadata,
                 check, counts, emit, diagnostic, limits, **options):
        filters.append(options.get("execution_filter"))
        emit(dict(metadata, steps=horizon, reward_sum=0., J=0.))
        counts["train_episodes"] += 1
        return {}
    monkeypatch.setattr(runner, "collect_episode", training)
    def update(actor, critic, optimizer, episodes, chunk, check, counts, **options):
        assert len(episodes) == 2 and chunk == 32
        counts["optimizer_steps"] += 4
        return [{"epoch": e, "loss": 0.} for e in range(4)]
    monkeypatch.setattr(runner, "update", update)
    def evaluation(env, base, gate, critic, seed, arm, phase, e, horizon, check, counts, emit):
        eval_arms.append(arm)
        emit(panel()[e])
    monkeypatch.setattr(runner, "collect", evaluation)
    def make_env(seed):
        constructors.append(seed)
        return None
    output = tmp_path / train_rule
    code = runner.run(output, "fixture", time.monotonic(), 20., make_env=make_env,
        train_episodes=4, horizon=32, eval_episodes=2, master=MASTER,
        evaluation_namespace=EVALUATION_NAMESPACE, object_name=OBJECT, card_path=CARD,
        allocation_seconds=CAPS, train_rule=train_rule, eval_arms=("F",))
    assert code == 0 and eval_arms == ["F", "F"] and len(loads) == 1
    assert constructors == [100000 * MASTER + 1000, 100000 * EVALUATION_NAMESPACE + 63]
    if train_rule == "F":
        assert all(isinstance(f, FixedF) for f in filters) and len({id(f) for f in filters}) == 4
    else:
        assert filters == [None] * 4
    result = json.loads((output / "summary.json").read_text())
    assert result["configuration"]["training_rule"] == train_rule
    assert result["status"] == "complete" and result["primary"]["primaries"] == []
    assert result["training_rows"] == 4 and result["evaluation_rows"] == 2
    assert len((output / "updates.jsonl").read_text().splitlines()) == 8
