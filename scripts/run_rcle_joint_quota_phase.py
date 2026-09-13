"""B08 whole native invocation. Enclosing timeout includes adjacent admission."""
import os
for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ[name] = "1"
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, choices=(28,), default=28)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    args = parser.parse_args()
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    from experiments.candidates.roster_consistent_latent_exploration.joint_quota_phase.study import run
    result = run(args.out, args.launch_sha, args.seed)
    print(result["status"], flush=True)


if __name__ == "__main__":
    main()
