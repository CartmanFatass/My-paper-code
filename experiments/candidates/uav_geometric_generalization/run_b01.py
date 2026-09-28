#!/usr/bin/env python3
"""Admitted fixed c06 P/C deployment comparison on native S7-S2."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--checkpoint-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    from scripts.hmasd_admission import require_admission

    admission = require_admission(__file__, direction="uav_geometric_generalization")
    if admission["sha"] != args.launch_sha:
        raise RuntimeError("launch SHA does not match admission")
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[key] = "1"
    from experiments.candidates.uav_geometric_generalization.b01.study import run

    return run(args.out, args.launch_sha, args.checkpoint_dir)


if __name__ == "__main__":
    if main()["status"] != "complete":
        raise SystemExit(1)
