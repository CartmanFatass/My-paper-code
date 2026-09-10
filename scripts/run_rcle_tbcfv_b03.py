"""Fixed B03 runner; process startup and publication count toward its wall cap."""
import time
STARTED = time.perf_counter()
import faulthandler
faulthandler.enable()
import os
for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ[name] = "1"
import argparse
from pathlib import Path
import sys
import signal

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=("W1", "W100", "reference"), required=True)
    parser.add_argument("--seed", type=int, choices=(19, 20, 21, 22, 23), default=19)
    parser.add_argument("--updates", type=int, choices=(200, 1000), default=200)
    parser.add_argument("--reporting-object", default="RCLE-TBCFV-B03-ACTOR100")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--admission-receipt", type=Path, required=True)
    parser.add_argument("--control-summary", type=Path)
    parser.add_argument("--wall-cap", type=float, default=600)
    args = parser.parse_args()
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    from experiments.candidates.roster_consistent_latent_exploration_tbcfv_b03.study import run
    from experiments.candidates.roster_consistent_latent_exploration_tbcfv_b01.study import ArmWallExpired
    def expired(signum, frame):
        raise ArmWallExpired(f"{args.wall_cap}s complete invocation cap")
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, args.wall_cap - (time.perf_counter() - STARTED)))
    result = run(args.arm, args.out, args.launch_sha, args.admission_receipt,
                 STARTED, args.wall_cap, args.control_summary,
                 seed=args.seed, updates=args.updates, reporting_object=args.reporting_object)
    signal.setitimer(signal.ITIMER_REAL, 0)
    print(result["status"], args.arm, flush=True)
    return 0 if result["status"] == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
