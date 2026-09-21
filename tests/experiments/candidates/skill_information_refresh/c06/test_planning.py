"""Small semantic fixtures, not a new scientific policy comparison."""

from copy import deepcopy

import numpy as np
import pytest

from experiments.candidates.skill_information_refresh.c01.host import (
    APPROACH, DONE, PERIODS, SHARED, CrossingHost, Worlds,
)
from experiments.candidates.skill_information_refresh.c06 import planning
from experiments.candidates.skill_information_refresh.c06.belief import LocalRecord, take_local
from experiments.candidates.skill_information_refresh.c06.planning import (
    independent_model_worlds, model_host, paired_values,
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
    near = paired_values(record, weights, states, [0], seed=9, phase=1,
        particles=4, mode="NEAR_COMMIT")
    long = paired_values(record, weights, states, [0], seed=9, phase=1, particles=4, mode="LONG")
    assert near["model_branch_transitions"] <= 2 * 4 * 32
    assert long["model_branch_transitions"] == 2 * 4 * 32
    assert near["model_initialization_worlds"] == 8
    assert np.isfinite(near["delta"]).all() and np.isfinite(long["se"]).all()
    assert near["near_end"].shape == long["near_end"].shape == (1, 4)
    assert "long_hold_samples" not in near
    assert long["long_hold_samples"].shape == (1, 4)
    host.step(np.array([True]))
    host.step(np.array([False]))
    with pytest.raises(ValueError, match="optional"):
        paired_values(take_local(host, 0), weights, states, [0], seed=9, phase=1, particles=4, mode="LONG")
    with pytest.raises(ValueError, match="unknown value horizon"):
        paired_values(record, weights, states, [0], seed=9, phase=1, particles=4, mode="SHORT")


def opportunity_record(t=2, horizon=48):
    return LocalRecord(
        t=t,
        horizon=horizon,
        agent=0,
        own=np.array([[DONE, 0, 0, PERIODS[0] - t % PERIODS[0], SHARED]], dtype=np.int16),
        last_sent=np.array([[APPROACH, 0, 0, 12, SHARED]], dtype=np.int16),
        last_sent_time=np.array([0]),
        peer_packet=np.zeros((1, 5), dtype=np.int16),
        peer_packet_time=np.array([-1]),
        available=np.array([True]),
    )


def fixed_two_particle_worlds(record, ids, seed, phase, particles):
    assert len(ids) == 1 and particles == 2
    uniforms = np.array([[.25, .75]])
    advances = np.zeros((2, record.horizon, 2), dtype=bool)
    jobs = np.ones((2, record.horizon, 2), dtype=np.int16)
    return uniforms, advances, jobs


def test_near_commit_finds_gate_then_future_route_with_particle_endpoints(monkeypatch):
    monkeypatch.setattr(planning, "independent_model_worlds", fixed_two_particle_worlds)
    record = opportunity_record()
    states = np.array([
        [APPROACH, 0, 0, SHARED],
        [DONE, 0, 0, SHARED],
    ], dtype=np.int16)
    weights = np.array([[.5, .5]])
    result = paired_values(record, weights, states, [7], seed=91, phase=20,
        particles=2, mode="NEAR_COMMIT", diagnostics=True)

    # Particle 0 is blocked/yielding at the root and first reaches the cache-sensitive
    # shared gate at t=3. Particle 1 is DONE until receiver 1's route boundary at t=16.
    assert result["opportunity_tick"].tolist() == [[3, 16]]
    assert result["opportunity_kind"].tolist() == [[2, 1]]
    assert result["near_end"].tolist() == [[16, 32]]
    assert result["end"] == 32
    assert result["model_branch_transitions"] == 2 * 2 * (32 - record.t)
    assert result["near_hold_samples"].shape == (1, 2)
    diagnostics = result["diagnostics"]
    assert diagnostics["sent"].shape == (1, 2, 2, 30)
    assert diagnostics["payloads"].shape == (1, 2, 2, 30, 2, 5)
    assert diagnostics["wait_ticks"].shape == (1, 2, 2, 30)
    assert diagnostics["bypass_jobs"].shape == (1, 2, 2, 30)
    assert diagnostics["sent"][0, 0, :, 0].tolist() == [False, False]
    assert diagnostics["sent"][0, 1, :, 0].tolist() == [True, True]


def test_route_boundary_is_detected_before_preopportunity_route_equality(monkeypatch):
    def boundary_worlds(record, ids, seed, phase, particles):
        advances = np.zeros((2, record.horizon, 2), dtype=bool)
        advances[:, 12, 0] = True
        return (np.array([[.5, .5]]), advances,
            np.ones((2, record.horizon, 2), dtype=np.int16))

    monkeypatch.setattr(planning, "independent_model_worlds", boundary_worlds)
    record = LocalRecord(
        t=12,
        horizon=48,
        agent=0,
        own=np.array([[APPROACH, 1, 0, 12, SHARED]], dtype=np.int16),
        last_sent=np.array([[DONE, 0, 0, 6, SHARED]], dtype=np.int16),
        last_sent_time=np.array([6]),
        peer_packet=np.zeros((1, 5), dtype=np.int16),
        peer_packet_time=np.array([-1]),
        available=np.array([True]),
    )
    states = np.array([[DONE, 0, 0, SHARED]], dtype=np.int16)
    result = paired_values(record, np.ones((1, 1)), states, [5], seed=3, phase=20,
        particles=2, mode="NEAR_COMMIT", diagnostics=True)
    assert result["opportunity_tick"].tolist() == [[16, 16]]
    assert result["opportunity_kind"].tolist() == [[1, 1]]
    assert result["near_end"].tolist() == [[32, 32]]
    boundary_offset = 16 - record.t
    payloads = result["diagnostics"]["payloads"]
    hold_route = payloads[0, 0, :, boundary_offset, 1, 4]
    send_route = payloads[0, 1, :, boundary_offset, 1, 4]
    assert np.any(hold_route != send_route)


def test_terminal_done_has_no_opportunity_before_horizon(monkeypatch):
    def terminal_worlds(record, ids, seed, phase, particles):
        return (np.array([[.5, .5]]),
            np.zeros((2, record.horizon, 2), dtype=bool),
            np.ones((2, record.horizon, 2), dtype=np.int16))

    monkeypatch.setattr(planning, "independent_model_worlds", terminal_worlds)
    record = opportunity_record(t=44)
    states = np.array([[DONE, 0, 0, SHARED]], dtype=np.int16)
    result = paired_values(record, np.ones((1, 1)), states, [9], seed=3, phase=21,
        particles=2, mode="NEAR_COMMIT")
    assert result["opportunity_tick"].tolist() == [[-1, -1]]
    assert result["opportunity_kind"].tolist() == [[0, 0]]
    assert result["near_end"].tolist() == [[48, 48]]
    assert result["model_branch_transitions"] == 2 * 2 * 4


def test_long_reuses_exact_near_prefix_samples_without_extra_rollouts(monkeypatch):
    monkeypatch.setattr(planning, "independent_model_worlds", fixed_two_particle_worlds)
    record = opportunity_record()
    states = np.array([
        [APPROACH, 0, 0, SHARED],
        [DONE, 0, 0, SHARED],
    ], dtype=np.int16)
    weights = np.array([[.5, .5]])
    near_counters, long_counters = {}, {}
    near = paired_values(record, weights, states, [11], seed=101, phase=20,
        particles=2, mode="NEAR_COMMIT", counters=near_counters, diagnostics=True)
    long = paired_values(record, weights, states, [11], seed=101, phase=20,
        particles=2, mode="LONG", counters=long_counters, diagnostics=True)

    for key in ("near_hold_samples", "near_send_samples", "near_end",
                "opportunity_tick", "opportunity_kind"):
        np.testing.assert_array_equal(near[key], long[key])
    assert long["long_hold_samples"].shape == long["long_send_samples"].shape == (1, 2)
    assert long["model_branch_transitions"] == 2 * 2 * 32
    assert near["model_branch_transitions"] == 2 * 2 * 30
    assert near_counters["model_branch_transitions"] == near["model_branch_transitions"]
    assert long_counters["model_branch_transitions"] == long["model_branch_transitions"]
    assert near_counters["model_initialization_worlds"] == 4
    assert long_counters["model_initialization_worlds"] == 4
    assert near_counters["model_root_decisions"] == long_counters["model_root_decisions"] == 1
    for key in ("sent", "payloads", "wait_ticks", "bypass_jobs"):
        near_values = near["diagnostics"][key]
        long_prefix = long["diagnostics"][key][:, :, :, :near_values.shape[3]]
        np.testing.assert_array_equal(near_values, long_prefix)
