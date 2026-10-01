#!/usr/bin/env python3
"""Admitted fixed engineering exposure: four H8 episodes,32 native steps,zero fits."""

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
    parser.add_argument("--launch-sha",required=True)
    parser.add_argument("--seed",type=int,required=True)
    args=parser.parse_args(argv)
    if args.seed!=29641900:
        parser.error("fixed H8 correctness world29641900 required")
    for key in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
        os.environ[key]="1"
    from scripts.hmasd_admission import require_admission
    admission=require_admission(__file__,direction="uav_radio_uncertainty")
    if admission["sha"]!=args.launch_sha:
        raise RuntimeError("correctness admission/source mismatch")
    from experiments.candidates.uav_radio_uncertainty.b01.correctness import run_correctness
    return run_correctness(args.out,args.launch_sha,dict(admission),started)


if __name__=="__main__":
    if main()["status"]!="VERIFIED_COMPLETE":
        raise SystemExit(1)
