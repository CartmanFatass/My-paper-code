#!/usr/bin/env python3
"""Generic POSIX observation: up to eight probes, one pending wake per owning session."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import shlex
import signal
import threading
import subprocess
import sys
import time
import uuid

WINDOW = 1500
MAX_WINDOW = 86400
SCHEMA_VERSION = 2


def save(path, value):
    temporary = path.with_suffix('.tmp')
    with temporary.open('w', encoding='utf-8') as out:
        json.dump(value, out, ensure_ascii=False, indent=2)
        out.flush()
        os.fsync(out.fileno())
    temporary.replace(path)


@contextmanager
def transaction(folder):
    with (folder / 'state.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = folder / 'state.json'
        state = json.loads(path.read_text()) if path.exists() else {}
        yield state
        save(path, state)


def owner():
    value = os.environ.get('CODEX_THREAD_ID', '')
    uuid.UUID(value)
    return str(uuid.UUID(value))


def check_owner(state):
    if state.get('schema_version') != SCHEMA_VERSION:
        raise ValueError('incompatible state format; stop the old observer before using a new state directory')
    if state.get('thread') != owner():
        raise ValueError('wait state belongs to a different Codex session')


def validate_window(window):
    if type(window) not in (int, float) or not math.isfinite(window) or not 0 < window <= MAX_WINDOW:
        raise ValueError('window must be positive and <= 86400 seconds')


def validate_job(job):
    if not isinstance(job, dict) or not isinstance(job.get('id'), str) or not job['id']:
        raise ValueError('job needs a stable nonempty id')
    if 'protocol' in job:
        raise ValueError('business protocols belong in an adapter, not the generic observer')
    allowed = {'id', 'argv', 'cwd', 'interval_seconds', 'probe_timeout_seconds'}
    if set(job) - allowed:
        raise ValueError('unknown job fields: ' + ', '.join(sorted(set(job) - allowed)))
    argv = job.get('argv')
    if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or '\0' in x for x in argv):
        raise ValueError('probe argv must be a nonempty string array')
    if not Path(argv[0]).is_absolute() or not Path(argv[0]).is_file() or not os.access(argv[0], os.X_OK):
        raise ValueError('probe requires an existing absolute executable')
    cwd = job.get('cwd', '')
    if not isinstance(cwd, str) or not Path(cwd).is_absolute() or not Path(cwd).is_dir():
        raise ValueError('probe cwd must be an existing absolute directory')
    for key, default, maximum in (('interval_seconds', 30, 300), ('probe_timeout_seconds', 20, 3600)):
        value = job.get(key, default)
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 < value <= maximum:
            raise ValueError(f'{key} must be positive and <= {maximum} seconds')


def event(state, key, kind, evidence):
    # A terminal fact per operation, one checkpoint per generation, or one blocker
    # until the DM explicitly resumes that job. Event bodies stay in private state.
    event_id = hashlib.sha256(key.encode()).hexdigest()[:24]
    if event_id not in state['events']:
        state['events'][event_id] = {'id': event_id, 'kind': kind, 'evidence': evidence,
                                     'created': time.time(), 'consumed': False}
    return event_id


def pending(state):
    return [value for value in state['events'].values() if not value['consumed']]


def classify(body):
    if not isinstance(body, dict):
        raise ValueError('probe output is not a JSON object')
    status = body.get('state')
    if status not in ('running', 'complete', 'failed', 'blocked', 'unknown'):
        raise ValueError('unsupported probe state')
    return status


def stop_probe(process):
    """Terminate only the observation command group, never the observed work handle."""
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.communicate(timeout=3)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()


def probe(job, remaining, cancel=None):
    timeout = max(0.001, min(remaining, job.get('probe_timeout_seconds', 20)))
    # Let bounded long-poll adapters finish before their owning probe deadline.
    observation = max(0.001, timeout - min(5, timeout / 5))
    argv = [x.replace('{window_seconds}', str(observation)) for x in job['argv']]
    try:
        process = subprocess.Popen(argv, cwd=job['cwd'], stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                   start_new_session=True)
        until = time.monotonic() + timeout
        try:
            while True:
                if cancel is not None and cancel.is_set():
                    stop_probe(process)
                    return 'unknown', {'reason': 'observation cancelled; work unchanged'}
                seconds = until - time.monotonic()
                if seconds <= 0:
                    stop_probe(process)
                    return 'unknown', {'reason': 'read-only probe timed out; work state is unknown'}
                try:
                    stdout, stderr = process.communicate(timeout=min(.25, seconds))
                    break
                except subprocess.TimeoutExpired:
                    continue
        except BaseException:
            stop_probe(process)
            raise
        if process.returncode:
            return 'unknown', {'reason': 'probe exited nonzero', 'exit_code': process.returncode,
                               'stderr': stderr[-2000:]}
        body = json.loads(stdout)
        if not isinstance(body, dict):
            raise ValueError('probe output is not an object')
        return classify(body), body
    except subprocess.TimeoutExpired:
        return 'unknown', {'reason': 'read-only probe timed out; work state is unknown'}
    except (OSError, ValueError) as exc:
        return 'unknown', {'reason': 'probe failed', 'error_type': type(exc).__name__}


def submit(folder):
    with transaction(folder) as state:
        check_owner(state)
        if state.get('stopped') or state.get('wake') or not pending(state):
            return
        wake_id = str(uuid.uuid4())
        state['wake'] = {'id': wake_id, 'status': 'attempting', 'created': time.time()}
        binary, thread = state['codex'], state['thread']
    command = shlex.join([sys.executable, str(Path(__file__).resolve()), 'drain', '--state-dir', str(folder)])
    message = (f'[fix-wait {wake_id}] Saved observation events for this session at {folder}. '
               f'Run {command}. Read and handle all returned events, then acknowledge them with '
               'rearm using the returned generation, wake ID and event IDs. Resume only explicitly '
               'resolved blocked jobs. Verify artifacts before accepting results. Honor newer '
               'pause/stop instructions; continue only previously authorized work. Never restart '
               'the observed task, repeat its submission, or message another session because of this event. '
               'If this wake ID differs from the current state, this is a stale notice; read current state.')
    try:
        result = subprocess.run([binary, 'queue', '--thread', thread, '--message', message],
                                capture_output=True, text=True, timeout=20)
        delivery = {'status': 'queued' if result.returncode == 0 else 'delivery_unknown',
                    'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    except (subprocess.TimeoutExpired, OSError) as exc:
        delivery = {'status': 'delivery_unknown', 'error_type': type(exc).__name__}
    with transaction(folder) as state:
        # DM may already have consumed this wake while the subprocess returned.
        state['deliveries'].setdefault(wake_id, {}).update(delivery)
        if (state.get('wake') or {}).get('id') == wake_id:
            state['wake'].update(delivery)


def daemon(folder):
    with (folder/'daemon.lock').open('a') as lock:
        # A replacement may race an old daemon's final unlock. Wait briefly for that
        # handoff; if the old daemon stays active it owns the newly persisted generation.
        lock_deadline = time.monotonic() + 2
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= lock_deadline:
                    return
                time.sleep(0.05)
        futures = {}
        cancellation = threading.Event()
        with ThreadPoolExecutor(max_workers=8) as pool:
            while True:
                now = time.time()
                with transaction(folder) as state:
                    check_owner(state)
                    state['daemon_pid'] = os.getpid()
                    state['daemon_seen'] = now
                    stopped = state.get('stopped', False)
                    if stopped:
                        cancellation.set()
                    elif cancellation.is_set():
                        cancellation = threading.Event()
                    generation = state['generation']
                    # Completed read-only probes remain facts even if their original window expired.
                    for job_id, future in list(futures.items()):
                        if not future.done():
                            continue
                        try:
                            status, body = future.result()
                        except Exception as exc:
                            status, body = 'blocked', {'reason': 'observer exception', 'error_type': type(exc).__name__}
                        del futures[job_id]
                        job = state['jobs'][job_id]
                        job['last'] = body
                        job['observed'] = now
                        job['due'] = now + job['spec'].get('interval_seconds', 30)
                        if stopped or job['status'] != 'running':
                            continue
                        if body.get('reason') == 'observation cancelled; work unchanged':
                            job['due'] = now
                            continue
                        if status == 'unknown':
                            job['errors'] = job.get('errors', 0) + 1
                            job['due'] = now + min(120, 5 * 2 ** min(job['errors'], 5))
                            if job['errors'] < 3:
                                continue
                            status = 'blocked'
                        else:
                            job['errors'] = 0
                        if status != 'running':
                            job['status'] = status
                            kind = {'complete': 'COMPLETE', 'failed': 'FAILED', 'blocked': 'BLOCKED'}[status]
                            key = json.dumps([job_id, status, job.get("attempt", 0)])
                            event(state, key, kind, {'job_id': job_id, 'status': status, 'facts': body})
                    active = [key for key, value in state['jobs'].items() if value['status'] == 'running']
                    remaining = state['deadline'] - now
                    if not stopped and active and remaining <= 0:
                        # If another meaningful event is already pending, it also covers this checkpoint.
                        if not pending(state):
                            event(state, f'checkpoint:{generation}', 'CHECKPOINT', {'generation': generation, 'jobs': active})
                    if not stopped:
                        for job_id in active:
                            job = state['jobs'][job_id]
                            if job_id not in futures and job['due'] <= now:
                                # A checkpoint bounds notification, not observation. After it,
                                # each probe still gets its own bounded timeout budget.
                                budget = remaining if remaining > 0 else job['spec'].get('probe_timeout_seconds', 20)
                                futures[job_id] = pool.submit(probe, job['spec'], budget, cancellation)
                    finish = not futures and (stopped or not active)
                submit(folder)
                if finish:
                    # Hold state lock through the decision; rearm starts a replacement after lock release.
                    with transaction(folder) as state:
                        if state['generation'] != generation and not state.get('stopped'):
                            continue
                        state['daemon_seen'] = time.time()
                    return
                time.sleep(0.25)


def spawn(folder):
    with (folder/'daemon.log').open('ab') as log:
        child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '_run', '--state-dir', str(folder)],
                                 stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                 start_new_session=True, close_fds=True)
    return child.pid


def arm(folder, request, binary, window):
    validate_window(window)
    thread = owner()
    if not isinstance(request, dict) or set(request) != {'jobs'}:
        raise ValueError('request must contain only jobs; use --window for the session window')
    if not isinstance(request.get('jobs'), list) or not request['jobs'] or len(request['jobs']) > 8:
        raise ValueError('request must explicitly name 1..8 independent read-only probes')
    for job in request['jobs']:
        validate_job(job)
    if len({job['id'] for job in request['jobs']}) != len(request['jobs']):
        raise ValueError('duplicate job IDs')
    binary = str(Path(binary).resolve())
    support = subprocess.run([binary, 'queue', '--help'], capture_output=True, text=True, timeout=10)
    if support.returncode or '--thread' not in support.stdout or '--message' not in support.stdout:
        raise ValueError('Codex queue is not available')
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    with transaction(folder) as state:
        if state:
            check_owner(state)
            if state['codex'] != binary:
                raise ValueError('existing session is bound to a different Codex executable')
            if state.get('stopped') or state.get('wake') or pending(state):
                raise ValueError('drain and rearm the existing state before adding observations')
            active_ids = {key for key, job in state['jobs'].items() if job['status'] == 'running'}
            new_ids = {job['id'] for job in request['jobs']} - set(state['jobs'])
            if len(active_ids | new_ids) > 8:
                raise ValueError('at most 8 active probes per session')
            for job in request['jobs']:
                if job['id'] in state['jobs'] and state['jobs'][job['id']]['spec'] != job:
                    raise ValueError('existing job identity cannot be changed')
        else:
            state.update(schema_version=SCHEMA_VERSION, thread=thread, codex=binary, generation=0, deadline=0, jobs={},
                         events={}, deliveries={}, wake=None, stopped=False)
        if not any(job['status'] == 'running' for job in state['jobs'].values()):
            state['generation'] += 1
            state['deadline'] = time.time() + window - min(25, window / 5)
        for job in request['jobs']:
            state['jobs'].setdefault(job['id'], {'spec': job, 'status': 'running', 'due': 0, 'errors': 0})
    return {'status': 'registered', 'pid': spawn(folder), 'state_dir': str(folder),
            'note': 'registration is not handle adoption; drain exposes first observed facts'}


def drain(folder):
    with transaction(folder) as state:
        check_owner(state)
        items = pending(state)
        if items and not state.get('wake'):
            # Manual recovery after a crash between event persistence and queue claim.
            # The owning DM is reading now, so no additional wake is necessary.
            state['wake'] = {'id': str(uuid.uuid4()), 'status': 'read_locally', 'created': time.time()}
        if state.get('wake'):
            state['wake']['exposed_ids'] = list(dict.fromkeys(state['wake'].get('exposed_ids', []) + [x['id'] for x in items]))
        return {'generation': state['generation'], 'wake_id': (state.get('wake') or {}).get('id'),
                'events': items, 'jobs': state['jobs'], 'delivery': state.get('wake'),
                'stopped': state.get('stopped')}


def rearm(folder, generation, wake_id, event_ids, window, resume_jobs=()):
    validate_window(window)
    with transaction(folder) as state:
        check_owner(state)
        if generation != state['generation']:
            raise ValueError('stale generation; do not repeat rearm')
        wake = state.get('wake')
        if not wake and not state.get('stopped'):
            raise ValueError('drain pending events before rearm, or explicitly resume stopped observation')
        if wake_id != (wake or {}).get('id'):
            raise ValueError('wake identity does not match')
        if wake and 'exposed_ids' not in wake:
            raise ValueError('events must be returned by drain before rearm')
        if set(event_ids) - set((wake or {}).get('exposed_ids', [])):
            raise ValueError('consume only events returned by drain for this wake')
        if wake and not set((wake or {}).get('exposed_ids', [])) <= set(event_ids):
            raise ValueError('handle all drained events before rearm')
        if any(key not in state['jobs'] or state['jobs'][key]['status'] != 'blocked' for key in resume_jobs):
            raise ValueError('resume only an explicitly selected blocked observation')
        active_ids = {key for key, job in state['jobs'].items() if job['status'] == 'running'}
        if len(active_ids | set(resume_jobs)) > 8:
            raise ValueError('at most 8 active probes per session')
        for event_id in event_ids:
            state['events'][event_id]['consumed'] = True
        if wake:
            state['deliveries'].setdefault(wake['id'], {}).update(consumed=time.time())
        state['wake'] = None
        for key in resume_jobs:
            job = state['jobs'][key]
            job.update(status='running', errors=0, due=0, attempt=job.get('attempt', 0)+1)
        state['stopped'] = False
        state['generation'] += 1
        state['deadline'] = time.time() + window - min(25, window / 5)
        generation = state['generation']
    return {'generation': generation, 'pid': spawn(folder), 'window_seconds': window}


def status(folder):
    with transaction(folder) as state:
        check_owner(state)
        return state.copy()


def stop(folder):
    with transaction(folder) as state:
        check_owner(state)
        state['stopped'] = True
    return {'status': 'observation_stop_requested', 'work_unchanged': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('start', 'arm', 'status', 'drain', 'rearm', 'stop', '_run'))
    parser.add_argument('--state-dir', type=Path)
    parser.add_argument('--request', type=Path)
    parser.add_argument('--codex', default=shutil.which('codex'))
    parser.add_argument('--window', type=float, default=WINDOW)
    parser.add_argument('--generation', type=int)
    parser.add_argument('--wake-id')
    parser.add_argument('--event-ids', nargs='*', default=[])
    parser.add_argument('--resume-jobs', nargs='*', default=[])
    args = parser.parse_args()
    validate_window(args.window)
    folder = (args.state_dir or Path.home()/'.local/state/codex-wait'/owner()).resolve()
    if args.action in ('start', 'arm'):
        if not args.request or not args.codex:
            parser.error('start requires --request and an available Codex executable')
        result = arm(folder, json.loads(args.request.read_text()), args.codex, args.window)
    elif args.action == 'status':
        result = status(folder)
    elif args.action == 'drain':
        result = drain(folder)
    elif args.action == 'rearm':
        if args.generation is None:
            parser.error('rearm requires --generation from drain')
        result = rearm(folder, args.generation, args.wake_id, args.event_ids, args.window, args.resume_jobs)
    elif args.action == 'stop':
        result = stop(folder)
    else:
        daemon(folder)
        return
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        raise SystemExit(f'fix-wait: {exc}')
