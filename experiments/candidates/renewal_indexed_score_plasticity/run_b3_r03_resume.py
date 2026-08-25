"""Lease-bound production entry point for RISP-B3/TRG revision 03."""

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
    parser.add_argument("--result-root", type=Path)
    parser.add_argument("--certificate", type=Path)
    arguments = parser.parse_args()

    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

    from b3_r03_resume import default_paths, run_slice

    default_frontier, default_result_root, default_certificate = default_paths(Path(__file__).resolve())
    packet = run_slice(
        arguments.frontier or default_frontier,
        arguments.result_root or default_result_root,
        arguments.certificate or default_certificate,
        arguments.slice_wall_seconds,
        arguments.rss_limit_bytes,
    )
    print(json.dumps(packet, sort_keys=True, separators=(",", ":")), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
