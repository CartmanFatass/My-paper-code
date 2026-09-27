"""Admitted entry point for the fixed energy relay B01 imitation study."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", type=int, default=929031)
    args = parser.parse_args(argv)

    # Admission must run before scientific imports, checkpoint reads, or output creation.
    from scripts.hmasd_admission import require_admission

    admitted = require_admission(__file__, direction="energy_relay_imitation")
    if args.launch_sha != admitted["sha"]:
        raise ValueError("--launch-sha differs from admitted source SHA")
    if args.seed != 929031:
        raise ValueError("B01 fixes the model initialisation seed at 929031")

    # Set native library caps before importing NumPy/Torch through the study.
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                 "NUMEXPR_NUM_THREADS"):
        os.environ[name] = "1"

    from experiments.candidates.energy_relay_imitation.b01.study import run_batch

    result = run_batch(out=args.out, launch_sha=args.launch_sha, seed=args.seed)
    return 0 if result["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
