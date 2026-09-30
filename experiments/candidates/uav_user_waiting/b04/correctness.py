#!/usr/bin/env python3
"""One admitted H8 M/S/U/K native correctness fixture:32 transitions,zero fits."""

import argparse
import os
from pathlib import Path
import resource
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    started = time.perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--launch-sha', required=True)
    parser.add_argument('--seed', required=True, type=int)
    args = parser.parse_args(argv)
    if args.seed != 29426999:
        parser.error('fixed correctness world29426999 only')
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[key] = '1'
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction='uav_user_waiting')
    if admission['sha'] != args.launch_sha:
        raise RuntimeError('fixture admission/source mismatch')
    import torch
    from experiments.candidates.uav_user_waiting.b04.study import (
        ARMS, collect_episode, save_episode, factory, write_json, file_identity, frozen_config,
    )
    from experiments.candidates.uav_user_waiting.b04.read_core import verify_episode
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    out = args.out.resolve()
    if (out / 'summary.json').exists():
        raise FileExistsError('no duplicate fixture execution')
    (out / 'raw').mkdir(parents=True, exist_ok=True)
    counts = dict(constructors=0, explicit_resets=0, native_step_calls=0, team_steps=0,
                  complete_episodes=0, fit_started=0, optimizer_steps=0)
    result = dict(object='UAV-USER-WAITING-B04-CORRECTNESS', status='RUNNING', launch_sha=args.launch_sha,
        admission=dict(admission), counts=counts, rows=[], verification=[], scientific_invocation=False,
        source_identities=frozen_config(args.launch_sha)['source_identities'],
        scope='four programs on oneH8 world,32 native steps; full native/history/search/pool/floor reader; no quality pilot')
    env = None
    try:
        env = factory(args.seed)
        counts['constructors'] += 1
        env.env.max_steps = 8
        for arm in ARMS:
            row, raw = collect_episode(env, arm, args.seed, out, counts, horizon=8)
            save_episode(out, row, raw)
            result['rows'].append(row)
            result['verification'].append(verify_episode(row, raw))
            write_json(out / 'summary.json', result)
        assert counts['team_steps'] == 32 and counts['complete_episodes'] == 4
        result['status'] = 'COMPLETE'
    except Exception as exc:
        result['status'] = 'INCOMPLETE_TECHNICAL_FAILURE'
        result['error'] = dict(type=type(exc).__name__, message=str(exc), traceback=traceback.format_exc())
    finally:
        if env is not None:
            env.close()
        usage = resource.getrusage(resource.RUSAGE_SELF)
        result['resources'] = dict(wall_seconds=time.perf_counter() - started,
            process_user_seconds=usage.ru_utime, process_system_seconds=usage.ru_stime,
            peak_rss_kib=usage.ru_maxrss, rss_scope='fixture lifetime Linux KiB')
        result['artifacts'] = [file_identity(path) for path in sorted((out / 'raw').iterdir()) if path.is_file()]
        write_json(out / 'summary.json', result)
    return result


if __name__ == '__main__':
    if main()['status'] != 'COMPLETE':
        raise SystemExit(1)
