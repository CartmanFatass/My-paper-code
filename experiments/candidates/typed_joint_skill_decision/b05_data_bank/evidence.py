"""B05 shared crash-visible counters and bounded exclusive data evidence."""
from __future__ import annotations
import gzip
import hashlib
import json
import mmap
import os
from pathlib import Path
import resource
import struct
import time
import zlib
from . import contract as c

NATIVE=('static_calls','static_completed','native_steps','native_completed','fits','fits_completed',
 'hosts','hosts_completed','resets','resets_completed','radio_refresh_calls','radio_refresh_completed',
 'reward_calls','reward_completed','routing_calls','routing_completed','link_update_calls','link_update_completed',
 'frontend_capacity_calls','frontend_capacity_completed','path_loss_matrix_calls','path_loss_matrix_completed',
 'scalar_sinr_calls','scalar_sinr_completed','matching_calls','matching_completed','reader_state_checks',
 'audit_episodes','main_episodes','spawn_attempts','spawn_completed')
COUNTERS=NATIVE+('model_forwards','gpu_seconds','raw_constructions','raw_completed','rng_streams','rng_completed',
 'setup_attempts','setup_completed','child_setup_attempts','child_setup_completed','numpy_import_attempts','numpy_import_completed',
 'native_import_attempts','native_import_completed','producer_worlds_attempted','producer_worlds_completed',
 'reader_worlds_attempted','reader_worlds_completed','compatibility_attempts','compatibility_worlds','compatibility_label_attempts','compatibility_labels','permutation_reads','permutation_completed',
 'producer_shards_completed','reader_shards_completed','reader_check_attempts','reader_checks','resource_checks','parent_resource_checks','refused_effects')
CAPS={k:c.LIMITS[k] for k in ('static_calls','hosts','raw_constructions','fits','native_steps','model_forwards','gpu_seconds')}
CAPS.update(matching_calls=0,audit_episodes=0,main_episodes=0,rng_streams=33024)
LAUNCH_FILES={'launch-manifest.json','launch-status.json','status.json','stdout.log','stderr.log','admission-preflight.json'}
Q=struct.Struct('<Q');CONTEXT=('stage','shard','world','candidate');BLOCK_BYTES=8*(len(COUNTERS)+len(CONTEXT))
INDEX={name:i for i,name in enumerate(COUNTERS)}


def process_identity(pid):
    text=Path(f'/proc/{pid}/stat').read_text();fields=text.rsplit(')',1)[1].split()
    return {'pid':pid,'start_ticks':int(fields[19])}


def process_wall():
    return time.clock_gettime(time.CLOCK_BOOTTIME)-process_identity(os.getpid())['start_ticks']/os.sysconf('SC_CLK_TCK')


def cpu():
    """Parent self + already-reaped + all live direct children, without overlap."""
    own=resource.getrusage(resource.RUSAGE_SELF);before=resource.getrusage(resource.RUSAGE_CHILDREN)
    children=Path(f'/proc/{os.getpid()}/task/{os.getpid()}/children')
    live=[];unknown=[];seconds=0.
    for word in children.read_text().split() if children.exists() else []:
        pid=int(word)
        try:
            fields=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
            identity={'pid':pid,'start_ticks':int(fields[19])}
            amount=(int(fields[11])+int(fields[12]))/os.sysconf('SC_CLK_TCK')
            live.append({**identity,'cpu_seconds':amount});seconds+=amount
        except FileNotFoundError:unknown.append(pid)
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    if (before.ru_utime,before.ru_stime)!=(after.ru_utime,after.ru_stime):
        # One child can be reaped during sampling. Its CPU is now solely in RUSAGE_CHILDREN.
        live=[];seconds=0.;unknown=[]
    total=own.ru_utime+own.ru_stime+after.ru_utime+after.ru_stime+seconds
    return {'self_seconds':own.ru_utime+own.ru_stime,'reaped_children_seconds':after.ru_utime+after.ru_stime,
        'live_children':live,'unmeasured_live_pids':unknown,'total_seconds':total,
        'self_peak_rss_kib':own.ru_maxrss,'children_max_peak_rss_kib':after.ru_maxrss,
        'scope':'self + direct live + reaped once; separate process RSS maxima, not a simultaneous sum'}


def allocated(roots,seen=None):
    seen=set() if seen is None else seen;total=0
    for root in roots:
        if not Path(root).exists():continue
        for directory,dirs,files in os.walk(root,followlinks=False):
            dirs[:]=[d for d in dirs if not (Path(directory)/d).is_symlink()]
            for p in [Path(directory),*[Path(directory)/f for f in files]]:
                try:s=p.lstat()
                except FileNotFoundError:continue
                key=(s.st_dev,s.st_ino)
                if key not in seen:seen.add(key);total+=s.st_blocks*512
    return total


class Shared:
    """One active writer, aligned 64-bit counters on the declared 64-bit Linux node."""
    def __init__(self,path,create=False):
        self.path=Path(path);self.file=self.path.open('x+b' if create else 'r+b',buffering=0)
        if create:self.file.truncate(BLOCK_BYTES)
        if self.path.stat().st_size!=BLOCK_BYTES:raise ValueError('shared counter schema mismatch')
        self.buffer=mmap.mmap(self.file.fileno(),BLOCK_BYTES)
    def get(self,name):return Q.unpack_from(self.buffer,8*INDEX[name])[0]
    def charge(self,name,n=1):
        if type(n) is not int or n<0:raise ValueError('nonnegative integer counter charge')
        current=self.get(name)
        if name in CAPS and current+n>CAPS[name]:
            Q.pack_into(self.buffer,8*INDEX['refused_effects'],self.get('refused_effects')+1)
            raise RuntimeError('B05 hard effect cap before invocation: '+name)
        Q.pack_into(self.buffer,8*INDEX[name],current+n)
    def locate(self,stage,shard,world=0,candidate=0):
        for i,v in enumerate((1 if stage=='producer' else 2,shard,world,candidate)):
            Q.pack_into(self.buffer,8*(len(COUNTERS)+i),v)
    def snapshot(self):
        return {'counters':{name:self.get(name) for name in COUNTERS},
            'last_observed_context':{name:Q.unpack_from(self.buffer,8*(len(COUNTERS)+i))[0] for i,name in enumerate(CONTEXT)},
            'semantics':'attempt before effect; observed completion is a lower bound on returned calls, attempt count is an upper bound after confirmed reap (return-to-counter gap possible); mmap counts are separate from durable label records; context fields may be partially updated at a crash'}
    def flush(self):self.buffer.flush();os.fsync(self.file.fileno())
    def close(self):self.flush();self.buffer.close();self.file.close()


class Budget:
    def __init__(self,shared,roots,immutable,child=False,cached_fixed=None):
        self.shared,self.child=shared,child
        self.roots=[str(Path(p).resolve()) for p in roots];self.frozen=set()
        self.fixed=allocated(immutable,self.frozen) if cached_fixed is None else cached_fixed
        self.mutable=[p for p in self.roots if str(Path(p).resolve()) not in {str(Path(q).resolve()) for q in immutable}]
        self.disk_peak=self.fixed;self.last=-float('inf');self.pending=0
    def charge(self,name,n=1):
        self.shared.charge(name,n)
        if name=='static_calls' and self.shared.get(name)%100==0:self.check(sample_disk=False)
    def counter_snapshot(self):return self.shared.snapshot()['counters']
    def check(self,pending=0,sample_disk=True):
        self.shared.charge('resource_checks' if self.child else 'parent_resource_checks')
        usage=cpu();wall=process_wall()
        cpu_limit=115 if self.child else c.LIMITS['cpu_seconds']-10
        wall_limit=230 if self.child else c.LIMITS['wall_seconds']-10
        if usage['unmeasured_live_pids']:raise RuntimeError('live child CPU unmeasured; no zero substitution')
        if usage['total_seconds']>=cpu_limit or wall>=wall_limit:raise RuntimeError('B05 finite CPU/wall boundary')
        now=time.monotonic()
        if sample_disk and (now-self.last>=2 or self.pending+pending>=8*1024**2):
            self.disk_peak=max(self.disk_peak,self.fixed+allocated(self.mutable,set(self.frozen)));self.last=now;self.pending=0
        if self.disk_peak+self.pending+pending+2*1024**2>c.LIMITS['normal_disk_bytes']:raise RuntimeError('B05 normal scoped disk boundary')
        self.pending+=pending
    def snapshot(self):
        return {**self.shared.snapshot(),'cpu':cpu(),'wall_seconds':process_wall(),'disk_peak_allocated_bytes':self.disk_peak,
            'roots':self.roots,'immutable_allocated_bytes':self.fixed,'core_reserve_bytes':c.LIMITS['core_reserve_bytes'],
            'core_scope':'reserve only; existing/new external pipeline core and Git hydration metered separately by DM; core limits unchanged',
            'support':'unmetered external preparation/reading unknown, not zero','limits':c.LIMITS}
    def finalization_space(self,amount):
        # Reserve exact encoded metadata during closure without reopening a spent CPU allowance.
        actual=self.fixed+allocated(self.mutable,set(self.frozen));self.disk_peak=max(self.disk_peak,actual)
        if actual+amount+65536>c.LIMITS['normal_disk_bytes']:raise RuntimeError('final metadata exceeds normal scoped disk cap')


def durable(path,data):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as stream:
        if stream.write(data)!=len(data):raise OSError('short evidence write')
        stream.flush();os.fsync(stream.fileno())


def replace_json(path,value):
    p=Path(path);temporary=p.with_name(p.name+'.next')
    durable(temporary,c.encoded(value));os.replace(temporary,p)


class Store:
    """Only this serial child's manifest is mutable; parent merges verified entries."""
    def __init__(self,root,bill,stage,index):
        self.root,self.bill,self.stage,self.index=Path(root),bill,stage,index
        self.process_relative=f'raw/process/{stage}/{index:04d}';self.files={}
        split,local,_=c.shard(index)
        self.data_prefix=f'raw/{"bank" if stage=="producer" else "label-reader"}/{split}/{local:04d}'
    def allowed(self,name):
        if not (name.startswith(self.process_relative+'/') or name.startswith(self.data_prefix+'.')
            or name.startswith(self.data_prefix+'-') or (self.stage=='reader' and self.index==0 and name=='raw/engineering/static-permutations.json.gz')):
            raise ValueError('artifact outside exclusive child ownership')
        return c.relative(self.root,name)
    def register(self,name,**metadata):
        p=self.allowed(name);self.files[name]={'sha256':c.sha(p),'bytes':p.stat().st_size,**metadata}
        replace_json(self.root/self.process_relative/'artifact-manifest.json',{'schema':1,'stage':self.stage,'shard':self.index,'files':self.files})
    def write(self,name,value):
        data=c.encoded(value);self.bill.check(pending=len(data)+65536);durable(self.allowed(name),data);self.register(name)
    def gzip(self,name,value):
        data=c.encoded(value);compressed=gzip.compress(data,compresslevel=1,mtime=0)
        self.bill.check(pending=len(compressed)+65536);durable(self.allowed(name),compressed)
        self.register(name,content_format='gzip-json',uncompressed_bytes=len(data))
    def snapshot(self):return self.bill.snapshot()


class Trace:
    def __init__(self,path,bill,diagnostics=False):
        self.path,self.bill=Path(path),bill;bill.check(pending=1024**2)
        self.path.parent.mkdir(parents=True,exist_ok=True);self.file=self.path.open('xb',buffering=0)
        self.stream=gzip.GzipFile(filename='',mode='wb',fileobj=self.file,compresslevel=1,mtime=0)
        self.rows=0;self.format_seconds=self.write_seconds=0.;self.diagnostics=diagnostics
    def write(self,row):
        if self.diagnostics:self.bill.charge('reader_check_attempts')
        started=time.perf_counter()
        try:data=c.encoded(row)
        except (TypeError,ValueError) as exc:
            self.stream.write(c.encoded({'type':'serialization_failure','row_repr':repr(row),'error':str(exc)}));self.stream.flush()
            raise
        self.format_seconds+=time.perf_counter()-started
        if len(data)>1024**2:self.bill.check(pending=len(data)+1024**2)
        started=time.perf_counter();self.stream.write(data);self.rows+=1
        if self.diagnostics:self.bill.charge('reader_checks')
        if self.rows%25==0:
            self.stream.flush();self.bill.check(pending=1024**2)
        self.write_seconds+=time.perf_counter()-started
    def close(self):
        self.stream.close();self.file.flush();os.fsync(self.file.fileno());self.file.close()
    def timing(self):return {'rows':self.rows,'format_wall_seconds':self.format_seconds,'write_compress_wall_seconds':self.write_seconds}


def merge_child(root,stage,index,files):
    relative=f'raw/process/{stage}/{index:04d}/artifact-manifest.json';p=c.relative(root,relative)
    child=json.loads(p.read_bytes())
    if child['stage']!=stage or child['shard']!=index:raise ValueError('child artifact handoff identity')
    for name,expected in child['files'].items():
        c.verify_file(c.relative(root,name),expected)
        if name in files:raise ValueError('child attempted to replace earlier evidence')
        files[name]=expected
    files[relative]={'sha256':c.sha(p),'bytes':p.stat().st_size}


def failure_artifacts(root,stage,index,files):
    split,local,_=c.shard(index);roots=[Path(root)/f'raw/process/{stage}/{index:04d}']
    dirname='bank' if stage=='producer' else 'label-reader'
    roots.extend((Path(root)/f'raw/{dirname}/{split}').glob(f'{local:04d}*'))
    for p in roots:
        items=p.rglob('*') if p.is_dir() else [p]
        for item in items:
            if item.is_file():files[str(item.relative_to(root))]={'sha256':c.sha(item),'bytes':item.stat().st_size,'partial_or_failed':True}


def journal_bounds(path,deadline=None):
    """Streaming prefix inspection only; no footer repair, label fill or target encoding."""
    path=Path(path);decoder=zlib.decompressobj(31);buffer=b'';rows=labels=0;worlds={};last=None;error=None;source=set()
    tail=0;total=0;digest=hashlib.sha256()
    def row(line):
        nonlocal rows,labels,last
        value=json.loads(line);rows+=1
        if value.get('type')=='prepared':
            world=value['identity']['world'];entry=worlds.setdefault(world,{'M':None,'raw_indices':[]})
            entry['M']=len(value['features']['layouts_xyz']);source.add((value['source_sha'],value['input_sha256']))
        elif 'raw_index' in value and 'info' in value:
            world=value['world'];index=value['raw_index'];entry=worlds.setdefault(world,{'M':None,'raw_indices':[]})
            entry['raw_indices'].append(index);labels+=1;last={'world':world,'raw_index':index}
    try:
        with path.open('rb') as stream:
            for chunk in iter(lambda:stream.read(65536),b''):
                if deadline:deadline()
                digest.update(chunk);pending=chunk
                while pending:
                    data=decoder.decompress(pending,1024**2);pending=decoder.unconsumed_tail
                    total+=len(data);buffer+=data
                    if len(buffer)>2*1024**2 and b'\n' not in buffer:raise ValueError('oversize journal JSON row')
                    while b'\n' in buffer:
                        line,buffer=buffer.split(b'\n',1);row(line)
                    if decoder.unused_data:raise ValueError('unexpected bytes after gzip member')
        tail=len(buffer)
    except BaseException as exc:
        error={'type':type(exc).__name__,'error':str(exc)};tail=len(buffer)
    complete=[];counts=[]
    for world,entry in worlds.items():
        ordered=entry['raw_indices']==list(range(len(entry['raw_indices'])))
        if entry['M'] is not None and ordered and len(entry['raw_indices'])==entry['M']:complete.append(world)
        counts.append({'world':world,'M_from_prepared':entry['M'],'retained_label_rows':len(entry['raw_indices']),
            'raw_indices':entry['raw_indices'],'ordered_from_zero':ordered})
    return {'path':str(path),'sha256':c.sha(path) if error is None else None,'bytes':path.stat().st_size,
        'complete_json_rows':rows,'retained_label_rows':labels,'worlds':counts,'complete_producer_worlds':complete,
        'last_complete_producer_world':complete[-1] if complete else None,'last_complete_label':last,
        'gzip_eof':decoder.eof,'decompressed_bytes_seen':total,'unparsed_decompressed_tail_bytes':tail,
        'parse_or_resource_error':error,'source_identities':sorted(source),
        'scope':'durable complete newline rows only; no footer/tail repair, physical query or encoding replay; bounded read can leave later record bounds unknown'}
