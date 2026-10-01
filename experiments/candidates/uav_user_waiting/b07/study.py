"""One fixed C2 physical program and its complete LRS saved-SINR reading."""

from collections import Counter
import json
import os
from pathlib import Path
import platform
import resource
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_radio_activation.b01.study import factory
from experiments.candidates.uav_user_waiting.b02.storage import unpack_records
from . import protocol as p
from .collect import accounting_error, atomic_npz, collect_episode, error_details
from .metrics import paired_reading
from .outcomes import replay_lrs, compact_row, physical_comparison


def model_work(raw):
    total = Counter()
    for record in unpack_records(raw):
        total.update({name:int(value) for name,value in record['counts'].items()})
    return dict(total)


def resources(started, cpu_started):
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return dict(wall_seconds=time.perf_counter() - started, measured_cpu_seconds=time.process_time() - cpu_started,
                process_user_seconds=usage.ru_utime, process_system_seconds=usage.ru_stime,
                process_cpu_seconds=usage.ru_utime + usage.ru_stime, peak_rss_kib=usage.ru_maxrss,
                rss_scope='whole worker process Linux KiB; not simultaneous multi-process peak',
                torch_threads=torch.get_num_threads(), torch_interop_threads=torch.get_num_interop_threads(),
                thread_environment={key: os.environ.get(key) for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')})


def run_batch(out, baseline_sf, launch_sha, *, entry_start=None, admission=None):
    out = Path(out).resolve()
    if any((out / name).exists() for name in ('config.json', 'summary.json')):
        raise FileExistsError('existing B07 attempt; no implicit retry/resume')
    for name in ('raw', 'outcomes'):
        (out / name).mkdir(parents=True, exist_ok=True)
    started, cpu_started = time.perf_counter() if entry_start is None else entry_start, time.process_time()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    counts = Counter(dict(constructors=0, constructor_attempts=0, explicit_resets=0,
                          reset_calls_attempted=0, paired_resets_verified=0, constructor_internal_resets=0, native_step_calls=0,
                          mask_refresh_attempts=0, mask_refreshes=0,
                          team_steps=0, complete_episodes=0, fits=0, targets=0, optimizer_updates=0,
                          parameter_updates=0, future_c_calls=0, worker_current_c_calls=0,
                          worker_current_c_calls_attempted=0, worker_current_c_calls_failed=0,
                          native_lrs_fleet_ticks=0, native_lrs_row_selections=0,
                          native_lrs_user_age_updates=0, baseline_raw_files_loaded=0,
                          baseline_raw_bytes_hashed=0, baseline_array_bytes_loaded=0))
    summary = dict(object=p.OBJECT, status='RUNNING', scientific_invocation=True, launch_sha=launch_sha,
                   admission=admission, counts=counts, rows=[], collector_rows=[],
                   runtime=dict(python=platform.python_version(), numpy=np.__version__, torch=torch.__version__,
                                host=platform.node(), platform=platform.platform()),
                   model_counts={}, lrs_replay_timing=[], incomplete_raw=[], episode_accounting=[], accounting_errors=[])
    env = None
    current_seed = None
    try:
        _, fair, staged, metadata = p.load_baselines(baseline_sf)
        summary['config'] = p.frozen_config(launch_sha, metadata)
        p.write_json(out / 'config.json', summary['config'])
        counts['constructor_attempts'] += 1
        env = factory(p.SEED)
        counts['constructors'] += 1
        counts['constructor_internal_resets'] += 1
        env.env.max_steps = p.HORIZON
        for seed in p.SEEDS:
            current_seed = seed
            episode_accounting = dict(seed=seed)
            try:
                collector_row, raw, baseline = collect_episode(env, seed, out, counts, staged[seed], accounting=episode_accounting)
                # Preserve complete source evidence before any replay or downstream reducer.
                raw_path = out / 'raw' / f'{p.PROGRAM}_{seed}.npz'
                wall, cpu = time.perf_counter(), time.process_time()
                try:
                    atomic_npz(raw_path, raw)
                finally:
                    episode_accounting['base_storage_wall_seconds'] = time.perf_counter() - wall
                    episode_accounting['base_storage_cpu_seconds'] = time.process_time() - cpu
                if episode_accounting.get('errors'):
                    raise RuntimeError('episode accounting incomplete: ' +
                                       ', '.join(error['phase'] for error in episode_accounting['errors']))
                full_row, arrays, replay_timing = replay_lrs(raw, collector_row, counts)
                raw.update(arrays)
                full_row['physical_change'] = physical_comparison(raw, baseline)
                full_row['model_work'] = model_work(raw)
                full_row['service_capacity_exposure'] = collector_row['service_capacity_exposure']
                raw_path = out / 'raw' / f'{p.PROGRAM}_{seed}.npz'
                wall, cpu = time.perf_counter(), time.process_time()
                try:
                    atomic_npz(raw_path, raw)
                    raw_id = p.file_identity(raw_path)
                finally:
                    episode_accounting['final_storage_wall_seconds'] = time.perf_counter() - wall
                    episode_accounting['final_storage_cpu_seconds'] = time.process_time() - cpu
                collector_row['raw'] = raw_id
                collector_row['storage_wall_seconds'] = (episode_accounting['final_storage_wall_seconds'] +
                                                         episode_accounting['base_storage_wall_seconds'])
                collector_row['storage_cpu_seconds'] = (episode_accounting['final_storage_cpu_seconds'] +
                                                        episode_accounting['base_storage_cpu_seconds'])
                full_row['inherited'].update(storage_wall_seconds=collector_row['storage_wall_seconds'],
                                             storage_cpu_seconds=collector_row['storage_cpu_seconds'])
                full_row['raw'] = raw_id
                full_row['lrs_replay_timing'] = replay_timing
                outcome_path = out / 'outcomes' / f'{p.PROGRAM}_{seed}.json'
                p.write_json(outcome_path, full_row)
                row = compact_row(full_row)
                row['outcome'] = p.file_identity(outcome_path)
                summary['rows'].append(row)
                summary['collector_rows'].append(collector_row)
                summary['lrs_replay_timing'].append(replay_timing)
                print(json.dumps(dict(seed=seed, complete=len(summary['rows']), native_steps=counts['team_steps'],
                                      maximum_gap=row['max_unserved_gap'], F_user=row['F_user'],
                                      served=row['mean_served'], misses=collector_row['deadline_misses'])), flush=True)
            finally:
                for key, value in episode_accounting.get('model_work', {}).items():
                    summary['model_counts'][key] = summary['model_counts'].get(key, 0) + value
                summary['episode_accounting'].append(episode_accounting)
            summary['resources'] = resources(started, cpu_started)
            p.write_json(out / 'summary.json', summary)
        summary['paired'] = paired_reading(summary['rows'], fair)
        summary['fixed_policy_evaluation_counts'] = dict(episodes=p.WORLDS, transitions=p.WORLDS * p.HORIZON,
                                                        optimizer_updates=0, parameter_updates=0, fits=0)
        summary['status'] = 'COMPLETE'
    except Exception as exc:
        summary['status'] = 'INCOMPLETE_TECHNICAL_FAILURE'
        summary['error'] = dict(seed=current_seed, **error_details(exc), traceback=traceback.format_exc())
    finally:
        def support(phase, function):
            try:
                return function()
            except Exception as exc:
                accounting_error(dict(errors=summary['accounting_errors']), phase, exc)
                if 'error' not in summary:
                    summary['status'] = 'INCOMPLETE_TECHNICAL_FAILURE'
                    summary['error'] = dict(seed=current_seed, **error_details(exc),
                                            traceback=traceback.format_exc())
                return None

        if env is not None:
            support('environment_close', env.close)
        usage = support('resources', lambda: resources(started, cpu_started))
        if usage is not None:
            summary['resources'] = usage
        known = {row['raw']['path'] for row in summary['rows']}
        summary['artifacts'] = []
        for folder in ('raw', 'outcomes'):
            paths = support('artifact_inventory', lambda: sorted((out / folder).iterdir()))
            for path in paths or []:
                if path.is_file():
                    identity = support('artifact_identity', lambda: p.file_identity(path))
                    if identity is not None:
                        summary['artifacts'].append(identity)
                        if folder == 'raw' and path.suffix == '.npz' and str(path) not in known:
                            summary['incomplete_raw'].append(identity)
        support('summary_write', lambda: p.write_json(out / 'summary.json', summary))
    return summary
