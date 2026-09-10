"""The fixed fresh VSPC1 B06 matched training pair."""
import time
WHOLE_START = time.monotonic()

import os
for variable in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[variable] = "1"

import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

OBJECT = "VSPC1-NATIVE-HOLD-VALUE-B06"
CARD = "docs/research/candidates/vsp_c1/VSPC1_NATIVE_HOLD_VALUE_B06_SCIENCE_CARD_20260908.md"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.seed != 8302:
        parser.error("B06 requires --seed 8302")
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    from experiments.candidates.vsp_c1.native_hold_value_b01.study import Config, run_pair
    summary = run_pair(Config(seed=args.seed), args.out, WHOLE_START, object_id=OBJECT, card=CARD, normalize_value=True, second_mlp_width=133, extra_init_seed=100000 * args.seed + 12)
    print(f"{summary['mode']}: {summary['status']}; summary: {args.out / 'summary.json'}")
    return 0 if summary["status"] in ("COMPLETE", "PRIMARY_COMPLETE_WITH_LIMITS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
