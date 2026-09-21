"""Admitted entry for fixed VSP-03 B11 public R0 calibration."""

import time

START_WALL = time.monotonic()
START_CPU = time.process_time()

import argparse
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.hmasd_admission import require_admission


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, nargs=3, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if tuple(args.seeds) != (22001, 22002, 22003):
        parser.error("B11 seeds are fixed at 22001 22002 22003")
    admission = require_admission(__file__, direction="vsp_03")
    if args.launch_sha != admission["sha"]:
        parser.error("launch-sha differs from admitted source")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = "1"
    from experiments.candidates.vsp_03.opportunity_calibration_b11.study import run

    summary = run(args.out, args.launch_sha, args.seeds)
    summary["runner_wall_s_through_final_publication"] = time.monotonic() - START_WALL
    summary["runner_cpu_s"] = time.process_time() - START_CPU
    summary["runner_cpu_scope"] = "single process user plus system; no child computation"
    path = args.out / "summary.json"
    path.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    if json.loads(path.read_text(encoding="utf-8")) != summary:
        raise AssertionError("runner summary readback mismatch")
    print(json.dumps({"status": summary["status"],
                      "comparisons": summary["comparisons"]}), flush=True)


if __name__ == "__main__":
    main()
