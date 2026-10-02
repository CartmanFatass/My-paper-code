"""Paid ordinary responses and separate static readings; stdlib synthetic checks."""
from __future__ import annotations
import ast
import copy
import math
from pathlib import Path
import pytest
from experiments.candidates.typed_joint_skill_decision.b06_bank_consumer import reader,contract as c

ROOT=Path(__file__).resolve().parents[5]


def ordinary():
    infos=[{'contract_reward':.5,'coverage_backhauled':.5,'frontend_capacity_with_path_mbps':3.,'count':1,'mask':True,'uav_connection_count':0} for _ in range(2)]
    raw=[{'positions_xyz':[[float(i),1.,2.]]} for i in range(2)]
    paid=copy.deepcopy(infos);paid[1]['contract_reward']=math.nextafter(.5,1.)
    queries=[{'positions_xyz':r['positions_xyz'],'allow_a2a':True,'info':info,
              'state':{'positions_xyz':r['positions_xyz'],'current_step':0,
                       'reward_info':{k:v for k,v in info.items() if k!='uav_connection_count'},
                       'uav_connections':[[False]*6 for _ in range(6)]}}
             for r,info in zip(raw,paid)]
    decision={'arm':'RawJ','world':9,'chosen_raw_index':1,'scores':{str(i):info for i,info in enumerate(paid)},
              'selection_counts':{'static_calls':2},'P_menu':None}
    reference={'infos':infos,'best':0}
    return decision,queries,raw,reference


def test_paid_self_argmax_authority_and_three_distinct_scores():
    decision,queries,raw,reference=ordinary();diagnostics=[]
    result=reader.ordinary_paid(decision,queries,raw,[0,1],reference,diagnostics)
    assert result['paid_winner']==1 and result['bank_winner_on_paid_indices']==0 and result['winner_differs']
    assert result['bank_exact_max_indices']==[0,1] and result['paid_exact_max_indices']==[1]
    metrics=reader.static_values('RawJ',decision,reference,{'contract_reward':.6},result)
    assert metrics['bank_at_chosen_J']==.5
    assert metrics['online_paid_at_chosen_J']==math.nextafter(.5,1.)
    assert metrics['matched_minus_bank_J']==.6-.5
    assert metrics['matched_minus_online_J']==.6-math.nextafter(.5,1.)
    student=reader.static_values('R1000s0',decision,reference,{'contract_reward':.6})
    assert student['online_paid_at_chosen_J'] is student['matched_minus_online_J'] is None
    decision['P_menu']={'static':{'P_relay_contract_reward':.4}}
    p=reader.static_values('P',decision,reference,{'contract_reward':.6})
    assert p['bank_at_chosen_J'] is None and p['online_paid_at_chosen_J']==.4


@pytest.mark.parametrize('fault',['choice','scores','count','order','physics','discrete','nonfinite','state','a2a','shortlist','link_count','reward_keys'])
def test_paid_response_tampering_and_offline_forcing_refused(fault):
    decision,queries,raw,reference=ordinary()
    if fault=='choice':decision['chosen_raw_index']=0
    elif fault=='scores':decision['scores']['1']['contract_reward']=.5
    elif fault=='count':decision['selection_counts']['static_calls']=3
    elif fault=='order':queries.reverse()
    elif fault=='physics':queries[0]['info']['contract_reward']=.1
    elif fault=='discrete':queries[0]['info']['count']=1.
    elif fault=='nonfinite':queries[0]['info']['contract_reward']=float('nan')
    elif fault=='state':queries[0]['state']['current_step']=1
    elif fault=='a2a':queries[0]['allow_a2a']=False
    elif fault=='link_count':queries[0]['info']['uav_connection_count']=1
    elif fault=='reward_keys':queries[0]['info']['extra_unrecorded']=0
    else:decision.update(arm='Raw8J',shortlist={'source_indices':[1,0]})
    # Decisions must equal the actual trace values; break aliases in synthetic fixture.
    if fault=='scores':
        queries[1]['info']=dict(queries[1]['info'],contract_reward=math.nextafter(.5,1.))
        queries[1]['state']['reward_info']=queries[1]['info']
    with pytest.raises((AssertionError,ValueError)):
        reader.ordinary_paid(decision,queries,raw,[0,1],reference,[])


def test_complete_composition_keeps_unchanged_original_work():
    old=ast.parse((ROOT/'experiments/candidates/typed_joint_skill_decision/b04/reader.py').read_text())
    new=ast.parse((ROOT/'experiments/candidates/typed_joint_skill_decision/b06_bank_consumer/reader.py').read_text())
    a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=='complete')
    b=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='complete')
    # Whole fit/update/endpoint loop and all fresh512 offline references are unchanged.
    def loop(tree,expression):return next(n for n in tree.body if isinstance(n,ast.For) and ast.unparse(n.iter)==expression)
    for expression in ('assets','range(c.FRESH_START, c.FRESH_START + 512)','(0, 1)'):
        assert ast.dump(loop(a,expression),include_attributes=False)==ast.dump(loop(b,expression),include_attributes=False)
    text=ast.unparse(b)
    assert text.count('frame_reader(')==1 and text.count('original_audit(')==1 and text.count('replay(')==1
    assert 'ordinary_paid(decision' in text and 'expected_choice' not in text
    assert not any(isinstance(n,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr=='exact' for t in n.targets) for n in ast.walk(b))


def test_only_exact_selected_consumer_bounds():
    value={'selected':True,'limits':{'cpu_seconds':28800,'gpu_child_seconds':14400,'wall_seconds':57600,'disk_bytes':6442450944}}
    assert c.selected_investment(value)==value['limits']
    value['limits']['cpu_seconds']+=1
    with pytest.raises(ValueError):c.selected_investment(value)


def test_runtime_snapshot_roots_and_compact_proof_containment(tmp_path):
    bank=tmp_path/'staging';bank.mkdir();proof=bank/'validation';proof.mkdir();scratch=tmp_path/'scratch'
    scope={'producer_root':str(bank),'reader_root':str(proof),'own_scratch':str(scratch),
           'include_current_source_snapshot':True,'shared_interpreter_copied':False}
    binding={'disk_scope':scope,'bank':{'reader':{'root':str(proof)}}}
    source=tmp_path/'snapshot-selected-only-at-launch';out=tmp_path/'actual-admitted-out'
    result=c.disk_scope(binding,source,out,str(bank))
    assert result['roots']==list(map(str,(source,out,bank,scratch)))
    binding['bank']['reader']['root']=str(tmp_path/'uncounted-proof');scope['reader_root']=binding['bank']['reader']['root']
    with pytest.raises(ValueError,match='within'):c.disk_scope(binding,source,out,str(bank))


@pytest.mark.parametrize('fault',[None,'train_fresh','cold_bank','cold_receipt','hidden_cold','job','source','proof'])
def test_actual_worker_boundary_with_opaque_proof(tmp_path,monkeypatch,fault):
    from experiments.candidates.typed_joint_skill_decision.b06_bank_consumer import worker
    from experiments.candidates.typed_joint_skill_decision.b07_fixed_bank import contract as fixed,read
    bank=tmp_path/'bank';bank.mkdir();proof_root=bank/'validation';proof_root.mkdir();out=tmp_path/'out';out.mkdir()
    investment={'selected':True,'limits':{'cpu_seconds':28800,'gpu_child_seconds':14400,'wall_seconds':57600,'disk_bytes':6442450944}}
    proof_binding={'root':str(proof_root),'manifest_sha256':'opaque'}
    binding={'investment':investment,'bank':{'reader':proof_binding,'producer_root':str(bank)},
        'disk_scope':{'producer_root':str(bank),'reader_root':str(proof_root),'own_scratch':str(tmp_path/'scratch'),
                      'include_current_source_snapshot':True,'shared_interpreter_copied':False},
        'executable_sources':{name:c.sha(ROOT/name) for name in fixed.READER_FILES|fixed.CONSUMER_FILES|set(fixed.FROZEN_B05)}}
    if fault=='source':binding['executable_sources'][next(iter(fixed.CONSUMER_FILES))]='0'*64
    path=tmp_path/'input.json';path.write_bytes(c.encoded(binding))
    identity={'pid':42,'start_ticks':7};admission={'child_pid':42,'direction':c.DIRECTION,'sha':'a'*40,'command_sha256':'b'*64}
    (out/'launch-manifest.json').write_bytes(c.encoded({'sha':'a'*40,'command_sha256':'b'*64}))
    parent={'pid':42,'identity':identity,'admission':admission,'source_root':str(ROOT),'out':str(out),'launch_sha':'a'*40,
        'source_binding':{},'investment':investment,'consumer_input_path':str(path),'consumer_input_sha256':c.sha(path),
        'deployment':{'limits':investment['limits'],'disk_roots':list(map(str,(ROOT,out,bank,tmp_path/'scratch')))}}
    is_fit=fault=='train_fresh'
    job=next(c.jobs()) if is_fit else list(c.jobs())[7]
    if is_fit:job['new_stream']=True
    if fault=='job':job['world']+=128
    request={'parent':parent,'job':job,'original_input':{'original':True},'prior_parent_cpu_seconds':1.}
    if is_fit:
        request.update(bank={'root':str(bank),'files':{'raw/bank/train/0000.npz':{},'raw/bank/fresh/0000.npz':{}},
            'producer_source_sha':fixed.PRODUCER_SHA,'producer_input_sha256':fixed.PRODUCER_INPUT,'manifest_sha256':fixed.PRODUCER_MANIFEST,
            'certification':{'reader':proof_binding}},initial_hashes={})
    else:request.update(checkpoint_path='/opaque-full-final.pt',checkpoint_sha256='opaque-final')
    if fault=='cold_bank':request['bank']={}
    if fault=='cold_receipt':request['receipt']={}
    if fault=='hidden_cold':request['renamed_labels']={}
    monkeypatch.setattr(worker.os,'getppid',lambda:42)
    monkeypatch.setattr(worker,'parent_death',lambda value:None)
    monkeypatch.setattr(c,'scientific_binding',lambda *args:{'original':True})
    def opaque_receipt(*args):
        if fault=='proof':raise ValueError('opaque compact proof refused')
        return {'input':{'producer':{'root':str(bank)}}}
    monkeypatch.setattr(read,'receipt',opaque_receipt)
    monkeypatch.setattr(fixed,'producer',lambda *args,**kwargs:{'root':str(bank),'files':{'raw/bank/train/0000.npz':{},'raw/bank/fresh/0000.npz':{}}})
    if fault:
        with pytest.raises(ValueError):worker.checked_context(request)
    else:assert worker.checked_context(request)['input']['producer']['root']==str(bank)
