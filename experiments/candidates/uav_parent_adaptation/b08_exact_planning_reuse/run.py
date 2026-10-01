"""One admitted local B08 replay and zero-query reader of fixed B04 evidence."""
import argparse
import os
from pathlib import Path
import sys
import time

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main():
    entry_mark = time.perf_counter(), time.process_time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--original-records", type=Path, required=True)
    parser.add_argument("--original-bulk", type=Path, required=True)
    args = parser.parse_args()
    if args.seed != 29368991 or args.out.name != "b08_exact_planning_reuse_a01":
        parser.error("fixed B08 identity/output tag differs; no implicit retry")
    if not args.original_records.is_absolute() or not args.original_bulk.is_absolute():
        parser.error("immutable original record and bulk roots must be absolute")
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_parent_adaptation")
    if args.launch_sha != admission["sha"]:
        raise ValueError("B08 requires its accepted source/operation")
    for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = "1"
    from experiments.candidates.uav_parent_adaptation.b08_exact_planning_reuse.study import run_study
    run_study(args.out.resolve(), args.launch_sha, admission,
              args.original_records, args.original_bulk, entry_mark=entry_mark)


if __name__ == "__main__":
    main()
