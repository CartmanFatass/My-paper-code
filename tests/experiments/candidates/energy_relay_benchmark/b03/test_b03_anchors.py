"""B03 anchor set A(s): state offsets on a live S7-S2 env, rule, determinism, H1 agreement."""

from __future__ import annotations

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.heuristic import (
    LayoutHeuristic, estimator_kmeans, variant,
)
from experiments.candidates.energy_relay_benchmark.b03 import anchors as an


def test_state_offsets_match_the_live_environment(tiny_config, live_frames):
    assert not tiny_config.use_statenorm and not tiny_config.use_obsnorm
    assert int(tiny_config.state_dim) == an.STATE_DIM
    for frame in live_frames:
        state, area = frame["state"].astype(np.float64), frame["area"]
        assert area == an.AREA_M and state.shape == (306,)
        uav = frame["uav_positions"]
        np.testing.assert_allclose(state[an.STATE_UAV_XYZ].reshape(8, 3)[:, :2], uav[:, :2] / area,
                                   rtol=0, atol=1e-7)
        np.testing.assert_allclose(state[an.STATE_UAV_XYZ].reshape(8, 3)[:, 2],
                                   (uav[:, 2] - 50.0) / 150.0, rtol=0, atol=1e-6)
        users = state[an.STATE_USERS].reshape(30, 6)
        np.testing.assert_allclose(users[:, :2], frame["user_positions"][:, :2] / area,
                                   rtol=0, atol=1e-7)
        np.testing.assert_allclose(an.users_xy_m(state), frame["user_positions"][:, :2],
                                   rtol=0, atol=1e-3)
        assert frame["bs_positions"].shape == (1, 3)
        np.testing.assert_allclose(an.bs_xy_m(state), frame["bs_positions"][0, :2], rtol=0,
                                   atol=1e-3)
        np.testing.assert_allclose(state[an.STATE_STEP],
                                   frame["current_step"] / frame["max_steps"], atol=1e-7)
        # The actor's own xy (obs[0:2]) is the same quantity as the state's UAV xy.
        np.testing.assert_allclose(frame["obs"][:, 0:2], uav[:, :2] / area, rtol=0, atol=1e-7)


def test_anchor_rule(live_frames):
    for frame in live_frames:
        state = frame["state"]
        parts = an.anchor_set(state)
        anchors = parts["anchors"]
        assert anchors.shape == (9, 2) and anchors.dtype == np.float64
        assert np.all(anchors[an.FREE_LABEL] == 0.0)
        users = frame["state"].astype(np.float64)[32:212].reshape(30, 6)[:, :2] * 8000.0
        centroids, counts = estimator_kmeans(users, 6, 30)
        order = np.argsort(-counts, kind="stable")
        assert np.all(counts[order][:-1] >= counts[order][1:])
        np.testing.assert_array_equal(anchors[2:8], centroids[order] / 8000.0)
        np.testing.assert_array_equal(parts["counts"], counts)
        bs = an.bs_xy_m(state)
        centre = centroids.mean(axis=0)
        for label, fraction in ((0, 1 / 3), (1, 2 / 3)):
            np.testing.assert_allclose(anchors[label] * 8000.0, bs + fraction * (centre - bs),
                                       rtol=0, atol=1e-9)
        # On the BS -> centre segment, in ascending distance from the BS.
        d0, d1 = (np.linalg.norm(anchors[i] * 8000.0 - bs) for i in (0, 1))
        assert d0 <= d1 and np.isclose(d0 + d1, np.linalg.norm(centre - bs), rtol=0, atol=1e-6)
        # Determinism: the same state gives bit-identical anchors.
        np.testing.assert_array_equal(an.anchors_from_state(state), anchors)
        np.testing.assert_array_equal(an.anchors_from_state(state.copy()), anchors)


def test_anchors_agree_with_the_h1_central_plan(live_frames):
    """H1's central plan on the env's float64 positions: same priority list up to rounding."""
    heuristic = LayoutHeuristic(variant("H1", information="central"))
    for frame in live_frames:
        plan = heuristic.plan(frame["obs"], np.zeros(8, dtype=bool), {
            "users_xy": frame["user_positions"][:, :2], "bs_xy": frame["bs_positions"][:, :2]})
        anchors_m = an.anchor_set(frame["state"])["anchors_m"]
        assert plan["kinds"] == ["relay"] * 2 + ["service"] * 6
        # The state carries float32 x/area; x 8000 is within 1e-3 m of the env's float64 value.
        np.testing.assert_allclose(anchors_m[:8], plan["priority"], rtol=0, atol=5e-3)
        # Centroid sets equal up to ordering as well (one-to-one nearest match).
        gaps = np.linalg.norm(anchors_m[2:8, None, :] - plan["centroids"][None, :, :], axis=2)
        assert sorted(np.argmin(gaps, axis=1).tolist()) == list(range(6))
        assert np.max(np.min(gaps, axis=1)) < 5e-3
