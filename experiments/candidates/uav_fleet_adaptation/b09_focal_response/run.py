#!/usr/bin/env python3
"""Admitted four-fit B09 purchase followed by its complete saved-data reader."""
import argparse
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    wall, cpu = time.perf_counter(), time.process_time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--p0", type=Path, required=True)
    parser.add_argument("--p1", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.seed != 29994000:
        parser.error("B09 fixes four fits and one complete 2560-episode purchase")
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction="uav_fleet_adaptation")
    if admission["sha"] != args.launch_sha:
        raise RuntimeError("source differs from accepted admission")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[name] = "1"
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    from experiments.candidates.uav_fleet_adaptation.b09_focal_response.study import run_batch
    parents = {"P0": args.p0, "P1": args.p1}
    batch = run_batch(args.out, args.launch_sha, admission=admission, parent_paths=parents, entry_start=wall, entry_cpu=cpu)
    from experiments.candidates.uav_fleet_adaptation.b09_focal_response.read import publication, read_result
    reading = read_result(args.out, ROOT, parent_paths=parents)
    if reading["status"] != "VERIFIED":
        raise RuntimeError("complete saved-data reader did not finish")
    reading.update(chain_wall_seconds=time.perf_counter() - wall, chain_cpu_seconds=time.process_time() - cpu,
                   chain_timing_scope="Entry through sequential worker/full reader including import/serialization gaps; "
                                      "final writes, staging, admission, transfer and support separate.")
    from experiments.candidates.uav_local_history.b01.study import write_json
    write_json(args.out / "reading.json", reading)
    write_json(args.out / "publication.json", publication(batch, reading, args.out))
    return batch


if __name__ == "__main__":
    if main()["state"] != "COMPLETE":
        raise SystemExit(1)
