#!/usr/bin/env python3
"""Admitted fixed B03 R/S2/T2 panel, 64 worlds and zero fits."""

import argparse
import os
from pathlib import Path
import resource
import signal
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
    args = parser.parse_args(argv)
    if args.seed != 29307000:
        parser.error('B03 fixes reset seeds29307000..29307063')
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
                 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
        os.environ[name] = '1'
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction='uav_radio_activation')
    if admission['sha'] != args.launch_sha:
        raise RuntimeError('launch SHA differs from admission')
    from experiments.candidates.uav_radio_activation.b03.study import ResourceLimit, run_batch

    def cpu_exceeded(signum, frame):
        raise ResourceLimit('three CPU-hour native-worker ceiling reached (SIGXCPU)')

    signal.signal(signal.SIGXCPU, cpu_exceeded)
    resource.setrlimit(resource.RLIMIT_CPU, (10800, 10802))
    return run_batch(args.out, args.launch_sha, entry_start=started)


if __name__ == '__main__':
    if main()['status'] != 'COMPLETE':
        raise SystemExit(1)
