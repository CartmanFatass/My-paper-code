from copy import deepcopy
import json
import numpy as np
import pytest
from experiments.candidates.uav_episode_policy_search.b01.read import _read_all,read_result
from experiments.candidates.uav_episode_policy_search.b01.study import _execute,run_batch
from experiments.candidates.uav_episode_policy_search.b01.audit import audit_episode
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.study import artifact,load_raw
from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest


def report():return dict(actual=dict(native_steps=0,refits=0,optimizer_steps=0),inflight={})

def rows(root):
    with (root/'episodes.jsonl').open() as stream:return [json.loads(line) for line in stream]


def test_complete_synthetic_collector_reader_and_exposure(tiny,monkeypatch):
    root,protocol,actor,batch,env=tiny
    # The synthetic adapter generated scalar physics, so this verifies state plumbing, not independent native physics.
    # No real environment factory or production artifact can be consumed in the fixture.
    def forbidden(*args,**kwargs):raise AssertionError('native/extra fit forbidden in saved-data reader')
    import experiments.candidates.uav_episode_policy_search.b01.study as study
    monkeypatch.setattr(study,'make_real',forbidden)
    monkeypatch.setattr(study,'update',forbidden)
    before=state_digest(actor.state_dict())
    r=report();_read_all(batch,root,actor,protocol,r)
    e=protocol.expected()
    assert env.steps==e['native_steps']==880
    assert e['complete_episodes']==110 and len(rows(root))==110
    assert e['training_episodes']==64 and e['evaluation_episodes']==46
    assert r['actual']['saved_episodes']==110 and r['actual']['scalar_states']==1210
    assert r['actual']['native_steps']==r['actual']['refits']==r['actual']['optimizer_steps']==0
    assert r['actual']['updates']==8 and r['actual']['directions']==16 and r['actual']['normal_coordinates']==28096
    assert r['actual']['logical_power_links']==326700 and r['actual']['observation_rows']==6050
    assert batch['actual']['fits_started']==batch['actual']['fits_completed']==4
    assert r['policy_costs']['all_policy']['head_requests']==800
    assert r['policy_costs']['all_policy']['zero_head_requests']==320
    assert len(r['comparisons']['contrasts'])==37
    assert len(batch['search_artifacts'])==28
    assert before==state_digest(actor.state_dict())
    assert r['policy_costs']['all_policy']==batch['costs']['all_policy']


def test_tampered_policy_physics_and_saved_rows(tiny):
    root,p,actor,batch,_=tiny
    row=rows(root)[0];raw=load_raw(root/row['raw']['path'])
    theta=load_raw(root/'search/CAL0_i00_k00.npz')['delta']*.05
    for field,value,message in [('observations',.01,'saved old'),('commands',1,'held original motion'),
                                ('reward',.01,'native reward'),('head_logits',.01,'independent head'),
                                ('innovation',.01,'motion innovation'),('nav_pre',1,'navigation recurrence'),
                                ('action_index',1,'motion action_index')]:
        bad={k:v.copy() for k,v in raw.items()};bad[field].flat[0]+=value
        with pytest.raises(AssertionError,match=message):audit_episode(bad,row,p,actor,theta=theta)
    bad={k:v.copy() for k,v in raw.items()};bad['refresh_observations'][0,0,0]+=.01
    with pytest.raises(AssertionError,match='setter row'):audit_episode(bad,row,p,actor,theta=theta)
    bad={k:v.copy() for k,v in raw.items()};bad['terminated'][0]=True
    with pytest.raises(AssertionError,match='terminal clock'):audit_episode(bad,row,p,actor,theta=theta)


def test_tampered_gaussian_update_and_episode_binding(tiny,tmp_path):
    import shutil
    root,p,actor,batch,_=tiny
    for field,relative,message in [('delta','search/CAL0_i00_k00.npz','Gaussian'),
                                    ('theta','search/CONT1_center_02.npz','independent search update')]:
        copied=tmp_path/field;shutil.copytree(root,copied)
        path=copied/relative;data=load_raw(path);data[field].flat[-1]+=.1;np.savez_compressed(path,**data)
        bad=deepcopy(batch)
        index=next(i for i,a in enumerate(bad['search_artifacts']) if a['path']==relative)
        bad['search_artifacts'][index]=artifact(path,copied)
        with pytest.raises(AssertionError,match=message):_read_all(bad,copied,actor,p,report())
    copied=tmp_path/'rng';shutil.copytree(root,copied)
    bad=deepcopy(batch);rr=rows(copied);rr[0]['motion_root']+=1
    (copied/'episodes.jsonl').write_text('\n'.join(json.dumps(r) for r in rr)+'\n')
    bad['episode_log']=artifact(copied/'episodes.jsonl',copied)
    with pytest.raises(AssertionError,match='execution order motion_root'):_read_all(bad,copied,actor,p,report())


def test_attempt_journal_tamper(tiny,tmp_path):
    import shutil
    root,p,actor,batch,_=tiny
    copied=tmp_path/'attempt';shutil.copytree(root,copied)
    path=copied/'attempts.jsonl';events=[json.loads(line) for line in path.read_text().splitlines()]
    events[0]['effect']='native_step';path.write_text('\n'.join(json.dumps(e) for e in events)+'\n')
    bad=deepcopy(batch);bad['attempt_log']=artifact(path,copied)
    with pytest.raises(AssertionError,match='attempt identity/order'):_read_all(bad,copied,actor,p,report())


def test_failed_effect_preserves_attempt_and_started_fit(tiny,tmp_path):
    _,p,actor,_,original_env=tiny
    SyntheticEnv=type(original_env)
    out=tmp_path/'failed';out.mkdir()
    for name in ('raw','search'):(out/name).mkdir()
    env=SyntheticEnv(p.horizon);env.fail_at=0
    batch=dict(actual=dict(fits_started=0,fits_completed=0,updates=0,constructor_calls=1,constructor_resets=1,
               native_dense_power_slots=275,native_unique_distance_pairs=260,zero_decisions=0),inflight={},search_artifacts=[],
               initial_parent_state_sha256=state_digest(actor.state_dict()))
    with pytest.raises(RuntimeError,match='interrupted step'):_execute(out,actor,env,p,batch,lambda:None)
    assert batch['actual']['fits_started']==1 and batch['actual']['native_step_calls']==1
    assert batch['actual'].get('native_steps',0)==0 and not list((out/'raw').iterdir())
    assert batch['inflight']['tick']==0
    last=json.loads((out/'attempts.jsonl').read_text().splitlines()[-1])
    assert last['effect']=='native_step'
    assert batch['costs']['all_policy']['head_requests']==5
    assert len(batch['search_artifacts'])==3


def test_production_refuses_unadmitted_and_synthetic_results(tiny,tmp_path):
    root,p,actor,batch,_=tiny
    with pytest.raises(ValueError,match='admission'):run_batch(tmp_path/'absent','fake',admission=None,parent_path='missing')
    assert not (tmp_path/'absent').exists()
    with pytest.raises(FileExistsError):run_batch(root,'fake',admission={'sha':'fake'},parent_path='missing')
    out=tmp_path/'not_scientific';out.mkdir();(out/'summary.json').write_text(json.dumps(dict(batch,state='COMPLETE',protocol=p.to_dict())))
    with pytest.raises(AssertionError,match='fixed complete production'):read_result(out,root,'missing')
    assert json.loads((out/'reading.json').read_text())['actual']==dict(native_steps=0,refits=0,optimizer_steps=0)


def test_cli_admission_precedes_scientific_effects(monkeypatch,tmp_path):
    import scripts.hmasd_admission as admission
    from experiments.candidates.uav_episode_policy_search.b01 import run,read
    def denied(*args,**kwargs):raise RuntimeError('test admission denied')
    monkeypatch.setattr(admission,'require_admission',denied)
    args=['--out',str(tmp_path/'absent'),'--parent','missing','--launch-sha','fake','--seed','40160000']
    for module in (run,read):
        module_args=args if module is run else [*args,'--input-out',str(tmp_path/'source')]
        with pytest.raises(RuntimeError,match='admission denied'):module.main(module_args)
    assert not (tmp_path/'absent').exists()


def test_unique_center_storage_and_reconstructed_hidden(tiny):
    root,p,actor,batch,_=tiny
    for row in rows(root):
        raw=load_raw(root/row['raw']['path'])
        assert 'hbar' not in raw
    direction=load_raw(root/'search/CONT0_i00_k00.npz')
    assert set(direction)=={'delta','center_sha256'}
    assert direction['delta'].dtype==np.float64
    assert len([a for a in batch['search_artifacts'] if '_center_' in a['path']])==4*(p.iterations+1)
    assert batch['parent_body']['parameters']==34715
    assert batch['parent_movement']==dict(parameters=34715,l2=0.,max_abs=0.,changed_parameters=0)


def test_standalone_reader_keeps_canonical_inputs_unchanged(tiny,tmp_path,monkeypatch):
    """Mock admission/strict asset/runtime binding only; exercise real streaming fixture reader and distinct output."""
    import shutil
    from experiments.candidates.uav_episode_policy_search.b01 import contract,study
    from experiments.candidates.uav_fleet_adaptation.b08_local_gate import assets
    root,p,actor,batch,_=tiny
    source=tmp_path/'source';shutil.copytree(root,source)
    fake=deepcopy(batch)
    fake.update(object=contract.OBJECT,state='COMPLETE',scientific_execution=True,protocol=p.to_dict(),
                inherited_cost=contract.INHERITED_COST,sources={},parent={'fixture_only':True},launch_sha='synthetic',expected=p.expected(),admission={'sha':'synthetic'},
                runtime=dict(python='fixture',compiler='fixture',numpy='fixture',torch='fixture',device='cpu',numpy_config='fixture',
                             torch_threads=1,torch_interop_threads=1,deterministic_algorithms=True,
                             thread_environment={k:'1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')}))
    (source/'summary.json').write_text(json.dumps(fake))
    config={k:fake[k] for k in ('sources','protocol','runtime','parent','inherited_cost')}
    (source/'config.json').write_text(json.dumps(config))
    parent_path=tmp_path/'synthetic-parent-marker';parent_path.write_bytes(b'fixture is not a P0 checkpoint')
    from experiments.candidates.uav_local_history.b01.study import file_identity
    fake['parent']['sha256']=file_identity(parent_path)['sha256'];config['parent']=fake['parent']
    (source/'summary.json').write_text(json.dumps(fake));(source/'config.json').write_text(json.dumps(config))
    before={str(path.relative_to(source)):path.read_bytes() for path in source.rglob('*') if path.is_file()}
    monkeypatch.setattr(contract,'FROZEN',p);monkeypatch.setattr(contract,'source_identities',lambda repo:{})
    monkeypatch.setattr(study,'runtime',lambda:fake['runtime'])
    monkeypatch.setattr(assets,'load_parent',lambda path:(actor,fake['parent']))
    out=tmp_path/'reader_output'
    r=read_result(source,root,parent_path,report_out=out)
    assert r['status']=='VERIFIED' and r['actual']['native_steps']==0
    assert (out/'reading.json').exists() and not (source/'reading.json').exists()
    after={str(path.relative_to(source)):path.read_bytes() for path in source.rglob('*') if path.is_file()}
    assert after==before
    with pytest.raises(FileExistsError):read_result(source,root,parent_path,report_out=out)


def test_direct_read_script_sets_package_and_admits_first(monkeypatch,tmp_path):
    import inspect
    import runpy
    import sys
    import scripts.hmasd_admission as admission
    from experiments.candidates.uav_episode_policy_search.b01 import read
    seen=[]
    def denied(*args,**kwargs):
        seen.append(inspect.currentframe().f_back.f_globals['__package__'])
        raise RuntimeError('direct fixture admission denied')
    monkeypatch.setattr(admission,'require_admission',denied)
    monkeypatch.setattr(sys,'argv',[read.__file__,'--input-out',str(tmp_path/'source'),'--out',str(tmp_path/'report'),
                                  '--parent','missing','--launch-sha','synthetic','--seed','40160000'])
    with pytest.raises(RuntimeError,match='direct fixture admission denied'):runpy.run_path(read.__file__,run_name='__main__')
    assert seen==['experiments.candidates.uav_episode_policy_search.b01']
    assert not (tmp_path/'report').exists()


def test_invalid_episode_address_stops_before_effect(tiny,tmp_path):
    from experiments.candidates.uav_episode_policy_search.b01.collect import collect_episode
    _,p,actor,_,original_env=tiny
    env=type(original_env)(p.horizon)
    identity=next(p.identities());identity['motion_root']+=1
    with pytest.raises(ValueError,match='fixed domains'):
        collect_episode(env,identity=identity,actor=actor,out=tmp_path,protocol=p,counts={},inflight={},policy_sha='fixture',theta=np.zeros(28))
    assert env.steps==0 and not list(tmp_path.iterdir())
