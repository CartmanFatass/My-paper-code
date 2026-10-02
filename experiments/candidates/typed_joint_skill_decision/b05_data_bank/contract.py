"""Fixed B05 addresses, source/input contract and data-only import boundary."""
from __future__ import annotations
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys

SCIENCE_SHA='b19508a5c2825359e66a36b4fdc1db68b60cc809'
SCIENCE_INPUT='000588aa756405e25e9e3dbebec99b95927277b6a85ee38275947f322f4a12a3'
WORLDS={'train_start':109400000,'train_count':16000,'fresh_start':109420000,'fresh_count':512,'shard_worlds':64}
LIMITS={'static_calls':7298320,'hosts':33028,'raw_constructions':33024,'cpu_seconds':14400,'wall_seconds':28800,
 'child_cpu_seconds':120,'child_wall_seconds':240,'parent_address_space_bytes':536870912,'child_address_space_bytes':1073741824,
 'normal_disk_bytes':5368709120,'core_reserve_bytes':2147483648,'fits':0,'native_steps':0,'model_forwards':0,'gpu_seconds':0}
SOURCE_KEYS={f'experiments/candidates/typed_joint_skill_decision/b04/{s}.py' for s in ('__init__','bank','native','contract','evidence')}
SOURCE_KEYS|={f'experiments/candidates/coupled_host_joint_skills_stage1/{s}.py' for s in ('host','planner','menus','run_gate')}
SOURCE_KEYS|={f'envs/pettingzoo/{s}.py' for s in ('__init__','scenario1','scenario2','uav_env','uav_radio')}
FORBIDDEN=('torch','jax','tensorflow','cupy','cuda','numba.cuda',
 'experiments.candidates.typed_joint_skill_decision.b04.reader',
 'experiments.candidates.typed_joint_skill_decision.b04.model',
 'experiments.candidates.typed_joint_skill_decision.b04.functional',
 'experiments.candidates.typed_joint_skill_decision.b04.training')
THREAD_KEYS=('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS')


def encoded(value):
    # Inputs here are already ordinary data. No original recursive plain conversion.
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('ascii')


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024**2),b''):h.update(block)
    return h.hexdigest()


def relative(root,name):
    p=Path(name)
    if p.is_absolute() or '..' in p.parts:raise ValueError('contained relative artifact required')
    result=(Path(root)/p).resolve()
    if Path(root).resolve() not in result.parents:raise ValueError('artifact escapes declared root')
    return result


def verify_file(path,expected):
    p=Path(path)
    if p.stat().st_size!=expected['bytes'] or sha(p)!=expected['sha256']:raise ValueError('bound file changed: '+str(p))


def read_bound(path,digest):
    if sha(path)!=digest:raise ValueError('input manifest SHA256 mismatch')
    return json.loads(Path(path).read_bytes())


def shard(index):
    if type(index) is not int or not 0<=index<258:raise ValueError('fixed shard address required')
    split,local=('train',index) if index<250 else ('fresh',index-250)
    start=WORLDS[split+'_start']+local*64
    return split,local,range(start,start+64)


def partial_path(root,value):
    p=Path(value['reference']['partial']['path'])
    return p if p.is_absolute() else relative(root,str(p))


def validate(value,root,verify_references=True):
    if (value['schema']!=1 or value['study']!='b05_complete_cpu_data_bank' or value['direction']!='typed_joint_skill_decision'
        or value['scientific_source_sha']!=SCIENCE_SHA or value['scientific_input']!={'path':'docs/research/candidates/typed_joint_skill_decision/B04_INPUT.json','sha256':SCIENCE_INPUT}
        or value['worlds']!=WORLDS or value['ceilings']!=LIMITS or set(value['pinned_sources'])!=SOURCE_KEYS):
        raise ValueError('fixed B05 scientific/source contract mismatch')
    if sha(relative(root,value['scientific_input']['path']))!=SCIENCE_INPUT:raise ValueError('original scientific input changed')
    for name,digest in value['pinned_sources'].items():
        if sha(relative(root,name))!=digest:raise ValueError('pinned source changed: '+name)
    r=value['reference'];p=r['partial'];disk=value['disk_scope']
    if (r['old_source_sha']!=SCIENCE_SHA or r['old_input_sha256']!=SCIENCE_INPUT or r['complete_worlds']!=2501
        or r['complete_labels']!=430980 or set(r['files'])!={f'raw/bank/train/{i:04d}.npz' for i in range(39)}
        or p['complete_worlds']!=list(range(109402496,109402501)) or p['incomplete_world']!=109402501
        or p['incomplete_labels']!=165 or p['incomplete_candidates']!=172 or p['complete_rows']!=1025
        or p['complete_bytes']!=1056813 or p['gzip_eof'] is not False
        or p['sha256']!='a6dd341a5c827b78d69b3f2bdbeef97e4ef361f38c596356e54a7a205c35c282'
        or p['complete_sha256']!='f64bf50d0102cde03e0dd594adda924db263348785cc11060f7770e56f67a409'
        or p['bytes']!=116876 or not Path(r['root']).is_absolute()
        or disk['reference_root']!=r['root'] or not Path(disk['own_scratch']).is_absolute()
        or disk['include_current_source_snapshot'] is not True or disk['shared_interpreter_copied'] is not False):
        raise ValueError('fixed old compatibility/disk contract mismatch')
    rt=value['runtime']
    if (rt['node']!='local_linux' or rt['python_version']!='3.10.20' or rt['numpy_version']!='1.26.3'
        or rt['gymnasium_version']!='1.0.0' or rt['pettingzoo_version']!='1.24.3' or rt['cpu_threads']!=1
        or rt['executable_sha256']!='3303d2b5dc566818e412d2b5b6cd8e792bd360865da47593429a635f72668226'):
        raise ValueError('fixed existing runtime contract mismatch')
    if verify_references:
        for name,expected in r['files'].items():verify_file(relative(r['root'],name),expected)
        verify_file(partial_path(root,value),p)


def runtime(expected,numeric=False):
    actual={'resolved_executable':str(Path(sys.executable).resolve(strict=True)),
        'executable_sha256':sha(Path(sys.executable).resolve(strict=True)),'python_version':platform.python_version(),
        'numpy_version':importlib.metadata.version('numpy'),'gymnasium_version':importlib.metadata.version('gymnasium'),
        'pettingzoo_version':importlib.metadata.version('pettingzoo')}
    if any(actual[k]!=expected[k] for k in actual) or not os.path.samefile(sys.executable,expected['configured_python']):
        raise ValueError('actual configured runtime identity mismatch')
    if numeric:
        import numpy as np
        if np.__version__!=expected['numpy_version']:raise ValueError('imported NumPy identity mismatch')
    return actual


def imports(parent=False):
    names=sorted(sys.modules);prefixes=FORBIDDEN+(('numpy','envs') if parent else ())
    bad=[name for name in names if any(name==p or name.startswith(p+'.') for p in prefixes)]
    return {'modules':names,'forbidden_modules':bad,'parent_stdlib_only':parent}


def guard(parent=False):
    value=imports(parent)
    if value['forbidden_modules']:raise RuntimeError('forbidden data-stage imports: '+','.join(value['forbidden_modules']))
    return value


def threads():
    os.environ.update({key:'1' for key in THREAD_KEYS});os.environ['PYTHONDONTWRITEBYTECODE']='1';sys.dont_write_bytecode=True
    return {key:os.environ[key] for key in THREAD_KEYS}
