"""The single fixed three-fit/common-panel B05 purchase."""
from pathlib import Path
from dataclasses import asdict
import time

import numpy as np

from experiments.candidates.uav_decision_generalization.b03_joint_window import evidence as e
from . import contract as c
from .native import RequestHost
from .policy import Endpoint
from .storage import STATE_DTYPE, G_DTYPE, RolloutTrace, put_state, put_g, write_npz
from .task import (PublicState, QueueLedger, initial_assignment, pack_reset,
                   pack_report, pack_command)


def rng(name, *coordinates):
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence(c.rng_domain(name, *coordinates))))


def transition(arrays, index, next_index=None):
    terminal = next_index is None
    return {'features': arrays['features'][index].copy(),
            'raw_g': arrays['reports']['costs'][index].copy(),
            'action': int(arrays['action'][index]), 'cost': int(arrays['macro_cost'][index]),
            'next_features': None if terminal else arrays['features'][next_index].copy(),
            'next_raw_g': None if terminal else arrays['reports']['costs'][next_index].copy(),
            'terminated': terminal}


def store_update(arrays, index, answer):
    arrays['offline_wall'][index] = answer['wall_seconds']
    arrays['offline_cpu'][index] = answer['cpu_seconds']
    update = answer['update']
    if update is None:
        return
    arrays['update_number'][index] = update['update']
    arrays['update_samples'][index] = update['sample_indices']
    for column, key in enumerate(('loss', 'grad_norm_before_clip', 'grad_norm_after_clip',
                                  'target_mean', 'prediction_mean', 'nonterminal_rows')):
        arrays['update_values'][index, column] = update[key]


def scientific_manifest(out):
    """Only immutable worker evidence; supervisor status/logs have another owner."""
    out = Path(out)
    paths = [out / 'config.json', out / 'endpoint-counts.json']
    for fit in range(3):
        paths.append(out / f'fit{fit}.json')
        paths.extend(out / 'checkpoints' / f'fit{fit}_{kind}.pt'
                     for kind in ('initial', 'final', 'training'))
    paths.extend(path for path in (out / 'raw').rglob('*') if path.is_file())
    return {str(path.relative_to(out)): e.identity(path) for path in sorted(paths)}


def mission(out, world, label, endpoint, meter, records, *, training=False, initial=False, audit_endpoint=None):
    directory = out / 'raw' / label
    directory.mkdir(parents=True, exist_ok=True)
    npz_path, metadata_path = directory / f'{world}.npz', directory / f'{world}.json'
    if npz_path.exists() or metadata_path.exists():
        raise FileExistsError('mission record already exists')
    cost_before = meter.check()
    wall_before = time.monotonic()
    meter.add('actual_constructor_attempts')
    host = RequestHost(world)
    meter.add('actual_constructors')
    users = np.asarray(host.user_positions, dtype=np.int32)
    rates = rng('rates', world).permutation(np.array([6, 3, 2, 1], dtype=np.uint8))
    actual_rng = rng('actual_arrivals', world)
    arrival_draws = actual_rng.random((48, 4))
    actual_arrivals = arrival_draws < rates.astype(np.float64) / 10
    active, pairs = initial_assignment(users, rates, host.uav_positions)
    pending = active.copy()
    ledger = QueueLedger()
    arrays = {
        'users': users, 'rates': rates, 'pairs': np.asarray(pairs, dtype=np.uint8),
        'initial_slots': active.copy(), 'arrival_draws': arrival_draws,
        'arrival_tape': actual_arrivals, 'states': np.zeros(1201, dtype=STATE_DTYPE),
        'raw_actions': np.zeros((1200, 6, 3), dtype=np.float64),
        'executed_actions': np.zeros((1200, 6, 3), dtype=np.float64),
        'arrivals': np.zeros((1200, 4), dtype=bool),
        'tick_cost': np.zeros(1200, dtype=np.uint16),
        'reports': np.zeros(60, dtype=G_DTYPE),
        'features': np.zeros((60, 4, c.FEATURE_COUNT), dtype=np.float32),
        'commands': np.zeros((60, 6), dtype=np.uint8),
        'action': np.zeros(60, dtype=np.uint8),
        'g_action': np.full(60, -1, dtype=np.int8),
        'greedy_action': np.full(60, -1, dtype=np.int8),
        'total_q': np.zeros((60, 4), dtype=np.float64),
        'residual': np.zeros((60, 4), dtype=np.float32),
        'nn_complete': np.zeros(60, dtype=bool),
        'exploration_draw': np.zeros(60, dtype=np.float64),
        'exploratory_action': np.full(60, -1, dtype=np.int8),
        'macro_cost': np.zeros(60, dtype=np.uint32),
        'update_number': np.zeros(60, dtype=np.int32),
        'update_samples': np.full((60, 128), -1, dtype=np.int32),
        'update_values': np.zeros((60, 6), dtype=np.float64),
        'offline_wall': np.zeros(60, dtype=np.float64),
        'offline_cpu': np.zeros(60, dtype=np.float64),
        'initial_audit_residual': np.zeros((60, 4), dtype=np.float32),
        'initial_audit_complete': np.zeros(60, dtype=bool),
    }
    metadata = {'schema': 1, 'world': world, 'label': label, 'training': training,
                'initial_audit': initial, 'completed_native_steps': 0,
                'completed_decisions': 0, 'status': 'RUNNING', 'decisions': [],
                'rollout_traces': [], 'logical_reset_bytes': len(pack_reset(users, rates)),
                'logical_report_bytes': 0, 'logical_command_bytes': 0,
                'logical_training_feedback_bytes': 0,
                'offline_initial_audit_cpu_seconds': 0., 'offline_initial_audit_wall_seconds': 0.,
                'assignment_comparisons': 720, 'assignment_distances': 36}
    put_state(arrays['states'][0], host.snapshot(), ledger.counts, ledger.progress, active, 0)
    try:
        for tick in range(c.HORIZON):
            meter.check()
            macro = tick // c.CONTROL_PERIOD
            boundary = tick % c.CONTROL_PERIOD == 0
            if tick and boundary:
                active = pending.copy()
            arrivals = actual_arrivals[macro] if boundary and tick <= c.LAST_ARRIVAL_TICK else np.zeros(4, dtype=bool)
            arrays['arrivals'][tick] = arrivals
            charged = ledger.start_tick(tick, arrivals)
            arrays['tick_cost'][tick] = charged
            arrays['macro_cost'][macro] += charged
            if boundary:
                state = PublicState(world, tick, users, rates, host.uav_positions,
                                    host.ack(), ledger.counts, ledger.progress, active, pairs)
                metadata['logical_report_bytes'] += len(pack_report(state))
                put_g(arrays['reports'][macro], state)
                trace = None
                if endpoint.spec['kind'] == 'R':
                    trace_directory = out / 'scratch' / f'R_{world}_{macro}'
                    trace = RolloutTrace(trace_directory, create=True)
                decision = None
                try:
                    decision = endpoint.decide(state, trace.directory if trace else None)
                except BaseException as exc:
                    if hasattr(exc, 'partial_decision'):
                        metadata['incomplete_decision'] = e.jsonable(exc.partial_decision)
                    raise
                finally:
                    if trace is not None:
                        if trace.count('g_attempts'):
                            meter.add('R_base_g_reserved_candidate_ticks', 4 * min(c.G_HORIZON, c.HORIZON - tick))
                            meter.add('R_base_g_attempts')
                        relative = Path('raw') / 'rollouts' / f'{world}_{macro}.npz'
                        (out / relative).parent.mkdir(parents=True, exist_ok=True)
                        stats = trace.collect(out / relative)
                        metadata['rollout_traces'].append({'decision': macro, 'path': str(relative), 'stats': stats})
                        for key, value in stats.items():
                            meter.add('R_' + key, value)
                pending = decision['command'].copy()
                metadata['logical_command_bytes'] += len(pack_command(pending, pairs))
                arrays['commands'][macro], arrays['action'][macro] = pending, decision['action']
                if decision['raw_g'] is not None:
                    put_g(arrays['reports'][macro], state, decision['raw_g'])
                    arrays['features'][macro] = decision['features']
                for key in ('g_action', 'greedy_action', 'total_q', 'residual', 'exploration_draw', 'exploratory_action'):
                    if decision[key] is not None:
                        arrays[key][macro] = decision[key]
                arrays['nn_complete'][macro] = endpoint.spec['kind'] in ('train', 'L') and decision['residual'] is not None
                metadata['decisions'].append(e.jsonable({key: decision[key] for key in ('timing', 'cohorts')}))
                metadata['completed_decisions'] += 1
                if initial:
                    if endpoint.spec['kind'] != 'G' or audit_endpoint is None:
                        raise RuntimeError('L-initial uses canonical G plus a separate offline audit')
                    if decision['raw_g'] is None:
                        raise RuntimeError('initial audit lacks its timed G cache')
                    audit_before, audit_wall = meter.report()['phase_cpu_seconds'], time.monotonic()
                    audit = audit_endpoint.offline('audit_initial', features=decision['features'], raw_g=decision['raw_g'])
                    metadata['offline_initial_audit_cpu_seconds'] += meter.report()['phase_cpu_seconds'] - audit_before
                    metadata['offline_initial_audit_wall_seconds'] += time.monotonic() - audit_wall
                    arrays['initial_audit_residual'][macro] = audit['residual']
                    arrays['initial_audit_complete'][macro] = True
                if training and macro:
                    answer = endpoint.offline('observe', transition=transition(arrays, macro - 1, macro))
                    store_update(arrays, macro - 1, answer)
                    metadata['logical_training_feedback_bytes'] += 4
            meter.add('actual_native_attempts')
            raw, executed, snap = host.advance(active, users)
            arrays['raw_actions'][tick], arrays['executed_actions'][tick] = raw, executed
            ledger.finish_tick(tick, host.ack())
            put_state(arrays['states'][tick + 1], snap, ledger.counts, ledger.progress, active, tick + 1)
            metadata['completed_native_steps'] = tick + 1
            meter.add('actual_native_steps')
        arrays['macro_cost'][-1] += ledger.terminal_cost()
        terminal = PublicState(world, c.HORIZON, users, rates, host.uav_positions,
                               host.ack(), ledger.counts, ledger.progress, active, pairs)
        metadata['logical_report_bytes'] += len(pack_report(terminal))
        if training:
            answer = endpoint.offline('observe', transition=transition(arrays, 59))
            store_update(arrays, 59, answer)
            metadata['logical_training_feedback_bytes'] += 4
        metadata.update(status='COMPLETE', area_cost=ledger.area_cost,
                        terminal_charge=ledger.terminal_charge, total_cost=ledger.total_cost,
                        requests=[asdict(x) for x in ledger.arrivals],
                        completions=[asdict(x) for x in ledger.completions],
                        unfinished=[[asdict(x) for x in queue] for queue in ledger.unfinished],
                        last_command_unused=True, actual_native_events=dict(host.event_counts))
        if int(arrays['macro_cost'].sum()) != ledger.total_cost:
            raise AssertionError('macro costs do not conserve episode C')
        if metadata['logical_reset_bytes'] + metadata['logical_report_bytes'] + metadata['logical_command_bytes'] != 11195:
            raise AssertionError('complete logical wire bill differs from fixed contract')
    except BaseException as exc:
        metadata.update(status='FAILED', error_type=type(exc).__name__, error=str(exc),
                        actual_native_events=dict(host.event_counts), endpoint_counts=endpoint.counters())
        raise
    finally:
        write_npz(npz_path, arrays)
        cost_after = meter.report()
        metadata['cost'] = {'inclusive_cpu_seconds': cost_after['phase_cpu_seconds'] - cost_before['phase_cpu_seconds'],
                            'inclusive_wall_seconds': time.monotonic() - wall_before,
                            'before': cost_before, 'after': cost_after,
                            'scope': 'constructor/task/decision/native/offline acquisition and audits/trace compression; excludes final metadata write'}
        e.write_json(metadata_path, metadata)
        records.append({'world': world, 'label': label, 'status': metadata['status'],
                        'npz': str(npz_path.relative_to(out)), 'metadata': str(metadata_path.relative_to(out)),
                        'total_cost': metadata.get('total_cost'),
                        'completed_native_steps': metadata['completed_native_steps']})
        e.write_json(out / 'progress.json', {'records': records, 'cost': meter.report()})
    return metadata


def run(root, out, args, context):
    meter = context['meter']
    records, endpoints, fits = [], [], []
    source_identity = context['source_identity']
    endpoint_counts = []
    def make(spec, name):
        result = Endpoint(spec, out / 'scratch' / name, meter, source_identity)
        endpoints.append(result)
        return result
    try:
        checkpoints = out / 'checkpoints'
        checkpoints.mkdir(exist_ok=False)
        for fit, worlds in enumerate(c.TRAIN_WORLDS):
            fit_cpu_before, fit_wall_before = meter.report()['phase_cpu_seconds'], time.monotonic()
            initial_path, final_path = checkpoints / f'fit{fit}_initial.pt', checkpoints / f'fit{fit}_final.pt'
            training_path = checkpoints / f'fit{fit}_training.pt'
            endpoint = make({'kind': 'train', 'fit': fit,
                             'initial_checkpoint': str(initial_path)}, f'train{fit}')
            for world in worlds:
                mission(out, world, f'train/fit{fit}', endpoint, meter, records, training=True)
            result = endpoint.offline('checkpoint', deployment=str(final_path), training=str(training_path))
            if result['metrics']['transitions'] != 30720 or result['metrics']['updates'] != 30464 or result['metrics']['target_copies'] != 119:
                raise AssertionError('fixed training update/target schedule differs')
            fit_record = {'fit': fit, 'initial': e.identity(initial_path), 'final': e.identity(final_path),
                          'training': e.identity(training_path),
                          'metrics': result['metrics'], 'full_state_identity': result['identity']}
            fits.append(fit_record)
            endpoint_counts.append({'name': f'train{fit}', 'counts': endpoint.close(), 'starts': endpoint.starts})
            endpoints.remove(endpoint)
            fit_record['acquisition_cost'] = {
                'cpu_seconds': meter.report()['phase_cpu_seconds'] - fit_cpu_before,
                'wall_seconds': time.monotonic() - fit_wall_before,
                'scope': 'fit endpoint setup/all512 missions/initial+final+compact training checkpoints/hash/close'}
            e.write_json(out / f'fit{fit}.json', fit_record)
        frozen = {kind: make({'kind': kind}, kind) for kind in ('G', 'R')}
        for fit, record in enumerate(fits):
            frozen[f'L{fit}'] = make({'kind': 'L', 'fit': fit,
                                     'checkpoint': record['final']['path'],
                                     'checkpoint_sha256': record['final']['sha256']}, f'L{fit}')
        labels = ['G', 'R', 'L0', 'L1', 'L2']
        for index, world in enumerate(c.MAIN_WORLDS):
            for label in labels[index % 5:] + labels[:index % 5]:
                mission(out, world, f'main/{label}', frozen[label], meter, records)
        for fit, world in enumerate(c.AUDIT_WORLDS):
            initial_endpoint = make({'kind': 'initial', 'fit': fit,
                                     'checkpoint': fits[fit]['initial']['path'],
                                     'checkpoint_sha256': fits[fit]['initial']['sha256']}, f'initial{fit}')
            audit = {'G': frozen['G'], 'R': frozen['R'], 'initial': frozen['G'],
                     'final': frozen[f'L{fit}']}
            names = ['G', 'R', 'initial', 'final']
            for name in names[fit % 4:] + names[:fit % 4]:
                mission(out, world, f'audit{fit}/{name}', audit[name], meter, records,
                        initial=name == 'initial', audit_endpoint=initial_endpoint if name == 'initial' else None)
            endpoint_counts.append({'name': f'initial{fit}', 'counts': initial_endpoint.close(), 'starts': initial_endpoint.starts})
            endpoints.remove(initial_endpoint)
        if len(records) != 1708 or meter.counts['actual_native_steps'] != 2049600:
            raise AssertionError('complete fixed purchase count differs')
        for endpoint in list(endpoints):
            endpoint_counts.append({'name': endpoint.directory.name, 'counts': endpoint.close(), 'starts': endpoint.starts})
            endpoints.remove(endpoint)
        e.write_json(out / 'endpoint-counts.json', endpoint_counts)
        manifest = scientific_manifest(out)
        e.write_json(out / 'manifest.json', {'schema': 1, 'files': manifest, 'records': records,
                                          'fits': fits, 'endpoint_counts': endpoint_counts})
        meter.check()
        e.write_json(out / 'summary.json', {'schema': 1, 'object': 'B05_request_schedule',
                     'status': 'COMPLETE', 'launch_sha': args.launch_sha, 'missions': len(records),
                     'fits': fits, 'endpoint_counts': endpoint_counts, 'cost': meter.report(),
                     'source_identity': source_identity, 'reading_pending': True})
    finally:
        for endpoint in endpoints:
            # This is cancellation of this purchase, never a replacement fit.
            endpoint._reap(terminate=True)
            endpoint_counts.append({'name': endpoint.directory.name, 'counts': endpoint.close(), 'starts': endpoint.starts})
        e.write_json(out / 'endpoint-counts.json', endpoint_counts)
