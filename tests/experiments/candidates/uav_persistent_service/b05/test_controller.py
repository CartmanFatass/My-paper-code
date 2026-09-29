from collections import deque
from types import SimpleNamespace

import numpy as np

from experiments.candidates.uav_persistent_service.b05.controller import ServiceShiftController
from experiments.candidates.uav_persistent_service.b05.forecast import forecast
from experiments.candidates.uav_persistent_service.b03.controller import ReassignmentController
from experiments.candidates.uav_persistent_service.controllers import Commitment


def prepared():
    return {
        "step": 0, "features": np.zeros(1, dtype=np.float32),
        "transfer_candidates": [(.1, 0., 0., 2, 2, 1, .1, 700., 10., [5, 3])],
        "remaining": 1200, "margin": np.full(8, .1),
        "draw_w": np.full(8, 168.49), "station": np.zeros(8, dtype=int),
        "eligible": np.zeros(8, dtype=bool), "free": np.ones(8, dtype=bool),
        "tau_in": np.zeros(8), "tau_out": np.zeros(8),
    }


def test_transfer_alternatives_include_all_feasible_dwell_labels():
    controller = object.__new__(ServiceShiftController)
    controller._prepared = prepared()
    assert [item[4] for item in controller._transfer_alternatives()] == [0, 1, 2]


def test_transfer_can_defer_and_exact_tie_prefers_r(monkeypatch):
    controller = object.__new__(ServiceShiftController)
    controller._prepared = None
    controller.scheduler_snapshot_calls = 0
    controller.member_bin_updates = 0
    controller.forecast_grids = 0
    controller.options = {}
    controller.transfers = {}
    controller.heuristic = type("H", (), {"layout": object()})()
    monkeypatch.setattr(ReassignmentController, "prepare",
                        lambda self, observations, modes, step: setattr(self, "_prepared", prepared())
                        or self._prepared["features"])
    monkeypatch.setattr(ReassignmentController, "ordinary_action", lambda self: 31)
    monkeypatch.setattr("experiments.candidates.uav_persistent_service.b05.controller.own_energy",
                        lambda observations, layout: {"battery": np.full(8, .8),
                                                      "charging": np.zeros(8, dtype=bool)})
    monkeypatch.setattr("experiments.candidates.uav_persistent_service.b05.controller.own_positions",
                        lambda observations, layout: np.zeros((8, 3)))
    monkeypatch.setattr("experiments.candidates.uav_persistent_service.b05.controller.station_records",
                        lambda observations, layout: {"xyz_m": np.zeros((8, 2, 3))})
    monkeypatch.setattr("experiments.candidates.uav_persistent_service.b05.controller.decode_legal_observations",
                        lambda observations: (None, None, np.zeros(8, dtype=int), None, None))
    monkeypatch.setattr(ServiceShiftController, "_radio_weights",
                        lambda self, *args: (.8, np.ones(8)/8, np.zeros((8, 2))))
    monkeypatch.setattr(ServiceShiftController, "_forecast_input", lambda self, *args: type("V", (), {
        "xyz": np.zeros((8, 3)), "stations": np.zeros((2, 3)),
        "targets_xy": np.zeros((8, 2)), "battery": np.ones(8),
        "draw_w": np.ones(8), "weights": np.ones(8), "waiting": np.zeros(8),
        "slots": np.ones(2), "remaining": 1200,
    })())
    def fake_forecast(view, option):
        action_member = None if option is None else option.member
        minimum = .5 if action_member is None else .4
        return {"cutoff_ticks": 0, "depletion_ticks": 0, "min_qhat": minimum,
                "integral_qhat": 100., "reserve_ticks": 0, "grid_bins": 40,
                "member_bin_updates": 320, "release": [None]*8, "readiness": [None]*8,
                "qhat": [minimum]*40, "battery_min": [.5]*40}
    monkeypatch.setattr("experiments.candidates.uav_persistent_service.b05.controller.forecast",
                        fake_forecast)
    controller.prepare(None, np.zeros(8, dtype=bool), 0)
    assert controller.ordinary_action() == 0
    assert {31, 32, 33}.issubset(controller._prepared["scheduler"]["candidate_actions"])
    assert controller._prepared["scheduler"]["r_action"] == 31
    defer = controller._prepared["scheduler"]["defer"]
    assert defer["return_deadline_s"][2] > 300
    assert defer["transfer_candidates"][0] == {
        "member": 2, "duration": 120, "trip_energy_slack_s": .1,
        "next_clock_trip_energy_slack_s": .1-30,
        "next_clock_nominal_access": False,
    }
    assert defer["predicted_access_loss"]
    monkeypatch.setattr("experiments.candidates.uav_persistent_service.b05.controller.forecast",
                        lambda view, option: {**fake_forecast(view, option), "min_qhat": .5})
    controller._prepared = None
    controller.prepare(None, np.zeros(8, dtype=bool), 0)
    assert controller.ordinary_action() == 31


def test_charging_then_queued_without_strict_arrival_keeps_timeout(monkeypatch):
    from experiments.candidates.uav_persistent_service import controllers as base_module
    from experiments.candidates.uav_persistent_service.b03 import controller as r_module
    from experiments.candidates.uav_persistent_service.b05 import controller as s_module

    controller = object.__new__(ServiceShiftController)
    controller.heuristic = SimpleNamespace(layout=None, committed=np.zeros(8, bool))
    controller.options = {0: Commitment(0, 0, 120, 0),
                          1: Commitment(1, 1, 120, 0)}
    controller.transfers = {}
    controller._pending_restoration = set()
    controller.events = []
    controller._last_observed_step = None
    controller._battery_history = deque(maxlen=32)
    controller._real_modes = np.zeros(8, bool)
    controller._charged_without_decoded_arrival = set()
    controller._prepared = {"step": 30, "margin": np.full(8, .5),
                            "draw_w": np.full(8, 168.49), "remaining": 1200}
    controller.env = SimpleNamespace(env=SimpleNamespace(
        return_reserve_ratio=.1, service_cutoff_threshold=.02,
        emergency_return_threshold=.05))
    controller.limp_power_w = 168.49
    controller.max_power_w = 350.
    state = {"charging": True, "waiting": 0, "second_waiting": 0,
             "distance": 20.000001907}

    def energy(*_):
        charging = np.zeros(8, bool)
        charging[0] = state["charging"]
        waiting = np.zeros(8, int)
        waiting[0] = state["waiting"]
        waiting[1] = state["second_waiting"]
        return {"battery": np.full(8, .5), "charging": charging,
                "waiting_steps": waiting, "available": np.ones(8, bool),
                "return_margin": np.full(8, .5)}

    def decode(*_):
        distances = np.full(8, 100.)
        distances[:2] = state["distance"]
        nearest = np.zeros(8, int)
        nearest[1] = 1
        return (np.full(8, .5), np.full(8, .5), nearest,
                distances, np.zeros((8, 3)))

    xyz = np.c_[np.full(8, state["distance"]), np.zeros(8), np.full(8, 100.)]
    stations = np.array([[0., 0., 100.], [500., 0., 100.]])
    for module in (base_module, r_module, s_module):
        monkeypatch.setattr(module, "own_energy", energy)
        monkeypatch.setattr(module, "own_positions", lambda *_: xyz)
    for module in (base_module, r_module):
        monkeypatch.setattr(module, "decode_legal_observations", decode)
    monkeypatch.setattr(s_module, "station_records", lambda *_: {
        "xyz_m": np.repeat(stations[None, :, :], 8, axis=0),
        "capacity_ratio": np.zeros((8, 2)),
    })

    controller._observe(None, 0)
    assert controller.options[0].arrival is None
    assert ("ordinary", 0, 0) in controller._charged_without_decoded_arrival
    assert ("ordinary", 1, 0) not in controller._charged_without_decoded_arrival
    state.update(charging=False, waiting=1, second_waiting=1)
    controller._observe(None, 30)
    assert controller.options[0].arrival is None
    assert controller.options[1].arrival is None
    view = controller._forecast_input(None, np.zeros(8, bool), .8,
                                      np.zeros(8), np.c_[np.full(8, 300.), np.zeros(8)])
    assert all(option.observed_charging_without_arrival for option in view.options)
    assert forecast(view, None)["release"][:2] == [870, 870]
    state.update(waiting=0, second_waiting=0)
    controller._observe(None, 60)
    assert controller._charged_without_decoded_arrival == {
        ("ordinary", 0, 0), ("ordinary", 1, 0)}
    state["distance"] = 19.99
    controller._observe(None, 90)
    assert controller.options[0].arrival == 90
    assert controller.options[1].arrival == 90
    assert not controller._charged_without_decoded_arrival


def test_already_captured_ordinary_choice_has_zero_forecast_arrival_age(monkeypatch):
    from experiments.candidates.uav_persistent_service.b05 import controller as module

    controller = object.__new__(ServiceShiftController)
    controller._prepared = None
    controller.scheduler_snapshot_calls = controller.member_bin_updates = controller.forecast_grids = 0
    controller.heuristic = SimpleNamespace(layout=None)
    p = prepared()
    p["transfer_candidates"] = []
    p["distance"] = np.full(8, 100.)
    p["distance"][0] = 20.
    p["eligible"][0] = True
    monkeypatch.setattr(ReassignmentController, "prepare", lambda self, *_: setattr(
        self, "_prepared", p) or p["features"])
    monkeypatch.setattr(ReassignmentController, "ordinary_action", lambda self: 1)
    monkeypatch.setattr(ServiceShiftController, "_ordinary_alternatives", lambda self, modes: [1, 2, 3])
    monkeypatch.setattr(module, "own_energy", lambda *_: {"battery": np.full(8, .5)})
    monkeypatch.setattr(module, "own_positions", lambda *_: np.zeros((8, 3)))
    monkeypatch.setattr(module, "station_records", lambda *_: {"xyz_m": np.zeros((8, 2, 3))})
    monkeypatch.setattr(module, "decode_legal_observations", lambda *_: (
        None, None, np.zeros(8, int), None, None))
    monkeypatch.setattr(ServiceShiftController, "_radio_weights", lambda self, *_: (
        .8, np.zeros(8), np.zeros((8, 2))))
    view = SimpleNamespace(xyz=np.zeros((8, 3)), stations=np.zeros((2, 3)),
                           targets_xy=np.zeros((8, 2)), battery=np.ones(8),
                           draw_w=np.ones(8), weights=np.zeros(8), waiting=np.zeros(8),
                           slots=np.ones(2), remaining=1200)
    monkeypatch.setattr(ServiceShiftController, "_forecast_input", lambda self, *_: view)
    seen = []

    def score(_, option):
        if option is not None:
            seen.append((option.duration, option.arrival_age))
        return {"cutoff_ticks": 0, "depletion_ticks": 0, "min_qhat": .5,
                "integral_qhat": 100., "reserve_ticks": 0, "grid_bins": 40,
                "member_bin_updates": 320}

    monkeypatch.setattr(module, "forecast", score)
    controller.prepare(None, np.zeros(8, bool), 0)
    assert seen == [(120, 0), (300, 0), (600, 0)]
