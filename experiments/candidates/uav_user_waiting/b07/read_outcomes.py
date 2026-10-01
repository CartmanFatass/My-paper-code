"""Independent native LRS recurrence, complete gaps and paired reductions."""

import numpy as np

from experiments.candidates.uav_user_waiting.b05 import protocol as fair
from experiments.candidates.uav_user_waiting.b05.reader import (
    reference_outcome, _schema_row, _describe, compare_tree,
)
from . import protocol as p
from experiments.candidates.uav_user_waiting.b06.read_model import reference_grants, consume_grants


def verify_lrs(raw, full, compact, collector, counts, discrepancies):
    steps = int(raw['completed_steps'])
    assert full['complete'] and steps == len(raw['sinr'])
    values = raw['sinr']
    assert values.dtype == np.float64 and values.shape == (steps, p.N, p.U)
    assigned = np.zeros_like(values, dtype=bool)
    own = np.full((p.N, p.U), -1, np.int64)
    for tick in range(steps):
        active = ((int(raw['mask'][tick]) >> np.arange(p.N)) & 1).astype(bool)
        assert np.isfinite(values[tick, active]).all() and np.isneginf(values[tick, ~active]).all()
        counts['native_lrs_fleet_attempts'] += 1
        grants = reference_grants(values[tick], own, paid=counts)
        assigned[tick] = consume_grants(own, tick, grants)
        counts['native_lrs_fleet_completed'] += 1
    eligibility = values >= 3.
    reference = reference_outcome(values, eligibility, assigned, raw['connections'], counts)
    for name, expected in (('grants', assigned), ('contacts', reference['contacts']),
                           ('ages', reference['ages']), ('served', reference['served'])):
        np.testing.assert_array_equal(raw['lrs_' + name], expected)
    for name in ('quality', 'reward'):
        assert np.max(np.abs(raw['lrs_' + name] - reference[name]), initial=0.) <= p.ATOL
    assert np.array_equal(reference['served'], raw['served'])
    assert np.all(reference['quality'] <= raw['quality'] + p.ATOL)
    assert np.all(reference['reward'] <= raw['reward'] + p.ATOL)
    inherited = {key: collector[key] for key in fair.INHERITED_FIELDS if key in collector}
    expected = _schema_row(reference, p.PROGRAM, 'LRS', collector['seed'], inherited, steps)
    compare_tree({key: full[key] for key in expected}, expected, 'full LRS', discrepancies)
    slim = {key: value for key, value in expected.items() if key != 'per_user'}
    slim['per_user_vectors'] = {key: [row[key] for row in expected['per_user']] for key in fair.VECTOR_FIELDS}
    compare_tree({key: compact[key] for key in slim}, slim, 'compact LRS', discrepancies)
    return expected


def reference_physical(raw, baseline):
    for key, left, right in (
        ('reset', raw['positions'][0], baseline['positions'][0]),
        ('map', raw['map_packet'], baseline['map_packet']),
        ('sites', raw['true_sites'], baseline['true_sites']),
        ('obs', raw['observations'][0], baseline['observations'][0]),
    ):
        assert np.array_equal(left, right), key
    commands, masks = [], []
    for tick in range(len(raw['commands'])):
        if not np.array_equal(raw['commands'][tick], baseline['commands'][tick]):
            commands.append(tick)
        if int(raw['mask'][tick]) != int(baseline['mask'][tick]):
            masks.append(tick)
    positions = [tick for tick, (a, b) in enumerate(zip(raw['positions'], baseline['positions']))
                 if not np.array_equal(a, b)]
    first = min(commands + masks) if commands or masks else None
    if first is not None:
        assert all(np.array_equal(raw['positions'][tick], baseline['positions'][tick]) for tick in range(first + 1))
        assert np.array_equal(raw['observations'][:first], baseline['observations'][:first])
    return dict(first_executed_command_or_mask_tick=first,
                first_position_tick=min(positions) if positions else None,
                command_difference_ticks=len(commands), mask_difference_ticks=len(masks),
                position_difference_ticks=len(positions), activated=first is not None,
                scope='first divergence while histories coincide; later differences are whole-trajectory comparisons')


def reference_paired(rows, baselines, seeds=p.SEEDS):
    packages = (p.PROGRAM + ':LRS',) + p.REFERENCES
    combined = list(rows) + list(baselines.values())
    by = {(row['package'], row['seed']): row for row in combined}
    assert len(by) == len(combined)
    assert set(by) == {(package, seed) for package in packages for seed in seeds}
    names = fair.OUTCOME_METRICS + fair.INHERITED_METRICS
    values, levels, contrasts = {}, {}, {}
    for package in packages:
        values[package], levels[package] = {}, {}
        for name in names:
            vector = [float((by[package, seed]['inherited'] if name in fair.INHERITED_METRICS
                             else by[package, seed])[name]) for seed in seeds]
            values[package][name] = np.asarray(vector)
            levels[package][name] = _describe(vector)
    for package in p.REFERENCES:
        label = packages[0] + '-' + package
        contrasts[label] = {name: _describe(values[packages[0]][name] - values[package][name]) for name in names}
    primary = contrasts['C2:LRS-S_F:LRS']['max_unserved_gap']
    draws = np.random.RandomState(p.BOOTSTRAP_SEED).randint(len(seeds), size=(p.BOOTSTRAP_RESAMPLES, len(seeds)))
    boot = {}
    for label, result in contrasts.items():
        boot[label] = {}
        for name in ('max_unserved_gap', 'F_user', 'mean_served'):
            sampled_means = np.asarray(result[name]['values'])[draws].sum(axis=1) / len(seeds)
            boot[label][name] = dict(percentile95=np.percentile(sampled_means, [2.5, 97.5]).tolist())
    return dict(world_seeds=list(seeds), levels=levels, contrasts=contrasts,
                primary=dict(contrast='C2:LRS-S_F:LRS', metric='max_unserved_gap', mean_difference=primary['mean'],
                             favorable_worlds=sum(value < 0 for value in primary['values']),
                             equal_worlds=sum(value == 0 for value in primary['values']),
                             adverse_worlds=sum(value > 0 for value in primary['values'])),
                bootstrap=dict(seed=p.BOOTSTRAP_SEED, resamples=p.BOOTSTRAP_RESAMPLES, contrasts=boot),
                timing_scope='different historical runtime/context costs are not a matched speed comparison',
                scope='adaptively reused development worlds; descriptive paired uncertainty; no automatic adoption/confirmation')
