"""Fixed B06 endpoints on the frozen deadline/IPC lifecycle.

R4 calls the unchanged B05 search. R1 exits normally after that same search's
first complete publication, before it can enter tape1. No shared-arm cache.
"""
import json
import multiprocessing as mp
import os
from pathlib import Path
import signal
import time
import traceback

import numpy as np

from experiments.candidates.uav_decision_generalization.b05_request_schedule import policy as inherited
from experiments.candidates.uav_decision_generalization.b05_request_schedule.features import candidate_features
from experiments.candidates.uav_decision_generalization.b05_request_schedule.ordinary import g_values, greedy_action
from experiments.candidates.uav_decision_generalization.b05_request_schedule.storage import RolloutTrace
from experiments.candidates.uav_decision_generalization.b05_request_schedule.task import candidate_slots
from . import contract as c

LOAD_NAMES = ('checkpoint_load_attempts', 'checkpoint_loads',
              'scorer_constructor_attempts', 'scorer_constructors')
SHARED_NAMES = inherited.SHARED_NAMES + LOAD_NAMES + ('constant_score_attempts', 'constant_scores')
CACHE_DTYPE = np.dtype(inherited.CACHE_DTYPE.descr + [('constant_complete', 'u1')])


def open_counts(path, *, create=False):
    counts = np.memmap(path, dtype='<i8', mode='w+' if create else 'r+', shape=(len(SHARED_NAMES),))
    if create:
        counts[:] = 0
        counts.flush()
    return counts


class _FirstCohortComplete(Exception):
    """Normal R1 cap return, handled directly outside the inherited search."""


def search(state, raw_g, trace, publish, source_identity, tape_limit):
    if tape_limit not in (1, 4) or type(tape_limit) is not int:
        raise ValueError('only the selected one/four-cohort programs exist')
    from experiments.candidates.uav_decision_generalization.b05_request_schedule.rollout import search as original
    if tape_limit == 4:
        return original(state, raw_g, trace, publish, source_identity)
    first = []
    def publish_first(payload):
        if first or len(payload['cohorts']) != 1 or payload['cohorts'][0]['tape'] != 0:
            raise AssertionError('R1 must publish precisely original tape0')
        first.append(payload['cohorts'][0])
        publish(payload)
        # The original function's next scientific operation would draw tape1.
        # Raising here unwinds only local model objects; it is not a failed
        # request, a deadline exception, a repeated sample or a worker restart.
        raise _FirstCohortComplete
    try:
        original(state, raw_g, trace, publish_first, source_identity)
    except _FirstCohortComplete:
        return {'cohorts': first, 'cohort_limit': 1}
    raise AssertionError('R1 returned without its single complete cohort')


def _child(connection, spec, counts_path, source_identity, parent_pid):
    os.setsid()
    inherited._bind_parent_lifetime(parent_pid)
    signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGTERM, signal.SIGINT})
    counts = open_counts(counts_path)
    cache = np.memmap(str(counts_path) + '.cache', dtype=CACHE_DTYPE, mode='r+', shape=(1,))
    def add(name, amount=1):
        index = SHARED_NAMES.index(name)
        counts[index] += amount
        # Per persistent endpoint, at most32x60 actual decisions. Restarting
        # resets this mmap, but the unchanged complete roster bounds the total;
        # parent finished_counts retains all interrupted attempts.
        limits = {'g_attempts': 1920, 'g_complete': 1920,
                  'g_reserved_candidate_ticks': 1674240, 'g_complete_candidate_ticks': 1674240,
                  'frozen_nn_attempted_rows': 7680, 'frozen_nn_rows': 7680,
                  'constant_score_attempts': 1920, 'constant_scores': 1920,
                  **{key: 1 for key in LOAD_NAMES}}
        if name not in limits or counts[index] > limits[name]:
            raise RuntimeError('unselected deployment exposure: ' + name)
    class LoadMeter:
        def check(self):
            # The actual parent enforces cumulative CPU/wall every <=.2s and
            # reaps this process on a stop. A load has no task/model queries.
            if os.getppid() != parent_pid:
                raise RuntimeError('deployment parent disappeared')
        def add(self, name, amount=1):
            prefix = 'b06_deployment_load_'
            if not name.startswith(prefix) or name[len(prefix):] not in LOAD_NAMES:
                raise ValueError('unexpected checkpoint-load scientific work')
            add(name[len(prefix):], amount)
        def reserve(self, name, amount=1):
            self.check()
            self.add(name, amount)
    try:
        if spec['kind'] not in ('G', 'R4', 'R1', 'B', 'S'):
            raise ValueError('unsupported selected deployment endpoint')
        scorer, constant = None, None
        if spec['kind'] == 'S':
            import torch
            torch.set_num_threads(4)
            torch.set_num_interop_threads(1)
            torch.use_deterministic_algorithms(True)
            from .acquisition import load_scorer
            scorer = load_scorer(spec['checkpoint'], spec['checkpoint_identity'],
                                 fit_index=spec['fit'], stage='final', source_identity=source_identity,
                                 bank_identity=spec['bank_identity'], meter=LoadMeter(),
                                 phase='deployment_load')
            if scorer.payload['launch_sha'] != spec['checkpoint_launch_sha']:
                raise ValueError('student checkpoint original launch identity differs')
        elif spec['kind'] == 'B':
            from .acquisition import file_identity
            actual = file_identity(spec['constant_path'])
            expected = spec['constant_identity']
            if actual['bytes'] != expected['bytes'] or actual['sha256'] != expected['sha256']:
                raise ValueError('constant deployment byte identity changed')
            value = json.loads(Path(spec['constant_path']).read_bytes())
            if (value['schema'] != 1 or value['object'] != c.OBJECT
                    or value['source_identity'] != source_identity or value['bank_identity'] != spec['bank_identity']
                    or value['launch_sha'] != spec['constant_launch_sha']):
                raise ValueError('constant deployment source/bank lineage differs')
            constant = np.asarray(value['solution']['b'], dtype=np.float64)
            if constant.shape != (4,) or not np.isfinite(constant).all():
                raise ValueError('finite four-constant correction required')
        connection.send({'type': 'boot', 'ready_ns': time.monotonic_ns()})
        while True:
            request = connection.recv()
            if request['operation'] == 'stop':
                break
            if request['operation'] != 'decide':
                raise ValueError('B06 endpoints are frozen and have no offline update operation')
            state = request['state']
            trace = RolloutTrace(request['trace']) if spec['kind'] in ('R4', 'R1') else None
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
                    'score_complete': False, 'cohorts': []}
            if spec['kind'] in ('R4', 'R1'):
                connection.send({'type': 'fallback', 'payload': base, 'ready_ns': time.monotonic_ns()})
                def publish(cohort):
                    connection.send({'type': 'cohort', 'payload': {**base, **cohort},
                                     'ready_ns': time.monotonic_ns()})
                extra = search(state, raw_g, trace, publish, source_identity,
                               4 if spec['kind'] == 'R4' else 1)
                trace.close()
                connection.send({'type': 'done', 'extra': extra, 'ready_ns': time.monotonic_ns()})
                continue
            if spec['kind'] == 'S':
                from .acquisition import compose_q, greedy
                add('frozen_nn_attempted_rows', 4)
                residual = scorer.forward(features, training=False).reshape(4)
                add('frozen_nn_rows', 4)
                total = compose_q(raw_g, residual)
                action = int(greedy(total, raw_g))
                cache['residual'][0], cache['total_q'][0] = residual, total
                cache['greedy_action'][0], cache['nn_complete'][0] = action, 1
                base.update(action=action, greedy_action=action, command=choices[action].copy(),
                            total_q=total, residual=residual, score_complete=True)
            elif spec['kind'] == 'B':
                add('constant_score_attempts')
                total = raw_g + constant
                if not np.isfinite(total).all():
                    raise FloatingPointError('nonfinite B score')
                action = int(np.lexsort((np.arange(4), raw_g, total))[0])
                cache['total_q'][0], cache['greedy_action'][0] = total, action
                cache['constant_complete'][0] = 1
                add('constant_scores')
                base.update(action=action, greedy_action=action, command=choices[action].copy(),
                            total_q=total, score_complete=True)
            connection.send({'type': 'result', 'payload': base, 'ready_ns': time.monotonic_ns()})
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


class Endpoint(inherited.Endpoint):
    """Use original ready+receipt deadline, final KEEP and exact-child reap."""
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

    def decide(self, state, trace_path=None):
        result = super().decide(state, trace_path)
        constant_complete = bool(self.cache['constant_complete'][0])
        result['score_complete'] = constant_complete or bool(self.cache['nn_complete'][0])
        if constant_complete and result['total_q'] is None:
            result['total_q'] = self.cache['total_q'][0].copy()
            result['greedy_action'] = int(self.cache['greedy_action'][0])
        return result

    def counters(self):
        values = self.finished_counts + np.asarray(self.counts)
        return {name: int(values[index]) for index, name in enumerate(SHARED_NAMES)}
