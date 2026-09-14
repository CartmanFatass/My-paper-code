"""Fixed B06 entry: one fresh1000 fit or the attained reference endpoint."""
import time
STARTED = time.perf_counter()
import faulthandler
faulthandler.enable()
import os
for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ[name] = "1"
import argparse
from pathlib import Path
import signal
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=("learned", "reference"), required=True)
    parser.add_argument("--seed", type=int, choices=(26,), default=26)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--admission-receipt", type=Path, required=True)
    parser.add_argument("--learned-summary", type=Path)
    parser.add_argument("--wall-cap", type=float, required=True)
    args = parser.parse_args()
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    from experiments.candidates.roster_consistent_latent_exploration.b06_nearest99_prior1000.study import run, host
    def expired(signum, frame):
        raise host.ArmWallExpired(f"{args.wall_cap}s complete invocation cap")
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, max(.001, args.wall_cap - (time.perf_counter() - STARTED)))
    result = run(args.arm, args.out, args.launch_sha, args.admission_receipt,
                 STARTED, args.wall_cap, args.learned_summary, args.seed)
    signal.setitimer(signal.ITIMER_REAL, 0)
    print(result["status"], args.arm, flush=True)
    return 0 if result["status"] == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
