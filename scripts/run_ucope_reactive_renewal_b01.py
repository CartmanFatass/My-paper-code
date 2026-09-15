#!/usr/bin/env python3
"""Run the one prospective reactive-renewal instance after external memory admission."""
import argparse
import os
from pathlib import Path
import sys
import time


def main():
    start = time.monotonic()
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=8901)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--watchdog-seconds", type=float, default=6000)
    parser.add_argument("--fixture", action="store_true")
    args = parser.parse_args()
    for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = "1"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    from experiments.candidates.ucope.reactive_renewal_b01.study import Config, run
    config = Config.engineering() if args.fixture else Config(seed=args.seed,
                                                               watchdog_seconds=args.watchdog_seconds)
    result = run(config, args.out, start=start)
    print(f"status={result['status']} native_steps={result['counts'].get('team_steps', 0)} "
          f"adam_calls={result['counts'].get('optimizer_steps', 0)}", flush=True)
    return 0 if result["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
