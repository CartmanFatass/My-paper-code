from types import SimpleNamespace

import numpy as np
import pytest

import experiments.candidates.energy_relay_benchmark.b01.heuristic as h1
import experiments.candidates.uav_radio_placement.b01.placement as placement
from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
    central_plan_inputs, make_eval_config,
)
from experiments.candidates.energy_relay_benchmark.b01.heuristic import LayoutHeuristic
from experiments.candidates.energy_relay_benchmark.b01.observation import own_energy, own_positions
from experiments.candidates.uav_service_auxiliary.b01.native import make_env


def _fake_world(monkeypatch, *, own=None, F=None, available=None):
    if own is None:
        own = np.asarray([[100.0 + 300.0 * i, 100.0 + 200.0 * i, 100.0]
                          for i in range(8)])
    if F is None:
        F = np.zeros(8, dtype=bool)
    if available is None:
        available = np.ones(8, dtype=bool)
    users = np.asarray([[400.0 + 90.0 * i, 600.0 + 50.0 * (i % 5)] for i in range(30)])
    raw = SimpleNamespace(user_positions=np.column_stack((users, np.zeros(30))),
                          ground_bs_positions=np.asarray([[4000.0, 4000.0, 30.0]]))
    live, model = SimpleNamespace(env=raw), SimpleNamespace(env=object())
    monkeypatch.setattr(placement, "own_positions", lambda *_: own.copy())
    monkeypatch.setattr(h1, "own_positions", lambda *_: own.copy())
    monkeypatch.setattr(placement, "own_energy", lambda *_: {
        "battery": np.full(8, 0.5), "available": available, "charging": F,
    })
    return live, model, np.zeros((8, 365), dtype=np.float32), own, F


def test_geometric_best_of_eight_matches_original_first_solve_and_minimum_sse():
    users = np.asarray([[10.0 * i, float((i * 17) % 101)] for i in range(30)])
    centers, _, info = placement.best_geometric_centers(users)
    original, _ = placement.estimator_kmeans(users, 6, 30)
    np.testing.assert_array_equal(placement._lloyd(
        users, users[np.linspace(0, 29, 6, dtype=int)])[0], original)
    assert info["kmeans_solve_count"] == 8
    assert 8 <= info["kmeans_iteration_count"] <= 240
    assert info["kmeans_sse"] == min(info["kmeans_start_sse"])
    assert centers.shape == (6, 2)


def test_lloyd_preserves_empty_center_and_allclose_stop():
    users = np.asarray([[0.0, 0.0], [0.0, 0.0], [10.0, 0.0]])
    initial = np.asarray([[0.0, 0.0], [0.0, 0.0], [10.0, 0.0]])
    centers, counts, sse, iterations = placement._lloyd(users, initial)
    np.testing.assert_array_equal(centers, initial)
    np.testing.assert_array_equal(counts, [2, 0, 1])
    assert sse == 0.0 and iterations == 1


def test_h_proposal_is_original_h1_and_one_diagnostic_query(monkeypatch):
    live, model, obs, _, modes = _fake_world(monkeypatch)
    monkeypatch.setattr(placement.TransitHoldHeuristic, "_service_qos_at_snapshot",
                        staticmethod(lambda *_: 0.5))
    controller = placement.PlacementController("H", live, model)
    baseline = LayoutHeuristic(placement.PARAMS)
    expected = baseline.act(obs, modes, central_plan_inputs(live))
    actual = controller.propose(obs, None, 0, None, modes)
    np.testing.assert_array_equal(actual, expected)
    assert controller.decision_records[0]["query_count"] == 1
    assert controller.plan_input_steps == [0]
    for step in range(1, 31):
        actual = controller.propose(obs, None, step, None, modes)
        expected = baseline.act(obs, modes, central_plan_inputs(live) if step == 30 else None)
        np.testing.assert_array_equal(actual, expected)
    assert controller.plan_input_steps == [0, 30]


def test_r_full_query_bound_and_six_candidates_share_member_start(monkeypatch):
    live, model, obs, own, modes = _fake_world(monkeypatch)
    monkeypatch.setattr(placement.TransitHoldHeuristic, "_service_qos_at_snapshot",
                        staticmethod(lambda _raw, _inputs, layout, _battery: float(layout[0, 0] / 8000.0)))
    controller = placement.PlacementController("R", live, model)
    controller.propose(obs, None, 0, None, modes)
    record = controller.decision_records[0]
    assert record["query_count"] == 100
    assert len(record["candidates"]) == 100
    assert record["selected_qos"] >= max(record["initial_H_qos"], record["initial_G_qos"]) - 1e-10
    first_six = record["candidates"][4:10]
    for candidate in first_six:
        assert candidate["sweep"] == 0 and candidate["member"] == 0
    starting = np.asarray(record["candidates"][0]["targets_xyz"])
    # All six directions are based on the member-start incumbent, not earlier probes.
    winner_before = min(range(4), key=lambda i: (-record["candidates"][i]["score"],
                                                 record["candidates"][i]["travel_m"]))
    base = np.asarray(record["candidates"][winner_before]["targets_xyz"])
    for candidate in first_six:
        layout = np.asarray(candidate["targets_xyz"])
        np.testing.assert_array_equal(layout[1:], base[1:])
    assert np.isfinite(starting).all()


def test_r_f_members_fixed_but_cutoff_member_still_searched_and_clipped(monkeypatch):
    own = np.asarray([[8000.0, 8000.0, 200.0], [0.0, 0.0, 50.0]] +
                     [[1000.0 + i * 100.0, 1000.0, 100.0] for i in range(6)])
    F = np.asarray([False, True] + [False] * 6)
    available = np.asarray([True, False, False] + [True] * 5)
    live, model, obs, _, _ = _fake_world(monkeypatch, own=own, F=F, available=available)
    monkeypatch.setattr(placement.TransitHoldHeuristic, "_service_qos_at_snapshot",
                        staticmethod(lambda *_: 0.5))
    controller = placement.PlacementController("R", live, model)
    controller.propose(obs, None, 0, None, F)
    record = controller.decision_records[0]
    assert record["query_count"] == 88
    assert all(np.array_equal(np.asarray(c["targets_xyz"])[1], own[1])
               for c in record["candidates"])
    assert any(c["member"] == 2 for c in record["candidates"])
    assert all(np.asarray(c["targets_xyz"])[0, 0] <= 8000.0
               for c in record["candidates"])
    assert not np.isnan(np.asarray(record["candidates"][-1]["targets_xyz"])).any()


def test_fixed_service_tolerance_prefers_shorter_travel_then_incumbent():
    assert placement._better(0.5 + 0.5e-10, 10.0, 0.5, 11.0)
    assert not placement._better(0.5 + 0.5e-10, 11.0, 0.5, 11.0)
    assert placement._better(0.5 + 2e-10, 100.0, 0.5, 0.0)
    assert not placement._better(0.5, 10.0 - 0.5e-6, 0.5, 10.0)


def test_xyz_executor_equals_h1_when_targets_are_at_100m(monkeypatch):
    live, model, obs, _, modes = _fake_world(monkeypatch)
    original = LayoutHeuristic(placement.PARAMS)
    original_action = original.act(obs, modes, central_plan_inputs(live))
    controller = placement.PlacementController("R", live, model)
    controller.targets_xyz = np.column_stack((original.targets_xy, np.full(8, 100.0)))
    np.testing.assert_array_equal(controller._actions(obs), original_action)


def test_model_is_separate_and_native_score_keeps_live_state(monkeypatch):
    config = make_eval_config(20, policy_seed=0)
    live, model = make_env(config, 973711), make_env(config, 0)
    try:
        live_obs, _ = live.reset(seed=973711)
        model.reset(seed=0)
        with pytest.raises(ValueError, match="separate"):
            placement.PlacementController("H", live, live)
        raw = live.env
        before_users = raw.user_positions.copy()
        before_uavs = raw.uav_positions.copy()
        before_rng = raw.np_random.get_state()
        before_connections = raw.connections.copy()
        controller = placement.PlacementController("H", live, model)
        controller.propose(live_obs, None, 0, None, np.zeros(8, dtype=bool))
        record = controller.decision_records[0]
        scored = np.asarray(record["candidates"][0]["targets_xyz"])
        parity = placement.TransitHoldHeuristic._service_qos_at_snapshot(
            model.env, central_plan_inputs(live), scored,
            own_energy(live_obs)["battery"])
        assert record["selected_qos"] == parity
        assert model.env._communication_unavailable_mask().tolist() == [False] * 8
        model.env.uav_battery_ratios[0] = model.env.service_cutoff_threshold
        assert model.env._communication_unavailable_mask()[0]
        model.env.uav_battery_ratios[0] = 0.5
        model.env.uav_charging[0] = True
        assert not model.env._communication_unavailable_mask()[0]
        np.testing.assert_array_equal(raw.user_positions, before_users)
        np.testing.assert_array_equal(raw.uav_positions, before_uavs)
        np.testing.assert_array_equal(raw.connections, before_connections)
        assert raw.np_random.get_state()[1].tolist() == before_rng[1].tolist()
    finally:
        live.close()
        model.close()
