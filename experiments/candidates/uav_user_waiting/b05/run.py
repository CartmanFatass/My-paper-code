#!/usr/bin/env python3
"""Admitted complete conditional B04 allocation replay; zero native work/fits."""

import argparse
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    started = time.perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--launch-sha', required=True)
    parser.add_argument('--seed', required=True, type=int)
    parser.add_argument('--generic-summary', required=True, type=Path)
    parser.add_argument('--generic-summary-sha256', required=True)
    args = parser.parse_args(argv)
    if args.seed != 29426000:
        parser.error('B05 fixes reused worlds29426000..29426063')
    if len(args.launch_sha) != 40 or any(c not in '0123456789abcdef' for c in args.launch_sha):
        parser.error('complete lowercase launch SHA required')
    if not args.out.is_absolute() or not args.generic_summary.is_absolute() or args.generic_summary.name != 'summary.json':
        parser.error('absolute output and canonical summary.json paths required')
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[key] = '1'
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction='uav_user_waiting')
    if admission['sha'] != args.launch_sha:
        raise RuntimeError('launch SHA differs from admission')
    from experiments.candidates.uav_user_waiting.b05.protocol import SUMMARY_SHA256
    if args.generic_summary_sha256 != SUMMARY_SHA256:
        raise RuntimeError('frozen B04 summary digest mismatch')
    from experiments.candidates.uav_user_waiting.b05.study import run_batch
    reading = args.generic_summary.parent.parent / 'b04_service_floor_read_a01' / 'reading.json'
    return run_batch(args.out, args.launch_sha, args.generic_summary, reading,
                     ROOT, entry_start=started, admission=dict(admission))


if __name__ == '__main__':
    if main()['status'] != 'COMPLETE':
        raise SystemExit(1)
