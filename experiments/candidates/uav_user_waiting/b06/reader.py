"""Complete accepted B06 reading; no new native trajectory or baseline replay."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import resource
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_registered_service.b01.read import verify_periodic, compare_metrics
from experiments.candidates.uav_service_age.b01.read import verify_age
from experiments.candidates.uav_user_waiting.b02.storage import unpack_records
from experiments.candidates.uav_user_waiting.b04.metrics import episode_metrics
from experiments.candidates.uav_user_waiting.b05.reader import compare_tree
from . import protocol as p
from .collect import BASELINE_FIELDS
from .read_native import verify_native, verify_post_c_nav
from .read_model import verify_decisions
from .read_outcomes import verify_lrs, reference_physical, reference_alignment, reference_paired


def bound_json(identity):
    path = Path(identity['path'])
    data = path.read_bytes()
    p.require(len(data) == identity['bytes'] and hashlib.sha256(data).hexdigest() == identity['sha256'],
              'JSON input identity differs: ' + str(path))
    return json.loads(data)


def reference_model_work(raw):
    records = unpack_records(raw)
    result = {}
    for name, executed in zip(raw['execution_lrs_count_names'], raw['execution_lrs_counts']):
        online = sum(record['counts']['history_' + name] for record in records)
        terminal = int(executed) - online
        assert terminal >= 0
        result[str(name)] = sum(record['counts'][name] for record in records) + terminal
        result['terminal_' + name] = terminal
    return result


def verify_episode(collector, raw, full, compact, baseline, counts, discrepancies):
    assert str(raw['program']) == p.PROGRAM and str(raw['collector_program']) == collector['arm'] == 'S'
    assert not bool(raw['training_episode']) and not bool(raw['grant_feedback_used'])
    assert int(raw['world_seed']) == collector['seed'] == full['seed'] == compact['seed']
    checked = verify_native(collector, raw, counts)
    expected_calls = np.repeat((np.arange(collector['steps']) % 4 == 0)[:, None], p.N, axis=1)
    for name in ('current_c_attempted', 'current_c_completed'):
        assert raw[name].dtype == bool
        np.testing.assert_array_equal(raw[name], expected_calls)
    assert dict(zip(raw['current_c_source_counter_names'].tolist(), raw['current_c_source_counts'].tolist())) == collector['controller_counts']
    verify_post_c_nav(raw, counts)
    verify_periodic(collector, raw)
    verify_age(collector, raw)
    checked.update(verify_decisions(raw, counts))
    # Existing telemetry reduction remains shared. Native physics, greedy
    # contacts, scalar age/gaps and all LRS outcomes are checked independently.
    for key, value in episode_metrics(raw, collector['steps'], 'S', unpack_records(raw)).items():
        compare_metrics(value, collector[key])
    reconstructed = verify_lrs(raw, full, compact, collector, counts, discrepancies)
    physical, alignment, model_work = reference_physical(raw, baseline), reference_alignment(raw), reference_model_work(raw)
    for name, expected in (('physical_change', physical), ('model_alignment', alignment), ('model_work', model_work)):
        compare_tree(full[name], expected, name, discrepancies)
        compare_tree(compact[name], expected, 'compact.' + name, discrepancies)
    heights = [float(point[2]) for positions in raw['positions'][1:] for point in positions]
    height = dict(mean_height_m=sum(heights) / len(heights), min_height_m=min(heights), max_height_m=max(heights),
                  lower_boundary_uav_ticks=heights.count(50.), upper_boundary_uav_ticks=heights.count(150.),
                  scope='postmove physical altitude')
    for record in (full, compact):
        # Python scalar summation and NumPy pairwise summation may differ by
        # a few ulps after 1280 positive heights; altitude tolerance is1e-10m.
        assert abs(record['height_exposure']['mean_height_m'] - height['mean_height_m']) <= 1e-10
        compare_tree({key: value for key, value in record['height_exposure'].items() if key != 'mean_height_m'},
                     {key: value for key, value in height.items() if key != 'mean_height_m'}, 'height', discrepancies)
    assert full['raw'] == compact['raw'] == collector['raw']
    compare_tree(full['lrs_replay_timing'], compact['lrs_replay_timing'], 'LRS timing', discrepancies)
    assert all(np.isfinite(full['lrs_replay_timing'][key]) and full['lrs_replay_timing'][key] >= 0
               for key in ('wall_seconds', 'cpu_seconds'))
    checked.update(seed=collector['seed'], program=p.PROGRAM, physical_change=physical,
                   model_alignment=alignment, model_work=model_work,
                   outcome=dict(max_unserved_gap=reconstructed['max_unserved_gap'], F_user=reconstructed['F_user'],
                                mean_served=reconstructed['mean_served'], mean_quality=reconstructed['mean_quality']))
    return checked, reconstructed


def read_result(summary_path, destination, baseline_s, *, expected_summary_sha256,
                expected_launch_sha, admission, entry_started=None):
    destination, summary_path = Path(destination).resolve(), Path(summary_path).resolve(strict=True)
    destination.mkdir(parents=True, exist_ok=True)
    if (destination / 'reading.json').exists():
        raise FileExistsError('existing reading is never overwritten')
    # Own failure-record publication only after exclusive reservation.
    with (destination / 'reader-started.json').open('x', encoding='utf-8') as stream:
        json.dump(dict(worker_summary=str(summary_path), worker_sha256=expected_summary_sha256,
                       admission=admission), stream)
    started = time.perf_counter() if entry_started is None else entry_started
    cpu_started = time.process_time()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    counts = Counter(dict(new_native_steps=0, new_native_resets=0, new_environment_constructions=0,
                          new_fits=0, new_baseline_trajectories=0, verified_raw_files=0,
                          verified_raw_bytes=0, baseline_bytes_hashed=0))
    result = dict(object=p.OBJECT, status='READING', admission=admission, rows=[], counts=counts,
                  discrepancies={}, independent_model_counts={}, worker_launch_sha=expected_launch_sha)
    verified_rows, current_seed = [], None
    try:
        identity = p.file_identity(summary_path)
        assert identity['sha256'] == expected_summary_sha256
        result['worker_summary'] = identity
        summary = bound_json(identity)
        assert summary['status'] == 'COMPLETE' and summary['scientific_invocation']
        assert summary['launch_sha'] == expected_launch_sha and not summary['incomplete_raw']
        assert not summary['accounting_errors']
        _, baselines, staged, metadata = p.load_baselines(baseline_s)
        config = json.loads((summary_path.parent / 'config.json').read_text())
        assert summary['config'] == config == p.frozen_config(expected_launch_sha, metadata)
        assert json.loads((summary_path.parent / 'process-exit.json').read_text())['exit_code'] == 0
        assert [row['seed'] for row in summary['rows']] == list(p.SEEDS)
        assert [row['seed'] for row in summary['collector_rows']] == list(p.SEEDS)
        assert all(row['package'] == 'S_F:LRS' for row in summary['rows'])
        expected_counts = dict(constructors=1, constructor_attempts=1, explicit_resets=p.WORLDS,
            reset_calls_attempted=p.WORLDS, paired_resets_verified=p.WORLDS,
            native_step_calls=p.WORLDS * p.HORIZON, team_steps=p.WORLDS * p.HORIZON,
            complete_episodes=p.WORLDS, fits=0, targets=0, optimizer_updates=0,
            worker_current_c_calls=p.WORLDS * p.HORIZON // 4 * p.N,
            worker_current_c_calls_attempted=p.WORLDS * p.HORIZON // 4 * p.N, worker_current_c_calls_failed=0,
            native_lrs_fleet_ticks=p.WORLDS * p.HORIZON,
            native_lrs_row_selections=p.WORLDS * p.HORIZON * p.N,
            native_lrs_user_age_updates=p.WORLDS * p.HORIZON * p.U)
        for name, expected in expected_counts.items():
            assert summary['counts'][name] == expected, name
        assert [record['seed'] for record in summary['episode_accounting']] == list(p.SEEDS)
        assert summary['fixed_policy_evaluation_counts'] == dict(episodes=p.WORLDS,
            transitions=p.WORLDS * p.HORIZON, optimizer_updates=0, parameter_updates=0, fits=0)
        artifacts = [row[key] for row in summary['rows'] for key in ('raw', 'outcome')]
        assert sorted(summary['artifacts'], key=lambda row: row['path']) == sorted(artifacts, key=lambda row: row['path'])
        for collector, compact in zip(summary['collector_rows'], summary['rows']):
            current_seed = compact['seed']
            raw = p.load_raw(compact['raw'])
            counts['verified_raw_bytes'] += compact['raw']['bytes']
            baseline = p.load_raw(staged[current_seed], BASELINE_FIELDS)
            counts['baseline_bytes_hashed'] += staged[current_seed]['bytes']
            assert str(raw['baseline_s_sha256']) == staged[current_seed]['sha256']
            assert int(raw['baseline_s_bytes']) == staged[current_seed]['bytes']
            assert int(raw['completed_steps']) == collector['steps'] == p.HORIZON
            full = bound_json(compact['outcome'])
            checked, reconstructed = verify_episode(collector, raw, full, compact, baseline, counts, result['discrepancies'])
            accounting = summary['episode_accounting'][len(result['rows'])]
            assert accounting['current_c_attempted'] == accounting['current_c_completed'] == p.HORIZON // 4 * p.N
            assert accounting['current_c_failed'] == 0 and not accounting.get('errors')
            assert accounting['current_c_source_counts'] == collector['controller_counts']
            assert accounting['model_work'] == checked['model_work']
            result['rows'].append(checked)
            verified_rows.append(reconstructed)
            counts['verified_raw_files'] += 1
            for name, value in checked['model_work'].items():
                result['independent_model_counts'][name] = result['independent_model_counts'].get(name, 0) + value
            if len(result['rows']) % 8 == 0:
                p.write_json(destination / 'reading-progress.json', result)
            print(json.dumps(dict(verified=len(result['rows']), seed=current_seed)), flush=True)
        assert counts['reader_current_c_calls'] == counts['reader_current_c_calls_attempted'] == 40960
        assert counts['native_lrs_fleet_completed'] == counts['native_physics_completed'] == 16384
        assert result['independent_model_counts'] == summary['model_counts']
        for name in summary['collector_rows'][0]['controller_counts']:
            assert summary['counts']['worker_current_c_source_' + name] == sum(
                row['controller_counts'][name] for row in summary['collector_rows'])
        result['paired'] = reference_paired(verified_rows, baselines)
        compare_tree(summary['paired'], result['paired'], 'paired', result['discrepancies'])
        result['status'] = 'VERIFIED_COMPLETE'
        result['scope'] = ('all64 native/report/C/local-history/grant recurrence/age/key/search/output records; '
            'independent native LRS and complete censored gap/no-link/denial outcomes; '
            'winner and fixed-report candidate physics/priority only, not exhaustive candidate physics; '
            'two C passes; no new native trajectory or baseline allocation replay')
    except Exception as exc:
        result['status'] = 'READ_FAILED'
        result['error'] = dict(seed=current_seed, type=type(exc).__name__, message=str(exc), traceback=traceback.format_exc())
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        result['resources'] = dict(wall_seconds=time.perf_counter() - started,
            measured_cpu_seconds=time.process_time() - cpu_started,
            process_user_seconds=usage.ru_utime, process_system_seconds=usage.ru_stime,
            process_cpu_seconds=usage.ru_utime + usage.ru_stime, peak_rss_kib=usage.ru_maxrss,
            torch_threads=torch.get_num_threads(), torch_interop_threads=torch.get_num_interop_threads(),
            scope='reader process lifetime Linux KiB; measured phase excludes imports; zero environment instance')
        p.write_json(destination / 'reading.json', result)
    return result
