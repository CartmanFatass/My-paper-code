"""Run the EOCIV-B9R1 receiver-addressed one-step experiment."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from experiments.candidates.eociv_lite.b9r1.experiment import run_experiment


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("smoke", "full"), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args()
    torch.set_num_threads(1)
    command = [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]]
    summary = run_experiment(
        mode=args.mode,
        seed=args.seed,
        run_root=args.run_root.resolve(),
        repository_root=ROOT,
        exact_command=command,
    )
    print(summary["branch"])
    return 0 if summary["status"] != "INVALID_ATTEMPT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
