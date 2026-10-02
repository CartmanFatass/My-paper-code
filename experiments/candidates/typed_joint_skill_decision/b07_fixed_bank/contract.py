"""Effect-free fixed producer, reader source and selected resource contract."""
from __future__ import annotations
import copy
import json
from pathlib import Path
from experiments.candidates.typed_joint_skill_decision.b05_data_bank import contract as old

encoded=old.encoded
sha=old.sha
verify_file=old.verify_file
read_bound=old.read_bound
shard=old.shard
SCIENCE_SHA=old.SCIENCE_SHA
SCIENCE_INPUT=old.SCIENCE_INPUT
WORLDS=old.WORLDS
PRODUCER_SHA='c271c7370c6948b06f0a4a6fd783eddff0d8731a'
PRODUCER_INPUT='dd2bf2e7f54b0070587529559a1963438fa62fb8fb9bfe7db46202932e303394'
PRODUCER_MANIFEST='f18dcef40b320755e5b3bdfd94c4cc5be7869a7b549f58e0eccbe4090d6886e8'
PRODUCER_SUMMARY='90a0da52143b132ca3a718a77df8c549ae195e820574f45854c39399b3f4b221'
LABELS=2844367
STATUS='fixed_producer_version_validated'
LIMITS={'static_calls':LABELS,'hosts':16512,'raw_constructions':16512,
 'cpu_seconds':7200,'wall_seconds':14400,'child_cpu_seconds':120,'child_wall_seconds':240,
 'parent_address_space_bytes':536870912,'child_address_space_bytes':1073741824,
 'normal_disk_bytes':4294967296,'core_reserve_bytes':2147483648,
 'fits':0,'native_steps':0,'model_forwards':0,'gpu_seconds':0}
FROZEN_B05={'experiments/candidates/typed_joint_skill_decision/b05_data_bank/data.py': 'ed071814f2a64470072e6eb9d99492889f75f441e245c528399035d76e3a8111', 'experiments/candidates/typed_joint_skill_decision/b05_data_bank/read.py': '1b9e1d6171b69a67a0bc59e291469d9ebb2f2a867783692d952197f870ba037a', 'experiments/candidates/typed_joint_skill_decision/b05_data_bank/run.py': '747e0461f1c0d6b1a5f45ac3eafae44b989ef41ef1fdf97783066fe4399208a5', 'experiments/candidates/typed_joint_skill_decision/b05_data_bank/contract.py': '24bce02b7a7bc4598145e41de3c7da0a3968db858b5e56da2f1a45b57e3741d3', 'experiments/candidates/typed_joint_skill_decision/b05_data_bank/__init__.py': '65a0fd28b3c570530f5f2f7925bbd6c160290ac9da27da648dcb4d832e9276a7', 'experiments/candidates/typed_joint_skill_decision/b05_data_bank/evidence.py': '7f822526c643034b789d892da767a542280bce92eb287550d270c55c6c5868e8'}
READER_FILES={f'experiments/candidates/typed_joint_skill_decision/b07_fixed_bank/{name}.py'
 for name in ('__init__','contract','data','evidence','read','run')}
CONSUMER_FILES={f'experiments/candidates/typed_joint_skill_decision/b06_bank_consumer/{name}.py'
 for name in ('__init__','billing','commitment','contract','evidence','reader','run','worker')}


def relative(root,name):
    # Preserve canonical containment/symlink refusal without depending on mutable B06.
    p=Path(name)
    if not isinstance(name,str) or not name or p.is_absolute() or '..' in p.parts or str(p)!=name:
        raise ValueError('canonical contained artifact required')
    current=Path(root).absolute()
    if current.is_symlink():raise ValueError('artifact root symlink refused')
    for part in p.parts:
        current=current/part
        if current.is_symlink():raise ValueError('artifact symlink alias refused')
    return old.relative(root,name)


def verify(root,name,entry):
    path=relative(root,name);old.verify_file(path,entry);return path


def sources(mapping,root,consumer_stage=False):
    required=READER_FILES|set(FROZEN_B05)
    if consumer_stage:required|=CONSUMER_FILES
    if set(mapping)!=required:raise ValueError('exact executable source set required')
    for name,digest in mapping.items():
        if name in FROZEN_B05 and digest!=FROZEN_B05[name]:raise ValueError('frozen B05 helper identity changed')
        if sha(relative(root,name))!=digest:raise ValueError('executable source bytes changed: '+name)


def terminal(root,binding,source_sha,exit_code):
    launch=read_bound(relative(root,'launch-manifest.json'),binding['launch_manifest_sha256'])
    witness=read_bound(relative(root,'process-exit.json'),binding['process_exit_sha256'])
    if (launch['sha']!=source_sha or witness['status']!='exited' or type(witness['exit_code']) is not int
        or witness['exit_code']!=exit_code or witness['process_identity']!=launch['runner_process']['identity']
        or witness['supervisor_identity']!=launch['process']['identity'] or launch['direction']!='typed_joint_skill_decision'):
        raise ValueError('actual native terminal/source binding mismatch')
    return launch,witness


def producer(binding,verify_payload=True):
    expected={'root','manifest_sha256','summary_sha256','source_sha','input_sha256','terminal'}
    if set(binding)!=expected or (binding['source_sha'],binding['input_sha256'],binding['manifest_sha256'],binding['summary_sha256'])!=(PRODUCER_SHA,PRODUCER_INPUT,PRODUCER_MANIFEST,PRODUCER_SUMMARY):
        raise ValueError('immutable failed B05 producer version required')
    root=Path(binding['root']).resolve(strict=True)
    if not Path(binding['root']).is_absolute():raise ValueError('absolute producer root required')
    manifest=read_bound(root/'artifact-manifest.json',PRODUCER_MANIFEST)
    summary=read_bound(root/'summary.json',PRODUCER_SUMMARY)
    launch,witness=terminal(root,binding['terminal'],PRODUCER_SHA,2)
    for name in ('config.json','summary.json','shared-counters.bin','raw/parent/shards.json.gz','raw/engineering/static-permutations.json.gz'):
        verify(root,name,manifest['files'][name])
    config=json.loads((root/'config.json').read_bytes())
    if (manifest['launch_sha']!=PRODUCER_SHA or manifest['input_sha256']!=PRODUCER_INPUT
        or config['launch_sha']!=PRODUCER_SHA or config['input_sha256']!=PRODUCER_INPUT
        or summary['status']!='partial_or_failed' or summary['completed_producer_shards']!=258
        or summary['producer_labels']!=LABELS or summary['scientific_source_sha']!=SCIENCE_SHA
        or summary['scientific_input_sha256']!=SCIENCE_INPUT):raise ValueError('original failed producer facts changed')
    bank={f'raw/bank/{split}/{i:04d}.npz':manifest['files'][f'raw/bank/{split}/{i:04d}.npz']
          for split,count in (('train',250),('fresh',8)) for i in range(count)}
    if sum(x['bytes'] for x in bank.values())!=321771896:raise ValueError('complete immutable bank byte denominator')
    if verify_payload:
        from experiments.candidates.typed_joint_skill_decision.b05_data_bank.read import read
        observed=read(root,PRODUCER_MANIFEST)
        if observed['native_exit_code']!=2 or observed['status']!='partial_or_terminal_unconfirmed':raise ValueError('original failure must remain original failure')
        for index in range(258):
            name=f'raw/process/producer/{index:04d}/summary.json'
            s=json.loads(verify(root,name,manifest['files'][name]).read_bytes())
            w=json.loads(verify(root,f'raw/process/producer/{index:04d}/process-exit.json',manifest['files'][f'raw/process/producer/{index:04d}/process-exit.json']).read_bytes())
            if s['status']!='complete' or s['result']['worlds']!=64 or w['exit_code']!=0 or w['terminal_status']!='reaped':raise ValueError('all original producer children required')
    return {'root':str(root),'files':bank,'config':config,'summary':summary,'launch':launch,'witness':witness}


def validate(value,root,verify_references=True):
    if (value['schema']!=1 or value['study']!='b07_fixed_producer_reader' or value['direction']!='typed_joint_skill_decision'
        or value['scientific_source_sha']!=SCIENCE_SHA or value['scientific_input_sha256']!=SCIENCE_INPUT
        or value['worlds']!=WORLDS or value['ceilings']!=LIMITS):raise ValueError('fixed B07 selected contract mismatch')
    sources(value['executable_sources'],root)
    old.validate(value['b05_contract'],root,verify_references=verify_references)
    p=producer(value['producer'],verify_payload=verify_references)
    # Relocation changes storage addresses only, never original B05 scientific/identity data.
    a,b=copy.deepcopy(value['b05_contract']),copy.deepcopy(p['config']['manifest'])
    for item in (a,b):
        item['reference'].pop('root');item['disk_scope'].pop('reference_root');item['disk_scope'].pop('own_scratch')
    if encoded(a)!=encoded(b):raise ValueError('B05 contract delta beyond reference/scratch relocation')
    disk=value['disk_scope']
    if (set(disk)!={'producer_root','reference_root','own_scratch','include_current_source_snapshot','shared_interpreter_copied'}
        or disk['producer_root']!=p['root'] or disk['reference_root']!=value['b05_contract']['reference']['root']
        or not Path(disk['own_scratch']).is_absolute() or disk['include_current_source_snapshot'] is not True
        or disk['shared_interpreter_copied'] is not False):raise ValueError('one selected local disk scope required')
    if value['runtime']!=value['b05_contract']['runtime']:raise ValueError('existing B05 runtime identity required')
    return p

from experiments.candidates.typed_joint_skill_decision.b05_data_bank.contract import (
 runtime,imports,guard,threads,THREAD_KEYS)
