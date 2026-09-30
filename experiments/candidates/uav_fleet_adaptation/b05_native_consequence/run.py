#!/usr/bin/env python3
"""One admitted fixed B05 worker and its priced same-process saved-evidence reader."""
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
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args(argv)
    if args.seed != 29484000:
        parser.error("B05 fixes both inherited assets, every panel and all randomness domains")
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_fleet_adaptation")
    if admission["sha"] != args.launch_sha:
        raise RuntimeError("launch SHA differs from admission")
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[key] = "1"
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    from experiments.candidates.uav_fleet_adaptation.b05_native_consequence.study import run_batch
    batch = run_batch(args.out, args.launch_sha, admission=admission, scientific_invocation=True,
                      entry_start=start_wall, entry_cpu=start_cpu)
    from experiments.candidates.uav_fleet_adaptation.b05_native_consequence.read import read_result
    reading = read_result(args.out, ROOT)
    if reading["status"] != "VERIFIED":
        raise RuntimeError("the saved-evidence reader did not complete")
    reading.update(chain_wall_seconds=time.perf_counter() - start_wall,
                   chain_cpu_seconds=time.process_time() - start_cpu,
                   chain_timing_scope="runner entry through worker and complete reader, import/serialization gaps included; final write and engineering/admission additional")
    from experiments.candidates.uav_local_history.b01.study import write_json
    write_json(args.out / "reading.json", reading)
    return batch


if __name__ == "__main__":
    if main()["state"] != "COMPLETE":
        raise SystemExit(1)
