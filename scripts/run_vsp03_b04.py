"""Sole VSP03 B04 invocation; external timeout covers admission through exit."""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

for variable in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[variable] = "1"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.candidates.vsp_03.vsp03_b03.b03 import run


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, choices=[6], default=6)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--started-monotonic", type=float, required=True,
                        help="Monotonic time from immediately before adjacent admission")
    parser.add_argument("--node", choices=["wsl_4070"], required=True)
    args = parser.parse_args()
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    run(args.seed, args.out, sha, args.started_monotonic, args.node,
        os.environ["VSP03_B04_COMMAND"], object_name="VSP03_B04")
    print("runner_exit_ready elapsed_s=" + str(time.perf_counter() - args.started_monotonic), flush=True)
