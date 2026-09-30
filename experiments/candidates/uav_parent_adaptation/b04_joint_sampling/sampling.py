"""The selected B04 finite-grid decoder; no model or environment dependencies.

Only cumulative tail roundoff is saturated at the probability endpoint: a CDF
overshoot of at most 64 float64 epsilons is allowed, then clipped to one before
ceil conversion. Larger overshoots or decreasing CDFs are errors. This handles
roundoff before trailing zero bins consistently with the forced terminal M; it
does not change or renormalize the supplied modal probability.
"""

import math
import operator

import numpy as np


M = 1 << 53


def _integer(value, name, *, lower=0, upper=None):
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f'{name} must be an integer')
    try:
        result = operator.index(value)
    except TypeError as error:
        raise ValueError(f'{name} must be an integer') from error
    if result < lower or (upper is not None and result > upper):
        raise ValueError(f'{name} is outside its integer range')
    return result


def _grid(grid_bits):
    return 1 << _integer(grid_bits, 'grid_bits', lower=1, upper=53)


def make_bundle(world, tape, *, horizon=256, public_root=29346091,
                departure_root=29346092, tail_root=29346093):
    """Evaluator-only tapes. Decoder arguments contain only the current entries."""
    world = _integer(world, 'world')
    tape = _integer(tape, 'tape')
    horizon = _integer(horizon, 'horizon', lower=4)
    if horizon % 4:
        raise ValueError('horizon must be divisible by four')
    roots = [_integer(root, 'root') for root in (public_root, departure_root, tail_root)]
    if len(set(roots)) != 3:
        raise ValueError('public, departure and tail roots must be distinct')
    clocks = horizon // 4

    def stream(root, agent=None):
        address = [root, world, tape] + ([] if agent is None else [agent])
        rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(address)))
        return rng.integers(0, M, size=clocks, dtype=np.uint64)

    return {'public': stream(roots[0]),
            'private_depart': np.column_stack([stream(roots[1], agent) for agent in range(5)]),
            'private_tail': np.column_stack([stream(roots[2], agent) for agent in range(5)])}


def partition(probabilities, *, grid_bits=53):
    grid = _grid(grid_bits)
    supplied = np.asarray(probabilities)
    if np.iscomplexobj(supplied):
        raise ValueError('probabilities must be real')
    p = np.asarray(supplied, dtype=np.float64)
    if (p.shape != (27,) or not np.isfinite(p).all() or (p < 0).any()
            or (p > 1).any() or abs(float(p.sum(dtype=np.float64)) - 1) > 1e-12):
        raise ValueError('expected 27 finite nonnegative probabilities summing to one within 1e-12')
    modal = int(np.argmax(p))  # NumPy resolves ties at the lowest index.
    q = 1.0 - float(p[modal])
    departure_threshold = min(grid, max(0, math.ceil(grid * q)))
    tail_actions = np.delete(np.arange(27, dtype=np.int64), modal)
    tail_thresholds = np.zeros(26, dtype=np.uint64)
    if q != 0:
        tail = p[tail_actions]
        tail_sum = float(tail.sum(dtype=np.float64))
        if tail_sum <= 0:
            raise ValueError('positive departure probability requires positive tail mass')
        cdf = np.cumsum(tail / tail_sum, dtype=np.float64)
        slack = 64 * np.finfo(np.float64).eps
        if (not np.isfinite(cdf).all() or (np.diff(cdf) < 0).any()
                or (cdf < 0).any() or (cdf > 1 + slack).any()):
            raise ValueError('invalid normalized tail CDF')
        cdf = np.minimum(cdf, 1.0)
        tail_thresholds[:] = [math.ceil(grid * float(boundary)) for boundary in cdf]
    tail_thresholds[-1] = grid
    # Check using Python integers: uint64 differences would hide an underflow.
    boundaries = [0] + [int(boundary) for boundary in tail_thresholds]
    widths = [right - left for left, right in zip(boundaries, boundaries[1:])]
    if any(width < 0 for width in widths):
        raise ValueError('tail thresholds must be monotone')
    effective = np.zeros(27, dtype=np.float64)
    departure_probability = departure_threshold / grid
    effective[modal] = 1.0 - departure_probability
    effective[tail_actions] = departure_probability * (np.asarray(widths, dtype=np.float64) / grid)
    return {'modal': modal, 'q': q, 'departure_threshold': departure_threshold,
            'tail_actions': tail_actions, 'tail_thresholds': tail_thresholds,
            'effective_probabilities': effective}


def decode(p, *, law, rank, public, private_depart, private_tail, grid_bits=53):
    grid = _grid(grid_bits)
    if law not in ('I', 'A', 'B'):
        raise ValueError('law must be I, A or B')
    rank = _integer(rank, 'rank', upper=4)
    public = _integer(public, 'public', upper=grid - 1)
    private_depart = _integer(private_depart, 'private_depart', upper=grid - 1)
    private_tail = _integer(private_tail, 'private_tail', upper=grid - 1)
    result = partition(p, grid_bits=grid_bits)
    if law == 'I':
        departure_integer = private_depart
    elif law == 'A':
        departure_integer = (public + rank * grid // 5) % grid
    else:
        departure_integer = public
    requested_departure = departure_integer < result['departure_threshold']
    if requested_departure:
        tail_index = int(np.searchsorted(result['tail_thresholds'], np.uint64(private_tail),
                                         side='right'))
        action_index = int(result['tail_actions'][tail_index])
    else:
        action_index = result['modal']
    result.update(departure_integer=departure_integer,
                  requested_departure=requested_departure, action_index=action_index)
    return result


def _intervals(threshold, rank, grid):
    """Public K with (K + floor(rank*M/5)) % M < threshold."""
    if threshold == 0:
        return []
    start = (-(rank * grid // 5)) % grid
    end = start + threshold
    if end <= grid:
        return [(start, end)]
    return [(start, grid), (0, end - grid)]


def overlap_count(b_i, b_j, rank_i, rank_j, *, grid_bits=53):
    grid = _grid(grid_bits)
    b_i = _integer(b_i, 'b_i', upper=grid)
    b_j = _integer(b_j, 'b_j', upper=grid)
    rank_i = _integer(rank_i, 'rank_i', upper=4)
    rank_j = _integer(rank_j, 'rank_j', upper=4)
    return sum(max(0, min(right_i, right_j) - max(left_i, left_j))
               for left_i, right_i in _intervals(b_i, rank_i, grid)
               for left_j, right_j in _intervals(b_j, rank_j, grid))


def pair_expectations(thresholds, *, grid_bits=53):
    grid = _grid(grid_bits)
    values = list(thresholds)
    if len(values) != 5:
        raise ValueError('expected five thresholds in rank order 0..4')
    values = [_integer(value, 'threshold', upper=grid) for value in values]
    pairs = [(i, j) for i in range(5) for j in range(i + 1, 5)]
    return {'expected_departures': sum(values) / grid,
            'pairs_I': sum(values[i] * values[j] for i, j in pairs) / (grid * grid),
            'pairs_A': sum(overlap_count(values[i], values[j], i, j, grid_bits=grid_bits)
                           for i, j in pairs) / grid,
            'pairs_B': sum(min(values[i], values[j]) for i, j in pairs) / grid}
