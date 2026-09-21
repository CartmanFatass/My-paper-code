#!/usr/bin/env python3
"""Run one declared B10 paired-credit/full-PPO/scalar block after native admission."""
import argparse
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.hmasd_admission import require_admission


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", type=int, choices=(8971, 8972, 8973), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    args = parser.parse_args(argv)
    admission = require_admission(__file__, direction="ucope")
    if args.launch_sha != admission["sha"]:
        parser.error("--launch-sha must equal the admitted source SHA")
    for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = "1"
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    from experiments.candidates.ucope.paired_branch_credit_b10.study import Config, run
    result = run(Config(args.master), args.out, dict(admission))
    print(f"status={result['status']} master={args.master} "
          f"started_gate_fits={result['fit_accounting']['started_new_gate_fits']}", flush=True)
    return 0 if result["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
