#!/usr/bin/env python3
"""Admitted complete actual RF/conditional-model reading; no new native worlds."""

import argparse
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))


def main(argv=None):
    started=time.perf_counter()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--generic-summary",type=Path,required=True)
    parser.add_argument("--worker-summary-sha256",required=True)
    parser.add_argument("--worker-launch-sha",required=True)
    parser.add_argument("--launch-sha",required=True)
    parser.add_argument("--seed",type=int,required=True)
    args=parser.parse_args(argv)
    if args.seed!=29651000:
        parser.error("B01 fixes the complete32-world result reader")
    for value,length in ((args.worker_summary_sha256,64),(args.worker_launch_sha,40),(args.launch_sha,40)):
        if len(value)!=length or any(x not in "0123456789abcdef" for x in value):
            parser.error("full lowercase source/hash identities required")
    for key in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
        os.environ[key]="1"
    from scripts.hmasd_admission import require_admission
    admission=require_admission(__file__,direction="uav_radio_information_cost")
    if admission["sha"]!=args.launch_sha:
        raise RuntimeError("reader admission/source mismatch")
    from experiments.candidates.uav_radio_information_cost.b01.reader import read_result
    return read_result(args.generic_summary,args.out,args.worker_summary_sha256,
                       args.worker_launch_sha,dict(admission),started)


if __name__=="__main__":
    if main()["status"]!="VERIFIED_COMPLETE":
        raise SystemExit(1)
