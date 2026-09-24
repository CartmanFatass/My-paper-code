"""Admitted entry for the fixed complementary-skill B06 M/U comparison."""
import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.hmasd_admission import require_admission


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=("M", "U"), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.seed != 260923961:
        parser.error("B06 is fixed to initialization block 260923961")
    admission = require_admission(__file__, direction="complementary_skill_learning")
    if args.launch_sha != admission["sha"]:
        raise ValueError("launch SHA differs from admission")
    for variable in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ[variable] = "4"
    from experiments.candidates.complementary_skill_learning.b06.runner import (
        DEFAULT_SPEC,
        run_fit,
    )

    run_fit(
        args.arm,
        args.out,
        args.launch_sha,
        spec=DEFAULT_SPEC,
        device="cuda",
        admission=admission,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

