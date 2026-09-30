"""Collector to full episode reader with scripted hold behavior; no native env or planner calls."""
from copy import deepcopy
import hashlib
from types import SimpleNamespace

import numpy as np
import pytest

from envs.pettingzoo import uav_radio
from envs.pettingzoo.scenario1 import UAVBaseStationEnv
from envs.pettingzoo.uav_env import MultiUAVEnv
from experiments.candidates.uav_fleet_transmission.b02.controller import empty_counts
from experiments.candidates.uav_fleet_transmission.b04 import reader, study
from experiments.candidates.uav_fleet_transmission.host import MatchedWorld
from experiments.candidates.uav_fleet_transmission.reader import _native_view, _public_state
from experiments.candidates.uav_fleet_transmission.study import artifact


class FormulaFixture:
    """Saved-data formulas only: never constructs, resets or steps a native environment."""
    def __init__(self, scene):
        view = _native_view(8, scene.user_positions, 500)
        self.view, self.env = view, SimpleNamespace(env=view)
        view.uav_positions = scene.uav_positions.copy()
        view._transmitter_mask = np.ones(8, dtype=bool)
        loss = uav_radio.free_space_user_path_loss(view.uav_positions, view.user_positions)
        view.sinr_matrix = uav_radio.user_sinr_from_path_loss(loss, transmitter_mask=view._transmitter_mask)
        view.connections = uav_radio.greedy_connection_assignment(view.sinr_matrix, 0., 10)
        view._uav_uav_path_loss_matrix = MultiUAVEnv._compute_uav_path_loss_matrix(view)
        view.uav_sinr_matrix = MultiUAVEnv._compute_uav_uav_sinr_matrix(view)
        view.set_transmitter_mask = self.set_mask
        self.closed = False

    def set_mask(self, mask):
        np.testing.assert_array_equal(mask, np.ones(8, dtype=bool))

    def state(self):
        return _public_state(self.view.uav_positions, self.view.user_positions, self.view.current_step, 500)

    def observation(self):
        return np.asarray([MultiUAVEnv._get_observation_vectorized(self.view, f"uav_{i}")["obs"]
                           for i in range(8)])

    def reset(self, seed):
        self.view.current_step = 0
        return self.observation(), {"state": self.state()}

    def step(self, command):
        assert command.dtype == np.float32 and not command.any()
        self.view.current_step += 1
        UAVBaseStationEnv._compute_reward(self.view)
        return (self.observation(), self.view.reward_info["total_reward"] / 8, False,
                self.view.current_step == 500,
                {"next_state": self.state(), "reward_components": {"reward_info": self.view.reward_info.copy()}})

    def close(self):
        self.closed = True


class ScriptedProgram:
    """No search; exercises real streaming and rehashed artifact validation."""
    fail_at = None

    def __init__(self, arm, horizon, branch_sink, candidate_sink):
        self.arm, self.branch_sink, self.candidate_sink = arm, branch_sink, candidate_sink
        self.plans, self.selections, self.banks = {}, {}, {}

    def select(self, t, report, old_mask):
        if t == self.fail_at:
            raise RuntimeError("constructed live-cell failure")
        assert old_mask == 255 and (report is not None) == (t % 10 == 0)
        if t == 40 or (t == 120 and self.arm != "T"):
            bank_id, branch_id = f"actual/t{t}/bank", f"actual/t{t}/branch/stay"
            rows = np.empty((0, 41), dtype="<f8")
            self.banks[bank_id] = {"start_t": t, "counts": dict(study.zero_counts(), model_ticks=0),
                "candidate_count": 0, "candidate_digest": hashlib.sha256(rows.tobytes()).hexdigest()}
            self.candidate_sink(bank_id, rows)
            self.plans[t] = {"initiated": False}
            self.selections[t] = {"selected_branch": "stay", "selected_model_branch": branch_id}
            result = {"arrays": {"sentinel": np.asarray([t, 500], dtype=np.int64)},
                "decisions": [{"t": t, "fixture": True}],
                "summary": {"start_t": t, "model_transitions": 500 - t,
                    "ordinary_candidate_position_predictions": 0,
                    "controller_counts": empty_counts(), "reward_counts": study.zero_counts()}}
            self.branch_sink(branch_id, result)
        return np.zeros((8, 3), dtype=np.float32), 255, {"t": t, "old_mask": 255, "issued_mask": 255}


@pytest.fixture
def constructed(monkeypatch):
    positions = np.asarray([[60. + 100 * i, 40. + 110 * (i % 4), 50.] for i in range(8)])
    users = np.asarray([[20. + 18 * i, 70. + 10 * (i % 17)] for i in range(50)])
    scene = MatchedWorld(-4041, 1, 2, users, positions)
    environments = []
    def make_env(*args):
        instance = FormulaFixture(scene)
        environments.append(instance)
        return instance
    monkeypatch.setattr(study, "make_env", make_env)
    monkeypatch.setattr(study, "TemporalProgram", ScriptedProgram)
    monkeypatch.setattr(reader, "TemporalProgram", ScriptedProgram)
    return scene, environments


def test_complete_collector_reader_streaming_and_rehashed_rejected_branch(constructed, tmp_path):
    scene, envs = constructed
    row = study.evaluate_episode("A2", scene, 3, tmp_path)
    assert envs[0].closed
    catalog = reader.verify_episode(row, tmp_path, scene)
    assert len(catalog["model_branches"]) == len(catalog["candidate_banks"]) == 2
    assert row["costs"]["model_physical_transitions"] == 840
    assert row["costs"]["worker_state_mask_requests"] == 0
    cat_path = tmp_path / row["evidence_catalog"]["path"]
    def replace_catalog(value):
        cat_path.unlink()
        study.write_catalog(cat_path, value)
        row["evidence_catalog"] = artifact(cat_path, tmp_path)
    for alteration in (lambda c: c["model_branches"].pop(0),
                       lambda c: c["model_branches"].reverse(),
                       lambda c: c["candidate_banks"].reverse()):
        altered = deepcopy(catalog)
        alteration(altered)
        replace_catalog(altered)
        with pytest.raises(ValueError, match="branch|bank"):
            reader.verify_episode(row, tmp_path, scene)
    replace_catalog(catalog)
    bank = catalog["candidate_banks"][0]
    bank_path = tmp_path / bank["raw"]["path"]
    original_bank = bank_path.read_bytes()
    with bank_path.open("wb") as stream:
        np.save(stream, np.zeros((1, 41), dtype="<f8"), allow_pickle=False)
    altered = deepcopy(catalog)
    altered["candidate_banks"][0]["raw"] = artifact(bank_path, tmp_path)
    replace_catalog(altered)
    with pytest.raises(ValueError, match="stationary candidate"):
        reader.verify_episode(row, tmp_path, scene)
    bank_path.write_bytes(original_bank)
    replace_catalog(catalog)
    native_path = tmp_path / row["raw"]["path"]
    original_native = native_path.read_bytes()
    arrays = reader.load_arrays(native_path)
    arrays["components"][0, 3] += 1
    with native_path.open("wb") as stream:
        np.savez_compressed(stream, **arrays)
    row["raw"] = artifact(native_path, tmp_path)
    with pytest.raises(ValueError, match="native full objective"):
        reader.verify_episode(row, tmp_path, scene)
    native_path.write_bytes(original_native)
    row["raw"] = artifact(native_path, tmp_path)
    branch = catalog["model_branches"][0]
    path = tmp_path / branch["raw"]["path"]
    with path.open("wb") as stream:
        np.savez_compressed(stream, sentinel=np.asarray([41, 500], dtype=np.int64))
    branch["raw"] = artifact(path, tmp_path)
    replace_catalog(catalog)
    with pytest.raises(ValueError, match="model branch"):
        reader.verify_episode(row, tmp_path, scene)


def test_partial_live_cell_keeps_completed_model_evidence_and_native_prefix(constructed, monkeypatch, tmp_path):
    scene, envs = constructed
    monkeypatch.setattr(ScriptedProgram, "fail_at", 41)
    with pytest.raises(RuntimeError, match="live-cell failure"):
        study.evaluate_episode("A2", scene, 3, tmp_path)
    assert envs[0].closed
    path = tmp_path / "raw" / f"n8_A2_w{scene.world_id}"
    with np.load(path / "native.npz", allow_pickle=False) as arrays:
        assert arrays["positions"].shape == (42, 8, 3)
        assert arrays["actions"].shape == (41, 8, 3)
    catalog = study.read_catalog(path / "evidence.json.gz")
    assert len(catalog["model_branches"]) == len(catalog["candidate_banks"]) == 1
    assert set(catalog["plans"]) == {"40"}
    assert len(reader.load_decisions(path / "native.jsonl.gz")) == 41
