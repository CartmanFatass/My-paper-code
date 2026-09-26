"""Detached, model-free observation and one pending Codex wake per owning session.

Trusted requests contain read-only probe argv arrays and one of two protocols:
launch (hmasd_launch status JSON) or pro (jev_send wait JSON). A probe is never a
launcher or Send. The Pro argv must supply --timeout {window_seconds}.
Only Codex on POSIX is supported; this is not a Claude messaging adapter.
"""
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
import signal
import threading
import subprocess
import sys
import time
import uuid

WINDOW = 1500
ROOT = Path(__file__).resolve().parents[1]


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
    return value


def check_owner(state):
    if state.get('thread') != owner():
        raise ValueError('wait state belongs to a different Codex session')


def validate_job(job):
    if not isinstance(job, dict) or not isinstance(job.get('id'), str) or not job['id']:
        raise ValueError('job needs a stable nonempty id')
    argv = job.get('argv')
    if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or '\0' in x for x in argv):
        raise ValueError('probe argv must be a nonempty string array')
    if not Path(argv[0]).is_absolute() or not Path(argv[0]).is_file():
        raise ValueError('probe requires an existing absolute executable')
    if not Path(job.get('cwd', '')).is_absolute() or not Path(job['cwd']).is_dir():
        raise ValueError('probe cwd must be an existing absolute directory')
    if job.get('protocol') not in ('launch', 'pro'):
        raise ValueError('protocol must be launch or pro')
    if job['protocol'] == 'pro' and not any(
        argv[i:i+2] == ['--timeout', '{window_seconds}'] for i in range(len(argv)-1)
    ):
        raise ValueError('Pro observation requires --timeout {window_seconds}')
    if type(job.get('interval', 30)) not in (int, float) or not math.isfinite(job.get('interval', 30)) or not 1 <= job.get('interval', 30) <= 300:
        raise ValueError('probe interval must be 1..300 seconds')
    if type(job.get('timeout', 20)) not in (int, float) or not math.isfinite(job.get('timeout', 20)) or not 1 <= job.get('timeout', 20) <= 60:
        raise ValueError('launch probe timeout must be 1..60 seconds')


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


def classify(protocol, body):
    if protocol == 'launch':
        status = body.get('execution', {}).get('state')
        if status == 'running':
            return 'running'
        if status == 'exited':
            witness = body['execution'].get('exit_witness', {})
            if witness.get('state') != 'valid' or body.get('record_consistency', {}).get('state') != 'consistent':
                return 'unknown'
            code = body['execution'].get('exit_code')
            if isinstance(code, bool) or not isinstance(code, int):
                return 'unknown'
            return 'ready' if code == 0 else 'failed'
        return 'unknown'
    status = body.get('state')
    if status == 'IN_PROGRESS':
        return 'running'
    if status == 'COMPLETE':
        answer = body.get('answer_file')
        if not answer or not Path(answer).is_absolute() or not Path(answer).is_file():
            return 'blocked'
        # Collection is not delivery verification; the wake explicitly tells the DM to deliver/read.
        return 'collected'
    return 'blocked' if status in ('NEEDS_HUMAN', 'ERROR') else 'unknown'


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
    observation = max(0.1, remaining - 8)
    argv = [x.replace('{window_seconds}', str(observation)) for x in job['argv']]
    timeout = max(0.1, min(remaining, observation + 5 if job['protocol'] == 'pro' else job.get('timeout', 20)))
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
        return classify(job['protocol'], body), body
    except subprocess.TimeoutExpired:
        return 'unknown', {'reason': 'read-only probe timed out; work state is unknown'}
    except (OSError, ValueError) as exc:
        return 'unknown', {'reason': 'probe failed', 'error_type': type(exc).__name__}


def submit(folder):
    with transaction(folder) as state:
        if state.get('stopped') or state.get('wake') or not pending(state):
            return
        wake_id = str(uuid.uuid4())
        state['wake'] = {'id': wake_id, 'status': 'attempting', 'created': time.time()}
        binary, thread = state['codex'], state['thread']
    # No private question URL or model-generated instructions in the message.
    message = (f'[hmasd-wait {wake_id}] Saved observation events for this task at {folder}. '
               f'Run {sys.executable} {Path(__file__).resolve()} drain --state-dir {folder}. '
               'Read all pending evidence. Process exit is not scientific acceptance; Pro collected '
               'text still requires deliver verification and reading the full answer. Apply newer '
               'owner stop/pause instructions. Continue only previously authorized work. Rearm the '
               'remaining observations using the returned generation, wake ID and event IDs; never '
               'restart a worker, resend a Pro question, or message another task because of this event.')
    try:
        result = subprocess.run([binary, 'queue', '--thread', thread, '--message', message],
                                capture_output=True, text=True, timeout=20)
        delivery = {'status': 'queued' if result.returncode == 0 else 'delivery_unknown',
                    'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    except subprocess.TimeoutExpired as exc:
        delivery = {'status': 'delivery_unknown', 'error_type': type(exc).__name__}
    except OSError as exc:
        delivery = {'status': 'delivery_unknown', 'error_type': type(exc).__name__,
                    'executable': binary, 'errno': exc.errno, 'error': str(exc)}
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
                        job['due'] = now + job['spec'].get('interval', 30)
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
                            kind = 'READY' if status in ('ready', 'collected') else 'BLOCKED'
                            key = f'{job_id}:{status}:{job.get("attempt", 0)}'
                            event(state, key, kind, {'job_id': job_id, 'status': status, 'facts': body})
                    active = [key for key, value in state['jobs'].items() if value['status'] == 'running']
                    remaining = state['deadline'] - now
                    if not stopped and active and remaining <= 0 and not futures:
                        # If another meaningful event is already pending, it also covers this checkpoint.
                        if not pending(state):
                            event(state, f'checkpoint:{generation}', 'CHECKPOINT', {'generation': generation, 'jobs': active})
                    if not stopped and remaining > 1:
                        for job_id in active:
                            job = state['jobs'][job_id]
                            if job_id not in futures and job['due'] <= now:
                                futures[job_id] = pool.submit(probe, job['spec'], remaining, cancellation)
                    finish = not futures and (stopped or not active or remaining <= 0)
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


def validate_codex(binary):
    binary = str(Path(binary).resolve())
    support = subprocess.run([binary, 'queue', '--help'], capture_output=True, text=True, timeout=10)
    if support.returncode or '--thread' not in support.stdout or '--message' not in support.stdout:
        raise ValueError('Codex queue is not available')
    return binary


def arm(folder, request, binary, window):
    thread = owner()
    if not isinstance(request.get('jobs'), list) or not request['jobs'] or len(request['jobs']) > 8:
        raise ValueError('request must explicitly name 1..8 independent read-only probes')
    if len({job.get('id') for job in request['jobs']}) != len(request['jobs']):
        raise ValueError('duplicate job IDs')
    for job in request['jobs']:
        validate_job(job)
    binary = validate_codex(binary)
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    with transaction(folder) as state:
        if state:
            check_owner(state)
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
            state.update(thread=thread, codex=binary, generation=0, deadline=0, jobs={},
                         events={}, deliveries={}, wake=None, stopped=False)
        state['codex'] = binary
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


def rearm(folder, generation, wake_id, event_ids, window, resume_jobs=(), binary=None):
    with transaction(folder) as state:
        check_owner(state)
        if generation != state['generation']:
            raise ValueError('stale generation; do not repeat rearm')
        wake = state.get('wake')
        if wake_id != (wake or {}).get('id'):
            raise ValueError('wake identity does not match')
        if set(event_ids) - set((wake or {}).get('exposed_ids', [])):
            raise ValueError('consume only events returned by drain for this wake')
        if wake and not set((wake or {}).get('exposed_ids', [])) <= set(event_ids):
            raise ValueError('handle all drained events before rearm')
        if any(key not in state['jobs'] or state['jobs'][key]['status'] != 'blocked' for key in resume_jobs):
            raise ValueError('resume only an explicitly selected blocked observation')
        active_ids = {key for key, job in state['jobs'].items() if job['status'] == 'running'}
        if len(active_ids | set(resume_jobs)) > 8:
            raise ValueError('at most 8 active probes per session')
        if binary is not None:
            binary = validate_codex(binary)
            state['codex'] = binary
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('arm', 'drain', 'rearm', 'stop', '_run'))
    parser.add_argument('--state-dir', type=Path)
    parser.add_argument('--request', type=Path)
    parser.add_argument('--codex')
    parser.add_argument('--window', type=float, default=WINDOW)
    parser.add_argument('--generation', type=int)
    parser.add_argument('--wake-id')
    parser.add_argument('--event-ids', nargs='*', default=[])
    parser.add_argument('--resume-jobs', nargs='*', default=[])
    args = parser.parse_args()
    if not math.isfinite(args.window) or not 0 < args.window <= WINDOW:
        parser.error('window must be in (0, 1500] seconds')
    folder = (args.state_dir or Path.home()/'.local/state/hmasd-wait'/owner()).resolve()
    if args.action == 'arm':
        binary = args.codex or shutil.which('codex')
        if not args.request or not binary:
            parser.error('arm requires --request and an available Codex executable')
        result = arm(folder, json.loads(args.request.read_text()), binary, args.window)
    elif args.action == 'drain':
        result = drain(folder)
    elif args.action == 'rearm':
        result = rearm(folder, args.generation, args.wake_id, args.event_ids, args.window,
                       args.resume_jobs, args.codex or shutil.which('codex'))
    elif args.action == 'stop':
        with transaction(folder) as state:
            check_owner(state)
            state['stopped'] = True
        result = {'status': 'observation_stop_requested', 'work_unchanged': True}
    else:
        daemon(folder)
        return
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
