"""Complete inherited physics/neural replay plus descriptive paid-reference joins."""
import gc
import json
from pathlib import Path
import numpy as np
from experiments.candidates.uav_decision_generalization.b03_joint_window import contract as b03, evidence as e, independent as i
from . import bindings as b, contract as c
from .worker import load_endpoint


def comparisons(results, baselines):
    b.validate_roster(results)
    b.validate_roster(baselines, c.BASELINES)
    rows = {(r['programme'], r['world']): r for r in results + baselines if r['phase'] == 'main'}
    fields = [key for key, value in results[0]['metrics'].items() if isinstance(value, (int, float))]
    programmes = (*c.PROGRAMMES, *c.BASELINES)
    arrays = {p: {key: np.asarray([rows[p, w]['metrics'][key] for w in c.WORLDS], dtype=float) for key in fields} for p in programmes}
    pairs = [(c.PROGRAMMES[1], c.PROGRAMMES[0])]
    pairs += [(p, q) for p in c.PROGRAMMES for q in c.BASELINES]
    contrasts = {}
    details = {}
    for left, right in pairs:
        name = left + ' minus ' + right
        contrasts[name] = {key: i.paired(arrays[left][key] - arrays[right][key]) for key in fields}
        # Keep matched individual and window tails, including qualified geometry
        # acquisition (q>=8), twenty-tick completion and censored user gaps.
        details[name] = []
        for world in c.WORLDS:
            a, z = rows[left, world]['metrics'], rows[right, world]['metrics']
            users_a, users_z = a['user_details'], z['user_details']
            if [u['user'] for u in users_a] != list(range(50)) or [u['user'] for u in users_z] != list(range(50)):
                raise AssertionError('full matched user roster')
            windows_a, windows_z = a['window_details'], z['window_details']
            if [v['window'] for v in windows_a] != list(range(4)) or [v['window'] for v in windows_z] != list(range(4)):
                raise AssertionError('full matched window roster')
            if any(x['cluster'] != y['cluster'] for x, y in zip(windows_a, windows_z)):
                raise AssertionError('matched scheduled clusters')
            details[name].append({'world': world, 'W_delta': a['W'] - z['W'],
                'windows': [{'window': x['window'], 'cluster': x['cluster'],
                             'completed_delta': int(x['completed']) - int(y['completed']),
                             'qualified_ticks_delta': x['qualified_ticks'] - y['qualified_ticks'],
                             'max_consecutive_qualified_ticks_delta': x['max_consecutive_qualified_ticks'] - y['max_consecutive_qualified_ticks'],
                             'max_active_users_delta': x['max_active_users'] - y['max_active_users']} for x, y in zip(windows_a, windows_z)],
                'users': [{'user': x['user'], **{key + '_delta': x[key] - y[key] for key in
                          ('served_ticks', 'longest_gap', 'leading_gap', 'trailing_gap')}} for x, y in zip(users_a, users_z)]})
    interaction = {key: i.paired((arrays[c.PROGRAMMES[1]][key] - arrays[c.PROGRAMMES[0]][key]) -
                                  (arrays['SET-final'][key] - arrays['SET-initial'][key])) for key in fields}
    sampled_gain = float((arrays['SET-final']['W'] - arrays['SET-initial']['W']).mean())
    if sampled_gain != .0625:
        raise AssertionError('paid sampled +.0625 W contrast changed')
    cases = {name: {'adverse_worlds': [row['world'] for row in sorted(detail, key=lambda r: (r['W_delta'], r['world'])) if row['W_delta'] < 0],
                    'lowest_worlds': [row['world'] for row in sorted(detail, key=lambda r: (r['W_delta'], r['world']))[:3]]}
             for name, detail in details.items()}
    return {'scope': '32 development-exposed paired worlds conditional on the initial/final endpoints of one original SET training instance; descriptive mode interaction, no causal entropy or training replication claim.',
            'worlds': list(c.WORLDS), 'levels': {p: {key: i.paired(a) for key, a in values.items()} for p, values in arrays.items()},
            'contrasts': contrasts, 'mode_interaction': interaction, 'sampled_W_gain': sampled_gain,
            'case_worlds': cases, 'matched_tails': details}


def run(root, out, args, context):
    out = Path(out)
    meter = context['meter']
    manifest = context['manifest']
    b.validate_roster(manifest['frozen'])
    if manifest.get('object') != c.OBJECT or manifest.get('inference_mode') != c.MODE:
        raise ValueError('mean manifest object/mode')
    results = []
    summary = {'schema': 1, 'object': c.OBJECT, 'status': 'STARTED', 'mode': 'reader', 'launch_sha': args.launch_sha,
               'new_native_steps': 0, 'new_fits': 0, 'optimizer_steps': 0, 'frozen_checked': 0, 'inflight': None}
    def publish():
        summary['cost'] = meter.report()
        summary['actual_neural_agent_rows'] = b.neural_rows(meter)
        e.write_json(out / 'summary.json', summary)
    publish()
    for programme in c.PROGRAMMES:
        b.check_counts(meter, 'reader')
        agent, payload = load_endpoint(context['ancestor'], c.ENDPOINTS[programme], out, programme, meter)
        try:
            selected = [r for r in manifest['frozen'] if r['programme'] == programme]
            for row in sorted(selected, key=lambda r: (r['phase'] != 'main', r['world'])):
                b.check_counts(meter, 'reader')
                summary['inflight'] = {k: row[k] for k in ('programme', 'world', 'phase')}
                publish()
                worker_root = context['worker_root']
                metadata = json.loads(i.checked_file(worker_root, row['metadata']).read_bytes())
                if any(metadata[k] != row[k] for k in ('programme', 'world', 'phase')):
                    raise ValueError('mean mission metadata roster')
                if metadata['object'] != 'UAV-JOINT-WINDOW-B03' or metadata.get('inference_mode') != c.MODE or 'terminal_rng' not in metadata:
                    raise ValueError('inherited raw task/explicit mean RNG binding')
                if metadata['source_sha256'] != context['source_sha256'] or metadata['worker_config_sha256'] != context['config_identity']['sha256'] or metadata['launch_sha'] != context['worker_config']['launch_sha']:
                    raise ValueError('exact mean episode source/config/launch binding')
                if metadata['checkpoint'] != c.CHECKPOINTS[c.ENDPOINTS[programme]] or metadata['state_digest'] != payload['state_digest'] or metadata['optimizer_steps'] != 0 or metadata['sampling_seed'] != row['world'] + 51:
                    raise ValueError('exact mean checkpoint/state/seed/zero-update binding')
                delta = metadata['counts_delta']
                if any(delta.get(key) != 500 for key in ('native_step_attempts', 'native_steps', 'frozen_native_steps', 'frozen_model_steps')) or any(v for k, v in delta.items() if k.startswith('optimizer_')):
                    raise ValueError('mean episode exact paid exposure')
                raw = i.load_arrays(worker_root, row['raw'])
                initial = [raw[key] for key in ('users', 'schedule', 'packet', 'bs_positions')]
                initial += [raw[key][0] for key in b03.STATE_FIELDS]
                initial += [raw[key][0] for key in ('observations', 'states')]
                if e.array_digest(*initial) != metadata['initial_state_sha256']:
                    raise ValueError('complete mean initial physical/information state binding')
                meter.phase = 'reader/' + programme
                result, replay = i.check_episode(raw, row['world'], True, meter)
                i.compare_worker_metrics(result['metrics'], metadata['metrics'])
                result.update(programme=programme, phase=row['phase'], raw=row['raw'], metadata=row['metadata'])
                result['policy'] = i.replay_model(agent, payload, replay, metadata, meter, deterministic=True)
                e.write_json(out / 'checks' / 'frozen' / f"{programme}_{row['world']}.json", result)
                results.append(result)
                del raw, replay
                summary['frozen_checked'] += 1
                summary['inflight'] = None
                publish()
                b.check_counts(meter, 'reader')
        finally:
            del agent
            gc.collect()
    b.check_counts(meter, 'reader', terminal=True)
    b.neural_rows(meter, terminal=True)
    reading = {'schema': 1, 'object': c.OBJECT, 'inference_mode': c.MODE,
               'worker_config': context['config_identity'], 'worker_summary': context['summary_identity'],
               'worker_manifest': context['manifest_identity'], 'source_sha256': context['source_sha256'],
               'baseline_reading': context['baseline_reading_identity'],
               'comparisons': comparisons(results, context['baseline_results']),
               'frozen_results': [{k: v for k, v in r.items() if k not in ('policy', 'max_errors')} for r in results],
               'cost': meter.report(), 'coverage_counts': c.READER_COUNTS,
               'retained_baseline_cost': context['baseline_reading']['cost']}
    e.write_json(out / 'reading.json', reading)
    summary.update(status='COMPLETE', reading=e.identity(out / 'reading.json'), inflight=None)
    b.check_counts(meter, 'reader', terminal=True)
    publish()
