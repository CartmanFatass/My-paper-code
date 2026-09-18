"""Tests for ``tools/research_support/controllers.py``.

These are untuned diagnostic rules, not baselines, so the properties that matter are
mechanical rather than scientific:

* the same input gives the same output, including across two fresh instances;
* the clustering controller **draws no random numbers**, so attaching it to a run cannot
  move the environment's random stream by a single draw;
* the furthest-point seeding is deterministic given the same points;
* the commanded action stays inside the documented box.
"""

from __future__ import annotations

import copy
import pathlib
import random
import sys
from typing import Any

import numpy as np
import pytest

_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[3])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

from tools.research_support.controllers import (  # noqa: E402
    LEGACY_CONTROLLERS,
    LegacyClusterCoverageController,
    LegacyHoldController,
    build_legacy_controller,
)

_N_UAVS = 3
_ACTION_DIM = 3


def _state() -> dict[str, Any]:
    return {
        "uav_positions": np.array(
            [[10.0, 10.0, 100.0], [500.0, 500.0, 90.0], [900.0, 100.0, 130.0]]
        ),
        "user_positions": np.array(
            [
                [0.0, 0.0, 0.0], [20.0, 10.0, 0.0], [10.0, 30.0, 0.0],
                [800.0, 800.0, 0.0], [820.0, 780.0, 0.0],
                [900.0, 100.0, 0.0],
            ]
        ),
        "ground_bs_positions": np.array([[0.0, 0.0, 25.0]]),
    }


def _other_state() -> dict[str, Any]:
    return {
        "uav_positions": np.array(
            [[300.0, 700.0, 110.0], [100.0, 100.0, 100.0], [600.0, 600.0, 120.0]]
        ),
        "user_positions": np.array([[400.0, 400.0, 0.0], [450.0, 380.0, 0.0]]),
        "ground_bs_positions": np.array([[1000.0, 1000.0, 25.0]]),
    }


def _rng_fingerprint() -> tuple[Any, ...]:
    """Everything a controller could perturb without anyone noticing."""

    legacy = np.random.get_state()
    return (
        legacy[0],
        legacy[1].tobytes(),
        int(legacy[2]),
        int(legacy[3]),
        float(legacy[4]),
        random.getstate(),
    )


# --------------------------------------------------------------------------------------
# Hold controller
# --------------------------------------------------------------------------------------


def test_hold_controller_commands_exactly_nothing() -> None:
    controller = LegacyHoldController()
    assert controller.name == "legacy_hold"
    assert controller.reset() is None

    action = controller.act(_state(), n_uavs=_N_UAVS, action_dim=_ACTION_DIM)
    assert action.shape == (_N_UAVS, _ACTION_DIM)
    assert action.dtype == np.float32
    assert np.array_equal(action, np.zeros((_N_UAVS, _ACTION_DIM), dtype=np.float32))


def test_hold_controller_is_deterministic_across_fresh_instances() -> None:
    first = LegacyHoldController().act(_state(), n_uavs=_N_UAVS, action_dim=_ACTION_DIM)
    second = LegacyHoldController().act(_state(), n_uavs=_N_UAVS, action_dim=_ACTION_DIM)
    assert np.array_equal(first, second)


# --------------------------------------------------------------------------------------
# Determinism
# --------------------------------------------------------------------------------------


def test_cluster_controller_is_deterministic_across_fresh_instances() -> None:
    first = LegacyClusterCoverageController().act(
        _state(), n_uavs=_N_UAVS, action_dim=_ACTION_DIM
    )
    second = LegacyClusterCoverageController().act(
        _state(), n_uavs=_N_UAVS, action_dim=_ACTION_DIM
    )
    assert np.array_equal(first, second)
    assert first.dtype == np.float32
    assert first.shape == (_N_UAVS, _ACTION_DIM)


def test_cluster_controller_carries_no_hidden_state_between_decisions() -> None:
    fresh = LegacyClusterCoverageController()
    warm = LegacyClusterCoverageController()
    warm.act(_other_state(), n_uavs=_N_UAVS, action_dim=_ACTION_DIM)
    warm.act(_other_state(), n_uavs=_N_UAVS, action_dim=_ACTION_DIM)

    assert np.array_equal(
        warm.act(_state(), n_uavs=_N_UAVS, action_dim=_ACTION_DIM),
        fresh.act(_state(), n_uavs=_N_UAVS, action_dim=_ACTION_DIM),
    )
    # Repeating the same decision repeats the same command.
    assert np.array_equal(
        fresh.act(_state(), n_uavs=_N_UAVS, action_dim=_ACTION_DIM),
        fresh.act(_state(), n_uavs=_N_UAVS, action_dim=_ACTION_DIM),
    )


# --------------------------------------------------------------------------------------
# No random draws
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "factory", [LegacyHoldController, LegacyClusterCoverageController]
)
def test_a_decision_leaves_every_random_stream_untouched(factory) -> None:
    np.random.seed(12345)
    random.seed(999)
    generator = np.random.default_rng(2024)
    generator_state = copy.deepcopy(generator.bit_generator.state)
    before = _rng_fingerprint()

    controller = factory()
    controller.reset()
    for _ in range(3):
        controller.act(_state(), n_uavs=_N_UAVS, action_dim=_ACTION_DIM)

    assert _rng_fingerprint() == before, "the controller consumed a global random draw"
    assert generator.bit_generator.state == generator_state


def test_attaching_the_controller_does_not_shift_the_experiment_random_sequence() -> None:
    """The observable form of the same property: the draw sequence is identical."""

    np.random.seed(7)
    reference = [float(np.random.random()) for _ in range(3)]

    controller = LegacyClusterCoverageController()
    np.random.seed(7)
    observed = []
    for _ in range(3):
        observed.append(float(np.random.random()))
        controller.act(_state(), n_uavs=_N_UAVS, action_dim=_ACTION_DIM)

    assert observed == reference


# --------------------------------------------------------------------------------------
# Seeding
# --------------------------------------------------------------------------------------


def test_furthest_point_seeding_is_deterministic_and_separates_clusters() -> None:
    points = np.array(
        [
            [0.0, 0.0], [10.0, 0.0], [0.0, 10.0], [10.0, 10.0],
            [1000.0, 1000.0], [1010.0, 1000.0], [1000.0, 1010.0],
        ]
    )
    first = LegacyClusterCoverageController()._kmeans(points, 2)
    second = LegacyClusterCoverageController()._kmeans(points, 2)
    assert np.array_equal(first, second)

    # Seed 1 is the point with the smallest coordinate sum; seed 2 is the furthest from it.
    assert np.allclose(first[0], points[:4].mean(axis=0))
    assert np.allclose(first[1], points[4:].mean(axis=0))

    # A shuffled presentation of the same point set yields the same set of centroids.
    shuffled = points[[6, 0, 5, 3, 1, 4, 2]]
    centroids = LegacyClusterCoverageController()._kmeans(shuffled, 2)
    assert np.allclose(np.sort(centroids, axis=0), np.sort(first, axis=0))


def test_kmeans_degenerates_safely() -> None:
    controller = LegacyClusterCoverageController()
    points = np.array([[5.0, 5.0], [7.0, 9.0]])
    assert np.allclose(controller._kmeans(points, 1), points.mean(axis=0, keepdims=True))
    # More clusters than points is clamped, not an error.
    assert controller._kmeans(points, 9).shape == (2, 2)
    assert controller._kmeans(points, 0).shape == (1, 2)
    # Coincident points still terminate.
    identical = np.zeros((4, 2))
    assert np.allclose(controller._kmeans(identical, 3), np.zeros((3, 2)))


def test_assignment_is_a_stable_greedy_matching() -> None:
    uav_xy = np.array([[0.0, 0.0], [100.0, 0.0], [50.0, 50.0]])
    centroids = np.array([[0.0, 5.0], [100.0, 5.0]])
    first = LegacyClusterCoverageController._assign(uav_xy, centroids)
    second = LegacyClusterCoverageController._assign(uav_xy, centroids)
    assert np.array_equal(first, second)
    assert np.allclose(first[0], centroids[0])
    assert np.allclose(first[1], centroids[1])
    # With fewer centroids than UAVs, a centroid is reused rather than leaving a UAV idle.
    assert first[2].tolist() in (centroids[0].tolist(), centroids[1].tolist())


# --------------------------------------------------------------------------------------
# Commanded action
# --------------------------------------------------------------------------------------


def test_the_commanded_action_stays_inside_the_documented_box() -> None:
    action = LegacyClusterCoverageController().act(
        _state(), n_uavs=_N_UAVS, action_dim=_ACTION_DIM
    )
    assert action.dtype == np.float32
    assert np.all(action >= -1.0) and np.all(action <= 1.0)
    assert np.all(np.isfinite(action))
    horizontal = np.linalg.norm(action[:, :2], axis=1)
    assert np.all(horizontal <= 1.0 + 1e-6), "the horizontal command is a unit direction"


def test_altitude_command_is_a_clipped_proportional_term() -> None:
    controller = LegacyClusterCoverageController(
        target_altitude_m=120.0, altitude_gain=0.02, relay_fraction=0.0
    )
    state = _state()
    action = controller.act(state, n_uavs=_N_UAVS, action_dim=3)
    expected = np.clip((120.0 - state["uav_positions"][:, 2]) * 0.02, -1.0, 1.0)
    assert np.allclose(action[:, 2], expected.astype(np.float32), atol=1e-6)


def test_an_arrived_uav_is_commanded_to_hold_its_horizontal_position() -> None:
    controller = LegacyClusterCoverageController(
        relay_fraction=0.0, arrival_radius_m=40.0, altitude_gain=0.0
    )
    state = {
        "uav_positions": np.array([[100.0, 100.0, 120.0]]),
        "user_positions": np.array([[100.0, 100.0, 0.0], [110.0, 105.0, 0.0]]),
    }
    action = controller.act(state, n_uavs=1, action_dim=3)
    assert np.allclose(action[0, :2], 0.0), "a UAV inside the arrival radius must not jitter"


def test_a_distant_uav_is_commanded_toward_its_target() -> None:
    controller = LegacyClusterCoverageController(relay_fraction=0.0, altitude_gain=0.0)
    state = {
        "uav_positions": np.array([[0.0, 0.0, 120.0]]),
        "user_positions": np.array([[1000.0, 0.0, 0.0], [1000.0, 10.0, 0.0]]),
    }
    action = controller.act(state, n_uavs=1, action_dim=3)
    assert action[0, 0] == pytest.approx(1.0, abs=1e-3)
    assert abs(float(action[0, 1])) < 0.05


@pytest.mark.parametrize(
    "state",
    [
        {"uav_positions": np.zeros((3, 3))},
        {"uav_positions": np.zeros((3, 3)), "user_positions": None},
        {"uav_positions": np.zeros((3, 3)), "user_positions": np.zeros((0, 3))},
        {"uav_positions": np.zeros((0, 3)), "user_positions": np.zeros((2, 3))},
    ],
)
def test_a_frame_without_usable_positions_commands_zero(state: dict[str, Any]) -> None:
    action = LegacyClusterCoverageController().act(
        state, n_uavs=_N_UAVS, action_dim=_ACTION_DIM
    )
    assert np.array_equal(action, np.zeros((_N_UAVS, _ACTION_DIM), dtype=np.float32))


def test_a_two_dimensional_action_space_gets_no_altitude_channel() -> None:
    action = LegacyClusterCoverageController().act(_state(), n_uavs=_N_UAVS, action_dim=2)
    assert action.shape == (_N_UAVS, 2)


# --------------------------------------------------------------------------------------
# Relay placement and intent reporting
# --------------------------------------------------------------------------------------


def test_relay_targets_sit_on_the_station_to_demand_line() -> None:
    controller = LegacyClusterCoverageController(relay_fraction=0.34)
    state = _state()
    controller.act(state, n_uavs=_N_UAVS, action_dim=_ACTION_DIM)
    targets = controller.targets_xy
    assert targets is not None and targets.shape == (_N_UAVS, 2)

    station = state["ground_bs_positions"][0, :2]
    ue_centroid = state["user_positions"][:, :2].mean(axis=0)
    expected_relay = station + 0.5 * (ue_centroid - station)
    assert any(np.allclose(row, expected_relay) for row in targets), targets


def test_relay_fraction_zero_leaves_every_target_on_a_centroid() -> None:
    controller = LegacyClusterCoverageController(relay_fraction=0.0)
    state = _state()
    controller.act(state, n_uavs=_N_UAVS, action_dim=_ACTION_DIM)
    centroids = controller._kmeans(state["user_positions"][:, :2], _N_UAVS)
    targets = controller.targets_xy
    assert targets is not None
    for row in targets:
        assert any(np.allclose(row, centroid) for centroid in centroids)


def test_targets_are_reported_as_a_copy_and_cleared_by_reset() -> None:
    controller = LegacyClusterCoverageController()
    assert controller.targets_xy is None
    controller.act(_state(), n_uavs=_N_UAVS, action_dim=_ACTION_DIM)

    first = controller.targets_xy
    assert first is not None
    first[:] = -12345.0  # a report must not be able to corrupt the controller
    assert not np.allclose(controller.targets_xy, -12345.0)

    controller.reset()
    assert controller.targets_xy is None


# --------------------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------------------


def test_the_registry_exposes_both_named_rules() -> None:
    assert set(LEGACY_CONTROLLERS) == {"legacy_hold", "legacy_cluster_coverage"}
    assert LEGACY_CONTROLLERS["legacy_hold"] is LegacyHoldController
    assert LEGACY_CONTROLLERS["legacy_cluster_coverage"] is LegacyClusterCoverageController


def test_build_legacy_controller_forwards_settings() -> None:
    controller = build_legacy_controller("legacy_cluster_coverage", relay_fraction=0.5)
    assert isinstance(controller, LegacyClusterCoverageController)
    assert controller.relay_fraction == 0.5
    assert build_legacy_controller("legacy_hold").name == "legacy_hold"


def test_build_legacy_controller_names_the_available_rules_on_a_typo() -> None:
    with pytest.raises(ValueError) as error:
        build_legacy_controller("legacy_clusters")
    message = str(error.value)
    assert "unknown legacy controller 'legacy_clusters'" in message
    assert "legacy_cluster_coverage" in message and "legacy_hold" in message
