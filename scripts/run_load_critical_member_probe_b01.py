#!/usr/bin/env python3
"""Run the admitted source-bound load-critical-member frozen-policy panel."""

import argparse
import os
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.hmasd_admission import require_admission


def main(argv=None):
    command_start = time.perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--checkpoint-root", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    args = parser.parse_args(argv)

    # Admission precedes Torch, source-policy, environment, or evaluator import.
    admission = require_admission(__file__, direction="load_critical_member_generalization")
    if args.launch_sha != admission["sha"]:
        parser.error("--launch-sha must equal the admitted source SHA")
    for name in (
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        # Match the B03 producer's pre-import BLAS/OpenMP initialization.
        # The evaluator separately restores its declared four Torch threads.
        os.environ[name] = "1"

    from experiments.candidates.load_critical_member_generalization.load_probe.probe import (
        run_probe,
    )

    return run_probe(
        args.out,
        args.checkpoint_root,
        args.launch_sha,
        dict(admission),
        command_start=command_start,
    )


if __name__ == "__main__":
    raise SystemExit(main())
