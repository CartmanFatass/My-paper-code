"""Exact finite-grid checks using synthetic local distributions only."""

import itertools
import math
import random
from fractions import Fraction

import numpy as np
import pytest

from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.sampling import (
    M, decode, make_bundle, overlap_count, pair_expectations, partition,
)


def local_p(modal, mass, tail):
    p = np.zeros(27, dtype=np.float64)
    p[modal] = mass
    for action, probability in tail.items():
        p[action] = probability
    return p


def independent_grid_counts(p, bits):
    """Reference bin counts from scalar sums and rational ceil arithmetic."""
    grid = 1 << bits
    modal = min(range(27), key=lambda action: (-p[action], action))
    departure = Fraction.from_float(1.0 - float(p[modal])) * grid
    b = math.ceil(departure)
    tail_actions = [action for action in range(27) if action != modal]
    total = sum(float(p[action]) for action in tail_actions)
    boundaries = []
    cdf = 0.0
    for action in tail_actions:
        if total:
            cdf += float(p[action]) / total
        boundaries.append(min(grid, math.ceil(Fraction.from_float(cdf) * grid)))
    boundaries[-1] = grid
    counts = [0] * 27
    counts[modal] = (grid - b) * grid
    previous = 0
    for action, boundary in zip(tail_actions, boundaries):
        counts[action] = b * (boundary - previous)
        previous = boundary
    return modal, b, boundaries, counts


@pytest.mark.parametrize('bits', [2, 4])
@pytest.mark.parametrize('p', [local_p(13, .5, {2: .3125, 25: .1875}),
                              local_p(8, .45, {0: .325, 26: .225}),
                              local_p(14, .5, {21: .5}),
                              local_p(26, 1., {})])
def test_exhaustive_departure_tail_outcomes_preserve_each_agent_marginal(bits, p):
    grid = 1 << bits
    original = p.copy()
    modal, b, thresholds, expected_counts = independent_grid_counts(p, bits)
    for rank, law in itertools.product(range(5), ('I', 'A', 'B')):
        counts = np.zeros(27, dtype=np.int64)
        departures = 0
        for departure, tail in itertools.product(range(grid), repeat=2):
            result = decode(p, law=law, rank=rank, public=departure,
                            private_depart=departure, private_tail=tail, grid_bits=bits)
            counts[result['action_index']] += 1
            departures += result['requested_departure']
        assert counts.tolist() == expected_counts
        assert departures == b * grid
        assert result['modal'] == modal
        assert result['departure_threshold'] == b
        assert result['tail_thresholds'].tolist() == thresholds
        assert result['tail_actions'].dtype == np.int64
        assert result['tail_thresholds'].dtype == np.uint64
        assert result['effective_probabilities'].dtype == np.float64
        assert np.array_equal(result['effective_probabilities'], counts / (grid * grid))
    assert np.array_equal(p, original)


@pytest.mark.parametrize('bits', [1, 2, 3, 4])
def test_every_two_interval_overlap_matches_independent_integer_events(bits):
    grid = 1 << bits
    event = {(rank, b): {k for k in range(grid) if (k + rank * grid // 5) % grid < b}
             for rank in range(5) for b in range(grid + 1)}
    for rank_i, rank_j, b_i, b_j in itertools.product(range(5), range(5),
                                                    range(grid + 1), range(grid + 1)):
        expected = len(event[rank_i, b_i] & event[rank_j, b_j])
        assert overlap_count(b_i, b_j, rank_i, rank_j, grid_bits=bits) == expected


@pytest.mark.parametrize('thresholds', [[5, 2, 13, 7, 0], [16, 16, 16, 16, 16],
                                      [0, 0, 0, 0, 0], [1, 4, 8, 12, 15]])
def test_pair_expectations_unequal_overlapping_departures_by_exhaustion(thresholds):
    grid = 16
    expected_pairs = {}
    for law in ('A', 'B'):
        departure_counts = []
        pairs = []
        for k in range(grid):
            count = sum((((k + rank * grid // 5) % grid) if law == 'A' else k) < b
                        for rank, b in enumerate(thresholds))
            departure_counts.append(count)
            pairs.append(math.comb(count, 2))
        assert sum(departure_counts) / grid == sum(thresholds) / grid
        expected_pairs[law] = sum(pairs) / grid
    # Independent private integers: count each pair over its full Cartesian grid.
    independent_pairs = 0
    for i, j in itertools.combinations(range(5), 2):
        independent_pairs += sum(ki < thresholds[i] and kj < thresholds[j]
                                 for ki, kj in itertools.product(range(grid), repeat=2))
    expected_pairs['I'] = independent_pairs / grid ** 2
    result = pair_expectations(np.asarray(thresholds, dtype=np.uint64), grid_bits=4)
    assert result == dict(expected_departures=sum(thresholds) / grid,
                          pairs_I=expected_pairs['I'], pairs_A=expected_pairs['A'],
                          pairs_B=expected_pairs['B'])
    if thresholds == [5, 2, 13, 7, 0]:
        assert result['pairs_A'] > 0  # Staggering does not imply exclusivity for unequal q.


def test_production_q_grid_disjointness_and_large_python_integer_products():
    assert M == 1 << 53
    q = np.full(27, .1 / 26, dtype=np.float64)
    q[9] = .9
    result = partition(q)
    b = result['departure_threshold']
    assert b == math.ceil(Fraction.from_float(1 - float(q[9])) * M)
    assert b > 1 << 49
    for i, j in itertools.combinations(range(5), 2):
        assert overlap_count(b, b, i, j) == 0
    expectations = pair_expectations([np.uint64(b)] * 5)
    assert expectations == dict(expected_departures=5 * b / M,
                                pairs_I=10 * b * b / (M * M), pairs_A=0., pairs_B=10 * b / M)
    # The near-1/5 boundary cannot be promoted to a universal finite-grid rule.
    boundary_b = math.ceil(M * (1 - float(np.nextafter(.8, 0.0))))
    assert overlap_count(boundary_b, boundary_b, 0, 1) > 0


def test_half_open_tail_bins_endpoint_and_lowest_modal_tie():
    p = local_p(13, .5, {2: .3125, 25: .1875})
    result = partition(p, grid_bits=4)
    assert result['tail_thresholds'][-1] == 16
    assert np.all(np.diff(result['tail_thresholds'].astype(np.int64)) >= 0)
    for tail, action in ((0, 2), (9, 2), (10, 25), (15, 25)):
        assert decode(p, law='I', rank=4, public=15, private_depart=0,
                      private_tail=tail, grid_bits=4)['action_index'] == action
    for integer, departed in ((7, True), (8, False), (15, False)):
        assert decode(p, law='B', rank=0, public=integer, private_depart=0,
                      private_tail=0, grid_bits=4)['requested_departure'] is departed
    tied = partition(np.full(27, 1 / 27))
    assert tied['modal'] == 0
    assert tied['tail_actions'].tolist() == list(range(1, 27))
    deterministic = partition(local_p(26, 1., {}))
    assert deterministic['q'] == 0 and deterministic['departure_threshold'] == 0
    assert deterministic['tail_thresholds'].tolist() == [0] * 25 + [M]
    assert deterministic['effective_probabilities'][26] == 1


def test_tail_normalizes_own_mass_without_silently_tuning_modal_mass():
    p = local_p(13, .5, {2: .3125, 25: .1875 + 5e-13})
    result = partition(p, grid_bits=4)
    assert result['q'] == .5 and result['departure_threshold'] == 8
    assert result['tail_thresholds'][2] == math.ceil(16 * p[2] / (p[2] + p[25]))
    assert result['effective_probabilities'][13] == .5
    # A normalized CDF can overshoot one before trailing zero bins. Endpoint
    # saturation must leave monotone thresholds, without mutating the p input.
    rng = np.random.Generator(np.random.PCG64(72))
    overshooting = None
    for _ in range(100):
        tail = rng.random(20)
        tail = .2 * tail / tail.sum()
        candidate = local_p(26, .8, dict(enumerate(tail)))
        normalized_tail = candidate[:26] / candidate[:26].sum()
        if np.cumsum(normalized_tail)[19] > 1:
            overshooting = candidate
            break
    assert overshooting is not None
    original = overshooting.copy()
    result = partition(overshooting)
    thresholds = [int(t) for t in result['tail_thresholds']]
    assert thresholds == sorted(thresholds) and thresholds[-1] == M
    assert thresholds[19:] == [M] * 7
    assert np.array_equal(overshooting, original)


def test_bundle_exact_address_streams_pairing_separation_and_rng_isolation(tmp_path):
    numpy_state = np.random.get_state()
    python_state = random.getstate()
    first = make_bundle(29346000, 0)
    paired = make_bundle(29346000, 0)
    assert set(first) == {'public', 'private_depart', 'private_tail'}
    for name, array in first.items():
        assert array.shape == ((64,) if name == 'public' else (64, 5))
        assert array.dtype == np.uint64 and np.all(array < M)
        assert np.array_equal(array, paired[name])
    # For a power-of-two range, uint64 PCG raw >> 11 independently reconstructs
    # the generator's [0,2**53) uniform integer mapping.
    public = np.random.PCG64(np.random.SeedSequence([29346091, 29346000, 0]))
    assert np.array_equal(first['public'], public.random_raw(64) >> np.uint64(11))
    for name, root in (('private_depart', 29346092), ('private_tail', 29346093)):
        for agent in range(5):
            bitgen = np.random.PCG64(np.random.SeedSequence([root, 29346000, 0, agent]))
            assert np.array_equal(first[name][:, agent], bitgen.random_raw(64) >> np.uint64(11))
        assert all(not np.array_equal(first[name][:, i], first[name][:, j])
                   for i, j in itertools.combinations(range(5), 2))
    assert not np.array_equal(first['private_depart'], first['private_tail'])
    for other in (make_bundle(29346000, 1), make_bundle(29346001, 0)):
        assert all(not np.array_equal(array, other[name]) for name, array in first.items())
    short = make_bundle(29346000, 0, horizon=8)
    assert all(np.array_equal(short[name], array[:2]) for name, array in first.items())
    current_numpy = np.random.get_state()
    assert current_numpy[0] == numpy_state[0]
    assert np.array_equal(current_numpy[1], numpy_state[1])
    assert current_numpy[2:] == numpy_state[2:]
    assert random.getstate() == python_state
    path = tmp_path / 'paired_bundle.npz'
    np.savez(path, **first)
    with np.load(path, allow_pickle=False) as saved:
        assert all(np.array_equal(saved[name], array) for name, array in first.items())


def test_repeated_local_input_uses_fresh_entries_and_matched_private_tails():
    bundle = make_bundle(29346000, 0)
    p = local_p(13, .5, {2: .3125, 25: .1875})
    actions = []
    for clock in range(64):
        current = dict(rank=0, public=bundle['public'][clock],
                       private_depart=bundle['private_depart'][clock, 0],
                       private_tail=bundle['private_tail'][clock, 0])
        decoded = [decode(p, law=law, **current) for law in ('I', 'A', 'B')]
        departed = [row['action_index'] for row in decoded if row['requested_departure']]
        assert len(set(departed)) <= 1  # The same current tail is used by every law.
        assert decoded[1]['departure_integer'] == decoded[2]['departure_integer']
        actions.append(decoded[0]['action_index'])
    assert len(set(int(k) for k in bundle['private_depart'][:, 0])) == 64
    assert len(set(actions)) > 1


def test_tail_cdf_guard_rejects_material_or_decreasing_corruption(monkeypatch):
    p = local_p(13, .5, {2: .3125, 25: .1875})
    original = np.cumsum

    def overshoot(*args, **kwargs):
        cdf = original(*args, **kwargs)
        cdf[-2:] = 1 + 1e-10
        return cdf

    monkeypatch.setattr(np, 'cumsum', overshoot)
    with pytest.raises(ValueError, match='CDF'):
        partition(p)

    def decreasing(*args, **kwargs):
        cdf = original(*args, **kwargs)
        cdf[3] = cdf[2] / 2
        return cdf

    monkeypatch.setattr(np, 'cumsum', decreasing)
    with pytest.raises(ValueError, match='CDF'):
        partition(p)


def test_positive_q_with_zero_tail_is_rejected_even_within_sum_tolerance():
    with pytest.raises(ValueError, match='tail mass'):
        partition(local_p(0, 1 - 5e-13, {}))


@pytest.mark.parametrize('bad', [np.zeros(27), np.ones(26), np.full(27, float('nan')),
                                np.full(27, float('inf')), np.full(27, -1 / 27),
                                np.full(27, 1 / 27 + 1e-10), np.eye(1, 27)[0] * 1.0000000000001,
                                np.full(27, 1 / 27 + 0j)])
def test_invalid_probabilities_fail(bad):
    with pytest.raises(ValueError):
        partition(bad)


@pytest.mark.parametrize('field,value', [('law', 'S'), ('rank', -1), ('rank', 5),
                                       ('public', -1), ('public', M),
                                       ('private_depart', M), ('private_tail', M),
                                       ('rank', True), ('public', .5), ('grid_bits', 54),
                                       ('grid_bits', 0)])
def test_decode_integer_domains_and_law_are_validated(field, value):
    options = dict(law='I', rank=0, public=0, private_depart=0, private_tail=0)
    options[field] = value
    with pytest.raises(ValueError):
        decode(local_p(0, 1., {}), **options)


def test_pair_and_bundle_invalid_ranges():
    for thresholds in ([0] * 4, [0, 0, 0, 0, M + 1], [0, 0, 0, 0, .5]):
        with pytest.raises(ValueError):
            pair_expectations(thresholds)
    with pytest.raises(ValueError):
        overlap_count(-1, 0, 0, 1)
    with pytest.raises(ValueError):
        overlap_count(0, 0, 0, 5)
    for kwargs in (dict(horizon=255), dict(horizon=0), dict(public_root=29346092)):
        with pytest.raises(ValueError):
            make_bundle(29346000, 0, **kwargs)
    with pytest.raises(ValueError):
        make_bundle(29346000, -1)
