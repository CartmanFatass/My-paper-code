"""One complete B06 invocation; earlier required check wall is charged to the same cap."""
import time
STARTED = time.perf_counter()
import argparse
import json
import math
from pathlib import Path
import signal
import subprocess
import traceback


def report_numbers(value):
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, dict):
        return {key: report_numbers(item) for key, item in value.items()}
    if isinstance(value, list):
        return [report_numbers(item) for item in value]
    return value


def publish(output, result):
    (output / "summary.json").write_text(
        json.dumps(report_numbers(result), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf8")
    if "primary" in result:
        (output / "paired.json").write_text(
            json.dumps(report_numbers(result["primary"]), indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, choices=(113,), default=113)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--prior-check-seconds", type=float, required=True)
    args = parser.parse_args()
    allowance = 1800 - args.prior_check_seconds
    if not 0 < allowance <= 1800:
        parser.error("Prior check wall must leave a positive allowance within the single1800s cap")
    args.out.mkdir(parents=True)
    result = {"object": "DISH-SAMPLED-EXECUTION-B06", "seed": args.seed, "status": "INCOMPLETE",
              "launch_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "admission_receipt": str(args.admission), "prior_check_seconds": args.prior_check_seconds,
              "remaining_allowance_seconds": allowance}

    def timeout(signum, frame):
        raise TimeoutError("B06 complete invocation wall allowance reached")

    previous = signal.signal(signal.SIGALRM, timeout)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, STARTED + allowance - time.perf_counter()))
    try:
        from experiments.candidates.degraded_incumbent_shadow_handover.sampled_execution_b06 import study
        result["planned_cost"] = study.planned_cost()
        try:
            study.run_study(args.out, STARTED + allowance, result)
        finally:
            result["actual_exposure"] = study.actual_exposure(result)
    except Exception as error:
        result["status"] = "INCOMPLETE"
        result["exception"] = {"type": type(error).__name__, "message": str(error),
                               "traceback": traceback.format_exc(),
                               "classification": "observed exception; no unverified root cause asserted",
                               "count_scope": "successfully returned calls; interruption can leave the last operation uncounted"}
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    import resource
    result["peak_self_rss_bytes"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024
    result["peak_child_rss_bytes"] = int(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss) * 1024
    result["resources_unmeasured"] = True
    result["resource_scope"] = "Linux separate self/reaped-child RSS maxima, not summed; scratch unmeasured"
    result["prepublication_wall_seconds"] = time.perf_counter() - STARTED
    publish(args.out, result)
    result["completed_wall_seconds"] = time.perf_counter() - STARTED
    result["charged_wall_seconds"] = args.prior_check_seconds + result["completed_wall_seconds"]
    if result["charged_wall_seconds"] >= 1800:
        result["status"] = "INCOMPLETE"
        result["publication_cap_exceeded"] = True
        if "primary" in result:
            result["primary"]["status"] = "INCOMPLETE"
        publish(args.out, result)
    print(json.dumps(report_numbers(result), sort_keys=True, allow_nan=False))
    return 0 if result["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
