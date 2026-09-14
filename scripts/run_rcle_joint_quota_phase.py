"""B08 through B12 whole native invocation. Timing includes adjacent admission."""
import os
for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ[name] = "1"
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--object", choices=("b08", "b09", "b10", "b11", "b12"), default="b08")
    parser.add_argument("--seed", type=int, choices=(28, 29, 30, 31, 32), default=28)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    args = parser.parse_args()
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    from experiments.candidates.roster_consistent_latent_exploration.joint_quota_phase.study import (
        run, run_exposure1024, run_replication1024, run_b12_exposure1024,
    )
    if args.object == "b12":
        result = run_b12_exposure1024(args.out, args.launch_sha, args.seed)
    elif args.object == "b11":
        result = run_replication1024(args.out, args.launch_sha, args.seed)
    elif args.object == "b10":
        result = run_exposure1024(args.out, args.launch_sha, args.seed)
    else:
        result = run(args.out, args.launch_sha, args.seed, greedy_anchored=args.object == "b09")
    print(result["status"], flush=True)


if __name__ == "__main__":
    main()
