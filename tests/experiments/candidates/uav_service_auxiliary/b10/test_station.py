import copy
import numpy as np
import pytest

from experiments.candidates.uav_service_auxiliary.b09.native import B09Spec, make_b09_config
from experiments.candidates.uav_service_auxiliary.b10.metrics import station_intervals
from experiments.candidates.uav_service_auxiliary.b10.station import ContinuityStationEnv
from experiments.candidates.uav_service_auxiliary.b07.native import energy_ledger
from envs.pettingzoo.relay.energy_aware import UAVEnergyAwareRelayEnv


def test_actual_prior_station_survives_preparation_and_energy_path():
    config = make_b09_config(B09Spec())
    env = ContinuityStationEnv(config=config, seed=11, station_rule="C")
    try:
        env.reset(seed=11)
        env.charging_station_capacity[:2] = 1
        station = env.charging_station_positions[0].copy()
        env.uav_positions[0] = station
        env.uav_positions[1] = station
        env.uav_battery_ratios[:2] = [.6, .2]
        env.uav_charging[0] = True
        env.last_energy_charged_wh[0] = .1
        env.uav_target_stations[0] = 0
        pre_battery = env.uav_battery_ratios.copy()
        pre_charging = env.uav_charging.copy()
        actions = {env.agents[i]: np.asarray([0, 0, 0, 1], dtype=np.float32) for i in (0, 1)}
        pre_positions = env.uav_positions.copy()
        _, commanded = env._prepare_energy_actions(actions)
        assert env._prior_actual_station[0] == 0
        assert env.uav_target_stations[0] == 0
        env._apply_energy_dynamics(pre_positions, commanded)
        snap = env.selection_snapshots[-1]
        assert 0 in snap["eligible_by_station"]["0"] and 1 in snap["eligible_by_station"]["0"]
        assert snap["original_selected"]["0"] == [1]
        assert snap["actual_selected"]["0"] == [0]
        assert env.last_energy_charged_wh[0] > 0 and env.last_energy_charged_wh[1] == 0
        ledger = energy_ledger(env, pre_battery, pre_charging)
        assert np.isclose(ledger["signed_stored_energy_delta_wh"][0],
                          ledger["charger_input_wh"][0] - ledger["consumed_wh"][0]
                          + ledger["capacity_clipping_residual_wh"][0])
        env.station_rule = "O"
        env.uav_battery_ratios[:2] = [.6, .2]
        env._prior_actual_station[:2] = [0, -1]
        assert env._select_charging_uavs({0: [0, 1], 1: []})[0] == [1]
        env.uav_battery_ratios[:2] = [.4, .4]
        env.charging_wait_steps[:2] = [1, 3]
        assert env._select_charging_uavs({0: [0, 1], 1: []})[0] == [1]
        env.charging_wait_steps[:2] = [3, 3]
        assert env._select_charging_uavs({0: [0, 1], 1: []})[0] == [0]
        env.station_rule = "C"
        env.uav_battery_ratios[:2] = [.6, .2]
        assert env._select_charging_uavs({0: [1], 1: []})[0] == [1]
        env._prior_actual_station[:2] = [0, -1]
        env.uav_battery_ratios[:3] = [.6, .2, .1]
        assert env._select_charging_uavs({0: [1], 1: [0, 2]})[1] == [2]
        env.reset(seed=12)
        assert np.all(env._prior_actual_station == -1)
    finally:
        env.close()


def test_original_rule_full_native_step_equality():
    config = make_b09_config(B09Spec())
    original = UAVEnergyAwareRelayEnv(config=config, seed=19)
    candidate = ContinuityStationEnv(config=config, seed=19)  # Explicit O default.
    try:
        a, _ = original.reset(seed=19)
        b, _ = candidate.reset(seed=19)
        for member in original.agents:
            for key in a[member]:
                np.testing.assert_array_equal(a[member][key], b[member][key])
        actions = {member: np.asarray([0, 0, 0, 1], dtype=np.float32) for member in original.agents}
        for _ in range(2):
            old = original.step(actions)
            new = candidate.step(actions)
            for member in original.agents:
                for key in old[0][member]:
                    np.testing.assert_array_equal(old[0][member][key], new[0][member][key])
                assert old[1][member] == new[1][member]
            np.testing.assert_array_equal(original.uav_battery_ratios, candidate.uav_battery_ratios)
            np.testing.assert_array_equal(original.uav_charging, candidate.uav_charging)
            np.testing.assert_array_equal(original.charging_wait_steps, candidate.charging_wait_steps)
            np.testing.assert_array_equal(original.last_energy_charged_wh, candidate.last_energy_charged_wh)
    finally:
        original.close()
        candidate.close()


def test_wait_station_change_and_spell_endings():
    def snap(station, original, actual, prior=-1):
        return {"prior_actual_station": [prior], "current_target_station": [station],
                "battery_after_consumption": [.2], "wait_age_before_selection": [0],
                "eligible_by_station": {"0": [0] if station == 0 else [],
                                        "1": [0] if station == 1 else []},
                "original_selected": {"0": original if station == 0 else [],
                                      "1": original if station == 1 else []},
                "actual_selected": {"0": actual if station == 0 else [],
                                    "1": actual if station == 1 else []}}
    rows = [snap(0, [], []), snap(1, [], []), snap(1, [0], [0])]
    diagnostics = {"charger_input_wh": np.asarray([[0.], [0.], [.1]]),
                   "physical_post_battery": np.asarray([[.2], [.19], [.2]]),
                   "charging_wait_age": np.asarray([[1], [1], [0]]),
                   "signed_stored_energy_delta_wh": np.asarray([[-.01], [-.01], [.09]])}
    result = station_intervals(rows, diagnostics, terminal_type="truncated")
    assert [(row["start"], row["stop"], row["end"]) for row in result["waiting_intervals"]] == [
        (0, 1, "lost_eligibility_or_departed"), (1, 2, "actual_input")]
    assert result["waiting_eligible_uav_ticks"] == 2
    assert result["first_actual_input_step_by_member"] == [2]
    assert result["charging_spell_end_counts"]["observation_censored"] == 1
    rows = [snap(0, [0], [0]), snap(0, [0], [0], prior=0)]
    diagnostics["charger_input_wh"] = np.asarray([[.1], [0.]])
    diagnostics["signed_stored_energy_delta_wh"] = np.asarray([[.09], [-.01]])
    diagnostics["physical_post_battery"] = np.asarray([[.2], [.19]])
    diagnostics["charging_wait_age"] = np.asarray([[0], [0]])
    result = station_intervals(rows, diagnostics, terminal_type="terminated")
    assert result["charging_spell_end_counts"]["selected_without_positive_input"] == 1
    assert result["same_station_eligible_incumbent_replacements"] == 0


def test_local_order_reversal_with_identical_membership_is_not_allocation_change():
    snapshots = [{"prior_actual_station": [-1, -1], "current_target_station": [0, 0],
                  "battery_after_consumption": [.2, .3], "wait_age_before_selection": [0, 0],
                  "eligible_by_station": {"0": [0, 1]},
                  "original_selected": {"0": [0, 1]},
                  "actual_selected": {"0": [1, 0]}}]
    diagnostics = {"charger_input_wh": np.asarray([[.1, .1]]),
                   "physical_post_battery": np.asarray([[.3, .4]]),
                   "charging_wait_age": np.zeros((1, 2), dtype=int),
                   "signed_stored_energy_delta_wh": np.asarray([[.09, .09]])}
    result = station_intervals(snapshots, diagnostics, terminal_type="truncated")
    assert result["ticks_where_C_differs_from_local_original_sort"] == 0
