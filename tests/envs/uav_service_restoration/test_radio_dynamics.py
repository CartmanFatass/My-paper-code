"""Link budget arithmetic, and UAV kinematics including the integration order."""

from __future__ import annotations

import numpy as np
import pytest

from envs.uav_service_restoration import dynamics as dyn
from envs.uav_service_restoration import radio
from envs.uav_service_restoration.config import DynamicsConfig, RadioModelConfig, RegionConfig

MODEL = RadioModelConfig(
    frequency_hz=2.0e9,
    bandwidth_hz=10.0e6,
    tx_power_dbm=30.0,
    antenna_gain_db=0.0,
    noise_density_dbm_per_hz=-174.0,
    noise_figure_db=0.0,
    reference_distance_m=1.0,
    reference_loss_db=40.0,
    path_loss_exponent=2.0,
    extra_loss_db=0.0,
    spectral_efficiency=1.0,
    min_snr_db=-100.0,
    max_range_m=1.0e6,
)


# --------------------------------------------------------------------------------------
# Radio
# --------------------------------------------------------------------------------------


def test_db_conversions_round_trip():
    for dbm in (-120.0, -30.0, 0.0, 23.0, 43.0):
        assert float(radio.watt_to_dbm(radio.dbm_to_watt(dbm))) == pytest.approx(dbm, abs=1e-9)
    for db in (-40.0, 0.0, 3.0, 30.0):
        assert float(radio.linear_to_db(radio.db_to_linear(db))) == pytest.approx(db, abs=1e-9)
    # 30 dBm is exactly one watt; 3 dB is a factor of about two.
    assert float(radio.dbm_to_watt(30.0)) == pytest.approx(1.0, abs=1e-12)
    assert float(radio.db_to_linear(3.0)) == pytest.approx(1.9952623, abs=1e-6)


def test_noise_floor_matches_the_documented_formula():
    # -174 dBm/Hz over 10 MHz with a 0 dB noise figure is -104 dBm.
    assert radio.noise_power_dbm(MODEL) == pytest.approx(-104.0, abs=1e-9)


def test_path_loss_doubles_by_six_db_per_octave_at_exponent_two():
    near = float(radio.path_loss_db(100.0, MODEL))
    far = float(radio.path_loss_db(200.0, MODEL))
    assert far - near == pytest.approx(20.0 * np.log10(2.0), abs=1e-9)
    assert near == pytest.approx(40.0 + 20.0 * np.log10(100.0), abs=1e-9)


def test_path_loss_is_clamped_below_the_reference_distance():
    assert float(radio.path_loss_db(0.0, MODEL)) == pytest.approx(40.0, abs=1e-9)
    assert float(radio.path_loss_db(0.5, MODEL)) == pytest.approx(40.0, abs=1e-9)


def test_snr_includes_antenna_gain_additively():
    gained = RadioModelConfig(**{**MODEL.__dict__, "antenna_gain_db": 12.0})
    assert float(radio.snr_db(500.0, gained)) - float(radio.snr_db(500.0, MODEL)) == pytest.approx(
        12.0, abs=1e-9
    )


def test_capacity_matches_shannon_by_hand():
    distance = 100.0
    snr = float(radio.snr_db(distance, MODEL))
    expected = 1.0 * 10.0e6 * np.log2(1.0 + 10.0 ** (snr / 10.0)) / 1e6
    assert float(radio.capacity_mbps(distance, MODEL)) == pytest.approx(expected, rel=1e-12)


def test_capacity_is_exactly_zero_out_of_range_or_below_the_snr_floor():
    ranged = RadioModelConfig(**{**MODEL.__dict__, "max_range_m": 500.0})
    assert float(radio.capacity_mbps(499.0, ranged)) > 0.0
    assert float(radio.capacity_mbps(501.0, ranged)) == 0.0
    floored = RadioModelConfig(**{**MODEL.__dict__, "min_snr_db": 100.0})
    assert float(radio.capacity_mbps(10.0, floored)) == 0.0


def test_capacity_is_monotonically_non_increasing_in_distance():
    distances = np.linspace(1.0, 5000.0, 400)
    capacities = radio.capacity_mbps(distances, MODEL)
    assert np.all(np.diff(capacities) <= 1e-9)


def test_distance_helpers_agree():
    a = np.array([[0.0, 0.0, 0.0], [3.0, 4.0, 0.0]])
    b = np.array([[3.0, 4.0, 12.0]])
    assert float(radio.euclidean_distance_m(a[1], b[0])) == pytest.approx(12.0)
    matrix = radio.pairwise_distance_matrix_m(a, b)
    assert matrix.shape == (2, 1)
    assert matrix[0, 0] == pytest.approx(13.0)


# --------------------------------------------------------------------------------------
# Dynamics
# --------------------------------------------------------------------------------------

DYNAMICS = DynamicsConfig(max_speed_mps=20.0, altitude_range_m=(90.0, 160.0))
REGION = RegionConfig(min_xy_m=(0.0, 0.0), max_xy_m=(3000.0, 3000.0))


def test_speed_limit_applies_to_the_vector_norm_not_each_axis():
    request = np.array([[1.0, 1.0, 1.0]])
    velocity = dyn.requested_velocity_mps(request, DYNAMICS)
    speed = float(np.linalg.norm(velocity))
    assert speed == pytest.approx(20.0, abs=1e-9)
    # Per-axis clipping would have allowed sqrt(3) * 20 = 34.6 m/s diagonally.
    assert speed < 20.0 * np.sqrt(3.0) - 1.0


def test_requests_inside_the_unit_ball_are_not_rescaled():
    request = np.array([[0.3, -0.4, 0.0]])
    velocity = dyn.requested_velocity_mps(request, DYNAMICS)
    assert float(np.linalg.norm(velocity)) == pytest.approx(0.5 * 20.0, abs=1e-9)


def test_non_finite_requests_are_refused():
    with pytest.raises(ValueError, match="finite"):
        dyn.clamp_actions(np.array([[np.nan, 0.0, 0.0]]))


def test_boundaries_and_altitude_limits_are_enforced():
    position = np.array([[2990.0, 10.0, 155.0]])
    velocity = np.array([[20.0, -20.0, 20.0]])
    moved, realised, clipped = dyn.advance(position, velocity, 10.0, DYNAMICS, REGION)
    assert moved[0, 0] == pytest.approx(3000.0)
    assert moved[0, 1] == pytest.approx(0.0)
    assert moved[0, 2] == pytest.approx(160.0)
    assert clipped.all()
    # Realised velocity is the achieved displacement, so motion and velocity agree.
    np.testing.assert_allclose(realised, (moved - position) / 10.0, atol=1e-12)


def test_motion_effort_is_a_normalised_square_not_energy():
    at_limit = np.array([[20.0, 0.0, 0.0], [0.0, 20.0, 0.0]])
    assert dyn.motion_effort(at_limit, DYNAMICS) == pytest.approx(1.0)
    half = np.array([[10.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
    assert dyn.motion_effort(half, DYNAMICS) == pytest.approx(0.125)


def test_min_separation_is_reported():
    positions = np.array([[0.0, 0.0, 100.0], [30.0, 40.0, 100.0], [900.0, 0.0, 100.0]])
    assert dyn.min_pairwise_separation_m(positions) == pytest.approx(50.0)
    assert dyn.min_pairwise_separation_m(positions[:1]) == float("inf")


def test_initial_position_validation():
    assert dyn.valid_initial_positions(
        np.array([[100.0, 100.0, 120.0]]), DYNAMICS, REGION
    )
    assert not dyn.valid_initial_positions(
        np.array([[100.0, 100.0, 10.0]]), DYNAMICS, REGION
    )
    assert not dyn.valid_initial_positions(
        np.array([[-5.0, 100.0, 120.0]]), DYNAMICS, REGION
    )


def test_many_small_substeps_reach_the_same_place_as_one_large_one():
    """Motion itself is exact for constant velocity; only service integration has error."""

    position = np.array([[100.0, 100.0, 120.0]])
    velocity = np.array([[5.0, -3.0, 0.0]])
    one, _, _ = dyn.advance(position, velocity, 10.0, DYNAMICS, REGION)
    stepwise = position
    for _ in range(10):
        stepwise, _, _ = dyn.advance(stepwise, velocity, 1.0, DYNAMICS, REGION)
    np.testing.assert_allclose(one, stepwise, atol=1e-9)
