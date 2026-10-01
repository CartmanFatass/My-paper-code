"""Synthetic integration only; no native environment, production world or retained S asset."""
from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import make_student, state_digest
from experiments.candidates.uav_fleet_adaptation.b02.controllers import MemoC
from experiments.candidates.uav_fleet_adaptation.b02.policies import FeatureMemo
from experiments.candidates.uav_local_history.b01.study import file_identity
from experiments.candidates.uav_fleet_transmission.b05_score_sampling import read, study
from experiments.candidates.uav_fleet_transmission.b05_score_sampling.contract import (
    FROZEN, HIGH, LOW, Protocol, actor_for, source_identities, write_json,
)
from experiments.candidates.uav_fleet_transmission.b05_score_sampling.policies import FixedPolicy
from experiments.candidates.uav_fleet_transmission.b05_score_sampling.reading import comparisons, grid_probabilities

REPO = Path(__file__).resolve().parents[5]
PROTOCOL = Protocol(worlds=(13, 17), sampling_roots=(71, 73), actor_constructor_seeds=(79, 83),
                    bootstrap_seed=89, bootstrap_resamples=100, horizon=8)


class FabricatedEnvironment:
    """Original tuple/schema and deterministic clipped motion, without a radio environment."""
    steps = 0

    def __init__(self, seed):
        self.env = self
        self.transmitter_mask = np.ones(5, dtype=bool)
        self.reset(seed)

    def observation(self):
        obs = np.zeros((5, 104), dtype=np.float32)
        normalized = self.positions.copy()
        normalized[:, :2] /= 1000.
        normalized[:, 2] = (normalized[:, 2] - 50.) / 100.
        obs[:, :3] = normalized
        # One fabricated lawful local user and no observed peers. This produces
        # unequal candidate scores without invoking native state or radio code.
        obs[:, 3:5] = (self.users[0] - self.positions[:, :2]) / 1000.
        obs[:, 5] = .36
        obs[:, -1] = self.tick / PROTOCOL.horizon
        return obs

    def info(self):
        sinr = np.full((5, 50), 12., dtype=np.float64)
        connections = np.zeros((5, 50), dtype=bool)
        for agent in range(5):
            number = 1 + int(self.positions[agent, 0] // 200)
            connections[agent, agent * 10:agent * 10 + number] = True
        served = int(connections.sum())
        reward = .7 * served / 50. + .3 * .3
        return dict(state_info=dict(uav_positions=self.positions.copy(), user_positions=self.users.copy()),
                    infos_dict={"uav_0": {"global": dict(connections=connections, sinr_matrix=sinr, served_users=served)}},
                    rewards_dict={f"uav_{a}": reward / 5 for a in range(5)})

    def reset(self, seed):
        rng = np.random.default_rng(seed)
        self.positions = rng.uniform([100., 100., 70.], [900., 900., 130.], size=(5, 3))
        self.users = rng.uniform(0., 1000., size=(50, 2))
        self.tick = 0
        return self.observation(), self.info()

    def step(self, commands):
        type(self).steps += 1
        self.positions = np.clip(self.positions + commands.astype(np.float64) * 30., LOW, HIGH)
        self.tick += 1
        return self.observation(), np.zeros(5), False, self.tick == PROTOCOL.horizon, self.info()


@pytest.fixture
def completed(tmp_path, monkeypatch):
    counts = dict(fixed_queries=0, c_queries=0, feature_queries=0, actor_rows=0)
    for cls, key in ((FixedPolicy, "fixed_queries"), (MemoC, "c_queries"), (FeatureMemo, "feature_queries")):
        original = cls.query

        def wrapper(self, *args, original=original, key=key, **kwargs):
            counts[key] += 1
            return original(self, *args, **kwargs)

        monkeypatch.setattr(cls, "query", wrapper)
    models, records = [], []
    for lineage, seed in enumerate(PROTOCOL.actor_constructor_seeds):
        model = make_student(seed).eval().requires_grad_(False)
        original = model.forward

        def forward(x, original=original):
            counts["actor_rows"] += len(x)
            return original(x)

        monkeypatch.setattr(model, "forward", forward)
        path = tmp_path / f"fabricated_identity_{lineage}.txt"
        path.write_text(f"synthetic, untrained actor identity {seed}\n")
        models.append(model)
        records.append(dict(file_identity(path), path=str(path), state_sha256=state_digest(model.state_dict()), lineage=lineage))
    out = tmp_path / "output"
    before = FabricatedEnvironment.steps
    summary = study._execute(out, "synthetic", protocol=PROTOCOL, models=models, records=records,
                             env_factory=FabricatedEnvironment, repo=REPO, admission=None, scientific_invocation=False)
    yield out, models, records, summary, counts
    print("B05 integration synthetic work:", counts, "fabricated steps:", FabricatedEnvironment.steps - before)


def test_complete_worker_and_full_reader(completed):
    out, models, records, summary, counts = completed
    before = FabricatedEnvironment.steps
    result = read.read_result(out, REPO, fixture_models=models, fixture_records=records)
    assert result["status"] == "VERIFIED" and not result["scientific_invocation"]
    assert result["counts"] == PROTOCOL.expected()
    assert result["replay_counts"]["actor_rows"] == 120
    assert result["replay_counts"]["ordinary_queries"] == 140
    assert result["replay_counts"]["new_native_steps"] == 0
    assert len(result["paired"]["comparisons"]) == 21
    assert result["paired"]["aliases"] == {"Bstar_L1": "S_L1"}
    assert sum(r["queries"] for r in result["saved_G_Q10"]) == 40
    assert sum(r["geometric_agent_ticks"] for r in result["saved_G_Q10"]) == 160
    assert FabricatedEnvironment.steps == before
    with pytest.raises(FileExistsError):
        study._execute(out, "synthetic", protocol=PROTOCOL, models=models, records=records,
                       env_factory=FabricatedEnvironment, repo=REPO, admission=None, scientific_invocation=False)
    # Corruptions of the complete saved evidence must be rejected by the actual reader.
    config_path = out / "config.json"
    config = json.loads(config_path.read_text())
    bad = deepcopy(config)
    bad["source_identities"][next(iter(bad["source_identities"]))] = "wrong"
    write_json(config_path, bad)
    with pytest.raises(AssertionError, match="source identity"):
        read.read_result(out, REPO, fixture_models=models, fixture_records=records)
    write_json(config_path, config)
    row = next(r for r in summary["episodes"] if r["arm"] == "G")
    with np.load(out / row["raw"]["path"]) as archive:
        raw = {k: archive[k] for k in archive.files}
    for key in ("innovation", "policy_scores", "commands", "features", "nav_pre", "probabilities"):
        bad_raw = {k: v.copy() for k, v in raw.items()}
        bad_raw[key].flat[0] += 1
        with pytest.raises(AssertionError):
            read.check_episode(bad_raw, row, PROTOCOL, None)
    bad_row = dict(row, J=row["J"] + 1)
    with pytest.raises(AssertionError, match="episode metric"):
        read.check_episode(raw, bad_row, PROTOCOL, None)
    with pytest.raises(ValueError, match="missing, duplicated"):
        comparisons(summary["episodes"][:-1], PROTOCOL)
    first = summary["episodes"][0]
    path = out / first["raw"]["path"]
    with np.load(path) as archive:
        changed = {k: archive[k] for k in archive.files}
    changed["policy_scores"].flat[0] += 1
    np.savez_compressed(path, **changed)
    found = file_identity(path)
    first["raw"].update({k: found[k] for k in ("bytes", "sha256")})
    write_json(out / "summary.json", summary)
    with pytest.raises(AssertionError, match="full source C score replay"):
        read.read_result(out, REPO, fixture_models=models, fixture_records=records)
    failed = json.loads((out / "reading.json").read_text())
    assert failed["status"] == "FAILED" and failed["actual_work"]["completed_episodes"] == 0
    assert failed["actual_work"]["inflight"]["replay_counts"]["requests"] == 1
    assert failed["actual_work"]["inflight"]["actor_rows_attempted"] == 0
    assert failed["actual_work"]["inflight"]["verified_native_ticks"] == 8
    assert failed["new_native_steps"] == 0


def test_partial_failure_keeps_actual_exposure(tmp_path, monkeypatch):
    models = [make_student(s).eval() for s in PROTOCOL.actor_constructor_seeds]
    records = []
    for index, model in enumerate(models):
        path = tmp_path / f"dummy_{index}.txt"
        path.write_text("fabricated\n")
        records.append(dict(file_identity(path), path=str(path), state_sha256=state_digest(model.state_dict())))

    class FailingEnvironment(FabricatedEnvironment):
        def step(self, commands):
            if self.tick == 2:
                raise RuntimeError("synthetic native-call failure")
            return super().step(commands)

    out = tmp_path / "failure"
    with pytest.raises(RuntimeError, match="synthetic native-call"):
        study._execute(out, "fixture", protocol=PROTOCOL, models=models, records=records,
                       env_factory=FailingEnvironment, repo=REPO, admission=None, scientific_invocation=False)
    saved = json.loads((out / "summary.json").read_text())
    assert saved["state"] == "FAILED"
    assert saved["counts"]["native_step_calls"] == 3 and saved["counts"]["native_steps"] == 2
    assert saved["counts"]["ordinary_queries"] == 5 and saved["counts"]["complete_episodes"] == 0
    assert saved["inflight"]["policy_counts"]["requests"] == 5
    assert len(list((out / "raw").glob("*.partial.npz"))) == 1
    print("B05 failure fixture: 5 ordinary queries, 3 fabricated step attempts, 2 completions")


def test_frozen_exposure_and_53_bit_bins():
    counts = FROZEN.expected()
    assert counts["complete_episodes"] == 416 and counts["native_steps"] == 106496
    assert counts["ordinary_queries"] == 71680 and counts["student_queries"] == 61440
    assert counts["sampled_draws"] == 122880 and counts["score_tail_evaluations"] == 20480
    p = np.array([2. ** -54, .9, .1] + [0.] * 24, dtype=np.float64)
    effective = grid_probabilities(p)
    assert effective[0] == 2. ** -53 and np.all(effective >= 0) and effective.sum() == 1


def test_cli_admission_precedes_scientific_effects(tmp_path, monkeypatch):
    from scripts import hmasd_admission
    from experiments.candidates.uav_fleet_transmission.b05_score_sampling import run

    def refuse(*args, **kwargs):
        raise RuntimeError("synthetic admission refusal")

    monkeypatch.setattr(hmasd_admission, "require_admission", refuse)
    out = tmp_path / "forbidden_output"
    with pytest.raises(RuntimeError, match="synthetic admission refusal"):
        run.main(["--out", str(out), "--launch-sha", "synthetic", "--seed", "29630100"])
    assert not out.exists()
    with pytest.raises(ValueError, match="synthetic fixture cannot"):
        study._execute(out, "synthetic", protocol=FROZEN, models=[], records=[], env_factory=None,
                       repo=REPO, admission=None, scientific_invocation=False)
    assert not out.exists()
