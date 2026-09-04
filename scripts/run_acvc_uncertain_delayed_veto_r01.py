#!/usr/bin/env python3
"""CLI for ACVC uncertain/delayed veto R01."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.candidates.acvc.uncertain_delayed_veto_r01.experiment import (  # noqa: E402
    BASE_SEED,
    project_cost,
    run_object,
)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = value.add_subparsers(dest="command", required=True)
    cost = commands.add_parser("project-cost", allow_abbrev=False)
    cost.add_argument("--output")
    run = commands.add_parser("run", allow_abbrev=False)
    run.add_argument("--output-root", required=True)
    run.add_argument("--admission-receipt", required=True)
    run.add_argument("--project-cost")
    run.add_argument("--seed", type=int, choices=(BASE_SEED,), default=BASE_SEED)
    run.add_argument("--toy", action="store_true")
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "project-cost":
        result = project_cost()
        encoded = json.dumps(result, indent=2, sort_keys=True)
        if args.output:
            Path(args.output).write_text(encoded + "\n", encoding="utf-8")
        print(encoded)
        return 0 if result["all_within_caps"] else 4
    toy = bool(args.toy)
    path = run_object(
        args.output_root,
        admission_receipt=args.admission_receipt,
        base_seed=args.seed,
        updates=2 if toy else 128,
        batch_size=8 if toy else 64,
        eval_episodes=32 if toy else 4_096,
        argv=tuple(sys.argv),
        toy=toy,
        project_cost_path=args.project_cost,
    )
    record = json.loads(path.read_text(encoding="utf-8"))
    result = {"summary": str(path)}
    if record["result_rule"] is not None:
        result.update(record["result_rule"])
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
