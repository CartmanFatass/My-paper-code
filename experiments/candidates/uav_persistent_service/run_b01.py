"""Admitted entry for the selected single-fit finite commitment comparison."""

from pathlib import Path
import argparse
import os
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--workers", type=int, choices=range(1,5), default=4)
    args = parser.parse_args()
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_persistent_service")
    if args.launch_sha != admission["sha"]:
        raise ValueError("scientific source SHA differs from admission")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[name] = "1"
    from experiments.candidates.uav_persistent_service.batch import run
    result = run(args.out, args.launch_sha, args.workers)
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
