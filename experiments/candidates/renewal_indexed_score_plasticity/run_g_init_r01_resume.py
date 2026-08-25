"""Validated-production-binding entry point for RISP G-initialization R01."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--certificate", required=True, type=Path)
    parser.add_argument("--frontier", required=True, type=Path)
    parser.add_argument("--result-root", required=True, type=Path)
    parser.add_argument("--workers", required=True, type=int)
    parser.add_argument("--cpu-cores", required=True, type=int)
    parser.add_argument("--slice-wall-seconds", required=True, type=float)
    parser.add_argument("--per-worker-rss-limit-bytes", required=True, type=int)
    parser.add_argument("--process-group-rss-limit-bytes", required=True, type=int)
    args = parser.parse_args()
    for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"): os.environ.setdefault(key, "1")
    from g_init_r01_resume import _certificate_binding, run_slice
    from g_init_r01_coordinate_certificate import assert_production_paths
    import g_init_r01_coordinate_certificate as certificate_spec
    import g_init_r01_experiment as experiment
    if (args.workers != certificate_spec.WORKER_COUNT or args.cpu_cores != certificate_spec.CPU_CORES
            or args.slice_wall_seconds != certificate_spec.SLICE_WALL_SECONDS
            or args.per_worker_rss_limit_bytes != certificate_spec.PER_WORKER_RSS_LIMIT_BYTES
            or args.process_group_rss_limit_bytes != certificate_spec.PROCESS_GROUP_RSS_LIMIT_BYTES):
        raise RuntimeError("CLI resources do not match the validated R01 lease")
    assert_production_paths(args.certificate, args.frontier, args.result_root)
    certificate = _certificate_binding(args.certificate.resolve(), args.frontier.resolve(), args.result_root.resolve())
    # The sole production binder is reached only after full certificate validation.
    experiment.configure_production_coordinate_root(
        certificate["coordinate_root"], validated_production_binding=True,
    )
    packet = run_slice(
        args.frontier, args.result_root, args.certificate, args.slice_wall_seconds,
        args.per_worker_rss_limit_bytes, args.process_group_rss_limit_bytes,
        args.workers,
    )
    print(json.dumps(packet, sort_keys=True, separators=(",", ":")), flush=True)
    return 0
if __name__ == "__main__": raise SystemExit(main())
