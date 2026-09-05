"""Lightweight CLI; probe imports and native loading occur only after run timing starts."""

import argparse
import json
from pathlib import Path
import resource
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def project_cost():
    return {"law": "1.5 * (10 + 5 + 2)", "projected_seconds": 25.5, "cap_seconds": 60.0}


def run(admission, output, seed=50511, levels=(-2.0, 0.25, 2.0)):
    started = time.perf_counter()
    from experiments.candidates.degraded_incumbent_shadow_handover import head_contract_a05
    output.mkdir(parents=True)
    result = head_contract_a05.probe(seed, levels, output)
    result["launch_sha"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    result.update(admission_receipt=str(admission.resolve()),
                  timing_scope="Stdout wall and peak RSS include probe/Torch import, model, graphs, compile, helper, readout and summary publication.")
    (output / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    result["completed_peak_rss_bytes"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024
    result["resources_unmeasured"] = False
    result["completed_runner_wall_seconds"] = time.perf_counter() - started
    if result["completed_runner_wall_seconds"] >= 60:
        raise RuntimeError("incomplete A05: 60-second cap exceeded during publication")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("run", "project-cost"))
    parser.add_argument("--seed", type=int, choices=(50511,), default=50511)
    parser.add_argument("--admission", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    result = project_cost() if args.mode == "project-cost" else run(args.admission, args.out, seed=args.seed)
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
