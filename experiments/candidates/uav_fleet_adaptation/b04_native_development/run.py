#!/usr/bin/env python3
"""Admitted fixed two-lineage inherited native development and calibration."""
import argparse
import os
from pathlib import Path
import sys
import time

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
    if args.seed != 29354000:
        parser.error("B04 fixes both assets, every panel and all randomness domains in contract.py")
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_fleet_adaptation")
    if admission["sha"] != args.launch_sha:
        raise RuntimeError("launch SHA does not match admission")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
                 "VECLIB_MAXIMUM_THREADS"):
        os.environ[name] = "1"
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    from experiments.candidates.uav_fleet_adaptation.b04_native_development.study import run_batch
    batch = run_batch(args.out, args.launch_sha, admission=admission, scientific_invocation=True,
                      entry_start=start_wall, entry_cpu=start_cpu)
    # One accepted chain and one priced reader, after all native work completes.
    from experiments.candidates.uav_fleet_adaptation.b04_native_development.read import read_result
    reading = read_result(args.out, ROOT)
    if reading["status"] != "VERIFIED":
        raise RuntimeError("saved-evidence reading did not complete")
    reading.update(chain_wall_seconds=time.perf_counter() - start_wall,
                   chain_cpu_seconds=time.process_time() - start_cpu,
                   chain_timing_scope="runner entry through complete worker and reader, including import and prior "
                                      "serialization gaps; final self-report write excluded; engineering/admission additional")
    from experiments.candidates.uav_local_history.b01.study import write_json
    write_json(args.out / "reading.json", reading)
    return batch


if __name__ == "__main__":
    if main()["state"] != "COMPLETE":
        raise SystemExit(1)
