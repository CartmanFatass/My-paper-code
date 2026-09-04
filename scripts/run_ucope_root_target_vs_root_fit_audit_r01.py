#!/usr/bin/env python3
"""Runner for the UCOPE retained-tail root target-versus-fit A/RECON audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.candidates.ucope.root_target_vs_root_fit_audit_r01.audit import (  # noqa: E402
    project_cost,
    run_audit,
)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = value.add_subparsers(dest="command", required=True)
    commands.add_parser("project-cost", allow_abbrev=False)
    run = commands.add_parser("run", allow_abbrev=False)
    run.add_argument("--retained-summary", required=True)
    run.add_argument("--output-root", required=True)
    run.add_argument("--admission-receipt", required=True)
    run.add_argument("--thread-cap", type=int, choices=(1,), required=True)
    return value


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    if args.command == "project-cost":
        print(json.dumps(project_cost(), indent=2, sort_keys=True))
        return 0
    path = run_audit(
        args.retained_summary, args.output_root, args.admission_receipt,
        thread_cap=args.thread_cap, argv=sys.argv)
    result = json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps({"summary": str(path), "complete": result["complete"],
                      "result_rule": result["result_rule"]}, sort_keys=True))
    return 0 if result["complete"] else 6


if __name__ == "__main__":
    raise SystemExit(main())
