"""Fabricated integration only; zero native environment calls and no retained asset queries."""
from copy import deepcopy
import json
from pathlib import Path
import numpy as np
import pytest

from experiments.candidates.uav_fleet_adaptation.b02.model import make_student, state_digest
from experiments.candidates.uav_local_history.b01.study import file_identity
from experiments.candidates.uav_fleet_transmission.b06_cadence import read, study
from experiments.candidates.uav_fleet_transmission.b06_cadence.contract import (
    FROZEN, HIGH, LOW, Protocol, source_identities, write_json,
)
from experiments.candidates.uav_fleet_transmission.b06_cadence.reading import comparisons

REPO = Path(__file__).resolve().parents[5]
PROTOCOL = Protocol(worlds=(113, 117), sampling_roots=(171, 173), actor_constructor_seeds=(179, 183),
                    bootstrap_seed=189, bootstrap_resamples=100, horizon=8)


class FabricatedEnvironment:
    """Deterministic geometry and unique eligible slots; no native radio is imported."""
    steps = 0

    def __init__(self, seed):
        self.env = self
        self.transmitter_mask = np.ones(5, dtype=bool)
        self.reset(seed)

    def number(self):
        return (2, 3, 2, 1, 2, 1, 2, 1, 3)[self.tick]

    def observation(self):
        obs = np.zeros((5, 104), dtype=np.float32)
        normalized = self.positions.copy()
        normalized[:, :2] /= 1000.
        normalized[:, 2] = (normalized[:, 2] - 50.) / 100.
        obs[:, :3] = normalized
        for agent in range(5):
            slots = obs[agent, 3:63].reshape(20, 3)
            ids = np.arange(agent * 10, agent * 10 + self.number())
            slots[:len(ids), :2] = (self.users[ids] - self.positions[agent, :2]) / 1000.
            slots[:len(ids), 2] = .44  # (12 dB + 10)/50, all eligible.
        obs[:, -1] = self.tick / PROTOCOL.horizon
        return obs

    def info(self):
        sinr = np.full((5, 50), -20., dtype=np.float64)
        connections = np.zeros((5, 50), dtype=bool)
        for agent in range(5):
            ids = np.arange(agent * 10, agent * 10 + self.number())
            sinr[agent, ids] = 12.
            connections[agent, ids] = True
        served = int(connections.sum())
        reward = .7 * served / 50. + .3 * .3
        self.sinr_matrix, self.connections = sinr.copy(), connections.copy()
        return dict(state_info=dict(uav_positions=self.positions.copy(), user_positions=self.users.copy()),
                    infos_dict={"uav_0": {"global": dict(connections=connections, sinr_matrix=sinr, served_users=served)}},
                    rewards_dict={f"uav_{a}": reward / 5 for a in range(5)})

    def reset(self, seed):
        rng = np.random.default_rng(seed)
        self.positions = rng.uniform([100., 100., 70.], [900., 900., 130.], size=(5, 3))
        self.users = rng.uniform(0., 1000., size=(50, 2))
        self.tick = 0
        info = self.info()
        info["infos_dict"] = {f"uav_{a}": {} for a in range(5)}
        info.pop("rewards_dict")
        return self.observation(), info

    def step(self, commands):
        type(self).steps += 1
        self.positions = np.clip(self.positions + commands.astype(np.float64) * 30., LOW, HIGH)
        self.tick += 1
        return self.observation(), np.zeros(5), False, self.tick == PROTOCOL.horizon, self.info()


def fabricated_assets(tmp_path):
    models, records = [], []
    for lineage, seed in enumerate(PROTOCOL.actor_constructor_seeds):
        model = make_student(seed).eval().requires_grad_(False)
        path = tmp_path / f"fabricated_{lineage}.txt"
        path.write_text(f"synthetic untrained actor {seed}\n")
        models.append(model)
        records.append(dict(file_identity(path), path=str(path), state_sha256=state_digest(model.state_dict()), lineage=lineage))
    return models, records


def test_frozen_panel_counts():
    exact, bounds = FROZEN.expected(), FROZEN.query_bounds()
    assert exact["complete_episodes"] == 1120 and exact["native_steps"] == 286720
    assert exact["count_decodes"] == 450560 and exact["event_gate_checks"] == 337920
    assert bounds["ordinary_queries"][1] == 501760 and bounds["student_queries"][1] == 307200
    assert bounds["sampled_draws"][1] == 737280 and bounds["score_tail_evaluations"][1] == 143360
    assert len(FROZEN.episode_order(0)) == 35
    assert FROZEN.episode_order(1) == FROZEN.episode_order(0)[1:] + FROZEN.episode_order(0)[:1]


def test_complete_worker_reader_and_tamper_rejection(tmp_path):
    models, records = fabricated_assets(tmp_path)
    out = tmp_path / "output"
    before = FabricatedEnvironment.steps
    summary = study._execute(out, "synthetic", protocol=PROTOCOL, models=models, records=records,
                             env_factory=FabricatedEnvironment, repo=REPO, admission=None, scientific_invocation=False)
    assert FabricatedEnvironment.steps - before == 560
    before_read = FabricatedEnvironment.steps
    result = read.read_result(out, REPO, fixture_models=models, fixture_records=records)
    assert result["status"] == "VERIFIED" and not result["scientific_invocation"]
    assert FabricatedEnvironment.steps == before_read
    PROTOCOL.check_counts(result["counts"])
    assert result["replay_counts"]["ordinary_queries"] == result["counts"]["ordinary_queries"]
    assert result["replay_counts"]["actor_rows"] == result["counts"]["student_queries"]
    assert result["replay_counts"]["new_native_steps"] == 0
    assert len(result["paired"]["comparisons"]) == 45
    assert result["paired"]["aliases"] == {"Bstar_L1/H4": "S_L1/H4"}
    assert all(r["event_queries"] == 10 for r in summary["episodes"] if r["mode"] == "E")
    with pytest.raises(FileExistsError):
        study._execute(out, "synthetic", protocol=PROTOCOL, models=models, records=records,
                       env_factory=FabricatedEnvironment, repo=REPO, admission=None, scientific_invocation=False)
    config = json.loads((out / "config.json").read_text())
    bad = deepcopy(config)
    bad["source_identities"][next(iter(bad["source_identities"]))] = "wrong"
    write_json(out / "config.json", bad)
    with pytest.raises(AssertionError, match="source identity"):
        read.read_result(out, REPO, fixture_models=models, fixture_records=records)
    write_json(out / "config.json", config)
    row = next(r for r in summary["episodes"] if r["arm"] == "G" and r["mode"] == "E")
    with np.load(out / row["raw"]["path"]) as archive:
        raw = {k: archive[k] for k in archive.files}
    for key in ("innovation", "policy_scores", "commands", "features", "nav_pre", "probabilities",
                "decision_ticks", "held_before", "own_count"):
        bad_raw = {k: v.copy() for k, v in raw.items()}
        bad_raw[key].flat[0] += 1
        with pytest.raises(AssertionError):
            read.check_episode(bad_raw, row, PROTOCOL, None)
    for key in ("query_mask", "count_loss", "extra_available", "extra_used", "remaining_motion_changed"):
        bad_raw = {k: v.copy() for k, v in raw.items()}
        bad_raw[key].flat[0] = not bad_raw[key].flat[0]
        with pytest.raises(AssertionError):
            read.check_episode(bad_raw, row, PROTOCOL, None)
    with pytest.raises(ValueError, match="missing, duplicated"):
        comparisons(summary["episodes"][:-1], PROTOCOL)
    first = summary["episodes"][0]
    path = out / first["raw"]["path"]
    with np.load(path) as archive:
        changed = {k: archive[k] for k in archive.files}
    changed["policy_scores"].flat[0] += 1
    np.savez_compressed(path, **changed)
    identity = file_identity(path)
    first["raw"].update({k: identity[k] for k in ("bytes", "sha256")})
    write_json(out / "summary.json", summary)
    with pytest.raises(AssertionError, match="full original scores"):
        read.read_result(out, REPO, fixture_models=models, fixture_records=records)
    failed = json.loads((out / "reading.json").read_text())
    assert failed["status"] == "FAILED" and failed["actual_work"]["completed_episodes"] == 0
    assert failed["actual_work"]["inflight"]["ordinary_queries"] == 1
    assert failed["new_native_steps"] == 0
    print("B06 synthetic episodes/steps", len(summary["episodes"]), FabricatedEnvironment.steps - before,
          "worker queries", result["counts"]["ordinary_queries"], result["counts"]["student_queries"])


def test_partial_failure_preserves_counts(tmp_path):
    models, records = fabricated_assets(tmp_path)

    class FailingEnvironment(FabricatedEnvironment):
        def step(self, commands):
            if self.tick == 2:
                raise RuntimeError("fabricated native-call failure")
            return super().step(commands)

    out = tmp_path / "failed"
    with pytest.raises(RuntimeError, match="fabricated native-call"):
        study._execute(out, "synthetic", protocol=PROTOCOL, models=models, records=records,
                       env_factory=FailingEnvironment, repo=REPO, admission=None, scientific_invocation=False)
    saved = json.loads((out / "summary.json").read_text())
    assert saved["state"] == "FAILED"
    assert saved["counts"]["native_step_calls"] == 3 and saved["counts"]["native_steps"] == 2
    assert saved["counts"]["ordinary_queries"] == 5 and saved["counts"]["complete_episodes"] == 0
    assert len(list((out / "raw").glob("*.partial.npz"))) == 1


def test_admission_precedes_scientific_effects(tmp_path, monkeypatch):
    from scripts import hmasd_admission
    from experiments.candidates.uav_fleet_transmission.b06_cadence import run

    def refuse(*args, **kwargs):
        raise RuntimeError("fabricated admission refusal")

    monkeypatch.setattr(hmasd_admission, "require_admission", refuse)
    out = tmp_path / "not_created"
    with pytest.raises(RuntimeError, match="fabricated admission refusal"):
        run.main(["--out", str(out), "--launch-sha", "synthetic", "--seed", "29670100"])
    assert not out.exists()
    with pytest.raises(ValueError, match="synthetic fixture cannot"):
        study._execute(out, "synthetic", protocol=FROZEN, models=[], records=[], env_factory=None,
                       repo=REPO, admission=None, scientific_invocation=False)
    assert not out.exists()
