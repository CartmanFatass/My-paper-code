#!/usr/bin/env python3
"""Admitted frozen four-fit B01 worker followed by the full saved-data reader."""
import argparse
import os
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

def main(argv=None):
    wall,cpu=time.perf_counter(),time.process_time()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--parent',type=Path,required=True)
    parser.add_argument('--seed',type=int,required=True);parser.add_argument('--launch-sha',required=True)
    args=parser.parse_args(argv)
    if args.seed!=40160000: parser.error('B01 freezes all four fits, complete endpoints and full reader')
    from scripts.hmasd_admission import require_admission
    admission=require_admission(__file__,direction='uav_episode_policy_search')
    if admission['sha']!=args.launch_sha: raise RuntimeError('accepted source mismatch')
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'): os.environ[key]='1'
    import_wall,import_cpu=time.perf_counter(),time.process_time()
    import torch
    torch.set_num_threads(1);torch.set_num_interop_threads(1);torch.use_deterministic_algorithms(True)
    from experiments.candidates.uav_episode_policy_search.b01.study import run_batch
    import_timing=dict(wall_seconds=time.perf_counter()-import_wall,cpu_seconds=time.process_time()-import_cpu,scope='torch, candidate/dependency scientific imports and thread initialization after admission')
    batch=run_batch(args.out,args.launch_sha,admission=admission,parent_path=args.parent,entry_start=wall,entry_cpu=cpu,import_timing=import_timing)
    from experiments.candidates.uav_episode_policy_search.b01.read import read_result
    reading=read_result(args.out,ROOT,args.parent)
    reading.update(chain_wall_seconds=time.perf_counter()-wall,chain_cpu_seconds=time.process_time()-cpu,
                   chain_timing_scope='Main entry, argument parsing and admission handshake, imports, asset initialization, worker, compression, full reader. Staging, launcher preflight, process startup before main and support are additional/unmeasured.')
    from experiments.candidates.uav_local_history.b01.study import write_json
    write_json(args.out/'reading.json',reading)
    from experiments.candidates.uav_episode_policy_search.b01.read import _publication
    write_json(args.out/'publication.json',_publication(batch,reading,args.out))
    return batch
if __name__=='__main__': main()
