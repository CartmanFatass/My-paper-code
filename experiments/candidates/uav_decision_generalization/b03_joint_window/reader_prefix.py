"""Reuse only SHA-certified completed checks from the one failed B03 reader.

The original failure stays immutable. Changed movement arithmetic is rerun on
every reused raw command; model/physics/reward checks keep their original source
identity and paid counts. This module never advances an environment or model.
"""
import json
from pathlib import Path
import numpy as np

from . import contract as c, evidence as e
from .independent import checked_file, load_arrays, motion, same

PREFIX = 'experiments/candidates/uav_decision_generalization/b03_joint_window/'
ALLOWED_CHANGES = {PREFIX + name for name in ('independent.py', 'run.py', 'reader_prefix.py')}


def source_delta(old, new):
    return {key: {'before': old.get(key), 'after': new.get(key)}
            for key in old.keys() | new.keys() if old.get(key) != new.get(key)}


def validate_prefix(locator, context, prior):
    required = {'schema', 'root', 'config_sha256', 'summary_sha256', 'exit_sha256',
                'checks', 'source_changes'}
    if set(locator) != required or locator['schema'] != 1:
        raise ValueError('exact completed-reader prefix locator required')
    root = Path(locator['root'])
    if not root.is_absolute() or root.resolve() != root:
        raise ValueError('canonical external prefix root')
    config = e.bound_json(root / 'config.json', locator['config_sha256'])
    summary = e.bound_json(root / 'summary.json', locator['summary_sha256'])
    terminal = e.bound_json(root / 'process-exit.json', locator['exit_sha256'])
    old = context['worker_config']['source_sha256']
    delta = source_delta(old, context['source_sha256'])
    if set(delta) != ALLOWED_CHANGES or delta != locator['source_changes']:
        raise ValueError('only the published reader copy/prefix/entry delta is allowed')
    if config['source_sha256'] != old or config['mode'] != 'reader' or config['contract'] != context['worker_config']['contract']:
        raise ValueError('prefix reader must bind the original worker source and contract')
    if config['worker_input']['sha256'] != context['config']['worker_input']['sha256']:
        raise ValueError('prefix canonical worker input mismatch')
    if summary['launch_sha'] != config['launch_sha'] or summary['status'] != 'FAILED' or terminal['exit_code'] != 1:
        raise ValueError('original failed reader identity and terminal witness')
    if summary['error']['type'] != 'AssertionError' or summary['error']['message'] != 'dtype-preserving unit-ball clip: maximum absolute error 2.220446049250313e-16':
        raise ValueError('only the recorded movement arithmetic failure is covered')
    if (summary['training_rollouts_checked'], summary['frozen_checked']) != (135, 167):
        raise ValueError('exact135/167 completed prefix required')
    if summary['inflight'] != {'kind': 'frozen', 'programme': 'O', 'world': 109220001, 'phase': 'main'}:
        raise ValueError('fixed first-unchecked mission')
    cost = summary['cost']
    for key in cost['prior']['prior_counts'].keys() | cost['counts'].keys():
        if prior['prior_counts'].get(key, 0) < cost['prior']['prior_counts'].get(key, 0) + cost['counts'].get(key, 0):
            raise ValueError('prior ledger omits original failed-reader cost: ' + key)
    if prior['prior_cpu_seconds'] < cost['resources']['cumulative_cpu_seconds']:
        raise ValueError('prior ledger omits failed-reader CPU')
    manifest = context['manifest']
    train_rows = sorted(manifest['training'], key=lambda row: (c.ARMS.index(row['arm']), row['rollout']))
    expected = {
        'training': [f"checks/training/{row['arm']}_{row['rollout']:02}.json" for row in train_rows],
        'frozen': [f"checks/frozen/{row['programme']}_{row['world']}.json" for row in manifest['frozen'][:167]],
    }
    if set(locator['checks']) != set(expected):
        raise ValueError('complete check groups required')
    values = {}
    for kind, names in expected.items():
        identities = locator['checks'][kind]
        if [item['path'] for item in identities] != names:
            raise ValueError('ordered unique completed check roster: ' + kind)
        values[kind] = [json.loads(checked_file(root, item).read_bytes()) for item in identities]
    training = {(row['arm'], int(row['rollout'])): row for row in values['training']}
    frozen = {(row['programme'], int(row['world'])): row for row in values['frozen']}
    if len(training) != 135 or len(frozen) != 167:
        raise ValueError('duplicate completed check keys')
    return {'training': training, 'frozen': frozen, 'counts': cost['counts'],
            'identity': {'root': str(root), 'config_sha256': locator['config_sha256'],
                         'summary_sha256': locator['summary_sha256'],
                         'source_sha256': old, 'checks': locator['checks']}}


def recheck_movement(raw, meter):
    commands, following, events = motion(raw['positions'][..., :-1, :, :], raw['raw_actions'])
    same(raw['executed_actions'], commands, 'prefix copied-vector exact clip')
    same(raw['positions'][..., 1:, :, :], following, 'prefix exact successor motion')
    same(raw['action_clip_events'], events, 'prefix exact native clip-event count')
    meter.add('reader_prefix_movement_recheck_uav_ticks', raw['raw_actions'].size // 3)


def bound_check(prefix, row, worker_root, kind, key, meter):
    result = prefix[kind][key]
    if any(result[name] != row[name] for name in ('raw', 'metadata')):
        raise AssertionError('reused check must reference identical worker evidence')
    checked_file(worker_root, row['metadata'])
    raw = load_arrays(worker_root, row['raw'])
    recheck_movement(raw, meter)
    return result


def reuse_training(prefix, row, worker_root, meter):
    key = (row['arm'], int(row['rollout']))
    checked = bound_check(prefix, row, worker_root, 'training', key, meter)
    worlds = [c.training_world(lane, key[1] - 1) for lane in range(16)]
    same(checked['worlds'], worlds, 'reused complete training addresses')
    if [item['world'] for item in checked['lanes']] != worlds:
        raise AssertionError('reused16-lane identity')
    lanes = checked['lanes']
    scalar = [name for name, value in lanes[0]['metrics'].items() if isinstance(value, (int, float))]
    return {'arm': key[0], 'rollout': key[1],
            'means': {name: float(np.mean([x['metrics'][name] for x in lanes])) for name in scalar},
            'W_by_lane': [x['metrics']['W'] for x in lanes], 'losses': checked['losses'],
            'parameter_motion': checked['parameter_motion'], 'optimizer_total': checked['optimizer_total']}


def reuse_frozen(prefix, row, worker_root, meter):
    result = bound_check(prefix, row, worker_root, 'frozen', (row['programme'], int(row['world'])), meter)
    if result['phase'] != row['phase']:
        raise AssertionError('reused frozen phase')
    return result
