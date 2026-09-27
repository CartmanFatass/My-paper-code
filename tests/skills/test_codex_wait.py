"""Protocol and delivery tests; no browser model, actual queue message or research work."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('codex_wait', ROOT/'tools/codex_wait.py')
wait = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wait)


def launch_body(code=0):
    return {'state': 'complete' if code == 0 else 'failed', 'exit_code': code}


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setenv('CODEX_THREAD_ID', str(uuid.uuid4()))
    folder = tmp_path/'state'
    binary = tmp_path/'codex'
    calls = tmp_path/'calls'
    binary.write_text(f'''#!{sys.executable}
import sys
from pathlib import Path
if '--help' in sys.argv:
 print('--thread --message')
else:
 with Path({str(calls)!r}).open('a') as out: out.write('queued\\n')
 print('queued test message')
''')
    binary.chmod(0o700)
    job = {'id': 'one', 'argv': [sys.executable, '-c', 'print("{}")'],
           'cwd': str(tmp_path), 'interval_seconds': 1}
    monkeypatch.setattr(wait, 'spawn', lambda folder: 0)
    wait.arm(folder, {'jobs': [job]}, str(binary), 1500)
    return folder, binary, calls, job


def test_generic_state_protocol_rejects_project_specific_shapes():
    for state in ('running', 'complete', 'failed', 'blocked', 'unknown'):
        assert wait.classify({'state': state}) == state
    for body in ({'execution': {'state': 'exited'}}, {'state': 'COMPLETE'}, [], {'state': True}):
        with pytest.raises(ValueError):
            wait.classify(body)


def test_coalesce_duplicate_and_racing_events(setup):
    folder, _binary, calls, _job = setup
    with wait.transaction(folder) as state:
        first = wait.event(state, 'one:done', 'COMPLETE', {'job': 'one'})
        assert wait.event(state, 'one:done', 'COMPLETE', {}) == first
        wait.event(state, 'two:done', 'BLOCKED', {'job': 'two'})
    wait.submit(folder); wait.submit(folder)
    seen = wait.drain(folder)
    assert len(seen['events']) == 2
    assert calls.read_text().splitlines() == ['queued']
    with wait.transaction(folder) as state:
        late = wait.event(state, 'three:done', 'COMPLETE', {'job': 'three'})
    wait.submit(folder)
    assert len(calls.read_text().splitlines()) == 1
    wait.rearm(folder, seen['generation'], seen['wake_id'], [e['id'] for e in seen['events']], 1500)
    wait.submit(folder)
    assert [e['id'] for e in wait.drain(folder)['events']] == [late]
    assert len(calls.read_text().splitlines()) == 2
    with pytest.raises(ValueError, match='stale'):
        wait.rearm(folder, seen['generation'], seen['wake_id'], [], 1500)


def test_uncertain_send_claim_survives_and_never_retries(setup, monkeypatch):
    folder, _binary, _calls, _job = setup
    with wait.transaction(folder) as state:
        wait.event(state, 'done', 'COMPLETE', {})
    sent = []
    def timeout(*args, **kwargs):
        sent.append(args)
        raise subprocess.TimeoutExpired(args[0], 20)
    monkeypatch.setattr(wait.subprocess, 'run', timeout)
    wait.submit(folder); wait.submit(folder)
    result = wait.drain(folder)
    assert result['delivery']['status'] == 'delivery_unknown'
    assert len(sent) == 1
    # Crash after claim and before calling queue is also unknown; never blind retry.
    with wait.transaction(folder) as state:
        state['wake']['status'] = 'attempting'
    wait.submit(folder)
    assert len(sent) == 1


def test_unknown_handle_retries_are_bounded_then_report_blocker(setup, monkeypatch):
    folder, _binary, _calls, _job = setup
    with wait.transaction(folder) as state:
        state['jobs']['one']['errors'] = 2
    monkeypatch.setattr(wait, 'probe', lambda job, remaining, cancel=None: ('unknown', {'reason': 'SSH unavailable'}))
    wait.daemon(folder)
    seen = wait.drain(folder)
    assert len(seen['events']) == 1
    assert seen['events'][0]['kind'] == 'BLOCKED'
    assert seen['jobs']['one']['status'] == 'blocked'


def test_expired_checkpoint_does_not_execute_probe_and_rearm_preserves_job(setup, monkeypatch):
    folder, _binary, _calls, job = setup
    with wait.transaction(folder) as state:
        state['deadline'] = 0
    monkeypatch.setattr(wait, 'probe', lambda *_: pytest.fail('expired window ran probe'))
    wait.daemon(folder)
    seen = wait.drain(folder)
    assert [e['kind'] for e in seen['events']] == ['CHECKPOINT']
    wait.rearm(folder, seen['generation'], seen['wake_id'], [e['id'] for e in seen['events']], 1500)
    with wait.transaction(folder) as state:
        assert 1470 < state['deadline']-time.time() <= 1475
        assert state['jobs']['one']['spec'] == job


def test_stopped_watch_has_no_notifications_and_foreign_session_refused(setup, monkeypatch):
    folder, _binary, calls, _job = setup
    with wait.transaction(folder) as state:
        state['stopped'] = True
        wait.event(state, 'x', 'COMPLETE', {})
    wait.submit(folder)
    assert not calls.exists()
    monkeypatch.setenv('CODEX_THREAD_ID', str(uuid.uuid4()))
    with pytest.raises(ValueError, match='different'):
        wait.drain(folder)


def test_daemon_process_saves_terminal_and_one_wake(setup, tmp_path):
    folder, _binary, calls, job = setup
    body = launch_body(7)
    job['argv'] = [sys.executable, '-c', f'import json; print(json.dumps({body!r}))']
    with wait.transaction(folder) as state:
        state['jobs']['one']['spec'] = job
    child = subprocess.Popen([sys.executable, str(ROOT/'tools/codex_wait.py'), '_run', '--state-dir', str(folder)],
                             stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        out, err = child.communicate(timeout=10)
    finally:
        if child.poll() is None:
            child.kill(); child.wait()
    assert child.returncode == 0, err.decode()
    assert len(calls.read_text().splitlines()) == 1
    seen = wait.drain(folder)
    assert seen['events'][0]['kind'] == 'FAILED'
    assert seen['events'][0]['evidence']['facts']['exit_code'] == 7


def test_read_probe_timeout_and_invalid_json_stay_unknown(setup):
    _folder, _binary, _calls, job = setup
    job['argv'] = [sys.executable, '-c', 'import time; time.sleep(2)']
    assert wait.probe(job, .1)[0] == 'unknown'
    job['argv'] = [sys.executable, '-c', 'print("no JSON")']
    assert wait.probe(job, 2)[0] == 'unknown'


def test_rearm_cannot_consume_unseen_events_or_change_job_identity(setup):
    folder, binary, _calls, job = setup
    with wait.transaction(folder) as state:
        event_id = wait.event(state, 'x', 'COMPLETE', {})
    wait.submit(folder)
    raw = json.loads((folder/'state.json').read_text())
    with pytest.raises(ValueError, match='returned by drain'):
        wait.rearm(folder, raw['generation'], raw['wake']['id'], [event_id], 1500)
    changed = dict(job, argv=[sys.executable, '-c', 'print(2)'])
    with pytest.raises(ValueError):
        wait.arm(folder, {'jobs': [changed]}, str(binary), 1500)


def test_additions_cannot_exceed_session_pool_bound(setup):
    folder, binary, _calls, job = setup
    jobs = [dict(job, id=str(i)) for i in range(7)]
    wait.arm(folder, {'jobs': jobs}, str(binary), 1500)
    with pytest.raises(ValueError, match='at most 8'):
        wait.arm(folder, {'jobs': [dict(job, id='ninth')]}, str(binary), 1500)


@pytest.mark.parametrize('field,value', [('interval_seconds', '30'), ('probe_timeout_seconds', '20'), ('probe_timeout_seconds', True), ('interval_seconds', float('nan'))])
def test_invalid_numeric_types_rejected_before_detach(setup, field, value):
    _folder, _binary, _calls, job = setup
    with pytest.raises(ValueError):
        wait.validate_job(dict(job, **{field: value}))


def test_cancellation_stops_only_owned_read_probe(setup, tmp_path):
    import threading
    from concurrent.futures import ThreadPoolExecutor
    folder, _binary, _calls, job = setup
    pid_file = tmp_path/'probe.pid'
    marker = tmp_path/'probe.closed'
    code = ('import os,signal,time; from pathlib import Path; '
            f'Path({str(pid_file)!r}).write_text(str(os.getpid())); '
            f'signal.signal(signal.SIGTERM, lambda *_: (Path({str(marker)!r}).write_text("closed"), exit(0))); '
            'time.sleep(30)')
    job['argv'] = [sys.executable, '-c', code]
    cancel = threading.Event()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(wait.probe, job, 30, cancel)
        deadline = time.monotonic()+5
        while not pid_file.exists() and time.monotonic()<deadline:
            time.sleep(.01)
        assert pid_file.exists()
        cancel.set()
        status, body = future.result(timeout=5)
    assert status == 'unknown' and 'cancelled' in body['reason']
    assert marker.read_text() == 'closed'


def test_resuming_blockers_cannot_exceed_session_pool_bound(setup):
    folder, _binary, _calls, job = setup
    with wait.transaction(folder) as state:
        state['jobs'].update({str(i): {'spec': dict(job, id=str(i)), 'status': 'running', 'due': 0} for i in range(7)})
        state['jobs']['blocked'] = {'spec': dict(job, id='blocked'), 'status': 'blocked', 'due': 0}
    wait.stop(folder)
    seen = wait.drain(folder)
    with pytest.raises(ValueError, match='at most 8'):
        wait.rearm(folder, seen['generation'], None, [], 1500, ['blocked'])


def test_stop_then_immediate_rearm_replaces_cancellation_without_false_failure(setup, monkeypatch):
    import threading
    folder, _binary, _calls, _job = setup
    started, cancelled, release = threading.Event(), threading.Event(), threading.Event()
    calls = []
    def fake_probe(job, remaining, cancel):
        calls.append(cancel)
        if len(calls) == 1:
            started.set()
            assert cancel.wait(4)
            cancelled.set()
            assert release.wait(4)
            return 'unknown', {'reason': 'observation cancelled; work unchanged'}
        assert not cancel.is_set()
        return 'complete', launch_body()
    monkeypatch.setattr(wait, 'probe', fake_probe)
    thread = threading.Thread(target=wait.daemon, args=(folder,))
    thread.start()
    try:
        assert started.wait(3)
        with wait.transaction(folder) as state:
            state['stopped'] = True
        assert cancelled.wait(3)
        seen = wait.drain(folder)
        wait.rearm(folder, seen['generation'], None, [], 1500)
        release.set()
        thread.join(timeout=5)
        assert not thread.is_alive()
        seen = wait.drain(folder)
        assert seen['jobs']['one']['status'] == 'complete'
        assert [e['kind'] for e in seen['events']] == ['COMPLETE']
        assert len(calls) == 2 and calls[0] is not calls[1]
    finally:
        release.set()
        with wait.transaction(folder) as state:
            state['stopped'] = True
        thread.join(timeout=5)


def test_manual_recovery_of_event_persisted_before_queue_claim(setup):
    folder, _binary, calls, _job = setup
    with wait.transaction(folder) as state:
        event_id = wait.event(state, 'persisted-before-crash', 'COMPLETE', {})
    seen = wait.drain(folder)
    assert seen['wake_id'] and seen['delivery']['status'] == 'read_locally'
    wait.submit(folder)
    assert not calls.exists()
    wait.rearm(folder, seen['generation'], seen['wake_id'], [event_id], 1500)
    assert wait.drain(folder)['events'] == []


def test_eight_probes_run_in_parallel_and_share_one_notice(setup, monkeypatch):
    import threading
    folder, binary, calls, job = setup
    jobs = [dict(job, id=f'parallel-{i}') for i in range(7)]
    wait.arm(folder, {'jobs': jobs}, str(binary), 1500)
    barrier = threading.Barrier(8)
    def parallel_probe(spec, remaining, cancel):
        barrier.wait(timeout=5)
        return 'complete', {'state': 'complete', 'job': spec['id']}
    monkeypatch.setattr(wait, 'probe', parallel_probe)
    wait.daemon(folder)
    seen = wait.drain(folder)
    assert len(seen['events']) == 8
    assert all(event['kind'] == 'COMPLETE' for event in seen['events'])
    assert len(calls.read_text().splitlines()) == 1


def test_status_does_not_mark_events_read_and_incomplete_ack_is_rejected(setup):
    folder, _, _, _ = setup
    with wait.transaction(folder) as state:
        first = wait.event(state, 'first', 'COMPLETE', {})
        second = wait.event(state, 'second', 'BLOCKED', {})
    wait.submit(folder)
    raw = wait.status(folder)
    with pytest.raises(ValueError, match='returned by drain'):
        wait.rearm(folder, raw['generation'], raw['wake']['id'], [first, second], 1500)
    seen = wait.drain(folder)
    with pytest.raises(ValueError, match='all drained'):
        wait.rearm(folder, seen['generation'], seen['wake_id'], [first], 1500)
    with pytest.raises(ValueError, match='wake identity'):
        wait.rearm(folder, seen['generation'], 'wrong-wake', [first, second], 1500)
    assert len(wait.drain(folder)['events']) == 2


@pytest.mark.parametrize('delivery', ['queued', 'delivery_unknown', 'attempting'])
def test_empty_ack_without_drain_cannot_clear_or_resend_wake(setup, delivery):
    folder, _, calls, _ = setup
    with wait.transaction(folder) as state:
        wait.event(state, 'unread', 'COMPLETE', {})
    wait.submit(folder)
    with wait.transaction(folder) as state:
        state['wake']['status'] = delivery
    before = wait.status(folder)
    with pytest.raises(ValueError, match='returned by drain'):
        wait.rearm(folder, before['generation'], before['wake']['id'], [], 1500)
    assert wait.status(folder) == before
    wait.submit(folder)
    assert calls.read_text().splitlines() == ['queued']
    seen = wait.drain(folder)
    wait.rearm(folder, seen['generation'], seen['wake_id'], [e['id'] for e in seen['events']], 1500)
    assert wait.drain(folder)['events'] == []


def test_only_selected_blocked_job_resumes_and_terminal_task_stays_terminal(setup):
    folder, _, _, job = setup
    with wait.transaction(folder) as state:
        state['jobs']['one']['status'] = 'complete'
        for key in ('blocked-a', 'blocked-b'):
            state['jobs'][key] = {'spec': dict(job, id=key), 'status': 'blocked', 'due': 0}
            wait.event(state, key, 'BLOCKED', {'job_id': key})
    seen = wait.drain(folder)
    ids = [event['id'] for event in seen['events']]
    with pytest.raises(ValueError, match='blocked observation'):
        wait.rearm(folder, seen['generation'], seen['wake_id'], ids, 1500, ['one'])
    wait.rearm(folder, seen['generation'], seen['wake_id'], ids, 1500, ['blocked-a'])
    jobs = wait.status(folder)['jobs']
    assert jobs['one']['status'] == 'complete'
    assert jobs['blocked-a']['status'] == 'running'
    assert jobs['blocked-b']['status'] == 'blocked'


def test_repeated_registration_is_idempotent_and_job_identity_is_immutable(setup):
    folder, binary, _, job = setup
    before = wait.status(folder)
    wait.arm(folder, {'jobs': [job]}, str(binary), 1500)
    after = wait.status(folder)
    assert before == after
    with pytest.raises(ValueError, match='identity cannot be changed'):
        wait.arm(folder, {'jobs': [dict(job, argv=[sys.executable, '-c', 'print(2)'])]}, str(binary), 1500)


def test_window_placeholder_and_old_state_rejection(setup):
    folder, _, _, job = setup
    job = dict(job, argv=[sys.executable, '-c',
                         'import json,sys; print(json.dumps({"state":"running","budget":float(sys.argv[1])}))',
                         '{window_seconds}'])
    status, body = wait.probe(job, 2)
    assert status == 'running' and 0 < body['budget'] < 2
    with wait.transaction(folder) as state:
        del state['schema_version']
    with pytest.raises(ValueError, match='incompatible state'):
        wait.status(folder)


def test_invalid_window_and_request_never_spawn(setup, monkeypatch):
    folder, binary, _, job = setup
    monkeypatch.setattr(wait, 'spawn', lambda *_: pytest.fail('invalid request spawned'))
    for window in (0, -1, True, float('nan'), float('inf'), 86401):
        with pytest.raises(ValueError):
            wait.arm(folder, {'jobs': [job]}, str(binary), window)
    for request in ({}, {'argv': []}, {'jobs': [job, job]}, {'jobs': [None]}):
        with pytest.raises(ValueError):
            wait.arm(folder, request, str(binary), 1500)


def test_real_cli_start_drain_ack_flow_uses_only_fake_queue(setup, tmp_path):
    folder, binary, calls, job = setup
    folder = tmp_path / 'cli-state'
    request_path = tmp_path / 'request.json'
    job = dict(job, argv=[sys.executable, '-c', 'print(\'{"state":"complete"}\')'])
    request_path.write_text(json.dumps({'jobs': [job]}))
    def cli(action, *args):
        result = subprocess.run([sys.executable, str(ROOT/'tools/codex_wait.py'), action,
                                 '--state-dir', str(folder), *args],
                                capture_output=True, text=True, timeout=5)
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)
    daemons = {cli('start', '--request', str(request_path), '--codex', str(binary), '--window', '3')['pid']}
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            current = json.loads((folder/'state.json').read_text())
            if (current.get('wake') or {}).get('status') == 'queued':
                break
            time.sleep(.02)
        else:
            pytest.fail('CLI observer did not queue its result')
        seen = cli('drain')
        assert [event['kind'] for event in seen['events']] == ['COMPLETE']
        daemons.add(cli('rearm', '--generation', str(seen['generation']), '--wake-id', seen['wake_id'],
            '--event-ids', *[event['id'] for event in seen['events']])['pid'])
        assert cli('drain')['events'] == []
        assert len(calls.read_text().splitlines()) == 1
    finally:
        cli('stop')
        # CLI-launched observers are grandchildren, so Popen.wait cannot reap them.
        # A zombie has already exited and released files; otherwise verify disappearance.
        def still_running(pid):
            try:
                os.kill(pid, 0)
                stat = Path(f'/proc/{pid}/stat')
                if stat.exists() and stat.read_text().rsplit(')', 1)[1].split()[0] == 'Z':
                    return False
                return True
            except (ProcessLookupError, FileNotFoundError):
                return False
        deadline = time.monotonic() + 5
        while any(still_running(pid) for pid in daemons) and time.monotonic() < deadline:
            time.sleep(.02)
        assert not [pid for pid in daemons if still_running(pid)], 'test observer did not exit before scratch cleanup'


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q", "-p", "no:cacheprovider"]))
