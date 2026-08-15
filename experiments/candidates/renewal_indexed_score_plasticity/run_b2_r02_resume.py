"""Production entry point for the frozen RISP-B2 revision-02 panel."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slice-wall-seconds", type=float, required=True)
    parser.add_argument("--rss-limit-bytes", type=int, default=1 << 30)
    parser.add_argument("--frontier", type=Path)
    parser.add_argument("--result", type=Path)
    arguments = parser.parse_args()

    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

    from b2_r02_resume import default_paths, run_slice

    default_frontier, default_result = default_paths(Path(__file__).resolve())
    packet = run_slice(arguments.frontier or default_frontier, arguments.result or default_result, arguments.slice_wall_seconds, arguments.rss_limit_bytes)
    print(json.dumps(packet, sort_keys=True, separators=(",", ":")), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

