"""B04 half-training-data comparison; retain full final evaluation and B02 RNG family."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_ucope_shared_data_return_model_b02 import run

OBJECT_ID = "UCOPE-SHARED-DATA-RETURN-MODEL-B04"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True, choices=(6601, 6602))
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    return run(args.out, seed=args.seed, object_id=OBJECT_ID, batches=512)


if __name__ == "__main__":
    raise SystemExit(main())
