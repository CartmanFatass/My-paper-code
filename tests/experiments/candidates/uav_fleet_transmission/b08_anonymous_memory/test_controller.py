"""Finite lawful-array checks only: no native construction, query or rollout."""

from __future__ import annotations

import numpy as np
import pytest

from experiments.candidates.uav_fleet_transmission.b08_anonymous_memory import controller as b08
from experiments.candidates.uav_information_value.b02 import controller as frozen
from experiments.candidates.uav_information_value import controllers as sources


@pytest.fixture(scope="session", autouse=True)
def finite_operation_counts():
    """Count actual entry calls, including reference canonicalizers and failed checks."""
    counts = {"canonicalizations": 0, "associations": 0, "projections": 0}
    patch = pytest.MonkeyPatch()

    def counted(name, function):
        def invoke(*args, **kwargs):
            counts[name] += 1
            return function(*args, **kwargs)
        return invoke

    canonical = counted("canonicalizations", sources.canonical_legal_users)
    patch.setattr(sources, "canonical_legal_users", canonical)
    patch.setattr(frozen, "canonical_legal_users", canonical)
    patch.setattr(b08, "canonical_with_provenance",
                  counted("canonicalizations", b08.canonical_with_provenance))
    patch.setattr(b08.AnonymousTracker, "update",
                  counted("associations", b08.AnonymousTracker.update))
    project = b08.AnonymousTracker.supplied_points

    def supplied(self, arm, step):
        if arm == "V":
            counts["projections"] += 1
        return project(self, arm, step)

    patch.setattr(b08.AnonymousTracker, "supplied_points", supplied)
    yield counts
    patch.undo()
    print(f"\nB08 finite actual operation counts: {counts}")
    assert counts["canonicalizations"] <= 1024
    assert counts["associations"] <= 1024
    assert counts["projections"] <= 256


class Poison:
    def __getattribute__(self, name):
        raise AssertionError(f"truth/feedback was accessed: {name}")

    def __array__(self, *args, **kwargs):
        raise AssertionError("truth/feedback was converted")


def frame(users=(), *, bs=None, stations=((7000., 500.), (1000., 7000.))):
    layout = b08.S7S2_LAYOUT
    obs = np.zeros((8, layout.dim), dtype=np.float32)
    obs[:, :2] = (1000. / 8000., 900. / 8000.)
    obs[:, 2] = 1. / 3.
    own = obs[0, :2].astype(np.float64) * 8000.
    # One observer supplies all users: other lawful slots remain empty.
    for slot, xy in enumerate(users):
        base = layout.users.start + slot * layout.user_fields
        obs[0, base:base + 2] = (np.asarray(xy) - own) / 8000.
        obs[0, base + 4] = 1.
    for station, xy in enumerate(stations):
        if xy is not None:
            base = layout.energy_stations.start + station * layout.energy_station_fields
            obs[0, base:base + 2] = (np.asarray(xy) - own) / 8000.
            obs[0, base + 7] = 1.
    if bs is not None:
        obs[:, layout.bs.start:layout.bs.start + 2] = (np.asarray(bs) - own) / 8000.
        obs[:, layout.bs.start + 3] = 1.
    return obs


def propose(controller, observations, step, modes=None):
    modes = np.zeros(8, dtype=bool) if modes is None else modes
    before = observations.copy()
    result = controller.propose(observations, Poison(), step, Poison(), modes)
    np.testing.assert_array_equal(observations, before)
    return result


def test_canonical_frozen_bytes_and_raw_slot_provenance():
    obs = frame([(1000., 1000.), (1000.375, 1000.), (1000.75, 1000.), (5000., 2000.)])
    layout = b08.S7S2_LAYOUT
    # Duplicate the first point into a later observer, preserving raw slot identity.
    obs[3, layout.users.start:layout.users.start + layout.user_fields] = (
        obs[0, layout.users.start:layout.users.start + layout.user_fields])
    expected = sources.canonical_legal_users(obs, layout, .5)
    trace = b08.canonical_with_provenance(obs)
    assert trace["canonical_xy"].tobytes() == expected.tobytes()
    assert len(expected) == 3  # Greedy merge keeps endpoints of the near-neighbor chain.
    np.testing.assert_array_equal(trace["kept_flat_indices"], [0, 2, 3])
    np.testing.assert_array_equal(trace["raw_to_canonical"][0, :4], [0, 0, 1, 2])
    assert trace["raw_to_canonical"][3, 0] == 0
    assert np.count_nonzero(trace["raw_to_canonical"] >= 0) == 5
    empty = b08.canonical_with_provenance(frame())
    assert empty["canonical_xy"].shape == (0, 2)
    assert empty["raw_to_canonical"].shape == (8, 30)
    assert np.all(empty["raw_to_canonical"] == -1)


def test_mutual_unique_ambiguity_requires_clean_adjacent_history():
    tracker = b08.AnonymousTracker()
    tracker.update([[100., 100.], [104., 100.]], 0)
    result = tracker.update([[102., 100.]], 1)
    assert result["events"]["discarded"].tolist() == [0, 1]
    assert result["events"]["ambiguous"].tolist() == [2]
    assert not result["tracks"]["unambiguous"][0]
    np.testing.assert_array_equal(result["tracks"]["v"], [[0., 0.]])
    result = tracker.update([[103., 100.]], 2)
    assert result["events"]["continued"].tolist() == [2]
    assert result["tracks"]["unambiguous"][0]
    np.testing.assert_array_equal(result["tracks"]["v"], [[0., 0.]])
    result = tracker.update([[104., 100.]], 3)
    np.testing.assert_array_equal(result["tracks"]["v"], [[1., 0.]])
    # The reciprocal ambiguity case: one old hypothesis with two feasible currents.
    tracker.reset()
    tracker.update([[100., 100.]], 0)
    result = tracker.update([[99., 100.], [101., 100.]], 1)
    assert result["events"]["discarded"].tolist() == [0]
    assert result["events"]["ambiguous"].tolist() == [1, 2]
    assert result["event_counts"]["continued"] == 0


def test_gap_zero_velocity_and_expiration_before_matching():
    tracker = b08.AnonymousTracker()
    tracker.update([[100., 100.]], 0)
    tracker.update([[102., 100.]], 1)
    result = tracker.update([], 2)
    np.testing.assert_array_equal(result["tracks"]["v"], [[2., 0.]])
    assert not result["tracks"]["current"][0]
    result = tracker.update([[106., 100.]], 3)
    assert result["events"]["continued"].tolist() == [0]
    np.testing.assert_array_equal(result["tracks"]["v"], [[0., 0.]])
    tracker.reset()
    tracker.update([[100., 100.]], 0)
    result = tracker.update([], 30)
    assert len(result["tracks"]) == 1
    result = tracker.update([[100., 100.]], 31)
    assert result["events"]["expired"].tolist() == [0]
    assert result["events"]["new"].tolist() == [1]
    assert result["events"]["continued"].size == 0
    assert result["tracks"]["unambiguous"][0]


def test_cap_fresh_first_age_birth_ties_and_permanent_drop():
    tracker = b08.AnonymousTracker()
    old = np.column_stack((np.arange(30) * 100., np.full(30, 100.)))
    tracker.update(old, 0)
    tracker.update(old[:2], 1)  # births 0 and 1 now have the freshest last_seen.
    current = np.column_stack((np.arange(28) * 100., np.full(28, 5000.)))
    result = tracker.update(current, 2)
    assert len(result["tracks"]) == 30
    assert result["tracks"]["birth"].tolist() == list(range(30, 58)) + [0, 1]
    assert result["events"]["cap_drop"].tolist() == list(range(2, 30))
    points = tracker.supplied_points("M", 2)
    assert points[:28].tobytes() == current.astype(np.float64).tobytes()
    result = tracker.update([], 3)
    assert set(result["tracks"]["birth"]) == set(range(30, 58)) | {0, 1}
    with pytest.raises(AssertionError, match="cap"):
        tracker.update(np.zeros((31, 2)), 4)


def test_speed_norm_projection_age_arena_and_no_second_merge():
    tracker = b08.AnonymousTracker()
    tracker.update([[7997., 4000.], [2000., 10.]], 0)
    result = tracker.update([[8000., 4001.], [2000., 7.]], 1)
    np.testing.assert_allclose(result["tracks"]["v"][0], [3., 1.] / np.sqrt(10.) * 3.)
    assert np.linalg.norm(result["tracks"]["v"][0]) <= 3. + 1e-15
    tracker.update([], 2)
    projected = tracker.supplied_points("V", 2)
    np.testing.assert_allclose(projected[0], [8000., 4001. + 16. * 3. / np.sqrt(10.)])
    np.testing.assert_array_equal(projected[1], [2000., 0.])
    tracker.reset()
    tracker.update([[7996., 100.], [7996., 104.]], 0)
    tracker.update([[7999., 100.], [7999., 104.]], 1)
    result = tracker.supplied_points("V", 1)
    np.testing.assert_array_equal(result, [[8000., 100.], [8000., 104.]])
    # Projection can collide; array order/count must survive without a merge.
    tracker.reset()
    tracker.update([[7988., 7997.], [7997., 7988.]], 0)
    tracker.update([[7990., 7999.], [7999., 7990.]], 1)
    np.testing.assert_array_equal(tracker.supplied_points("V", 1),
                                  [[8000., 8000.], [8000., 8000.]])


def test_trace_copies_reset_and_input_ownership():
    controller = b08.MemoryController("M")
    propose(controller, frame([(1000., 2000.)]), 0)
    trace = controller.last_trace
    trace["canonical_xy"][:] = -1.
    trace["tracks"]["last_xy"][:] = -1.
    trace["events"]["new"][:] = -1
    trace["plan_supplied_xy"][:] = -1.
    trace["raw_to_canonical"][:] = -1
    fresh = controller.last_trace
    assert np.all(fresh["canonical_xy"] >= 0.)
    assert fresh["events"]["new"].tolist() == [0]
    assert fresh["raw_to_canonical"][0, 0] == 0
    snapshot = controller.tracker.snapshot()
    snapshot["tracks"]["v"][:] = 100.
    assert np.all(controller.tracker.snapshot()["tracks"]["v"] == 0.)
    counters = controller.counters
    counters["associations"] = -1
    assert controller.counters["associations"] == 1
    controller.reset()
    assert controller.last_trace is None
    assert all(value == 0 for value in controller.counters.values())
    propose(controller, frame([(3000., 4000.)]), 0)
    assert controller.last_trace["tracks"]["birth"].tolist() == [0]
    with pytest.raises(ValueError, match="arm"):
        b08.MemoryController("OTHER")


def test_c_direct_inherited_path_and_m_v_exact_static_stream_parity():
    reference = frozen.StationPriorController()
    controllers = [b08.MemoryController(arm) for arm in ("C", "M", "V")]
    users = [(1400. + i * 700., 4100. - i * 170.) for i in range(8)]
    numpy_rng = np.random.get_state()
    for step in range(61):
        obs = frame(users, bs=(3300., 5200.) if step in (7, 60) else None,
                    stations=((2000., 2000.), (5000., 5000.)) if step else
                    ((7000., 500.), (1000., 7000.)))
        modes = np.zeros(8, dtype=bool)
        modes[6:] = step >= 30  # exercise availability and previous-target hysteresis.
        expected = propose(reference, obs, step, modes)
        for controller in controllers:
            actual = propose(controller, obs, step, modes)
            assert actual.tobytes() == expected.tobytes()
            assert controller.targets_xy.tobytes() == reference.targets_xy.tobytes()
            assert controller.diagnostics == reference.diagnostics
            trace = controller.last_trace
            assert trace["replanned"] == (step % 30 == 0)
            if step % 30 == 0:
                assert trace["plan_supplied_xy"].tobytes() == reference.heuristic.last_plan["users"].tobytes()
            else:
                assert trace["plan_supplied_xy"] is None
    assert [row["bs_input_source"] for row in controllers[0].diagnostics] == [
        "inferred", "observed-memory", "observed-current"]
    assert controllers[0].counters == {"proposals": 61, "plans": 3, "canonicalizations": 3,
                                        "associations": 0, "projections": 0}
    assert controllers[1].counters == {"proposals": 61, "plans": 3, "canonicalizations": 61,
                                        "associations": 61, "projections": 0}
    assert controllers[2].counters == {"proposals": 61, "plans": 3, "canonicalizations": 61,
                                        "associations": 61, "projections": 3}
    after = np.random.get_state()
    assert numpy_rng[0] == after[0] and numpy_rng[2:] == after[2:]
    np.testing.assert_array_equal(numpy_rng[1], after[1])


def test_primitive_ingestion_memory_prefix_and_original_empty_fallback():
    memory = b08.MemoryController("M")
    propose(memory, frame(), 0)
    assert memory.heuristic.last_plan["search"]
    assert memory.last_trace["plan_supplied_xy"].shape == (0, 2)
    propose(memory, frame([(1000., 2000.), (5000., 6000.)]), 1)
    for step in range(2, 30):
        propose(memory, frame([(1000., 2000.)]), step)
    obs = frame([(1000., 2000.)])
    propose(memory, obs, 30)
    trace = memory.last_trace
    assert trace["plan_supplied_xy"][:1].tobytes() == trace["canonical_xy"].tobytes()
    assert len(trace["plan_supplied_xy"]) == 2
    assert trace["tracks"]["current"].tolist() == [True, False]
    assert trace["tracks"]["last_seen"].tolist() == [30, 1]
    assert memory.counters["canonicalizations"] == memory.counters["associations"] == 31


def test_inclusive_matching_boundary_and_30s_retention():
    tracker = b08.AnonymousTracker()
    tracker.update([[100., 100.]], 0)
    result = tracker.update([[103.5, 100.]], 1)
    assert result["events"]["continued"].tolist() == [0]
    np.testing.assert_array_equal(result["tracks"]["v"], [[3., 0.]])
    tracker.reset()
    tracker.update([[100., 100.]], 0)
    result = tracker.update([[103.500001, 100.]], 1)
    assert result["events"]["new"].tolist() == [1]
    assert result["tracks"]["birth"].tolist() == [1, 0]
    tracker.reset()
    tracker.update([[100., 100.]], 0)
    result = tracker.update([[190.5, 100.]], 30)
    assert result["events"]["continued"].tolist() == [0]
    np.testing.assert_array_equal(result["tracks"]["v"], [[0., 0.]])


def test_v_adapter_projects_adjacent_primitive_history_at_replan():
    controller = b08.MemoryController("V")
    for step in range(31):
        obs = frame([(2000. + step, 3000.)])
        propose(controller, obs, step)
    previous = sources.canonical_legal_users(frame([(2029., 3000.)]), b08.S7S2_LAYOUT, .5)
    current = sources.canonical_legal_users(obs, b08.S7S2_LAYOUT, .5)
    velocity = current - previous
    assert velocity[0, 0] > .99
    expected = current + 15. * velocity
    assert controller.last_trace["canonical_xy"].tobytes() == current.tobytes()
    assert controller.last_trace["plan_supplied_xy"].tobytes() == expected.tobytes()
    assert controller.heuristic.last_plan["users"].tobytes() == expected.tobytes()
    assert controller.counters == {"proposals": 31, "plans": 2, "canonicalizations": 31,
                                    "associations": 31, "projections": 2}
