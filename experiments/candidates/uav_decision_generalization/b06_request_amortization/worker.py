"""The single selected fixed-bank acquisition and seven-arm native purchase."""
from dataclasses import asdict
from pathlib import Path
import time

import numpy as np

from experiments.candidates.uav_decision_generalization.b03_joint_window import evidence as e
from experiments.candidates.uav_decision_generalization.b05_request_schedule.native import RequestHost
from experiments.candidates.uav_decision_generalization.b05_request_schedule.task import (
    PublicState, QueueLedger, initial_assignment, pack_reset, pack_report, pack_command,
)
from . import acquisition as a, contract as c
from .bindings import validate_roster
from .policy import Endpoint
from .storage import MISSION_SHAPES, R_SHAPES, RolloutTrace, new_mission_arrays, put_state, put_g, write_npz


def rng(name, *coordinates):
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence(c.rng_domain(name, *coordinates))))


def bytes_for_shapes(shapes):
    return sum(int(np.prod(shape)) * np.dtype(dtype).itemsize for shape, dtype in shapes.values())


def mission_allocation_bound(is_rollout):
    # Compressed npz can exceed uncompressed bytes only by ZIP/deflate framing;
    # doubling plus per-array framing is conservative for these fixed arrays.
    # Retain all60 compressed rollouts and at most one live scratch trace.
    mission = 2 * bytes_for_shapes(MISSION_SHAPES) + 1024**2
    trace = 2 * bytes_for_shapes(R_SHAPES) + 1024**2
    return mission + (61 * trace if is_rollout else 0) + 16 * 1024**2


def cost_since(meter, cpu, wall, scope):
    return {'cpu_seconds': meter.report()['phase_cpu_seconds'] - cpu,
            'wall_seconds': time.monotonic() - wall, 'scope': scope}


def scientific_manifest(out):
    paths = [out / name for name in ('config.json', 'endpoint-counts.json', 'bank.npz',
                                     'bank-provenance.json', 'constant.json')]
    paths.extend(path for name in ('fits', 'raw') for path in (out / name).rglob('*') if path.is_file())
    return {str(path.relative_to(out)): e.identity(path) for path in sorted(paths)}


def mission(out, world, label, endpoint, meter, records):
    directory = out / 'raw' / label
    directory.mkdir(parents=True, exist_ok=True)
    npz_path, metadata_path = directory / f'{world}.npz', directory / f'{world}.json'
    if npz_path.exists() or metadata_path.exists():
        raise FileExistsError('mission record already exists; no replay')
    is_rollout = endpoint.spec['kind'] in ('R4', 'R1')
    meter.check_disk(anticipated_bytes=mission_allocation_bound(is_rollout))
    before, wall = meter.check(), time.monotonic()
    arrays = new_mission_arrays()
    metadata = {'schema': 1, 'world': world, 'label': label, 'training': False,
                'initial_audit': False, 'completed_native_steps': 0,
                'completed_decisions': 0, 'status': 'RUNNING', 'decisions': [],
                'rollout_traces': [], 'logical_reset_bytes': 0,
                'logical_report_bytes': 0, 'logical_command_bytes': 0,
                'logical_training_feedback_bytes': 0,
                'offline_initial_audit_cpu_seconds': 0., 'offline_initial_audit_wall_seconds': 0.,
                'assignment_comparisons': 720, 'assignment_distances': 36}
    host = None
    try:
        meter.reserve('actual_constructor_attempts')
        host = RequestHost(world)
        meter.add('actual_constructors')
        users = np.asarray(host.user_positions, dtype=np.int32)
        rates = rng('rates', world).permutation(np.array([6, 3, 2, 1], dtype=np.uint8))
        arrival_draws = rng('actual_arrivals', world).random((48, 4))
        actual_arrivals = arrival_draws < rates.astype(np.float64) / 10
        active, pairs = initial_assignment(users, rates, host.uav_positions)
        pending, ledger = active.copy(), QueueLedger()
        arrays.update(users=users, rates=rates, pairs=np.asarray(pairs, dtype=np.uint8),
                      initial_slots=active.copy(), arrival_draws=arrival_draws, arrival_tape=actual_arrivals)
        metadata['logical_reset_bytes'] = len(pack_reset(users, rates))
        put_state(arrays['states'][0], host.snapshot(), ledger.counts, ledger.progress, active, 0)
        for tick in range(c.HORIZON):
            meter.check()
            macro, boundary = tick // c.CONTROL_PERIOD, tick % c.CONTROL_PERIOD == 0
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
                if is_rollout:
                    trace = RolloutTrace(out / 'scratch' / f'{endpoint.spec["kind"]}_{world}_{macro}', create=True)
                try:
                    decision = endpoint.decide(state, trace.directory if trace else None)
                except BaseException as exc:
                    if hasattr(exc, 'partial_decision'):
                        metadata['incomplete_decision'] = e.jsonable(exc.partial_decision)
                    raise
                finally:
                    if trace is not None:
                        # Endpoint.decide returns only with a waiting child or
                        # after reaping it; its fixed mmap is safe to collect.
                        if trace.count('g_attempts'):
                            meter.add('R_base_g_reserved_candidate_ticks', 4 * min(c.G_HORIZON, c.HORIZON - tick))
                            meter.add('R_base_g_attempts')
                        relative = Path('raw') / 'rollouts' / endpoint.spec['kind'] / f'{world}_{macro}.npz'
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
                for key in ('g_action', 'greedy_action', 'total_q', 'residual'):
                    if decision[key] is not None:
                        arrays[key][macro] = decision[key]
                arrays['nn_complete'][macro] = endpoint.spec['kind'] == 'S' and decision['residual'] is not None
                arrays['score_complete'][macro] = decision['score_complete']
                metadata['decisions'].append(e.jsonable({key: decision[key] for key in ('timing', 'cohorts', 'score_complete')}))
                metadata['completed_decisions'] += 1
            meter.reserve('actual_native_attempts')
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
        metadata.update(status='COMPLETE', area_cost=ledger.area_cost,
                        terminal_charge=ledger.terminal_charge, total_cost=ledger.total_cost,
                        requests=[asdict(x) for x in ledger.arrivals],
                        completions=[asdict(x) for x in ledger.completions],
                        unfinished=[[asdict(x) for x in queue] for queue in ledger.unfinished],
                        last_command_unused=True, actual_native_events=dict(host.event_counts))
        if int(arrays['macro_cost'].sum()) != ledger.total_cost:
            raise AssertionError('macro costs do not conserve episode C')
        if sum(metadata[name] for name in ('logical_reset_bytes', 'logical_report_bytes', 'logical_command_bytes')) != 11195:
            raise AssertionError('complete logical wire bill differs')
    except BaseException as exc:
        metadata.update(status='FAILED', error_type=type(exc).__name__, error=str(exc),
                        actual_native_events={} if host is None else dict(host.event_counts),
                        endpoint_counts=endpoint.counters())
        raise
    finally:
        write_npz(npz_path, arrays)
        after = meter.report()
        metadata['cost'] = {'inclusive_cpu_seconds': after['phase_cpu_seconds'] - before['phase_cpu_seconds'],
                            'inclusive_wall_seconds': time.monotonic() - wall,
                            'before': before, 'after': after,
                            'scope': 'constructor/task/decision/native/trace compression; excludes final metadata write'}
        e.write_json(metadata_path, metadata)
        records.append({'world': world, 'label': label, 'status': metadata['status'],
                        'npz': str(npz_path.relative_to(out)), 'metadata': str(metadata_path.relative_to(out)),
                        'total_cost': metadata.get('total_cost'),
                        'completed_native_steps': metadata['completed_native_steps']})
        e.write_json(out / 'progress.json', {'records': records, 'cost': meter.report()})
    meter.check_disk()
    return metadata


def run(root, out, args, context):
    meter, source = context['meter'], context['source_identity']
    records, endpoints, fits, endpoint_counts = [], [], [], []
    acquisition_cpu, acquisition_wall = meter.check()['phase_cpu_seconds'], time.monotonic()
    def make(spec, name):
        endpoint = Endpoint(spec, out / 'scratch' / name, meter, source)
        endpoints.append(endpoint)
        return endpoint
    try:
        # Upper bounds cover temporary+final bank, provenance, journal and
        # checkpoints; no old evidence copy and no model warm-up is created.
        meter.check_disk(anticipated_bytes=64 * 1024**2)
        bank_cpu, bank_wall = meter.report()['phase_cpu_seconds'], time.monotonic()
        bank = a.binding_bank(context['teacher_root'], context['teacher_reader_summary'], meter=meter)
        write_npz(out / 'bank.npz', {'features': bank.features, 'raw_g': bank.raw_g,
                                    'teacher': bank.teacher, 'keys': np.asarray(bank.keys, dtype=np.int64)})
        e.write_json(out / 'bank-provenance.json', bank.provenance)
        bank_cost = cost_since(meter, bank_cpu, bank_wall, 'old identities/labels plus new derived bank serialization')
        bank_record = {'identity': bank.identity, 'arrays': e.identity(out / 'bank.npz'),
                       'provenance': e.identity(out / 'bank-provenance.json')}
        cpu, wall = meter.check()['phase_cpu_seconds'], time.monotonic()
        solution = a.solve_constant(bank, meter=meter)
        constant = {'schema': 1, 'object': c.OBJECT, 'source_identity': source,
                    'launch_sha': args.launch_sha, 'bank_identity': bank.identity,
                    'solution': e.jsonable(solution)}
        constant['acquisition_cost'] = cost_since(meter, cpu, wall, 'one ordered anchored LS system and solve')
        e.write_json(out / 'constant.json', constant)
        constant_identity = e.identity(out / 'constant.json')
        for fit in range(3):
            meter.check_disk(anticipated_bytes=64 * 1024**2)
            cpu, wall = meter.check()['phase_cpu_seconds'], time.monotonic()
            fit_out = out / 'fits' / f'fit{fit}'
            record = a.fit_endpoint(bank, fit, fit_out, source_identity=source,
                                    launch_sha=args.launch_sha, meter=meter)
            record['acquisition_cost'] = cost_since(meter, cpu, wall,
                                                   'scorer initialization/all64 epochs/initial+final bank/checkpoints/journal')
            e.write_json(fit_out / 'fit.json', record)
            fits.append(record)
            meter.check_disk()
        acquisition_cost = cost_since(meter, acquisition_cpu, acquisition_wall,
                                      'all bank handling/B fit/three independent supervised fits and artifacts')
        frozen = {kind: make({'kind': kind}, kind) for kind in ('G', 'R4', 'R1')}
        frozen['B'] = make({'kind': 'B', 'constant_path': str(out / 'constant.json'),
                            'constant_identity': constant_identity, 'constant_launch_sha': args.launch_sha,
                            'bank_identity': bank.identity}, 'B')
        for fit, record in enumerate(fits):
            name = f'S{fit}'
            frozen[name] = make({'kind': 'S', 'fit': fit, 'checkpoint': record['final']['path'],
                                 'checkpoint_identity': record['final'], 'checkpoint_launch_sha': args.launch_sha,
                                 'bank_identity': bank.identity}, name)
        for world, label in c.expected_roster():
            mission(out, world, label, frozen[label.split('/')[1]], meter, records)
        validate_roster(records)
        for endpoint in list(endpoints):
            endpoint_counts.append({'name': endpoint.directory.name, 'counts': endpoint.close(), 'starts': endpoint.starts})
            endpoints.remove(endpoint)
        e.write_json(out / 'endpoint-counts.json', endpoint_counts)
        manifest = {'schema': 1, 'files': scientific_manifest(out), 'records': records,
                    'fits': fits, 'bank': bank_record, 'constant': constant_identity,
                    'endpoint_counts': endpoint_counts}
        e.write_json(out / 'manifest.json', manifest)
        meter.check()
        totals = {'constant_fits': solution['counts']['solves'], 'neural_fits': len(fits),
                  'updates': sum(fit['counts']['updates'] for fit in fits),
                  'backwards': sum(fit['counts']['backwards'] for fit in fits),
                  'context_presentations': sum(fit['counts']['forward_rows'] for fit in fits) // 4,
                  'training_neural_rows': sum(fit['counts']['forward_rows'] for fit in fits),
                  'bank_endpoint_neural_rows': sum(fit[stage + '_forward_counts']['forward_rows']
                                                   for fit in fits for stage in ('initial', 'final'))}
        e.write_json(out / 'summary.json', {'schema': 1, 'object': c.OBJECT, 'status': 'COMPLETE',
                     'launch_sha': args.launch_sha, 'missions': len(records), 'fits': fits,
                     'bank': bank_record, 'constant': constant_identity, 'bank_handling_cost': bank_cost,
                     'acquisition_cost': acquisition_cost, 'acquisition_totals': totals,
                     'endpoint_counts': endpoint_counts, 'cost': meter.report(),
                     'source_identity': source, 'reading_pending': True})
    finally:
        for endpoint in endpoints:
            endpoint._reap(terminate=True)
            endpoint_counts.append({'name': endpoint.directory.name, 'counts': endpoint.close(), 'starts': endpoint.starts})
        e.write_json(out / 'endpoint-counts.json', endpoint_counts)
