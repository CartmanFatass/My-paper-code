"""Focused semantic checks for the B01 host, joint filter, and paired planner."""

from dataclasses import replace

import numpy as np
import pytest

from experiments.candidates.finite_model_decision_value.b01.belief import (
    BeliefContradiction, JointPhysicalBelief, LocalRecord, STATE_SUPPORT,
    _STATE_INDEX, take_local,
)
from experiments.candidates.finite_model_decision_value.b01.host import (
    APPROACH, CROSSING, SHARED, CrossingHost, Worlds, choose_route, project,
)
from experiments.candidates.finite_model_decision_value.b01.planning import (
    independent_model_worlds, paired_values, select_record,
)


def _record(t=0, *, agent=1, own_distance=0, own_stage=APPROACH,
            own_cross=0, peer_packet_time=-1, peer_distance=0):
    remaining = (12, 16)[agent] - t % (12, 16)[agent]
    packet = [APPROACH, peer_distance, 0, 12, SHARED]
    return LocalRecord(t, 48, agent,
        np.array([[own_stage, own_distance, own_cross, remaining, SHARED]]),
        np.zeros((1, 5), dtype=np.int16), np.array([-1]),
        np.array([packet]), np.array([peer_packet_time]), np.array([True]))


def test_host_parameter_law_preserves_original_rng_and_nominal_receiver():
    ids = (19, 7)
    law = np.array([.0, 1.0])
    worlds = Worlds.make(81, 9, ids, horizon=48, probabilities=law)
    assert not worlds.advances[0].any()
    assert worlds.advances[1].all()
    for row, world in enumerate(ids):
        expected = np.random.default_rng(np.random.SeedSequence([81, 9, world, 2]))
        np.testing.assert_array_equal(worlds.jobs[row], expected.integers(1, 8, (48, 2), dtype=np.int16))
    known = Worlds.make(81, 9, ids, horizon=48, probabilities=.75)
    for row, world in enumerate(ids):
        expected = np.random.default_rng(np.random.SeedSequence([81, 9, world, 1]))
        np.testing.assert_array_equal(known.advances[row], expected.random((48, 2)) < .75)
    packet = np.array([[APPROACH, 6, 0, 12, SHARED]], dtype=np.int16)
    assert project(packet, np.array([0]), 4)[0][0, 1] == 3
    assert choose_route(np.array([3]), 12, packet, np.array([True]))[0] == SHARED


def test_joint_packet_likelihood_retains_parameter_mass_and_one_global_normalizer():
    old = _record()
    belief = JointPhysicalBelief(old, np.array([.25, .75]), np.array([[.5, .5]]))
    i1 = _STATE_INDEX[(APPROACH, 1, 0, SHARED)]
    i2 = _STATE_INDEX[(APPROACH, 2, 0, SHARED)]
    belief.weights.fill(0)
    belief.weights[0, 0, i1], belief.weights[0, 0, i2] = .1, .4
    belief.weights[0, 1, i1], belief.weights[0, 1, i2] = .4, .1
    new = _record(t=1, own_stage=CROSSING, own_cross=1,
                  peer_packet_time=0, peer_distance=1)
    belief.update(new)
    np.testing.assert_allclose(belief.parameter_weights[0], [.2, .8], atol=1e-14)
    np.testing.assert_allclose(belief.weights.sum(), 1., atol=1e-14)
    assert belief.stats['packet_updates'] == 1
    assert belief.stats['transition_cases'] > 0
    # One component can lose all packet support while the other survives.
    belief2 = JointPhysicalBelief(old, [.25, .75], [[.5, .5]])
    belief2.weights.fill(0)
    belief2.weights[0, 0, i1] = .5
    belief2.weights[0, 1, i2] = .5
    belief2.update(new)
    np.testing.assert_array_equal(belief2.parameter_weights[0], [1., 0.])
    impossible = replace(new, peer_packet=np.array([[APPROACH, 0, 0, 12, SHARED]]))
    belief3 = JointPhysicalBelief(old, [.25, .75], [[.5, .5]])
    with pytest.raises(BeliefContradiction):
        belief3.update(impossible)


def test_own_likelihood_and_boundary_mask():
    initial = _record(agent=1, own_distance=3)
    progressed = _record(t=1, agent=1, own_distance=2)
    belief = JointPhysicalBelief(initial, [.25, .75], [[.5, .5]])
    belief.update(progressed)
    np.testing.assert_allclose(belief.parameter_weights[0], [.25, .75], atol=1e-14)
    # At t=16 robot 1 receives an exogenous job; its new distance is not a
    # Bernoulli observation. Reach that boundary with lawful synthetic records.
    first = _record(t=15, agent=1, own_distance=3)
    boundary = _record(t=16, agent=1, own_distance=7)
    masked = JointPhysicalBelief(_record(agent=1, own_distance=3), [.25, .75], [[.5, .5]])
    masked.record = first
    masked.update(boundary)
    np.testing.assert_allclose(masked.parameter_weights[0], [.5, .5], atol=1e-14)


def test_lawful_host_records_filter_without_peer_truth_or_futures():
    worlds = Worlds.make(219, 5, [13, 27], horizon=48, probabilities=[.35, .95])
    host = CrossingHost(worlds)
    left = JointPhysicalBelief(take_local(host, 0), [.35, .95], [[.5, .5], [.5, .5]])
    right = JointPhysicalBelief(take_local(host, 1), [.35, .95], [[.5, .5], [.5, .5]])
    for _ in range(47):
        # Sending every available slot includes delivery and quota boundaries.
        host.step(np.ones(host.batch, dtype=bool))
        left.update(take_local(host, 0))
        right.update(take_local(host, 1))
        np.testing.assert_allclose(left.weights.sum(axis=(1, 2)), 1., atol=1e-12)
        np.testing.assert_allclose(right.weights.sum(axis=(1, 2)), 1., atol=1e-12)
    assert left.stats['packet_updates'] > 0
    assert right.stats['packet_updates'] > 0


def test_planner_degenerate_identity_root_coupling_and_addressing():
    host = CrossingHost(Worlds.make(31, 2, [7, 9], horizon=48))
    record = take_local(host, 0)
    belief = JointPhysicalBelief(record, [.65], np.ones((2, 1)))
    kwargs = dict(seed=101, phase=4, particles=3)
    p = paired_values(record, belief.weights, belief.theta_values, belief.states,
                      [7, 9], mode='POSTERIOR_MEAN', **kwargs)
    u = paired_values(record, belief.weights, belief.theta_values, belief.states,
                      [7, 9], mode='JOINT', **kwargs)
    for name in ('root_state_index', 'root_theta', 'sample_delta', 'near_end',
                 'opportunity_tick', 'opportunity_kind', 'delta', 'mc_se'):
        np.testing.assert_array_equal(p[name], u[name])
    assert p['sample_delta'].shape == (2, 3)
    assert np.all(p['near_end'] <= 32)
    assert p['model_branch_transitions'] == 2 * 2 * 3 * p['end']
    # Reordering observations does not change ID-addressed exogenous streams.
    reordered = select_record(record, [1, 0])
    q = paired_values(reordered, belief.weights[[1, 0]], belief.theta_values[[1, 0]],
                      belief.states, [9, 7], mode='JOINT', **kwargs)
    for name in ('root_state_index', 'root_theta', 'sample_delta', 'near_end'):
        np.testing.assert_array_equal(q[name], u[name][[1, 0]])
    a = independent_model_worlds(record, [7, 9], 101, 4, 3)
    b = independent_model_worlds(reordered, [9, 7], 101, 4, 3)
    np.testing.assert_array_equal(a[0][::-1], b[0])
    np.testing.assert_array_equal(a[1][::-1], b[1])
    np.testing.assert_array_equal(a[2].reshape(2, 3, 48, 2)[::-1], b[2].reshape(2, 3, 48, 2))


def test_near_commitment_includes_next_receiver_opportunity():
    host = CrossingHost(Worlds.make(31, 2, [7], horizon=48))
    record = take_local(host, 0)
    weights = np.zeros((1, 1, len(STATE_SUPPORT)))
    weights[0, 0, _STATE_INDEX[(APPROACH, 1, 0, SHARED)]] = 1.
    quick = paired_values(record, weights, [[1.]], STATE_SUPPORT, [7],
                          seed=13, phase=4, particles=2, mode='JOINT')
    np.testing.assert_array_equal(quick['opportunity_tick'], [[1, 1]])
    np.testing.assert_array_equal(quick['near_end'], [[16, 16]])
    slow = paired_values(record, weights, [[0.]], STATE_SUPPORT, [7],
                         seed=13, phase=4, particles=2, mode='JOINT')
    np.testing.assert_array_equal(slow['opportunity_tick'], [[16, 16]])
    np.testing.assert_array_equal(slow['near_end'], [[32, 32]])


def test_planner_samples_joint_conditional_law_and_persistent_shared_theta(monkeypatch):
    from experiments.candidates.finite_model_decision_value.b01 import planning
    host = CrossingHost(Worlds.make(15, 2, [3], horizon=48))
    record = take_local(host, 0)
    belief = JointPhysicalBelief(record, [.0, 1.0], [[.5, .5]])
    belief.weights.fill(0)
    low = _STATE_INDEX[(APPROACH, 1, 0, SHARED)]
    high = _STATE_INDEX[(APPROACH, 7, 0, SHARED)]
    belief.weights[0, 0, low] = .5
    belief.weights[0, 1, high] = .5
    args = (record, belief.weights, belief.theta_values, STATE_SUPPORT, [3])
    original_model_host = planning.model_host
    inspected = []
    def inspect_model(record, payloads, advances, jobs):
        # In this independently specified joint law, distance1 requires theta0
        # and distance7 requires theta1. Inspect the real simulated process,
        # without using candidate-reported root_theta as a correctness oracle.
        expected = np.broadcast_to((payloads[..., 1].reshape(-1, 1, 1) == 7), advances.shape)
        np.testing.assert_array_equal(advances, expected)
        modeled = original_model_host(record, payloads, advances, jobs)
        np.testing.assert_array_equal(modeled.worlds.advances, np.concatenate((expected, expected)))
        inspected.append(True)
        return modeled
    monkeypatch.setattr(planning, "model_host", inspect_model)
    u = paired_values(*args, seed=4, phase=8, particles=16, mode='JOINT')
    assert inspected == [True]
    monkeypatch.setattr(planning, "model_host", original_model_host)
    p = paired_values(*args, seed=4, phase=8, particles=16, mode='POSTERIOR_MEAN')
    np.testing.assert_array_equal(u['root_state_index'], p['root_state_index'])
    assert set(u['root_theta'][0]) == {0., 1.}
    np.testing.assert_array_equal(u['root_theta'][0], np.where(u['root_state_index'][0] == low, 0., 1.))
    np.testing.assert_array_equal(p['root_theta'], .5)
    # Neither the copied record nor the model estimate can read a later host
    # mutation of hidden peer truth or actual exogenous futures.
    host.stage[:, 1] = CROSSING
    host.distance[:, 1] = 0
    host.worlds.advances[:] = ~host.worlds.advances
    host.worlds.jobs[:] = 7
    u_after = paired_values(*args, seed=4, phase=8, particles=16, mode='JOINT')
    np.testing.assert_array_equal(u_after['sample_delta'], u['sample_delta'])
    np.testing.assert_array_equal(u_after['root_theta'], u['root_theta'])
