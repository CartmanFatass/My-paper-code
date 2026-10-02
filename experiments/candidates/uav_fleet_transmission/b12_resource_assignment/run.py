#!/usr/bin/env python3
"""Admit one frozen B12 phase and exactly one full reader; preserve any failure."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def prior_costs(checks_path, engineering_dir, phase):
    from experiments.candidates.uav_fleet_transmission.b12_resource_assignment.contract import (
        OBJECT, identity, source_binding, jobs, CPU_REVIEW_SECONDS)
    checks = json.loads(checks_path.read_text())
    if checks["object"] != OBJECT or checks["status"] != "passed" or checks["source_binding"] != source_binding():
        raise ValueError("finite checks do not bind exact current source")
    cpu = float(checks["cpu_seconds"])
    evidence = [dict(kind="all finite/static/mock/failed checks", path=str(checks_path),
                     **identity(checks_path), cpu_seconds=cpu)]
    if phase == "scientific":
        if engineering_dir is None:
            raise ValueError("scientific phase requires selected full engineering reading")
        config = json.loads((engineering_dir / "config.json").read_text())
        reading = json.loads((engineering_dir / "reading.json").read_text())
        if (config["object"] != OBJECT or config["phase"] != "engineering" or
            config["jobs"] != jobs("engineering") or config["source_binding"] != source_binding() or
            reading["status"] != "VERIFIED" or not reading["frozen_reference_verified"]):
            raise ValueError("engineering incomplete or input/reference binding differs")
        bound = lambda entries: [{k: e[k] for k in ("kind", "sha256", "bytes", "cpu_seconds")} for e in entries]
        if bound(config["prior_cost_evidence"]) != bound(evidence):
            raise ValueError("engineering check costs differ")
        added = float(reading["chain_total_cpu_seconds"])
        evidence.append(dict(kind="complete engineering workers and reader", path=str(engineering_dir / "reading.json"),
            **identity(engineering_dir / "reading.json"), cpu_seconds=added))
        cpu += added
    elif engineering_dir is not None:
        raise ValueError("engineering cannot import another attempt")
    if not 0 <= cpu < CPU_REVIEW_SECONDS:
        raise ValueError("invalid or exhausted cumulative CPU")
    return cpu, evidence


def main(argv=None):
    wall = time.perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--phase", required=True, choices=("engineering", "scientific"))
    parser.add_argument("--workers", required=True, type=int, choices=(1, 2, 3, 4))
    parser.add_argument("--reader-workers", required=True, type=int, choices=(1, 2))
    parser.add_argument("--checks", required=True, type=Path)
    parser.add_argument("--engineering-dir", type=Path)
    args = parser.parse_args(argv)
    if args.seed != 29910000 or (args.phase == "engineering" and (args.workers != 1 or args.reader_workers != 1)):
        parser.error("fixed B12 seeds; full engineering runs serially")
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_fleet_transmission")
    if admission["sha"] != args.launch_sha:
        raise RuntimeError("admitted SHA differs")
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[key] = "1"
    from experiments.candidates.uav_fleet_transmission.b12_resource_assignment.contract import (
        write_json, telemetry, reference_evidence, reference_root_for_output, CPU_REVIEW_SECONDS)
    from experiments.candidates.uav_fleet_transmission.b10_service_assignment.budget import CpuBudget, children_cpu
    budget = None
    dispatched = False
    try:
        import torch
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        from experiments.candidates.uav_fleet_transmission.b12_resource_assignment.study import run_batch
        from experiments.candidates.uav_fleet_transmission.b12_resource_assignment.reader import read_result
        prior, evidence = prior_costs(args.checks, args.engineering_dir, args.phase)
        budget = CpuBudget(args.out, prior, cpu_origin=0., child_origin=children_cpu(), limit=CPU_REVIEW_SECONDS)
        budget.prior_evidence = evidence
        reference = reference_evidence(reference_root_for_output(args.out), args.phase)
        if not budget.poll():
            raise RuntimeError("CPU review boundary during frozen reference validation")
        dispatched = True
        batch = run_batch(args.out, args.launch_sha, args.phase, args.workers, budget, reference)
        if budget.poll():
            reading = read_result(args.out, args.reader_workers, budget)
        else:
            reading = dict(status="INCOMPLETE_BUDGET", phase=args.phase, performance_result=False,
                reason="CPU review boundary before complete reader; actual prefix retained")
        budget.poll()
        reading["chain_resources"] = telemetry(wall, 0.)
        reading["chain_resources"]["cpu_scope"] = "parent plus actual live/reaped descendant accounting"
        reading["chain_total_cpu_seconds"] = budget.last["checkpoint_cpu_seconds"] - prior
        reading["cumulative_cpu_checkpoint"] = budget.last
        reading["budget_stopped"] = budget.stopped
        write_json(args.out / "reading.json", reading)
        if batch["status"] != "complete" or reading["status"] != "VERIFIED":
            raise RuntimeError("B12 incomplete; preserve evidence without automatic retry or completed claim")
    except BaseException as error:
        args.out.mkdir(parents=True, exist_ok=True)
        if budget is not None:
            budget.poll()
        write_json(args.out / "failure.json", dict(error=repr(error), traceback=traceback.format_exc(),
            resources=telemetry(wall, 0.), cumulative_cpu_checkpoint=None if budget is None else budget.last,
            dispatched=dispatched, known_no_native_dispatch=not dispatched))
        raise


if __name__ == "__main__":
    main()
