from __future__ import annotations

import numpy as np
import pytest

from experiments.candidates.energy_relay_benchmark.b01.observation import S7S2_LAYOUT
from experiments.candidates.energy_relay_benchmark.b01.evaluation import make_eval_config
from experiments.candidates.uav_geometric_generalization.b01.symmetry import (
    D4,
    get_transform,
    inverse_actions,
    transform_actions,
    transform_observations,
    transform_state,
)
from experiments.candidates.uav_service_auxiliary.b01.native import make_env


def _apply_xy(values, transform, *, absolute=False):
    """Independent signed-permutation oracle for one or more xy pairs."""
    original = np.asarray(values)
    matrix = np.asarray(transform.matrix)
    result = np.einsum("ij,...j->...i", matrix, original)
    return result + (1 - matrix.sum(axis=1)) / 2 if absolute else result


def _observation_xy_indices():
    layout = S7S2_LAYOUT
    indices = [0, 1, 4, 5, 9, 10]
    for section, slots, fields in (
        (layout.users, layout.user_slots, layout.user_fields),
        (layout.uavs, layout.uav_slots, layout.uav_fields),
        (layout.bs, layout.bs_slots, layout.bs_fields),
        (layout.overloaded, layout.overloaded_slots, layout.overloaded_fields),
        (layout.energy_uavs, layout.energy_uav_records, layout.energy_uav_fields),
        (layout.energy_stations, layout.energy_station_records, layout.energy_station_fields),
    ):
        for slot in range(slots):
            indices.extend((section.start + slot * fields, section.start + slot * fields + 1))
    return indices


def _state_xy_indices():
    indices = []
    for slot in range(8):
        indices.extend((slot * 3, slot * 3 + 1))
    for slot in range(30):
        start = 32 + slot * 6
        indices.extend((start, start + 1, start + 2, start + 3))
    indices.extend((212, 213))
    for slot in range(2):
        indices.extend((288 + slot * 7, 289 + slot * 7))
    return indices


def test_d4_group_and_dtype_and_source_immutability():
    rng = np.random.default_rng(952001)
    observations = rng.uniform(-0.5, 1.0, (8, 365)).astype(np.float32)
    state = rng.uniform(-0.5, 1.0, 306).astype(np.float64)
    actions = rng.uniform(-1, 1, (8, 4)).astype(np.float32)
    originals = [x.copy() for x in (observations, state, actions)]
    assert get_transform("mirror_x") is D4.MIRROR_X
    for first in D4:
        assert first.compose(first.inverse()) is D4.IDENTITY
        for second in D4:
            product = first.compose(second)
            assert product.matrix == tuple(map(tuple, np.asarray(first.matrix) @ np.asarray(second.matrix)))
            np.testing.assert_allclose(
                transform_observations(transform_observations(observations, second), first),
                transform_observations(observations, product), atol=1e-6,
            )
            np.testing.assert_allclose(
                transform_state(transform_state(state, second), first),
                transform_state(state, product), atol=1e-12,
            )
            np.testing.assert_allclose(
                transform_actions(transform_actions(actions, second), first),
                transform_actions(actions, product), atol=1e-6,
            )
        np.testing.assert_allclose(inverse_actions(transform_actions(actions, first), first), actions)
        assert transform_observations(observations, first).dtype == observations.dtype
        assert transform_state(state, first).dtype == state.dtype
        assert transform_actions(actions, first).dtype == actions.dtype
    for original, expected in zip((observations, state, actions), originals):
        np.testing.assert_array_equal(original, expected)
    assert transform_observations(observations, D4.IDENTITY) is not observations


@pytest.mark.parametrize("transform", list(D4))
def test_every_encoded_xy_and_unchanged_fields(transform):
    obs = np.arange(8 * 365, dtype=np.float32).reshape(8, 365) / 8192
    state = np.arange(306, dtype=np.float32) / 512
    actions = np.arange(32, dtype=np.float32).reshape(8, 4) / 64
    obs[:, S7S2_LAYOUT.users.start + 6 : S7S2_LAYOUT.users.start + 12] = 0
    result = transform_observations(obs, transform)
    obs_indices = _observation_xy_indices()
    for start in obs_indices[::2]:
        np.testing.assert_allclose(
            result[:, start:start + 2],
            _apply_xy(obs[:, start:start + 2], transform, absolute=start == 0), atol=1e-7,
        )
    unchanged = np.setdiff1d(np.arange(365), obs_indices)
    np.testing.assert_array_equal(result[:, unchanged], obs[:, unchanged])
    np.testing.assert_array_equal(result[:, S7S2_LAYOUT.users.start + 6:S7S2_LAYOUT.users.start + 12], 0)

    state_result = transform_state(state, transform)
    state_indices = _state_xy_indices()
    velocity_starts = {32 + slot * 6 + 2 for slot in range(30)}
    for start in state_indices[::2]:
        np.testing.assert_allclose(
            state_result[start:start + 2],
            _apply_xy(state[start:start + 2], transform, absolute=start not in velocity_starts), atol=1e-7,
        )
    np.testing.assert_array_equal(
        state_result[np.setdiff1d(np.arange(306), state_indices)],
        state[np.setdiff1d(np.arange(306), state_indices)],
    )
    action_result = transform_actions(actions, transform)
    np.testing.assert_allclose(action_result[:, :2], _apply_xy(actions[:, :2], transform))
    np.testing.assert_array_equal(action_result[:, 2:], actions[:, 2:])


@pytest.mark.parametrize("function,shape", [
    (transform_observations, (8, 364)),
    (transform_state, (305,)),
    (transform_actions, (8, 3)),
])
def test_reject_wrong_shape_or_dtype(function, shape):
    with pytest.raises(ValueError, match="shape"):
        function(np.zeros(shape, dtype=np.float32), D4.IDENTITY)
    correct = {transform_observations: (8, 365), transform_state: (306,),
               transform_actions: (8, 4)}[function]
    with pytest.raises(TypeError, match="floating dtype"):
        function(np.zeros(correct, dtype=np.int32), D4.IDENTITY)


def _reflect_world(raw, transform):
    """Reflect the native geometry and its exogenous geometric caches in place."""
    for name in ("uav_positions", "user_positions", "ground_bs_positions",
                 "charging_station_positions"):
        values = getattr(raw, name)
        values[:, :2] = _apply_xy(values[:, :2] / raw.area_size, transform, absolute=True) * raw.area_size
    for name in ("user_waypoints", "cluster_centers_history", "cluster_waypoints"):
        values = getattr(raw, name)
        values[:, :2] = _apply_xy(values[:, :2] / raw.area_size, transform, absolute=True) * raw.area_size
    for name in ("user_velocities", "cluster_velocities"):
        values = getattr(raw, name)
        values[:, :2] = _apply_xy(values[:, :2], transform)
    raw.global_bs_cache = {
        index: (_apply_xy(position[:2], transform).tolist() + [position[2]], visible)
        for index, (position, visible) in raw.global_bs_cache.items()
    }
    raw._update_channel_state()
    raw._update_uav_connections()


@pytest.mark.parametrize("transform", [D4.MIRROR_X, D4.MIRROR_Y])
def test_native_reflected_schema_speed_and_guard(transform):
    config = make_eval_config(60, 925031)
    left, right = make_env(config, 952001), make_env(config, 952001)
    try:
        left.reset(seed=952001)
        right.reset(seed=952001)
        original, reflected = left.env, right.env
        positions = original.uav_positions.copy()
        positions[:6, :2] = original.user_positions[[0, 5, 10, 15, 20, 25], :2] + 200.0
        positions[6, :2] = original.ground_bs_positions[0, :2] + 300.0
        positions[7, :2] = original.user_positions[3, :2] - 400.0
        positions[:, 2] = 100.0
        for raw in (original, reflected):
            raw.uav_positions = positions.copy()
            raw._update_channel_state()
            raw._update_uav_connections()
            raw._update_global_bs_cache()
        _reflect_world(reflected, transform)
        left_obs = np.stack([original._get_observation(f"uav_{i}")["obs"] for i in range(8)])
        right_obs = np.stack([reflected._get_observation(f"uav_{i}")["obs"] for i in range(8)])
        assert np.count_nonzero(left_obs[:, S7S2_LAYOUT.users]) > 0
        assert np.count_nonzero(left_obs[:, S7S2_LAYOUT.bs]) > 0
        np.testing.assert_allclose(right_obs, transform_observations(left_obs, transform), atol=2e-5)
        np.testing.assert_allclose(reflected._get_state(), transform_state(original._get_state(), transform), atol=1e-6)
        np.testing.assert_allclose(
            np.linalg.norm(original.uav_positions[0] - original.charging_station_positions[0]),
            np.linalg.norm(reflected.uav_positions[0] - reflected.charging_station_positions[0]),
        )

        movement = np.array([0.8, -0.9, 0.4], dtype=np.float32)
        reflected_movement = np.r_[_apply_xy(movement[:2], transform), movement[2]]
        velocity = original._movement_velocity_from_action(movement)
        reflected_velocity = reflected._movement_velocity_from_action(reflected_movement)
        np.testing.assert_allclose(reflected_velocity[:2], _apply_xy(velocity[:2], transform), atol=1e-6)
        assert np.linalg.norm(velocity[:2]) <= original.max_speed + 1e-12
        assert reflected_velocity[2] == velocity[2]
        # A matched routed BS link activates the native shield in both worlds.
        route = ([("uav", 6), ("bs", 0)], 0.0)
        for raw in (original, reflected):
            raw.routing_paths[6] = route
            raw.connections[6, 0] = True
            raw.backhaul_guard_checked_actions = 0
            raw.backhaul_guard_blocked_actions = 0
        for threshold in (original.backhaul_guard_min_capacity_mbps, 1e9):
            for raw in (original, reflected):
                raw.backhaul_guard_min_capacity_mbps = threshold
            before_left = original.backhaul_guard_checked_actions
            before_right = reflected.backhaul_guard_checked_actions
            guarded = original._apply_backhaul_action_guard(6, velocity)
            reflected_guarded = reflected._apply_backhaul_action_guard(6, reflected_velocity)
            assert original.backhaul_guard_checked_actions == before_left + 1
            assert reflected.backhaul_guard_checked_actions == before_right + 1
            np.testing.assert_allclose(reflected_guarded[:2], _apply_xy(guarded[:2], transform), atol=1e-6)
            np.testing.assert_allclose(reflected_guarded[2], guarded[2], atol=1e-6)
            assert original.backhaul_guard_blocked_actions == reflected.backhaul_guard_blocked_actions
        assert original.backhaul_guard_blocked_actions > 0
    finally:
        left.close()
        right.close()
