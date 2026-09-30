"""Outcome-blind synthetic integration, sampling and failed-evidence checks."""
from dataclasses import replace
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02.contract import ARMS, FROZEN
from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS
from experiments.candidates.uav_fleet_adaptation.b02.collect import collect_episode
from experiments.candidates.uav_fleet_adaptation.b02.model import make_student, state_digest
from experiments.candidates.uav_fleet_adaptation.b02.policies import StudentPolicy, indexed_uniform
from experiments.candidates.uav_fleet_adaptation.b02.read import check_episode, read_batch
from experiments.candidates.uav_fleet_adaptation.b02.study import new_counts, run_batch
from experiments.candidates.uav_local_history.b01.study import file_identity


SMALL = replace(FROZEN, training_worlds=((111, 112), (113,), (114,)), evaluation_worlds=(211, 212),
                init_seed=311, shuffle_root=312, sampling_root=313, horizon=8, epochs=(1, 1, 1), batch_size=10)


class Synthetic:
    """Protocol-shaped fixture; no native UAV transition or latent-policy data."""
    def __init__(self, seed):
        self.env = self
        self.transmitter_mask = np.ones(5, dtype=bool)
        self.reset(seed)

    def reset(self, seed):
        rng = np.random.default_rng(seed)
        self.positions = rng.uniform([100., 100., 60.], [900., 900., 140.], (5, 3))
        self.users = rng.uniform(0., 1000., (50, 2))
        self.tick = 0
        self.transmitter_mask[:] = True
        return self.obs(), self.info()

    def obs(self):
        result = np.zeros((5, 104), dtype=np.float32)
        for i in range(5):
            own = self.positions[i]
            result[i, :3] = own / [1000., 1000., 100.] - [0., 0., .5]
            result[i, 3:5] = (self.users[i] - own[:2]) / 1000.
            result[i, 5] = .4
            for j, peer in enumerate(np.delete(self.positions, i, axis=0)):
                result[i, 63 + j * 4:66 + j * 4] = (peer - own) / [1000., 1000., 100.]
                result[i, 66 + j * 4] = 1.
            result[i, -1] = self.tick / 8.
        return result

    def info(self):
        sinr = np.full((5, 50), -5., dtype=np.float64)
        connections = np.zeros((5, 50), dtype=bool)
        for i in range(5):
            sinr[i, i] = 4. + self.positions[i, 0] / 1000.
            connections[i, i] = True
        q = float(np.clip((sinr[connections] - 3.) / 30., 0., 1.).mean())
        reward = .7 * 5 / 50. + .3 * q
        return dict(state_info=dict(uav_positions=self.positions.copy(), user_positions=self.users.copy()),
                    infos_dict={"uav_0": {"global": dict(connections=connections, sinr_matrix=sinr, served_users=5)}},
                    rewards_dict={f"uav_{i}": reward / 5. for i in range(5)})

    def step(self, commands):
        self.positions = np.clip(self.positions + commands.astype(np.float64) * 30.,
                                 [0., 0., 50.], [1000., 1000., 150.])
        self.tick += 1
        return self.obs(), 0., False, self.tick == 8, self.info()


@pytest.fixture(scope="module")
def study(tmp_path_factory):
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    out = tmp_path_factory.mktemp("b02") / "result"
    result = run_batch(out, "fixture", protocol=SMALL, factory=Synthetic)
    yield out, result
    torch.set_num_threads(previous)


def test_production_contract_and_no_bypass(tmp_path):
    expected = FROZEN.expected()
    assert expected["native_steps"] == 114688 and expected["complete_episodes"] == 448
    assert expected["datasets"] == [40960, 61440, 81920]
    assert expected["phase_updates"] == [2400, 2400, 3200]
    assert expected["optimizer_updates"] == 8000 and expected["sample_presentations"] == 4096000
    assert expected["full_C_requests"] == 92160 and expected["C7_requests"] == 10240
    assert expected["helper_request_ceiling"] == 133120 and expected["neural_rollout_row_ceiling"] == 81920
    with pytest.raises(ValueError, match="admitted"):
        run_batch(tmp_path / "native", "bad")
    with pytest.raises(ValueError, match="nonproduction"):
        run_batch(tmp_path / "injected", "bad", factory=Synthetic)
    assert not (tmp_path / "native").exists() and not (tmp_path / "injected").exists()


def test_native_collector_interface_eight_tick_correctness_only(tmp_path):
    from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
    env = make_real(819171)
    env.env.max_steps = 8
    (tmp_path / "raw").mkdir()
    counts = new_counts()
    try:
        result, cases = collect_episode(env, arm="expert", world=819172, out=tmp_path, protocol=SMALL,
                                        counts=counts, kind="training", phase=0, policy_sha="test-only")
        with np.load(tmp_path / result["raw"]["path"], allow_pickle=False) as data:
            raw = {k: data[k] for k in data.files}
        check_episode(raw, result, SMALL)
        assert counts["native_steps"] == 8 and counts["fit_started"] == 0
        assert cases[0].shape == (10, 114) and cases[1].shape == (10,)
    finally:
        env.close()


def test_full_synthetic_lineage_and_saved_reader(study, monkeypatch):
    out, result = study
    assert result["status"] == "COMPLETE"
    assert result["actual"]["native_steps"] == 128
    assert result["actual"]["optimizer_steps"] == 9
    assert result["actual"]["sample_presentations"] == 90
    assert result["actual"]["fit_started"] == 1 and result["actual_learning"]
    assert result["actual"]["complete_episodes"] == 16
    assert [p["adam_step_values"][0] for p in result["phases"]] == [2, 5, 9]
    assert {r["arm"] for r in result["rows"] if r["kind"] == "evaluation"} == set(ARMS)
    # A saved-data reader must not hide extra expert/actor/environment calls.
    def forbidden(*args, **kwargs):
        raise AssertionError("reader made an undeclared scientific call")
    from experiments.candidates.uav_fleet_adaptation.b02 import controllers, model
    monkeypatch.setattr(controllers.original, "_power", forbidden)
    monkeypatch.setattr(controllers.MemoC, "query", forbidden)
    monkeypatch.setattr(model.Student, "forward", forbidden)
    monkeypatch.setattr(Synthetic, "step", forbidden)
    reading = read_batch(out, permit_fixture=True)
    assert reading["status"] == "VERIFIED" and reading["raw_files"] == 16
    assert reading["native_ticks_verified"] == 128
    assert not any(reading["reader_calls"].values())
    with pytest.raises(ValueError, match="fixed scientific"):
        read_batch(out)
    with pytest.raises(FileExistsError):
        run_batch(out, "fixture", protocol=SMALL, factory=Synthetic)


def test_cached_sampled_policy_uses_new_address_not_cached_command():
    actor = make_student(700).eval()
    for p in actor.parameters():
        p.data.zero_()
    row = np.zeros(104, dtype=np.float32); row[:3] = [.5, .5, .5]
    policy = StudentPolicy(actor, world=211, agent=2, sampled=True, sampling_root=313)
    results = [policy.query(row, t, 2) for t in range(0, 40, 4)]
    assert not results[0]["memo_hit"] and all(r["memo_hit"] for r in results[1:])
    assert policy.counters["neural_rows"] == 1 and policy.counters["sampled_draws"] == 10
    assert len({r["innovation"] for r in results}) == 10
    assert len({r["action_index"] for r in results}) > 1
    for t, r in zip(range(0, 40, 4), results):
        u = indexed_uniform(313, 211, t, 2)
        assert r["innovation"] == u and r["action_index"] == int(u * 27)
    # Mutation cannot alter memo storage, and another agent/episode gets no cache.
    results[0]["logits"][:] = 10
    assert np.all(policy.query(row, 40, 2)["logits"] == 0)
    policy.reset()
    assert not policy.query(row, 44, 2)["memo_hit"]
    assert not StudentPolicy(actor, world=212, agent=2).query(row, 0, 2)["memo_hit"]


def test_initialization_is_addressed_and_does_not_change_global_rng():
    before = torch.random.get_rng_state().clone()
    a = make_student(99)
    assert torch.equal(before, torch.random.get_rng_state())
    assert state_digest(a.state_dict()) == state_digest(make_student(99).state_dict())
    assert state_digest(a.state_dict()) != state_digest(make_student(100).state_dict())
    assert sum(p.numel() for p in a.parameters()) == 34715


def test_reader_rejects_rehashed_wrong_draw_and_wrong_endpoint(study, tmp_path):
    src, _ = study
    out = tmp_path / "mutated"
    shutil.copytree(src, out)
    summary = json.loads((out / "summary.json").read_text())
    row = next(r for r in summary["rows"] if r["arm"] == "S_sampled")
    path = out / row["raw"]["path"]
    with np.load(path, allow_pickle=False) as z:
        raw = {k: z[k] for k in z.files}
    raw["innovation"][0, 0] = .123456789
    np.savez_compressed(path, **raw)
    value = file_identity(path); value["path"] = row["raw"]["path"]; row["raw"] = value
    (out / "summary.json").write_text(json.dumps(summary))
    with pytest.raises(AssertionError, match="fresh addressed"):
        read_batch(out, permit_fixture=True)
    row["policy_sha256"] = summary["assets"]["S0"]["state_sha256"]
    (out / "summary.json").write_text(json.dumps(summary))
    with pytest.raises(AssertionError, match="wrong behavior"):
        read_batch(out, permit_fixture=True)


def test_failed_worker_keeps_partial_actual_exposure_and_no_result(tmp_path):
    class Failing(Synthetic):
        def step(self, commands):
            if self.tick == 3:
                raise RuntimeError("fixture failure")
            return super().step(commands)
    out = tmp_path / "failed"
    with pytest.raises(RuntimeError, match="fixture failure"):
        run_batch(out, "fixture", protocol=SMALL, factory=Failing)
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "INCOMPLETE"
    assert summary["actual"]["native_step_calls"] == 4 and summary["actual"]["native_steps"] == 3
    assert summary["actual"]["fit_started"] == 0 and summary["actual"]["complete_episodes"] == 0
    assert summary["actual"]["expert_label_requests"] == 5
    assert summary["costs"]["full_C"]["requests"] == 5
    assert summary["costs"]["full_C"]["trajectories"] == 5 * 27
    assert summary["costs"]["helper"]["helper_calls"] == 5 and summary["costs"]["incomplete"]
    assert summary["partial_episode"]["world"] == 111 and summary["rows"] == []
    with pytest.raises(ValueError, match="incomplete/failed"):
        read_batch(out, permit_fixture=True)


def test_cli_requires_admission_before_any_scientific_import_or_output(tmp_path):
    from experiments.candidates.uav_fleet_adaptation.b02 import run
    command = [sys.executable, str(Path(run.__file__).resolve()), "--out", str(tmp_path / "forbidden"),
               "--launch-sha", "x", "--seed", "29342001"]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode != 0 and "admission" in result.stderr.lower()
    assert not (tmp_path / "forbidden").exists()
    source = Path(run.__file__).read_text()
    assert source.index("admission = require_admission") < source.index("    import torch")
