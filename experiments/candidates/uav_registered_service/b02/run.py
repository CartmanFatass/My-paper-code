#!/usr/bin/env python3
"""Admitted fixed three-arm B02 periodic-efficiency panel:64 worlds,192episodes,zero fits."""

import argparse
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))


def main(argv=None):
    started=time.perf_counter()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--launch-sha',required=True)
    parser.add_argument('--seed',required=True,type=int)
    args=parser.parse_args(argv)
    if args.seed!=29309000:
        parser.error('B02 fixes reset seeds29309000..29309063')
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
        os.environ[name]='1'
    from scripts.hmasd_admission import require_admission
    admission=require_admission(__file__,direction='uav_registered_service')
    if admission['sha']!=args.launch_sha:
        raise RuntimeError('launch SHA differs from admission')
    from experiments.candidates.uav_registered_service.b02.study import run_batch
    return run_batch(args.out,args.launch_sha,entry_start=started,admission=dict(admission))


if __name__=='__main__':
    if main()['status']!='COMPLETE':
        raise SystemExit(1)
