"""Full canonical read and portable compact witnessed proof; no numerical effects."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from experiments.candidates.typed_joint_skill_decision.b05_data_bank import evidence as e,contract as old
from . import contract as c


def receipt(binding,source_root):
    """Verify published compact completion evidence, without copying raw reader bulk.

    The assigning DM pins the actual full manifest/native witness after full() over the
    canonical output. This reader rechecks all bound child/native identities and counts.
    A summary Boolean alone cannot satisfy the interface. Shard consumers still hash
    actual bank bytes on load. Missing raw artifacts do not become verified bytes here.
    """
    if set(binding)!={'root','source_sha','manifest_sha256','input_manifest','terminal'}:raise ValueError('exact reader/result/input/native binding required')
    root=Path(binding['root']).resolve(strict=True)
    input_path=Path(binding['input_manifest']['path'])
    if not input_path.is_absolute():input_path=c.relative(source_root,str(input_path))
    value=c.read_bound(input_path,binding['input_manifest']['sha256'])
    if (value['schema']!=1 or value['study']!='b07_fixed_producer_reader' or value['direction']!='typed_joint_skill_decision'
        or value['scientific_source_sha']!=c.SCIENCE_SHA or value['scientific_input_sha256']!=c.SCIENCE_INPUT
        or value['worlds']!=c.WORLDS or value['ceilings']!=c.LIMITS):raise ValueError('actual selected B07 input required')
    c.sources(value['executable_sources'],source_root)
    manifest=c.read_bound(root/'artifact-manifest.json',binding['manifest_sha256']);files=manifest['files']
    def load(name):return json.loads(c.verify(root,name,files[name]).read_bytes())
    config=load('config.json');summary=load('summary.json')
    launch,witness=c.terminal(root,binding['terminal'],binding['source_sha'],0)
    if (summary['status']!=c.STATUS or summary['input_sha256']!=binding['input_manifest']['sha256']
        or summary['input_sha256']!=manifest['input_sha256'] or config['input_sha256']!=summary['input_sha256']
        or manifest['launch_sha']!=binding['source_sha'] or summary['launch_sha']!=manifest['launch_sha'] or config['launch_sha']!=manifest['launch_sha']
        or config['manifest']!=value or config['producer']!=value['producer'] or summary['producer']!=value['producer']
        or summary['original_native_exit_code']!=2 or summary['producer_labels']!=c.LABELS
        or summary['reader_labels']!=c.LABELS or summary['completed_reader_shards']!=258
        or summary['completed_producer_shards']!=0 or summary['compatibility_worlds']!=2501
        or summary['compatibility_labels']!=430980 or summary['scientific_source_sha']!=c.SCIENCE_SHA
        or summary['scientific_input_sha256']!=c.SCIENCE_INPUT
        or config['counter_schema']!=list(e.COUNTERS) or config['source_root']!=launch['source_root']
        or config['output_root']!=launch['output_root'] or config['admission']['sha']!=launch['sha']
        or config['admission']['command_sha256']!=launch['command_sha256']
        or config['admission']['child_pid']!=launch['runner_process']['identity']['pid']
        or config['admission']['parent_pid']!=launch['process']['identity']['pid']
        or launch['node']!='local_linux' or summary['retry'] is not False):raise ValueError('complete fixed-version provenance/denominators required')
    for record in (config,summary):
        limits=record['active_limits']
        if limits['address_space']!=[c.LIMITS['parent_address_space_bytes'],c.LIMITS['child_address_space_bytes']] or limits['cpu']!=[7190,7200]:
            raise ValueError('selected parent resource limits changed')
    if config['imports']['forbidden_modules'] or summary['imports_after']['forbidden_modules']:raise ValueError('forbidden parent science import')
    block=c.verify(root,'shared-counters.bin',files['shared-counters.bin']).read_bytes()
    if len(block)!=e.BLOCK_BYTES:raise ValueError('fixed reader counter layout')
    counts={name:e.Q.unpack_from(block,8*i)[0] for i,name in enumerate(e.COUNTERS)}
    if counts!=summary['bill']['counters']:raise ValueError('final counter/summary mismatch')
    from .run import complete_counts,BOOTSTRAP
    class Counters:
        def snapshot(self):return {'counters':counts}
    complete_counts(Counters(),c.LABELS)
    readings=json.loads(gzip.decompress(c.verify(root,'raw/parent/shards.json.gz',files['raw/parent/shards.json.gz']).read_bytes()))
    if len(readings)!=258 or [r['index'] for r in readings]!=list(range(258)):raise ValueError('all258 chronological reader handoffs')
    total_labels=old_worlds=old_labels=0;differences={pair:0 for pair in ('rebuild_vs_producer','rebuild_vs_original','producer_vs_original')}
    excluded=None
    for index,reading in enumerate(readings):
        base=f'raw/process/reader/{index:04d}'
        context=load(base+'/context.json');child_config=load(base+'/config.json');child_summary=load(base+'/summary.json')
        child_manifest=load(base+'/artifact-manifest.json');exit_record=load(base+'/process-exit.json')
        context_bytes=(root/(base+'/context.json')).read_bytes();digest=hashlib.sha256(context_bytes).hexdigest()
        if (context['stage']!='reader' or context['shard']!=index or context['launch_sha']!=manifest['launch_sha']
            or context['input_sha256']!=manifest['input_sha256'] or context['parent_identity']!={key:launch['runner_process']['identity'][key] for key in ('pid','start_ticks')}
            or context['admission']!=config['admission'] or context['producer_root']!=value['producer']['root']
            or context['source_root']!=config['source_root'] or context['output_root']!=config['output_root']
            or context['context_relative']!=base+'/context.json'
            or child_summary['status']!='complete' or child_summary['stage']!='reader' or child_summary['shard']!=index
            or child_summary['launch_sha']!=manifest['launch_sha'] or child_summary['input_sha256']!=manifest['input_sha256']
            or child_config!=child_summary['config'] or child_config['context_sha256']!=digest
            or exit_record['context_sha256']!=digest or exit_record['exit_code']!=0 or exit_record['terminal_status']!='reaped'
            or exit_record['stage']!='reader' or exit_record['shard']!=index
            or exit_record['parent_identity']!=context['parent_identity'] or exit_record['child_identity']!=child_config['child_identity']
            or exit_record['command'][-1]!=BOOTSTRAP or exit_record['cwd']!=context['source_root']
            or exit_record['error'] is not None or exit_record['retry'] is not False
            or child_summary['retry'] is not False or child_manifest['stage']!='reader' or child_manifest['shard']!=index):
            raise ValueError('actual child context/summary/source/reaped witness mismatch')
        active=child_summary['active_limits']
        if active['address_space']!=[1073741824,1073741824] or active['cpu']!=[115,120]:raise ValueError('original numeric child limits changed')
        if child_summary['imports_after']['forbidden_modules'] or child_config['imports_before_hosts']['forbidden_modules']:raise ValueError('forbidden data-only child import')
        result=child_summary['result']
        if reading!={'stage':'reader','index':index,**result}:raise ValueError('complete handoff differs from actual child')
        split,local,worlds=c.shard(index);prefix=f'raw/label-reader/{split}/{local:04d}'
        if (result['worlds']!=64 or result['split']!=split or result['shard']!=local
            or [row[0] for row in result['world_candidate_counts']]!=list(worlds)
            or any(type(row[1]) is not int or not 133<=row[1]<=210 or type(row[2]) is not int or not 0<=row[2]<row[1] for row in result['world_candidate_counts'])
            or sum(row[1] for row in result['world_candidate_counts'])!=result['labels']):raise ValueError('complete chronological world/menu/label counts')
        for name in (prefix+'.npz',prefix+'-full.jsonl.gz',prefix+'-checks.jsonl.gz'):
            if name not in child_manifest['files'] or files[name]!=child_manifest['files'][name]:raise ValueError('full-vector/diagnostic bulk digest binding missing')
        for name,entry in child_manifest['files'].items():
            if name not in files or files[name]!=entry:raise ValueError('child/full artifact digest identity')
        expected_old=64 if index<39 else 5 if index==39 else 0
        if (result['compatibility_worlds']!=expected_old
            or result['compatibility_labels']!=sum(row[1] for row in result['world_candidate_counts'][:expected_old])):
            raise ValueError('2501 complete original worlds and exact label denominators only')
        if index==39:excluded=result['excluded_old_partial']
        total_labels+=result['labels'];old_worlds+=expected_old;old_labels+=result['compatibility_labels']
        for pair in differences:
            number=result['winner_difference_counts'][pair]
            if type(number) is not int or not 0<=number<=(64 if pair=='rebuild_vs_producer' else expected_old):raise ValueError('winner difference count range')
            differences[pair]+=number
    if (total_labels!=c.LABELS or old_worlds!=2501 or old_labels!=430980 or differences!=summary['winner_difference_counts']
        or excluded!={'world':109402501,'retained_labels':165,'candidates':172,'excluded_from_complete_compatibility':True}):
        raise ValueError('complete original/producer/reader aggregates or incomplete exclusion changed')
    return {'status':c.STATUS,'summary':summary,'manifest':manifest,'input':value,
            'native_exit_code':0,'raw_payload_verified_here':False,'verified_compact_children':258,
            'trust':'published full-read manifest plus all bound compact native/child witnesses; raw digests preserved, no raw replay'}


def full(binding,source_root):
    result=receipt(binding,source_root)
    c.validate(result['input'],source_root,verify_references=True)
    for name,entry in result['manifest']['files'].items():c.verify(binding['root'],name,entry)
    result['raw_payload_verified_here']=True
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binding',required=True,type=Path);p.add_argument('--binding-sha256',required=True)
    p.add_argument('--source-root',required=True,type=Path)
    args=p.parse_args(argv);result=full(c.read_bound(args.binding,args.binding_sha256),args.source_root)
    result.pop('manifest');result.pop('input');print(c.encoded(result).decode('ascii'),end='')


if __name__=='__main__':main()
