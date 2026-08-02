import numpy as np
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
pytest.importorskip("gymnasium")

from config_1 import Config
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from envs.pettingzoo.relay.energy_aware import UAVEnergyAwareRelayEnv
from tests._scenario7_fixtures import (
    capture_environment_rng_state,
    capture_structured_evidence,
    make_arm_env,
    make_env,
    make_variant_env,
    rng_states_equal,
    zero_actions,
)


def test_fdma_frontend_capacity_reuses_each_users_sinr_once():
    env = make_env("S7-S1", seed=46)
    try:
        env.reset(seed=46)
        connected_users = np.array([0, 1, 2], dtype=int)
        sinr_db = float(env.min_sinr + 10.0)
        env._compute_air_to_ground_path_loss = Mock(return_value=100.0)
        env._compute_uav_to_user_sinr = Mock(return_value=sinr_db)

        spectral_efficiency = env._get_spectral_efficiency_from_sinr(sinr_db)
        bandwidth_per_user = env.bandwidth / env.n_uavs / len(connected_users)
        expected = sum(
            bandwidth_per_user * spectral_efficiency for _ in connected_users
        )

        actual = env._compute_uav_frontend_capacity(0, connected_users)

        assert actual == expected
        assert env._compute_air_to_ground_path_loss.call_count == len(connected_users)
        assert env._compute_uav_to_user_sinr.call_count == len(connected_users)
    finally:
        env.close()

def test_user_sinr_validates_the_step_cache_once_per_calculation():
    env = make_env("S7-S1", seed=48)
    try:
        env.reset(seed=48)
        env.uav_positions[:] = env.user_positions[0]
        env._refresh_step_communication_cache()
        env._current_step_communication_cache = Mock(
            wraps=env._current_step_communication_cache
        )

        env._compute_uav_to_user_sinr(0, 0, env.tx_power)

        assert env._current_step_communication_cache.call_count == 1
    finally:
        env.close()

def test_widest_path_capacity_cache_is_exactly_equivalent():
    config_cached = Config("S7-S1")
    config_cached.max_steps = 8
    config_uncached = Config("S7-S1")
    config_uncached.max_steps = 8
    cached = ParallelToArrayAdapter(
        UAVEnergyAwareRelayEnv(config=config_cached, seed=47), seed=47
    )
    uncached = ParallelToArrayAdapter(
        UAVEnergyAwareRelayEnv(config=config_uncached, seed=47), seed=47
    )
    uncached.env._disable_routing_link_capacity_cache = True
    uncached.env._disable_sinr_matrix_reuse = True
    uncached.env._disable_step_communication_cache = True
    try:
        cached_reset = cached.reset(seed=47)
        uncached_reset = uncached.reset(seed=47)
        assert capture_structured_evidence(cached_reset) == capture_structured_evidence(
            uncached_reset
        )
        cached.env.uav_positions[0, 0] += 1.0
        uncached.env.uav_positions[0, 0] += 1.0
        assert cached.env._access_capacity_bps(
            0, 0, cached.env.bandwidth, relaxed=True
        ) == uncached.env._access_capacity_bps(
            0, 0, uncached.env.bandwidth, relaxed=True
        )
        action_template = np.linspace(
            -0.8, 0.8, num=int(np.prod(cached.action_space.shape)), dtype=np.float32
        ).reshape(cached.action_space.shape)
        cached.env._compute_link_sinr = Mock(wraps=cached.env._compute_link_sinr)
        uncached.env._compute_link_sinr = Mock(wraps=uncached.env._compute_link_sinr)
        cached.env._compute_uav_to_user_sinr = Mock(
            wraps=cached.env._compute_uav_to_user_sinr
        )
        uncached.env._compute_uav_to_user_sinr = Mock(
            wraps=uncached.env._compute_uav_to_user_sinr
        )
        for step in range(5):
            actions = np.roll(action_template, step, axis=0)
            cached_step = cached.step(actions)
            uncached_step = uncached.step(actions)
            assert capture_structured_evidence(
                cached_step
            ) == capture_structured_evidence(uncached_step)
            np.testing.assert_array_equal(
                cached.env._get_state(), uncached.env._get_state()
            )
            assert capture_structured_evidence(
                cached.env.routing_paths
            ) == capture_structured_evidence(uncached.env.routing_paths)
            assert rng_states_equal(
                capture_environment_rng_state(cached),
                capture_environment_rng_state(uncached),
            )
        assert (
            cached.env._compute_link_sinr.call_count
            < uncached.env._compute_link_sinr.call_count
        )
        assert (
            cached.env._compute_uav_to_user_sinr.call_count
            < uncached.env._compute_uav_to_user_sinr.call_count
        )
    finally:
        cached.close()
        uncached.close()

def test_step_communication_cache_reuses_user_geometry_exactly():
    cached = UAVEnergyAwareRelayEnv(config=Config("S7-S1"), seed=49)
    uncached = UAVEnergyAwareRelayEnv(config=Config("S7-S1"), seed=49)
    uncached._disable_step_communication_cache = True
    try:
        cached.reset(seed=49)
        uncached.reset(seed=49)
        cached._compute_air_to_ground_path_loss = Mock(
            wraps=cached._compute_air_to_ground_path_loss
        )
        uncached._compute_air_to_ground_path_loss = Mock(
            wraps=uncached._compute_air_to_ground_path_loss
        )

        cached._update_channel_state()
        uncached._update_channel_state()

        np.testing.assert_array_equal(cached.sinr_matrix, uncached.sinr_matrix)
        np.testing.assert_array_equal(cached.connections, uncached.connections)
        assert (
            cached._compute_air_to_ground_path_loss.call_count
            < uncached._compute_air_to_ground_path_loss.call_count
        )
    finally:
        cached.close()
        uncached.close()

def test_directional_path_loss_cache_reuses_exact_link_geometry():
    cached = UAVEnergyAwareRelayEnv(config=Config("S7-S1"), seed=58)
    scalar = UAVEnergyAwareRelayEnv(config=Config("S7-S1"), seed=58)
    scalar._disable_directional_path_loss_cache = True
    try:
        cached.reset(seed=58)
        scalar.reset(seed=58)
        cached._refresh_step_communication_cache()
        scalar._refresh_step_communication_cache()
        for env in (cached, scalar):
            env._compute_air_to_air_path_loss = Mock(
                wraps=env._compute_air_to_air_path_loss
            )
            env._compute_air_to_ground_path_loss = Mock(
                wraps=env._compute_air_to_ground_path_loss
            )
            env._compute_ground_to_air_path_loss = Mock(
                wraps=env._compute_ground_to_air_path_loss
            )

        def link_rows(env):
            return np.asarray(
                [
                    env._compute_uav_to_uav_sinr(0, 1),
                    env._get_link_capacity("uav", 0, "uav", 1),
                    env._get_link_capacity("uav", 1, "ground_bs", 0),
                    env._get_link_capacity("uav", 0, "ground_bs", 0),
                    env._get_link_capacity("ground_bs", 0, "uav", 0),
                ]
            )

        np.testing.assert_array_equal(link_rows(cached), link_rows(scalar))
        cached_calls = sum(
            row.call_count
            for row in (
                cached._compute_air_to_air_path_loss,
                cached._compute_air_to_ground_path_loss,
                cached._compute_ground_to_air_path_loss,
            )
        )
        scalar_calls = sum(
            row.call_count
            for row in (
                scalar._compute_air_to_air_path_loss,
                scalar._compute_air_to_ground_path_loss,
                scalar._compute_ground_to_air_path_loss,
            )
        )
        assert cached_calls < scalar_calls
    finally:
        cached.close()
        scalar.close()

def test_step_link_cache_reuses_exact_state_and_bypasses_trial_inputs():
    env = UAVEnergyAwareRelayEnv(config=Config("S7-S1"), seed=53)
    try:
        env.reset(seed=53)
        env._compute_link_sinr = Mock(wraps=env._compute_link_sinr)
        original_positions = env.uav_positions.copy()

        baseline = env._get_link_capacity("uav", 0, "uav", 1)
        calls_after_baseline = env._compute_link_sinr.call_count
        repeated = env._get_link_capacity("uav", 0, "uav", 1)
        assert repeated == baseline
        assert env._compute_link_sinr.call_count == calls_after_baseline

        env.uav_positions[0, 0] += 1.0
        env._get_link_capacity("uav", 0, "uav", 1)
        assert env._compute_link_sinr.call_count > calls_after_baseline
        calls_after_trial = env._compute_link_sinr.call_count

        env.uav_positions[:] = original_positions
        restored = env._get_link_capacity("uav", 0, "uav", 1)
        assert restored == baseline
        assert env._compute_link_sinr.call_count == calls_after_trial

        env.noise_power += 1.0
        env._get_link_capacity("uav", 0, "uav", 1)
        assert env._compute_link_sinr.call_count > calls_after_trial
        calls_after_config_change = env._compute_link_sinr.call_count
        env.noise_power -= 1.0
        assert env._get_link_capacity("uav", 0, "uav", 1) == baseline
        assert env._compute_link_sinr.call_count == calls_after_config_change

        env.uav_failed[2] = True
        env._get_link_capacity("uav", 0, "uav", 1)
        assert env._compute_link_sinr.call_count > calls_after_config_change
        calls_after_unavailable_change = env._compute_link_sinr.call_count
        env.uav_failed[2] = False
        assert env._get_link_capacity("uav", 0, "uav", 1) == baseline
        assert env._compute_link_sinr.call_count == calls_after_unavailable_change
    finally:
        env.close()

def test_graph_radio_reuse_is_exact_and_avoids_revalidation():
    fast = UAVEnergyAwareRelayEnv(config=Config("S7-S1"), seed=57)
    scalar = UAVEnergyAwareRelayEnv(config=Config("S7-S1"), seed=57)
    scalar._disable_graph_radio_reuse = True
    try:
        fast.reset(seed=57)
        scalar.reset(seed=57)
        fast._is_uav_unavailable = Mock(wraps=fast._is_uav_unavailable)
        scalar._is_uav_unavailable = Mock(wraps=scalar._is_uav_unavailable)
        fast._compute_link_sinr = Mock(wraps=fast._compute_link_sinr)
        scalar._compute_link_sinr = Mock(wraps=scalar._compute_link_sinr)

        fast_potential = fast._graph_service_potential()
        scalar_potential = scalar._graph_service_potential()

        assert fast_potential == scalar_potential
        np.testing.assert_array_equal(
            fast.last_widest_backhaul_capacities_bps,
            scalar.last_widest_backhaul_capacities_bps,
        )
        assert (
            fast._is_uav_unavailable.call_count
            < scalar._is_uav_unavailable.call_count
        )
        assert fast._compute_link_sinr.call_count < scalar._compute_link_sinr.call_count
    finally:
        fast.close()
        scalar.close()

def test_step_keeps_one_read_only_previous_route_snapshot_and_no_agent_copies():
    env = make_env("S7-S1", seed=59)
    try:
        env.reset(seed=59)
        previous_routes = env.routing_paths
        previous_values = {
            owner: (tuple(path), capacity)
            for owner, (path, capacity) in previous_routes.items()
        }

        _, _, _, _, infos = env.step(zero_actions(env))

        assert env.previous_routing_paths_snapshot is not previous_routes
        assert env.previous_routing_paths_snapshot.keys() == previous_values.keys()
        for owner, (path, capacity) in previous_values.items():
            stored_path, stored_capacity = env.previous_routing_paths_snapshot[owner]
            assert tuple(stored_path) == path
            assert stored_capacity == capacity

        reward_infos = [info["reward_info"] for info in infos.values()]
        connections_snapshot = reward_infos[0]["connections"]
        routing_paths_snapshot = reward_infos[0]["routing_paths"]
        assert connections_snapshot is not env.connections
        np.testing.assert_array_equal(connections_snapshot, env.connections)
        assert routing_paths_snapshot is not env.routing_paths
        assert routing_paths_snapshot == env.routing_paths
        assert all(
            info["connections"] is connections_snapshot for info in reward_infos
        )
        assert all(
            info["routing_paths"] is routing_paths_snapshot for info in reward_infos
        )
    finally:
        env.close()
