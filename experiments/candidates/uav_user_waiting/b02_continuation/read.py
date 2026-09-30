#!/usr/bin/env python3
"""Read the retained six and new250 episodes as one fixed B02 panel."""

import argparse
import os
from pathlib import Path
import resource
import sys
import time

for _key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[_key] = '1'
ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from experiments.candidates.uav_user_waiting.b02 import read as original_reader
from experiments.candidates.uav_user_waiting.b02 import study as original
from experiments.candidates.uav_user_waiting.b02_continuation import study


def validate_summary(out, summary, parent):
    require = study.require
    require(summary['status'] == 'COMPLETE' and summary['scientific_invocation'] and summary['parent_unchanged'],
            'continuation is not complete with protected parent')
    config = study.read_json(out / 'config.json')
    require(summary['config'] == config == study.continuation_config(summary['launch_sha'], parent), 'continuation config mismatch')
    require(summary['counts'] == study.NEW_COUNTS, 'continuation counts mismatch')
    require(summary['fixed_policy_evaluation_counts'] == dict(episodes=256, transitions=65536,
            optimizer_updates=0, parameter_updates=0), 'valid panel count mismatch')
    require(summary['exposure'] == study.exposure(summary['counts'], summary['rows']), 'exposure ledger mismatch')
    require(summary['exposure']['total_result_steps'] == 65648 and summary['exposure']['failed_prefix_steps'] == 112,
            'failed-prefix exposure omitted or duplicated')
    rows = summary['rows']
    require([(r['arm'], r['seed']) for r in rows] == list(study.PLAN), 'panel order mismatch')
    require(all(row['steps'] == 256 for row in rows), 'non-H256 panel row')
    require(rows[:study.REUSED] == parent['rows'], 'reused metrics/raw rows changed')
    require(summary['artifacts'] == [row['raw'] for row in rows], 'panel artifact list mismatch')
    new = sorted([row['raw'] for row in rows[study.REUSED:]], key=lambda item: item['path'])
    require(summary['new_artifacts'] == new, 'new artifact identity set mismatch')
    for row in rows[study.REUSED:]:
        require(row['raw']['path'] == str(out / 'raw' / f"{row['arm']}_{row['seed']}.npz"), 'new raw is not in its output')
    exit_record = study.read_json(out / 'process-exit.json')
    require(exit_record['exit_code'] == 0, 'continuation worker did not exit successfully')
    manifest = study.read_json(out / 'launch-manifest.json')
    require(manifest['sha'] == summary['launch_sha'] and manifest['output_root'] == str(out)
            and manifest['node'] == 'wsl_4070' and manifest['acceptance'] == 'accepted', 'continuation admission mismatch')
    return rows


def read_result(out):
    started, cpu_started = time.perf_counter(), time.process_time()
    out = Path(out).resolve()
    parent = study.validate_parent()
    summary = study.read_json(out / 'summary.json')
    source_rows = validate_summary(out, summary, parent)
    rows, worlds, total_bytes = [], {}, 0
    for row in source_rows:
        path = Path(row['raw']['path'])
        identity = original.file_identity(path)
        study.require(identity == row['raw'], f'raw identity mismatch: {path}')
        total_bytes += identity['bytes']
        raw = original_reader.load_episode(path)
        world = raw['true_sites'], raw['positions'][0]
        if row['seed'] in worlds:
            for left, right in zip(world, worlds[row['seed']]):
                np.testing.assert_array_equal(left, right)
        else:
            worlds[row['seed']] = tuple(value.copy() for value in world)
        rows.append(original_reader.verify_episode(row, raw))
        del raw
        print(f"verified {len(rows)}/256 {row['arm']} {row['seed']}", flush=True)
    paired = original.paired_reading(source_rows, parent['config']['seeds'], original.ARMS)
    study.require(paired == summary['paired'], 'paired readings mismatch')
    result = dict(status='VERIFIED_COMPLETE', launch_sha=summary['launch_sha'], original_source_sha=study.ORIGINAL_SHA,
        summary_sha256=original.file_identity(out / 'summary.json')['sha256'],
        parent_summary_sha256=study.PARENT_HASHES['summary.json'], exposure=summary['exposure'],
        verified_raw_files=len(rows), verified_raw_bytes=total_bytes, rows=rows, paired=paired,
        continuation_diagnostics=original_reader.summarize_continuation(rows),
        scope='all256 native/C/age/history/key/continuation records across protected6 and new250; original B02 physical subset; prior112-step failure retained separately; zero new native steps/fits',
        wall_seconds=time.perf_counter() - started, cpu_seconds=time.process_time() - cpu_started,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        rss_scope='reader lifetime peak; Linux KiB')
    original.write_json(out / 'reading.json', result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    return read_result(parser.parse_args(argv).out)


if __name__ == '__main__':
    main()
