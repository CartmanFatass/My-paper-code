"""Frozen B04 control-loop injection with evaluator-only reset pairing."""

from pathlib import Path

import numpy as np

from experiments.candidates.uav_radio_activation.b01.protocol import encode_map
from experiments.candidates.uav_user_waiting.b02.storage import pack_records, unpack_records
from experiments.candidates.uav_user_waiting.b04.study import LocalController, collect_episode as frozen_collect
from . import protocol as p

BASELINE_FIELDS = ('positions', 'true_sites', 'map_packet', 'observations', 'commands', 'mask')


def error_details(exc):
    try:
        message = str(exc)
    except Exception:
        message = '<exception message unavailable>'
    return dict(type=type(exc).__name__, message=message)


def accounting_error(accounting, phase, exc):
    accounting.setdefault('errors', []).append(dict(phase=phase, **error_details(exc)))


class _ControllerMeter:
    def __init__(self, controller, member, attempted, completed, counts):
        self.controller, self.member = controller, member
        self.attempted, self.completed, self.counts = attempted, completed, counts

    def __getattr__(self, name):
        return getattr(self.controller, name)

    def act(self, observation, tick):
        self.attempted[tick, self.member] = True
        self.counts['worker_current_c_calls_attempted'] += 1
        try:
            result = self.controller.act(observation, tick)
        except Exception:
            self.counts['worker_current_c_calls_failed'] += 1
            raise
        self.completed[tick, self.member] = True
        self.counts['worker_current_c_calls'] += 1
        return result


class _SchedulerMeter:
    def __init__(self, scheduler, rounds, accounting):
        self.scheduler, self.rounds, self.accounting = scheduler, rounds, accounting

    def __getattr__(self, name):
        return getattr(self.scheduler, name)

    def decide(self, *args, **kwargs):
        result = None
        try:
            result = self.scheduler.decide(*args, **kwargs)
            return result
        finally:
            try:
                record = result['record'] if result is not None else getattr(self.scheduler, 'last_record', {})
                if record:
                    self.rounds[int(record['tick'])] = dict(record['counts'])
            except Exception as support:
                accounting_error(self.accounting, 'round_accounting', support)


def live_model_work(scheduler, rounds):
    result = {}
    for name, executed in scheduler.execution.work_counts.items():
        online_history = sum(row.get('history_' + name, 0) for row in rounds.values())
        result[name] = int(sum(row.get(name, 0) for row in rounds.values()) + executed - online_history)
        result['terminal_' + name] = int(executed - online_history)
    return result


def _frozen_failure(exc):
    """Recover the already allocated raw prefix if frozen finalization itself failed."""
    raw, records, primary = None, None, exc
    trace = exc.__traceback__
    while trace is not None:
        if trace.tb_frame.f_code is frozen_collect.__code__:
            raw = trace.tb_frame.f_locals.get('raw')
            records = trace.tb_frame.f_locals.get('records')
            failure = trace.tb_frame.f_locals.get('failure')
            if isinstance(failure, Exception):
                primary = failure
        trace = trace.tb_next
    return primary, raw, records


def _add_c_raw(raw, attempted, completed, controllers):
    raw['current_c_attempted'], raw['current_c_completed'] = attempted.copy(), completed.copy()
    names = sorted({key for controller in controllers for key in controller.counters})
    raw['current_c_source_counter_names'] = np.asarray(names, dtype=str)
    raw['current_c_source_counts'] = np.asarray(
        [sum(controller.counters.get(name, 0) for controller in controllers) for name in names], np.int64)


class PairCheckedEnvironment:
    """The baseline is evaluator state and is never passed to Scheduler/C."""
    def __init__(self, wrapped, baseline, counts):
        self.wrapped, self.baseline, self.counts = wrapped, baseline, counts

    def __getattr__(self, name):
        return getattr(self.wrapped, name)

    def reset(self, *, seed):
        self.counts['reset_calls_attempted'] += 1
        obs, info = self.wrapped.reset(seed=seed)
        actual = (info['state_info']['uav_positions'], info['state_info']['user_positions'],
                  np.frombuffer(encode_map(info['state_info']['user_positions']), np.uint8), obs)
        expected = (self.baseline['positions'][0], self.baseline['true_sites'],
                    self.baseline['map_packet'], self.baseline['observations'][0])
        for name, left, right in zip(('positions', 'sites', 'map', 'observation'), actual, expected):
            p.require(np.array_equal(left, right), 'reset pairing differs before policy query: ' + name)
        self.counts['paired_resets_verified'] += 1
        return obs, info


def atomic_npz(path, raw):
    path = Path(path)
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('wb') as stream:
        np.savez_compressed(stream, **raw)
    temporary.replace(path)


def augment_model_raw(raw, scheduler, baseline_identity):
    horizon = len(raw['commands'])
    grants = np.full((horizon, p.N, 10), -1, np.int8)
    for tick, selected in scheduler.execution.predicted_grants.items():
        grants[int(tick)] = selected
    raw['model_lrs_grants'] = grants
    raw['terminal_last_grant'] = scheduler.execution.history.last_grant.copy()
    names = sorted(scheduler.execution.work_counts)
    raw['execution_lrs_count_names'] = np.asarray(names)
    raw['execution_lrs_counts'] = np.asarray([scheduler.execution.work_counts[name] for name in names], np.int64)
    extra = pack_records([scheduler.execution.settlement_partial])
    raw['terminal_lrs_schema'], raw['terminal_lrs_bytes'] = extra['decision_schema'], extra['decision_bytes']
    raw['collector_program'], raw['program'] = np.array('S'), np.array(p.PROGRAM)
    raw['baseline_s_sha256'] = np.array(baseline_identity['sha256'])
    raw['baseline_s_bytes'] = np.array(baseline_identity['bytes'], np.int64)
    raw['grant_feedback_used'] = np.array(False)


def collect_episode(env, seed, out, counts, baseline_identity, *, horizon=p.HORIZON,
                    scheduler_type=None, controller_type=None, accounting=None):
    from .scheduler import Scheduler
    baseline = p.load_raw(baseline_identity, BASELINE_FIELDS)
    counts['baseline_raw_files_loaded'] += 1
    counts['baseline_raw_bytes_hashed'] += baseline_identity['bytes']
    counts['baseline_array_bytes_loaded'] += sum(value.nbytes for value in baseline.values())
    accounting = {} if accounting is None else accounting
    holder, rounds, controllers = {}, {}, []
    attempted, completed = np.zeros((horizon, p.N), bool), np.zeros((horizon, p.N), bool)
    raw = None
    attempted_augmentation = set()

    def construct(arm, map_packet, *, horizon):
        holder['scheduler'] = (scheduler_type or Scheduler)(arm, map_packet, horizon=horizon)
        return _SchedulerMeter(holder['scheduler'], rounds, accounting)

    def construct_controller(**kwargs):
        controller = (controller_type or LocalController)(**kwargs)
        meter = _ControllerMeter(controller, len(controllers), attempted, completed, counts)
        controllers.append(meter)
        return meter

    kwargs = dict(horizon=horizon, scheduler_type=construct, controller_type=construct_controller)
    try:
        row, raw = frozen_collect(PairCheckedEnvironment(env, baseline, counts), 'S', seed,
                                  out, counts, **kwargs)
        attempted_augmentation.add('current_c_raw')
        _add_c_raw(raw, attempted, completed, controllers)
        attempted_augmentation.add('model_raw')
        augment_model_raw(raw, holder['scheduler'], baseline_identity)
        return row, raw, baseline
    except Exception as exc:
        # The frozen collector preserves its native prefix before raising.
        primary, traceback_raw, traceback_records = _frozen_failure(exc)
        if primary is not exc:
            accounting_error(accounting, 'frozen_finalization', exc)
        if raw is None:
            raw = traceback_raw
        original = Path(out) / 'raw' / f'S_{seed}.npz'
        try:
            if raw is None and original.exists():
                with np.load(original, allow_pickle=False) as archive:
                    raw = {name: archive[name].copy() for name in archive.files}
            if raw is not None:
                # Persist available source raw even if optional augmentation fails.
                for phase, function in (
                    ('current_c_raw', lambda: _add_c_raw(raw, attempted, completed, controllers)),
                    ('model_raw', lambda: augment_model_raw(raw, holder['scheduler'], baseline_identity))):
                    if phase in attempted_augmentation:
                        continue
                    attempted_augmentation.add(phase)
                    try:
                        function()
                    except Exception as support:
                        accounting_error(accounting, phase, support)
                if 'scheduler' in holder:
                    try:
                        records = traceback_records if traceback_records is not None else unpack_records(raw)
                        last = getattr(holder['scheduler'], 'last_record', None)
                        if last and (not records or records[-1]['tick'] != last['tick']):
                            records.append(last)
                            raw.update(pack_records(records))
                    except Exception as support:
                        accounting_error(accounting, 'partial_record', support)
                atomic_npz(Path(out) / 'raw' / f'{p.PROGRAM}_{seed}.npz', raw)
                if original.exists():
                    original.unlink()  # Only after all source contents have been preserved.
        except Exception as support:
            accounting_error(accounting, 'failed_raw_preservation', support)
        raise primary
    finally:
        try:
            accounting['current_c_attempted'] = int(attempted.sum())
            accounting['current_c_completed'] = int(completed.sum())
            accounting['current_c_failed'] = int((attempted & ~completed).sum())
            names = sorted({key for controller in controllers for key in controller.counters})
            accounting['current_c_source_counts'] = {
                name: int(sum(controller.counters.get(name, 0) for controller in controllers)) for name in names}
            for name, value in accounting['current_c_source_counts'].items():
                counts['worker_current_c_source_' + name] += value
        except Exception as support:
            accounting_error(accounting, 'current_c_accounting', support)
        try:
            if 'scheduler' in holder:
                accounting['model_work'] = live_model_work(holder['scheduler'], rounds)
        except Exception as support:
            accounting_error(accounting, 'model_accounting', support)
