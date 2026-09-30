"""Admitted fixed-artifact B07 evaluation; no fitting or implicit retry entry."""
import argparse
import os
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--fit-sha256", required=True)
    args = parser.parse_args()
    if args.seed != 29367991 or args.out.name != "b07_shortlist_amortization_a01":
        parser.error("fixed B07 seed/output tag differs; no implicit panel or retry")
    if args.fit_sha256 != "a2b5d1a8c127c50494e8b8aa76ff84ba3ca61e4b5db6281e4713e524ea2fd0c1":
        parser.error("B07 requires the original unchanged ranker")
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_parent_adaptation")
    if args.launch_sha != admission["sha"]:
        raise ValueError("CLI launch SHA differs from accepted immutable input")
    for variable in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[variable] = "1"
    from experiments.candidates.uav_parent_adaptation.b07_shortlist_amortization.study import run_study
    run_study(args.out.resolve(), args.launch_sha, admission, args.fit_sha256)


if __name__ == "__main__":
    main()
