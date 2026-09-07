"""Selected arm call; GENERIC includes the one rule evaluation and paired publication.

Existing external admission and one whole-call 2700s timeout are supplied at launch.
"""
import time

START = time.perf_counter()

import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[name] = "1"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=("FACTOR", "GENERIC"), required=True)
    parser.add_argument("--seed", type=int, choices=(402,), default=402)
    parser.add_argument("--out", type=Path, required=True, help="This arm's output directory")
    parser.add_argument("--factor-summary", type=Path, help="Accepted FACTOR summary; required for GENERIC")
    parser.add_argument("--describe", action="store_true", help="Configuration only; no interaction or learning")
    args = parser.parse_args()
    if args.arm == "GENERIC" and not args.describe and args.factor_summary is None:
        parser.error("GENERIC requires --factor-summary for the selected paired publication")
    from experiments.candidates.vsp_c1.k4_service_allocation_b01.experiment import (
        Budget, QNetwork, configuration, evaluate_rule, run)
    from experiments.candidates.vsp_c1.k4_service_allocation_b01.reporting import publish_comparison, write_read
    budget = Budget(seed=args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    if args.describe:
        write_read(args.out / "configuration.json", configuration(QNetwork(args.arm, args.seed), budget))
        print("Configuration only: one model initialization, zero host/update/evaluation/selection exposure.")
        return
    import numpy
    import torch
    torch.set_num_interop_threads(1)
    launch = {"sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "cwd": str(Path.cwd()), "hostname": platform.node(), "python": sys.executable,
              "argv": sys.argv, "numpy": numpy.__version__, "torch": torch.__version__}

    def publish(value):
        value["launch"] = launch
        write_read(args.out / "summary.json", value)

    summary = run(args.arm, budget, publish)
    if args.arm == "GENERIC":
        factor = json.loads(args.factor_summary.read_text(encoding="utf-8"))
        pair_path = args.out / "paired_summary.json"
        # Preserve a trustworthy learner contrast if the separate rule dependency fails.
        publish_comparison(pair_path, factor, summary)
        summary["rule"] = evaluate_rule(budget)
        publish(summary)
        publish_comparison(pair_path, factor, summary, summary["rule"])
    if os.name == "nt":
        try:
            import psutil
        except ImportError:
            rss = None
        else:
            rss = psutil.Process().memory_info().peak_wset
    else:
        import resource
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
    summary["resources"] = {
        "status": "measured" if rss is not None else "resources_unmeasured", "peak_rss_bytes": rss,
        "rss_scope": "main process lifetime high-water",
        "wall_seconds_through_primary_readback": time.perf_counter() - START,
        "wall_scope": "imports/learner/all evaluations/primary readback, including rule and paired publication for GENERIC; final metadata/stdout/exit inside external complete-call timing"}
    publish(summary)
    print(json.dumps({"status": summary["status"], "observed_counts": summary["observed_counts"],
                      "rule_observed_counts": summary.get("rule", {}).get("observed_counts"),
                      "wall_seconds_through_final_readback": time.perf_counter() - START}), flush=True)


if __name__ == "__main__":
    main()
