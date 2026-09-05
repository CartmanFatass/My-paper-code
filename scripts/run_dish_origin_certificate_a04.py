"""Data-only A04 readout; run via python -m after external admit-memory && runner."""

import argparse
import json
from pathlib import Path
import subprocess
import time

from experiments.candidates.degraded_incumbent_shadow_handover import certificate_a04 as certificate

ROOT = Path(__file__).resolve().parents[1]


def project_cost():
    return {"law": "1.5 * (5 + 4 * (1 + 1))", "projected_seconds": 19.5, "cap_seconds": 60.0}


def run(trace, admission, output):
    started = time.perf_counter()
    result = certificate.read_trace(trace, started + certificate.CAP_SECONDS)
    launch_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                                capture_output=True, text=True).stdout.strip()
    try:
        import resource
        rss = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024
    except (ImportError, OSError):
        rss = None
    wall = time.perf_counter() - started
    result.update(trace_path=str(trace.resolve()), admission_receipt=str(admission.resolve()),
                  launch_sha=launch_sha, wall_seconds=wall, peak_rss_bytes=rss,
                  resources_unmeasured=rss is None,
                  measured_cost={"origin_reconstructions": 4, "wall_seconds": wall, "seconds_per_origin": wall / 4},
                  timing_scope="Full trace read, four reconstructions and metadata; summary serialization/write excluded, cap checked after publication.")
    if wall >= certificate.CAP_SECONDS:
        raise RuntimeError("incomplete A04: 60-second cap reached before publication")
    output.mkdir(parents=True)
    (output / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    result["completed_peak_rss_bytes"] = (int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024
                                          if rss is not None else None)
    completed_wall = time.perf_counter() - started
    if completed_wall >= certificate.CAP_SECONDS:
        raise RuntimeError("incomplete A04: 60-second cap reached during publication")
    result["completed_runner_wall_seconds"] = completed_wall
    result["summary_publication_seconds"] = completed_wall - wall
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    modes = parser.add_subparsers(dest="mode", required=True)
    modes.add_parser("project-cost")
    command = modes.add_parser("run")
    command.add_argument("--seed", type=int, choices=(11,), required=True)
    command.add_argument("--trace", type=Path, required=True)
    command.add_argument("--admission", type=Path, required=True)
    command.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    result = project_cost() if args.mode == "project-cost" else run(args.trace, args.admission, args.out)
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
