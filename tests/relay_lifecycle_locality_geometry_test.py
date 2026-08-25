from __future__ import annotations

import numpy as np
import pytest

from config_1 import Config
from envs.pettingzoo.relay.energy_aware import UAVEnergyAwareRelayEnv
from envs.pettingzoo.relay.forced_relay import UAVForcedRelayEnv
from envs.pettingzoo.relay.progressive import UAVProgressiveRelayEnv
from envs.pettingzoo.relay.routed_core import UAVRoutedRelayEnv
import envs.pettingzoo.uav_cpp_backend as geometry_backend


def _canonical(value):
    if isinstance(value, np.ndarray):
        array = np.ascontiguousarray(value)
        return ("array", array.dtype.str, array.shape, array.tobytes())
    if isinstance(value, np.generic):
        scalar = np.asarray(value)
        return ("scalar", scalar.dtype.str, scalar.tobytes())
    if isinstance(value, dict):
        return (
            "dict",
            tuple((key, _canonical(item)) for key, item in value.items()),
        )
    if isinstance(value, (list, tuple)):
        return (type(value).__name__, tuple(_canonical(item) for item in value))
    return (type(value).__name__, value)


def _make_routed(*, backend="python_reference", seed=123, routing="widest_path"):
    return UAVRoutedRelayEnv(
        n_uavs=4,
        n_users=8,
        n_ground_bs=2,
        n_clusters=4,
        area_size=1000.0,
        observation_radius=100.0,
        max_steps=20,
        user_movement_model="stationary",
        action_space_type="continuous",
        routing_protocol=routing,
        randomize_bs=True,
        randomize_users=True,
        randomize_uav_start=True,
        relay_geometry_backend=backend,
        seed=seed,
    )


def test_native_geometry_is_the_fail_closed_per_environment_default():
    routed = UAVRoutedRelayEnv(
        n_uavs=2,
        n_users=4,
        n_ground_bs=1,
        n_clusters=4,
        max_steps=2,
        user_movement_model="stationary",
        action_space_type="continuous",
        seed=29,
    )
    energy_config = Config("S7-S3")
    energy_config.n_uavs = 2
    energy_config.n_users = 4
    energy_config.n_ground_bs = 1
    energy = UAVEnergyAwareRelayEnv(config=energy_config, seed=29)
    forced = UAVForcedRelayEnv(
        n_uavs=2,
        n_users=4,
        n_ground_bs=1,
        n_clusters=4,
        max_steps=2,
        user_movement_model="stationary",
        seed=29,
    )
    try:
        assert geometry_backend.DEFAULT_ROUTED_RELAY_GEOMETRY_BACKEND == "cpp"
        assert geometry_backend.DEFAULT_ENERGY_RELAY_GEOMETRY_BACKEND == "cpp"
        assert geometry_backend.DEFAULT_FORCED_RELAY_GEOMETRY_BACKEND == "cpp"
        assert geometry_backend.DEFAULT_RELAY_GEOMETRY_BACKEND == "cpp"
        assert routed.relay_geometry_backend == "cpp"
        assert energy.relay_geometry_backend == "cpp"
        assert forced.relay_geometry_backend == "cpp"
    finally:
        routed.close()
        energy.close()
        forced.close()


def test_explicit_cpp_preserves_existing_float64_discrete_movement_order():
    env = UAVRoutedRelayEnv(
        n_uavs=2,
        n_users=4,
        n_ground_bs=1,
        n_clusters=4,
        max_steps=2,
        user_movement_model="stationary",
        action_space_type="discrete",
        relay_geometry_backend="cpp",
        seed=30,
    )
    try:
        env.reset(seed=30)
        diagonal_action = 5
        before = env.uav_positions.copy()
        expected = before.copy()
        expected[0] += env.action_to_velocity[diagonal_action] * env.time_step
        expected[0, 0] = np.clip(expected[0, 0], 0, env.area_size)
        expected[0, 1] = np.clip(expected[0, 1], 0, env.area_size)
        expected[0, 2] = np.clip(expected[0, 2], *env.height_range)

        env.step({"uav_0": diagonal_action})

        np.testing.assert_array_equal(env.uav_positions, expected)
    finally:
        env.close()


def test_routed_reset_clears_episode_cache_and_rebuilds_hggr_topology():
    dirty = _make_routed(seed=31, routing="hggr")
    fresh = _make_routed(seed=31, routing="hggr")
    try:
        dirty.reset(seed=31)
        dirty.global_bs_cache = {99: (np.ones(3), 1.0)}
        dirty.last_global_sync_step = 17
        dirty.hop_map = {index: 999 for index in range(dirty.n_uavs)}
        dirty.uav_positions[:] = 0.0
        dirty.routing_paths = {0: ([('uav', 0), ('ground_bs', 0)], 123.0)}

        dirty_reset = dirty.reset(seed=31)
        fresh_reset = fresh.reset(seed=31)

        assert _canonical(dirty_reset) == _canonical(fresh_reset)
        assert dirty.global_bs_cache == {}
        assert dirty.last_global_sync_step == -1
        assert dirty.hop_map == fresh.hop_map == dirty._calculate_hop_map()
        assert _canonical(dirty.routing_paths) == _canonical(fresh.routing_paths)
        np.testing.assert_array_equal(dirty.sinr_matrix, fresh.sinr_matrix)
        np.testing.assert_array_equal(dirty.uav_connections, fresh.uav_connections)
        np.testing.assert_array_equal(dirty.uav_bs_connections, fresh.uav_bs_connections)
    finally:
        dirty.close()
        fresh.close()


def test_energy_reset_rebuilds_topology_after_energy_state_is_resampled():
    config_dirty = Config("S7-S3")
    config_dirty.relay_geometry_backend = "python_reference"
    config_fresh = Config("S7-S3")
    config_fresh.relay_geometry_backend = "python_reference"
    dirty = UAVEnergyAwareRelayEnv(config=config_dirty, seed=37)
    fresh = UAVEnergyAwareRelayEnv(config=config_fresh, seed=37)
    try:
        dirty.reset(seed=37)
        dirty.uav_battery_ratios[:] = 0.0
        dirty.uav_failed[:] = True
        dirty.global_bs_cache = {99: (np.ones(3), 1.0)}
        dirty.last_global_sync_step = 18
        dirty.hop_map = {index: 999 for index in range(dirty.n_uavs)}
        dirty.connections[:] = False
        dirty.uav_connections[:] = False
        dirty.uav_bs_connections[:] = False
        dirty.routing_paths = {}

        dirty_reset = dirty.reset(seed=37)
        fresh_reset = fresh.reset(seed=37)

        assert _canonical(dirty_reset) == _canonical(fresh_reset)
        assert dirty.global_bs_cache == {}
        assert dirty.last_global_sync_step == -1
        np.testing.assert_array_equal(dirty.sinr_matrix, fresh.sinr_matrix)
        np.testing.assert_array_equal(dirty.connections, fresh.connections)
        np.testing.assert_array_equal(dirty.uav_connections, fresh.uav_connections)
        np.testing.assert_array_equal(dirty.uav_bs_connections, fresh.uav_bs_connections)
        assert _canonical(dirty.routing_paths) == _canonical(fresh.routing_paths)
    finally:
        dirty.close()
        fresh.close()


def test_energy_reset_partial_prior_unavailability_has_one_fresh_counter_view():
    dirty_config = Config("S7-S3")
    fresh_config = Config("S7-S3")
    for config in (dirty_config, fresh_config):
        config.relay_geometry_backend = "python_reference"
        config.enable_soft_handover = True
    dirty = UAVEnergyAwareRelayEnv(config=dirty_config, seed=39)
    fresh = UAVEnergyAwareRelayEnv(config=fresh_config, seed=39)
    try:
        dirty.reset(seed=39)
        dirty.uav_failed[:] = False
        dirty.uav_failed[: max(1, dirty.n_uavs // 2)] = True
        dirty.uav_battery_ratios[:] = 1.0
        dirty.uav_battery_ratios[1::2] = 0.0
        dirty.user_serving_sets = [
            [index % dirty.n_uavs] for index in range(dirty.n_users)
        ]
        dirty.serving_set_changes = 91
        dirty.uav_joins_count = 92
        dirty.uav_leaves_count = 93

        dirty_observations, dirty_infos = dirty.reset(seed=39)
        fresh_observations, fresh_infos = fresh.reset(seed=39)

        assert _canonical(dirty_observations) == _canonical(fresh_observations)
        assert _canonical(dirty_infos) == _canonical(fresh_infos)
        assert _canonical(dirty.state) == _canonical(fresh.state)
        assert dirty.serving_set_changes == fresh.serving_set_changes
        assert dirty.uav_joins_count == fresh.uav_joins_count
        assert dirty.uav_leaves_count == fresh.uav_leaves_count
        assert dirty.user_serving_sets == fresh.user_serving_sets
    finally:
        dirty.close()
        fresh.close()


@pytest.mark.parametrize("environment_type", (UAVRoutedRelayEnv, UAVForcedRelayEnv))
def test_nearest_uav_and_base_summary_is_zero_outside_local_radius(environment_type):
    common = dict(
        n_uavs=2,
        n_users=4,
        n_ground_bs=1,
        n_clusters=4,
        area_size=1000.0,
        observation_radius=100.0,
        max_steps=4,
        user_movement_model="stationary",
        randomize_bs=False,
        randomize_users=False,
        randomize_uav_start=False,
        seed=41,
    )
    if environment_type is UAVRoutedRelayEnv:
        common.update(
            action_space_type="continuous",
            relay_geometry_backend="python_reference",
        )
    env = environment_type(**common)
    try:
        env.reset(seed=41)
        env.global_bs_cache = {} if hasattr(env, "global_bs_cache") else None
        env.uav_positions[0] = np.array([0.0, 0.0, 100.0])
        env.uav_positions[1] = np.array([101.0, 0.0, 100.0])
        env.ground_bs_positions[0] = np.array([101.0, 0.0, 100.0])

        outside = env._get_observation("uav_0")["obs"]
        np.testing.assert_array_equal(outside[3:6], np.zeros(3))
        if environment_type is UAVRoutedRelayEnv:
            np.testing.assert_array_equal(outside[9:11], np.zeros(2))
        else:
            assert outside[9] == 0.0

        env.uav_positions[1] = np.array([99.0, 0.0, 100.0])
        env.ground_bs_positions[0] = np.array([99.0, 0.0, 100.0])
        inside = env._get_observation("uav_0")["obs"]
        assert inside.shape == outside.shape
        assert not np.array_equal(inside[3:6], np.zeros(3))
        if environment_type is UAVRoutedRelayEnv:
            assert not np.array_equal(inside[9:11], np.zeros(2))
        else:
            assert inside[9] > 0.0
    finally:
        env.close()


def test_complete_routed_step_is_exact_across_reference_and_cpp_backends():
    reference = _make_routed(backend="python_reference", seed=43)
    optimized = _make_routed(backend="cpp", seed=43)
    try:
        assert _canonical(reference.reset(seed=43)) == _canonical(
            optimized.reset(seed=43)
        )
        action = np.array([0.2, -0.3, 0.1], dtype=np.float32)
        for _ in range(3):
            left = reference.step({agent: action.copy() for agent in reference.agents})
            right = optimized.step({agent: action.copy() for agent in optimized.agents})
            assert _canonical(left) == _canonical(right)
            np.testing.assert_array_equal(
                reference.uav_positions, optimized.uav_positions
            )
            np.testing.assert_array_equal(reference.sinr_matrix, optimized.sinr_matrix)
            assert _canonical(reference.np_random.get_state()) == _canonical(
                optimized.np_random.get_state()
            )
    finally:
        reference.close()
        optimized.close()


def test_complete_forced_relay_step_is_exact_across_reference_and_cpp_backends():
    common = dict(
        n_uavs=4,
        n_users=8,
        n_ground_bs=2,
        n_clusters=4,
        area_size=1000.0,
        max_steps=20,
        user_movement_model="stationary",
        randomize_bs=True,
        randomize_users=True,
        randomize_uav_start=True,
        seed=45,
    )
    reference = UAVForcedRelayEnv(
        **common, relay_geometry_backend="python_reference"
    )
    optimized = UAVForcedRelayEnv(**common, relay_geometry_backend="cpp")
    try:
        assert _canonical(reference.reset(seed=45)) == _canonical(
            optimized.reset(seed=45)
        )
        action = np.array([0.2, -0.3, 0.1], dtype=np.float32)
        for _ in range(2):
            left = reference.step({agent: action.copy() for agent in reference.agents})
            right = optimized.step({agent: action.copy() for agent in optimized.agents})
            assert _canonical(left) == _canonical(right)
            np.testing.assert_array_equal(reference.sinr_matrix, optimized.sinr_matrix)
            assert _canonical(reference.np_random.get_state()) == _canonical(
                optimized.np_random.get_state()
            )
    finally:
        reference.close()
        optimized.close()


def _assert_observation_contract(environment, observations):
    for agent, observation in observations.items():
        space = environment.observation_space(agent)
        for key, value in observation.items():
            assert value.shape == space[key].shape
            assert value.dtype == space[key].dtype
        assert space.contains(observation)


@pytest.mark.parametrize("preset", (None, "S6-S0", "S7-S1"))
def test_reset_and_step_observations_match_declared_dtype_and_shape(preset):
    if preset is None:
        environment = _make_routed(backend="python_reference", seed=49)
        action = np.zeros(3, dtype=np.float32)
    elif preset.startswith("S6"):
        config = Config(preset)
        config.relay_geometry_backend = "python_reference"
        config.max_steps = 4
        environment = UAVProgressiveRelayEnv(config=config, seed=49)
        action = np.zeros(3, dtype=np.float32)
    else:
        config = Config(preset)
        config.relay_geometry_backend = "python_reference"
        config.max_steps = 4
        environment = UAVEnergyAwareRelayEnv(config=config, seed=49)
        action = np.zeros(4, dtype=np.float32)
    try:
        reset_observations, _ = environment.reset(seed=49)
        _assert_observation_contract(environment, reset_observations)
        step_observations = environment.step(
            {agent: action.copy() for agent in environment.agents}
        )[0]
        _assert_observation_contract(environment, step_observations)
    finally:
        environment.close()


def test_cpp_selection_fails_closed_without_native_backend(monkeypatch):
    env = _make_routed(backend="cpp", seed=47)
    monkeypatch.setattr(
        geometry_backend,
        "load_uav_cpp_backend",
        lambda **_kwargs: (_ for _ in ()).throw(
            geometry_backend.UAVCppBackendUnavailable("native unavailable")
        ),
    )
    try:
        with pytest.raises(
            geometry_backend.UAVCppBackendUnavailable, match="native unavailable"
        ):
            env.reset(seed=47)
    finally:
        env.close()


@pytest.mark.parametrize(
    ("field", "mutation"),
    (
        ("tx_power", lambda value: float(value) + 1.0),
        ("ground_bs_tx_power", lambda value: float(value) + 1.0),
        ("noise_power", lambda value: float(value) + 1.0),
        ("carrier_frequency", lambda value: float(value) * 1.01),
        ("use_fdma", lambda value: not bool(value)),
        ("aclr_linear", lambda value: float(value) * 2.0 + 1.0e-9),
        (
            "environment_type",
            lambda value: "suburban" if str(value) != "suburban" else "urban",
        ),
        ("n_uavs", lambda value: int(value) + 1),
        ("n_users", lambda value: int(value) + 1),
        ("n_ground_bs", lambda value: int(value) + 1),
    ),
)
def test_forced_retained_radio_invalidates_every_material_configuration_field(
    field, mutation
) -> None:
    environment = UAVForcedRelayEnv(
        n_uavs=4,
        n_users=8,
        n_ground_bs=2,
        n_clusters=4,
        max_steps=4,
        user_movement_model="stationary",
        relay_geometry_backend="cpp",
        seed=53,
    )
    try:
        environment.reset(seed=53)
        assert environment._retained_radio() is not None
        current = getattr(
            environment, field, "urban" if field == "environment_type" else None
        )
        setattr(environment, field, mutation(current))
        # Even the observation-local position-validation fast path must first
        # validate every scalar/count that determines the retained radio tensor.
        environment._retained_radio_validation_active = True
        assert environment._retained_radio() is None
    finally:
        environment.close()


def test_forced_radio_config_mutation_uses_scalar_fallback_not_stale_tensor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    environment = UAVForcedRelayEnv(
        n_uavs=4,
        n_users=8,
        n_ground_bs=2,
        n_clusters=4,
        max_steps=4,
        user_movement_model="stationary",
        relay_geometry_backend="cpp",
        seed=59,
    )
    try:
        environment.reset(seed=59)
        assert environment._retained_radio() is not None
        environment.tx_power = float(environment.tx_power) + 1.0
        calls = []

        def scalar_fallback(uav_idx, user_idx, rx_power):
            calls.append((uav_idx, user_idx, rx_power))
            return 123.25

        monkeypatch.setattr(
            environment, "_compute_uav_to_user_sinr", scalar_fallback
        )
        assert environment._compute_sinr(0, 0) == 123.25
        assert calls and calls[0][:2] == (0, 0)
    finally:
        environment.close()
