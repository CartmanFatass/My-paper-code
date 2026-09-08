"""Fixed seed127 pair; prior checking and publication share the original caps."""
import time
STARTED = time.perf_counter()
import argparse
import json
import math
from pathlib import Path
import platform
import signal
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


def publication_deadline(study, result, started, prior_shared_seconds, now):
    """All remaining work is shared; preserve two seconds for process closure."""
    remaining = 3600 - prior_shared_seconds - (now - started)
    if study is not None:
        cost = study.allocate_cost(result, started, prior_shared_seconds, now=now)
        remaining = min(remaining, *(2 * value for value in cost["remaining_arm_seconds"].values()))
    return now + remaining - 2.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, choices=(127,), default=127)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--prior-shared-seconds", type=float, required=True)
    args = parser.parse_args()
    if not 0 <= args.prior_shared_seconds < 3600:
        parser.error("Prior shared check wall must leave allowance within the pair cap")
    args.output.mkdir(parents=True)
    result = {"object": "DISH-OWN-COMMAND-MEAN-B07", "seed": args.seed,
              "launch_sha": args.launch_sha, "status": "INCOMPLETE", "arms": {},
              "node": platform.node(), "device": "cpu", "native_dtype": "float64",
              "policy_dtype": "float32", "torch_blas_threads": 1,
              "resources_unmeasured": True,
              "count_scope": "successfully returned calls; interrupted last operations can be uncounted"}

    def timeout(signum, frame):
        raise TimeoutError("B07 complete arm/pair wall allowance reached")

    def set_deadline(deadline):
        signal.setitimer(signal.ITIMER_REAL, max(0.001, deadline - time.perf_counter()))

    signal.signal(signal.SIGALRM, timeout)
    set_deadline(STARTED + 3600 - args.prior_shared_seconds - 10.0)
    study = None
    try:
        from experiments.candidates.degraded_incumbent_shadow_handover.own_command_mean_b07 import study
        result["planned_cost"] = study.planned_cost()
        study.run_study(args.output, STARTED, args.prior_shared_seconds, result, set_deadline=set_deadline)
    except Exception as error:
        result["status"] = "INCOMPLETE"
        result["exception"] = {"type": type(error).__name__, "message": str(error),
                               "traceback": traceback.format_exc()}
    finally:
        # Default disposition terminates even if final I/O is stuck in native code.
        # Leave this alarm armed through stdout flush and interpreter shutdown.
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
        set_deadline(publication_deadline(study, result, STARTED,
                                          args.prior_shared_seconds, time.perf_counter()))
    if study is not None:
        result["primary"] = study.reduce_pair(result["arms"])
        result["actual_exposure"] = study.exposure(result["arms"])
    try:
        import resource
        result["peak_self_rss_bytes"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024
        result["peak_child_rss_bytes"] = int(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss) * 1024
        result["resource_scope"] = "Linux separate self/reaped-child RSS maxima; H and scratch unmeasured"
    except ImportError:
        result["resource_scope"] = "RSS unavailable; H and scratch unmeasured"
    if study is not None:
        study.allocate_cost(result, STARTED, args.prior_shared_seconds)
    result["accounting_boundary"] = "summary measured before final write; terminal cost follows substantive publication; external whole-chain readback includes closure"
    publish(args.output, result)
    if study is not None:
        study.allocate_cost(result, STARTED, args.prior_shared_seconds)
        if result.get("budget_exhausted"):
            publish(args.output, result)
    print(json.dumps({"status": result["status"], "primary": result.get("primary"),
                      "cost": result.get("cost")}, sort_keys=True))
    return 0 if result["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
