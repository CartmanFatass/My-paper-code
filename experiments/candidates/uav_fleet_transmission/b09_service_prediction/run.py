#!/usr/bin/env python3
"""Admitted fixed B09 native comparison followed by one complete actual-policy reader."""
import argparse
import os
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    wall, cpu = time.perf_counter(), time.process_time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--phase", required=True, choices=("engineering", "scientific"))
    parser.add_argument("--workers", required=True, type=int, choices=(1, 2, 3, 4))
    parser.add_argument("--reader-workers", required=True, type=int, choices=(1, 2))
    args = parser.parse_args(argv)
    if args.seed != 29890000 or (args.phase == "engineering" and (args.workers != 1 or args.reader_workers != 1)):
        parser.error("B09 has fixed addresses and serial engineering streams")
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_fleet_transmission")
    if admission["sha"] != args.launch_sha:
        raise RuntimeError("source SHA differs from admission")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[name] = "1"
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    from experiments.candidates.uav_fleet_transmission.b09_service_prediction.contract import write_json, telemetry
    from experiments.candidates.uav_fleet_transmission.b09_service_prediction.study import run_batch
    from experiments.candidates.uav_fleet_transmission.b09_service_prediction.reader import read_result
    try:
        batch = run_batch(args.out, args.launch_sha, args.phase, args.workers)
        reading = read_result(args.out, args.reader_workers)
        reading["chain_resources"] = telemetry(wall, cpu)
        reading["chain_resources"]["cpu_scope"] = "parent only; worker and reader CPU sums recorded separately"
        reading["chain_total_cpu_seconds"] = (reading["chain_resources"]["cpu_seconds"]
            + batch["reaped_worker_cpu_seconds"] + reading["reaped_reader_cpu_seconds"])
        reading["chain_resources"]["cpu_scope"] = ("parent plus reaped worker/reader CPU for chain total; "
                                                   "includes spawn/import/serialization overhead; support/admission additional")
        write_json(args.out / "reading.json", reading)
        if batch["status"] != "complete":
            raise RuntimeError("B09 incomplete native panel; preserved and prefix-read without retry")
    except BaseException as error:
        args.out.mkdir(parents=True, exist_ok=True)
        write_json(args.out / "failure.json", dict(error=repr(error), traceback=traceback.format_exc(),
                                                   resources=telemetry(wall, cpu)))
        raise


if __name__ == "__main__":
    main()
