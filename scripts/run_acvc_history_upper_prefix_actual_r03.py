"""Linux inspection, profile-cost, or single actual R03 bound invocation."""
import argparse
import json
from pathlib import Path
import resource
import socket
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.candidates.acvc.history_upper_prefix_assessment_r03.arithmetic import prefix_bound, structural_counts
from experiments.candidates.acvc.history_upper_prefix_actual_r03.calculation import (
    load_inputs, profile, synthetic_inputs, result_payload, serialize,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("inspect", "profile-cost", "actual"), required=True)
    for name in ("input", "out", "admission", "profile-cost-reference"):
        parser.add_argument("--"+name, type=Path, required=name in ("input", "out", "admission"))
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.smoke and args.mode != "profile-cost":
        parser.error("--smoke is only a synthetic publication check")
    started = time.perf_counter()
    wall_cap, rss_cap = (120, 1.5*1024**3) if args.mode == "actual" else (40, 0.75*1024**3)
    rss = lambda: resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    def check():
        if time.perf_counter()-started >= wall_cap or rss() >= rss_cap:
            raise TimeoutError("calculation cap")
    summary = {"mode": args.mode, "complete": False, "status": "incomplete"}
    try:
        inputs, facts = load_inputs(args.input, check)
        summary["actual_profile" if args.mode == "profile-cost" else "input_facts"] = (
            facts["profile"] if args.mode == "profile-cost" else facts)
        if not facts["source_facts_match"] or not facts["profile"]["within_actual_range"]:
            summary["status"] = "input_diagnostic"
        elif args.mode == "inspect":
            summary.update(status="inspection_complete", complete=True)
        else:
            contexts, prefix = (1, 2) if args.smoke else (12, 4)
            if args.mode == "profile-cost":
                inputs = synthetic_inputs(facts["profile"]["D_star"], contexts, check)
                summary["synthetic_profile"] = profile(inputs)
            bound = prefix_bound(*inputs, prefix=prefix, check=check)
            payload = result_payload(bound, inputs, facts, synthetic=args.mode == "profile-cost",
                                     contexts=contexts, prefix=prefix)
            serialize(payload)  # Same exact fraction/JSON path, synthetic values discarded.
            check()
            if args.mode == "actual":
                summary.update(payload)
            summary.update(status="complete", complete=True,
                           static_counts=structural_counts(2*contexts, contexts, 3, prefix))
        summary["execution"] = {"source_sha": args.source_sha, "argv": sys.argv,
            "node": socket.gethostname(), "cwd": str(Path.cwd()), "input": str(args.input.resolve()),
            "input_source": {"commit": "1d023aaa59097c92e1b72221d893aac21a42ff54",
                "path": "docs/research/candidates/acvc/ACVC_HISTORY_HEADROOM_CERTIFICATE_R02_RESULT_20260904.json",
                "sha256": "6243e867eea3556a67aafebbf2f09640a0efa50d5d231ab0eff2c9ce52737b3b"},
            "admission": {"path": str(args.admission), "record": json.loads(args.admission.read_text())},
            "profile_cost_reference": str(args.profile_cost_reference) if args.profile_cost_reference else None}
        check()
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "summary.json").write_text(serialize(summary), encoding="utf-8")
        check()
        summary["resources"] = {"wall_seconds": time.perf_counter()-started,
                                "peak_rss_bytes": rss(), "status": "measured"}
        (args.out / "summary.json").write_text(serialize(summary), encoding="utf-8")
        check()
    except TimeoutError:
        summary = {"mode": args.mode, "complete": False, "status": "cap_reached",
                   "static_counts": structural_counts(), "resources": {
                       "wall_seconds": time.perf_counter()-started, "peak_rss_bytes": rss(), "status": "measured"}}
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "summary.json").write_text(serialize(summary), encoding="utf-8")
    print(json.dumps({"status": summary["status"], "complete": summary["complete"], **summary["resources"]}))
    return 0 if summary["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
