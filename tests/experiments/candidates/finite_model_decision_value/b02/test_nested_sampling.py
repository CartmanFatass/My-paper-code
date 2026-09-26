"""Actual 32/256 RNG prefixes and endpoint credit on independent correctness inputs."""

import numpy as np
import pytest

from experiments.candidates.finite_model_decision_value.b01 import planning
from experiments.candidates.finite_model_decision_value.b01.belief import (
    STATE_SUPPORT, _STATE_INDEX, take_local,
)
from experiments.candidates.finite_model_decision_value.b01.host import (
    APPROACH, SHARED, CrossingHost, Worlds,
)


def root_fixture():
    ids = (19, 7)
    host = CrossingHost(Worlds.make(441833, 61, ids, horizon=96))
    record = take_local(host, 0)
    # An independently specified associated state/parameter law also tests
    # conditional-theta sampling, beyond the factorized initial experiment root.
    weights = np.zeros((2, 4, len(STATE_SUPPORT)))
    for row in range(2):
        for component, distance in enumerate((1, 3, 5, 7)):
            weights[row, component, _STATE_INDEX[(APPROACH, distance, 0, SHARED)]] = (
                (.1, .2, .3, .4) if row == 0 else (.4, .3, .2, .1))[component]
    return ids, record, weights, np.array([.35, .55, .75, .95])


def streams(record, ids, particles):
    state, theta, process, jobs = planning.independent_model_worlds(
        record, ids, 442073, 62, particles)
    return state, theta, process.reshape(len(ids), particles, 96, 2), jobs.reshape(
        len(ids), particles, 96, 2)


def test_actual_numpy_stream_prefixes_reorder_split_and_selected_roots():
    ids, record, _, _ = root_fixture()
    low, high = streams(record, ids, 32), streams(record, ids, 256)
    for a, b in zip(low, high):
        np.testing.assert_array_equal(a, b[:, :32])
    reverse = streams(planning.select_record(record, [1, 0]), ids[::-1], 256)
    selected = streams(planning.select_record(record, [1]), [ids[1]], 256)
    split = [streams(planning.select_record(record, [i]), [ids[i]], 256) for i in range(2)]
    for kind, b in enumerate(high):
        np.testing.assert_array_equal(reverse[kind], b[::-1])
        np.testing.assert_array_equal(selected[kind], b[1:2])
        np.testing.assert_array_equal(np.concatenate([s[kind] for s in split]), b)


@pytest.mark.parametrize("mode", ["POSTERIOR_MEAN", "JOINT"])
def test_particle_outcomes_and_credit_prefixes_survive_budget_and_batch_changes(mode):
    ids, record, weights, thetas = root_fixture()

    def evaluate(indices, particles):
        return planning.paired_values(
            planning.select_record(record, indices), weights[indices], thetas,
            STATE_SUPPORT, [ids[i] for i in indices], seed=442073, phase=62,
            particles=particles, mode=mode)

    low, high = evaluate([0, 1], 32), evaluate([0, 1], 256)
    reversed_roots, selected_root = evaluate([1, 0], 256), evaluate([1], 256)
    particle_fields = ("root_state_index", "root_theta", "near_hold_samples",
                       "near_send_samples", "sample_delta", "near_end",
                       "opportunity_tick", "opportunity_kind")
    for field in particle_fields:
        np.testing.assert_array_equal(low[field], high[field][:, :32])
        np.testing.assert_array_equal(reversed_roots[field], high[field][::-1])
        np.testing.assert_array_equal(selected_root[field], high[field][1:2])
    # The joint law assigns each peer distance to exactly one parameter.
    if mode == "JOINT":
        distances = STATE_SUPPORT[high["root_state_index"]][..., 1]
        expected = np.choose((distances - 1) // 2, thetas)
    else:
        expected = np.broadcast_to(np.array([.75, .55])[:, None], (2, 256))
    np.testing.assert_allclose(high["root_theta"], expected, rtol=0, atol=1e-15)


def test_extra_slow_particle_extends_padding_without_extending_first_32_credit(monkeypatch):
    ids = (11,)
    record = take_local(CrossingHost(Worlds.make(441837, 61, ids, horizon=96)), 0)
    weights = np.zeros((1, 2, len(STATE_SUPPORT)))
    weights[0, :, _STATE_INDEX[(APPROACH, 1, 0, SHARED)]] = .5
    original = planning.independent_model_worlds

    def force_late_slow_particle(record, ids, seed, phase, particles):
        state, theta, process, jobs = original(record, ids, seed, phase, particles)
        theta.fill(.75)  # law1: reach the gate on the next tick, commitment ends16
        if particles > 32:
            theta[:, -1] = .25  # law0: wait for boundary16, commitment ends32
        return state, theta, process, jobs

    monkeypatch.setattr(planning, "independent_model_worlds", force_late_slow_particle)
    results = [planning.paired_values(
        record, weights, [0., 1.], STATE_SUPPORT, ids, seed=442077, phase=62,
        particles=m, mode="JOINT") for m in (32, 256)]
    low, high = results
    assert (low["end"], high["end"]) == (16, 32)
    assert high["near_end"][0, -1] == 32
    np.testing.assert_array_equal(high["near_end"][:, :32], 16)
    for field in ("near_hold_samples", "near_send_samples", "sample_delta", "near_end"):
        np.testing.assert_array_equal(high[field][:, :32], low[field])
