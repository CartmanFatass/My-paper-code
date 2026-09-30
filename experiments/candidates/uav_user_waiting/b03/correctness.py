#!/usr/bin/env python3
"""Fixed necessary40-step native interface fixture; zero scientific fits."""
import argparse
import os
from pathlib import Path
import resource
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))


def main(argv=None):
    start=time.perf_counter()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--launch-sha',required=True)
    parser.add_argument('--seed',required=True,type=int)
    args=parser.parse_args(argv)
    if args.seed!=29425999: parser.error('fixed correctness world29425999 only')
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        os.environ[key]='1'
    from scripts.hmasd_admission import require_admission
    admission=require_admission(__file__,direction='uav_user_waiting')
    if admission['sha']!=args.launch_sha: raise RuntimeError('fixture admission/source mismatch')
    import numpy as np
    import torch
    from experiments.candidates.uav_user_waiting.b03.collector import collect_episode,save_episode,ARMS
    from experiments.candidates.uav_user_waiting.b03.features import FEATURE_DIM,FEATURE_SLICES
    from experiments.candidates.uav_user_waiting.b03.learner import ValueModel,initial_neural_model
    from experiments.candidates.uav_user_waiting.b03.read_core import verify_episode
    from experiments.candidates.uav_user_waiting.b03.study import factory,write_json,file_identity,frozen_config
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    out=args.out.resolve()
    if (out/'summary.json').exists(): raise FileExistsError('no duplicate fixture execution')
    (out/'raw').mkdir(parents=True,exist_ok=True)
    coeff=np.zeros(FEATURE_DIM,np.float64);coeff[FEATURE_SLICES['age']]=.02
    models={'LR':ValueModel('ridge',coefficients=coeff),'LN':initial_neural_model()}
    counts=dict(constructors=0,explicit_resets=0,native_step_calls=0,team_steps=0,
                complete_episodes=0,fit_started=0,optimizer_steps=0)
    result=dict(object='UAV-USER-WAITING-B03-CORRECTNESS',status='RUNNING',launch_sha=args.launch_sha,
        admission=dict(admission),counts=counts,rows=[],verification=[],scientific_invocation=False,
        source_identities=frozen_config(args.launch_sha)['source_identities'],
        scope='five interfaces on oneH8 world,40 native steps; LR fixed literal weights/LNzero-output initialization; no scientific fit/outcome estimate')
    env=None
    try:
        env=factory(args.seed);counts['constructors']+=1;env.env.max_steps=8
        for arm in ARMS:
            row,raw=collect_episode(env,arm,args.seed,out,counts,horizon=8,value=models.get(arm))
            save_episode(out,row,raw);result['rows'].append(row)
            result['verification'].append(verify_episode(row,raw,value=models.get(arm)))
            write_json(out/'summary.json',result)
        assert counts['team_steps']==40 and counts['complete_episodes']==5
        result['status']='COMPLETE'
    except Exception as exc:
        result['status']='INCOMPLETE_TECHNICAL_FAILURE'
        result['error']=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
    finally:
        if env is not None: env.close()
        usage=resource.getrusage(resource.RUSAGE_SELF)
        result['resources']=dict(wall_seconds=time.perf_counter()-start,process_user_seconds=usage.ru_utime,
            process_system_seconds=usage.ru_stime,peak_rss_kib=usage.ru_maxrss)
        result['artifacts']=[file_identity(p) for p in sorted((out/'raw').iterdir()) if p.is_file()]
        write_json(out/'summary.json',result)
    return result


if __name__=='__main__':
    if main()['status']!='COMPLETE': raise SystemExit(1)
