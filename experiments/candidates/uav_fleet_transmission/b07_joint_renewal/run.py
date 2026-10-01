#!/usr/bin/env python3
"""Admitted B07 native worker followed by its complete independent reader."""
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
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", required=True, type=int)
    args = parser.parse_args(argv)
    if args.seed != 29750100:
        parser.error("B07 fixes all worlds and addresses in contract.py")
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_fleet_transmission")
    if admission["sha"] != args.launch_sha:
        raise RuntimeError("source SHA differs from admission")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[name] = "1"
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    from experiments.candidates.uav_fleet_transmission.b07_joint_renewal.study import run_batch
    from experiments.candidates.uav_fleet_transmission.b07_joint_renewal.read import read_result
    from experiments.candidates.uav_fleet_transmission.b07_joint_renewal.contract import write_json
    try:
        batch = run_batch(args.out, args.launch_sha, admission=admission, entry_wall=start_wall, entry_cpu=start_cpu)
        reading = read_result(args.out, ROOT)
        reading.update(chain_wall_seconds=time.perf_counter() - start_wall,
                       chain_cpu_seconds=time.process_time() - start_cpu,
                       chain_timing_scope="runner entry through complete worker/reader, imports and serialization; "
                                          "final self-report write excluded; engineering/admission additional")
        write_json(args.out / "reading.json", reading)
        return batch
    except BaseException as error:
        args.out.mkdir(parents=True, exist_ok=True)
        write_json(args.out / "failure.json", dict(error=repr(error), traceback=traceback.format_exc(),
                   chain_wall_seconds=time.perf_counter() - start_wall, chain_cpu_seconds=time.process_time() - start_cpu))
        raise


if __name__ == "__main__":
    main()
