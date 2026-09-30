#!/usr/bin/env python3
"""One admitted B06 producer and its fixed complete saved-evidence reader."""
import argparse
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    started, cpu_started = time.perf_counter(), time.process_time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args(argv)
    if args.seed != 29514000:
        parser.error("B06 fixes both inherited assets, the complete count panel and randomness")
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_fleet_adaptation")
    if admission["sha"] != args.launch_sha:
        raise RuntimeError("source differs from accepted admission")
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[key] = "1"
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    from experiments.candidates.uav_fleet_adaptation.b06_count_development.study import run_batch
    batch = run_batch(args.out, args.launch_sha, admission=admission, entry_start=started, entry_cpu=cpu_started)
    from experiments.candidates.uav_fleet_adaptation.b06_count_development.read import read_result
    reading = read_result(args.out, ROOT)
    if reading["status"] != "VERIFIED":
        raise RuntimeError("complete saved-evidence reading did not finish")
    reading.update(chain_wall_seconds=time.perf_counter() - started,
                   chain_cpu_seconds=time.process_time() - cpu_started,
                   chain_timing_scope="runner entry through producer and fixed reader, import/serialization gaps included; final write/admission/support additional")
    from experiments.candidates.uav_local_history.b01.study import write_json
    write_json(args.out / "reading.json", reading)
    return batch


if __name__ == "__main__":
    if main()["state"] != "COMPLETE":
        raise SystemExit(1)
