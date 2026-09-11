"""One B01 arm; external agent-task timeout and node-local admission bound the invocation."""
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
    parser.add_argument("--arm", choices=("FACTOR", "GENERIC"))
    parser.add_argument("--seed", type=int, choices=(401,), default=401)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--describe", action="store_true", help="Configuration only; zero interaction/update exposure")
    parser.add_argument("--technical-fixture", action="store_true", help="Fixed seed 9401, 16 updates, 2 episodes per period; not B01 evidence")
    parser.add_argument("--compare", nargs=2, type=Path, metavar=("FACTOR_SUMMARY", "GENERIC_SUMMARY"))
    args = parser.parse_args()
    from experiments.candidates.vsp_c1.k4_reactive_queues_b01.experiment import Budget, configuration, run
    from experiments.candidates.vsp_c1.k4_reactive_queues_b01.reporting import compare, write_read
    if args.compare:
        value = compare(*(json.loads(p.read_text(encoding="utf-8")) for p in args.compare))
        args.out.parent.mkdir(parents=True, exist_ok=True)
        write_read(args.out, value)
        print(json.dumps({"status": value["status"], "output": str(args.out)}))
        return
    if args.arm is None:
        parser.error("--arm is required for an arm invocation")
    budget = Budget(seed=args.seed) if not args.technical_fixture else Budget(
        seed=9401, updates=16, train_per_period=2, eval_per_period=2, checkpoints=(0, 16))
    args.out.mkdir(parents=True, exist_ok=True)
    if args.describe:
        write_read(args.out / "configuration.json", configuration(args.arm, budget))
        print("Configuration only: zero environment, update, evaluation, selection exposure.")
        return
    import numpy
    import torch
    torch.set_num_interop_threads(1)
    launch = {"sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "cwd": str(Path.cwd()), "hostname": platform.node(), "python": sys.executable,
              "argv": sys.argv, "numpy": numpy.__version__, "torch": torch.__version__}

    def publish(value):
        value["launch"] = launch
        value["exposure_class"] = "technical_fixture_not_selected_result" if args.technical_fixture else "selected_B01"
        write_read(args.out / "summary.json", value)

    summary = run(args.arm, budget, publish)
    if os.name == "nt":
        try:
            import psutil
        except ImportError:
            rss = None  # The configured local test interpreter does not include psutil.
        else:
            rss = psutil.Process().memory_info().peak_wset
    else:
        import resource
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
    summary["resources"] = {"status": "measured" if rss is not None else "resources_unmeasured", "peak_rss_bytes": rss,
                            "rss_scope": "main process lifetime high-water",
                            "wall_seconds_through_primary_readback": time.perf_counter() - START,
                            "wall_scope": "imports through primary publication/readback; final resource write/stdout/exit remain inside external whole-invocation timing"}
    publish(summary)
    print(json.dumps({"status": summary["status"], "observed_counts": summary["observed_counts"],
                      "wall_seconds_through_final_readback": time.perf_counter() - START}), flush=True)


if __name__ == "__main__":
    main()
