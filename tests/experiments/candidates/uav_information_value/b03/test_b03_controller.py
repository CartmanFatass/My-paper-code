from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.energy_relay_benchmark.b01.observation import S7S2_LAYOUT, station_records
from experiments.candidates.uav_information_value.b03.batch import make_controller
from experiments.candidates.uav_information_value.b03.controller import station_zero_xy
from experiments.candidates.uav_information_value.b03.observer import AnchorObserver


def frame(stations=((7000.0, 500.0), (1000.0, 7000.0)), bs=None):
    obs = np.zeros((8, 365), dtype=np.float32)
    for uav in range(8):
        own = np.asarray((1000.0 + uav * 100, 900.0 + uav * 80), dtype=np.float64)
        obs[uav, :2] = own / 8000
        obs[uav, 2] = 1 / 3
        for slot in range(8):
            user = np.asarray((1400.0 + slot * 700, 4100.0 - slot * 170))
            base = 11 + slot * 6
            obs[uav, base:base + 2] = (user - own) / 8000
            obs[uav, base + 4] = 1
        if bs is not None:
            obs[uav, 223:225] = (np.asarray(bs) - own) / 8000
            obs[uav, 226] = 1
        for station_id, xy in enumerate(stations):
            if xy is not None:
                base = 349 + station_id * 8
                obs[uav, base:base + 2] = (np.asarray(xy) - own) / 8000
                obs[uav, base + 7] = 1
    return obs


class Poison:
    def __getattribute__(self, name):
        raise AssertionError(f"state read: {name}")


def propose(controller, obs, step):
    return controller.propose(obs, Poison(), step, Poison(), np.zeros(8, dtype=bool))


def test_station_zero_id_first_valid_and_reset_freeze():
    initial = frame()
    initial[0, 356] = 0
    decoded = station_records(initial, S7S2_LAYOUT)
    expected = decoded["xyz_m"][1, 0, :2]
    np.testing.assert_array_equal(station_zero_xy(initial, S7S2_LAYOUT), expected)
    controller = make_controller("S0_BS")
    before = initial.copy()
    propose(controller, initial, 0)
    np.testing.assert_array_equal(initial, before)
    np.testing.assert_array_equal(controller.prior_bs_xy, expected)
    for step in range(1, 31):
        propose(controller, frame(stations=((2000, 2000), (5000, 5000))), step)
    np.testing.assert_array_equal(controller.prior_bs_xy, expected)
    np.testing.assert_array_equal(controller.heuristic.last_plan["bs_xy"], expected)
    controller.reset()
    propose(controller, frame(stations=((2000, 2000), (5000, 5000))), 0)
    assert not np.array_equal(controller.prior_bs_xy, expected)


def test_nonfinite_first_station_zero_record_has_no_anchor():
    obs = frame()
    obs[0, 349] = np.nan
    assert station_zero_xy(obs, S7S2_LAYOUT) is None


def test_missing_station_zero_is_permanent_h_fallback_and_truth_supersedes():
    missing = frame(stations=(None, (1000, 7000)))
    later = frame()
    s0, h = make_controller("S0_BS"), make_controller("H_BS")
    for step in range(31):
        obs = missing if step == 0 else later
        np.testing.assert_array_equal(propose(s0, obs, step), propose(h, obs, step))
    assert s0.prior_bs_xy is None
    assert [r["bs_input_source"] for r in s0.diagnostics] == ["absent", "absent"]
    s0.reset()
    for step in range(61):
        obs = frame(bs=(3300, 5200)) if step == 7 else frame()
        propose(s0, obs, step)
    assert [r["bs_input_source"] for r in s0.diagnostics] == [
        "inferred", "observed-memory", "observed-memory"]
    assert s0.diagnostics[1]["prior_used"] is False


def test_common_service_plan_and_exact_relay_geometry():
    obs = frame()
    p, s0, h = (make_controller(arm) for arm in ("P_BS", "S0_BS", "H_BS"))
    for controller in (p, s0, h):
        propose(controller, obs, 0)
    pp, sp, hp = (controller.heuristic.last_plan for controller in (p, s0, h))
    np.testing.assert_array_equal(pp["centroids"], sp["centroids"])
    assert len(pp["relays"]) == len(sp["relays"]) == 2
    assert len(hp["relays"]) == 0
    for j in range(2):
        np.testing.assert_allclose(pp["relays"][j] - sp["relays"][j],
                                   (1 - (j + 1) / 3) * (p.prior_bs_xy - s0.prior_bs_xy), atol=1e-9)


def test_true_sighting_has_common_p_h_s0_action_parity():
    obs = frame(bs=(3300, 5200))
    controllers = [make_controller(arm) for arm in ("P_BS", "S0_BS", "H_BS")]
    for step in range(31):
        current = obs if step == 0 else frame()
        actions = [propose(controller, current, step) for controller in controllers]
        np.testing.assert_array_equal(actions[0], actions[1])
        np.testing.assert_array_equal(actions[1], actions[2])
        if step in (0, 30):
            plans = [controller.heuristic.last_plan for controller in controllers]
            for key in ("bs_xy", "centroids", "relays", "targets"):
                np.testing.assert_array_equal(plans[0][key], plans[1][key])
                np.testing.assert_array_equal(plans[1][key], plans[2][key])


@pytest.mark.parametrize("arm", ("P_BS", "S0_BS"))
@pytest.mark.parametrize("has_users,available,generated,assigned", (
    (False, 8, 0, 0), (True, 0, 2, 0), (True, 1, 2, 1), (True, 8, 2, 2),
))
def test_observer_separates_supplied_anchor_generation_assignment_and_movement(
        arm, has_users, available, generated, assigned):
    obs = frame()
    if not has_users:
        obs[:, 11:191] = 0
    modes = np.ones(8, dtype=bool)
    modes[:available] = False
    controller = make_controller(arm)
    raw = SimpleNamespace(uav_positions=np.zeros((8, 3)), uav_battery_ratios=np.ones(8))
    observer = AnchorObserver(arm, raw)
    with observer.attach(controller):
        actions = controller.propose(obs, Poison(), 0, Poison(), modes)
        observer.on_step(t=0, observations_t=obs, proposal_t=actions,
                         submitted_t=np.zeros_like(actions), controller=controller)
    row = observer.plans[0]
    assert row["bs_input_source"] == "inferred" and row["prior_used"]
    assert not row["bs_seen_so_far"]
    assert row["generated_relay_count"] == generated
    assert row["assigned_relay_count"] == assigned
    arrays = observer.arrays()
    np.testing.assert_array_equal(arrays["info_controller_proposal"][0], actions)
    assert not arrays["info_shield_submitted"].any()
    assert not arrays["info_native_delta_xyz"].any()
