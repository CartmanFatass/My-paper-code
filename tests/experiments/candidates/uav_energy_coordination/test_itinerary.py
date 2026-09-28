"""Closed-form contracts for the B01 analytical itinerary solver."""

from dataclasses import replace

import numpy as np
import pytest

from experiments.candidates.uav_energy_coordination.b01.itinerary import (
    ForecastConfig,
    forecast_itineraries,
)


def forecast(positions, batteries, stations, goals, ids, modes, times, *, config=None, power=None):
    return forecast_itineraries(
        np.array(positions, dtype=np.float64), np.array(batteries, dtype=np.float64),
        np.array(stations, dtype=np.float64), np.array(goals, dtype=np.float64),
        np.array(ids, dtype=np.int64), np.array(modes, dtype=np.bool_),
        np.array(times, dtype=np.float64), config=config or ForecastConfig(),
        power=power or (lambda _horizontal, _vertical: 360.0),
    )


def test_outbound_constant_velocity_and_energy_between_samples():
    calls = []

    def power(horizontal, vertical):
        calls.append((horizontal, vertical))
        return 360.0

    result = forecast([[0, 0, 0]], [0.5], [[500, 0, 0]], [[30, 40, 5]],
                      [-1], [False], [1, 2, 3], power=power)
    np.testing.assert_allclose(result.positions[0, 0], [18, 24, 3])
    np.testing.assert_allclose(result.positions[1:, 0], [[30, 40, 5]] * 2)
    np.testing.assert_allclose(calls[0], [30, 3])
    expected_wh = 360 * (5 / 3) / 3600 + 168.49 * (3 - 5 / 3) / 3600
    assert result.consumed_wh == pytest.approx(expected_wh)
    assert result.batteries[-1, 0] == pytest.approx((80 - expected_wh) / 160)
    assert np.isinf(result.arrival_times[0])
    assert result.input_wh == 0


def test_station_outer_and_docking_capture_geometry():
    result = forecast([[200, 0, 0]], [1], [[0, 0, 0]], [[0, 0, 0]],
                      [0], [False], [1, 48, 49])
    np.testing.assert_allclose(result.positions[0, 0], [170, 0, 0])
    np.testing.assert_allclose(result.positions[1:, 0], [[20, 0, 0]] * 2)
    assert result.arrival_times[0] == pytest.approx(48)
    assert np.isinf(result.release_times[0])
    assert result.input_wh > 0


def test_equalization_and_conservation_without_ticks():
    config = replace(ForecastConfig(), capacity_wh=10, hover_w=3600,
                     charge_w=10800, release_margin=0.2)
    result = forecast([[0, 0, 0], [0, 0, 0]], [0.2, 0.4], [[0, 0, 0]],
                      [[0, 0, 0], [0, 0, 0]], [0, 0], [False, False],
                      [0.5, 1, 2], config=config)
    np.testing.assert_allclose(result.batteries[0], [0.3, 0.35])
    np.testing.assert_allclose(result.batteries[1], [0.35, 0.35])
    np.testing.assert_allclose(result.batteries[2], [0.4, 0.4])
    assert result.consumed_wh == pytest.approx(4)
    assert result.input_wh == pytest.approx(6)
    assert result.floor_clip_wh == 0
    assert 3 <= result.event_count < 20


def test_staggered_arrival_rebalances_station_stream():
    config = replace(ForecastConfig(), capacity_wh=10, hover_w=3600,
                     charge_w=10800, dock_horizontal=3)
    result = forecast([[0, 0, 0], [30, 0, 0]], [0.2, 0.8], [[0, 0, 0]],
                      [[0, 0, 0], [0, 0, 0]], [0, 0], [False, False],
                      [1, 4, 5], config=config)
    assert result.arrival_times[1] == pytest.approx(10 / 3)
    np.testing.assert_allclose(result.batteries[0], [0.4, 0.79])
    np.testing.assert_allclose(result.batteries[1], [0.85, 0.85])
    np.testing.assert_allclose(result.batteries[2], [0.9, 0.9])
    initial = 10.0
    final = result.batteries[-1].sum() * config.capacity_wh
    assert final == pytest.approx(initial - result.consumed_wh
                                  + result.input_wh + result.floor_clip_wh)


def test_full_station_only_replaces_hover_and_floor_clip_is_counted():
    config = replace(ForecastConfig(), capacity_wh=10, hover_w=3600,
                     charge_w=10800)
    full = forecast([[0, 0, 0], [0, 0, 0]], [1, 1], [[0, 0, 0]],
                    [[0, 0, 0], [0, 0, 0]], [0, 0], [False, False],
                    [1, 2, 3], config=config)
    np.testing.assert_allclose(full.batteries, 1)
    assert full.input_wh == pytest.approx(full.consumed_wh)
    assert full.floor_clip_wh == 0

    config = replace(config, charge_w=3600)
    empty = forecast([[0, 0, 0], [0, 0, 0], [0, 0, 0]], [0, 0, 0],
                     [[0, 0, 0]], [[0, 0, 0]] * 3, [0, 0, 0], [False] * 3,
                     [1, 2, 3], config=config)
    np.testing.assert_allclose(empty.batteries, 0)
    assert empty.input_wh == pytest.approx(3)
    assert empty.consumed_wh == pytest.approx(9)
    assert empty.floor_clip_wh == pytest.approx(6)

    crowded = forecast([[0, 0, 0]] * 8, [1] * 8, [[0, 0, 0]],
                       [[0, 0, 0]] * 8, [0] * 8, [False] * 8,
                       [1, 2, 3], config=ForecastConfig())
    assert crowded.input_wh == pytest.approx(1000 * 3 / 3600)
    assert crowded.batteries[-1, 0] < 1


def test_f_mode_release_redeployment_and_no_second_visit():
    config = replace(ForecastConfig(), capacity_wh=10, hover_w=3600,
                     charge_w=7200, outer_horizontal=10, release_margin=0.2,
                     reserve_ratio=0)
    result = forecast([[0, 0, 0]], [0.1], [[0, 0, 0]], [[30, 0, 0]],
                      [-1], [True], [4, 6, 10], config=config)
    assert result.arrival_times[0] == pytest.approx(0)
    assert result.release_times[0] == pytest.approx(1)
    np.testing.assert_allclose(result.positions[:, 0], [[30, 0, 0]] * 3)
    assert result.batteries[1, 0] == 0
    assert result.batteries[2, 0] == 0
    assert result.depletion_events == 1
    assert result.input_wh == pytest.approx(2)


def test_release_targets_use_capture_distance_and_reallocate_stream():
    config = replace(ForecastConfig(), capacity_wh=10, hover_w=3600,
                     charge_w=10800, outer_horizontal=10,
                     reserve_ratio=0, release_margin=0.2,
                     return_power_w=1080)
    result = forecast([[0, 0, 0], [10, 0, 0]], [0.1, 0.1],
                      [[0, 0, 0]], [[30, 0, 0], [40, 0, 0]],
                      [-1, -1], [True, True], [1, 2, 3], config=config)
    np.testing.assert_allclose(result.arrival_times, [0, 0])
    np.testing.assert_allclose(result.release_times, [2, 2.5])
    np.testing.assert_allclose(result.positions[-1], [[10, 0, 0], [15, 0, 0]])
    assert result.input_wh == pytest.approx(3 * 2.5)


def test_cutoff_and_depletion_between_samples_freeze_before_station():
    config = replace(ForecastConfig(), capacity_wh=10, hover_w=3600,
                     outer_horizontal=10, cutoff_ratio=0.02)
    result = forecast([[200, 0, 0]], [0.03], [[0, 0, 0]], [[0, 0, 0]],
                      [0], [False], [0.5, 1, 2], config=config,
                      power=lambda _h, _v: 3600)
    np.testing.assert_allclose(result.positions[:, 0], [[197, 0, 0]] * 3)
    np.testing.assert_allclose(result.batteries[:, 0], 0)
    assert result.cutoff_events == 1
    assert result.depletion_events == 1
    assert np.isinf(result.arrival_times[0])
    assert result.min_battery[0] == 0
    assert result.floor_clip_wh == pytest.approx(1.7)


def test_exact_segment_end_depletion_does_not_start_next_leg():
    config = replace(ForecastConfig(), capacity_wh=10, hover_w=3600,
                     outer_horizontal=30)
    station = forecast([[200, 0, 0]], [4 / 30], [[0, 0, 0]], [[0, 0, 0]],
                       [0], [False], [1, 2, 3], config=config,
                       power=lambda _h, _v: 3600)
    np.testing.assert_allclose(station.positions[1:, 0], [[160, 0, 0]] * 2)
    assert np.isinf(station.arrival_times[0])

    service = forecast([[0, 0, 0]], [0.1], [[500, 0, 0]], [[30, 0, 0]],
                       [-1], [False], [1, 2, 3], config=config,
                       power=lambda _h, _v: 3600)
    np.testing.assert_allclose(service.positions[:, 0], [[30, 0, 0]] * 3)
    assert np.isinf(service.arrival_times[0])


def test_input_arrays_and_event_masks_are_not_modified():
    positions = np.array([[200., 0, 0]])
    batteries = np.array([0.03])
    stations = np.array([[0., 0, 0]])
    goals = stations.copy()
    ids = np.array([0])
    modes = np.array([False])
    times = np.array([0.5, 1., 2.])
    cutoff_seen = np.array([True])
    depletion_seen = np.array([True])
    originals = [a.copy() for a in (positions, batteries, stations, goals, ids,
                                     modes, times, cutoff_seen, depletion_seen)]
    result = forecast_itineraries(positions, batteries, stations, goals, ids, modes,
                                  times, config=replace(ForecastConfig(),
                                                        capacity_wh=10, hover_w=3600,
                                                        outer_horizontal=10),
                                  power=lambda _h, _v: 3600,
                                  cutoff_seen=cutoff_seen,
                                  depletion_seen=depletion_seen)
    assert result.cutoff_events == 0
    assert result.depletion_events == 0
    for actual, expected in zip((positions, batteries, stations, goals, ids,
                                  modes, times, cutoff_seen, depletion_seen), originals):
        np.testing.assert_array_equal(actual, expected)


def test_mixed_fleet_events_conserve_energy_and_station_power():
    rng = np.random.RandomState(70193)
    config = ForecastConfig()
    stations = np.asarray([[3000., 3000., 50.], [5000., 5000., 50.]])
    power = lambda horizontal, vertical: 168.49 + .1 * horizontal ** 2 + 15 * abs(vertical)
    for _ in range(25):
        positions = np.column_stack((rng.uniform(2000, 6000, (8, 2)), rng.uniform(50, 150, 8)))
        positions[:4] = stations[0] + rng.uniform(-15, 15, (4, 3))
        battery = rng.uniform(0, 1, 8)
        goals = np.column_stack((rng.uniform(2000, 6000, (8, 2)), np.full(8, 100.)))
        station_ids = rng.choice([-1, 0, 1], 8)
        modes = battery < .2
        result = forecast_itineraries(positions, battery, stations, goals, station_ids,
                                      modes, np.asarray([200., 400., 600.]),
                                      config=config, power=power)
        assert np.isfinite(result.positions).all()
        assert np.all((0 <= result.batteries) & (result.batteries <= 1))
        final_energy = result.batteries[-1].sum() * config.capacity_wh
        balance = battery.sum() * config.capacity_wh - result.consumed_wh + result.input_wh + result.floor_clip_wh
        assert final_energy == pytest.approx(balance, abs=1e-7)
        assert result.input_wh <= 2 * config.charge_w * 600 / 3600 + 1e-7
        assert result.event_count < 1000
