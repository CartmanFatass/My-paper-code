from __future__ import annotations

import copy
import random

import numpy as np
import pytest
import torch

from experiments.candidates.load_critical_member_generalization.load_probe.scenes import (
    MAX_UAVS,
    N_USERS,
    make_native_scene,
    matched_world,
    refresh_native_scene,
    service_diagnostics,
)


def _global_rng_state():
    numpy_state = np.random.get_state()
    return (
        random.getstate(),
        (
            numpy_state[0],
            numpy_state[1].copy(),
            numpy_state[2],
            numpy_state[3],
            numpy_state[4],
        ),
        torch.random.get_rng_state().clone(),
    )


def _assert_global_rng_equal(before, after):
    assert before[0] == after[0]
    assert before[1][0] == after[1][0]
    np.testing.assert_array_equal(before[1][1], after[1][1])
    assert before[1][2:] == after[1][2:]
    assert torch.equal(before[2], after[2])


def _observation_array(observations, agents):
    return np.stack([observations[agent]["obs"] for agent in agents])


def test_world_streams_are_exact_float64_prefixes_and_do_not_touch_global_rng():
    before = _global_rng_state()
    world = matched_world(7)
    env4 = make_native_scene(n_uavs=4, capacity=10, world_id=7, horizon=10)
    env8 = make_native_scene(n_uavs=8, capacity=5, world_id=7, horizon=10)
    after = _global_rng_state()
    _assert_global_rng_equal(before, after)

    user_seed = int(
        np.random.SeedSequence([260922, 6, 7, 1]).generate_state(
            1, dtype=np.uint32
        )[0]
    )
    uav_seed = int(
        np.random.SeedSequence([260922, 6, 7, 2]).generate_state(
            1, dtype=np.uint32
        )[0]
    )
    expected_users = np.empty((N_USERS, 2), dtype=np.float64)
    user_rng = np.random.RandomState(user_seed)
    for i in range(N_USERS):
        expected_users[i] = [user_rng.uniform(0, 1000), user_rng.uniform(0, 1000)]
    expected_uavs = np.empty((MAX_UAVS, 3), dtype=np.float64)
    uav_rng = np.random.RandomState(uav_seed)
    for i in range(MAX_UAVS):
        expected_uavs[i] = [
            uav_rng.uniform(0, 1000),
            uav_rng.uniform(0, 1000),
            uav_rng.uniform(50, 150),
        ]

    assert world.user_seed == user_seed and world.uav_seed == uav_seed
    assert world.user_positions.dtype == world.uav_positions.dtype == np.float64
    np.testing.assert_array_equal(world.user_positions, expected_users)
    np.testing.assert_array_equal(world.uav_positions, expected_uavs)
    np.testing.assert_array_equal(env4.user_positions, env8.user_positions)
    np.testing.assert_array_equal(env4.uav_positions, env8.uav_positions[:4])


def test_repeat_reset_is_exact_and_capacity_is_hidden_from_observation_and_state():
    low = make_native_scene(n_uavs=6, capacity=1, world_id=3, horizon=10)
    high = make_native_scene(n_uavs=6, capacity=20, world_id=3, horizon=10)
    low_obs, _ = low.reset(seed=811)
    high_obs, _ = high.reset(seed=811)
    first_obs = _observation_array(low_obs, low.agents)
    first_state = low._get_state().copy()

    np.testing.assert_array_equal(first_obs, _observation_array(high_obs, high.agents))
    np.testing.assert_array_equal(first_state, high._get_state())
    np.testing.assert_array_equal(low.sinr_matrix, high.sinr_matrix)
    assert first_obs.shape == (6, 104)
    assert first_state.shape == (3 * 6 + 2 * N_USERS + 1,)

    low.step({agent: np.zeros(3, dtype=np.float32) for agent in low.agents})
    repeated_obs, _ = low.reset(seed=811)
    np.testing.assert_array_equal(first_obs, _observation_array(repeated_obs, low.agents))
    np.testing.assert_array_equal(first_state, low._get_state())


def test_same_n_capacity_pair_has_exact_action_driven_geometry_through_k10_terminal():
    low = make_native_scene(n_uavs=4, capacity=1, world_id=11, horizon=10)
    high = make_native_scene(n_uavs=4, capacity=20, world_id=11, horizon=10)
    low.reset(seed=977)
    high.reset(seed=977)
    saw_reward_difference = False

    for step in range(10):
        action = np.asarray(
            [
                [0.20, -0.10, 0.05],
                [-0.15, 0.05, -0.02],
                [0.00, 0.10, 0.00],
                [0.05, 0.00, 0.01],
            ],
            dtype=np.float32,
        )
        actions = {agent: action[i].copy() for i, agent in enumerate(low.agents)}
        low_result = low.step(actions)
        high_result = high.step(copy.deepcopy(actions))
        low_obs, low_rewards, low_term, low_trunc, _ = low_result
        high_obs, high_rewards, high_term, high_trunc, _ = high_result

        np.testing.assert_array_equal(low.uav_positions, high.uav_positions)
        np.testing.assert_array_equal(low.user_positions, high.user_positions)
        np.testing.assert_array_equal(low.sinr_matrix, high.sinr_matrix)
        np.testing.assert_array_equal(low._get_state(), high._get_state())
        np.testing.assert_array_equal(
            _observation_array(low_obs, low.agents),
            _observation_array(high_obs, high.agents),
        )
        saw_reward_difference |= low_rewards != high_rewards
        assert all(low_term.values()) is (step == 9)
        assert all(high_term.values()) is (step == 9)
        assert not any(low_trunc.values()) and not any(high_trunc.values())
        assert low._get_state()[-1] == pytest.approx((step + 1) / 10)

    assert saw_reward_difference
    assert low.current_step == high.current_step == 10


def test_diagnostics_capture_actual_caps_service_partition_and_reward_composition():
    env = make_native_scene(n_uavs=4, capacity=1, world_id=5, horizon=10)
    diagnostics = service_diagnostics(env)

    occupancy = np.count_nonzero(env.connections, axis=1)
    np.testing.assert_array_equal(occupancy, np.ones(4, dtype=int))
    assert diagnostics["e_i"] == np.count_nonzero(
        env.sinr_matrix >= env.min_sinr, axis=1
    ).tolist()
    assert diagnostics["at_most_one_eligible"] == {
        "holds": True,
        "maximum_eligible_uavs_per_user": 1,
    }
    identity = diagnostics["capacity_identity"]
    assert identity["applicable"] and identity["holds"]
    assert identity["predicted_served_S_c"] == identity["actual_served"]
    assert identity["actual_served"] == int(np.count_nonzero(env.connections))
    assert diagnostics["user_counts"]["eligible_unserved"] > 0
    assert diagnostics["full_uavs"]["numerator"] == int(np.count_nonzero(occupancy == 1))

    truncation = diagnostics["visible_user_truncation"]
    e_i = np.asarray(diagnostics["e_i"])
    assert truncation["numerator"] == int(np.maximum(e_i - 20, 0).sum())
    assert truncation["denominator"] == int(e_i.sum())

    components = diagnostics["reward_components"]
    quality = diagnostics["quality_composition"]
    assert quality["connected_links"] == identity["actual_served"]
    assert quality["normalized_sinr_mean"] == pytest.approx(
        quality["normalized_sinr_sum"] / max(quality["connected_links"], 1)
    )
    native_reward = env._compute_reward()
    assert components == pytest.approx(env.reward_info)
    assert native_reward == pytest.approx(components["total_reward"])


def test_diagnostics_are_read_only_and_refuse_identity_outside_its_domain():
    env = make_native_scene(n_uavs=4, capacity=10, world_id=2, horizon=10)
    before_rng = _global_rng_state()
    before = {
        "sinr": env.sinr_matrix.copy(),
        "connections": env.connections.copy(),
        "positions": env.uav_positions.copy(),
        "reward_info": copy.deepcopy(getattr(env, "reward_info", None)),
    }
    service_diagnostics(env)
    _assert_global_rng_equal(before_rng, _global_rng_state())
    np.testing.assert_array_equal(before["sinr"], env.sinr_matrix)
    np.testing.assert_array_equal(before["connections"], env.connections)
    np.testing.assert_array_equal(before["positions"], env.uav_positions)
    assert before["reward_info"] == getattr(env, "reward_info", None)

    env.min_sinr = -0.25
    refresh_native_scene(env)
    refused = service_diagnostics(env)["capacity_identity"]
    assert not refused["applicable"]
    assert refused["holds"] is None and refused["predicted_served_S_c"] is None
    assert "min_sinr must be at least 0 dB" in refused["reasons"]

    env.min_sinr = 0
    env.use_fdma = True
    refresh_native_scene(env)
    refused = service_diagnostics(env)["capacity_identity"]
    assert not refused["applicable"]
    assert "use_fdma must be False" in refused["reasons"]


@pytest.mark.parametrize(
    "kwargs, error",
    [
        ({"n_uavs": 0, "capacity": 1, "world_id": 0}, "n_uavs"),
        ({"n_uavs": 4, "capacity": 0, "world_id": 0}, "capacity"),
        ({"n_uavs": 4, "capacity": 1, "world_id": 16}, "world_id"),
        ({"n_uavs": 4, "capacity": 1, "world_id": 0, "horizon": 0}, "horizon"),
    ],
)
def test_scene_inputs_fail_closed(kwargs, error):
    with pytest.raises((TypeError, ValueError), match=error):
        make_native_scene(**kwargs)
