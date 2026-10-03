"""One admitted B01 purchase: fixed audits, fits, calibration, finals and reader."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import json
import multiprocessing
import os
from pathlib import Path
import resource
import sys
import time
import traceback

SOURCE_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(SOURCE_ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--preparation", type=Path, required=True)
    args = parser.parse_args(argv)
    wall_origin, cpu_origin = time.monotonic(), time.process_time()
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    child_origin = usage.ru_utime + usage.ru_stime
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_service_resource_control")
    if admission["sha"] != args.launch_sha:
        raise ValueError("CLI source differs from admission")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
                 "VECLIB_MAXIMUM_THREADS", "BLIS_NUM_THREADS"):
        os.environ[name] = "1"

    from experiments.candidates.uav_service_resource_control.b01_native_selector.contract import (
        ROOT, OBJECT, DIRECTION, HORIZON, CPU_LIMIT, WALL_LIMIT, BYTE_LIMIT, FIT_SEEDS,
        audit_jobs, calibration_jobs, final_jobs, select_ordinary, source_binding,
        clean, identity, sum_counts, write_json,
    )
    from experiments.candidates.uav_service_resource_control.b01_native_selector.budget import (
        PurchaseBudget, execute, request_stop, check_stop, children_cpu,
    )
    from experiments.candidates.uav_service_resource_control.b01_native_selector.study import (
        initialize_worker, mission_worker, fit_worker,
    )
    from experiments.candidates.uav_service_resource_control.b01_native_selector.reading import (
        reader_worker, fit_reader_worker, check_audit_pairs, check_exogenous,
    )
    from experiments.candidates.uav_service_resource_control.b01_native_selector.results import summarize_finals
    from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
    from experiments.candidates.energy_relay_benchmark.b01.evaluation import TRACE_TIMING

    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    for name in ("config.json", "raw", "summary.json", "purchase-stop.json"):
        if (out/name).exists():
            raise FileExistsError(out/name)
    (out/"raw").mkdir()
    preparation = args.preparation.resolve()
    prep = json.loads(preparation.read_text())
    if prep["status"] != "accepted" or prep["native_steps"] != 0 or prep["real_rf_samples"] != 0:
        raise ValueError("preparation receipt is incomplete or spent undeclared native effects")
    budget = PurchaseBudget(out, prep["cpu_seconds"], cpu_origin=cpu_origin,
        child_origin=child_origin, wall_origin=wall_origin,
        storage_paths=(ROOT, out, Path("/home/fires/hmasd-wsl/temp/directions")/DIRECTION,
                       preparation.parent))
    config = dict(object=OBJECT, direction=DIRECTION, launch_sha=args.launch_sha,
        source_binding=source_binding(), admission=admission, horizon=HORIZON,
        workers=3, readers=2, numeric_threads=1, worker_reader_overlap=False,
        fit_seeds=FIT_SEEDS, planned_fits=3, planned_max_missions=678,
        planned_max_native_steps=2034000, planned_max_training_updates=33600,
        planned_max_verification_optimizer_executions=33600,
        cpu_limit=CPU_LIMIT, wall_limit=WALL_LIMIT, allocated_byte_limit=BYTE_LIMIT,
        preparation=dict(path=str(preparation), **identity(preparation), receipt=prep),
        shield=asdict(PRODUCTION_PARAMS), trace_timing=TRACE_TIMING,
        final_selection="all3 fixed128 mission endpoint bytes and T* sealed before any fresh world",
        native_reader_limit="independent endpoint arithmetic, not independent native RF; every purchased private H query and training update replayed once",
        first_failure="closes this purchase without automatic retry or missing-cell completion")
    write_json(out/"config.json", config)
    phases, episodes, fits, reads = {}, [], [], []
    selection = seal = None
    summary = dict(object=OBJECT, launch_sha=args.launch_sha, status="running")

    def run_phase(name, jobs, concurrency, worker, payload):
        check_stop(out)
        phase_wall, phase_cpu, phase_children = time.monotonic(), time.process_time(), children_cpu()
        rows = []
        phase = dict(status="running", planned=len(jobs), submitted=[], rows=rows)
        phases[name] = phase
        phase_path = out/(name+".json")
        order = {spec["job_key"]: i for i, spec in enumerate(jobs)}

        def received(row):
            rows.append(row)
            rows.sort(key=lambda r: order[r["job_key"]])
            write_json(phase_path, clean(phase))
            write_json(out/"progress.json", dict(phase=name, returned=len(rows), planned=len(jobs),
                                                 budget=budget.last))

        write_json(phase_path, clean(phase))
        pool = None
        try:
            pool = ProcessPoolExecutor(max_workers=concurrency, mp_context=multiprocessing.get_context("spawn"),
                                       initializer=initialize_worker)
            phase["submitted"] = execute(pool, jobs, concurrency, worker, payload, received, budget)
        except BaseException as phase_error:
            budget.stopped = True
            phase["control_error"] = repr(phase_error)
            try:
                request_stop(out, "phase control/collection failed", phase=name, error=repr(phase_error))
            except OSError as receipt_error:
                phase["stop_receipt_error"] = repr(receipt_error)
            if pool is not None:
                # This drains the same captured handles, with no submissions and
                # no scientific callback. It also works when budget/output polling
                # caused the exception; no accepted operation is repeated.
                class Stopped:
                    def __init__(self, target):
                        self.out = target
                    def poll(self):
                        return False
                execute(pool, [], 0, None, None, lambda row: None, Stopped(out))
            raise
        finally:
            if pool is not None:
                nonblocking = getattr(pool, "_b01_nonblocking_shutdown", False)
                if not getattr(pool, "_b01_shutdown_started", False):
                    pool.shutdown(wait=not nonblocking, cancel_futures=True)
                phase["unreconciled_pool_shutdown"] = nonblocking
            phase["status"] = "completed" if len(rows) == len(jobs) and all(
                row["status"] == "completed" for row in rows) else "incomplete"
            phase.update(parent_cpu_seconds=time.process_time()-phase_cpu,
                         reaped_descendant_cpu_seconds=children_cpu()-phase_children,
                         aggregate_cpu_seconds=time.process_time()-phase_cpu+children_cpu()-phase_children,
                         elapsed_wall_seconds=time.monotonic()-phase_wall,
                         cost_scope="parent plus fully reaped phase children including imports/setup/serialization; do not add mission CPU again")
            write_json(phase_path, clean(phase))
        if phase["status"] != "completed":
            raise RuntimeError("phase failed/incomplete: " + name)
        return rows

    try:
        audits = run_phase("audits", audit_jobs(), 1, mission_worker, lambda spec: (spec, str(out), None))
        episodes.extend(audits)
        summary["audit_equivalence"] = check_audit_pairs(out, audits)
        fits = run_phase("training", [dict(job_key=f"fit/{i}", fit=i) for i in range(3)], 3,
                         fit_worker, lambda spec: (spec, str(out)))
        for fit in fits:
            episodes.extend(fit["episodes"])
        calibration = run_phase("calibration", calibration_jobs(), 3, mission_worker,
                                lambda spec: (spec, str(out), None))
        episodes.extend(calibration)
        selection = select_ordinary(calibration)
        write_json(out/"selection.json", selection)
        checkpoints = {fit["fit"]: fit["checkpoints"][-1] for fit in fits}
        seal = dict(selection=selection, checkpoints=checkpoints, launch_sha=args.launch_sha,
                    source_binding=config["source_binding"], final_jobs=final_jobs(selection["selected"]))
        for receipt in checkpoints.values():
            actual = identity(out/receipt["path"])
            if any(actual[k] != receipt[k] for k in ("bytes", "sha256")):
                raise AssertionError("final checkpoint changed before seal")
        write_json(out/"final-seal.json", seal)
        seal_identity = identity(out/"final-seal.json")
        finals = run_phase("finals", seal["final_jobs"], 3, mission_worker,
            lambda spec: (spec, str(out), checkpoints[spec["fit"]] if "fit" in spec else None))
        episodes.extend(finals)
        if identity(out/"final-seal.json") != seal_identity:
            raise AssertionError("sealed endpoints changed during fresh evaluation")
        summary["exogenous_identity"] = check_exogenous(out, episodes)
        # Worker pools are fully reaped before any full private-query replay.
        fit_reads = run_phase("training_read", [dict(job_key=f"fit_read/{i}", fit=i) for i in range(3)], 2,
            fit_reader_worker, lambda spec: (spec, str(out), fits[spec["fit"]]))
        for read in fit_reads:
            reads.extend(read["episodes"])
        nontraining = audits+calibration+finals
        by_key = {r["job_key"]: r for r in nontraining}
        read_specs = [dict(job_key=r["job_key"]) for r in nontraining]
        reads.extend(run_phase("evaluation_read", read_specs, 2, reader_worker,
            lambda spec: (spec, str(out), by_key[spec["job_key"]],
                checkpoints[by_key[spec["job_key"]]["fit"]] if "fit" in by_key[spec["job_key"]] else None)))
        check_stop(out)
        summary.update(status="complete_read", findings=summarize_finals(finals, selection),
                       selection=selection, seal=dict(path="final-seal.json", **seal_identity),
                       read_episodes=len(reads), verification_optimizer_executions=sum(r["optimizer_executions"] for r in reads),
                       verification_replay_presentations=sum(r["replay_presentations"] for r in reads),
                       reader_policy_counts=sum_counts(r["policy_counts"] for r in reads))
    except BaseException as error:
        request_stop(out, "purchase failed or protective stop", error=repr(error))
        summary.update(status="incomplete", error=repr(error), traceback=traceback.format_exc(),
                       no_automatic_retry=True)
    finally:
        # Retain every returned completed/failed mission even when a phase raised
        # before its normal episodes.extend call. Fit ledgers also preserve prefixes.
        all_episodes = {}
        for name in ("audits", "calibration", "finals"):
            for row in phases.get(name, {}).get("rows", []):
                all_episodes[row["job_key"]] = row
        for fit in phases.get("training", {}).get("rows", []):
            for row in fit.get("episodes", []):
                all_episodes[row["job_key"]] = row
        known = list(all_episodes.values())
        completed = [r for r in known if r["status"] == "completed"]
        counts = sum_counts(r["policy_counts"] for r in completed)
        if not budget.poll() and summary["status"] == "complete_read":
            summary["status"] = "complete_read_protective_stop"
        summary.update(phases={name: {k: v for k, v in p.items() if k != "rows"} |
                           dict(reported=len(p["rows"])) for name, p in phases.items()},
            completed_episodes=len(completed), known_mission_rows=len(known),
            known_native_steps=sum(r.get("actual_length", r.get("observed_native_steps", 0)) for r in known),
            completed_policy_counts=counts,
            training_updates=sum(r.get("learner_episode_counts", {}).get("updates", 0) for r in completed if r["phase"] == "train"),
            training_replay_presentations=64*sum(r.get("learner_episode_counts", {}).get("updates", 0) for r in completed if r["phase"] == "train"),
            parent_cpu_seconds=time.process_time()-cpu_origin,
            reaped_descendant_cpu_seconds=children_cpu()-child_origin,
            cumulative_cpu_seconds=prep["cpu_seconds"]+time.process_time()-cpu_origin+children_cpu()-child_origin,
            operation_wall_seconds=time.monotonic()-wall_origin, budget=budget.last,
            partial_counts_scope="completed counts plus preserved failed prefixes; unreturned worker effects may remain unknown",
            resources_unmeasured=any(p.get("unreconciled_pool_shutdown", False) for p in phases.values()),
            support_hours_unmetered="unknown")
        write_json(out/"episodes.json", clean(known))
        write_json(out/"summary.json", clean(summary))
    if any(p.get("unreconciled_pool_shutdown", False) for p in phases.values()):
        # All exact owned targets already received SIGKILL. A surviving kernel
        # wait or broken pool-manager join is an explicit blocker in the saved
        # receipt, not permission to leave the purchase silently running/retry it.
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(3)
    return 0 if summary["status"] == "complete_read" else 2


if __name__ == "__main__":
    raise SystemExit(main())
