from __future__ import annotations

import numpy as np
import pytest

from experiments.candidates.energy_relay_benchmark.b01 import feedback as fb
from experiments.candidates.uav_service_auxiliary.b06.feedback import apply_feedback

FIELDS = ("submitted_actions", "modes", "entered", "exited", "margins", "batteries",
          "selected_stations", "station_distances_m", "station_vectors_m")


def _perturbed(frames, count, rng):
    """Live observations with own margins/station vectors pushed across every boundary."""
    cases = []
    boundary = np.asarray((0.0, 0.05, np.nextafter(np.float32(0.05), np.float32(0)),
                           np.nextafter(np.float32(0.0), np.float32(1))), dtype=np.float32)
    for index in range(count):
        obs = frames[index % len(frames)].copy()
        suffix = obs[:, -120:]
        uavs = suffix[:, :104].reshape(8, 8, 13)
        stations = suffix[:, 104:].reshape(8, 2, 8)
        own = np.arange(8)
        margins = rng.uniform(-0.1, 0.2, size=8).astype(np.float32)
        pick = rng.random(8) < 0.3
        margins[pick] = rng.choice(boundary, size=int(pick.sum()))
        uavs[own, own, 12] = margins
        near = rng.random(8) < 0.25   # some observers inside the 160 m docking radius
        for observer in np.flatnonzero(near):
            station = int(rng.integers(2))
            stations[observer, station, :3] = rng.uniform(-100, 100, 3) / np.asarray((8000, 8000, 150))
        actions = rng.uniform(-1, 1, size=(8, 4)).astype(np.float32)
        modes = rng.random(8) < 0.5
        cases.append((obs, actions, modes))
    return cases


def test_bit_identical_to_b06_at_production_margins(live_frames):
    rng = np.random.default_rng(7)
    cases = _perturbed(live_frames, 200, rng)
    entered = exited = docked = 0
    for obs, actions, modes in cases:
        old = apply_feedback(obs, actions, modes)
        new = fb.apply_feedback_params(obs, actions, modes, fb.PRODUCTION_PARAMS)
        for field in FIELDS:
            left, right = getattr(old, field), getattr(new, field)
            assert left.dtype == right.dtype and left.shape == right.shape, field
            assert np.array_equal(left, right), field
        entered += int(new.entered.sum())
        exited += int(new.exited.sum())
        docked += int(np.all(new.submitted_actions == (0, 0, 0, 1), axis=1).sum())
    assert entered and exited and docked  # every branch exercised


def test_params_validation_and_label():
    assert fb.PRODUCTION_PARAMS == fb.FeedbackParams(0.0, 0.05)
    assert fb.PRODUCTION_PARAMS.label == "e0.00_x0.05"
    with pytest.raises(ValueError, match="exceed"):
        fb.FeedbackParams(0.10, 0.05)
    with pytest.raises(ValueError, match="exceed"):
        fb.FeedbackParams(0.2, 0.2)
    with pytest.raises(ValueError, match="finite"):
        fb.FeedbackParams(0.0, float("nan"))
    assert type(fb.FeedbackParams(np.float64(0.1), np.float32(0.25)).exit_margin) is float


def test_non_production_margins_move_both_thresholds(live_frames):
    obs = live_frames[0].copy()
    uavs = obs[:, -120:][:, :104].reshape(8, 8, 13)
    margins = np.asarray((-0.01, 0.05, 0.10, 0.15, 0.30, 0.45, 0.50, 0.20), dtype=np.float32)
    uavs[np.arange(8), np.arange(8), 12] = margins
    prior = np.asarray((False, True, False, True, True, True, False, False))
    decision = fb.apply_feedback_params(obs, np.zeros((8, 4), np.float32), prior,
                                        fb.FeedbackParams(0.10, 0.45))
    np.testing.assert_array_equal(
        decision.modes, (True, True, True, True, True, False, False, False))
    np.testing.assert_array_equal(decision.exited, (False,) * 5 + (True,) + (False,) * 2)
