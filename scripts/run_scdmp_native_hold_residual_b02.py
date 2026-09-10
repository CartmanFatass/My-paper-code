"""One unchanged independent SCDMP held-residual B02 pair, master8202."""
import time
WHOLE_START = time.monotonic()

import os
for variable in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[variable] = "1"

import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

OBJECT = "SCDMP-NATIVE-HOLD-RESIDUAL-B02"
CARD = "docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_HOLD_RESIDUAL_B02_SCIENCE_CARD_20260910.md"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.seed != 8202:
        parser.error("this object requires --seed 8202")
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    from experiments.candidates.scdmp_variable_k.native_hold_residual_b01.study import Config, run_pair
    summary = run_pair(Config(seed=args.seed), args.out, WHOLE_START,
                       object_name=OBJECT, card_path=CARD)
    print(f"{summary['mode']}: {summary['status']}; summary: {args.out / 'summary.json'}")
    return 0 if summary["status"] in ("COMPLETE", "PRIMARY_COMPLETE_WITH_LIMITS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
