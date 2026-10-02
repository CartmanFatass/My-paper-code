#!/usr/bin/env python3
"""Admitted B10 phase and one complete reader, under the cumulative CPU purchase."""
import argparse
import json
import os
from pathlib import Path
import resource
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))


def prior_costs(checks_path, engineering_dir, phase):
    from experiments.candidates.uav_fleet_transmission.b10_service_assignment.contract import (
        OBJECT, identity, source_binding, jobs, equal)
    checks=json.loads(checks_path.read_text())
    if checks["object"]!=OBJECT or checks["status"]!="passed" or checks["source_binding"]!=source_binding():
        raise ValueError("finite checks do not bind the current source")
    cpu=float(checks["cpu_seconds"])
    evidence=[dict(kind="all finite/static/mock/failed check attempts",path=str(checks_path),
                   **identity(checks_path),cpu_seconds=cpu)]
    if phase=="scientific":
        if engineering_dir is None:
            raise ValueError("scientific phase requires complete selected engineering evidence")
        config=json.loads((engineering_dir/"config.json").read_text())
        reading=json.loads((engineering_dir/"reading.json").read_text())
        if (config["object"]!=OBJECT or config["phase"]!="engineering" or
                config["jobs"]!=jobs("engineering") or config["source_binding"]!=source_binding() or
                reading["status"]!="VERIFIED" or not reading["exact_native_reference_C"]):
            raise ValueError("engineering is incomplete, mismatched or not exactly C-equivalent")
        bound=lambda entries:[{k:x[k] for k in ("kind","sha256","bytes","cpu_seconds")} for x in entries]
        if bound(config["prior_cost_evidence"])!=bound(evidence):
            raise ValueError("engineering finite-check cost/input binding differs")
        added=float(reading["chain_total_cpu_seconds"])
        evidence.append(dict(kind="complete engineering workers and reader",path=str(engineering_dir/"reading.json"),
                             **identity(engineering_dir/"reading.json"),cpu_seconds=added))
        cpu+=added
    elif engineering_dir is not None:
        raise ValueError("engineering cannot import another engineering attempt")
    if not 0<=cpu<43200 or not all(0<=float(x["cpu_seconds"])<43200 for x in evidence):
        raise ValueError("invalid or already exhausted prior CPU")
    return cpu,evidence


def main(argv=None):
    wall=time.perf_counter()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--launch-sha",required=True)
    parser.add_argument("--seed",required=True,type=int)
    parser.add_argument("--phase",required=True,choices=("engineering","scientific"))
    parser.add_argument("--workers",required=True,type=int,choices=(1,2,3,4))
    parser.add_argument("--reader-workers",required=True,type=int,choices=(1,2))
    parser.add_argument("--checks",required=True,type=Path)
    parser.add_argument("--engineering-dir",type=Path)
    args=parser.parse_args(argv)
    if args.seed!=29910000 or (args.phase=="engineering" and (args.workers!=1 or args.reader_workers!=1)):
        parser.error("fixed B10 addresses; serial full engineering missions")
    from scripts.hmasd_admission import require_admission
    admission=require_admission(__file__,direction="uav_fleet_transmission")
    if admission["sha"]!=args.launch_sha:
        raise RuntimeError("source SHA differs from admission")
    for name in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
        os.environ[name]="1"
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    from experiments.candidates.uav_fleet_transmission.b10_service_assignment.contract import write_json,telemetry
    from experiments.candidates.uav_fleet_transmission.b10_service_assignment.budget import CpuBudget,children_cpu
    from experiments.candidates.uav_fleet_transmission.b10_service_assignment.study import run_batch
    from experiments.candidates.uav_fleet_transmission.b10_service_assignment.reader import read_result
    prior,evidence=prior_costs(args.checks,args.engineering_dir,args.phase)
    budget=CpuBudget(args.out,prior,cpu_origin=0.,child_origin=children_cpu())
    budget.prior_evidence=evidence
    try:
        batch=run_batch(args.out,args.launch_sha,args.phase,args.workers,budget)
        if budget.poll():
            reading=read_result(args.out,args.reader_workers,budget)
        else:
            reading=dict(status="INCOMPLETE_BUDGET",phase=args.phase,performance_result=False,
                         reason="CPU review boundary before complete reader; native artifacts retained")
        budget.poll()
        reading["chain_resources"]=telemetry(wall,0.)
        reading["chain_resources"]["cpu_scope"]="full parent process plus Linux reaped/live descendant CPU at final checkpoint"
        reading["chain_total_cpu_seconds"]=budget.last["checkpoint_cpu_seconds"]-prior
        reading["cumulative_cpu_checkpoint"]=budget.last
        reading["budget_stopped"]=budget.stopped
        write_json(args.out/"reading.json",reading)
        if batch["status"]!="complete" or reading["status"]!="VERIFIED":
            raise RuntimeError("B10 incomplete panel/reader retained; no completed performance conclusion or automatic retry")
    except BaseException as error:
        args.out.mkdir(parents=True,exist_ok=True)
        budget.poll()
        write_json(args.out/"failure.json",dict(error=repr(error),traceback=traceback.format_exc(),
            resources=telemetry(wall,0.),cumulative_cpu_checkpoint=budget.last))
        raise


if __name__=="__main__":
    main()
