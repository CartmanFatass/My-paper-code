"""C06 physical-belief contract checks; no research score is produced here."""

from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from experiments.candidates.skill_information_refresh.c01.host import (
    APPROACH,
    BYPASS,
    CROSSING,
    DONE,
    PERIODS,
    SHARED,
    CrossingHost,
    Worlds,
    choose_route,
    project,
)
from experiments.candidates.skill_information_refresh.c06.belief import (
    BeliefContradiction,
    LocalRecord,
    PhysicalBelief,
    take_local,
)


def fixture_host(batch=4):
    return CrossingHost(Worlds.make(1, 6, range(batch), horizon=48))


def record(t, agent, own, *, last_sent=None, last_time=None, peer=None, peer_time=None):
    own = np.asarray(own, dtype=np.int16)
    batch = own.shape[0]
    zeros = np.zeros((batch, 5), dtype=np.int16)
    return LocalRecord(
        t=t,
        horizon=48,
        agent=agent,
        own=own,
        last_sent=zeros if last_sent is None else last_sent,
        last_sent_time=np.full(batch, -1) if last_time is None else last_time,
        peer_packet=zeros if peer is None else peer,
        peer_packet_time=np.full(batch, -1) if peer_time is None else peer_time,
        available=np.ones(batch, dtype=bool),
    )


def state_index(belief, state):
    matches = np.all(belief.states == np.asarray(state), axis=1)
    assert matches.sum() == 1
    return int(np.flatnonzero(matches)[0])


def test_take_local_is_copied_readonly_and_has_no_unsent_peer_or_world_input():
    host = fixture_host(batch=2)
    host.cache[0, 0] = [CROSSING, 0, 1, 9, SHARED]
    host.cache_time[0, 0] = -3  # Raw cache/time must not be projected at the boundary.
    before = take_local(host, 0)
    snapshots = {name: getattr(before, name).copy() for name in (
        "own", "last_sent", "last_sent_time", "peer_packet", "peer_packet_time", "available")}

    host.stage[:, 1] = DONE
    host.distance[:, 1] = 0
    host.cross_left[:, 1] = 0
    host.route[:, 1] = BYPASS
    host.worlds.advances[:, 1:] = ~host.worlds.advances[:, 1:]
    host.worlds.jobs[:, 1:] = 7
    after = take_local(host, 0)
    for name, expected in snapshots.items():
        np.testing.assert_array_equal(getattr(after, name), expected)
        assert not getattr(before, name).flags.writeable
    assert before.peer_packet[0].tolist() == [CROSSING, 0, 1, 9, SHARED]
    assert before.peer_packet_time[0] == -3
    with pytest.raises(ValueError):
        before.own[0, 0] = DONE
    with pytest.raises(FrozenInstanceError):
        before.t = 3


def test_initial_support_sampling_shape_probabilities_and_counts():
    belief = PhysicalBelief(take_local(fixture_host(batch=2), 0))
    assert belief.states.shape == (22, 4)
    assert not belief.states.flags.writeable
    np.testing.assert_allclose(belief.weights.sum(axis=1), 1)
    for distance in range(1, 8):
        assert belief.weights[0, state_index(belief, (APPROACH, distance, 0, SHARED))] == pytest.approx(1 / 7)
    assert np.count_nonzero(belief.weights[0]) == 7

    uniforms = np.array([[0, .14, .50, .999], [.01, .30, .70, .98]])
    payloads = belief.sample_payloads(uniforms)
    assert payloads.shape == (2, 4, 5)
    assert (payloads[..., 0] == APPROACH).all()
    assert (payloads[..., 3] == PERIODS[1]).all()
    assert (payloads[..., 4] == SHARED).all()
    sampled, counts = belief.sample(uniforms)
    np.testing.assert_array_equal(sampled, payloads)
    assert counts.shape == belief.weights.shape
    assert counts.sum(axis=1).tolist() == [4, 4]
    rng_payloads, rng_counts = belief.sample(np.random.default_rng(9), particles=5)
    assert rng_payloads.shape == (2, 5, 5)
    assert rng_counts.sum(axis=1).tolist() == [5, 5]
    assert belief.stats == {"observations": 1, "packet_updates": 0, "contradictions": 0}


def test_new_packet_conditions_previous_tick_before_motion():
    initial = record(0, 0, [[APPROACH, 1, 0, 12, SHARED]])
    belief = PhysicalBelief(initial)
    delivered = np.array([[APPROACH, 3, 0, 16, SHARED]], dtype=np.int16)
    current = record(1, 0, [[APPROACH, 0, 0, 11, SHARED]],
        peer=delivered, peer_time=np.array([0]))
    belief.update(current)

    # The t=0 packet is first a point mass at distance 3, then the t=0 motion is
    # propagated. Treating it as a current-tick packet would leave only distance 3.
    d2 = state_index(belief, (APPROACH, 2, 0, SHARED))
    d3 = state_index(belief, (APPROACH, 3, 0, SHARED))
    assert belief.weights[0, d2] == pytest.approx(.75)
    assert belief.weights[0, d3] == pytest.approx(.25)
    assert np.count_nonzero(belief.weights[0]) == 2
    assert belief.stats["packet_updates"] == 1


def test_deterministic_own_collision_observation_conditions_hidden_peer():
    belief = PhysicalBelief(record(0, 0, [[APPROACH, 1, 0, 12, SHARED]]))
    belief.update(record(1, 0, [[APPROACH, 0, 0, 11, SHARED]]))
    crossing = state_index(belief, (CROSSING, 0, 1, SHARED))
    done = state_index(belief, (DONE, 0, 0, SHARED))
    belief.weights.fill(0)
    belief.weights[0, crossing] = .5
    belief.weights[0, done] = .5

    belief.update(record(2, 0, [[DONE, 0, 0, 10, SHARED]]))
    assert belief.weights[0, done] == pytest.approx(1)
    assert np.count_nonzero(belief.weights[0]) == 1


def test_period_reset_uses_newly_sent_own_packet_before_route_choice():
    host = fixture_host(batch=3)
    beliefs = [PhysicalBelief(take_local(host, agent)) for agent in (0, 1)]
    at_boundary = None
    for tick in range(12):
        if tick:
            for agent, belief in enumerate(beliefs):
                belief.update(take_local(host, agent))
        # The requested t=11 agent-1 send is delivered before peer 0 resets at t=12.
        host.step(np.full(host.batch, tick == 11))
    at_boundary = take_local(host, 1)
    assert (at_boundary.last_sent_time == 11).all()
    beliefs[1].update(at_boundary)

    for row in range(host.batch):
        cache, valid, _ = project(at_boundary.last_sent[row:row + 1],
            at_boundary.last_sent_time[row:row + 1], 12)
        distances = np.arange(1, 8, dtype=np.int16)
        routes = choose_route(distances, PERIODS[0], cache, valid)
        expected = {
            state_index(beliefs[1], (APPROACH, int(distance), 0, int(route)))
            for distance, route in zip(distances, routes)
        }
        positive = set(np.flatnonzero(beliefs[1].weights[row] > 0))
        assert positive == expected
        np.testing.assert_allclose(beliefs[1].weights[row, list(expected)], 1 / 7)


def test_fixed_lawful_trace_keeps_actual_peer_in_positive_support():
    host = fixture_host(batch=6)
    beliefs = [PhysicalBelief(take_local(host, agent)) for agent in (0, 1)]
    packet_updates = 0
    for tick in range(host.horizon):
        if tick:
            for agent, belief in enumerate(beliefs):
                belief.update(take_local(host, agent))
                peer = 1 - agent
                for row in range(host.batch):
                    actual = (int(host.stage[row, peer]), int(host.distance[row, peer]),
                        int(host.cross_left[row, peer]), int(host.route[row, peer]))
                    assert belief.weights[row, state_index(belief, actual)] > 0
            packet_updates = sum(belief.stats["packet_updates"] for belief in beliefs)
        requests = (np.arange(host.batch) + 2 * tick) % 5 < 2
        host.step(requests)

    assert packet_updates > 0
    assert host.metrics["conflicts"].sum() > 0
    assert all(belief.stats["observations"] == host.horizon for belief in beliefs)
    assert all(belief.stats["contradictions"] == 0 for belief in beliefs)


def test_zero_support_packet_raises_and_counts_without_hidden_state_fallback():
    initial = record(0, 0, [[APPROACH, 1, 0, 12, SHARED]])
    belief = PhysicalBelief(initial)
    impossible = np.array([[CROSSING, 0, 1, 16, SHARED]], dtype=np.int16)
    current = record(1, 0, [[APPROACH, 0, 0, 11, SHARED]],
        peer=impossible, peer_time=np.array([0]))
    before = belief.weights.copy()
    with pytest.raises(BeliefContradiction, match="zero compatible support"):
        belief.update(current)
    np.testing.assert_array_equal(belief.weights, before)
    assert belief.record is initial
    assert belief.stats["contradictions"] == 1
    assert belief.stats["observations"] == 1


def test_consecutive_same_cadence_records_are_required():
    belief = PhysicalBelief(record(0, 0, [[APPROACH, 1, 0, 12, SHARED]]))
    with pytest.raises(ValueError, match="every consecutive tick"):
        belief.update(record(2, 0, [[APPROACH, 0, 0, 10, SHARED]]))
