"""The allocated continue/end-credit L/F comparison, master8801."""
import time
WHOLE_START = time.monotonic()
import os
for variable in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[variable] = "1"
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, choices=(8801,), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--admission-start-unix", type=float)
    args = parser.parse_args()
    start = WHOLE_START if args.admission_start_unix is None else time.monotonic()-(time.time()-args.admission_start_unix)
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    from experiments.candidates.ucope.uav_continue_end_credit_b01.study import Config, run_pair
    result = run_pair(Config(seed=args.seed), args.out, start)
    print(json.dumps(dict(status=result["status"], primary=result["primary"], counts=result["counts"]), allow_nan=False))
    return 0 if result["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
