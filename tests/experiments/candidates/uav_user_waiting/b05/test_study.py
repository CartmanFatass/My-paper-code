"""Synthetic hash/source/input, numerical and streaming producer fixtures."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import types

import numpy as np
import pytest

from experiments.candidates.uav_user_waiting.b05 import protocol as p, study as s, run


@pytest.fixture
def radio():
    counts = s.counters()
    binding = p.file_identity(s.ROOT / p.RADIO_PATH)
    return s.load_radio(s.ROOT, binding, counts)


def scalar_reference(contacts):
    H, U = contacts.shape
    ages = np.zeros((H, U), np.int16)
    gaps = []
    maxima = []
    for user in range(U):
        age, start, maximum = 0, None, 0
        for tick in range(H):
            age = 0 if contacts[tick, user] else age + 1
            ages[tick, user] = age
            if not contacts[tick, user] and start is None:
                start = tick
            if contacts[tick, user] and start is not None:
                gaps.append([user, start, tick, tick-start, int(start == 0), 0])
                maximum = max(maximum, tick-start)
                start = None
        if start is not None:
            gaps.append([user, start, H, H-start, int(start == 0), 1])
            maximum = max(maximum, H-start)
        maxima.append(maximum)
    return ages, np.array(gaps, np.int64).reshape(-1, 6), maxima


def fixture_trace(radio, H=8, program='M', seed=p.SEED):
    values = np.full((H, 5, 50), -10., np.float64)
    values[:, 0, :15] = 10 + np.arange(15)/10
    values[:, 1, 15:25] = 8 + np.arange(10)/10
    values[:, 3, 25:27] = 3.
    values[:, 4, 27:30] = 20.
    masks = np.full(H, 31, np.uint8)
    if H > 2:
        values[2, 0] = -10.
    if H > 3:
        values[3, 0, 0] = -10.
        values[3, 1, 0] = 25.
    if H > 4:
        masks[4] &= ~(1 << 1)
        values[4, 1] = -np.inf
    connections = np.array([radio.greedy_connection_assignment(v) for v in values])
    metrics = [radio.service_metrics(v, c) for v, c in zip(values, connections)]
    contacts = connections.any(axis=1)
    ages, gaps, maxima = scalar_reference(contacts)
    raw = dict(program=np.array(program), world_seed=np.array(seed), completed_steps=np.array(H),
               sinr=values, connections=connections, mask=masks,
               served=np.array([m['served'] for m in metrics], np.int16),
               quality=np.array([m['quality'] for m in metrics], np.float64),
               reward=np.array([m['J'] for m in metrics], np.float64), actual_contacts=contacts,
               actual_ages=ages, unserved_gap_rows=gaps, per_user_mean_age=ages.mean(axis=0),
               reset_connections=np.ones((5, 50), bool))  # unscored contacts are ignored
    row = dict(arm=program, seed=seed, steps=H, J=float(raw['reward'].mean()), return_sum=float(raw['reward'].sum()),
               mean_served=float(raw['served'].mean()), mean_quality=float(raw['quality'].mean()),
               A=float(ages.mean()), age_sum=int(ages.sum()), F_user=float(ages.mean(axis=0).max()),
               max_user_mean_age=float(ages.mean(axis=0).max()), max_unserved_gap=max(maxima),
               mean_user_max_unserved_gap=float(np.mean(maxima)), age_p95=float(np.quantile(ages, .95)),
               terminal_mean_age=float(ages[-1].mean()), terminal_max_age=int(ages[-1].max()),
               mean_age_square=float(np.square(ages.astype(np.int64)).mean()),
               age_square_sum=int(np.square(ages.astype(np.int64)).sum()),
               per_user_mean_age=ages.mean(axis=0).tolist(), per_user_gaps={'old': 'excluded'}, worst_users=[49])
    row.update({key: 0 for key in p.INHERITED_METRICS})
    row.update(cpu_seconds=.25, wall_seconds=.5, controller_counts={'decisions': 10})
    return raw, row


def destination(tmp_path):
    out = tmp_path / 'result'
    out.mkdir()
    (out / 'contacts').mkdir()
    (out / 'outcomes').mkdir()
    return out


def source_identity(raw, row, tmp_path):
    path = tmp_path / f"{row['arm']}_{row['seed']}.npz"
    np.savez_compressed(path, **raw)
    return p.file_identity(path)


def test_standalone_source_import_never_imports_envs_or_torch(tmp_path):
    code = """
import sys
from experiments.candidates.uav_user_waiting.b05 import protocol as p, study as s
module = s.load_radio(s.ROOT, p.file_identity(s.ROOT / p.RADIO_PATH), s.counters())
assert 'torch' not in sys.modules and 'envs' not in sys.modules
assert module.greedy_connection_assignment.__module__ == '_b05_frozen_radio'
"""
    import os
    env = dict(os.environ, PYTHONPATH=str(s.ROOT))
    completed = subprocess.run([sys.executable, '-c', code], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr


def test_full_synthetic_trace_baseline_counts_streams_and_unserved_partition(radio, tmp_path):
    raw, row = fixture_trace(radio)
    source = source_identity(raw, row, tmp_path)
    out, counts = destination(tmp_path), s.counters()
    compact, artifacts, differences, timing = s.produce_trace(raw, row, source, out, counts, radio, horizon=8)
    assert len(compact) == 3 and all(r['complete'] for r in compact)
    assert counts['source_ticks'] == counts['original_kernel_calls'] == 8
    assert counts['fleet_allocations'] == counts['transition_reductions'] == 24
    assert counts['uav_allocation_decisions'] == 120
    assert counts['rr_row_selections'] == counts['lrs_row_selections'] == 40
    assert counts['user_age_updates'] == 1200 and counts['threshold_entries'] == 4000
    assert counts['threshold_scans'] == 16
    assert counts['original_outcomes'] == 1 and counts['fair_outcomes'] == 2
    assert all(counts[key] == 0 for key in p.ZERO_COUNTS)
    assert max(differences.values()) <= p.ATOL
    assert all(v >= 0 for v in timing.values())
    details = p.read_json(out / 'outcomes' / f'M_{p.SEED}.json')
    assert details['gap_columns'] == list(p.GAP_COLUMNS) and details['complete']
    assert len(details['rows']) == 3
    for item in details['rows']:
        assert item['mean_served'] == row['mean_served']
        assert item['J'] <= row['J'] + p.ATOL
        assert item['mean_quality'] <= row['mean_quality'] + p.ATOL
        assert 'per_user_mean_age' not in item['inherited'] and 'per_user_gaps' not in item['inherited']
        assert item['inherited']['cpu_seconds'] == .25
        assert item['inherited']['controller_counts'] == {'decisions': 10}
        for user in item['per_user']:
            assert user['capacity_denied_ticks'] + user['no_link_ticks'] == 8 - user['service_count']
            for start, end, left, right, denied, no_link in user['gaps']:
                assert denied + no_link == end - start
                assert left == int(start == 0) and right == int(end == 8)
        never = item['per_user'][49]
        assert never['mean_age'] == 4.5 and never['terminal_age'] == never['max_gap'] == 8
        assert never['gaps'] == [[0, 8, 1, 1, 0, 8]]
        assert never['no_link_intervals'] == [[0, 8, 1, 1]]
    assert compact[0]['changed_grant_user_ticks'] == 0
    assert compact[1]['changed_grant_user_ticks'] > 0
    with np.load(out / 'contacts' / f'M_{p.SEED}.npz', allow_pickle=False) as saved:
        assert saved['contacts'].shape == (2, 8, 50) and saved['contacts'].dtype == bool
        np.testing.assert_array_equal(saved['completed_steps'], [8, 8])
        np.testing.assert_array_equal(saved['laws'], ['RR', 'LRS'])
        assert str(saved['source_sha256']) == source['sha256']
        assert 'sinr' not in saved.files and 'connections' not in saved.files
    for identity in artifacts:
        assert p.file_identity(identity['path']) == identity
    with pytest.raises(ValueError, match='no retry'):
        s.produce_trace(raw, row, source, out, counts, radio, horizon=8)


@pytest.mark.parametrize('fault', ['connections', 'served', 'quality', 'reward', 'ages', 'gaps', 'row', 'overlap', 'off', 'active_nonfinite', 'truncated'])
def test_invalid_source_stops_and_retains_paid_prefix(fault, radio, tmp_path):
    raw, row = fixture_trace(radio)
    if fault == 'connections': raw['connections'][3, 0, 0] = True
    elif fault == 'served': raw['served'][3] += 1
    elif fault == 'quality': raw['quality'][3] += .01
    elif fault == 'reward': raw['reward'][3] += .01
    elif fault == 'ages': raw['actual_ages'][3, 49] += 1
    elif fault == 'gaps': raw['unserved_gap_rows'][0, 2] += 1
    elif fault == 'row': row['F_user'] += 1
    elif fault == 'overlap': raw['sinr'][3, 1, 1] = 6.
    elif fault == 'off': raw['sinr'][4, 1, 0] = -2.
    elif fault == 'active_nonfinite': raw['sinr'][3, 0, 49] = -np.inf
    else: raw['sinr'] = raw['sinr'][:7]
    source = source_identity(raw, row, tmp_path)
    out, counts = destination(tmp_path), s.counters()
    with pytest.raises(ValueError) as error:
        s.produce_trace(raw, row, source, out, counts, radio, horizon=8)
    paid = error.value.b05_paid_prefix
    assert len(paid['rows']) == 3 and not paid['details']['complete']
    assert all(not r['complete'] for r in paid['rows'])
    assert counts['original_outcomes'] == counts['fair_outcomes'] == counts['source_traces'] == 0
    assert counts['original_kernel_calls'] < 8 if fault in ('connections','served','quality','reward','overlap','off','active_nonfinite','truncated') else counts['original_kernel_calls'] == 8
    assert all(Path(a['path']).is_file() for a in paid['artifacts'])
    with np.load(out / 'contacts' / f'M_{p.SEED}.npz', allow_pickle=False) as saved:
        done = saved['completed_steps']
        assert done.shape == (2,)
        for law, count in enumerate(done):
            assert not saved['contacts'][law, count:].any()


def test_uneven_rule_failure_retains_original_and_rr_completed_work(radio, monkeypatch, tmp_path):
    original = s.LeastRecentlyServed.grant
    def fail(self, ids, values, tick):
        if tick == 2:
            raise RuntimeError('synthetic interrupted LRS')
        return original(self, ids, values, tick)
    monkeypatch.setattr(s.LeastRecentlyServed, 'grant', fail)
    raw, row = fixture_trace(radio)
    source = source_identity(raw, row, tmp_path)
    out, counts = destination(tmp_path), s.counters()
    with pytest.raises(RuntimeError) as error:
        s.produce_trace(raw, row, source, out, counts, radio, horizon=8)
    assert error.value.b05_paid_prefix['details']['completed_by_law'] == {'ORIGINAL': 3, 'RR': 3, 'LRS': 2}
    assert counts['original_kernel_calls'] == 3 and counts['rr_row_selections'] == 15
    assert counts['lrs_row_selections'] == 11 and counts['transition_reductions'] == 8


def test_quality_ceiling_violation_stops_even_when_bad_original_bits_match(tmp_path):
    # Analytical failing baseline: an intentionally suboptimal original comparator.
    module = types.SimpleNamespace(greedy_connection_assignment=lambda values, **kwargs: np.array(
        [[user < 10 for user in range(50)]] + [[False]*50 for _ in range(4)], bool),
        service_metrics=lambda values, connections: dict(served=10, quality=float(np.clip((values[connections]-3)/30, 0, 1).mean()),
            J=.7*10/50 + .3*float(np.clip((values[connections]-3)/30, 0, 1).mean())))
    raw, row = fixture_trace(module, H=1)
    raw['sinr'][0, 1:] = -10.
    raw['sinr'][0, 0, :15] = np.arange(15) + 3.
    bad = module.service_metrics(raw['sinr'][0], raw['connections'][0])
    raw['quality'][0], raw['reward'][0] = bad['quality'], bad['J']
    source = source_identity(raw, row, tmp_path)
    out, counts = destination(tmp_path), s.counters()
    with pytest.raises(ValueError, match='ceiling'):
        s.produce_trace(raw, row, source, out, counts, module, horizon=1)


def test_contact_age_and_gap_boundary_fixtures():
    contacts = np.zeros((6, 50), bool)
    contacts[:, 0] = True
    contacts[[2, 4], 1] = True
    ages, gaps, maximum = scalar_reference(contacts)
    eligible = np.zeros((6, 5, 50), bool)
    eligible[:, 0, :2] = True
    eligible[1, 0, 1] = False
    stats = s.outcome(contacts, ages, np.zeros((6, 3)), eligible, np.zeros((6, 5), bool), contacts,
                      dict(arm='M', seed=0), 'ORIGINAL', True)
    assert stats['per_user'][0]['gaps'] == []
    assert stats['per_user'][1]['gaps'] == [[0, 2, 1, 0, 1, 1], [3, 4, 0, 0, 1, 0], [5, 6, 0, 1, 1, 0]]
    assert stats['per_user'][2]['gaps'] == [[0, 6, 1, 1, 0, 6]]
    assert stats['max_closed_gap'] == 1 and stats['max_unserved_gap'] == 6
    assert stats['per_user'][1]['mean_age'] == 5/6


def test_paired_complete_36_vectors_and_fixed_descriptive_t95():
    rows = []
    seeds = tuple(range(64))
    for index, package in enumerate(p.PACKAGES):
        for seed in seeds:
            row = dict(package=package, seed=seed, complete=True)
            row.update({key: index * seed for key in p.OUTCOME_METRICS})
            row['inherited'] = {key: index * seed for key in p.INHERITED_METRICS}
            rows.append(row)
    paired = s.paired_reading(rows, seeds)
    assert len(paired['contrasts']) == 36
    chosen = paired['contrasts']['M:RR-M:ORIGINAL']['F_user']
    assert chosen['values'] == list(seeds) and chosen['n'] == 64
    half = p.T_CRITICAL * np.std(seeds, ddof=1) / 8
    np.testing.assert_allclose(chosen['descriptive_t95'], [31.5-half, 31.5+half], rtol=0, atol=p.ATOL)
    with pytest.raises(ValueError, match='incomplete'):
        s.paired_reading(rows[:-1], seeds)
    assert p.expected_counts()['original_kernel_calls'] == 49152
    assert p.expected_counts()['rr_row_selections'] == p.expected_counts()['lrs_row_selections'] == 245760
    assert p.expected_counts()['fleet_allocations'] == 147456


def test_selective_hash_bound_trace_load_rejects_objects_corruption_and_missing_fields(radio, tmp_path):
    raw, row = fixture_trace(radio)
    raw['unneeded_bulk'] = np.array([object()], object)
    identity = source_identity(raw, row, tmp_path)
    counts = s.counters()
    loaded = s.load_trace(identity, counts)
    assert set(loaded) == set(s.RAW_FIELDS) and 'unneeded_bulk' not in loaded
    assert counts['input_hash_bytes'] == counts['hash_bytes'] == identity['bytes']
    np.testing.assert_array_equal(loaded['sinr'], raw['sinr'])
    wrong = dict(identity, sha256='0'*64)
    with pytest.raises(ValueError, match='hash'):
        s.load_trace(wrong, counts)
    raw['sinr'] = np.array([object()], object)
    bad = source_identity(raw, row, tmp_path)
    with pytest.raises(ValueError, match='Object arrays'):
        s.load_trace(bad, counts)
    del raw['sinr']
    bad = source_identity(raw, row, tmp_path)
    with pytest.raises(KeyError):
        s.load_trace(bad, counts)


def metadata(tmp_path, monkeypatch):
    source_root = tmp_path / 'frozen'
    bindings = []
    for name in p.SOURCE_PATHS:
        path = source_root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('synthetic source: ' + name)
        bindings.append(dict(p.file_identity(path), path=name))
    run_root = tmp_path / 'b04'
    run_root.mkdir()
    monkeypatch.setattr(p, 'B04_CANONICAL_RUN', run_root)
    summary_path, reading_path = run_root / 'summary.json', tmp_path / 'reading.json'
    rows = [dict(arm=program, seed=seed, steps=256, raw=dict(path=str(run_root / 'raw' / f'{program}_{seed}.npz'),
                bytes=0, sha256='0'*64)) for seed in p.SEEDS for program in ('M','S','U','K')]
    config = dict(launch_sha=p.SOURCE_SHA, seeds=list(p.SEEDS), arms=['M','S','U','K'], horizon=256, nodes=5, users=50,
                  source_identities=bindings)
    summary = dict(object='UAV-USER-WAITING-B04', status='COMPLETE', scientific_invocation=True, launch_sha=p.SOURCE_SHA,
                   config=config, rows=rows, artifacts=[row['raw'] for row in rows], counts=dict(constructors=1,
                   explicit_resets=256, native_step_calls=65536, team_steps=65536, complete_episodes=256, fit_started=0, optimizer_steps=0))
    p.write_json(summary_path, summary)
    summary_id = p.file_identity(summary_path)
    reading = dict(status='VERIFIED_COMPLETE', worker_launch_sha=p.SOURCE_SHA, expected_summary_sha256=summary_id['sha256'],
                   worker_summary=summary_id, rows=[dict(arm=row['arm'], seed=row['seed']) for row in rows], counts=dict(verified_raw_files=256))
    p.write_json(reading_path, reading)
    monkeypatch.setattr(p, 'SUMMARY_SHA256', summary_id['sha256'])
    monkeypatch.setattr(p, 'READING_SHA256', p.file_identity(reading_path)['sha256'])
    return summary_path, reading_path, source_root


def test_frozen_metadata_bindings_and_source_changes(tmp_path, monkeypatch):
    paths = metadata(tmp_path, monkeypatch)
    counts = s.counters()
    result = s.validate_inputs(*paths, counts)
    assert len(result[2]) == len(p.SOURCE_PATHS) and len(result[3]) == 256
    assert counts['input_hash_files'] == len(p.SOURCE_PATHS) + 2
    (paths[2] / p.RADIO_PATH).write_text('changed')
    with pytest.raises(ValueError, match='source mismatch'):
        s.validate_inputs(*paths, counts)
    assert counts['fleet_allocations'] == 0


def test_relocated_metadata_preserves_canonical_members_without_original_files(tmp_path, monkeypatch):
    from experiments.candidates.uav_user_waiting.b05 import reader
    summary, reading, source_root = metadata(tmp_path, monkeypatch)
    frozen = p.read_json(summary)
    # This metadata-only fixture meets the independent inventory byte constraint.
    frozen['rows'][0]['raw']['bytes'] = 262741183
    frozen['artifacts'][0]['bytes'] = 262741183
    p.write_json(summary, frozen)
    summary_id = p.file_identity(summary)
    original_reading = p.read_json(reading)
    original_reading.update(worker_summary=summary_id, expected_summary_sha256=summary_id['sha256'])
    p.write_json(reading, original_reading)
    monkeypatch.setattr(p, 'SUMMARY_SHA256', summary_id['sha256'])
    monkeypatch.setattr(p, 'READING_SHA256', p.file_identity(reading)['sha256'])
    stage = tmp_path / 'stage'
    stage.mkdir()
    staged_summary, staged_reading = stage / 'summary.json', stage / 'reading.json'
    staged_summary.write_bytes(summary.read_bytes())
    staged_reading.write_bytes(reading.read_bytes())
    summary.unlink()
    reading.unlink()
    _, _, _, producer_rows, _ = s.validate_inputs(staged_summary, staged_reading, source_root, s.counters())
    independent_rows, source = reader.read_source(stage, staged_reading, s.counters(), source_root)
    assert len(independent_rows) == 192
    assert source['summary']['path'] == str(staged_summary)
    for key, row in independent_rows.items():
        member = f'{key[0]}_{key[1]}.npz'
        assert row['raw'] == producer_rows[key]['raw']
        assert row['raw']['path'] == str(stage / 'raw' / member)
        assert row['raw']['canonical_path'] == str(p.B04_CANONICAL_RUN / 'raw' / member)

    # Rehashing a synthetic substituted manifest must not remove membership checks.
    changed = p.read_json(staged_summary)
    wrong_path = str(p.B04_CANONICAL_RUN / 'raw' / 'wrong_member.npz')
    changed['rows'][0]['raw']['path'] = wrong_path
    changed['artifacts'][0]['path'] = wrong_path
    p.write_json(staged_summary, changed)
    changed_id = p.file_identity(staged_summary)
    original_reading.update(worker_summary=dict(changed_id, path=str(summary)),
                            expected_summary_sha256=changed_id['sha256'])
    p.write_json(staged_reading, original_reading)
    monkeypatch.setattr(p, 'SUMMARY_SHA256', changed_id['sha256'])
    monkeypatch.setattr(p, 'READING_SHA256', p.file_identity(staged_reading)['sha256'])
    with pytest.raises(ValueError, match='canonical member'):
        s.validate_inputs(staged_summary, staged_reading, source_root, s.counters())
    with pytest.raises(ValueError, match='path binding'):
        reader.read_source(stage, staged_reading, s.counters(), source_root)


def test_run_failure_summary_keeps_prefix_counts_and_refuses_retry(tmp_path, monkeypatch):
    paths = metadata(tmp_path, monkeypatch)
    (paths[2] / p.RADIO_PATH).write_text('bad source before replay')
    out = tmp_path / 'b05'
    result = s.run_batch(out, 'a'*40, *paths, admission=dict(sha='a'*40))
    assert result['status'] == 'INCOMPLETE_TECHNICAL_FAILURE'
    assert result['counts']['fleet_allocations'] == result['counts']['native_steps'] == 0
    assert result['counts']['hash_files'] >= 3
    assert result['resources']['process_user_seconds'] >= 0 and result['resources']['peak_rss_kib'] > 0
    assert p.read_json(out / 'summary.json') == result
    assert p.read_json(out / 'config.json') == result['config']
    with pytest.raises(FileExistsError, match='no implicit'):
        s.run_batch(out, 'a'*40, *paths)


def test_cli_admission_precedes_any_result_effects(tmp_path, monkeypatch):
    order = []
    module = types.ModuleType('scripts.hmasd_admission')
    def admission(*args, **kwargs):
        order.append('admission')
        assert not (tmp_path / 'out').exists()
        return dict(sha='a'*40)
    module.require_admission = admission
    monkeypatch.setitem(sys.modules, 'scripts.hmasd_admission', module)
    def batch(*args, **kwargs):
        order.append('batch')
        assert kwargs['admission']['sha'] == 'a'*40
        assert args[2] == tmp_path/'summary.json'
        assert args[3] == tmp_path.parent/'b04_service_floor_read_a01'/'reading.json'
        assert args[4] == run.ROOT
        return dict(status='COMPLETE')
    monkeypatch.setattr(s, 'run_batch', batch)
    args = ['--out', str(tmp_path/'out'), '--seed', str(p.SEED), '--launch-sha', 'a'*40,
            '--generic-summary', str(tmp_path/'summary.json'), '--generic-summary-sha256', p.SUMMARY_SHA256]
    assert run.main(args)['status'] == 'COMPLETE' and order == ['admission','batch']
    order.clear()
    with pytest.raises(SystemExit):
        run.main([*args, '--seed', '1'])
    assert order == []
    with pytest.raises(RuntimeError, match='digest mismatch'):
        run.main([*args, '--generic-summary-sha256', '0'*64])
    assert order == ['admission']


def tiny_runner_inputs(tmp_path, monkeypatch, radio):
    """Test-only dependency injection; the admitted CLI exposes no smaller panel."""
    by = {}
    for program in p.PROGRAMS:
        raw, row = fixture_trace(radio, program=program)
        row['raw'] = source_identity(raw, row, tmp_path)
        by[program, p.SEED] = row
    summary, reading = tmp_path/'summary.json', tmp_path/'reading.json'
    p.write_json(summary, {})
    p.write_json(reading, {})
    monkeypatch.setattr(s, 'validate_inputs', lambda *args: (
        p.file_identity(summary), p.file_identity(reading), [], by, p.file_identity(s.ROOT/p.RADIO_PATH)))
    monkeypatch.setattr(p, 'SEEDS', (p.SEED,))
    expected = dict(source_traces=3, original_outcomes=3, fair_outcomes=6, source_ticks=24,
        fleet_allocations=72, uav_allocation_decisions=360, original_kernel_calls=24,
        rr_row_selections=120, lrs_row_selections=120, transition_reductions=72, user_age_updates=3600,
        threshold_scans=48, threshold_entries=12000, contact_values_retained=2400,
        fair_contact_valid_user_ticks=2400, **{key: 0 for key in p.ZERO_COUNTS})
    monkeypatch.setattr(p, 'expected_counts', lambda: expected)
    original = s.produce_trace
    monkeypatch.setattr(s, 'produce_trace', lambda *args, **kwargs: original(*args, **kwargs, horizon=8))
    return summary, reading, s.ROOT


def test_streaming_runner_complete_artifacts_config_and_all_package_rows(radio, tmp_path, monkeypatch):
    paths = tiny_runner_inputs(tmp_path, monkeypatch, radio)
    out = tmp_path / 'producer'
    result = s.run_batch(out, 'a'*40, *paths, admission=dict(sha='a'*40))
    assert result['status'] == 'COMPLETE', result.get('error')
    assert len(result['rows']) == 9 and len(result['artifacts']) == 6 and len(result['sources']) == 3
    assert set(row['package'] for row in result['rows']) == set(p.PACKAGES)
    assert len(result['paired']['contrasts']) == 36
    assert result['counts']['fleet_allocations'] == 72
    assert result['counts']['input_hash_files'] == len(result['config']['source_identities']) + 1 + 3
    assert result['counts']['raw_array_bytes_loaded'] > 0
    assert result['counts']['contact_values_retained'] == result['counts']['fair_contact_valid_user_ticks'] == 2400
    assert result['counts']['contact_bytes_written'] == sum(a['bytes'] for a in result['artifacts'] if a['path'].endswith('.npz'))
    for row in result['rows']:
        assert 'per_user' not in row and len(row['per_user_vectors']['mean_age']) == 50
        details = p.read_json(row['outcome']['path'])
        full = next(item for item in details['rows'] if item['law'] == row['law'])
        for key in p.VECTOR_FIELDS:
            assert row['per_user_vectors'][key] == [user[key] for user in full['per_user']]
    assert p.read_json(out/'summary.json') == result
    assert p.read_json(out/'config.json') == result['config']


def test_streaming_runner_failure_preserves_completed_trace_and_partial_next_trace(radio, tmp_path, monkeypatch):
    paths = tiny_runner_inputs(tmp_path, monkeypatch, radio)
    grant = s.LeastRecentlyServed.grant
    instances = [0]
    constructor = s.LeastRecentlyServed.__init__
    def init(self):
        constructor(self)
        self.fixture_member = instances[0]
        instances[0] += 1
    def fail(self, ids, values, tick):
        if self.fixture_member == 5 and tick == 2:
            raise RuntimeError('synthetic next-trace failure')
        return grant(self, ids, values, tick)
    monkeypatch.setattr(s.LeastRecentlyServed, '__init__', init)
    monkeypatch.setattr(s.LeastRecentlyServed, 'grant', fail)
    result = s.run_batch(tmp_path/'producer', 'a'*40, *paths, admission=dict(sha='a'*40))
    assert result['status'] == 'INCOMPLETE_TECHNICAL_FAILURE'
    assert len(result['rows']) == 3 and len(result['partial_rows']) == 3
    assert len(result['artifacts']) == 4 and len(result['sources']) == 2
    assert result['counts']['source_traces'] == 1 and result['counts']['original_outcomes'] == 1
    assert result['counts']['fair_outcomes'] == 2
    assert result['error']['type'] == 'RuntimeError'
    partial = result['partial_rows']
    assert [row['steps'] for row in partial] == [3, 3, 2]
    assert not any(row['complete'] for row in partial)
    assert result['allocation_timing']['allocator_cpu_seconds'] >= 0
