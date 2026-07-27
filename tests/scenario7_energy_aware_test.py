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
    pre_positions = env.uav_positions.copy()
    actions = zero_actions(env)
    actions[env.agents[0]] = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32)
    _, velocities = env._prepare_energy_actions(actions)

    # Pin the expected docking speed as a LITERAL from the frozen spec
    # (`config_1.py:504`, `docking_horizontal_speed_mps = 3.0`), not against
    # the live `env.docking_horizontal_speed_mps` attribute the production
    # clamp (`_docking_velocity`, ":1643") itself uses -- a clamped value
    # bounded by its own clamp attribute holds for ANY setting of that
    # attribute, so it could not have caught `config_1.py:504` being changed
    # to `1.0` (measured 2026-07-27: 44/44 green under that mutation with the
    # old assertion). If this literal and the configuration ever disagree,
    # the configuration is wrong until a round says otherwise -- do not edit
    # this literal to match the code.
    expected_docking_horizontal_speed_mps = 3.0
    horizontal_speed = float(np.linalg.norm(velocities[0, :2]))
    # The UAV is 100 m out (past both the capture and charging-approach
    # radii), so the only thing capping horizontal speed here is the
    # configured docking limit -- not distance/dt, not max_speed (30).
    assert np.isclose(horizontal_speed, expected_docking_horizontal_speed_mps, atol=1e-6)
    # Discriminating form: a UAV under a 1.0 m/s docking cap cannot exceed
    # 1.0 m/s here; only something above it (the configured 3.0) can.
    assert horizontal_speed > 1.0 + 1e-6
    assert abs(velocities[0, 2]) <= env.docking_vertical_speed_mps + 1e-6
    assert env.uav_dock_requests[0]
    assert env.uav_target_stations[0] == 0

    # Reach: the same speed must move `uav_positions` itself each step, not
    # just the intermediate `velocities` array this test inspects above --
    # `_docking_velocity` feeds `commanded_velocities`, which the base
    # environment's `step` turns directly into displacement.
    env.step(actions)
    horizontal_displacement = float(
        np.linalg.norm(env.uav_positions[0, :2] - pre_positions[0, :2])
    )
    assert np.isclose(
        horizontal_displacement,
        expected_docking_horizontal_speed_mps * env.time_step,
        atol=1e-3,
    )


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


def test_charging_hover_gate_excludes_a_moving_uav_but_not_a_hovering_one():
    # Two UAVs, otherwise identical: same station, same distance (0 m, both
    # sitting on the pad), same requested dock, same starting battery. The
    # only difference is the ACTUAL velocity implied by the position delta
    # across the step: UAV 0 hovers (zero displacement), UAV 1 is credited
    # with a displacement that implies a speed above
    # `charging_hover_speed_threshold`. If the hover gate at
    # `_charging_candidates_by_station` (":1784-1785") is deleted, both UAVs
    # become eligible and, with two free slots at the station, both get
    # selected and charged -- this pair is what would go red under that
    # deletion. A single hovering UAV cannot show that: charging.py already
    # asserts the positive case in
    # `test_charging_requires_request_capture_and_actual_hover`.
    env = make_env("S7-S3", seed=73)
    env.reset(seed=73)
    env.n_charging_stations = 1
    env.charging_station_capacity[:] = 2.0  # room for both, so the gate --
    # not slot contention -- is what must exclude UAV 1.
    env.uav_failed[:] = False

    station = env.charging_station_positions[0].copy()
    env.uav_battery_ratios[:2] = 0.5
    env.uav_positions[:2] = station
    env.uav_dock_requests[:2] = True
    env.uav_target_stations[:2] = 0

    pre_positions = env.uav_positions.copy()
    speed_above_threshold = env.charging_hover_speed_threshold + 5.0
    displacement = speed_above_threshold * env.time_step
    pre_positions[1] = station + np.array([displacement, 0.0, 0.0])

    before = env.uav_battery_ratios.copy()
    env._apply_energy_dynamics(pre_positions, np.zeros((env.n_uavs, 3)))

    # The hovering UAV is credited with charge -- the field that actually
    # reaches battery state, `_energy_failure_mask` and the 5.0/10.0-weighted
    # safety penalties, not a diagnostic sibling.
    assert env.uav_charging[0]
    assert env.uav_battery_ratios[0] > before[0]
    # The moving UAV must NOT be credited: no charge added, battery only
    # falls from its own consumption.
    assert not env.uav_charging[1]
    assert env.uav_battery_ratios[1] < before[1]


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

    # The two assertions this test used to make could not fail.
    #
    #   `return_threshold_min <= x <= return_threshold_max` is the clamp
    #   asserting its own bounds -- true for every implementation that clamps,
    #   including one that ignores distance and returns a constant.
    #
    #   `isclose(uav_return_energy_margins[0], _raw_return_energy_margins()[0])`
    #   compared two copies of the SAME formula: `_update_return_energy_state`
    #   and `_raw_return_energy_margins` each write out
    #   `battery - required_ratio - reserve` independently. Both sides came from
    #   the code, neither from an independent source of truth, so a wrong
    #   formula moved both together and stayed green.
    #
    # Measured 2026-07-27: replacing the threshold with the constant
    # `return_threshold_min` left 42/42 of this file green and 197/197 of the
    # D7.S set green. The threshold is not a cosmetic field -- it drives the
    # return trigger (`:1908`, `:2035`) and is observation feature 7
    # (`:2250`), so a constant one changes trajectories and what the policy
    # sees. It does not enter primary `G` directly: `return_constraint_cost`
    # reads `_raw_return_energy_margins()`, not the threshold.

    # Paired negative 1 -- the threshold must DISCRIMINATE on distance. No
    # constant can satisfy this, and it needs no re-derivation of the physics.
    near = np.asarray(env.charging_station_positions[0], dtype=float).copy()
    near[2] = env.height_range[0]
    env.uav_positions[1] = near
    env._update_return_energy_state()
    far_threshold = env.uav_return_threshold_ratios[0]
    near_threshold = env.uav_return_threshold_ratios[1]
    assert far_threshold > near_threshold, (
        "a UAV in the far corner must carry a strictly higher return threshold "
        f"than one parked at a station; got far={far_threshold} near={near_threshold}"
    )
    assert env.return_threshold_min <= near_threshold <= far_threshold <= env.return_threshold_max

    # Paired negative 2 -- the margin against an INDEPENDENT arithmetic path,
    # not against the production function that computes it. The hover/travel
    # power model is separately pinned by
    # `test_power_model_hover_endurance_matches_current_defaults`, so taking
    # the power figure from it is a pinned input rather than the same code.
    _, _, distance = env._nearest_charging_station(0)
    power_w = env._calculate_power_consumption(env.limp_home_speed_mps, 0.0)
    expected_margin = (
        env.uav_battery_ratios[0]
        - ((distance / env.limp_home_speed_mps) * power_w / 3600.0) / env.battery_capacity_wh
        - env.return_reserve_ratio
    )
    assert np.isclose(env.uav_return_energy_margins[0], expected_margin), (
        f"margin {env.uav_return_energy_margins[0]} disagrees with the physics "
        f"recomputed here: {expected_margin}")

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


def test_energy_observation_slot_k_carries_uav_ks_own_state():
    # Anchor: `_energy_observation` (":2190") writes each UAV's own 13-field
    # record at `start = uav_idx * self.energy_uav_obs_dim`. The only
    # existing test that touches this structure,
    # `test_observation_and_state_use_fixed_team_and_station_identity`,
    # asserts dimensions only -- a shape assertion cannot see a permutation.
    # Measured 2026-07-27: replacing `start` with
    # `(min(n_uavs, max_energy_observed_uavs) - 1 - uav_idx) *
    # energy_uav_obs_dim` -- binding every slot to the wrong UAV -- still
    # left 44/44 green, because the array's shape and the *set* of records it
    # contains are unchanged; only which slot holds which UAV's record moves.
    #
    # This checks CONTENT identity, not shape: every UAV is given a distinct
    # battery ratio (identical UAVs would make any permutation
    # undetectable), and slot k must report UAV k's own ratio -- the
    # `battery_ratio` field at record offset 3, the same field
    # `_energy_failure_mask` and the safety penalties are keyed on, not a
    # convenient sibling.
    env = make_env("S7-S3", seed=63)
    env.reset(seed=63)
    assert env.battery_enabled

    n = min(env.n_uavs, env.max_energy_observed_uavs)
    assert n == env.n_uavs  # fixture precondition: every UAV gets a slot
    distinct_battery_ratios = np.linspace(0.10, 0.90, n)
    assert len(set(distinct_battery_ratios)) == n  # genuinely distinguishable
    env.uav_battery_ratios[:n] = distinct_battery_ratios

    energy_obs = env._energy_observation(0)
    battery_ratio_field_offset = 3

    for uav_idx in range(n):
        start = uav_idx * env.energy_uav_obs_dim
        slot_battery_ratio = energy_obs[start + battery_ratio_field_offset]
        assert np.isclose(slot_battery_ratio, env.uav_battery_ratios[uav_idx]), (
            f"slot {uav_idx} reports battery ratio {slot_battery_ratio}, but "
            f"UAV {uav_idx}'s own battery ratio is "
            f"{env.uav_battery_ratios[uav_idx]} -- the per-slot record has "
            "been re-bound to a different UAV")


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


def test_episode_survives_when_only_some_uavs_are_exhausted():
    # The termination gate at ":559-563" is `np.all(... <= 0.0)`: the whole
    # fleet must be dead, not just one member. `test_episode_terminates_
    # when_every_uav_is_exhausted` alone cannot show this -- an all-dead
    # fixture terminates identically whether the quantifier is `all` or
    # `any`. This fixture puts SOME but not all UAVs at zero battery: it must
    # survive under `all` (the frozen contract) and would wrongly end the
    # episode on the first dead UAV under `any`.
    env = make_env("S7-S3", seed=42)
    env.reset(seed=42)
    env.uav_battery_ratios[:] = 0.5
    env.uav_battery_ratios[0] = 0.0
    env.uav_battery_ratios[1] = 0.0
    env.uav_charging[:] = False

    _, _, terminations, truncations, _ = env.step(zero_actions(env))

    assert not np.all(env.uav_battery_ratios <= 0.0), (
        "fixture invalid: the whole fleet drained to zero, which cannot "
        "discriminate `all` from `any`")
    assert not any(terminations.values()), (
        "episode ended with some UAVs still alive -- the termination "
        "quantifier is not the frozen `np.all` over the whole fleet")
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


def test_scenario7_skips_discarded_base_views_without_changing_transitions():
    fast = make_env("S7-S1", seed=45)
    reference = make_env("S7-S1", seed=45)
    assert getattr(fast, "_defer_base_view_materialization", False)
    reference._defer_base_view_materialization = False

    fast._get_observation = Mock(wraps=fast._get_observation)
    reference._get_observation = Mock(wraps=reference._get_observation)
    fast._get_state = Mock(wraps=fast._get_state)
    reference._get_state = Mock(wraps=reference._get_state)
    try:
        fast_reset = fast.reset(seed=45)
        reference_reset = reference.reset(seed=45)
        assert capture_structured_evidence(fast_reset) == capture_structured_evidence(
            reference_reset
        )
        assert fast._get_observation.call_count == fast.n_uavs
        assert reference._get_observation.call_count == 2 * reference.n_uavs
        assert fast._get_state.call_count == 1
        assert reference._get_state.call_count == 2

        fast._get_observation.reset_mock()
        reference._get_observation.reset_mock()
        fast._get_state.reset_mock()
        reference._get_state.reset_mock()
        actions = zero_actions(fast)
        fast_step = fast.step(actions)
        reference_step = reference.step(zero_actions(reference))

        assert capture_structured_evidence(fast_step) == capture_structured_evidence(
            reference_step
        )
        assert fast._get_observation.call_count == fast.n_uavs
        assert reference._get_observation.call_count == 2 * reference.n_uavs
        assert fast._get_state.call_count == 1
        assert reference._get_state.call_count == 2
        assert rng_states_equal(
            capture_structured_evidence(fast.np_random.get_state()),
            capture_structured_evidence(reference.np_random.get_state()),
        )
    finally:
        fast.close()
        reference.close()


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

    def fixed_access(uav_idx, user_idx, bandwidth_hz, relaxed, **_reuse_context):
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

    def position_based_backhaul(**_reuse_context):
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
def test_reward_ablation_variants_have_explicit_objectives(variant, monkeypatch):
    # Measured 2026-07-27: under the previous fixture (a fresh reset, then a
    # single `env.step` with all-zero actions) `depletion_penalty` is 0.0 at
    # this seed and step for every arm, so `qos_depletion_penalty`'s
    # `- depletion_penalty` term was the identity and deleting it outright at
    # `envs/pettingzoo/scenario7_energy_aware.py:807` still left every test in
    # this file green. The five arms realized only two distinct numbers.
    #
    # This fixture forces exactly one UAV across the depleted-battery
    # threshold (`depleted_battery_threshold == 0.0`) for the first time it
    # is ever checked, which is simultaneously a genuine
    # `depletion_event_count == 1` and -- because
    # `service_cutoff_threshold == 0.02 > 0.0` -- a genuine
    # `cutoff_event_count == 1`. Both penalties are then strictly positive,
    # so the arms that include them are forced away from the ones that don't.
    #
    # `_calculate_constrained_safety_reward` is called directly (the same
    # pattern `test_cutoff_and_depletion_events_fire_once_per_uav` already
    # uses) instead of through `env.step`, so QoS and the return margin are
    # pinned to exact literals rather than left to network physics. The
    # expected reward for each arm is then a closed-form sum of config-level
    # constants (`env.cutoff_event_penalty`, `env.depletion_event_penalty`)
    # and the literal event count (1) this fixture engineers -- never a
    # value read back out of the same `reward_info` dict the assertion
    # checks, which is the two-copies trap the previous version of this test
    # was already in.
    env = make_variant_env(variant, seed=61)
    env.reset(seed=61)

    assert env.depleted_battery_threshold == 0.0
    assert env.service_cutoff_threshold > 0.0

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
        lambda: np.full(env.n_uavs, 0.5),
    )

    env.uav_battery_ratios[:] = 0.9
    env.uav_battery_ratios[2] = 0.0

    metrics = env._calculate_constrained_safety_reward(
        0.0, 0.0, 0.0, 0.0, False, 0.0, {}
    )

    # Fixture sanity, not the property under test: confirm the engineered
    # single-UAV crossing produced exactly the counts the expected-value
    # literals below assume.
    assert metrics["depletion_event_count"] == 1
    assert metrics["cutoff_event_count"] == 1
    assert metrics["qos_satisfaction_ratio"] == 0.0
    assert metrics["return_constraint_cost"] == 0.0
    assert metrics["shaping_potential_delta"] == 0.0

    depletion_penalty = env.depletion_event_penalty * 1
    cutoff_penalty = env.cutoff_event_penalty * 1

    if variant == "qos_only":
        expected = 0.0
    elif variant == "qos_depletion_penalty":
        expected = -depletion_penalty
    else:
        expected = -cutoff_penalty - depletion_penalty

    assert metrics["scenario7_reward_variant"] == variant
    assert np.isclose(metrics["scenario7_reward"], expected)


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

    # "per uav" was in the name and not in the test: everything above drives UAV
    # 0 alone, so a GLOBAL latch -- one flag for the whole fleet -- passes every
    # assertion. Measured 2026-07-27: replacing the per-UAV mask with
    # `mask & (not seen.any())` left 214/214 green.
    #
    # This is the heaviest-weighted term in the primary quantity: `compute_G`
    # subtracts `5*new_cutoff + 10*new_depletion`. A global latch undercounts
    # both whenever a SECOND UAV crosses a threshold, which is the ordinary case
    # in an eight-UAV fleet under energy stress, so `G` comes out systematically
    # high. D7.S's window-local latching counts exactly these events.
    #
    # A second UAV's first event must therefore be counted even though the first
    # UAV has already latched.
    env.uav_battery_ratios[1] = env.service_cutoff_threshold * 0.5
    second_uav_cutoff = env._calculate_constrained_safety_reward(
        0.0, 0.0, 0.0, 0.0, False, 0.0, {}
    )
    assert second_uav_cutoff["cutoff_event_count"] == 1, (
        "UAV 1's first cutoff must count even though UAV 0 has already latched; "
        "a zero here means the latch is fleet-global rather than per-UAV")

    env.uav_battery_ratios[1] = 0.0
    second_uav_depletion = env._calculate_constrained_safety_reward(
        0.0, 0.0, 0.0, 0.0, False, 0.0, {}
    )
    assert second_uav_depletion["depletion_event_count"] == 1, (
        "UAV 1's first depletion must count even though UAV 0 has already latched")

    # ...and still exactly once for it, too -- otherwise the repair above could
    # be satisfied by removing the latch entirely.
    repeated_second = env._calculate_constrained_safety_reward(
        0.0, 0.0, 0.0, 0.0, False, 0.0, {}
    )
    assert repeated_second["cutoff_event_count"] == 0
    assert repeated_second["depletion_event_count"] == 0


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
