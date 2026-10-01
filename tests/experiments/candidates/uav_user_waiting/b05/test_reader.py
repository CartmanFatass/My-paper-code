"""Small synthetic independent-reader checks; no recorded production arrays."""

from collections import Counter
from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from experiments.candidates.uav_user_waiting.b05.reader import (
    compare_tree, read_raw, reference_allocations, reference_outcome, reference_paired, verify_trace,
)


def test_reference_gap_boundaries_and_mixed_exclusion_are_exact():
    sinr = np.full((5, 5, 50), -30.0)
    sinr[0, 0, :12] = 5.0
    sinr[1, 0, :10] = 5.0
    sinr[2, 0, 10] = 5.0
    counts = Counter()
    allocations, eligible, _ = reference_allocations(sinr, np.full(5, 31, np.uint8), counts)
    actual = reference_outcome(sinr, eligible, allocations[0], allocations[0], counts)
    user = actual['per_user'][10]
    assert user['mean_age'] == 1.2
    assert user['service_count'] == 1
    assert user['terminal_age'] == user['max_gap'] == 2
    assert user['gaps'] == [
        dict(start=0, end=2, left_censored=True, right_censored=False,
             capacity_denied_ticks=1, no_link_ticks=1),
        dict(start=3, end=5, left_censored=False, right_censored=True,
             capacity_denied_ticks=0, no_link_ticks=2),
    ]
    never = actual['per_user'][11]
    assert never['mean_age'] == 3.0
    assert never['gaps'] == [dict(start=0, end=5, left_censored=True,
                                 right_censored=True, capacity_denied_ticks=1, no_link_ticks=4)]
    assert actual['metrics']['mean_served'] == 4.2
    assert actual['metrics']['mean_quality'] == pytest.approx(0.04, abs=1e-15)
    assert actual['metrics']['J'] == pytest.approx(0.0708, abs=1e-15)
    assert counts['fleet_allocations'] == 15
    assert counts['uav_allocation_decisions'] == 75
    assert counts['threshold_entries'] == 1250
    assert counts['service_quality_age_reductions'] == 5
    assert counts['user_tick_age_updates'] == 250


def test_reference_round_robin_cursor_survives_empty_tick_and_resets_each_trace():
    sinr = np.full((3, 5, 50), -30.0)
    sinr[0, 0, :12] = 10.0
    sinr[2, 0, :12] = 10.0
    first, _, _ = reference_allocations(sinr, np.full(3, 31, np.uint8), Counter())
    second, _, _ = reference_allocations(sinr, np.full(3, 31, np.uint8), Counter())
    assert np.array_equal(first, second)
    assert np.flatnonzero(first[1, 0, 0]).tolist() == list(range(10))
    assert not first[1, 1].any()
    assert np.flatnonzero(first[1, 2, 0]).tolist() == list(range(8)) + [10, 11]


def test_reference_lrs_is_local_at_handoff_and_breaks_ties_by_sinr_then_id():
    sinr = np.full((2, 5, 50), -30.0)
    # User0 was granted by UAV0. On handoff UAV1 has no grant history for it.
    sinr[0, 0, 0] = 5.0
    sinr[0, 1, 1:11] = 8.0
    sinr[1, 1, :12] = 8.0
    sinr[1, 1, 0] = 9.0
    assignments, _, _ = reference_allocations(sinr, np.full(2, 31, np.uint8), Counter())
    assert assignments[2, 1, 1, 0]
    assert assignments[2, 1, 1, 11]
    assert np.flatnonzero(assignments[2, 1, 1]).tolist() == list(range(9)) + [11]
    # The larger-SINR tie rule is visible on the first tick, before any history.
    assert np.array_equal(assignments[0, 0], assignments[2, 0])


@pytest.mark.parametrize('kind', ['overlap', 'active_nan', 'off_finite', 'mask_bits'])
def test_reference_rejects_source_invariance_violations(kind):
    sinr = np.full((1, 5, 50), -30.0)
    masks = np.array([31], dtype=np.uint8)
    if kind == 'overlap':
        sinr[0, :2, 0] = 4.0
    elif kind == 'active_nan':
        sinr[0, 0, 0] = np.nan
    elif kind == 'off_finite':
        masks[0] = 30
    else:
        masks[0] = 32
    with pytest.raises(ValueError):
        reference_allocations(sinr, masks, Counter())


def test_comparison_rejects_structural_integer_and_float_corruption():
    compare_tree({'a': [1, True, 0.125]}, {'a': [1, True, 0.125]}, 'row', {})
    for value in ({'a': [1, True, 0.126]}, {'a': [1.0, True, 0.125]},
                  {'a': [1, True]}, {'a': [1, True, float('nan')]},
                  {'a': [1, True, 0.125], 'extra': 0}):
        with pytest.raises(ValueError):
            compare_tree(value, {'a': [1, True, 0.125]}, 'row', {})


def _synthetic_production(tmp_path):
    from experiments.candidates.uav_user_waiting.b05 import protocol as p, study
    root = Path(__file__).resolve().parents[5]
    radio_path = root / p.RADIO_PATH
    producer_counts = study.counters()
    radio = study.load_radio(root, p.file_identity(radio_path), producer_counts)
    horizon = 8
    sinr = np.full((horizon, 5, 50), -30.0)
    sinr[:, 0, :12] = np.arange(12) / 10 + 4.0
    sinr[:, 1, 12:23] = 8.0
    sinr[2, 0, 11] = -30.0
    sinr[4, 0, :12] = -30.0
    # A scored handoff supplies the same registered IDs to a different own state.
    sinr[6:, 0, :12] = -30.0
    sinr[6:, 2, :12] = np.arange(12) / 10 + 4.0
    connections = np.stack([radio.greedy_connection_assignment(values) for values in sinr])
    service = [radio.service_metrics(values, links) for values, links in zip(sinr, connections)]
    contacts = connections.any(axis=1)
    ages = np.zeros((horizon, 50), np.int64)
    for tick in range(horizon):
        ages[tick] = np.where(contacts[tick], 0, (ages[tick - 1] if tick else np.zeros(50, np.int64)) + 1)
    gaps = []
    for user in range(50):
        points = [-1, *np.flatnonzero(contacts[:, user]).tolist(), horizon]
        for previous, next_contact in zip(points, points[1:]):
            start, end = previous + 1, next_contact
            if start < end:
                gaps.append([user, start, end, end-start, int(start == 0), int(end == horizon)])
    raw = dict(program=np.array('M'), world_seed=np.array(7), completed_steps=np.array(horizon),
               sinr=sinr, connections=connections, mask=np.full(horizon, 31, np.uint8),
               served=np.array([row['served'] for row in service], np.int16),
               quality=np.array([row['quality'] for row in service]),
               reward=np.array([row['J'] for row in service]), actual_contacts=contacts,
               actual_ages=ages, unserved_gap_rows=np.array(gaps, np.int64).reshape(-1, 6),
               per_user_mean_age=ages.mean(axis=0), training_episode=np.array(False))
    source_path = tmp_path / 'synthetic.npz'
    np.savez_compressed(source_path, **raw)
    identity = p.file_identity(source_path)
    source_row = dict(arm='M', seed=7, steps=horizon, raw=identity,
                      **dict.fromkeys(p.INHERITED_METRICS, 0.0))
    out = tmp_path / 'output'
    (out / 'contacts').mkdir(parents=True)
    (out / 'outcomes').mkdir()
    compact, _, _, _ = study.produce_trace(raw, source_row, identity, out,
                                          producer_counts, radio, horizon=horizon)
    full = p.read_json(out / 'outcomes/M_7.json')
    with np.load(out / 'contacts/M_7.npz', allow_pickle=False) as archive:
        saved = {key: archive[key] for key in archive.files}
    return raw, source_row, full, compact, saved


def test_complete_synthetic_producer_is_independently_reconstructed(tmp_path):
    raw, source_row, full, compact, saved = _synthetic_production(tmp_path)
    counts = Counter()
    reconstructed, _ = verify_trace(raw, source_row, full, compact, saved, counts, {})
    assert len(reconstructed) == 3
    assert counts['original_outcomes'] == 1 and counts['fair_outcomes'] == 2
    assert counts['fleet_allocations'] == 24
    assert counts['service_quality_age_reductions'] == 24
    assert counts['user_tick_age_updates'] == 1200
    assert reconstructed[1]['changed_grant_user_ticks'] > 0


@pytest.mark.parametrize('corruption', ['contacts', 'gap', 'source', 'duplicate_law'])
def test_reader_rejects_synthetic_output_corruption(tmp_path, corruption):
    raw, source_row, full, compact, saved = _synthetic_production(tmp_path)
    if corruption == 'contacts':
        saved['contacts'][0, 0, 0] = not saved['contacts'][0, 0, 0]
    elif corruption == 'gap':
        full['rows'][0]['per_user'][-1]['gaps'][0][1] -= 1
    elif corruption == 'source':
        compact[0]['source'] = dict(compact[0]['source'], sha256='f' * 64)
    else:
        full['rows'][2]['law'] = full['rows'][1]['law']
    with pytest.raises(ValueError):
        verify_trace(raw, source_row, full, compact, saved, Counter(), {})


def test_independent_pairing_retains_all36_world_vectors(tmp_path):
    from experiments.candidates.uav_user_waiting.b05 import protocol as p, study
    _, _, _, compact, _ = _synthetic_production(tmp_path)
    rows = []
    for seed in (1, 2):
        for i, program in enumerate(p.PROGRAMS):
            for j, law in enumerate(p.LAWS):
                row = deepcopy(compact[j])
                row.update(program=program, law=law, package=f'{program}:{law}', seed=seed,
                           F_user=float(i + j + seed))
                rows.append(row)
    reference = reference_paired(rows, seeds=(1, 2))
    produced = study.paired_reading(rows, seeds=(1, 2))
    compare_tree({key: produced[key] for key in reference}, reference, 'paired', {})
    assert len(reference['contrasts']) == 36
    assert reference['contrasts']['U:LRS-M:ORIGINAL']['F_user']['values'] == [4.0, 4.0]


def test_independent_raw_reader_rejects_hash_and_shape_corruption(tmp_path, monkeypatch):
    from experiments.candidates.uav_user_waiting.b05 import protocol as p
    raw, source_row, _, _, _ = _synthetic_production(tmp_path)
    monkeypatch.setattr(p, 'HORIZON', 8)
    loaded, _ = read_raw(source_row, Counter())
    assert np.array_equal(loaded['connections'], raw['connections'])
    source_path = Path(source_row['raw']['path'])
    original_bytes = source_path.read_bytes()
    source_path.write_bytes(original_bytes + b'x')
    with pytest.raises(ValueError, match='hash/bytes'):
        read_raw(source_row, Counter())
    truncated = dict(raw, sinr=raw['sinr'][:-1])
    np.savez_compressed(source_path, **truncated)
    source_row['raw'] = p.file_identity(source_path)
    with pytest.raises(ValueError, match='SINR shape'):
        read_raw(source_row, Counter())


def test_staged_raw_copy_is_hash_bound_without_fallback_to_origin(tmp_path, monkeypatch):
    from experiments.candidates.uav_user_waiting.b05 import protocol as p, study
    raw, source_row, _, _, _ = _synthetic_production(tmp_path)
    monkeypatch.setattr(p, 'HORIZON', 8)
    origin = Path(source_row['raw']['path'])
    staged = tmp_path / 'staged-copy.npz'
    staged.write_bytes(origin.read_bytes())
    source_row['raw'] = dict(source_row['raw'], path=str(staged), canonical_path=str(origin))
    origin.unlink()
    produced = study.load_trace(source_row['raw'], study.counters())
    independently_read, identity = read_raw(source_row, Counter())
    assert identity['path'] == str(staged)
    assert np.array_equal(produced['sinr'], raw['sinr'])
    assert np.array_equal(independently_read['sinr'], raw['sinr'])
    staged.write_bytes(staged.read_bytes() + b'changed')
    with pytest.raises(ValueError, match='hash/size'):
        study.load_trace(source_row['raw'], study.counters())
    with pytest.raises(ValueError, match='hash/bytes'):
        read_raw(source_row, Counter())


def test_reader_cli_requires_admission_before_reading_or_writing(tmp_path):
    root = Path(__file__).resolve().parents[5]
    entry = root / 'experiments/candidates/uav_user_waiting/b05/read.py'
    out = tmp_path / 'not_created'
    missing = tmp_path / 'missing'
    environment = {key: value for key, value in os.environ.items() if not key.startswith('HMASD_')}
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    result = subprocess.run(
        [sys.executable, '-B', str(entry), '--out', str(out), '--launch-sha', '0' * 40,
         '--seed', '29426000', '--generic-summary', str(missing / 'summary.json'),
         '--worker-launch-sha', '0' * 40, '--generic-summary-sha256', '0' * 64],
        cwd=root, env=environment, text=True, capture_output=True, timeout=20)
    assert result.returncode != 0
    assert 'admission' in result.stderr.lower()
    assert not out.exists()


def _tiny_complete_worker(tmp_path, monkeypatch):
    """Test-only source-loader injection; no CLI exposes a reduced/fake panel."""
    from experiments.candidates.uav_user_waiting.b05 import protocol as p, reader, study
    base = tmp_path / 'fixture'
    base.mkdir()
    raw, original_row, _, _, _ = _synthetic_production(base)
    by = {}
    for program in p.PROGRAMS:
        fixture = dict(raw, program=np.array(program))
        path = tmp_path / f'{program}_7.npz'
        np.savez_compressed(path, **fixture)
        by[program, 7] = dict(original_row, arm=program, raw=p.file_identity(path))
    metadata = tmp_path / 'original'
    metadata.mkdir()
    summary, reading = metadata / 'summary.json', metadata / 'reading.json'
    p.write_json(summary, {})
    p.write_json(reading, {})
    summary_id, reading_id = p.file_identity(summary), p.file_identity(reading)
    bindings = [dict(p.file_identity(study.ROOT / path), relative_path=path) for path in p.SOURCE_PATHS]
    reader_bindings = [dict(item, path=item['relative_path']) for item in bindings]
    for item in reader_bindings:
        del item['relative_path']
    monkeypatch.setattr(p, 'SEEDS', (7,))
    monkeypatch.setattr(p, 'HORIZON', 8)
    expected = dict(source_traces=3, original_outcomes=3, fair_outcomes=6, source_ticks=24,
        fleet_allocations=72, uav_allocation_decisions=360, original_kernel_calls=24,
        rr_row_selections=120, lrs_row_selections=120, transition_reductions=72, user_age_updates=3600,
        threshold_scans=48, threshold_entries=12000, contact_values_retained=2400,
        fair_contact_valid_user_ticks=2400, **{key: 0 for key in p.ZERO_COUNTS})
    monkeypatch.setattr(p, 'expected_counts', lambda: expected)
    monkeypatch.setattr(study, 'validate_inputs', lambda *args: (
        summary_id, reading_id, bindings, by, p.file_identity(study.ROOT / p.RADIO_PATH)))
    monkeypatch.setattr(reader, 'read_source', lambda *args: (by, dict(
        summary=summary_id, reading=reading_id, frozen_source_identities=reader_bindings)))
    produce = study.produce_trace
    monkeypatch.setattr(study, 'produce_trace', lambda *args, **kwargs: produce(*args, **kwargs, horizon=8))
    worker = tmp_path / 'worker'
    result = study.run_batch(worker, 'a' * 40, summary, reading, study.ROOT, admission=dict(sha='a' * 40))
    assert result['status'] == 'COMPLETE', result.get('error')
    return worker, result


def test_complete_independent_reader_assembly_and_failure_timing(tmp_path, monkeypatch):
    from experiments.candidates.uav_user_waiting.b05 import protocol as p, reader
    worker, produced = _tiny_complete_worker(tmp_path, monkeypatch)
    worker_hash = p.file_identity(worker / 'summary.json')['sha256']
    complete = reader.read_batch(worker, tmp_path / 'verified', 'b' * 40, 'a' * 40, worker_hash)
    assert complete['status'] == 'COMPLETE', complete.get('failure')
    assert len(complete['rows']) == 9 and len(complete['paired']['contrasts']) == 36
    assert complete['counts']['complete_traces'] == 3
    assert all(value > 0 for value in complete['allocator_cpu_seconds'].values())
    assert p.read_json(tmp_path / 'verified/reading.json') == complete
    # Corrupt a numeric result while consistently rebinding file/summary hashes.
    # This exercises independent proof, not merely the digest mismatch guard.
    first = produced['rows'][0]['outcome']
    path = Path(first['path'])
    changed = p.read_json(path)
    changed['rows'][0]['per_user'][-1]['gaps'][0][1] -= 1
    p.write_json(path, changed)
    identity = p.file_identity(path)
    for row in produced['rows']:
        if row['outcome']['path'] == str(path):
            row['outcome'] = identity
    p.write_json(worker / 'summary.json', produced)
    failed = reader.read_batch(worker, tmp_path / 'failed', 'b' * 40, 'a' * 40,
                               p.file_identity(worker / 'summary.json')['sha256'])
    assert failed['status'] == 'FAILED'
    assert failed['traces'] == []
    assert failed['counts']['fleet_allocations'] == 24
    assert all(value > 0 for value in failed['allocator_cpu_seconds'].values())
    assert p.read_json(tmp_path / 'failed/reading.json')['allocator_cpu_seconds'] == failed['allocator_cpu_seconds']
