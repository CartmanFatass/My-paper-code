#!/usr/bin/env python3
"""Replay only the failed S2/world29309033/t12 report, without an environment.

Materialize SOURCE_PATHS from SOURCE_SHA into a fresh minimal directory, preserving
relative paths. Do not copy envs/pettingzoo/__init__.py: namespace imports let the
unaltered scheduler import its pure radio module without eager environment imports.
Example (Root owns execution): python -B s2_replay_stress.py --source-root ROOT
  --raw S2_29309033.npz --config config.json --seconds 180 --out UNIQUE_DIRECTORY
Optional --reconstruction accepts the preserved one-report diagnostic JSON.
--clock real checks the scheduler deadline and fails on its first late report;
it excludes the original controller's compute time and is not an episode test.
The default constant-zero clock cannot establish actual-deadline equivalence.
"""

import argparse
import faulthandler
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import platform
import resource
import sys
import sysconfig
import time
import traceback


SOURCE_SHA = '8ab72e5e2c2123e6cf0af6744ada24f8188ec2dc'
RAW_SHA256 = 'c814063d2709353162ce73348d00263569de941941b866723e1f4666feb30117'
CONFIG_SHA256 = 'a579f6023c1b20ff679d57338ad77f61fdbf5862032d0e154211e4021717cab3'
SOURCE_PATHS = (
    'envs/pettingzoo/uav_radio.py',
    'experiments/candidates/uav_local_history/b01/controller.py',
    'experiments/candidates/uav_radio_activation/b01/__init__.py',
    'experiments/candidates/uav_radio_activation/b01/protocol.py',
    'experiments/candidates/uav_radio_activation/b02/__init__.py',
    'experiments/candidates/uav_radio_activation/b02/protocol.py',
    'experiments/candidates/uav_radio_activation/b02/scheduler.py',
    'experiments/candidates/uav_radio_activation/b03/__init__.py',
    'experiments/candidates/uav_radio_activation/b03/protocol.py',
    'experiments/candidates/uav_radio_activation/b03/scheduler.py',
)


def file_identity(path):
    path = Path(path).resolve()
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=digest.hexdigest())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_sources(root, config):
    records = {item['path']: item for item in config['source_identities']}
    verified = []
    # Unexpected package initializers can import environments before radio is loaded.
    allowed_initializers = set(SOURCE_PATHS)
    parents = {parent for name in SOURCE_PATHS for parent in Path(name).parents}
    for parent in parents:
        initializer = parent / '__init__.py'
        require(str(initializer) in allowed_initializers or not (root / initializer).exists(),
                'Use a minimal namespace source root; unexpected initializer: ' + str(initializer))
        require(not list((root / parent / '__pycache__').glob('*.pyc')),
                'Source root must contain no cached bytecode: ' + str(parent))
    for name in SOURCE_PATHS:
        identity = file_identity(root / name)
        expected = records[name]
        require(identity['sha256'] == expected['sha256'] and identity['bytes'] == expected['bytes'],
                'Frozen source mismatch: ' + name)
        verified.append(dict(identity, relative_path=name))
    return verified


def numpy_identity(np):
    root = Path(np.__file__).resolve().parent
    digest = hashlib.sha256()
    count = byte_count = 0
    # Hash executable NumPy inputs, excluding runtime-created bytecode caches.
    bundled_libraries = root.parent / 'numpy.libs'
    bundled = []
    for directory in (root, bundled_libraries):
        for path in sorted(directory.rglob('*')):
            if path.is_file() and (path.suffix == '.py' or '.so' in path.name):
                item = file_identity(path)
                digest.update((str(path.relative_to(root.parent)) + '\0' + item['sha256'] + '\n').encode())
                count += 1
                byte_count += item['bytes']
                if directory == bundled_libraries:
                    bundled.append(item)
    fromnumeric = importlib.import_module('numpy.core.fromnumeric')
    extension = importlib.import_module('numpy.core._multiarray_umath')
    return dict(version=np.__version__, package_root=str(root),
                python_and_shared_object_files=count, bytes=byte_count,
                relative_path_sha256_manifest_digest=digest.hexdigest(),
                bundled_libraries=bundled,
                fromnumeric=file_identity(fromnumeric.__file__),
                multiarray_umath=file_identity(extension.__file__),
                all_dispatcher_bytecode_sha256=hashlib.sha256(
                    fromnumeric._all_dispatcher.__code__.co_code).hexdigest())


def fingerprint(np, arrival):
    selected = (arrival['selected_q'], arrival['selected_mask'])
    require(arrival['timely'] and None not in selected, 'Report did not complete within scheduler clock deadline')
    require(bool(np.isfinite(arrival['commands']).all()), 'Nonfinite selected commands')
    scores = np.asarray(arrival['scores'])
    finite = np.isfinite(scores)
    require(not bool(np.isinf(scores).any()), 'Infinite candidate score')
    expected_finite = np.zeros_like(finite)
    for q, mask in arrival['evaluated_pairs']:
        require(0 <= q < 27 and 1 <= mask <= 31, 'Invalid evaluated pair identity')
        expected_finite[q, mask] = True
    require(bool(np.array_equal(finite, expected_finite)),
            'Score validity differs from completed candidate pairs')
    # Normalize uncomputed NaNs to zero while retaining their exact validity bitmap.
    digest = hashlib.sha256()
    for array in (arrival['commands'], finite, np.where(finite, scores, 0.0)):
        array = np.ascontiguousarray(array)
        digest.update((array.dtype.str + repr(array.shape)).encode())
        digest.update(array.tobytes())
    digest.update(str((selected, arrival['mask'])).encode())
    digest.update(arrival['command_packet'])
    digest.update(b''.join(arrival['reports']))
    return dict(sha256=digest.hexdigest(), selected_q=int(selected[0]),
                selected_mask=int(selected[1]), mask=int(arrival['mask']),
                commands=arrival['commands'].tolist(), selected_score=scores[selected].tolist(),
                evaluated_pairs=len(arrival['evaluated_pairs']),
                candidate_requests=int(arrival['candidate_requests']),
                state_reductions=int(arrival['state_reductions']))


def input_fingerprint(np, arrays, mask, map_packet):
    digest = hashlib.sha256()
    for array in arrays:
        array = np.ascontiguousarray(array)
        digest.update((array.dtype.str + repr(array.shape)).encode())
        digest.update(array.tobytes())
    digest.update(str(mask).encode())
    digest.update(map_packet)
    return digest.hexdigest()


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source-root', 'raw', 'config', 'out'):
        parser.add_argument('--' + name, required=True, type=Path)
    bounds = parser.add_mutually_exclusive_group(required=True)
    bounds.add_argument('--count', type=int)
    bounds.add_argument('--seconds', type=float)
    parser.add_argument('--reconstruction', type=Path)
    parser.add_argument('--clock', choices=('constant-zero', 'real'), default='constant-zero')
    args = parser.parse_args()
    if args.count is not None and args.count <= 0:
        parser.error('--count must be positive')
    if args.seconds is not None and (not math.isfinite(args.seconds) or args.seconds <= 0):
        parser.error('--seconds must be finite and positive')
    return args


def main():
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    started, cpu_started = time.monotonic(), time.process_time()
    record = dict(scope='saved failed report runtime stress; no environment, transitions, fits or endpoint',
                  source_sha=SOURCE_SHA, arm='S2', world=29309033, tick=12,
                  native_steps=0, environments=0, episodes=0, fits=0,
                  report_calls_started=0, report_calls_completed=0,
                  candidate_requests_completed=0, candidate_pairs_completed=0,
                  state_reductions_completed=0, count_limit=args.count,
                  seconds_limit=args.seconds, pid=os.getpid(),
                  clock=args.clock,
                  deadline_scope=('constant zero; no actual deadline claim' if args.clock == 'constant-zero' else
                                  'scheduler report only; original controller compute excluded; no episode endpoint'),
                  deadline_misses=0, report_wall_seconds_max=0.0, report_cpu_seconds_max=0.0,
                  scheduler_clock_seconds_max=0.0,
                  partial_call_counters='Unavailable if decide raises before returning; completed calls only',
                  output=str(args.out.resolve()), python=sys.version, platform=platform.platform(),
                  allocator=os.environ.get('PYTHONMALLOC'), dev_mode=sys.flags.dev_mode,
                  optimize=sys.flags.optimize, pythonoptimize=os.environ.get('PYTHONOPTIMIZE'),
                  seconds_bound_scope='workload only; checked between reports; one in-flight report may overrun')
    output = args.out / 'summary.json'

    def emit(status):
        usage = resource.getrusage(resource.RUSAGE_SELF)
        record.update(status=status, wall_seconds=time.monotonic() - started,
                      process_cpu_seconds=time.process_time() - cpu_started,
                      peak_rss_kib=usage.ru_maxrss,
                      rss_scope='Linux process lifetime maximum, KiB')
        temporary = args.out / 'summary.json.tmp'
        temporary.write_text(json.dumps(record, indent=2, allow_nan=False) + '\n')
        temporary.replace(output)

    with (args.out / 'faulthandler.log').open('w', buffering=1) as faults:
        faulthandler.enable(file=faults, all_threads=True)
        emit('INITIALIZING')
        try:
            sys.dont_write_bytecode = True
            for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
                os.environ[name] = '1'
            record['thread_environment'] = {name: os.environ[name] for name in
                                            ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')}
            record['executable'] = file_identity(sys.executable)
            library = Path(sysconfig.get_config_var('LIBDIR') or '') / (sysconfig.get_config_var('LDLIBRARY') or '')
            if library.is_file():
                record['libpython'] = file_identity(library)
            record['probe'] = file_identity(__file__)
            record['config'] = file_identity(args.config)
            record['raw'] = file_identity(args.raw)
            require(record['config']['sha256'] == CONFIG_SHA256, 'Config is not the failed run config')
            require(record['raw']['sha256'] == RAW_SHA256, 'Raw is not the failed S2 input')
            config = json.loads(args.config.read_text())
            require(config['launch_sha'] == SOURCE_SHA and config['horizon'] == 256,
                    'Frozen launch/config identity mismatch')
            root = args.source_root.resolve()
            record['sources'] = verify_sources(root, config)
            # Namespace roots merge across sys.path; a later full checkout's regular
            # pettingzoo package would otherwise win and eagerly import environments.
            excluded = []
            import_paths = []
            for entry in sys.path:
                directory = Path(entry or os.getcwd()).resolve()
                if directory == root:
                    continue
                if (directory / 'envs').exists() or (directory / 'experiments').exists():
                    excluded.append(str(directory))
                else:
                    import_paths.append(entry)
            record['excluded_other_code_roots'] = excluded
            sys.path[:] = [str(root), *import_paths]
            import numpy as np
            record['numpy'] = numpy_identity(np)
            scheduler_module = importlib.import_module('experiments.candidates.uav_radio_activation.b03.scheduler')
            record['deadline_seconds'] = scheduler_module.DEADLINE_SECONDS
            for item in record['sources']:
                name = item['relative_path'].removesuffix('.py').replace('/', '.')
                if name.endswith('.__init__'):
                    name = name.removesuffix('.__init__')
                module = sys.modules[name]
                require(Path(module.__file__).resolve() == root / item['relative_path'],
                        'Import escaped frozen source root: ' + name)
            require('envs.pettingzoo.uav_env' not in sys.modules and 'torch' not in sys.modules,
                    'Unexpected environment/Torch import')
            with np.load(args.raw, allow_pickle=False) as raw:
                require(int(raw['completed_steps']) == 12 and int(raw['round_count']) == 3,
                        'Unexpected partial-report boundary')
                require(str(raw['episode_failure_type']) == 'SystemError', 'Unexpected saved failure')
                own = raw['observations'][12, :, :3].copy()
                actual, proposals = raw['commands'][12].copy(), raw['proposals'][12].copy()
                mask = int(raw['mask'][12])
                map_packet = raw['map_packet'].tobytes()
                require(bool(raw['c_called'][12]), 'Failed report proposals were not recorded')
            record['saved_inputs'] = dict(observation_dtype=own.dtype.str,
                                         commands_dtype=actual.dtype.str, proposals_dtype=proposals.dtype.str,
                                         current_mask=mask, map_bytes=len(map_packet))
            frozen_inputs = (own, actual, proposals)
            for array in frozen_inputs:
                array.setflags(write=False)
            record['saved_inputs']['dtype_shape_bytes_sha256'] = input_fingerprint(
                np, frozen_inputs, mask, map_packet)
            if args.reconstruction:
                prior = json.loads(args.reconstruction.read_text())
                require((prior['source_sha'], prior['arm'], prior['seed'], prior['tick']) ==
                        (SOURCE_SHA, 'S2', 29309033, 12), 'Prior reconstruction identity mismatch')
                require(prior['raw_identity']['sha256'] == RAW_SHA256 and
                        prior['config_identity']['sha256'] == CONFIG_SHA256,
                        'Prior reconstruction input mismatch')
                require(prior['check']['status'] == 'RECONSTRUCTED_WITHOUT_EXCEPTION',
                        'Prior reconstruction did not complete')
                record['prior_reconstruction'] = dict(identity=file_identity(args.reconstruction),
                    compared_readings='112 evaluated pairs, finite commands and completion only; no saved selection fingerprint',
                    check=prior['check'])
            emit('READY')
            workload_started = time.monotonic()
            record['workload_started_wall_seconds'] = workload_started - started
            next_progress = workload_started
            while (record['report_calls_completed'] == 0 or
                   (record['report_calls_completed'] < args.count if args.count is not None else
                    time.monotonic() - workload_started < args.seconds)):
                # Fresh normal per-report state; no subclass, algorithm replacement or tracing wrapper.
                call_inputs = tuple(array.copy() for array in frozen_inputs)
                report_clock = (lambda: 0.0) if args.clock == 'constant-zero' else time.perf_counter
                scheduler = scheduler_module.Scheduler('S2', map_packet, clock=report_clock,
                                                      cpu_clock=time.process_time, horizon=256)
                report_wall_start, report_cpu_start = time.perf_counter(), time.process_time()
                record['report_calls_started'] += 1
                try:
                    arrival = scheduler.decide(*call_inputs, 12, mask,
                                               started=report_clock(), cpu_started=report_cpu_start)
                finally:
                    report_wall = time.perf_counter() - report_wall_start
                    report_cpu = time.process_time() - report_cpu_start
                    record['last_call_elapsed'] = dict(wall_seconds=report_wall, cpu_seconds=report_cpu)
                    record['report_wall_seconds_max'] = max(record['report_wall_seconds_max'], report_wall)
                    record['report_cpu_seconds_max'] = max(record['report_cpu_seconds_max'], report_cpu)
                record['report_calls_completed'] += 1
                record['candidate_requests_completed'] += int(arrival['candidate_requests'])
                record['candidate_pairs_completed'] += len(arrival['evaluated_pairs'])
                record['state_reductions_completed'] += int(arrival['state_reductions'])
                record['scheduler_clock_seconds_max'] = max(record['scheduler_clock_seconds_max'], arrival['wall_seconds'])
                record['last_report'] = dict(timely=bool(arrival['timely']),
                    selected_q=arrival['selected_q'], selected_mask=arrival['selected_mask'],
                    applied_mask=int(arrival['mask']), command_packet_bytes=len(arrival['command_packet']),
                    evaluated_pairs=len(arrival['evaluated_pairs']), candidate_requests=int(arrival['candidate_requests']),
                    state_reductions=int(arrival['state_reductions']), wall_seconds=report_wall,
                    cpu_seconds=report_cpu, scheduler_clock_seconds=float(arrival['wall_seconds']))
                if not arrival['timely']:
                    record['deadline_misses'] += 1
                    raise RuntimeError('Scheduler deadline miss; completed/missed report retained in last_report')
                reading = fingerprint(np, arrival)
                record['last_fingerprint'] = reading
                require(input_fingerprint(np, call_inputs, mask, map_packet) ==
                        record['saved_inputs']['dtype_shape_bytes_sha256'], 'Scheduler mutated call inputs')
                require(input_fingerprint(np, frozen_inputs, mask, map_packet) ==
                        record['saved_inputs']['dtype_shape_bytes_sha256'], 'Frozen saved input changed')
                require(reading['evaluated_pairs'] == 112, 'Mismatch with preserved reconstruction: expected112pairs')
                require(reading['candidate_requests'] == 116 and reading['state_reductions'] == 448,
                        'Unexpected frozen sequential-search request/reduction counts')
                if args.reconstruction:
                    check = record['prior_reconstruction']['check']
                    require(reading['evaluated_pairs'] == check['evaluated_pairs'] and
                            check['finite_commands'] and check['timely_under_test_clock'],
                            'Mismatch with preserved reconstruction readings')
                if 'first_fingerprint' not in record:
                    record['first_fingerprint'] = reading
                require(reading == record['first_fingerprint'], 'Replay command/mask/score fingerprint changed')
                del arrival, scheduler, call_inputs
                now = time.monotonic()
                if now >= next_progress:
                    record['workload_wall_seconds'] = now - workload_started
                    emit('RUNNING')
                    print(json.dumps(dict(status='RUNNING', reports=record['report_calls_completed'],
                                          candidate_requests=record['candidate_requests_completed'])), flush=True)
                    next_progress = now + 5.0
            record['workload_wall_seconds'] = time.monotonic() - workload_started
            emit('PASS')
        except BaseException:
            record['exception'] = traceback.format_exc()
            emit('FAIL')
            raise
        finally:
            faulthandler.disable()
    print(json.dumps(dict(status=record['status'], summary=str(output),
                          reports=record['report_calls_completed'])), flush=True)


if __name__ == '__main__':
    main()
