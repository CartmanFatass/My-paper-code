#!/usr/bin/env python3
"""Admitted, fixed B01 finite-model decision-value comparison."""

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", type=int, default=925731)
    parser.add_argument("--model-seed", type=int, default=925973)
    args = parser.parse_args(argv)
    if args.seed != 925731 or args.model_seed != 925973:
        parser.error("B01 seeds are fixed prospectively; no replacement seed")
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="finite_model_decision_value")
    if args.launch_sha != admission["sha"]:
        raise ValueError("launch-sha disagrees with native admission")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = "1"
    from experiments.candidates.finite_model_decision_value.b01.study import Config, run_study
    run_study(args.out, args.launch_sha, Config(seed=args.seed, model_seed=args.model_seed))


if __name__ == "__main__":
    main()
