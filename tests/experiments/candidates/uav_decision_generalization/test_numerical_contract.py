import copy
import json
from pathlib import Path
import pytest
import torch
import numpy as np
from experiments.candidates.uav_decision_generalization import contract as c,models,independent,phases,reading,data


@pytest.fixture
def features():
    initial=[[100+100*i,200+50*i,100] for i in range(6)]
    users=[[50+20*i,40+10*i] for i in range(50)]
    plans=[{'construction_slot':slot,'kind':kind,'k':4,'assigned_targets_xyz':[[300+30*i+slot,500+20*i,100] for i in range(6)]}
           for slot,kind in ((1,'kmeans_plain'),(3,'subset_relay'))]
    return c.make_features(initial,users,[2500,2500,100],plans)


def test_exact_tensor_values_and_identity(features):
    t=models.geometry_tensors(features)
    for name,shape in c.TENSOR_SHAPES.items():
        assert t[name].shape==(2,*shape)
        assert t[name].dtype==np.float32
    slot=features['display_order'][0]
    plan=next(p for p in features['plans'] if p['construction_slot']==slot)
    np.testing.assert_array_equal(t['U'][0,:,6:],np.eye(6,dtype=np.float32))
    np.testing.assert_array_equal(t['Y'][0,:,2:],np.eye(50,dtype=np.float32))
    delta=(np.asarray(features['initial_uav_xyz'][0])-np.asarray([*features['user_xy'][0],0]))/5000
    np.testing.assert_array_equal(t['E_UY'][0,0,0,:4],np.asarray([*delta,np.sum(delta**2)],dtype=np.float32))
    target_delta=(np.asarray(plan['assigned_targets_xyz'][0])-np.asarray(plan['assigned_targets_xyz'][1]))/5000
    np.testing.assert_array_equal(t['E_UU'][0,0,0,4:],np.asarray([*target_delta,np.sum(target_delta**2)],dtype=np.float32))
    candidate={k:torch.from_numpy(v) for k,v in t.items()}
    assert models.flatten_tensors(candidate).shape==(2,5377)
    reconstructed,slots=independent.fields(features,'R')
    assert slots==features['display_order']
    for key in t:
        torch.testing.assert_close(candidate[key],reconstructed[key],rtol=0,atol=0)
    assert sum(np.count_nonzero(t[k][0][...,6:] if k=='U' else t[k][0][...,2:]) for k in ('U','Y'))==56


@pytest.mark.parametrize('arm',['A','R','N'])
def test_parameter_counts_and_functional_layers(features,arm):
    model=models.make_model(arm,123,device='cpu').eval()
    assert sum(p.numel() for p in model.parameters())==c.PARAMETERS[arm]
    record={'features':features}
    x=models.context_input(record,arm,device='cpu')
    with torch.inference_mode():
        answer=model(x).squeeze(-1).tolist()
    independent_x,slots=independent.fields(features,arm)
    reconstructed=independent.logits(model.state_dict(),independent_x,arm)
    assert independent.comparison(reconstructed,answer)['all_within_tolerance']
    assert models.select_slot(answer,slots)==models.select_slot(reconstructed,slots)


@pytest.mark.parametrize('arm',['A','R'])
def test_tiny_deterministic_update_and_mask(features,arm):
    torch.set_num_threads(1)
    slots=sorted(p['construction_slot'] for p in features['plans'])
    record={'features':features,'labels':{'slot_order':slots,'soft_targets':[.2,.8]}}
    x,mask,target=models.training_batch([record],arm,device='cpu')
    digests=[]
    for _ in range(2):
        model=models.make_model(arm,321,device='cpu');before=models.parameter_digest(model.state_dict())
        optimizer=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.0001)
        logits=model(x).squeeze(-1).masked_fill(~mask,-1e4)
        loss=-(target*torch.log_softmax(logits,-1)).sum(-1).mean();loss.backward()
        assert torch.isfinite(loss) and all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters())
        assert sum(float(p.grad.square().sum()) for p in model.parameters())>0
        optimizer.step();after=models.parameter_digest(model.state_dict())
        assert before!=after
        digests.append(after)
    assert digests[0]==digests[1]
    assert mask.sum()==2 and target.sum()==1
    assert target[0,:2].tolist()==pytest.approx([dict(zip(slots,[.2,.8]))[s] for s in features['display_order']])


def test_frozen_worlds_counts_tie_fallback_and_budget(tmp_path):
    train=list(c.worlds('train'));fresh=list(c.worlds())
    assert len(train)==768 and len(fresh)==384
    assert [r['world'] for r in fresh if r['block']==1]==list(range(106130000,106130128))
    assert {r['world'] for r in train}.isdisjoint(r['world'] for r in fresh)
    with pytest.raises(ValueError):list(c.worlds('test'))
    assert c.MAX_NATIVE_STEPS==(384*8+384+16)*500==1736000
    assert c.MAX_STATIC_CALLS==384*(9+6001)==2307840
    assert 6*2*(256+128)+3*128==4992
    assert models.select_slot([1.,1.],[3,1])==3
    assert c.fallback_slot(3,[1,5])==1
    ledger={'schema':1,'prior_counters':dict.fromkeys(data.COUNTERS,0),'prior_cpu_seconds':0.,'prior_gpu_seconds':0.,'disk_roots':[str(tmp_path)]}
    bill=data.Bill(ledger,tmp_path/'out');bill.enter('native_step_calls',c.MAX_NATIVE_STEPS)
    with pytest.raises(data.BudgetExceeded):bill.enter('native_step_calls')
    assert bill.delta['native_step_calls']==1736000


def test_wrong_locator_manifest_source_hashes_rejected(tmp_path,monkeypatch):
    p=tmp_path/'locator.json';p.write_text('{}')
    with pytest.raises(ValueError,match='digest'):phases.load_bound_json(p,'0'*64)
    (tmp_path/'manifest.jsonl').write_text('')
    with pytest.raises(ValueError,match='digest'):models.verify_manifest(tmp_path,'0'*64)
    monkeypatch.setattr(c,'SOURCE_SHA256',{'source.py':'0'*64});(tmp_path/'source.py').write_text('bad')
    with pytest.raises(ValueError,match='source'):phases.verify_sources(tmp_path)
    payload=tmp_path/'payload.json';payload.write_text('{}')
    entry={'path':'payload.json','bytes':2,'sha256':'0'*64}
    manifest=tmp_path/'manifest.jsonl';manifest.write_bytes(c.encode_json(entry))
    with pytest.raises(ValueError,match='drift'):models.verify_manifest(tmp_path,data.hash_file(manifest))


def test_tolerance_flags_and_service_harm_preserved():
    flags=independent.comparison([.1,.4],[.1000005,.401])
    assert flags['component_within_tolerance']==[True,False]
    values=[0.]*469+[.5]*31
    tail=reading.service_tail(values)
    assert tail=={'minimum':0.,'p10':0.,'zero_steps':469,'longest_zero_run':469,'final100_mean':.155}
    with pytest.raises(ValueError):reading.service_tail(values[:-1])

def test_train_only_dataset_binding_and_rejected_address(features,tmp_path,monkeypatch):
    address=next(c.worlds('train'))
    prefix=f"prepared/b1/train/{address['world']}"
    labels={'address':address,'feature_sha256':c.digest(features),'slot_order':[1,3],
            'Q':[.2,.4],'soft_targets':c.soft_targets([.2,.4])}
    values={'summary.json':{'status':'complete','contract_sha256':c.ORIGINAL_CONTRACT_SHA256,'source_sha256':c.SOURCE_SHA256},
            'config.json':{},prefix+'/features.json':features,
            prefix+'/provenance.json':{'address':address,'feature_sha256':c.digest(features)},
            prefix+'/codec.json':{'feature_sha256':c.digest(features)},f"worlds/b1/train/{address['world']}/labels.json":labels}
    entries=[]
    for relative,value in values.items():
        path=tmp_path/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(c.encode_json(value))
        entries.append({'path':relative,'bytes':path.stat().st_size,'sha256':data.hash_file(path)})
    manifest=tmp_path/'manifest.jsonl';manifest.write_bytes(b''.join(c.encode_json(e) for e in entries))
    locator={'root':str(tmp_path),'manifest_sha256':data.hash_file(manifest),'summary_sha256':data.hash_file(tmp_path/'summary.json')}
    calls=[]
    def addresses(split='fresh'):
        calls.append(split);return iter([address])
    monkeypatch.setattr(c,'worlds',addresses)
    dataset=phases.Dataset(tmp_path,locator,old=True,training_only=True)
    assert calls==['train'] and dataset.split(1,'train')[0]['features']==features
    bad=copy.deepcopy(values);bad[f"worlds/b1/train/{address['world']}/labels.json"]['address']={**address,'world':address['world']+1}
    original=phases.Dataset.json
    monkeypatch.setattr(phases.Dataset,'json',lambda self,relative:bad[relative])
    with pytest.raises(ValueError,match='binding'):phases.Dataset(tmp_path,locator,old=True,training_only=True)


def test_gpu_choice_preserved_when_independent_reconstruction_changes(features,tmp_path,monkeypatch):
    from experiments.candidates.uav_decision_generalization import read_b01
    slots=features['display_order'];world=106130000
    record={'address':{'world':world,'split':'fresh'},'features':features,
            'labels':{'slot_order':slots,'Q':[.1,.7]}}
    prediction={'world':world,'slots':slots,'feature_sha256':c.digest(features),'logits':[1.,0.],'selected_slot':slots[0]}
    bill=data.Bill({'schema':1,'prior_counters':dict.fromkeys(data.COUNTERS,0),'prior_cpu_seconds':0.,'prior_gpu_seconds':0.,'disk_roots':[str(tmp_path)]},tmp_path/'out')
    from types import SimpleNamespace
    monkeypatch.setattr(independent,'logits',lambda *args:[0.,1.])
    rows=read_b01.endpoint_read(SimpleNamespace(bill=bill),[record],{},'A','final',{'predictions':[prediction]})
    assert rows[0]['executed_Q']==.1 and rows[0]['independent_Q']==.7
    assert rows[0]['choice_mismatch'] and not rows[0]['float_comparison']['all_within_tolerance']
    assert bill.delta['reader_A_contexts']==1
    prediction['feature_sha256']='0'*64
    with pytest.raises(ValueError,match='identity'):read_b01.endpoint_read(SimpleNamespace(bill=bill),[record],{},'A','final',{'predictions':[prediction]})

def test_complete_update_chain_reader_checks_order_and_terminal_optimizer(features,tmp_path):
    from types import SimpleNamespace
    records=[{'address':{'world':106100000+i},'features':features} for i in range(256)]
    initial={'test.weight':torch.tensor([.2])};final={'test.weight':torch.tensor([.3])}
    before=models.parameter_digest(initial);after=models.parameter_digest(final)
    config={'initial_sha256':before,'order_seed':106120002,'arm':'A'}
    out=tmp_path/'fits';out.mkdir();rng=np.random.Generator(np.random.PCG64(config['order_seed']))
    rows=[]
    for epoch in range(64):
        order=rng.permutation(256).tolist()
        for batch in range(8):
            indices=order[32*batch:32*(batch+1)]
            update=len(rows)+1
            rows.append({'update':update,'epoch':epoch,'batch':batch,'indices':indices,
                         'worlds':[records[i]['address']['world'] for i in indices],
                         'feature_sha256':[c.digest(features)]*32,'parameter_before_sha256':before if update==1 else after,
                         'parameter_after_sha256':after,'loss':.2,'grad_l2':.1,'grad_max_absolute':.1,'gradient_sha256':'a'*64})
    path=out/'updates.jsonl';path.write_bytes(b''.join(c.encode_json(row) for row in rows))
    optimizer={'param_groups':[{'lr':.001,'weight_decay':.0001,'betas':(.9,.999),'eps':1e-8}],
               'state':{0:{'step':torch.tensor(512.),'exp_avg':torch.tensor([.1]),'exp_avg_sq':torch.tensor([.01])}}}
    torch.save(optimizer,out/'optimizer.pt')
    ledger={'schema':1,'prior_counters':dict.fromkeys(data.COUNTERS,0),'prior_cpu_seconds':0.,'prior_gpu_seconds':0.,'disk_roots':[str(tmp_path)]}
    bill=data.Bill(ledger,tmp_path/'out')
    result=reading.read_update_chain(tmp_path,'fits',config,initial,final,records,bill)
    assert result['updates']==512 and result['contexts']==16384 and result['movement']['l2']>0
    assert bill.delta['reader_updates_read']==512
    rows[0]['indices']=list(reversed(rows[0]['indices']));path.write_bytes(b''.join(c.encode_json(row) for row in rows))
    with pytest.raises(AssertionError,match='order'):reading.read_update_chain(tmp_path,'fits',config,initial,final,records,data.Bill(ledger,tmp_path/'out'))


def test_sequential_bill_and_external_storage_categories(tmp_path):
    root=tmp_path/'old';root.mkdir();(root/'evidence').write_bytes(b'evidence')
    output=tmp_path/'new';output.mkdir()
    ledger={'schema':1,'prior_counters':dict.fromkeys(data.COUNTERS,0),'prior_cpu_seconds':0.,'prior_gpu_seconds':0.,'disk_roots':[str(output)]}
    bill=data.Bill(ledger,output/'phase')
    from types import SimpleNamespace
    phases.register_external_roots(SimpleNamespace(bill=bill),root)
    snapshot=bill.snapshot()
    assert snapshot['disk_root_categories']['inherited_evidence']==[str(root)]
    assert snapshot['current_phase_new_evidence_allocated_bytes']==0
    summary={'bill':{'cumulative_counters':ledger['prior_counters'],'cumulative_cpu_seconds':1.,'cumulative_gpu_seconds':2.}}
    with pytest.raises(ValueError,match='underprices'):phases.assert_prior(ledger,summary)
    revised={**ledger,'prior_cpu_seconds':1.,'prior_gpu_seconds':2.};phases.assert_prior(revised,summary)
    changed={**revised,'prior_counters':{**revised['prior_counters'],'fit_calls':1}}
    with pytest.raises(ValueError,match='counters'):phases.assert_prior(changed,summary)
