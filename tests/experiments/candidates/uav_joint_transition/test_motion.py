from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.energy_relay_availability.b04.transit_hold import TransitHoldHeuristic
from experiments.candidates.uav_radio_placement.b01.placement import PlacementController
from experiments.candidates.uav_joint_transition.controllers import FEATURE_DIM, TransitionController
from experiments.candidates.uav_joint_transition.motion import forecast, legal_start, waypoints


class Model:
    time_step = 1.0
    max_speed = 30.0
    limp_home_speed_mps = 3.0
    battery_capacity_wh = 160.0
    return_reserve_ratio = 0.1
    emergency_return_threshold = 0.05
    service_cutoff_threshold = 0.02
    charging_radius_m = 160.0
    charging_capture_radius_m = 20.0
    charging_hover_speed_threshold = 1.0
    docking_horizontal_speed_mps = 3.0
    docking_vertical_speed_mps = 1.0
    charging_power_w = 1000.0
    return_margin_scale = 0.05
    return_cost_cap = 1.0
    lambda_return = 2.0

    @staticmethod
    def _calculate_power_consumption(horizontal, vertical):
        return np.zeros_like(horizontal, dtype=np.float64)


def start(*, battery=0.8, margin=0.7):
    xyz = np.column_stack((np.arange(8) * 500.0 + 100.0,
                           np.full(8, 100.0), np.full(8, 100.0)))
    return {"xyz": xyz, "battery": np.full(8, battery),
            "margin": np.full(8, margin), "available": np.ones(8, dtype=bool),
            "charging": np.zeros(8, dtype=bool), "waits": np.zeros(8, dtype=np.int64),
            "stations": np.array([[100.0, 100.0, 100.0], [7000.0, 7000.0, 100.0]]),
            "capacity": np.array([1, 1])}


def legal_obs(s, margin=None):
    obs = np.zeros((8, 365), dtype=np.float32)
    obs[:, :2] = s["xyz"][:, :2] / 8000.0
    obs[:, 2] = (s["xyz"][:, 2] - 50.0) / 150.0
    for i in range(8):
        own = 245 + 13 * i
        obs[i, own + 3] = s["battery"][i]
        obs[i, own + 5] = s["available"][i]
        obs[i, own + 10] = s["waits"][i] / 3000.0
        obs[i, own + 12] = s["margin"][i] if margin is None else margin[i]
        for station in range(2):
            offset = 349 + 8 * station
            rel = s["stations"][station] - s["xyz"][i]
            obs[i, offset:offset + 2] = rel[:2] / 8000.0
            obs[i, offset + 2] = rel[2] / 150.0
            obs[i, offset + 4] = 1.0 / 8.0
            obs[i, offset + 7] = 1.0
    return obs


def test_joint_modes_and_waypoints():
    s = start()
    target = s["xyz"].copy()
    target[:, 0] += 900.0
    intermediate = waypoints(s["xyz"], target)
    np.testing.assert_allclose(intermediate[0, 0], [550.0, 250.0, 100.0])
    np.testing.assert_allclose(intermediate[1, 0], [550.0, 0.0, 100.0])
    np.testing.assert_allclose(intermediate[1, 0, 1], 0.0)
    modes = np.array([0, 1, 2, 3, 0, 0, 0, 0])
    result = forecast(s, target, modes, np.zeros(8, dtype=bool), Model())
    assert result.xyz[0, 0, 0] > s["xyz"][0, 0]
    assert result.xyz[0, 1, 0] == s["xyz"][1, 0]
    assert result.xyz[0, 2, 1] > s["xyz"][2, 1]
    assert result.xyz[0, 3, 1] < s["xyz"][3, 1]
    assert result.xyz[2, 1, 0] > s["xyz"][1, 0]


def test_dock_priority_waits_and_cancellation_release():
    s = start()
    s["xyz"][0] = s["stations"][0]
    s["xyz"][1] = s["stations"][0]
    s["battery"][0] = 0.2
    s["battery"][1] = 0.3
    s["margin"][0] = -0.01
    s["margin"][1] = -0.01
    target = s["xyz"].copy()
    target[:, 0] += 900.0
    high_reserve = Model()
    high_reserve.return_reserve_ratio = 0.4
    result = forecast(s, target, np.array([2, 2, 0, 0, 0, 0, 0, 0]),
                      np.zeros(8, dtype=bool), high_reserve)
    assert result.cancelled[:2].all()
    assert result.crossed_F[:2].all()
    assert result.battery[-1, 0] > 0.2
    assert result.battery[-1, 1] == pytest.approx(0.3)
    assert result.waits[-1, 1] == 30
    assert result.F[-1, 0]
    released = forecast(s, target, np.array([2, 2, 0, 0, 0, 0, 0, 0]),
                        np.zeros(8, dtype=bool), Model())
    assert not released.F[-1, 0]
    assert released.cancelled[0]
    assert released.xyz[-1, 0, 0] > s["xyz"][0, 0]


def test_zero_battery_immobile_but_cutoff_member_limp_moves():
    s = start()
    s["battery"][0] = 0.0
    s["battery"][1] = 0.015
    s["margin"][:2] = -0.2
    s["xyz"][0] = [2000.0, 2000.0, 100.0]
    s["xyz"][1] = [2500.0, 2500.0, 100.0]
    target = s["xyz"].copy()
    target[:, 0] += 900.0
    result = forecast(s, target, np.zeros(8, dtype=np.int64),
                      np.zeros(8, dtype=bool), Model())
    np.testing.assert_array_equal(result.xyz[-1, 0], s["xyz"][0])
    assert np.linalg.norm(result.xyz[-1, 1] - s["xyz"][1]) > 0.0


def test_F_station_command_uses_common_xy_z_duration():
    s = start()
    s["xyz"][0] = [2000.0, 2000.0, 50.0]
    s["margin"][0] = -0.2
    model = Model()
    model.return_reserve_ratio = 1.0
    result = forecast(s, s["xyz"].copy(), np.zeros(8, dtype=np.int64),
                      np.zeros(8, dtype=bool), model)
    displacement = result.xyz[0, 0] - s["xyz"][0]
    assert result.F[0, 0]
    np.testing.assert_allclose(displacement[2] / displacement[0], 50.0 / -1900.0,
                               rtol=1e-6)
    assert 0.0 < displacement[2] < 10.0


def test_direct_identity_and_prior_F_at_clock(monkeypatch):
    monkeypatch.setattr(TransitHoldHeuristic, "_service_qos_at_snapshot",
                        staticmethod(lambda *args: 0.5))
    s = start()
    s["margin"][0] = -0.01  # Entry happens after R receives the prior false F at clock zero.
    obs = legal_obs(s)
    users = np.column_stack((np.linspace(100, 7000, 30), np.linspace(200, 6000, 30)))
    env = SimpleNamespace(user_positions=users, ground_bs_positions=np.array([[4000.0, 4000.0]]))
    model = Model()
    direct = PlacementController("R", env, model)
    transition = TransitionController("L", env, model)
    prior = np.zeros(8, dtype=bool)
    for step in range(31):
        if step == 30:
            prior[0] = True
            obs = legal_obs(s, margin=np.full(8, 0.2))
        if step % 30 == 0:
            features = transition.prepare_clock(obs, prior, step)
            assert features.shape == (FEATURE_DIM,)
            assert features.dtype == np.float32
            assert features[0] == (0.0 if step == 30 else 1.0)
            transition.set_modes(np.zeros(8, dtype=np.int64))
        expected = direct.propose(obs, None, step, None, prior)
        observed = transition.propose(obs, None, step, None, prior)
        np.testing.assert_array_equal(observed, expected)
    assert transition.source._calls == 31
    assert transition.work_counts()["destination_snapshot_calls"] == direct.snapshot_calls_started


def test_phase_and_F_entry_cancel(monkeypatch):
    monkeypatch.setattr(TransitHoldHeuristic, "_service_qos_at_snapshot",
                        staticmethod(lambda *args: 0.5))
    s = start()
    users = np.column_stack((np.linspace(100, 7000, 30), np.linspace(200, 6000, 30)))
    env = SimpleNamespace(user_positions=users, ground_bs_positions=np.array([[4000.0, 4000.0]]))
    direct = PlacementController("R", env, Model())
    transition = TransitionController("L", env, Model())
    prior = np.zeros(8, dtype=bool)
    obs = legal_obs(s)
    transition.prepare_clock(obs, prior, 0)
    transition.set_modes(np.array([1, 0, 0, 0, 0, 0, 0, 0], dtype=np.int64))
    for step in range(16):
        if step == 1:
            s["xyz"][0, 0] += 20.0
            obs = legal_obs(s)
        base = direct.propose(obs, None, step, None, prior)
        actual = transition.propose(obs, None, step, None, prior)
        if step == 0:
            np.testing.assert_array_equal(actual[0], np.zeros(4, dtype=np.float32))
        elif step < 15:
            np.testing.assert_allclose(actual[0], [-20.0 / 30.0, 0.0, 0.0, 0.0], atol=1e-7)
        else:
            np.testing.assert_array_equal(actual, base)
    assert not transition.decision_records[0]["cancelled_members"].any()

    direct.reset()
    transition.reset()
    s["margin"][0] = -0.01
    obs = legal_obs(s)
    transition.prepare_clock(obs, prior, 0)
    transition.set_modes(np.array([2, 0, 0, 0, 0, 0, 0, 0], dtype=np.int64))
    for step in range(2):
        if step == 1:
            prior[0] = True
            obs = legal_obs(s, margin=np.full(8, 0.2))
        base = direct.propose(obs, None, step, None, prior)
        actual = transition.propose(obs, None, step, None, prior)
        np.testing.assert_array_equal(actual, base)
    assert transition.decision_records[0]["cancelled_members"][0]
    assert transition.decision_records[0]["cancelled_member_ticks"][0] == 2


def test_ordinary_bound_and_model_coupling(monkeypatch):
    monkeypatch.setattr(TransitHoldHeuristic, "_service_qos_at_snapshot",
                        staticmethod(lambda *args: 0.5))
    s = start()
    obs = legal_obs(s)
    users = np.column_stack((np.linspace(100, 7000, 30), np.linspace(200, 6000, 30)))
    env = SimpleNamespace(user_positions=users, ground_bs_positions=np.array([[4000.0, 4000.0]]))
    controller = TransitionController("O", env, Model())
    features = controller.prepare_clock(obs, np.zeros(8, dtype=bool), 0)
    assert features.shape == (FEATURE_DIM,)
    controller.propose(obs, None, 0, None, np.zeros(8, dtype=bool))
    record = controller.decision_records[0]
    assert record["feature_forecasts"] == 25
    assert record["candidate_count"] == 161
    assert controller.work_counts()["transition_snapshot_calls"] == 483
    assert controller.work_counts()["prediction_team_ticks"] == (25 + 161) * 30
