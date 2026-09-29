import numpy as np

from experiments.candidates.uav_local_history.b01.controller import LocalController
from experiments.candidates.uav_local_history.b02.inputs import ObservationHistory, current_only


def row_with_users(users):
    row = np.zeros(104, dtype=np.float32)
    row[:3] = [.2, .3, .5]
    for index, (x, y, signal) in enumerate(users):
        row[3 + 3 * index:6 + 3 * index] = [x - .2, y - .3, signal]
    return row


def test_history_matches_ordinary_and_never_retains_absent_sinr():
    history = ObservationHistory()
    ordinary = LocalController(history=True)
    observations = [row_with_users([(.4, .5, .8), (.6, .7, .7)]),
                    row_with_users([(.4, .5, .6)]), row_with_users([])]
    for clock, row in enumerate(observations):
        history.ingest(row, clock)
        ordinary.act(row, clock)
        np.testing.assert_array_equal(history.cache.points, ordinary.points)
        np.testing.assert_array_equal(history.cache.last_seen, ordinary.last_seen)
        np.testing.assert_array_equal(history.cache.current_mask, ordinary.current_mask)
    context, points, valid = history.features([0, -1, 1])
    assert context.shape == (107,)
    np.testing.assert_array_equal(context[-3:], [0, -1, 1])
    assert valid.sum() == 2
    np.testing.assert_array_equal(points[:2, 5:], 0)
    np.testing.assert_allclose(points[:2, 4], [1 / 256, 2 / 256])
    assert history.association_distance_evaluations == 3


def test_current_only_is_nonmutating_and_preserves_current_fields():
    history = ObservationHistory()
    history.ingest(row_with_users([(.4, .5, .8), (.6, .7, .7)]), 0)
    history.ingest(row_with_users([(.4, .5, .6)]), 4)
    _, points, valid = history.features([0, 0, 0])
    before = points.copy()
    shadow, shadow_valid = current_only(points, valid)
    assert shadow_valid.sum() == 1
    np.testing.assert_array_equal(points, before)
    np.testing.assert_array_equal(shadow[0], points[0])
    np.testing.assert_array_equal(shadow[1:], 0)
    np.testing.assert_array_equal(history.cache.current_mask, [True, False])
