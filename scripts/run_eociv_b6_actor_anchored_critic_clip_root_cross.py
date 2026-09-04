"""Production phase runner for EOCIV-B6."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.eociv_lite.actor_anchored_critic_clip_root_cross import (
    analyze_evaluation,
    evaluate_raw,
    read_json,
    run_train,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="EOCIV-B6 frozen train/evaluate/analyze runner")
    sub = parser.add_subparsers(dest="phase", required=True)
    train = sub.add_parser("train")
    train.add_argument("--mode", choices=("smoke", "full"), required=True)
    train.add_argument("--source-commit", required=True)
    train.add_argument("--run-id", required=True)
    train.add_argument("--output", required=True)
    for phase in ("evaluate", "analyze"):
        child = sub.add_parser(phase)
        child.add_argument("--input", required=True)
        child.add_argument("--output", required=True)
    args = parser.parse_args()
    torch.set_num_threads(1)
    if args.phase == "train":
        result = run_train(args.mode, source_commit=args.source_commit, run_id=args.run_id)
    elif args.phase == "evaluate":
        result = evaluate_raw(read_json(args.input))
    else:
        result = analyze_evaluation(read_json(args.input))
    write_json(result, args.output)
    print(json.dumps({
        "phase": args.phase,
        "mechanical_status": result["mechanical_status"],
        "mode": result["mode"],
        "terminal_label": result.get("terminal_label"),
        "output": args.output,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
