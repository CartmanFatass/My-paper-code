#!/usr/bin/env python3
"""CLI for the exact ACVC history-headroom reconstruction."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.candidates.acvc.history_headroom_r01.experiment import run_object  # noqa: E402


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    value.add_argument("--output-root", required=True)
    value.add_argument("--admission-receipt", required=True)
    value.add_argument("--toy", action="store_true")
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    summary = run_object(
        args.output_root,
        admission_receipt=args.admission_receipt,
        argv=tuple(sys.argv),
        toy=bool(args.toy),
    )
    record = json.loads(summary.read_text(encoding="utf-8"))
    response = {"summary": str(summary), "result_rule": record["result_rule"]}
    print(json.dumps(response, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
