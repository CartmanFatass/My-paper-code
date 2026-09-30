"""Reuse six fixed complete records and collect only the selected 250-row suffix."""

import json
import os
import platform
from pathlib import Path
import resource
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_user_waiting.b02 import study as original
from .failure_capture import capture_failure

ROOT = Path(__file__).resolve().parents[4]
ORIGINAL_SHA = '16500b6f85c8cd20a7765801ed413608c36cf9f0'
PARENT = Path('/home/wu/projects/HMASD/runs/uav_user_waiting/b02_continuity_a01')
PARENT_OPERATION = '/home/wu/projects/HMASD/.git/hmasd-admission/d93ce289af2028b3c172d7b3cc21daa31d7dd32569f276d18400d265d776dc84.json'
PARENT_HASHES = {
    'launch-manifest.json': 'f20656715060fb50126fe368fde717e8626ef2a30b38a43799ac7b9cff81a4b1',
    'config.json': 'e2c1ddee800b9afde9e2efbe7d1ebc2eb2ed9352388b7d33a0dc6cb3221d28cb',
    'summary.json': 'd9e1060d93d4d8181e371a6ccc7220c74102f6740c797fea09188706366d62a8',
    'process-exit.json': '03ada784587a8beb1b8195a48207151b9d4f392e50b5b1e24fee485ab8f01d0c',
}
PROOF = ROOT / 'runs/uav_user_waiting/b02_continuity_a01/failure-reading.json'
PROOF_HASH = 'e971cf194942ecc99278e63e8ba64f397242c44a638a5a1acf88fbd5636bbd18'
REUSED = 6
PRIOR_COUNTS = dict(constructors=1, explicit_resets=7, native_step_calls=1648,
                    team_steps=1648, complete_episodes=6, fit_started=0, optimizer_steps=0)
NEW_COUNTS = dict(constructors=1, explicit_resets=250, native_step_calls=64000,
                  team_steps=64000, complete_episodes=250, fit_started=0, optimizer_steps=0)
PLAN = tuple((arm, seed) for index, seed in enumerate(range(original.SEED, original.SEED + original.WORLDS))
             for arm in original.ARM_ORDERS[index % len(original.ARM_ORDERS)])


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def read_json(path):
    return json.loads(Path(path).read_text())


def check_digest(path, expected):
    require(Path(path).is_file() and not Path(path).is_symlink(), f'missing or linked input: {path}')
    value = original.file_identity(path)
    require(value['sha256'] == expected, f'input digest mismatch: {path}')
    return value


def validate_parent():
    """Immutable inputs only; no environment construction, replay or native steps."""
    for name, digest in PARENT_HASHES.items():
        check_digest(PARENT / name, digest)
    summary, config, manifest, exit_record = (read_json(PARENT / name) for name in
        ('summary.json', 'config.json', 'launch-manifest.json', 'process-exit.json'))
    require(summary['status'] == 'INCOMPLETE_TECHNICAL_FAILURE' and summary['scientific_invocation'],
            'parent is not the accepted incomplete scientific attempt')
    require(summary['launch_sha'] == manifest['sha'] == ORIGINAL_SHA, 'parent source mismatch')
    require(manifest['output_root'] == str(PARENT) and manifest['operation_ref'] == PARENT_OPERATION,
            'parent output/operation mismatch')
    require(manifest['acceptance'] == 'accepted' and manifest['node'] == 'wsl_4070', 'parent acceptance/node mismatch')
    require(exit_record['exit_code'] == 1, 'parent terminal exit mismatch')
    # This also hashes each original source file. New continuation files live outside B02.
    require(summary['config'] == config == original.frozen_config(ORIGINAL_SHA), 'original scientific inputs changed')
    require(summary['counts'] == PRIOR_COUNTS, 'parent exposure mismatch')
    require([(r['arm'], r['seed']) for r in summary['rows']] == list(PLAN[:REUSED]), 'reusable prefix mismatch')
    require(all(r['steps'] == original.HORIZON for r in summary['rows']), 'reused episode incomplete')
    expected_paths = {str(PARENT / 'raw' / f'{arm}_{seed}.npz') for arm, seed in PLAN[:REUSED + 1]}
    require({r['path'] for r in summary['artifacts']} == expected_paths and len(summary['artifacts']) == 7,
            'parent complete/partial artifact set mismatch')
    artifacts = {item['path']: item for item in summary['artifacts']}
    for item in summary['artifacts']:
        require(original.file_identity(Path(item['path'])) == item, 'parent raw identity mismatch')
    for row in summary['rows']:
        require(row['raw'] == artifacts[str(PARENT / 'raw' / f"{row['arm']}_{row['seed']}.npz")],
                'reused row/raw binding mismatch')
    check_digest(PROOF, PROOF_HASH)
    proof = read_json(PROOF)
    require(proof['status'] == 'READ_INCOMPLETE_TECHNICAL_COLLECTION'
            and proof['summary_sha256'] == PARENT_HASHES['summary.json']
            and proof['verified_native_steps'] == 1648
            and proof['native_steps_added'] == proof['fits_added'] == 0, 'parent reading mismatch')
    require([(r['arm'], r['seed'], r['verified_steps']) for r in proof['complete_rows']]
            == [(arm, seed, 256) for arm, seed in PLAN[:REUSED]], 'parent complete reading coverage mismatch')
    partial = proof['partial']
    require((partial['arm'], partial['seed'], partial['verified_steps']) == (*PLAN[REUSED], 112),
            'parent partial reading coverage mismatch')
    return summary


def verify_parent_stopped():
    from scripts.hmasd_launch import status
    facts = status(PARENT_OPERATION)
    execution = facts['execution']
    require(execution['state'] == 'exited' and execution['exit_code'] == 1
            and execution['exit_witness']['state'] == 'valid', 'parent terminal state is not reconciled')
    require(all(execution[role]['state'] in ('absent', 'not_running', 'identity_mismatch')
                for role in ('runner', 'supervisor')), 'parent runner/supervisor is not stopped')
    return facts


def continuation_config(launch_sha, parent):
    sources = [dict(original.file_identity(path), path=str(path.relative_to(ROOT)))
               for path in sorted(Path(__file__).parent.glob('*.py'))]
    return dict(object='UAV-USER-WAITING-B02-CONTINUATION', launch_sha=launch_sha,
                original_scientific_config=parent['config'], continuation_source_identities=sources,
                parent=dict(source_sha=ORIGINAL_SHA, output_root=str(PARENT), operation_ref=PARENT_OPERATION,
                            metadata_hashes=PARENT_HASHES, reading_sha256=PROOF_HASH,
                            original_counts=PRIOR_COUNTS, artifacts=parent['artifacts']),
                reused_complete_episodes=REUSED, new_schedule=[list(pair) for pair in PLAN[REUSED:]],
                planned_new_episodes=250, planned_new_steps=64000, planned_fits=0,
                valid_panel_episodes=256, valid_panel_steps=65536,
                original_failed_prefix_steps=112, total_result_exposure_steps=65648,
                retry_contract='selected distinct continuation; standard fresh admission; not --retry-of same-source replay',
                failure_capture='exception-only selected traceback operands; no normal policy/search/RNG hook; no automatic further retry')


def exposure(counts, rows):
    return dict(prior_result_steps=PRIOR_COUNTS['team_steps'], new_result_steps=counts['team_steps'],
                total_result_steps=PRIOR_COUNTS['team_steps'] + counts['team_steps'],
                valid_panel_steps=sum(row['steps'] for row in rows), valid_panel_episodes=len(rows),
                reused_complete_steps=REUSED * original.HORIZON,
                failed_prefix_steps=112 + counts['team_steps'] - counts['complete_episodes'] * original.HORIZON,
                fits=0, optimizer_updates=0)


def run_batch(out, launch_sha, *, entry_start, admission):
    out = Path(out).resolve()
    require(out != PARENT and PARENT not in out.parents and out not in PARENT.parents, 'output overlaps protected parent')
    require(not (out / 'config.json').exists() and not (out / 'summary.json').exists()
            and not ((out / 'raw').exists() and any((out / 'raw').iterdir())), 'continuation output already contains science')
    parent = validate_parent()
    terminal = verify_parent_stopped()
    out.mkdir(parents=True, exist_ok=True)
    (out / 'raw').mkdir(exist_ok=True)
    cpu_started = time.process_time()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    config = continuation_config(launch_sha, parent)
    original.write_json(out / 'config.json', config)
    counts = dict(constructors=0, explicit_resets=0, native_step_calls=0, team_steps=0,
                  complete_episodes=0, fit_started=0, optimizer_steps=0)
    summary = dict(object=config['object'], status='RUNNING', launch_sha=launch_sha,
                   scientific_invocation=True, config=config, counts=counts, rows=parent['rows'],
                   admission=admission, parent_terminal=terminal,
                   runtime=dict(python=platform.python_version(), numpy=np.__version__,
                                torch=torch.__version__, host=platform.node(), platform=platform.platform()))
    env = None
    try:
        env = original.factory(original.SEED)
        counts['constructors'] += 1
        env.env.max_steps = original.HORIZON
        for arm, seed in PLAN[REUSED:]:
            row, raw = original.collect_episode(env, arm, seed, out, counts)
            original.save_episode(out, row, raw)
            summary['rows'].append(row)
            summary['exposure'] = exposure(counts, summary['rows'])
            original.write_json(out / 'summary.json', summary)
            print(json.dumps(dict(arm=arm, seed=seed, new_completed=counts['complete_episodes'],
                                  new_steps=counts['team_steps'], panel_rows=len(summary['rows']),
                                  gap=row['mean_user_max_unserved_gap'], misses=row['deadline_misses'])), flush=True)
        require(counts == NEW_COUNTS, 'new exposure differs from selected suffix')
        require([(r['arm'], r['seed']) for r in summary['rows']] == list(PLAN), 'composite panel order mismatch')
        summary['paired'] = original.paired_reading(summary['rows'], parent['config']['seeds'], original.ARMS)
        summary['status'] = 'COMPLETE'
        summary['fixed_policy_evaluation_counts'] = dict(episodes=256, transitions=65536,
                                                        optimizer_updates=0, parameter_updates=0)
    except Exception as exc:
        summary['status'] = 'INCOMPLETE_TECHNICAL_FAILURE'
        summary['error'] = dict(type=type(exc).__name__, message=str(exc), traceback=traceback.format_exc())
        summary['failure_capture'] = capture_failure(exc, out)
        summary['failure_capture_artifacts'] = [original.file_identity(out / name)
            for name in ('failure-operands.json', 'failure-operands.npz') if (out / name).is_file()]
    finally:
        if env is not None:
            env.close()
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary['resources'] = dict(wall_seconds=time.perf_counter() - entry_start,
            measured_cpu_seconds=time.process_time() - cpu_started,
            process_user_seconds=usage.ru_utime, process_system_seconds=usage.ru_stime,
            peak_rss_kib=usage.ru_maxrss, rss_scope='continuation worker lifetime peak; Linux KiB',
            scope='entry wall includes imports; process CPU includes imports/init; prior attempt recorded separately',
            torch_threads=torch.get_num_threads(), torch_interop_threads=torch.get_num_interop_threads(),
            thread_environment={key: os.environ.get(key) for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')})
        summary['new_artifacts'] = [original.file_identity(path) for path in sorted((out / 'raw').iterdir()) if path.is_file()]
        summary['artifacts'] = [row['raw'] for row in summary['rows']]
        summary['exposure'] = exposure(counts, summary['rows'])
        # Rehash the protected original bytes even if the continuation failed.
        try:
            validate_parent()
            summary['parent_unchanged'] = True
        except Exception as exc:
            summary['parent_unchanged'] = False
            summary['status'] = 'INCOMPLETE_INPUT_IDENTITY_FAILURE'
            summary['parent_validation_error'] = dict(type=type(exc).__name__, message=str(exc))
        original.write_json(out / 'summary.json', summary)
    return summary
