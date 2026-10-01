"""Native LRS outcomes from the C2, already collected physical trajectory."""

import time

import numpy as np

from experiments.candidates.uav_user_waiting.b05.allocation import LeastRecentlyServed
from experiments.candidates.uav_user_waiting.b05.study import outcome
from . import protocol as p


def replay_lrs(raw, collector_row, counts):
    steps = int(raw['completed_steps'])
    values = np.asarray(raw['sinr'][:steps])
    states = [LeastRecentlyServed() for _ in range(p.N)]
    assignment = np.zeros((steps, p.N, p.U), bool)
    contacts, ages = np.zeros((steps, p.U), bool), np.zeros((steps, p.U), np.int64)
    native, eligible = np.zeros((steps, 3), np.float64), values >= 3.
    changed = np.zeros((steps, p.N), bool)
    current_age = np.zeros(p.U, np.int64)
    p.require(values.dtype == np.float64 and values.shape == (steps, p.N, p.U), 'native SINR shape/dtype')
    p.require(np.all(eligible.sum(axis=1) <= 1), 'non-disjoint native eligibility')
    before_wall, before_cpu = time.perf_counter(), time.process_time()
    for tick in range(steps):
        active = (int(raw['mask'][tick]) >> np.arange(p.N)) & 1
        p.require(np.isfinite(values[tick, active.astype(bool)]).all() and
                  np.isneginf(values[tick, ~active.astype(bool)]).all(), 'native mask/SINR mismatch')
        counts['native_lrs_fleet_ticks'] += 1
        for member, state in enumerate(states):
            ids = np.flatnonzero(eligible[tick, member])
            counts['native_lrs_row_selections'] += 1
            chosen = state.grant(ids, values[tick, member, ids], tick)
            assignment[tick, member, chosen] = True
        grants = assignment[tick]
        p.require(np.array_equal(grants.sum(axis=1), np.minimum(10, eligible[tick].sum(axis=1))),
                  'LRS work conservation failed')
        contacts[tick] = grants.any(axis=0)
        current_age = np.where(contacts[tick], 0, current_age + 1)
        ages[tick] = current_age
        served = int(grants.sum())
        quality = float(np.clip((values[tick][grants] - 3.) / 30., 0., 1.).sum() / max(served, 1))
        native[tick] = served, quality, .7 * served / p.U + .3 * quality
        p.require(served == int(raw['served'][tick]), 'LRS changed same-path service count')
        p.require(native[tick, 1] <= raw['quality'][tick] + p.ATOL and
                  native[tick, 2] <= raw['reward'][tick] + p.ATOL, 'LRS exceeded greedy quality ceiling')
        changed[tick] = (grants != raw['connections'][tick]).any(axis=1)
        counts['native_lrs_user_age_updates'] += p.U
    timing = dict(wall_seconds=time.perf_counter() - before_wall, cpu_seconds=time.process_time() - before_cpu,
                  scope='offline per-tick LRS grants/native/age arrays, excluding gap reduction; not integrated allocation latency')
    original = raw['connections'][:steps].any(axis=1)
    row = outcome(contacts, ages, native, eligible, changed, original,
                  dict(collector_row, arm=p.PROGRAM), 'LRS', steps == len(raw['commands']))
    if 'positions' in raw:
        heights = raw['positions'][1:steps + 1, :, 2]
        row['height_exposure'] = dict(mean_height_m=float(heights.mean()), min_height_m=float(heights.min()),
                                      max_height_m=float(heights.max()), lower_boundary_uav_ticks=int((heights == 50).sum()),
                                      upper_boundary_uav_ticks=int((heights == 150).sum()), scope='postmove physical altitude')
    arrays = dict(lrs_grants=assignment, lrs_contacts=contacts, lrs_ages=ages,
                  lrs_served=native[:, 0].astype(np.int64), lrs_quality=native[:, 1], lrs_reward=native[:, 2])
    return row, arrays, timing


def compact_row(row):
    result = {key: value for key, value in row.items() if key != 'per_user'}
    from experiments.candidates.uav_user_waiting.b05.protocol import VECTOR_FIELDS
    result['per_user_vectors'] = {key: [user[key] for user in row['per_user']] for key in VECTOR_FIELDS}
    return result


def physical_comparison(raw, baseline):
    """Saved-input comparison only; no old-policy call at any new state."""
    for name, left, right in (
        ('initial_positions', raw['positions'][0], baseline['positions'][0]),
        ('true_sites', raw['true_sites'], baseline['true_sites']),
        ('map_packet', raw['map_packet'], baseline['map_packet']),
        ('reset_observation', raw['observations'][0], baseline['observations'][0]),
    ):
        p.require(np.array_equal(left, right), 'old-world binding differs: ' + name)
    commands = (raw['commands'] != baseline['commands']).any(axis=(1, 2))
    masks = raw['mask'] != baseline['mask']
    positions = (raw['positions'] != baseline['positions']).any(axis=(1, 2))
    decision_ticks = np.flatnonzero(commands | masks)
    position_ticks = np.flatnonzero(positions)
    first = int(decision_ticks[0]) if len(decision_ticks) else None
    if first is not None:
        p.require(np.array_equal(raw['positions'][:first + 1], baseline['positions'][:first + 1]),
                  'position diverged before any executed command/mask divergence')
        p.require(np.array_equal(raw['observations'][:first], baseline['observations'][:first]),
                  'observations diverged before executed physical decisions')
    return dict(first_executed_command_or_mask_tick=first,
                first_position_tick=int(position_ticks[0]) if len(position_ticks) else None,
                command_difference_ticks=int(commands.sum()), mask_difference_ticks=int(masks.sum()),
                position_difference_ticks=int(positions.sum()), activated=first is not None,
                scope='first divergence while histories coincide; later differences are whole-trajectory comparisons')
