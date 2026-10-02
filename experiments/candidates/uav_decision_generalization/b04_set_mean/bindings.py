"""Bindings checked before model construction; no checkpoint copy or new baseline queries."""
import ast
import json
from pathlib import Path
from experiments.candidates.uav_decision_generalization.b03_joint_window import evidence as e, independent as i, run as b03run
from . import contract as c


def source_manifest(root):
    root = Path(root)
    pending = [root / p for p in e.source_manifest(root)]
    pending += list((root / 'experiments/candidates/uav_decision_generalization/b04_set_mean').glob('*.py'))
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
                names = [x.name for x in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = '.'.join(package[:len(package) - node.level + 1]) if node.level else ''
                module = '.'.join(x for x in (base, node.module or '') if x)
                names = [module] + [module + '.' + x.name for x in node.names]
            for name in names:
                stem = root / Path(*name.split('.'))
                for candidate in (stem.with_suffix('.py'), stem / '__init__.py'):
                    if candidate.is_file():
                        pending.append(candidate)
                        for parent in candidate.relative_to(root).parents:
                            pending.append(root / parent / '__init__.py')
    return {str(p.relative_to(root)): digest for p, digest in sorted(seen.items())}


def validate_roster(rows, programmes=c.PROGRAMMES):
    actual = [(r['programme'], r['world'], r['phase']) for r in rows]
    if len(actual) != len(c.roster(programmes)) or set(actual) != set(c.roster(programmes)):
        raise ValueError('exact unique programme/world/phase roster required')
    if any(type(r['world']) != int for r in rows):
        raise ValueError('integer world addresses required')


def study_context(study, sources):
    if set(study) != {'schema', 'contract', 'source_sha256', 'ancestor', 'baseline_reading', 'baseline_checks'} or study['schema'] != 1:
        raise ValueError('explicit bound B04 study schema required')
    if study['contract'] != c.frozen_contract() or study['source_sha256'] != sources or study['ancestor'] != c.ANCESTOR:
        raise ValueError('fixed study/source/ancestor identity changed')
    reading_id = study['baseline_reading']
    if {k: reading_id[k] for k in ('path', 'sha256')} != c.READING:
        raise ValueError('paid final B03 reading identity')
    reading_root = Path(c.READING['path']).parent
    reading = json.loads(i.checked_file(reading_root, reading_id).read_bytes())
    if len(reading['source_sha256']) != 46 or any(sources.get(p) != sha for p, sha in reading['source_sha256'].items() if p not in c.EXCEPTIONS):
        raise ValueError('unchanged inherited B03 scientific source bytes required')
    ancestor = b03run.worker_context(study['ancestor'])
    for endpoint, identity in c.CHECKPOINTS.items():
        if ancestor['manifest']['checkpoints']['SET'][endpoint] != identity:
            raise ValueError('fixed SET checkpoint identity')
        i.checked_file(ancestor['worker_root'], identity)
    if any(reading['worker_' + name]['sha256'] != c.ANCESTOR[name + '_sha256'] for name in ('config', 'summary', 'manifest')):
        raise ValueError('paid reading belongs to canonical ancestor')
    checks = study['baseline_checks']
    validate_roster(checks, c.BASELINES)
    paid_rows = {(r['programme'], r['world'], r['phase']): r for r in reading['frozen_results']}
    baselines = []
    for row in checks:
        programme, world, phase = row['programme'], row['world'], row['phase']
        # Final B03 completion reused the original reader's bound finished
        # prefix. Preserve those paid checks at their actual canonical root.
        prefix = programme in ('SET-initial', 'SET-final') or (programme == 'O' and world == c.WORLDS[0] and phase == 'main')
        check_root = reading_root.with_name('b03_joint_window_read_a01') if prefix else reading_root
        expected_path = check_root / 'checks' / 'frozen' / f'{programme}_{world}.json'
        path = i.checked_file(check_root, row['identity'])
        if path != expected_path:
            raise ValueError('canonical paid check path')
        if prefix:
            reused = reading['reused_prefix']
            relative = str(path.relative_to(check_root))
            paid_identity = next((item for item in reused['checks']['frozen'] if item['path'] == relative), None)
            if reused['root'] != str(check_root) or paid_identity is None or any(row['identity'][k] != paid_identity[k] for k in ('bytes', 'sha256')):
                raise ValueError('final paid reading prefix check identity')
        result = json.loads(path.read_bytes())
        paid = paid_rows[programme, world, phase]
        if any(result[k] != paid[k] for k in ('programme', 'world', 'phase', 'raw', 'metadata')):
            raise ValueError('paid full check/reading lineage')
        compact = {k: v for k, v in result['metrics'].items() if k != 'user_details'}
        if compact != paid['metrics'] or len(result['metrics']['user_details']) != 50:
            raise ValueError('paid complete metric/user identity')
        baselines.append(result)
    return {'ancestor': ancestor, 'baseline_reading': reading, 'baseline_results': baselines,
            'baseline_reading_identity': reading_id}


def worker_context(locator, config):
    if set(locator) != {'schema', 'root', 'config_sha256', 'summary_sha256', 'manifest_sha256'} or locator['schema'] != 1:
        raise ValueError('complete bound B04 worker locator')
    root = Path(locator['root'])
    if not root.is_absolute() or root.resolve() != root:
        raise ValueError('canonical absolute worker root')
    values = {name: e.bound_json(root / (name + '.json'), locator[name + '_sha256']) for name in ('config', 'summary', 'manifest')}
    old = values['config']
    if old['mode'] != 'worker' or old['contract'] != c.frozen_contract() or values['summary']['status'] != 'COMPLETE':
        raise ValueError('complete fixed B04 worker required')
    for key in ('contract', 'source_sha256', 'ancestor', 'baseline_reading'):
        if old[key] != config[key]:
            raise ValueError('worker/reader exact source and study binding: ' + key)
    if old['study_input']['sha256'] != config['study_input']['sha256']:
        raise ValueError('worker/reader exact study input bytes')
    if values['summary']['launch_sha'] != old['launch_sha'] or values['manifest']['checkpoints'] != c.CHECKPOINTS:
        raise ValueError('worker launch/checkpoint identity')
    if any(values[name].get('object') != c.OBJECT or values[name].get('inference_mode') != c.MODE for name in ('summary', 'manifest')):
        raise ValueError('explicit B04 worker object/mean mode')
    validate_roster(values['manifest']['frozen'])
    return {'worker_root': root, 'worker_config': old, 'worker_summary': values['summary'], 'manifest': values['manifest'],
            **{name + '_identity': e.identity(root / (name + '.json')) for name in ('config', 'summary', 'manifest')}}


def check_counts(meter, mode, terminal=False):
    expected = c.WORKER_COUNTS if mode == 'worker' else c.READER_COUNTS
    for key, maximum in expected.items():
        value = meter.counts.get(key, 0)
        if value > maximum or terminal and value != maximum:
            raise AssertionError('fixed ' + mode + ' exposure: ' + key)
    if any(value for key, value in meter.counts.items() if key.startswith('optimizer_')):
        raise AssertionError('zero optimizer calls required')
    if mode == 'reader' and any(meter.counts.get(key, 0) for key in ('native_steps', 'native_step_attempts', 'frozen_model_steps')):
        raise AssertionError('reader performed worker effects')
    cost = meter.resources()
    if cost['cumulative_cpu_seconds'] > 7200 or cost['wall_seconds'] > 7200:
        raise RuntimeError('new-study CPU/operation wall watchdog exceeded')


def bind_ledger(prior, worker):
    cost = worker['cost']
    expected = dict(cost['prior']['prior_counts'])
    for key, value in cost['counts'].items():
        expected[key] = expected.get(key, 0) + value
    if prior['prior_counts'] != expected or prior['prior_cpu_seconds'] < cost['resources']['cumulative_cpu_seconds']:
        raise ValueError('reader ledger omits or changes worker/check cumulative cost')
    if worker.get('new_native_steps') != 33000 or worker.get('new_fits') != 0 or worker.get('optimizer_steps') != 0:
        raise ValueError('complete exact zero-update worker required')
    if any(cost['counts'].get(k, 0) != v for k, v in c.WORKER_COUNTS.items()):
        raise ValueError('worker complete counters')


def neural_rows(meter, terminal=False):
    """Count actual hooked actor/critic forwards, including the critic's work."""
    rows = {name: sum(item['leading_rows'] for address, item in meter.calls.items()
                      if address.endswith('|skill_discoverer.' + name)) for name in ('actor', 'critic')}
    if terminal and rows != {'actor': 198000, 'critic': 198000}:
        raise AssertionError('complete actual actor and critic forward rows')
    return rows
