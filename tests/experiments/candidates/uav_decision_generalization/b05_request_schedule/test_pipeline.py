"""Pure/mocked pipeline and benign-process checks; no scientific effects."""
from copy import deepcopy
from dataclasses import replace
import multiprocessing as mp
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import numpy as np
import pytest

from experiments.candidates.uav_decision_generalization.b05_request_schedule import (
    bindings, contract as c, native, policy, rollout, storage, worker)
from experiments.candidates.uav_decision_generalization.b05_request_schedule.task import (
    PublicState, candidate_slots, slot_positions)


def state(tick=0):
    users = np.repeat(np.array([[2500, 2500], [500, 500], [4500, 500],
                                [4500, 4500], [500, 4500]], dtype=np.int32), 10, axis=0)
    slots = np.arange(6, dtype=np.uint8)
    return PublicState(123, tick, users, np.array([6, 3, 2, 1]),
                       slot_positions(users, slots), np.zeros(50, bool),
                       np.zeros(4, int), np.zeros(4, int), slots,
                       ((0, 1), (2, 3), (4, 5)))


def fake_snapshot(positions):
    return {'positions': np.array(positions, copy=True),
            'connections': np.zeros((6, 50), bool),
            'routes': np.full((6, 7), -1, dtype=np.int16),
            'route_lengths': np.zeros(6, dtype=np.int16),
            'uav_connections': np.zeros((6, 6), bool),
            'bs_connections': np.zeros((6, 1), bool),
            'transmitter_mask': np.ones(6, bool)}


class FakeMeter:
    def __init__(self):
        self.live, self.counts = set(), {}

    def report(self):
        return {'phase_cpu_seconds': 0., 'phase_wall_seconds': 0., 'counts': dict(self.counts)}

    check = report

    def add(self, name, amount=1):
        self.counts[name] = self.counts.get(name, 0) + amount


def test_actual_launcher_accepts_literal_admission_declaration():
    from scripts.hmasd_launch import _validate_guard_contract
    entry = Path(worker.__file__).with_name('run.py')
    _validate_guard_contract(entry, 'uav_decision_generalization')


def test_selected_local_runtime_and_thread_setup_use_only_mocks(monkeypatch):
    import platform
    from types import SimpleNamespace
    from experiments.candidates.uav_decision_generalization.b05_request_schedule import run
    calls = []
    fake = SimpleNamespace(__version__='2.7.0+cpu',
        set_num_threads=lambda value: calls.append(('threads', value)),
        set_num_interop_threads=lambda value: calls.append(('interop', value)),
        use_deterministic_algorithms=lambda value: calls.append(('deterministic', value)))
    monkeypatch.setitem(sys.modules, 'torch', fake)
    monkeypatch.setattr(platform, 'python_version', lambda: '3.10.20')
    monkeypatch.setattr(platform, 'system', lambda: 'Linux')
    monkeypatch.setattr(np, '__version__', '1.26.3')
    result = run.runtime()
    assert result['node'] == 'local_linux' and result['device'] == 'cpu'
    assert calls == [('threads', 4), ('interop', 1), ('deterministic', True)]
    fake.__version__ = '2.7.0+cu118'
    with pytest.raises(RuntimeError, match='selected Linux'):
        run.runtime()
    assert len(calls) == 3
    assert c.frozen_contract()['runtime_versions'] == ['3.10.20', '1.26.3', '2.7.0+cpu']


def test_scientific_manifest_excludes_mutable_supervisor_files(tmp_path):
    names = ['config.json', 'endpoint-counts.json', 'raw/mission.npz',
             'raw/rollouts/prefix.npz']
    for fit in range(3):
        names.append(f'fit{fit}.json')
        names.extend(f'checkpoints/fit{fit}_{kind}.pt' for kind in ('initial', 'final', 'training'))
    for name in names:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
    changing = ['launch-status.json', 'stdout.log', 'stderr.log', 'progress.json',
                'process-exit.json', 'summary.json', 'scratch/counts.bin']
    for name in changing:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'before exit')
    manifest = worker.scientific_manifest(tmp_path)
    assert set(manifest) == set(names)
    for name in changing:
        (tmp_path / name).write_bytes(b'terminal status and flushed logs')
    assert worker.scientific_manifest(tmp_path) == manifest


@pytest.mark.parametrize('parents', [(8,), (7, 8)])
def test_parent_lifetime_refuses_a_parent_death_race(monkeypatch, parents):
    parents = iter(parents)
    monkeypatch.setattr(policy.os, 'getppid', lambda: next(parents))
    syscall = type('Call', (), {'__call__': lambda self, *args: 0})()
    monkeypatch.setattr(policy.ctypes, 'CDLL', lambda *args, **kwargs:
                        type('Lib', (), {'prctl': syscall})())
    with pytest.raises(RuntimeError, match='worker disappeared'):
        policy._bind_parent_lifetime(7)


@pytest.mark.parametrize('boundary', ['start', 'send'])
def test_decision_start_or_send_failure_reaps_before_return(tmp_path, monkeypatch, boundary):
    endpoint = policy.Endpoint({'kind': 'R'}, tmp_path / boundary, FakeMeter(), 'source')
    events = []
    def fail(*args, **kwargs):
        events.append(boundary)
        raise SystemExit(143)
    monkeypatch.setattr(endpoint, '_start', fail if boundary == 'start' else lambda: None)
    endpoint.connection = type('Pipe', (), {'send': fail})()
    monkeypatch.setattr(endpoint, '_reap', lambda **kwargs: events.append('reaped'))
    with pytest.raises(SystemExit):
        endpoint.decide(state(), tmp_path)
    assert events == [boundary, 'reaped']
    endpoint.connection = None
    endpoint.close()


def test_parent_death_kills_and_reaps_benign_policy_child(tmp_path):
    # The isolated fixture process owns subreaping, so no child is abandoned to
    # the host init. Only sleep/pause runs in descendants; no policy is built.
    script = tmp_path / 'parent_death.py'
    script.write_text('''import ctypes, os, signal, time
from experiments.candidates.uav_decision_generalization.b05_request_schedule.policy import _bind_parent_lifetime
libc = ctypes.CDLL(None, use_errno=True)
assert libc.prctl(36, 1, 0, 0, 0) == 0
read_fd, write_fd = os.pipe()
fixture_parent = os.getpid()
parent = os.fork()
if parent == 0:
    os.close(read_fd)
    _bind_parent_lifetime(fixture_parent)
    expected_parent = os.getpid()
    child = os.fork()
    if child == 0:
        os.setsid()
        _bind_parent_lifetime(expected_parent)
        os.write(write_fd, str(os.getpid()).encode() + b"\\n")
        while True: signal.pause()
    os.close(write_fd)
    while True: signal.pause()
os.close(write_fd)
alive = {parent}
def expired(_signum, _frame):
    raise TimeoutError('benign parent-death fixture deadline')
signal.signal(signal.SIGALRM, expired)
signal.alarm(8)
try:
    child = int(os.read(read_fd, 80).strip())
    os.close(read_fd)
    alive.add(child)
    os.kill(parent, signal.SIGTERM)
    waited, status = os.waitpid(parent, 0)
    alive.remove(parent)
    assert waited == parent and os.WIFSIGNALED(status)
    waited, status = os.waitpid(child, 0)
    alive.remove(child)
    assert waited == child and os.WIFSIGNALED(status) and os.WTERMSIG(status) == signal.SIGKILL
    assert not os.path.exists('/proc/' + str(child))
    print('parent and child reaped; zero scientific calls')
finally:
    signal.alarm(0)
    for pid in alive:
        try: os.kill(pid, signal.SIGKILL)
        except ProcessLookupError: pass
    while True:
        try: os.waitpid(-1, 0)
        except ChildProcessError: break
''')
    environment = dict(os.environ, PYTHONPATH=str(Path.cwd()), PYTHONDONTWRITEBYTECODE='1')
    result = subprocess.run([sys.executable, '-B', str(script)], env=environment,
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert 'parent and child reaped' in result.stdout


def test_bounded_trace_commits_and_structured_finite_write(tmp_path):
    trace = storage.RolloutTrace(tmp_path / 'mapped', create=True)
    s = state()
    storage.put_state(trace.arrays['states'][0, 0], fake_snapshot(s.positions),
                      s.counts, s.progress, s.active_slots, s.tick)
    trace.arrays['rows'][0] = 1
    storage.put_g(trace.arrays['g'][0], s, np.arange(4, dtype=np.float64))
    trace.add('g_attempts')
    # Intentional cancelled publication window: payload committed before count.
    assert trace.count('g_complete') == 0 and trace.arrays['g'][0]['complete'] == 1
    path = tmp_path / 'trace.npz'
    stats = trace.collect(path)
    assert stats['g_attempts'] == 1 and not (tmp_path / 'mapped').exists()
    with np.load(path, allow_pickle=False) as result:
        assert result['rows'][0] == 1 and result['g'][0]['complete'] == 1
        assert not result['branch_complete'].any()
    bad = np.zeros(1, dtype=storage.G_DTYPE)
    bad['costs'][0, 0] = np.nan
    with pytest.raises(ValueError, match='nonfinite'):
        storage.write_npz(tmp_path / 'bad.npz', {'g': bad})
    assert not (tmp_path / 'bad.npz').exists()


def test_native_event_deepcopy_shares_sink_without_emitting_events():
    events = []
    counts = native.NativeCounts(dict.fromkeys(c.NATIVE_EVENT_NAMES, 0),
                                 lambda name, amount: events.append((name, amount)))
    counts['native_step_calls'] += 1
    copied = deepcopy(counts)
    assert events == [('native_step_calls', 1)]
    copied['native_steps'] += 1
    assert events[-1] == ('native_steps', 1) and counts['native_steps'] == 0


def mock_rollout(monkeypatch, trace, *, cancel_after=None, varying_tapes=False):
    calls, steps, terminal_slots = [], [], []
    class Host:
        def __init__(self, public):
            self.uav_positions = public.positions.copy()
            self.current_step = public.tick
            self.event_counts = {}
        def snapshot(self):
            return fake_snapshot(self.uav_positions)
        def ack(self):
            return np.zeros(50, bool)
        def advance(self, slots, users):
            if cancel_after is not None and len(steps) == cancel_after:
                raise InterruptedError('synthetic cancelled native call')
            steps.append((self.current_step, slots.copy()))
            self.current_step += 1
            return np.zeros((6, 3)), np.zeros((6, 3)), self.snapshot()
    monkeypatch.setattr(native, 'from_public_state', lambda public, event_sink=None: Host(public))
    monkeypatch.setattr(native, 'clone_public_host', deepcopy)
    def tape(public, tape_index, horizon):
        times = np.arange(public.tick + 20, min(public.tick + horizon, 940) + 1, 20)
        values = np.zeros((len(times), 4), bool)
        if len(times):
            values[-1, 3] = True
            if varying_tapes and tape_index:
                values[0, 0] = True
        return times, values
    monkeypatch.setattr(rollout, 'future_tape', tape)
    def mocked_g(public):
        index = len(calls)
        costs = np.array([9., 2., 11., 12.])
        calls.append(public)
        if public.tick == 920:
            terminal_slots.append(candidate_slots(public)[1].copy())
        elif public.tick == 940:
            np.testing.assert_array_equal(public.active_slots, terminal_slots[-1])
            np.testing.assert_array_equal(public.counts, [0, 0, 0, 1])
        storage.put_g(trace.arrays['g'][index], public, costs)
        trace.add('g_attempts')
        trace.add('g_complete')
        return index, costs
    monkeypatch.setattr(trace, 'g_values', mocked_g)
    return calls, steps


def test_rollout_tail_arrival_promotion_and_exact_cohort_reuse_are_mocked(tmp_path, monkeypatch):
    trace = storage.RolloutTrace(tmp_path / 'tail', create=True)
    calls, steps = mock_rollout(monkeypatch, trace)
    published = []
    rollout.search(state(780), np.arange(4, dtype=float), trace, published.append, 'source')
    assert len(steps) == 640 and len(calls) == 32
    assert trace.count('cohorts_reused') == 3 and len(published) == 4
    assert np.array_equal(trace.arrays['branch_cost'][:4], [2., 2., 2., 2.])
    assert trace.arrays['cohort_reuse'].tolist() == [-1, 0, 0, 0]
    assert trace.arrays['cohort_complete'].tolist() == [1, 1, 1, 1]
    trace.close()


def test_cancelled_prefix_keeps_complete_cohort_and_unfinished_attempt(tmp_path, monkeypatch):
    trace = storage.RolloutTrace(tmp_path / 'cancelled', create=True)
    _, steps = mock_rollout(monkeypatch, trace, cancel_after=643, varying_tapes=True)
    published = []
    with pytest.raises(InterruptedError):
        rollout.search(state(100), np.arange(4, dtype=float), trace, published.append, 'source')
    assert len(published) == 1 and len(steps) == 643
    assert trace.count('native_attempts') == 644 and trace.count('native_complete') == 643
    assert trace.arrays['cohort_complete'].tolist() == [1, 0, 0, 0]
    assert trace.arrays['branch_complete'][:5].tolist() == [1, 1, 1, 1, 0]
    assert trace.arrays['rows'][4] == 4
    trace.close()


@pytest.mark.parametrize('kind', ['G', 'R', 'L'])
def test_expired_endpoint_keeps_only_eligible_command_and_reaps(tmp_path, monkeypatch, kind):
    meter = FakeMeter()
    endpoint = policy.Endpoint({'kind': kind}, tmp_path / kind, meter, 'source')
    sent, reaped = [], []
    endpoint.connection = type('Pipe', (), {'send': lambda self, value: sent.append(value)})()
    monkeypatch.setattr(endpoint, '_start', lambda: None)
    clock = [0]
    monkeypatch.setattr(policy.time, 'monotonic_ns', lambda: clock[0])
    s = state()
    base = {'action': 2, 'command': candidate_slots(s)[2].copy(),
            'raw_g': np.arange(4, dtype=float), 'features': np.zeros((4, 303), np.float32),
            'cohorts': [{'tape': 0}], 'g_action': 0, 'greedy_action': 2,
            'total_q': np.arange(4, dtype=float), 'residual': np.zeros(4, np.float32),
            'exploration_draw': None, 'exploratory_action': None}
    call = [0]
    def message(timeout):
        call[0] += 1
        if kind == 'R' and call[0] == 1:
            clock[0] = 5_000_000_000
            return {'type': 'cohort', 'payload': base, 'ready_ns': clock[0]}
        clock[0] = 21_000_000_000
        if kind == 'L':
            endpoint.cache['g_complete'][0] = 1
            endpoint.cache['raw_g'][0] = [3., 2., 1., 4.]
            return {'type': 'result', 'payload': base, 'ready_ns': clock[0]}
        return None
    monkeypatch.setattr(endpoint, '_message', message)
    monkeypatch.setattr(endpoint, '_reap', lambda terminate=False: reaped.append(terminate))
    result = endpoint.decide(s)
    assert result['timing']['deadline_expired'] and reaped == [True]
    assert result['action'] == (2 if kind == 'R' else 0)
    if kind != 'R':
        np.testing.assert_array_equal(result['command'], s.active_slots)
    if kind == 'L':
        np.testing.assert_array_equal(result['raw_g'], [3., 2., 1., 4.])
    assert len(sent) == 1
    endpoint.close()


def benign_sleep(connection):
    os.setsid()
    connection.send('ready')
    time.sleep(60)


def test_real_benign_process_is_terminated_joined_and_removed(tmp_path):
    endpoint = policy.Endpoint({'kind': 'G'}, tmp_path / 'benign', FakeMeter(), 'source')
    context = mp.get_context('spawn')
    parent, child = context.Pipe()
    process = context.Process(target=benign_sleep, args=(child,))
    process.start()
    child.close()
    endpoint.process, endpoint.connection = process, parent
    endpoint.meter.live.add(process.pid)
    pid = process.pid
    try:
        assert parent.poll(15) and parent.recv() == 'ready'
        endpoint._reap(terminate=True)
        assert endpoint.process is None and pid not in endpoint.meter.live
        assert not Path(f'/proc/{pid}').exists()
    finally:
        if endpoint.process is not None:
            endpoint._reap(terminate=True)
        endpoint.close()


def test_reap_exit_race_still_joins(tmp_path, monkeypatch):
    endpoint = policy.Endpoint({'kind': 'G'}, tmp_path / 'race', FakeMeter(), 'source')
    class ExitedProcess:
        pid = 999999
        alive = True
        joined = False
        def is_alive(self): return self.alive
        def join(self, timeout): self.alive, self.joined = False, True
        def close(self): pass
    process = ExitedProcess()
    endpoint.process = process
    endpoint.connection = type('Pipe', (), {'close': lambda self: None})()
    def absent(pid): raise ProcessLookupError('synthetic exited process')
    monkeypatch.setattr(policy.os, 'getpgid', absent)
    endpoint._reap(terminate=True)
    assert process.joined and endpoint.process is None
    endpoint.close()


def test_mission_decision_precedes_previous_offline_update_and_delay(tmp_path, monkeypatch):
    s = state()
    events, actual_slots = [], []
    class Host:
        def __init__(self, world):
            self.user_positions = s.users.copy()
            self.uav_positions = s.positions.copy()
            self.current_step = 0
            self.event_counts = {}
        def snapshot(self): return fake_snapshot(self.uav_positions)
        def ack(self): return s.ack.copy()
        def advance(self, slots, users):
            actual_slots.append(slots.copy())
            self.current_step += 1
            return np.zeros((6, 3)), np.zeros((6, 3)), self.snapshot()
    class Random:
        def permutation(self, values): return values.copy()
        def random(self, shape): return np.full(shape, .99)
    class Endpoint:
        spec = {'kind': 'train'}
        def decide(self, public, trace_path):
            events.append(('decide', public.tick, public.active_slots.copy()))
            return {'command': candidate_slots(public)[1], 'action': 1,
                    'raw_g': np.arange(4, dtype=float), 'features': np.zeros((4, 303), np.float32),
                    'g_action': 0, 'greedy_action': 1, 'total_q': np.arange(4, dtype=float),
                    'residual': np.zeros(4, np.float32), 'exploration_draw': .2,
                    'exploratory_action': None, 'timing': {}, 'cohorts': []}
        def offline(self, operation, transition):
            events.append(('observe', transition['terminated'], transition['next_raw_g']))
            return {'update': None, 'wall_seconds': 0., 'cpu_seconds': 0.}
        def counters(self): return {}
    monkeypatch.setattr(worker, 'RequestHost', Host)
    monkeypatch.setattr(worker, 'rng', lambda *args: Random())
    records = []
    result = worker.mission(tmp_path, 123, 'mock', Endpoint(), FakeMeter(), records, training=True)
    assert result['total_cost'] == 0 and len(records) == 1
    assert [event[0] for event in events[:5]] == ['decide', 'decide', 'observe', 'decide', 'observe']
    assert events[-1][0:2] == ('observe', True) and events[-1][2] is None
    decisions = [event for event in events if event[0] == 'decide']
    for macro, event in enumerate(decisions):
        for tick in range(macro * 20, macro * 20 + 20):
            np.testing.assert_array_equal(actual_slots[tick], event[2])
    with np.load(tmp_path / 'raw/mock/123.npz', allow_pickle=False) as arrays:
        for macro in range(1, 60):
            np.testing.assert_array_equal(decisions[macro][2], arrays['commands'][macro - 1])


@pytest.mark.parametrize('bad', [float('nan'), float('inf'), -1., True])
def test_nonfinite_or_invalid_budget_is_rejected(bad):
    prior = {'schema': 1, 'object': 'B05_request_schedule',
             'cumulative_cpu_seconds': bad, 'aggregate_operation_wall_seconds': 0.}
    with pytest.raises(ValueError):
        bindings.bind_prior(prior)
