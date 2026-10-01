#!/usr/bin/env python3
"""Admitted independent complete reading of the fixed B05 allocation replay."""

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
    parser.add_argument('--generic-summary', required=True, type=Path,
                        help='external canonical B05 summary; preserved by the snapshot launcher')
    parser.add_argument('--generic-summary-sha256', required=True)
    parser.add_argument('--worker-launch-sha', required=True)
    args = parser.parse_args(argv)
    if args.seed != 29426000:
        parser.error('B05 fixes all64 worlds29426000..29426063')
    if (len(args.generic_summary_sha256) != 64 or
            any(character not in '0123456789abcdef' for character in args.generic_summary_sha256)):
        parser.error('worker summary requires its exact SHA256')
    if (not args.out.is_absolute() or not args.generic_summary.is_absolute()
            or args.generic_summary.name != 'summary.json'):
        parser.error('absolute output and canonical summary.json paths required')
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
                'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
        os.environ[key] = '1'
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction='uav_user_waiting')
    if admission['sha'] != args.launch_sha:
        raise RuntimeError('reader launch SHA differs from admission')
    from experiments.candidates.uav_user_waiting.b05.reader import read_batch
    return read_batch(args.generic_summary.parent, args.out, args.launch_sha,
                      args.worker_launch_sha, args.generic_summary_sha256,
                      entry_start=started, admission=dict(admission))


if __name__ == '__main__':
    if main()['status'] != 'COMPLETE':
        raise SystemExit(1)
