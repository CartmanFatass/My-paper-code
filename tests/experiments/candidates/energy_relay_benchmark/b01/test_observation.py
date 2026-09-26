from __future__ import annotations

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01 import observation as ob
from experiments.candidates.uav_service_auxiliary.b01.native import make_env

ATOL_M = 0.05  # float32 normalisation rounding at 8000 m scale


def expected_users(raw, uav):
    own = raw.uav_positions[uav]
    distances = np.linalg.norm(raw.user_positions - own, axis=1)
    inside = [(d, idx) for idx, d in enumerate(distances) if d <= raw.observation_radius]
    return [idx for _, idx in sorted(inside)][: raw.max_observed_users]


def check_frame(obs, raw):
    layout = ob.S7S2_LAYOUT
    np.testing.assert_allclose(ob.own_positions(obs), raw.uav_positions, atol=ATOL_M)
    stations = ob.station_records(obs)
    for observer in range(8):
        np.testing.assert_allclose(stations["xyz_m"][observer], raw.charging_station_positions,
                                   atol=ATOL_M)
        np.testing.assert_allclose(ob.energy_uav_positions(obs)[observer], raw.uav_positions,
                                   atol=ATOL_M)
    assert stations["valid"].all()
    users = ob.user_records(obs)
    bs = ob.bs_records(obs)
    seen_users = seen_bs = 0
    for uav in range(8):
        indices = expected_users(raw, uav)
        present = np.flatnonzero(users["present"][uav])
        np.testing.assert_array_equal(present, np.arange(len(indices)))
        np.testing.assert_allclose(users["xy_m"][uav, : len(indices)],
                                   raw.user_positions[indices, :2], atol=ATOL_M)
        seen_users += len(indices)
        local = [idx for idx, _ in raw._get_local_bs(uav)]
        cached = [idx for idx in raw.global_bs_cache if idx not in local]
        expected_bs = (local + cached)[: layout.bs_slots]
        np.testing.assert_array_equal(np.flatnonzero(bs["present"][uav]),
                                      np.arange(len(expected_bs)))
        np.testing.assert_allclose(bs["xyz_m"][uav, : len(expected_bs), :2],
                                   raw.ground_bs_positions[expected_bs, :2], atol=ATOL_M)
        seen_bs += len(expected_bs)
    own = ob.own_energy(obs, ob.layout_from_env(raw))
    np.testing.assert_allclose(own["battery"], raw.uav_battery_ratios, atol=1e-6)
    np.testing.assert_array_equal(own["charging"], raw.uav_charging)
    np.testing.assert_array_equal(own["waiting_steps"], raw.charging_wait_steps)
    np.testing.assert_allclose(own["return_margin"], raw.uav_return_energy_margins, atol=1e-6)
    return seen_users, seen_bs


def test_layout_is_derived_from_the_live_env(config_60):
    env = make_env(config_60, 952001)
    try:
        obs, _ = env.reset(seed=952001)
        raw = env.env
        layout = ob.layout_from_env(raw)
        assert layout.dim == 365 == obs.shape[1]
        assert (layout.user_fields, raw.enable_soft_handover, raw.predictive_handover) == (6, True, False)
        assert layout.max_steps == 60  # the fixture horizon; S7S2_LAYOUT pins 3000
        assert layout == ob.ObservationLayout(max_steps=60)
        assert ob.S7S2_LAYOUT.offsets() == {
            "own": [0, 3], "nearest_uav": [3, 6], "self_state": [6, 11], "users": [11, 191],
            "uavs": [191, 223], "bs": [223, 235], "overloaded": [235, 244],
            "energy_uavs": [245, 349], "energy_stations": [349, 365], "step": [244, 245],
            "dim": [0, 365]}
        for index in range(8):
            np.testing.assert_array_equal(obs[index], raw._get_observation(f"uav_{index}")["obs"])
    finally:
        env.close()


def test_decode_matches_env_on_three_real_steps(config_60):
    env = make_env(config_60, 952001)
    try:
        obs, _ = env.reset(seed=952001)
        raw = env.env
        layout = ob.layout_from_env(raw)
        assert layout == ob.ObservationLayout(max_steps=60)
        check_frame(obs, raw)
        for step in range(3):
            action = np.zeros((8, 4), dtype=np.float32)
            action[:, 0] = -1.0
            obs, *_ = env.step(action)
            assert np.isclose(obs[0, ob.S7S2_LAYOUT.step], (step + 1) / 60)
            check_frame(obs, raw)
    finally:
        env.close()


def test_decode_users_and_bs_when_observed(config_60):
    """Test-only placement so the radius-gated user/BS slots are populated."""
    env = make_env(config_60, 952001)
    try:
        env.reset(seed=952001)
        raw = env.env
        positions = raw.uav_positions.copy()
        positions[:6, :2] = raw.user_positions[[0, 5, 10, 15, 20, 25], :2] + 200.0
        positions[6, :2] = raw.ground_bs_positions[0, :2] + 300.0
        positions[7, :2] = raw.user_positions[3, :2] - 400.0
        positions[:, 2] = 100.0
        raw.uav_positions = positions
        raw._update_global_bs_cache()   # UAV 6 sees the BS; everyone else reads the cache
        obs = np.stack([raw._get_observation(f"uav_{i}")["obs"] for i in range(8)])
        seen_users, seen_bs = check_frame(obs, raw)
        assert seen_users >= 20 and seen_bs == 8
    finally:
        env.close()
