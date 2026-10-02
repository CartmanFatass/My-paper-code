"""Single admitted B04 bank→six final fits→cold native comparison→complete reader."""
from __future__ import annotations
import argparse
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from experiments.candidates.typed_joint_skill_decision.b04 import contract as c, evidence as e


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--launch-sha',required=True)
    p.add_argument('--seed',required=True,type=int,choices=[0])
    p.add_argument('--input-manifest',required=True,type=Path)
    p.add_argument('--input-manifest-sha256',required=True)
    return p


def validate_manifest(m,root):
    if (m['schema']!=1 or m['direction']!='typed_joint_skill_decision' or m['study']!='b04_raw_layout_finite_data_curve'
        or m['fits']!=list(c.FITS) or m['native_arms']!=list(c.ARMS)
        or m['worlds']!={'common_train_probe_count':512,'engineering_train_offsets':[0,1,2,3],
             'fresh_count':512,'fresh_start':109420000,'native_count':128,'sizes':[1000,4000,16000],
             'train_count':16000,'train_start':109400000}
        or m['training']['updates_per_fit']!=4096 or m['training']['batch_worlds']!=32
        or m['training']['subset_candidates']!=16 or m['training']['temperature']!=.02
        or m['training']['optimizer']!={'name':'AdamW','lr':.001,'weight_decay':.0001,'betas':[.9,.999],'eps':1e-8}
        or m['training']['clip'] is not None or m['training']['schedule'] is not None
        or m['model']['parameters']!=205441 or m['model']['full_menu_chunk']!=64
        or m['model']['dtype']!='float32' or m['model']['tf32'] is not False
        or m['runtime']['device']!='cuda:0' or m['runtime']['package_installs']!=0 or m['runtime']['weight_downloads']!=0):
        raise ValueError('fixed B04 scientific manifest mismatch')
    ceilings={'all_candidate_presentations':15471824,'cold_candidate_presentations':169728,'cpu_seconds':28800,
              'disk_allocated_bytes':7516192768,'endpoint_candidate_presentations':1357824,'engineering_candidate_presentations':3536,
              'fits':6,'functional_reader_candidate_presentations':1357824,'gpu_reserved_wall_seconds':14400,
              'native_steps':584000,'static_calls':8682080,'training_candidate_presentations':12582912,
              'training_world_presentations':786432,'updates':24576}
    if m['ceilings']!=ceilings or m['model']['tensor_shapes']!={k:list(v) for k,v in c.SHAPES.items()}:
        raise ValueError('complete ceiling/feature tensor contract mismatch')
    expected={f'envs/pettingzoo/{k}.py' for k in ('scenario2','uav_env','uav_radio')}
    expected.update(f'experiments/candidates/coupled_host_joint_skills_stage1/{k}.py' for k in ('host','menus','planner','run_gate'))
    if set(m['pinned_upstream_sources'])!=expected:
        raise ValueError('complete native source set required')
    for relative,digest in m['pinned_upstream_sources'].items():
        if e.sha(e.relative_path(root,relative))!=digest:
            raise ValueError('pinned upstream bytes changed: '+relative)
    if m['audits']!={'P_world_offsets':[0,1],'Raw8J_world_offsets':[0],'RawJ_world_offsets':[0],'students_world_offsets':[0,1]}:
        raise ValueError('fixed audit allocation mismatch')
    if m['disk_scope']['include_current_source_snapshot'] is not True or m['disk_scope']['shared_interpreter_copied'] is not False:
        raise ValueError('fixed complete disk scope')
    if (m['ordinary']['Raw8J']['reference_commit']!='61a2dfa9cde0178d482d0a079c5629c3bcb7789e'
        or m['ordinary']['Raw8J']['reference_path']!='experiments/candidates/typed_joint_skill_decision/contract.py'
        or m['ordinary']['Raw8J']['reference_sha256']!='71c5eb1d904370cbb853ce1cbfbde652391bb78b25b3a42c4ecebaeb653d82fe'
        or m['ordinary']['Raw8J']['max_static_calls']!=8 or m['ordinary']['RawJ']['max_static_calls']!=221
        or m['ordinary']['P']['entry']!='compute_menu(world, area_size=5000, budget=3000)'
        or m['ordinary']['P']['max_static_calls']!=6001):
        raise ValueError('fixed ordinary source/procedure mismatch')


CHILD_KEYS={'parent_pid','admission','launch_sha','input_sha256','source_root','out','runtime','checkpoint_path','checkpoint_sha256','prior_parent_cpu_seconds'}


def checked_child(context):
    if (set(context)!=CHILD_KEYS or context['parent_pid']!=os.getppid() or context['admission']['child_pid']!=os.getppid()
        or context['admission']['direction']!='typed_joint_skill_decision' or context['admission']['sha']!=context['launch_sha']
        or Path(context['source_root']).resolve()!=ROOT):
        raise RuntimeError('legal-only admitted parent/source context required')
    launch=json.loads((Path(context['out'])/'launch-manifest.json').read_bytes())
    if launch['sha']!=context['launch_sha'] or launch['command_sha256']!=context['admission']['command_sha256']:
        raise RuntimeError('child launch/source identity mismatch')


def child_write(root,relative,value,bill):
    path=e.relative_path(root,relative);data=e.encoded(value)
    bill.check(pending=len(data)+1024**2);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:
        f.write(data);f.flush();os.fsync(f.fileno())
    return e.sha(path)


def case_main(connection,context,bill,world,arm):
    trace=None;paths=[]
    try:
        checked_child(context)
        if world not in range(c.FRESH_START,c.FRESH_START+128) or arm not in c.ARMS:
            raise ValueError('undeclared native program/world')
        bill.prior_parent_cpu_seconds=context['prior_parent_cpu_seconds'];c.threads()
        before=bill.snapshot()['counters'];started=time.perf_counter()
        from experiments.candidates.typed_joint_skill_decision.b04.native import Native,execute
        from experiments.candidates.typed_joint_skill_decision.b04.online import select
        base=f'raw/main/{world}/{arm}';query_path=base+'/queries.jsonl.gz'
        trace=e.Trace(e.relative_path(context['out'],query_path),bill);paths.append(query_path)
        imports=time.perf_counter()-started
        with Native(bill) as native:
            native.query_trace=trace
            env,decision=select(native,world,arm,context,bill)
            native.query_trace=None;trace.close();query_instrumentation=trace.timing();trace=None
            decision['timing'].update(import_seconds=imports,child_selection_seconds=time.perf_counter()-started)
            decision['timing']['query_trace_instrumentation']=query_instrumentation
            decision['selection_counts']={k:v-before[k] for k,v in bill.snapshot()['counters'].items()}
            relative=base+'/selection.json'
            digest=child_write(context['out'],relative,decision,bill);paths.append(relative)
            connection.send({'kind':'selection_ready','selection':relative,'sha256':digest,'paths':paths,'cpu':e.cpu()})
            permission=connection.recv()
            if permission!={'kind':'verified','sha256':digest}:
                raise AssertionError('immutable selection authorization mismatch')
            # One real matched diagnostic after commitment, then a full execution reset.
            matched=e.plain(native.host.static_evaluate(env,decision['assigned_targets_xyz'],allow_a2a=True))
            path=base+'/trace.jsonl.gz';paths.append(path)
            result=execute(env,decision,e.relative_path(context['out'],path),bill)
            bill.charge('main_episodes')
            native_path=base+'/native.json';child_write(context['out'],native_path,result,bill);paths.append(native_path)
            connection.send({'kind':'complete','paths':paths,'matched_endpoint':matched,'cpu':e.cpu(),
                             'case_counts':{k:v-before[k] for k,v in bill.snapshot()['counters'].items()}})
    except BaseException as exc:
        if trace is not None:
            trace.close()
        failure={'world':world,'arm':arm,'type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc(),
                 'paths':paths,'bill':bill.snapshot(),'retry':False}
        if 'env' in locals():
            from experiments.candidates.typed_joint_skill_decision.b04.native import state
            try:
                failure['last_native_state_repr']=repr(state(env))
            except BaseException as capture_error:
                failure['state_capture_error']=repr(capture_error)
        path=e.relative_path(context['out'],f'raw/main/{world}/{arm}/failure.json')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(e.encoded(failure))
        connection.send({'kind':'failed',**failure})
    finally:
        connection.close()


def endpoint_choice(store,asset,world):
    import numpy as np
    fit=asset['fit'];relative=f'raw/endpoints/{fit["id"]}/fresh.npz'
    if relative not in store.files or e.sha(e.relative_path(store.root,relative))!=store.files[relative]['sha256']:
        raise ValueError('unbound GPU fresh endpoint')
    with np.load(e.relative_path(store.root,relative),allow_pickle=False) as z:
        records=json.loads(str(z['records']))
    row=records[world-c.FRESH_START]
    if row['world']!=world:
        raise ValueError('endpoint address mismatch')
    return row['choice']


def spawn_case(ctx,context,store,view,assets,diagnostics,world,arm):
    from experiments.candidates.typed_joint_skill_decision.b04.reader import world_gate,exact
    parent,child=ctx.Pipe(duplex=True);bill=store.bill
    asset=next((a for a in assets if a['fit']['id']==arm),None)
    context={**context,'prior_parent_cpu_seconds':e.cpu()['total_seconds'],
             'checkpoint_path':None if asset is None else str(e.relative_path(store.root,asset['path'])),
             'checkpoint_sha256':None if asset is None else asset['sha256']}
    process=ctx.Process(target=case_main,args=(child,context,bill,world,arm))
    started=time.perf_counter();parent_self=e.cpu()['self_seconds'];ready=None;decision=None;completed=None
    bill.charge('spawn_attempts')
    try:
        process.start();child.close()
        while process.is_alive() or parent.poll():
            if parent.poll(.25):
                try:
                    message=parent.recv()
                except EOFError:
                    break
                if message['kind']=='selection_ready':
                    if ready is not None:
                        raise AssertionError('duplicate immutable selection-ready')
                    ready=time.perf_counter()-started;selection_parent_cpu=e.cpu()['self_seconds']-parent_self
                    for relative in message['paths']:
                        store.register(relative)
                    path=e.relative_path(store.root,message['selection'])
                    if e.sha(path)!=message['sha256']:
                        raise AssertionError('immutable selection changed')
                    decision=e.load_output(store.root,store.files,message['selection'])
                    exact(decision['world'],world,'cold program world',diagnostics);exact(decision['arm'],arm,'cold program arm',diagnostics)
                    exact(decision['source_sha'],store.launch_sha,'cold source SHA',diagnostics)
                    exact(decision['input_sha256'],store.input_sha256,'cold input SHA',diagnostics)
                    # Fresh label/endpoint read occurs only AFTER selection/time commitment.
                    record=view.load(world);world_gate(decision,record,diagnostics)
                    if asset is not None:
                        exact(decision['chosen_raw_index'],endpoint_choice(store,asset,world),'cold actual vs frozen GPU choice',diagnostics)
                    decision.update(parent_cold_selection_seconds=ready,selection_child_cpu=message['cpu'],
                                    selection_parent_cpu_seconds=selection_parent_cpu,
                                    cold_scope='fresh process through immutable selection-ready, including required evidence serialization; not uninstrumented production latency')
                    bill.check();parent.send({'kind':'verified','sha256':message['sha256']})
                elif message['kind'] in ('complete','failed'):
                    completed=message
                else:
                    raise AssertionError('unknown child message')
            bill.check()
        process.join();bill.check()
        if completed is not None:
            for relative in completed['paths']:
                if e.relative_path(store.root,relative).is_file():
                    store.register(relative)
        if process.exitcode!=0 or completed is None or completed['kind']!='complete' or ready is None:
            store.progress('child_failed',world=world,arm=arm,exitcode=process.exitcode,message=completed)
            raise RuntimeError(f'child {world}/{arm} failed without retry: {completed and completed.get("error")}')
        decision.update(case_counts=completed['case_counts'],child_total_cpu=completed['cpu'],
                        parent_case_wall_seconds=time.perf_counter()-started)
        relative=f'raw/main/{world}/{arm}/decision.json';store.write(relative,decision)
        store.write(f'raw/main/{world}/{arm}/matched-endpoint.json',completed['matched_endpoint'])
        bill.charge('spawn_completed')
        return {'world':world,'arm':arm,'decision':relative,'native':f'raw/main/{world}/{arm}/native.json',
                'trace':f'raw/main/{world}/{arm}/trace.jsonl.gz','queries':f'raw/main/{world}/{arm}/queries.jsonl.gz',
                'matched_endpoint':completed['matched_endpoint'],'selection_counts':decision['selection_counts']}
    except BaseException:
        if process.pid is not None and process.is_alive():
            process.terminate();process.join()
        base=store.root/'raw'/'main'/str(world)/arm
        if base.exists():
            for path in base.rglob('*'):
                if path.is_file():
                    store.register(str(path.relative_to(store.root)))
        raise
    finally:
        parent.close();child.close()


def count_complete(store,cases,bank_rows):
    counts=store.bill.snapshot()['counters']
    required={'fits':6,'fits_completed':6,'updates':24576,'updates_completed':24576,
              'training_world_presentations':786432,'training_candidate_presentations':12582912,
              'training_completed_candidates':12582912,'bank_worlds':16512,'label_rebuild_worlds':16512,
              'native_steps':584000,'native_completed':584000,'main_episodes':1152,'audit_episodes':16,
              'spawn_attempts':1152,'spawn_completed':1152,'reader_state_checks':585168,
              'functional_contexts':6144,'endpoint_contexts':6144,'cold_contexts':768,'engineering_contexts':16}
    expected_static=2*bank_rows+sum(r['selection_counts']['static_calls'] for r in cases)+1152+585168+16
    if any(counts[k]!=v for k,v in required.items()) or counts['static_calls']!=expected_static or counts['static_completed']!=expected_static:
        raise AssertionError('complete declared work/count mismatch: '+str(counts))
    for phase in e.ROW_PHASES:
        if counts[phase+'_candidate_presentations']!=counts[phase+'_completed_candidates']:
            raise AssertionError('incomplete neural attempt stream '+phase)
    if counts['all_candidate_presentations']!=sum(counts[p+'_candidate_presentations'] for p in e.ROW_PHASES):
        raise AssertionError('full neural-row cost identity mismatch')


def main(argv=None):
    args=parser().parse_args(argv)
    spec=json.loads(os.environ.get('HMASD_ADMISSION_V1','{}'))
    from scripts.hmasd_admission import require_admission
    admission=dict(require_admission(__file__,direction='typed_joint_skill_decision'))
    source,out=Path(spec['source_root']).resolve(strict=True),args.out.resolve()
    if source!=ROOT or out!=Path(spec['output_root']).resolve() or args.launch_sha!=admission['sha'] or len(args.launch_sha)!=40:
        raise ValueError('exact admitted source/output/SHA required')
    launch=json.loads((out/'launch-manifest.json').read_bytes())
    if (launch['sha']!=args.launch_sha or launch['command_sha256']!=admission['command_sha256']
        or Path(launch['source_root']).resolve()!=source or Path(launch['output_root']).resolve()!=out
        or launch['direction']!='typed_joint_skill_decision'):
        raise ValueError('launcher identity mismatch')
    manifest=e.bound_json(args.input_manifest,args.input_manifest_sha256);validate_manifest(manifest,source)
    thread_env=c.threads();scope=manifest['disk_scope'];ctx=multiprocessing.get_context('spawn')
    # Absolute external locators come from published metadata, not remapped scientific argv.
    roots=[source,scope['canonical_direction_runs'],scope['own_scratch'],scope['retained_model_root']]
    if not Path(scope['canonical_direction_runs']).resolve() in out.parents:
        raise ValueError('admitted output must be within declared canonical direction runs')
    os.environ['CUDA_CACHE_PATH']=str(Path(scope['own_scratch'])/'b04-cuda-cache')
    bill=e.Bill(ctx.Array('q',len(e.COUNTERS),lock=False),ctx.Lock(),roots,
                immutable_roots=[source,scope['retained_model_root']])
    store=e.Store(out,bill);store.launch_sha=args.launch_sha;store.input_sha256=args.input_manifest_sha256;store.input_manifest=manifest
    diagnostics=e.Diagnostics(store)
    try:
        store.write('config.json',{'schema':1,'study':manifest['study'],'launch_sha':store.launch_sha,'input_sha256':store.input_sha256,
                                  'admission':admission,'input_manifest_data':manifest,'source_root':source,'out':out,'seed':0,
                                  'threads':thread_env,'CUDA_CACHE_PATH':os.environ['CUDA_CACHE_PATH'],
                                  'argv':sys.argv[1:] if argv is None else argv})
        effective=c.configure(cuda=False,expected=manifest['runtime'])
        store.write('runtime.json',effective)
        from experiments.candidates.typed_joint_skill_decision.b04 import bank,training,reader,online
        from experiments.candidates.typed_joint_skill_decision.b04.native import Native
        with Native(bill) as native:
            bank.build_bank(store,native,'train');bank.build_bank(store,native,'fresh')
            train=bank.Bank(out,store.files,'train',store.launch_sha,store.input_sha256)
            fresh=bank.Bank(out,store.files,'fresh',store.launch_sha,store.input_sha256)
            reader.rebuild_bank(store,native,train,diagnostics);reader.rebuild_bank(store,native,fresh,diagnostics)
            reader.engineering_static(store,native,train)
        bank_rows=sum(len(train.load(w)['infos']) for w in range(c.TRAIN_START,c.TRAIN_START+c.TRAIN_COUNT))
        bank_rows+=sum(len(fresh.load(w)['infos']) for w in range(c.FRESH_START,c.FRESH_START+c.FRESH_COUNT))
        assets=[];initials={}
        training_view=bank.TrainingBank(train)
        for i,fit in enumerate(c.FITS):
            assets.append(training.fit_once(store,training_view,fit,initials,engineering=i==0))
            store.write(f'assets/{fit["id"]}.json',assets[-1])
        # All six final checkpoints are fixed before fresh scorer/model access.
        for asset in assets:
            with bill.gpu():
                network=online.checkpoint_model(e.relative_path(out,asset['path']),asset['sha256'],asset['fit'],store.launch_sha,store.input_sha256)
                training.endpoint(store,network,fresh,asset['fit'],'fresh')
                del network
                import torch
                torch.cuda.empty_cache()
        context={'parent_pid':os.getpid(),'admission':admission,'launch_sha':store.launch_sha,'input_sha256':store.input_sha256,
                 'source_root':str(source),'out':str(out),'runtime':manifest['runtime']}
        cases=[]
        for i,world in enumerate(range(c.FRESH_START,c.FRESH_START+128)):
            order=list(c.ARMS);order=order[i%9:]+order[:i%9]
            for arm in order:
                cases.append(spawn_case(ctx,context,store,fresh,assets,diagnostics,world,arm))
                store.progress('native_main',completed_cases=len(cases),total_cases=1152,world=world,arm=arm)
        store.write_gzip('raw/main/cases.json.gz',cases)
        summary=reader.complete(store,train,training_view,fresh,assets,{(r['world'],r['arm']):r for r in cases},diagnostics)
        count_complete(store,cases,bank_rows);diagnostics.close();bill.check()
        summary.update(schema=1,direction='typed_joint_skill_decision',launch_sha=store.launch_sha,input_sha256=store.input_sha256,
                       bill=bill.snapshot(),diagnostics={'path':diagnostics.relative,'count':len(diagnostics),'format':'gzip-jsonl'},
                       dtype='float32',coordinates='float64 normalized before float32 network',tolerances=c.TOLERANCES)
        store.write('summary.json',summary);store.progress('complete',fits=6,main_cases=1152,reader_worlds=128)
        return 0
    except BaseException as exc:
        diagnostics.close();store.failure(exc)
        raise


if __name__=='__main__':
    raise SystemExit(main())
