"""Focused fixed-panel and controller invariants; 90 native transitions total."""

import hashlib
from collections import deque

import numpy as np
import pytest

from experiments.candidates.uav_persistent_service.b03.controller import (
    ReassignmentController, Transfer, max_nearest_distance, transfer_action,
)
from experiments.candidates.uav_persistent_service.b03.episode import (
    HORIZON, LongMissionEpisode, fixed_window_readings, transfer_readings,
)
from experiments.candidates.uav_persistent_service.b03.readout import (
    ARMS, CONTRAST_FIELDS, SEEDS, plan, summarize, verify_pair,
)
from experiments.candidates.uav_persistent_service.controllers import N_ACTIONS


def test_geometry_and_action_address():
    stations = np.asarray([[0., 0., 0.], [10., 0., 0.]])
    assert max_nearest_distance(stations[0], stations[1], stations) == pytest.approx(5.)
    assert max_nearest_distance(np.asarray([-2., 0., 0.]), stations[1], stations) == pytest.approx(5.)
    assert transfer_action(0, 0) == N_ACTIONS
    assert transfer_action(7, 2) == N_ACTIONS+23


def test_transfer_candidate_load_slack_duration_and_busy_destination(monkeypatch):
    from types import SimpleNamespace
    from experiments.candidates.uav_persistent_service.b03 import controller as module

    controller = object.__new__(ReassignmentController)
    controller.options = {}
    controller.transfers = {}
    controller.max_power_w = 500.0
    controller.limp_power_w = 150.0
    controller.heuristic = SimpleNamespace(
        layout=SimpleNamespace(max_steps=12000, energy_uavs=slice(0, 104)),
        h1_targets_xy=np.ones((8, 2))*100.0)
    controller._draw_w = lambda step: (np.full(8, 168.49), np.zeros(8, dtype=bool))
    xyz = np.zeros((8, 3))
    xyz[:, 2] = 100
    xyz[7, 0] = 1000
    stations = np.asarray([[0., 0., 100.], [1000., 0., 100.]])
    nearest = np.asarray([0]*7+[1])
    battery = np.full(8, .30)
    margin = np.full(8, .50)
    observations = np.zeros((8, 104))
    monkeypatch.setattr(module, "own_positions", lambda *_: xyz)
    monkeypatch.setattr(module, "own_energy", lambda *_: {
        "available": np.ones(8, dtype=bool), "battery": battery})
    monkeypatch.setattr(module, "decode_legal_observations", lambda *_: (
        margin, battery, nearest, np.zeros(8), np.zeros((8, 3))))
    monkeypatch.setattr(module, "station_records", lambda *_: {
        "xyz_m": np.repeat(stations[None, :, :], 8, axis=0),
        "valid": np.ones((8, 2), dtype=bool),
        "capacity_ratio": np.ones((8, 2))*.125})
    candidates = controller._candidates(observations, np.zeros(8, dtype=bool), 0)
    assert candidates
    best = candidates[0]
    assert best[3:6] == (0, 2, 1)
    assert best[-1] == [7, 1]
    expected = .10 + (500*best[2] + 150*500/3)/(160*3600)
    assert best[6] == pytest.approx(expected)
    assert best[0] == pytest.approx((.30-expected)*160*3600/168.49)
    assert controller.feasibility_rejections["source_under_capacity"] == 1
    controller.transfers[7] = Transfer(7, 1, 120, 0)
    assert controller._candidates(observations, np.zeros(8, dtype=bool), 0) == []
    assert controller.feasibility_rejections["destination_busy"] == 7
    controller.transfers.clear()
    battery[:] = .05
    assert controller._candidates(observations, np.zeros(8, dtype=bool), 0) == []
    assert controller.feasibility_rejections["nonpositive_slack"] == 7


def test_real_f_cancels_only_before_intended_basin(monkeypatch):
    from types import SimpleNamespace
    from experiments.candidates.uav_persistent_service.b03 import controller as module
    from experiments.candidates.uav_persistent_service import controllers as parent_module

    controller = object.__new__(ReassignmentController)
    controller.options = {}
    controller.transfers = {0: Transfer(0, 1, 300, 0)}
    controller.events = []
    controller._pending_restoration = set()
    controller._last_observed_step = None
    controller._battery_history = deque(maxlen=32)
    controller._real_modes = np.zeros(8, dtype=bool)
    controller._real_modes[0] = True
    controller.heuristic = SimpleNamespace(layout=object(), committed=np.zeros(8, dtype=bool))
    nearest = np.zeros(8, dtype=int)
    distances = np.full(8, 100.)
    battery = np.full(8, .4)
    monkeypatch.setattr(module, "own_energy", lambda *_: {
        "battery": battery, "charging": np.zeros(8, dtype=bool),
        "return_margin": np.full(8, .02)})
    monkeypatch.setattr(module, "own_positions", lambda *_: np.zeros((8, 3)))
    monkeypatch.setattr(module, "decode_legal_observations", lambda *_: (
        np.full(8, .02), np.full(8, .4), nearest, distances, np.zeros((8, 3))))
    monkeypatch.setattr(parent_module, "own_energy", module.own_energy)
    monkeypatch.setattr(parent_module, "own_positions", module.own_positions)
    monkeypatch.setattr(parent_module, "decode_legal_observations", module.decode_legal_observations)
    controller._observe(np.zeros((8, 1)), 1)
    assert controller.transfers == {}
    assert controller.events[-1]["reason"] == "f_other_station"
    assert not controller.heuristic.committed[0]
    controller.transfers[0] = Transfer(0, 1, 300, 0)
    nearest[0] = 1
    controller._observe(np.zeros((8, 1)), 2)
    assert 0 in controller.transfers
    assert controller.heuristic.committed[0]
    controller._real_modes[0] = False
    distances[0] = 20
    controller._observe(np.zeros((8, 1)), 3)
    assert controller.transfers[0].arrival == 3
    controller._observe(np.zeros((8, 1)), 303)
    assert controller.transfers == {}
    assert controller.events[-1]["reason"] == "dwell"
    controller.transfers[1] = Transfer(1, 1, 120, 303)
    battery[1] = 1.0
    controller._observe(np.zeros((8, 1)), 304)
    assert controller.events[-1]["reason"] == "full"
    controller.transfers[2] = Transfer(2, 1, 120, 0)
    controller._observe(np.zeros((8, 1)), 900)
    assert controller.events[-1]["reason"] == "timeout_no_arrival"
    controller.transfers[3] = Transfer(3, 1, 300, 901)
    controller.finish(902, np.zeros((8, 1)), np.zeros(8, dtype=bool))
    assert controller.events[-1]["kind"] == "censored"
    assert controller.events[-1]["member"] == 3


def test_transfer_choice_command_and_combined_option_cap(monkeypatch):
    from types import SimpleNamespace
    from experiments.candidates.uav_persistent_service.b03 import controller as module
    from experiments.candidates.uav_persistent_service import controllers as parent_module

    controller = object.__new__(ReassignmentController)
    controller.options = {}
    controller.transfers = {}
    controller.events = []
    controller.diagnostics = []
    controller.macro_choices = 0
    controller.heuristic = SimpleNamespace(layout=object(), committed=np.zeros(8, dtype=bool))
    controller.feasibility_rejections = {"source_under_capacity": 1}
    candidate = (100., 0., 50, 0, 2, 1, .2, 1000., 40, [7, 1])
    controller._prepared = {"step": 0, "transfer_candidates": [candidate]}
    choice = controller.apply_choice(transfer_action(0, 2))
    assert choice["executed_action"] == transfer_action(0, 2)
    assert controller.diagnostics[-1] == choice
    assert len(controller.transfers) == 1 and not controller.options

    xyz = np.zeros((8, 3))
    xyz[:, 2] = 100
    stations = np.asarray([[0., 0., 100.], [1000., 0., 100.]])
    nearest = np.zeros(8, dtype=int)
    distances = np.full(8, 100.)
    vectors = np.zeros((8, 3))
    vectors[0, 0] = 100
    monkeypatch.setattr(parent_module.CommitmentController, "propose",
                        lambda *_: np.zeros((8, 4), dtype=np.float32))
    monkeypatch.setattr(module, "own_positions", lambda *_: xyz)
    monkeypatch.setattr(module, "station_records", lambda *_: {
        "xyz_m": np.repeat(stations[None, :, :], 8, axis=0)})
    monkeypatch.setattr(module, "decode_legal_observations", lambda *_: (
        np.zeros(8), np.zeros(8), nearest, distances, vectors))
    before = controller.propose(None, None, 0, None, np.zeros(8, dtype=bool))
    assert before[0, 0] > 0 and before[0, 3] == 0
    nearest[0] = 1
    after = controller.propose(None, None, 1, None, np.zeros(8, dtype=bool))
    assert np.array_equal(after[0], np.asarray([0, 0, 0, 1]))

    controller.options[1] = object()
    second = (100., 0., 50, 2, 0, 1, .2, 1000., 40, [7, 1])
    controller._prepared = {"step": 30, "transfer_candidates": [second]}
    rejected = controller.apply_choice(transfer_action(2, 0))
    assert rejected["executed_action"] == 0
    assert len(controller.options) + len(controller.transfers) == 2


def test_native_early_window_has_fixed_denominator_and_missing_final():
    length = 9001
    reward = np.ones(length)
    qos = np.ones(length)
    battery = np.ones((length, 8))*.2
    ends = np.zeros((length, 2), dtype=bool)
    ends[-1, 0] = True
    row = fixed_window_readings(reward, qos, battery, ends, battery[0])
    assert row["horizon_normalized_qos"] == pytest.approx(length/HORIZON)
    assert row["late6000_mission_qos"] == pytest.approx((length-6000)/6000)
    assert row["bins"][-1]["observed_steps"] == 1
    assert row["bins"][-1]["mission_qos"] == pytest.approx(1/3000)
    assert row["final300_persistent_reserve_members"] is None


def test_transfer_event_boundaries_and_free_recovery():
    arrays = {
        "native_post_xyz": np.zeros((6, 8, 3)),
        "native_pre_xyz": np.zeros((6, 8, 3)),
        "nearest_station": np.zeros((6, 8), dtype=int),
        "native_post_nearest_station": np.ones((6, 8), dtype=int),
        "charging": np.zeros((6, 8), dtype=bool),
        "native_charger_input_wh": np.zeros((6, 8)),
        "mode": np.zeros((6, 8), dtype=bool),
        "submitted": np.zeros((6, 8, 4)),
        "proposed": np.zeros((6, 8, 4)),
        "native_load": np.zeros((6, 8)),
        "commit_active": np.zeros((6, 8), dtype=bool),
    }
    arrays["commit_active"][:5, 0] = True
    arrays["native_load"][5, 0] = 1
    events = [
        {"kind": "start", "option_type": "transfer", "member": 0, "step": 0,
         "station": 1, "duration": 120},
        {"kind": "release", "option_type": "transfer", "member": 0, "step": 3,
         "reason": "full"},
        {"kind": "start", "option_type": "transfer", "member": 0, "step": 3,
         "station": 1, "duration": 120},
        {"kind": "arrival", "option_type": "transfer", "member": 0, "step": 4},
        {"kind": "release", "option_type": "transfer", "member": 0, "step": 5,
         "reason": "full"},
        {"kind": "assignment_restored", "member": 0, "step": 5},
    ]
    old, new = transfer_readings(arrays, events)
    assert (old["start"], old["stop"], old["free_followup_stop"]) == (0, 3, 3)
    assert old["assignment_restored"] is None
    assert old["post_release_connected_load"] is False
    assert (new["start"], new["stop"], new["first_decoded_arrival"]) == (3, 5, 4)
    assert new["assignment_restored"] == 5
    assert new["post_release_connected_load"] is True
    missing_release = [event for event in events if not (
        event["kind"] == "release" and event["step"] == 3)]
    bounded_old = transfer_readings(arrays, missing_release)[0]
    assert bounded_old["stop"] == 3
    assert bounded_old["end_kind"] == "partial"
    interleaved = events[:1] + [
        {"kind": "start", "option_type": "transfer", "member": 1, "step": 1,
         "station": 0, "duration": 120},
        {"kind": "arrival", "option_type": "transfer", "member": 1, "step": 2},
        {"kind": "release", "option_type": "transfer", "member": 1, "step": 2,
         "reason": "full"},
    ] + events[1:]
    first, other, restarted = transfer_readings(arrays, interleaved)
    assert first["member"] == 0 and first["stop"] == 3
    assert first["first_decoded_arrival"] is None
    assert other["member"] == 1 and other["stop"] == 2
    assert restarted["member"] == 0 and restarted["stop"] == 5


def test_fixed_job_plan_and_incomplete_contrasts():
    jobs = plan()
    assert len(jobs) == 24
    assert {job["seed"] for job in jobs} == set(SEEDS)
    assert {job["arm"] for job in jobs} == set(ARMS)
    assert len({job["job_key"] for job in jobs}) == 24
    assert summarize([])["status"] == "incomplete"
    rows = []
    for job in jobs:
        rows.append(job | {"status": "completed", "actual_length": HORIZON,
                           "terminal_zero_service": False,
                           "final300_persistent_reserve_members": 0,
                           **{field: 0.0 for field in CONTRAST_FIELDS}})
    assert summarize(rows)["contrasts"] == {}
    pairing = {seed: {"status": "verified"} for seed in SEEDS}
    complete = summarize(rows, pairing=pairing)
    assert complete["status"] == "complete"
    assert complete["contrasts"]["raw_native_J"]["R-O_H"]["ties"] == 8
    rows.pop()
    assert summarize(rows, pairing=pairing)["status"] == "incomplete"


def test_raw_prefix_pairing_detects_corruption(tmp_path):
    rows = {}
    for arm in ARMS:
        users = np.zeros((3, 30, 2))
        rng = np.asarray(["a"*64]*3, dtype="U64")
        ends = np.asarray([[False, False], [True, False]])
        path = tmp_path/f"{arm}.npz"
        np.savez(path, user_xy_m=users, rng_state_sha256_by_step=rng,
                 reward=np.zeros(2), ends=ends)
        decision = tmp_path/f"{arm}.json"
        decision.write_text("{}")
        rows[arm] = {"arm": arm, "seed": SEEDS[0], "actual_length": 2,
                     "initial_state_sha256": "a", "ground_bs_sha256": "b",
                     "user_xy_trace_sha256": "c"*64,
                     "rng_state_stream_sha256": "d"*64,
                     "raw_path": path.name,
                     "raw_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                     "decisions_path": decision.name,
                     "decisions_sha256": hashlib.sha256(decision.read_bytes()).hexdigest()}
    assert verify_pair(tmp_path, rows)["status"] == "verified"
    with np.load(tmp_path/"R.npz") as raw:
        users = raw["user_xy_m"].copy()
        rng = raw["rng_state_sha256_by_step"].copy()
        ends = raw["ends"].copy()
    users[1, 0, 0] = 1
    np.savez(tmp_path/"R.npz", user_xy_m=users, rng_state_sha256_by_step=rng,
             reward=np.zeros(2), ends=ends)
    rows["R"]["raw_sha256"] = hashlib.sha256((tmp_path/"R.npz").read_bytes()).hexdigest()
    assert verify_pair(tmp_path, rows)["reason"] == "exogenous_prefix"


def test_raw_prefix_checks_longer_pair_when_third_ends_early(tmp_path):
    rows = {}
    for arm in ARMS:
        length = 2 if arm == "R" else 4
        users = np.zeros((length+1, 30, 2))
        if arm == "O_H":
            users[3, 0, 0] = 1
        rng = np.asarray(["a"*64]*(length+1), dtype="U64")
        ends = np.zeros((length, 2), dtype=bool)
        ends[-1, 0] = True
        path = tmp_path/f"{arm}.npz"
        np.savez(path, user_xy_m=users, rng_state_sha256_by_step=rng,
                 reward=np.zeros(length), ends=ends)
        decision = tmp_path/f"{arm}.json"
        decision.write_text("{}")
        rows[arm] = {"arm": arm, "seed": SEEDS[0], "actual_length": length,
                     "initial_state_sha256": "a", "ground_bs_sha256": "b",
                     "user_xy_trace_sha256": "c"*64, "rng_state_stream_sha256": "d"*64,
                     "raw_path": path.name,
                     "raw_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                     "decisions_path": decision.name,
                     "decisions_sha256": hashlib.sha256(decision.read_bytes()).hexdigest()}
    result = verify_pair(tmp_path, rows)
    assert result["status"] == "failed"
    assert result["pairs"]["P-O_H"]["prefix_states"] == 5
    assert result["pairs"]["P-O_H"]["status"] == "failed"
    assert result["pairs"]["P-R"]["status"] == "verified"
    assert result["pairs"]["O_H-R"]["status"] == "verified"


def test_initial_controller_and_one_macro_each_native():
    # This is the sole native-transition test: 3 arms x exactly 30 one-second steps.
    episodes = []
    try:
        for arm in ARMS:
            episode = LongMissionEpisode(SEEDS[0], arm)
            episodes.append(episode)
            assert episode.t == 0
            assert episode.controller.heuristic.layout.max_steps == HORIZON
            if arm == "R":
                assert episode.controller.transfers == {}
                assert episode.controller.options == {}
            action = 0 if arm == "P" else episode.controller.ordinary_action()
            episode.macro_step(action)
            assert episode.t == 30
            arrays = episode.arrays()
            assert arrays["station_xyz"].shape == (30, 2, 3)
            assert arrays["native_eligible_station_count"].shape == (30, 2)
            assert arrays["native_station_target"].shape == (30, 8)
            assert arrays["native_station_request"].shape == (30, 8)
            assert np.array_equal(arrays["native_eligible_station_count"].sum(axis=1),
                                  arrays["native_charging_eligible"].sum(axis=1))
            assert np.allclose(arrays["native_station_input_wh"].sum(axis=1),
                               arrays["native_charger_input_wh"].sum(axis=1))
            assert arrays["rng_state_sha256_by_step"].shape == (31,)
            assert arrays["proposed"].shape == (30, 8, 4)
            assert arrays["submitted"].shape == (30, 8, 4)
        initial = [episode.pairing.digests()["initial_state_sha256"] for episode in episodes]
        assert len(set(initial)) == 1
        for left in episodes[1:]:
            assert np.array_equal(episodes[0].arrays()["user_xy_m"], left.arrays()["user_xy_m"])
            assert np.array_equal(episodes[0].arrays()["rng_state_sha256_by_step"],
                                  left.arrays()["rng_state_sha256_by_step"])
    finally:
        for episode in episodes:
            episode.close()
