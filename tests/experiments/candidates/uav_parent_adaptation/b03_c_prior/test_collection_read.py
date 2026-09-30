"""Synthetic interface/physics fixtures; never construct or step the native host."""

from collections import defaultdict
from pathlib import Path
import json
import subprocess
import sys

import numpy as np
import pytest
import torch

from experiments.candidates.uav_parent_adaptation.b03_c_prior.collection import LocalWrapper, collect_episode
from experiments.candidates.uav_parent_adaptation.b03_c_prior.policy import templates
from experiments.candidates.uav_parent_adaptation.b03_c_prior.read import verify_episode, verify_file
from experiments.candidates.uav_parent_adaptation.b03_c_prior.protocol import identity, expected_counts, train_world, eval_world
from experiments.candidates.uav_parent_adaptation.b03_c_prior.policy import optimizers
from experiments.candidates.uav_parent_adaptation.b03_c_prior.study import save_checkpoint


class GeometryFixture:
    """Small deterministic analytic fixture with native adapter's public keys."""

    def __init__(self, horizon=256):
        self.horizon = horizon
        self.commands = []

    def observation(self):
        obs = np.zeros((5, 104), np.float32)
        obs[:, :2] = self.positions[:, :2] / 1000
        obs[:, 2] = (self.positions[:, 2] - 50) / 100
        obs[:, -1] = self.tick / self.horizon
        # Empty local rows exercise C's waypoint branch without a hidden-map actor.
        return obs

    def state(self):
        return np.r_[self.positions.ravel(), self.users.ravel(), self.tick / self.horizon].astype(np.float32)

    def reset(self, seed=None):
        self.tick = 0
        self.positions = np.array([[0, 0, 50], [1000, 1000, 150], [100, 100, 50],
                                   [900, 500, 60], [500, 500, 100]], np.float64)
        self.users = np.array([(50 + 100 * (i % 10), 100 + 170 * (i // 10)) for i in range(50)], np.float64)
        return self.observation(), dict(state=self.state(), state_info=dict(
            uav_positions=self.positions.copy(), user_positions=self.users.copy()))

    def step(self, command):
        self.commands.append(command.copy())
        self.positions = np.clip(self.positions + 30 * command, [0, 0, 50], [1000, 1000, 150])
        self.tick += 1
        dist2 = ((self.positions[:, None, :2] - self.users) ** 2).sum(-1) + self.positions[:, None, 2] ** 2
        power = 10 ** 2.3 * (.15 / (4 * np.pi)) ** 2 / dist2
        sinr = 10 * np.log10(power / (power.sum(0, keepdims=True) - power + 1e-8))
        top = np.argsort(-sinr, axis=-1, kind="stable")[:, :10]
        connections = np.zeros((5, 50), bool)
        np.put_along_axis(connections, top, np.take_along_axis(sinr >= 3, top, axis=-1), axis=-1)
        served = connections.sum()
        quality = np.clip((sinr[connections] - 3) / 30, 0, 1).sum() / max(served, 1)
        reward = .7 * served / 50 + .3 * quality
        info = dict(next_state=self.state(),
                    state_info=dict(uav_positions=self.positions.copy(), user_positions=self.users.copy()),
                    rewards_dict={f"uav_{i}": reward / 5 for i in range(5)},
                    infos_dict={"uav_0": {"global": dict(connections=connections, sinr_matrix=sinr, served_users=served)}})
        return self.observation(), reward / 5, self.tick == self.horizon, False, info


def load(path):
    with np.load(path, allow_pickle=False) as raw:
        return {key: raw[key] for key in raw.files}


def test_initial_c_identity_and_full_saved_reader(tmp_path):
    torch.set_num_threads(1)
    actor, _ = templates(303031)
    path = tmp_path / "c.npz"
    counts = defaultdict(int)
    _, row = collect_episode(GeometryFixture(), actor, None, arm="C", master=303031,
                            world_seed=30300000, training=False, out=path, counts=counts)
    data = load(path)
    facts = verify_episode(data, row, actor)
    assert facts["endpoint_actor_rows"] == 320
    assert np.array_equal(data["commands"], data["c_commands"])
    assert counts["identity_shadow_rows"] == 320
    assert counts["c_ingests"] == 1280 and counts["c_decisions"] == 320
    assert counts["c_trajectories"] == 8640 and counts["c_model_ticks"] == 34560
    assert counts["team_steps"] == counts["native_step_calls"] == 256
    assert row["requested_departure_decisions"] == row["applied_departure_agent_ticks"] == 0
    broken = {key: value.copy() for key, value in data.items()}
    broken["macro_context"][3, 2, 107] += 1
    with pytest.raises(ValueError, match="feature packing"):
        verify_episode(broken, row, actor)
    broken = {key: value.copy() for key, value in data.items()}
    broken["macro_log_prob"][1, 0] += .1
    with pytest.raises(ValueError, match="category density"):
        verify_episode(broken, row, actor)


def test_sampled_law_hold_prior_and_matched_addresses(tmp_path):
    actor, _ = templates(303031)
    first = None
    for arm in ("I", "Ls"):
        path = tmp_path / (arm + ".npz")
        _, row = collect_episode(GeometryFixture(), actor, None, arm=arm, master=303031,
            world_seed=30300000, training=False, out=path, counts=defaultdict(int))
        data = load(path)
        verify_episode(data, row, actor)
        assert np.array_equal(data["commands"], np.repeat(data["commands"][::4], 4, axis=0))
        assert row["requested_departure_decisions"] > 0
        assert row["probability_role"] == "sampled_behavior"
        if first is None:
            first = data
        else:
            for key in ("macro_seeds", "macro_action", "commands", "post_positions"):
                assert np.array_equal(data[key], first[key])
    assert abs(row["mean_c_probability"] - .9) < 1e-6


def test_wrapper_ingests_actual_history_and_preserves_sent_hold():
    fixture = GeometryFixture(8)
    obs, _ = fixture.reset()
    wrapper = LocalWrapper()
    _, _, _, context = wrapper.ingest(obs, 0)
    assert np.array_equal(context[:, 107:110], np.zeros((5, 3)))
    learned = np.array([[0, 1, 0]] * 5, np.float32)
    wrapper.sent(learned)
    next_obs, *_ = fixture.step(learned)
    nominal, _, _, context = wrapper.ingest(next_obs, 1)
    assert np.array_equal(context[:, :104], next_obs)
    assert np.array_equal(context[:, 107:110], learned)
    assert np.any(nominal != learned)
    with pytest.raises(ValueError, match="every primitive"):
        wrapper.ingest(next_obs, 3)
    assert all(c.counters["ingests"] == 2 for c in wrapper.controllers)


def test_training_handoff_and_partial_failure_evidence(tmp_path):
    actor, critic = templates(303031)
    path = tmp_path / "train.npz"
    episodes, row = collect_episode(GeometryFixture(8), actor, critic, arm="train", master=303031,
        world_seed=30310000, training=True, out=path, counts=defaultdict(int), horizon=8)
    assert set(episodes) == {"context", "c_index", "action", "logp", "value", "critic", "reward"}
    assert episodes["context"].shape == (2, 5, 120)
    assert not any(value.requires_grad for value in episodes.values())
    class Broken(GeometryFixture):
        def step(self, command):
            if self.tick == 2:
                raise RuntimeError("synthetic native failure")
            return super().step(command)
    counts = defaultdict(int)
    path = tmp_path / "partial.npz"
    with pytest.raises(RuntimeError, match="synthetic native failure"):
        collect_episode(Broken(8), actor, critic, arm="train", master=303031,
            world_seed=30310000, training=True, out=path, counts=counts, horizon=8)
    data = load(path)
    assert counts["native_step_calls"] == 3 and counts["team_steps"] == 2
    assert data["commands"].shape[0] == 3 and data["reward"].shape[0] == 2
    assert counts["c_ingests"] == 15 and data["terminal_observation"].shape == (0, 104)


def test_seed_disjointness_count_algebra_and_artifact_hash(tmp_path):
    train = {train_world(b, e) for b in range(3) for e in range(512)}
    evaluation = {eval_world(b, e) for b in range(3) for e in range(32)}
    assert len(train) == 1536 and len(evaluation) == 96 and not train & evaluation
    expected = expected_counts()
    assert expected["team_steps"] == (1536 + 96 * 4) * 256 == 491520
    assert expected["c_model_ticks"] == expected["team_steps"] * 5 // 4 * 27 * 4
    path = tmp_path / "fixture"
    path.write_bytes(b"bound")
    record = identity(path, tmp_path)
    assert verify_file(tmp_path, record) == path
    path.write_bytes(b"wrong")
    with pytest.raises(ValueError, match="artifact identity"):
        verify_file(tmp_path, record)


def test_checkpoint_binding_survives_run_relocation(tmp_path):
    actor, critic = templates(303031)
    aopt, copt = optimizers(actor, critic)
    run = tmp_path / "original"
    (run / "checkpoints").mkdir(parents=True)
    record = save_checkpoint(run / "checkpoints" / "initial.pt", actor, critic, aopt, copt,
                             endpoint="initial", master=303031, launch_sha="a" * 40)
    assert record["path"] == "checkpoints/initial.pt"
    moved = tmp_path / "collected"
    run.rename(moved)
    assert verify_file(moved, record) == moved / "checkpoints" / "initial.pt"


def test_clean_worker_manifest_binds_pure_reader_dependency():
    script = """import json, sys
from experiments.candidates.uav_parent_adaptation.b03_c_prior.study import source_manifest
assert 'experiments.candidates.uav_local_history.b01.read_b01' not in sys.modules
print(json.dumps([r['path'] for r in source_manifest()]))
"""
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True)
    assert "experiments/candidates/uav_local_history/b01/read_b01.py" in json.loads(result.stdout)


def test_reduced_synthetic_whole_batch_freezes_every_endpoint_before_eval(tmp_path, monkeypatch):
    from experiments.candidates.uav_parent_adaptation.b03_c_prior import study
    torch.set_num_threads(1)
    monkeypatch.setattr(study, "TRAIN_EPISODES", 2)
    monkeypatch.setattr(study, "EVAL_WORLDS", 1)
    small_counts = dict(fits=3, train_episodes=6, eval_episodes=12,
        native_step_calls=4608, team_steps=4608, train_team_steps=1536, eval_team_steps=3072,
        explicit_resets=18, ppo_rollouts=3, actor_optimizer_steps=12, critic_optimizer_steps=12,
        train_actor_rows=1920, train_critic_rows=384, eval_actor_rows=2880, identity_shadow_rows=960,
        actor_replay_rows=7680, critic_replay_rows=1536, c_ingests=23040, c_decisions=5760,
        c_trajectories=155520, c_model_ticks=622080)
    monkeypatch.setattr(study, "expected_counts", lambda: small_counts)
    real_collect = study.collect_episode
    order = []
    out = tmp_path / "batch"
    def observed(*args, **kwargs):
        if not kwargs["training"]:
            assert all((out / "checkpoints" / f"{master}_final.pt").is_file() for master in study.MASTERS)
        result = real_collect(*args, **kwargs)
        order.append((kwargs["master"], kwargs["arm"]))
        return result
    monkeypatch.setattr(study, "collect_episode", observed)
    result = study.run_batch(out, "a" * 40, factory=lambda seed: GeometryFixture())
    assert result["status"] == "COMPLETE", result["limits"]
    assert not result["limits"] and result["evaluation_started_after_all_fits_complete"]
    for key, value in small_counts.items():
        assert result["counts"][key] == value
    assert [a for _, a in order[:6]] == ["train"] * 6
    assert [a for _, a in order[6:]] == ["C", "I", "Lg", "Ls", "I", "Lg", "Ls", "C", "Lg", "Ls", "C", "I"]
    for fit in result["fits"]:
        for endpoint in ("initial", "final"):
            path = verify_file(out, fit[endpoint + "_checkpoint"])
            checkpoint = torch.load(path, weights_only=True)
            assert checkpoint["endpoint"] == endpoint and checkpoint["master"] == fit["master"]
    for record in result["artifacts"].values():
        verify_file(out, record)
    with pytest.raises(FileExistsError, match="never overwrites"):
        study.run_batch(out, "a" * 40, factory=lambda seed: GeometryFixture())
