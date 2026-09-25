"""Protocol and delivery tests; no browser model, actual queue message or research work."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('hmasd_wait', ROOT/'tools/hmasd_wait.py')
wait = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wait)


def launch_body(code=0):
    return {'execution': {'state': 'exited', 'exit_code': code, 'exit_witness': {'state': 'valid'}},
            'record_consistency': {'state': 'consistent'}}


def fake_codex(binary, calls, queue_help='--thread --message'):
    binary.write_text(f'''#!{sys.executable}
import sys
from pathlib import Path
if '--help' in sys.argv:
 print({queue_help!r})
else:
 with Path({str(calls)!r}).open('a') as out: out.write('queued\\n')
 print('queued test message')
''')
    binary.chmod(0o700)


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setenv('CODEX_THREAD_ID', str(uuid.uuid4()))
    folder = tmp_path/'state'
    binary = tmp_path/'codex'
    calls = tmp_path/'calls'
    fake_codex(binary, calls)
    job = {'id': 'one', 'protocol': 'launch', 'argv': [sys.executable, '-c', 'print("{}")'],
           'cwd': str(tmp_path), 'interval': 1}
    monkeypatch.setattr(wait, 'spawn', lambda folder: 0)
    wait.arm(folder, {'jobs': [job]}, str(binary), 1500)
    return folder, binary, calls, job


def test_exit_requires_matching_witness_and_does_not_infer_from_missing_pid():
    assert wait.classify('launch', launch_body()) == 'ready'
    assert wait.classify('launch', launch_body(7)) == 'failed'
    bad = launch_body(); bad['execution']['exit_witness']['state'] = 'invalid'
    assert wait.classify('launch', bad) == 'unknown'
    bad = launch_body(); bad['record_consistency']['state'] = 'conflict'
    assert wait.classify('launch', bad) == 'unknown'
    assert wait.classify('launch', {'execution': {'state': 'unknown'}}) == 'unknown'
    assert wait.classify('launch', launch_body(True)) == 'unknown'


def test_pro_window_is_not_failure_and_complete_is_only_collected(tmp_path):
    assert wait.classify('pro', {'state': 'IN_PROGRESS'}) == 'running'
    assert wait.classify('pro', {'state': 'COMPLETE'}) == 'blocked'
    answer = tmp_path/'answer'; answer.write_text('full answer')
    assert wait.classify('pro', {'state': 'COMPLETE', 'answer_file': str(answer)}) == 'collected'
    assert wait.classify('pro', {'state': 'NEEDS_HUMAN'}) == 'blocked'


def test_coalesce_duplicate_and_racing_events(setup):
    folder, _binary, calls, _job = setup
    with wait.transaction(folder) as state:
        first = wait.event(state, 'one:done', 'READY', {'job': 'one'})
        assert wait.event(state, 'one:done', 'READY', {}) == first
        wait.event(state, 'two:done', 'BLOCKED', {'job': 'two'})
    wait.submit(folder); wait.submit(folder)
    seen = wait.drain(folder)
    assert len(seen['events']) == 2
    assert calls.read_text().splitlines() == ['queued']
    with wait.transaction(folder) as state:
        late = wait.event(state, 'three:done', 'READY', {'job': 'three'})
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
        wait.event(state, 'done', 'READY', {})
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


def test_reused_arm_replaces_missing_binary_before_one_submit(setup, tmp_path):
    folder, old_binary, old_calls, job = setup
    new_binary, new_calls = tmp_path/'new-codex', tmp_path/'new-calls'
    fake_codex(new_binary, new_calls)
    old_binary.unlink()
    wait.arm(folder, {'jobs': [job]}, str(new_binary), 1500)
    with wait.transaction(folder) as state:
        assert state['codex'] == str(new_binary)
        assert state['jobs']['one']['spec'] == job
        wait.event(state, 'done', 'READY', {})
    wait.submit(folder)
    wait.submit(folder)
    assert new_calls.read_text().splitlines() == ['queued']
    assert not old_calls.exists()
    assert wait.drain(folder)['delivery']['status'] == 'queued'


@pytest.mark.parametrize('explicit_codex', [False, True])
def test_rearm_cli_refreshes_missing_binary_and_consumes_original_event(
    setup, tmp_path, monkeypatch, capsys, explicit_codex
):
    folder, old_binary, old_calls, job = setup
    new_binary, new_calls = tmp_path/'new-codex', tmp_path/'new-calls'
    fake_codex(new_binary, new_calls)
    old_binary.unlink()
    with wait.transaction(folder) as state:
        event_id = wait.event(state, 'original', 'READY', {'job_id': 'one'})
    seen = wait.drain(folder)
    monkeypatch.setattr(wait.shutil, 'which', lambda name: str(new_binary))
    argv = ['hmasd_wait.py', 'rearm', '--state-dir', str(folder),
            '--generation', str(seen['generation']), '--wake-id', seen['wake_id'],
            '--event-ids', event_id]
    if explicit_codex:
        argv.extend(['--codex', str(new_binary)])
    monkeypatch.setattr(sys, 'argv', argv)
    wait.main()
    assert json.loads(capsys.readouterr().out)['generation'] == seen['generation'] + 1
    with wait.transaction(folder) as state:
        assert state['codex'] == str(new_binary)
        assert state['events'][event_id]['consumed'] is True
        assert state['jobs']['one']['spec'] == job
        wait.event(state, 'next', 'READY', {})
    wait.submit(folder)
    assert new_calls.read_text().splitlines() == ['queued']
    assert not old_calls.exists()
    assert wait.drain(folder)['delivery']['status'] == 'queued'


@pytest.mark.parametrize('invalid', ['missing', 'no-queue'])
def test_rearm_bad_binary_does_not_consume_or_change_state(setup, tmp_path, invalid):
    folder, old_binary, _calls, _job = setup
    with wait.transaction(folder) as state:
        event_id = wait.event(state, 'original', 'READY', {})
    seen = wait.drain(folder)
    before = json.loads((folder/'state.json').read_text())
    candidate = tmp_path/'new-codex'
    if invalid == 'no-queue':
        fake_codex(candidate, tmp_path/'new-calls', queue_help='no queue support')
    with pytest.raises((OSError, ValueError)):
        wait.rearm(folder, seen['generation'], seen['wake_id'], [event_id], 1500, binary=str(candidate))
    assert json.loads((folder/'state.json').read_text()) == before
    assert old_binary.exists()


def test_binary_refresh_keeps_owner_pending_and_generation_guards(setup, tmp_path, monkeypatch):
    folder, old_binary, _calls, job = setup
    candidate = tmp_path/'new-codex'
    fake_codex(candidate, tmp_path/'new-calls')
    with wait.transaction(folder) as state:
        event_id = wait.event(state, 'original', 'READY', {})
    seen = wait.drain(folder)
    before = json.loads((folder/'state.json').read_text())
    with pytest.raises(ValueError, match='drain and rearm'):
        wait.arm(folder, {'jobs': [job]}, str(candidate), 1500)
    with pytest.raises(ValueError, match='stale'):
        wait.rearm(folder, seen['generation'] - 1, seen['wake_id'], [event_id], 1500, binary=str(candidate))
    with pytest.raises(ValueError, match='blocked observation'):
        wait.rearm(folder, seen['generation'], seen['wake_id'], [event_id], 1500,
                   resume_jobs=['one'], binary=str(candidate))
    with monkeypatch.context() as patch:
        patch.setenv('CODEX_THREAD_ID', str(uuid.uuid4()))
        with pytest.raises(ValueError, match='different'):
            wait.rearm(folder, seen['generation'], seen['wake_id'], [event_id], 1500, binary=str(candidate))
    assert json.loads((folder/'state.json').read_text()) == before
    assert before['codex'] == str(old_binary)


def test_submit_missing_binary_records_executable_and_errno_once(setup):
    folder, binary, _calls, _job = setup
    binary.unlink()
    with wait.transaction(folder) as state:
        wait.event(state, 'done', 'READY', {})
    wait.submit(folder)
    wait.submit(folder)
    delivery = wait.drain(folder)['delivery']
    assert delivery['status'] == 'delivery_unknown'
    assert delivery['error_type'] == 'FileNotFoundError'
    assert delivery['executable'] == str(binary)
    assert delivery['errno'] == 2
    assert str(binary) in delivery['error']


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
        wait.event(state, 'x', 'READY', {})
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
    child = subprocess.Popen([sys.executable, str(ROOT/'tools/hmasd_wait.py'), '_run', '--state-dir', str(folder)],
                             stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        out, err = child.communicate(timeout=10)
    finally:
        if child.poll() is None:
            child.kill(); child.wait()
    assert child.returncode == 0, err.decode()
    assert len(calls.read_text().splitlines()) == 1
    seen = wait.drain(folder)
    assert seen['events'][0]['kind'] == 'BLOCKED'
    assert seen['events'][0]['evidence']['facts']['execution']['exit_code'] == 7


def test_read_probe_timeout_and_invalid_json_stay_unknown(setup):
    _folder, _binary, _calls, job = setup
    job['argv'] = [sys.executable, '-c', 'import time; time.sleep(2)']
    assert wait.probe(job, .1)[0] == 'unknown'
    job['argv'] = [sys.executable, '-c', 'print("no JSON")']
    assert wait.probe(job, 2)[0] == 'unknown'


def test_rearm_cannot_consume_unseen_events_or_change_job_identity(setup):
    folder, binary, _calls, job = setup
    with wait.transaction(folder) as state:
        event_id = wait.event(state, 'x', 'READY', {})
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


@pytest.mark.parametrize('field,value', [('interval', '30'), ('timeout', '20'), ('timeout', True), ('interval', float('nan'))])
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
        return 'ready', launch_body()
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
        assert seen['jobs']['one']['status'] == 'ready'
        assert [e['kind'] for e in seen['events']] == ['READY']
        assert len(calls) == 2 and calls[0] is not calls[1]
    finally:
        release.set()
        with wait.transaction(folder) as state:
            state['stopped'] = True
        thread.join(timeout=5)


def test_manual_recovery_of_event_persisted_before_queue_claim(setup):
    folder, _binary, calls, _job = setup
    with wait.transaction(folder) as state:
        event_id = wait.event(state, 'persisted-before-crash', 'READY', {})
    seen = wait.drain(folder)
    assert seen['wake_id'] and seen['delivery']['status'] == 'read_locally'
    wait.submit(folder)
    assert not calls.exists()
    wait.rearm(folder, seen['generation'], seen['wake_id'], [event_id], 1500)
    assert wait.drain(folder)['events'] == []
