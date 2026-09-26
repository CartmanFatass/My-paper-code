import numpy as np

from envs.pettingzoo.relay.energy_aware import UAVEnergyAwareRelayEnv
from experiments.candidates.uav_service_auxiliary.b09.native import B09Spec, make_b09_config
from experiments.candidates.uav_service_auxiliary.b11.station import GuardedStationEnv
from experiments.candidates.uav_service_auxiliary.b11.metrics import station_intervals


def _env(rule="G", seed=11):
    config = make_b09_config(B09Spec())
    env = GuardedStationEnv(config=config, seed=seed, station_rule=rule)
    env.reset(seed=seed)
    return env


def test_guard_strict_boundary_local_fallback_and_same_selection(monkeypatch):
    env = _env()
    try:
        env.charging_station_capacity[:2] = 1
        env._prior_actual_station[:4] = [0, -1, 1, -1]
        env.uav_battery_ratios[:4] = [.4, .1, .4, .1]
        env.uav_return_energy_margins[:4] = [1, 1, 1, 1]  # Cached state is irrelevant.
        margins = np.ones(env.n_uavs)
        margins[:4] = [.2, 0., .2, -.01]
        monkeypatch.setattr(env, "_raw_return_energy_margins", lambda: margins.copy())
        chosen = env._select_charging_uavs({0: [0, 1], 1: [2, 3]})
        snap = env.selection_snapshots[-1]
        assert chosen[0] == [0]  # Strict zero is safe; C stays local.
        assert chosen[1] == [3]  # Negative C-excluded member triggers native O.
        assert snap["guard_trigger"] == {"0": False, "1": True}
        assert snap["continuous_selected"] == {"0": [0], "1": [2]}
        assert snap["raw_margin_before_input"][:4] == [.2, 0., .2, -.01]
        margins[1] = -1e-12
        chosen = env._select_charging_uavs({0: [0, 1], 1: [2, 3]})
        assert chosen[0] == [1]
        env._prior_actual_station[1] = 0
        env.uav_battery_ratios[1] = .1
        env.uav_battery_ratios[0] = .4
        chosen = env._select_charging_uavs({0: [0, 1], 1: []})
        assert chosen[0] == [1]
        assert env.selection_snapshots[-1]["guard_trigger"]["0"] is False
    finally:
        env.close()


def test_fallback_actual_input_becomes_next_incumbent_and_reset():
    env = _env()
    try:
        env.charging_station_capacity[0] = 1
        station = env.charging_station_positions[0].copy()
        env.uav_positions[:2] = station
        env.uav_battery_ratios[:2] = [.6, .05]
        env.uav_charging[0] = True
        env.last_energy_charged_wh[0] = .1
        env.uav_target_stations[0] = 0
        actions = {env.agents[i]: np.asarray([0, 0, 0, 1], dtype=np.float32) for i in (0, 1)}
        pre = env.uav_positions.copy()
        _, velocities = env._prepare_energy_actions(actions)
        env._apply_energy_dynamics(pre, velocities)
        snap = env.selection_snapshots[-1]
        assert snap["prior_actual_station"][0] == 0
        assert snap["continuous_selected"]["0"] == [0]
        assert snap["guard_trigger"]["0"]
        assert snap["actual_selected"]["0"] == [1]
        assert snap["raw_margin_before_input"][1] < 0
        assert env.last_energy_charged_wh[1] > 0 and env.last_energy_charged_wh[0] == 0
        assert env.uav_battery_ratios[1] > snap["battery_after_consumption"][1]
        env._prepare_energy_actions(actions)
        assert env._prior_actual_station[1] == 0
        assert env._prior_actual_station[0] == -1
        env.reset(seed=12)
        assert np.all(env._prior_actual_station == -1)
        assert env.selection_snapshots == []
    finally:
        env.close()


def test_original_native_physics_and_rng_order():
    config = make_b09_config(B09Spec())
    old = UAVEnergyAwareRelayEnv(config=config, seed=19)
    new = GuardedStationEnv(config=config, seed=19, station_rule="O")
    try:
        old.reset(seed=19)
        new.reset(seed=19)
        actions = {member: np.asarray([0, 0, 0, 1], dtype=np.float32) for member in old.agents}
        for _ in range(3):
            a, b = old.step(actions), new.step(actions)
            for member in old.agents:
                assert a[1][member] == b[1][member]
                for key in a[0][member]:
                    np.testing.assert_array_equal(a[0][member][key], b[0][member][key])
            for key in ("uav_battery_ratios", "last_energy_charged_wh", "charging_wait_steps", "station_occupancy"):
                np.testing.assert_array_equal(getattr(old, key), getattr(new, key))
            assert new.selection_snapshots[-1]["actual_selected"] == new.selection_snapshots[-1]["original_selected"]
            left, right = old.np_random.get_state(), new.np_random.get_state()
            assert left[0] == right[0] and left[2:] == right[2:]
            np.testing.assert_array_equal(left[1], right[1])
    finally:
        old.close()
        new.close()


def test_guard_denominators_count_actual_waiters_not_automatic_rescue():
    snap = {"rule": "G", "prior_actual_station": [0, -1, -1],
            "current_target_station": [0, 0, 0], "battery_after_consumption": [.3, .2, .1],
            "raw_margin_before_input": [.1, -.02, -.03], "wait_age_before_selection": [0, 1, 2],
            "eligible_by_station": {"0": [0, 1, 2]}, "original_selected": {"0": [2]},
            "continuous_selected": {"0": [0]}, "guard_trigger": {"0": True},
            "actual_selected": {"0": [2]}}
    diagnostics = {"charger_input_wh": np.asarray([[0., 0., .1]]),
                   "physical_post_battery": np.asarray([[.3, .2, .11]]),
                   "charging_wait_age": np.asarray([[1, 2, 0]]),
                   "signed_stored_energy_delta_wh": np.asarray([[-.01, -.01, .09]])}
    result = station_intervals([snap], diagnostics, terminal_type="truncated")
    counts = result["guard_counts"]
    assert counts["station_ticks"] == counts["eligible_station_ticks"] == 1
    assert counts["trigger_changes_continuity_to_O"] == 1
    assert counts["negative_excluded_by_C_uav_ticks"] == 2
    assert counts["negative_excluded_by_C_actual_input_uav_ticks"] == 1
    assert counts["negative_excluded_by_C_actual_wait_uav_ticks"] == 1
    assert counts["negative_actual_waiter_uav_ticks"] == 1
    assert result["negative_wait_interval_end_counts"]["observation_censored"] == 1
    terminal = station_intervals([snap], diagnostics, terminal_type="terminated")
    assert terminal["negative_wait_interval_end_counts"]["episode_terminated"] == 1
    assert terminal["negative_wait_interval_end_counts"]["observation_censored"] == 0
    assert terminal["wait_interval_end_counts"]["episode_terminated"] > 0


def test_trigger_with_same_O_and_C_selection_is_diagnostic_not_intervention(monkeypatch):
    env = _env()
    try:
        env.charging_station_capacity[0] = 1
        env._prior_actual_station[:2] = [0, -1]
        env.uav_battery_ratios[:2] = [.1, .2]
        margins = np.ones(env.n_uavs)
        margins[1] = -.01
        monkeypatch.setattr(env, "_raw_return_energy_margins", lambda: margins.copy())
        assert env._select_charging_uavs({0: [0, 1]})[0] == [0]
        snap = env.selection_snapshots[-1]
        assert snap["guard_trigger"]["0"]
        assert snap["original_selected"]["0"] == snap["continuous_selected"]["0"]
        input_wh = np.zeros((1, env.n_uavs))
        input_wh[0, 0] = .1
        post = env.uav_battery_ratios[None].copy()
        post[0, 0] = .11
        age = np.zeros((1, env.n_uavs), dtype=int)
        age[0, 1] = 1
        stored = np.zeros((1, env.n_uavs))
        stored[0, :2] = [.09, -.01]
        diagnostics = {"charger_input_wh": input_wh, "physical_post_battery": post,
                       "charging_wait_age": age, "signed_stored_energy_delta_wh": stored}
        counts = station_intervals([snap], diagnostics, terminal_type="truncated")["guard_counts"]
        assert counts["trigger_same_selection"] == 1
        assert counts["trigger_changes_continuity_to_O"] == 0
        assert counts["actual_G_fallback_station_ticks"] == 0
    finally:
        env.close()
