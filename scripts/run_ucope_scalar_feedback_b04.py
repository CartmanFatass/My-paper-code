#!/usr/bin/env python3
"""Run one admitted fixed B/G/H scalar-feedback B04 block."""

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
    parser.add_argument("--launch-sha", help="must equal the admitted source SHA")
    args = parser.parse_args(argv)

    # No output, Torch import, environment, learner or evaluator exists yet.
    admission = require_admission(__file__, direction="ucope")
    if args.launch_sha is not None and args.launch_sha != admission["sha"]:
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
    from experiments.candidates.ucope.scalar_feedback_b04.study import Config, run

    result = run(
        Config(seed=args.master),
        args.out,
        admission=dict(admission),
        start=start,
    )
    print(
        f"status={result['status']} master={args.master} "
        f"native_steps={result['counts'].get('team_steps', 0)} "
        f"adam_calls={result['counts'].get('optimizer_steps', 0)}",
        flush=True,
    )
    return 0 if result["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
