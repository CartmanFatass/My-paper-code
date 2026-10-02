"""One admitted B07 full reader; 258 fresh independent data-only children."""
from __future__ import annotations
import argparse
import ctypes
import faulthandler
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import signal
import subprocess
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[4]
sys.dont_write_bytecode=True
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from experiments.candidates.typed_joint_skill_decision.b07_fixed_bank import contract as c,evidence as e


class Stop(RuntimeError):pass


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',required=True,type=Path);p.add_argument('--launch-sha',required=True)
    p.add_argument('--seed',required=True,type=int,choices=[0]);p.add_argument('--input-manifest',required=True,type=Path)
    p.add_argument('--input-manifest-sha256',required=True)
    return p


def limits(fatal,child=False):
    def stopped(number,frame):raise Stop('signal '+signal.Signals(number).name)
    for number in (signal.SIGTERM,signal.SIGINT,signal.SIGALRM,signal.SIGXCPU):signal.signal(number,stopped)
    soft=c.LIMITS['child_address_space_bytes'] if child else c.LIMITS['parent_address_space_bytes']
    # Parent hard AS permits exec child to raise its soft AS, without lifting parent's soft bound.
    resource.setrlimit(resource.RLIMIT_AS,(soft,c.LIMITS['child_address_space_bytes']))
    resource.setrlimit(resource.RLIMIT_CPU,(115,120) if child else (7190,7200))
    seconds=(240 if child else 14400)-e.process_wall()
    faulthandler.enable(file=fatal,all_threads=True)
    if seconds<=10:raise Stop('setup consumed wall boundary')
    faulthandler.dump_traceback_later(seconds,repeat=False,file=fatal,exit=True)
    signal.setitimer(signal.ITIMER_REAL,seconds-10)
    return {'address_space':resource.getrlimit(resource.RLIMIT_AS),'cpu':resource.getrlimit(resource.RLIMIT_CPU),
        'core_unchanged':resource.getrlimit(resource.RLIMIT_CORE),'hard_wall_remaining_seconds':seconds,
        'finalization_reserve_seconds':10,'parent_soft_AS_reason':'hard1GiB inherited; parent soft512MiB remains enforced'}


def parent_death(expected):
    libc=ctypes.CDLL(None,use_errno=True)
    if libc.prctl(1,signal.SIGKILL,0,0,0)!=0:raise OSError(ctypes.get_errno(),'PR_SET_PDEATHSIG failed')
    if os.getppid()!=expected['pid'] or e.process_identity(os.getppid())!=expected:
        raise ValueError('parent died or identity changed during death-signal setup')


def verify_context(ctx,payload):
    expected_keys={'schema','stage','shard','source_root','output_root','launch_sha','input_path','input_sha256',
        'parent_identity','parent_cmdline_sha256','admission','context_relative','context_sha_scope','cached_fixed_allocated_bytes',
        'counter_path','producer_artifact','producer_root'}
    if set(ctx)!=expected_keys or ctx['schema']!=1 or ctx['stage']!='reader':
        raise ValueError('exact legal callable-child context required')
    c.shard(ctx['shard']);parent_death(ctx['parent_identity'])
    if (Path(ctx['source_root']).resolve()!=ROOT or ctx['admission']['child_pid']!=os.getppid()
        or ctx['admission']['sha']!=ctx['launch_sha'] or ctx['context_sha_scope']!='exact stdin bytes'):
        raise ValueError('child source/admission identity mismatch')
    if hashlib.sha256(Path(f'/proc/{os.getppid()}/cmdline').read_bytes()).hexdigest()!=ctx['parent_cmdline_sha256']:
        raise ValueError('live parent invocation changed')
    out=Path(ctx['output_root']).resolve(strict=True)
    if c.relative(out,ctx['context_relative']).read_bytes()!=payload:raise ValueError('private stdin/context bytes mismatch')
    launch=json.loads((out/'launch-manifest.json').read_bytes())
    if (launch['sha']!=ctx['launch_sha'] or launch['command_sha256']!=ctx['admission']['command_sha256']
        or launch['runner_process']['identity']['pid']!=ctx['parent_identity']['pid']
        or Path(launch['source_root']).resolve()!=ROOT or Path(launch['output_root']).resolve()!=out
        or launch['node']!='local_linux' or launch['host_identity']!=platform.node()
        or ctx['counter_path']!=str(out/'shared-counters.bin')
        or ctx['context_relative']!=f'raw/process/{ctx["stage"]}/{ctx["shard"]:04d}/context.json'):
        raise ValueError('child durable launch/counter/stage binding mismatch')
    return out


def worker():
    """Private exec callback. No standalone child CLI or unadmitted scientific route."""
    payload=sys.stdin.buffer.read(65537)
    if len(payload)>65536:raise ValueError('oversize legal child context')
    ctx=json.loads(payload);out=verify_context(ctx,payload)
    shared=e.Shared(out/'shared-counters.bin')
    shared.locate(ctx['stage'],ctx['shard']);bill=None;store=None;result=None;error=None;code=2;active=None
    config={'schema':1,'context_sha256':hashlib.sha256(payload).hexdigest(),'child_identity':e.process_identity(os.getpid())}
    process_root=out/f'raw/process/{ctx["stage"]}/{ctx["shard"]:04d}'
    with (process_root/'fatal.log').open('xb',buffering=0) as fatal:
        try:
            active=limits(fatal,child=True);c.guard();thread_env=c.threads()
            value=c.read_bound(ctx['input_path'],ctx['input_sha256']);producer=c.validate(value,ROOT,verify_references=False)
            config.update(runtime=c.runtime(value['runtime']),threads=thread_env,active_limits=active,
                scientific_source_sha=c.SCIENCE_SHA,scientific_input_sha256=c.SCIENCE_INPUT)
            roots=[ROOT,out,value['disk_scope']['producer_root'],value['disk_scope']['reference_root'],value['disk_scope']['own_scratch']]
            bill=e.Budget(shared,roots,[ROOT,value['disk_scope']['producer_root'],value['disk_scope']['reference_root']],child=True,cached_fixed=ctx['cached_fixed_allocated_bytes'])
            store=e.Store(out,bill,ctx['stage'],ctx['shard']);bill.check()
            shared.charge('numpy_import_attempts');c.runtime(value['runtime'],numeric=True);shared.charge('numpy_import_completed')
            shared.charge('native_import_attempts')
            import numpy as np
            from experiments.candidates.typed_joint_skill_decision.b04 import bank
            from experiments.candidates.typed_joint_skill_decision.b04.native import Native
            native=Native(bill);config['imports_before_hosts']=c.guard();shared.charge('native_import_completed')
            e.durable(process_root/'config.json',c.encoded(config));store.register(str((process_root/'config.json').relative_to(out)))
            shared.charge('child_setup_completed')
            old_rng=np.random.default_rng
            def rng(*args,**kwargs):
                bill.charge('rng_streams');answer=old_rng(*args,**kwargs);bill.charge('rng_completed');return answer
            np.random.default_rng=rng
            try:
                with native:
                    old_build=native.p.build_candidates
                    def build(*args,**kwargs):
                        bill.charge('raw_constructions');answer=old_build(*args,**kwargs);bill.charge('raw_completed');return answer
                    native.p.build_candidates=build
                    try:
                        from . import data
                        split,local,worlds=c.shard(ctx['shard']);name=f'raw/bank/{split}/{local:04d}.npz'
                        expected=ctx['producer_artifact']
                        if expected!={'relative':name,**producer['files'][name]} or ctx['producer_root']!=value['producer']['root']:
                            raise ValueError('reader immutable producer artifact/root address mismatch')
                        from experiments.candidates.typed_joint_skill_decision.b05_data_bank.data import load_shard
                        saved=load_shard(c.relative(ctx['producer_root'],name),expected,worlds.start,c.PRODUCER_SHA,c.PRODUCER_INPUT)
                        result=data.rebuild(store,native,bank,saved,value,ROOT)
                    finally:native.p.build_candidates=old_build
            finally:np.random.default_rng=old_rng
            c.guard();bill.check();code=0
        except BaseException as exc:
            error={'type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc()}
        finally:
            signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGXCPU,signal.SIG_IGN)
            imported=c.imports()
            if imported['forbidden_modules']:
                error={'type':'ForbiddenImport','modules':imported['forbidden_modules'],'prior_error':error};code=2
            shared.flush()
            summary={'schema':1,'stage':ctx['stage'],'shard':ctx['shard'],'launch_sha':ctx['launch_sha'],
                'input_sha256':ctx['input_sha256'],'scientific_source_sha':c.SCIENCE_SHA,'scientific_input_sha256':c.SCIENCE_INPUT,
                'status':'complete' if code==0 else 'failed','result':result,'error':error,'config':config,
                'active_limits':active,'imports_after':imported,'bill':bill.snapshot() if bill else {'shared':shared.snapshot(),'cpu':e.cpu(),'wall_seconds':e.process_wall()},
                'retry':False,'counters_vs_records':'observed returned-effect counts are distinct from durable journal records'}
            e.durable(process_root/'summary.json',c.encoded(summary))
            if store:store.register(str((process_root/'summary.json').relative_to(out)))
            shared.close()
    faulthandler.cancel_dump_traceback_later()
    return code


BOOTSTRAP="from experiments.candidates.typed_joint_skill_decision.b07_fixed_bank.run import worker; raise SystemExit(worker())"


def stop_child(child):
    if child.poll() is None:
        child.terminate()
        try:child.wait(timeout=2)
        except subprocess.TimeoutExpired:
            child.kill()
            try:child.wait(timeout=2)
            except subprocess.TimeoutExpired:return None
    return child.returncode


def supervise(child,bill):
    try:
        while child.poll() is None:
            bill.check();time.sleep(.2)
        return child.wait()
    except BaseException:
        stop_child(child);raise


def spawn_case(context,shared,bill):
    out=Path(context['output_root']);directory=out/Path(context['context_relative']).parent
    payload=c.encoded(context);e.durable(out/context['context_relative'],payload)
    shared.charge('spawn_attempts');shared.charge('child_setup_attempts')
    before=shared.snapshot();started=time.perf_counter();error=None;child=None;identity=None
    command=[sys.executable,'-c',BOOTSTRAP]
    env=dict(os.environ);env.update({key:'1' for key in c.THREAD_KEYS});env['PYTHONDONTWRITEBYTECODE']='1'
    env['PYTHONPATH']=str(ROOT)
    with (directory/'stdout.log').open('xb',buffering=0) as stdout,(directory/'stderr.log').open('xb',buffering=0) as stderr:
        try:
            child=subprocess.Popen(command,cwd=ROOT,env=env,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr)
            identity=e.process_identity(child.pid);child.stdin.write(payload);child.stdin.close()
            code=supervise(child,bill)
        except BaseException as exc:
            error={'type':type(exc).__name__,'error':str(exc)}
            code=stop_child(child) if child else None
    if child and child.returncode is not None:shared.charge('spawn_completed')
    shared.flush()
    witness={'schema':1,'command':command,'cwd':str(ROOT),'context_sha256':hashlib.sha256(payload).hexdigest(),
        'child_identity':identity,'exit_code':code,'terminal_status':'reaped' if child and child.returncode is not None else 'unknown',
        'parent_identity':context['parent_identity'],'stage':context['stage'],'shard':context['shard'],
        'wall_seconds':time.perf_counter()-started,'counter_before':before,'counter_after':shared.snapshot(),
        'aggregate_cpu_after_reap':e.cpu(),'error':error,'retry':False}
    e.durable(directory/'process-exit.json',c.encoded(witness))
    if code!=0 or error is not None:raise RuntimeError(f'first child failure: {context["stage"]}/{context["shard"]} exit={code} error={error}')
    summary=json.loads((directory/'summary.json').read_bytes())
    if (summary['status']!='complete' or summary['stage']!=context['stage'] or summary['shard']!=context['shard']
        or summary['launch_sha']!=context['launch_sha'] or summary['input_sha256']!=context['input_sha256']
        or summary['config']['context_sha256']!=witness['context_sha256']
        or summary['config']['child_identity']!=identity or summary['result']['worlds']!=64):
        raise ValueError('complete child witness/summary binding mismatch')
    return summary['result']


def complete_counts(shared,reader_labels):
    counts=shared.snapshot()['counters']
    exact={'setup_attempts':1,'setup_completed':1,'numpy_import_attempts':258,'numpy_import_completed':258,
        'native_import_attempts':258,'native_import_completed':258,'hosts':16512,'hosts_completed':16512,'raw_constructions':16512,'raw_completed':16512,
        'resets':16512,'resets_completed':16512,'child_setup_attempts':258,'child_setup_completed':258,
        'rng_streams':16512,'rng_completed':16512,'reader_worlds_attempted':16512,'reader_worlds_completed':16512,
        'compatibility_attempts':2501,'compatibility_worlds':2501,'compatibility_label_attempts':430980,'compatibility_labels':430980,
        'reader_shards_completed':258,'spawn_attempts':258,'spawn_completed':258,
        'static_calls':c.LABELS,'static_completed':c.LABELS,'refused_effects':0}
    if reader_labels!=c.LABELS or any(counts[k]!=v for k,v in exact.items()):raise ValueError('full B07 reader/old complete denominator mismatch')
    for name in e.NATIVE:
        if name.endswith('_calls') and name[:-6]+'_completed' in counts:
            if counts[name]!=counts[name[:-6]+'_completed']:raise ValueError('internal native attempt/completion mismatch: '+name)
    if counts['reader_check_attempts']!=counts['reader_checks']:raise ValueError('incomplete numeric diagnostics')
    if any(counts[k] for k in ('producer_worlds_attempted','producer_worlds_completed','producer_shards_completed',
        'permutation_reads','permutation_completed','fits','native_steps','model_forwards','gpu_seconds','matching_calls')):
        raise ValueError('forbidden additional effect count')
    return counts


def main(argv=None):
    args=parser().parse_args(argv)
    from scripts.hmasd_admission import require_admission
    admission=dict(require_admission(__file__,direction='typed_joint_skill_decision'))
    out=args.out.resolve(strict=True);launch=json.loads((out/'launch-manifest.json').read_bytes())
    runner_identity=e.process_identity(os.getpid())
    if (launch['sha']!=args.launch_sha or admission['sha']!=args.launch_sha
        or launch['command_sha256']!=admission['command_sha256'] or Path(launch['source_root']).resolve()!=ROOT
        or Path(launch['output_root']).resolve()!=out or launch['node']!='local_linux'
        or launch['host_identity']!=platform.node() or admission['child_pid']!=os.getpid()
        or {key:launch['runner_process']['identity'][key] for key in ('pid','start_ticks')}!=runner_identity or admission['parent_pid']!=os.getppid()
        or launch['process']['identity']['pid']!=admission['parent_pid']
        or launch['direction']!='typed_joint_skill_decision' or admission['direction']!='typed_joint_skill_decision'):
        raise ValueError('durable parent admission/source/output/node binding mismatch')
    if any(p.name not in e.LAUNCH_FILES and not p.name.startswith('.hmasd-launch-') for p in out.iterdir()):
        raise ValueError('output already contains non-launcher evidence')
    shared=e.Shared(out/'shared-counters.bin',create=True);shared.charge('setup_attempts')
    files={};results=[];current=None;bill=None;value=None;error=None;code=2;active=None;failed_records=[]
    with (out/'fatal.log').open('xb',buffering=0) as fatal:
        try:
            active=limits(fatal);c.guard(parent=True);thread_env=c.threads()
            value=c.read_bound(args.input_manifest,args.input_manifest_sha256);producer=c.validate(value,ROOT)
            runtime=c.runtime(value['runtime']);roots=[ROOT,out,value['disk_scope']['producer_root'],value['disk_scope']['reference_root'],value['disk_scope']['own_scratch']]
            bill=e.Budget(shared,roots,[ROOT,value['disk_scope']['producer_root'],value['disk_scope']['reference_root']]);bill.check()
            config={'schema':1,'manifest':value,'input_sha256':args.input_manifest_sha256,'source_root':str(ROOT),
                'output_root':str(out),'launch_sha':args.launch_sha,'admission':admission,'runtime':runtime,'active_limits':active,
                'threads':thread_env,'seed':0,'imports':c.guard(parent=True),'scientific_source_sha':c.SCIENCE_SHA,
                'scientific_input_sha256':c.SCIENCE_INPUT,'producer':value['producer'],'serialization':'unchanged ordinary B05 JSON conversion; no crash-cause claim',
                'counter_schema':list(e.COUNTERS),'process_topology':'fresh exec/stdin callable; no multiprocessing/resource tracker'}
            e.durable(out/'config.json',c.encoded(config));shared.charge('setup_completed')
            stage='reader'
            for index in range(258):
                bill.check();current=(stage,index);split,local,_=c.shard(index)
                name=f'raw/bank/{split}/{local:04d}.npz'
                context={'schema':1,'stage':stage,'shard':index,'source_root':str(ROOT),'output_root':str(out),
                    'launch_sha':args.launch_sha,'input_path':str(args.input_manifest.resolve(strict=True)),
                    'input_sha256':args.input_manifest_sha256,'parent_identity':e.process_identity(os.getpid()),
                    'parent_cmdline_sha256':hashlib.sha256(Path('/proc/self/cmdline').read_bytes()).hexdigest(),
                    'admission':admission,'context_relative':f'raw/process/{stage}/{index:04d}/context.json',
                    'context_sha_scope':'exact stdin bytes','cached_fixed_allocated_bytes':bill.fixed,
                    'counter_path':str(out/'shared-counters.bin'),'producer_root':value['producer']['root'],
                    'producer_artifact':{'relative':name,**producer['files'][name]}}
                result=spawn_case(context,shared,bill);e.merge_child(out,stage,index,files)
                for p in (out/f'raw/process/{stage}/{index:04d}').iterdir():
                    relative=str(p.relative_to(out))
                    if p.is_file() and relative not in files:files[relative]={'sha256':c.sha(p),'bytes':p.stat().st_size}
                results.append({'stage':stage,'index':index,**result})
                e.replace_json(out/'artifact-manifest.json',{'schema':1,'launch_sha':args.launch_sha,'input_sha256':args.input_manifest_sha256,'files':files})
                e.replace_json(out/'progress.json',{'stage':stage,'shard':index,'completed_reader_shards':shared.get('reader_shards_completed'),'bill':bill.snapshot()})
            complete_counts(shared,sum(r['labels'] for r in results));c.guard(parent=True);bill.check();code=0
        except BaseException as exc:
            error={'type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc()}
            if current:
                stage,index=current;e.failure_artifacts(out,stage,index,files)
                witness_path=out/f'raw/process/{stage}/{index:04d}/process-exit.json'
                witness=json.loads(witness_path.read_bytes()) if witness_path.exists() else None
                if witness and witness['terminal_status']=='reaped':
                    split,local,_=c.shard(index);kind='bank' if stage=='producer' else 'label-reader'
                    def deadline():
                        if e.cpu()['total_seconds']>=7198 or e.process_wall()>=14398:raise Stop('failed-journal finalization read allowance exhausted')
                    for p in (out/f'raw/{kind}/{split}').glob(f'{local:04d}*jsonl.gz'):
                        bounds=e.journal_bounds(p,deadline)
                        if bounds['sha256'] is None:bounds['sha256']=files[str(p.relative_to(out))]['sha256']
                        failed_records.append(bounds)
                else:failed_records=[{'status':'unknown','reason':'child not confirmed reaped; no journal reading while a writer might remain'}]
        finally:
            signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGXCPU,signal.SIG_IGN);shared.flush()
            compressed=gzip.compress(c.encoded(results),compresslevel=1,mtime=0)
            summary={'schema':1,'status':c.STATUS if code==0 else 'partial_or_failed','launch_sha':args.launch_sha,
                'input_sha256':args.input_manifest_sha256,'scientific_source_sha':c.SCIENCE_SHA,'scientific_input_sha256':c.SCIENCE_INPUT,
                'error':error,'last_child':current,'completed_producer_shards':shared.get('producer_shards_completed'),
                'failed_child_durable_record_bounds':failed_records,
                'completed_reader_shards':shared.get('reader_shards_completed'),
                'producer_labels':c.LABELS,'producer':value['producer'] if value else None,'original_native_exit_code':2,
                'reader_labels':sum(r['labels'] for r in results if r['stage']=='reader'),
                'label_sum_scope':'confirmed successful-child handoffs only; lower bounds on failure, not total returned or retained labels; see mmap and failed-journal bounds separately',
                'compatibility_worlds':shared.get('compatibility_worlds'),'compatibility_labels':shared.get('compatibility_labels'),
                'shard_readings_artifact':'raw/parent/shards.json.gz','active_limits':active,
                'bill':bill.snapshot() if bill else {'shared':shared.snapshot(),'cpu':e.cpu(),'wall_seconds':e.process_wall()},
                'imports_after':c.imports(parent=True),'retry':False,'old_reference_is_acquisition_progress':False,
                'winner_difference_counts':{pair:sum(r['winner_difference_counts'][pair] for r in results) for pair in ('rebuild_vs_producer','rebuild_vs_original','producer_vs_original')},
                'interpretation':'fixed producer version only; B05 stays exit2/uncertified; no learned/native or runtime-health claim',
                'reference_scope':'2501 complete old worlds/430980 labels compatibility only; old incomplete 109402501 excluded; exact adverse evidence retained',
                'resources':'AS includes library/thread mappings; core reserve is not observed core usage; external support/Git/core measured separately'}
            summary_data=c.encoded(summary)
            if bill:bill.finalization_space(len(summary_data)+len(compressed)+len(c.encoded(files))+65536)
            e.durable(out/'raw/parent/shards.json.gz',compressed)
            files['raw/parent/shards.json.gz']={'sha256':c.sha(out/'raw/parent/shards.json.gz'),'bytes':len(compressed),'content_format':'gzip-json'}
            e.durable(out/'summary.json',summary_data);shared.close()
            for p in (out/'config.json',out/'summary.json',out/'shared-counters.bin',out/'fatal.log',out/'progress.json'):
                if p.exists():files[p.name]={'sha256':c.sha(p),'bytes':p.stat().st_size}
            e.replace_json(out/'artifact-manifest.json',{'schema':1,'launch_sha':args.launch_sha,'input_sha256':args.input_manifest_sha256,'files':files})
    faulthandler.cancel_dump_traceback_later()
    return code


if __name__=='__main__':raise SystemExit(main())
