"""B03 independent-dataset follow-up; retain the B02 RNG family and learner."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_ucope_shared_data_return_model_b02 import run

OBJECT_ID = "UCOPE-SHARED-DATA-RETURN-MODEL-B03"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True, choices=(6501, 6502))
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    return run(args.out, seed=args.seed, object_id=OBJECT_ID)


if __name__ == "__main__":
    raise SystemExit(main())
