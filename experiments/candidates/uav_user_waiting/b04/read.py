#!/usr/bin/env python3
"""Admitted saved-data reading with zero new native steps or fits."""

import argparse
import json
import os
from pathlib import Path
import resource
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def read_result(summary_path, destination, *, admission, expected_summary_sha256, expected_launch_sha):
    import numpy as np
    import torch
    from experiments.candidates.uav_registered_service.b01.read import load_episode
    from experiments.candidates.uav_user_waiting.b04.study import (
        SEED, WORLDS, ARMS, ARM_ORDERS, frozen_config, file_identity, write_json,
    )
    from experiments.candidates.uav_user_waiting.b04.metrics import paired_reading
    from experiments.candidates.uav_user_waiting.b04.read_core import verify_episode
    started, cpu_started = time.perf_counter(), time.process_time()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    summary_path, destination = Path(summary_path), Path(destination)
    if (destination / 'reading.json').exists() or (destination / 'reading-progress.json').exists():
        raise FileExistsError('existing reader output; no implicit repeat')
    destination.mkdir(parents=True, exist_ok=True)
    result = dict(object='UAV-USER-WAITING-B04-READ', status='READING', admission=admission,
                  reader_launch_sha=admission['sha'], worker_launch_sha=expected_launch_sha,
                  expected_summary_sha256=expected_summary_sha256, rows=[],
                  counts=dict(new_native_steps=0, new_fits=0, verified_raw_files=0,
                              verified_raw_bytes=0, verified_native_transitions=0,
                              verified_model_transitions=0, candidate_physics_pairs=0,
                              candidate_physics_transitions=0, prefix_physics_transitions=0,
                              reader_current_c_calls=0))
    try:
        summary_identity = file_identity(summary_path)
        assert summary_identity['sha256'] == expected_summary_sha256
        result['worker_summary'] = summary_identity
        summary = json.loads(summary_path.read_text())
        assert summary['status'] == 'COMPLETE' and summary['scientific_invocation']
        assert summary['launch_sha'] == expected_launch_sha
        config = json.loads((summary_path.parent / 'config.json').read_text())
        assert summary['config'] == config == frozen_config(expected_launch_sha)
        seeds = list(range(SEED, SEED + WORLDS))
        assert summary['counts'] == dict(constructors=1, explicit_resets=256, native_step_calls=65536,
            team_steps=65536, complete_episodes=256, fit_started=0, optimizer_steps=0)
        assert summary['fixed_policy_evaluation_counts'] == dict(
            episodes=256, transitions=65536, optimizer_updates=0, parameter_updates=0)
        assert [(row['arm'], row['seed']) for row in summary['rows']] == [
            (arm, seed) for index, seed in enumerate(seeds) for arm in ARM_ORDERS[index % 8]]
        assert sorted(summary['artifacts'], key=lambda row: row['path']) == sorted(
            [row['raw'] for row in summary['rows']], key=lambda row: row['path'])
        assert json.loads((summary_path.parent / 'process-exit.json').read_text())['exit_code'] == 0
        worlds = {}
        for row in summary['rows']:
            identity = file_identity(Path(row['raw']['path']))
            assert identity == row['raw'], 'raw source binding changed'
            raw = load_episode(Path(identity['path']))
            world = raw['true_sites'], raw['positions'][0]
            if row['seed'] in worlds:
                for left, right in zip(world, worlds[row['seed']]):
                    np.testing.assert_array_equal(left, right)
            else:
                worlds[row['seed']] = tuple(value.copy() for value in world)
            checked = verify_episode(row, raw)
            result['rows'].append(checked)
            result['counts']['verified_raw_files'] += 1
            result['counts']['verified_raw_bytes'] += identity['bytes']
            result['counts']['verified_native_transitions'] += row['steps']
            result['counts']['reader_current_c_calls'] += row['steps'] // 4 * 5 * 2
            for key in ('verified_model_transitions', 'candidate_physics_pairs',
                        'candidate_physics_transitions', 'prefix_physics_transitions'):
                result['counts'][key] += checked[key]
            if len(result['rows']) % 8 == 0:
                write_json(destination / 'reading-progress.json', result)
            print(json.dumps(dict(verified=len(result['rows']), arm=row['arm'], seed=row['seed'])), flush=True)
        result['paired'] = paired_reading(summary['rows'], seeds, ARMS)
        assert result['paired'] == summary['paired']
        result['status'] = 'VERIFIED_COMPLETE'
        result['scope'] = ('all256 native/C/age/periodic/history records; all contact-cost-key arithmetic, '
            'exact O/W/S paths and U/K pool/floor/selection; declared physical subset; zero new native steps/fits')
    except Exception as exc:
        result['status'] = 'READ_FAILED'
        result['error'] = dict(type=type(exc).__name__, message=str(exc), traceback=traceback.format_exc())
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        result['resources'] = dict(wall_seconds=time.perf_counter() - started,
            cpu_seconds=time.process_time() - cpu_started, process_user_seconds=usage.ru_utime,
            process_system_seconds=usage.ru_stime, peak_rss_kib=usage.ru_maxrss,
            scope='reader lifetime Linux KiB; two C reconstruction passes and shared native radio, no env.step')
        write_json(destination / 'reading.json', result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--generic-summary', type=Path, required=True)
    parser.add_argument('--worker-summary-sha256', required=True)
    parser.add_argument('--worker-launch-sha', required=True)
    parser.add_argument('--launch-sha', required=True)
    parser.add_argument('--seed', type=int, required=True)
    args = parser.parse_args(argv)
    if args.seed != 29426000 or args.generic_summary.name != 'summary.json':
        parser.error('fixed B04 identity and canonical worker summary.json required')
    for value, length in ((args.worker_summary_sha256, 64), (args.worker_launch_sha, 40)):
        if len(value) != length or any(char not in '0123456789abcdef' for char in value):
            parser.error('complete lowercase worker summary digest and source SHA required')
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[key] = '1'
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction='uav_user_waiting')
    if admission['sha'] != args.launch_sha:
        raise RuntimeError('reader admission/source mismatch')
    return read_result(args.generic_summary.resolve(strict=True), args.out, admission=dict(admission),
        expected_summary_sha256=args.worker_summary_sha256, expected_launch_sha=args.worker_launch_sha)


if __name__ == '__main__':
    if main()['status'] != 'VERIFIED_COMPLETE':
        raise SystemExit(1)
