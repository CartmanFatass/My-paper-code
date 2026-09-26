from __future__ import annotations

import numpy as np
import pytest

from experiments.candidates.uav_service_auxiliary.b06.feedback import (
    PRODUCTION_LAYOUT,
    apply_feedback,
    decode_legal_observations,
)


def legal_observations(margins=None, batteries=None):
    layout = PRODUCTION_LAYOUT
    obs = np.zeros((layout.n_uavs, layout.observation_dim), dtype=np.float32)
    suffix = obs[:, -layout.suffix_fields :]
    uavs = suffix[:, : layout.n_uavs * layout.uav_record_fields].reshape(8, 8, 13)
    stations = suffix[:, -layout.station_count * layout.station_record_fields :].reshape(8, 2, 8)
    margins = np.full(8, 0.1, dtype=np.float32) if margins is None else np.asarray(margins, dtype=np.float32)
    batteries = np.full(8, 0.8, dtype=np.float32) if batteries is None else np.asarray(batteries, dtype=np.float32)
    for index in range(8):
        uavs[index, index, 3] = batteries[index]
        uavs[index, index, 12] = margins[index]
        stations[index, 0, :3] = (300.0 / 8000.0, 400.0 / 8000.0, 50.0 / 150.0)
        stations[index, 0, 7] = 1.0
        stations[index, 1, :3] = (-600.0 / 8000.0, 0.0, 0.0)
        stations[index, 1, 7] = 1.0
    return obs


def test_own_index_decode_station_tie_and_physical_motion_command():
    obs = legal_observations()
    suffix = obs[:, -PRODUCTION_LAYOUT.suffix_fields :]
    uavs = suffix[:, : 8 * 13].reshape(8, 8, 13)
    for observer in range(8):
        uavs[observer, :, 12] = np.arange(8, dtype=np.float32) + 10 * observer
        uavs[observer, observer, 3] = 0.2 + observer / 100
    stations = suffix[:, -16:].reshape(8, 2, 8)
    stations[0, 1, :3] = stations[0, 0, :3]  # exact tie must choose station zero

    margins, batteries, selected, distances, vectors = decode_legal_observations(obs)
    np.testing.assert_array_equal(margins, np.arange(8, dtype=np.float32) * 11)
    np.testing.assert_allclose(batteries, 0.2 + np.arange(8) / 100)
    assert selected[0] == 0
    assert distances[0] == pytest.approx(np.sqrt(300.0**2 + 400.0**2 + 50.0**2))
    np.testing.assert_allclose(vectors[0], (300.0, 400.0, 50.0), atol=2e-5)

    obs = legal_observations(margins=np.full(8, -0.01))
    proposed = np.full((8, 4), -0.25, dtype=np.float32)
    decision = apply_feedback(obs, proposed, np.zeros(8, dtype=bool))
    # T=500/30, giving velocity (18, 24, 3) m/s.
    np.testing.assert_allclose(
        decision.submitted_actions[:, :3], np.tile((0.6, 0.8, 0.6), (8, 1)), atol=2e-6
    )
    np.testing.assert_array_equal(decision.submitted_actions[:, 3], 1.0)


def test_threshold_equalities_hysteresis_and_inactive_identity():
    margins = (-0.1, 0.0, 0.025, 0.025, 0.05, 0.05, 0.1, 0.1)
    prior = np.asarray((False, False, False, True, False, True, False, True), dtype=bool)
    proposed = np.arange(32, dtype=np.float32).reshape(8, 4) / 32
    decision = apply_feedback(legal_observations(margins=margins), proposed, prior)
    expected = np.asarray((True, True, False, True, False, False, False, False))
    np.testing.assert_array_equal(decision.modes, expected)
    np.testing.assert_array_equal(decision.entered, (True, True, False, False, False, False, False, False))
    np.testing.assert_array_equal(decision.exited, (False, False, False, False, False, True, False, True))
    np.testing.assert_array_equal(decision.submitted_actions[~expected], proposed[~expected])


def test_inside_radius_docks_and_invalid_legal_fields_fail():
    obs = legal_observations(margins=np.full(8, -0.01))
    stations = obs[:, -16:].reshape(8, 2, 8)
    stations[:, 0, :3] = (159.0 / 8000.0, 0.0, 0.0)
    decision = apply_feedback(obs, np.ones((8, 4), dtype=np.float32), np.zeros(8, dtype=bool))
    np.testing.assert_array_equal(decision.submitted_actions, np.tile((0, 0, 0, 1), (8, 1)))

    stations[:, :, 7] = 0.0
    with pytest.raises(ValueError, match="valid charging station"):
        apply_feedback(obs, np.zeros((8, 4), dtype=np.float32), np.zeros(8, dtype=bool))
    bad = legal_observations()
    bad[0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        decode_legal_observations(bad)
