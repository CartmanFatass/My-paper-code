"""One frozen A02 invocation, including imports/build/loading and publication."""

import time

STARTED = time.perf_counter()

import argparse
import json
import os
from pathlib import Path
import signal
import sys

for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ[name] = "1"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--summary-root", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--admission-receipt", type=Path, required=True)
    parser.add_argument("--seed", type=int, choices=(18,), default=18)
    parser.add_argument("--wall-cap", type=float, default=288.0)
    args = parser.parse_args(argv)

    def stop(signum, frame):
        raise TimeoutError("A02 complete-invocation wall limit; publication reserve")

    # The configured node is POSIX. The frozen external timeout also charges
    # prior focused checks against 300s; this alarm reserves publication time.
    signal.signal(signal.SIGALRM, stop)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, args.wall_cap - (time.perf_counter() - STARTED)))
    try:
        import torch
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        from experiments.candidates.roster_consistent_latent_exploration.tbcfv_a02.study import run
        summary = run(args.out, args.state_root, args.summary_root, args.launch_sha,
                      args.admission_receipt, STARTED)
    except Exception as exc:
        args.out.mkdir(parents=True, exist_ok=True)
        previous = args.out / "summary.json"
        try:
            summary = json.loads(previous.read_text()) if previous.exists() else {}
        except json.JSONDecodeError:
            summary = {"partial_summary_interrupted": True}
        summary.update({"status": "TECHNICAL_STOP", "stop_reason": f"{type(exc).__name__}: {exc}",
                        "launch_sha": args.launch_sha, "wall_seconds": time.perf_counter() - STARTED})
        temporary = args.out / "summary.tmp"
        temporary.write_text(json.dumps(summary, indent=2) + "\n")
        temporary.replace(args.out / "summary.json")
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    print(json.dumps({"status": summary["status"], "wall_seconds": summary["wall_seconds"]}))
    return 0 if summary["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
