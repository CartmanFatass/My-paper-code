"""Admission-guarded one-purchase B08 entry; no resume or hidden test mode."""
import argparse
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--input-manifest", type=Path, required=True)
    parser.add_argument("--input-manifest-sha256", required=True)
    args = parser.parse_args(argv)
    if args.seed != 26100388:
        raise ValueError("B08 uses only its prospectively bound namespace")
    from scripts.hmasd_admission import require_admission
    accepted = require_admission(__file__, direction="typed_joint_skill_decision")
    if accepted["sha"] != args.launch_sha:
        raise ValueError("source SHA differs from admitted operation")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = "1"
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    from experiments.candidates.typed_joint_skill_decision.b08_two_stage_value.execution import run_study
    run_study(args.out.resolve(), args.launch_sha, accepted, args.input_manifest.resolve(),
              args.input_manifest_sha256, started)


if __name__ == "__main__":
    main()
