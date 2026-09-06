"""Bounded DISH-INIT-WITNESS-A01 entry; one invocation, two views, zero training."""
import time
STARTED = time.perf_counter()
import resource
CPU_STARTED = sum(getattr(resource.getrusage(who), name) for who in
                  (resource.RUSAGE_SELF, resource.RUSAGE_CHILDREN) for name in ("ru_utime", "ru_stime"))
import argparse
import json
import math
from pathlib import Path
import signal
import subprocess
import traceback


def report_numbers(value):
    """Retain nonfinite failure observations as explicit strings in the published JSON."""
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, dict):
        return {key: report_numbers(item) for key, item in value.items()}
    if isinstance(value, list):
        return [report_numbers(item) for item in value]
    return value


def publish(output, result):
    (output / "summary.json").write_text(json.dumps(report_numbers(result), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("run", "project-cost"))
    parser.add_argument("--shared-preparation-seconds", type=float)
    parser.add_argument("--admission", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--b03-root", type=Path)
    parser.add_argument("--cap-seconds", type=float, default=120.0)
    args = parser.parse_args()
    if args.mode == "project-cost":
        print(json.dumps({"law": "2 views x 4 conditions x <= 1200 ticks",
                          "evaluation_ticks_upper": 9600, "initializer_calls": 1,
                          "optimizer_steps": 0, "ordinary_training_transitions": 0,
                          "whole_item_cap_seconds": 120.0, "projected_wall_seconds": None,
                          "projection_status": "spend choice; no per-episode evaluation wall in B02/B03 records"}))
        return 0
    if args.out is None or args.admission is None or args.shared_preparation_seconds is None:
        parser.error("run requires out, admission and measured shared-preparation-seconds")
    allowance = args.cap_seconds - args.shared_preparation_seconds
    if not 0 < allowance <= args.cap_seconds:
        parser.error("shared preparation leaves no valid allowance")
    result = {"object": "DISH-INIT-WITNESS-A01", "status": "INCOMPLETE",
              "shared_preparation_seconds": args.shared_preparation_seconds,
              "allowance_seconds": allowance, "cap_seconds": args.cap_seconds,
              "admission_receipt": str(args.admission),
              "launch_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()}
    args.out.mkdir(parents=True, exist_ok=True)
    def timeout(signum, frame):
        raise TimeoutError("INIT-WITNESS-A01 whole-item wall allowance reached")
    previous = signal.signal(signal.SIGALRM, timeout)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, STARTED + allowance - time.perf_counter()))
    try:
        from experiments.candidates.degraded_incumbent_shadow_handover.init_witness_a01.study import (
            B03_ROOT, new_progress, run_witness,
        )
        b03_root = args.b03_root if args.b03_root is not None else B03_ROOT
        result.update(new_progress())
        run_witness(args.out, STARTED + allowance, result, b03_root)
    except Exception as error:
        if result.get("status") != "INPUT_GAP":
            result["status"] = "INCOMPLETE"
        result["exception"] = {"type": type(error).__name__, "message": str(error),
                               "traceback": traceback.format_exc(),
                               "classification": "observed exception; no reproduced diagnosis asserted",
                               "count_scope": "completed successfully returned calls; interruption may leave the last native operation uncounted"}
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        own = resource.getrusage(resource.RUSAGE_SELF)
        children = resource.getrusage(resource.RUSAGE_CHILDREN)
        result["prepublication_wall_seconds"] = time.perf_counter() - STARTED
        result["cpu_seconds"] = own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime - CPU_STARTED
        result["peak_self_rss_bytes"] = int(own.ru_maxrss) * 1024
        result["peak_child_rss_bytes"] = int(children.ru_maxrss) * 1024
        result["resources_unmeasured"] = True
        result["resource_scope"] = "Linux self + reaped-child CPU; separate self/child RSS maxima, not summed; scratch unmeasured. Wall starts before runner imports except time."
        result["completion_scope"] = "Final stdout records post-summary wall and governs publication cap; summary resource samples precede its write."
        if result["prepublication_wall_seconds"] >= allowance and result.get("status") != "INPUT_GAP":
            result["status"] = "INCOMPLETE"
        publish(args.out, result)
    result["completed_wall_seconds"] = time.perf_counter() - STARTED
    result["charged_wall_seconds"] = result["completed_wall_seconds"] + args.shared_preparation_seconds
    if result["charged_wall_seconds"] >= args.cap_seconds and result.get("status") != "INPUT_GAP":
        result["status"] = "INCOMPLETE"
        result["publication_cap_exceeded"] = True
        publish(args.out, result)
    print(json.dumps(report_numbers(result), sort_keys=True, allow_nan=False))
    return 0 if result["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
