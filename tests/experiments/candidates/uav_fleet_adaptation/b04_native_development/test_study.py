"""Synthetic complete-package checks; no native pilot or retained actor query."""
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS
from experiments.candidates.uav_fleet_adaptation.b02.model import checkpoint, make_student, state_digest
from experiments.candidates.uav_fleet_adaptation.b02.policies import indexed_uniform
from experiments.candidates.uav_fleet_adaptation.b04_native_development import run
from experiments.candidates.uav_fleet_adaptation.b04_native_development.assets import load_initial_assets
from experiments.candidates.uav_fleet_adaptation.b04_native_development.contract import (
    CANDIDATES, FROZEN, evaluation_plan, policy_identity, source_identities,
)
from experiments.candidates.uav_fleet_adaptation.b04_native_development.policies import LocalPolicy, shadow_on_features
from experiments.candidates.uav_fleet_adaptation.b04_native_development.reading import METRICS, calibration_result, validate_counts
from experiments.candidates.uav_fleet_adaptation.b04_native_development.study import ROOT, run_batch
from experiments.candidates.uav_local_history.b01.study import file_identity


SMALL = replace(FROZEN, training_worlds=(tuple(range(101, 109)), tuple(range(121, 129))),
                evaluation_worlds=((201, 202), (221, 222)), calibration_world_count=1, horizon=8,
                critic_seeds=(311, 312), actor_constructor_seeds=(313, 314), training_roots=(321, 322),
                calibration_roots=(323, 324), evaluation_roots=(325, 326))


class Synthetic:
    """Deterministic array fixture matching the saved source contract, not the UAV host."""
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
        state = np.concatenate((self.positions.ravel(), self.users.ravel(), [self.tick / 8.])).astype(np.float32)
        return dict(state=state, next_state=state.copy(),
                    state_info=dict(uav_positions=self.positions.copy(), user_positions=self.users.copy()),
                    infos_dict={"uav_0": {"global": dict(connections=connections, sinr_matrix=sinr, served_users=5)}},
                    rewards_dict={f"uav_{i}": reward / 5. for i in range(5)})

    def step(self, commands):
        self.positions = np.clip(self.positions + commands.astype(np.float64) * 30.,
                                 [0., 0., 50.], [1000., 1000., 150.])
        self.tick += 1
        return self.obs(), 0., False, self.tick == 8, self.info()


def fixture_bindings(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    bindings = []
    for lineage in range(2):
        actor = make_student(7001 + lineage).eval()
        payload = checkpoint(actor)
        payload.update(endpoint="S", launch_sha="fixture-source", optimizer_steps=8000)
        path = root / f"S{lineage}.pt"
        torch.save(payload, path)
        bindings.append(dict(file_identity(path), state_sha256=state_digest(actor.state_dict()),
                             launch_sha="fixture-source"))
    return bindings


@pytest.fixture(scope="module")
def study(tmp_path_factory):
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    root = tmp_path_factory.mktemp("fleet_b04")
    bindings = fixture_bindings(root / "inputs")
    out = root / "result"
    result = run_batch(out, "fixture", protocol=SMALL, factory=Synthetic, bindings=bindings)
    yield out, result, bindings
    torch.set_num_threads(previous)


def test_fixed_full_envelope_and_no_production_bypass(tmp_path):
    maximum = FROZEN.expected()
    assert maximum["complete_episodes"] == 1344 and maximum["native_steps"] == 344064
    assert FROZEN.expected((False, False))["native_steps"] == 327680
    assert FROZEN.expected((True, False))["native_steps"] == 335872
    assert maximum["actor_optimizer_steps"] == maximum["critic_optimizer_steps"] == 1024
    assert maximum["actor_replay_rows"] == 655360 and maximum["critic_replay_rows"] == 131072
    assert maximum["shadow_actor_rows"] == 20480 and maximum["shadow_motion_ticks"] == 81920
    with pytest.raises(ValueError, match="admitted"):
        run_batch(tmp_path / "native", "bad")
    with pytest.raises(ValueError, match="nonproduction"):
        run_batch(tmp_path / "fixture", "bad", factory=Synthetic, bindings=[])
    assert not (tmp_path / "native").exists() and not (tmp_path / "fixture").exists()
    with pytest.raises(ValueError, match="substitution"):
        load_initial_assets(SMALL)


def test_both_lineages_full_synthetic_contract(study):
    out, result, bindings = study
    assert result["state"] == "COMPLETE" and not result["scientific_execution"]
    validate_counts(result, SMALL)
    assert result["actual"]["training_episodes"] == result["actual"]["calibration_episodes"] == 16
    assert result["actual"]["fits_completed"] == result["actual"]["calibrations_completed"] == 2
    assert result["actual"]["actor_optimizer_steps"] == result["actual"]["critic_optimizer_steps"] == 32
    assert result["actual"]["expert_labels"] == 0
    assert all(r["actor_movement"]["changed_parameters"] > 0 for r in result["updates"])
    assert all(r["critic_movement"]["changed_parameters"] > 0 for r in result["updates"])
    assert all(r["policy_counts"].get("trajectories", 0) == 0 for r in result["rows"] if r["kind"] == "training")
    for lineage, update in enumerate(result["updates"]):
        assert len(update["groups"]) == 4
        assert [g["actor_optimizer_step_values"][0] for g in update["groups"]] == [4, 8, 12, 16]
        assert all(g["initial_identity"]["logits_exact"] for g in update["groups"])
        assert result["initial_assets"][lineage]["sha256"] == file_identity(Path(bindings[lineage]["path"]))["sha256"]
    first_final = next(i for i, r in enumerate(result["rows"]) if r["kind"] == "evaluation")
    assert first_final == 32
    assert len(list((out / "raw").glob("*.npz"))) == result["actual"]["complete_episodes"]
    assert {p.name for p in (out / "assets").iterdir()} == {"R0.pt", "R1.pt"}
    with pytest.raises(FileExistsError, match="existing scientific"):
        run_batch(out, "fixture", protocol=SMALL, factory=Synthetic, bindings=bindings)


def test_calibration_ties_and_exact_source_decoder_reuse():
    rows = [dict(lineage=0, kind="calibration", arm=candidate, world=101,
                 **{metric: 1. for metric in METRICS}) for candidate in CANDIDATES]
    assert calibration_result(rows, 0, SMALL)["winner"] == "C_0"
    for winner, expected in (("C_0", "C"), ("C_.10", "Q"), ("S_T1", "S"),
                              ("C_.05", "Bstar"), ("S_greedy", "Bstar"), ("S_T2", "Bstar")):
        plan, record = evaluation_plan(winner, "old", "new", 9)
        assert record["reference_arm"] == expected
        assert len(plan) == (4 if record["reused"] else 5)
    assert policy_identity("S_T1", "old", 9) != policy_identity("S_T1", "new", 9)
    assert policy_identity("S_T1", "old", 9) != policy_identity("S_T1", "old", 10)
    assert policy_identity("S_T1", "old", 9) != policy_identity("S_T2", "old", 9)


def test_asset_rejection_happens_before_native_constructor(tmp_path):
    bindings = fixture_bindings(tmp_path / "inputs")
    bindings[1]["sha256"] = "incorrect"
    calls = []
    def forbidden(seed):
        calls.append(seed)
        raise AssertionError("asset guard failed")
    out = tmp_path / "bad"
    with pytest.raises(ValueError, match="asset file identity"):
        run_batch(out, "fixture", protocol=SMALL, factory=forbidden, bindings=bindings)
    assert not calls
    summary = json.loads((out / "summary.json").read_text())
    assert summary["state"] == "INCOMPLETE" and not any(summary["actual"].values())


def test_no_cached_draw_or_category_mask_and_physical_aliases():
    actor = make_student(1).eval()
    with torch.no_grad():
        for parameter in actor.parameters():
            parameter.zero_()
    obs = np.zeros(104, dtype=np.float32); obs[:3] = [0., 0., 0.]
    policy = LocalPolicy("S_T1", actor, world=8, agent=2, sampling_root=9)
    answers = [policy.query(obs, tick, 2) for tick in range(0, 40, 4)]
    assert answers[0]["fallback"] and all(a["probabilities"].min() > 0 for a in answers)
    assert not answers[0]["memo_hit"] and all(a["memo_hit"] for a in answers[1:])
    assert policy.counters["neural_rows"] == 1 and policy.counters["sampled_draws"] == 10
    assert [a["innovation"] for a in answers] == [indexed_uniform(9, 8, t, 2) for t in range(0, 40, 4)]
    assert len({a["action_index"] for a in answers}) > 1
    assert not LocalPolicy("S_T1", actor, world=8, agent=2, sampling_root=9).query(obs, 0, 2)["memo_hit"]
    positions = np.tile([0., 0., 50.], (5, 1))
    # All-negative requested commands clip to no motion at the lower corner.
    index = int(np.flatnonzero(np.all(COMMANDS == -1, axis=1))[0])
    uniforms = np.full(5, (index + .5) / 27.)
    counts = {"shadow_actor_rows": 0, "shadow_motion_ticks": 0}
    shadow = shadow_on_features(actor, np.stack([a["features"] for a in answers[:5]]), uniforms, positions, counts)
    assert np.all(shadow["action_index"] == index)
    assert np.array_equal(shadow["positions"], np.broadcast_to(positions, (4, 5, 3)))
    assert counts == {"shadow_actor_rows": 5, "shadow_motion_ticks": 20}


def test_failed_prefix_is_recorded_without_replacement(tmp_path):
    class Failing(Synthetic):
        def step(self, commands):
            if self.tick == 3:
                raise RuntimeError("fixture transition failure")
            return super().step(commands)
    bindings = fixture_bindings(tmp_path / "inputs")
    out = tmp_path / "failed"
    with pytest.raises(RuntimeError, match="fixture transition failure"):
        run_batch(out, "fixture", protocol=SMALL, factory=Failing, bindings=bindings)
    summary = json.loads((out / "summary.json").read_text())
    assert summary["state"] == "INCOMPLETE" and summary["rows"] == []
    assert summary["actual"]["fits_started"] == 1 and summary["actual"]["fits_completed"] == 0
    assert summary["actual"]["native_step_calls"] == 4 and summary["actual"]["native_steps"] == 3
    assert summary["actual"]["collected_critic_rows"] == 1
    assert summary["actual"]["actor_optimizer_steps"] == 0
    assert summary["costs"]["student"]["requests"] == 5 and summary["costs"]["incomplete"]
    assert (out / summary["partial_episode"]["partial_raw"]["path"]).is_file()
    assert (out / summary["interrupted_training_state"]["path"]).is_file()


def test_cli_admission_precedes_scientific_imports_and_outputs(tmp_path):
    out = tmp_path / "forbidden"
    command = [sys.executable, str(Path(run.__file__).resolve()), "--out", str(out), "--launch-sha", "x",
               "--seed", "29354000"]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode != 0 and "admission" in result.stderr.lower() and not out.exists()
    source = Path(run.__file__).read_text()
    assert source.index("admission = require_admission") < source.index("    import torch")
    assert source_identities(ROOT)


def test_critic_failure_preserves_paid_actor_update_and_live_diagnostics(tmp_path, monkeypatch):
    from experiments.candidates.uav_fleet_adaptation.b04_native_development import study as module
    original = module.fresh_critic
    def failing_critic(seed):
        critic = original(seed)
        forward = critic.forward
        def wrapped(features):
            if features.ndim == 3:
                raise RuntimeError("fixture critic replay failure after actor step")
            return forward(features)
        critic.forward = wrapped
        return critic
    monkeypatch.setattr(module, "fresh_critic", failing_critic)
    bindings = fixture_bindings(tmp_path / "inputs")
    out = tmp_path / "failed_update"
    with pytest.raises(RuntimeError, match="critic replay failure"):
        run_batch(out, "fixture", protocol=SMALL, factory=Synthetic, bindings=bindings)
    summary = json.loads((out / "summary.json").read_text())
    assert summary["state"] == "INCOMPLETE"
    assert summary["actual"]["complete_episodes"] == 2
    assert summary["actual"]["actor_optimizer_steps"] == 1 and summary["actual"]["critic_optimizer_steps"] == 0
    group = summary["updates"][0]["groups"][0]
    assert group["status"] == "INCOMPLETE" and group["initial_identity"]["logits_exact"]
    assert group["actor_after_sha"] != group["actor_before_sha"]
    assert group["critic_after_sha"] == group["critic_before_sha"]
    epoch, = group["epochs"]
    assert epoch["actor_step_completed"] and not epoch["critic_step_completed"]
    assert np.isfinite(epoch["actor_loss"]) and epoch["actor_movement_l2"] > 0
    assert all(step == 1 for step in epoch["actor_optimizer_step_values"])
    assert (out / summary["interrupted_training_state"]["path"]).is_file()
