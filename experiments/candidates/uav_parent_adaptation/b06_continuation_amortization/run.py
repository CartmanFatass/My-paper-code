"""Admitted single-fit or fixed-artifact B06 evaluation, never an implicit retry."""
import argparse
import os
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("fit", "evaluate"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--fit-sha256")
    args = parser.parse_args()
    expected_tag = "b06_paid_ranker_fit_a01" if args.phase == "fit" else "b06_continuation_amortization_a01"
    if args.seed != 29366991 or args.out.name != expected_tag:
        parser.error("fixed seed/output tag differs; no implicit new panel or retry")
    if (args.phase == "evaluate") != (args.fit_sha256 is not None):
        parser.error("only evaluation requires its published fit SHA256")
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_parent_adaptation")
    if args.launch_sha != admission["sha"]:
        raise ValueError("CLI launch SHA differs from accepted immutable input")
    for variable in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[variable] = "1"
    if args.phase == "fit":
        from experiments.candidates.uav_parent_adaptation.b06_continuation_amortization.fit import run_fit
        run_fit(args.out.resolve(), args.launch_sha, admission)
    else:
        from experiments.candidates.uav_parent_adaptation.b06_continuation_amortization.study import run_study
        run_study(args.out.resolve(), args.launch_sha, admission, args.fit_sha256)


if __name__ == "__main__":
    main()
