"""Mock-only integration: no scorer, optimizer, G, rollout or native host calls."""
from types import SimpleNamespace
import json
import time

import numpy as np
import pytest

from experiments.candidates.uav_decision_generalization.b06_request_amortization import (
    policy as p, worker as w, run,
)
from experiments.candidates.uav_decision_generalization.b06_request_amortization.costs import Meter
from experiments.candidates.uav_decision_generalization.b05_request_schedule import rollout as old_rollout


def meter(tmp_path):
    return Meter({'cumulative_cpu_seconds': 0., 'aggregate_operation_wall_seconds': 0.},
                 time.monotonic(), disk_roots=[tmp_path])


def test_r1_stops_before_second_tape_and_r4_keeps_original_result(monkeypatch):
    visited, publications = [], []
    def original(state, raw, trace, publish, source):
        cohorts = []
        for tape in range(4):
            visited.append(tape)
            cohorts.append({'tape': tape})
            publish({'cohorts': list(cohorts)})
        return {'cohorts': cohorts, 'original_extra': 42}
    monkeypatch.setattr(old_rollout, 'search', original)
    result = p.search(None, None, None, publications.append, 'synthetic', 1)
    assert visited == [0] and publications == [{'cohorts': [{'tape': 0}]}]
    assert result == {'cohorts': [{'tape': 0}], 'cohort_limit': 1}
    visited.clear()
    publications.clear()
    result = p.search(None, None, None, publications.append, 'synthetic', 4)
    assert visited == [0, 1, 2, 3] and len(publications) == 4
    assert result['original_extra'] == 42
    with pytest.raises(ValueError):
        p.search(None, None, None, publications.append, 'synthetic', 2)


def test_r1_does_not_swallow_a_failed_publication(monkeypatch):
    def original(state, raw, trace, publish, source):
        publish({'cohorts': [{'tape': 0}]})
    monkeypatch.setattr(old_rollout, 'search', original)
    def fail(_):
        raise OSError('synthetic pipe failure')
    with pytest.raises(OSError, match='pipe failure'):
        p.search(None, None, None, fail, 'synthetic', 1)


def test_late_constant_is_diagnostic_and_cannot_replace_keep(tmp_path, monkeypatch):
    endpoint = p.Endpoint({'kind': 'B'}, tmp_path / 'B', meter(tmp_path), 'synthetic')
    times = iter((100, 101, 20_000_000_102, 20_000_000_103, 20_000_000_104, 20_000_000_105))
    monkeypatch.setattr(p.inherited.time, 'monotonic_ns', lambda: next(times))
    monkeypatch.setattr(endpoint, '_start', lambda: None)
    endpoint.connection = SimpleNamespace(send=lambda value: None)
    def late_message(_):
        endpoint.cache['g_complete'][0] = 1
        endpoint.cache['raw_g'][0] = [2., 1., 3., 4.]
        endpoint.cache['constant_complete'][0] = 1
        endpoint.cache['total_q'][0] = [2., 1., -3., 4.]
        endpoint.cache['greedy_action'][0] = 2
        return {'type': 'result', 'payload': {'action': 2}, 'ready_ns': 1000}
    monkeypatch.setattr(endpoint, '_message', late_message)
    reaps = []
    monkeypatch.setattr(endpoint, '_reap', lambda **kwargs: reaps.append(kwargs))
    state = SimpleNamespace(active_slots=np.arange(6, dtype=np.uint8))
    answer = endpoint.decide(state)
    assert answer['timing']['deadline_expired']
    assert answer['timing']['messages'][0]['eligible'] is False
    assert answer['action'] == 0 and np.array_equal(answer['command'], state.active_slots)
    assert answer['score_complete'] and answer['greedy_action'] == 2
    assert np.array_equal(answer['total_q'], [2., 1., -3., 4.])
    assert reaps == [{'terminate': True}]
    endpoint.connection = None
    endpoint.close()


def test_endpoint_starts_once_until_real_reap(tmp_path, monkeypatch):
    endpoint = p.Endpoint({'kind': 'G'}, tmp_path / 'G', meter(tmp_path), 'synthetic')
    starts, closed = [], []
    parent = SimpleNamespace(close=lambda: closed.append('parent'))
    child = SimpleNamespace(close=lambda: closed.append('child'))
    class Process:
        pid = 123456
        def __init__(self, **kwargs):
            self.kwargs = kwargs
        def start(self):
            starts.append(self.kwargs)
    context = SimpleNamespace(Pipe=lambda **kwargs: (parent, child), Process=Process)
    monkeypatch.setattr(p.mp, 'get_context', lambda name: context)
    endpoint._start()
    endpoint._start()
    assert len(starts) == 1 and endpoint.starts == 1 and closed == ['child']
    assert starts[0]['target'] is p._child and endpoint.process.pid in endpoint.meter.live
    endpoint.process = endpoint.connection = None  # Only fabricated objects exist.
    endpoint.meter.live.clear()
    endpoint.close()


def test_worker_applies_command_only_after_twenty_ticks_and_preserves_prefix(tmp_path, monkeypatch):
    advances = []
    class Host:
        def __init__(self, world):
            self.user_positions = np.zeros((50, 2), dtype=np.int32)
            self.uav_positions = np.zeros((6, 3), dtype=np.float64)
            self.event_counts = {}
        def snapshot(self):
            return {}
        def ack(self):
            return np.zeros(50, dtype=bool)
        def advance(self, active, users):
            if len(advances) == 22:
                raise RuntimeError('synthetic failure after22')
            advances.append(active.copy())
            return np.zeros((6, 3)), np.zeros((6, 3)), {}
    class Ledger:
        counts = np.zeros(4, dtype=np.uint16)
        progress = np.zeros(4, dtype=np.uint8)
        def start_tick(self, tick, arrivals):
            return 0
        def finish_tick(self, tick, ack):
            pass
    monkeypatch.setattr(w, 'RequestHost', Host)
    monkeypatch.setattr(w, 'QueueLedger', Ledger)
    monkeypatch.setattr(w, 'initial_assignment', lambda *args: (np.zeros(6, dtype=np.uint8), np.zeros((3, 2), dtype=np.uint8)))
    monkeypatch.setattr(w, 'put_state', lambda row, snap, counts, progress, slots, tick: None)
    monkeypatch.setattr(w, 'put_g', lambda *args: None)
    monkeypatch.setattr(w, 'pack_reset', lambda *args: b'')
    monkeypatch.setattr(w, 'pack_report', lambda *args: b'')
    monkeypatch.setattr(w, 'pack_command', lambda *args: b'')
    monkeypatch.setattr(w, 'PublicState', lambda *args: SimpleNamespace(tick=args[1], active_slots=args[8]))
    def decide(state, trace):
        return {'command': np.full(6, 1 + state.tick // 20, dtype=np.uint8), 'action': 1,
                'raw_g': None, 'features': None, 'g_action': None, 'greedy_action': None,
                'total_q': None, 'residual': None, 'score_complete': False, 'timing': {}, 'cohorts': []}
    endpoint = SimpleNamespace(spec={'kind': 'G'}, decide=decide, counters=lambda: {})
    budget, records = meter(tmp_path), []
    with pytest.raises(RuntimeError, match='after22'):
        w.mission(tmp_path, 17, 'main/G', endpoint, budget, records)
    assert np.array_equal(np.stack(advances[:20]), np.zeros((20, 6)))
    assert np.array_equal(np.stack(advances[20:]), np.ones((2, 6)))
    assert budget.counts['actual_native_attempts'] == 23
    assert budget.counts['actual_native_steps'] == 22
    metadata = json.loads((tmp_path / 'raw/main/G/17.json').read_text())
    assert metadata['status'] == 'FAILED' and metadata['completed_native_steps'] == 22
    assert metadata['completed_decisions'] == 2 and records[0]['status'] == 'FAILED'
    assert all(row['score_complete'] is False for row in metadata['decisions'])
    with np.load(tmp_path / 'raw/main/G/17.npz', allow_pickle=False) as arrays:
        assert not arrays['nn_complete'].any() and not arrays['score_complete'].any()


def test_entry_rejects_unselected_seed_before_any_admission():
    arguments = ['--mode', 'worker', '--seed', '17', '--launch-sha', 'synthetic', '--out', '/nonexistent',
                 '--study-input', '/nonexistent', '--study-input-sha256', 'synthetic',
                 '--budget-ledger', '/nonexistent', '--budget-ledger-sha256', 'synthetic']
    with pytest.raises(ValueError, match='fixed literal'):
        run.main(arguments)


def test_allocation_bounds_cover_fixed_schema_bytes():
    assert w.mission_allocation_bound(False) > 2 * w.bytes_for_shapes(w.MISSION_SHAPES)
    assert w.mission_allocation_bound(True) > 61 * 2 * w.bytes_for_shapes(w.R_SHAPES)
    assert w.mission_allocation_bound(True) < 256 * 1024**2


def test_worker_orchestrates_one_acquisition_before_rotated_frozen_roster(tmp_path, monkeypatch):
    events, endpoints = [], []
    bank = SimpleNamespace(identity='synthetic-bank', features=np.zeros((1, 4, 303), dtype=np.float32),
                           raw_g=np.zeros((1, 4)), teacher=np.zeros((1, 4)), keys=((17, 0),), provenance={})
    def bind(*args, **kwargs):
        events.append('bank')
        return bank
    def constant(*args, **kwargs):
        events.append('B-fit')
        return {'counts': {'solves': 1}, 'b': np.zeros(4)}
    def fit(bank, index, out, **kwargs):
        events.append('fit' + str(index))
        out.mkdir(parents=True)
        checkpoint = out / 'synthetic.pt'
        checkpoint.write_bytes(b'not-a-model')
        return {'fit': index, 'final': w.e.identity(checkpoint),
                'counts': {'updates': 2112, 'backwards': 2112, 'forward_rows': 537600},
                'initial_forward_counts': {'forward_rows': 8400}, 'final_forward_counts': {'forward_rows': 8400}}
    class Endpoint:
        def __init__(self, spec, directory, budget, source):
            self.spec, self.directory, self.starts = spec, directory, 0
            endpoints.append(self)
        def close(self):
            events.append('close-' + self.directory.name)
            return {}
    def mission(out, world, label, endpoint, budget, records):
        events.append((world, label))
        records.append({'world': world, 'label': label, 'status': 'COMPLETE', 'completed_native_steps': 1200})
    monkeypatch.setattr(w.a, 'binding_bank', bind)
    monkeypatch.setattr(w.a, 'solve_constant', constant)
    monkeypatch.setattr(w.a, 'fit_endpoint', fit)
    monkeypatch.setattr(w, 'Endpoint', Endpoint)
    monkeypatch.setattr(w, 'mission', mission)
    (tmp_path / 'config.json').write_text('{}')
    args = SimpleNamespace(launch_sha='synthetic-launch')
    w.run(tmp_path, tmp_path, args, {'meter': meter(tmp_path), 'source_identity': 'synthetic-source',
                                   'teacher_root': 'synthetic-old-root', 'teacher_reader_summary': 'synthetic-reading'})
    assert events[:5] == ['bank', 'B-fit', 'fit0', 'fit1', 'fit2']
    assert events[5:229] == w.c.expected_roster()
    assert [endpoint.directory.name for endpoint in endpoints] == list(w.c.ARMS)
    assert all(endpoint.starts == 0 for endpoint in endpoints)
    b_spec = endpoints[3].spec
    assert b_spec['constant_launch_sha'] == 'synthetic-launch' and b_spec['bank_identity'] == 'synthetic-bank'
    assert [endpoint.spec['fit'] for endpoint in endpoints[4:]] == [0, 1, 2]
    summary = json.loads((tmp_path / 'summary.json').read_text())
    assert summary['missions'] == 224 and summary['acquisition_totals']['updates'] == 6336
    assert summary['acquisition_totals']['bank_endpoint_neural_rows'] == 50400
    assert summary['bank_handling_cost']['cpu_seconds'] >= 0
