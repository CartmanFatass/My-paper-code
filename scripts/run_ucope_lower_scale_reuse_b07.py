#!/usr/bin/env python3
"""Run one admitted prepared UCOPE B07 Bhalf/retained-Ghalf comparison."""

import argparse
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.hmasd_admission import require_admission


def main(argv=None):
    start = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", type=int, choices=(8941, 8942, 8943), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    args = parser.parse_args(argv)

    # Admission precedes output, Torch/scientific imports, models and native effects.
    admission = require_admission(__file__, direction="ucope")
    if args.launch_sha != admission["sha"]:
        parser.error("--launch-sha must equal the admitted source SHA")

    for name in (
        "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"
    ):
        os.environ[name] = "1"

    import torch

    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    from experiments.candidates.ucope.lower_scale_reuse_b07.study import Config, run

    result = run(Config(master=args.master), args.out, dict(admission), start=start)
    print(
        f"status={result['status']} master={args.master} "
        f"started_new_fits={result['fit_accounting']['started_new_fits']} "
        f"optimizer_steps={result['counts']['new_optimizer_steps']}",
        flush=True,
    )
    return 0 if result["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
