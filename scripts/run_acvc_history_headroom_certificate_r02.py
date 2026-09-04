#!/usr/bin/env python3
"""Run the exact ACVC R02 threshold certificate or its result-blind cost path."""

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

from experiments.candidates.acvc.history_headroom_certificate_r02.experiment import (  # noqa: E402
    RSS_CAP_BYTES,
    WALL_CAP_SECONDS,
    run_mock_publication,
    run_result,
    run_synthetic,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    subparsers = result.add_subparsers(dest="mode", required=True)
    subparsers.add_parser("project-cost", help="run the full result-blind synthetic cost path")
    smoke = subparsers.add_parser("smoke", help="run a reduced result-blind publication smoke")
    smoke.add_argument("--output-root", required=True)
    formal = subparsers.add_parser("result", help="run the sole formal exact invocation")
    formal.add_argument("--output-root", required=True)
    formal.add_argument("--admission-receipt", required=True)
    formal.add_argument("--launch-sha", required=True)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.mode == "project-cost":
        record = run_synthetic(full_candidates=True)
        # The synthetic objective and choices are discarded before this result-blind report.
        print(json.dumps(record, sort_keys=True))
        peak = record["peak_rss_bytes"]
        passed = (
            3 * record["wall_seconds"] <= WALL_CAP_SECONDS
            and peak is not None
            and 2 * peak <= RSS_CAP_BYTES
        )
        return 0 if passed else 2
    if args.mode == "smoke":
        summary = run_mock_publication(args.output_root, argv=tuple(sys.argv))
        print(json.dumps({"summary": str(summary), "result_blind": True}, sort_keys=True))
        return 0
    summary = run_result(
        args.output_root,
        admission_receipt=args.admission_receipt,
        launch_sha=args.launch_sha,
        argv=tuple(sys.argv),
    )
    print(json.dumps({"summary": str(summary)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
