"""Exact source/input/roster and whole-study counter bindings."""
import ast
import hashlib
import json
import math
from pathlib import Path

from experiments.candidates.uav_decision_generalization.b03_joint_window import evidence as e
from . import contract as c


def source_manifest(root):
    root = Path(root)
    pending = list((root / 'experiments/candidates/uav_decision_generalization/b05_request_schedule').glob('*.py'))
    seen = {}
    while pending:
        path = pending.pop()
        if path in seen or not path.is_file():
            continue
        seen[path] = e.hash_file(path)
        package = list(path.relative_to(root).parts[:-1])
        for node in ast.walk(ast.parse(path.read_text())):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = '.'.join(package[:len(package) - node.level + 1]) if node.level else ''
                module = '.'.join(value for value in (base, node.module or '') if value)
                names = [module] + [module + '.' + alias.name for alias in node.names]
            for name in names:
                stem = root / Path(*name.split('.'))
                for candidate in (stem.with_suffix('.py'), stem / '__init__.py'):
                    if candidate.is_file():
                        pending.append(candidate)
                        for parent in candidate.relative_to(root).parents:
                            pending.append(root / parent / '__init__.py')
    return {str(path.relative_to(root)): digest for path, digest in sorted(seen.items())}


def source_identity(sources):
    return hashlib.sha256(json.dumps(sources, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def expected_roster():
    rows = [(world, f'train/fit{fit}') for fit, worlds in enumerate(c.TRAIN_WORLDS) for world in worlds]
    labels = ['G', 'R', 'L0', 'L1', 'L2']
    for index, world in enumerate(c.MAIN_WORLDS):
        rows.extend((world, 'main/' + label) for label in labels[index % 5:] + labels[:index % 5])
    names = ['G', 'R', 'initial', 'final']
    for fit, world in enumerate(c.AUDIT_WORLDS):
        rows.extend((world, f'audit{fit}/' + name) for name in names[fit % 4:] + names[:fit % 4])
    return rows


def validate_roster(records):
    if [(row['world'], row['label']) for row in records] != expected_roster():
        raise ValueError('complete unique ordered fixed B05 roster differs')
    if any(row['status'] != 'COMPLETE' or row['completed_native_steps'] != c.HORIZON for row in records):
        raise ValueError('a complete worker record is missing')


def study_context(study, sources):
    if (set(study) != {'schema', 'contract', 'source_sha256'} or study['schema'] != 1
            or study['contract'] != c.frozen_contract() or study['source_sha256'] != sources):
        raise ValueError('exact fixed study/source bytes differ')
    return {'source_sha256': sources, 'source_identity': source_identity(sources)}


def worker_context(locator, config):
    if set(locator) != {'schema', 'root', 'config_sha256', 'summary_sha256', 'manifest_sha256'} or locator['schema'] != 1:
        raise ValueError('bound complete worker locator required')
    root = Path(locator['root'])
    if not root.is_absolute() or root.resolve() != root:
        raise ValueError('canonical absolute worker root required')
    values = {name: e.bound_json(root / (name + '.json'), locator[name + '_sha256'])
              for name in ('config', 'summary', 'manifest')}
    old, summary, manifest = values['config'], values['summary'], values['manifest']
    if (summary['status'] != 'COMPLETE' or old['mode'] != 'worker'
            or summary['object'] != 'B05_request_schedule'
            or summary['launch_sha'] != old['launch_sha']):
        raise ValueError('complete matching B05 worker required')
    for key in ('contract', 'source_sha256', 'source_identity'):
        if old[key] != config[key]:
            raise ValueError('worker/reader source or contract differs: ' + key)
    if old['study_input']['sha256'] != config['study_input']['sha256']:
        raise ValueError('worker/reader exact study input differs')
    validate_roster(manifest['records'])
    validate_worker_counts(summary)
    return {'worker_root': root, 'worker_config': old, 'worker_summary': summary,
            'manifest': manifest,
            **{name + '_identity': e.identity(root / (name + '.json')) for name in values}}


def bind_prior(prior, worker=None, *, mode='worker'):
    if prior.get('schema') != 1 or prior.get('object') != 'B05_request_schedule':
        raise ValueError('B05 whole-study prior cost required')
    if any(type(prior.get(name)) not in (int, float) or not math.isfinite(prior[name]) or prior[name] < 0
           for name in ('cumulative_cpu_seconds', 'aggregate_operation_wall_seconds')):
        raise ValueError('nonnegative measured cumulative cost required')
    if worker is not None:
        cost = worker['cost']
        if any(prior[name] < cost[name] for name in ('cumulative_cpu_seconds', 'aggregate_operation_wall_seconds')):
            raise ValueError('reader prior omits completed worker cost')
        if prior.get('worker_launch_sha') != worker['launch_sha']:
            raise ValueError('reader prior worker identity differs')
    elif mode == 'worker' and prior.get('worker_launch_sha') is not None:
        raise ValueError('worker prior cannot include a prior worker/resume')


def validate_worker_counts(summary):
    counts = summary['cost']['counts']
    endpoints = summary['endpoint_counts']
    aggregate = {}
    for endpoint in endpoints:
        for key, value in endpoint['counts'].items():
            if type(value) is not int or value < 0:
                raise ValueError('invalid endpoint exposure count')
            aggregate[key] = aggregate.get(key, 0) + value
    exact = {'actual_constructors': 1708, 'actual_native_steps': 2049600,
             'actual_native_attempts': 2049600}
    if summary['missions'] != 1708 or any(counts.get(key) != value for key, value in exact.items()):
        raise ValueError('fixed actual native count differs')
    for key, expected in (('transitions', 92160), ('updates', 91392),
                          ('backwards', 91392), ('optimizer_steps', 91392),
                          ('target_copies', 357), ('initial_target_copies', 3),
                          ('collection_rows', 368640), ('update_current_rows', 11698176),
                          ('offline_audit_rows', 720)):
        if aggregate.get(key) != expected:
            raise ValueError('fixed learning/audit count differs: ' + key)
    if aggregate.get('update_failures') != 0:
        raise ValueError('complete worker includes a failed update')
    # R trace g0 is the same timed top-level query counted by Endpoint.
    # Exact base-query overlap is recorded per trace for final accounting below.
    overlap_ticks = counts.get('R_base_g_reserved_candidate_ticks', 0)
    g_ticks = aggregate.get('g_reserved_candidate_ticks', 0) + counts.get('R_g_reserved_candidate_ticks', 0) - overlap_ticks
    neural = sum(aggregate.get(role + '_attempted_rows', 0) for role in
                 ('collection', 'update_current', 'update_next_online', 'update_next_target'))
    neural += aggregate.get('frozen_nn_attempted_rows', 0) + aggregate.get('offline_audit_attempted_rows', 0)
    if (counts.get('R_native_attempts', 0) > 4424000 or g_ticks > 292844160
            or neural > 70582176 or aggregate.get('g_attempts', 0) > 102480):
        raise ValueError('selected full work exposure ceiling exceeded')
    return {'endpoint_counts': aggregate, 'worker_neural_attempted_rows': neural,
            'worker_g_reserved_candidate_ticks': g_ticks}
