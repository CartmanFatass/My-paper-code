"""Synthetic saved vectors/compact witnesses only; no real bank, physics, model or exec."""
from __future__ import annotations
import ast
import copy
import gzip
import json
import math
from pathlib import Path
import time
import pytest
from experiments.candidates.typed_joint_skill_decision.b07_fixed_bank import contract as c,data,evidence,read,run
from experiments.candidates.typed_joint_skill_decision.b05_data_bank import data as old_data,evidence as old_e
from experiments.candidates.typed_joint_skill_decision.b06_bank_consumer import contract as consumer

ROOT=Path(__file__).resolve().parents[5]


class Diagnostics:
    def __init__(self):self.rows=[];self.bill=self;self.counts={}
    def write(self,row):self.rows.append(row)
    def charge(self,name):self.counts[name]=self.counts.get(name,0)+1


def record(js):
    return {'identity':{'world':7,'rng':'fixed'},'construction':{'raw_metadata':[{'source_index':i} for i in range(len(js))]},
            'layouts_xyz':[[[float(i),0.,1.]] for i in range(len(js))],
            'infos':[{'contract_reward':j,'coverage_backhauled':.5,'frontend_capacity_with_path_mbps':10.,'flag':True,'count':3} for j in js],
            'best':max(range(len(js)),key=lambda i:(js[i],-i))}


def test_exact_self_winners_report_one_ulp_and_ties():
    a=record([.5,.5]);b=record([.5,math.nextafter(.5,1.)]);sink=Diagnostics()
    class Bank:
        @staticmethod
        def features(r):return {'layouts_xyz':r['layouts_xyz']}
    result=data.compare_world(a,b,Bank,sink,'synthetic',True)
    assert result['winner_differs'] and result['left']['best']==0 and result['right']['best']==1
    assert result['left']['exact_max_indices']==[0,1]
    assert result['right_cross_selected_regret']<=result['algebraic_regret_bound_2delta']
    assert sink.counts=={'compatibility_label_attempts':2,'compatibility_labels':2}
    # Old contract still refuses the same pair; no monkeypatch or label mutation.
    with pytest.raises(AssertionError,match='lower-index teacher'):
        old_data.compare_world(a,b,Bank,Diagnostics(),'synthetic old')
    b['best']=0
    with pytest.raises(AssertionError,match='self argmax'):data.vector(b)


@pytest.mark.parametrize('fault',['physics','nonfinite','type','discrete','order','geometry','metadata'])
def test_unchanged_physical_and_exact_checks_refuse(fault):
    a=record([.5,.6]);b=copy.deepcopy(a)
    if fault=='physics':b['infos'][0]['contract_reward']+=1e-6
    elif fault=='nonfinite':b['infos'][0]['contract_reward']=float('nan')
    elif fault=='type':b['infos'][0]['count']=3.
    elif fault=='discrete':b['infos'][0]['flag']=False
    elif fault=='order':b['layouts_xyz'].reverse()
    elif fault=='geometry':b['identity']['world']=8
    else:b['construction']['raw_metadata'][0]['source_index']=1
    class Bank:
        @staticmethod
        def features(r):return {'layouts_xyz':r['layouts_xyz']}
    with pytest.raises((AssertionError,ValueError)):
        data.compare_world(a,b,Bank,Diagnostics(),'tamper')


def complete_counters():
    counts={name:0 for name in old_e.COUNTERS}
    counts.update(setup_attempts=1,setup_completed=1,numpy_import_attempts=258,numpy_import_completed=258,
        native_import_attempts=258,native_import_completed=258,hosts=16512,hosts_completed=16512,raw_constructions=16512,raw_completed=16512,resets=16512,resets_completed=16512,
        child_setup_attempts=258,child_setup_completed=258,rng_streams=16512,rng_completed=16512,
        reader_worlds_attempted=16512,reader_worlds_completed=16512,compatibility_attempts=2501,compatibility_worlds=2501,
        compatibility_label_attempts=430980,compatibility_labels=430980,reader_shards_completed=258,spawn_attempts=258,spawn_completed=258,
        static_calls=c.LABELS,static_completed=c.LABELS)
    return counts


@pytest.mark.parametrize('fault',[None,'partial','label','extra_producer','permutation','native','unfinished'])
def test_complete_denominators_and_zero_extra_effects(fault):
    counts=complete_counters()
    if fault=='partial':counts['reader_worlds_completed']-=1
    elif fault=='label':counts['compatibility_labels']-=1
    elif fault=='extra_producer':counts['producer_worlds_attempted']=1
    elif fault=='permutation':counts['permutation_reads']=1
    elif fault=='native':counts['native_steps']=1
    elif fault=='unfinished':counts['radio_refresh_calls']=1
    class Shared:
        def snapshot(self):return {'counters':counts}
    if fault:
        with pytest.raises(ValueError):run.complete_counts(Shared(),c.LABELS)
    else:assert run.complete_counts(Shared(),c.LABELS)==counts


def test_selected_limits_effect_refusal(tmp_path):
    shared=evidence.Shared(tmp_path/'counters.bin',create=True)
    try:
        for name in ('producer_worlds_attempted','permutation_reads','fits','native_steps','model_forwards','matching_calls'):
            with pytest.raises(RuntimeError):shared.charge(name)
        shared.charge('static_calls',c.LABELS)
        with pytest.raises(RuntimeError):shared.charge('static_calls')
        assert shared.get('refused_effects')==7
    finally:shared.close()
    assert c.LIMITS['normal_disk_bytes']==4*1024**3 and c.LIMITS['core_reserve_bytes']==2*1024**3


@pytest.fixture
def synthetic_receipt(tmp_path):
    """Opaque synthetic compact records exercise binding; cannot certify fixed B05 bytes."""
    out=tmp_path/'output';out.mkdir();files={}
    def put(name,value,blob=False):
        path=out/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(value if blob else c.encoded(value))
        files[name]={'sha256':c.sha(path),'bytes':path.stat().st_size}
    source_sha='a'*40;input_path=tmp_path/'input.json'
    producer={'root':'/synthetic-unused-producer','manifest_sha256':c.PRODUCER_MANIFEST,'summary_sha256':c.PRODUCER_SUMMARY,
        'source_sha':c.PRODUCER_SHA,'input_sha256':c.PRODUCER_INPUT,'terminal':{'launch_manifest_sha256':'0'*64,'process_exit_sha256':'0'*64}}
    value={'schema':1,'study':'b07_fixed_producer_reader','direction':'typed_joint_skill_decision',
        'scientific_source_sha':c.SCIENCE_SHA,'scientific_input_sha256':c.SCIENCE_INPUT,'worlds':c.WORLDS,'ceilings':c.LIMITS,
        'executable_sources':{name:c.sha(ROOT/name) for name in c.READER_FILES|set(c.FROZEN_B05)},'producer':producer}
    input_path.write_bytes(c.encoded(value));input_sha=c.sha(input_path)
    identity={'pid':12,'start_ticks':34};admission={'sha':source_sha,'command_sha256':'b'*64,'child_pid':12,'parent_pid':11}
    limits={'address_space':[536870912,1073741824],'cpu':[7190,7200]}
    launch={'sha':source_sha,'direction':'typed_joint_skill_decision','runner_process':{'identity':identity},
        'process':{'identity':{'pid':11,'start_ticks':33}},'source_root':str(ROOT),'output_root':str(out),'node':'local_linux','command_sha256':'b'*64}
    put('launch-manifest.json',launch)
    put('process-exit.json',{'status':'exited','exit_code':0,'process_identity':identity,'supervisor_identity':launch['process']['identity']})
    config={'manifest':value,'producer':producer,'input_sha256':input_sha,'launch_sha':source_sha,'counter_schema':list(old_e.COUNTERS),
        'source_root':str(ROOT),'output_root':str(out),'admission':admission,'active_limits':limits,'imports':{'forbidden_modules':[]}}
    put('config.json',config)
    readings=[];total=0
    for index in range(258):
        split,local,worlds=c.shard(index);base=f'raw/process/reader/{index:04d}';prefix=f'raw/label-reader/{split}/{local:04d}'
        rows=[]
        for world in worlds:
            offset=world-(109400000 if split=='train' else 109420000)+(16000 if split=='fresh' else 0)
            m=172+(offset<808 or 2501<=offset<5996);rows.append([world,m,0])
        labels=sum(row[1] for row in rows);total+=labels
        count_old=64 if index<39 else 5 if index==39 else 0
        result={'split':split,'shard':local,'worlds':64,'labels':labels,'world_candidate_counts':rows,
            'compatibility_worlds':count_old,'compatibility_labels':sum(row[1] for row in rows[:count_old]),
            'excluded_old_partial':{'world':109402501,'retained_labels':165,'candidates':172,'excluded_from_complete_compatibility':True} if index==39 else None,
            'winner_difference_counts':{pair:0 for pair in ('rebuild_vs_producer','rebuild_vs_original','producer_vs_original')}}
        context={'stage':'reader','shard':index,'launch_sha':source_sha,'input_sha256':input_sha,'parent_identity':identity,
            'admission':admission,'producer_root':producer['root'],'source_root':str(ROOT),'output_root':str(out),'context_relative':base+'/context.json'}
        put(base+'/context.json',context);digest=files[base+'/context.json']['sha256']
        child_identity={'pid':100+index,'start_ticks':1000+index}
        child_config={'context_sha256':digest,'child_identity':child_identity,'imports_before_hosts':{'forbidden_modules':[]}}
        put(base+'/config.json',child_config)
        child_summary={'status':'complete','stage':'reader','shard':index,'launch_sha':source_sha,'input_sha256':input_sha,
            'config':child_config,'active_limits':{'address_space':[1073741824,1073741824],'cpu':[115,120]},
            'imports_after':{'forbidden_modules':[]},'result':result,'retry':False}
        put(base+'/summary.json',child_summary)
        child_files={}
        for name in (prefix+'.npz',prefix+'-full.jsonl.gz',prefix+'-checks.jsonl.gz'):
            put(name,b'opaque synthetic raw digest only',True);child_files[name]=files[name]
        put(base+'/artifact-manifest.json',{'stage':'reader','shard':index,'files':child_files})
        put(base+'/process-exit.json',{'context_sha256':digest,'exit_code':0,'terminal_status':'reaped','stage':'reader','shard':index,
            'parent_identity':identity,'child_identity':child_identity,'command':['python','-c',run.BOOTSTRAP],
            'cwd':str(ROOT),'error':None,'retry':False})
        readings.append({'stage':'reader','index':index,**result})
    assert total==c.LABELS
    put('raw/parent/shards.json.gz',gzip.compress(c.encoded(readings)),True)
    counts=complete_counters();block=bytearray(old_e.BLOCK_BYTES)
    for i,name in enumerate(old_e.COUNTERS):old_e.Q.pack_into(block,8*i,counts[name])
    put('shared-counters.bin',bytes(block),True)
    summary={'status':c.STATUS,'input_sha256':input_sha,'launch_sha':source_sha,'producer':producer,'original_native_exit_code':2,
        'producer_labels':c.LABELS,'reader_labels':c.LABELS,'completed_reader_shards':258,'completed_producer_shards':0,
        'compatibility_worlds':2501,'compatibility_labels':430980,'scientific_source_sha':c.SCIENCE_SHA,'scientific_input_sha256':c.SCIENCE_INPUT,
        'bill':{'counters':counts},'active_limits':limits,'imports_after':{'forbidden_modules':[]},'retry':False,
        'winner_difference_counts':{pair:0 for pair in ('rebuild_vs_producer','rebuild_vs_original','producer_vs_original')}}
    put('summary.json',summary)
    manifest={'launch_sha':source_sha,'input_sha256':input_sha,'files':dict(files)};put('artifact-manifest.json',manifest)
    binding={'root':str(out),'source_sha':source_sha,'manifest_sha256':c.sha(out/'artifact-manifest.json'),
        'input_manifest':{'path':str(input_path),'sha256':input_sha},
        'terminal':{'launch_manifest_sha256':c.sha(out/'launch-manifest.json'),'process_exit_sha256':c.sha(out/'process-exit.json')}}
    return binding,put,files,manifest


def test_full_compact_denominators_without_raw_transport(synthetic_receipt):
    binding,put,files,manifest=synthetic_receipt
    out=Path(binding['root'])
    for name in manifest['files']:
        if name.startswith('raw/label-reader/'): (out/name).unlink()
    proof=read.receipt(binding,ROOT)
    assert proof['verified_compact_children']==258 and not proof['raw_payload_verified_here']
    assert proof['summary']['compatibility_labels']==430980
    # No synthetic producer/Boolean can satisfy real certify_bank.
    with pytest.raises((ValueError,FileNotFoundError)):
        consumer.certify_bank({'reader':binding,'producer_root':'/synthetic-unused-producer'},ROOT)


@pytest.mark.parametrize('fault',['summary_bytes','child_exit','missing_child','input_sha','source_sha','source_pin','denominator','raw_digest','context','counter','old_exit'])
def test_receipt_tampering_refused(synthetic_receipt,fault):
    binding,put,files,manifest=synthetic_receipt;out=Path(binding['root'])
    if fault=='input_sha':binding['input_manifest']['sha256']='0'*64
    elif fault=='source_sha':binding['source_sha']='c'*40
    elif fault=='source_pin':
        path=Path(binding['input_manifest']['path']);v=json.loads(path.read_bytes());v['executable_sources'][next(iter(c.READER_FILES))]='0'*64
        path.write_bytes(c.encoded(v));binding['input_manifest']['sha256']=c.sha(path)
    elif fault=='missing_child':(out/'raw/process/reader/0257/process-exit.json').unlink()
    else:
        name=('summary.json' if fault in ('summary_bytes','denominator','old_exit') else 'shared-counters.bin' if fault=='counter'
            else 'raw/process/reader/0000/artifact-manifest.json' if fault=='raw_digest'
            else 'raw/process/reader/0000/context.json' if fault=='context' else 'raw/process/reader/0000/process-exit.json')
        if fault in ('summary_bytes','counter'):
            (out/name).write_bytes(b'tampered');return_failure=True
        else:
            v=json.loads((out/name).read_bytes())
            if fault=='child_exit':v['exit_code']=2
            elif fault=='denominator':v['compatibility_worlds']=2500
            elif fault=='old_exit':v['original_native_exit_code']=0
            elif fault=='context':v['parent_identity']['start_ticks']+=1
            else:v['files'][next(iter(v['files']))]['sha256']='0'*64
            put(name,v);manifest['files'][name]=files[name]
            put('artifact-manifest.json',manifest);binding['manifest_sha256']=c.sha(out/'artifact-manifest.json')
    with pytest.raises((ValueError,FileNotFoundError,KeyError)):
        read.receipt(binding,ROOT)


def test_adapter_has_only_rebuild_and_original_no_permutation_calls():
    tree=ast.parse((ROOT/'experiments/candidates/typed_joint_skill_decision/b07_fixed_bank/data.py').read_text())
    rebuild=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='rebuild')
    calls=[ast.unparse(n.func) for n in ast.walk(rebuild) if isinstance(n,ast.Call)]
    assert calls.count('native.host.static_evaluate')==1
    assert not any('acquire' in name or 'permutation' in name or 'model' in name for name in calls)
    for path,digest in c.FROZEN_B05.items():assert c.sha(ROOT/path)==digest


def test_relative_input_resolves_against_source_not_cwd(synthetic_receipt,monkeypatch):
    binding,*_=synthetic_receipt
    binding['input_manifest']['path']=str(Path(binding['input_manifest']['path']).relative_to(ROOT))
    monkeypatch.chdir(Path(binding['root']))
    assert read.receipt(binding,ROOT)['status']==c.STATUS


def test_rebuild_composes_three_pairs_and_full_vectors_without_added_calls(tmp_path,monkeypatch):
    import numpy as np
    split,local,worlds=c.shard(39)
    saved=[]
    for world in worlds:
        r=record([.5,.5]);r['identity']['world']=world;saved.append(r)
    originals=copy.deepcopy(saved[:5])
    for r in originals:
        r['infos'][1]['contract_reward']=math.nextafter(.5,1.);r['best']=1
    excluded={'world':109402501,'retained_labels':165,'candidates':172,'excluded_from_complete_compatibility':True}
    monkeypatch.setattr(old_data,'partial_records',lambda *args:(originals,excluded))
    class Bill:
        def __init__(self):self.shared=self;self.counts={};self.mock_static_calls=0
        def check(self,**kwargs):pass
        def charge(self,name,n=1):self.counts[name]=self.counts.get(name,0)+n
        def locate(self,*args):pass
        def flush(self):pass
    bill=Bill();store=old_e.Store(tmp_path,bill,'reader',39)
    class Bank:
        @staticmethod
        def features(r):return {'layouts_xyz':r['layouts_xyz']}
        @staticmethod
        def prepare(native,world):
            r=saved[world-worlds.start]
            return None,r['identity'],[{'positions_xyz':np.asarray(x)} for x in r['layouts_xyz']],Bank.features(r),r['construction'],0.
    class Host:
        @staticmethod
        def static_evaluate(env,xyz,allow_a2a):
            bill.mock_static_calls+=1
            i=int(xyz[0,0]);return {**saved[0]['infos'][i],
                'contract_reward':.5 if i==0 else math.nextafter(.5,1.)}
    class Native:host=Host()
    result=data.rebuild(store,Native(),Bank,saved,{'b05_contract':{'reference':{'partial':{'path':'synthetic-partial'},
        'old_source_sha':'old','old_input_sha256':'old-input'}}},tmp_path)
    assert bill.mock_static_calls==128  # Mock callbacks; zero actual physical calls.
    assert result['compatibility_worlds']==5 and result['compatibility_labels']==10
    assert bill.counts['compatibility_label_attempts']==bill.counts['compatibility_labels']==10
    assert result['winner_difference_counts']=={'rebuild_vs_producer':64,'rebuild_vs_original':0,'producer_vs_original':5}
    assert bill.counts.get('permutation_reads',0)==bill.counts.get('producer_worlds_attempted',0)==0
    with np.load(tmp_path/(store.data_prefix+'.npz'),allow_pickle=False) as z:
        rows=json.loads(str(z['records']));assert len(rows)==64 and z['J_C_frontend'].shape==(128,3)
    assert rows[0]['winner_comparisons']['producer_vs_original']['winner_differs']
    assert len(rows[0]['winner_comparisons']['rebuild_vs_producer']['right']['J_C_frontend'])==2
    full=tmp_path/(store.data_prefix+'-full.jsonl.gz')
    assert len(gzip.decompress(full.read_bytes()).splitlines())==128 and str(full.relative_to(tmp_path)) in store.files


@pytest.mark.parametrize('fault',[None,'runner_start','supervisor'])
def test_parent_consumed_admission_identity_before_child_effects(tmp_path,monkeypatch,fault):
    import sys,types
    out=tmp_path/'output';out.mkdir();identity={'pid':run.os.getpid(),'start_ticks':77}
    parent=run.os.getppid()
    grant={'sha':'a'*40,'command_sha256':'b'*64,'child_pid':identity['pid'],'parent_pid':parent,'direction':'typed_joint_skill_decision'}
    launch={'sha':grant['sha'],'command_sha256':grant['command_sha256'],'source_root':str(ROOT),'output_root':str(out),
        'node':'local_linux','host_identity':run.platform.node(),'direction':'typed_joint_skill_decision',
        'runner_process':{'identity':{**identity,'start_ticks':78 if fault=='runner_start' else 77}},
        'process':{'identity':{'pid':parent+1 if fault=='supervisor' else parent}}}
    (out/'launch-manifest.json').write_bytes(c.encoded(launch))
    input_path=tmp_path/'input.json';input_path.write_bytes(b'{}\n')
    monkeypatch.setenv('HMASD_ADMISSION_V1','synthetic single-use')
    def admitted(*args,**kwargs):
        assert run.os.environ.pop('HMASD_ADMISSION_V1');return grant
    monkeypatch.setitem(sys.modules,'scripts.hmasd_admission',types.SimpleNamespace(require_admission=admitted))
    monkeypatch.setattr(run.e,'process_identity',lambda pid:dict(identity))
    # No resource limit, import guard or child execution is performed by this mock.
    monkeypatch.setattr(run,'limits',lambda *args,**kwargs:{'synthetic':True})
    monkeypatch.setattr(c,'guard',lambda **kwargs:{'forbidden_modules':[]})
    monkeypatch.setattr(c,'imports',lambda **kwargs:{'forbidden_modules':[]})
    monkeypatch.setattr(run,'spawn_case',lambda *args:pytest.fail('no child effect before valid input hash'))
    argv=['--out',str(out),'--seed','0','--launch-sha',grant['sha'],'--input-manifest',str(input_path),'--input-manifest-sha256','0'*64]
    if fault:
        with pytest.raises(ValueError,match='durable parent admission'):run.main(argv)
        assert not (out/'shared-counters.bin').exists()
    else:
        assert run.main(argv)==2
        summary=json.loads((out/'summary.json').read_bytes())
        assert summary['status']=='partial_or_failed' and 'SHA256 mismatch' in summary['error']['error']
        assert summary['completed_reader_shards']==0 and summary['bill']['shared']['counters']['spawn_attempts']==0
