#!/usr/bin/env python3
"""Admitted B07:64 new physical episodes,16384 steps,zero fits."""

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
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--launch-sha', required=True)
    parser.add_argument('--seed', type=int, required=True)
    args = parser.parse_args(argv)
    if args.seed != 29426000:
        parser.error('B07 fixes all64 worlds29426000..29426063')
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
        os.environ[key] = '1'
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction='uav_user_waiting')
    if admission['sha'] != args.launch_sha:
        raise RuntimeError('B07 admission/source mismatch')
    from experiments.candidates.uav_user_waiting.b07.protocol import baseline_directory
    from experiments.candidates.uav_user_waiting.b07.study import run_batch
    return run_batch(args.out, baseline_directory(args.out), args.launch_sha,
                     entry_start=started, admission=dict(admission))


if __name__ == '__main__':
    if main()['status'] != 'COMPLETE':
        raise SystemExit(1)
