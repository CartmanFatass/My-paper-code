import numpy as np
import pytest
import sys
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
pytest.importorskip("gymnasium")

from config_1 import Config
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from envs.pettingzoo.scenario7_energy_aware import UAVEnergyAwareRelayEnv
from train_multiproc_config_1 import validate_scenario7_configuration


def capture_structured_evidence(value):
    """Canonicalize the small set of structured values used by this test."""

    if isinstance(value, np.ndarray):
        array = np.ascontiguousarray(value)
        return ("ndarray", array.dtype.str, array.shape, array.tobytes())
    if isinstance(value, np.generic):
        scalar = np.asarray(value)
        return ("numpy-scalar", scalar.dtype.str, scalar.tobytes())
    if isinstance(value, dict):
        return (
            "dict",
            tuple(
                (capture_structured_evidence(key), capture_structured_evidence(item))
                for key, item in value.items()
            ),
        )
    if isinstance(value, (list, tuple)):
        return (
            type(value).__name__,
            tuple(capture_structured_evidence(item) for item in value),
        )
    return (type(value).__name__, value)


def capture_environment_rng_state(adapter):
    scenario_rng = adapter.env.np_random
    adapter_rng = adapter.np_random
    return (
        capture_structured_evidence(scenario_rng.get_state()),
        capture_structured_evidence(adapter_rng.bit_generator.state),
    )


def rng_states_equal(left, right):
    return left == right


def make_env(preset="S7-S3", seed=123):
    config = Config(preset)
    config.max_steps = 8
    return UAVEnergyAwareRelayEnv(config=config, seed=seed)


def make_variant_env(variant, seed=123):
    config = Config("S7-S3")
    config.apply_scenario7_reward_variant(variant)
    config.max_steps = 8
    return UAVEnergyAwareRelayEnv(config=config, seed=seed)


def make_arm_env(arm, seed=123):
    config = Config("S7-S3")
    config.apply_scenario7_experiment_arm(arm)
    config.max_steps = 8
    return UAVEnergyAwareRelayEnv(config=config, seed=seed)


def zero_actions(env):
    return {agent: np.zeros(4, dtype=np.float32) for agent in env.agents}


def test_s7_s3_uses_load_balance_and_seeded_station_layout():
    env_a = make_env("S7-S3", seed=123)
    env_a.reset(seed=123)
    env_b = make_env("S7-S3", seed=123)
    env_b.reset(seed=123)
    env_c = make_env("S7-S3", seed=124)
    env_c.reset(seed=124)

    assert env_a.reward_type == "load_balance"
    assert env_a.energy_stage == "S3"
    np.testing.assert_allclose(env_a.charging_station_positions, env_b.charging_station_positions)
    assert not np.allclose(env_a.charging_station_positions, env_c.charging_station_positions)


def test_power_model_hover_endurance_matches_current_defaults():
    env = make_env("S7-S3")
    hover_power = env._calculate_power_consumption(0.0, 0.0)
    endurance_steps = 0.75 * env.battery_capacity_wh / (hover_power * env.time_step / 3600.0)

    assert np.isclose(hover_power, 168.49)
    assert env.battery_capacity_wh == 160.0
    assert 2560 <= endurance_steps <= 2570


def test_finite_charging_slot_selects_lowest_battery_candidate():
    env = make_env("S7-S3", seed=7)
    env.reset(seed=7)
    env.n_charging_stations = 1
    env.charging_station_capacity[:] = [1.0, 1.0]
    env.uav_failed[:] = False

    station = env.charging_station_positions[0].copy()
    env.uav_positions[:3] = station
    env.uav_battery_ratios[:3] = [0.20, 0.08, 0.12]
    env.charging_wait_steps[:3] = [0, 0, 10]
    env.uav_dock_requests[:3] = True
    env.uav_target_stations[:3] = 0

    pre_positions = env.uav_positions.copy()
    commanded_velocities = np.zeros((env.n_uavs, 3), dtype=float)
    env._apply_energy_dynamics(pre_positions, commanded_velocities)

    assert int(np.sum(env.uav_charging[:3])) == 1
    assert env.uav_charging[1]
    assert env.station_occupancy[0] == 1
    assert env.station_queue_lengths[0] == 2


def test_critical_battery_limp_home_keeps_motion_but_disables_service():
    env = make_env("S7-S3", seed=11)
    env.reset(seed=11)
    env.uav_failed[:] = False
    env.uav_battery_ratios[0] = env.service_cutoff_threshold * 0.5
    env.uav_positions[0] = np.array([env.area_size, env.area_size, env.height_range[1]], dtype=float)

    _, distance = env._nearest_charging_station_vector(0)
    assert distance > env.charging_radius_m
    assert env._is_uav_unavailable(0)

    actions = {agent: np.ones(4, dtype=np.float32) for agent in env.agents}
    adjusted, velocities = env._prepare_energy_actions(actions)

    assert np.linalg.norm(velocities[0]) <= env.limp_home_speed_mps + 1e-6
    assert np.linalg.norm(np.asarray(adjusted[env.agents[0]], dtype=float)) > 0

    env.uav_battery_ratios[0] = 0.0
    adjusted, velocities = env._prepare_energy_actions(actions)
    np.testing.assert_allclose(velocities[0], np.zeros(3))
    np.testing.assert_allclose(adjusted[env.agents[0]], np.zeros(3))


def test_four_dimensional_action_semantics_and_docking_speed_limits():
    env = make_env("S7-S3", seed=19)
    env.reset(seed=19)
    assert env.action_space(env.agents[0]).shape == (4,)

    movement = env._movement_velocity_from_action(np.array([1.0, 0.0, 1.0]))
    np.testing.assert_allclose(movement, [env.max_speed, 0.0, env.max_vertical_speed_mps])

    station = env.charging_station_positions[0].copy()
    env.uav_positions[0] = station + np.array([100.0, 0.0, 20.0])
    actions = zero_actions(env)
    actions[env.agents[0]] = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32)
    _, velocities = env._prepare_energy_actions(actions)

    assert np.linalg.norm(velocities[0, :2]) <= env.docking_horizontal_speed_mps + 1e-6
    assert abs(velocities[0, 2]) <= env.docking_vertical_speed_mps + 1e-6
    assert env.uav_dock_requests[0]
    assert env.uav_target_stations[0] == 0


def test_charging_requires_request_capture_and_actual_hover():
    env = make_env("S7-S3", seed=23)
    env.reset(seed=23)
    env.n_charging_stations = 1
    env.uav_positions[0] = env.charging_station_positions[0]
    env.uav_battery_ratios[0] = 0.5
    pre_positions = env.uav_positions.copy()

    env._apply_energy_dynamics(pre_positions, np.zeros((env.n_uavs, 3)))
    assert not env.uav_charging[0]

    env.uav_dock_requests[0] = True
    env.uav_target_stations[0] = 0
    before = env.uav_battery_ratios[0]
    env._apply_energy_dynamics(pre_positions, np.zeros((env.n_uavs, 3)))
    assert env.uav_charging[0]
    assert env.uav_battery_ratios[0] > before

    env.uav_positions[0] = env.charging_station_positions[0] + np.array([
        env.charging_capture_radius_m + 1.0, 0.0, 0.0
    ])
    pre_positions = env.uav_positions.copy()
    env._apply_energy_dynamics(pre_positions, np.zeros((env.n_uavs, 3)))
    assert not env.uav_charging[0]


def test_effective_charging_episode_statistics_count_transition_and_energy():
    env = make_env("S7-S3", seed=25)
    env.reset(seed=25)
    env.n_charging_stations = 1
    env.uav_failed[:] = False
    env.uav_positions[0] = env.charging_station_positions[0]
    env.uav_battery_ratios[0] = 0.5

    actions = zero_actions(env)
    actions[env.agents[0]][3] = 1.0
    _, _, _, _, infos = env.step(actions)
    first = infos[env.agents[0]]["reward_info"]

    assert first["episode_charging_session_count"] == 1
    assert first["episode_first_effective_charge_step"] == 1
    assert first["episode_charging_uav_steps"] >= 1
    assert first["episode_energy_charged_wh"] > 0.0

    _, _, _, _, infos = env.step(actions)
    second = infos[env.agents[0]]["reward_info"]
    assert second["episode_charging_session_count"] == 1
    assert second["episode_first_effective_charge_step"] == 1
    assert second["episode_charging_uav_steps"] > first["episode_charging_uav_steps"]
    assert second["episode_energy_charged_wh"] > first["episode_energy_charged_wh"]


def test_1000w_charging_uses_net_energy_after_hover_consumption():
    env = make_env("S7-S3", seed=27)
    env.reset(seed=27)
    env.n_charging_stations = 1
    env.uav_positions[0] = env.charging_station_positions[0]
    env.uav_battery_ratios[0] = 0.5
    env.uav_dock_requests[0] = True
    env.uav_target_stations[0] = 0
    before = env.uav_battery_ratios[0]

    env._apply_energy_dynamics(
        env.uav_positions.copy(),
        np.zeros((env.n_uavs, 3), dtype=float),
    )

    hover_power = env._calculate_power_consumption(0.0, 0.0)
    expected_delta = (
        (env.charging_power_w - hover_power)
        * env.time_step
        / 3600.0
        / env.battery_capacity_wh
    )
    assert np.isclose(env.uav_battery_ratios[0] - before, expected_delta)
    assert np.isclose(
        env.last_net_energy_charged_wh[0],
        (env.charging_power_w - hover_power) * env.time_step / 3600.0,
    )
    assert env.last_energy_charged_wh[0] > env.last_net_energy_charged_wh[0]


def test_dynamic_return_threshold_and_service_cutoff_are_separate():
    env = make_env("S7-S3", seed=29)
    env.reset(seed=29)
    env.uav_positions[0] = np.array([env.area_size, env.area_size, env.height_range[1]])
    env._update_return_energy_state()

    assert env.return_threshold_min <= env.uav_return_threshold_ratios[0] <= env.return_threshold_max
    assert np.isclose(
        env.uav_return_energy_margins[0],
        env._raw_return_energy_margins()[0],
    )
    env.uav_battery_ratios[0] = env.emergency_return_threshold - 0.001
    assert env._is_uav_in_limp_home(0)
    assert not env._is_uav_unavailable(0)
    env.uav_battery_ratios[0] = env.service_cutoff_threshold - 0.001
    assert env._is_uav_unavailable(0)


def test_observation_and_state_use_fixed_team_and_station_identity():
    env = make_env("S7-S3", seed=31)
    observations, _ = env.reset(seed=31)
    agent = env.agents[0]

    assert env.n_uavs == 8
    assert env.max_energy_observed_uavs == 8
    assert observations[agent]["obs"].shape == (env.obs_dim,)
    assert env._get_state().shape == (env.state_dim,)
    assert env.energy_obs_extra_dim == 8 * 13 + 2 * 8


def test_failed_uav_consumes_hover_power_and_s4_keeps_six_active():
    env = make_env("S7-S4", seed=37)
    env.reset(seed=37)
    env.uav_failed[0] = True
    before = env.uav_battery_ratios[0]
    env._apply_energy_dynamics(
        env.uav_positions.copy(),
        np.zeros((env.n_uavs, 3), dtype=float),
    )
    assert env.uav_battery_ratios[0] < before

    env.uav_failure_probability = 1.0
    env.uav_failure_timers[:] = 0
    env.uav_failed[:] = False
    env._update_uav_failures()
    assert np.sum(~env.uav_failed) >= 6


def test_episode_terminates_when_every_uav_is_exhausted():
    env = make_env("S7-S3", seed=41)
    env.reset(seed=41)
    env.uav_battery_ratios[:] = 0.0

    _, _, terminations, truncations, _ = env.step(zero_actions(env))
    assert all(terminations.values())
    assert not any(truncations.values())


def test_startup_validation_accepts_parallel_array_adapter():
    config = Config("S7-S3")
    raw_env = UAVEnergyAwareRelayEnv(config=config, seed=43)
    adapter = ParallelToArrayAdapter(raw_env, seed=43)
    args = SimpleNamespace(scenario="energy", config="config_1")
    try:
        validate_scenario7_configuration(config, args, env=adapter)
    finally:
        adapter.close()


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


def test_constrained_safety_reward_metrics_are_exposed():
    env = make_env("S7-S3", seed=5)
    env.reset(seed=5)

    _, rewards, _, _, infos = env.step(zero_actions(env))
    reward_info = infos[env.agents[0]]["reward_info"]

    assert reward_info["scenario7_reward_model"] == "constrained_qos_safety_pbrs_v2"
    assert "qos_satisfaction_ratio" in reward_info
    assert "normalized_propulsion_energy" in reward_info
    assert "return_constraint_cost" in reward_info
    assert "return_constraint_cost_raw" in reward_info
    assert reward_info["return_cost_cap"] == 1.0
    assert "return_risk_penalty" in reward_info
    assert "cutoff_event_count" in reward_info
    assert "depletion_event_count" in reward_info
    assert "graph_potential_delta" in reward_info
    assert "instantaneous_bits_per_joule" in reward_info
    assert np.isclose(
        reward_info["scenario7_reward"],
        reward_info["safety_reward_before_pbrs"]
        + reward_info["graph_potential_delta"],
    )
    assert np.isfinite(np.mean(list(rewards.values())))


def test_end_to_end_rate_respects_access_and_backhaul_and_avoids_soft_handover_double_count(monkeypatch):
    env = make_env("S7-S3", seed=47)
    env.reset(seed=47)
    env.connections[:] = False
    env.connections[0, 0] = True
    env.connections[1, 0] = True
    env.connections[0, 1] = True
    env.routing_paths = {
        0: ([("uav", 0), ("ground_bs", 0)], 6e6),
        1: ([("uav", 1), ("ground_bs", 0)], 2e6),
    }

    def fixed_access(uav_idx, user_idx, bandwidth_hz, relaxed):
        capacities = {
            (0, 0): 4e6,
            (0, 1): 4e6,
            (1, 0): 3e6,
        }
        return capacities.get((uav_idx, user_idx), 0.0)

    monkeypatch.setattr(env, "_access_capacity_bps", fixed_access)
    rates, access, backhaul = env._calculate_end_to_end_user_rates()

    # UAV 0 has 8 Mbps access and 6 Mbps backhaul, so both links are scaled to 3 Mbps.
    assert np.isclose(rates[0], 3e6)
    assert np.isclose(rates[1], 3e6)
    # UAV 1 offers only 2 Mbps after backhaul scaling; soft handover takes max, not sum.
    assert np.sum(rates) <= np.sum(np.minimum(np.sum(access, axis=1), backhaul)) + 1e-6
    assert np.isclose(rates[0], max(3e6, 2e6))


def test_graph_pbrs_has_discounted_telescope_boundary():
    env = make_env("S7-S3", seed=53)
    gamma = env.reward_discount_gamma
    potentials = [0.2, 0.5, 0.4, 0.7]
    rewards = [
        env._graph_potential_reward(potentials[t], potentials[t + 1], terminal=False)
        for t in range(len(potentials) - 1)
    ]
    rewards.append(env._graph_potential_reward(potentials[-1], 0.0, terminal=True))

    discounted_sum = sum((gamma ** t) * reward for t, reward in enumerate(rewards))
    assert np.isclose(discounted_sum, -potentials[0])


def test_graph_potential_increases_when_relay_moves_toward_reachable_backhaul(monkeypatch):
    env = make_env("S7-S3", seed=57)
    env.reset(seed=57)
    qos_bps = env.user_qos_rate_mbps * 1e6
    monkeypatch.setattr(
        env,
        "_access_capacity_bps",
        lambda *args, **kwargs: 2.0 * qos_bps,
    )

    bs_xy = env.ground_bs_positions[0, :2].copy()

    def position_based_backhaul():
        distances = np.linalg.norm(env.uav_positions[:, :2] - bs_xy, axis=1)
        return np.clip(1.0 - distances / (env.area_size * np.sqrt(2.0)), 0.0, 1.0) * qos_bps

    monkeypatch.setattr(env, "_widest_backhaul_capacities", position_based_backhaul)
    env.uav_positions[:, :2] = env.area_size
    far_potential = env._graph_service_potential()
    env.uav_positions[0, :2] = bs_xy
    near_potential = env._graph_service_potential()

    assert near_potential > far_potential


def test_runtime_safety_dual_changes_only_adaptive_return_penalty():
    env = make_variant_env("qos_adaptive_safety_graph_pbrs", seed=59)
    env.reset(seed=59)
    env.set_scenario7_safety_dual(3.0)
    _, _, _, _, infos = env.step(zero_actions(env))
    metrics = infos[env.agents[0]]["reward_info"]

    assert metrics["safety_dual"] == 3.0
    assert metrics["return_penalty_coefficient"] == 3.0
    assert np.isclose(
        metrics["return_risk_penalty"],
        3.0 * metrics["return_constraint_cost"],
    )


@pytest.mark.parametrize(
    "variant",
    [
        "qos_only",
        "qos_depletion_penalty",
        "qos_fixed_safety",
        "qos_fixed_safety_graph_pbrs",
        "qos_adaptive_safety_graph_pbrs",
    ],
)
def test_reward_ablation_variants_have_explicit_objectives(variant):
    env = make_variant_env(variant, seed=61)
    env.reset(seed=61)
    _, rewards, _, _, infos = env.step(zero_actions(env))
    metrics = infos[env.agents[0]]["reward_info"]
    reward = rewards[env.agents[0]]

    if variant == "qos_only":
        expected = metrics["qos_satisfaction_ratio"]
    elif variant == "qos_depletion_penalty":
        expected = (
            metrics["qos_satisfaction_ratio"]
            - metrics["depletion_event_penalty"]
        )
    elif variant == "qos_fixed_safety":
        expected = metrics["safety_reward_before_pbrs"]
        assert metrics["shaping_potential_delta"] == 0.0
    else:
        expected = (
            metrics["safety_reward_before_pbrs"]
            + metrics["shaping_potential_delta"]
        )

    assert metrics["scenario7_reward_variant"] == variant
    assert np.isclose(reward, expected)


def test_return_constraint_is_zero_for_positive_margins_and_uses_worst_uav(monkeypatch):
    env = make_variant_env("qos_fixed_safety", seed=67)
    env.reset(seed=67)
    monkeypatch.setattr(
        env,
        "_calculate_end_to_end_user_rates",
        lambda: (
            np.zeros(env.n_users),
            np.zeros((env.n_uavs, env.n_users)),
            np.zeros(env.n_uavs),
        ),
    )
    monkeypatch.setattr(env, "_normalized_step_energy", lambda: (0.0, 0.0))

    monkeypatch.setattr(
        env,
        "_raw_return_energy_margins",
        lambda: np.full(env.n_uavs, 0.01),
    )
    safe = env._calculate_constrained_safety_reward(
        0.0, 0.0, 0.0, 0.0, False, 0.0, {}
    )
    assert safe["return_constraint_cost"] == 0.0

    margins = np.full(env.n_uavs, 0.20)
    margins[3] = -0.05
    monkeypatch.setattr(env, "_raw_return_energy_margins", lambda: margins)
    unsafe = env._calculate_constrained_safety_reward(
        0.0, 0.0, 0.0, 0.0, False, 0.0, {}
    )
    assert np.isclose(unsafe["return_constraint_cost"], 1.0)
    assert np.isclose(unsafe["return_risk_penalty"], env.lambda_return)


def test_v2_return_risk_is_bounded_even_for_severe_deficit(monkeypatch):
    env = make_arm_env("C", seed=69)
    env.reset(seed=69)
    margins = np.full(env.n_uavs, 0.20)
    margins[5] = -0.25
    monkeypatch.setattr(env, "_raw_return_energy_margins", lambda: margins)

    metrics = env._calculate_constrained_safety_reward(
        0.0, 0.0, 0.0, 0.0, False, 0.0, {}
    )

    assert np.isclose(metrics["return_constraint_cost_raw"], 5.0)
    assert metrics["return_constraint_cost"] == 1.0
    assert metrics["return_risk_penalty"] == 2.0
    assert 0.0 <= metrics["return_risk_penalty"] <= 2.0


def test_arm_a_preserves_unbounded_v1_return_risk(monkeypatch):
    env = make_arm_env("A", seed=70)
    env.reset(seed=70)
    margins = np.full(env.n_uavs, 0.20)
    margins[5] = -0.25
    monkeypatch.setattr(env, "_raw_return_energy_margins", lambda: margins)

    metrics = env._calculate_constrained_safety_reward(
        0.0, 0.0, 0.0, 0.0, False, 0.0, {}
    )

    assert env.scenario7_reward_model == "constrained_qos_safety_pbrs_v1"
    assert env.battery_capacity_wh == 200.0
    assert np.isinf(metrics["return_cost_cap"])
    assert metrics["return_constraint_cost_raw"] == 5.0
    assert metrics["return_constraint_cost"] == 5.0
    assert metrics["return_risk_penalty"] == 10.0


def test_cutoff_and_depletion_events_fire_once_per_uav(monkeypatch):
    env = make_variant_env("qos_fixed_safety", seed=71)
    env.reset(seed=71)
    monkeypatch.setattr(
        env,
        "_calculate_end_to_end_user_rates",
        lambda: (
            np.zeros(env.n_users),
            np.zeros((env.n_uavs, env.n_users)),
            np.zeros(env.n_uavs),
        ),
    )
    monkeypatch.setattr(env, "_normalized_step_energy", lambda: (0.0, 0.0))
    monkeypatch.setattr(
        env,
        "_raw_return_energy_margins",
        lambda: np.ones(env.n_uavs),
    )

    env.uav_battery_ratios[0] = env.service_cutoff_threshold * 0.5
    first_cutoff = env._calculate_constrained_safety_reward(
        0.0, 0.0, 0.0, 0.0, False, 0.0, {}
    )
    repeated_cutoff = env._calculate_constrained_safety_reward(
        0.0, 0.0, 0.0, 0.0, False, 0.0, {}
    )
    assert first_cutoff["cutoff_event_count"] == 1
    assert repeated_cutoff["cutoff_event_count"] == 0

    env.uav_battery_ratios[0] = 0.0
    first_depletion = env._calculate_constrained_safety_reward(
        0.0, 0.0, 0.0, 0.0, False, 0.0, {}
    )
    repeated_depletion = env._calculate_constrained_safety_reward(
        0.0, 0.0, 0.0, 0.0, False, 0.0, {}
    )
    assert first_depletion["cutoff_event_count"] == 0
    assert first_depletion["depletion_event_count"] == 1
    assert repeated_depletion["depletion_event_count"] == 0


def test_legacy_ablation_restores_original_reward_weights():
    config = Config("S7-S3")
    config.apply_scenario7_reward_variant("legacy_engineering")

    assert config.w_load_balance == 0.35
    assert config.w_backhaul_outage == 0.8
    assert config.w_energy_motion == 0.02
    assert config.w_charge_progress == 0.20


@pytest.mark.parametrize("seed", [0, 3, 7])
def test_heuristic_layout_demonstrates_configured_qos_feasibility(seed):
    env = make_env("S7-S3", seed=seed)
    env.reset(seed=seed)
    result = env.estimate_heuristic_qos_feasibility()

    assert result["feasible"]
    assert result["qos_satisfaction_ratio"] >= env.qos_target_ratio


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_rotation_charging_certificate_is_physically_feasible(seed):
    config = Config("S7-S3")
    env = UAVEnergyAwareRelayEnv(config=config, seed=seed)
    env.reset(seed=seed)
    result = env.estimate_rotation_charging_feasibility()

    assert result["effective_charging"]
    assert result["depletion_free"]
    assert (
        result["rotation_qos_satisfaction_ratio"]
        >= config.scenario7_heuristic_qos_min
    )
