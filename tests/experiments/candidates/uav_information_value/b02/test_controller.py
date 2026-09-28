from __future__ import annotations

import inspect

import numpy as np
import pytest

from experiments.candidates.energy_relay_benchmark.b01.observation import (
    S7S2_LAYOUT,
    station_records,
)
from experiments.candidates.uav_information_value.b02.controller import (
    StationPriorController,
    station_prior_bs_xy,
)
from experiments.candidates.uav_information_value.controllers import (
    PointSetHeuristic,
    canonical_legal_users,
    make_controller,
)
from experiments.candidates.energy_relay_benchmark.b01.heuristic import (
    UnobservedRegime,
    observed_bs_xy,
    variant,
)


USERS = [(1400.0 + i * 700.0, 4100.0 - i * 170.0) for i in range(8)]
S0 = (7000.0, 500.0)
S1 = (1000.0, 7000.0)
BS = (3300.0, 5200.0)


def set_station(obs, observer, station_id, xy, *, valid=True):
    own = obs[observer, :2].astype(np.float64) * 8000.0
    base = 349 + station_id * 8
    obs[observer, base:base + 2] = (np.asarray(xy) - own) / 8000.0
    obs[observer, base + 7] = float(valid)


def frame(*, stations=(S0, S1), bs=None, users=USERS):
    obs = np.zeros((8, 365), dtype=np.float32)
    for uav in range(8):
        obs[uav, :2] = (1000.0 + uav * 100.0, 900.0 + uav * 80.0)
        obs[uav, :2] /= 8000.0
        obs[uav, 2] = (100.0 - 50.0) / 150.0
        own = obs[uav, :2].astype(np.float64) * 8000.0
        for slot, user in enumerate(users):
            base = 11 + slot * 6
            obs[uav, base:base + 2] = (np.asarray(user) - own) / 8000.0
            obs[uav, base + 4] = 1.0
        if bs is not None:
            obs[uav, 223:225] = (np.asarray(bs) - own) / 8000.0
            obs[uav, 226] = 1.0
    for station_id, xy in enumerate(stations):
        if xy is not None:
            set_station(obs, 0, station_id, xy)
    return obs


def propose(controller, obs, step, modes=None):
    if modes is None:
        modes = np.zeros(8, dtype=bool)
    return controller.propose(obs, Poison(), step, Poison(), modes)


class Poison:
    def __getattribute__(self, name):
        raise AssertionError(f"state was accessed: {name}")

    def __array__(self, dtype=None):
        raise AssertionError("state was converted")


def test_station_ids_first_valid_observer_projection_and_copy():
    obs = frame(stations=(None, None))
    set_station(obs, 1, 0, S0)
    set_station(obs, 3, 1, S1)
    set_station(obs, 5, 0, (2000.0, 2000.0))
    set_station(obs, 6, 1, (3000.0, 3000.0))
    decoded = station_records(obs)
    expected = np.clip((decoded["xyz_m"][1, 0, :2] -
                        0.3 * decoded["xyz_m"][3, 1, :2]) / 0.7, 0.0, 8000.0)
    before = obs.copy()
    controller = StationPriorController()
    propose(controller, obs, 0)
    np.testing.assert_array_equal(obs, before)
    np.testing.assert_array_equal(controller.prior_bs_xy, expected)
    np.testing.assert_array_equal(controller.heuristic.last_plan["bs_xy"], expected)
    assert expected[0] == 8000.0 and expected[1] == 0.0
    exposed = controller.prior_bs_xy
    exposed[:] = -1.0
    np.testing.assert_array_equal(controller.prior_bs_xy, expected)
    assert controller.diagnostics[0]["bs_input_source"] == "inferred"
    assert controller.diagnostics[0]["prior_used"] is True
    assert controller.diagnostics[0]["seen_bs_so_far"] is False
    assert controller.diagnostics[0]["memory_used"] is False


def test_reset_prior_is_frozen_across_changed_station_records():
    initial = frame()
    changed = frame(stations=((2000.0, 2000.0), (5000.0, 5000.0)))
    controller = StationPriorController()
    propose(controller, initial, 0)
    prior = controller.prior_bs_xy
    for step in range(1, 31):
        propose(controller, changed, step)
    np.testing.assert_array_equal(controller.prior_bs_xy, prior)
    np.testing.assert_array_equal(controller.heuristic.last_plan["bs_xy"], prior)
    assert controller.diagnostics[1]["bs_input_source"] == "inferred"
    controller.reset()
    propose(controller, changed, 0)
    np.testing.assert_array_equal(controller.prior_bs_xy,
                                  station_prior_bs_xy(changed, S7S2_LAYOUT))
    assert not np.array_equal(controller.prior_bs_xy, prior)


def test_genuine_sighting_between_replans_permanently_supersedes_prior():
    absent = frame()
    first = frame(bs=BS)
    second = frame(bs=(2400.0, 6600.0))
    controller = StationPriorController()
    for step in range(61):
        obs = first if step == 7 else second if step == 31 else absent
        propose(controller, obs, step)
    assert [row["call"] for row in controller.diagnostics] == [0, 30, 60]
    assert [row["bs_input_source"] for row in controller.diagnostics] == [
        "inferred", "observed-memory", "observed-memory"]
    assert [row["memory_used"] for row in controller.diagnostics] == [False, True, True]
    assert [row["prior_used"] for row in controller.diagnostics] == [True, False, False]
    assert [row["seen_bs_so_far"] for row in controller.diagnostics] == [False, True, True]
    assert not np.array_equal(controller.heuristic.last_plan["bs_xy"], controller.prior_bs_xy)
    np.testing.assert_array_equal(controller.heuristic.last_plan["bs_xy"],
                                  observed_bs_xy(second, S7S2_LAYOUT))
    controller.reset()
    propose(controller, absent, 0)
    assert controller.diagnostics[0]["bs_input_source"] == "inferred"
    assert controller.diagnostics[0]["seen_bs_so_far"] is False


@pytest.mark.parametrize("stations", [(None, S1), (S0, None), (S0, (float("nan"), 10.0)),
                                     ((float("inf"), 10.0), S1)])
def test_missing_or_nonfinite_reset_station_has_no_prior(stations):
    obs = frame(stations=stations)
    modes = np.zeros(8, dtype=bool)
    modes[6:] = True  # no station ring is needed for this constructed missing-record case
    controller = StationPriorController()
    if stations[1] is None:
        assert station_prior_bs_xy(obs, S7S2_LAYOUT) is None
        with pytest.raises(UnobservedRegime):
            propose(controller, obs, 0, modes)
        with pytest.raises(UnobservedRegime):
            propose(make_controller("H_BS"), obs, 0, modes)
        assert controller.prior_bs_xy is None
        return
    propose(controller, obs, 0, modes)
    assert controller.prior_bs_xy is None
    assert controller.heuristic.last_plan["bs_xy"] is None
    assert controller.diagnostics[0]["bs_input_source"] == "absent"
    assert controller.diagnostics[0]["seen_bs_so_far"] is False
    assert controller.diagnostics[0]["prior_used"] is False
    assert controller.diagnostics[0]["memory_used"] is False


@pytest.mark.parametrize("has_current_bs", [True, False])
def test_off_path_exact_h_bs_action_target_parity(has_current_bs):
    obs = frame(bs=BS) if has_current_bs else frame(stations=(None, S1))
    absent = frame(stations=(None, S1)) if not has_current_bs else frame()
    proposed = StationPriorController()
    baseline = make_controller("H_BS")
    for step in range(31):
        current = obs if step == 0 else absent
        np.testing.assert_array_equal(propose(proposed, current, step),
                                      propose(baseline, current, step))
        np.testing.assert_array_equal(proposed.targets_xy, baseline.targets_xy)
        if step in (0, 30):
            for key in ("users", "bs_xy", "centroids", "relays", "priority", "targets"):
                np.testing.assert_array_equal(proposed.heuristic.last_plan[key],
                                              baseline.heuristic.last_plan[key])
    if has_current_bs:
        assert proposed.diagnostics[0]["bs_input_source"] == "observed-current"
        assert proposed.diagnostics[0]["memory_used"] is False
        assert proposed.diagnostics[0]["prior_used"] is False
        assert proposed.diagnostics[1]["bs_input_source"] == "observed-memory"
    else:
        assert [row["bs_input_source"] for row in proposed.diagnostics] == ["absent", "absent"]


def test_prior_uses_exact_common_point_set_planner_and_no_env_or_state():
    assert list(inspect.signature(StationPriorController).parameters) == []
    with pytest.raises(TypeError):
        StationPriorController(env=object())
    obs = frame()
    before = obs.copy()
    controller = StationPriorController()
    assert not hasattr(controller, "env")
    actions = propose(controller, obs, 0)
    np.testing.assert_array_equal(obs, before)
    planner = PointSetHeuristic(variant("H1", information="local"))
    users = canonical_legal_users(obs, planner.layout, planner.params.dedup_tolerance_m)
    expected = planner.act(obs, np.zeros(8, bool),
                           {"users_xy": users, "bs_xy": controller.prior_bs_xy})
    np.testing.assert_array_equal(actions, expected)
    np.testing.assert_array_equal(controller.targets_xy, planner.targets_xy)
    assert controller.diagnostics[0]["supplied_user_count"] == len(users)
    assert controller.diagnostics[0]["search"] == planner.last_plan["search"]
