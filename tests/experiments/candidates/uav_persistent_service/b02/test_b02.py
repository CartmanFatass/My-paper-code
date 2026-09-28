"""B02 correctness fixtures use no selected study world or result launch."""

import json
from dataclasses import replace
from types import SimpleNamespace
import numpy as np
import pytest

from experiments.candidates.energy_relay_availability.runner import _sha256
from experiments.candidates.energy_relay_benchmark.b01.observation import S7S2_LAYOUT, own_energy
from experiments.candidates.uav_persistent_service import controllers as controller_module
from experiments.candidates.uav_persistent_service.controllers import Commitment, ordinary_dispatch
from experiments.candidates.uav_persistent_service.macro_env import NativeEpisode
from experiments.candidates.uav_persistent_service.b02 import batch
from experiments.candidates.uav_persistent_service.b02.episode import (
    HORIZON, LongMissionEpisode, add_block_readings, fixed_window_readings,
    rng_state_digest,
)
from experiments.candidates.uav_persistent_service.b02.readout import (
    ARMS, SEEDS, plan, summarize, verify_pair,
)


def _window(length):
    reward = np.full(length, 2.0)
    qos = np.full(length, .5)
    battery = np.full((length, 8), .5)
    ends = np.zeros((length, 2), bool)
    ends[-1, 0] = length < HORIZON
    ends[-1, 1] = length == HORIZON
    return fixed_window_readings(reward, qos, battery, ends, np.full(8, .75))


@pytest.mark.parametrize("length,late_steps,final_observed", [
    (5000, 0, 0), (6500, 500, 0), (11800, 5800, 100), (12000, 6000, 300),
])
def test_fixed_windows_use_planned_denominators_without_padding(length, late_steps,
                                                                  final_observed):
    row = _window(length)
    assert row["terminal_step"] == length
    assert row["unserved_remaining_mission_steps"] == HORIZON-length
    assert row["horizon_normalized_qos"] == pytest.approx(.5*length/HORIZON)
    assert row["late6000_mission_qos"] == pytest.approx(.5*late_steps/6000)
    assert row["late6000_native_J"] == 2*late_steps
    assert row["final300_observed_steps"] == final_observed
    assert row["final300_persistent_reserve_members"] == (0 if length == HORIZON else None)
    assert len(row["bins"]) == 4
    assert sum(item["observed_steps"] for item in row["bins"]) == length
    assert all(item["planned_steps"] == 3000 for item in row["bins"])
    assert sum(item["native_J"] for item in row["bins"]) == 2*length
    assert sum(item["mission_qos"] for item in row["bins"]) == pytest.approx(.5*length/3000)
    assert row["terminal_reason"] == ("truncated" if length == HORIZON else "terminated")


def test_wholly_unobserved_bins_keep_unknown_stock_and_zero_accrual():
    row = _window(5000)
    arrays = {"native_charger_input_wh": np.ones((5000, 8)),
              "native_consumed_wh": np.ones((5000, 8))*2,
              "native_positive_net_charge_wh": np.ones((5000, 8))*.5,
              "native_station_occupancy": np.ones((5000, 2), int),
              "native_station_queue": np.zeros((5000, 2), int),
              "waiting_steps": np.zeros((5000, 8), int),
              "metrics": np.zeros((5000, 14)),
              "native_battery": np.full((5000, 8), .5)}
    add_block_readings(row, arrays)
    assert row["block0_gross_charger_input_wh"] == 24000
    assert row["block1_observed_steps"] == 2000
    assert row["block1_stock_change_wh"] == 0
    assert row["block2_observed_steps"] == 0
    assert row["block2_native_J"] == 0
    assert row["block2_stock_change_wh"] is None
    assert row["block2_observed_reserve_uav_step_fraction"] is None


def _artifact(tmp_path, arm, length, users, rng):
    stem = arm
    raw = tmp_path / f"{stem}.npz"
    decisions = tmp_path / f"{stem}.decisions.json"
    np.savez_compressed(raw, reward=np.ones(length), ends=np.asarray(
        [[False, False]]*(length-1)+[[True, False]], bool),
        user_xy_m=np.asarray(users), rng_state_sha256_by_step=np.asarray(rng, dtype="U64"))
    decisions.write_text(json.dumps({"macros": []}))
    return {"arm": arm, "seed": SEEDS[0], "actual_length": length,
            "initial_state_sha256": "same", "ground_bs_sha256": "same",
            "user_xy_trace_sha256": "0"*64,
            "rng_state_stream_sha256": "1"*64,
            "raw_path": raw.name, "raw_sha256": _sha256(raw),
            "decisions_path": decisions.name, "decisions_sha256": _sha256(decisions)}


def test_pairing_checks_prefix_and_artifact_integrity(tmp_path):
    users = np.zeros((5, 30, 2))
    rng = [f"{i:064x}" for i in range(5)]
    left = _artifact(tmp_path, "O_H", 4, users, rng)
    right = _artifact(tmp_path, "P", 2, users[:3], rng[:3])
    verified = verify_pair(tmp_path, left, right)
    assert verified["status"] == "verified"
    assert verified["prefix_states"] == 3
    assert verified["unequal_lengths"]
    bad_rng = list(rng[:3])
    bad_rng[1] = "f"*64
    right = _artifact(tmp_path, "P", 2, users[:3], bad_rng)
    assert verify_pair(tmp_path, left, right)["reason"] == "exogenous_prefix"
    bad_users = users[:3].copy()
    bad_users[2, 0, 0] = 1
    right = _artifact(tmp_path, "P", 2, bad_users, rng[:3])
    assert verify_pair(tmp_path, left, right)["reason"] == "exogenous_prefix"
    right = _artifact(tmp_path, "P", 2, users[:3], rng[:3])
    (tmp_path / right["decisions_path"]).write_text("corrupt")
    assert verify_pair(tmp_path, left, right)["reason"] == "artifact_integrity"
    same_length = _artifact(tmp_path, "P", 4, users, rng)
    same_length["rng_state_stream_sha256"] = "different full stream"
    assert verify_pair(tmp_path, left, same_length)["reason"] == "exogenous_prefix"


def test_retained_ordinary_arithmetic_and_decoded_arrival_boundary(monkeypatch):
    eligible = np.asarray([True]+[False]*7)
    free = np.asarray([True, True]+[False]*6)
    station = np.zeros(8, int)
    margin = np.asarray([200., 600.]+[9999.]*6) * 168.49 / (160*3600)
    assert ordinary_dispatch(eligible, free, station, margin, np.full(8, 168.49),
                             np.asarray([100., 100.]+[0.]*6),
                             np.asarray([20.]*8), np.zeros(8), 3000) == 3
    assert controller_module.CAPTURE_RADIUS_M == 20.0
    controller = object.__new__(controller_module.CommitmentController)
    controller.heuristic = type("Heuristic", (), {"layout": None, "committed": np.zeros(8, bool)})()
    controller.options = {0: Commitment(0, 0, 120, 0)}
    controller.events = []
    controller._last_observed_step = None
    from collections import deque
    controller._battery_history = deque(maxlen=32)
    monkeypatch.setattr(controller_module, "own_energy", lambda *_: {
        "battery": np.full(8, .5), "charging": np.zeros(8, bool)})
    monkeypatch.setattr(controller_module, "own_positions", lambda *_: np.zeros((8, 3)))
    distances = np.full(8, 100.)
    distances[0] = 20.0001
    monkeypatch.setattr(controller_module, "decode_legal_observations", lambda *_: (
        np.ones(8), np.full(8, .5), np.zeros(8, int), distances, np.zeros((8, 3))))
    controller._observe(None, 1)
    assert controller.options[0].arrival is None
    distances[0] = 20.0
    controller._observe(None, 2)
    assert controller.options[0].arrival == 2
    layout = replace(S7S2_LAYOUT, max_steps=HORIZON)
    held = np.zeros((8, layout.dim), dtype=np.float32)
    records = held[:, layout.energy_uavs].reshape(8, 8, 13)
    records[np.arange(8), np.arange(8), 10] = 1.0/HORIZON
    np.testing.assert_array_equal(own_energy(held, layout)["waiting_steps"], np.ones(8, int))


def test_rng_digest_does_not_advance_stream():
    rng = np.random.RandomState(17)
    before = rng.get_state()
    digest = rng_state_digest(SimpleNamespace(np_random=rng))
    after = rng.get_state()
    assert len(digest) == 64
    assert before[0] == after[0]
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]


def _row(arm, seed, *, early=False, final_missing=False):
    return {"arm": arm, "seed": seed, "job_key": f"{arm}/{seed}", "status": "completed",
            "actual_length": 5000 if early else HORIZON,
            "horizon_normalized_qos": .81 if arm == "O_H" else .79,
            "raw_native_J": 100. if arm == "O_H" else 90.,
            "late6000_mission_qos": .70 if arm == "O_H" else .68,
            "late6000_native_J": 40. if arm == "O_H" else 30.,
            "native_reserve_uav_step_fraction": .1,
            "cutoff_event_count_sum": 0, "depletion_event_count_sum": 0,
            "terminal_zero_service": False,
            "final300_persistent_reserve_members": None if final_missing else 0,
            "net_stored_energy_wh": -100., "gross_charger_input_wh": 100.,
            "native_consumed_wh": 200., "native_positive_net_charge_wh": 80.,
            "native_station_occupancy_uav_steps": 10,
            "native_station_queue_steps": 0, "actual_team_travel_m": 100.,
            "unserved_remaining_mission_steps": 7000 if early else 0}


def test_fixed_plan_complete_pairs_and_missing_risk():
    jobs = plan()
    assert len(jobs) == 16 and len(SEEDS) == 8 and ARMS == ("O_H", "P")
    assert batch.MAX_NATIVE_STEPS == 192000
    rows = [_row(job["arm"], job["seed"]) for job in jobs]
    paired = {seed: {"seed": seed, "status": "verified"} for seed in SEEDS}
    summary = summarize(rows, pairing=paired)
    assert summary["status"] == "complete"
    assert summary["retention_rule"]["status"] == "supported"
    rows[0] = _row("O_H", SEEDS[0], early=True, final_missing=True)
    summary = summarize(rows, pairing=paired)
    assert summary["status"] == "complete"
    assert summary["retention_rule"]["status"] == "not_supported"
    assert summary["retention_rule"]["missing_final300_seeds"] == [SEEDS[0]]
    assert summarize(rows, pairing={})["contrasts"] == {}


def test_worker_preserves_preconstruction_failure(tmp_path, monkeypatch):
    (tmp_path / "raw").mkdir()
    def fail(*args, **kwargs):
        raise RuntimeError("fixture failure")
    monkeypatch.setattr(batch, "LongMissionEpisode", fail)
    row = batch.worker((plan()[0], str(tmp_path)))
    assert row["status"] == "failed"
    assert row["partial_observed_steps"] == 0
    assert json.loads((tmp_path / "raw" / f'{plan()[0]["arm"]}_{SEEDS[0]}.progress.json').read_text())[
        "status"] == "failed"


def test_worker_retains_partial_trace_after_failure(tmp_path, monkeypatch):
    (tmp_path / "raw").mkdir()
    class Partial:
        def __init__(self, *_):
            self.t, self.done = 3, False
            self.external_arm = "P"
        def macro_step(self, *_):
            raise RuntimeError("after three native steps")
        def save(self, path, *, complete):
            assert not complete
            path.write_text("partial witness")
            return {"raw_path": str(path), "raw_sha256": _sha256(path)}
        def close(self):
            pass
    monkeypatch.setattr(batch, "LongMissionEpisode", Partial)
    row = batch.worker((plan()[0], str(tmp_path)))
    assert row["status"] == "failed" and row["partial_observed_steps"] == 3
    assert row["error"] == "after three native steps"
    assert row["raw_path"].endswith(".partial.npz")
    assert (tmp_path / row["raw_path"]).exists()


def test_native_horizon_binding_and_no_commit_p_identity():
    seed, steps = 70293, 30
    original = NativeEpisode(seed, "P", horizon=HORIZON)
    long_p = LongMissionEpisode(seed, "P")
    long_o = LongMissionEpisode(seed, "O_H")
    try:
        assert long_p.controller.heuristic.layout.max_steps == HORIZON
        assert long_o.controller.heuristic.layout.max_steps == HORIZON
        assert long_o.env.env.max_steps == HORIZON
        long_o.controller.apply_choice(0)
        for _ in range(steps):
            np.testing.assert_array_equal(original.observations, long_p.observations)
            np.testing.assert_array_equal(original.observations, long_o.observations)
            original.step_native()
            long_p.step_native()
            long_o.step_native()
            for other in (long_p, long_o):
                np.testing.assert_array_equal(original.data["proposed"][-1], other.data["proposed"][-1])
                np.testing.assert_array_equal(original.data["submitted"][-1], other.data["submitted"][-1])
                assert original.data["reward"][-1] == other.data["reward"][-1]
                np.testing.assert_array_equal(original.controller.targets_xy, other.controller.targets_xy)
        assert long_p.controller.heuristic.service_snapshot_calls == original.controller.heuristic.service_snapshot_calls
        assert long_o.controller.heuristic.service_snapshot_calls == original.controller.heuristic.service_snapshot_calls
        assert len(long_p.rng_state_sha256_by_step) == steps+1
        assert len(long_o.rng_state_sha256_by_step) == steps+1
        assert long_p.rng_state_sha256_by_step == long_o.rng_state_sha256_by_step
    finally:
        original.close()
        long_p.close()
        long_o.close()


def test_native_short_observed_trace_reads_and_saves_without_padding(tmp_path):
    episode = LongMissionEpisode(70295, "P")
    try:
        for _ in range(30):
            episode.step_native()
        assert episode.t == 30 and not episode.done
        episode.data["ends"][-1] = (True, False)  # Test-only early terminal witness.
        episode.done = True
        row = episode.row()
        assert row["status"] == "completed" and row["terminal_step"] == 30
        assert row["unserved_remaining_mission_steps"] == HORIZON-30
        assert row["final300_persistent_reserve_members"] is None
        assert row["block0_observed_steps"] == 30
        assert row["block1_stock_change_wh"] is None
        paths = episode.save(tmp_path / "trace.npz", complete=True)
        assert _sha256(tmp_path / "trace.npz") == paths["raw_sha256"]
        with np.load(tmp_path / "trace.npz", allow_pickle=False) as raw:
            assert len(raw["reward"]) == 30
            assert len(raw["rng_state_sha256_by_step"]) == 31
            assert len(raw["user_xy_m"]) == 31
    finally:
        episode.close()
