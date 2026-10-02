"""Literal/mock-only B04 checks: no host, model, PRNG rollout or fitted asset."""
import ast
import contextlib
import copy
import gzip
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import uuid

import numpy as np
import pytest

from experiments.candidates.typed_joint_skill_decision.b04 import (
    bank, contract as c, evidence as e, functional, model, online,
    planner_reader, reader, run, shortlist, training, native,
)

ROOT=Path(__file__).resolve().parents[5]
SOURCE=ROOT/'experiments/candidates/typed_joint_skill_decision/b04'


@pytest.fixture(autouse=True)
def no_result_rng_or_model(monkeypatch):
    def refused(*args,**kwargs):
        raise AssertionError('unpermitted actual result RNG/model construction in pure checks')
    monkeypatch.setattr(np.random,'default_rng',refused)
    monkeypatch.setattr(model,'build',refused)


def geometry(m=3):
    return {'users_xy':[[float(i*70),float(i*20)] for i in range(50)],'bs_xyz':[100.,100.,0.],
            'layouts_xyz':[[[float(500+j*50+i),float(600+j*20),100.] for j in range(6)] for i in range(m)],
            'kinds':[c.KINDS[i%3] for i in range(m)],'ks':[4+i%3 for i in range(m)]}


class FakeBill:
    def __init__(self):
        self.values={k:0 for k in e.COUNTERS};self.pending=[]
    def check(self,**kwargs):
        self.pending.append(kwargs.get('pending',0))
    def snapshot(self):
        return {'counters':dict(self.values)}
    def charge(self,key,n=1):
        self.values[key]+=n
    def rows(self,phase,n,valid=None):
        self.charge('all_candidate_presentations',n);self.charge(phase+'_candidate_presentations',n)
        self.charge(phase+'_valid_candidates',n if valid is None else valid)
    def rows_done(self,phase,n):
        self.charge(phase+'_completed_candidates',n)


def store(tmp_path):
    result=e.Store(tmp_path/'out',FakeBill());result.launch_sha='a'*40;result.input_sha256='b'*64
    return result


def test_imports_and_architecture_are_effect_free():
    for path in SOURCE.glob('*.py'):
        tree=ast.parse(path.read_bytes())
        for node in tree.body:
            if isinstance(node,(ast.FunctionDef,ast.ClassDef,ast.AsyncFunctionDef)):
                continue
            calls=[n for n in ast.walk(node) if isinstance(n,ast.Call)]
            names=[ast.unparse(n.func) for n in calls]
            assert not any(n.endswith(('default_rng','manual_seed','make_host','build','forward')) for n in names)
    # Literal topology arithmetic; does not construct or run a network.
    two=lambda a,b:a*b+b+b*b+b
    assert sum(two(a,64) for a in (9,52,3))==16768
    assert 3*3*two(132,64)==114048
    assert 3*two(256,64)==61824
    assert 198*64+64+64+1==12801
    assert 16768+114048+61824+12801==c.PARAMETERS==205441
    source=(SOURCE/'model.py').read_text()
    assert "nn.Linear(198,64)" in source and "two(256) for _ in range(3)" in source
    assert 'autocast' not in source and 'torch.compile' not in source


def test_launcher_guard_output_and_effect_refusal(tmp_path,monkeypatch):
    from scripts import hmasd_launch,hmasd_admission
    hmasd_launch._validate_guard_contract(SOURCE/'run.py','typed_joint_skill_decision')
    assert '--out' in hmasd_launch.OUTPUT_ARGUMENTS
    args=['--out',str(tmp_path/'forbidden'),'--seed','0','--launch-sha','a'*40,
          '--input-manifest',str(tmp_path/'absent.json'),'--input-manifest-sha256','b'*64]
    def reject(*args,**kwargs):
        raise RuntimeError('literal admission refusal')
    monkeypatch.setattr(hmasd_admission,'require_admission',reject)
    monkeypatch.setattr(c,'threads',lambda:pytest.fail('topology effects before admission'))
    with pytest.raises(RuntimeError,match='literal admission refusal'):
        run.main(args)
    assert not (tmp_path/'forbidden').exists()
    with pytest.raises(SystemExit):
        run.parser().parse_args([*args[:2],'--seed','1',*args[4:]])


def test_published_manifest_fixed_optimizer_ordinary_and_hashes():
    manifest=json.loads((ROOT/'docs/research/candidates/typed_joint_skill_decision/B04_INPUT.json').read_bytes())
    run.validate_manifest(manifest,ROOT)
    for category,key,value in [('training','optimizer',{'name':'AdamW','lr':.002}),
                               ('ordinary','P',{'entry':'search_placement','max_static_calls':6001})]:
        changed=copy.deepcopy(manifest);changed[category][key]=value
        with pytest.raises(ValueError):
            run.validate_manifest(changed,ROOT)
    changed=copy.deepcopy(manifest)
    changed['pinned_upstream_sources'][next(iter(changed['pinned_upstream_sources']))]='0'*64
    with pytest.raises(ValueError,match='upstream bytes'):
        run.validate_manifest(changed,ROOT)


@pytest.mark.parametrize('representation',[str,lambda v:'GPU-'+str(v),lambda v:v,lambda v:v.bytes])
def test_gpu_uuid_literal_serializations(representation):
    value=uuid.UUID('294302a9-40ff-1a09-43b0-5fd98e06b557')
    assert c.gpu_uuid(representation(value))=='GPU-'+str(value)
    with pytest.raises(ValueError):
        c.gpu_uuid('wrong-device')


def test_features_exact_whitelist_and_independent_literal_encoding(monkeypatch):
    f=geometry();assert c.validate_features(f)==3
    with pytest.raises(ValueError,match='whitelist'):
        c.validate_features({**f,'initial_uav_coordinates':[[0.,0.,0.]]*6})
    with pytest.raises(ValueError):
        c.validate_features({**f,'layouts_xyz':f['layouts_xyz'][0]})
    # Stub tensor creation only. No torch module/model/forward is instantiated.
    monkeypatch.setitem(sys.modules,'torch',SimpleNamespace(float32=np.float32,tensor=lambda v,dtype:np.asarray(v,dtype=dtype)))
    actual=model.fields(f,[2,0]);independent=functional.fields(f,[2,0])
    assert set(actual)==set(c.SHAPES)
    for key,shape in c.SHAPES.items():
        assert actual[key].shape==(2,*shape)
        assert actual[key].dtype==np.float32
        np.testing.assert_array_equal(actual[key],independent[key])
    assert actual['U'][0,0,0]==np.float32(f['layouts_xyz'][2][0][0]/5000.)
    assert actual['U'][0,0,3:].tolist()==[1.,0.,0.,0.,0.,0.]
    assert actual['E_UU'][0,0,0,0]==np.float32((f['layouts_xyz'][2][0][0]-f['layouts_xyz'][2][1][0])/5000.)


class LiteralRng:
    def __init__(self,permutations=()):
        self.permutations=iter(permutations);self.calls=[]
    def permutation(self,n):
        self.calls.append(('permutation',n));return np.asarray(next(self.permutations))
    def choice(self,others,n,replace):
        self.calls.append(('choice',others.tolist(),n,replace));return np.asarray(others[:n])


def test_continuous_order_crosses_permutation_boundaries():
    rng=LiteralRng([[2,0,1],[1,2,0],[0,1,2]])
    order=training.ContinuousOrder(3,rng)
    assert order.batch(5)==[2,0,1,1,2]
    assert order.batch(4)==[0,0,1,2]
    assert rng.calls==[('permutation',3)]*3


def test_teacher_subset_padding_soft_entropy_and_ties():
    rng=LiteralRng()
    ids,mask,q,h=training.subset_indices([0.,.02,.02],rng)
    assert ids==[0,1,2]+[0]*13 and mask==[True]*3+[False]*13
    expected=np.exp([-1.,0.,0.]);expected/=expected.sum()
    np.testing.assert_allclose(q[:3],expected,atol=1e-8,rtol=1e-7)
    assert float(q[3:].sum())==0 and q.dtype==np.float32
    assert h==pytest.approx(-float(np.sum(expected*np.log(expected))))
    assert rng.calls==[]
    rewards=[0.]*20;rewards[17]=1.
    ids,mask,q,_=training.subset_indices(rewards,rng)
    assert ids==[*range(15),17] and all(mask) and len(set(ids))==16
    assert rng.calls[0][2:]==(15,False) and 17 not in rng.calls[0][1]
    assert model.choose([3.,3.,2.],[8,2,1])==2
    compared=functional.compare([1.,0.],[0.,1.])
    assert compared['choice_discrepancy'] and not compared['all_within_tolerance']


def test_padded_batch_charges_physical_rows_not_labels():
    r={'features':geometry(2),'J':np.asarray([.1,.2])}
    packed,ids,mask,q,h,js=training.training_batch([r]*32,LiteralRng())
    assert all(v.shape[0]==512 for v in packed.values())
    assert mask.shape==(32,16) and int(mask.sum())==64
    assert ids[0]==[0,1]+[0]*14
    assert np.all(q[:,2:]==0) and js.shape==(32,16)
    assert len(h)==32


def test_train_numeric_cache_has_no_fresh_or_nested_infos(monkeypatch):
    monkeypatch.setattr(c,'TRAIN_COUNT',2)
    f=geometry(2)
    class Original:
        split='train';cache={}
        def load(self,world):
            return {'identity':{'world':world,'user_positions_xy':f['users_xy'],'bs_xyz':f['bs_xyz']},
                    'layouts_xyz':f['layouts_xyz'],'infos':[{'contract_reward':.2},{'contract_reward':.3}],
                    'construction':{'raw_metadata':[{'kind':k,'k':n} for k,n in zip(f['kinds'],f['ks'])]}}
    view=bank.TrainingBank(Original());record=view.load(c.TRAIN_START)
    assert set(record)=={'identity','J','features'} and not any(isinstance(v,(list,dict)) for v in vars(view).values())
    assert all(not v.flags.writeable for v in vars(view).values())
    assert bank.features(record)['layouts_xyz'].dtype==np.float64
    np.testing.assert_array_equal(bank.rewards(record),[.2,.3])
    with pytest.raises(ValueError,match='train-only'):
        view.load(c.FRESH_START)


def test_bank_hash_binding_and_train_fresh_address(tmp_path):
    s=store(tmp_path);f=geometry(1);world=c.TRAIN_START
    metadata=[{'identity':{'world':world},'construction':{'raw_metadata':[{'kind':'kmeans_plain','k':4}]},
               'infos':[{'contract_reward':.1}],'source_sha':s.launch_sha,'input_sha256':s.input_sha256}]
    relative='raw/bank/train/0000.npz'
    e.npz_write(s,relative,{'layouts':np.asarray(f['layouts_xyz']),'users':np.asarray([f['users_xy']]),
        'initial':np.asarray([f['layouts_xyz'][0]]),'bs':np.asarray([f['bs_xyz']]),
        'offsets':np.asarray([0,1]),'metadata':np.asarray(e.encoded(metadata).decode())})
    view=bank.Bank(s.root,s.files,'train',s.launch_sha,s.input_sha256)
    assert view.load(world)['identity']['world']==world
    with pytest.raises(ValueError,match='leakage'):
        view.load(c.FRESH_START)
    (s.root/relative).write_bytes(b'tamper');view.cache.clear()
    with pytest.raises(ValueError,match='modified'):
        view.load(world)


def test_raw8_dedupe_keeps_original_source_rows():
    f=geometry(8)
    raw=[{'index':i,'kind':k,'k':n,'positions_xyz':xyz,'served':[0]*(i%4)}
         for i,(k,n,xyz) in enumerate(zip(f['kinds'],f['ks'],f['layouts_xyz']))]
    raw[1]={'index':1,'kind':'subset_relay','k':4,'positions_xyz':list(reversed(raw[0]['positions_xyz'])),'served':[0,1]}
    raw[2]['positions_xyz']=list(reversed(raw[2]['positions_xyz']))
    selected,provenance=shortlist.select_menu(raw)
    assert len(selected)<=8 and provenance['canonical_distinct']==7
    assert len({p['layout_sha256'] for p in selected})==len(selected)
    assert any(raw[p['source_index']]['positions_xyz']!=p['positions_xyz'] for p in selected)
    online_source=(SOURCE/'online.py').read_text()
    assert "positions=np.asarray(raw[chosen]['positions_xyz']" in online_source
    assert "indices=sorted(p['source_index'] for p in selected)" in online_source


def test_shortlist_four_functions_match_pinned_original_ast():
    import subprocess
    original=subprocess.run(['git','show','61a2dfa9cde0178d482d0a079c5629c3bcb7789e:experiments/candidates/typed_joint_skill_decision/contract.py'],
                            cwd=ROOT,check=True,capture_output=True).stdout
    assert hashlib.sha256(original).hexdigest()=='71c5eb1d904370cbb853ce1cbfbde652391bb78b25b3a42c4ecebaeb653d82fe'
    extract=lambda text:{n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
    old,new=extract(original),extract((SOURCE/'shortlist.py').read_bytes())
    assert all(old[k]==new[k] for k in ('rows','canonical_layout','layout_bytes','select_menu'))


def test_gzip_manifest_identity_exclusive_and_pending_budget(tmp_path):
    s=store(tmp_path);value={'adverse':[False,True],'all':[1.,-.2]}
    path=s.write_gzip('raw/reading.json.gz',value)
    assert gzip.decompress(path.read_bytes())==e.encoded(value)
    assert s.files['raw/reading.json.gz']['sha256']==e.sha(path)
    assert s.bill.pending[-1]==path.stat().st_size+65536
    with pytest.raises(FileExistsError):
        s.write_gzip('raw/reading.json.gz',value)
    with pytest.raises(ValueError,match='unbound'):
        e.load_output(s.root,s.files,'raw/unlisted.json')


def test_trace_preserves_completed_row_when_budget_refuses(tmp_path):
    bill=FakeBill();trace=e.Trace(tmp_path/'trace.gz',bill)
    for i in range(24):
        trace.write({'i':i})
    def refuse(**kwargs):
        raise RuntimeError('count boundary')
    bill.check=refuse
    with pytest.raises(RuntimeError,match='count boundary'):
        trace.write({'i':24,'adverse':True})
    trace.close();rows=list(e.read_trace(trace.path))
    assert rows[-1]=={'i':24,'adverse':True} and len(rows)==25
    timings=trace.timing()
    assert timings['rows']==25 and timings['format_cpu_seconds']>=0 and timings['write_compress_flush_wall_seconds']>=0


def test_partial_bank_labels_survive_original_query_failure(tmp_path,monkeypatch):
    s=store(tmp_path);monkeypatch.setattr(c,'TRAIN_COUNT',1);f=geometry(2)
    identity={'world':c.TRAIN_START,'initial_positions_xyz':f['layouts_xyz'][0],
              'user_positions_xy':f['users_xy'],'bs_xyz':f['bs_xyz']}
    raw=[{'index':i,'positions_xyz':np.asarray(x)} for i,x in enumerate(f['layouts_xyz'])]
    monkeypatch.setattr(bank,'prepare',lambda n,w:(object(),identity,raw,f,{},0.))
    calls=[]
    def static(*args,**kwargs):
        calls.append(1)
        if len(calls)==2:
            raise RuntimeError('original physics failure')
        return {'contract_reward':-.4}
    fake=SimpleNamespace(host=SimpleNamespace(static_evaluate=static))
    with pytest.raises(RuntimeError,match='original physics failure'):
        bank.build_bank(s,fake,'train')
    rows=list(e.read_trace(s.root/'raw/bank/train/0000-partial.jsonl.gz'))
    assert rows[0]['type']=='prepared' and rows[1]['info']=={'contract_reward':-.4}
    assert not (s.root/'raw/bank/train/0000.npz').exists() and len(calls)==2


def test_bill_padding_gpu_wall_and_immutable_unique_roots(tmp_path,monkeypatch):
    paths=[tmp_path/x for x in ('source','asset','runs')]
    for p in paths:p.mkdir()
    calls=[]
    monkeypatch.setattr(e,'allocated',lambda roots,seen=None:(calls.append(list(roots)) or 100))
    monkeypatch.setattr(e,'cpu',lambda:{'total_seconds':0.})
    values=[0]*len(e.COUNTERS)
    bill=e.Bill(values,contextlib.nullcontext(),[*paths,paths[2]/'nested'],paths[:2])
    assert len(bill.roots)==3 and len(calls)==2
    bill.rows('training',512,64);bill.rows_done('training',512)
    assert values[e.COUNTERS.index('training_valid_candidates')]==64
    assert values[e.COUNTERS.index('all_candidate_presentations')]==512
    with pytest.raises(RuntimeError,match='ceiling'):
        bill.charge('native_steps',e.LIMITS['native_steps']+1)
    monkeypatch.setitem(sys.modules,'torch',SimpleNamespace(cuda=SimpleNamespace(is_initialized=lambda:False)))
    times=iter([10.,10.75,10.75]);monkeypatch.setattr(e.time,'perf_counter',lambda:next(times))
    with bill.gpu():pass
    assert values[e.COUNTERS.index('gpu_reserved_microseconds')]==750000


def test_resource_failure_snapshot_preserves_original_error(tmp_path,monkeypatch):
    monkeypatch.setattr(e,'allocated',lambda roots,seen=None:0)
    monkeypatch.setattr(e,'cpu',lambda:{'total_seconds':0.})
    bill=e.Bill([0]*len(e.COUNTERS),contextlib.nullcontext(),[tmp_path],[])
    class Cuda:
        def is_initialized(self):return True
        def synchronize(self):raise RuntimeError('secondary synchronization failure')
    monkeypatch.setitem(sys.modules,'torch',SimpleNamespace(cuda=Cuda()))
    with pytest.raises(ValueError,match='original effect failure'):
        with bill.gpu():raise ValueError('original effect failure')
    bill.values[e.COUNTERS.index('gpu_reserved_microseconds')]=e.LIMITS['gpu_reserved_microseconds']+1
    assert bill.snapshot()['counters']['gpu_reserved_microseconds']>e.LIMITS['gpu_reserved_microseconds']
    assert bill.snapshot()['gpu_cleanup_errors']==["RuntimeError('secondary synchronization failure')"]
    with pytest.raises(RuntimeError,match='GPU wall ceiling'):bill.check()


def test_child_whitelist_rejects_bank_or_future_context(tmp_path,monkeypatch):
    monkeypatch.setattr(run.os,'getppid',lambda:123)
    context={k:None for k in run.CHILD_KEYS}
    context.update(parent_pid=123,admission={'child_pid':123,'direction':'typed_joint_skill_decision','sha':'a'*40,'command_sha256':'c'},
        launch_sha='a'*40,source_root=str(run.ROOT),out=str(tmp_path))
    (tmp_path/'launch-manifest.json').write_bytes(e.encoded({'sha':'a'*40,'command_sha256':'c'}))
    run.checked_child(context)
    with pytest.raises(RuntimeError,match='legal-only'):
        run.checked_child({**context,'bank':{}})
    context['launch_sha']='d'*40
    with pytest.raises(RuntimeError):run.checked_child(context)


def test_world_geometry_rng_gate_refuses_mutations():
    f=geometry(1)
    identity={'world':c.FRESH_START,'initial_positions_xyz':f['layouts_xyz'][0],
              'user_positions_xy':f['users_xy'],'bs_xyz':f['bs_xyz'],'native_rng_sha256':'fixed',
              'agents':[str(i) for i in range(6)],'transmitter_mask':[True]*6,'current_step':0}
    record={'identity':identity,'layouts_xyz':f['layouts_xyz'],'construction':{'raw_metadata':[{'kind':'kmeans_plain','k':4}]}}
    decision={**{k:identity[k] for k in ('world','initial_positions_xyz','user_positions_xy','bs_xyz')},'arm':'RawJ',
              'construction_identity':identity,'reset_identity':{**identity,'state':{'current_step':0,'positions_xyz':identity['initial_positions_xyz']}},
              'chosen_raw_index':0,'positions_xyz':f['layouts_xyz'][0],
              'feature_sha256':hashlib.sha256(e.encoded(bank.features(record))).hexdigest(),
              'construction_sha256':hashlib.sha256(e.encoded(record['construction'])).hexdigest()}
    reader.world_gate(decision,record,[])
    for key in ('world','native_rng_sha256','bs_xyz'):
        changed=copy.deepcopy(decision)
        if key=='native_rng_sha256':changed['reset_identity'][key]='other'
        else:changed[key]=None
        with pytest.raises(AssertionError):reader.world_gate(changed,record,[])


def test_committed_reset_failure_stops_before_native_step(tmp_path,monkeypatch):
    monkeypatch.setattr(native,'reset_identity',lambda env,d:{'state':'changed'})
    env=SimpleNamespace(step=lambda *a:pytest.fail('step before reset proof'))
    with pytest.raises(AssertionError,match='before first'):
        native.execute(env,{'reset_identity':{'state':'committed'}},tmp_path/'no.gz',FakeBill())
    assert not (tmp_path/'no.gz').exists()


def test_service_gaps_censoring_and_adverse_reading():
    masks=[[False]*50 for _ in range(500)]
    for row in masks:row[0]=True
    masks[10][1]=True
    result=reader.service_summary(masks)
    assert result['always_served_users']==[0] and 49 in result['never_served_users']
    assert result['per_user'][1]['first_service_step']==11
    assert result['per_user'][1]['gaps']==[
        {'start_step':1,'length':10,'left_censored':True,'right_censored':False},
        {'start_step':12,'length':489,'left_censored':False,'right_censored':True}]
    assert result['per_user'][49]['longest_gap']==500
    diagnostics=[]
    assert not reader.close([1.],[2.],'adverse score',diagnostics,fatal=False)
    assert diagnostics[-1]['passed'] is False


def test_exact_matching_first_permutation_against_pinned_pure_source():
    from experiments.candidates.coupled_host_joint_skills_stage1.planner import assign_targets
    initial=np.asarray([[0.,0.,100.],[0.,0.,100.],[1.,0.,100.],[1.,0.,100.],[2.,0.,100.],[2.,0.,100.]])
    for target in (initial[::-1].copy(),initial.copy(),initial+np.asarray([1e-12,0.,0.])):
        assert planner_reader.assignment(initial,target,FakeBill())==assign_targets(initial,target).tolist()


def test_cached_queries_refuse_tamper_and_unconsumed_tail():
    f=geometry(1);xyz=f['layouts_xyz'][0]
    row={'positions_xyz':xyz,'allow_a2a':True,'info':{'J':-.1},'state':{'positions_xyz':xyz,
        'connections':[[False]*50]*6,'routing_paths':{},'uav_connections':[[False]*6]*6,'uav_bs_connections':[[False]]*6}}
    cache=planner_reader.CachedQueries([row,row],SimpleNamespace())
    assert cache.evaluate(xyz,True)=={'J':-.1}
    with pytest.raises(AssertionError,match='unconsumed'):cache.finish()
    with pytest.raises(AssertionError,match='request'):planner_reader.CachedQueries([row],SimpleNamespace()).evaluate(xyz,False)


def test_complete_counts_include_reader_and_padded_paths():
    bill=FakeBill();s=SimpleNamespace(bill=bill)
    counts={'fits':6,'fits_completed':6,'updates':24576,'updates_completed':24576,'training_world_presentations':786432,
        'training_candidate_presentations':12582912,'training_completed_candidates':12582912,'bank_worlds':16512,
        'label_rebuild_worlds':16512,'native_steps':584000,'native_completed':584000,'main_episodes':1152,'audit_episodes':16,
        'spawn_attempts':1152,'spawn_completed':1152,'reader_state_checks':585168,'functional_contexts':6144,
        'endpoint_contexts':6144,'cold_contexts':768,'engineering_contexts':16}
    bill.values.update(counts);calls=2*10+1152+585168+16
    bill.values.update(static_calls=calls,static_completed=calls,all_candidate_presentations=12582912)
    run.count_complete(s,[],10)
    bill.values['reader_state_checks']-=1
    with pytest.raises(AssertionError):run.count_complete(s,[],10)


def test_immutable_selection_commits_before_parent_future_reads():
    tree=ast.parse((SOURCE/'run.py').read_bytes())
    functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    child=ast.unparse(functions['case_main']);parent=ast.unparse(functions['spawn_case'])
    assert child.index('child_write(')<child.index("'selection_ready'")<child.index('connection.recv(')<child.index('native.host.static_evaluate(')
    assert parent.index("'selection_ready'")<parent.index('view.load(')<parent.index('endpoint_choice(')<parent.index("'verified'")
    assert set(run.CHILD_KEYS).isdisjoint({'bank','labels','endpoint','chosen_raw_index','future','cached_decision'})
    complete=ast.unparse(functions['main'])
    assert complete.index('training.fit_once(')<complete.index('for asset in assets:')<complete.index('training.endpoint(')
    assert 'retry' not in [a.dest for a in run.parser()._actions]


def test_preserved_update_attempt_completion_and_partial_refusal():
    attempt={'type':'attempt','fit':'R1000s0','update':1,'worlds':[c.TRAIN_START],
             'raw_indices':[[0]],'valid_mask':[[True]],'subset_identity_sha256':'a'*64}
    complete={**attempt,'type':'complete','CE':[1.]}
    assert list(training.completed_updates([attempt,complete]))==[complete]
    with pytest.raises(AssertionError,match='attempted-update'):
        list(training.completed_updates([attempt]))
    with pytest.raises(AssertionError,match='attempted-update'):
        list(training.completed_updates([attempt,{**complete,'worlds':[c.FRESH_START]}]))


def test_independent_saved_array_movement_and_gradient_tamper():
    initial={'a':np.asarray([1.,2.],dtype=np.float32),'b':np.asarray([[0.]],dtype=np.float32)}
    final={'a':np.asarray([4.,6.],dtype=np.float32),'b':np.asarray([[0.]],dtype=np.float32)}
    observed=reader.learner_movement(final,initial)
    assert observed=={'l2':5.,'max_absolute':4.}
    good={'grad_norm':2.,'parameter_movement':observed}
    assert reader.gradient_and_movement(good)==(2.,observed)
    for bad in ({**good,'grad_norm':-1.},{**good,'grad_norm':float('nan')},
                {**good,'parameter_movement':{'l2':5.,'max_absolute':-4.}}):
        with pytest.raises(AssertionError,match='diagnostic'):reader.gradient_and_movement(bad)
    with pytest.raises(AssertionError):reader.close(5.,6.,'tampered final movement',[])


def test_immutable_and_mutable_disk_hardlink_counted_once(tmp_path):
    import os
    frozen=tmp_path/'frozen';mutable=tmp_path/'mutable';frozen.mkdir();mutable.mkdir()
    (frozen/'a').write_bytes(b'fixed literal artifact')
    os.link(frozen/'a',mutable/'same-inode')
    seen=set();first=e.allocated([frozen],seen);second=e.allocated([mutable],seen)
    assert first+second==e.allocated([frozen,mutable])


def test_full_planner_control_cache_against_mocked_original(tmp_path,monkeypatch):
    from experiments.candidates.coupled_host_joint_skills_stage1 import planner as p,host,menus
    f=geometry(3)
    env=SimpleNamespace(n_uavs=6,n_ground_bs=1,area_size=5000,height_range=(50.,150.),
        ground_bs_positions=np.asarray([f['bs_xyz']]),uav_positions=np.asarray(f['layouts_xyz'][0]),
        connections=np.zeros((6,50),dtype=bool),uav_connections=np.zeros((6,6),dtype=bool),
        uav_bs_connections=np.zeros((6,1),dtype=bool),routing_paths={i:[('uav',i),('bs',0)] for i in range(6)})
    def candidates(*args,**kwargs):
        return [{'index':i,'kind':'kmeans_plain','k':4+i,'relay_targets':[0,1],
                 'positions_xyz':np.asarray(x)} for i,x in enumerate(f['layouts_xyz'])]
    rows=[]
    def literal_static(g,x,allow_a2a=True):
        g.uav_positions=np.asarray(x).copy()
        info={'contract_reward':.2,'coverage_backhauled':.4,'uav_connection_count':0}
        rows.append(e.plain({'positions_xyz':x,'allow_a2a':allow_a2a,'info':info,'state':{
            'positions_xyz':x,'connections':g.connections,'routing_paths':g.routing_paths,
            'uav_connections':g.uav_connections,'uav_bs_connections':g.uav_bs_connections}}))
        return info
    monkeypatch.setattr(np.random,'default_rng',lambda world:object())
    monkeypatch.setattr(p,'build_candidates',candidates);monkeypatch.setattr(p,'link_ranges',lambda env:{})
    monkeypatch.setattr(p,'static_evaluate',literal_static);monkeypatch.setattr(host,'static_evaluate',literal_static)
    monkeypatch.setattr(host,'make_host',lambda *a,**kw:env)
    initial=env.uav_positions.copy();menu=menus.compute_menu(c.FRESH_START,area_size=5000,budget=3000)
    path=tmp_path/'queries.gz'
    with gzip.open(path,'wb') as stream:
        for row in rows:stream.write(e.encoded(row))
    decision={'world':c.FRESH_START,'initial_positions_xyz':initial.tolist(),'positions_xyz':menu['positions_xyz'],
              'target_permutation':menu['m_permutation'],'P_menu':menu}
    calls=len(rows);result=planner_reader.replay(env,p,path,decision,FakeBill())
    assert result['complete_consumption'] and result['new_physics_queries']==0 and len(rows)==calls
    assert result['query_rows']==sum(menu['static']['evaluations'])+1
    changed=copy.deepcopy(rows);changed[0]['positions_xyz'][0][0]+=.001
    with gzip.open(path,'wb') as stream:
        for row in changed:stream.write(e.encoded(row))
    with pytest.raises(AssertionError,match='request'):
        planner_reader.replay(env,p,path,decision,FakeBill())
