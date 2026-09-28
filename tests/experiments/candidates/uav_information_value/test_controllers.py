from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.energy_relay_benchmark.b01.evaluation import HeuristicController
from experiments.candidates.energy_relay_benchmark.b01.heuristic import variant
from experiments.candidates.energy_relay_benchmark.b01.observation import S7S2_LAYOUT, user_records
from experiments.candidates.uav_information_value.controllers import (
    ARMS,
    _canonical_users,
    make_controller,
)


OWN_XY = [(700.0 + 330.0 * i, 900.0 + 190.0 * i) for i in range(8)]
USERS_XY = [(1000.0 + 850.0 * i, 5000.0 - 240.0 * i) for i in range(8)]
BS_XY = (700.0, 750.0)
STATION_XY = (6100.0, 6200.0)


def observations(users=USERS_XY, bs=BS_XY, own=OWN_XY, station=STATION_XY):
    obs = np.zeros((8, 365), dtype=np.float32)
    for uav in range(8):
        obs[uav, :2] = np.asarray(own[uav]) / 8000.0
        obs[uav, 2] = (100.0 - 50.0) / 150.0
        decoded_own = obs[uav, :2].astype(np.float64) * 8000.0
        for slot, user in enumerate(users):
            start = 11 + 6 * slot
            obs[uav, start:start + 2] = (np.asarray(user) - decoded_own) / 8000.0
            obs[uav, start + 4] = 1.0
        if bs is not None:
            obs[uav, 223:225] = (np.asarray(bs) - decoded_own) / 8000.0
            obs[uav, 226] = 1.0
        if station is not None:
            start = 357
            obs[uav, start:start + 2] = (np.asarray(station) - decoded_own) / 8000.0
            obs[uav, start + 7] = 1.0
    return obs


def propose(controller, obs, step, modes=None, state=None):
    if modes is None:
        modes = np.zeros(8, dtype=bool)
    return controller.propose(obs, state, step, np.zeros(1, dtype=bool), modes)


def test_already_canonical_legal_input_preserves_original_planner_search_and_hysteresis():
    original = HeuristicController(variant("H1", information="local"))
    local = make_controller("L", env=object())
    assert not hasattr(local, "env")
    frames = [observations(users=[], bs=None), observations(users=USERS_XY[:2]),
              observations(users=USERS_XY)]
    for frame in frames:
        # One observer supplies the sorted, separated hits: both input rules agree.
        frame[1:, S7S2_LAYOUT.users] = 0
    modes = np.zeros(8, dtype=bool)
    original.reset()
    local.reset()
    for step in range(65):
        if step == 30:
            modes[[1, 4]] = True
        if step == 60:
            modes[:] = False
        obs = frames[0 if step < 30 else 1 if step < 60 else 2]
        np.testing.assert_array_equal(propose(local, obs, step, modes, object()),
                                      propose(original, obs, step, modes, object()))
        np.testing.assert_array_equal(local.targets_xy, original.targets_xy)
        if step in (0, 30, 60):
            assert local.heuristic.last_plan["information"] == original.heuristic.last_plan["information"]
            for key in ("users", "bs_xy", "station_xy", "centroids", "counts",
                        "relays", "priority", "targets", "search_waypoints"):
                np.testing.assert_array_equal(local.heuristic.last_plan[key],
                                              original.heuristic.last_plan[key])
            assert local.heuristic.last_plan["search"] == original.heuristic.last_plan["search"]
    assert [row["call"] for row in local.diagnostics] == [0, 30, 60]
    assert [row["search"] for row in local.diagnostics] == [True, True, False]


def test_reference_is_original_central_controller():
    raw = SimpleNamespace(user_positions=np.asarray(USERS_XY, dtype=np.float64),
                          ground_bs_positions=np.asarray([BS_XY], dtype=np.float64))
    env = SimpleNamespace(env=raw)
    reference = make_controller("R", env)
    original = HeuristicController(variant("H1", information="central"), env)
    assert type(reference) is HeuristicController
    obs = observations(users=[], bs=None)
    for step in range(32):
        np.testing.assert_array_equal(propose(reference, obs, step),
                                      propose(original, obs, step))
        np.testing.assert_array_equal(reference.targets_xy, original.targets_xy)
    assert reference.plan_input_steps == [0, 30]


def test_equal_supplied_points_have_equal_assignments_and_fallback():
    # Unmerged legal hits are used as full truth, including exact float64 values.
    from experiments.candidates.energy_relay_benchmark.b01.heuristic import (
        observed_bs_xy,
    )

    for users, bs in (([], None), (USERS_XY[:2], BS_XY), (USERS_XY, BS_XY)):
        obs = observations(users=users, bs=bs)
        records = user_records(obs)
        truth = SimpleNamespace(user_positions=records["xy_m"][records["present"]],
                                ground_bs_positions=np.asarray([observed_bs_xy(
                                    obs, make_controller("L").heuristic.layout)]))
        if bs is None:
            # True BS is present in the simulator even when no legal BS slot exists.
            truth.ground_bs_positions = np.asarray([BS_XY], dtype=np.float64)
        controllers = {arm: make_controller(arm, truth) for arm in ("L", "U", "B", "F", "H_BS")}
        for arm, controller in controllers.items():
            propose(controller, obs, 0)
        same = ("L", "U", "B", "F", "H_BS") if bs is not None else ("L", "U", "H_BS")
        for arm in same[1:]:
            np.testing.assert_array_equal(controllers[arm].targets_xy, controllers[same[0]].targets_xy)
            assert controllers[arm].heuristic.last_plan["search"] == controllers[same[0]].heuristic.last_plan["search"]
        assert controllers["L"].diagnostics[0]["supplied_user_count"] == len(users)
        if bs is None:
            assert controllers["L"].heuristic.last_plan["bs_xy"] is None
            assert controllers["B"].heuristic.last_plan["bs_xy"] is not None


def test_near_neighbor_chain_has_one_common_merge_rule_for_all_sources():
    from experiments.candidates.energy_relay_benchmark.b01.heuristic import observed_bs_xy, pooled_users

    points = [(1000.4, 1000.0), (1000.0, 1000.0), (1000.8, 1000.0)]
    obs = observations(users=points)
    obs[1:, S7S2_LAYOUT.users] = 0
    records = user_records(obs)
    raw_points = records["xy_m"][records["present"]]
    assert len(pooled_users(obs, S7S2_LAYOUT, 0.5)) == 1
    assert len(_canonical_users(raw_points, 0.5)) == 2
    env = SimpleNamespace(user_positions=raw_points,
                          ground_bs_positions=np.asarray([observed_bs_xy(obs, S7S2_LAYOUT)]))
    controllers = [make_controller(arm, env) for arm in ("L", "U", "B", "F", "H_BS")]
    for controller in controllers:
        propose(controller, obs, 0)
        assert len(controller.heuristic.last_plan["users"]) == 2
        np.testing.assert_array_equal(controller.targets_xy, controllers[0].targets_xy)
    permuted = obs.copy()
    permuted[0, S7S2_LAYOUT.users] = obs[0, S7S2_LAYOUT.users].reshape(30, 6)[::-1].ravel()
    local = make_controller("L")
    propose(local, permuted, 0)
    np.testing.assert_array_equal(local.targets_xy, controllers[0].targets_xy)


def test_canonical_full_users_ignore_order_and_dedup_geometrically():
    points = np.asarray([[4000.0, 3000.0], [1000.0, 1000.0], [1000.4, 1000.0],
                         [2500.0, 2000.0], [2500.0, 2000.0]])
    expected = np.asarray([[1000.0, 1000.0], [2500.0, 2000.0], [4000.0, 3000.0]])
    for perm in (np.arange(len(points)), np.arange(len(points))[::-1], np.asarray([2, 4, 0, 3, 1])):
        np.testing.assert_array_equal(_canonical_users(points[perm], 0.5), expected)
    obs = observations(users=[])
    for arm in ("U", "F"):
        outputs = []
        for perm in (np.arange(len(points)), np.arange(len(points))[::-1]):
            raw = SimpleNamespace(user_positions=points[perm],
                                  ground_bs_positions=np.asarray([BS_XY]))
            controller = make_controller(arm, raw)
            propose(controller, obs, 0)
            outputs.append(controller.targets_xy)
        np.testing.assert_array_equal(*outputs)


class ReadOnceRaw:
    def __init__(self):
        self.user_reads = 0
        self.bs_reads = 0

    @property
    def user_positions(self):
        self.user_reads += 1
        return np.asarray(USERS_XY)

    @property
    def ground_bs_positions(self):
        self.bs_reads += 1
        return np.asarray([BS_XY])


def test_source_isolation_and_off_clock_true_reads():
    obs = observations(users=USERS_XY[:2], bs=None)
    for arm, expected in (("U", (2, 0)), ("B", (0, 2)), ("F", (2, 2))):
        raw = ReadOnceRaw()
        controller = make_controller(arm, raw)
        for step in range(31):
            propose(controller, obs, step, state=object())
        assert (raw.user_reads, raw.bs_reads) == expected
        assert controller.plan_input_steps == [0, 30]
    for arm in ("L", "H_BS"):
        controller = make_controller(arm, ReadOnceRaw())
        assert not hasattr(controller, "env")
        for step in range(31):
            propose(controller, obs, step, state=object())
        assert controller.plan_input_steps == []


def test_bs_memory_sees_intermediate_step_and_clears_on_reset():
    controller = make_controller("H_BS", env=object())
    absent = observations(users=USERS_XY[:2], bs=None)
    present = observations(users=USERS_XY[:2], bs=BS_XY)
    for step in range(31):
        propose(controller, present if step == 7 else absent, step, state=object())
    assert len(controller.diagnostics) == 2
    assert controller.diagnostics[0]["memory_used"] is False
    assert controller.diagnostics[0]["seen_bs_so_far"] is False
    assert controller.diagnostics[1]["memory_used"] is True
    assert controller.diagnostics[1]["current_bs_present"] is False
    assert controller.diagnostics[1]["seen_bs_so_far"] is True
    assert controller.heuristic.last_plan["bs_xy"] is not None
    controller.reset()
    propose(controller, absent, 0)
    assert controller.heuristic.last_plan["bs_xy"] is None
    assert controller.diagnostics[0]["seen_bs_so_far"] is False


def test_invalid_arm_and_missing_true_source():
    assert ARMS == ("L", "U", "B", "F", "R", "H_BS")
    with pytest.raises(ValueError, match="unknown arm"):
        make_controller("X")
    for arm in ("U", "B", "F", "R"):
        with pytest.raises(ValueError, match="environment"):
            make_controller(arm)
