"""One admitted finite ordinary-data encoder process; no scientific dependencies."""
from __future__ import annotations
import argparse
import contextlib
import faulthandler
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import signal
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[4]
sys.dont_write_bytecode=True
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from experiments.candidates.typed_joint_skill_decision.b04_serialization import records as r

CPU_RESERVE,WALL_RESERVE,OUTPUT_RESERVE=10.,10.,1024**2
PROHIBITED_MODULE_PREFIXES=('numpy','torch','envs','host',
    'experiments.candidates.coupled_host_joint_skills_stage1')


class Stop(Exception):pass
class ByteMismatch(Exception):pass


def module_record():
    names=sorted(sys.modules)
    return {'module_names':names,'prohibited_prefixes':list(PROHIBITED_MODULE_PREFIXES),
        'prohibited_modules':[name for name in names if any(name==prefix or name.startswith(prefix+'.')
            for prefix in PROHIBITED_MODULE_PREFIXES)]}


def require_ordinary_modules(record):
    if record['prohibited_modules']:
        raise ValueError('prohibited imported modules: '+', '.join(record['prohibited_modules']))


@contextlib.contextmanager
def protected():
    """Keep ordinal/counter/digest bookkeeping coherent across soft stop signals."""
    numbers=(signal.SIGXCPU,signal.SIGALRM,signal.SIGTERM,signal.SIGINT)
    previous=signal.pthread_sigmask(signal.SIG_BLOCK,numbers)
    try:yield
    finally:signal.pthread_sigmask(signal.SIG_SETMASK,previous)


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',required=True,type=Path);p.add_argument('--launch-sha',required=True)
    p.add_argument('--seed',required=True,type=int,choices=[0])
    p.add_argument('--node',required=True,choices=['wsl_4070','local_linux'])
    p.add_argument('--input-manifest',required=True,type=Path);p.add_argument('--input-manifest-sha256',required=True)
    return p


def write_json(path,value):
    with Path(path).open('xb') as stream:
        data=r.json_bytes(value)
        if stream.write(data)!=len(data):raise OSError('short metadata write')
        stream.flush();os.fsync(stream.fileno())


class Budget:
    def __init__(self,source,out):
        self.source,self.out=Path(source),Path(out)
        self.source_allocated=r.allocated([source],excluded={self.out.resolve()});self.output_peak=0
        self.last_disk=-float('inf');self.output_allocated=0
        self.wall_birth=time.clock_gettime(time.CLOCK_BOOTTIME)-r.process_wall()
    def check(self):
        if time.process_time()>=300-CPU_RESERVE:raise Stop('cpu_cap_finalization_reserve')
        if time.clock_gettime(time.CLOCK_BOOTTIME)-self.wall_birth>=600-WALL_RESERVE:raise Stop('wall_cap_finalization_reserve')
        now=time.monotonic()
        if now-self.last_disk>=1:
            self.output_allocated=r.allocated([self.out]);self.output_peak=max(self.output_peak,self.output_allocated);self.last_disk=now
        if self.output_allocated+OUTPUT_RESERVE>r.LIMITS['ordinary_output_bytes_per_node']:raise Stop('ordinary_output_cap')
        if self.source_allocated+r.LIMITS['ordinary_output_bytes_per_node']+r.LIMITS['core_reserve_bytes']>r.LIMITS['incremental_disk_bytes']:
            raise Stop('incremental_disk_cap_including_core_reserve')
    def snapshot(self):
        return {'cpu':r.cpu(),'wall_seconds':r.process_wall(),'source_allocated_bytes':self.source_allocated,
            'ordinary_output_peak_allocated_bytes':self.output_peak,'core_reserve_bytes':r.LIMITS['core_reserve_bytes'],
            'ordinary_output_full_reservation_bytes':r.LIMITS['ordinary_output_bytes_per_node'],
            'disk_scope':'one source snapshot + this output + reserved new core; prior retained assets/Git hydration and actual new core measured separately by DM',
            'cpu_finalization_reserve_seconds':CPU_RESERVE,'wall_finalization_reserve_seconds':WALL_RESERVE,
            'ordinary_output_pending_reserve_bytes':OUTPUT_RESERVE}


def arm_limits(fatal):
    def stop_signal(number,frame):raise Stop('signal_'+signal.Signals(number).name)
    for number in (signal.SIGXCPU,signal.SIGALRM,signal.SIGTERM,signal.SIGINT):signal.signal(number,stop_signal)
    resource.setrlimit(resource.RLIMIT_AS,(r.LIMITS['address_space_bytes'],r.LIMITS['address_space_bytes']))
    resource.setrlimit(resource.RLIMIT_CPU,(290,300))
    # Keep the pre-existing core setting; the node's core-pattern pipeline is external.
    faulthandler.enable(file=fatal,all_threads=True)
    remaining=600-r.process_wall()
    if remaining<=WALL_RESERVE:raise Stop('wall_cap_during_setup')
    faulthandler.dump_traceback_later(remaining,repeat=False,file=fatal,exit=True)
    signal.setitimer(signal.ITIMER_REAL,remaining-WALL_RESERVE)
    return {'address_space':resource.getrlimit(resource.RLIMIT_AS),'cpu':resource.getrlimit(resource.RLIMIT_CPU),
            'core_unchanged':resource.getrlimit(resource.RLIMIT_CORE),'hard_wall_faulthandler_exit_seconds':remaining}


def replay(lines,encoder,attempts,checkpoints,guard,state):
    """Fixed chronology; state is updated only after an exact byte comparison."""
    for cycle in range(1000):
        for row,line in enumerate(lines):
            guard()
            ordinal=cycle*len(lines)+row+1
            with protected():
                if attempts.write(r.ORDINAL.pack(ordinal))!=8:raise OSError('short unbuffered attempt-ordinal write')
                state['attempted']=ordinal
            decoded=json.loads(line)  # A fresh ordinary object for EVERY attempt.
            encoded=encoder(decoded)
            if encoded!=line:
                state['mismatch']={'ordinal':ordinal,'row':row,'cycle':cycle,'expected_bytes':len(line),
                    'actual_bytes':len(encoded),'expected_sha256':hashlib.sha256(line).hexdigest(),
                    'actual_sha256':hashlib.sha256(encoded).hexdigest()}
                raise ByteMismatch('exact original line bytes including newline differ')
            with protected():
                state['rolling'].update(encoded);state['completed']+=1;state['encoded_bytes']+=len(encoded)
        checkpoint(checkpoints,state,len(lines))
    return 'cycles'


def checkpoint(stream,state,row_count):
    with protected():
        r.append_json(stream,{'attempted':state['attempted'],'completed':state['completed'],
            'encoded_bytes':state['encoded_bytes'],'rolling_sha256':state['rolling'].hexdigest(),
            'cycles_complete':state['completed']//row_count,'cpu':r.cpu(),'wall_seconds':r.process_wall()})


def main(argv=None):
    args=parser().parse_args(argv)
    from scripts.hmasd_admission import require_admission
    admission=dict(require_admission(__file__,direction='typed_joint_skill_decision'))
    source,out=ROOT,args.out.resolve(strict=True)
    launch=json.loads((out/'launch-manifest.json').read_bytes())
    if (args.launch_sha!=admission['sha']
        or launch['sha']!=args.launch_sha or launch['command_sha256']!=admission['command_sha256']
        or Path(launch['source_root']).resolve()!=source or Path(launch['output_root']).resolve()!=out
        or launch['node']!=args.node or launch['direction']!='typed_joint_skill_decision'):
        raise ValueError('exact admitted source/output/node identity required')
    if any(p.name not in r.LAUNCH_FILES and not p.name.startswith('.hmasd-launch-') for p in out.iterdir()):
        raise ValueError('output already holds non-launcher evidence')
    budget=None
    state={'attempted':0,'completed':0,'encoded_bytes':0,'rolling':hashlib.sha256()}
    stop='setup_failure';error=None;exit_code=2;modules_before=None;modules_after=None
    with (out/'fatal.log').open('xb',buffering=0) as fatal,(out/'attempts.bin').open('xb',buffering=0) as attempts,\
         (out/'checkpoints.jsonl').open('xb',buffering=0) as checkpoints:
        try:
            active=arm_limits(fatal)
            value=r.manifest(args.input_manifest,args.input_manifest_sha256)
            runtime={'executable_realpath':str(Path(sys.executable).resolve(strict=True)),
                'executable_sha256':r.sha(Path(sys.executable).resolve(strict=True)),'python_version':platform.python_version(),
                'hostname':platform.node()}
            if runtime!=value['nodes'][args.node] or runtime['hostname']!=launch['host_identity']:
                raise ValueError('actual executable/hash/version/node mismatch')
            budget=Budget(source,out)
            write_json(out/'config.json',{'schema':1,'launch_sha':args.launch_sha,'command_sha256':admission['command_sha256'],
                'manifest_sha256':args.input_manifest_sha256,'manifest':value,'node':args.node,'runtime':runtime,
                'admission':admission,'source_root':str(source),'output_root':str(out),'seed':0,
                'setup_budget':budget.snapshot(),'target_import_after_admission':True})
            budget.check()
            lines=r.input_lines(source,value['input']);budget.check()
            modules_before=module_record();require_ordinary_modules(modules_before)
            encoder=r.target(source,value['target']);budget.check()
            stop=replay(lines,encoder,attempts,checkpoints,budget.check,state);exit_code=0
        except Stop as exc:
            stop=str(exc);exit_code=0
        except BaseException as exc:
            stop='byte_mismatch' if isinstance(exc,ByteMismatch) else 'exception'
            error={'type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc()}
        finally:
            signal.setitimer(signal.ITIMER_REAL,0)
            signal.signal(signal.SIGXCPU,signal.SIG_IGN)
            modules_after=module_record()
            try:require_ordinary_modules(modules_after)
            except ValueError as exc:
                error={'type':type(exc).__name__,'error':str(exc),'prior_error':error}
                stop='prohibited_import';exit_code=2
            checkpoint(checkpoints,state,1025)
            summary={'schema':1,'stop':stop,'attempted':state['attempted'],'completed':state['completed'],
                'encoded_bytes':state['encoded_bytes'],'rolling_sha256':state['rolling'].hexdigest(),
                'cycles_complete':state['completed']//1025,'requested_cycles':1000,'error':error,
                'mismatch':state.get('mismatch'),'budget':budget.snapshot() if budget else
                    {'cpu':r.cpu(),'wall_seconds':r.process_wall(),'source_or_output_allocation':'unknown setup failure'},'retry':False,
                'active_limits':locals().get('active'),'startup_or_setup_included_in_process_cpu':True,
                'modules_before_target_import':modules_before,'modules_after_last_call':modules_after,
                'attempt_scope':'ordinal emitted before fresh decode/encode; interrupted decode does not prove encoder invocation',
                'completion_scope':'durably recorded comparison-returned completions; an uncommitted final attempt remains uncertain; caps are partial, not a fixed-count pass'}
            write_json(out/'summary.json',summary)
    faulthandler.cancel_dump_traceback_later()  # Hard wall watchdog remains armed through all output closure.
    return exit_code


if __name__=='__main__':raise SystemExit(main())
