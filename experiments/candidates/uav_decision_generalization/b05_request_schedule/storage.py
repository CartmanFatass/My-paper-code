"""Bounded trace arrays; interrupted calls never become completed evidence."""
from pathlib import Path

import numpy as np

from . import contract as c
from .task import PublicState

STATE_DTYPE = np.dtype([
    ('positions', '<f8', (6, 3)), ('connections', 'u1', (38,)),
    ('routes', 'i1', (6, 7)), ('route_lengths', 'u1', (6,)),
    ('uav_connections', 'u1', (5,)), ('bs_connections', 'u1', (1,)),
    ('ack', 'u1', (7,)), ('counts', '<u2', (4,)),
    ('progress', 'u1', (4,)), ('slots', 'u1', (6,)), ('tick', '<u2')])
G_DTYPE = np.dtype([
    ('positions', '<f8', (6, 3)), ('ack', 'u1', (7,)),
    ('counts', '<u2', (4,)), ('progress', 'u1', (4,)),
    ('slots', 'u1', (6,)), ('tick', '<u2'), ('costs', '<f8', (4,)),
    ('complete', 'u1')])
R_STATS = ('initial_attempts', 'initial_complete', 'clone_attempts', 'clones',
           'native_attempts', 'native_complete', 'g_attempts', 'g_complete',
           'g_reserved_candidate_ticks', 'g_complete_candidate_ticks',
           'tape_attempts', 'tape_draws', 'tape_uniforms', 'cohorts_complete', 'cohorts_reused')
R_SHAPES = {
    'states': ((16, 161), STATE_DTYPE),
    'initial': ((1,), STATE_DTYPE),
    'g': ((160,), G_DTYPE),
    'rows': ((16,), np.dtype('<i8')),
    'branch_action': ((16,), np.dtype('i1')),
    'branch_tape': ((16,), np.dtype('i1')),
    'branch_complete': ((16,), np.dtype('u1')),
    'branch_cost': ((16,), np.dtype('<f8')),
    'arrivals': ((16, 161, 4), np.dtype('u1')),
    'tick_cost': ((16, 160), np.dtype('<u2')),
    'g_links': ((16, 9), np.dtype('<i2')),
    'tape_times': ((4, 8), np.dtype('<i2')),
    'tapes': ((4, 8, 4), np.dtype('u1')),
    'tape_lengths': ((4,), np.dtype('u1')),
    'tape_complete': ((4,), np.dtype('u1')),
    'cohort_complete': ((4,), np.dtype('u1')),
    'cohort_reuse': ((4,), np.dtype('i1')),
    'cohort_costs': ((4, 4), np.dtype('<f8')),
    'cohort_branches': ((4, 4), np.dtype('i1')),
    'cohort_input_sha256': ((4, 32), np.dtype('u1')),
    'cohort_ready_ns': ((4,), np.dtype('<i8')),
    'stats': ((len(R_STATS),), np.dtype('<i8')),
    'native_events': ((len(c.NATIVE_EVENT_NAMES),), np.dtype('<i8')),
}


def bits(value):
    return np.packbits(np.asarray(value, dtype=bool).ravel(), bitorder='little')


def unbits(value, shape):
    return np.unpackbits(np.asarray(value, dtype=np.uint8), bitorder='little')[:int(np.prod(shape))].reshape(shape).astype(bool)


def write_npz(path, arrays):
    """Finite typed arrays, including structured records; no object/pickle."""
    path = Path(path)
    if path.exists():
        raise FileExistsError('no duplicate scientific trace')
    def check(value):
        value = np.asarray(value)
        if value.dtype.hasobject:
            raise ValueError('object trace array forbidden')
        if value.dtype.names:
            for field in value.dtype.names:
                check(value[field])
        elif value.dtype.kind in 'fc' and not np.isfinite(value).all():
            raise ValueError('nonfinite trace array')
    for value in arrays.values():
        check(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.partial.npz')
    np.savez_compressed(temporary, **arrays)
    temporary.replace(path)


def ack_of(snapshot):
    return np.any(snapshot['connections'] & (snapshot['route_lengths'] > 0)[:, None], axis=0)


def put_state(row, snapshot, counts, progress, slots, tick):
    row['positions'] = snapshot['positions']
    for key in ('connections', 'uav_connections', 'bs_connections'):
        row[key] = bits(snapshot[key])
    row['routes'] = snapshot['routes']
    row['route_lengths'] = snapshot['route_lengths']
    row['ack'] = bits(ack_of(snapshot))
    row['counts'], row['progress'], row['slots'], row['tick'] = counts, progress, slots, tick


def public_from_row(row, *, world, users, rates, pairs):
    return PublicState(world, int(row['tick']), users, rates, row['positions'],
                       unbits(row['ack'], (50,)), row['counts'], row['progress'],
                       row['slots'], pairs)


def put_g(row, state, costs=None):
    # Write the input before entry. The caller commits complete only after costs.
    row['positions'], row['ack'] = state.positions, bits(state.ack)
    row['counts'], row['progress'] = state.counts, state.progress
    row['slots'], row['tick'] = state.active_slots, state.tick
    if costs is not None:
        row['costs'] = costs
        row['complete'] = 1


class RolloutTrace:
    """Parent creates files; one child writes; parent reads after join/reap."""
    def __init__(self, directory, *, create=False):
        self.directory = Path(directory)
        if create:
            self.directory.mkdir(parents=True, exist_ok=False)
        self.arrays = {}
        for name, (shape, dtype) in R_SHAPES.items():
            value = np.memmap(self.directory / (name + '.bin'), dtype=dtype,
                              mode='w+' if create else 'r+', shape=shape)
            if create:
                value[:] = 0
                if name in ('g_links', 'branch_action', 'branch_tape', 'tape_times', 'cohort_reuse', 'cohort_branches'):
                    value[:] = -1
                value.flush()
            self.arrays[name] = value

    def add(self, name, amount=1):
        self.arrays['stats'][R_STATS.index(name)] += amount

    def count(self, name):
        return int(self.arrays['stats'][R_STATS.index(name)])

    def native_event(self, name, amount):
        self.arrays['native_events'][c.NATIVE_EVENT_NAMES.index(name)] += amount

    def g_values(self, state):
        from .ordinary import g_values
        index = self.count('g_attempts')
        if index >= len(self.arrays['g']):
            raise RuntimeError('bounded rollout G storage exceeded')
        put_g(self.arrays['g'][index], state)
        horizon = min(c.G_HORIZON, c.HORIZON - state.tick)
        self.add('g_attempts')
        self.add('g_reserved_candidate_ticks', 4 * horizon)
        result = g_values(state)
        put_g(self.arrays['g'][index], state, result.costs)
        self.add('g_complete_candidate_ticks', result.counters['candidate_ticks'])
        self.add('g_complete')
        return index, result.costs

    def close(self):
        for value in self.arrays.values():
            value.flush()
            value._mmap.close()
        self.arrays.clear()

    def collect(self, path):
        # No reader may race the child. The Process owner calls this after reap.
        arrays = {name: np.array(value, copy=True) for name, value in self.arrays.items()}
        write_npz(Path(path), arrays)
        self.close()
        for name in R_SHAPES:
            (self.directory / (name + '.bin')).unlink()
        self.directory.rmdir()
        return {name: int(arrays['stats'][i]) for i, name in enumerate(R_STATS)}
