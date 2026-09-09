"""One SCDMP held-residual pair or the explicit synthetic engineering fixture."""
import time
WHOLE_START = time.monotonic()

import os
for variable in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[variable] = "1"

import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engineering-fixture", action="store_true")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    expected = 9001 if args.engineering_fixture else 8201
    if args.seed != expected:
        parser.error(f"this mode requires --seed {expected}")
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    from experiments.candidates.scdmp_variable_k.native_hold_residual_b01.study import Config, run_pair
    config = Config.engineering() if args.engineering_fixture else Config()
    summary = run_pair(config, args.out, WHOLE_START)
    print(f"{summary['mode']}: {summary['status']}; summary: {args.out / 'summary.json'}")
    return 0 if summary["status"] in ("COMPLETE", "PRIMARY_COMPLETE_WITH_LIMITS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
