import numpy as np
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
pytest.importorskip("gymnasium")

from _scenario7_fixtures import make_env, zero_actions


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
