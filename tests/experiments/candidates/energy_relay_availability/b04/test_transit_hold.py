from types import SimpleNamespace

import numpy as np

import experiments.candidates.energy_relay_availability.b04.transit_hold as transit_hold
import experiments.candidates.energy_relay_benchmark.b01.heuristic as h1
from experiments.candidates.energy_relay_availability.b04.transit_hold import (
    BASELINE_HOLD_ID,
    H1_CENTRAL_10,
    TransitHoldHeuristic,
    battery_tail_readings,
    choose_plan,
    hold_plan_candidates,
    project_h1_positions,
)
from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
    central_plan_inputs,
    make_eval_config,
)
from experiments.candidates.energy_relay_benchmark.b01.heuristic import LayoutHeuristic, variant
from experiments.candidates.energy_relay_benchmark.b01.observation import (
    own_energy,
    own_positions,
)
from experiments.candidates.uav_service_auxiliary.b01.native import make_env


def test_comparison_uses_exact_ten_step_replan_clock():
    assert H1_CENTRAL_10.record()["replan_period"] == 10
    heuristic = LayoutHeuristic(H1_CENTRAL_10)
    replans = []
    for step in range(31):
        heuristic.calls = step
        if heuristic.replans_next():
            replans.append(step)
    assert replans == [0, 10, 20, 30]


def test_battery_tail_fractions_use_inclusive_native_thresholds():
    readings = battery_tail_readings(
        np.asarray([[0.15, 0.10], [0.05, 0.02], [0.0, 0.11]]),
        reserve_ratio=0.10,
        service_cutoff_ratio=0.02,
    )
    assert readings["below_fixed_reserve_uav_step_fraction"] == 4.0 / 6.0
    assert readings["service_cutoff_uav_step_fraction"] == 2.0 / 6.0


def test_temporary_hold_preserves_h1_target_continuation_memory(monkeypatch):
    own = np.asarray([[600.0, 0.0, 100.0], [400.0, 0.0, 100.0]])
    monkeypatch.setattr(h1, "own_positions", lambda *_: own.copy())
    monkeypatch.setattr(transit_hold, "own_positions", lambda *_: own.copy())
    monkeypatch.setattr(transit_hold, "own_energy", lambda *_: {
        "available": np.ones(2, dtype=bool),
        "return_margin": np.ones(2),
        "battery": np.ones(2),
    })
    choices = iter([BASELINE_HOLD_ID, 0, BASELINE_HOLD_ID])
    monkeypatch.setattr(transit_hold, "choose_plan", lambda _: next(choices))
    monkeypatch.setattr(TransitHoldHeuristic, "_service_qos_at_snapshot",
                        staticmethod(lambda *_: 0.5))
    heuristic = TransitHoldHeuristic(
        variant("H1", n_uavs=2, n_service=1, information="central", replan_period=10),
        SimpleNamespace(routing_protocol="widest_path"),
    )
    observations = np.zeros((2, 365))
    modes = np.zeros(2, dtype=bool)
    inputs = {"users_xy": np.asarray([[1000.0, 0.0]]),
              "bs_xy": np.asarray([[-1000.0, 0.0]])}
    expected_h1 = np.asarray([[1000.0, 0.0], [0.0, 0.0]])
    np.testing.assert_array_equal(
        heuristic.plan(observations, modes, inputs)["targets"], expected_h1)

    # These identical later inputs keep the cross-assignment under H1's 300m
    # hysteresis. Treating the temporary hold at x=400 as its old target instead
    # switches the assignment, which is the unintended behavior this guards.
    own[:, 0] = [400.0, 600.0]
    heuristic.calls = 10
    held = heuristic.plan(observations, modes, inputs)
    np.testing.assert_array_equal(held["targets"][0], own[0, :2])
    heuristic.calls = 20
    resumed = heuristic.plan(observations, modes, inputs)
    np.testing.assert_array_equal(resumed["targets"], expected_h1)


def test_project_h1_positions_respects_speed_vertical_control_and_unavailable_members():
    own = np.asarray([[100.0, 100.0, 0.0], [900.0, 900.0, 100.0]])
    targets = np.asarray([[1000.0, 100.0], [0.0, 0.0]])
    projected = project_h1_positions(
        own, targets, np.asarray([True, False]), variant("H1"), 5, 8000.0
    )
    np.testing.assert_allclose(projected[0], [250.0, 100.0, 25.0])
    np.testing.assert_array_equal(projected[1], own[1])


def test_hold_candidates_are_ordered_and_exclude_shielded_or_unavailable_members():
    targets = np.asarray([[20.0, 10.0], [40.0, 30.0], [60.0, 50.0]])
    own = np.asarray([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    candidates = hold_plan_candidates(
        targets, own, np.asarray([True, True, False]), np.asarray([False, True, False])
    )
    assert [hold_id for hold_id, _ in candidates] == [BASELINE_HOLD_ID, 0]
    np.testing.assert_array_equal(candidates[0][1], targets)
    np.testing.assert_array_equal(candidates[1][1][0], own[0])
    np.testing.assert_array_equal(candidates[1][1][1:], targets[1:])


def test_strict_tie_keeps_all_move_baseline():
    assert choose_plan([(BASELINE_HOLD_ID, 0.5), (0, 0.5), (1, 0.49)]) == BASELINE_HOLD_ID
    assert choose_plan([(BASELINE_HOLD_ID, 0.5), (0, 0.5001)]) == 0


def test_native_snapshot_score_does_not_mutate_live_environment_or_rng():
    config = make_eval_config(20, policy_seed=0)
    env = make_env(config, 973001)
    try:
        observations, _ = env.reset(seed=973001)
        raw = env.env
        controller = TransitHoldHeuristic(variant("H1", information="central"), raw)
        plan_inputs = central_plan_inputs(env)
        own = own_positions(observations, controller.layout)
        batteries = own_energy(observations, controller.layout)["battery"]
        before_rng = raw.np_random.get_state()
        before_users = raw.user_positions.copy()
        before_uavs = raw.uav_positions.copy()
        before_connections = raw.connections.copy()
        before_routes = raw.routing_paths.copy()

        score = controller._service_qos_at_snapshot(raw, plan_inputs, own, batteries)

        assert 0.0 <= score <= 1.0
        np.testing.assert_array_equal(raw.user_positions, before_users)
        np.testing.assert_array_equal(raw.uav_positions, before_uavs)
        np.testing.assert_array_equal(raw.connections, before_connections)
        assert raw.routing_paths == before_routes
        after_rng = raw.np_random.get_state()
        assert before_rng[0] == after_rng[0]
        np.testing.assert_array_equal(before_rng[1], after_rng[1])
        assert before_rng[2:] == after_rng[2:]
    finally:
        env.close()
