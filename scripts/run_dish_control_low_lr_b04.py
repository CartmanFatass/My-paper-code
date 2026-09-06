"""Bounded B04 arm; LOW_LR also publishes the paired primary output."""
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
    (output / "summary.json").write_text(
        json.dumps(report_numbers(result), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf8")
    if "paired_primary" in result:
        (output / "paired.json").write_text(
            json.dumps(report_numbers(result["paired_primary"]), indent=2, sort_keys=True,
                       allow_nan=False) + "\n",
            encoding="utf8")


def _resources(result, started):
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    result["prepublication_wall_seconds"] = time.perf_counter() - started
    result["cpu_seconds"] = own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime - CPU_STARTED
    result["peak_self_rss_bytes"] = int(own.ru_maxrss) * 1024
    result["peak_child_rss_bytes"] = int(children.ru_maxrss) * 1024
    result["resources_unmeasured"] = True
    result["resource_scope"] = (
        "Linux self + reaped-child CPU; separate self/child RSS maxima, not summed; "
        "scratch unmeasured. Wall starts before runner imports except time."
    )
    result["completion_scope"] = (
        "Final stdout records post-summary wall and governs publication cap; "
        "summary resource samples precede its write."
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("shared", "run", "project-cost"))
    parser.add_argument("--arm", choices=("CONTROL", "LOW_LR"))
    parser.add_argument("--seed", type=int, choices=(89,), default=89)
    parser.add_argument("--shared", type=Path)
    parser.add_argument("--shared-preparation-seconds", type=float)
    parser.add_argument("--admission", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--control-summary", type=Path)
    args = parser.parse_args()
    if args.mode == "project-cost":
        print(json.dumps({"law": "N + L + 2E + H; H <= 20E", "N": 65536, "L": 65536,
                          "native_training_calls_upper": 1572864, "evaluation_ticks_upper": 4800,
                          "optimizer_steps": 512, "projected_wall_seconds": None,
                          "projection_status": "unmeasured; no extra pilot selected",
                          "arm_cap_seconds": 1800, "shared_charge_per_arm": "measured preparation / 2"}))
        return 0
    if args.out is None or args.admission is None:
        parser.error("shared and run require out and admission")
    args.out.mkdir(parents=True, exist_ok=True)
    result = {"object": "DISH-CONTROL-LOW-LR-B04", "status": "INCOMPLETE",
              "admission_receipt": str(args.admission),
              "launch_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()}
    if args.mode == "shared":
        try:
            from experiments.candidates.degraded_incumbent_shadow_handover.control_low_lr_b04.study import (
                new_progress, prepare_shared, planned_cost,
            )
            result.update(new_progress())
            prepare_shared(args.out, float("inf"), result)
            result["planned_cost"] = planned_cost()
        except Exception as error:
            result["status"] = "INCOMPLETE"
            result["exception"] = {"type": type(error).__name__, "message": str(error),
                                   "traceback": traceback.format_exc(),
                                   "classification": "observed exception; no reproduced diagnosis asserted",
                                   "count_scope": "completed successfully returned calls; interruption may leave the last native/optimizer operation uncounted"}
        _resources(result, STARTED)
        publish(args.out, result)
        result["completed_wall_seconds"] = time.perf_counter() - STARTED
        print(json.dumps(report_numbers(result), sort_keys=True, allow_nan=False))
        return 0 if result["status"] == "COMPLETE" else 1
    if args.arm is None or args.shared is None or args.shared_preparation_seconds is None:
        parser.error("run requires arm, out, admission, shared and measured shared-preparation-seconds")
    if args.arm == "LOW_LR" and args.control_summary is None:
        parser.error("LOW_LR run requires the completed CONTROL summary path for paired publication")
    allowance = 1800 - args.shared_preparation_seconds / 2
    if not 0 < allowance <= 1800:
        parser.error("shared preparation leaves no valid arm allowance")
    result.update(arm=args.arm, shared_preparation_seconds=args.shared_preparation_seconds,
                  shared_preparation_charge_seconds=args.shared_preparation_seconds / 2,
                  remaining_arm_allowance_seconds=allowance)

    def timeout(signum, frame):
        raise TimeoutError("B04 whole-arm wall allowance reached")

    previous = signal.signal(signal.SIGALRM, timeout)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, STARTED + allowance - time.perf_counter()))
    try:
        from experiments.candidates.degraded_incumbent_shadow_handover.control_low_lr_b04.study import (
            new_progress, run_arm, paired_result, exposure, planned_cost,
        )
        result.update(new_progress())
        run_arm(args.arm, args.out, STARTED + allowance, result, args.shared)
        if args.arm == "LOW_LR":
            control = json.loads(args.control_summary.read_text(encoding="utf8"))
            shared_summary = json.loads((args.shared / "summary.json").read_text(encoding="utf8"))
            result["paired_primary"] = paired_result(control, result, shared_summary)
        result["planned_cost"] = planned_cost()
    except Exception as error:
        result["status"] = "INCOMPLETE"
        result["exception"] = {"type": type(error).__name__, "message": str(error),
                               "traceback": traceback.format_exc(),
                               "classification": "observed exception; no reproduced diagnosis asserted",
                               "count_scope": "completed successfully returned calls; interruption may leave the last native/optimizer operation uncounted"}
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        if "ordinary_training_transitions" in result:
            result["actual_exposure"] = exposure(result)
        _resources(result, STARTED)
        if result["prepublication_wall_seconds"] >= allowance:
            result["status"] = "INCOMPLETE"
            if "paired_primary" in result:
                result["paired_primary"]["status"] = "INCOMPLETE_PAIR"
        publish(args.out, result)
    result["completed_wall_seconds"] = time.perf_counter() - STARTED
    result["charged_wall_seconds"] = result["completed_wall_seconds"] + args.shared_preparation_seconds / 2
    if result["charged_wall_seconds"] >= 1800:
        result["status"] = "INCOMPLETE"
        result["publication_cap_exceeded"] = True
        if "paired_primary" in result:
            result["paired_primary"]["status"] = "INCOMPLETE_PAIR"
        publish(args.out, result)
    print(json.dumps(report_numbers(result), sort_keys=True, allow_nan=False))
    return 0 if result["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
