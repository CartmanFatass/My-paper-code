"""Admitted fixed B02 worker (audit+main) or complete independent reader."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import traceback

if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
from experiments.candidates.uav_decision_generalization.b02_feedback_cooperation import contract as c,io


def parser():
    result=argparse.ArgumentParser(description=__doc__)
    result.add_argument('--mode',required=True,choices=('worker','reader'))
    result.add_argument('--seed',required=True,type=int)
    result.add_argument('--launch-sha',required=True)
    result.add_argument('--out',required=True,type=Path)
    for name in ('actor-input','budget-ledger','worker-input'):
        result.add_argument('--'+name,type=Path,required=name!='worker-input')
        result.add_argument('--'+name+'-sha256',required=name!='worker-input')
    return result


def runtime():
    for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
    import numpy as np
    import torch
    if torch.__version__!='2.7.0+cu118' or np.__version__!='1.26.3':raise RuntimeError('frozen CPU runtime Torch2.7.0+cu118/NumPy1.26.3 required')
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    return {'torch':torch.__version__,'numpy':np.__version__,'torch_threads':torch.get_num_threads(),
            'torch_interop_threads':torch.get_num_interop_threads(),'device':'cpu','dtype':'float32'}


def disk(root,out,records,worker=None):
    roots=[{'category':'new_source_snapshot','root':str(root),'allocated_bytes':io.allocated_bytes(root)},
           {'category':'new_evidence','root':str(out),'allocated_bytes':io.allocated_bytes(out)}]
    roots += [{'category':'inherited_canonical_actor','root':r['path'],'allocated_bytes':Path(r['path']).stat().st_blocks*512} for r in records]
    if worker is not None:roots.append({'category':'existing_B02_worker_evidence','root':str(worker),'allocated_bytes':io.allocated_bytes(worker)})
    return roots


def worker(root,out,args,actors,records,budget,config,summary,inflight):
    from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
    from experiments.candidates.uav_decision_generalization.b02_feedback_cooperation import collect,phases
    all_rows=[];tables=[];counts_by_phase={}
    summary.update(rows_completed=0,counts=counts_by_phase)
    for phase in ('audit','main'):
        budget.check();counts={'constructor_resets':0,'explicit_resets':0,'native_step_calls':0,'native_steps':0,'episodes':0}
        counts_by_phase[phase]=counts
        constructor_cpu,constructor_wall=time.process_time(),time.perf_counter()
        # The frozen factory owns exactly one native constructor reset; the adapter does not reset.
        counts['constructor_resets']+=1
        env=make_real(c.AUDIT_WORLDS[0] if phase=='audit' else c.WORLDS[0])
        summary.setdefault('constructor_times',{})[phase]={'cpu_seconds':time.process_time()-constructor_cpu,'wall_seconds':time.perf_counter()-constructor_wall}
        rows=[]
        try:
            for spec in c.episode_order(phase):
                budget.check();row=collect.episode(env,spec,actors,out,counts,inflight);rows.append(row);all_rows.append(row)
                summary['rows_completed']=len(all_rows)
                io.write_json(out/'episodes.json',{'rows':all_rows})
                summary['cost']=budget.snapshot();io.write_json(out/'summary.json',summary);budget.check()
        finally:
            env.close()
        io.verify_actors(actors,records)
        if phase=='audit':
            # No native/policy state survives into main; addressed draws and isolated reader controllers.
            import torch
            import numpy as np
            torch_rng=torch.get_rng_state().clone();numpy_rng=np.random.get_state()
            audit=phases.read_phase(out,rows,actors,budget,out,inflight,phase='audit')
            if not torch.equal(torch_rng,torch.get_rng_state()) or any(not np.array_equal(a,b) for a,b in zip(numpy_rng,np.random.get_state())):
                raise AssertionError('independent audit reading changed global RNG state')
            io.verify_actors(actors,records)
            table=phases.work_table(rows,audit['results'],'audit',counts);tables.append(table)
            audit.update(source_sha256=config['source_sha256'],actor_input_sha256=args.actor_input_sha256,
                         worker_config=io.identity(out/'config.json'),table=table,
                         episode_metrics=[{'spec':{k:r[k] for k in ('phase','arm','world','tape','sampling_root')},'metrics':r['metrics']} for r in rows],
                         cost=budget.snapshot())
            io.write_json(out/'audit_reading.json',audit);summary['audit_reading']=io.identity(out/'audit_reading.json')
            summary['audit_table']=table;summary['audit_reader_cpu_seconds']=audit['reader_cpu_seconds']
        else:
            # Final reader will independently reconstruct these480 files. Worker reports only online work.
            summary['main_online_counts']=counts
    io.verify_actors(actors,records);budget.check()
    summary['online_episode_cpu_seconds']=sum(r['episode_cpu_seconds'] for r in all_rows)
    summary.update(status='COMPLETE',episodes=io.identity(out/'episodes.json'),cost=budget.snapshot(),
                   disk_roots=disk(root,out,records),new_native_steps=sum(x['native_steps'] for x in counts_by_phase.values()),
                   audit_verified_before_main=True,new_fits=0,optimizer_updates=0,GPU_seconds=0)


def reader(root,out,args,actors,records,budget,config,summary,inflight):
    from experiments.candidates.uav_decision_generalization.b02_feedback_cooperation import phases,metrics
    worker_root,worker_config,worker_summary,audit_rows,main_rows,audit=phases.bound_worker(args.worker_input,args.worker_input_sha256,config['source_sha256'],args.actor_input_sha256)
    if (budget.prior['prior_cpu_seconds']<worker_summary['cost']['cumulative_cpu_seconds']
            or budget.synthetic!=worker_summary['cost']['synthetic']):raise ValueError('reader ledger omits worker CPU/check usage')
    config['worker_input']=io.identity(args.worker_input);config['worker_input_sha256']=args.worker_input_sha256
    config['worker_root']=str(worker_root);io.write_json(out/'config.json',config)
    result=phases.read_phase(worker_root,main_rows,actors,budget,out,inflight,phase='main')
    io.verify_actors(actors,records)
    table=phases.work_table(main_rows,result['results'],'main',worker_summary['counts']['main'])
    audit_table=phases.work_table(audit_rows,audit['results'],'audit',worker_summary['counts']['audit'])
    if audit_table!=audit['table'] or audit['worker_config']!=io.identity(worker_root/'config.json'):raise ValueError('audit source/work binding')
    # Bound audit metrics/identities are adopted, without additional source replay or native queries.
    if audit['episode_metrics']!=[{'spec':{k:r[k] for k in ('phase','arm','world','tape','sampling_root')},'metrics':r['metrics']} for r in audit_rows]:raise ValueError('audit metrics binding')
    budget.check();contrasts=metrics.comparisons(main_rows);budget.check()
    result.update(status='VERIFIED',source_sha256=config['source_sha256'],actor_input_sha256=args.actor_input_sha256,
                  launch_sha=args.launch_sha,worker_config=io.identity(worker_root/'config.json'),worker_summary=io.identity(worker_root/'summary.json'),
                  adopted_audit=io.identity(worker_root/'audit_reading.json'),audit_replayed_episodes=0,main_replayed_episodes=480,
                  complete_evidence_episodes=496,audit_first4_parent_identity=audit['first4_parent_identity'],
                  cost_table=phases.combined_cost((audit_table,table),budget.synthetic),phase_tables=[audit_table,table],
                  comparisons=contrasts,cost=budget.snapshot())
    io.write_json(out/'reading.json',result)
    summary.update(status='COMPLETE',reading=io.identity(out/'reading.json'),cost=budget.snapshot(),
                   new_native_steps=0,new_source_replay_episodes=480,adopted_audit_episodes=16,
                   main_reader_cpu_seconds=result['reader_cpu_seconds'],
                   disk_roots=disk(root,out,records,worker_root),GPU_seconds=0)


def main(argv=None):
    args=parser().parse_args(argv)
    if args.seed!=c.MASTER:raise ValueError('fixed master seed required')
    if (args.worker_input is None)!=(args.worker_input_sha256 is None) or (args.mode=='reader')!=(args.worker_input is not None):raise ValueError('reader requires exactly one bound worker locator')
    from scripts.hmasd_admission import ENVIRONMENT_KEY,require_admission
    paths=json.loads(os.environ.get(ENVIRONMENT_KEY,'{}'))
    admission=require_admission(__file__,direction='uav_decision_generalization')
    root,out,budget=io.accepted_output(__file__,args,admission,paths)
    summary={'status':'PARTIAL','mode':args.mode,'launch_sha':args.launch_sha,'seed':args.seed};inflight={}
    try:
        source=io.source_identity(root);io.verify_calibration(root)
        records=io.asset_records(args.actor_input,args.actor_input_sha256)
        versions=runtime()
        config={'mode':args.mode,'seed':args.seed,'launch_sha':args.launch_sha,'admission':admission,'contract':c.contract(),
                'source_sha256':source,'actor_input':io.identity(args.actor_input),'actor_input_sha256':args.actor_input_sha256,
                'budget_ledger':io.identity(args.budget_ledger),'budget_ledger_sha256':args.budget_ledger_sha256,'runtime':versions}
        io.write_json(out/'config.json',config)
        t0,t1=time.perf_counter(),time.process_time();actors=io.load_actors(records)
        summary['actor_load']={'cpu_seconds':time.process_time()-t1,'wall_seconds':time.perf_counter()-t0};budget.check()
        if args.mode=='worker':worker(root,out,args,actors,records,budget,config,summary,inflight)
        else:reader(root,out,args,actors,records,budget,config,summary,inflight)
        budget.check();summary['cost']=budget.snapshot()
        components={'actor_load':summary['actor_load']['cpu_seconds']}
        if args.mode=='worker':
            components.update(native_constructors=sum(t['cpu_seconds'] for t in summary['constructor_times'].values()),
                              online_episodes=summary['online_episode_cpu_seconds'],audit_reader=summary['audit_reader_cpu_seconds'])
        else:components['main_reader']=summary['main_reader_cpu_seconds']
        components['entry_import_identity_disk_serialization_and_other']=summary['cost']['process_and_finished_children_cpu_seconds']-sum(components.values())
        summary['cpu_components_seconds']=components
        io.write_json(out/'summary.json',summary)
    except BaseException as error:
        summary.update(status='FAILED',error={'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()},
                       inflight=inflight,cost=budget.snapshot())
        io.write_json(out/'summary.json',summary)
        raise


if __name__=='__main__':main()
