"""Published source, canonical in-place teacher and single-chain identities."""
import ast
import hashlib
import json
import math
from pathlib import Path

from experiments.candidates.uav_decision_generalization.b03_joint_window import evidence as e
from . import contract as c


def source_manifest(root):
    root = Path(root)
    pending = list((root / 'experiments/candidates/uav_decision_generalization/b06_request_amortization').glob('*.py'))
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


def study_context(study, sources):
    if (set(study) != {'schema', 'contract', 'source_sha256', 'teacher'} or study['schema'] != 1
            or study['contract'] != c.frozen_contract() or study['source_sha256'] != sources):
        raise ValueError('exact selected B06 study/source input differs')
    teacher = study['teacher']
    if set(teacher) != {'root', 'reader_summary', 'identities'} or teacher['identities'] != c.TEACHER_IDENTITIES:
        raise ValueError('original teacher and reader anchors required')
    root, reading = Path(teacher['root']), Path(teacher['reader_summary'])
    expected = Path('/home/fires/hmasd-wsl/runs/uav_decision_generalization')
    if (root != expected / 'b05_request_a01' or reading != expected / 'b05_request_read_a02/summary.json'
            or root.resolve() != root or reading.resolve() != reading):
        raise ValueError('selected original teacher evidence must remain in place')
    # No old physical/model reconstruction. The acquisition/reader subsequently
    # bind every selected mission/rollout identity and reconstruct the labels.
    original = e.bound_json(root / 'config.json', c.TEACHER_IDENTITIES['config'])
    for path, digest in sources.items():
        previous = original['source_sha256'].get(path)
        if previous is not None and previous != digest:
            raise ValueError('a frozen inherited B05 dependency changed: ' + path)
    return {'source_sha256': sources, 'source_identity': source_identity(sources),
            'teacher_root': root, 'teacher_reader_summary': reading}


def validate_roster(records):
    if [(record['world'], record['label']) for record in records] != c.expected_roster():
        raise ValueError('fixed complete unique B06 seven-arm roster differs')
    if any(record['status'] != 'COMPLETE' or record['completed_native_steps'] != c.HORIZON
           for record in records):
        raise ValueError('incomplete B06 mission')


def worker_context(locator, config):
    if set(locator) != {'schema', 'root', 'config_sha256', 'summary_sha256', 'manifest_sha256'} or locator['schema'] != 1:
        raise ValueError('one bound complete B06 worker locator required')
    root = Path(locator['root'])
    expected = Path('/home/fires/hmasd-wsl/runs/uav_decision_generalization') / c.WORKER_TAG
    if root != expected or root.resolve() != root:
        raise ValueError('canonical original B06 worker root required')
    values = {name: e.bound_json(root / (name + '.json'), locator[name + '_sha256'])
              for name in ('config', 'summary', 'manifest')}
    old, summary, manifest = values['config'], values['summary'], values['manifest']
    if (summary['status'] != 'COMPLETE' or old['mode'] != 'worker' or summary['object'] != c.OBJECT
            or summary['launch_sha'] != old['launch_sha']):
        raise ValueError('complete original B06 worker required; no failure retry')
    for key in ('contract', 'source_sha256', 'source_identity', 'teacher'):
        if old[key] != config[key]:
            raise ValueError('worker/reader selected inputs differ: ' + key)
    if old['study_input']['sha256'] != config['study_input']['sha256']:
        raise ValueError('worker/reader study input bytes differ')
    validate_roster(manifest['records'])
    validate_worker_counts(summary)
    return {'worker_root': root, 'worker_config': old, 'worker_summary': summary,
            'manifest': manifest,
            **{name + '_identity': e.identity(root / (name + '.json')) for name in values}}


def bind_prior(prior, worker=None, *, mode='worker'):
    if prior.get('schema') != 1 or prior.get('object') != c.OBJECT:
        raise ValueError('B06 cumulative new-computation ledger required')
    for name in ('cumulative_cpu_seconds', 'aggregate_operation_wall_seconds', 'engineering_cpu_seconds'):
        if type(prior.get(name)) not in (int, float) or not math.isfinite(prior[name]) or prior[name] < 0:
            raise ValueError('invalid measured prior cost: ' + name)
    if prior['engineering_cpu_seconds'] > c.ENGINEERING_CPU_LIMIT_SECONDS:
        raise ValueError('selected pure-engineering price exceeded')
    if prior.get('unknown_support_is_zero') is not False:
        raise ValueError('unmetered support must remain nonzero/unknown')
    if worker is not None:
        cost = worker['cost']
        if (any(prior[name] < cost[name] for name in
                ('cumulative_cpu_seconds', 'aggregate_operation_wall_seconds'))
                or prior.get('worker_launch_sha') != worker['launch_sha']):
            raise ValueError('reader ledger omits its original complete worker')
    elif mode == 'worker' and prior.get('worker_launch_sha') is not None:
        raise ValueError('one worker only; no resumed or replacement fit purchase')


def validate_worker_counts(summary):
    counts, aggregate = summary['cost']['counts'], {}
    for endpoint in summary['endpoint_counts']:
        for key, value in endpoint['counts'].items():
            if type(value) is not int or value < 0:
                raise ValueError('invalid endpoint attempt/completion count')
            aggregate[key] = aggregate.get(key, 0) + value
    if summary['missions'] != 224:
        raise ValueError('B06 complete mission count differs')
    for key, exact in {'actual_constructor_attempts': 224, 'actual_constructors': 224,
                       'actual_native_attempts': 268800, 'actual_native_steps': 268800}.items():
        if counts.get(key) != exact:
            raise ValueError('B06 complete actual exposure differs: ' + key)
    acquisition = summary['acquisition_totals']
    for key, exact in {'constant_fits': 1, 'neural_fits': 3, 'updates': 6336,
                       'backwards': 6336, 'context_presentations': 403200,
                       'training_neural_rows': 1612800, 'bank_endpoint_neural_rows': 50400}.items():
        if acquisition.get(key) != exact:
            raise ValueError('B06 fixed acquisition exposure differs: ' + key)
    g_queries = aggregate.get('g_attempts', 0) + counts.get('R_g_attempts', 0) - counts.get('R_base_g_attempts', 0)
    g_ticks = (aggregate.get('g_reserved_candidate_ticks', 0) + counts.get('R_g_reserved_candidate_ticks', 0)
               - counts.get('R_base_g_reserved_candidate_ticks', 0))
    neural = acquisition['training_neural_rows'] + acquisition['bank_endpoint_neural_rows'] + aggregate.get('frozen_nn_attempted_rows', 0)
    if (aggregate.get('g_attempts', 0) > 13440 or g_queries > 271488 or g_ticks > 246912000
            or counts.get('R_native_attempts', 0) > 5201920 or neural > 1686240):
        raise ValueError('B06 complete worker exceeds selected scientific calls')
    return {'endpoint_counts': aggregate, 'worker_g_attempts': g_queries,
            'worker_g_reserved_candidate_ticks': g_ticks,
            'worker_neural_attempted_rows': neural}
