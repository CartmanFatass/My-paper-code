from __future__ import annotations

import numpy as np
import pytest

from experiments.candidates.energy_relay_benchmark.b01 import heuristic as hz
from experiments.candidates.energy_relay_benchmark.b01.feedback import (
    PRODUCTION_PARAMS,
    apply_feedback_params,
)
from experiments.candidates.energy_relay_benchmark.b01.observation import (
    own_positions,
    station_records,
)
from experiments.candidates.uav_service_auxiliary.b01.native import make_env


def test_variants_and_estimator_kmeans_match_the_env_estimator(config_60):
    assert (hz.VARIANTS["H1"].n_service, hz.VARIANTS["H1"].n_relay) == (6, 2)
    assert (hz.VARIANTS["H2"].n_service, hz.VARIANTS["H2"].n_relay) == (5, 3)
    assert hz.VARIANTS["H3"].cruise_mps == 10.0 and hz.VARIANTS["H1"].cruise_mps == 30.0
    assert all(v.height_m == 100.0 and v.replan_period == 30 for v in hz.VARIANTS.values())
    assert all(v.information == "central" for v in hz.VARIANTS.values())
    assert hz.VARIANTS["H1"].record()["controller_information"] == "central-positions"
    with pytest.raises(ValueError, match="information"):
        hz.HeuristicParams(information="oracle")
    env = make_env(config_60, 952001)
    try:
        env.reset(seed=952001)
        raw = env.env
        users = raw.user_positions[:, :2].copy()
        bs = raw.ground_bs_positions[0, :2].copy()
        best = raw.estimate_heuristic_qos_feasibility()   # throwaway env: mutates positions
        service = best["service_uavs"]
        relay = raw.n_uavs - service
        centroids, counts = hz.estimator_kmeans(users, service, 30)
        np.testing.assert_array_equal(raw.uav_positions[relay:, :2], centroids)
        assert counts.sum() == len(users)
        centre = centroids.mean(axis=0)
        for index in range(relay):
            fraction = (index + 1) / (relay + 1)
            np.testing.assert_allclose(raw.uav_positions[index, :2],
                                       bs + fraction * (centre - bs), atol=1e-9)
    finally:
        env.close()


def test_local_plan_at_reset_sends_uavs_to_the_station_one_ring(config_60):
    env = make_env(config_60, 952001)
    try:
        obs, _ = env.reset(seed=952001)
        obs = np.asarray(obs, np.float32)
        raw = env.env
        station = raw.charging_station_positions[1, :2]
        decoded = station_records(obs)["xyz_m"][:, 1, :2]
        np.testing.assert_allclose(decoded, np.broadcast_to(station, decoded.shape), atol=0.05)
        controller = hz.LayoutHeuristic(hz.variant("H1", information="local"))
        plan = controller.plan(obs, np.zeros(8, bool))
    finally:
        env.close()
    assert len(plan["users"]) == 0 and plan["search"] is True    # nothing visible at reset
    assert plan["search_uavs"] == list(range(8)) and len(plan["priority"]) == 0
    np.testing.assert_allclose(plan["station_xy"], station, atol=0.05)
    ring = plan["search_waypoints"]
    np.testing.assert_allclose(ring, hz.search_ring(plan["station_xy"], 1000.0, 8))
    np.testing.assert_allclose(ring[0], plan["station_xy"] + (1000.0, 0.0))
    np.testing.assert_allclose(ring[2], plan["station_xy"] + (0.0, 1000.0), atol=1e-9)
    targets = controller.targets_xy
    np.testing.assert_allclose(np.linalg.norm(targets - station, axis=1), 1000.0, atol=0.1)
    # every ring point used exactly once, by the minimum-cost (nearest) assignment
    matches = [int(np.argmin(np.linalg.norm(ring - target, axis=1))) for target in targets]
    assert sorted(matches) == list(range(8))
    np.testing.assert_allclose(targets, ring[matches], atol=1e-9)
    own = own_positions(obs)[:, :2]
    cost = np.linalg.norm(own[:, None, :] - ring[None, :, :], axis=2)
    best = hz._assign(cost)
    assert np.isclose(sum(cost[r, c] for r, c in best), cost[np.arange(8), matches].sum())


def test_local_search_with_few_visible_users_and_unobserved_regime():
    station_obs = synthetic_observations([(1000.0 * i, 500.0) for i in range(8)],
                                         [(4000.0, 4000.0), (4100.0, 4000.0)], (500.0, 500.0),
                                         station=(6000.0, 6000.0))
    controller = hz.LayoutHeuristic(hz.HeuristicParams(information="local"))
    plan = controller.plan(station_obs, np.zeros(8, bool))
    # 2 visible users -> 2 centroids, a BS -> 2 relays, the other 4 UAVs search the ring.
    assert len(plan["centroids"]) == 2 and len(plan["relays"]) == 2
    assert plan["kinds"] == ["relay", "relay", "service", "service"]
    assert plan["search"] and len(plan["search_uavs"]) == 4
    searching = controller.targets_xy[plan["search_uavs"]]
    np.testing.assert_allclose(np.linalg.norm(searching - (6000.0, 6000.0), axis=1), 1000.0,
                               atol=0.1)
    assert np.isfinite(controller.targets_xy).all()
    # No BS: centroids but no relays; the rest search.
    no_bs = synthetic_observations([(1000.0 * i, 500.0) for i in range(8)],
                                   [(4000.0, 4000.0)], None, station=(6000.0, 6000.0))
    plan = hz.LayoutHeuristic(hz.HeuristicParams(information="local")).plan(no_bs, np.zeros(8, bool))
    assert len(plan["relays"]) == 0 and len(plan["centroids"]) == 1 and len(plan["search_uavs"]) == 7
    # Ring needed but station 1 not decodable, and neither BS nor station: UnobservedRegime.
    no_station = synthetic_observations([(1000.0 * i, 500.0) for i in range(8)],
                                        [(4000.0, 4000.0)], (500.0, 500.0))
    with pytest.raises(hz.UnobservedRegime, match="not decodable"):
        hz.LayoutHeuristic(hz.HeuristicParams(information="local")).plan(no_station, np.zeros(8, bool))
    nothing = synthetic_observations([(1000.0 * i, 500.0) for i in range(8)], [], None)
    with pytest.raises(hz.UnobservedRegime, match="no BS and no station"):
        hz.LayoutHeuristic(hz.HeuristicParams(information="local")).plan(nothing, np.zeros(8, bool))
    with pytest.raises(ValueError, match="unobserved"):
        hz.HeuristicParams(unobserved="hold")


def synthetic_observations(uav_xy, users_xy, bs_xy, station=None):
    """Legal-layout observations holding own xy, every user in slots, the BS (unless None)
    and, if given, station 1's xy in the energy suffix (station records otherwise invalid)."""
    obs = np.zeros((8, 365), dtype=np.float32)
    for uav in range(8):
        obs[uav, 0:2] = np.asarray(uav_xy[uav]) / 8000.0
        obs[uav, 2] = (100.0 - 50.0) / 150.0
        own = obs[uav, 0:2].astype(np.float64) * 8000.0
        for slot, user in enumerate(users_xy):
            base = 11 + 6 * slot
            obs[uav, base:base + 2] = (np.asarray(user) - own) / 8000.0
            obs[uav, base + 4] = 1.0
        if bs_xy is not None:
            obs[uav, 223:225] = (np.asarray(bs_xy) - own) / 8000.0
            obs[uav, 226] = 1.0
        if station is not None:
            base = 349 + 8   # station record 1
            obs[uav, base:base + 2] = (np.asarray(station) - own) / 8000.0
            obs[uav, base + 7] = 1.0
    return obs


def test_plan_priority_and_switch_hysteresis():
    params = hz.HeuristicParams(n_service=8, information="local")   # no relays: the two used targets are A, B
    a, b = np.asarray((3000.0, 2000.0)), np.asarray((2000.0, 2000.0))
    # Eight tight groups ordered by x so the estimator's index seeds land one per group:
    # B (3 users), six 3-user groups, A (4 users) -> priority A (4) then B (first of the 3s).
    groups = [(b, 3)] + [(np.asarray((2000.0 + 100 * i, 7000.0 - 1000 * i)), 3)
                         for i in range(1, 7)] + [(a, 4)]
    users = [centre + (0.0, 2.0 * k) for centre, size in groups for k in range(size)]
    bs = (500.0, 500.0)
    modes = np.ones(8, dtype=bool)
    modes[[0, 1]] = False
    far = np.asarray((2500.0, 3500.0))            # equidistant from A and B
    xy = [far] * 8
    xy[0], xy[1] = a + (0.0, 10.0), b + (0.0, 10.0)
    controller = hz.LayoutHeuristic(params)
    plan = controller.plan(synthetic_observations(xy, users, bs), modes)
    assert plan["counts"][np.argsort(-plan["counts"], kind="stable")][:2].tolist() == [4, 3]
    np.testing.assert_allclose(controller.targets_xy[0], a, atol=5.0)
    np.testing.assert_allclose(controller.targets_xy[1], b, atol=5.0)
    assert np.isnan(controller.targets_xy[2:]).all()          # unavailable: no target
    # UAV 0 now 700 m from A and 500 m from B (B closer by 200 < 300); UAV 1 equidistant.
    between = np.asarray((2380.0, 2000.0 + np.sqrt(250000.0 - 380.0 ** 2)))
    xy[0], xy[1] = between, far
    controller.plan(synthetic_observations(xy, users, bs), modes)
    np.testing.assert_allclose(controller.targets_xy[0], a, atol=5.0)
    # UAV 0 now 50 m from B (closer by 900 m > 300 m): swap.
    xy[0] = b - (50.0, 0.0)
    controller.plan(synthetic_observations(xy, users, bs), modes)
    np.testing.assert_allclose(controller.targets_xy[0], b, atol=5.0)
    np.testing.assert_allclose(controller.targets_xy[1], a, atol=5.0)
    # Without hysteresis a 200 m advantage would already swap.
    fresh = hz.LayoutHeuristic(hz.HeuristicParams(n_service=8, switch_margin_m=0.0,
                                                     information="local"))
    fresh.targets_xy[0], fresh.targets_xy[1] = a, b
    xy[0], xy[1] = between, far
    fresh.plan(synthetic_observations(xy, users, bs), modes)
    np.testing.assert_allclose(fresh.targets_xy[0], b, atol=5.0)


def test_observed_regime_24_steps_moves_toward_targets(config_60):
    """Test-only placement puts users and the BS inside the observation radius."""
    env = make_env(config_60, 953001)
    try:
        env.reset(seed=953001)
        raw = env.env
        positions = raw.uav_positions.copy()
        positions[:7, :2] = raw.user_positions[[0, 4, 8, 12, 16, 20, 24], :2] + 900.0
        positions[7, :2] = raw.ground_bs_positions[0, :2] + 700.0
        positions[:, 2] = 60.0
        raw.uav_positions = positions
        raw._update_global_bs_cache()
        obs = np.stack([raw._get_observation(f"uav_{i}")["obs"] for i in range(8)])
        controller = hz.LayoutHeuristic(hz.variant("H1", information="local"))
        modes = np.zeros(8, dtype=bool)
        start = None
        for step in range(24):
            actions = controller.act(obs, modes)
            assert actions.dtype == np.float32 and np.isfinite(actions).all()
            assert actions.min() >= -1.0 and actions.max() <= 1.0
            assert np.all(actions[:, 3] == 0.0)
            if start is None:
                targets = controller.targets_xy.copy()
                assert np.isfinite(targets).all()
                assert len(controller.last_plan["users"]) >= 10
                # >= n_service visible users and an observed BS: the ring is not used
                assert controller.last_plan["bs_xy"] is not None
                assert controller.last_plan["search"] is False
                assert controller.last_plan["search_uavs"] == []
                assert len(controller.last_plan["search_waypoints"]) == 0
                assert controller.last_plan["kinds"] == ["relay"] * 2 + ["service"] * 6
                np.testing.assert_array_equal(
                    np.sort(targets, axis=0), np.sort(controller.last_plan["priority"], axis=0))
                start = np.linalg.norm(own_positions(obs)[:, :2] - targets, axis=1)
            decision = apply_feedback_params(obs, actions, modes, PRODUCTION_PARAMS)
            modes = decision.modes
            obs, reward, terminated, truncated, _ = env.step(decision.submitted_actions)
            obs = np.asarray(obs, dtype=np.float32)
        end = np.linalg.norm(own_positions(obs)[:, :2] - targets, axis=1)
        assert not modes.any()
        moving = start > 1.0
        assert moving.any() and np.all(end[moving] < start[moving])
        assert np.all(np.abs(own_positions(obs)[:, 2] - 100.0) < np.abs(60.0 - 100.0))
    finally:
        env.close()


def test_greedy_fallback_matches_hysteresis_rule(monkeypatch):
    monkeypatch.setattr(hz, "_lsa", None)
    assert hz._assign(np.asarray([[500.0 - 300.0, 260.0]])) == [(0, 0)]
    assert hz._assign(np.asarray([[500.0 - 300.0, 150.0]])) == [(0, 1)]
    assert hz._assign(np.asarray([[1.0, 5.0], [2.0, 9.0]])) == [(0, 0), (1, 1)]
    test_plan_priority_and_switch_hysteresis()


def test_central_mode_requires_inputs_only_at_replans(live_frames):
    controller = hz.LayoutHeuristic(hz.VARIANTS["H1"])
    obs, modes = live_frames[0], np.zeros(8, dtype=bool)
    with pytest.raises(ValueError, match="requires plan_inputs"):
        controller.act(obs, modes)
    users = np.random.default_rng(3).uniform(0, 8000, size=(30, 2))
    inputs = {"users_xy": users, "bs_xy": np.asarray([[1000.0, 7000.0]])}
    controller.act(obs, modes, inputs)
    with pytest.raises(ValueError, match="only at replan"):
        controller.act(obs, modes, inputs)
    local = hz.LayoutHeuristic(hz.variant("H1", information="local"))
    with pytest.raises(ValueError, match="must not receive"):
        local.plan(obs, modes, inputs)
