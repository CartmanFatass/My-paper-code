import numpy as np

from experiments.candidates.uav_local_history.b01.read_b01 import reconstruct_native


def test_offline_reconstruction_enforces_capacity():
    positions = np.array([[[500.0, 500.0, 50.0]]])
    users = np.repeat([[500.0, 500.0]], 20, axis=0)
    reward, served, quality = reconstruct_native(positions, users)
    db = 23 - 20 * np.log10(50) - 20 * np.log10(4 * np.pi / .15) + 80
    expected_quality = np.clip((db - 3) / 30, 0, 1)
    np.testing.assert_array_equal(served, [10])
    np.testing.assert_allclose(quality, [expected_quality], atol=1e-14, rtol=0)
    np.testing.assert_allclose(reward, [.7 * 10 / 50 + .3 * expected_quality], atol=1e-14, rtol=0)


def test_offline_reconstruction_keeps_joint_interference():
    positions = np.repeat([[[500.0, 500.0, 50.0]]], 5, axis=1)
    users = np.repeat([[500.0, 500.0]], 20, axis=0)
    reward, served, quality = reconstruct_native(positions, users)
    np.testing.assert_array_equal(served, [0])
    np.testing.assert_array_equal(quality, [0])
    np.testing.assert_array_equal(reward, [0])
