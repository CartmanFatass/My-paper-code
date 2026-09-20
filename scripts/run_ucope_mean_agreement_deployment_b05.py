#!/usr/bin/env python3
"""Run one admitted UCOPE B05 frozen-checkpoint deployment block."""

import argparse
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.hmasd_admission import require_admission


def main(argv=None):
    start = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", type=int, choices=(8931, 8932, 8933), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    args = parser.parse_args(argv)

    # Admission precedes output, Torch, checkpoint access and native construction.
    admission = require_admission(__file__, direction="ucope")
    if args.launch_sha != admission["sha"]:
        parser.error("--launch-sha must equal the admitted source SHA")

    for name in (
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        os.environ[name] = "1"

    import torch

    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    from experiments.candidates.ucope.mean_agreement_deployment_b05.study import Config, run

    result = run(Config(master=args.master), args.out, dict(admission), start=start)
    print(
        f"status={result['status']} master={args.master} "
        f"eval_steps={result['counts']['eval_team_steps']} optimizer_steps=0",
        flush=True,
    )
    return 0 if result["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
