"""Admitted entry for five fixed VSP-03 confirmation blocks."""

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
    parser.add_argument("--seeds", type=int, nargs=5, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if tuple(args.seeds) != (21901, 21902, 21903, 21904, 21905):
        parser.error("B09 seeds are fixed at 21901 21902 21903 21904 21905")
    admission = require_admission(__file__, direction="vsp_03")
    if args.launch_sha != admission["sha"]:
        parser.error("launch-sha differs from admitted source")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = "1"
    from experiments.candidates.vsp_03.opportunity_b09.study import run
    summary = run(args.out, args.launch_sha, args.seeds)
    summary["runner_wall_s_through_final_publication"] = time.monotonic() - START_WALL
    summary["runner_cpu_s"] = time.process_time() - START_CPU
    summary["runner_cpu_scope"] = "single process user plus system; no child computation"
    path = args.out / "summary.json"
    path.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    if json.loads(path.read_text(encoding="utf-8")) != summary:
        raise AssertionError("runner summary readback mismatch")
    print(json.dumps({"status": summary["status"], "reading": summary["reading"],
                      "primary": summary["comparisons"]["O-G"]}), flush=True)


if __name__ == "__main__":
    main()
