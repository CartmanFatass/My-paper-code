"""Failure accounting fixtures: no native environment, radio or rollout."""
from collections import Counter
from types import SimpleNamespace
import json

import numpy as np
import pytest

from experiments.candidates.uav_user_waiting.b02.storage import pack_records
from experiments.candidates.uav_user_waiting.b06 import collect as c, study as s
from experiments.candidates.uav_user_waiting.b06.history import ServiceHistory


def raw_fixture():
    return dict(commands=np.zeros((8, 5, 3), np.float32), c_called=np.zeros(8, bool),
                completed_steps=np.array(2), sinr=np.zeros((8, 5, 50)),
                execution_lrs_count_names=np.array(['model_fleet_ticks']), execution_lrs_counts=np.array([5]),
                **pack_records([dict(tick=0, counts=dict(model_fleet_ticks=9, history_model_fleet_ticks=2))]))


class Scheduler:
    def __init__(self, *args, **kwargs):
        self.execution = SimpleNamespace(predicted_grants={}, history=ServiceHistory(),
            settlement_partial={}, work_counts={'model_fleet_ticks': 5})
        self.last_record = {}

    def decide(self, *args, **kwargs):
        self.last_record = dict(tick=0, counts=dict(model_fleet_ticks=9, history_model_fleet_ticks=2))
        return dict(record=self.last_record)


@pytest.fixture
def collector(monkeypatch, tmp_path):
    (tmp_path / 'raw').mkdir()
    monkeypatch.setattr(c.p, 'load_raw', lambda *args: {'positions': np.zeros((9, 5, 3))})
    return tmp_path, Counter(), dict(bytes=100, sha256='bound-original')


def controller_factory(fail_at):
    created = []
    class Controller:
        def __init__(self, **kwargs):
            self.member = len(created)
            created.append(self)
            self.counters = dict(ingests=0, decisions=0, model_ticks=0)
        def act(self, observation, tick):
            self.counters['ingests'] += 1
            self.counters['decisions'] += 1  # Source counters are charged before computation.
            self.counters['model_ticks'] += 108
            if self.member == fail_at:
                raise ValueError('original C failure')
            return np.zeros(3), {}
    return Controller


def fake_frozen(*, c_failure=False, finalization_failure=False):
    def collect(env, arm, seed, out, counts, *, horizon, scheduler_type, controller_type):
        scheduler = scheduler_type(arm, b'', horizon=horizon)
        controllers = [controller_type(history=False) for _ in range(5)]
        raw, failure = raw_fixture(), None
        scheduler.decide()
        try:
            pairs = [controller.act(np.zeros(104), 0) for controller in controllers]
            raw['c_called'][0] = True
            assert len(pairs) == 5
        except Exception as exc:
            failure = exc
        if finalization_failure:
            raise OSError('frozen raw write failed')
        if failure:
            np.savez_compressed(out / 'raw' / f'S_{seed}.npz', **raw)
            raise failure
        return dict(seed=seed), raw
    return collect


@pytest.mark.parametrize('finalization_failure', [False, True])
def test_failed_current_c_vector_has_exact_attempts_and_live_source_counts(collector, monkeypatch, finalization_failure):
    out, counts, identity = collector
    monkeypatch.setattr(c, 'frozen_collect', fake_frozen(c_failure=True, finalization_failure=finalization_failure))
    accounting = {}
    with pytest.raises(ValueError, match='original C failure'):
        c.collect_episode(None, 7, out, counts, identity, horizon=8, scheduler_type=Scheduler,
                          controller_type=controller_factory(2), accounting=accounting)
    assert counts['worker_current_c_calls_attempted'] == 3
    assert counts['worker_current_c_calls'] == 2
    assert counts['worker_current_c_calls_failed'] == 1
    assert counts['worker_current_c_source_ingests'] == 3
    assert counts['worker_current_c_source_model_ticks'] == 324
    assert accounting['current_c_failed'] == 1
    assert accounting['model_work'] == dict(model_fleet_ticks=12, terminal_model_fleet_ticks=3)
    with np.load(out / 'raw' / 'S_F_7.npz', allow_pickle=False) as raw:
        np.testing.assert_array_equal(raw['current_c_attempted'][0], [1, 1, 1, 0, 0])
        np.testing.assert_array_equal(raw['current_c_completed'][0], [1, 1, 0, 0, 0])
        assert not raw['c_called'].any()
        assert dict(zip(raw['current_c_source_counter_names'], raw['current_c_source_counts']))['ingests'] == 3
    assert not (out / 'raw' / 'S_7.npz').exists()
    if finalization_failure:
        assert accounting['errors'][0]['phase'] == 'frozen_finalization'


def test_current_c_success_count_is_not_folded_twice(collector, monkeypatch):
    out, counts, identity = collector
    monkeypatch.setattr(c, 'frozen_collect', fake_frozen())
    accounting = {}
    _, raw, _ = c.collect_episode(None, 7, out, counts, identity, horizon=8,
        scheduler_type=Scheduler, controller_type=controller_factory(-1), accounting=accounting)
    assert counts['worker_current_c_calls_attempted'] == counts['worker_current_c_calls'] == 5
    assert counts['worker_current_c_source_decisions'] == 5
    assert accounting['current_c_failed'] == 0
    assert raw['current_c_completed'].sum() == 5
    assert accounting['model_work'] == s.model_work(raw)


def test_failed_preservation_keeps_original_error_and_source_file(collector, monkeypatch):
    out, counts, identity = collector
    monkeypatch.setattr(c, 'frozen_collect', fake_frozen(c_failure=True))
    monkeypatch.setattr(c, 'atomic_npz', lambda *args: (_ for _ in ()).throw(OSError('preservation unavailable')))
    accounting = {}
    with pytest.raises(ValueError, match='original C failure'):
        c.collect_episode(None, 7, out, counts, identity, horizon=8, scheduler_type=Scheduler,
                          controller_type=controller_factory(2), accounting=accounting)
    assert (out / 'raw' / 'S_7.npz').exists()
    assert accounting['errors'][-1]['phase'] == 'failed_raw_preservation'
    assert accounting['model_work']['model_fleet_ticks'] == 12
    assert counts['worker_current_c_calls_attempted'] == 3


def test_propagated_scheduler_failure_is_metered_before_serialization(collector, monkeypatch):
    out, counts, identity = collector
    class FailingScheduler(Scheduler):
        def decide(self, *args, **kwargs):
            super().decide()
            raise ArithmeticError('original planner failure')
    monkeypatch.setattr(c, 'frozen_collect', fake_frozen())
    accounting = {}
    with pytest.raises(ArithmeticError, match='original planner failure'):
        c.collect_episode(None, 7, out, counts, identity, horizon=8,
                          scheduler_type=FailingScheduler, controller_type=controller_factory(-1), accounting=accounting)
    assert accounting['model_work']['model_fleet_ticks'] == 12
    assert counts['worker_current_c_calls_attempted'] == 0


def test_augmentation_failure_preserves_successful_source_without_retry(collector, monkeypatch):
    out, counts, identity = collector
    monkeypatch.setattr(c, 'frozen_collect', fake_frozen())
    calls = [0]
    def failed(*args):
        calls[0] += 1
        raise OSError('original augmentation failure')
    monkeypatch.setattr(c, 'augment_model_raw', failed)
    accounting = {}
    with pytest.raises(OSError, match='original augmentation failure'):
        c.collect_episode(None, 7, out, counts, identity, horizon=8, scheduler_type=Scheduler,
                          controller_type=controller_factory(-1), accounting=accounting)
    assert calls[0] == 1
    assert counts['worker_current_c_calls'] == counts['worker_current_c_calls_attempted'] == 5
    assert accounting['model_work']['model_fleet_ticks'] == 12
    with np.load(out / 'raw' / 'S_F_7.npz', allow_pickle=False) as raw:
        assert raw['c_called'][0] and raw['current_c_completed'].sum() == 5


def test_accounting_error_does_not_mask_original_model_failure(collector, monkeypatch):
    out, counts, identity = collector
    monkeypatch.setattr(c, 'frozen_collect', fake_frozen(c_failure=True))
    monkeypatch.setattr(c, 'live_model_work', lambda *args: (_ for _ in ()).throw(OSError('accounting unavailable')))
    accounting = {}
    with pytest.raises(ValueError, match='original C failure'):
        c.collect_episode(None, 7, out, counts, identity, horizon=8, scheduler_type=Scheduler,
                          controller_type=controller_factory(2), accounting=accounting)
    assert accounting['errors'][-1]['phase'] == 'model_accounting'
    assert 'model_work' not in accounting
    assert counts['worker_current_c_calls_attempted'] == 3


@pytest.fixture
def batch(monkeypatch, tmp_path):
    monkeypatch.setattr(s.torch, 'set_num_threads', lambda *args: None)
    monkeypatch.setattr(s.torch, 'set_num_interop_threads', lambda *args: None)
    monkeypatch.setattr(s.p, 'SEEDS', (7, 8))
    monkeypatch.setattr(s.p, 'WORLDS', 2)
    monkeypatch.setattr(s.p, 'load_baselines', lambda *args: (None, {}, {7: {}, 8: {}}, {}))
    monkeypatch.setattr(s.p, 'frozen_config', lambda *args: {})
    monkeypatch.setattr(s, 'resources', lambda *args: {'measured_cpu_seconds': 1.})
    env = SimpleNamespace(env=SimpleNamespace(max_steps=0), close=lambda: None)
    monkeypatch.setattr(s, 'factory', lambda *args: env)
    monkeypatch.setattr(s, 'physical_comparison', lambda *args: {})
    monkeypatch.setattr(s, 'model_alignment', lambda *args: {})
    monkeypatch.setattr(s, 'paired_reading', lambda *args: {})
    monkeypatch.setattr(s, 'compact_row', lambda row: dict(row))
    def collect(env, seed, out, counts, identity, *, accounting):
        accounting.update(model_work={'model_fleet_ticks': 12, 'terminal_model_fleet_ticks': 3})
        counts['worker_current_c_calls_attempted'] += 5
        counts['worker_current_c_calls'] += 5
        return dict(seed=seed, deadline_misses=0), raw_fixture(), {}
    monkeypatch.setattr(s, 'collect_episode', collect)
    def replay(raw, row, counts):
        counts['native_lrs_fleet_ticks'] += 2
        counts['native_lrs_row_selections'] += 10
        return dict(inherited={}, max_unserved_gap=1, F_user=0., mean_served=5), {'lrs_test': np.array([1])}, {}
    monkeypatch.setattr(s, 'replay_lrs', replay)
    return tmp_path, env, collect, replay


def test_complete_multiple_episodes_fold_model_and_c_once(batch):
    out, _, _, _ = batch
    result = s.run_batch(out, 'unused', 'sha')
    assert result['status'] == 'COMPLETE'
    assert result['model_counts'] == dict(model_fleet_ticks=24, terminal_model_fleet_ticks=6)
    assert result['counts']['worker_current_c_calls'] == 10
    assert result['counts']['worker_current_c_calls_attempted'] == 10
    assert len(result['episode_accounting']) == len(result['rows']) == 2


def test_missing_accounting_is_explicit_failure_after_source_raw_is_preserved(batch, monkeypatch):
    out, _, collect, _ = batch
    def incomplete(*args, **kwargs):
        result = collect(*args, **kwargs)
        kwargs['accounting'].pop('model_work')
        kwargs['accounting']['errors'] = [dict(phase='model_accounting', type='OSError', message='unavailable')]
        return result
    monkeypatch.setattr(s, 'collect_episode', incomplete)
    result = s.run_batch(out, 'unused', 'sha')
    assert result['status'] == 'INCOMPLETE_TECHNICAL_FAILURE'
    assert result['error']['message'] == 'episode accounting incomplete: model_accounting'
    assert result['model_counts'] == {} and not result['rows']
    assert result['counts']['worker_current_c_calls'] == 5
    assert (out / 'raw' / 'S_F_7.npz').exists()
    assert len(result['incomplete_raw']) == 1


@pytest.mark.parametrize('where', ['collect', 'replay', 'final_npz', 'outcome', 'identity'])
def test_later_failure_retains_paid_prefix_exactly_once(batch, monkeypatch, where):
    out, env, collect, replay = batch
    if where == 'collect':
        def failed(*args, **kwargs):
            _, raw, _ = collect(*args, **kwargs)
            c.atomic_npz(out / 'raw' / 'S_F_7.npz', raw)
            raise ValueError('original failure')
        monkeypatch.setattr(s, 'collect_episode', failed)
    elif where == 'replay':
        def failed(*args):
            replay(*args)
            raise ValueError('original failure')
        monkeypatch.setattr(s, 'replay_lrs', failed)
    elif where == 'final_npz':
        calls = [0]
        def failed(*args):
            calls[0] += 1
            if calls[0] == 2:
                raise ValueError('original failure')
            c.atomic_npz(*args)
        monkeypatch.setattr(s, 'atomic_npz', failed)
    elif where == 'outcome':
        write = s.p.write_json
        def failed(path, value):
            if path.parent.name == 'outcomes':
                raise ValueError('original failure')
            return write(path, value)
        monkeypatch.setattr(s.p, 'write_json', failed)
    else:
        monkeypatch.setattr(s.p, 'file_identity', lambda *args: (_ for _ in ()).throw(ValueError('original failure')))
    env.close = lambda: (_ for _ in ()).throw(OSError('cleanup failure'))
    result = s.run_batch(out, 'unused', 'sha')
    assert result['status'] == 'INCOMPLETE_TECHNICAL_FAILURE'
    assert result['error']['message'] == 'original failure'
    assert result['model_counts'] == dict(model_fleet_ticks=12, terminal_model_fleet_ticks=3)
    assert result['counts']['worker_current_c_calls'] == result['counts']['worker_current_c_calls_attempted'] == 5
    assert len(result['episode_accounting']) == 1 and not result['rows']
    assert result['counts']['native_lrs_row_selections'] == (0 if where == 'collect' else 10)
    assert any(error['phase'] == 'environment_close' for error in result['accounting_errors'])
    path = out / 'raw' / 'S_F_7.npz'
    with np.load(path, allow_pickle=False) as raw:
        assert int(raw['completed_steps']) == 2
        assert ('lrs_test' in raw) == (where in ('outcome', 'identity'))
    persisted = json.loads((out / 'summary.json').read_text())
    assert persisted['model_counts']['model_fleet_ticks'] == 12


def test_final_summary_write_failure_returns_original_identity_and_paid_counts(batch, monkeypatch):
    out, _, _, _ = batch
    def replay(*args):
        args[-1]['native_lrs_row_selections'] += 1
        raise ValueError('original replay failure')
    monkeypatch.setattr(s, 'replay_lrs', replay)
    write = s.p.write_json
    def failed(path, value):
        if path.name == 'summary.json':
            raise OSError('summary unavailable')
        write(path, value)
    monkeypatch.setattr(s.p, 'write_json', failed)
    result = s.run_batch(out, 'unused', 'sha')
    assert result['error']['message'] == 'original replay failure'
    assert result['model_counts']['model_fleet_ticks'] == 12
    assert result['counts']['native_lrs_row_selections'] == 1
    assert result['accounting_errors'][-1]['phase'] == 'summary_write'


def test_hostile_cleanup_representation_does_not_replace_original_failure(batch, monkeypatch):
    out, env, _, _ = batch
    class HostileError(Exception):
        def __str__(self):
            raise RuntimeError('unavailable representation')
    def failed_replay(*args):
        raise ValueError('original replay failure')
    monkeypatch.setattr(s, 'replay_lrs', failed_replay)
    env.close = lambda: (_ for _ in ()).throw(HostileError())
    result = s.run_batch(out, 'unused', 'sha')
    assert result['error']['message'] == 'original replay failure'
    assert result['accounting_errors'][0] == dict(phase='environment_close', type='HostileError',
                                                message='<exception message unavailable>')
    assert result['model_counts']['model_fleet_ticks'] == 12
