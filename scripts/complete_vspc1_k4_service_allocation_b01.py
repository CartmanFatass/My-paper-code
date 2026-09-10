"""Outcome-informed, rule-only completion; external admission and 120s complete cap."""
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
    parser.add_argument("--seed", type=int, choices=(402,), default=402)
    parser.add_argument("--factor-summary", type=Path, required=True)
    parser.add_argument("--generic-summary", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="Separate completion output root")
    args = parser.parse_args()
    from experiments.candidates.vsp_c1.k4_service_allocation_b01.experiment import Budget, evaluate_rule
    from experiments.candidates.vsp_c1.k4_service_allocation_b01.reporting import publish_comparison, write_read
    import numpy
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    factor = json.loads(args.factor_summary.read_text(encoding="utf-8"))
    generic = json.loads(args.generic_summary.read_text(encoding="utf-8"))
    args.out.mkdir(parents=True, exist_ok=True)
    launch = {
        "sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "cwd": str(Path.cwd()), "hostname": platform.node(), "python": sys.executable,
        "argv": sys.argv, "numpy": numpy.__version__, "torch": torch.__version__}
    rule = evaluate_rule(Budget(seed=args.seed))
    rule["completion"] = {
        "status": "outcome_informed_completion_after_original_publication_failure",
        "learner_source_sha": "faf786e135b3f55e535c898e17e646dcc341bdec",
        "factor_summary": str(args.factor_summary), "generic_summary": str(args.generic_summary),
        "original_GENERIC_exit_code": 1, "new_learner_updates": 0,
        "dtype": "float32", "device": "cpu", "compute_threads": 1}
    rule["launch"] = launch
    write_read(args.out / "summary.json", rule)
    paired = publish_comparison(args.out / "paired_summary.json", factor, generic, rule)
    paired["completion"] = rule["completion"]
    paired["launch"] = rule["launch"]
    write_read(args.out / "paired_summary.json", paired)
    if os.name == "nt":
        rss = None
    else:
        import resource
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
    rule["resources"] = {
        "status": "measured" if rss is not None else "resources_unmeasured",
        "peak_rss_bytes": rss, "rss_scope": "main process lifetime high-water",
        "wall_seconds_through_primary_readback": time.perf_counter() - START,
        "wall_scope": "imports/input reads/rule/paired publication/readback; external cap includes admission/exit"}
    write_read(args.out / "summary.json", rule)
    print(json.dumps({"status": paired["status"], "observed_counts": rule["observed_counts"],
                      "completion": rule["completion"], "resources": rule["resources"]}), flush=True)


if __name__ == "__main__":
    main()
