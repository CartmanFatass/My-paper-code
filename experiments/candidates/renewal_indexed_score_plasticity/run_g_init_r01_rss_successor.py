"""Exact launch wrapper for the RISP G-init R01 RSS technical successor."""
from __future__ import annotations

import argparse
from pathlib import Path

try:
    from . import g_init_r01_rss_successor as successor
except ImportError:
    import g_init_r01_rss_successor as successor


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--certificate", required=True, type=Path)
    parser.add_argument("--frontier", required=True, type=Path)
    parser.add_argument("--result-root", required=True, type=Path)
    parser.add_argument("--successor-acceptance", required=True, type=Path)
    parser.add_argument("--successor-lease", required=True, type=Path)
    parser.add_argument("--workers", required=True, type=int)
    parser.add_argument("--cpu-cores", required=True, type=int)
    parser.add_argument("--slice-wall-seconds", required=True, type=float)
    parser.add_argument("--per-worker-rss-limit-bytes", required=True, type=int)
    parser.add_argument("--process-group-rss-limit-bytes", required=True, type=int)
    args = parser.parse_args()
    if {
        "workers": args.workers, "cpu_cores": args.cpu_cores,
        "slice": args.slice_wall_seconds, "worker_rss": args.per_worker_rss_limit_bytes,
        "group_rss": args.process_group_rss_limit_bytes,
    } != {
        "workers": successor.WORKERS, "cpu_cores": successor.CPU_CORES,
        "slice": successor.SLICE_SECONDS, "worker_rss": successor.PER_WORKER_RSS_BYTES,
        "group_rss": successor.SUCCESSOR_GROUP_RSS_BYTES,
    }:
        raise successor.SuccessorValidationError("wrapper resources differ from the exact RSS successor whitelist")
    return successor.invoke_unchanged_runner(
        certificate=args.certificate, frontier=args.frontier, result_root=args.result_root,
        successor_acceptance=args.successor_acceptance, successor_lease=args.successor_lease,
    )


if __name__ == "__main__":
    raise SystemExit(main())
