"""Complete collection/count identity and the native metric boundary."""

import json

import numpy as np
import pytest

from experiments.candidates.uav_local_history.b01.study import (
    audit_points, native_reading, paired_reading, run_batch,
)


class FixtureEnv:
    def __init__(self, seed, horizon=8):
        self.horizon = horizon
        self.reset(seed)
        self.closed = False

    def reset(self, seed):
        rng = np.random.default_rng(seed)
        self.positions = rng.uniform(200, 800, size=(5, 3))
        self.positions[:, 2] = 100
        self.users = rng.uniform(100, 900, size=(50, 2))
        self.clock = 0
        return self.observation(), {"state_info": self.state_info()}

    def state_info(self):
        return {"user_positions": self.users.copy(), "uav_positions": self.positions.copy()}

    def observation(self):
        obs = np.zeros((5, 104), dtype=np.float32)
        obs[:, :2] = self.positions[:, :2] / 1000
        obs[:, 2] = (self.positions[:, 2] - 50) / 100
        for agent in range(5):
            if self.clock % 3 != 1:
                obs[agent, 3:5] = (self.users[agent] - self.positions[agent, :2]) / 1000
                obs[agent, 5] = .4
        obs[:, -1] = self.clock / self.horizon
        return obs

    def step(self, commands):
        self.positions = np.clip(self.positions + 30 * commands, [0, 0, 50], [1000, 1000, 150])
        self.clock += 1
        connections = np.zeros((5, 50), dtype=bool)
        connections[np.arange(5), np.arange(5)] = True
        sinr = np.full((5, 50), 9.0)
        reward = .7 * 5 / 50 + .3 * .2
        global_info = {"connections": connections, "sinr_matrix": sinr, "served_users": 5}
        info = {"infos_dict": {"uav_0": {"global": global_info}},
                "rewards_dict": {f"uav_{agent}": reward / 5 for agent in range(5)},
                "state_info": self.state_info()}
        return self.observation(), reward / 5, self.clock == self.horizon, False, info

    def close(self):
        self.closed = True


def test_complete_fixture_counts_raw_and_summary(tmp_path):
    output = tmp_path / "run"
    environments = []

    def factory(seed):
        env = FixtureEnv(seed)
        environments.append(env)
        return env

    summary = run_batch(output, "a" * 40, factory=factory, seeds=(17, 18), horizon=8)
    assert summary["status"] == "COMPLETE", summary["limits"]
    assert summary["counts"] == {"constructors": 1, "explicit_resets": 4,
                                 "native_step_calls": 32, "team_steps": 32,
                                 "complete_episodes": 4, "fit_started": 0, "optimizer_steps": 0}
    assert environments[0].closed
    assert summary == json.loads((output / "summary.json").read_text())
    assert summary["paired"]["metrics"]["J"]["mean_H_minus_C"] == 0
    for row in summary["rows"]:
        with np.load(row["raw"]["path"]) as raw:
            assert raw["observations"].shape == (8, 5, 104)
            assert raw["terminal_observation"].shape == (5, 104)
            np.testing.assert_array_equal(raw["terminal_observation"][:, -1], np.ones(5))
            np.testing.assert_allclose(raw["terminal_observation"][:, :2] * 1000,
                                       raw["post_positions"][-1, :, :2], atol=1e-4, rtol=0)
            assert raw["cache_points"].shape == (2, 5, 64, 2)
            assert raw["decision"].sum() == 10
            assert row["controller_counts"]["ingests"] == 40
            assert row["J"] == raw["reward"].mean()
            assert row["mean_served"] == raw["served"].mean()
            assert np.all(raw["commands"][1:4] == raw["commands"][0])
            assert np.all(raw["commands"][5:8] == raw["commands"][4])
    with pytest.raises(FileExistsError):
        run_batch(output, "a" * 40, factory=factory, seeds=(17, 18), horizon=8)


def test_missing_pair_is_not_filled():
    with pytest.raises(ValueError, match="every C/H"):
        paired_reading([{"arm": "C", "seed": 17}])
    with pytest.raises(ValueError, match="duplicate"):
        paired_reading([{"arm": "C", "seed": 17}, {"arm": "C", "seed": 17}])


def test_audit_distinguishes_roundoff_duplicate_and_missing():
    audit = audit_points(np.array([[0, 0], [.0001, 0], [2, 2]]), np.array([[0, 0], [1, 1]]))
    assert audit["duplicate_matches"] == 1
    assert audit["unmatched"] == 1
    assert audit["unique_true_users"] == 2


def test_native_reading_uses_team_sum_and_checks_service():
    env = FixtureEnv(1)
    _, scalar, _, _, info = env.step(np.zeros((5, 3)))
    reward, service, quality = native_reading(info)
    assert reward == pytest.approx(5 * scalar)
    assert service == 5
    assert quality == pytest.approx(.2)
    info["infos_dict"]["uav_0"]["global"]["served_users"] = 6
    with pytest.raises(RuntimeError, match="service"):
        native_reading(info)


def test_entry_requires_admission_before_scientific_effects(monkeypatch, tmp_path):
    from experiments.candidates.uav_local_history.b01 import run, study
    from scripts import hmasd_admission

    def denied(*args, **kwargs):
        raise PermissionError("fixture admission refusal")

    def forbidden(*args, **kwargs):
        pytest.fail("scientific batch reached before admission")

    monkeypatch.setattr(hmasd_admission, "require_admission", denied)
    monkeypatch.setattr(study, "run_batch", forbidden)
    output = tmp_path / "unadmitted"
    with pytest.raises(PermissionError, match="fixture admission"):
        run.main(["--out", str(output), "--launch-sha", "a" * 40, "--seed", "29091000"])
    assert not output.exists()
