"""Admitted fixed B03 native worker or complete saved-state independent reader."""
import argparse
import json
import os
from pathlib import Path
import sys
import shutil
import traceback

if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
from experiments.candidates.uav_decision_generalization.b03_joint_window import contract as c


def parser():
    result=argparse.ArgumentParser(description=__doc__)
    result.add_argument('--mode',required=True,choices=('worker','reader'))
    result.add_argument('--seed',required=True,type=int)
    result.add_argument('--launch-sha',required=True)
    result.add_argument('--out',required=True,type=Path)
    for name in ('study-input','budget-ledger','worker-input'):
        result.add_argument('--'+name,type=Path,required=name!='worker-input')
        result.add_argument('--'+name+'-sha256',required=name!='worker-input')
    return result


def runtime():
    for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
    import numpy as np
    import torch
    if torch.__version__!='2.7.0+cu118' or np.__version__!='1.26.3':raise RuntimeError('frozen Torch2.7.0+cu118/NumPy1.26.3 runtime required')
    torch.set_num_threads(4);torch.set_num_interop_threads(1);torch.use_deterministic_algorithms(True)
    return {'torch':torch.__version__,'numpy':np.__version__,'device':'cpu','torch_threads':4,'torch_interop_threads':1,
            'blas_threads':1,'GPU_seconds':0,'nominal_cpu_forecast_hours':[18,26],'forecast_is_hard_stop':False}


def resource_request(out):
    from scripts.hmasd_resource_preflight import capture_snapshot,assess_memory_floor
    snapshot=capture_snapshot();assessment=assess_memory_floor(snapshot);disk_free=shutil.disk_usage(out).free
    minimum=8*1024**3
    facts={'snapshot':snapshot,'shared_floor_assessment':assessment,'requested_memory_bytes':minimum,'requested_disk_free_bytes':minimum,'disk_free_bytes':disk_free}
    if any(assessment.get(key) is None or assessment[key]<minimum for key in ('available_physical_bytes','effective_available_bytes')) or disk_free<minimum:
        raise RuntimeError('selected8GiB physical/effective available memory and free disk request not satisfied: '+json.dumps(facts))
    return facts


def accepted_output(args,admission,paths):
    root=Path(__file__).resolve().parents[4];out=args.out.absolute()
    if args.launch_sha!=admission['sha'] or str(root)!=paths.get('source_root') or str(out)!=paths.get('output_root') or out.resolve()!=out:raise ValueError('admitted source/output/sha mismatch')
    launch=json.loads((out/'launch-manifest.json').read_bytes())
    if any(launch.get(k)!=v for k,v in {'source_root':str(root),'output_root':str(out),'direction':c.DIRECTION,'sha':admission['sha'],'command_sha256':admission['command_sha256']}.items()):raise ValueError('bound launch invocation mismatch')
    if any((out/name).exists() for name in ('config.json','raw','summary.json')):raise FileExistsError('no repeat of prior scientific output')
    return root,out


def worker_context(locator):
    """The locator root is canonical external storage, never source-snapshot remapped."""
    from experiments.candidates.uav_decision_generalization.b03_joint_window import evidence as e
    if set(locator)!={'schema','root','config_sha256','summary_sha256','manifest_sha256'} or locator['schema']!=1:raise ValueError('complete bound worker locator required')
    root=Path(locator['root'])
    if not root.is_absolute() or root.resolve()!=root:raise ValueError('canonical absolute worker root')
    values={name:e.bound_json(root/(name+'.json'),locator[name+'_sha256']) for name in ('config','summary','manifest')}
    if values['summary']['status']!='COMPLETE' or values['config']['mode']!='worker' or values['config']['contract']!=e.jsonable(c.frozen_contract()):raise ValueError('complete fixed worker identity')
    return {'worker_root':root,'worker_config':values['config'],'worker_summary':values['summary'],'manifest':values['manifest'],
            'manifest_identity':e.identity(root/'manifest.json'),'worker_config_identity':e.identity(root/'config.json'),'worker_summary_identity':e.identity(root/'summary.json')}


def main(argv=None):
    args=parser().parse_args(argv)
    if args.seed!=c.MASTER:raise ValueError('fixed master seed required')
    if (args.worker_input is None)!=(args.worker_input_sha256 is None) or (args.mode=='reader')!=(args.worker_input is not None):raise ValueError('reader requires exactly one bound canonical worker locator')
    from scripts.hmasd_admission import ENVIRONMENT_KEY,require_admission
    paths=json.loads(os.environ.get(ENVIRONMENT_KEY,'{}'))
    admission=require_admission(__file__,direction='uav_decision_generalization')
    root,out=accepted_output(args,admission,paths)
    # Pin BLAS before evidence imports NumPy; admission precedes numerical effects.
    for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
    from experiments.candidates.uav_decision_generalization.b03_joint_window import evidence as e
    meter=None
    try:
        study=e.bound_json(args.study_input,args.study_input_sha256);prior=e.bound_json(args.budget_ledger,args.budget_ledger_sha256);meter=e.Meter(prior)
        sources=e.source_manifest(root)
        if set(study)!={'schema','contract','source_sha256'} or study['schema']!=1 or study['contract']!=e.jsonable(c.frozen_contract()) or study['source_sha256']!=sources:raise ValueError('exact fixed study/source input changed')
        resources=resource_request(out);versions=runtime()
        config={'schema':1,'mode':args.mode,'seed':args.seed,'launch_sha':args.launch_sha,'admission':admission,'contract':e.jsonable(c.frozen_contract()),
                'source_sha256':sources,'study_input':e.identity(args.study_input),'budget_ledger':e.identity(args.budget_ledger),'runtime':versions,'resource_request':resources}
        context={'meter':meter,'config':config,'study_input':study,'source_sha256':sources}
        if args.mode=='reader':
            context.update(worker_context(e.bound_json(args.worker_input,args.worker_input_sha256)));config['worker_input']=e.identity(args.worker_input)
            if context['worker_config']['source_sha256']!=sources:raise ValueError('worker and reader source bytes differ')
            cost=context['worker_summary']['cost'];expected={key:cost['prior']['prior_counts'].get(key,0)+value for key,value in cost['counts'].items()}
            if any(prior['prior_counts'].get(key)!=value for key,value in expected.items()) or prior['prior_cpu_seconds']<cost['resources']['cumulative_cpu_seconds']:raise ValueError('reader ledger omits bound cumulative worker cost')
        e.write_json(out/'config.json',config)
        if args.mode=='worker':
            from experiments.candidates.uav_decision_generalization.b03_joint_window import worker
            worker.run(root,out,args,context)
        else:
            from experiments.candidates.uav_decision_generalization.b03_joint_window import independent
            independent.run(root,out,args,context)
    except BaseException as exc:
        summary=json.loads((out/'summary.json').read_bytes()) if (out/'summary.json').exists() else {}
        summary.update(status='FAILED',mode=args.mode,launch_sha=args.launch_sha,error={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()},cost=meter.report() if meter is not None else {'unmeasured_input_failure':True})
        e.write_json(out/'summary.json',summary);raise


if __name__=='__main__':main()
