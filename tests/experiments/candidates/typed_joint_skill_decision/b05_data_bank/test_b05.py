"""Synthetic arrays/mocks only: no host, static/native query, RNG draw or learner."""
import ast
import copy
import gzip
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import zlib
import pytest
from experiments.candidates.typed_joint_skill_decision.b05_data_bank import contract as c,data,evidence as e,run,read

ROOT=Path(__file__).resolve().parents[5]
PACKAGE=ROOT/'experiments/candidates/typed_joint_skill_decision/b05_data_bank'
INPUT=ROOT/'docs/research/candidates/typed_joint_skill_decision/B05_INPUT.json'


@pytest.fixture(scope='module',autouse=True)
def bounded_checks(request):
    yield
    usage=resource.getrusage(resource.RUSAGE_SELF)
    allocated=e.allocated([request.config._hmasd_owned_scratch])
    print(f'own_process_cpu={usage.ru_utime+usage.ru_stime:.6f}s scratch_allocated_before_teardown={allocated}B actual_hosts=0 static=0 native=0 RNG=0 model=0')
    assert usage.ru_utime+usage.ru_stime<115
    assert allocated<15*1024**2


def record(world):
    positions=[[float(i),0.,100.] for i in range(6)];layouts=[positions,[[float(i+1),1.,100.] for i in range(6)]]
    return {'identity':{'world':world,'initial_positions_xyz':positions,'user_positions_xy':[[0.,0.]]*50,
        'bs_xyz':[0.,0.,0.],'native_rng_sha256':'0'*64,'agents':[f'uav_{i}' for i in range(6)],
        'transmitter_mask':[True]*6,'current_step':0},'layouts_xyz':layouts,
        'construction':{'report':{'candidates':2},'rng_type':'PCG64','rng_state_sha256':'1'*64,
            'raw_metadata':[{'kind':'kmeans_plain','k':4,'index':0},{'kind':'subset_flat','k':4,'index':1}]},
        'infos':[{'contract_reward':.5,'coverage_backhauled':.25,'frontend_capacity_with_path_mbps':100.,'flag':True,'count':2},
                 {'contract_reward':.5,'coverage_backhauled':.25,'frontend_capacity_with_path_mbps':100.,'flag':True,'count':2}],
        'best':0,'prepare_seconds':0.,'static_attempts':2,'source_sha':'a'*40,'input_sha256':'b'*64}


class Diagnostics:
    def __init__(self):self.rows=[];self.bill=self;self.counts={}
    def write(self,row):self.rows.append(row)
    def charge(self,name,n=1):self.counts[name]=self.counts.get(name,0)+n


def test_fixed_shards_ranges_and_fresh_separation():
    addresses=[c.shard(i) for i in range(258)]
    assert sum(len(w) for _,_,w in addresses)==16512
    assert addresses[0][2]==range(109400000,109400064)
    assert addresses[249][2].stop==109416000
    assert addresses[250][0]=='fresh' and addresses[250][2].start==109420000
    assert addresses[-1][2].stop==109420512
    for invalid in (-1,258,True,1.):
        with pytest.raises(ValueError):c.shard(invalid)
    assert data.teacher([{'contract_reward':.4},{'contract_reward':.4}])==0
    with pytest.raises(ValueError):data.teacher([{'contract_reward':float('nan')}])


def test_fixed_manifest_and_source_rejection(tmp_path):
    value=c.read_bound(INPUT,c.sha(INPUT));c.validate(value,ROOT,verify_references=False)
    with pytest.raises(ValueError,match='SHA256'):c.read_bound(INPUT,'0'*64)
    for key in ('train_count','fresh_count','shard_worlds'):
        wrong=copy.deepcopy(value);wrong['worlds'][key]+=1
        with pytest.raises(ValueError,match='contract'):c.validate(wrong,ROOT,False)
    wrong=copy.deepcopy(value);name=next(iter(wrong['pinned_sources']));wrong['pinned_sources'][name]='0'*64
    with pytest.raises(ValueError,match='pinned source'):c.validate(wrong,ROOT,False)
    with pytest.raises(ValueError):c.relative(tmp_path,'../escape')
    path=tmp_path/'literal';path.write_bytes(b'fixed')
    with pytest.raises(ValueError,match='bound file'):c.verify_file(path,{'bytes':5,'sha256':'0'*64})


def test_original_schema_synthetic_roundtrip_and_original_consumer(tmp_path):
    import numpy as np
    from experiments.candidates.typed_joint_skill_decision.b04.bank import Bank,features
    records=[record(109400000+i) for i in range(64)];a=data.arrays(records)
    relative='raw/bank/train/0000.npz';path=c.relative(tmp_path,relative);path.parent.mkdir(parents=True)
    np.savez_compressed(path,**a);descriptor={'bytes':path.stat().st_size,'sha256':c.sha(path)}
    rebuilt=data.load_shard(path,descriptor,109400000,'a'*40,'b'*64)
    assert rebuilt[0]==records[0] and rebuilt[-1]==records[-1]
    original=Bank(tmp_path,{relative:descriptor},'train','a'*40,'b'*64)
    assert original.load(109400001)==records[1]
    assert features(original.load(109400001))['layouts_xyz']==records[1]['layouts_xyz']
    with pytest.raises(ValueError,match='leakage'):original.load(109420000)
    with pytest.raises(ValueError,match='identity'):data.load_shard(path,descriptor,109400064,'a'*40,'b'*64)
    assert path.stat().st_size<1024**2


def test_full_field_frozen_tolerance_exact_types_and_adverse_diagnostics():
    diagnostics=Diagnostics();base={'J':1.,'nested':[{'x':2.}],'count':2,'valid':True,'kind':'raw'}
    acceptable=copy.deepcopy(base);acceptable['J']+=1e-10
    data.physical(acceptable,base,'literal',diagnostics)
    for altered in ({**base,'J':1.+1e-8},{**base,'count':2.},{**base,'valid':1},{**base,'extra':0.},{**base,'J':float('nan')}):
        with pytest.raises(AssertionError):data.physical(altered,base,'literal adverse',diagnostics)
        assert not diagnostics.rows[-1]['passed'] and diagnostics.rows[-1]['actual']==altered
    with pytest.raises(AssertionError):data.exact([1.,2.],[2.,1.],'raw order',diagnostics)
    assert diagnostics.rows[-1]['expected']==[2.,1.]


def test_old_partial_denominator_excludes_incomplete_world():
    descriptor={'complete_worlds':[109402496,109402497],'incomplete_world':109402498,'incomplete_labels':1,'incomplete_candidates':2}
    rows=[]
    for world in descriptor['complete_worlds']+[descriptor['incomplete_world']]:
        r=record(world)
        from experiments.candidates.typed_joint_skill_decision.b04.bank import features
        rows.append({'type':'prepared','identity':r['identity'],'features':features(r),'construction':r['construction'],
            'source_sha':'a'*40,'input_sha256':'b'*64})
        for i,info in enumerate(r['infos'][:1 if world==descriptor['incomplete_world'] else 2]):
            rows.append({'type':'label','world':world,'raw_index':i,'info':info})
    complete,excluded=data.parse_partial(rows,descriptor,'a'*40,'b'*64)
    assert len(complete)==2 and sum(len(r['infos']) for r in complete)==4
    assert excluded=={'world':109402498,'retained_labels':1,'candidates':2,'excluded_from_complete_compatibility':True}
    bad=copy.deepcopy(rows);bad[-1]['raw_index']=1
    with pytest.raises(ValueError,match='chronology'):data.parse_partial(bad,descriptor,'a'*40,'b'*64)


def test_mmap_attempts_survive_reopen_and_caps_before_effect(tmp_path,monkeypatch):
    path=tmp_path/'counts';a=e.Shared(path,create=True);b=e.Shared(path)
    try:
        monkeypatch.setitem(e.CAPS,'static_calls',1)
        a.locate('producer',0,109400000,1);a.charge('static_calls')
        assert b.get('static_calls')==1 and b.get('static_completed')==0
        with pytest.raises(RuntimeError,match='before invocation'):a.charge('static_calls')
        with pytest.raises(RuntimeError):a.charge('native_steps')
        with pytest.raises(RuntimeError):a.charge('fits')
        assert b.get('static_calls')==1 and b.get('refused_effects')==3
        a.charge('parent_resource_checks');b.charge('resource_checks')
        assert b.get('parent_resource_checks')==b.get('resource_checks')==1
        assert 'lower bound' in b.snapshot()['semantics']
    finally:b.close();a.close()
    recovered=e.Shared(path)
    try:assert recovered.snapshot()['last_observed_context']['world']==109400000
    finally:recovered.close()


def test_trace_reservations_cached_disk_and_lossless_diagnostics(tmp_path,monkeypatch):
    calls=[]
    def allocated(roots,seen=None):calls.append(tuple(map(str,roots)));return 4096
    monkeypatch.setattr(e,'allocated',allocated);monkeypatch.setattr(e,'cpu',lambda:{'total_seconds':0.,'unmeasured_live_pids':[]})
    monkeypatch.setattr(e,'process_wall',lambda:0.)
    shared=e.Shared(tmp_path/'counts',True)
    try:
        bill=e.Budget(shared,[tmp_path/'fixed',tmp_path/'out'],[tmp_path/'fixed'],child=True)
        path=tmp_path/'out'/'trace.gz';trace=e.Trace(path,bill,diagnostics=True)
        for i in range(640):trace.write({'literal':i,'payload':'x'*64})
        trace.close()
        assert bill.pending<9*1024**2 and calls.count((str(tmp_path/'fixed'),))==1
        assert shared.get('reader_checks')==shared.get('reader_check_attempts')==640
        lines=gzip.decompress(path.read_bytes()).splitlines();assert len(lines)==640 and json.loads(lines[-1])['literal']==639
        bill.finalization_space(1024)
        assert path.stat().st_size<1024**2
    finally:shared.close()


def test_failed_unclosed_journal_bounds_without_repair(tmp_path):
    rows=[{'type':'prepared','identity':{'world':10},'features':{'layouts_xyz':[[1],[2]]},'source_sha':'s','input_sha256':'i'},
          {'type':'label','world':10,'raw_index':0,'info':{'J':.1}},
          {'type':'label','world':10,'raw_index':1,'info':{'J':.2}},
          {'type':'prepared','identity':{'world':11},'features':{'layouts_xyz':[[1],[2]]},'source_sha':'s','input_sha256':'i'}]
    original=b''.join(c.encoded(r) for r in rows)+b'{"incomplete":'
    compressor=zlib.compressobj(wbits=31);compressed=compressor.compress(original)+compressor.flush(zlib.Z_SYNC_FLUSH)
    path=tmp_path/'partial.gz';path.write_bytes(compressed);before=c.sha(path)
    result=e.journal_bounds(path)
    assert not result['gzip_eof'] and result['complete_json_rows']==4 and result['retained_label_rows']==2
    assert result['last_complete_producer_world']==10 and result['last_complete_label']=={'world':10,'raw_index':1}
    assert result['unparsed_decompressed_tail_bytes']==len(b'{"incomplete":')
    assert result['sha256']==before==c.sha(path)
    capped=e.journal_bounds(path,lambda:(_ for _ in ()).throw(run.Stop('synthetic closure cap')))
    assert capped['parse_or_resource_error']['type']=='Stop' and capped['sha256'] is None


def test_serial_child_failure_aborts_without_retry(monkeypatch):
    calls=[]
    class Child:
        returncode=None
        def poll(self):return self.returncode
        def terminate(self):calls.append('TERM');self.returncode=-15
        def wait(self,timeout=None):calls.append('wait');return self.returncode
        def kill(self):calls.append('KILL');self.returncode=-9
    class Bill:
        def check(self):raise run.Stop('synthetic aggregate cap')
    with pytest.raises(run.Stop,match='aggregate cap'):run.supervise(Child(),Bill())
    assert calls==['TERM','wait']
    class Unknown(Child):
        def terminate(self):calls.append('TERM')
        def kill(self):calls.append('KILL')
        def wait(self,timeout=None):raise subprocess.TimeoutExpired('mock',timeout)
    assert run.stop_child(Unknown()) is None


def test_import_admission_and_limit_source_guards(monkeypatch,tmp_path):
    from scripts import hmasd_admission,hmasd_launch
    hmasd_launch._validate_guard_contract(PACKAGE/'run.py','typed_joint_skill_decision')
    assert '--out' in hmasd_launch.OUTPUT_ARGUMENTS
    monkeypatch.setitem(sys.modules,'torch.forbidden_literal',object())
    with pytest.raises(RuntimeError,match='forbidden'):c.guard()
    def refused(*a,**kw):raise RuntimeError('synthetic admission refusal')
    monkeypatch.setattr(hmasd_admission,'require_admission',refused)
    with pytest.raises(RuntimeError,match='admission refusal'):
        run.main(['--out',str(tmp_path/'not-created'),'--launch-sha','a'*40,'--seed','0',
            '--input-manifest','unused','--input-manifest-sha256','b'*64])
    assert not (tmp_path/'not-created').exists()
    for path in PACKAGE.glob('*.py'):
        tree=ast.parse(path.read_bytes())
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):assert node.module not in ('torch','jax') and not (node.module or '').endswith(('b04.reader','b04.model','b04.functional'))
            if isinstance(node,ast.Import):assert all(name.name!='torch' for name in node.names)
    source=(PACKAGE/'run.py').read_text()
    assert 'resource.setrlimit(resource.RLIMIT_CORE' not in source and 'PR_SET_PDEATHSIG' in source
    assert "resource.setrlimit(resource.RLIMIT_AS,(soft,c.LIMITS['child_address_space_bytes']))" in source
    assert 'resource_tracker' not in run.BOOTSTRAP
    assert [a.dest for a in run.parser()._actions]==['help','out','launch_sha','seed','input_manifest','input_manifest_sha256']


def test_child_context_rejects_wrong_parent_and_source_before_numpy(tmp_path,monkeypatch):
    parent={'pid':123,'start_ticks':42};command=b'bound parent\0';admission={'sha':'a'*40,'command_sha256':'b'*64,'child_pid':123}
    context={'schema':1,'stage':'producer','shard':0,'source_root':str(ROOT),'output_root':str(tmp_path),
        'launch_sha':'a'*40,'input_path':'unused','input_sha256':'c'*64,'parent_identity':parent,
        'parent_cmdline_sha256':hashlib.sha256(command).hexdigest(),'admission':admission,
        'context_relative':'raw/process/producer/0000/context.json','context_sha_scope':'exact stdin bytes',
        'cached_fixed_allocated_bytes':1024,'counter_path':str(tmp_path/'shared-counters.bin'),'producer_artifact':None}
    launch={'sha':'a'*40,'command_sha256':'b'*64,'runner_process':{'identity':{'pid':123}},
        'source_root':str(ROOT),'output_root':str(tmp_path),'node':'local_linux','host_identity':run.platform.node()}
    e.durable(tmp_path/'launch-manifest.json',c.encoded(launch));payload=c.encoded(context)
    e.durable(tmp_path/context['context_relative'],payload)
    original=Path.read_bytes
    monkeypatch.setattr(Path,'read_bytes',lambda p:command if str(p)=='/proc/123/cmdline' else original(p))
    monkeypatch.setattr(run.os,'getppid',lambda:123);monkeypatch.setattr(run,'parent_death',lambda expected:None)
    assert run.verify_context(context,payload)==tmp_path
    wrong={**context,'source_root':str(tmp_path)}
    with pytest.raises(ValueError,match='source/admission'):run.verify_context(wrong,payload)
    monkeypatch.setattr(run.os,'getppid',lambda:456)
    with pytest.raises(ValueError,match='source/admission'):run.verify_context(context,payload)


def test_parent_mock_first_child_failure_preserves_partial_no_second_child(tmp_path,monkeypatch):
    from scripts import hmasd_admission
    value=json.loads(INPUT.read_bytes());admission={'sha':'a'*40,'command_sha256':'b'*64,'child_pid':os.getpid()}
    launch={'sha':'a'*40,'command_sha256':'b'*64,'source_root':str(ROOT),'output_root':str(tmp_path),
        'node':'local_linux','host_identity':run.platform.node()}
    e.durable(tmp_path/'launch-manifest.json',c.encoded(launch))
    monkeypatch.setattr(hmasd_admission,'require_admission',lambda *a,**kw:admission)
    monkeypatch.setattr(run,'limits',lambda *a,**kw:{'mock':True});monkeypatch.setattr(c,'guard',lambda **kw:{'mock':True})
    monkeypatch.setattr(c,'read_bound',lambda *a:value);monkeypatch.setattr(c,'validate',lambda *a,**kw:None)
    monkeypatch.setattr(c,'runtime',lambda *a,**kw:{'mock':True});monkeypatch.setattr(c,'imports',lambda **kw:{'mock':True})
    monkeypatch.setattr(run.signal,'setitimer',lambda *a:None);monkeypatch.setattr(run.signal,'signal',lambda *a:None)
    monkeypatch.setattr(run.faulthandler,'cancel_dump_traceback_later',lambda:None)
    class Bill:
        fixed=1024
        def __init__(self,shared,*a,**kw):self.shared=shared
        def check(self):pass
        def snapshot(self):return {**self.shared.snapshot(),'cpu':{'mock':True}}
        def finalization_space(self,size):assert 0<size<1024**2
    monkeypatch.setattr(e,'Budget',Bill);calls=[]
    def failed(context,shared,bill):
        calls.append((context['stage'],context['shard']));shared.charge('spawn_attempts')
        raise RuntimeError('synthetic child crash')
    monkeypatch.setattr(run,'spawn_case',failed)
    assert run.main(['--out',str(tmp_path),'--launch-sha','a'*40,'--seed','0','--input-manifest',str(INPUT),
        '--input-manifest-sha256','c'*64])==2
    assert calls==[('producer',0)]
    summary=json.loads((tmp_path/'summary.json').read_bytes())
    assert summary['status']=='partial_or_failed' and not summary['retry'] and summary['producer_labels']==0
    assert summary['bill']['counters']['spawn_attempts']==1
    assert summary['bill']['counters']['producer_worlds_completed']==0
    assert 'lower bounds' in summary['label_sum_scope'] and (tmp_path/'artifact-manifest.json').exists()


def test_artifact_merge_and_terminal_counter_reconstruction(tmp_path,monkeypatch):
    shared=e.Shared(tmp_path/'shared-counters.bin',True);counters=shared.snapshot()['counters'];shared.close()
    config={'launch_sha':'a'*40,'input_sha256':'b'*64,'counter_schema':list(e.COUNTERS)}
    summary={'status':'partial_or_failed','launch_sha':'a'*40,'input_sha256':'b'*64,'scientific_source_sha':c.SCIENCE_SHA,
        'scientific_input_sha256':c.SCIENCE_INPUT,'bill':{'counters':counters}}
    identity={'pid':123};supervisor={'pid':122}
    launch={'sha':'a'*40,'runner_process':{'identity':identity},'process':{'identity':supervisor}}
    witness={'status':'exited','exit_code':-11,'process_identity':identity,'supervisor_identity':supervisor}
    for name,value in [('config.json',config),('summary.json',summary),('launch-manifest.json',launch),('process-exit.json',witness)]:
        e.durable(tmp_path/name,c.encoded(value))
    files={name:{'bytes':(tmp_path/name).stat().st_size,'sha256':c.sha(tmp_path/name)} for name in ('config.json','summary.json','shared-counters.bin')}
    manifest={'schema':1,'launch_sha':'a'*40,'input_sha256':'b'*64,'files':files}
    e.durable(tmp_path/'artifact-manifest.json',c.encoded(manifest));monkeypatch.setattr(c,'guard',lambda **kw:{'synthetic_numeric_import_allowed_in_test':True})
    reading=read.read(tmp_path,c.sha(tmp_path/'artifact-manifest.json'))
    assert reading['status']=='partial_or_terminal_unconfirmed' and reading['native_exit_code']==-11
    assert reading['final_counter_block_matches_summary']
    shared=e.Shared(tmp_path/'shared-counters.bin');shared.charge('static_calls');shared.close()
    files['shared-counters.bin']['sha256']=c.sha(tmp_path/'shared-counters.bin')
    e.replace_json(tmp_path/'artifact-manifest.json',manifest)
    with pytest.raises(ValueError,match='counter block/summary'):read.read(tmp_path,c.sha(tmp_path/'artifact-manifest.json'))
    child=tmp_path/'raw/process/producer/0000';child.mkdir(parents=True)
    item=child/'literal.json';item.write_bytes(b'{}\n');name=str(item.relative_to(tmp_path))
    descriptor={'bytes':item.stat().st_size,'sha256':c.sha(item)}
    e.durable(child/'artifact-manifest.json',c.encoded({'stage':'producer','shard':0,'files':{name:descriptor}}))
    merged={};e.merge_child(tmp_path,'producer',0,merged);assert merged[name]==descriptor
    item.write_bytes(b'changed')
    with pytest.raises(ValueError,match='bound file'):e.merge_child(tmp_path,'producer',0,{})
