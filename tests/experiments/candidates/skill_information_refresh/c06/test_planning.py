"""Small semantic fixtures, not a new scientific policy comparison."""

from copy import deepcopy

import numpy as np
import pytest

from experiments.candidates.skill_information_refresh.c01.host import CrossingHost, DONE, Worlds
from experiments.candidates.skill_information_refresh.c06.belief import take_local
from experiments.candidates.skill_information_refresh.c06.planning import (
    commitment_end, independent_model_worlds, model_host, paired_values,
)


def host_at(t):
    host = CrossingHost(Worlds.make(61, 2, [0], 48))
    while host.t < t:
        host.step(np.array([host.t % 3 == 0]))
    return host


@pytest.mark.parametrize("t", [0, 5, 8, 11, 14, 23, 31])
def test_hydrated_model_replays_original_physics_and_caches(t):
    host = host_at(t)
    record = take_local(host, t % 2)
    # Privileged fixture state is supplied only to prove hydration/transition
    # correctness. Production paired_values samples its own finite belief.
    peer = np.repeat(host.payloads()[:, 1 - record.agent, None, :], 2, axis=1)
    model = model_host(record, peer,
        np.repeat(host.worlds.advances, 2, axis=0), np.repeat(host.worlds.jobs, 2, axis=0))
    references = [deepcopy(host), deepcopy(host)]
    for step in range(min(8, host.horizon - t)):
        requests = np.array([False, False, True, True]) if step == 0 else model.view().own[:, 0] != DONE
        actual_reward = model.step(requests)
        for branch, reference in enumerate(references):
            wanted = np.array([bool(branch)]) if step == 0 else reference.view().own[:, 0] != DONE
            expected_reward = reference.step(wanted)
            np.testing.assert_array_equal(actual_reward[branch * 2:(branch + 1) * 2], np.repeat(expected_reward, 2))
            for name in ("stage", "distance", "cross_left", "route", "cache", "cache_time",
                         "last_sent", "last_sent_time", "spent", "pending", "pending_payload", "pending_time"):
                # Unused pending storage is immaterial after delivery. Payload
                # and time are tested only while a real packet is pending.
                if name in ("pending_payload", "pending_time"):
                    continue
                np.testing.assert_array_equal(getattr(model, name)[branch * 2], getattr(reference, name)[0])


def test_short_target_assigns_boundary_delivery_to_new_commitment():
    assert commitment_end(11, 0, 96) == 24
    assert commitment_end(14, 1, 96) == 16
    assert commitment_end(15, 1, 96) == 32
    assert commitment_end(95, 0, 96) == 96


def test_model_noise_does_not_read_host_future_or_hidden_peer():
    host = host_at(0)
    record = take_local(host, 0)
    first = independent_model_worlds(record, [71], 8001, 9, 4)
    host.worlds.advances.fill(False)
    host.worlds.jobs.fill(7)
    host.distance[:, 1] = 0
    second = independent_model_worlds(take_local(host, 0), [71], 8001, 9, 4)
    for a, b in zip(first, second):
        np.testing.assert_array_equal(a, b)
    other = independent_model_worlds(record, [71], 8002, 9, 4)
    assert any(not np.array_equal(a, b) for a, b in zip(first, other))


def test_paired_values_count_complete_branch_work_and_reject_masked_calls():
    host = host_at(0)
    record = take_local(host, 0)
    states = np.array([[0, distance, 0, 0] for distance in range(1, 8)])
    weights = np.full((1, 7), 1 / 7)
    short = paired_values(record, weights, states, [0], seed=9, phase=1, particles=4, mode="SHORT")
    long = paired_values(record, weights, states, [0], seed=9, phase=1, particles=4, mode="LONG")
    assert short["model_branch_transitions"] == 2 * 4 * 16
    assert long["model_branch_transitions"] == 2 * 4 * 32
    assert short["model_initialization_worlds"] == 8
    assert np.isfinite(short["delta"]).all() and np.isfinite(long["se"]).all()
    host.step(np.array([True]))
    host.step(np.array([False]))
    with pytest.raises(ValueError, match="optional"):
        paired_values(take_local(host, 0), weights, states, [0], seed=9, phase=1, particles=4, mode="LONG")
