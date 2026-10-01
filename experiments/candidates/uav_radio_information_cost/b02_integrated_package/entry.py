"""Common admission boundary for the three explicit argparse entrypoints."""

import argparse
import os
from pathlib import Path
import time

from .config import DIRECTION, specification
from .source import verify_sources


def main(script, mode, argv=None):
    started = time.perf_counter()
    parser = argparse.ArgumentParser(description={
        "run":"B02: fixed 64 H256 episodes, zero fits",
        "check":"B02: exactly one paired H8 world and its complete reader",
        "read":"B02: full saved-byte reconstruction of the 32 paired worlds",
    }[mode])
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--launch-sha",required=True)
    parser.add_argument("--seed",type=int,required=True)
    if mode == "read":
        parser.add_argument("--generic-summary",type=Path,required=True)
        parser.add_argument("--worker-summary-sha256",required=True)
        parser.add_argument("--worker-launch-sha",required=True)
    args = parser.parse_args(argv)
    spec = specification("check" if mode == "check" else "main")
    if args.seed != spec["worlds"][0]:
        parser.error("fixed B02 world seed required")
    identities = [(args.launch_sha,40)]
    if mode == "read":
        identities += [(args.worker_launch_sha,40),(args.worker_summary_sha256,64)]
    for value,length in identities:
        if len(value) != length or any(x not in "0123456789abcdef" for x in value):
            parser.error("full lowercase source/hash identities required")
    if not __debug__:
        raise RuntimeError("original reconstruction requires Python assertions")
    for key in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
        os.environ[key] = "1"
    from scripts.hmasd_admission import require_admission
    admission = dict(require_admission(script,direction=DIRECTION))
    if admission["sha"] != args.launch_sha:
        raise ValueError("admission/source mismatch")
    verify_sources()
    if mode == "read":
        from .reader import read_result
        return read_result(args.generic_summary,args.out,args.worker_summary_sha256,
                           args.worker_launch_sha,admission,started)
    from .study import run_batch, run_check
    return (run_check if mode == "check" else run_batch)(
        args.out,args.launch_sha,admission,started)
