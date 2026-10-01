#!/usr/bin/env python3
"""Admitted B08 acquisition, two fixed fits, finals and complete saved-data reader."""
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
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--launch-sha', required=True)
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--parent', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.seed != 29832000:
        parser.error('B08 fixes one paired acquisition, exactly two ridge fits and the complete final panel')
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction='uav_fleet_adaptation')
    if admission['sha'] != args.launch_sha:
        raise RuntimeError('source differs from accepted admission')
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
        os.environ[name] = '1'
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    from experiments.candidates.uav_fleet_adaptation.b08_local_gate.study import run_batch
    batch = run_batch(args.out, args.launch_sha, admission=admission, parent_path=args.parent,
                      entry_start=wall, entry_cpu=cpu)
    from experiments.candidates.uav_fleet_adaptation.b08_local_gate.read import _publication, read_result
    reading = read_result(args.out, ROOT)
    if reading['status'] != 'VERIFIED':
        raise RuntimeError('complete reader did not finish')
    reading.update(chain_wall_seconds=time.perf_counter() - wall, chain_cpu_seconds=time.process_time() - cpu,
                   chain_timing_scope='Runner entry through sequential worker and full reader, including import/serialization gaps; '
                                      'final writes, launch admission, staging and support additional.')
    from experiments.candidates.uav_local_history.b01.study import write_json
    write_json(args.out / 'reading.json', reading)
    write_json(args.out / 'publication.json', _publication(batch, reading, args.out))
    return batch


if __name__ == '__main__':
    if main()['state'] != 'COMPLETE':
        raise SystemExit(1)
