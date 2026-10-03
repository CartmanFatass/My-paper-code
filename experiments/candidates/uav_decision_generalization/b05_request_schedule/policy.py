"""Sequential policy process with a parent-enforced report deadline.

Replay updates are explicit offline requests after the next timed decision is
fixed. Persistent processes contain only a policy/replay, never an actual task.
"""
import copy
import ctypes
import multiprocessing as mp
import os
from pathlib import Path
import signal
import time
import traceback

import numpy as np

from . import contract as c
from .features import candidate_features
from .ordinary import greedy_action, g_values
from .storage import RolloutTrace
from .task import candidate_slots

LEARN_COUNTS = ('transition_attempts', 'transitions', 'update_attempts', 'updates', 'backward_attempts',
                'backwards', 'optimizer_attempts', 'optimizer_steps',
                'initial_target_copy_attempts', 'initial_target_copies', 'target_copy_attempts', 'target_copies',
                'update_failures')
FORWARD_ROLES = ('collection', 'update_current', 'update_next_online', 'update_next_target')
SHARED_NAMES = ('g_attempts', 'g_complete', 'g_reserved_candidate_ticks',
                'g_complete_candidate_ticks', 'frozen_nn_attempted_rows',
                'frozen_nn_rows', 'offline_audit_attempted_rows', 'offline_audit_rows') + LEARN_COUNTS + tuple(
    role + '_' + key for role in FORWARD_ROLES
    for key in ('attempts', 'calls', 'attempted_rows', 'rows'))
CACHE_DTYPE = np.dtype([('g_complete', 'u1'), ('nn_complete', 'u1'),
                        ('raw_g', '<f8', (4,)), ('features', '<f4', (4, c.FEATURE_COUNT)),
                        ('residual', '<f4', (4,)), ('total_q', '<f8', (4,)),
                        ('greedy_action', 'u1')])


def open_counts(path, create=False):
    counts = np.memmap(path, dtype='<i8', mode='w+' if create else 'r+', shape=(len(SHARED_NAMES),))
    if create:
        counts[:] = 0
        counts.flush()
    return counts


def _bind_parent_lifetime(parent_pid):
    """Linux child dies with its actual worker, including an uncatchable kill."""
    if os.getppid() != parent_pid:
        raise RuntimeError('policy worker disappeared before parent-death binding')
    libc = ctypes.CDLL(None, use_errno=True)
    prctl = libc.prctl
    prctl.argtypes = (ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong,
                     ctypes.c_ulong, ctypes.c_ulong)
    prctl.restype = ctypes.c_int
    if prctl(1, signal.SIGKILL, 0, 0, 0) != 0:  # PR_SET_PDEATHSIG
        raise OSError(ctypes.get_errno(), 'cannot bind policy parent-death signal')
    # Parent death between the first check and prctl does not deliver a signal.
    if os.getppid() != parent_pid:
        raise RuntimeError('policy worker disappeared while binding parent death')


def _child(connection, spec, counts_path, source_identity, parent_pid):
    os.setsid()
    _bind_parent_lifetime(parent_pid)
    signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGTERM, signal.SIGINT})
    counts = open_counts(counts_path)
    cache = np.memmap(str(counts_path) + '.cache', dtype=CACHE_DTYPE, mode='r+', shape=(1,))
    def add(name, amount=1):
        counts[SHARED_NAMES.index(name)] += amount
    def learn_event(event, values):
        for name in LEARN_COUNTS:
            counts[SHARED_NAMES.index(name)] = values[name]
        for role in FORWARD_ROLES:
            for key, value in values.get('forward', {}).get(role, {}).items():
                counts[SHARED_NAMES.index(role + '_' + key)] = value
        ceilings = {'transition_attempts': 30720, 'transitions': 30720,
                    'update_attempts': 30464, 'updates': 30464,
                    'backward_attempts': 30464, 'optimizer_attempts': 30464,
                    'initial_target_copy_attempts': 1, 'target_copy_attempts': 119}
        if any(values[key] > limit for key, limit in ceilings.items()):
            raise RuntimeError('fit counter ceiling reached before an extra call')
        row_limits = {'collection': 122880, 'update_current': 3899392,
                      'update_next_online': 15597568, 'update_next_target': 3899392}
        if any(values.get('forward', {}).get(role, {}).get('attempted_rows', 0) > limit
               for role, limit in row_limits.items()):
            raise RuntimeError('fit neural row ceiling reached before an extra call')
    try:
        learner = scorer = None
        if spec['kind'] in ('train', 'L', 'initial'):
            import torch
            torch.set_num_threads(4)
            torch.set_num_interop_threads(1)
            torch.use_deterministic_algorithms(True)
            from .learner import ResidualLearner, ResidualScorer, compose_q, lexicographic_actions
            if spec['kind'] == 'train':
                learner = ResidualLearner(spec['fit'], event_callback=learn_event)
                initial = learner.deployment_state_dict()
                if not initial['certificate']['exact_zero_head']:
                    raise AssertionError('initial head certificate is not zero')
                torch.save(initial, spec['initial_checkpoint'])
                exploration = np.random.Generator(np.random.PCG64(np.random.SeedSequence(
                    c.rng_domain('exploration', spec['fit']))))
            else:
                from experiments.candidates.uav_decision_generalization.b03_joint_window.evidence import hash_file
                if hash_file(spec['checkpoint']) != spec['checkpoint_sha256']:
                    raise ValueError('frozen checkpoint byte identity changed')
                checkpoint = torch.load(spec['checkpoint'], map_location='cpu', weights_only=False)
                if checkpoint['fit_index'] != spec['fit'] or checkpoint['init_seed'] != c.TORCH_INIT_SEEDS[spec['fit']]:
                    raise ValueError('frozen checkpoint fit/seed mismatch')
                scorer = ResidualScorer(checkpoint['init_seed'])
                scorer.load_state_dict(checkpoint['online'])
                scorer.eval()
                if spec['kind'] == 'initial' and not checkpoint['certificate']['exact_zero_head']:
                    raise ValueError('initial deployment lacks zero-head certificate')
        connection.send({'type': 'boot', 'ready_ns': time.monotonic_ns()})
        while True:
            request = connection.recv()
            operation = request['operation']
            if operation == 'stop':
                break
            if operation == 'decide':
                if spec['kind'] == 'initial':
                    raise RuntimeError('initial deployment must use the canonical G endpoint')
                state = request['state']
                trace = RolloutTrace(request['trace']) if spec['kind'] == 'R' else None
                add('g_attempts')
                ticks = 4 * min(c.G_HORIZON, c.HORIZON - state.tick)
                add('g_reserved_candidate_ticks', ticks)
                if trace is None:
                    raw_g = g_values(state).costs.copy()
                else:
                    _, raw_g = trace.g_values(state)
                    raw_g = raw_g.copy()
                features, raw_g = candidate_features(state, raw_g)
                cache['raw_g'][0], cache['features'][0] = raw_g, features
                cache['g_complete'][0] = 1
                add('g_complete')
                add('g_complete_candidate_ticks', ticks)
                g_action = greedy_action(raw_g)
                choices = candidate_slots(state)
                base = {'raw_g': raw_g.copy(), 'features': features,
                        'g_action': g_action, 'action': g_action,
                        'command': choices[g_action].copy(), 'greedy_action': g_action,
                        'total_q': raw_g / c.HORIZON,
                        'residual': np.zeros(4, dtype=np.float32),
                        'exploration_draw': None, 'exploratory_action': None,
                        'cohorts': []}
                if spec['kind'] == 'R':
                    connection.send({'type': 'fallback', 'payload': base,
                                     'ready_ns': time.monotonic_ns()})
                    from .rollout import search
                    def publish(cohort):
                        value = {**base, **cohort}
                        connection.send({'type': 'cohort', 'payload': value,
                                         'ready_ns': time.monotonic_ns()})
                    extra = search(state, raw_g, trace, publish, source_identity)
                    trace.close()
                    connection.send({'type': 'done', 'extra': extra,
                                     'ready_ns': time.monotonic_ns()})
                    continue
                if spec['kind'] == 'train':
                    action, total, residual = learner.choose(features, raw_g)
                    cache['residual'][0], cache['total_q'][0] = residual, total
                    cache['greedy_action'][0], cache['nn_complete'][0] = action, 1
                    draw = float(exploration.random())
                    explored = int(exploration.integers(4)) if draw < .1 else None
                    base.update(greedy_action=action, total_q=total, residual=residual,
                                exploration_draw=draw, exploratory_action=explored)
                    if explored is not None:
                        action = explored
                    base.update(action=action, command=choices[action].copy())
                elif spec['kind'] == 'L':
                    add('frozen_nn_attempted_rows', 4)
                    with torch.no_grad():
                        residual = scorer(torch.from_numpy(features)).numpy().copy()
                    add('frozen_nn_rows', 4)
                    total = compose_q(raw_g, residual)
                    action = int(lexicographic_actions(total, raw_g))
                    cache['residual'][0], cache['total_q'][0] = residual, total
                    cache['greedy_action'][0], cache['nn_complete'][0] = action, 1
                    base.update(action=action, greedy_action=action,
                                command=choices[action].copy(), total_q=total, residual=residual)
                connection.send({'type': 'result', 'payload': base,
                                 'ready_ns': time.monotonic_ns()})
            elif operation == 'observe':
                if learner is None:
                    raise RuntimeError('offline update outside a selected fit')
                row = request['transition']
                wall, cpu = time.monotonic(), time.process_time()
                update = learner.observe(**row)
                connection.send({'type': 'offline', 'update': update,
                                 'wall_seconds': time.monotonic() - wall,
                                 'cpu_seconds': time.process_time() - cpu})
            elif operation == 'audit_initial':
                if spec['kind'] != 'initial':
                    raise RuntimeError('zero-head audit outside initial deployment')
                features, raw_g = request['features'], request['raw_g']
                add('offline_audit_attempted_rows', 4)
                with torch.no_grad():
                    residual = scorer(torch.from_numpy(features)).numpy().copy()
                add('offline_audit_rows', 4)
                total = compose_q(raw_g, residual)
                action = int(lexicographic_actions(total, raw_g))
                if np.any(residual != 0) or action != greedy_action(raw_g):
                    raise AssertionError('saved initial path violates exact G identity')
                connection.send({'type': 'audit', 'residual': residual, 'action': action})
            elif operation == 'checkpoint':
                if learner is None:
                    raise RuntimeError('checkpoint outside selected training')
                torch.save(learner.deployment_state_dict(), request['deployment'])
                if request.get('training'):
                    torch.save(learner.compact_training_state_dict(), request['training'])
                connection.send({'type': 'checkpoint', 'metrics': learner.metrics(),
                                 'identity': learner.checkpoint_identity()})
            elif operation == 'metrics':
                connection.send({'type': 'metrics', 'metrics': learner.metrics() if learner else None})
            else:
                raise ValueError('unknown policy protocol operation')
    except BaseException as exc:
        try:
            connection.send({'type': 'error', 'error': type(exc).__name__,
                             'message': str(exc), 'traceback': traceback.format_exc()})
        finally:
            raise
    finally:
        counts.flush()
        counts._mmap.close()
        cache.flush()
        cache._mmap.close()
        connection.close()


class Endpoint:
    def __init__(self, spec, directory, meter, source_identity):
        self.spec, self.meter, self.source_identity = spec, meter, source_identity
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=False)
        self.count_path = self.directory / 'counts.bin'
        self.counts = open_counts(self.count_path, create=True)
        self.cache = np.memmap(str(self.count_path) + '.cache', dtype=CACHE_DTYPE, mode='w+', shape=(1,))
        self.cache[:] = 0
        self.process = self.connection = None
        self.booted = False
        self.starts = 0
        self.finished_counts = np.zeros(len(SHARED_NAMES), dtype=np.int64)

    def _start(self):
        if self.process is not None:
            return
        context = mp.get_context('spawn')
        # Publish the Process/Pipe identity before a catchable stop can unwind
        # into mission trace collection. The child explicitly clears this mask.
        old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGTERM, signal.SIGINT})
        child = None
        try:
            parent, child = context.Pipe(duplex=True)
            self.connection = parent
            self.counts[:] = 0
            self.process = context.Process(target=_child, args=(child, self.spec, str(self.count_path),
                                                               self.source_identity, os.getpid()))
            self.process.start()
            self.meter.live.add(self.process.pid)
            self.booted = False
            self.starts += 1
        finally:
            if child is not None:
                child.close()
            signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)

    def _message(self, timeout):
        if not self.connection.poll(timeout):
            if not self.process.is_alive():
                raise RuntimeError(f'policy child exited without response: {self.process.exitcode}')
            return None
        try:
            result = self.connection.recv()
        except EOFError as exc:
            raise RuntimeError('policy pipe closed before a response') from exc
        if result['type'] == 'error':
            raise RuntimeError('policy child failed: ' + repr(result))
        if result['type'] == 'boot':
            self.booted = True
            return None
        return result

    def _reap(self, *, terminate=False):
        if self.process is None:
            if self.connection is not None:
                self.connection.close()
                self.connection = None
            return
        pid = self.process.pid
        if pid is None:
            self.process.close()
            self.connection.close()
            self.connection = self.process = None
            self.booted = False
            return
        if terminate and self.process.is_alive():
            # The child calls setsid before any scientific import. If startup
            # has not reached that line, terminate this exact Process only.
            try:
                if os.getpgid(pid) == pid:
                    os.killpg(pid, signal.SIGTERM)
                else:
                    self.process.terminate()
            except ProcessLookupError:
                pass
        self.process.join(.5)
        if self.process.is_alive():
            try:
                if os.getpgid(pid) == pid:
                    os.killpg(pid, signal.SIGKILL)
                else:
                    self.process.kill()
            except ProcessLookupError:
                pass
            self.process.join(5)
        if self.process.is_alive():
            raise RuntimeError('policy process did not die; no next effect may start')
        self.meter.live.discard(pid)
        self.finished_counts += np.asarray(self.counts).copy()
        self.counts[:] = 0
        self.connection.close()
        self.process.close()
        self.connection = self.process = None
        self.booted = False

    def decide(self, state, trace_path=None):
        before_cost = self.meter.check()
        start = time.monotonic_ns()
        deadline = start + 20_000_000_000
        self.cache[:] = 0
        best = None
        messages = []
        done, expired = False, False
        try:
            self._start()
            self.connection.send({'operation': 'decide', 'state': state,
                                  'trace': str(trace_path) if trace_path else None})
            while True:
                remaining = (deadline - time.monotonic_ns()) / 1e9
                if remaining <= 0:
                    expired = True
                    break
                message = self._message(min(.2, remaining))
                received = time.monotonic_ns()
                self.meter.check()
                if message is None:
                    continue
                kind = message['type']
                eligible = received <= deadline and message.get('ready_ns', received) <= deadline
                messages.append({'type': kind, 'ready_ns': message.get('ready_ns'),
                                 'received_ns': received, 'eligible': eligible})
                if kind in ('fallback', 'cohort', 'result') and eligible:
                    best = message['payload']
                if kind in ('result', 'done'):
                    done = True
                    if not eligible:
                        expired = True
                    break
            fixed = time.monotonic_ns()
            if expired:
                self._reap(terminate=True)
            # A nonexpired child is waiting at recv and has closed its trace.
            if best is None:
                best = {'action': 0, 'command': state.active_slots.copy(),
                        'raw_g': None, 'features': None, 'cohorts': [],
                        'g_action': None, 'greedy_action': None, 'total_q': None,
                        'residual': None, 'exploration_draw': None, 'exploratory_action': None}
                if self.cache['g_complete'][0]:
                    best.update(raw_g=self.cache['raw_g'][0].copy(),
                                features=self.cache['features'][0].copy(),
                                g_action=greedy_action(self.cache['raw_g'][0]))
                if self.cache['nn_complete'][0]:
                    best.update(residual=self.cache['residual'][0].copy(),
                                total_q=self.cache['total_q'][0].copy(),
                                greedy_action=int(self.cache['greedy_action'][0]))
            best.update(timing={'start_ns': start, 'deadline_ns': deadline,
                                'command_fixed_ns': fixed, 'reaped_ns': time.monotonic_ns(),
                                'deadline_expired': expired, 'completed_request': done,
                                'messages': messages, 'process_starts': self.starts})
            after_cost = self.meter.report()
            best['timing'].update(cpu_seconds=after_cost['phase_cpu_seconds'] - before_cost['phase_cpu_seconds'],
                                  elapsed_wall_seconds=(time.monotonic_ns() - start) / 1e9,
                                  includes_start_ipc_cancel_reap=True,
                                  trace_collection_is_in_mission_bill=True)
            if self.spec['kind'] == 'train' and (expired or best['raw_g'] is None):
                error = RuntimeError('timed training decision/cache incomplete')
                error.partial_decision = best
                raise error
            return best
        except BaseException:
            self._reap(terminate=True)
            raise

    def offline(self, operation, **payload):
        try:
            if self.process is None:
                if self.spec['kind'] == 'initial' and operation == 'audit_initial':
                    self._start()
                else:
                    raise RuntimeError('offline acquisition has no retained policy process')
            self.meter.check()
            self.connection.send({'operation': operation, **payload})
            while True:
                message = self._message(.2)
                self.meter.check()
                if message is not None:
                    return message
        except BaseException:
            self._reap(terminate=True)
            raise

    def counters(self):
        values = self.finished_counts + np.asarray(self.counts)
        return {name: int(values[i]) for i, name in enumerate(SHARED_NAMES)}

    def close(self):
        if self.process is not None:
            if self.process.is_alive():
                self.connection.send({'operation': 'stop'})
            self._reap()
        result = self.counters()
        self.counts.flush()
        self.counts._mmap.close()
        self.cache.flush()
        self.cache._mmap.close()
        return result
