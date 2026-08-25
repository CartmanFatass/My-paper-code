import numpy as np

from envs.pettingzoo.relay.channel_geometry import RelayChannelGeometry


def _geometry():
    geometry = RelayChannelGeometry()
    geometry.carrier_frequency = 2.4e9
    return geometry


def test_distance_and_zero_distance_air_to_air_are_stable():
    geometry = _geometry()

    distance = geometry._compute_distance(
        np.array([0.0, 0.0, 0.0]),
        np.array([3.0, 4.0, 0.0]),
    )
    assert distance == 5.0

    zero_distance_loss = geometry._compute_air_to_air_path_loss(
        np.array([1.0, 2.0, 3.0]),
        np.array([1.0, 2.0, 3.0]),
    )
    assert np.isfinite(zero_distance_loss)


def test_ground_to_air_reverses_air_to_ground():
    geometry = _geometry()
    ground_pos = np.array([100.0, 200.0, 1.5])
    uav_pos = np.array([300.0, 500.0, 120.0])

    np.testing.assert_equal(
        geometry._compute_ground_to_air_path_loss(ground_pos, uav_pos),
        geometry._compute_air_to_ground_path_loss(uav_pos, ground_pos),
    )


def test_path_loss_pads_2d_user_position_to_1_5_metres():
    geometry = _geometry()
    uav_pos = np.array([300.0, 500.0, 120.0])
    user_pos_2d = np.array([100.0, 200.0])

    np.testing.assert_equal(
        geometry._compute_path_loss(uav_pos, user_pos_2d),
        geometry._compute_air_to_ground_path_loss(
            uav_pos,
            np.array([100.0, 200.0, 1.5]),
        ),
    )


def test_supported_environment_types_produce_finite_path_loss():
    geometry = _geometry()
    uav_pos = np.array([300.0, 500.0, 120.0])
    ground_pos = np.array([100.0, 200.0, 1.5])

    for environment_type in ("suburban", "urban", "dense_urban"):
        geometry.environment_type = environment_type
        assert np.isfinite(
            geometry._compute_air_to_ground_path_loss(uav_pos, ground_pos)
        )
