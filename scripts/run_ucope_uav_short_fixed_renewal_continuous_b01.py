"""One continuous short fixed renewal pair or synthetic engineering fixture."""
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
from experiments.candidates.ucope.uav_short_fixed_renewal_continuous_b01.study import Config, SELECTOR, run_pair


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pair", choices=(SELECTOR,), default=SELECTOR)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--engineering-fixture", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.seed != (9001 if args.engineering_fixture else 8601):
        parser.error("requires seed9001 for fixture or seed8601 for real pair")
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    result = run_pair(Config.engineering() if args.engineering_fixture else Config(args.seed), args.out, WHOLE_START)
    print(json.dumps(dict(mode=result["mode"], status=result["status"], primary=result["primary"], counts=result["counts"]), allow_nan=False))
    return 0 if result["status"] in ("COMPLETE", "PRIMARY_COMPLETE_WITH_LIMITS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
