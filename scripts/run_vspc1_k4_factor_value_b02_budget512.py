"""One arm invocation; memory admission and the 2700 s timeout are external."""
import time

START_WALL = time.perf_counter()
START_CPU = time.process_time()

import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

# Set before importing NumPy/Torch, including BLAS libraries inside those imports.
for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[name] = "1"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=("FACTOR", "GENERIC"), required=True)
    parser.add_argument("--seed", type=int, choices=(3,), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    from experiments.candidates.vsp_c1.k4_factor_value_b01.budget512 import run
    from experiments.candidates.vsp_c1.k4_factor_value_b01.reporting import write_read
    import numpy
    import torch

    launch = {"sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "hostname": platform.node(), "cwd": str(Path.cwd()), "python": sys.executable,
              "argv": sys.argv, "numpy": numpy.__version__, "torch": torch.__version__}
    args.out.mkdir(parents=True, exist_ok=True)
    summary = run(args.arm, args.seed, args.out, launch)
    if os.name == "nt":
        import psutil
        peak_rss = psutil.Process().memory_info().peak_wset
        aggregate_cpu = None  # Exited git child CPU is not retained by this Windows primitive.
    else:
        import resource
        own = resource.getrusage(resource.RUSAGE_SELF)
        children = resource.getrusage(resource.RUSAGE_CHILDREN)
        peak_rss = int(own.ru_maxrss) * (1 if sys.platform == "darwin" else 1024)
        aggregate_cpu = own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime
    summary["resources"] = {
        "wall_seconds_through_primary_readback": time.perf_counter() - START_WALL,
        "peak_rss_bytes": peak_rss, "rss_scope": "main process lifetime high-water",
        "aggregate_cpu_seconds_through_primary_readback": aggregate_cpu,
        "cpu_scope": "process cumulative plus exited child cumulative; threads not counted twice",
        "status": "measured" if aggregate_cpu is not None else "resources_unmeasured",
        "timing_note": "Includes heavy imports, initialization, training, 33 evaluations and primary publication/readback; final metadata write/read and stdout are covered by external invocation timing.",
    }
    write_read(args.out / "summary.json", summary)
    print(json.dumps({"arm": args.arm, "status": summary["status"],
                      "wall_seconds_through_final_readback": time.perf_counter() - START_WALL,
                      "process_cpu_seconds": time.process_time() - START_CPU,
                      "cost_law": summary["cost_law"]}), flush=True)
    return 0 if summary["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
