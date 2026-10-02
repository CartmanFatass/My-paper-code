"""Bound bytes and recorded completion reconstruction; never re-encode a row."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import struct
import time
import zlib

TARGET={'path':'experiments/candidates/typed_joint_skill_decision/b04/evidence.py',
        'sha256':'74c197cf2ab1db82e8899ba9ad4c7c04d0decc93476731eefb4161bc21f10583','function':'encoded'}
INPUT={'path':'docs/research/candidates/typed_joint_skill_decision/b04_serialization/0039-partial.jsonl.gz',
       'sha256':'a6dd341a5c827b78d69b3f2bdbeef97e4ef361f38c596356e54a7a205c35c282','bytes':116876,
       'complete_rows':1025,'complete_bytes':1056813,
       'complete_sha256':'f64bf50d0102cde03e0dd594adda924db263348785cc11060f7770e56f67a409','gzip_eof':False}
LIMITS={'cycles':1000,'cpu_seconds':300,'wall_seconds':600,'address_space_bytes':536870912,
        'incremental_disk_bytes':3221225472,'core_reserve_bytes':1073741824,'ordinary_output_bytes_per_node':16777216}
ORDINAL=struct.Struct('>Q')
LAUNCH_FILES={'launch-manifest.json','launch-status.json','status.json','stdout.log','stderr.log','admission-preflight.json'}


def json_bytes(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('ascii')


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024**2),b''):digest.update(block)
    return digest.hexdigest()


def contained(root,relative):
    path=Path(relative)
    if path.is_absolute() or '..' in path.parts:raise ValueError('relative contained source path required')
    result=(Path(root)/path).resolve(strict=True)
    if Path(root).resolve() not in result.parents:raise ValueError('source path escaped root')
    return result


def manifest(path,digest):
    if sha(path)!=digest:raise ValueError('manifest SHA256 mismatch')
    value=json.loads(Path(path).read_bytes())
    if (set(value)!={'schema','direction','study','input','target','limits','nodes'} or value['schema']!=1
        or value['direction']!='typed_joint_skill_decision' or value['study']!='b04_ordinary_json_serialization'
        or value['input']!=INPUT or value['target']!=TARGET or value['limits']!=LIMITS
        or set(value['nodes'])!={'local_linux','wsl_4070'}):
        raise ValueError('fixed serialization contract mismatch')
    expected={'local_linux':('3.10.20','3303d2b5dc566818e412d2b5b6cd8e792bd360865da47593429a635f72668226'),
              'wsl_4070':('3.10.21','039033f129d33a69044ceff71ca87b109ad99d511b59946f81ffc3f728b1a3a1')}
    for node,entry in value['nodes'].items():
        if (set(entry)!={'executable_realpath','executable_sha256','python_version','hostname'}
            or (entry['python_version'],entry['executable_sha256'])!=expected[node]
            or not Path(entry['executable_realpath']).is_absolute() or not entry['hostname']):
            raise ValueError('fixed node/executable contract mismatch')
    return value


def input_lines(root,descriptor):
    path=contained(root,descriptor['path'])
    if path.stat().st_size!=descriptor['bytes'] or sha(path)!=descriptor['sha256']:
        raise ValueError('original compressed input identity mismatch')
    decoder=zlib.decompressobj(wbits=31)
    data=decoder.decompress(path.read_bytes(),descriptor['complete_bytes']+1)
    if (len(data)!=descriptor['complete_bytes'] or hashlib.sha256(data).hexdigest()!=descriptor['complete_sha256']
        or decoder.eof!=descriptor['gzip_eof'] or decoder.unconsumed_tail or decoder.unused_data):
        raise ValueError('complete unclosed-gzip prefix mismatch')
    lines=data.splitlines(keepends=True)
    if len(lines)!=descriptor['complete_rows'] or any(not line.endswith(b'\n') for line in lines):
        raise ValueError('original complete chronological lines required')
    return lines


def target(root,descriptor):
    path=contained(root,descriptor['path'])
    if descriptor!=TARGET or sha(path)!=descriptor['sha256']:
        raise ValueError('unchanged target source SHA256 mismatch')
    spec=importlib.util.spec_from_file_location('_hmasd_b04_bound_evidence',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.encoded


def cpu():
    own=resource.getrusage(resource.RUSAGE_SELF);child=resource.getrusage(resource.RUSAGE_CHILDREN)
    return {'process_seconds':own.ru_utime+own.ru_stime,'process_user_seconds':own.ru_utime,
            'process_system_seconds':own.ru_stime,'setup_admission_children_seconds':child.ru_utime+child.ru_stime,
            'max_rss_kib':own.ru_maxrss,'child_scope':'admission/setup subprocess overhead separate; no scientific subprocess'}


def process_wall():
    fields=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()
    return time.clock_gettime(time.CLOCK_BOOTTIME)-int(fields[19])/os.sysconf('SC_CLK_TCK')


def allocated(roots,excluded=()):
    seen=set();total=0
    for root in roots:
        for directory,dirs,files in os.walk(root,followlinks=False):
            dirs[:]=[d for d in dirs if not (Path(directory)/d).is_symlink()
                     and (Path(directory)/d).resolve() not in excluded]
            for path in [Path(directory),*[Path(directory)/f for f in files]]:
                try:s=path.lstat()
                except FileNotFoundError:continue
                key=(s.st_dev,s.st_ino)
                if key not in seen:total+=s.st_blocks*512;seen.add(key)
    return total


def append_json(stream,value):
    data=json_bytes(value)
    if stream.write(data)!=len(data):raise OSError('short checkpoint write')
    os.fsync(stream.fileno())


def terminal_witness(out,launch):
    path=Path(out)/'process-exit.json'
    if not path.exists():return None
    value=json.loads(path.read_bytes())
    if (value['status']!='exited' or type(value['exit_code']) is not int
        or value['process_identity']!=launch['runner_process']['identity']
        or value['supervisor_identity']!=launch['process']['identity']):
        raise ValueError('terminal native witness mismatch')
    return value


def read_records(out,value,source_root,manifest_sha256):
    """Reconstruct byte/digest completion from records and native terminal identity."""
    out=Path(out);lines=input_lines(source_root,value['input'])
    if sha(contained(source_root,value['target']['path']))!=value['target']['sha256']:
        raise ValueError('reader target source binding mismatch')
    launch=json.loads((out/'launch-manifest.json').read_bytes())
    if (launch['node'] not in value['nodes'] or launch['direction']!=value['direction']
        or launch['host_identity']!=value['nodes'][launch['node']]['hostname']):
        raise ValueError('launcher node binding mismatch')
    witness=terminal_witness(out,launch)
    if not (out/'config.json').exists():
        return {'status':'setup_record_missing','node':launch['node'],'source_sha':launch['sha'],
                'attempted_ordinals':None,'completed_lower_bound':0,'completed_upper_bound':None,
                'terminal_exit_code':None if witness is None else witness['exit_code'],
                'trust':'setup/admission/identity failure may precede config; missing records are unknown, not a completed replay',
                'present_record_files':[p.name for p in out.iterdir() if p.is_file()],'reader_cpu':cpu()}
    config=json.loads((out/'config.json').read_bytes())
    if (config['manifest']!=value or config['manifest_sha256']!=manifest_sha256 or config['launch_sha']!=launch['sha']
        or config['command_sha256']!=launch['command_sha256'] or config['node']!=launch['node']
        or config['admission']['sha']!=launch['sha'] or config['admission']['command_sha256']!=launch['command_sha256']
        or config['admission']['child_pid']!=launch['runner_process']['identity']['pid']
        or config['source_root']!=launch['source_root'] or config['output_root']!=launch['output_root']
        or launch['host_identity']!=value['nodes'][config['node']]['hostname']
        or config['runtime']!=value['nodes'][config['node']]):raise ValueError('record source/node/manifest binding mismatch')
    data=(out/'attempts.bin').read_bytes();partial_bytes=len(data)%8
    attempted=len(data)//8
    if attempted>1025*1000:raise ValueError('attempt ceiling exceeded')
    for i in range(attempted):
        if ORDINAL.unpack_from(data,i*8)[0]!=i+1:raise ValueError('attempt ordinal stream changed/reordered')
    rows=[];incomplete_checkpoint_tail=False
    for line in (out/'checkpoints.jsonl').read_bytes().splitlines(keepends=True):
        if not line.endswith(b'\n'):
            incomplete_checkpoint_tail=True;break
        rows.append(json.loads(line))
    rolling=hashlib.sha256();completed=0;encoded_bytes=0
    for row in rows:
        n=row['completed']
        if (type(n) is not int or not completed<=n<=attempted or row['attempted']>attempted
            or row['attempted']<n or row['attempted']>n+1):raise ValueError('checkpoint counter inconsistency')
        for i in range(completed,n):
            line=lines[i%len(lines)];rolling.update(line);encoded_bytes+=len(line)
        completed=n
        if (rolling.hexdigest()!=row['rolling_sha256'] or encoded_bytes!=row['encoded_bytes']
            or row['cycles_complete']!=n//1025):raise ValueError('checkpoint byte/digest inconsistency')
    summary=None
    if (out/'summary.json').exists():
        summary=json.loads((out/'summary.json').read_bytes())
        if not rows or any(summary[k]!=rows[-1][k] for k in ('completed','attempted','encoded_bytes','rolling_sha256','cycles_complete')):
            raise ValueError('summary/final checkpoint mismatch')
        if summary['attempted']!=attempted or partial_bytes:raise ValueError('summary/attempt stream mismatch')
    if summary and summary.get('active_limits') is not None:
        active=summary['active_limits']
        if active['address_space']!=[536870912,536870912] or active['cpu']!=[290,300]:
            raise ValueError('recorded active resource limits mismatch')
    full=bool(summary and summary.get('active_limits') is not None and witness and witness['exit_code']==0 and summary['stop']=='cycles'
              and completed==1025000 and attempted==completed and not incomplete_checkpoint_tail)
    return {'node':config['node'],'source_sha':config['launch_sha'],'status':'fixed_count_pass' if full else 'partial_or_failed',
            'attempted_ordinals':attempted,'last_attempted_ordinal':attempted or None,
            'completed_lower_bound':completed,'completed_upper_bound':attempted,
            'completion_scope':'lower bound is durably recorded comparison-returned completions; an uncommitted final attempt remains uncertain even with a summary',
            'encoded_bytes_lower_bound':encoded_bytes,'rolling_sha256_at_completed_lower_bound':rolling.hexdigest(),
            'checkpoint_count':len(rows),'attempt_tail_bytes':partial_bytes,'incomplete_checkpoint_tail':incomplete_checkpoint_tail,
            'worker_stop':None if summary is None else summary['stop'],'terminal_exit_code':None if witness is None else witness['exit_code'],
            'worker_budget':None if summary is None else summary['budget'],
            'attempt_scope':'ordinal emitted before fresh decode/encode; interrupted decode does not prove encoder invocation',
            'trust':'checks bound original bytes, recorded byte comparisons/digests and terminal witnesses; zero target-encoding replay; attempted location is not fault-object proof',
            'interpretation':'bounded ordinary-data observation; does not replay prior heap history or certify runtime/scientific suitability',
            'record_sha256':{p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name in
                              {'config.json','attempts.bin','checkpoints.jsonl','summary.json','process-exit.json','launch-manifest.json','fatal.log'}},
            'reader_cpu':cpu()}
